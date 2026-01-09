#!/usr/bin/env python3
"""
Archive Badge Meter
===================

Assessment system that evaluates archive completeness after recursive provenance scanning.
Determines badge level based on:
- Twitter verification status
- Wallet connection count
- Works discovered vs documented
- Lost works recovered
- Blockchain verification rate
- Social proof strength

Badge Levels:
    SEED        - Just started, minimal data
    SPROUT      - Twitter verified, wallets connected
    GROWTH      - First pass complete, works detected
    BLOOM       - Multi-chain coverage, good verification
    FLOURISH    - High recovery rate, strong social proof
    LEGACY      - Complete archive, all works verified

This drives the UI badge display and unlocks features at each tier.
"""

import logging
import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BadgeLevel(Enum):
    """Archive badge levels - progression through archive completeness"""
    SEED = 1        # Just started
    SPROUT = 2      # Basic verification
    GROWTH = 3      # First scan complete
    BLOOM = 4       # Multi-chain, good coverage
    FLOURISH = 5    # High recovery, strong proof
    LEGACY = 6      # Complete archive


class ArchiveBadgeMeter:
    """
    Assess and track archive badge level based on recursive scan results

    Scoring Dimensions:
    1. Identity Verification (0-100)
       - Twitter OAuth verified
       - Multiple wallets connected
       - Cross-platform presence

    2. Discovery Coverage (0-100)
       - Works detected from social
       - Platforms covered
       - Timeline completeness

    3. Blockchain Verification (0-100)
       - Contract addresses resolved
       - Token IDs matched
       - Ownership verified

    4. Recovery Success (0-100)
       - Lost works found
       - Dead platform recovery
       - Shared contract resolution

    5. Social Proof Strength (0-100)
       - Engagement on mint posts
       - Collector witnesses
       - Cross-reference confirmation

    Badge Level = Average of all dimensions
    """

    # Score thresholds for each badge level
    BADGE_THRESHOLDS = {
        BadgeLevel.SEED: 0,
        BadgeLevel.SPROUT: 20,
        BadgeLevel.GROWTH: 40,
        BadgeLevel.BLOOM: 60,
        BadgeLevel.FLOURISH: 80,
        BadgeLevel.LEGACY: 95
    }

    # Features unlocked at each badge level
    BADGE_FEATURES = {
        BadgeLevel.SEED: [
            'Basic archive viewing',
            'Manual document upload'
        ],
        BadgeLevel.SPROUT: [
            'Twitter import',
            'Wallet connection',
            'Basic search'
        ],
        BadgeLevel.GROWTH: [
            'NFT release detection',
            'Platform coverage report',
            'Timeline view'
        ],
        BadgeLevel.BLOOM: [
            'Multi-chain tracking',
            'Collector network',
            'Edition constellation'
        ],
        BadgeLevel.FLOURISH: [
            'Lost work recovery',
            'Provenance certificates',
            'Export for legal use'
        ],
        BadgeLevel.LEGACY: [
            'Complete archive seal',
            'Public profile generation',
            'Legacy preservation mode'
        ]
    }

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialize badge tracking database"""
        db_path = Path(__file__).parent.parent.parent / 'db' / 'badge_meter.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db_conn.row_factory = sqlite3.Row

        cursor = self.db_conn.cursor()

        # Badge assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS badge_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER NOT NULL,

                -- Dimension scores (0-100)
                identity_score INTEGER DEFAULT 0,
                discovery_score INTEGER DEFAULT 0,
                verification_score INTEGER DEFAULT 0,
                recovery_score INTEGER DEFAULT 0,
                social_proof_score INTEGER DEFAULT 0,

                -- Overall
                total_score INTEGER DEFAULT 0,
                badge_level TEXT DEFAULT 'SEED',
                badge_level_numeric INTEGER DEFAULT 1,

                -- Metadata
                assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_passes_completed INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        # Dimension breakdown for detailed display
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dimension_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                dimension TEXT,
                metric TEXT,
                value REAL,
                max_value REAL,
                contribution_to_score REAL,
                FOREIGN KEY (assessment_id) REFERENCES badge_assessments(id)
            )
        ''')

        # Badge history for progression tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS badge_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER,
                old_badge TEXT,
                new_badge TEXT,
                score_change INTEGER,
                trigger_event TEXT,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.db_conn.commit()
        logger.info("Badge meter database initialized")

    def assess_archive(self, artist_id: int) -> Dict:
        """
        Perform full badge assessment for an artist's archive

        Returns comprehensive assessment with:
        - Individual dimension scores
        - Overall badge level
        - Improvement suggestions
        - Features unlocked
        """
        logger.info(f"Assessing archive badge for artist_id={artist_id}")

        # Load data from provenance scanner database
        provenance_db = Path(__file__).parent.parent.parent / 'db' / 'provenance_recovery.db'

        if not provenance_db.exists():
            return self._empty_assessment(artist_id)

        prov_conn = sqlite3.connect(str(provenance_db))
        prov_conn.row_factory = sqlite3.Row

        # Calculate each dimension
        identity = self._assess_identity(prov_conn, artist_id)
        discovery = self._assess_discovery(prov_conn, artist_id)
        verification = self._assess_verification(prov_conn, artist_id)
        recovery = self._assess_recovery(prov_conn, artist_id)
        social_proof = self._assess_social_proof(prov_conn, artist_id)

        prov_conn.close()

        # Calculate total score
        scores = [
            identity['score'],
            discovery['score'],
            verification['score'],
            recovery['score'],
            social_proof['score']
        ]
        total_score = sum(scores) // len(scores)

        # Determine badge level
        badge_level = self._score_to_badge(total_score)

        # Store assessment
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO badge_assessments
            (artist_id, identity_score, discovery_score, verification_score,
             recovery_score, social_proof_score, total_score, badge_level,
             badge_level_numeric)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            artist_id,
            identity['score'],
            discovery['score'],
            verification['score'],
            recovery['score'],
            social_proof['score'],
            total_score,
            badge_level.name,
            badge_level.value
        ))

        assessment_id = cursor.lastrowid

        # Store dimension details
        for dim, data in [
            ('identity', identity),
            ('discovery', discovery),
            ('verification', verification),
            ('recovery', recovery),
            ('social_proof', social_proof)
        ]:
            for metric, detail in data.get('details', {}).items():
                cursor.execute('''
                    INSERT INTO dimension_details
                    (assessment_id, dimension, metric, value, max_value, contribution_to_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    assessment_id,
                    dim,
                    metric,
                    detail.get('value', 0),
                    detail.get('max', 0),
                    detail.get('contribution', 0)
                ))

        self.db_conn.commit()

        # Build response
        return {
            'artist_id': artist_id,
            'assessment_id': assessment_id,
            'assessment_date': datetime.now().isoformat(),

            'badge_level': badge_level.name,
            'badge_level_numeric': badge_level.value,
            'total_score': total_score,

            'dimensions': {
                'identity': identity,
                'discovery': discovery,
                'verification': verification,
                'recovery': recovery,
                'social_proof': social_proof
            },

            'features_unlocked': self._get_unlocked_features(badge_level),
            'next_badge': self._get_next_badge_info(badge_level, total_score),
            'improvement_suggestions': self._generate_suggestions(
                identity, discovery, verification, recovery, social_proof
            )
        }

    def _assess_identity(self, prov_conn, artist_id: int) -> Dict:
        """Assess identity verification dimension"""
        cursor = prov_conn.cursor()

        cursor.execute('''
            SELECT twitter_handle, twitter_id, wallet_addresses, verification_date
            FROM verified_artists WHERE id = ?
        ''', (artist_id,))

        artist = cursor.fetchone()

        if not artist:
            return {'score': 0, 'details': {}}

        details = {}
        score = 0

        # Twitter verification (40 points)
        if artist['twitter_id']:
            score += 40
            details['twitter_verified'] = {'value': 1, 'max': 1, 'contribution': 40}
        else:
            details['twitter_verified'] = {'value': 0, 'max': 1, 'contribution': 0}

        # Wallet count (30 points for 3+ wallets)
        wallets = json.loads(artist['wallet_addresses'] or '[]')
        wallet_score = min(30, len(wallets) * 10)
        score += wallet_score
        details['wallets_connected'] = {'value': len(wallets), 'max': 3, 'contribution': wallet_score}

        # Verification age (30 points for 7+ days)
        if artist['verification_date']:
            # Older verification = more trust
            days_verified = 7  # Simplified
            age_score = min(30, days_verified * 4)
            score += age_score
            details['verification_age'] = {'value': days_verified, 'max': 7, 'contribution': age_score}

        return {'score': min(100, score), 'details': details}

    def _assess_discovery(self, prov_conn, artist_id: int) -> Dict:
        """Assess work discovery dimension"""
        cursor = prov_conn.cursor()

        details = {}
        score = 0

        # Count detected works
        cursor.execute('''
            SELECT COUNT(*) as count FROM social_nft_mentions
            WHERE artist_id = ? AND mention_type = 'mint'
        ''', (artist_id,))
        mint_count = cursor.fetchone()['count']

        # Works detected (40 points for 20+ works)
        work_score = min(40, mint_count * 2)
        score += work_score
        details['works_detected'] = {'value': mint_count, 'max': 20, 'contribution': work_score}

        # Platform coverage (30 points for 5+ platforms)
        cursor.execute('''
            SELECT COUNT(DISTINCT platform_detected) as count
            FROM social_nft_mentions WHERE artist_id = ?
        ''', (artist_id,))
        platform_count = cursor.fetchone()['count']

        platform_score = min(30, platform_count * 6)
        score += platform_score
        details['platforms_covered'] = {'value': platform_count, 'max': 5, 'contribution': platform_score}

        # Collections detected (30 points for 10+ collections)
        cursor.execute('''
            SELECT COUNT(*) as count FROM social_nft_mentions
            WHERE artist_id = ? AND mention_type = 'collect'
        ''', (artist_id,))
        collect_count = cursor.fetchone()['count']

        collect_score = min(30, collect_count * 3)
        score += collect_score
        details['collections_detected'] = {'value': collect_count, 'max': 10, 'contribution': collect_score}

        return {'score': min(100, score), 'details': details}

    def _assess_verification(self, prov_conn, artist_id: int) -> Dict:
        """Assess blockchain verification dimension"""
        cursor = prov_conn.cursor()

        details = {}
        score = 0

        # Verification rate
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN blockchain_verified = 1 THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN contract_address IS NOT NULL THEN 1 ELSE 0 END) as has_contract
            FROM social_nft_mentions WHERE artist_id = ?
        ''', (artist_id,))

        stats = cursor.fetchone()
        total = stats['total'] or 1
        verified = stats['verified'] or 0
        has_contract = stats['has_contract'] or 0

        # Blockchain verified (50 points)
        verify_rate = (verified / total) * 100 if total > 0 else 0
        verify_score = int(verify_rate * 0.5)
        score += verify_score
        details['blockchain_verified_rate'] = {
            'value': round(verify_rate, 1),
            'max': 100,
            'contribution': verify_score
        }

        # Contract resolution (30 points)
        contract_rate = (has_contract / total) * 100 if total > 0 else 0
        contract_score = int(contract_rate * 0.3)
        score += contract_score
        details['contract_resolution_rate'] = {
            'value': round(contract_rate, 1),
            'max': 100,
            'contribution': contract_score
        }

        # Ownership match (20 points)
        cursor.execute('''
            SELECT SUM(CASE WHEN ownership_matches_artist = 1 THEN 1 ELSE 0 END) as matches
            FROM social_nft_mentions WHERE artist_id = ? AND blockchain_verified = 1
        ''', (artist_id,))
        matches = cursor.fetchone()['matches'] or 0
        match_rate = (matches / verified) * 100 if verified > 0 else 0
        match_score = int(match_rate * 0.2)
        score += match_score
        details['ownership_match_rate'] = {
            'value': round(match_rate, 1),
            'max': 100,
            'contribution': match_score
        }

        return {'score': min(100, score), 'details': details}

    def _assess_recovery(self, prov_conn, artist_id: int) -> Dict:
        """Assess lost work recovery dimension"""
        cursor = prov_conn.cursor()

        details = {}
        score = 0

        # Count lost works and recovery status
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN recovery_status = 'recovered' THEN 1 ELSE 0 END) as recovered
            FROM lost_works WHERE artist_id = ?
        ''', (artist_id,))

        stats = cursor.fetchone()
        total_lost = stats['total'] or 0
        recovered = stats['recovered'] or 0

        # No lost works = full points
        if total_lost == 0:
            score = 100
            details['no_lost_works'] = {'value': 1, 'max': 1, 'contribution': 100}
        else:
            # Recovery rate (70 points)
            recovery_rate = (recovered / total_lost) * 100
            recovery_score = int(recovery_rate * 0.7)
            score += recovery_score
            details['recovery_rate'] = {
                'value': round(recovery_rate, 1),
                'max': 100,
                'contribution': recovery_score
            }

            # Investigation progress (30 points for attempted)
            cursor.execute('''
                SELECT COUNT(*) as investigating
                FROM lost_works WHERE artist_id = ? AND recovery_status != 'detected'
            ''', (artist_id,))
            investigating = cursor.fetchone()['investigating'] or 0
            invest_rate = (investigating / total_lost) * 100
            invest_score = int(invest_rate * 0.3)
            score += invest_score
            details['investigation_progress'] = {
                'value': investigating,
                'max': total_lost,
                'contribution': invest_score
            }

        return {'score': min(100, score), 'details': details}

    def _assess_social_proof(self, prov_conn, artist_id: int) -> Dict:
        """Assess social proof strength dimension"""
        cursor = prov_conn.cursor()

        details = {}
        score = 0

        # Average engagement on mint posts
        cursor.execute('''
            SELECT AVG(engagement_score) as avg_engagement,
                   AVG(reply_count) as avg_replies
            FROM social_nft_mentions
            WHERE artist_id = ? AND mention_type = 'mint'
        ''', (artist_id,))

        stats = cursor.fetchone()
        avg_engagement = stats['avg_engagement'] or 0
        avg_replies = stats['avg_replies'] or 0

        # Engagement score (40 points)
        engagement_score = min(40, int(avg_engagement / 10))
        score += engagement_score
        details['avg_engagement'] = {'value': round(avg_engagement, 1), 'max': 400, 'contribution': engagement_score}

        # Reply/witness count (30 points)
        reply_score = min(30, int(avg_replies * 3))
        score += reply_score
        details['avg_witnesses'] = {'value': round(avg_replies, 1), 'max': 10, 'contribution': reply_score}

        # Image availability (30 points)
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN image_urls IS NOT NULL AND image_urls != '[]' THEN 1 ELSE 0 END) as has_images
            FROM social_nft_mentions WHERE artist_id = ?
        ''', (artist_id,))

        img_stats = cursor.fetchone()
        total = img_stats['total'] or 1
        has_images = img_stats['has_images'] or 0
        image_rate = (has_images / total) * 100
        image_score = int(image_rate * 0.3)
        score += image_score
        details['image_availability'] = {
            'value': round(image_rate, 1),
            'max': 100,
            'contribution': image_score
        }

        return {'score': min(100, score), 'details': details}

    def _score_to_badge(self, score: int) -> BadgeLevel:
        """Convert score to badge level"""
        for badge in reversed(list(BadgeLevel)):
            if score >= self.BADGE_THRESHOLDS[badge]:
                return badge
        return BadgeLevel.SEED

    def _get_unlocked_features(self, badge_level: BadgeLevel) -> List[str]:
        """Get all features unlocked up to current badge level"""
        features = []
        for badge in BadgeLevel:
            if badge.value <= badge_level.value:
                features.extend(self.BADGE_FEATURES.get(badge, []))
        return features

    def _get_next_badge_info(self, current: BadgeLevel, score: int) -> Optional[Dict]:
        """Get info about next badge level"""
        if current == BadgeLevel.LEGACY:
            return None

        next_badge = BadgeLevel(current.value + 1)
        threshold = self.BADGE_THRESHOLDS[next_badge]
        points_needed = threshold - score

        return {
            'badge': next_badge.name,
            'threshold': threshold,
            'points_needed': max(0, points_needed),
            'features_unlocked': self.BADGE_FEATURES.get(next_badge, [])
        }

    def _generate_suggestions(self, identity, discovery, verification, recovery, social) -> List[str]:
        """Generate improvement suggestions based on lowest scoring dimensions"""
        suggestions = []

        # Find weakest dimension
        scores = [
            ('identity', identity['score']),
            ('discovery', discovery['score']),
            ('verification', verification['score']),
            ('recovery', recovery['score']),
            ('social_proof', social['score'])
        ]

        scores.sort(key=lambda x: x[1])

        # Generate suggestions for lowest dimensions
        for dim, score in scores[:2]:
            if dim == 'identity' and score < 80:
                suggestions.append("Connect additional wallets to improve identity verification")
                suggestions.append("Ensure Twitter account is fully verified with OAuth")

            elif dim == 'discovery' and score < 80:
                suggestions.append("Run recursive scan to detect more NFT releases from your timeline")
                suggestions.append("The scanner checks for mint announcements, collection posts, and sale confirmations")

            elif dim == 'verification' and score < 80:
                suggestions.append("Cross-reference detected works with blockchain data")
                suggestions.append("Verify contract addresses for detected NFT mentions")

            elif dim == 'recovery' and score < 80:
                suggestions.append("Investigate anomalous works - some may be on shared contracts")
                suggestions.append("Use Wayback Machine recovery for dead platform links")

            elif dim == 'social_proof' and score < 80:
                suggestions.append("Higher engagement on mint announcements strengthens provenance")
                suggestions.append("Collector replies act as witnesses to your ownership")

        return suggestions

    def _empty_assessment(self, artist_id: int) -> Dict:
        """Return empty assessment when no data exists"""
        return {
            'artist_id': artist_id,
            'badge_level': 'SEED',
            'badge_level_numeric': 1,
            'total_score': 0,
            'dimensions': {
                'identity': {'score': 0, 'details': {}},
                'discovery': {'score': 0, 'details': {}},
                'verification': {'score': 0, 'details': {}},
                'recovery': {'score': 0, 'details': {}},
                'social_proof': {'score': 0, 'details': {}}
            },
            'features_unlocked': self.BADGE_FEATURES[BadgeLevel.SEED],
            'next_badge': self._get_next_badge_info(BadgeLevel.SEED, 0),
            'improvement_suggestions': [
                'Complete Twitter verification to begin',
                'Connect at least one wallet address',
                'Run initial recursive scan on your timeline'
            ]
        }

    def get_badge_display(self, badge_level: str) -> Dict:
        """Get display data for a badge level (icons, colors, etc.)"""
        badge_display = {
            'SEED': {
                'icon': 'circle',
                'color': '#6b7280',
                'glow': 'rgba(107, 114, 128, 0.3)',
                'description': 'Archive initiated'
            },
            'SPROUT': {
                'icon': 'circle-dot',
                'color': '#84cc16',
                'glow': 'rgba(132, 204, 22, 0.4)',
                'description': 'Identity verified'
            },
            'GROWTH': {
                'icon': 'diamond',
                'color': '#22c55e',
                'glow': 'rgba(34, 197, 94, 0.5)',
                'description': 'Works detected'
            },
            'BLOOM': {
                'icon': 'hexagon',
                'color': '#3b82f6',
                'glow': 'rgba(59, 130, 246, 0.5)',
                'description': 'Multi-chain verified'
            },
            'FLOURISH': {
                'icon': 'star',
                'color': '#a855f7',
                'glow': 'rgba(168, 85, 247, 0.6)',
                'description': 'Recovery complete'
            },
            'LEGACY': {
                'icon': 'crown',
                'color': '#d4a574',
                'glow': 'rgba(212, 165, 116, 0.7)',
                'description': 'Archive sealed'
            }
        }
        return badge_display.get(badge_level, badge_display['SEED'])


# CLI interface
if __name__ == '__main__':
    import sys

    meter = ArchiveBadgeMeter()

    if len(sys.argv) < 2:
        print("""
Archive Badge Meter
===================

Usage:
  python archive_badge_meter.py assess <artist_id>
  python archive_badge_meter.py levels

Examples:
  # Assess an artist's archive
  python archive_badge_meter.py assess 1

  # Show all badge levels
  python archive_badge_meter.py levels
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'assess':
        artist_id = int(sys.argv[2])
        result = meter.assess_archive(artist_id)
        print(json.dumps(result, indent=2))

    elif command == 'levels':
        print("\nArchive Badge Levels:")
        print("=" * 60)
        for badge in BadgeLevel:
            threshold = meter.BADGE_THRESHOLDS[badge]
            features = meter.BADGE_FEATURES.get(badge, [])
            display = meter.get_badge_display(badge.name)

            print(f"\n{badge.name} (Level {badge.value})")
            print(f"  Threshold: {threshold} points")
            print(f"  {display['description']}")
            print(f"  Features:")
            for feature in features:
                print(f"    - {feature}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
