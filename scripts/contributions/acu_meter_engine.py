"""
ACU-METER Engine - 4-component weighted scoring system

Formula (from WISDOM_KNOWLEDGE_BASE.md):
ACU_SCORE = (
  (INTENT_WEIGHT × intent_data) +
  (WISDOM_WEIGHT × alignment_data) +
  (APPLICATION_WEIGHT × usage_data) +
  (LEGACY_WEIGHT × impact_data)
) / 4

Components:
1. INTENT: Heart-forward verification scores
2. WISDOM: Existing authenticity score + wisdom shares
3. APPLICATION: Contribution count + diversity
4. LEGACY: Long-term positive impact, community endorsements

Thresholds:
- ≥75% = standard access
- ≥90% = elevated access
- <75% = restricted access

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 7-8
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

from .micro_tx_db import (
    MicroTXDatabase,
    ACUMeterScore,
    AlignmentLog,
    AccessLevel
)


# Default weights (all equal as per protocol)
DEFAULT_WEIGHTS = {
    'intent': 1.0,
    'wisdom': 1.0,
    'application': 1.0,
    'legacy': 1.0
}

# Access thresholds
ACCESS_THRESHOLDS = {
    'restricted': 0,
    'standard': 75,
    'elevated': 90
}

# Quantum state file path
QUANTUM_STATE_PATH = Path(__file__).parent.parent.parent / 'inspiration' / 'quantum_state'


@dataclass
class ACUMeterResult:
    """Full ACU-METER calculation result."""
    contributor_id: int
    address: str

    # Component scores (0.0 to 1.0)
    intent_score: float
    wisdom_score: float
    application_score: float
    legacy_score: float

    # Weights applied
    weights: Dict[str, float]

    # Final calculations
    weighted_total: float  # 0.0 to 1.0
    percentage: float  # 0 to 100
    percentile_rank: float  # 0 to 100

    # Access determination
    threshold_met: bool
    access_level: str

    # Details
    calculation_details: Dict[str, Any]


class ACUMeterEngine:
    """
    ACU-METER scoring engine implementing the 4-component formula.

    Integrates with:
    - Heart-forward verifier (INTENT component)
    - Existing reputation system (WISDOM component)
    - Contribution tracking (APPLICATION component)
    - Community endorsements (LEGACY component)
    """

    def __init__(self, db: MicroTXDatabase = None, weights: Dict[str, float] = None):
        self.db = db or MicroTXDatabase()
        self.weights = weights or DEFAULT_WEIGHTS.copy()

    # ================================================================
    # MAIN CALCULATION
    # ================================================================

    def calculate_score(self, contributor_id: int) -> ACUMeterResult:
        """
        Calculate full ACU-METER score for a contributor.

        Formula:
        ACU_SCORE = (I×w1 + W×w2 + A×w3 + L×w4) / 4
        """
        # Get contributor info
        from .micro_tx_db import ContributorProfile
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contributor_profiles WHERE id = ?", (contributor_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Contributor {contributor_id} not found")

        address = row['primary_address']

        # Calculate each component
        intent_score, intent_details = self._calculate_intent(contributor_id)
        wisdom_score, wisdom_details = self._calculate_wisdom(contributor_id, address)
        application_score, application_details = self._calculate_application(contributor_id)
        legacy_score, legacy_details = self._calculate_legacy(contributor_id)

        # Apply weighted formula
        weighted_total = (
            (self.weights['intent'] * intent_score) +
            (self.weights['wisdom'] * wisdom_score) +
            (self.weights['application'] * application_score) +
            (self.weights['legacy'] * legacy_score)
        ) / 4

        # Convert to percentage
        percentage = weighted_total * 100

        # Calculate percentile rank
        percentile_rank = self._calculate_percentile(contributor_id, weighted_total)

        # Determine access level
        access_level = self._determine_access_level(percentile_rank)
        threshold_met = percentile_rank >= ACCESS_THRESHOLDS['standard']

        # Create result
        result = ACUMeterResult(
            contributor_id=contributor_id,
            address=address,
            intent_score=intent_score,
            wisdom_score=wisdom_score,
            application_score=application_score,
            legacy_score=legacy_score,
            weights=self.weights,
            weighted_total=weighted_total,
            percentage=percentage,
            percentile_rank=percentile_rank,
            threshold_met=threshold_met,
            access_level=access_level,
            calculation_details={
                'intent': intent_details,
                'wisdom': wisdom_details,
                'application': application_details,
                'legacy': legacy_details
            }
        )

        # Save to database
        self._save_score(result)

        # Update contributor profile
        self.db.update_contributor_score(
            contributor_id,
            weighted_total,
            percentile_rank,
            access_level
        )

        # Log the calculation
        self.db.log_alignment_event(AlignmentLog(
            event_type='score_update',
            contributor_id=contributor_id,
            action='recalculated',
            new_state=json.dumps({
                'intent': intent_score,
                'wisdom': wisdom_score,
                'application': application_score,
                'legacy': legacy_score,
                'total': weighted_total,
                'percentile': percentile_rank,
                'access': access_level
            }),
            triggered_by='system',
            triggering_entity='acu_meter_engine'
        ))

        return result

    # ================================================================
    # COMPONENT CALCULATIONS
    # ================================================================

    def _calculate_intent(self, contributor_id: int) -> Tuple[float, Dict]:
        """
        Calculate INTENT component (Heart-Forward Score).

        Based on average heart-forward verification scores of contributions.
        """
        contributions = self.db.get_contributions_by_contributor(contributor_id, limit=100)

        if not contributions:
            return 0.0, {'reason': 'No contributions', 'count': 0}

        # Get verified contributions with heart-forward scores
        verified = [c for c in contributions if c.validation_status in [
            'auto_approved', 'community_verified', 'manual_approved'
        ]]

        if not verified:
            return 0.0, {'reason': 'No verified contributions', 'count': len(contributions)}

        # Calculate average heart-forward score
        total_score = sum(c.heart_forward_score for c in verified)
        avg_score = total_score / len(verified)

        return avg_score, {
            'verified_count': len(verified),
            'total_count': len(contributions),
            'avg_heart_forward_score': avg_score
        }

    def _calculate_wisdom(self, contributor_id: int, address: str) -> Tuple[float, Dict]:
        """
        Calculate WISDOM component (Alignment Score).

        Combines:
        - Existing authenticity score from reputation system
        - Wisdom share contribution count
        """
        # Try to get existing reputation score
        authenticity_score = self._get_authenticity_score(address)

        # Count wisdom share contributions
        wisdom_shares = self.db.count_contributions_by_type(contributor_id, 'wisdom_share')

        # Wisdom factor: max 1.0 at 10 shares
        wisdom_factor = min(1.0, wisdom_shares / 10)

        # Combine: 60% authenticity + 40% wisdom shares
        if authenticity_score is not None:
            combined = (authenticity_score * 0.6) + (wisdom_factor * 0.4)
        else:
            combined = wisdom_factor

        return combined, {
            'authenticity_score': authenticity_score,
            'wisdom_shares': wisdom_shares,
            'wisdom_factor': wisdom_factor,
            'combined': combined
        }

    def _get_authenticity_score(self, address: str) -> Optional[float]:
        """
        Get authenticity score from existing reputation system.

        Integrates with scripts/interface/reputation_score.py
        """
        try:
            # Try to import and use existing reputation scorer
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / 'interface'))

            from reputation_score import ReputationScorer

            scorer = ReputationScorer()
            result = scorer.calculate_reputation(address)

            if result:
                # Convert from 0-100 to 0-1
                return result.score / 100.0

        except ImportError:
            pass
        except Exception:
            pass

        return None

    def _calculate_application(self, contributor_id: int) -> Tuple[float, Dict]:
        """
        Calculate APPLICATION component (Usage Score).

        Based on:
        - Total contribution count
        - Contribution diversity (different types)
        - Recent activity
        """
        contributions = self.db.get_contributions_by_contributor(contributor_id, limit=100)

        if not contributions:
            return 0.0, {'reason': 'No contributions', 'count': 0}

        # Count by type
        type_counts = {}
        for c in contributions:
            type_counts[c.contribution_type] = type_counts.get(c.contribution_type, 0) + 1

        # Count factor: max 1.0 at 20 contributions
        count_factor = min(1.0, len(contributions) / 20)

        # Diversity factor: max 1.0 at 4 different types
        diversity_factor = min(1.0, len(type_counts) / 4)

        # Recency factor: based on most recent contribution
        recency_factor = 0.0
        if contributions:
            most_recent = contributions[0]  # Already sorted by created_at DESC
            if most_recent.created_at:
                try:
                    created = datetime.fromisoformat(most_recent.created_at.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - created.replace(tzinfo=None)).days
                    # Full score if within 7 days, decreasing to 0 at 90 days
                    recency_factor = max(0.0, 1.0 - (days_ago / 90))
                except:
                    recency_factor = 0.5

        # Combine: 40% count + 30% diversity + 30% recency
        combined = (count_factor * 0.40) + (diversity_factor * 0.30) + (recency_factor * 0.30)

        return combined, {
            'total_contributions': len(contributions),
            'type_distribution': type_counts,
            'count_factor': count_factor,
            'diversity_factor': diversity_factor,
            'recency_factor': recency_factor,
            'combined': combined
        }

    def _calculate_legacy(self, contributor_id: int) -> Tuple[float, Dict]:
        """
        Calculate LEGACY component (Impact Score).

        Based on:
        - Account age
        - Social endorsements received
        - Long-term positive impact
        """
        # Get contributor creation date
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT created_at FROM contributor_profiles WHERE id = ?",
            (contributor_id,)
        )
        row = cursor.fetchone()
        conn.close()

        # Age factor: max 1.0 at 1 year
        age_factor = 0.0
        if row and row['created_at']:
            try:
                created = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
                days_active = (datetime.now() - created.replace(tzinfo=None)).days
                age_factor = min(1.0, days_active / 365)
            except:
                age_factor = 0.0

        # Endorsement factor: count social endorsements received
        endorsements = self._count_endorsements_received(contributor_id)
        endorsement_factor = min(1.0, endorsements / 10)

        # Mint factor: creative output
        mints = self.db.count_contributions_by_type(contributor_id, 'mint')
        mint_factor = min(1.0, mints / 5)

        # Combine: 30% age + 40% endorsements + 30% mints
        combined = (age_factor * 0.30) + (endorsement_factor * 0.40) + (mint_factor * 0.30)

        return combined, {
            'age_factor': age_factor,
            'endorsements_received': endorsements,
            'endorsement_factor': endorsement_factor,
            'mints': mints,
            'mint_factor': mint_factor,
            'combined': combined
        }

    def _count_endorsements_received(self, contributor_id: int) -> int:
        """Count social endorsements received by this contributor."""
        # For now, return 0 - would need to track endorsement targets
        # This would require extending the contribution content to track who is being endorsed
        return 0

    # ================================================================
    # PERCENTILE & ACCESS
    # ================================================================

    def _calculate_percentile(self, contributor_id: int, score: float) -> float:
        """Calculate percentile rank among all contributors."""
        all_scores = self.db.get_all_scores_for_percentile()

        if not all_scores:
            return 50.0  # Default to middle if no data

        # Sort scores descending
        sorted_scores = sorted([s[1] for s in all_scores], reverse=True)

        # Find position
        count_below = sum(1 for s in sorted_scores if s < score)
        total = len(sorted_scores)

        if total == 0:
            return 50.0

        percentile = (count_below / total) * 100
        return percentile

    def _determine_access_level(self, percentile: float) -> str:
        """Determine access level from percentile."""
        if percentile >= ACCESS_THRESHOLDS['elevated']:
            return 'elevated'
        elif percentile >= ACCESS_THRESHOLDS['standard']:
            return 'standard'
        else:
            return 'restricted'

    # ================================================================
    # PERSISTENCE
    # ================================================================

    def _save_score(self, result: ACUMeterResult):
        """Save ACU-METER score to database."""
        score = ACUMeterScore(
            contributor_id=result.contributor_id,
            intent_score=result.intent_score,
            wisdom_score=result.wisdom_score,
            application_score=result.application_score,
            legacy_score=result.legacy_score,
            intent_weight=result.weights['intent'],
            wisdom_weight=result.weights['wisdom'],
            application_weight=result.weights['application'],
            legacy_weight=result.weights['legacy'],
            weighted_total=result.weighted_total,
            percentile_rank=result.percentile_rank,
            threshold_met=result.threshold_met,
            access_level=result.access_level
        )

        self.db.save_acu_score(score)

    # ================================================================
    # QUANTUM STATE UPDATE
    # ================================================================

    def update_quantum_state(self):
        """
        Update quantum state snapshot with current ACU metrics.

        Called after significant changes to update the system perspective.
        """
        stats = self.db.get_contribution_stats()

        snapshot = {
            'ALIGNMENT_STATUS': 'ACTIVE',
            'HEART_FORWARD_GATE': 'ACTIVE',
            'WISDOM_SYNC': 'OPERATIONAL',
            'USER_TX_BUFFER': 'PROCESSING',
            'LAST_OBSERVATION': datetime.now().isoformat(),

            'metrics': {
                'total_contributors': stats.get('total_contributors', 0),
                'total_contributions': stats.get('total_contributions', 0),
                'avg_acu_score': stats.get('avg_acu_score', 0),
                'contributions_by_type': stats.get('by_type', {}),
                'contributions_by_status': stats.get('by_status', {}),
                'access_distribution': stats.get('access_distribution', {})
            },

            'alignment_weights': self.weights,

            'thresholds': ACCESS_THRESHOLDS
        }

        # Write to quantum state folder
        QUANTUM_STATE_PATH.mkdir(parents=True, exist_ok=True)

        # Update CURRENT_STATE.md
        state_md = QUANTUM_STATE_PATH / 'CURRENT_STATE.md'
        with open(state_md, 'w') as f:
            f.write(f"""# QUANTUM STATE SNAPSHOT
## Current Perspective: {datetime.now().strftime('%b %d, %Y %H:%M')}

---

## State Vector

```
ALIGNMENT_STATUS: {snapshot['ALIGNMENT_STATUS']}
HEART_FORWARD_GATE: {snapshot['HEART_FORWARD_GATE']}
WISDOM_SYNC: {snapshot['WISDOM_SYNC']}
USER_TX_BUFFER: {snapshot['USER_TX_BUFFER']}
LAST_OBSERVATION: {snapshot['LAST_OBSERVATION']}
```

---

## System Metrics

| Metric | Value |
|--------|-------|
| Total Contributors | {snapshot['metrics']['total_contributors']} |
| Total Contributions | {snapshot['metrics']['total_contributions']} |
| Avg ACU Score | {snapshot['metrics']['avg_acu_score']:.2f} |

---

## Contributions by Type

| Type | Count |
|------|-------|
""")
            for t, c in snapshot['metrics']['contributions_by_type'].items():
                f.write(f"| {t} | {c} |\n")

            f.write(f"""
---

## Access Distribution

| Level | Count |
|-------|-------|
""")
            for level, count in snapshot['metrics']['access_distribution'].items():
                f.write(f"| {level} | {count} |\n")

            f.write(f"""
---

## Alignment Weights (Current)

```
INTENT_WEIGHT: {self.weights['intent']}
WISDOM_WEIGHT: {self.weights['wisdom']}
APPLICATION_WEIGHT: {self.weights['application']}
LEGACY_WEIGHT: {self.weights['legacy']}
```

---

*Snapshot updated: {datetime.now().isoformat()}*
*State: OPERATIONAL*
""")

        # Also save JSON snapshot
        json_path = QUANTUM_STATE_PATH / 'acu_scores_snapshot.json'
        with open(json_path, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)

        return snapshot

    # ================================================================
    # CONVENIENCE METHODS
    # ================================================================

    def get_score(self, address: str) -> Optional[ACUMeterResult]:
        """Get ACU-METER score for an address."""
        contributor = self.db.get_contributor_by_address(address)
        if not contributor:
            return None

        return self.calculate_score(contributor.id)

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top contributors by ACU-METER score."""
        return self.db.get_leaderboard(limit)

    def check_access(self, address: str, required_level: str) -> bool:
        """Check if address has required access level."""
        contributor = self.db.get_contributor_by_address(address)
        if not contributor:
            return required_level == 'restricted'

        # Get current score
        score = self.db.get_latest_acu_score(contributor.id)
        if not score:
            return required_level == 'restricted'

        # Check level hierarchy
        levels = ['restricted', 'standard', 'elevated']
        current_idx = levels.index(score.access_level) if score.access_level in levels else 0
        required_idx = levels.index(required_level) if required_level in levels else 0

        return current_idx >= required_idx


# Convenience functions
def calculate_acu_score(address: str) -> Optional[ACUMeterResult]:
    """Calculate ACU-METER score for an address."""
    engine = ACUMeterEngine()
    return engine.get_score(address)


def check_access_level(address: str, required_level: str) -> bool:
    """Check if address has required access level."""
    engine = ACUMeterEngine()
    return engine.check_access(address, required_level)
