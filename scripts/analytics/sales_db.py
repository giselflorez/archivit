#!/usr/bin/env python3
"""
Sales Analytics Database Manager
Tracks NFT sales data from marketplaces (linked to tracked blockchain addresses only)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SalesDB:
    """Database manager for sales analytics"""

    def __init__(self, db_path: str = "db/sales_analytics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database with sales analytics schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')

        # Create all tables
        cursor.executescript('''
            -- NFT sales records
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_contract TEXT NOT NULL,
                token_id TEXT NOT NULL,
                network TEXT NOT NULL,           -- 'ethereum', 'solana', etc.
                seller_address TEXT NOT NULL,
                buyer_address TEXT NOT NULL,
                sale_price_wei TEXT,             -- Price in smallest unit (wei, lamports)
                sale_price_native REAL,          -- Price in native currency (ETH, SOL)
                sale_price_usd REAL,             -- Price in USD at time of sale
                currency TEXT NOT NULL,          -- 'ETH', 'WETH', 'SOL', etc.
                marketplace TEXT NOT NULL,       -- 'opensea', 'foundation', 'superrare', etc.
                tx_hash TEXT UNIQUE,             -- Transaction hash
                block_number INTEGER,
                sale_timestamp TIMESTAMP NOT NULL,
                royalty_amount REAL,             -- Royalty paid to creator
                platform_fee REAL,               -- Platform fee
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tracked_address_id INTEGER,      -- Link to tracked address (if applicable)
                UNIQUE(tx_hash, nft_contract, token_id)
            );

            -- Collections (aggregated from NFT contracts)
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT UNIQUE NOT NULL,
                network TEXT NOT NULL,
                collection_name TEXT,
                creator_address TEXT,
                total_supply INTEGER,
                floor_price_native REAL,
                floor_price_usd REAL,
                total_volume_native REAL,        -- All-time volume
                total_volume_usd REAL,
                total_sales INTEGER,             -- Number of sales
                last_sale_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Marketplace sync history
            CREATE TABLE IF NOT EXISTS marketplace_sync (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marketplace TEXT NOT NULL,       -- 'opensea', 'foundation', etc.
                network TEXT NOT NULL,
                sync_type TEXT NOT NULL,         -- 'tracked_addresses', 'collection', 'full'
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                items_found INTEGER,
                items_new INTEGER,
                error_message TEXT,
                status TEXT NOT NULL             -- 'running', 'success', 'failed'
            );

            -- Price history (for charts and trends)
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_contract TEXT NOT NULL,
                token_id TEXT,                   -- NULL for collection floor price
                network TEXT NOT NULL,
                price_native REAL NOT NULL,
                price_usd REAL,
                price_type TEXT NOT NULL,        -- 'sale', 'listing', 'floor'
                recorded_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(nft_contract, token_id, price_type, recorded_at)
            );

            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_sales_contract ON sales(nft_contract, token_id);
            CREATE INDEX IF NOT EXISTS idx_sales_seller ON sales(seller_address);
            CREATE INDEX IF NOT EXISTS idx_sales_buyer ON sales(buyer_address);
            CREATE INDEX IF NOT EXISTS idx_sales_timestamp ON sales(sale_timestamp);
            CREATE INDEX IF NOT EXISTS idx_sales_marketplace ON sales(marketplace);
            CREATE INDEX IF NOT EXISTS idx_sales_tracked ON sales(tracked_address_id);
            CREATE INDEX IF NOT EXISTS idx_collections_contract ON collections(contract_address);
            CREATE INDEX IF NOT EXISTS idx_collections_creator ON collections(creator_address);
            CREATE INDEX IF NOT EXISTS idx_price_history_contract ON price_history(nft_contract);
            CREATE INDEX IF NOT EXISTS idx_price_history_time ON price_history(recorded_at);
        ''')

        conn.commit()
        conn.close()

        logger.info(f"Sales analytics database initialized at {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def record_sale(
        self,
        nft_contract: str,
        token_id: str,
        network: str,
        seller: str,
        buyer: str,
        price_wei: str,
        price_native: float,
        price_usd: float,
        currency: str,
        marketplace: str,
        tx_hash: str,
        sale_timestamp: str,
        block_number: int = None,
        tracked_address_id: int = None
    ) -> Dict:
        """Record a new NFT sale"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO sales
                (nft_contract, token_id, network, seller_address, buyer_address,
                 sale_price_wei, sale_price_native, sale_price_usd, currency,
                 marketplace, tx_hash, block_number, sale_timestamp, tracked_address_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nft_contract, token_id, network, seller, buyer,
                price_wei, price_native, price_usd, currency,
                marketplace, tx_hash, block_number, sale_timestamp, tracked_address_id
            ))

            conn.commit()
            sale_id = cursor.lastrowid

            logger.info(f"Recorded sale: {nft_contract} #{token_id} for {price_native} {currency}")

            conn.close()
            return {'success': True, 'id': sale_id}

        except Exception as e:
            logger.error(f"Error recording sale: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}

    def get_cumulative_sales_for_nft(self, contract: str, token_id: str) -> Dict:
        """Get cumulative sales data for a specific NFT"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_sales,
                SUM(sale_price_native) as total_volume_native,
                SUM(sale_price_usd) as total_volume_usd,
                MAX(sale_price_native) as highest_sale_native,
                MAX(sale_price_usd) as highest_sale_usd,
                MIN(sale_price_native) as lowest_sale_native,
                MIN(sale_price_usd) as lowest_sale_usd,
                AVG(sale_price_native) as avg_price_native,
                AVG(sale_price_usd) as avg_price_usd,
                currency
            FROM sales
            WHERE nft_contract = ? AND token_id = ?
            GROUP BY currency
        ''', (contract, token_id))

        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(result)
        else:
            return {}

    def get_cumulative_sales_for_collection(self, contract: str) -> Dict:
        """Get cumulative sales data for entire collection"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(DISTINCT token_id) as unique_nfts_sold,
                COUNT(*) as total_sales,
                SUM(sale_price_native) as total_volume_native,
                SUM(sale_price_usd) as total_volume_usd,
                MAX(sale_price_native) as highest_sale_native,
                AVG(sale_price_native) as avg_price_native,
                MIN(sale_price_native) as floor_price_native,
                currency
            FROM sales
            WHERE nft_contract = ?
            GROUP BY currency
        ''', (contract,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(result)
        else:
            return {}

    def get_sales_for_tracked_address(self, address_id: int) -> List[Dict]:
        """Get all sales for NFTs from a tracked address"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM sales
            WHERE tracked_address_id = ?
            ORDER BY sale_timestamp DESC
        ''', (address_id,))

        sales = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return sales

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total sales
        cursor.execute('SELECT COUNT(*) as count FROM sales')
        stats['total_sales'] = cursor.fetchone()['count']

        # Total volume (USD)
        cursor.execute('SELECT SUM(sale_price_usd) as total FROM sales')
        result = cursor.fetchone()
        stats['total_volume_usd'] = result['total'] if result['total'] else 0

        # Unique NFTs sold
        cursor.execute('SELECT COUNT(DISTINCT nft_contract || token_id) as count FROM sales')
        stats['unique_nfts_sold'] = cursor.fetchone()['count']

        # Sales by marketplace
        cursor.execute('''
            SELECT marketplace, COUNT(*) as count, SUM(sale_price_usd) as volume
            FROM sales
            GROUP BY marketplace
        ''')
        stats['by_marketplace'] = {row['marketplace']: {
            'sales': row['count'],
            'volume_usd': row['volume']
        } for row in cursor.fetchall()}

        conn.close()
        return stats


# Singleton instance
_db_instance = None

def get_sales_db() -> SalesDB:
    """Get or create singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SalesDB()
    return _db_instance


if __name__ == '__main__':
    # Test database creation
    db = SalesDB()
    stats = db.get_stats()
    print("Sales analytics database initialized successfully!")
    print(f"Stats: {stats}")
