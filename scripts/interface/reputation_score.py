#!/usr/bin/env python3
"""
Reputation Score Algorithm v2
==============================

ONE-TIME badge assessment at Twitter certification.
AUTHENTICITY-FOCUSED algorithm measuring REAL activity, not volume.

The Problem:
    - Volume metrics are easily faked (wash trading, sybil wallets)
    - Dead-end wallets inflate collector counts
    - Circular trading creates fake price history
    - Burst-and-silence patterns indicate artificial inflation

What We Actually Measure:
    - Are collectors REAL active wallets, not sybils?
    - Is trading organic, not circular/wash?
    - Do wallets show signs of life?
    - Does growth pattern look natural?

4 Reputation States:
    VERIFIED     - Authentic network, organic activity (top 25%)
    ESTABLISHED  - Good signals, some minor flags (25-60%)
    EMERGING     - Building presence, limited data (60-85%)
    UNCERTAIN    - Red flags detected (bottom 15%)

Algorithm Weights:
    Collector Vitality     35% - Are collectors real & active?
    Network Authenticity   30% - Connected to real ecosystem?
    Transaction Legitimacy 20% - Organic sales patterns?
    Timeline Health        15% - Natural growth over time?
"""

import logging
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import statistics
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.network_authenticity_analyzer import (
    NetworkAuthenticityAnalyzer,
    NetworkAnalysis,
    SuspicionLevel,
    WalletProfile
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReputationState(Enum):
    """4 reputation states - one-time badge assignment"""
    VERIFIED = 4      # Top tier - authentic activity
    ESTABLISHED = 3   # Standard - good signals
    EMERGING = 2      # Building - limited data
    UNCERTAIN = 1     # Red flags detected


@dataclass
class AuthenticityMetrics:
    """
    Authenticity-focused metrics from network analysis.

    These measure REAL activity, not volume.
    """
    # Collector Vitality
    total_collectors: int = 0
    verified_real_collectors: int = 0      # High vitality wallets
    suspicious_collectors: int = 0         # Low vitality / flagged
    dead_end_wallets: int = 0              # No activity after receiving
    single_artist_collectors: int = 0      # Only collect this artist (sybil indicator)

    # Network Authenticity
    sybil_cluster_count: int = 0           # Groups of likely same-owner wallets
    sybil_wallet_count: int = 0            # Total wallets in sybil clusters
    circular_trading_detected: bool = False
    circular_ring_wallets: int = 0
    shared_funding_clusters: int = 0       # Wallets funded from same source
    ecosystem_connected_collectors: int = 0  # Collectors who collect OTHER artists

    # Transaction Legitimacy
    total_sales_count: int = 0
    suspicious_sales_count: int = 0
    legitimate_volume_eth: float = 0.0
    suspicious_volume_eth: float = 0.0
    wash_trade_indicators: int = 0
    quick_flip_count: int = 0              # Sold within 24 hours

    # Timeline Health
    activity_pattern: str = "unknown"      # organic, burst_silence, declining, growing
    growth_consistency: float = 0.0        # 0-100
    active_months_count: int = 0
    longest_silence_days: int = 0          # Longest gap in activity

    # Social Identity
    collectors_with_ens: int = 0
    collectors_with_twitter: int = 0

    # Raw findings for display
    findings: List[Dict] = field(default_factory=list)


class ReputationScorer:
    """
    Calculate reputation score using AUTHENTICITY metrics.

    This is NOT about how many NFTs you sold.
    This is about: Are those sales REAL?

    Weights:
        Collector Vitality:     35%
        Network Authenticity:   30%
        Transaction Legitimacy: 20%
        Timeline Health:        15%
    """

    # Weights focused on AUTHENTICITY, not volume
    WEIGHTS = {
        'collector_vitality': 0.35,      # Are collectors real?
        'network_authenticity': 0.30,    # Real ecosystem connections?
        'transaction_legitimacy': 0.20,  # Organic trading?
        'timeline_health': 0.15          # Natural growth?
    }

    # Percentile thresholds for reputation states
    STATE_THRESHOLDS = {
        ReputationState.VERIFIED: 75,      # Top 25%
        ReputationState.ESTABLISHED: 40,   # 40-75%
        ReputationState.EMERGING: 15,      # 15-40%
        ReputationState.UNCERTAIN: 0       # Bottom 15%
    }

    def __init__(self):
        self._init_db()
        self.network_analyzer = NetworkAuthenticityAnalyzer()

    def _init_db(self):
        """Initialize reputation database"""
        db_path = Path(__file__).parent.parent.parent / 'db' / 'reputation_scores.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db_conn.row_factory = sqlite3.Row

        cursor = self.db_conn.cursor()

        # Artist reputation scores (v2 schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reputation_scores_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER NOT NULL UNIQUE,
                twitter_handle TEXT,
                wallet_address TEXT,

                -- Raw metrics (JSON blob)
                authenticity_metrics TEXT,

                -- Component scores (0-100)
                collector_vitality_score REAL,
                network_authenticity_score REAL,
                transaction_legitimacy_score REAL,
                timeline_health_score REAL,

                -- Final calculations
                weighted_score REAL,
                percentile_rank REAL,
                reputation_state TEXT,
                suspicion_level TEXT,

                -- Red flag counts
                sybil_clusters_found INTEGER DEFAULT 0,
                circular_rings_found INTEGER DEFAULT 0,
                dead_end_wallets_found INTEGER DEFAULT 0,
                wash_trade_indicators INTEGER DEFAULT 0,

                -- Positive signals
                verified_collectors_count INTEGER DEFAULT 0,
                ecosystem_connections INTEGER DEFAULT 0,

                -- Comparison data
                compared_against_count INTEGER,

                -- Timestamps
                certified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_completed_at TIMESTAMP
            )
        ''')

        # Historical scores for calibration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authenticity_distribution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                score_value REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.db_conn.commit()
        logger.info("Reputation score database initialized (v2 - authenticity focused)")

    def assess_artist(self, artist_id: int,
                      wallet_address: str,
                      twitter_handle: str = None,
                      collector_addresses: List[str] = None,
                      transfers: List[Dict] = None) -> Dict:
        """
        Perform ONE-TIME authenticity assessment.

        This is called at Twitter certification to assign the badge.

        Args:
            artist_id: Internal artist ID
            wallet_address: Artist's primary wallet
            twitter_handle: Verified Twitter handle
            collector_addresses: All wallets that collected from this artist
            transfers: All NFT transfers involving this artist's works

        Returns:
            Assessment result with badge state and detailed breakdown
        """
        logger.info(f"Assessing authenticity for artist_id={artist_id}")

        # Run network analysis
        network_analysis = self.network_analyzer.analyze_artist_network(
            artist_address=wallet_address,
            collector_addresses=collector_addresses or [],
            transfers=transfers or []
        )

        # Convert to our metrics format
        metrics = self._extract_metrics(network_analysis)

        # Calculate component scores
        vitality_score = self._calc_collector_vitality(metrics)
        network_score = self._calc_network_authenticity(metrics)
        transaction_score = self._calc_transaction_legitimacy(metrics)
        timeline_score = self._calc_timeline_health(metrics)

        # Weighted combination
        weighted_score = (
            vitality_score * self.WEIGHTS['collector_vitality'] +
            network_score * self.WEIGHTS['network_authenticity'] +
            transaction_score * self.WEIGHTS['transaction_legitimacy'] +
            timeline_score * self.WEIGHTS['timeline_health']
        )

        # Get percentile rank
        percentile_rank = self._calculate_percentile(weighted_score)

        # Determine reputation state
        reputation_state = self._score_to_state(percentile_rank, network_analysis.suspicion_level)

        # Get comparison context
        comparison_context = self._get_comparison_context()

        # Store the score
        self._store_score(
            artist_id=artist_id,
            wallet_address=wallet_address,
            twitter_handle=twitter_handle,
            metrics=metrics,
            vitality_score=vitality_score,
            network_score=network_score,
            transaction_score=transaction_score,
            timeline_score=timeline_score,
            weighted_score=weighted_score,
            percentile_rank=percentile_rank,
            reputation_state=reputation_state,
            network_analysis=network_analysis
        )

        return {
            'artist_id': artist_id,
            'wallet_address': wallet_address,
            'twitter_handle': twitter_handle,
            'certified_at': datetime.now().isoformat(),

            'weighted_score': round(weighted_score, 2),
            'percentile_rank': round(percentile_rank, 1),
            'reputation_state': reputation_state.name,
            'suspicion_level': network_analysis.suspicion_level.value,

            'component_scores': {
                'collector_vitality': {
                    'score': round(vitality_score, 2),
                    'weight': f"{self.WEIGHTS['collector_vitality']*100:.0f}%",
                    'contribution': round(vitality_score * self.WEIGHTS['collector_vitality'], 2),
                    'description': 'Are your collectors real, active wallets?'
                },
                'network_authenticity': {
                    'score': round(network_score, 2),
                    'weight': f"{self.WEIGHTS['network_authenticity']*100:.0f}%",
                    'contribution': round(network_score * self.WEIGHTS['network_authenticity'], 2),
                    'description': 'Is your collector network connected to the real ecosystem?'
                },
                'transaction_legitimacy': {
                    'score': round(transaction_score, 2),
                    'weight': f"{self.WEIGHTS['transaction_legitimacy']*100:.0f}%",
                    'contribution': round(transaction_score * self.WEIGHTS['transaction_legitimacy'], 2),
                    'description': 'Do your sales look organic?'
                },
                'timeline_health': {
                    'score': round(timeline_score, 2),
                    'weight': f"{self.WEIGHTS['timeline_health']*100:.0f}%",
                    'contribution': round(timeline_score * self.WEIGHTS['timeline_health'], 2),
                    'description': 'Is your growth pattern natural?'
                }
            },

            'authenticity_breakdown': self._get_authenticity_breakdown(metrics, network_analysis),
            'red_flags': self._get_red_flags(network_analysis),
            'positive_signals': self._get_positive_signals(metrics, network_analysis),

            'comparison_context': comparison_context,
            'badge_display': self._get_badge_display(reputation_state)
        }

    def _extract_metrics(self, analysis: NetworkAnalysis) -> AuthenticityMetrics:
        """Extract our metrics from network analysis"""
        metrics = AuthenticityMetrics(
            total_collectors=analysis.total_collectors,
            verified_real_collectors=analysis.verified_real_collectors,
            suspicious_collectors=analysis.suspicious_collectors,
            dead_end_wallets=analysis.dead_end_wallets,

            sybil_cluster_count=analysis.sybil_cluster_count,
            circular_trading_detected=analysis.circular_trading_detected,
            circular_ring_wallets=analysis.circular_ring_size,

            wash_trade_indicators=analysis.wash_trade_indicators,
            legitimate_volume_eth=analysis.legitimate_volume_eth,
            suspicious_volume_eth=analysis.self_dealing_volume_eth,

            activity_pattern=analysis.activity_pattern,
            growth_consistency=analysis.growth_consistency,

            findings=analysis.findings
        )

        return metrics

    # =========================================================================
    # Component Score Calculations
    # =========================================================================

    def _calc_collector_vitality(self, m: AuthenticityMetrics) -> float:
        """
        Collector Vitality Score (0-100)

        Are your collectors REAL people with active wallets?

        Penalizes:
            - Dead-end wallets (no activity after receiving)
            - Single-artist collectors (sybil indicator)
            - Suspicious/low-vitality wallets

        Rewards:
            - Verified real collectors
            - Collectors with ENS/Twitter
            - Diverse collecting patterns
        """
        if m.total_collectors == 0:
            return 50  # No collectors yet - neutral

        score = 50  # Start neutral

        # Positive: verified real collectors
        real_ratio = m.verified_real_collectors / m.total_collectors
        score += real_ratio * 30  # Up to +30

        # Positive: collectors with identity (ENS, Twitter)
        identity_ratio = (m.collectors_with_ens + m.collectors_with_twitter) / m.total_collectors
        score += min(10, identity_ratio * 15)  # Up to +10

        # Negative: dead-end wallets
        dead_ratio = m.dead_end_wallets / m.total_collectors
        score -= dead_ratio * 25  # Up to -25

        # Negative: single-artist collectors (sybil indicator)
        single_ratio = m.single_artist_collectors / m.total_collectors
        score -= single_ratio * 20  # Up to -20

        # Negative: suspicious collectors
        suspicious_ratio = m.suspicious_collectors / m.total_collectors
        score -= suspicious_ratio * 15  # Up to -15

        return max(0, min(100, score))

    def _calc_network_authenticity(self, m: AuthenticityMetrics) -> float:
        """
        Network Authenticity Score (0-100)

        Is your collector network connected to the REAL ecosystem?
        Or is it an isolated cluster of fake wallets?

        Penalizes:
            - Sybil clusters (wallets controlled by same entity)
            - Circular trading rings
            - Shared funding sources

        Rewards:
            - Collectors who collect OTHER artists
            - Diverse funding sources
            - Second-degree connections
        """
        if m.total_collectors == 0:
            return 50

        score = 70  # Start optimistic

        # Major penalty: sybil clusters
        if m.sybil_cluster_count > 0:
            sybil_ratio = m.sybil_wallet_count / m.total_collectors
            score -= min(35, sybil_ratio * 50 + m.sybil_cluster_count * 5)

        # Major penalty: circular trading
        if m.circular_trading_detected:
            ring_ratio = m.circular_ring_wallets / m.total_collectors
            score -= min(30, ring_ratio * 40 + 10)  # Base penalty + ratio

        # Positive: ecosystem connections
        if m.ecosystem_connected_collectors > 0:
            eco_ratio = m.ecosystem_connected_collectors / m.total_collectors
            score += eco_ratio * 25  # Up to +25

        return max(0, min(100, score))

    def _calc_transaction_legitimacy(self, m: AuthenticityMetrics) -> float:
        """
        Transaction Legitimacy Score (0-100)

        Do your sales look organic?

        Penalizes:
            - Wash trading indicators
            - Quick flips (sold within 24 hours)
            - Suspicious volume

        Rewards:
            - Legitimate volume
            - Reasonable hold times
            - Diverse buyers
        """
        total_volume = m.legitimate_volume_eth + m.suspicious_volume_eth

        if total_volume == 0:
            return 50  # No sales yet - neutral

        score = 50  # Start neutral

        # Positive: legitimate volume ratio
        legit_ratio = m.legitimate_volume_eth / total_volume
        score += legit_ratio * 35  # Up to +35

        # Negative: wash trade indicators
        if m.wash_trade_indicators > 0:
            indicator_penalty = min(25, m.wash_trade_indicators * 5)
            score -= indicator_penalty

        # Negative: quick flips
        if m.total_sales_count > 0:
            flip_ratio = m.quick_flip_count / m.total_sales_count
            score -= flip_ratio * 15  # Up to -15

        # Bonus: no suspicious activity
        if m.suspicious_sales_count == 0 and m.wash_trade_indicators == 0:
            score += 15

        return max(0, min(100, score))

    def _calc_timeline_health(self, m: AuthenticityMetrics) -> float:
        """
        Timeline Health Score (0-100)

        Does your growth pattern look natural?

        Penalizes:
            - Burst-and-silence patterns
            - Long gaps in activity
            - Artificial-looking growth

        Rewards:
            - Gradual, sustained growth
            - Consistent activity over time
            - Natural patterns
        """
        score = 50  # Start neutral

        # Pattern-based scoring
        pattern_scores = {
            'organic': 85,
            'growing': 90,
            'declining': 50,
            'burst_silence': 20,
            'limited_data': 50,
            'no_data': 50,
            'unknown': 50
        }

        base_score = pattern_scores.get(m.activity_pattern, 50)
        score = base_score

        # Adjust for consistency
        if m.growth_consistency > 0:
            consistency_bonus = (m.growth_consistency - 50) / 5  # -10 to +10
            score += consistency_bonus

        # Penalty for long silences
        if m.longest_silence_days > 180:  # 6 months
            silence_penalty = min(20, (m.longest_silence_days - 180) / 30)
            score -= silence_penalty

        # Bonus for sustained activity
        if m.active_months_count > 12:
            score += min(10, (m.active_months_count - 12) * 0.5)

        return max(0, min(100, score))

    # =========================================================================
    # Comparative Analysis
    # =========================================================================

    def _calculate_percentile(self, score: float) -> float:
        """Calculate percentile rank against all other assessed artists"""
        cursor = self.db_conn.cursor()

        cursor.execute('SELECT weighted_score FROM reputation_scores_v2')
        all_scores = [row['weighted_score'] for row in cursor.fetchall()]

        if not all_scores:
            # First artist - use absolute thresholds
            if score >= 80:
                return 90
            elif score >= 60:
                return 70
            elif score >= 40:
                return 50
            elif score >= 20:
                return 30
            else:
                return 10

        all_scores.append(score)
        all_scores.sort()

        position = all_scores.index(score)
        percentile = (position / len(all_scores)) * 100

        return percentile

    def _score_to_state(self, percentile: float,
                        suspicion_level: SuspicionLevel) -> ReputationState:
        """
        Convert percentile rank to reputation state.

        Can be OVERRIDDEN by severe red flags regardless of percentile.
        """
        # Severe suspicion = automatic UNCERTAIN
        if suspicion_level == SuspicionLevel.SEVERE:
            return ReputationState.UNCERTAIN

        # High suspicion caps at EMERGING
        if suspicion_level == SuspicionLevel.HIGH:
            if percentile >= self.STATE_THRESHOLDS[ReputationState.ESTABLISHED]:
                return ReputationState.EMERGING

        # Normal percentile-based assignment
        if percentile >= self.STATE_THRESHOLDS[ReputationState.VERIFIED]:
            return ReputationState.VERIFIED
        elif percentile >= self.STATE_THRESHOLDS[ReputationState.ESTABLISHED]:
            return ReputationState.ESTABLISHED
        elif percentile >= self.STATE_THRESHOLDS[ReputationState.EMERGING]:
            return ReputationState.EMERGING
        else:
            return ReputationState.UNCERTAIN

    def _get_comparison_context(self) -> Dict:
        """Get statistical context for comparison"""
        cursor = self.db_conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_artists,
                AVG(weighted_score) as avg_score,
                MIN(weighted_score) as min_score,
                MAX(weighted_score) as max_score
            FROM reputation_scores_v2
        ''')

        stats = cursor.fetchone()

        if not stats or stats['total_artists'] == 0:
            return {
                'total_artists_assessed': 0,
                'note': 'First artist - comparative data will build over time'
            }

        cursor.execute('SELECT weighted_score FROM reputation_scores_v2')
        scores = [row['weighted_score'] for row in cursor.fetchall()]

        return {
            'total_artists_assessed': stats['total_artists'],
            'average_score': round(stats['avg_score'], 2) if stats['avg_score'] else 0,
            'score_range': {
                'min': round(stats['min_score'], 2) if stats['min_score'] else 0,
                'max': round(stats['max_score'], 2) if stats['max_score'] else 0
            },
            'standard_deviation': round(statistics.stdev(scores), 2) if len(scores) > 1 else 0
        }

    # =========================================================================
    # Display Helpers
    # =========================================================================

    def _get_authenticity_breakdown(self, m: AuthenticityMetrics,
                                     analysis: NetworkAnalysis) -> Dict:
        """Get human-readable authenticity breakdown"""
        if m.total_collectors == 0:
            return {
                'summary': 'No collector data available yet',
                'collectors': None
            }

        return {
            'summary': f"{m.verified_real_collectors}/{m.total_collectors} collectors verified as active",
            'collectors': {
                'total': m.total_collectors,
                'verified_real': m.verified_real_collectors,
                'dead_end_wallets': m.dead_end_wallets,
                'suspicious': m.suspicious_collectors,
                'with_identity': m.collectors_with_ens + m.collectors_with_twitter
            },
            'network': {
                'sybil_clusters': m.sybil_cluster_count,
                'circular_trading': m.circular_trading_detected,
                'ecosystem_connected': m.ecosystem_connected_collectors
            },
            'transactions': {
                'legitimate_volume_eth': round(m.legitimate_volume_eth, 4),
                'suspicious_volume_eth': round(m.suspicious_volume_eth, 4),
                'wash_trade_indicators': m.wash_trade_indicators
            },
            'timeline': {
                'pattern': m.activity_pattern,
                'consistency': round(m.growth_consistency, 1),
                'active_months': m.active_months_count
            }
        }

    def _get_red_flags(self, analysis: NetworkAnalysis) -> List[Dict]:
        """Extract red flags from analysis findings"""
        red_flags = []

        for finding in analysis.findings:
            if finding.get('severity') in ['high', 'moderate', 'critical']:
                red_flags.append({
                    'type': finding['type'],
                    'severity': finding['severity'],
                    'title': finding['title'],
                    'description': finding['description']
                })

        return red_flags

    def _get_positive_signals(self, m: AuthenticityMetrics,
                               analysis: NetworkAnalysis) -> List[Dict]:
        """Extract positive signals"""
        signals = []

        # Verified collectors
        if m.verified_real_collectors > 0:
            signals.append({
                'type': 'verified_collectors',
                'title': f'{m.verified_real_collectors} verified real collectors',
                'description': 'These wallets show diverse activity and authentic engagement'
            })

        # Ecosystem connections
        if m.ecosystem_connected_collectors > 0:
            signals.append({
                'type': 'ecosystem_connected',
                'title': f'{m.ecosystem_connected_collectors} collectors active in broader ecosystem',
                'description': 'These collectors also support other artists'
            })

        # Healthy timeline
        if m.activity_pattern in ['organic', 'growing']:
            signals.append({
                'type': 'healthy_timeline',
                'title': f'{m.activity_pattern.title()} growth pattern',
                'description': 'Activity shows natural, sustained growth over time'
            })

        # No wash trading
        if m.wash_trade_indicators == 0 and m.legitimate_volume_eth > 0:
            signals.append({
                'type': 'clean_transactions',
                'title': 'No wash trading detected',
                'description': 'All transactions appear organic'
            })

        return signals

    def _get_badge_display(self, state: ReputationState) -> Dict:
        """Get visual display data for the reputation badge"""

        # Green-to-red spectrum as requested
        displays = {
            ReputationState.VERIFIED: {
                'label': 'VERIFIED',
                'color': '#22c55e',          # Green
                'color_light': '#4ade80',
                'color_dark': '#15803d',
                'glow': 'rgba(34, 197, 94, 0.6)',
                'fill_percent': 85,
                'description': 'Authentic network - high confidence',
                'css_state': 'VERIFIED'
            },
            ReputationState.ESTABLISHED: {
                'label': 'ESTABLISHED',
                'color': '#84cc16',          # Lime
                'color_light': '#a3e635',
                'color_dark': '#65a30d',
                'glow': 'rgba(132, 204, 22, 0.4)',
                'fill_percent': 65,
                'description': 'Good signals - standard confidence',
                'css_state': 'ESTABLISHED'
            },
            ReputationState.EMERGING: {
                'label': 'EMERGING',
                'color': '#eab308',          # Yellow
                'color_light': '#facc15',
                'color_dark': '#ca8a04',
                'glow': 'rgba(234, 179, 8, 0.3)',
                'fill_percent': 40,
                'description': 'Building presence - limited data',
                'css_state': 'EMERGING'
            },
            ReputationState.UNCERTAIN: {
                'label': 'UNCERTAIN',
                'color': '#ef4444',          # Red
                'color_light': '#f87171',
                'color_dark': '#b91c1c',
                'glow': 'rgba(239, 68, 68, 0.15)',
                'fill_percent': 15,
                'description': 'Red flags detected - investigate',
                'css_state': 'UNCERTAIN'
            }
        }

        return displays[state]

    # =========================================================================
    # Storage
    # =========================================================================

    def _store_score(self, artist_id: int, wallet_address: str,
                    twitter_handle: str, metrics: AuthenticityMetrics,
                    vitality_score: float, network_score: float,
                    transaction_score: float, timeline_score: float,
                    weighted_score: float, percentile_rank: float,
                    reputation_state: ReputationState,
                    network_analysis: NetworkAnalysis):
        """Store the calculated score"""
        cursor = self.db_conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO reputation_scores_v2
            (artist_id, twitter_handle, wallet_address, authenticity_metrics,
             collector_vitality_score, network_authenticity_score,
             transaction_legitimacy_score, timeline_health_score,
             weighted_score, percentile_rank, reputation_state, suspicion_level,
             sybil_clusters_found, circular_rings_found, dead_end_wallets_found,
             wash_trade_indicators, verified_collectors_count, ecosystem_connections,
             compared_against_count, scan_completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            artist_id,
            twitter_handle,
            wallet_address,
            json.dumps({
                'total_collectors': metrics.total_collectors,
                'verified_real': metrics.verified_real_collectors,
                'dead_ends': metrics.dead_end_wallets,
                'activity_pattern': metrics.activity_pattern
            }),
            vitality_score,
            network_score,
            transaction_score,
            timeline_score,
            weighted_score,
            percentile_rank,
            reputation_state.name,
            network_analysis.suspicion_level.value,
            metrics.sybil_cluster_count,
            1 if metrics.circular_trading_detected else 0,
            metrics.dead_end_wallets,
            metrics.wash_trade_indicators,
            metrics.verified_real_collectors,
            metrics.ecosystem_connected_collectors,
            self._get_comparison_context().get('total_artists_assessed', 0)
        ))

        # Store for distribution tracking
        for metric_name, score in [
            ('collector_vitality', vitality_score),
            ('network_authenticity', network_score),
            ('transaction_legitimacy', transaction_score),
            ('timeline_health', timeline_score),
            ('weighted_score', weighted_score)
        ]:
            cursor.execute('''
                INSERT INTO authenticity_distribution (metric_name, score_value)
                VALUES (?, ?)
            ''', (metric_name, score))

        self.db_conn.commit()

    def get_artist_badge(self, artist_id: int) -> Optional[Dict]:
        """Retrieve stored badge for an artist"""
        cursor = self.db_conn.cursor()

        cursor.execute('''
            SELECT * FROM reputation_scores_v2 WHERE artist_id = ?
        ''', (artist_id,))

        row = cursor.fetchone()
        if not row:
            return None

        state = ReputationState[row['reputation_state']]

        return {
            'artist_id': row['artist_id'],
            'reputation_state': row['reputation_state'],
            'weighted_score': row['weighted_score'],
            'percentile_rank': row['percentile_rank'],
            'suspicion_level': row['suspicion_level'],
            'certified_at': row['certified_at'],
            'badge_display': self._get_badge_display(state)
        }

    def calculate_reputation(self, wallet_address: str) -> 'ReputationResult':
        """
        Simple interface for calculating reputation from a wallet address.

        This is a convenience wrapper around assess_artist() for the setup flow.
        Returns a ReputationResult object with state, score, findings, and component_scores.
        """
        # Get blockchain data directly from database
        db_path = Path(__file__).parent.parent.parent / 'db' / 'blockchain_tracking.db'
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find address_id
        cursor.execute(
            'SELECT id FROM tracked_addresses WHERE LOWER(address) = LOWER(?)',
            (wallet_address,)
        )
        addr_row = cursor.fetchone()

        collector_addresses = []
        transfers = []
        address_id = 0

        if addr_row:
            address_id = addr_row['id']

            # Get collectors
            cursor.execute('''
                SELECT DISTINCT c.collector_address
                FROM collectors c
                JOIN nft_mints m ON c.nft_mint_id = m.id
                WHERE m.address_id = ?
            ''', (address_id,))
            collector_addresses = [r['collector_address'] for r in cursor.fetchall()]

            # Get transfers/transactions
            cursor.execute('''
                SELECT from_address, to_address, value_native, block_timestamp, tx_type
                FROM transactions
                WHERE address_id = ?
            ''', (address_id,))
            transfers = [dict(r) for r in cursor.fetchall()]

        conn.close()

        # Run assessment
        result = self.assess_artist(
            artist_id=address_id if addr_row else 0,
            wallet_address=wallet_address,
            twitter_handle=None,
            collector_addresses=collector_addresses,
            transfers=transfers
        )

        # Convert to ReputationResult object
        return ReputationResult(
            state=ReputationState[result['reputation_state']],
            score=result['weighted_score'],
            component_scores={
                'collector_vitality': result['component_scores']['collector_vitality']['score'],
                'network_authenticity': result['component_scores']['network_authenticity']['score'],
                'transaction_legitimacy': result['component_scores']['transaction_legitimacy']['score'],
                'timeline_health': result['component_scores']['timeline_health']['score'],
            },
            findings=[s['title'] for s in result.get('positive_signals', [])] +
                     [f['title'] for f in result.get('red_flags', [])]
        )


@dataclass
class ReputationResult:
    """Simple result object for reputation calculation"""
    state: ReputationState
    score: float
    component_scores: Dict[str, float]
    findings: List[str]


# Example usage and testing
if __name__ == '__main__':
    scorer = ReputationScorer()

    if len(sys.argv) < 2:
        print("""
Reputation Score Algorithm v2 (Authenticity-Focused)
=====================================================

Usage:
  python reputation_score.py test
  python reputation_score.py weights
  python reputation_score.py distribution

This version measures AUTHENTICITY, not volume:
  - Are collectors real or sybil wallets?
  - Is trading organic or wash trading?
  - Do wallets show signs of life?
  - Does growth look natural?
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'test':
        # Test assessment
        print("\nTesting authenticity assessment...")
        print("(In production, this would analyze real blockchain data)\n")

        # Simulate a basic assessment
        result = scorer.assess_artist(
            artist_id=999,
            wallet_address='0x1234567890abcdef1234567890abcdef12345678',
            twitter_handle='test_artist',
            collector_addresses=[],
            transfers=[]
        )

        print(json.dumps(result, indent=2))

    elif command == 'weights':
        print("\nAuthenticity Weight Configuration:")
        print("=" * 45)
        for metric, weight in scorer.WEIGHTS.items():
            print(f"  {metric.replace('_', ' ').title()}: {weight*100:.0f}%")
        print("\nThese weights prioritize REAL activity over volume.")

    elif command == 'distribution':
        cursor = scorer.db_conn.cursor()
        cursor.execute('''
            SELECT reputation_state, COUNT(*) as count,
                   AVG(weighted_score) as avg_score
            FROM reputation_scores_v2
            GROUP BY reputation_state
        ''')

        print("\nReputation State Distribution:")
        print("=" * 45)
        for row in cursor.fetchall():
            avg = row['avg_score'] if row['avg_score'] else 0
            print(f"  {row['reputation_state']}: {row['count']} artists (avg: {avg:.1f})")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
