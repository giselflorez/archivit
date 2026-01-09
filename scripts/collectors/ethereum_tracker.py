#!/usr/bin/env python3
"""
Ethereum Blockchain Tracker
Tracks NFT mints, transactions, and metadata for Ethereum addresses
NOW WITH MULTI-PROVIDER FAILOVER (Alchemy → Infura → Public nodes)
"""

import os
import json
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.blockchain_db import get_db
from collectors.multi_provider_web3 import MultiProviderWeb3

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EthereumTracker:
    """
    Track Ethereum NFTs and transactions using multi-provider RPC

    Resilient design with automatic failover:
    - Alchemy (primary - enhanced APIs)
    - Infura (fallback)
    - Public RPC nodes (backup)
    """

    def __init__(self, use_multi_provider: bool = True):
        """
        Initialize Ethereum tracker

        Args:
            use_multi_provider: Use multi-provider client (True) or single Alchemy (False)
        """
        self.db = get_db()
        self.use_multi_provider = use_multi_provider

        if use_multi_provider:
            # Use resilient multi-provider client
            self.web3_client = MultiProviderWeb3('ethereum')
            logger.info("Using multi-provider RPC (resilient mode)")
        else:
            # Legacy single-provider mode
            self.api_key = os.getenv('ALCHEMY_API_KEY', '')
            if not self.api_key:
                logger.warning("No ALCHEMY_API_KEY found in .env")
            self.base_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.api_key}"
            self.web3_client = None
            logger.info("Using single-provider RPC (legacy mode)")

    def _rpc_call(self, method: str, params: List) -> Optional[Dict]:
        """
        Make a JSON-RPC call with automatic failover

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            RPC result or None
        """
        if self.use_multi_provider and self.web3_client:
            # Use multi-provider with failover
            return self.web3_client.rpc_call(method, params)
        else:
            # Legacy single-provider mode
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1
            }

            try:
                response = requests.post(self.base_url, json=payload, timeout=30)
                result = response.json()

                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    logger.error(f"RPC error: {result['error'].get('message', 'Unknown')}")
                    return None

            except Exception as e:
                logger.error(f"Request error: {e}")
                return None

    def get_nfts_created_by(self, creator_address: str, start_block: int = 0) -> List[Dict]:
        """
        Get all NFTs minted by a specific address

        Uses alchemy_getAssetTransfers to find mint transactions
        (from 0x0000... to creator address)

        Args:
            creator_address: Ethereum address
            start_block: Starting block number (default: 0 for all history)

        Returns:
            List of NFT mint records
        """
        logger.info(f"Fetching NFTs created by {creator_address}")

        result = self._rpc_call('alchemy_getAssetTransfers', [{
            "fromBlock": hex(start_block),
            "toBlock": "latest",
            "fromAddress": "0x0000000000000000000000000000000000000000",  # Null address = mint
            "toAddress": creator_address,
            "category": ["erc721", "erc1155"],
            "withMetadata": True,
            "maxCount": "0x3e8"  # 1000 results max per call
        }])

        if not result:
            return []

        mints = []
        for transfer in result.get('transfers', []):
            # Extract mint data
            mint = {
                'contract_address': transfer.get('rawContract', {}).get('address'),
                'token_id': transfer.get('tokenId'),
                'tx_hash': transfer.get('hash'),
                'block_number': int(transfer.get('blockNum', '0'), 16),
                'timestamp': transfer.get('metadata', {}).get('blockTimestamp'),
                'category': transfer.get('category'),  # erc721 or erc1155
            }

            # Filter out invalid entries
            if mint['contract_address'] and mint['token_id']:
                mints.append(mint)

        logger.info(f"Found {len(mints)} NFT mints")
        return mints

    def get_nft_metadata(self, contract_address: str, token_id: str) -> Optional[Dict]:
        """
        Fetch full metadata for an NFT using Alchemy Enhanced API

        Args:
            contract_address: NFT contract address
            token_id: Token ID (as string)

        Returns:
            Dict with NFT metadata
        """
        logger.info(f"Fetching metadata for {contract_address} #{token_id}")

        result = self._rpc_call('alchemy_getNFTMetadata', [
            contract_address,
            token_id
        ])

        if not result:
            return None

        # Extract and structure metadata
        metadata = {
            'name': result.get('title') or result.get('name'),
            'description': result.get('description'),
            'token_uri': result.get('tokenUri', {}).get('raw'),
            'token_uri_gateway': result.get('tokenUri', {}).get('gateway'),
            'media': result.get('media', []),
            'image': None,
            'attributes': result.get('metadata', {}).get('attributes', []),
            'metadata_json': json.dumps(result.get('metadata', {})),
        }

        # Extract image URL (prefer gateway over raw)
        if metadata['media']:
            media = metadata['media'][0]
            metadata['image'] = media.get('gateway') or media.get('raw')

        # Extract IPFS hash from token_uri
        token_uri = metadata['token_uri']
        if token_uri and 'ipfs://' in token_uri:
            metadata['ipfs_hash'] = token_uri.replace('ipfs://', '').split('/')[0]

        return metadata

    def get_nft_sales(self, contract_address: str, token_id: str) -> List[Dict]:
        """
        Get sales history for an NFT

        Args:
            contract_address: NFT contract address
            token_id: Token ID (as string)

        Returns:
            List of sale records
        """
        logger.info(f"Fetching sales for {contract_address} #{token_id}")

        result = self._rpc_call('alchemy_getNFTSales', [{
            "contractAddress": contract_address,
            "tokenId": token_id,
            "order": "desc"  # Most recent first
        }])

        if not result:
            return []

        sales = []
        for sale in result.get('nftSales', []):
            sale_record = {
                'buyer_address': sale.get('buyerAddress'),
                'seller_address': sale.get('sellerAddress'),
                'marketplace': sale.get('marketplace'),
                'tx_hash': sale.get('transactionHash'),
                'block_timestamp': sale.get('blockTimestamp'),
                'quantity': sale.get('quantity', 1),
            }

            # Extract price information
            seller_fee = sale.get('sellerFee', {})
            sale_record['price_wei'] = seller_fee.get('amount')
            sale_record['currency'] = seller_fee.get('symbol', 'ETH')

            # Convert to native amount (ETH)
            if sale_record['price_wei']:
                try:
                    sale_record['price_native'] = int(sale_record['price_wei']) / 1e18
                except:
                    sale_record['price_native'] = None

            sales.append(sale_record)

        logger.info(f"Found {len(sales)} sales")
        return sales

    def get_asset_transfers(
        self,
        address: str,
        from_address: bool = True,
        start_block: int = 0
    ) -> List[Dict]:
        """
        Get asset transfer history for an address

        Args:
            address: Ethereum address
            from_address: If True, get transfers FROM address; if False, get transfers TO address
            start_block: Starting block number

        Returns:
            List of transfer records
        """
        params = {
            "fromBlock": hex(start_block),
            "toBlock": "latest",
            "category": ["external", "erc20", "erc721", "erc1155"],
            "withMetadata": True,
            "maxCount": "0x3e8"
        }

        if from_address:
            params["fromAddress"] = address
        else:
            params["toAddress"] = address

        result = self._rpc_call('alchemy_getAssetTransfers', [params])

        if not result:
            return []

        transfers = result.get('transfers', [])
        logger.info(f"Found {len(transfers)} transfers")

        return transfers

    def sync_address(self, address_id: int, address: str, full_sync: bool = True):
        """
        Sync all NFT data for a tracked address

        Args:
            address_id: Database ID of tracked address
            address: Ethereum address
            full_sync: If True, sync from genesis; if False, sync from last sync

        Returns:
            Dict with sync results
        """
        logger.info(f"Starting sync for address {address} (ID: {address_id})")

        # Get last sync block
        start_block = 0
        if not full_sync:
            # Get highest block number from previous sync
            last_mint = self.db.execute('''
                SELECT MAX(mint_block_number) as max_block
                FROM nft_mints
                WHERE address_id = ?
            ''', (address_id,))

            if last_mint and last_mint[0]['max_block']:
                start_block = last_mint[0]['max_block'] + 1

        # Record sync start
        sync_result = self.db.execute('''
            INSERT INTO sync_history (address_id, sync_type, started_at, status)
            VALUES (?, ?, ?, 'running')
        ''', (address_id, 'full' if full_sync else 'incremental', datetime.utcnow().isoformat()))

        sync_id = sync_result[0]['last_id']

        try:
            # Get NFT mints
            mints = self.get_nfts_created_by(address, start_block)

            items_new = 0

            for mint in mints:
                # Get metadata
                metadata = self.get_nft_metadata(
                    mint['contract_address'],
                    mint['token_id']
                )

                if metadata:
                    # Insert or update NFT record
                    self.db.execute('''
                        INSERT OR REPLACE INTO nft_mints
                        (address_id, token_id, contract_address, mint_tx_hash,
                         mint_block_number, mint_timestamp, token_uri,
                         metadata_json, ipfs_hash, name, description, attributes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        address_id,
                        mint['token_id'],
                        mint['contract_address'],
                        mint['tx_hash'],
                        mint['block_number'],
                        mint['timestamp'],
                        metadata.get('token_uri'),
                        metadata.get('metadata_json'),
                        metadata.get('ipfs_hash'),
                        metadata.get('name'),
                        metadata.get('description'),
                        json.dumps(metadata.get('attributes', []))
                    ))

                    items_new += 1

                    # Get sales data
                    sales = self.get_nft_sales(
                        mint['contract_address'],
                        mint['token_id']
                    )

                    # Get NFT ID from database
                    nft_result = self.db.execute('''
                        SELECT id FROM nft_mints
                        WHERE contract_address = ? AND token_id = ? AND address_id = ?
                    ''', (mint['contract_address'], mint['token_id'], address_id))

                    if nft_result:
                        nft_id = nft_result[0]['id']

                        # Insert sales/collectors
                        for sale in sales:
                            if sale.get('buyer_address'):
                                self.db.execute('''
                                    INSERT OR REPLACE INTO collectors
                                    (collector_address, network, nft_mint_id,
                                     purchase_tx_hash, purchase_price_wei,
                                     purchase_price_native, currency,
                                     purchase_timestamp, platform)
                                    VALUES (?, 'ethereum', ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    sale['buyer_address'],
                                    nft_id,
                                    sale.get('tx_hash'),
                                    sale.get('price_wei'),
                                    sale.get('price_native'),
                                    sale.get('currency'),
                                    sale.get('block_timestamp'),
                                    sale.get('marketplace')
                                ))

            # Update sync record
            self.db.execute('''
                UPDATE sync_history
                SET completed_at = ?, items_found = ?, items_new = ?, status = 'success'
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), len(mints), items_new, sync_id))

            # Update address last_synced
            self.db.execute('''
                UPDATE tracked_addresses
                SET last_synced = ?
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), address_id))

            logger.info(f"Sync complete: {items_new} new NFTs")

            return {
                'success': True,
                'items_found': len(mints),
                'items_new': items_new,
                'sync_id': sync_id
            }

        except Exception as e:
            logger.error(f"Sync error: {e}")

            # Update sync record with error
            self.db.execute('''
                UPDATE sync_history
                SET completed_at = ?, error_message = ?, status = 'failed'
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), str(e), sync_id))

            return {
                'success': False,
                'error': str(e),
                'sync_id': sync_id
            }


# Test interface
if __name__ == '__main__':
    import sys

    tracker = EthereumTracker()

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python ethereum_tracker.py mints <address>")
        print("  python ethereum_tracker.py metadata <contract> <token_id>")
        print("  python ethereum_tracker.py sales <contract> <token_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'mints':
        address = sys.argv[2]
        mints = tracker.get_nfts_created_by(address)

        print(f"\nNFTs Minted by {address}:\n")
        for mint in mints:
            print(f"Contract: {mint['contract_address']}")
            print(f"Token ID: {mint['token_id']}")
            print(f"TX Hash: {mint['tx_hash']}")
            print(f"Block: {mint['block_number']}")
            print()

    elif command == 'metadata':
        contract = sys.argv[2]
        token_id = sys.argv[3]
        metadata = tracker.get_nft_metadata(contract, token_id)

        if metadata:
            print("\nNFT Metadata:\n")
            print(json.dumps(metadata, indent=2))

    elif command == 'sales':
        contract = sys.argv[2]
        token_id = sys.argv[3]
        sales = tracker.get_nft_sales(contract, token_id)

        print(f"\nSales History:\n")
        for sale in sales:
            print(f"Buyer: {sale['buyer_address']}")
            print(f"Price: {sale['price_native']} {sale['currency']}")
            print(f"Platform: {sale['marketplace']}")
            print(f"Date: {sale['block_timestamp']}")
            print()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
