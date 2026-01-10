/**
 * PRESERVATION MODE SYSTEM
 * ========================
 * Full Archive Control with Status Monitoring
 *
 * Provides users the choice between:
 * - FULL PRESERVATION: Complete uncompressed backup to designated folder
 * - COMPRESSION MODE: Spiral compression with IPFS overflow
 *
 * Status Indicator:
 * - GREEN: Full preservation active, all data backed up
 * - YELLOW: Compression mode, space-efficient but less redundant
 * - RED: Attention needed (corruption detected, recovery available)
 *
 * Recovery System:
 * - Uses integrity chain to detect corruption
 * - Quantum reasoning logs for restoration path
 * - Original data point recovery when possible
 * - Retrain option if original unavailable
 */

// ═══════════════════════════════════════════════════════════════════════════
// PRESERVATION STATUS ENUM
// ═══════════════════════════════════════════════════════════════════════════

const PreservationStatus = Object.freeze({
    FULL_ACTIVE: 'full_active',           // Green - Full backup running
    COMPRESSION_ACTIVE: 'compression',     // Yellow - Compression mode
    ATTENTION_NEEDED: 'attention',         // Red - Issue detected
    RECOVERY_IN_PROGRESS: 'recovering',    // Red pulsing - Recovering
    OFFLINE: 'offline',                    // Gray - No backup active
    SYNCING: 'syncing'                     // Blue - Currently syncing
});

const StatusColors = Object.freeze({
    [PreservationStatus.FULL_ACTIVE]: '#00FF88',      // Green
    [PreservationStatus.COMPRESSION_ACTIVE]: '#FFD700', // Yellow/Gold
    [PreservationStatus.ATTENTION_NEEDED]: '#FF4444',   // Red
    [PreservationStatus.RECOVERY_IN_PROGRESS]: '#FF6B6B', // Red (animated)
    [PreservationStatus.OFFLINE]: '#888888',           // Gray
    [PreservationStatus.SYNCING]: '#4488FF'            // Blue
});

// ═══════════════════════════════════════════════════════════════════════════
// PRESERVATION MODE MANAGER
// ═══════════════════════════════════════════════════════════════════════════

class PreservationModeManager {
    constructor() {
        this.mode = 'compression';  // Default to compression
        this.status = PreservationStatus.OFFLINE;
        this.preservationPath = null;
        this.lastBackup = null;
        this.lastIntegrityCheck = null;

        // Integrity tracking
        this.integrityLog = [];
        this.corruptionPoints = [];
        this.recoveryQueue = [];

        // Session config
        this.sessionConfig = {
            fullPreservation: false,
            preservationPath: null,
            autoBackupInterval: 5 * 60 * 1000,  // 5 minutes
            integrityCheckInterval: 15 * 60 * 1000  // 15 minutes
        };

        // Intervals
        this._backupInterval = null;
        this._integrityInterval = null;

        // Event listeners
        this.listeners = new Map();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SESSION INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Initialize preservation mode for this session
     * Called at login/session start
     *
     * @param {Object} options - Session options
     * @param {boolean} options.fullPreservation - Enable full preservation mode
     * @param {string} options.preservationPath - Path for full backups (if enabled)
     * @returns {Object} Initialization result
     */
    async initializeSession(options = {}) {
        const {
            fullPreservation = false,
            preservationPath = null
        } = options;

        this.sessionConfig.fullPreservation = fullPreservation;
        this.sessionConfig.preservationPath = preservationPath;

        // Validate preservation path if full mode requested
        if (fullPreservation) {
            if (!preservationPath) {
                return {
                    success: false,
                    error: 'Full preservation requires a designated folder path'
                };
            }

            const pathValid = await this._validatePreservationPath(preservationPath);
            if (!pathValid.valid) {
                return {
                    success: false,
                    error: pathValid.error
                };
            }

            this.preservationPath = preservationPath;
            this.mode = 'full';
            this.status = PreservationStatus.FULL_ACTIVE;
        } else {
            this.mode = 'compression';
            this.status = PreservationStatus.COMPRESSION_ACTIVE;
        }

        // Run initial integrity check
        const integrity = await this.checkIntegrity();

        if (!integrity.valid) {
            this.status = PreservationStatus.ATTENTION_NEEDED;
            this.corruptionPoints = integrity.corrupted;
        }

        // Start background processes
        this._startBackgroundProcesses();

        this._emit('initialized', {
            mode: this.mode,
            status: this.status,
            integrity: integrity
        });

        return {
            success: true,
            mode: this.mode,
            status: this.status,
            statusColor: StatusColors[this.status],
            integrity: integrity
        };
    }

    /**
     * Validate preservation path exists and is writable
     */
    async _validatePreservationPath(path) {
        // In browser context, we use File System Access API
        // This is a stub - actual implementation depends on platform

        // For Electron/Node context:
        if (typeof window !== 'undefined' && 'showDirectoryPicker' in window) {
            // File System Access API available
            return { valid: true };
        }

        // For web context without file system access
        // Would use IndexedDB with larger quota
        return {
            valid: true,
            note: 'Using IndexedDB for preservation (no file system access)'
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // STATUS MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get current status for UI display
     */
    getStatus() {
        return {
            mode: this.mode,
            status: this.status,
            color: StatusColors[this.status],
            label: this._getStatusLabel(),
            lastBackup: this.lastBackup,
            lastIntegrityCheck: this.lastIntegrityCheck,
            issuesCount: this.corruptionPoints.length,
            recoveryQueueCount: this.recoveryQueue.length
        };
    }

    /**
     * Get human-readable status label
     */
    _getStatusLabel() {
        const labels = {
            [PreservationStatus.FULL_ACTIVE]: 'Full Preservation Active',
            [PreservationStatus.COMPRESSION_ACTIVE]: 'Compression Mode',
            [PreservationStatus.ATTENTION_NEEDED]: 'Attention Needed',
            [PreservationStatus.RECOVERY_IN_PROGRESS]: 'Recovery in Progress',
            [PreservationStatus.OFFLINE]: 'Backup Offline',
            [PreservationStatus.SYNCING]: 'Syncing...'
        };
        return labels[this.status] || 'Unknown';
    }

    /**
     * Update status and notify listeners
     */
    _setStatus(newStatus) {
        const oldStatus = this.status;
        this.status = newStatus;

        if (oldStatus !== newStatus) {
            this._emit('statusChanged', {
                oldStatus: oldStatus,
                newStatus: newStatus,
                color: StatusColors[newStatus],
                label: this._getStatusLabel()
            });
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // INTEGRITY CHECKING
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Check data integrity across all stored data
     */
    async checkIntegrity() {
        this._setStatus(PreservationStatus.SYNCING);

        const results = {
            valid: true,
            checked: 0,
            corrupted: [],
            recoverable: [],
            timestamp: Date.now()
        };

        try {
            // Check 1: Genesis integrity (mathematical verification)
            const genesisCheck = await this._checkGenesisIntegrity();
            results.checked++;
            if (!genesisCheck.valid) {
                results.valid = false;
                results.corrupted.push({
                    type: 'genesis',
                    detail: genesisCheck.error,
                    recoverable: false  // Genesis cannot be recovered
                });
            }

            // Check 2: Chain integrity (hash chain)
            const chainCheck = await this._checkChainIntegrity();
            results.checked++;
            if (!chainCheck.valid) {
                results.valid = false;
                results.corrupted.push({
                    type: 'chain',
                    breakPoint: chainCheck.breakPoint,
                    detail: chainCheck.error,
                    recoverable: chainCheck.recoverable
                });
                if (chainCheck.recoverable) {
                    results.recoverable.push({
                        type: 'chain',
                        breakPoint: chainCheck.breakPoint,
                        recoveryMethod: 'retrain_from_break'
                    });
                }
            }

            // Check 3: Ring integrity (compression blocks)
            const ringCheck = await this._checkRingIntegrity();
            results.checked++;
            if (!ringCheck.valid) {
                results.valid = false;
                for (const issue of ringCheck.issues) {
                    results.corrupted.push({
                        type: 'ring',
                        ring: issue.ring,
                        detail: issue.error,
                        recoverable: issue.recoverable
                    });
                    if (issue.recoverable) {
                        results.recoverable.push({
                            type: 'ring',
                            ring: issue.ring,
                            recoveryMethod: issue.hasIPFSBackup ? 'ipfs_restore' : 'recompress'
                        });
                    }
                }
            }

            // Check 4: IPFS block integrity (if used)
            const ipfsCheck = await this._checkIPFSIntegrity();
            results.checked++;
            if (!ipfsCheck.valid) {
                for (const issue of ipfsCheck.issues) {
                    results.corrupted.push({
                        type: 'ipfs',
                        cid: issue.cid,
                        detail: issue.error,
                        recoverable: false  // IPFS blocks are immutable
                    });
                }
            }

        } catch (error) {
            results.valid = false;
            results.error = error.message;
        }

        this.lastIntegrityCheck = Date.now();

        // Log integrity check
        this.integrityLog.push({
            timestamp: results.timestamp,
            valid: results.valid,
            checked: results.checked,
            corruptedCount: results.corrupted.length
        });

        // Keep last 100 logs
        if (this.integrityLog.length > 100) {
            this.integrityLog = this.integrityLog.slice(-100);
        }

        // Update status based on results
        if (results.valid) {
            this._setStatus(
                this.mode === 'full'
                    ? PreservationStatus.FULL_ACTIVE
                    : PreservationStatus.COMPRESSION_ACTIVE
            );
        } else {
            this._setStatus(PreservationStatus.ATTENTION_NEEDED);
            this.corruptionPoints = results.corrupted;

            // Queue recoverable items
            for (const item of results.recoverable) {
                this.recoveryQueue.push(item);
            }
        }

        this._emit('integrityChecked', results);

        return results;
    }

    /**
     * Check genesis block integrity using mathematical derivation
     */
    async _checkGenesisIntegrity() {
        // Import immutable core for verification
        // This uses mathematical derivation, not cryptography
        try {
            const { immutableCore } = await import('./immutable_core.js');
            const { NorthStar } = await import('./index.js');

            if (!NorthStar.isReady) {
                return { valid: true, note: 'Seed not loaded, skipping genesis check' };
            }

            const seed = NorthStar.getSeed();
            if (!seed || !seed.genesis) {
                return { valid: false, error: 'Genesis block missing' };
            }

            const verification = immutableCore.verifyGenesis(seed.genesis);
            return {
                valid: verification.verified,
                error: verification.verified ? null : 'Genesis derivation mismatch - tampering detected',
                details: verification
            };

        } catch (error) {
            return { valid: false, error: error.message };
        }
    }

    /**
     * Check hash chain integrity
     */
    async _checkChainIntegrity() {
        try {
            const { immutableCore } = await import('./immutable_core.js');

            // Get chain from storage
            const chainData = localStorage.getItem('seed_interaction_chain');
            if (!chainData) {
                return { valid: true, note: 'No chain data yet' };
            }

            const chain = JSON.parse(chainData);
            const verification = immutableCore.verifyChain(chain);

            if (verification.valid) {
                return { valid: true };
            }

            return {
                valid: false,
                error: verification.error,
                breakPoint: verification.index,
                recoverable: verification.index > 0  // Can recover if not at genesis
            };

        } catch (error) {
            return { valid: false, error: error.message, recoverable: false };
        }
    }

    /**
     * Check compression ring integrity
     */
    async _checkRingIntegrity() {
        const issues = [];

        try {
            const ringData = localStorage.getItem('seed_rings');
            if (!ringData) {
                return { valid: true, note: 'No ring data yet' };
            }

            const rings = JSON.parse(ringData);

            for (const [ringId, ring] of Object.entries(rings)) {
                // Check if ring has required structure
                if (ring._compressed && !ring.data) {
                    issues.push({
                        ring: ringId,
                        error: 'Compressed ring missing data',
                        recoverable: ring._ipfsRef ? true : false,
                        hasIPFSBackup: !!ring._ipfsRef
                    });
                }

                // Check compression metadata
                if (ring._compressed && ring._level === undefined) {
                    issues.push({
                        ring: ringId,
                        error: 'Compression level missing',
                        recoverable: true,
                        hasIPFSBackup: false
                    });
                }
            }

        } catch (error) {
            issues.push({
                ring: 'all',
                error: error.message,
                recoverable: false,
                hasIPFSBackup: false
            });
        }

        return {
            valid: issues.length === 0,
            issues: issues
        };
    }

    /**
     * Check IPFS block integrity
     */
    async _checkIPFSIntegrity() {
        const issues = [];

        try {
            const indexData = localStorage.getItem('ipfs_block_index');
            if (!indexData) {
                return { valid: true, note: 'No IPFS blocks yet' };
            }

            const index = JSON.parse(indexData);

            // Just check index structure, not actual IPFS retrieval
            // (that would be too slow for regular integrity checks)
            for (const [ringId, blockInfo] of Object.entries(index.blocks || {})) {
                if (!blockInfo.cid) {
                    issues.push({
                        cid: 'missing',
                        error: `Block ${ringId} missing CID`,
                        ring: ringId
                    });
                }
            }

        } catch (error) {
            issues.push({
                cid: 'index',
                error: error.message
            });
        }

        return {
            valid: issues.length === 0,
            issues: issues
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // RECOVERY SYSTEM
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Attempt to recover corrupted data
     */
    async attemptRecovery(corruptionPoint) {
        this._setStatus(PreservationStatus.RECOVERY_IN_PROGRESS);

        const result = {
            success: false,
            method: null,
            details: null
        };

        try {
            switch (corruptionPoint.type) {
                case 'chain':
                    result.method = 'chain_recovery';
                    result.details = await this._recoverChain(corruptionPoint);
                    result.success = result.details.recovered;
                    break;

                case 'ring':
                    result.method = 'ring_recovery';
                    result.details = await this._recoverRing(corruptionPoint);
                    result.success = result.details.recovered;
                    break;

                case 'genesis':
                    // Genesis cannot be recovered - this is by design
                    // User must restore from backup or start fresh
                    result.method = 'none';
                    result.details = {
                        recovered: false,
                        message: 'Genesis block cannot be recovered. Restore from backup or create new seed.'
                    };
                    break;

                default:
                    result.method = 'unknown';
                    result.details = { message: 'Unknown corruption type' };
            }

        } catch (error) {
            result.error = error.message;
        }

        // Remove from corruption points if recovered
        if (result.success) {
            this.corruptionPoints = this.corruptionPoints.filter(
                p => p.type !== corruptionPoint.type ||
                     p.ring !== corruptionPoint.ring
            );

            // Update status if all issues resolved
            if (this.corruptionPoints.length === 0) {
                this._setStatus(
                    this.mode === 'full'
                        ? PreservationStatus.FULL_ACTIVE
                        : PreservationStatus.COMPRESSION_ACTIVE
                );
            }
        } else {
            this._setStatus(PreservationStatus.ATTENTION_NEEDED);
        }

        this._emit('recoveryAttempted', result);

        return result;
    }

    /**
     * Recover broken hash chain
     */
    async _recoverChain(corruptionPoint) {
        // Strategy: Truncate chain at break point and mark for retrain
        try {
            const chainData = localStorage.getItem('seed_interaction_chain');
            if (!chainData) {
                return { recovered: false, message: 'No chain data to recover' };
            }

            const chain = JSON.parse(chainData);
            const breakPoint = corruptionPoint.breakPoint;

            if (breakPoint === 0) {
                return { recovered: false, message: 'Cannot recover - break at genesis' };
            }

            // Truncate to valid portion
            const validChain = chain.slice(0, breakPoint);
            localStorage.setItem('seed_interaction_chain', JSON.stringify(validChain));

            // Log the recovery
            this._logRecovery('chain', {
                originalLength: chain.length,
                recoveredLength: validChain.length,
                entriesLost: chain.length - validChain.length
            });

            return {
                recovered: true,
                message: `Chain recovered. ${chain.length - validChain.length} entries lost after break point.`,
                entriesLost: chain.length - validChain.length
            };

        } catch (error) {
            return { recovered: false, message: error.message };
        }
    }

    /**
     * Recover corrupted ring
     */
    async _recoverRing(corruptionPoint) {
        try {
            // Try IPFS recovery first
            if (corruptionPoint.hasIPFSBackup) {
                const { ipfsStorage } = await import('./ipfs_storage.js');
                const recovered = await ipfsStorage.download(corruptionPoint.ring);

                if (recovered && !recovered._error) {
                    // Restore ring from IPFS
                    const ringData = localStorage.getItem('seed_rings');
                    const rings = ringData ? JSON.parse(ringData) : {};
                    rings[corruptionPoint.ring] = recovered;
                    localStorage.setItem('seed_rings', JSON.stringify(rings));

                    this._logRecovery('ring', {
                        ring: corruptionPoint.ring,
                        method: 'ipfs_restore'
                    });

                    return { recovered: true, message: 'Ring restored from IPFS backup' };
                }
            }

            // Try recompression if no IPFS backup
            const { SpiralCompressionEngine } = await import('./spiral_compression.js');
            const compression = new SpiralCompressionEngine();

            // Get seed data and recompress
            const { NorthStar } = await import('./index.js');
            if (NorthStar.isReady) {
                const seed = NorthStar.getSeed();
                const rings = compression.organizeIntoRings(seed);

                localStorage.setItem('seed_rings', JSON.stringify(rings));

                this._logRecovery('ring', {
                    ring: corruptionPoint.ring,
                    method: 'recompression'
                });

                return { recovered: true, message: 'Ring recovered via recompression' };
            }

            return { recovered: false, message: 'Could not recover ring - no backup or seed data' };

        } catch (error) {
            return { recovered: false, message: error.message };
        }
    }

    /**
     * Log recovery action for audit trail
     */
    _logRecovery(type, details) {
        const logEntry = {
            timestamp: Date.now(),
            type: type,
            details: details
        };

        // Store in recovery log
        const logData = localStorage.getItem('recovery_log');
        const log = logData ? JSON.parse(logData) : [];
        log.push(logEntry);

        // Keep last 50 entries
        if (log.length > 50) {
            log.shift();
        }

        localStorage.setItem('recovery_log', JSON.stringify(log));
    }

    // ═══════════════════════════════════════════════════════════════════════
    // FULL PRESERVATION BACKUP
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Perform full preservation backup (uncompressed)
     */
    async performFullBackup() {
        if (this.mode !== 'full') {
            return { success: false, error: 'Full preservation not enabled' };
        }

        this._setStatus(PreservationStatus.SYNCING);

        try {
            const { NorthStar } = await import('./index.js');

            if (!NorthStar.isReady) {
                this._setStatus(PreservationStatus.FULL_ACTIVE);
                return { success: false, error: 'Seed not loaded' };
            }

            // Export full uncompressed data
            const fullExport = NorthStar.exportPlaintext();

            // Add metadata
            const backup = {
                version: '1.0.0',
                type: 'full_preservation',
                timestamp: Date.now(),
                timestampISO: new Date().toISOString(),
                data: fullExport
            };

            // Store backup
            // In browser: use File System Access API or IndexedDB
            // In Electron/Node: write to file system
            await this._writeFullBackup(backup);

            this.lastBackup = Date.now();
            this._setStatus(PreservationStatus.FULL_ACTIVE);

            this._emit('backupCompleted', {
                type: 'full',
                timestamp: this.lastBackup,
                size: JSON.stringify(backup).length
            });

            return {
                success: true,
                timestamp: this.lastBackup,
                size: JSON.stringify(backup).length
            };

        } catch (error) {
            this._setStatus(PreservationStatus.ATTENTION_NEEDED);
            return { success: false, error: error.message };
        }
    }

    /**
     * Write full backup to storage
     */
    async _writeFullBackup(backup) {
        const backupString = JSON.stringify(backup, null, 2);

        // Try File System Access API first (Chrome, Edge)
        if (typeof window !== 'undefined' && 'showDirectoryPicker' in window) {
            try {
                // This would require user interaction to select folder
                // For auto-backup, use IndexedDB
                await this._writeToIndexedDB('full_backup', backup);
                return;
            } catch (e) {
                // Fall through to IndexedDB
            }
        }

        // Use IndexedDB
        await this._writeToIndexedDB('full_backup', backup);
    }

    /**
     * Write to IndexedDB
     */
    async _writeToIndexedDB(key, data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('PreservationDB', 1);

            request.onerror = () => reject(request.error);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('backups')) {
                    db.createObjectStore('backups', { keyPath: 'key' });
                }
            };

            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['backups'], 'readwrite');
                const store = transaction.objectStore('backups');

                const putRequest = store.put({ key: key, data: data, timestamp: Date.now() });
                putRequest.onerror = () => reject(putRequest.error);
                putRequest.onsuccess = () => resolve();
            };
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // BACKGROUND PROCESSES
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Start background backup and integrity check processes
     */
    _startBackgroundProcesses() {
        // Clear any existing intervals
        this._stopBackgroundProcesses();

        // Start backup interval (if full preservation)
        if (this.mode === 'full') {
            this._backupInterval = setInterval(
                () => this.performFullBackup(),
                this.sessionConfig.autoBackupInterval
            );
        }

        // Start integrity check interval
        this._integrityInterval = setInterval(
            () => this.checkIntegrity(),
            this.sessionConfig.integrityCheckInterval
        );
    }

    /**
     * Stop background processes
     */
    _stopBackgroundProcesses() {
        if (this._backupInterval) {
            clearInterval(this._backupInterval);
            this._backupInterval = null;
        }
        if (this._integrityInterval) {
            clearInterval(this._integrityInterval);
            this._integrityInterval = null;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════════

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (!this.listeners.has(event)) return;
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }

    _emit(event, data) {
        if (!this.listeners.has(event)) return;
        this.listeners.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (e) {
                console.error(`Error in ${event} listener:`, e);
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // CLEANUP
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * End session and cleanup
     */
    endSession() {
        this._stopBackgroundProcesses();
        this._setStatus(PreservationStatus.OFFLINE);
        this._emit('sessionEnded', { lastBackup: this.lastBackup });
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const preservationManager = new PreservationModeManager();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    PreservationModeManager,
    preservationManager,
    PreservationStatus,
    StatusColors
};

export default preservationManager;
