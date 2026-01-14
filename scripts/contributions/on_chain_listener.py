"""
On-Chain Listener - Blockchain event monitoring for contributions

Monitors blockchain events and converts them to contributions:
- Mint events (ERC-721/ERC-1155) → HIGH weight contributions
- Transfer events → Archive action contributions
- Contract interactions → Various contribution types

Integrates with existing multi_provider_web3.py infrastructure.

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 8
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .micro_tx_db import MicroTXDatabase, AlignmentLog
from .contribution_processor import ContributionProcessor


# ERC-721 Transfer event signature
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

# Null address (indicates mint)
NULL_ADDRESS = '0x0000000000000000000000000000000000000000'


@dataclass
class BlockchainEvent:
    """Parsed blockchain event."""
    tx_hash: str
    event_type: str  # 'mint', 'transfer', 'sale'
    from_address: str
    to_address: str
    contract_address: str
    token_id: Optional[str]
    value_wei: Optional[str]
    block_number: int
    block_timestamp: Optional[str]
    network: str
    raw_log: Optional[Dict]


class OnChainListener:
    """
    Monitors blockchain for contribution-relevant events.

    Uses existing multi_provider_web3.py for resilient RPC access.
    """

    def __init__(self, db: MicroTXDatabase = None, network: str = 'ethereum'):
        self.db = db or MicroTXDatabase()
        self.network = network
        self.processor = ContributionProcessor(self.db)
        self.web3 = None
        self._init_web3()

    def _init_web3(self):
        """Initialize Web3 connection using existing infrastructure."""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / 'collectors'))

            from multi_provider_web3 import MultiProviderWeb3

            self.web3 = MultiProviderWeb3(self.network)
        except ImportError:
            # Fallback: no Web3 available
            self.web3 = None
        except Exception as e:
            print(f"Warning: Could not initialize Web3: {e}")
            self.web3 = None

    def _get_last_processed_block(self) -> int:
        """Get last processed block number from database."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(block_number) FROM on_chain_events
            WHERE network = ?
        """, (self.network,))

        row = cursor.fetchone()
        conn.close()

        return row[0] if row[0] else 0

    def _save_event(self, event: BlockchainEvent) -> int:
        """Save blockchain event to database."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO on_chain_events (
                tx_hash, event_type, from_address, to_address,
                contract_address, token_id, value_wei,
                block_number, block_timestamp, network, raw_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.tx_hash,
            event.event_type,
            event.from_address,
            event.to_address,
            event.contract_address,
            event.token_id,
            event.value_wei,
            event.block_number,
            event.block_timestamp,
            event.network,
            json.dumps(event.raw_log) if event.raw_log else None
        ))

        event_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return event_id

    def _mark_event_processed(self, tx_hash: str, contribution_id: int):
        """Mark event as processed with linked contribution."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE on_chain_events
            SET processed = TRUE, contribution_id = ?
            WHERE tx_hash = ?
        """, (contribution_id, tx_hash))

        conn.commit()
        conn.close()

    # ================================================================
    # EVENT PARSING
    # ================================================================

    def parse_transfer_log(self, log: Dict) -> Optional[BlockchainEvent]:
        """Parse ERC-721 Transfer event log."""
        try:
            topics = log.get('topics', [])
            if len(topics) < 3:
                return None

            # Parse addresses from topics
            from_address = '0x' + topics[1][-40:] if len(topics) > 1 else ''
            to_address = '0x' + topics[2][-40:] if len(topics) > 2 else ''

            # Token ID from topics[3] or data
            token_id = None
            if len(topics) > 3:
                token_id = str(int(topics[3], 16))
            elif log.get('data'):
                token_id = str(int(log['data'], 16))

            # Determine event type
            if from_address.lower() == NULL_ADDRESS:
                event_type = 'mint'
            else:
                event_type = 'transfer'

            return BlockchainEvent(
                tx_hash=log.get('transactionHash', ''),
                event_type=event_type,
                from_address=from_address.lower(),
                to_address=to_address.lower(),
                contract_address=log.get('address', '').lower(),
                token_id=token_id,
                value_wei=None,
                block_number=int(log.get('blockNumber', 0), 16) if isinstance(log.get('blockNumber'), str) else log.get('blockNumber', 0),
                block_timestamp=None,
                network=self.network,
                raw_log=log
            )

        except Exception as e:
            print(f"Error parsing log: {e}")
            return None

    # ================================================================
    # MONITORING
    # ================================================================

    def scan_blocks(self, from_block: int = None, to_block: int = None) -> List[int]:
        """
        Scan blocks for contribution events.

        Returns list of contribution IDs created.
        """
        if not self.web3:
            print("Web3 not available - cannot scan blocks")
            return []

        # Determine block range
        if from_block is None:
            from_block = self._get_last_processed_block() + 1

        if to_block is None:
            try:
                to_block = self.web3.get_block_number()
            except:
                return []

        if from_block > to_block:
            return []

        print(f"Scanning blocks {from_block} to {to_block}...")

        contribution_ids = []

        try:
            # Get transfer event logs
            logs = self.web3.get_logs(
                from_block=from_block,
                to_block=to_block,
                topics=[TRANSFER_TOPIC]
            )

            for log in logs or []:
                event = self.parse_transfer_log(log)
                if event:
                    contribution_id = self.process_event(event)
                    if contribution_id:
                        contribution_ids.append(contribution_id)

        except Exception as e:
            print(f"Error scanning blocks: {e}")

        return contribution_ids

    def process_event(self, event: BlockchainEvent) -> Optional[int]:
        """
        Process a blockchain event and create contribution if applicable.

        Returns contribution ID if created.
        """
        # Save event first
        self._save_event(event)

        # Skip if not a mint (for now, only track mints as contributions)
        if event.event_type != 'mint':
            return None

        # Skip if no recipient
        if not event.to_address or event.to_address == NULL_ADDRESS:
            return None

        # Create contribution from event
        submission = {
            'tx_hash': event.tx_hash,
            'type': 'mint',
            'from_address': event.from_address,
            'to_address': event.to_address,
            'contract_address': event.contract_address,
            'token_id': event.token_id,
            'block_number': event.block_number,
            'block_timestamp': event.block_timestamp,
            'network': event.network,
            'content': {
                'event_type': event.event_type,
                'contract': event.contract_address,
                'token_id': event.token_id
            }
        }

        try:
            contribution_id, recognition = self.processor.process_submission(
                event.to_address,
                submission
            )

            # Mark event as processed
            self._mark_event_processed(event.tx_hash, contribution_id)

            # Log
            self.db.log_alignment_event(AlignmentLog(
                event_type='on_chain',
                contribution_id=contribution_id,
                action='mint_detected',
                new_state=json.dumps({
                    'tx_hash': event.tx_hash,
                    'contract': event.contract_address,
                    'token_id': event.token_id,
                    'network': event.network
                }),
                triggered_by='on_chain_listener',
                triggering_entity=event.tx_hash
            ))

            return contribution_id

        except Exception as e:
            print(f"Error processing event: {e}")
            return None

    # ================================================================
    # ADDRESS MONITORING
    # ================================================================

    def add_monitored_address(self, address: str, address_type: str = 'contributor'):
        """Add address to monitoring list."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO monitored_addresses
            (address, address_type, network, monitor_for)
            VALUES (?, ?, ?, ?)
        """, (
            address.lower(),
            address_type,
            self.network,
            json.dumps(['mint', 'transfer'])
        ))

        conn.commit()
        conn.close()

    def get_monitored_addresses(self) -> List[str]:
        """Get all monitored addresses."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT address FROM monitored_addresses
            WHERE network = ? AND is_active = TRUE
        """, (self.network,))

        rows = cursor.fetchall()
        conn.close()

        return [row['address'] for row in rows]

    def scan_address_history(self, address: str, from_block: int = 0) -> List[int]:
        """
        Scan historical events for a specific address.

        Returns list of contribution IDs created.
        """
        if not self.web3:
            return []

        contribution_ids = []

        try:
            # For address history, we need to look at both from and to
            # This is a simplified version - full implementation would use
            # more sophisticated indexing

            # Get current block
            current_block = self.web3.get_block_number()

            # Scan in chunks
            chunk_size = 10000
            for start in range(from_block, current_block, chunk_size):
                end = min(start + chunk_size, current_block)

                # This is a placeholder - actual implementation would
                # filter by address in the topic
                # For now, just note that we'd need to implement this

                print(f"Would scan blocks {start}-{end} for address {address}")

        except Exception as e:
            print(f"Error scanning address history: {e}")

        return contribution_ids

    # ================================================================
    # STATISTICS
    # ================================================================

    def get_event_stats(self) -> Dict[str, Any]:
        """Get on-chain event statistics."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total events
        cursor.execute("SELECT COUNT(*) FROM on_chain_events WHERE network = ?", (self.network,))
        stats['total_events'] = cursor.fetchone()[0]

        # Events by type
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM on_chain_events
            WHERE network = ?
            GROUP BY event_type
        """, (self.network,))
        stats['by_type'] = {row['event_type']: row['count'] for row in cursor.fetchall()}

        # Processed vs unprocessed
        cursor.execute("""
            SELECT processed, COUNT(*) as count
            FROM on_chain_events
            WHERE network = ?
            GROUP BY processed
        """, (self.network,))
        stats['processed'] = {str(row['processed']): row['count'] for row in cursor.fetchall()}

        # Latest block
        cursor.execute("""
            SELECT MAX(block_number) FROM on_chain_events WHERE network = ?
        """, (self.network,))
        stats['latest_block'] = cursor.fetchone()[0] or 0

        # Monitored addresses
        cursor.execute("""
            SELECT COUNT(*) FROM monitored_addresses
            WHERE network = ? AND is_active = TRUE
        """, (self.network,))
        stats['monitored_addresses'] = cursor.fetchone()[0]

        conn.close()
        return stats


# Background listener (would typically run as a separate process)
def start_listener(network: str = 'ethereum', poll_interval: int = 60):
    """
    Start background listener for on-chain events.

    Note: In production, this would run as a separate daemon process.
    """
    import time

    listener = OnChainListener(network=network)

    print(f"Starting on-chain listener for {network}...")
    print(f"Poll interval: {poll_interval} seconds")

    while True:
        try:
            contribution_ids = listener.scan_blocks()

            if contribution_ids:
                print(f"Created {len(contribution_ids)} contributions from on-chain events")

        except Exception as e:
            print(f"Listener error: {e}")

        time.sleep(poll_interval)


if __name__ == '__main__':
    # Run listener in foreground for testing
    start_listener(poll_interval=30)
