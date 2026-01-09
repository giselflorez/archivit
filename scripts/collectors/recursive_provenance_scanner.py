#!/usr/bin/env python3
"""
Recursive Provenance Scanner
============================

Multi-pass recursive system that uses social media as a provenance recovery layer
for blockchain art. Solves the "shared contract problem" where artists minted on
platform contracts and lost connection to their work.

The Problem:
- SuperRare v1, Foundation, OpenSea Storefront = SHARED contracts
- 10,000+ artists on ONE contract address
- Creator field shows PLATFORM wallet, not artist
- Platform dies = connection between artist and work is SEVERED
- Work may be "stuck" in platform escrow wallets
- Artists literally forgot works they made in 2020-2021

The Solution:
- Twitter posts ARE the provenance layer
- "Just minted on SuperRare!" + image + link = PROOF
- Collector comments = witnesses
- Timestamps predate any theft claims
- Recursive scraping recovers lost works

Architecture:
    Pass 1: Identity & Twitter Verification
    Pass 2: NFT Release Detection (mints, sales announcements)
    Pass 3: Collection Detection (purchases, acquisitions)
    Pass 4: Blockchain Cross-Reference & Anomaly Detection
    Pass 5: Platform Death Recovery (Wayback Machine integration)
    Pass 6: Image Matching (perceptual hash comparison)
"""

import logging
import sys
import re
import json
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecursiveProvenanceScanner:
    """
    Multi-pass recursive scanner that uses social media
    as a provenance recovery layer for blockchain art

    This is the "major solidifier" - proving artist association
    through social evidence when blockchain records are incomplete
    """

    # NFT Release Detection Patterns
    MINT_PATTERNS = [
        r'just minted',
        r'now available',
        r'now live',
        r'listed on',
        r'dropping today',
        r'dropping now',
        r'minted my',
        r'new piece on',
        r'new work on',
        r'excited to release',
        r'excited to drop',
        r'proud to present',
        r'available on',
        r'live on',
        r'up for auction',
        r'auction live',
        r'1/1 on',
        r'edition of \d+',
        r'editions available',
        r'/1 available',
        r'mint link',
        r'collect link',
        r'link in bio',
        r'first time minting',
        r'debut on',
        r'genesis piece',
        r'genesis drop',
    ]

    # Collection Detection Patterns
    COLLECT_PATTERNS = [
        r'just collected',
        r'just grabbed',
        r'had to grab',
        r'had to collect',
        r'couldn\'t resist',
        r'new addition',
        r'finally got',
        r'collected this',
        r'added to collection',
        r'welcome to my collection',
        r'honored to collect',
        r'proud to own',
        r'thank you for selling',
        r'congrats on the sale',
        r'gm .* collected',
    ]

    # Sale/Purchase Confirmation Patterns
    SALE_PATTERNS = [
        r'sold!',
        r'just sold',
        r'thank you .* for collecting',
        r'thank you .* for the collect',
        r'grateful .* collected',
        r'new collector',
        r'found a new home',
        r'went to',
        r'collected by',
        r'purchased by',
    ]

    # Platform Domains (including dead ones)
    PLATFORM_DOMAINS = {
        # Active Platforms
        'opensea.io': {'name': 'OpenSea', 'chain': 'multi', 'status': 'active'},
        'superrare.com': {'name': 'SuperRare', 'chain': 'ethereum', 'status': 'active'},
        'superrare.co': {'name': 'SuperRare', 'chain': 'ethereum', 'status': 'active'},
        'foundation.app': {'name': 'Foundation', 'chain': 'ethereum', 'status': 'active'},
        'rarible.com': {'name': 'Rarible', 'chain': 'multi', 'status': 'active'},
        'zora.co': {'name': 'Zora', 'chain': 'ethereum', 'status': 'active'},
        'niftygateway.com': {'name': 'Nifty Gateway', 'chain': 'ethereum', 'status': 'active'},
        'knownorigin.io': {'name': 'KnownOrigin', 'chain': 'ethereum', 'status': 'active'},
        'makersplace.com': {'name': 'MakersPlace', 'chain': 'ethereum', 'status': 'active'},
        'async.art': {'name': 'Async Art', 'chain': 'ethereum', 'status': 'active'},
        'async.market': {'name': 'Async Art', 'chain': 'ethereum', 'status': 'active'},
        '1stdibs.com': {'name': '1stDibs', 'chain': 'ethereum', 'status': 'active'},
        'manifold.xyz': {'name': 'Manifold', 'chain': 'ethereum', 'status': 'active'},
        'sound.xyz': {'name': 'Sound.xyz', 'chain': 'ethereum', 'status': 'active'},
        'catalog.works': {'name': 'Catalog', 'chain': 'ethereum', 'status': 'active'},

        # Tezos Platforms
        'objkt.com': {'name': 'objkt', 'chain': 'tezos', 'status': 'active'},
        'fxhash.xyz': {'name': 'fxhash', 'chain': 'tezos', 'status': 'active'},
        'teia.art': {'name': 'Teia', 'chain': 'tezos', 'status': 'active'},
        'versum.xyz': {'name': 'Versum', 'chain': 'tezos', 'status': 'active'},

        # Dead/Archived Platforms (CRITICAL for recovery)
        'hicetnunc.xyz': {'name': 'Hic Et Nunc', 'chain': 'tezos', 'status': 'dead', 'died': '2021-11'},
        'portion.io': {'name': 'Portion', 'chain': 'ethereum', 'status': 'uncertain'},
        'mintable.app': {'name': 'Mintable', 'chain': 'ethereum', 'status': 'reduced'},
        'cargo.build': {'name': 'Cargo', 'chain': 'ethereum', 'status': 'dead'},
        'mintbase.io': {'name': 'Mintbase', 'chain': 'near', 'status': 'active'},
        'paras.id': {'name': 'Paras', 'chain': 'near', 'status': 'active'},

        # Bitcoin/Ordinals
        'ordinals.com': {'name': 'Ordinals', 'chain': 'bitcoin', 'status': 'active'},
        'gamma.io': {'name': 'Gamma', 'chain': 'bitcoin', 'status': 'active'},
        'magiceden.io': {'name': 'Magic Eden', 'chain': 'multi', 'status': 'active'},
    }

    # CRITICAL: Shared Contract Addresses
    # These are contracts where THOUSANDS of artists minted
    # The "creator" field shows the PLATFORM, not the artist
    SHARED_CONTRACTS = {
        'ethereum': {
            # SuperRare
            '0x41a322b28d0ff354040e2cbc676f0320d8c8850d': {
                'name': 'SuperRare v1',
                'type': 'shared',
                'note': 'Early SuperRare - creator field unreliable'
            },
            '0xb932a70a57673d89f4acffbe830e8ed7f75fb9e0': {
                'name': 'SuperRare v2',
                'type': 'shared',
                'note': 'SuperRare shared storefront'
            },

            # Foundation
            '0x3b3ee1931dc30c1957379fac9aba94d1c48a5405': {
                'name': 'Foundation',
                'type': 'shared',
                'note': 'Foundation shared contract'
            },

            # Rarible
            '0xd07dc4262bcdbf85190c01c996b4c06a461d2430': {
                'name': 'Rarible',
                'type': 'shared',
                'note': 'Rarible ERC-1155 shared'
            },
            '0x60f80121c31a0d46b5279700f9df786054aa5ee5': {
                'name': 'Rarible ERC-721',
                'type': 'shared',
                'note': 'Rarible 721 shared'
            },

            # OpenSea
            '0x495f947276749ce646f68ac8c248420045cb7b5e': {
                'name': 'OpenSea Shared Storefront',
                'type': 'shared',
                'note': 'Massive shared contract - millions of tokens'
            },
            '0x2953399124f0cbb46d2cbacd8a89cf0599974963': {
                'name': 'OpenSea Shared (Polygon)',
                'type': 'shared',
                'note': 'Polygon shared storefront'
            },

            # Art Blocks
            '0xa7d8d9ef8d8ce8992df33d8b8cf4aebabd5bd270': {
                'name': 'Art Blocks',
                'type': 'shared_generative',
                'note': 'Art Blocks curated'
            },
            '0x059edd72cd353df5106d2b9cc5ab83a52287ac3a': {
                'name': 'Art Blocks (old)',
                'type': 'shared_generative',
                'note': 'Original Art Blocks contract'
            },

            # Async Art
            '0xb6dae651468e9593e4581705a09c10a76ac1e0c8': {
                'name': 'Async Art',
                'type': 'shared',
                'note': 'Async programmable art'
            },

            # KnownOrigin
            '0xfbeef911dc5821886e1dda71586d90ed28174b7d': {
                'name': 'KnownOrigin v1',
                'type': 'shared',
                'note': 'Early KO contract'
            },

            # Zora
            '0xabefbc9fd2f806065b4f3c237d4b59d9a97bcac7': {
                'name': 'Zora',
                'type': 'shared',
                'note': 'Zora shared media'
            },

            # MakersPlace
            '0x2a46f2ffd99e19a89476e2f62270e0a35bbf0756': {
                'name': 'MakersPlace',
                'type': 'shared',
                'note': 'MakersPlace shared'
            },
        },
        'tezos': {
            'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton': {
                'name': 'Hic Et Nunc',
                'type': 'shared',
                'note': 'HEN v2 - platform is DEAD but tokens exist'
            },
            'KT1M2JnD1wsg7w2B4UXJXtKQPuDUpU2L7cTq': {
                'name': 'Hic Et Nunc v1',
                'type': 'shared',
                'note': 'Original HEN - deprecated'
            },
        },
        'polygon': {
            '0x2953399124f0cbb46d2cbacd8a89cf0599974963': {
                'name': 'OpenSea Polygon',
                'type': 'shared',
                'note': 'OpenSea shared on Polygon'
            },
        }
    }

    # Regex for extracting blockchain data from tweets
    ETH_ADDRESS_PATTERN = r'0x[a-fA-F0-9]{40}'
    TX_HASH_PATTERN = r'0x[a-fA-F0-9]{64}'
    IPFS_HASH_PATTERN = r'(?:Qm[1-9A-HJ-NP-Za-km-z]{44}|bafy[a-zA-Z0-9]{50,})'
    TOKEN_ID_PATTERN = r'(?:token[_\s]?id|#)[\s:]*(\d+)'

    def __init__(self, network: str = 'ethereum'):
        self.network = network
        self._init_db()

    def _init_db(self):
        """Initialize provenance recovery database"""
        db_path = Path(__file__).parent.parent.parent / 'db' / 'provenance_recovery.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db_conn.row_factory = sqlite3.Row

        cursor = self.db_conn.cursor()

        # Verified artists table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verified_artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                twitter_handle TEXT UNIQUE,
                twitter_id TEXT,
                display_name TEXT,
                wallet_addresses TEXT,  -- JSON array
                verification_date TIMESTAMP,
                badge_level TEXT,
                total_works_found INTEGER DEFAULT 0,
                total_lost_recovered INTEGER DEFAULT 0,
                scan_status TEXT DEFAULT 'pending',
                last_scan TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Detected NFT mentions from social media
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_nft_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER,
                tweet_id TEXT,
                tweet_date TIMESTAMP,
                tweet_text TEXT,
                mention_type TEXT,  -- 'mint', 'sale', 'collect', 'unknown'
                platform_detected TEXT,
                platform_url TEXT,

                -- Extracted blockchain data
                contract_address TEXT,
                token_id TEXT,
                tx_hash TEXT,
                ipfs_hash TEXT,

                -- Image data
                image_urls TEXT,  -- JSON array
                image_hashes TEXT,  -- Perceptual hashes for matching

                -- Recovery status
                blockchain_verified INTEGER DEFAULT 0,
                blockchain_owner TEXT,
                ownership_matches_artist INTEGER DEFAULT NULL,
                anomaly_detected INTEGER DEFAULT 0,
                anomaly_type TEXT,

                -- Metadata
                engagement_score INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                witness_addresses TEXT,  -- Collectors who commented

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artist_id) REFERENCES verified_artists(id)
            )
        ''')

        # Lost/Anomalous works requiring investigation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lost_works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mention_id INTEGER,
                artist_id INTEGER,

                -- Social proof
                social_proof_strength TEXT,  -- 'strong', 'medium', 'weak'
                proof_tweets TEXT,  -- JSON array of supporting tweets
                witness_count INTEGER DEFAULT 0,

                -- Blockchain state
                current_owner TEXT,
                expected_owner TEXT,
                contract_address TEXT,
                token_id TEXT,
                is_shared_contract INTEGER DEFAULT 0,
                shared_contract_name TEXT,

                -- Recovery status
                recovery_status TEXT DEFAULT 'detected',  -- 'detected', 'investigating', 'recovered', 'unrecoverable'
                recovery_notes TEXT,

                -- Platform death info
                original_platform TEXT,
                platform_status TEXT,
                wayback_url TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mention_id) REFERENCES social_nft_mentions(id),
                FOREIGN KEY (artist_id) REFERENCES verified_artists(id)
            )
        ''')

        # Platform death registry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dead_platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                platform_name TEXT,
                death_date TEXT,
                chain TEXT,
                shared_contracts TEXT,  -- JSON array
                wayback_available INTEGER DEFAULT 1,
                recovery_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Scan progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER,
                pass_number INTEGER,
                pass_name TEXT,
                status TEXT DEFAULT 'pending',
                items_found INTEGER DEFAULT 0,
                anomalies_found INTEGER DEFAULT 0,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (artist_id) REFERENCES verified_artists(id)
            )
        ''')

        self.db_conn.commit()
        logger.info("Provenance recovery database initialized")

    # =========================================================================
    # PASS 1: Identity Verification & Initial Setup
    # =========================================================================

    def verify_artist(
        self,
        twitter_handle: str,
        wallet_addresses: List[str],
        twitter_id: str = None,
        display_name: str = None
    ) -> Dict:
        """
        Pass 1: Verify artist identity and set up for scanning

        This is the entry point - after Twitter OAuth verification,
        we store the verified identity and prepare for recursive scanning.
        """
        logger.info(f"Verifying artist: @{twitter_handle}")

        cursor = self.db_conn.cursor()

        # Normalize wallet addresses
        normalized_wallets = [w.lower() for w in wallet_addresses]

        # Store verified artist
        cursor.execute('''
            INSERT OR REPLACE INTO verified_artists
            (twitter_handle, twitter_id, display_name, wallet_addresses,
             verification_date, scan_status)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'verified')
        ''', (
            twitter_handle.lower().replace('@', ''),
            twitter_id,
            display_name,
            json.dumps(normalized_wallets)
        ))

        artist_id = cursor.lastrowid
        self.db_conn.commit()

        return {
            'success': True,
            'artist_id': artist_id,
            'twitter_handle': twitter_handle,
            'wallet_addresses': normalized_wallets,
            'message': 'Artist verified. Ready for recursive provenance scan.',
            'next_step': 'Run full_recursive_scan() to begin multi-pass analysis'
        }

    # =========================================================================
    # PASS 2: NFT Release Detection
    # =========================================================================

    def scan_nft_releases(self, artist_id: int, tweets: List[Dict]) -> Dict:
        """
        Pass 2: Detect NFT releases from tweet content

        Scans all tweets for:
        - Mint announcements ("just minted", "now available", etc.)
        - Platform links (SuperRare, Foundation, OpenSea, etc.)
        - Contract addresses and token IDs mentioned
        - IPFS hashes
        - Images (for later perceptual matching)
        """
        logger.info(f"Pass 2: Scanning for NFT releases (artist_id={artist_id})")

        self._log_scan_progress(artist_id, 2, 'nft_release_detection', 'running')

        releases_found = []
        cursor = self.db_conn.cursor()

        for tweet in tweets:
            tweet_text = tweet.get('text', '').lower()
            tweet_id = tweet.get('id')
            tweet_date = tweet.get('created_at')

            # Check for mint patterns
            is_mint = any(re.search(pattern, tweet_text, re.IGNORECASE)
                        for pattern in self.MINT_PATTERNS)

            if not is_mint:
                continue

            # Extract blockchain data
            extracted = self._extract_blockchain_data(tweet.get('text', ''))

            # Detect platform
            platform_info = self._detect_platform(tweet)

            # Get image URLs
            image_urls = self._extract_image_urls(tweet)

            # Store the mention
            cursor.execute('''
                INSERT INTO social_nft_mentions
                (artist_id, tweet_id, tweet_date, tweet_text, mention_type,
                 platform_detected, platform_url, contract_address, token_id,
                 tx_hash, ipfs_hash, image_urls, engagement_score, reply_count)
                VALUES (?, ?, ?, ?, 'mint', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                artist_id,
                tweet_id,
                tweet_date,
                tweet.get('text'),
                platform_info.get('platform'),
                platform_info.get('url'),
                extracted.get('contract_address'),
                extracted.get('token_id'),
                extracted.get('tx_hash'),
                extracted.get('ipfs_hash'),
                json.dumps(image_urls),
                tweet.get('public_metrics', {}).get('like_count', 0),
                tweet.get('public_metrics', {}).get('reply_count', 0)
            ))

            releases_found.append({
                'tweet_id': tweet_id,
                'date': tweet_date,
                'platform': platform_info.get('platform'),
                'contract': extracted.get('contract_address'),
                'token_id': extracted.get('token_id'),
                'has_images': len(image_urls) > 0
            })

        self.db_conn.commit()
        self._log_scan_progress(artist_id, 2, 'nft_release_detection', 'completed',
                               items_found=len(releases_found))

        return {
            'pass': 2,
            'name': 'NFT Release Detection',
            'releases_found': len(releases_found),
            'details': releases_found
        }

    # =========================================================================
    # PASS 3: Collection Detection
    # =========================================================================

    def scan_collections(self, artist_id: int, tweets: List[Dict]) -> Dict:
        """
        Pass 3: Detect collected works from tweet content

        Important because:
        - Artists often collected works on platforms they also minted on
        - Collection announcements contain platform/contract data
        - Can reveal additional platforms the artist used
        """
        logger.info(f"Pass 3: Scanning for collections (artist_id={artist_id})")

        self._log_scan_progress(artist_id, 3, 'collection_detection', 'running')

        collections_found = []
        cursor = self.db_conn.cursor()

        for tweet in tweets:
            tweet_text = tweet.get('text', '').lower()

            # Check for collection patterns
            is_collect = any(re.search(pattern, tweet_text, re.IGNORECASE)
                           for pattern in self.COLLECT_PATTERNS)

            if not is_collect:
                continue

            # Extract and store
            extracted = self._extract_blockchain_data(tweet.get('text', ''))
            platform_info = self._detect_platform(tweet)
            image_urls = self._extract_image_urls(tweet)

            cursor.execute('''
                INSERT INTO social_nft_mentions
                (artist_id, tweet_id, tweet_date, tweet_text, mention_type,
                 platform_detected, platform_url, contract_address, token_id,
                 tx_hash, ipfs_hash, image_urls)
                VALUES (?, ?, ?, ?, 'collect', ?, ?, ?, ?, ?, ?, ?)
            ''', (
                artist_id,
                tweet.get('id'),
                tweet.get('created_at'),
                tweet.get('text'),
                platform_info.get('platform'),
                platform_info.get('url'),
                extracted.get('contract_address'),
                extracted.get('token_id'),
                extracted.get('tx_hash'),
                extracted.get('ipfs_hash'),
                json.dumps(image_urls)
            ))

            collections_found.append({
                'tweet_id': tweet.get('id'),
                'platform': platform_info.get('platform')
            })

        self.db_conn.commit()
        self._log_scan_progress(artist_id, 3, 'collection_detection', 'completed',
                               items_found=len(collections_found))

        return {
            'pass': 3,
            'name': 'Collection Detection',
            'collections_found': len(collections_found),
            'details': collections_found
        }

    # =========================================================================
    # PASS 4: Blockchain Cross-Reference & Anomaly Detection
    # =========================================================================

    def cross_reference_blockchain(self, artist_id: int) -> Dict:
        """
        Pass 4: Cross-reference social mentions with blockchain state

        THIS IS THE CRITICAL PASS:
        - For each detected NFT mention, verify on blockchain
        - Check if current owner matches artist's wallets
        - Detect anomalies:
          * Work on shared contract (creator != artist)
          * Work in platform escrow wallet
          * Work transferred to unknown address
          * Work burned but social proof exists
        """
        logger.info(f"Pass 4: Cross-referencing with blockchain (artist_id={artist_id})")

        self._log_scan_progress(artist_id, 4, 'blockchain_crossref', 'running')

        cursor = self.db_conn.cursor()

        # Get artist's verified wallets
        cursor.execute('SELECT wallet_addresses FROM verified_artists WHERE id = ?',
                      (artist_id,))
        artist = cursor.fetchone()
        artist_wallets = set(json.loads(artist['wallet_addresses']))

        # Get all unverified mentions
        cursor.execute('''
            SELECT * FROM social_nft_mentions
            WHERE artist_id = ? AND blockchain_verified = 0
            AND contract_address IS NOT NULL
        ''', (artist_id,))

        mentions = cursor.fetchall()
        anomalies_found = []
        verified_count = 0

        for mention in mentions:
            contract = mention['contract_address']
            token_id = mention['token_id']

            if not contract:
                continue

            # Check if this is a shared contract
            is_shared = self._is_shared_contract(contract)

            # Query blockchain for current owner
            # (This would call your blockchain RPC)
            blockchain_state = self._get_blockchain_state(contract, token_id)

            if blockchain_state:
                current_owner = blockchain_state.get('owner', '').lower()

                # Check for anomalies
                anomaly_type = None

                if is_shared:
                    # Shared contract - creator field is UNRELIABLE
                    anomaly_type = 'shared_contract'

                elif current_owner and current_owner not in artist_wallets:
                    # Owner doesn't match - could be:
                    # - Legitimately sold
                    # - Stuck in platform wallet
                    # - Stolen/transferred unexpectedly

                    if self._is_platform_wallet(current_owner):
                        anomaly_type = 'platform_escrow'
                    elif current_owner == '0x0000000000000000000000000000000000000000':
                        anomaly_type = 'burned'
                    else:
                        # Need to check transfer history
                        anomaly_type = 'ownership_mismatch'

                # Update mention record
                cursor.execute('''
                    UPDATE social_nft_mentions
                    SET blockchain_verified = 1,
                        blockchain_owner = ?,
                        ownership_matches_artist = ?,
                        anomaly_detected = ?,
                        anomaly_type = ?
                    WHERE id = ?
                ''', (
                    current_owner,
                    1 if current_owner in artist_wallets else 0,
                    1 if anomaly_type else 0,
                    anomaly_type,
                    mention['id']
                ))

                verified_count += 1

                if anomaly_type:
                    anomalies_found.append({
                        'mention_id': mention['id'],
                        'tweet_id': mention['tweet_id'],
                        'contract': contract,
                        'token_id': token_id,
                        'anomaly_type': anomaly_type,
                        'current_owner': current_owner,
                        'is_shared_contract': is_shared
                    })

                    # Log as lost work for investigation
                    self._log_lost_work(
                        mention['id'],
                        artist_id,
                        anomaly_type,
                        contract,
                        token_id,
                        current_owner,
                        artist_wallets
                    )

        self.db_conn.commit()
        self._log_scan_progress(artist_id, 4, 'blockchain_crossref', 'completed',
                               items_found=verified_count,
                               anomalies_found=len(anomalies_found))

        return {
            'pass': 4,
            'name': 'Blockchain Cross-Reference',
            'verified_count': verified_count,
            'anomalies_found': len(anomalies_found),
            'anomalies': anomalies_found
        }

    # =========================================================================
    # PASS 5: Platform Death Recovery
    # =========================================================================

    def recover_dead_platform_data(self, artist_id: int) -> Dict:
        """
        Pass 5: Recover data from dead platforms using Wayback Machine

        For detected NFT mentions on dead platforms:
        - Query Wayback Machine for archived pages
        - Extract contract/token data from archives
        - Match with blockchain state
        - Recover "lost" provenance
        """
        logger.info(f"Pass 5: Dead platform recovery (artist_id={artist_id})")

        self._log_scan_progress(artist_id, 5, 'dead_platform_recovery', 'running')

        cursor = self.db_conn.cursor()

        # Get mentions with dead platform URLs
        cursor.execute('''
            SELECT * FROM social_nft_mentions
            WHERE artist_id = ? AND platform_url IS NOT NULL
        ''', (artist_id,))

        mentions = cursor.fetchall()
        recovered = []

        for mention in mentions:
            platform_url = mention['platform_url']
            if not platform_url:
                continue

            domain = urlparse(platform_url).netloc.lower()
            platform_info = self.PLATFORM_DOMAINS.get(domain, {})

            if platform_info.get('status') != 'dead':
                continue

            # Query Wayback Machine
            wayback_data = self._query_wayback(platform_url)

            if wayback_data:
                # Extract blockchain data from archived page
                archived_data = self._extract_from_wayback(wayback_data)

                if archived_data.get('contract_address'):
                    # Update mention with recovered data
                    cursor.execute('''
                        UPDATE social_nft_mentions
                        SET contract_address = COALESCE(contract_address, ?),
                            token_id = COALESCE(token_id, ?)
                        WHERE id = ?
                    ''', (
                        archived_data.get('contract_address'),
                        archived_data.get('token_id'),
                        mention['id']
                    ))

                    recovered.append({
                        'mention_id': mention['id'],
                        'platform': platform_info.get('name'),
                        'wayback_url': wayback_data.get('url'),
                        'contract_recovered': archived_data.get('contract_address'),
                        'token_recovered': archived_data.get('token_id')
                    })

        self.db_conn.commit()
        self._log_scan_progress(artist_id, 5, 'dead_platform_recovery', 'completed',
                               items_found=len(recovered))

        return {
            'pass': 5,
            'name': 'Dead Platform Recovery',
            'recovered_count': len(recovered),
            'details': recovered
        }

    # =========================================================================
    # PASS 6: Image Matching
    # =========================================================================

    def match_images(self, artist_id: int) -> Dict:
        """
        Pass 6: Use perceptual hashing to match artwork images

        For mentions where we have images but no contract:
        - Generate perceptual hash of image
        - Compare against known NFT images
        - Match to recover contract/token association
        """
        logger.info(f"Pass 6: Image matching (artist_id={artist_id})")

        self._log_scan_progress(artist_id, 6, 'image_matching', 'running')

        # This would use imagehash library for perceptual hashing
        # For now, return placeholder

        self._log_scan_progress(artist_id, 6, 'image_matching', 'completed')

        return {
            'pass': 6,
            'name': 'Image Matching',
            'matches_found': 0,
            'note': 'Perceptual hashing comparison pending'
        }

    # =========================================================================
    # Full Recursive Scan
    # =========================================================================

    def full_recursive_scan(self, artist_id: int, tweets: List[Dict]) -> Dict:
        """
        Execute full 6-pass recursive provenance scan

        This is the "major solidifier" - comprehensive social proof
        recovery for blockchain art provenance.
        """
        logger.info(f"Starting full recursive scan for artist_id={artist_id}")

        results = {
            'artist_id': artist_id,
            'scan_started': datetime.now().isoformat(),
            'passes': []
        }

        # Pass 1 already done (verification)

        # Pass 2: NFT Release Detection
        pass2 = self.scan_nft_releases(artist_id, tweets)
        results['passes'].append(pass2)

        # Pass 3: Collection Detection
        pass3 = self.scan_collections(artist_id, tweets)
        results['passes'].append(pass3)

        # Pass 4: Blockchain Cross-Reference
        pass4 = self.cross_reference_blockchain(artist_id)
        results['passes'].append(pass4)

        # Pass 5: Dead Platform Recovery
        pass5 = self.recover_dead_platform_data(artist_id)
        results['passes'].append(pass5)

        # Pass 6: Image Matching
        pass6 = self.match_images(artist_id)
        results['passes'].append(pass6)

        # Update artist record
        cursor = self.db_conn.cursor()
        cursor.execute('''
            UPDATE verified_artists
            SET total_works_found = ?,
                total_lost_recovered = ?,
                scan_status = 'completed',
                last_scan = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            pass2['releases_found'] + pass3['collections_found'],
            pass4['anomalies_found'],
            artist_id
        ))
        self.db_conn.commit()

        results['scan_completed'] = datetime.now().isoformat()
        results['summary'] = {
            'total_works_detected': pass2['releases_found'] + pass3['collections_found'],
            'anomalies_requiring_investigation': pass4['anomalies_found'],
            'dead_platform_recoveries': pass5['recovered_count'],
            'image_matches': pass6['matches_found']
        }

        return results

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_blockchain_data(self, text: str) -> Dict:
        """Extract contract addresses, tx hashes, IPFS from text"""
        result = {}

        # Contract address
        eth_match = re.search(self.ETH_ADDRESS_PATTERN, text)
        if eth_match:
            result['contract_address'] = eth_match.group().lower()

        # Transaction hash
        tx_match = re.search(self.TX_HASH_PATTERN, text)
        if tx_match:
            result['tx_hash'] = tx_match.group().lower()

        # IPFS hash
        ipfs_match = re.search(self.IPFS_HASH_PATTERN, text)
        if ipfs_match:
            result['ipfs_hash'] = ipfs_match.group()

        # Token ID
        token_match = re.search(self.TOKEN_ID_PATTERN, text, re.IGNORECASE)
        if token_match:
            result['token_id'] = token_match.group(1)

        return result

    def _detect_platform(self, tweet: Dict) -> Dict:
        """Detect NFT platform from tweet URLs"""
        result = {'platform': None, 'url': None}

        # Check tweet URLs
        urls = tweet.get('entities', {}).get('urls', [])
        for url_entity in urls:
            expanded_url = url_entity.get('expanded_url', '')
            domain = urlparse(expanded_url).netloc.lower()

            # Remove www prefix
            domain = domain.replace('www.', '')

            if domain in self.PLATFORM_DOMAINS:
                result['platform'] = self.PLATFORM_DOMAINS[domain]['name']
                result['url'] = expanded_url
                result['chain'] = self.PLATFORM_DOMAINS[domain]['chain']
                result['platform_status'] = self.PLATFORM_DOMAINS[domain]['status']
                break

        return result

    def _extract_image_urls(self, tweet: Dict) -> List[str]:
        """Extract image URLs from tweet media"""
        images = []

        media = tweet.get('attachments', {}).get('media', [])
        for item in media:
            if item.get('type') == 'photo':
                images.append(item.get('url'))

        # Also check for Twitter card images
        urls = tweet.get('entities', {}).get('urls', [])
        for url_entity in urls:
            images_from_url = url_entity.get('images', [])
            for img in images_from_url:
                images.append(img.get('url'))

        return [img for img in images if img]

    def _is_shared_contract(self, contract_address: str) -> bool:
        """Check if contract is a known shared contract"""
        contract_lower = contract_address.lower()

        for chain, contracts in self.SHARED_CONTRACTS.items():
            if contract_lower in contracts:
                return True

        return False

    def _get_shared_contract_info(self, contract_address: str) -> Optional[Dict]:
        """Get info about a shared contract"""
        contract_lower = contract_address.lower()

        for chain, contracts in self.SHARED_CONTRACTS.items():
            if contract_lower in contracts:
                info = contracts[contract_lower].copy()
                info['chain'] = chain
                return info

        return None

    def _is_platform_wallet(self, address: str) -> bool:
        """Check if address is a known platform escrow wallet"""
        # Known platform wallets
        platform_wallets = {
            '0x3b3ee1931dc30c1957379fac9aba94d1c48a5405',  # Foundation
            '0xec9c519d49856fd2f8133a0741b4dbe002ce211b',  # SuperRare
            # Add more as discovered
        }
        return address.lower() in platform_wallets

    def _get_blockchain_state(self, contract: str, token_id: str) -> Optional[Dict]:
        """Query blockchain for current token state"""
        # This would integrate with your MultiProviderWeb3
        # For now, return None (will be implemented with real RPC)
        try:
            from collectors.multi_provider_web3 import MultiProviderWeb3
            web3 = MultiProviderWeb3(self.network)

            # ownerOf call for ERC-721
            # Would need to handle ERC-1155 differently

            return None  # Placeholder
        except Exception as e:
            logger.warning(f"Blockchain query failed: {e}")
            return None

    def _query_wayback(self, url: str) -> Optional[Dict]:
        """Query Wayback Machine for archived page"""
        try:
            import requests

            # Wayback Machine Availability API
            api_url = f"http://archive.org/wayback/available?url={url}"
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                snapshots = data.get('archived_snapshots', {})
                closest = snapshots.get('closest', {})

                if closest.get('available'):
                    return {
                        'url': closest.get('url'),
                        'timestamp': closest.get('timestamp'),
                        'status': closest.get('status')
                    }

            return None
        except Exception as e:
            logger.warning(f"Wayback query failed: {e}")
            return None

    def _extract_from_wayback(self, wayback_data: Dict) -> Dict:
        """Extract blockchain data from archived page"""
        # This would fetch and parse the archived page
        # Looking for contract addresses, token IDs, etc.
        return {}

    def _log_scan_progress(self, artist_id: int, pass_number: int,
                          pass_name: str, status: str,
                          items_found: int = 0, anomalies_found: int = 0):
        """Log scan progress"""
        cursor = self.db_conn.cursor()

        if status == 'running':
            cursor.execute('''
                INSERT INTO scan_progress
                (artist_id, pass_number, pass_name, status, started_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (artist_id, pass_number, pass_name, status))
        else:
            cursor.execute('''
                UPDATE scan_progress
                SET status = ?, items_found = ?, anomalies_found = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE artist_id = ? AND pass_number = ?
            ''', (status, items_found, anomalies_found, artist_id, pass_number))

        self.db_conn.commit()

    def _log_lost_work(self, mention_id: int, artist_id: int, anomaly_type: str,
                      contract: str, token_id: str, current_owner: str,
                      artist_wallets: Set[str]):
        """Log a detected lost/anomalous work"""
        cursor = self.db_conn.cursor()

        shared_info = self._get_shared_contract_info(contract)

        cursor.execute('''
            INSERT INTO lost_works
            (mention_id, artist_id, social_proof_strength, current_owner,
             expected_owner, contract_address, token_id, is_shared_contract,
             shared_contract_name, recovery_status)
            VALUES (?, ?, 'medium', ?, ?, ?, ?, ?, ?, 'detected')
        ''', (
            mention_id,
            artist_id,
            current_owner,
            list(artist_wallets)[0] if artist_wallets else None,
            contract,
            token_id,
            1 if shared_info else 0,
            shared_info.get('name') if shared_info else None
        ))

        self.db_conn.commit()

    # =========================================================================
    # Reporting Methods
    # =========================================================================

    def get_lost_works_report(self, artist_id: int) -> Dict:
        """Generate report of all detected lost/anomalous works"""
        cursor = self.db_conn.cursor()

        cursor.execute('''
            SELECT lw.*, snm.tweet_text, snm.tweet_date, snm.platform_detected
            FROM lost_works lw
            JOIN social_nft_mentions snm ON lw.mention_id = snm.id
            WHERE lw.artist_id = ?
            ORDER BY snm.tweet_date DESC
        ''', (artist_id,))

        works = [dict(row) for row in cursor.fetchall()]

        # Categorize
        categories = {
            'shared_contract': [],
            'platform_escrow': [],
            'ownership_mismatch': [],
            'burned': []
        }

        for work in works:
            anomaly = work.get('anomaly_type') or 'ownership_mismatch'
            if anomaly in categories:
                categories[anomaly].append(work)

        return {
            'total_anomalies': len(works),
            'categories': categories,
            'summary': {
                'shared_contract_issues': len(categories['shared_contract']),
                'platform_escrow_stuck': len(categories['platform_escrow']),
                'ownership_mismatches': len(categories['ownership_mismatch']),
                'burned_with_social_proof': len(categories['burned'])
            }
        }


# CLI interface
if __name__ == '__main__':
    scanner = RecursiveProvenanceScanner('ethereum')

    if len(sys.argv) < 2:
        print("""
Recursive Provenance Scanner
============================

Usage:
  python recursive_provenance_scanner.py verify <twitter_handle> <wallet1> [wallet2...]
  python recursive_provenance_scanner.py scan <artist_id>
  python recursive_provenance_scanner.py report <artist_id>
  python recursive_provenance_scanner.py shared-contracts

Examples:
  # Verify an artist
  python recursive_provenance_scanner.py verify giselx 0x1234... 0x5678...

  # Run full scan (requires tweets to be loaded)
  python recursive_provenance_scanner.py scan 1

  # Get lost works report
  python recursive_provenance_scanner.py report 1

  # List known shared contracts
  python recursive_provenance_scanner.py shared-contracts
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'verify':
        twitter = sys.argv[2]
        wallets = sys.argv[3:]
        result = scanner.verify_artist(twitter, wallets)
        print(json.dumps(result, indent=2))

    elif command == 'shared-contracts':
        print("\nKnown Shared Contracts (Creator field UNRELIABLE):")
        print("=" * 60)
        for chain, contracts in scanner.SHARED_CONTRACTS.items():
            print(f"\n{chain.upper()}:")
            for addr, info in contracts.items():
                print(f"  {addr[:10]}...{addr[-6:]}: {info['name']}")
                print(f"    Note: {info['note']}")

    elif command == 'report':
        artist_id = int(sys.argv[2])
        report = scanner.get_lost_works_report(artist_id)
        print(json.dumps(report, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
