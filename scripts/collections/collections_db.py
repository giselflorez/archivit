#!/usr/bin/env python3
"""
Collections Database Manager
Manages hierarchical collections with art history perspective:
- Collections → Series → Works (canonical model)
- Creative Periods (like Picasso's Blue Period)
- Cross-reference intelligence (deduplicate NFTs across venues)
- Evolution analysis (subject/tone/medium tracking)
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CollectionsDB:
    """Database manager for collections and artistic periods"""

    def __init__(self, db_path: str = "db/collections.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database with collections schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('PRAGMA foreign_keys = ON')

        cursor.executescript('''
            -- Collections (top-level groupings)
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                creator_address TEXT,
                network TEXT,
                collection_type TEXT,         -- 'nft_collection', 'artistic_period', 'custom'
                start_date DATE,
                end_date DATE,
                tags TEXT,                    -- JSON array
                metadata TEXT,                -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Series (mid-level groupings within collections)
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                start_date DATE,
                end_date DATE,
                tags TEXT,                    -- JSON array
                metadata TEXT,                -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Canonical Works (the actual artworks/NFTs)
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_title TEXT NOT NULL,
                description TEXT,
                series_id INTEGER REFERENCES series(id) ON DELETE SET NULL,
                collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL,
                creation_date DATE,
                medium TEXT,                  -- 'digital', 'photography', 'generative', etc.
                tags TEXT,                    -- JSON array
                visual_signature TEXT,        -- pHash or embedding hash for deduplication
                metadata TEXT,                -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Cross-References (linking works to multiple appearances)
            CREATE TABLE IF NOT EXISTS cross_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER REFERENCES works(id) ON DELETE CASCADE,
                platform TEXT NOT NULL,       -- 'foundation', 'opensea', 'superrare', 'blog', etc.
                platform_url TEXT,
                platform_id TEXT,             -- Token ID, blog post ID, etc.
                document_id TEXT,             -- Link to knowledge base document
                nft_contract TEXT,
                nft_token_id TEXT,
                appearance_date DATE,
                is_primary BOOLEAN DEFAULT FALSE,  -- Primary canonical source
                metadata TEXT,                -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, platform_id, work_id)
            );

            -- Creative Periods (art historian perspective)
            CREATE TABLE IF NOT EXISTS creative_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,           -- e.g., "Blue Period", "Generative Phase"
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE,
                auto_detected BOOLEAN DEFAULT FALSE,  -- Auto vs manual
                dominant_subjects TEXT,       -- JSON array: ["portraits", "urban"]
                dominant_tones TEXT,          -- JSON array: ["melancholic", "vibrant"]
                dominant_mediums TEXT,        -- JSON array: ["photography", "AI"]
                tags TEXT,                    -- JSON array
                metadata TEXT,                -- JSON object with clustering features
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Period-Work associations
            CREATE TABLE IF NOT EXISTS period_works (
                period_id INTEGER REFERENCES creative_periods(id) ON DELETE CASCADE,
                work_id INTEGER REFERENCES works(id) ON DELETE CASCADE,
                confidence REAL DEFAULT 1.0,  -- Confidence of assignment (auto-detected)
                PRIMARY KEY (period_id, work_id)
            );

            -- Evolution tracking (subject/tone/medium over time)
            CREATE TABLE IF NOT EXISTS evolution_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER REFERENCES works(id) ON DELETE CASCADE,
                feature_type TEXT NOT NULL,   -- 'subject', 'tone', 'medium', 'style'
                feature_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                extracted_from TEXT,          -- 'vision_api', 'manual', 'embeddings'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_collections_creator ON collections(creator_address);
            CREATE INDEX IF NOT EXISTS idx_collections_type ON collections(collection_type);
            CREATE INDEX IF NOT EXISTS idx_series_collection ON series(collection_id);
            CREATE INDEX IF NOT EXISTS idx_works_series ON works(series_id);
            CREATE INDEX IF NOT EXISTS idx_works_collection ON works(collection_id);
            CREATE INDEX IF NOT EXISTS idx_works_signature ON works(visual_signature);
            CREATE INDEX IF NOT EXISTS idx_xref_work ON cross_references(work_id);
            CREATE INDEX IF NOT EXISTS idx_xref_platform ON cross_references(platform, platform_id);
            CREATE INDEX IF NOT EXISTS idx_xref_nft ON cross_references(nft_contract, nft_token_id);
            CREATE INDEX IF NOT EXISTS idx_periods_dates ON creative_periods(start_date, end_date);
            CREATE INDEX IF NOT EXISTS idx_evolution_work ON evolution_features(work_id);
            CREATE INDEX IF NOT EXISTS idx_evolution_type ON evolution_features(feature_type);
        ''')

        conn.commit()
        conn.close()

        logger.info(f"Collections database initialized at {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def create_collection(
        self,
        name: str,
        description: str = None,
        creator_address: str = None,
        collection_type: str = 'custom',
        tags: List[str] = None
    ) -> Dict:
        """Create a new collection"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO collections (name, description, creator_address, collection_type, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                name,
                description,
                creator_address,
                collection_type,
                json.dumps(tags or [])
            ))

            conn.commit()
            collection_id = cursor.lastrowid

            logger.info(f"Created collection: {name} (ID: {collection_id})")

            conn.close()
            return {'success': True, 'id': collection_id}

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}

    def create_work(
        self,
        canonical_title: str,
        description: str = None,
        collection_id: int = None,
        series_id: int = None,
        creation_date: str = None,
        medium: str = None,
        tags: List[str] = None,
        visual_signature: str = None
    ) -> Dict:
        """Create a canonical work"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO works
                (canonical_title, description, collection_id, series_id,
                 creation_date, medium, tags, visual_signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                canonical_title,
                description,
                collection_id,
                series_id,
                creation_date,
                medium,
                json.dumps(tags or []),
                visual_signature
            ))

            conn.commit()
            work_id = cursor.lastrowid

            logger.info(f"Created work: {canonical_title} (ID: {work_id})")

            conn.close()
            return {'success': True, 'id': work_id}

        except Exception as e:
            logger.error(f"Error creating work: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}

    def add_cross_reference(
        self,
        work_id: int,
        platform: str,
        platform_url: str = None,
        platform_id: str = None,
        document_id: str = None,
        nft_contract: str = None,
        nft_token_id: str = None,
        is_primary: bool = False
    ) -> Dict:
        """Add a cross-reference (appearance) for a work"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO cross_references
                (work_id, platform, platform_url, platform_id,
                 document_id, nft_contract, nft_token_id, is_primary,
                 appearance_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                work_id,
                platform,
                platform_url,
                platform_id,
                document_id,
                nft_contract,
                nft_token_id,
                is_primary,
                datetime.now().date().isoformat()
            ))

            conn.commit()
            xref_id = cursor.lastrowid

            logger.info(f"Added cross-reference for work {work_id} on {platform}")

            conn.close()
            return {'success': True, 'id': xref_id}

        except Exception as e:
            logger.error(f"Error adding cross-reference: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}

    def find_work_by_signature(self, visual_signature: str) -> Optional[Dict]:
        """Find work by visual signature (for deduplication)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM works
            WHERE visual_signature = ?
            LIMIT 1
        ''', (visual_signature,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return dict(result)
        return None

    def get_work_with_references(self, work_id: int) -> Dict:
        """Get work with all cross-references"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get work
        cursor.execute('SELECT * FROM works WHERE id = ?', (work_id,))
        work = cursor.fetchone()

        if not work:
            conn.close()
            return {}

        work_dict = dict(work)

        # Get cross-references
        cursor.execute('''
            SELECT * FROM cross_references
            WHERE work_id = ?
            ORDER BY is_primary DESC, appearance_date DESC
        ''', (work_id,))

        work_dict['cross_references'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return work_dict

    def create_creative_period(
        self,
        name: str,
        start_date: str,
        end_date: str = None,
        description: str = None,
        auto_detected: bool = False,
        dominant_subjects: List[str] = None,
        dominant_tones: List[str] = None,
        dominant_mediums: List[str] = None
    ) -> Dict:
        """Create a creative period (like Picasso's Blue Period)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO creative_periods
                (name, description, start_date, end_date, auto_detected,
                 dominant_subjects, dominant_tones, dominant_mediums)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                description,
                start_date,
                end_date,
                auto_detected,
                json.dumps(dominant_subjects or []),
                json.dumps(dominant_tones or []),
                json.dumps(dominant_mediums or [])
            ))

            conn.commit()
            period_id = cursor.lastrowid

            logger.info(f"Created creative period: {name} (ID: {period_id})")

            conn.close()
            return {'success': True, 'id': period_id}

        except Exception as e:
            logger.error(f"Error creating period: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}

    def assign_work_to_period(self, work_id: int, period_id: int, confidence: float = 1.0) -> Dict:
        """Assign a work to a creative period"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO period_works (period_id, work_id, confidence)
                VALUES (?, ?, ?)
            ''', (period_id, work_id, confidence))

            conn.commit()
            conn.close()

            logger.info(f"Assigned work {work_id} to period {period_id}")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error assigning work to period: {e}")
            conn.close()
            return {'success': False, 'error': str(e)}

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total counts
        cursor.execute('SELECT COUNT(*) as count FROM collections')
        stats['total_collections'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM works')
        stats['total_works'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM cross_references')
        stats['total_cross_references'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM creative_periods')
        stats['total_periods'] = cursor.fetchone()['count']

        # Works with multiple references (deduplicated)
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM (
                SELECT work_id, COUNT(*) as ref_count
                FROM cross_references
                GROUP BY work_id
                HAVING ref_count > 1
            )
        ''')
        stats['works_with_multiple_refs'] = cursor.fetchone()['count']

        conn.close()
        return stats


# Singleton instance
_db_instance = None

def get_collections_db() -> CollectionsDB:
    """Get or create singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = CollectionsDB()
    return _db_instance


if __name__ == '__main__':
    # Test database creation
    db = CollectionsDB()
    stats = db.get_stats()
    print("Collections database initialized successfully!")
    print(f"Stats: {stats}")
