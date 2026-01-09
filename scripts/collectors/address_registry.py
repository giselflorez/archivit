#!/usr/bin/env python3
"""
Address Registry Manager
Handles validation, CRUD operations, and management of tracked blockchain addresses
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.blockchain_db import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AddressRegistry:
    """Manage tracked blockchain addresses"""

    def __init__(self):
        self.db = get_db()

    def validate_address(self, address: str) -> Optional[str]:
        """
        Validate and detect network from address format

        Returns:
            Network name ('ethereum', 'solana', 'bitcoin') or None if invalid
        """
        # Ethereum: 0x followed by 40 hex chars
        if re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return 'ethereum'

        # Bitcoin P2PKH: starts with 1, 25-34 chars
        if re.match(r'^1[a-km-zA-HJ-NP-Z1-9]{25,34}$', address):
            return 'bitcoin'

        # Bitcoin P2SH: starts with 3, 25-34 chars
        if re.match(r'^3[a-km-zA-HJ-NP-Z1-9]{25,34}$', address):
            return 'bitcoin'

        # Bitcoin Bech32: starts with bc1
        if re.match(r'^bc1[a-z0-9]{39,59}$', address):
            return 'bitcoin'

        # Solana: Base58, 32-44 chars (simplified check)
        if re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
            return 'solana'

        return None

    def add_address(
        self,
        address: str,
        network: str = None,
        label: str = None,
        address_type: str = 'wallet',
        notes: str = None
    ) -> Dict:
        """
        Add a new address to track

        Args:
            address: Blockchain address to track
            network: Network name (ethereum, solana, bitcoin) - if not provided, auto-detect
            label: User-friendly name
            address_type: 'wallet', 'contract', or 'ordinal'
            notes: Additional notes

        Returns:
            Dict with address info and status
        """
        # Clean address (remove whitespace)
        address = address.strip()

        # If network not provided, auto-detect
        if not network:
            network = self.validate_address(address)

            if not network:
                return {
                    'success': False,
                    'error': f"Invalid or unrecognized address format: {address}"
                }
        else:
            # Network provided - validate it matches the format
            detected_network = self.validate_address(address)
            if detected_network and detected_network != network:
                return {
                    'success': False,
                    'error': f"Address format doesn't match selected network. Detected: {detected_network}, Selected: {network}"
                }

        # Normalize address: lowercase for Ethereum (case-insensitive), preserve case for Tezos (case-sensitive)
        normalized_address = address.lower() if network == 'ethereum' else address
        try:
            result = self.db.execute('''
                INSERT INTO tracked_addresses
                (address, network, label, address_type, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (normalized_address, network, label, address_type, notes))

            logger.info(f"Added {network} address to tracking: {address}")

            return {
                'success': True,
                'id': result[0]['last_id'],
                'address': address,
                'network': network,
                'label': label,
                'address_type': address_type
            }

        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                logger.warning(f"Address already tracked: {address}")
                return {
                    'success': False,
                    'error': 'Address already tracked',
                    'address': address
                }
            else:
                logger.error(f"Error adding address: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }

    def get_all_addresses(self, network: str = None, enabled_only: bool = True) -> List[Dict]:
        """
        Get all tracked addresses, optionally filtered

        Args:
            network: Filter by network ('ethereum', 'solana', 'bitcoin')
            enabled_only: Only return addresses with sync_enabled=True

        Returns:
            List of address records
        """
        query = 'SELECT * FROM tracked_addresses WHERE 1=1'
        params = []

        if network:
            query += ' AND network = ?'
            params.append(network)

        if enabled_only:
            query += ' AND sync_enabled = TRUE'

        query += ' ORDER BY created_at DESC'

        addresses = self.db.execute(query, tuple(params))
        return addresses if addresses else []

    def get_address_by_id(self, address_id: int) -> Optional[Dict]:
        """Get a tracked address by ID"""
        result = self.db.execute(
            'SELECT * FROM tracked_addresses WHERE id = ?',
            (address_id,)
        )
        return result[0] if result else None

    def get_address_by_value(self, address: str) -> Optional[Dict]:
        """Get a tracked address by address string (case-insensitive)"""
        result = self.db.execute(
            'SELECT * FROM tracked_addresses WHERE LOWER(address) = LOWER(?)',
            (address,)
        )
        return result[0] if result else None

    def update_address(
        self,
        address_id: int,
        label: str = None,
        notes: str = None,
        sync_enabled: bool = None
    ) -> Dict:
        """
        Update a tracked address

        Args:
            address_id: ID of address to update
            label: New label (optional)
            notes: New notes (optional)
            sync_enabled: Enable/disable syncing (optional)

        Returns:
            Dict with success status
        """
        # Build dynamic update query
        updates = []
        params = []

        if label is not None:
            updates.append('label = ?')
            params.append(label)

        if notes is not None:
            updates.append('notes = ?')
            params.append(notes)

        if sync_enabled is not None:
            updates.append('sync_enabled = ?')
            params.append(sync_enabled)

        if not updates:
            return {
                'success': False,
                'error': 'No fields to update'
            }

        query = f"UPDATE tracked_addresses SET {', '.join(updates)} WHERE id = ?"
        params.append(address_id)

        try:
            result = self.db.execute(query, tuple(params))

            if result[0]['affected_rows'] > 0:
                logger.info(f"Updated address ID {address_id}")
                return {
                    'success': True,
                    'id': address_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Address not found'
                }

        except Exception as e:
            logger.error(f"Error updating address: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_address(self, address_id: int) -> Dict:
        """
        Delete a tracked address (cascades to related data)

        Args:
            address_id: ID of address to delete

        Returns:
            Dict with success status
        """
        try:
            result = self.db.execute(
                'DELETE FROM tracked_addresses WHERE id = ?',
                (address_id,)
            )

            if result[0]['affected_rows'] > 0:
                logger.info(f"Deleted address ID {address_id}")
                return {
                    'success': True,
                    'id': address_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Address not found'
                }

        except Exception as e:
            logger.error(f"Error deleting address: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_last_synced(self, address_id: int):
        """Update the last_synced timestamp for an address"""
        self.db.execute(
            'UPDATE tracked_addresses SET last_synced = ? WHERE id = ?',
            (datetime.utcnow().isoformat(), address_id)
        )

    def get_addresses_for_sync(self, network: str = None) -> List[Dict]:
        """
        Get addresses that need syncing (enabled and not recently synced)

        Args:
            network: Optional network filter

        Returns:
            List of addresses ready for sync
        """
        query = '''
            SELECT * FROM tracked_addresses
            WHERE sync_enabled = TRUE
        '''
        params = []

        if network:
            query += ' AND network = ?'
            params.append(network)

        # Could add logic here to filter by last_synced timestamp
        # For now, return all enabled addresses

        query += ' ORDER BY last_synced ASC NULLS FIRST'

        addresses = self.db.execute(query, tuple(params) if params else ())
        return addresses if addresses else []


# Test and CLI interface
if __name__ == '__main__':
    import sys

    registry = AddressRegistry()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python address_registry.py add <address> [label] [notes]")
        print("  python address_registry.py list [network]")
        print("  python address_registry.py delete <id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'add':
        if len(sys.argv) < 3:
            print("Error: Address required")
            sys.exit(1)

        address = sys.argv[2]
        label = sys.argv[3] if len(sys.argv) > 3 else None
        notes = sys.argv[4] if len(sys.argv) > 4 else None

        result = registry.add_address(address, label=label, notes=notes)
        print(result)

    elif command == 'list':
        network = sys.argv[2] if len(sys.argv) > 2 else None
        addresses = registry.get_all_addresses(network=network)

        print(f"\nTracked Addresses ({len(addresses)}):\n")
        for addr in addresses:
            print(f"ID: {addr['id']}")
            print(f"  Address: {addr['address']}")
            print(f"  Network: {addr['network']}")
            print(f"  Label: {addr['label'] or 'N/A'}")
            print(f"  Sync Enabled: {bool(addr['sync_enabled'])}")
            print(f"  Last Synced: {addr['last_synced'] or 'Never'}")
            print()

    elif command == 'delete':
        if len(sys.argv) < 3:
            print("Error: Address ID required")
            sys.exit(1)

        address_id = int(sys.argv[2])
        result = registry.delete_address(address_id)
        print(result)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
