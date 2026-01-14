/**
 * QUANTUM CHECKPOINT SYSTEM
 * φ-Weighted Auto-Save for Crash-Proof Session State
 *
 * Philosophy: "The last second should never be lost"
 *
 * Uses golden ratio mathematics for optimal checkpoint frequency:
 * - Early work: frequent saves (learning phase)
 * - Stable work: sparser saves (confidence phase)
 * - Never more than 30 seconds without state capture
 *
 * Lightweight: Only saves STATE, not CONTENT
 */

const fs = require('fs');
const path = require('path');

class QuantumCheckpoint {
    constructor(projectRoot) {
        this.PHI = 1.618033988749895;
        this.PHI_INVERSE = 0.6180339887498949;

        this.projectRoot = projectRoot;
        this.checkpointDir = path.join(projectRoot, '.quantum_state');
        this.stateFile = path.join(this.checkpointDir, 'session_state.json');
        this.historyFile = path.join(this.checkpointDir, 'checkpoint_history.jsonl');

        // Fibonacci checkpoint intervals (seconds)
        this.CHECKPOINT_INTERVALS = [1, 1, 2, 3, 5, 8, 13, 21, 30];
        this.currentIntervalIndex = 0;
        this.lastCheckpoint = Date.now();
        this.checkpointCount = 0;

        // Session state (lightweight)
        this.state = {
            sessionId: this._generateSessionId(),
            startedAt: new Date().toISOString(),
            lastUpdate: null,

            // Core state vector (minimal)
            currentFocus: null,           // 1 sentence: what are we doing?
            filesModified: [],            // List of paths (not content)
            filesCreated: [],             // List of new files
            todoItems: [],                // Current todo list
            lastAction: null,             // Last completed action
            nextAction: null,             // Intended next action
            progressPercent: 0,           // 0-100

            // Recovery hints
            thoughtFragment: null,        // Last coherent thought (1-2 sentences)
            contextFiles: [],             // Files Claude was reading
            decisionPending: null,        // Any decision waiting for input

            // Crash metadata
            checkpointNumber: 0,
            crashRecoveries: 0
        };

        this._ensureDir();
        this._loadPreviousState();
    }

    /**
     * Generate session ID using timestamp + random
     */
    _generateSessionId() {
        const timestamp = new Date().toISOString().split('T')[0];
        const random = Math.random().toString(36).substring(2, 8);
        return `${timestamp}-${random}`;
    }

    /**
     * Ensure checkpoint directory exists
     */
    _ensureDir() {
        if (!fs.existsSync(this.checkpointDir)) {
            fs.mkdirSync(this.checkpointDir, { recursive: true });
        }

        // Add to .gitignore if not present
        const gitignorePath = path.join(this.projectRoot, '.gitignore');
        if (fs.existsSync(gitignorePath)) {
            const gitignore = fs.readFileSync(gitignorePath, 'utf8');
            if (!gitignore.includes('.quantum_state')) {
                fs.appendFileSync(gitignorePath, '\n# Quantum checkpoint state (session-only)\n.quantum_state/\n');
            }
        }
    }

    /**
     * Load previous state if crash recovery
     */
    _loadPreviousState() {
        if (fs.existsSync(this.stateFile)) {
            try {
                const previousState = JSON.parse(fs.readFileSync(this.stateFile, 'utf8'));

                // Check if previous session ended cleanly
                if (!previousState.endedCleanly) {
                    console.log(`\n╔══════════════════════════════════════════════════════════════╗`);
                    console.log(`║           🔄 CRASH RECOVERY DETECTED                         ║`);
                    console.log(`╠══════════════════════════════════════════════════════════════╣`);
                    console.log(`║ Previous Session: ${previousState.sessionId.padEnd(40)}║`);
                    console.log(`║ Last Checkpoint:  ${previousState.lastUpdate?.substring(0, 40) || 'Unknown'.padEnd(40)}║`);
                    console.log(`║ Progress:         ${(previousState.progressPercent + '%').padEnd(40)}║`);
                    console.log(`╠══════════════════════════════════════════════════════════════╣`);
                    console.log(`║ LAST FOCUS:                                                  ║`);
                    console.log(`║ ${(previousState.currentFocus || 'Unknown').substring(0, 60).padEnd(60)}║`);
                    console.log(`╠══════════════════════════════════════════════════════════════╣`);
                    console.log(`║ THOUGHT FRAGMENT:                                            ║`);
                    console.log(`║ ${(previousState.thoughtFragment || 'None captured').substring(0, 60).padEnd(60)}║`);
                    console.log(`╠══════════════════════════════════════════════════════════════╣`);
                    console.log(`║ NEXT ACTION WAS:                                             ║`);
                    console.log(`║ ${(previousState.nextAction || 'Unknown').substring(0, 60).padEnd(60)}║`);
                    console.log(`╚══════════════════════════════════════════════════════════════╝\n`);

                    // Carry over recovery count
                    this.state.crashRecoveries = (previousState.crashRecoveries || 0) + 1;

                    // Save recovery context
                    this._appendHistory({
                        type: 'CRASH_RECOVERY',
                        previousSession: previousState.sessionId,
                        recoveredAt: new Date().toISOString(),
                        lostState: {
                            focus: previousState.currentFocus,
                            thought: previousState.thoughtFragment,
                            nextAction: previousState.nextAction,
                            progress: previousState.progressPercent
                        }
                    });
                }
            } catch (e) {
                console.log('[Quantum] Could not parse previous state, starting fresh');
            }
        }
    }

    /**
     * Calculate next checkpoint interval using Fibonacci
     * More frequent early, stabilizing over time
     */
    _getNextInterval() {
        const interval = this.CHECKPOINT_INTERVALS[
            Math.min(this.currentIntervalIndex, this.CHECKPOINT_INTERVALS.length - 1)
        ];

        // Advance interval index (slower saves over time)
        if (this.checkpointCount > 0 && this.checkpointCount % 5 === 0) {
            this.currentIntervalIndex = Math.min(
                this.currentIntervalIndex + 1,
                this.CHECKPOINT_INTERVALS.length - 1
            );
        }

        return interval * 1000; // Convert to milliseconds
    }

    /**
     * UPDATE STATE - Call this frequently with minimal overhead
     *
     * @param {Object} updates - Partial state updates
     */
    update(updates) {
        // Merge updates into state
        Object.assign(this.state, updates, {
            lastUpdate: new Date().toISOString(),
            checkpointNumber: this.checkpointCount
        });

        // Check if checkpoint needed
        const timeSinceLastCheckpoint = Date.now() - this.lastCheckpoint;
        const nextInterval = this._getNextInterval();

        if (timeSinceLastCheckpoint >= nextInterval) {
            this._saveCheckpoint();
        }
    }

    /**
     * FORCE CHECKPOINT - Call before risky operations
     */
    forceCheckpoint(reason = 'manual') {
        this.state.lastCheckpointReason = reason;
        this._saveCheckpoint();
    }

    /**
     * Internal: Save checkpoint to disk
     */
    _saveCheckpoint() {
        this.state.endedCleanly = false; // Will be set true on clean exit
        this.checkpointCount++;
        this.lastCheckpoint = Date.now();

        // Write state file (atomic via temp file)
        const tempFile = this.stateFile + '.tmp';
        fs.writeFileSync(tempFile, JSON.stringify(this.state, null, 2));
        fs.renameSync(tempFile, this.stateFile);

        // Append to history (for debugging)
        this._appendHistory({
            type: 'CHECKPOINT',
            number: this.checkpointCount,
            timestamp: new Date().toISOString(),
            focus: this.state.currentFocus,
            progress: this.state.progressPercent
        });
    }

    /**
     * Append to checkpoint history log
     */
    _appendHistory(entry) {
        fs.appendFileSync(this.historyFile, JSON.stringify(entry) + '\n');
    }

    /**
     * CLEAN EXIT - Call when session ends normally
     */
    endSession(summary = null) {
        this.state.endedCleanly = true;
        this.state.sessionSummary = summary;
        this.state.endedAt = new Date().toISOString();

        this._saveCheckpoint();

        this._appendHistory({
            type: 'SESSION_END',
            sessionId: this.state.sessionId,
            duration: Date.now() - new Date(this.state.startedAt).getTime(),
            checkpoints: this.checkpointCount,
            crashes: this.state.crashRecoveries
        });

        console.log(`[Quantum] Session ended cleanly after ${this.checkpointCount} checkpoints`);
    }

    /**
     * GET RECOVERY CONTEXT - For Claude to read on startup
     */
    getRecoveryContext() {
        if (!fs.existsSync(this.stateFile)) {
            return null;
        }

        try {
            const state = JSON.parse(fs.readFileSync(this.stateFile, 'utf8'));
            if (!state.endedCleanly) {
                return {
                    crashed: true,
                    previousSession: state.sessionId,
                    lastFocus: state.currentFocus,
                    thoughtFragment: state.thoughtFragment,
                    nextAction: state.nextAction,
                    progress: state.progressPercent,
                    filesModified: state.filesModified,
                    todoItems: state.todoItems
                };
            }
        } catch (e) {
            return null;
        }

        return { crashed: false };
    }
}

/**
 * USAGE EXAMPLE FOR CLAUDE SESSIONS:
 *
 * // At session start:
 * const checkpoint = new QuantumCheckpoint('/Users/onthego/ARCHIVIT_01');
 * const recovery = checkpoint.getRecoveryContext();
 * if (recovery?.crashed) {
 *     console.log('Recovering from crash:', recovery);
 * }
 *
 * // During work (call frequently, minimal overhead):
 * checkpoint.update({
 *     currentFocus: 'Implementing quantum containment ACU',
 *     thoughtFragment: 'Deciding between recursive vs iterative ACU calculation',
 *     nextAction: 'Write the RecursiveACUEngine class',
 *     progressPercent: 45,
 *     filesModified: ['scripts/quantum_containment.js']
 * });
 *
 * // Before risky operation:
 * checkpoint.forceCheckpoint('before-major-refactor');
 *
 * // At clean session end:
 * checkpoint.endSession('Completed quantum containment implementation');
 */

module.exports = { QuantumCheckpoint };

// CLI usage
if (require.main === module) {
    const projectRoot = process.argv[2] || process.cwd();
    const checkpoint = new QuantumCheckpoint(projectRoot);
    const recovery = checkpoint.getRecoveryContext();

    if (recovery?.crashed) {
        console.log('\n=== CRASH RECOVERY AVAILABLE ===');
        console.log(JSON.stringify(recovery, null, 2));
    } else {
        console.log('No crash recovery needed - starting fresh session');
    }
}
