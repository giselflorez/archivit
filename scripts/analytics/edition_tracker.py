#!/usr/bin/env python3
"""
Edition Tracker
Tracks ERC-1155 editions and collector distribution for the Edition Constellation visualization

Provides:
- Edition work detection (ERC-1155 vs ERC-721)
- Collector distribution mapping
- Transfer path tracking
- Hold duration metrics
- Value trajectory analysis
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.blockchain_event_parser import BlockchainEventParser
from collectors.multi_provider_web3 import MultiProviderWeb3
from analytics.sales_db import get_sales_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EditionTracker:
    """
    Track ERC-1155 editions and generate constellation data

    Features:
    - Detect edition works (multiple tokens same ID)
    - Map collector distribution
    - Track transfer paths between collectors
    - Calculate collector metrics (hold duration, volume, activity)
    - Generate constellation visualization data
    """

    # ERC-1155 interface ID
    ERC1155_INTERFACE_ID = '0xd9b67a26'

    # ERC-1155 TransferSingle event signature
    TRANSFER_SINGLE_TOPIC = '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'

    # ERC-1155 TransferBatch event signature
    TRANSFER_BATCH_TOPIC = '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'

    def __init__(self, network: str = 'ethereum'):
        self.network = network
        self.parser = BlockchainEventParser(network)
        self.web3 = MultiProviderWeb3(network)
        self.sales_db = get_sales_db()
        self._init_edition_db()

    def _init_edition_db(self):
        """Initialize edition tracking database"""
        db_path = Path(__file__).parent.parent.parent / 'db' / 'edition_tracking.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db_conn.row_factory = sqlite3.Row

        cursor = self.db_conn.cursor()

        # Edition works table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edition_works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT NOT NULL,
                token_id INTEGER NOT NULL,
                title TEXT,
                token_standard TEXT DEFAULT 'ERC-1155',
                total_supply INTEGER DEFAULT 0,
                unique_holders INTEGER DEFAULT 0,
                metadata_uri TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contract_address, token_id)
            )
        ''')

        # Edition holders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edition_holders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT NOT NULL,
                token_id INTEGER NOT NULL,
                holder_address TEXT NOT NULL,
                editions_held INTEGER DEFAULT 1,
                first_acquired TIMESTAMP,
                last_acquired TIMESTAMP,
                total_spent_eth REAL DEFAULT 0,
                is_current_holder INTEGER DEFAULT 1,
                UNIQUE(contract_address, token_id, holder_address)
            )
        ''')

        # Edition transfers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edition_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT NOT NULL,
                token_id INTEGER NOT NULL,
                from_address TEXT NOT NULL,
                to_address TEXT NOT NULL,
                amount INTEGER DEFAULT 1,
                value_eth REAL DEFAULT 0,
                tx_hash TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                timestamp INTEGER,
                transfer_type TEXT DEFAULT 'transfer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Collector metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collector_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE,
                total_editions_held INTEGER DEFAULT 0,
                total_editions_sold INTEGER DEFAULT 0,
                total_spent_eth REAL DEFAULT 0,
                total_earned_eth REAL DEFAULT 0,
                avg_hold_days REAL DEFAULT 0,
                first_activity TIMESTAMP,
                last_activity TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.db_conn.commit()
        logger.info("Edition tracking database initialized")

    def detect_token_standard(self, contract_address: str) -> str:
        """
        Detect if contract is ERC-721 or ERC-1155

        Returns: 'ERC-721', 'ERC-1155', or 'unknown'
        """
        try:
            # Check for ERC-1155 interface support
            supports_1155 = self._check_interface_support(contract_address, self.ERC1155_INTERFACE_ID)
            if supports_1155:
                return 'ERC-1155'

            # Default to ERC-721 for NFT contracts
            return 'ERC-721'
        except Exception as e:
            logger.warning(f"Could not detect token standard: {e}")
            return 'unknown'

    def _check_interface_support(self, contract_address: str, interface_id: str) -> bool:
        """Check if contract supports a specific interface via ERC-165"""
        try:
            # supportsInterface(bytes4) selector
            data = f'0x01ffc9a7{interface_id[2:].zfill(64)}'

            result = self.web3.rpc_call('eth_call', [{
                'to': contract_address,
                'data': data
            }, 'latest'])

            # Result should be true (1) if supported
            return result and int(result, 16) == 1
        except:
            return False

    def get_edition_works(self, contract_address: str = None) -> List[Dict]:
        """
        Get all tracked edition works

        Args:
            contract_address: Optional filter by contract

        Returns:
            List of edition work data
        """
        cursor = self.db_conn.cursor()

        if contract_address:
            cursor.execute('''
                SELECT * FROM edition_works
                WHERE contract_address = ?
                ORDER BY updated_at DESC
            ''', (contract_address.lower(),))
        else:
            cursor.execute('''
                SELECT * FROM edition_works
                ORDER BY updated_at DESC
            ''')

        return [dict(row) for row in cursor.fetchall()]

    def track_edition_work(
        self,
        contract_address: str,
        token_id: int,
        title: str = None,
        from_block: int = 0
    ) -> Dict:
        """
        Track an edition work and all its collectors

        Args:
            contract_address: Contract address
            token_id: Token ID
            title: Optional artwork title
            from_block: Starting block for history

        Returns:
            Edition tracking data
        """
        contract_address = contract_address.lower()
        logger.info(f"Tracking edition {contract_address} #{token_id}")

        # Detect token standard
        token_standard = self.detect_token_standard(contract_address)

        # Get all transfers for this token
        transfers = self._get_edition_transfers(contract_address, token_id, from_block)

        if not transfers:
            logger.warning("No transfers found")
            return {'success': False, 'error': 'No transfers found'}

        # Process transfers to build holder data
        holders = self._process_edition_transfers(transfers)

        # Calculate totals
        total_supply = sum(h['editions_held'] for h in holders.values() if h['is_current_holder'])
        unique_holders = len([h for h in holders.values() if h['is_current_holder']])

        # Store edition work
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO edition_works
            (contract_address, token_id, title, token_standard, total_supply, unique_holders, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (contract_address, token_id, title, token_standard, total_supply, unique_holders))

        # Store holders
        for address, holder_data in holders.items():
            cursor.execute('''
                INSERT OR REPLACE INTO edition_holders
                (contract_address, token_id, holder_address, editions_held,
                 first_acquired, last_acquired, total_spent_eth, is_current_holder)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contract_address, token_id, address,
                holder_data['editions_held'],
                holder_data.get('first_acquired'),
                holder_data.get('last_acquired'),
                holder_data.get('total_spent_eth', 0),
                1 if holder_data['is_current_holder'] else 0
            ))

        # Store transfers
        for transfer in transfers:
            cursor.execute('''
                INSERT OR IGNORE INTO edition_transfers
                (contract_address, token_id, from_address, to_address, amount,
                 value_eth, tx_hash, block_number, timestamp, transfer_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contract_address, token_id,
                transfer['from_address'],
                transfer['to_address'],
                transfer.get('amount', 1),
                transfer.get('value_eth', 0),
                transfer['tx_hash'],
                transfer['block_number'],
                transfer.get('timestamp'),
                transfer.get('transfer_type', 'transfer')
            ))

        self.db_conn.commit()

        return {
            'success': True,
            'contract_address': contract_address,
            'token_id': token_id,
            'token_standard': token_standard,
            'total_supply': total_supply,
            'unique_holders': unique_holders,
            'total_transfers': len(transfers)
        }

    def _get_edition_transfers(
        self,
        contract_address: str,
        token_id: int,
        from_block: int = 0
    ) -> List[Dict]:
        """Get all transfers for an edition token"""
        transfers = []

        # Try ERC-1155 TransferSingle events first
        try:
            # Token ID as hex, padded to 32 bytes
            token_id_hex = hex(token_id)[2:].zfill(64)

            logs_1155 = self.web3.rpc_call('eth_getLogs', [{
                'address': contract_address,
                'fromBlock': hex(from_block),
                'toBlock': 'latest',
                'topics': [
                    self.TRANSFER_SINGLE_TOPIC,
                    None,  # operator
                    None,  # from
                    None   # to
                ]
            }])

            for log in logs_1155 or []:
                # Parse TransferSingle event
                # topics: [event sig, operator, from, to]
                # data: [id, value]
                if len(log.get('topics', [])) >= 4:
                    from_addr = '0x' + log['topics'][2][-40:]
                    to_addr = '0x' + log['topics'][3][-40:]

                    # Parse data for token ID and amount
                    data = log.get('data', '0x')
                    if len(data) >= 130:  # 0x + 64 + 64
                        log_token_id = int(data[2:66], 16)
                        amount = int(data[66:130], 16)

                        if log_token_id == token_id:
                            transfers.append({
                                'from_address': from_addr.lower(),
                                'to_address': to_addr.lower(),
                                'amount': amount,
                                'tx_hash': log['transactionHash'],
                                'block_number': int(log['blockNumber'], 16),
                                'log_index': int(log.get('logIndex', '0x0'), 16)
                            })
        except Exception as e:
            logger.warning(f"Error getting ERC-1155 transfers: {e}")

        # Fall back to ERC-721 Transfer events
        if not transfers:
            transfers = self.parser.get_nft_transfers_for_token(
                contract_address,
                token_id,
                from_block
            )

        # Enrich with timestamps and values
        for transfer in transfers:
            try:
                # Get block timestamp
                block = self.web3.get_block(transfer['block_number'])
                if block:
                    transfer['timestamp'] = block.get('timestamp')

                # Get transaction value
                tx = self.web3.rpc_call('eth_getTransactionByHash', [transfer['tx_hash']])
                if tx:
                    value_wei = int(tx.get('value', '0x0'), 16)
                    transfer['value_eth'] = value_wei / 1e18

                # Classify transfer type
                if transfer['from_address'] == '0x0000000000000000000000000000000000000000':
                    transfer['transfer_type'] = 'mint'
                elif transfer.get('value_eth', 0) > 0:
                    transfer['transfer_type'] = 'sale'
                else:
                    transfer['transfer_type'] = 'transfer'

            except Exception as e:
                logger.warning(f"Error enriching transfer: {e}")

        # Sort by block number
        transfers.sort(key=lambda x: (x['block_number'], x.get('log_index', 0)))

        return transfers

    def _process_edition_transfers(self, transfers: List[Dict]) -> Dict[str, Dict]:
        """
        Process transfers to build holder state

        Returns dict of address -> holder data
        """
        holders = defaultdict(lambda: {
            'editions_held': 0,
            'total_acquired': 0,
            'total_sold': 0,
            'total_spent_eth': 0,
            'total_earned_eth': 0,
            'first_acquired': None,
            'last_acquired': None,
            'is_current_holder': False
        })

        null_address = '0x0000000000000000000000000000000000000000'

        for transfer in transfers:
            from_addr = transfer['from_address']
            to_addr = transfer['to_address']
            amount = transfer.get('amount', 1)
            value_eth = transfer.get('value_eth', 0)
            timestamp = transfer.get('timestamp')

            # Update sender (unless mint)
            if from_addr != null_address:
                holders[from_addr]['editions_held'] -= amount
                holders[from_addr]['total_sold'] += amount
                holders[from_addr]['total_earned_eth'] += value_eth

            # Update receiver (unless burn)
            if to_addr != null_address:
                holders[to_addr]['editions_held'] += amount
                holders[to_addr]['total_acquired'] += amount
                holders[to_addr]['total_spent_eth'] += value_eth

                if timestamp:
                    if not holders[to_addr]['first_acquired']:
                        holders[to_addr]['first_acquired'] = timestamp
                    holders[to_addr]['last_acquired'] = timestamp

        # Mark current holders
        for address, data in holders.items():
            data['is_current_holder'] = data['editions_held'] > 0

        return dict(holders)

    def get_constellation_data(
        self,
        contract_address: str,
        token_id: int
    ) -> Dict:
        """
        Get data formatted for edition constellation visualization

        Returns:
            {
                title: str,
                total_supply: int,
                unique_holders: int,
                avg_hold_days: float,
                total_volume_eth: float,
                collectors: [...],
                transfers: [...],
                recent_activity: [...]
            }
        """
        contract_address = contract_address.lower()
        cursor = self.db_conn.cursor()

        # Get edition work info
        cursor.execute('''
            SELECT * FROM edition_works
            WHERE contract_address = ? AND token_id = ?
        ''', (contract_address, token_id))

        edition = cursor.fetchone()
        if not edition:
            # Try to track it first
            result = self.track_edition_work(contract_address, token_id)
            if not result.get('success'):
                return {'error': 'Edition not found'}

            cursor.execute('''
                SELECT * FROM edition_works
                WHERE contract_address = ? AND token_id = ?
            ''', (contract_address, token_id))
            edition = cursor.fetchone()

        # Get holders
        cursor.execute('''
            SELECT * FROM edition_holders
            WHERE contract_address = ? AND token_id = ?
            ORDER BY editions_held DESC
        ''', (contract_address, token_id))

        holders = cursor.fetchall()

        # Get transfers
        cursor.execute('''
            SELECT * FROM edition_transfers
            WHERE contract_address = ? AND token_id = ?
            ORDER BY block_number DESC
            LIMIT 100
        ''', (contract_address, token_id))

        transfers = cursor.fetchall()

        # Calculate metrics
        current_holders = [h for h in holders if h['is_current_holder']]
        total_volume = sum(t['value_eth'] or 0 for t in transfers if t['transfer_type'] == 'sale')

        # Calculate average hold days
        avg_hold_days = 0
        if current_holders:
            now = datetime.now().timestamp()
            hold_days = []
            for holder in current_holders:
                if holder['first_acquired']:
                    days = (now - holder['first_acquired']) / 86400
                    hold_days.append(days)
            if hold_days:
                avg_hold_days = sum(hold_days) / len(hold_days)

        # Build collector data for visualization
        collectors = []
        for holder in holders:
            # Calculate value change (simplified)
            value_change = 0
            if holder['total_spent_eth'] > 0:
                value_change = ((holder['total_earned_eth'] - holder['total_spent_eth'])
                               / holder['total_spent_eth'] * 100)

            # Calculate individual hold days
            hold_days = 0
            if holder['first_acquired']:
                hold_days = (datetime.now().timestamp() - holder['first_acquired']) / 86400

            collectors.append({
                'address': holder['holder_address'],
                'editions_held': holder['editions_held'],
                'is_current_holder': bool(holder['is_current_holder']),
                'hold_days': round(hold_days, 1),
                'volume_eth': holder['total_spent_eth'] or 0,
                'value_change': round(value_change, 1)
            })

        # Build transfer paths for visualization
        transfer_paths = []
        seen_paths = set()
        for transfer in transfers:
            if transfer['from_address'] != '0x0000000000000000000000000000000000000000':
                path_key = f"{transfer['from_address']}-{transfer['to_address']}"
                if path_key not in seen_paths:
                    seen_paths.add(path_key)
                    transfer_paths.append({
                        'from': transfer['from_address'],
                        'to': transfer['to_address']
                    })

        # Recent activity
        recent_activity = []
        for transfer in transfers[:20]:
            recent_activity.append({
                'timestamp': transfer['timestamp'],
                'type': transfer['transfer_type'].title(),
                'from': transfer['from_address'],
                'to': transfer['to_address'],
                'value_eth': transfer['value_eth']
            })

        return {
            'title': edition['title'] or f'Edition #{token_id}',
            'contract_address': contract_address,
            'token_id': token_id,
            'token_standard': edition['token_standard'],
            'total_supply': edition['total_supply'],
            'unique_holders': len(current_holders),
            'avg_hold_days': round(avg_hold_days, 1),
            'total_volume_eth': round(total_volume, 4),
            'collectors': collectors,
            'transfers': transfer_paths,
            'recent_activity': recent_activity
        }

    def get_collector_network(self, address: str) -> Dict:
        """
        Get collector's edition network - other collectors they share editions with

        Returns network of related collectors across editions
        """
        address = address.lower()
        cursor = self.db_conn.cursor()

        # Get all editions this collector holds
        cursor.execute('''
            SELECT contract_address, token_id, editions_held
            FROM edition_holders
            WHERE holder_address = ? AND is_current_holder = 1
        ''', (address,))

        collector_editions = cursor.fetchall()

        if not collector_editions:
            return {'error': 'Collector not found', 'editions': []}

        # Find other holders of the same editions
        related_collectors = defaultdict(lambda: {'shared_editions': 0, 'editions': []})

        for edition in collector_editions:
            cursor.execute('''
                SELECT holder_address, editions_held
                FROM edition_holders
                WHERE contract_address = ? AND token_id = ?
                AND holder_address != ? AND is_current_holder = 1
            ''', (edition['contract_address'], edition['token_id'], address))

            for holder in cursor.fetchall():
                related_collectors[holder['holder_address']]['shared_editions'] += 1
                related_collectors[holder['holder_address']]['editions'].append({
                    'contract': edition['contract_address'],
                    'token_id': edition['token_id']
                })

        return {
            'address': address,
            'editions_held': len(collector_editions),
            'related_collectors': [
                {
                    'address': addr,
                    'shared_editions': data['shared_editions'],
                    'editions': data['editions']
                }
                for addr, data in sorted(
                    related_collectors.items(),
                    key=lambda x: x[1]['shared_editions'],
                    reverse=True
                )
            ]
        }


# CLI interface
if __name__ == '__main__':
    tracker = EditionTracker('ethereum')

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python edition_tracker.py track <contract> <token_id> [title]")
        print("  python edition_tracker.py constellation <contract> <token_id>")
        print("  python edition_tracker.py collector <address>")
        print("  python edition_tracker.py list [contract]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'track':
        contract = sys.argv[2]
        token_id = int(sys.argv[3])
        title = sys.argv[4] if len(sys.argv) > 4 else None

        result = tracker.track_edition_work(contract, token_id, title)
        print(json.dumps(result, indent=2))

    elif command == 'constellation':
        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        result = tracker.get_constellation_data(contract, token_id)
        print(json.dumps(result, indent=2))

    elif command == 'collector':
        address = sys.argv[2]

        result = tracker.get_collector_network(address)
        print(json.dumps(result, indent=2))

    elif command == 'list':
        contract = sys.argv[2] if len(sys.argv) > 2 else None

        editions = tracker.get_edition_works(contract)
        for edition in editions:
            print(f"{edition['contract_address']} #{edition['token_id']}: {edition['title'] or 'Untitled'}")
            print(f"  Supply: {edition['total_supply']}, Holders: {edition['unique_holders']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
