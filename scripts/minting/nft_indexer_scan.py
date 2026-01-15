#!/usr/bin/env python3
"""
NFT-8 Indexer-Based Scanner

Uses NFT indexer APIs (Alchemy, Reservoir, SimpleHash) instead of raw RPC calls.
This is the PROPER way to do historical scans - fast, unlimited, free tiers available.

Why indexers over raw RPC:
- Raw RPC eth_getLogs has block range limits (800-1000 blocks)
- Scanning full history via RPC = thousands of requests = rate limited
- Indexers pre-index all NFT data = instant queries
"""

import os
import sys
import json
import time
import logging
import requests
from typing import List, Dict, Optional, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class NFTData:
    """Normalized NFT data from any indexer"""
    contract_address: str
    token_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    platform: Optional[str] = None
    network: str = 'ethereum'
    mint_timestamp: Optional[str] = None
    mint_block: Optional[int] = None
    token_uri: Optional[str] = None
    collection_name: Optional[str] = None
    owner: Optional[str] = None


class AlchemyNFTScanner:
    """
    Scan NFTs using Alchemy NFT API

    Free tier: 300M compute units/month (plenty for scanning)
    Get key at: https://www.alchemy.com/
    """

    BASE_URLS = {
        'ethereum': 'https://eth-mainnet.g.alchemy.com/nft/v3',
        'polygon': 'https://polygon-mainnet.g.alchemy.com/nft/v3',
        'base': 'https://base-mainnet.g.alchemy.com/nft/v3',
        'arbitrum': 'https://arb-mainnet.g.alchemy.com/nft/v3',
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ALCHEMY_API_KEY')
        if not self.api_key:
            logger.warning("No Alchemy API key found. Set ALCHEMY_API_KEY environment variable.")

    def get_nfts_for_owner(self, address: str, network: str = 'ethereum') -> List[NFTData]:
        """Get all NFTs owned by an address"""
        if not self.api_key:
            return []

        base_url = self.BASE_URLS.get(network)
        if not base_url:
            logger.warning(f"Network {network} not supported by Alchemy")
            return []

        nfts = []
        page_key = None

        try:
            while True:
                url = f"{base_url}/{self.api_key}/getNFTsForOwner"
                params = {
                    'owner': address,
                    'withMetadata': 'true',
                    'pageSize': 100
                }
                if page_key:
                    params['pageKey'] = page_key

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    for nft in data.get('ownedNfts', []):
                        nfts.append(NFTData(
                            contract_address=nft.get('contract', {}).get('address', ''),
                            token_id=nft.get('tokenId', ''),
                            name=nft.get('name') or nft.get('title'),
                            description=nft.get('description'),
                            image_url=nft.get('image', {}).get('cachedUrl') or nft.get('image', {}).get('originalUrl'),
                            platform=nft.get('contract', {}).get('openSeaMetadata', {}).get('collectionName'),
                            network=network,
                            token_uri=nft.get('tokenUri'),
                            collection_name=nft.get('contract', {}).get('name'),
                            owner=address
                        ))

                    page_key = data.get('pageKey')
                    if not page_key:
                        break

                    logger.info(f"  Fetched {len(nfts)} NFTs so far...")
                else:
                    logger.error(f"Alchemy API error: {response.status_code}")
                    break

        except Exception as e:
            logger.error(f"Error fetching NFTs: {e}")

        return nfts

    def get_minted_nfts(self, address: str, network: str = 'ethereum') -> List[NFTData]:
        """
        Get NFTs minted/created by an address

        Uses getTransfersForOwner with FROM_ADDRESS category
        """
        if not self.api_key:
            return []

        base_url = self.BASE_URLS.get(network)
        if not base_url:
            return []

        mints = []
        page_key = None

        try:
            while True:
                # Use v3 asset transfers endpoint
                url = f"https://{'eth' if network == 'ethereum' else network}-mainnet.g.alchemy.com/v2/{self.api_key}"

                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "alchemy_getAssetTransfers",
                    "params": [{
                        "fromBlock": "0x0",
                        "toBlock": "latest",
                        "fromAddress": "0x0000000000000000000000000000000000000000",
                        "toAddress": address,
                        "category": ["erc721", "erc1155"],
                        "withMetadata": True,
                        "maxCount": "0x64"  # 100
                    }]
                }

                if page_key:
                    payload["params"][0]["pageKey"] = page_key

                response = requests.post(url, json=payload, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', {})

                    for transfer in result.get('transfers', []):
                        # This is a mint (from null address to user)
                        raw_contract = transfer.get('rawContract', {})

                        mints.append(NFTData(
                            contract_address=raw_contract.get('address', ''),
                            token_id=transfer.get('tokenId') or raw_contract.get('value', ''),
                            name=transfer.get('asset'),
                            network=network,
                            mint_timestamp=transfer.get('metadata', {}).get('blockTimestamp'),
                            mint_block=int(transfer.get('blockNum', '0x0'), 16) if transfer.get('blockNum') else None,
                        ))

                    page_key = result.get('pageKey')
                    if not page_key:
                        break

                    logger.info(f"  Found {len(mints)} mints so far...")
                else:
                    logger.error(f"Alchemy API error: {response.status_code} - {response.text[:200]}")
                    break

        except Exception as e:
            logger.error(f"Error fetching mints: {e}")

        return mints

    def get_nft_sales(self, address: str, network: str = 'ethereum') -> List[Dict]:
        """Get NFT sales for an address (sold NFTs)"""
        if not self.api_key:
            return []

        # Use Alchemy's getNFTSales endpoint
        base_url = self.BASE_URLS.get(network)
        if not base_url:
            return []

        sales = []
        page_key = None

        try:
            while True:
                url = f"{base_url}/{self.api_key}/getNFTSales"
                params = {
                    'fromBlock': 0,
                    'toBlock': 'latest',
                    'order': 'desc',
                    'limit': 100,
                    'sellerAddress': address
                }
                if page_key:
                    params['pageKey'] = page_key

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    for sale in data.get('nftSales', []):
                        sales.append({
                            'contract': sale.get('contractAddress'),
                            'token_id': sale.get('tokenId'),
                            'buyer': sale.get('buyerAddress'),
                            'seller': sale.get('sellerAddress'),
                            'price_eth': float(sale.get('sellerFee', {}).get('amount', 0)) / 1e18,
                            'marketplace': sale.get('marketplace'),
                            'timestamp': sale.get('blockTimestamp'),
                            'tx_hash': sale.get('transactionHash')
                        })

                    page_key = data.get('pageKey')
                    if not page_key:
                        break
                else:
                    break

        except Exception as e:
            logger.error(f"Error fetching sales: {e}")

        return sales


class ReservoirScanner:
    """
    Scan NFTs using Reservoir API (free tier available)

    Free tier: 120 requests/minute
    Get key at: https://reservoir.tools/
    """

    BASE_URL = "https://api.reservoir.tools"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('RESERVOIR_API_KEY')
        self.headers = {}
        if self.api_key:
            self.headers['x-api-key'] = self.api_key

    def get_user_tokens(self, address: str, limit: int = 500) -> List[NFTData]:
        """Get all tokens owned by user"""
        nfts = []
        continuation = None

        try:
            while len(nfts) < limit:
                url = f"{self.BASE_URL}/users/{address}/tokens/v7"
                params = {'limit': 100}
                if continuation:
                    params['continuation'] = continuation

                response = requests.get(url, params=params, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    for token in data.get('tokens', []):
                        t = token.get('token', {})
                        nfts.append(NFTData(
                            contract_address=t.get('contract'),
                            token_id=t.get('tokenId'),
                            name=t.get('name'),
                            description=t.get('description'),
                            image_url=t.get('image'),
                            platform=t.get('collection', {}).get('name'),
                            network='ethereum',
                            collection_name=t.get('collection', {}).get('name'),
                            owner=address
                        ))

                    continuation = data.get('continuation')
                    if not continuation:
                        break
                else:
                    logger.warning(f"Reservoir API error: {response.status_code}")
                    break

        except Exception as e:
            logger.error(f"Reservoir error: {e}")

        return nfts

    def get_user_activity(self, address: str, types: List[str] = None) -> List[Dict]:
        """
        Get user's NFT activity (mints, sales, purchases)

        types: ['mint', 'sale', 'transfer', 'bid', 'ask']
        """
        if types is None:
            types = ['mint', 'sale']

        activities = []
        continuation = None

        try:
            while True:
                url = f"{self.BASE_URL}/users/activity/v6"
                params = {
                    'users': address,
                    'types': types,
                    'limit': 100
                }
                if continuation:
                    params['continuation'] = continuation

                response = requests.get(url, params=params, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    for activity in data.get('activities', []):
                        activities.append({
                            'type': activity.get('type'),
                            'contract': activity.get('contract'),
                            'token_id': activity.get('token', {}).get('tokenId'),
                            'token_name': activity.get('token', {}).get('name'),
                            'collection': activity.get('collection', {}).get('name'),
                            'from': activity.get('fromAddress'),
                            'to': activity.get('toAddress'),
                            'price_eth': activity.get('price'),
                            'timestamp': activity.get('timestamp'),
                            'tx_hash': activity.get('txHash')
                        })

                    continuation = data.get('continuation')
                    if not continuation:
                        break
                else:
                    break

        except Exception as e:
            logger.error(f"Reservoir activity error: {e}")

        return activities


class SimpleHashScanner:
    """
    Scan NFTs using SimpleHash API

    Free tier: 1000 requests/day
    Supports: Ethereum, Polygon, Solana, Bitcoin Ordinals, etc.
    Get key at: https://simplehash.com/
    """

    BASE_URL = "https://api.simplehash.com/api/v0"

    CHAIN_MAP = {
        'ethereum': 'ethereum',
        'polygon': 'polygon',
        'solana': 'solana',
        'bitcoin': 'bitcoin',
        'base': 'base',
        'arbitrum': 'arbitrum',
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SIMPLEHASH_API_KEY')
        self.headers = {}
        if self.api_key:
            self.headers['X-API-KEY'] = self.api_key

    def get_nfts_by_owner(self, address: str, chains: List[str] = None) -> List[NFTData]:
        """Get NFTs owned across multiple chains"""
        if not self.api_key:
            logger.warning("SimpleHash API key required")
            return []

        if chains is None:
            chains = ['ethereum', 'polygon']

        chain_str = ','.join([self.CHAIN_MAP.get(c, c) for c in chains])
        nfts = []
        cursor = None

        try:
            while True:
                url = f"{self.BASE_URL}/nfts/owners"
                params = {
                    'chains': chain_str,
                    'wallet_addresses': address,
                    'limit': 50
                }
                if cursor:
                    params['cursor'] = cursor

                response = requests.get(url, params=params, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    for nft in data.get('nfts', []):
                        nfts.append(NFTData(
                            contract_address=nft.get('contract_address'),
                            token_id=nft.get('token_id'),
                            name=nft.get('name'),
                            description=nft.get('description'),
                            image_url=nft.get('image_url') or nft.get('previews', {}).get('image_medium_url'),
                            platform=nft.get('collection', {}).get('name'),
                            network=nft.get('chain'),
                            collection_name=nft.get('collection', {}).get('name'),
                            owner=address
                        ))

                    cursor = data.get('next_cursor')
                    if not cursor:
                        break
                else:
                    logger.error(f"SimpleHash error: {response.status_code}")
                    break

        except Exception as e:
            logger.error(f"SimpleHash error: {e}")

        return nfts


class UnifiedNFTScanner:
    """
    Unified scanner that tries multiple indexers

    Priority: Alchemy > Reservoir > SimpleHash > Raw RPC (fallback)
    """

    def __init__(self):
        self.alchemy = AlchemyNFTScanner()
        self.reservoir = ReservoirScanner()
        self.simplehash = SimpleHashScanner()

        # Track which APIs are available
        self.available_apis = []
        if os.getenv('ALCHEMY_API_KEY'):
            self.available_apis.append('alchemy')
        if os.getenv('RESERVOIR_API_KEY'):
            self.available_apis.append('reservoir')
        if os.getenv('SIMPLEHASH_API_KEY'):
            self.available_apis.append('simplehash')

        logger.info(f"Available indexer APIs: {self.available_apis or ['none - using fallback']}")

    def scan_wallet(self, address: str, network: str = 'ethereum') -> Dict:
        """
        Comprehensive wallet scan using best available indexer

        Returns:
            Dict with owned_nfts, minted_nfts, sales, etc.
        """
        result = {
            'address': address,
            'network': network,
            'scan_date': datetime.utcnow().isoformat(),
            'owned_nfts': [],
            'minted_nfts': [],
            'sales': [],
            'source': None
        }

        # Try Alchemy first (best for Ethereum)
        if 'alchemy' in self.available_apis and network in AlchemyNFTScanner.BASE_URLS:
            logger.info(f"Using Alchemy API for {network}...")
            result['source'] = 'alchemy'

            # Get owned NFTs
            result['owned_nfts'] = self.alchemy.get_nfts_for_owner(address, network)
            logger.info(f"  Found {len(result['owned_nfts'])} owned NFTs")

            # Get mints
            result['minted_nfts'] = self.alchemy.get_minted_nfts(address, network)
            logger.info(f"  Found {len(result['minted_nfts'])} mints")

            # Get sales
            result['sales'] = self.alchemy.get_nft_sales(address, network)
            logger.info(f"  Found {len(result['sales'])} sales")

            return result

        # Try Reservoir
        if 'reservoir' in self.available_apis and network == 'ethereum':
            logger.info("Using Reservoir API...")
            result['source'] = 'reservoir'

            result['owned_nfts'] = self.reservoir.get_user_tokens(address)
            activity = self.reservoir.get_user_activity(address, types=['mint', 'sale'])

            result['minted_nfts'] = [a for a in activity if a['type'] == 'mint']
            result['sales'] = [a for a in activity if a['type'] == 'sale']

            return result

        # Try SimpleHash
        if 'simplehash' in self.available_apis:
            logger.info("Using SimpleHash API...")
            result['source'] = 'simplehash'

            result['owned_nfts'] = self.simplehash.get_nfts_by_owner(address, [network])
            return result

        logger.warning(f"No indexer API available for {network}. Add ALCHEMY_API_KEY to .env")
        return result


def scan_artist_comprehensive(
    address: str,
    network: str = 'ethereum',
    output_dir: Path = None
) -> Dict:
    """
    Comprehensive artist scan using indexer APIs

    Args:
        address: Wallet address
        network: Network to scan
        output_dir: Optional output directory

    Returns:
        Scan results
    """
    scanner = UnifiedNFTScanner()
    result = scanner.scan_wallet(address, network)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{address[:16]}_{network}_scan.json"

        with open(output_path, 'w') as f:
            # Convert NFTData objects to dicts
            export_data = {
                **result,
                'owned_nfts': [asdict(n) if hasattr(n, '__dataclass_fields__') else n for n in result['owned_nfts']],
                'minted_nfts': [asdict(n) if hasattr(n, '__dataclass_fields__') else n for n in result['minted_nfts']],
            }
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Saved to {output_path}")

    return result


# CLI
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""
NFT-8 Indexer Scanner

Fast historical NFT scanning using indexer APIs.

Usage:
  python nft_indexer_scan.py <address> [--network ethereum] [--output ./scans/]

Environment Variables (at least one required):
  ALCHEMY_API_KEY    - Get free at https://www.alchemy.com/
  RESERVOIR_API_KEY  - Get free at https://reservoir.tools/
  SIMPLEHASH_API_KEY - Get free at https://simplehash.com/

Example:
  export ALCHEMY_API_KEY="your_key_here"
  python nft_indexer_scan.py 0x14287e62B859A3A5E19B3C2D59Ed1F12ac94ba4c --output ./scans/
        """)
        sys.exit(0)

    address = sys.argv[1]
    network = 'ethereum'
    output_dir = None

    for i, arg in enumerate(sys.argv):
        if arg == '--network' and i + 1 < len(sys.argv):
            network = sys.argv[i + 1]
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_dir = Path(sys.argv[i + 1])

    result = scan_artist_comprehensive(address, network, output_dir)

    print(f"\n{'='*50}")
    print(f"SCAN RESULTS: {address[:20]}...")
    print(f"{'='*50}")
    print(f"Network: {network}")
    print(f"Source: {result['source'] or 'none'}")
    print(f"Owned NFTs: {len(result['owned_nfts'])}")
    print(f"Minted NFTs: {len(result['minted_nfts'])}")
    print(f"Sales: {len(result['sales'])}")
