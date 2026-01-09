#!/usr/bin/env python3
"""
Blockchain Tracking Database Manager
Manages SQLite database for blockchain address tracking, NFT mints, transactions, and collectors
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlockchainDB:
    """Database manager for blockchain tracking system"""

    def __init__(self, db_path: str = "db/blockchain_tracking.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database with full schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')

        # Create all tables
        cursor.executescript('''
            -- Tracked addresses (primary entity)
            CREATE TABLE IF NOT EXISTS tracked_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                network TEXT NOT NULL,  -- 'ethereum', 'solana', 'bitcoin'
                label TEXT,             -- User-friendly name
                address_type TEXT,      -- 'wallet', 'contract', 'ordinal'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced TIMESTAMP,
                sync_enabled BOOLEAN DEFAULT TRUE,
                notes TEXT
            );

            -- NFT creations/mints by tracked addresses
            CREATE TABLE IF NOT EXISTS nft_mints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address_id INTEGER REFERENCES tracked_addresses(id) ON DELETE CASCADE,
                token_id TEXT,
                contract_address TEXT,
                mint_tx_hash TEXT,
                mint_block_number INTEGER,
                mint_timestamp TIMESTAMP,
                token_uri TEXT,          -- IPFS or HTTP metadata URI
                metadata_json TEXT,      -- Cached JSON metadata
                ipfs_hash TEXT,
                image_ipfs_hash TEXT,
                name TEXT,
                description TEXT,
                attributes TEXT,         -- JSON array
                platform TEXT,           -- 'foundation', 'opensea', etc.
                document_id TEXT,        -- Link to knowledge base document
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(contract_address, token_id, address_id)
            );

            -- Transaction history
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address_id INTEGER REFERENCES tracked_addresses(id) ON DELETE CASCADE,
                tx_hash TEXT UNIQUE NOT NULL,
                block_number INTEGER,
                block_timestamp TIMESTAMP,
                from_address TEXT,
                to_address TEXT,
                value_wei TEXT,          -- Store as string for precision
                value_native REAL,       -- Converted ETH/SOL/BTC amount
                gas_used INTEGER,
                gas_price TEXT,
                tx_type TEXT,            -- 'mint', 'transfer', 'sale', 'purchase'
                nft_mint_id INTEGER REFERENCES nft_mints(id) ON DELETE SET NULL,
                raw_data TEXT,           -- Full JSON response
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Collector/buyer tracking
            CREATE TABLE IF NOT EXISTS collectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collector_address TEXT NOT NULL,
                network TEXT NOT NULL,
                nft_mint_id INTEGER REFERENCES nft_mints(id) ON DELETE CASCADE,
                purchase_tx_hash TEXT,
                purchase_price_wei TEXT,
                purchase_price_native REAL,
                currency TEXT,           -- 'ETH', 'WETH', 'SOL', 'BTC'
                purchase_timestamp TIMESTAMP,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(collector_address, nft_mint_id)
            );

            -- IPFS metadata cache
            CREATE TABLE IF NOT EXISTS ipfs_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ipfs_hash TEXT UNIQUE NOT NULL,
                content_type TEXT,       -- 'json', 'image', 'html'
                content TEXT,            -- JSON content or file path for media
                gateway_used TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid BOOLEAN DEFAULT TRUE
            );

            -- Sync history
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address_id INTEGER REFERENCES tracked_addresses(id) ON DELETE CASCADE,
                sync_type TEXT,          -- 'full', 'incremental'
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                items_found INTEGER,
                items_new INTEGER,
                error_message TEXT,
                status TEXT              -- 'success', 'partial', 'failed'
            );

            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_tracked_address ON tracked_addresses(address);
            CREATE INDEX IF NOT EXISTS idx_tracked_network ON tracked_addresses(network);
            CREATE INDEX IF NOT EXISTS idx_nft_address_id ON nft_mints(address_id);
            CREATE INDEX IF NOT EXISTS idx_nft_contract ON nft_mints(contract_address);
            CREATE INDEX IF NOT EXISTS idx_tx_address_id ON transactions(address_id);
            CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions(tx_hash);
            CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(block_timestamp);
            CREATE INDEX IF NOT EXISTS idx_collector_nft ON collectors(nft_mint_id);
            CREATE INDEX IF NOT EXISTS idx_ipfs_hash ON ipfs_cache(ipfs_hash);
            CREATE INDEX IF NOT EXISTS idx_sync_address ON sync_history(address_id);

            -- ============================================================
            -- LIVING WORKS TEMPORAL FRAMEWORK TABLES
            -- Tracks NFTs as temporal entities with past, present, future
            -- ============================================================

            -- Historical states table - tracks all states an NFT has been in
            CREATE TABLE IF NOT EXISTS nft_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_id INTEGER REFERENCES nft_mints(id) ON DELETE CASCADE,
                state_number INTEGER,
                block_number INTEGER,
                timestamp DATETIME,
                state_type TEXT,  -- 'initial', 'reveal', 'evolution', 'decay', 'update'
                token_uri TEXT,
                metadata_json TEXT,
                image_archive_path TEXT,
                visual_hash TEXT,  -- perceptual hash for visual comparison
                trigger_type TEXT,  -- 'mint', 'transaction', 'time', 'oracle', 'owner_action'
                trigger_tx_hash TEXT,
                trigger_description TEXT,
                changes_from_previous TEXT,  -- JSON describing what changed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Scheduled events table - future events for NFTs
            CREATE TABLE IF NOT EXISTS nft_scheduled_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_id INTEGER REFERENCES nft_mints(id) ON DELETE CASCADE,
                event_type TEXT,  -- 'reveal', 'phase_change', 'decay', 'unlock', 'auction_end'
                scheduled_time DATETIME,
                source TEXT,  -- 'contract_storage', 'metadata', 'inferred', 'manual'
                source_variable TEXT,  -- e.g. 'revealTime', 'phase_2_start'
                description TEXT,
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern TEXT,  -- 'daily', 'weekly', 'seasonal', etc.
                completed BOOLEAN DEFAULT FALSE,
                completed_at DATETIME,
                notification_sent BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Reactivity profiles table - defines how NFTs respond to inputs
            CREATE TABLE IF NOT EXISTS nft_reactivity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_id INTEGER REFERENCES nft_mints(id) ON DELETE CASCADE,
                is_reactive BOOLEAN DEFAULT FALSE,
                reactivity_types TEXT,  -- JSON array: ['oracle_fed', 'time_responsive', 'chain_state', 'interactive']
                data_sources TEXT,  -- JSON array of data source configs
                update_frequency TEXT,  -- 'real_time', 'hourly', 'daily', 'on_trigger'
                is_deterministic BOOLEAN DEFAULT TRUE,  -- same inputs = same output?
                monitoring_active BOOLEAN DEFAULT FALSE,
                capture_schedule TEXT,  -- JSON config for when to capture states
                last_capture DATETIME,
                next_scheduled_capture DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Live state captures table - snapshots of reactive works
            CREATE TABLE IF NOT EXISTS nft_live_captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_id INTEGER REFERENCES nft_mints(id) ON DELETE CASCADE,
                capture_id TEXT UNIQUE,  -- human-readable ID like 'state_001'
                capture_timestamp DATETIME,
                block_height INTEGER,
                input_state TEXT,  -- JSON of oracle values, time, chain state at capture
                visual_hash TEXT,
                visual_archive_path TEXT,
                metadata_snapshot TEXT,  -- JSON of metadata at capture time
                changes_from_previous TEXT,  -- JSON describing what changed
                capture_trigger TEXT,  -- 'scheduled', 'oracle_delta', 'manual', 'transfer'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- Contract time logic table - detected time-based contract features
            CREATE TABLE IF NOT EXISTS contract_time_logic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT UNIQUE NOT NULL,
                network TEXT,
                has_reveal_function BOOLEAN DEFAULT FALSE,
                has_reveal_time BOOLEAN DEFAULT FALSE,
                has_phase_logic BOOLEAN DEFAULT FALSE,
                has_decay_logic BOOLEAN DEFAULT FALSE,
                has_seasonal_logic BOOLEAN DEFAULT FALSE,
                time_variables TEXT,  -- JSON array of detected time variables
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_analyzed DATETIME
            );

            -- ============================================================
            -- PROVENANCE CERTIFICATION CACHE
            -- Caches certification results for NFTs (24 hour expiry)
            -- ============================================================

            CREATE TABLE IF NOT EXISTS certification_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,      -- "contract:token_id" format
                contract_address TEXT,
                token_id TEXT,
                certification_data TEXT,              -- Full JSON certification result
                certification_level TEXT,             -- VERIFIED, LIKELY, UNVERIFIED
                score INTEGER,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Indexes for temporal tables
            CREATE INDEX IF NOT EXISTS idx_nft_states_nft ON nft_states(nft_id);
            CREATE INDEX IF NOT EXISTS idx_nft_states_timestamp ON nft_states(timestamp);
            CREATE INDEX IF NOT EXISTS idx_nft_states_type ON nft_states(state_type);
            CREATE INDEX IF NOT EXISTS idx_scheduled_events_nft ON nft_scheduled_events(nft_id);
            CREATE INDEX IF NOT EXISTS idx_scheduled_events_time ON nft_scheduled_events(scheduled_time);
            CREATE INDEX IF NOT EXISTS idx_scheduled_events_completed ON nft_scheduled_events(completed);
            CREATE INDEX IF NOT EXISTS idx_reactivity_nft ON nft_reactivity(nft_id);
            CREATE INDEX IF NOT EXISTS idx_reactivity_active ON nft_reactivity(monitoring_active);
            CREATE INDEX IF NOT EXISTS idx_live_captures_nft ON nft_live_captures(nft_id);
            CREATE INDEX IF NOT EXISTS idx_live_captures_timestamp ON nft_live_captures(capture_timestamp);
            CREATE INDEX IF NOT EXISTS idx_contract_time_logic ON contract_time_logic(contract_address);

            -- Certification cache indexes
            CREATE INDEX IF NOT EXISTS idx_cert_cache_key ON certification_cache(cache_key);
            CREATE INDEX IF NOT EXISTS idx_cert_cache_contract ON certification_cache(contract_address);
            CREATE INDEX IF NOT EXISTS idx_cert_cache_timestamp ON certification_cache(cached_at);

            -- ============================================================
            -- CROSS-CHAIN IDENTITY LINKING
            -- Links blockchain addresses across chains via social profiles
            -- ============================================================

            -- Social profiles - unified identity across chains
            CREATE TABLE IF NOT EXISTS social_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Primary identifiers (any can be null)
                twitter_handle TEXT,          -- @username (lowercase)
                ens_name TEXT,                -- name.eth
                tezos_domain TEXT,            -- name.tez
                lens_handle TEXT,             -- name.lens
                farcaster_name TEXT,          -- farcaster username
                -- Profile metadata
                display_name TEXT,
                bio TEXT,
                avatar_url TEXT,
                verified BOOLEAN DEFAULT FALSE,
                verification_source TEXT,     -- 'ens_reverse', 'twitter_bio', 'tzkt_api', 'manual'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(twitter_handle),
                UNIQUE(ens_name),
                UNIQUE(tezos_domain)
            );

            -- Links profiles to blockchain addresses (many-to-many)
            CREATE TABLE IF NOT EXISTS profile_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER REFERENCES social_profiles(id) ON DELETE CASCADE,
                address TEXT NOT NULL,        -- Case-preserved for Tezos
                network TEXT NOT NULL,        -- 'ethereum', 'tezos', 'solana', etc.
                is_primary BOOLEAN DEFAULT FALSE,
                discovered_via TEXT,          -- 'ens_reverse', 'twitter_bio', 'tzkt_domain', 'manual'
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(address, network)
            );

            -- Cross-chain collector overlap - detected shared collectors
            CREATE TABLE IF NOT EXISTS cross_chain_overlaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER REFERENCES social_profiles(id) ON DELETE CASCADE,
                -- Addresses on different chains
                ethereum_address TEXT,
                tezos_address TEXT,
                solana_address TEXT,
                -- Overlap evidence
                overlap_type TEXT,            -- 'social_link', 'ens_match', 'transaction_pattern'
                confidence REAL,              -- 0.0 to 1.0
                evidence TEXT,                -- JSON describing how overlap was detected
                -- Stats
                ethereum_nfts_collected INTEGER DEFAULT 0,
                tezos_nfts_collected INTEGER DEFAULT 0,
                shared_artists INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Indexes for social/cross-chain tables
            CREATE INDEX IF NOT EXISTS idx_social_twitter ON social_profiles(twitter_handle);
            CREATE INDEX IF NOT EXISTS idx_social_ens ON social_profiles(ens_name);
            CREATE INDEX IF NOT EXISTS idx_social_tezos ON social_profiles(tezos_domain);
            CREATE INDEX IF NOT EXISTS idx_profile_addresses_profile ON profile_addresses(profile_id);
            CREATE INDEX IF NOT EXISTS idx_profile_addresses_address ON profile_addresses(address);
            CREATE INDEX IF NOT EXISTS idx_profile_addresses_network ON profile_addresses(network);
            CREATE INDEX IF NOT EXISTS idx_overlap_eth ON cross_chain_overlaps(ethereum_address);
            CREATE INDEX IF NOT EXISTS idx_overlap_tez ON cross_chain_overlaps(tezos_address);
        ''')

        conn.commit()
        conn.close()

        logger.info(f"Blockchain tracking database initialized at {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def execute(self, query: str, params: tuple = ()) -> Optional[List[Dict]]:
        """Execute a query and return results as list of dicts"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)

            # If SELECT query, fetch results
            if query.strip().upper().startswith('SELECT'):
                results = [dict(row) for row in cursor.fetchall()]
                conn.close()
                return results

            # For INSERT/UPDATE/DELETE, commit and return affected rows
            conn.commit()
            affected = cursor.rowcount
            last_id = cursor.lastrowid
            conn.close()

            return [{'affected_rows': affected, 'last_id': last_id}]

        except Exception as e:
            logger.error(f"Database error: {e}")
            conn.close()
            raise

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Count tracked addresses by network
        cursor.execute('''
            SELECT network, COUNT(*) as count
            FROM tracked_addresses
            WHERE sync_enabled = TRUE
            GROUP BY network
        ''')
        stats['addresses_by_network'] = {row['network']: row['count'] for row in cursor.fetchall()}

        # Total NFTs minted
        cursor.execute('SELECT COUNT(*) as count FROM nft_mints')
        stats['total_nfts'] = cursor.fetchone()['count']

        # Total transactions
        cursor.execute('SELECT COUNT(*) as count FROM transactions')
        stats['total_transactions'] = cursor.fetchone()['count']

        # Total collectors
        cursor.execute('SELECT COUNT(DISTINCT collector_address) as count FROM collectors')
        stats['unique_collectors'] = cursor.fetchone()['count']

        # Latest sync
        cursor.execute('''
            SELECT MAX(completed_at) as last_sync
            FROM sync_history
            WHERE status = 'success'
        ''')
        result = cursor.fetchone()
        stats['last_successful_sync'] = result['last_sync'] if result else None

        conn.close()
        return stats


# Singleton instance
_db_instance = None

def get_db() -> BlockchainDB:
    """Get or create singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = BlockchainDB()
    return _db_instance


if __name__ == '__main__':
    # Test database creation
    db = BlockchainDB()
    stats = db.get_stats()
    print("Database initialized successfully!")
    print(f"Stats: {stats}")
