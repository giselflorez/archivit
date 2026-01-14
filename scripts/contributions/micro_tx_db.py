"""
Micro TX Database - SQLite schema and operations for contribution tracking

Database: db/micro_tx_contributions.db

Tables:
- contributor_profiles: User profiles linked to wallet addresses
- user_contributions: Individual contributions with validation status
- acu_meter_scores: 4-component ACU-METER score history
- verification_queue: Pending verification states
- community_votes: Stake-weighted voting
- alignment_logs: Full audit trail
- on_chain_events: Monitored blockchain events

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 8
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class ContributionType(Enum):
    MINT = 'mint'
    WISDOM_SHARE = 'wisdom_share'
    CURATION_VOTE = 'curation_vote'
    ARCHIVE_ACTION = 'archive_action'
    SOCIAL_ENDORSEMENT = 'social_endorsement'


class ValidationStatus(Enum):
    PENDING = 'pending'
    AUTO_APPROVED = 'auto_approved'
    COMMUNITY_VERIFIED = 'community_verified'
    MANUAL_APPROVED = 'manual_approved'
    REJECTED = 'rejected'


class AccessLevel(Enum):
    RESTRICTED = 'restricted'
    STANDARD = 'standard'
    ELEVATED = 'elevated'


@dataclass
class ContributorProfile:
    id: Optional[int] = None
    user_id: Optional[int] = None
    primary_address: str = ''
    display_name: Optional[str] = None
    acu_meter_score: float = 0.0
    percentile_rank: float = 0.0
    access_level: str = 'restricted'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_contribution_at: Optional[str] = None


@dataclass
class UserContribution:
    id: Optional[int] = None
    contributor_id: int = 0
    tx_hash: Optional[str] = None
    contribution_type: str = ''
    content_hash: Optional[str] = None
    content_summary: Optional[str] = None
    content_json: Optional[str] = None
    validation_status: str = 'pending'
    heart_forward_score: float = 0.0
    validation_details: Optional[str] = None
    base_weight: str = 'MEDIUM'
    calculated_weight: float = 0.0
    block_number: Optional[int] = None
    block_timestamp: Optional[str] = None
    network: str = 'ethereum'
    created_at: Optional[str] = None
    validated_at: Optional[str] = None
    processed_at: Optional[str] = None


@dataclass
class ACUMeterScore:
    id: Optional[int] = None
    contributor_id: int = 0
    intent_score: float = 0.0
    wisdom_score: float = 0.0
    application_score: float = 0.0
    legacy_score: float = 0.0
    intent_weight: float = 1.0
    wisdom_weight: float = 1.0
    application_weight: float = 1.0
    legacy_weight: float = 1.0
    weighted_total: float = 0.0
    percentile_rank: float = 0.0
    threshold_met: bool = False
    access_level: str = 'restricted'
    calculation_version: str = 'v1'
    calculated_at: Optional[str] = None


@dataclass
class AlignmentLog:
    id: Optional[int] = None
    event_type: str = ''
    contributor_id: Optional[int] = None
    contribution_id: Optional[int] = None
    action: str = ''
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    change_reason: Optional[str] = None
    triggered_by: str = 'system'
    triggering_entity: Optional[str] = None
    logged_at: Optional[str] = None


class MicroTXDatabase:
    """
    Database manager for User Micro TX Protocol.

    Handles all CRUD operations for contribution tracking,
    ACU-METER scoring, and alignment logging.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / 'db' / 'micro_tx_contributions.db'

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_database(self):
        """Initialize database with full schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # ============================================================
        # CONTRIBUTOR PROFILES
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contributor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                primary_address TEXT UNIQUE NOT NULL,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acu_meter_score REAL DEFAULT 0.0,
                percentile_rank REAL DEFAULT 0.0,
                access_level TEXT DEFAULT 'restricted',
                last_contribution_at TIMESTAMP
            )
        """)

        # ============================================================
        # USER CONTRIBUTIONS
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contributor_id INTEGER REFERENCES contributor_profiles(id) ON DELETE CASCADE,

                tx_hash TEXT UNIQUE,
                contribution_type TEXT NOT NULL,

                content_hash TEXT,
                content_summary TEXT,
                content_json TEXT,

                validation_status TEXT DEFAULT 'pending',
                heart_forward_score REAL DEFAULT 0.0,
                validation_details TEXT,

                base_weight TEXT NOT NULL,
                calculated_weight REAL DEFAULT 0.0,

                block_number INTEGER,
                block_timestamp TIMESTAMP,
                network TEXT DEFAULT 'ethereum',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated_at TIMESTAMP,
                processed_at TIMESTAMP
            )
        """)

        # ============================================================
        # ACU-METER SCORES
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acu_meter_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contributor_id INTEGER REFERENCES contributor_profiles(id) ON DELETE CASCADE,

                intent_score REAL DEFAULT 0.0,
                wisdom_score REAL DEFAULT 0.0,
                application_score REAL DEFAULT 0.0,
                legacy_score REAL DEFAULT 0.0,

                intent_weight REAL DEFAULT 1.0,
                wisdom_weight REAL DEFAULT 1.0,
                application_weight REAL DEFAULT 1.0,
                legacy_weight REAL DEFAULT 1.0,

                weighted_total REAL DEFAULT 0.0,
                percentile_rank REAL DEFAULT 0.0,

                threshold_met BOOLEAN DEFAULT FALSE,
                access_level TEXT DEFAULT 'restricted',

                calculation_version TEXT DEFAULT 'v1',
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(contributor_id, calculated_at)
            )
        """)

        # ============================================================
        # ACU THRESHOLDS
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acu_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threshold_name TEXT UNIQUE NOT NULL,
                min_percentile REAL NOT NULL,
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default thresholds
        cursor.execute("""
            INSERT OR IGNORE INTO acu_thresholds (threshold_name, min_percentile, permissions) VALUES
                ('restricted', 0, '["view", "basic_contribute"]'),
                ('standard', 75, '["view", "contribute", "vote", "archive"]'),
                ('elevated', 90, '["view", "contribute", "vote", "archive", "curate", "moderate"]')
        """)

        # ============================================================
        # VERIFICATION QUEUE
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contribution_id INTEGER REFERENCES user_contributions(id) ON DELETE CASCADE,

                keyword_score REAL DEFAULT 0.0,
                sentiment_score REAL DEFAULT 0.0,
                pattern_score REAL DEFAULT 0.0,
                automated_result TEXT,

                community_votes_for INTEGER DEFAULT 0,
                community_votes_against INTEGER DEFAULT 0,
                community_stake_weighted_score REAL DEFAULT 0.0,
                community_result TEXT,

                manual_reviewer TEXT,
                manual_result TEXT,
                manual_notes TEXT,

                final_status TEXT DEFAULT 'pending',
                verification_path TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # ============================================================
        # COMMUNITY VOTES
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contribution_id INTEGER REFERENCES user_contributions(id) ON DELETE CASCADE,
                voter_address TEXT NOT NULL,
                voter_stake REAL DEFAULT 1.0,
                vote_type TEXT NOT NULL,
                vote_reason TEXT,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(contribution_id, voter_address)
            )
        """)

        # ============================================================
        # ALIGNMENT LOGS
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alignment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                contributor_id INTEGER,
                contribution_id INTEGER,

                action TEXT NOT NULL,
                previous_state TEXT,
                new_state TEXT,
                change_reason TEXT,

                triggered_by TEXT,
                triggering_entity TEXT,

                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============================================================
        # ON-CHAIN EVENTS
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS on_chain_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,

                from_address TEXT,
                to_address TEXT,
                contract_address TEXT,
                token_id TEXT,
                value_wei TEXT,

                processed BOOLEAN DEFAULT FALSE,
                contribution_id INTEGER,

                block_number INTEGER,
                block_timestamp TIMESTAMP,
                network TEXT DEFAULT 'ethereum',
                raw_log TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============================================================
        # MONITORED ADDRESSES
        # ============================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitored_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                address_type TEXT NOT NULL,
                network TEXT DEFAULT 'ethereum',
                monitor_for TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ============================================================
        # INDEXES
        # ============================================================
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_contributions_contributor ON user_contributions(contributor_id)",
            "CREATE INDEX IF NOT EXISTS idx_contributions_type ON user_contributions(contribution_type)",
            "CREATE INDEX IF NOT EXISTS idx_contributions_status ON user_contributions(validation_status)",
            "CREATE INDEX IF NOT EXISTS idx_contributions_created ON user_contributions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_acu_scores_contributor ON acu_meter_scores(contributor_id)",
            "CREATE INDEX IF NOT EXISTS idx_acu_scores_calculated ON acu_meter_scores(calculated_at)",
            "CREATE INDEX IF NOT EXISTS idx_verification_status ON verification_queue(final_status)",
            "CREATE INDEX IF NOT EXISTS idx_alignment_logs_event ON alignment_logs(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_alignment_logs_time ON alignment_logs(logged_at)",
            "CREATE INDEX IF NOT EXISTS idx_on_chain_processed ON on_chain_events(processed)",
            "CREATE INDEX IF NOT EXISTS idx_on_chain_block ON on_chain_events(block_number)",
            "CREATE INDEX IF NOT EXISTS idx_profiles_address ON contributor_profiles(primary_address)"
        ]

        for idx in indexes:
            cursor.execute(idx)

        conn.commit()
        conn.close()

    # ================================================================
    # CONTRIBUTOR PROFILE OPERATIONS
    # ================================================================

    def get_or_create_contributor(self, address: str, display_name: str = None) -> ContributorProfile:
        """Get existing contributor or create new one."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM contributor_profiles WHERE primary_address = ?",
            (address.lower(),)
        )
        row = cursor.fetchone()

        if row:
            profile = ContributorProfile(**dict(row))
        else:
            cursor.execute("""
                INSERT INTO contributor_profiles (primary_address, display_name)
                VALUES (?, ?)
            """, (address.lower(), display_name))
            conn.commit()

            profile = ContributorProfile(
                id=cursor.lastrowid,
                primary_address=address.lower(),
                display_name=display_name,
                created_at=datetime.now().isoformat()
            )

        conn.close()
        return profile

    def update_contributor_score(self, contributor_id: int, score: float, percentile: float, access_level: str):
        """Update contributor's cached ACU-METER score."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE contributor_profiles
            SET acu_meter_score = ?, percentile_rank = ?, access_level = ?, updated_at = ?
            WHERE id = ?
        """, (score, percentile, access_level, datetime.now().isoformat(), contributor_id))

        conn.commit()
        conn.close()

    def get_contributor_by_address(self, address: str) -> Optional[ContributorProfile]:
        """Get contributor by wallet address."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM contributor_profiles WHERE primary_address = ?",
            (address.lower(),)
        )
        row = cursor.fetchone()
        conn.close()

        return ContributorProfile(**dict(row)) if row else None

    # ================================================================
    # CONTRIBUTION OPERATIONS
    # ================================================================

    def create_contribution(self, contribution: UserContribution) -> int:
        """Create new contribution record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_contributions (
                contributor_id, tx_hash, contribution_type,
                content_hash, content_summary, content_json,
                validation_status, heart_forward_score,
                base_weight, calculated_weight,
                block_number, block_timestamp, network
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contribution.contributor_id,
            contribution.tx_hash,
            contribution.contribution_type,
            contribution.content_hash,
            contribution.content_summary,
            contribution.content_json,
            contribution.validation_status,
            contribution.heart_forward_score,
            contribution.base_weight,
            contribution.calculated_weight,
            contribution.block_number,
            contribution.block_timestamp,
            contribution.network
        ))

        contribution_id = cursor.lastrowid

        # Update last contribution timestamp
        cursor.execute("""
            UPDATE contributor_profiles
            SET last_contribution_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), contribution.contributor_id))

        conn.commit()
        conn.close()

        return contribution_id

    def get_contribution(self, contribution_id: int) -> Optional[UserContribution]:
        """Get contribution by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_contributions WHERE id = ?", (contribution_id,))
        row = cursor.fetchone()
        conn.close()

        return UserContribution(**dict(row)) if row else None

    def get_contributions_by_contributor(self, contributor_id: int, limit: int = 100) -> List[UserContribution]:
        """Get all contributions for a contributor."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_contributions
            WHERE contributor_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (contributor_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [UserContribution(**dict(row)) for row in rows]

    def update_contribution_validation(
        self,
        contribution_id: int,
        status: str,
        heart_forward_score: float,
        calculated_weight: float
    ):
        """Update contribution validation status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_contributions
            SET validation_status = ?, heart_forward_score = ?,
                calculated_weight = ?, validated_at = ?
            WHERE id = ?
        """, (status, heart_forward_score, calculated_weight, datetime.now().isoformat(), contribution_id))

        conn.commit()
        conn.close()

    def count_contributions_by_type(self, contributor_id: int, contribution_type: str) -> int:
        """Count contributions of specific type."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM user_contributions
            WHERE contributor_id = ? AND contribution_type = ?
            AND validation_status IN ('auto_approved', 'community_verified', 'manual_approved')
        """, (contributor_id, contribution_type))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    # ================================================================
    # ACU-METER SCORE OPERATIONS
    # ================================================================

    def save_acu_score(self, score: ACUMeterScore) -> int:
        """Save new ACU-METER score calculation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO acu_meter_scores (
                contributor_id,
                intent_score, wisdom_score, application_score, legacy_score,
                intent_weight, wisdom_weight, application_weight, legacy_weight,
                weighted_total, percentile_rank,
                threshold_met, access_level, calculation_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score.contributor_id,
            score.intent_score, score.wisdom_score,
            score.application_score, score.legacy_score,
            score.intent_weight, score.wisdom_weight,
            score.application_weight, score.legacy_weight,
            score.weighted_total, score.percentile_rank,
            score.threshold_met, score.access_level, score.calculation_version
        ))

        score_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return score_id

    def get_latest_acu_score(self, contributor_id: int) -> Optional[ACUMeterScore]:
        """Get most recent ACU-METER score for contributor."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM acu_meter_scores
            WHERE contributor_id = ?
            ORDER BY calculated_at DESC
            LIMIT 1
        """, (contributor_id,))

        row = cursor.fetchone()
        conn.close()

        return ACUMeterScore(**dict(row)) if row else None

    def get_all_scores_for_percentile(self) -> List[Tuple[int, float]]:
        """Get all contributor scores for percentile calculation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT contributor_id, MAX(weighted_total) as score
            FROM acu_meter_scores
            GROUP BY contributor_id
            ORDER BY score DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [(row['contributor_id'], row['score']) for row in rows]

    # ================================================================
    # VERIFICATION OPERATIONS
    # ================================================================

    def create_verification_entry(self, contribution_id: int) -> int:
        """Create verification queue entry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO verification_queue (contribution_id)
            VALUES (?)
        """, (contribution_id,))

        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return entry_id

    def update_automated_verification(
        self,
        contribution_id: int,
        keyword_score: float,
        sentiment_score: float,
        pattern_score: float,
        result: str
    ):
        """Update automated verification results."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE verification_queue
            SET keyword_score = ?, sentiment_score = ?, pattern_score = ?,
                automated_result = ?
            WHERE contribution_id = ?
        """, (keyword_score, sentiment_score, pattern_score, result, contribution_id))

        conn.commit()
        conn.close()

    def record_community_vote(
        self,
        contribution_id: int,
        voter_address: str,
        voter_stake: float,
        vote_type: str,
        reason: str = None
    ):
        """Record a community vote."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO community_votes
            (contribution_id, voter_address, voter_stake, vote_type, vote_reason)
            VALUES (?, ?, ?, ?, ?)
        """, (contribution_id, voter_address.lower(), voter_stake, vote_type, reason))

        # Update vote counts
        cursor.execute("""
            UPDATE verification_queue
            SET community_votes_for = (
                SELECT COUNT(*) FROM community_votes
                WHERE contribution_id = ? AND vote_type = 'for'
            ),
            community_votes_against = (
                SELECT COUNT(*) FROM community_votes
                WHERE contribution_id = ? AND vote_type = 'against'
            ),
            community_stake_weighted_score = (
                SELECT COALESCE(
                    SUM(CASE WHEN vote_type = 'for' THEN voter_stake ELSE -voter_stake END),
                    0
                ) FROM community_votes WHERE contribution_id = ?
            )
            WHERE contribution_id = ?
        """, (contribution_id, contribution_id, contribution_id, contribution_id))

        conn.commit()
        conn.close()

    def finalize_verification(
        self,
        contribution_id: int,
        final_status: str,
        verification_path: str
    ):
        """Finalize verification with result."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE verification_queue
            SET final_status = ?, verification_path = ?, completed_at = ?
            WHERE contribution_id = ?
        """, (final_status, verification_path, datetime.now().isoformat(), contribution_id))

        conn.commit()
        conn.close()

    def get_pending_verifications(self, limit: int = 50) -> List[Dict]:
        """Get contributions pending verification."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT uc.*, vq.keyword_score, vq.sentiment_score, vq.pattern_score,
                   vq.automated_result, vq.community_votes_for, vq.community_votes_against,
                   vq.final_status
            FROM user_contributions uc
            JOIN verification_queue vq ON uc.id = vq.contribution_id
            WHERE vq.final_status = 'pending'
            ORDER BY uc.created_at ASC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ================================================================
    # ALIGNMENT LOG OPERATIONS
    # ================================================================

    def log_alignment_event(self, log: AlignmentLog) -> int:
        """Log alignment event for audit trail."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alignment_logs (
                event_type, contributor_id, contribution_id,
                action, previous_state, new_state, change_reason,
                triggered_by, triggering_entity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log.event_type, log.contributor_id, log.contribution_id,
            log.action, log.previous_state, log.new_state, log.change_reason,
            log.triggered_by, log.triggering_entity
        ))

        log_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return log_id

    def get_alignment_logs(
        self,
        contributor_id: int = None,
        event_type: str = None,
        limit: int = 100
    ) -> List[AlignmentLog]:
        """Get alignment logs with optional filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM alignment_logs WHERE 1=1"
        params = []

        if contributor_id:
            query += " AND contributor_id = ?"
            params.append(contributor_id)

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        query += " ORDER BY logged_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [AlignmentLog(**dict(row)) for row in rows]

    # ================================================================
    # STATISTICS
    # ================================================================

    def get_contribution_stats(self) -> Dict[str, Any]:
        """Get overall contribution statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total contributors
        cursor.execute("SELECT COUNT(*) FROM contributor_profiles")
        stats['total_contributors'] = cursor.fetchone()[0]

        # Total contributions
        cursor.execute("SELECT COUNT(*) FROM user_contributions")
        stats['total_contributions'] = cursor.fetchone()[0]

        # Contributions by type
        cursor.execute("""
            SELECT contribution_type, COUNT(*) as count
            FROM user_contributions
            GROUP BY contribution_type
        """)
        stats['by_type'] = {row['contribution_type']: row['count'] for row in cursor.fetchall()}

        # Contributions by status
        cursor.execute("""
            SELECT validation_status, COUNT(*) as count
            FROM user_contributions
            GROUP BY validation_status
        """)
        stats['by_status'] = {row['validation_status']: row['count'] for row in cursor.fetchall()}

        # Average ACU score
        cursor.execute("SELECT AVG(acu_meter_score) FROM contributor_profiles WHERE acu_meter_score > 0")
        stats['avg_acu_score'] = cursor.fetchone()[0] or 0.0

        # Access level distribution
        cursor.execute("""
            SELECT access_level, COUNT(*) as count
            FROM contributor_profiles
            GROUP BY access_level
        """)
        stats['access_distribution'] = {row['access_level']: row['count'] for row in cursor.fetchall()}

        conn.close()
        return stats

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top contributors by ACU-METER score."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                cp.id, cp.primary_address, cp.display_name,
                cp.acu_meter_score, cp.percentile_rank, cp.access_level,
                COUNT(uc.id) as contribution_count
            FROM contributor_profiles cp
            LEFT JOIN user_contributions uc ON cp.id = uc.contributor_id
            WHERE cp.acu_meter_score > 0
            GROUP BY cp.id
            ORDER BY cp.acu_meter_score DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]


# Initialize database on module import
if __name__ == '__main__':
    db = MicroTXDatabase()
    print(f"Database initialized at: {db.db_path}")
    stats = db.get_contribution_stats()
    print(f"Stats: {stats}")
