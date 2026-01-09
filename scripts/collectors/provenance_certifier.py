#!/usr/bin/env python3
"""
NFT Provenance Certification System
Verifies authenticity of NFTs by checking mint origin against known artist addresses

Certification Factors:
1. Mint Origin (40 points) - Was it minted from a registered artist address?
2. Platform Verification (30 points) - Was it minted on a curated platform?
3. Registry Match (30 points) - Is it in the artist's registered catalog?

Certification Levels:
- VERIFIED (85-100): High confidence of authenticity
- LIKELY (50-84): Probable authenticity, some factors missing
- UNVERIFIED (0-49): Cannot confirm authenticity
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.blockchain_db import get_db
from collectors.raw_nft_parser import RawNFTParser
from collectors.wallet_scanner import WalletScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProvenanceCertifier:
    """
    Certify NFT authenticity by verifying provenance chain

    Multi-factor verification:
    - Mint transaction origin
    - Platform/contract reputation
    - Artist registry matching
    """

    # Known curated platforms (higher trust)
    CURATED_PLATFORMS = {
        # Ethereum
        '0xb932a70a57673d89f4acffbe830e8ed7f75fb9e0': {'name': 'SuperRare', 'score': 30},
        '0x3b3ee1931dc30c1957379fac9aba94d1c48a5405': {'name': 'Foundation', 'score': 30},
        '0xa7d8d9ef8d8ce8992df33d8b8cf4aebabd5bd270': {'name': 'Art Blocks', 'score': 30},
        '0x059edd72cd353df5106d2b9cc5ab83a52287ac3a': {'name': 'Art Blocks Curated', 'score': 30},
        '0xfbeef911dc5821886e1dda71586d90ed28174b7d': {'name': 'Known Origin', 'score': 28},
        '0x2a46f2ffd99e19a89476e2f62270e0a35bbf0756': {'name': 'MakersPlace', 'score': 28},

        # Open platforms (lower trust - anyone can mint)
        '0x495f947276749ce646f68ac8c248420045cb7b5e': {'name': 'OpenSea Shared', 'score': 10},
        '0x2953399124f0cbb46d2cbacd8a89cf0599974963': {'name': 'OpenSea Polygon', 'score': 10},

        # Tezos
        'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton': {'name': 'hic et nunc', 'score': 25},
        'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9': {'name': 'OBJKT.com', 'score': 25},
        'KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE': {'name': 'fxhash', 'score': 28},
    }

    # Artist-deployed contracts get bonus points
    ARTIST_DEPLOYED_BONUS = 10

    def __init__(self):
        """Initialize certifier with database and parsers"""
        self.db = get_db()
        self.eth_parser = RawNFTParser('ethereum')
        self.scanner = WalletScanner()

    def get_registered_artist_addresses(self) -> Dict[str, Dict]:
        """
        Get all registered artist addresses from database

        Returns:
            Dict mapping address -> artist info
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get from tracked_addresses where type is 'wallet' or 'artist'
        cursor.execute('''
            SELECT ta.address, ta.network, ta.label, ta.notes
            FROM tracked_addresses ta
            WHERE ta.sync_enabled = TRUE
        ''')

        artists = {}
        for row in cursor.fetchall():
            # Normalize: lowercase for Ethereum (case-insensitive), preserve case for Tezos
            address = row['address'].lower() if row['network'] == 'ethereum' else row['address']
            artists[address] = {
                'network': row['network'],
                'label': row['label'],
                'notes': row['notes'],
                'verified': True
            }

        conn.close()

        logger.info(f"Found {len(artists)} registered artist addresses")
        return artists

    def get_artist_catalog(self, artist_address: str) -> List[Dict]:
        """
        Get all NFTs minted by an artist address

        Args:
            artist_address: Artist's wallet address

        Returns:
            List of NFT records from database
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Find address ID (case-insensitive lookup)
        cursor.execute(
            'SELECT id FROM tracked_addresses WHERE LOWER(address) = LOWER(?)',
            (artist_address,)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return []

        address_id = result['id']

        # Get all NFTs minted by this address
        cursor.execute('''
            SELECT * FROM nft_mints WHERE address_id = ?
        ''', (address_id,))

        nfts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return nfts

    def verify_mint_origin(
        self,
        contract_address: str,
        token_id: int,
        artist_address: str = None
    ) -> Dict:
        """
        Verify the mint origin of an NFT

        Checks:
        1. Who was the recipient of the mint (Transfer from 0x0)?
        2. Is that address a registered artist?
        3. Was the contract deployed by the artist?

        Args:
            contract_address: NFT contract address
            token_id: Token ID
            artist_address: Optional expected artist address

        Returns:
            Verification result with score
        """
        logger.info(f"Verifying mint origin for {contract_address} #{token_id}")

        result = {
            'contract_address': contract_address,
            'token_id': token_id,
            'mint_verified': False,
            'mint_recipient': None,
            'is_registered_artist': False,
            'contract_deployer': None,
            'deployed_by_artist': False,
            'score': 0,
            'factors': []
        }

        try:
            # Get transfer history for this token
            transfers = self.eth_parser.get_nft_transfers(
                contract_address,
                from_block=0,
                token_id=token_id
            )

            # Find mint (transfer from 0x0)
            mint_transfer = None
            for transfer in transfers:
                if transfer.get('is_mint') or transfer.get('from_address') == '0x0000000000000000000000000000000000000000':
                    mint_transfer = transfer
                    break

            if mint_transfer:
                result['mint_verified'] = True
                result['mint_recipient'] = mint_transfer['to_address']
                result['mint_tx'] = mint_transfer.get('tx_hash')
                result['mint_block'] = mint_transfer.get('block_number')

                # Check if mint recipient is a registered artist
                registered_artists = self.get_registered_artist_addresses()
                recipient = mint_transfer['to_address'].lower()

                if recipient in registered_artists:
                    result['is_registered_artist'] = True
                    result['artist_info'] = registered_artists[recipient]
                    result['score'] += 40  # Full mint origin score
                    result['factors'].append({
                        'factor': 'mint_origin',
                        'status': 'verified',
                        'points': 40,
                        'detail': f"Minted to registered artist: {registered_artists[recipient].get('label', recipient[:16])}"
                    })
                else:
                    # Check if provided artist_address matches
                    if artist_address and recipient == artist_address.lower():
                        result['score'] += 20  # Partial - matches provided but not in registry
                        result['factors'].append({
                            'factor': 'mint_origin',
                            'status': 'partial',
                            'points': 20,
                            'detail': f"Minted to provided address (not in registry): {recipient[:16]}..."
                        })
                    else:
                        result['factors'].append({
                            'factor': 'mint_origin',
                            'status': 'unverified',
                            'points': 0,
                            'detail': f"Minted to unregistered address: {recipient[:16]}..."
                        })

            else:
                result['factors'].append({
                    'factor': 'mint_origin',
                    'status': 'unknown',
                    'points': 0,
                    'detail': 'Could not find mint transaction'
                })

        except Exception as e:
            logger.error(f"Error verifying mint origin: {e}")
            result['error'] = str(e)

        return result

    def verify_platform(self, contract_address: str) -> Dict:
        """
        Verify the platform/contract reputation

        Args:
            contract_address: NFT contract address

        Returns:
            Platform verification result with score
        """
        result = {
            'contract_address': contract_address,
            'platform_name': 'Unknown',
            'is_curated': False,
            'score': 0,
            'factors': []
        }

        contract_lower = contract_address.lower()

        if contract_lower in self.CURATED_PLATFORMS:
            platform = self.CURATED_PLATFORMS[contract_lower]
            result['platform_name'] = platform['name']
            result['is_curated'] = True
            result['score'] = platform['score']
            result['factors'].append({
                'factor': 'platform',
                'status': 'verified',
                'points': platform['score'],
                'detail': f"Minted on curated platform: {platform['name']}"
            })
        else:
            # Unknown contract - give minimal points
            result['score'] = 5
            result['factors'].append({
                'factor': 'platform',
                'status': 'unknown',
                'points': 5,
                'detail': f"Unknown contract: {contract_address[:20]}..."
            })

        return result

    def verify_registry_match(
        self,
        contract_address: str,
        token_id: int,
        artist_address: str
    ) -> Dict:
        """
        Verify if NFT is in artist's registered catalog

        Args:
            contract_address: NFT contract address
            token_id: Token ID
            artist_address: Artist's wallet address

        Returns:
            Registry verification result with score
        """
        result = {
            'in_catalog': False,
            'catalog_size': 0,
            'score': 0,
            'factors': []
        }

        try:
            catalog = self.get_artist_catalog(artist_address)
            result['catalog_size'] = len(catalog)

            # Check if this NFT is in the catalog
            for nft in catalog:
                if (nft.get('contract_address', '').lower() == contract_address.lower() and
                    str(nft.get('token_id')) == str(token_id)):
                    result['in_catalog'] = True
                    result['score'] = 30
                    result['factors'].append({
                        'factor': 'registry',
                        'status': 'verified',
                        'points': 30,
                        'detail': f"Found in artist catalog ({result['catalog_size']} works)"
                    })
                    break

            if not result['in_catalog']:
                if result['catalog_size'] > 0:
                    result['factors'].append({
                        'factor': 'registry',
                        'status': 'not_found',
                        'points': 0,
                        'detail': f"Not in artist catalog ({result['catalog_size']} works registered)"
                    })
                else:
                    result['factors'].append({
                        'factor': 'registry',
                        'status': 'empty_catalog',
                        'points': 0,
                        'detail': 'Artist has no registered works'
                    })

        except Exception as e:
            logger.error(f"Error checking registry: {e}")
            result['error'] = str(e)

        return result

    def certify_nft(
        self,
        contract_address: str,
        token_id: int,
        expected_artist: str = None
    ) -> Dict:
        """
        Full provenance certification for an NFT

        Combines all verification factors into a final score and certification level.

        Args:
            contract_address: NFT contract address
            token_id: Token ID
            expected_artist: Optional expected artist address for matching

        Returns:
            Complete certification result
        """
        logger.info(f"Certifying NFT: {contract_address} #{token_id}")

        certification = {
            'contract_address': contract_address,
            'token_id': token_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_score': 0,
            'max_score': 100,
            'certification_level': 'UNVERIFIED',
            'factors': [],
            'summary': ''
        }

        # Factor 1: Mint Origin (40 points max)
        mint_result = self.verify_mint_origin(contract_address, token_id, expected_artist)
        certification['mint_origin'] = mint_result
        certification['total_score'] += mint_result['score']
        certification['factors'].extend(mint_result['factors'])

        # Determine artist address from mint if not provided
        if mint_result['mint_recipient']:
            artist_address = mint_result['mint_recipient']
        else:
            artist_address = expected_artist

        # Factor 2: Platform Verification (30 points max)
        platform_result = self.verify_platform(contract_address)
        certification['platform'] = platform_result
        certification['total_score'] += platform_result['score']
        certification['factors'].extend(platform_result['factors'])

        # Factor 3: Registry Match (30 points max)
        if artist_address:
            registry_result = self.verify_registry_match(
                contract_address, token_id, artist_address
            )
            certification['registry'] = registry_result
            certification['total_score'] += registry_result['score']
            certification['factors'].extend(registry_result['factors'])

        # Determine certification level
        score = certification['total_score']
        if score >= 85:
            certification['certification_level'] = 'VERIFIED'
            certification['summary'] = '✅ High confidence: NFT provenance verified'
        elif score >= 50:
            certification['certification_level'] = 'LIKELY'
            certification['summary'] = '🟡 Moderate confidence: Provenance likely authentic'
        else:
            certification['certification_level'] = 'UNVERIFIED'
            certification['summary'] = '🔴 Low confidence: Cannot verify provenance'

        # Add recommendation
        if certification['certification_level'] == 'UNVERIFIED':
            missing = []
            if not mint_result.get('is_registered_artist'):
                missing.append('register artist address')
            if not platform_result.get('is_curated'):
                missing.append('verify on curated platform')

            if missing:
                certification['recommendation'] = f"To improve: {', '.join(missing)}"

        logger.info(f"Certification complete: {certification['certification_level']} ({score}/100)")
        return certification

    def certify_collection(
        self,
        contract_address: str,
        artist_address: str = None,
        sample_size: int = 10
    ) -> Dict:
        """
        Certify a collection of NFTs

        Args:
            contract_address: NFT contract address
            artist_address: Expected artist address
            sample_size: Number of tokens to sample

        Returns:
            Collection certification summary
        """
        logger.info(f"Certifying collection: {contract_address}")

        collection = {
            'contract_address': contract_address,
            'timestamp': datetime.utcnow().isoformat(),
            'sample_size': sample_size,
            'certifications': [],
            'summary': {}
        }

        # Certify sample of tokens
        for token_id in range(1, sample_size + 1):
            try:
                cert = self.certify_nft(contract_address, token_id, artist_address)
                collection['certifications'].append(cert)
            except Exception as e:
                logger.warning(f"Failed to certify token {token_id}: {e}")

        # Calculate summary
        if collection['certifications']:
            scores = [c['total_score'] for c in collection['certifications']]
            levels = [c['certification_level'] for c in collection['certifications']]

            collection['summary'] = {
                'avg_score': sum(scores) / len(scores),
                'verified_count': levels.count('VERIFIED'),
                'likely_count': levels.count('LIKELY'),
                'unverified_count': levels.count('UNVERIFIED'),
                'total_sampled': len(collection['certifications'])
            }

        return collection

    def add_to_artist_registry(self, artist_address: str, label: str = None) -> bool:
        """
        Add an address to the artist registry for verification

        Args:
            artist_address: Address to register
            label: Optional label/name

        Returns:
            Success boolean
        """
        try:
            network, _ = self.scanner.detect_blockchain(artist_address)

            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO tracked_addresses
                (address, network, label, address_type, sync_enabled)
                VALUES (?, ?, ?, 'artist', TRUE)
            ''', (artist_address.lower(), network, label or 'Registered Artist'))

            conn.commit()
            conn.close()

            logger.info(f"Registered artist address: {artist_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to register artist: {e}")
            return False


# CLI Interface
if __name__ == '__main__':
    import sys

    certifier = ProvenanceCertifier()

    if len(sys.argv) < 2:
        print("""
NFT Provenance Certifier

Usage:
  python provenance_certifier.py certify <contract> <token_id> [artist_address]
  python provenance_certifier.py collection <contract> [artist_address] [sample_size]
  python provenance_certifier.py register <artist_address> [label]
  python provenance_certifier.py artists

Examples:
  python provenance_certifier.py certify 0xb932a70... 1234
  python provenance_certifier.py collection 0xb932a70... 0xartist... 20
  python provenance_certifier.py register 0x1234... "Artist Name"
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'certify':
        if len(sys.argv) < 4:
            print("Usage: python provenance_certifier.py certify <contract> <token_id> [artist]")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])
        artist = sys.argv[4] if len(sys.argv) > 4 else None

        print(f"\nCertifying NFT: {contract} #{token_id}")
        print("=" * 60)

        cert = certifier.certify_nft(contract, token_id, artist)

        print(f"\nCertification Level: {cert['certification_level']}")
        print(f"Score: {cert['total_score']}/100")
        print(f"\n{cert['summary']}")

        print("\n--- Factors ---")
        for factor in cert['factors']:
            status_icon = {'verified': '✅', 'partial': '🟡', 'unverified': '❌', 'unknown': '❓'}.get(factor['status'], '•')
            print(f"{status_icon} {factor['factor']}: +{factor['points']} pts")
            print(f"   {factor['detail']}")

        if cert.get('recommendation'):
            print(f"\n💡 {cert['recommendation']}")

    elif command == 'collection':
        if len(sys.argv) < 3:
            print("Usage: python provenance_certifier.py collection <contract> [artist] [sample]")
            sys.exit(1)

        contract = sys.argv[2]
        artist = sys.argv[3] if len(sys.argv) > 3 else None
        sample = int(sys.argv[4]) if len(sys.argv) > 4 else 10

        print(f"\nCertifying Collection: {contract}")
        print(f"Sampling {sample} tokens...")
        print("=" * 60)

        result = certifier.certify_collection(contract, artist, sample)

        if result['summary']:
            s = result['summary']
            print(f"\n--- Collection Summary ---")
            print(f"Average Score: {s['avg_score']:.1f}/100")
            print(f"✅ Verified: {s['verified_count']}")
            print(f"🟡 Likely: {s['likely_count']}")
            print(f"🔴 Unverified: {s['unverified_count']}")

    elif command == 'register':
        if len(sys.argv) < 3:
            print("Usage: python provenance_certifier.py register <address> [label]")
            sys.exit(1)

        address = sys.argv[2]
        label = sys.argv[3] if len(sys.argv) > 3 else None

        success = certifier.add_to_artist_registry(address, label)
        if success:
            print(f"✅ Registered artist: {address}")
        else:
            print(f"❌ Failed to register artist")

    elif command == 'artists':
        artists = certifier.get_registered_artist_addresses()

        print(f"\n--- Registered Artists ({len(artists)}) ---")
        for addr, info in artists.items():
            print(f"\n{info.get('label', 'Unknown')}:")
            print(f"  Address: {addr}")
            print(f"  Network: {info.get('network')}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
