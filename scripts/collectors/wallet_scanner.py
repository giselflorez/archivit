#!/usr/bin/env python3
"""
Multi-Chain Wallet Scanner - No API Keys Required
Scans wallet addresses across multiple blockchains to discover:
- NFTs created (minted) by the address
- NFTs currently owned by the address
- Collectors who bought the artist's NFTs
- Transfer history of artist's creations
- Interactions between collectors

Supported Networks:
- Ethereum (ETH) - Full support via raw events
- Polygon (MATIC) - Full support via raw events
- Tezos (XTZ) - Basic support via TzKT API (free, no key)
- Solana (SOL) - Basic support via public RPC
"""

import os
import re
import json
import logging
import requests
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.multi_provider_web3 import MultiProviderWeb3
from collectors.raw_nft_parser import RawNFTParser
from collectors.blockchain_db import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WalletScanner:
    """
    Multi-chain wallet scanner for NFT tracking

    Automatically detects blockchain from address format and scans for:
    - Minted NFTs (creations)
    - Owned NFTs (holdings)
    - Sales and collectors
    - Transfer history
    """

    # Address patterns for blockchain detection
    ADDRESS_PATTERNS = {
        'ethereum': r'^0x[a-fA-F0-9]{40}$',
        'polygon': r'^0x[a-fA-F0-9]{40}$',  # Same as ETH, need context
        'tezos': r'^(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}$',
        'solana': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$',
        'bitcoin': r'^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$',
    }

    # Known NFT platforms and their contracts
    KNOWN_CONTRACTS = {
        'ethereum': {
            '0xb932a70a57673d89f4acffbe830e8ed7f75fb9e0': 'SuperRare',
            '0x3b3ee1931dc30c1957379fac9aba94d1c48a5405': 'Foundation',
            '0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d': 'BAYC',
            '0x60e4d786628fea6478f785a6d7e704777c86a7c6': 'MAYC',
            '0xa7d8d9ef8d8ce8992df33d8b8cf4aebabd5bd270': 'Art Blocks',
            '0x059edd72cd353df5106d2b9cc5ab83a52287ac3a': 'Art Blocks Curated',
            '0xfbeef911dc5821886e1dda71586d90ed28174b7d': 'Known Origin',
            '0x495f947276749ce646f68ac8c248420045cb7b5e': 'OpenSea Shared',
        },
        'polygon': {
            '0x2953399124f0cbb46d2cbacd8a89cf0599974963': 'OpenSea Polygon',
        },
        'tezos': {
            # Objkt.com marketplace contracts
            'KT1WvzYHCNBvDSdwafTHv7nJ1dWmZ8GCYuuC': 'Objkt',
            'KT1FvqJwEDWb1Gwc55Jd1jjTHRVWbYKUUpyq': 'Objkt v1',
            'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9': 'Objkt v2',
            # Hic et Nunc (HEN) - historical
            'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton': 'Hic et Nunc',
            'KT1AFA2mwNUMNd4SsujE1YYp29vd8BZejyKW': 'HEN v2',
            # fxhash generative art
            'KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE': 'fxhash',
            'KT1U6EHmNxJTkvaWJ4ThczG4FSDaHC21ssvi': 'fxhash v2',
            'KT1EfsNuqwLAWDd3o4pvfUx1CAh5GMdTrRvr': 'fxhash Gentk',
            # Teia (HEN community fork)
            'KT1PHubm9HtyQEJ4BBpMTVomq6mhbfNZ9z5w': 'Teia',
            # Versum
            'KT1LjmAdYQCLBjwv4S2oFkEzyHVkomAf5MrW': 'Versum',
            # 8bidou
            'KT1MxDwChiDwd6WBVs24g1NjERUoK622ZEFp': '8bidou',
            # Typed
            'KT1J6NY5AU61GzUX51n59wwiZcGJ9DrNTwbK': 'Typed',
        }
    }

    def __init__(self):
        """Initialize wallet scanner with multi-chain support"""
        self.db = get_db()
        self.eth_parser = RawNFTParser('ethereum')
        self.polygon_parser = RawNFTParser('polygon')

        # Cache for collector interactions
        self.collector_cache = {}

    def detect_blockchain(self, address: str) -> Tuple[str, float]:
        """
        Detect blockchain from address format

        Args:
            address: Wallet address string

        Returns:
            Tuple of (network_name, confidence_score)
        """
        address = address.strip()

        # Tezos - unique format
        if re.match(self.ADDRESS_PATTERNS['tezos'], address):
            return ('tezos', 1.0)

        # Bitcoin - unique format
        if re.match(self.ADDRESS_PATTERNS['bitcoin'], address):
            return ('bitcoin', 1.0)

        # Solana - base58, 32-44 chars (but not Bitcoin)
        if re.match(self.ADDRESS_PATTERNS['solana'], address):
            # Distinguish from Bitcoin by length and pattern
            if len(address) >= 32 and not address.startswith(('1', '3', 'bc1')):
                return ('solana', 0.9)

        # Ethereum/Polygon - same format, default to Ethereum
        if re.match(self.ADDRESS_PATTERNS['ethereum'], address):
            return ('ethereum', 0.8)  # Lower confidence since could be Polygon

        return ('unknown', 0.0)

    def detect_all_networks(self, address: str) -> List[str]:
        """
        Get all possible networks for an address (0x addresses can be both ETH and Polygon)

        Args:
            address: Wallet address

        Returns:
            List of possible network names
        """
        primary_network, confidence = self.detect_blockchain(address)

        if primary_network == 'ethereum':
            return ['ethereum', 'polygon']  # Check both
        elif primary_network == 'unknown':
            return []
        else:
            return [primary_network]

    def scan_ethereum_wallet(
        self,
        address: str,
        scan_mints: bool = True,
        scan_owned: bool = True,
        scan_collectors: bool = True,
        recent_blocks: int = 100000
    ) -> Dict:
        """
        Scan Ethereum wallet for NFT activity

        Args:
            address: Ethereum address (0x...)
            scan_mints: Scan for NFTs minted by this address
            scan_owned: Scan for NFTs currently owned
            scan_collectors: Track collectors who bought from this address
            recent_blocks: How many blocks to scan back

        Returns:
            Scan results with mints, holdings, collectors, transfers
        """
        logger.info(f"Scanning Ethereum wallet: {address}")

        results = {
            'address': address,
            'network': 'ethereum',
            'scan_date': datetime.utcnow().isoformat(),
            'minted_nfts': [],
            'owned_nfts': [],
            'collectors': [],
            'transfers': [],
            'stats': {}
        }

        parser = self.eth_parser

        # 1. Find NFTs minted by this address
        if scan_mints:
            logger.info("Scanning for minted NFTs...")
            mints = self._find_mints_by_address(parser, address, recent_blocks)
            results['minted_nfts'] = mints
            results['stats']['total_minted'] = len(mints)

        # 2. For each minted NFT, track collectors and transfers
        if scan_collectors and results['minted_nfts']:
            logger.info("Tracking collectors and transfers...")
            all_collectors = {}
            all_transfers = []

            for mint in results['minted_nfts'][:20]:  # Limit to first 20 for speed
                contract = mint['contract_address']
                token_id = mint['token_id']

                # Get transfer history for this NFT
                transfers = parser.get_nft_transfers(
                    contract,
                    from_block=mint.get('block_number', 0),
                    token_id=token_id
                )

                for transfer in transfers:
                    # Skip the mint itself
                    if transfer.get('is_mint'):
                        continue

                    all_transfers.append({
                        'contract': contract,
                        'token_id': token_id,
                        'from': transfer['from_address'],
                        'to': transfer['to_address'],
                        'tx_hash': transfer['tx_hash'],
                        'block': transfer['block_number'],
                    })

                    # Track collector
                    collector_addr = transfer['to_address']
                    if collector_addr not in all_collectors:
                        all_collectors[collector_addr] = {
                            'address': collector_addr,
                            'nfts_acquired': [],
                            'total_pieces': 0,
                            'first_acquisition_block': transfer['block_number'],
                        }

                    all_collectors[collector_addr]['nfts_acquired'].append({
                        'contract': contract,
                        'token_id': token_id,
                        'block': transfer['block_number'],
                    })
                    all_collectors[collector_addr]['total_pieces'] += 1

            results['collectors'] = list(all_collectors.values())
            results['transfers'] = all_transfers
            results['stats']['unique_collectors'] = len(all_collectors)
            results['stats']['total_transfers'] = len(all_transfers)

        # 3. Check current ownership of minted NFTs
        if scan_owned and results['minted_nfts']:
            logger.info("Checking current ownership...")
            for mint in results['minted_nfts']:
                current_owner = parser.get_current_owner(
                    mint['contract_address'],
                    mint['token_id']
                )
                mint['current_owner'] = current_owner
                mint['still_owned'] = (current_owner and current_owner.lower() == address.lower())

        logger.info(f"Scan complete: {results['stats']}")
        return results

    def _find_mints_by_address(
        self,
        parser: RawNFTParser,
        address: str,
        recent_blocks: int
    ) -> List[Dict]:
        """
        Find all NFT mints where this address received the token from null address

        This catches NFTs minted TO this address (artist receiving their own mint)
        """
        logger.info(f"Finding mints to {address} in last {recent_blocks} blocks...")

        mints = parser.get_mints_by_address(address, from_block=0)

        # Enrich with metadata
        enriched_mints = []
        for mint in mints[:50]:  # Limit for speed
            try:
                # Get token URI and metadata
                token_uri = parser.get_token_uri(mint['contract_address'], mint['token_id'])

                enriched_mint = {
                    'contract_address': mint['contract_address'],
                    'token_id': mint['token_id'],
                    'tx_hash': mint['tx_hash'],
                    'block_number': mint['block_number'],
                    'token_uri': token_uri,
                    'platform': self._identify_platform(mint['contract_address'], 'ethereum'),
                }

                # Fetch metadata if URI available
                if token_uri:
                    metadata = parser.fetch_ipfs_metadata(token_uri)
                    if metadata:
                        enriched_mint['name'] = metadata.get('name')
                        enriched_mint['description'] = metadata.get('description')
                        enriched_mint['image'] = metadata.get('image')
                        enriched_mint['attributes'] = metadata.get('attributes', [])

                enriched_mints.append(enriched_mint)

            except Exception as e:
                logger.warning(f"Failed to enrich mint {mint['token_id']}: {e}")
                enriched_mints.append(mint)

        return enriched_mints

    def _identify_platform(self, contract_address: str, network: str) -> str:
        """Identify NFT platform from contract address (case-aware)"""
        contracts = self.KNOWN_CONTRACTS.get(network, {})
        # Ethereum/Polygon: case-insensitive lookup
        # Tezos: case-sensitive lookup (base58check addresses)
        if network in ('ethereum', 'polygon'):
            return contracts.get(contract_address.lower(), 'Unknown')
        else:
            return contracts.get(contract_address, 'Unknown')

    def scan_solana_wallet(self, address: str) -> Dict:
        """
        Scan Solana wallet for NFTs using public RPC

        Args:
            address: Solana address (base58)

        Returns:
            Scan results with NFTs
        """
        logger.info(f"Scanning Solana wallet: {address}")

        results = {
            'address': address,
            'network': 'solana',
            'scan_date': datetime.utcnow().isoformat(),
            'minted_nfts': [],
            'owned_nfts': [],
            'collectors': [],
            'stats': {}
        }

        # Solana public RPC endpoints
        rpc_endpoints = [
            "https://api.mainnet-beta.solana.com",
            "https://solana-api.projectserum.com",
            "https://rpc.ankr.com/solana",
        ]

        try:
            # Try to get token accounts (NFTs are SPL tokens with supply=1)
            for rpc_url in rpc_endpoints:
                try:
                    # Get all token accounts owned by this wallet
                    response = requests.post(
                        rpc_url,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getTokenAccountsByOwner",
                            "params": [
                                address,
                                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                                {"encoding": "jsonParsed"}
                            ]
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if 'result' in data and 'value' in data['result']:
                            token_accounts = data['result']['value']

                            for account in token_accounts:
                                parsed = account.get('account', {}).get('data', {}).get('parsed', {})
                                info = parsed.get('info', {})

                                # NFTs typically have amount=1 and decimals=0
                                token_amount = info.get('tokenAmount', {})
                                if token_amount.get('decimals') == 0 and token_amount.get('amount') == '1':
                                    mint_address = info.get('mint')

                                    nft = {
                                        'contract_address': mint_address,
                                        'token_id': mint_address,  # Solana uses mint address as ID
                                        'owner': info.get('owner'),
                                        'platform': 'Solana',
                                    }

                                    # Try to get metadata from Metaplex
                                    metadata = self._get_solana_nft_metadata(mint_address, rpc_url)
                                    if metadata:
                                        nft.update(metadata)

                                    results['owned_nfts'].append(nft)

                            results['stats']['total_owned'] = len(results['owned_nfts'])
                            break  # Success, don't try other endpoints

                except requests.Timeout:
                    logger.warning(f"Solana RPC timeout: {rpc_url}")
                    continue
                except Exception as e:
                    logger.warning(f"Solana RPC error ({rpc_url}): {e}")
                    continue

            # Try to find minted NFTs using Helius or other indexer APIs (free tier)
            self._find_solana_mints(address, results)

        except Exception as e:
            logger.error(f"Solana scan error: {e}")
            results['error'] = str(e)

        return results

    def _get_solana_nft_metadata(self, mint_address: str, rpc_url: str) -> Optional[Dict]:
        """Fetch Solana NFT metadata from Metaplex"""
        try:
            # Metaplex metadata PDA derivation would go here
            # For now, try common metadata APIs
            apis = [
                f"https://api.helius.xyz/v0/tokens/metadata?api-key=&mint={mint_address}",
                f"https://api-mainnet.magiceden.dev/v2/tokens/{mint_address}",
            ]

            for api_url in apis:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'name': data.get('name') or data.get('onChainMetadata', {}).get('metadata', {}).get('data', {}).get('name'),
                            'image': data.get('image') or data.get('offChainMetadata', {}).get('image'),
                            'description': data.get('description'),
                        }
                except:
                    continue

        except Exception as e:
            logger.debug(f"Failed to get Solana metadata: {e}")

        return None

    def _find_solana_mints(self, address: str, results: Dict):
        """Find NFTs minted by a Solana address"""
        # This would require indexer API access
        # Magic Eden, Helius, or similar
        # For now, note this as a limitation
        results['stats']['mint_scan_note'] = 'Full mint history requires indexer API'

    def scan_bitcoin_ordinals(self, address: str) -> Dict:
        """
        Scan Bitcoin address for Ordinals inscriptions

        Args:
            address: Bitcoin address (1.../3.../bc1...)

        Returns:
            Scan results with inscriptions
        """
        logger.info(f"Scanning Bitcoin ordinals for: {address}")

        results = {
            'address': address,
            'network': 'bitcoin',
            'scan_date': datetime.utcnow().isoformat(),
            'inscriptions': [],
            'owned_ordinals': [],
            'stats': {}
        }

        try:
            # Use ordinals.com API or Hiro API
            apis = [
                f"https://api.hiro.so/ordinals/v1/inscriptions?address={address}",
                f"https://ordapi.xyz/address/{address}/inscriptions",
            ]

            for api_url in apis:
                try:
                    response = requests.get(api_url, timeout=30)

                    if response.status_code == 200:
                        data = response.json()

                        # Handle Hiro API format
                        if 'results' in data:
                            inscriptions = data['results']
                        elif isinstance(data, list):
                            inscriptions = data
                        else:
                            inscriptions = []

                        for insc in inscriptions:
                            ordinal = {
                                'inscription_id': insc.get('id') or insc.get('inscription_id'),
                                'inscription_number': insc.get('number') or insc.get('inscription_number'),
                                'content_type': insc.get('content_type') or insc.get('mime_type'),
                                'genesis_address': insc.get('genesis_address') or insc.get('address'),
                                'genesis_tx': insc.get('genesis_transaction') or insc.get('genesis_tx_id'),
                                'genesis_block': insc.get('genesis_block_height'),
                                'sat_ordinal': insc.get('sat_ordinal'),
                                'platform': 'Bitcoin Ordinals',
                            }

                            # Try to get content preview
                            if ordinal['inscription_id']:
                                ordinal['content_url'] = f"https://ordinals.com/content/{ordinal['inscription_id']}"
                                ordinal['preview_url'] = f"https://ordinals.com/preview/{ordinal['inscription_id']}"

                            results['owned_ordinals'].append(ordinal)

                        results['stats']['total_inscriptions'] = len(results['owned_ordinals'])

                        # Check if any were created by this address
                        for ordinal in results['owned_ordinals']:
                            if ordinal.get('genesis_address') == address:
                                results['inscriptions'].append(ordinal)

                        results['stats']['inscriptions_created'] = len(results['inscriptions'])
                        break  # Success

                except requests.Timeout:
                    logger.warning(f"Ordinals API timeout: {api_url}")
                    continue
                except Exception as e:
                    logger.warning(f"Ordinals API error ({api_url}): {e}")
                    continue

        except Exception as e:
            logger.error(f"Bitcoin ordinals scan error: {e}")
            results['error'] = str(e)

        return results

    def scan_tezos_wallet(self, address: str, scan_collectors: bool = True) -> Dict:
        """
        Scan Tezos wallet using TzKT API (free, no key required)
        Full support: mints, transfers, collectors, platform detection

        Args:
            address: Tezos address (tz1...) - CASE SENSITIVE
            scan_collectors: Whether to track collectors via transfer history

        Returns:
            Scan results with mints, transfers, collectors
        """
        logger.info(f"Scanning Tezos wallet: {address}")

        results = {
            'address': address,  # Preserve case - Tezos is case-sensitive
            'network': 'tezos',
            'scan_date': datetime.utcnow().isoformat(),
            'minted_nfts': [],
            'owned_nfts': [],
            'collectors': [],
            'transfers': [],
            'stats': {}
        }

        try:
            base_url = "https://api.tzkt.io/v1"

            # 1. Get tokens created by this address
            logger.info("Fetching minted tokens...")
            response = requests.get(
                f"{base_url}/tokens",
                params={
                    'creator': address,
                    'limit': 200,
                    'sort.desc': 'id'
                },
                timeout=30
            )

            if response.status_code == 200:
                tokens = response.json()

                for token in tokens:
                    contract_addr = token.get('contract', {}).get('address')
                    nft = {
                        'contract_address': contract_addr,
                        'token_id': token.get('tokenId'),
                        'name': token.get('metadata', {}).get('name'),
                        'description': token.get('metadata', {}).get('description'),
                        'image': token.get('metadata', {}).get('displayUri') or token.get('metadata', {}).get('artifactUri'),
                        'platform': self._identify_platform(contract_addr, 'tezos') if contract_addr else 'Tezos',
                        'total_supply': token.get('totalSupply'),
                        'first_level': token.get('firstLevel'),
                    }
                    results['minted_nfts'].append(nft)

                results['stats']['total_minted'] = len(results['minted_nfts'])
                logger.info(f"Found {len(results['minted_nfts'])} minted tokens")

            # 2. Track collectors via multiple methods for comprehensive coverage
            if scan_collectors:
                logger.info("Tracking collectors comprehensively...")
                all_collectors = {}
                all_transfers = []

                # Method A: Get direct transfers FROM the artist (sales/gifts)
                try:
                    transfers_resp = requests.get(
                        f"{base_url}/tokens/transfers",
                        params={
                            'from': address,
                            'limit': 500,
                            'sort.desc': 'level'
                        },
                        timeout=60
                    )

                    if transfers_resp.status_code == 200:
                        direct_transfers = transfers_resp.json()
                        logger.info(f"Found {len(direct_transfers)} direct transfers from artist")

                        for transfer in direct_transfers:
                            to_addr = transfer.get('to', {}).get('address') if transfer.get('to') else None
                            token = transfer.get('token', {})
                            contract = token.get('contract', {}).get('address') if token.get('contract') else None
                            token_id = token.get('tokenId')

                            if not to_addr or to_addr == address:
                                continue

                            # Record transfer
                            all_transfers.append({
                                'contract': contract,
                                'token_id': token_id,
                                'from': address,
                                'to': to_addr,
                                'tx_hash': transfer.get('transactionId'),
                                'level': transfer.get('level'),
                                'timestamp': transfer.get('timestamp'),
                                'is_mint': False,
                            })

                            # Track collector
                            if to_addr not in all_collectors:
                                all_collectors[to_addr] = {
                                    'address': to_addr,
                                    'nfts_acquired': [],
                                    'total_pieces': 0,
                                    'first_acquisition_level': transfer.get('level'),
                                    'first_acquisition_time': transfer.get('timestamp'),
                                    'source': 'direct_transfer'
                                }

                            all_collectors[to_addr]['nfts_acquired'].append({
                                'contract': contract,
                                'token_id': token_id,
                                'level': transfer.get('level'),
                                'name': token.get('metadata', {}).get('name') if token.get('metadata') else None,
                            })
                            all_collectors[to_addr]['total_pieces'] += 1

                except requests.RequestException as e:
                    logger.warning(f"Failed to get direct transfers: {e}")

                # Method B: Get current holders of minted tokens (paginated)
                logger.info("Checking current token holders...")
                tokens_checked = 0
                max_tokens = 500

                for mint in results['minted_nfts'][:max_tokens]:
                    contract = mint.get('contract_address')
                    token_id = mint.get('token_id')

                    if not contract or token_id is None:
                        continue

                    try:
                        # Get current holders of this token
                        holders_resp = requests.get(
                            f"{base_url}/tokens/balances",
                            params={
                                'token.contract': contract,
                                'token.tokenId': token_id,
                                'balance.gt': 0,
                                'limit': 100
                            },
                            timeout=15
                        )

                        if holders_resp.status_code == 200:
                            holders = holders_resp.json()

                            for holder in holders:
                                holder_addr = holder.get('account', {}).get('address')
                                if holder_addr and holder_addr != address:
                                    if holder_addr not in all_collectors:
                                        all_collectors[holder_addr] = {
                                            'address': holder_addr,
                                            'nfts_acquired': [],
                                            'total_pieces': 0,
                                            'first_acquisition_level': None,
                                            'first_acquisition_time': None,
                                            'source': 'current_holder'
                                        }

                                    # Add this token if not already tracked
                                    existing_tokens = [n.get('contract') + str(n.get('token_id'))
                                                      for n in all_collectors[holder_addr]['nfts_acquired']]
                                    token_key = str(contract) + str(token_id)

                                    if token_key not in existing_tokens:
                                        all_collectors[holder_addr]['nfts_acquired'].append({
                                            'contract': contract,
                                            'token_id': token_id,
                                            'level': None,
                                            'name': mint.get('name'),
                                        })
                                        all_collectors[holder_addr]['total_pieces'] += 1

                        tokens_checked += 1
                        if tokens_checked % 100 == 0:
                            logger.info(f"Checked {tokens_checked} tokens, found {len(all_collectors)} collectors")

                    except requests.RequestException as e:
                        continue  # Skip this token on error

                results['collectors'] = list(all_collectors.values())
                results['transfers'] = all_transfers
                results['stats']['unique_collectors'] = len(all_collectors)
                results['stats']['total_transfers'] = len(all_transfers)
                logger.info(f"Found {len(all_collectors)} unique collectors from {len(all_transfers)} transfers")

            # 3. Get tokens currently owned
            logger.info("Fetching owned tokens...")
            response = requests.get(
                f"{base_url}/tokens/balances",
                params={
                    'account': address,
                    'balance.gt': 0,
                    'limit': 100,
                    'sort.desc': 'id'
                },
                timeout=30
            )

            if response.status_code == 200:
                balances = response.json()

                for balance in balances:
                    token = balance.get('token', {})
                    contract_addr = token.get('contract', {}).get('address')
                    nft = {
                        'contract_address': contract_addr,
                        'token_id': token.get('tokenId'),
                        'name': token.get('metadata', {}).get('name'),
                        'balance': balance.get('balance'),
                        'platform': self._identify_platform(contract_addr, 'tezos') if contract_addr else 'Tezos',
                    }
                    results['owned_nfts'].append(nft)

                results['stats']['total_owned'] = len(results['owned_nfts'])

        except Exception as e:
            logger.error(f"Tezos scan error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results['error'] = str(e)

        logger.info(f"Tezos scan complete: {results['stats']}")
        return results

    def scan_wallet(self, address: str, networks: List[str] = None) -> Dict:
        """
        Scan wallet across detected or specified networks

        Args:
            address: Wallet address
            networks: Optional list of networks to scan (auto-detects if None)

        Returns:
            Combined scan results from all networks
        """
        if networks is None:
            networks = self.detect_all_networks(address)

        if not networks:
            return {
                'error': f"Could not detect blockchain for address: {address}",
                'address': address,
            }

        results = {
            'address': address,
            'networks_scanned': networks,
            'scan_date': datetime.utcnow().isoformat(),
            'network_results': {},
            'combined_stats': {
                'total_minted': 0,
                'total_owned': 0,
                'unique_collectors': 0,
            }
        }

        for network in networks:
            logger.info(f"Scanning {network} for {address[:16]}...")

            try:
                if network == 'ethereum':
                    network_result = self.scan_ethereum_wallet(address)
                elif network == 'polygon':
                    network_result = self.scan_polygon_wallet(address)
                elif network == 'tezos':
                    network_result = self.scan_tezos_wallet(address)
                elif network == 'solana':
                    network_result = self.scan_solana_wallet(address)
                elif network == 'bitcoin':
                    network_result = self.scan_bitcoin_ordinals(address)
                else:
                    network_result = {'error': f'Network {network} not yet supported'}

                results['network_results'][network] = network_result

                # Aggregate stats
                if 'stats' in network_result:
                    stats = network_result['stats']
                    results['combined_stats']['total_minted'] += stats.get('total_minted', 0)
                    results['combined_stats']['total_owned'] += stats.get('total_owned', 0)
                    results['combined_stats']['unique_collectors'] += stats.get('unique_collectors', 0)

            except Exception as e:
                logger.error(f"Error scanning {network}: {e}")
                results['network_results'][network] = {'error': str(e)}

        return results

    def scan_polygon_wallet(self, address: str) -> Dict:
        """Scan Polygon wallet (same as Ethereum but different network)"""
        logger.info(f"Scanning Polygon wallet: {address}")

        # Use Polygon-specific parser
        results = {
            'address': address,
            'network': 'polygon',
            'scan_date': datetime.utcnow().isoformat(),
            'minted_nfts': [],
            'owned_nfts': [],
            'stats': {'note': 'Polygon scanning uses same logic as Ethereum'}
        }

        # Polygon scanning follows same pattern as Ethereum
        # but with polygon-specific RPC providers
        try:
            parser = self.polygon_parser
            mints = parser.get_mints_by_address(address, from_block=0)
            results['minted_nfts'] = mints[:20]
            results['stats']['total_minted'] = len(mints)
        except Exception as e:
            logger.error(f"Polygon scan error: {e}")
            results['error'] = str(e)

        return results

    def find_collector_interactions(self, artist_address: str) -> Dict:
        """
        Find interactions between collectors of the same artist

        Discovers:
        - Collectors who own multiple pieces
        - Transfers between collectors
        - Collector "communities"

        Args:
            artist_address: Artist's wallet address

        Returns:
            Collector interaction analysis
        """
        logger.info(f"Analyzing collector interactions for {artist_address}")

        # First, scan the artist's wallet
        scan_results = self.scan_wallet(artist_address)

        all_collectors = {}
        collector_connections = []

        # Process results from each network
        for network, result in scan_results.get('network_results', {}).items():
            collectors = result.get('collectors', [])

            for collector in collectors:
                addr = collector['address']

                if addr not in all_collectors:
                    all_collectors[addr] = {
                        'address': addr,
                        'networks': [],
                        'total_pieces': 0,
                        'nfts': [],
                    }

                all_collectors[addr]['networks'].append(network)
                all_collectors[addr]['total_pieces'] += collector.get('total_pieces', 0)
                all_collectors[addr]['nfts'].extend(collector.get('nfts_acquired', []))

        # Identify super collectors (multiple pieces)
        super_collectors = [
            c for c in all_collectors.values()
            if c['total_pieces'] >= 2
        ]

        # Find connections (collectors who share NFTs from same collection)
        collections = {}
        for addr, collector in all_collectors.items():
            for nft in collector['nfts']:
                contract = nft.get('contract')
                if contract:
                    if contract not in collections:
                        collections[contract] = set()
                    collections[contract].add(addr)

        # Collectors connected through same collection
        for contract, collectors_in_collection in collections.items():
            if len(collectors_in_collection) >= 2:
                collector_connections.append({
                    'contract': contract,
                    'collectors': list(collectors_in_collection),
                    'connection_type': 'same_collection'
                })

        return {
            'artist_address': artist_address,
            'total_collectors': len(all_collectors),
            'super_collectors': super_collectors,
            'collector_connections': collector_connections,
            'all_collectors': list(all_collectors.values()),
        }

    def save_scan_to_db(self, scan_results: Dict, address_id: int = None) -> bool:
        """
        Save scan results to blockchain database

        Args:
            scan_results: Results from scan_wallet()
            address_id: Optional tracked_addresses ID

        Returns:
            Success boolean
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            address = scan_results['address']

            # Get or create tracked address (case-insensitive lookup)
            if not address_id:
                cursor.execute(
                    'SELECT id FROM tracked_addresses WHERE LOWER(address) = LOWER(?)',
                    (address,)
                )
                result = cursor.fetchone()

                if result:
                    address_id = result['id']
                else:
                    # Detect network
                    network, _ = self.detect_blockchain(address)

                    # Normalize: lowercase for Ethereum, preserve case for Tezos (case-sensitive)
                    normalized_address = address.lower() if network == 'ethereum' else address

                    cursor.execute('''
                        INSERT INTO tracked_addresses (address, network, address_type, label)
                        VALUES (?, ?, 'wallet', 'Scanned Wallet')
                    ''', (normalized_address, network))
                    address_id = cursor.lastrowid

            # Save NFT mints
            for network, result in scan_results.get('network_results', {}).items():
                for nft in result.get('minted_nfts', []):
                    cursor.execute('''
                        INSERT OR REPLACE INTO nft_mints
                        (address_id, token_id, contract_address, mint_tx_hash,
                         mint_block_number, token_uri, name, description, platform)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        address_id,
                        str(nft.get('token_id')),
                        nft.get('contract_address'),
                        nft.get('tx_hash'),
                        nft.get('block_number'),
                        nft.get('token_uri'),
                        nft.get('name'),
                        nft.get('description'),
                        nft.get('platform') or network,
                    ))

                    nft_mint_id = cursor.lastrowid

                    # Save collectors
                    for collector in result.get('collectors', []):
                        for acquired_nft in collector.get('nfts_acquired', []):
                            if acquired_nft.get('contract') == nft.get('contract_address'):
                                cursor.execute('''
                                    INSERT OR IGNORE INTO collectors
                                    (collector_address, network, nft_mint_id)
                                    VALUES (?, ?, ?)
                                ''', (
                                    collector['address'],
                                    network,
                                    nft_mint_id,
                                ))

            # Update last synced
            cursor.execute('''
                UPDATE tracked_addresses
                SET last_synced = ?
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), address_id))

            conn.commit()
            conn.close()

            logger.info(f"Saved scan results for {address}")
            return True

        except Exception as e:
            logger.error(f"Failed to save scan: {e}")
            return False

    def resolve_tezos_domain(self, domain: str) -> Optional[str]:
        """
        Resolve a Tezos domain (like giselx.tez) to an address using TzKT API

        Args:
            domain: Tezos domain (e.g., "giselx.tez")

        Returns:
            Resolved Tezos address or None
        """
        try:
            # TzKT provides domain resolution
            base_url = "https://api.tzkt.io/v1"

            # Try domains endpoint
            response = requests.get(
                f"{base_url}/domains",
                params={'name': domain},
                timeout=15
            )

            if response.status_code == 200:
                domains = response.json()
                if domains and len(domains) > 0:
                    owner = domains[0].get('owner', {}).get('address')
                    logger.info(f"Resolved {domain} -> {owner}")
                    return owner

            return None

        except Exception as e:
            logger.warning(f"Failed to resolve Tezos domain {domain}: {e}")
            return None

    def find_cross_chain_overlaps(self, artist_addresses: List[str]) -> Dict:
        """
        Find collectors who appear on multiple chains, indicating same person

        This detects collectors who:
        1. Have matching ENS/Tezos domains
        2. Collected from same artist on multiple chains
        3. Have linked social profiles (Twitter)

        Args:
            artist_addresses: List of artist's addresses across chains

        Returns:
            Dict with overlap analysis and unified collector profiles
        """
        logger.info(f"Finding cross-chain overlaps for {len(artist_addresses)} addresses")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        results = {
            'overlaps': [],
            'eth_only_collectors': [],
            'tezos_only_collectors': [],
            'multi_chain_collectors': [],
            'stats': {}
        }

        try:
            # Get all collectors for this artist by network
            eth_collectors = set()
            tezos_collectors = set()

            for address in artist_addresses:
                network, _ = self.detect_blockchain(address)

                # Get address_id (case-insensitive for ETH, case-sensitive for Tezos)
                if network == 'ethereum':
                    cursor.execute('''
                        SELECT id FROM tracked_addresses WHERE LOWER(address) = LOWER(?)
                    ''', (address,))
                else:
                    cursor.execute('''
                        SELECT id FROM tracked_addresses WHERE address = ?
                    ''', (address,))

                addr_row = cursor.fetchone()
                if not addr_row:
                    continue

                address_id = addr_row['id']

                # Get collectors for this address
                cursor.execute('''
                    SELECT DISTINCT c.collector_address, c.network
                    FROM collectors c
                    JOIN nft_mints m ON c.nft_mint_id = m.id
                    WHERE m.address_id = ?
                ''', (address_id,))

                for row in cursor.fetchall():
                    if row['network'] == 'ethereum':
                        eth_collectors.add(row['collector_address'])
                    elif row['network'] == 'tezos':
                        tezos_collectors.add(row['collector_address'])

            results['stats']['eth_collectors'] = len(eth_collectors)
            results['stats']['tezos_collectors'] = len(tezos_collectors)

            # Method 1: Check for Tezos domain -> ETH address resolution patterns
            # Collectors with similar names across chains
            potential_overlaps = []

            # Try to resolve Tezos collector addresses to domains
            for tez_addr in list(tezos_collectors)[:50]:  # Limit API calls
                try:
                    # Query TzKT for domain associated with this address
                    response = requests.get(
                        "https://api.tzkt.io/v1/domains",
                        params={'owner': tez_addr},
                        timeout=10
                    )

                    if response.status_code == 200:
                        domains = response.json()
                        if domains:
                            domain_name = domains[0].get('name', '')
                            # Extract base name (remove .tez)
                            base_name = domain_name.replace('.tez', '').lower()

                            # Check if any ETH collector has matching ENS or pattern
                            for eth_addr in eth_collectors:
                                # Could extend to ENS lookup here
                                potential_overlaps.append({
                                    'tezos_address': tez_addr,
                                    'tezos_domain': domain_name,
                                    'base_name': base_name,
                                    'match_type': 'domain_pattern',
                                    'confidence': 0.5
                                })

                except Exception as e:
                    continue

            # Method 2: Check for collectors active in both networks around same time
            # This suggests same person operating on both chains
            cursor.execute('''
                SELECT c.collector_address, c.network, m.contract_address, m.name,
                       COUNT(*) as pieces_collected
                FROM collectors c
                JOIN nft_mints m ON c.nft_mint_id = m.id
                JOIN tracked_addresses ta ON m.address_id = ta.id
                WHERE ta.address IN ({})
                GROUP BY c.collector_address, c.network
                ORDER BY pieces_collected DESC
            '''.format(','.join('?' * len(artist_addresses))), tuple(artist_addresses))

            collector_activity = {}
            for row in cursor.fetchall():
                addr = row['collector_address']
                network = row['network']
                pieces = row['pieces_collected']

                if addr not in collector_activity:
                    collector_activity[addr] = {'ethereum': 0, 'tezos': 0}
                collector_activity[addr][network] = pieces

            # Find collectors active on both chains
            for addr, activity in collector_activity.items():
                if activity.get('ethereum', 0) > 0 and activity.get('tezos', 0) > 0:
                    results['multi_chain_collectors'].append({
                        'address': addr,
                        'eth_pieces': activity['ethereum'],
                        'tezos_pieces': activity['tezos'],
                        'total_pieces': activity['ethereum'] + activity['tezos']
                    })

            # Categorize single-chain collectors
            for addr in eth_collectors:
                if not any(c['address'] == addr for c in results['multi_chain_collectors']):
                    results['eth_only_collectors'].append(addr)

            for addr in tezos_collectors:
                if not any(c['address'] == addr for c in results['multi_chain_collectors']):
                    results['tezos_only_collectors'].append(addr)

            results['overlaps'] = potential_overlaps
            results['stats']['multi_chain_count'] = len(results['multi_chain_collectors'])
            results['stats']['potential_overlaps'] = len(potential_overlaps)

            logger.info(f"Found {len(results['multi_chain_collectors'])} multi-chain collectors, "
                       f"{len(potential_overlaps)} potential domain overlaps")

        except Exception as e:
            logger.error(f"Cross-chain overlap detection error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results['error'] = str(e)
        finally:
            conn.close()

        return results

    def get_unified_artist_overview(self, addresses: List[str]) -> Dict:
        """
        Get a unified overview of an artist's presence across all chains

        Args:
            addresses: List of artist's wallet addresses on different chains

        Returns:
            Unified view of mints, collectors, and activity across chains
        """
        logger.info(f"Building unified artist overview for {len(addresses)} addresses")

        overview = {
            'addresses': [],
            'networks': set(),
            'total_mints': 0,
            'total_collectors': 0,
            'mints_by_network': {},
            'collectors_by_network': {},
            'top_collectors': [],
            'platforms': {}
        }

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            for address in addresses:
                network, _ = self.detect_blockchain(address)
                overview['networks'].add(network)

                # Get address from DB
                if network == 'ethereum':
                    cursor.execute(
                        'SELECT id FROM tracked_addresses WHERE LOWER(address) = LOWER(?)',
                        (address,)
                    )
                else:
                    cursor.execute(
                        'SELECT id FROM tracked_addresses WHERE address = ?',
                        (address,)
                    )

                addr_row = cursor.fetchone()
                if not addr_row:
                    continue

                address_id = addr_row['id']

                # Get mint count
                cursor.execute('''
                    SELECT COUNT(*) as count, platform
                    FROM nft_mints WHERE address_id = ?
                    GROUP BY platform
                ''', (address_id,))

                network_mints = 0
                for row in cursor.fetchall():
                    network_mints += row['count']
                    platform = row['platform'] or network
                    overview['platforms'][platform] = overview['platforms'].get(platform, 0) + row['count']

                overview['mints_by_network'][network] = network_mints
                overview['total_mints'] += network_mints

                # Get collector count
                cursor.execute('''
                    SELECT COUNT(DISTINCT collector_address) as count
                    FROM collectors c
                    JOIN nft_mints m ON c.nft_mint_id = m.id
                    WHERE m.address_id = ?
                ''', (address_id,))

                collector_count = cursor.fetchone()['count']
                overview['collectors_by_network'][network] = collector_count
                overview['total_collectors'] += collector_count

                overview['addresses'].append({
                    'address': address,
                    'network': network,
                    'mints': network_mints,
                    'collectors': collector_count
                })

            # Get top collectors across all networks
            cursor.execute('''
                SELECT c.collector_address, c.network, COUNT(*) as pieces
                FROM collectors c
                JOIN nft_mints m ON c.nft_mint_id = m.id
                JOIN tracked_addresses ta ON m.address_id = ta.id
                WHERE ta.address IN ({})
                GROUP BY c.collector_address, c.network
                ORDER BY pieces DESC
                LIMIT 20
            '''.format(','.join('?' * len(addresses))), tuple(addresses))

            for row in cursor.fetchall():
                overview['top_collectors'].append({
                    'address': row['collector_address'],
                    'network': row['network'],
                    'pieces': row['pieces']
                })

            overview['networks'] = list(overview['networks'])

        except Exception as e:
            logger.error(f"Unified overview error: {e}")
            overview['error'] = str(e)
        finally:
            conn.close()

        return overview


# CLI Interface
if __name__ == '__main__':
    import sys

    scanner = WalletScanner()

    if len(sys.argv) < 2:
        print("""
Multi-Chain Wallet Scanner

Usage:
  python wallet_scanner.py detect <address>           Detect blockchain
  python wallet_scanner.py scan <address>             Full wallet scan
  python wallet_scanner.py collectors <address>       Analyze collector interactions

Examples:
  python wallet_scanner.py detect 0x1234...           # Ethereum
  python wallet_scanner.py detect tz1abc...           # Tezos
  python wallet_scanner.py scan 0x1234...             # Scan ETH + Polygon
  python wallet_scanner.py collectors 0x1234...       # Find collector network
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'detect':
        if len(sys.argv) < 3:
            print("Usage: python wallet_scanner.py detect <address>")
            sys.exit(1)

        address = sys.argv[2]
        network, confidence = scanner.detect_blockchain(address)
        all_networks = scanner.detect_all_networks(address)

        print(f"\nAddress: {address}")
        print(f"Detected Network: {network} (confidence: {confidence:.0%})")
        print(f"All Possible Networks: {', '.join(all_networks)}")

    elif command == 'scan':
        if len(sys.argv) < 3:
            print("Usage: python wallet_scanner.py scan <address>")
            sys.exit(1)

        address = sys.argv[2]

        print(f"\nScanning wallet: {address}")
        print("=" * 60)

        results = scanner.scan_wallet(address)

        print(f"\nNetworks Scanned: {', '.join(results['networks_scanned'])}")
        print(f"\n--- Combined Stats ---")
        for key, value in results['combined_stats'].items():
            print(f"  {key}: {value}")

        for network, result in results.get('network_results', {}).items():
            print(f"\n--- {network.upper()} ---")

            if 'error' in result:
                print(f"  Error: {result['error']}")
                continue

            mints = result.get('minted_nfts', [])
            print(f"  Minted NFTs: {len(mints)}")

            for nft in mints[:5]:
                name = nft.get('name') or f"Token #{nft.get('token_id')}"
                platform = nft.get('platform', 'Unknown')
                print(f"    - {name} ({platform})")

            if len(mints) > 5:
                print(f"    ... and {len(mints) - 5} more")

            collectors = result.get('collectors', [])
            if collectors:
                print(f"\n  Collectors: {len(collectors)}")
                for c in collectors[:3]:
                    print(f"    - {c['address'][:16]}... ({c['total_pieces']} pieces)")

    elif command == 'collectors':
        if len(sys.argv) < 3:
            print("Usage: python wallet_scanner.py collectors <address>")
            sys.exit(1)

        address = sys.argv[2]

        print(f"\nAnalyzing collectors for: {address}")
        print("=" * 60)

        analysis = scanner.find_collector_interactions(address)

        print(f"\nTotal Collectors: {analysis['total_collectors']}")
        print(f"Super Collectors (2+ pieces): {len(analysis['super_collectors'])}")

        if analysis['super_collectors']:
            print("\n--- Super Collectors ---")
            for sc in analysis['super_collectors'][:5]:
                print(f"  {sc['address'][:20]}... - {sc['total_pieces']} pieces")

        if analysis['collector_connections']:
            print(f"\n--- Collector Connections ---")
            for conn in analysis['collector_connections'][:5]:
                print(f"  Contract {conn['contract'][:20]}... connects {len(conn['collectors'])} collectors")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
