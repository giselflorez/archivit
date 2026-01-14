#!/usr/bin/env python3
"""
QUANTUM CHECKPOINT SYSTEM
φ-Weighted Auto-Save for Crash-Proof Session State

Philosophy: "The last second should never be lost"

Uses golden ratio mathematics for optimal checkpoint frequency.
Integrates with Claude Code sessions for automatic crash recovery.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import random
import string

class QuantumCheckpoint:
    """
    Lightweight crash-proof state persistence using φ-weighted checkpoints.

    Design Principles:
    1. MINIMAL OVERHEAD: Only save state vectors, not content
    2. FIBONACCI TIMING: Frequent early, sparse when stable
    3. ATOMIC WRITES: Temp file + rename for crash safety
    4. RECOVERY CONTEXT: Machine-readable recovery on startup
    """

    PHI = 1.618033988749895
    PHI_INVERSE = 0.6180339887498949

    # Fibonacci checkpoint intervals (seconds)
    CHECKPOINT_INTERVALS = [1, 1, 2, 3, 5, 8, 13, 21, 30]

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.checkpoint_dir = self.project_root / '.quantum_state'
        self.state_file = self.checkpoint_dir / 'session_state.json'
        self.history_file = self.checkpoint_dir / 'checkpoint_history.jsonl'

        self.current_interval_index = 0
        self.last_checkpoint = time.time()
        self.checkpoint_count = 0

        # Session state (lightweight)
        self.state = {
            'sessionId': self._generate_session_id(),
            'startedAt': datetime.now().isoformat(),
            'lastUpdate': None,

            # Core state vector (minimal)
            'currentFocus': None,           # 1 sentence: what are we doing?
            'filesModified': [],            # List of paths (not content)
            'filesCreated': [],             # List of new files
            'todoItems': [],                # Current todo list
            'lastAction': None,             # Last completed action
            'nextAction': None,             # Intended next action
            'progressPercent': 0,           # 0-100

            # Recovery hints
            'thoughtFragment': None,        # Last coherent thought (1-2 sentences)
            'contextFiles': [],             # Files being read
            'decisionPending': None,        # Any decision waiting for input

            # Crash metadata
            'checkpointNumber': 0,
            'crashRecoveries': 0,
            'endedCleanly': False
        }

        self._ensure_dir()
        self._load_previous_state()

    def _generate_session_id(self) -> str:
        timestamp = datetime.now().strftime('%Y-%m-%d')
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{timestamp}-{random_suffix}"

    def _ensure_dir(self):
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Add to .gitignore if not present
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            gitignore = gitignore_path.read_text()
            if '.quantum_state' not in gitignore:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# Quantum checkpoint state (session-only)\n.quantum_state/\n')

    def _load_previous_state(self):
        if self.state_file.exists():
            try:
                previous_state = json.loads(self.state_file.read_text())

                if not previous_state.get('endedCleanly', True):
                    self._print_recovery_banner(previous_state)
                    self.state['crashRecoveries'] = previous_state.get('crashRecoveries', 0) + 1

                    self._append_history({
                        'type': 'CRASH_RECOVERY',
                        'previousSession': previous_state.get('sessionId'),
                        'recoveredAt': datetime.now().isoformat(),
                        'lostState': {
                            'focus': previous_state.get('currentFocus'),
                            'thought': previous_state.get('thoughtFragment'),
                            'nextAction': previous_state.get('nextAction'),
                            'progress': previous_state.get('progressPercent')
                        }
                    })
            except json.JSONDecodeError:
                print('[Quantum] Could not parse previous state, starting fresh')

    def _print_recovery_banner(self, previous_state: dict):
        print()
        print('╔══════════════════════════════════════════════════════════════╗')
        print('║           🔄 CRASH RECOVERY DETECTED                         ║')
        print('╠══════════════════════════════════════════════════════════════╣')
        print(f'║ Previous Session: {previous_state.get("sessionId", "Unknown"):<40}║')
        print(f'║ Last Checkpoint:  {str(previous_state.get("lastUpdate", "Unknown"))[:40]:<40}║')
        print(f'║ Progress:         {str(previous_state.get("progressPercent", 0)) + "%":<40}║')
        print('╠══════════════════════════════════════════════════════════════╣')
        print('║ LAST FOCUS:                                                  ║')
        focus = (previous_state.get('currentFocus') or 'Unknown')[:60]
        print(f'║ {focus:<60}║')
        print('╠══════════════════════════════════════════════════════════════╣')
        print('║ THOUGHT FRAGMENT:                                            ║')
        thought = (previous_state.get('thoughtFragment') or 'None captured')[:60]
        print(f'║ {thought:<60}║')
        print('╠══════════════════════════════════════════════════════════════╣')
        print('║ NEXT ACTION WAS:                                             ║')
        next_action = (previous_state.get('nextAction') or 'Unknown')[:60]
        print(f'║ {next_action:<60}║')
        print('╚══════════════════════════════════════════════════════════════╝')
        print()

    def _get_next_interval(self) -> float:
        """Fibonacci-based checkpoint intervals"""
        interval = self.CHECKPOINT_INTERVALS[
            min(self.current_interval_index, len(self.CHECKPOINT_INTERVALS) - 1)
        ]

        # Advance interval index (slower saves over time)
        if self.checkpoint_count > 0 and self.checkpoint_count % 5 == 0:
            self.current_interval_index = min(
                self.current_interval_index + 1,
                len(self.CHECKPOINT_INTERVALS) - 1
            )

        return interval

    def update(self, **kwargs):
        """
        Update session state. Call frequently with minimal overhead.

        Example:
            checkpoint.update(
                currentFocus='Implementing ACU calculation',
                thoughtFragment='Deciding between recursive vs iterative',
                progressPercent=45
            )
        """
        self.state.update(kwargs)
        self.state['lastUpdate'] = datetime.now().isoformat()
        self.state['checkpointNumber'] = self.checkpoint_count

        # Check if checkpoint needed
        time_since_last = time.time() - self.last_checkpoint
        next_interval = self._get_next_interval()

        if time_since_last >= next_interval:
            self._save_checkpoint()

    def force_checkpoint(self, reason: str = 'manual'):
        """Force immediate checkpoint before risky operations"""
        self.state['lastCheckpointReason'] = reason
        self._save_checkpoint()

    def _save_checkpoint(self):
        """Atomic checkpoint save"""
        self.state['endedCleanly'] = False
        self.checkpoint_count += 1
        self.last_checkpoint = time.time()

        # Atomic write via temp file
        temp_file = self.state_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(self.state, indent=2))
        temp_file.rename(self.state_file)

        # Append to history
        self._append_history({
            'type': 'CHECKPOINT',
            'number': self.checkpoint_count,
            'timestamp': datetime.now().isoformat(),
            'focus': self.state.get('currentFocus'),
            'progress': self.state.get('progressPercent')
        })

    def _append_history(self, entry: dict):
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def end_session(self, summary: str = None):
        """Call on clean session end"""
        self.state['endedCleanly'] = True
        self.state['sessionSummary'] = summary
        self.state['endedAt'] = datetime.now().isoformat()

        self._save_checkpoint()

        self._append_history({
            'type': 'SESSION_END',
            'sessionId': self.state['sessionId'],
            'duration': time.time() - datetime.fromisoformat(self.state['startedAt']).timestamp(),
            'checkpoints': self.checkpoint_count,
            'crashes': self.state['crashRecoveries']
        })

        print(f'[Quantum] Session ended cleanly after {self.checkpoint_count} checkpoints')

    def get_recovery_context(self) -> dict:
        """Get recovery context for Claude startup"""
        if not self.state_file.exists():
            return None

        try:
            state = json.loads(self.state_file.read_text())
            if not state.get('endedCleanly', True):
                return {
                    'crashed': True,
                    'previousSession': state.get('sessionId'),
                    'lastFocus': state.get('currentFocus'),
                    'thoughtFragment': state.get('thoughtFragment'),
                    'nextAction': state.get('nextAction'),
                    'progress': state.get('progressPercent'),
                    'filesModified': state.get('filesModified', []),
                    'todoItems': state.get('todoItems', [])
                }
        except Exception:
            return None

        return {'crashed': False}


def main():
    """CLI interface for quantum checkpoint system"""
    import argparse

    parser = argparse.ArgumentParser(description='Quantum Checkpoint System')
    parser.add_argument('--project', '-p', default=os.getcwd(), help='Project root path')
    parser.add_argument('--check', '-c', action='store_true', help='Check for crash recovery')
    parser.add_argument('--update', '-u', nargs=2, metavar=('KEY', 'VALUE'), action='append',
                        help='Update state (can use multiple times)')
    parser.add_argument('--end', '-e', action='store_true', help='End session cleanly')
    parser.add_argument('--summary', '-s', help='Session summary (for --end)')

    args = parser.parse_args()

    checkpoint = QuantumCheckpoint(args.project)

    if args.check:
        recovery = checkpoint.get_recovery_context()
        if recovery and recovery.get('crashed'):
            print('\n=== CRASH RECOVERY AVAILABLE ===')
            print(json.dumps(recovery, indent=2))
            return 1  # Signal crash detected
        else:
            print('No crash recovery needed - starting fresh session')
            return 0

    if args.update:
        updates = {key: value for key, value in args.update}
        checkpoint.update(**updates)
        print(f'[Quantum] State updated: {list(updates.keys())}')

    if args.end:
        checkpoint.end_session(args.summary)

    return 0


if __name__ == '__main__':
    exit(main())
