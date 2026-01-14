"""
Heart-Forward Verifier - Multi-tier verification system

Verification tiers:
1. AUTOMATED: Keyword analysis, sentiment scoring, pattern matching
2. COMMUNITY: Stake-weighted voting by verified contributors
3. MANUAL: Review queue for flagged or disputed items

Heart-forward alignment is measured by:
- Positive keywords (preserve, protect, share, teach, heart, wisdom, etc.)
- Negative keywords (spam, scam, exploit, harmful, etc.)
- Sentiment analysis of contribution content
- Pattern matching against wisdom knowledge base

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 8
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

from .micro_tx_db import (
    MicroTXDatabase,
    ValidationStatus,
    AlignmentLog
)


# ================================================================
# HEART-FORWARD KEYWORDS FROM WISDOM KNOWLEDGE BASE
# ================================================================

POSITIVE_KEYWORDS = [
    # Core values
    'preserve', 'protect', 'share', 'teach', 'help', 'support',
    'community', 'collaborative', 'open', 'transparent', 'authentic',
    'sovereignty', 'humanity', 'hope', 'wisdom', 'legacy',
    'heart', 'soul', 'intention', 'purpose', 'meaning',

    # From WISDOM_KNOWLEDGE_BASE.md
    'recognize', 'generate', 'manifest', 'transform', 'transmute',
    'comprehension', 'infinite', 'potential', 'collective',
    'history', 'truth', 'verify', 'local', 'free',

    # Spiritual alignment
    'gratitude', 'love', 'healing', 'awareness', 'alignment',
    'balance', 'creation', 'vision', 'light', 'positive',

    # Technical alignment
    'archive', 'document', 'backup', 'restore', 'curate',
    'validate', 'contribute', 'build', 'create', 'innovate'
]

NEGATIVE_KEYWORDS = [
    # Misalignment indicators
    'spam', 'scam', 'fake', 'manipulation', 'exploit',
    'extraction', 'profit-only', 'selfish', 'harmful',

    # Toxic patterns
    'hate', 'attack', 'destroy', 'steal', 'cheat',
    'deceive', 'fraud', 'abuse', 'harass', 'threat',

    # Corporate extraction patterns
    'captive', 'lock-in', 'paywall', 'monetize-only',
    'surveillance', 'tracking', 'datamine',

    # Low-effort patterns
    'giveaway', 'airdrop-hunt', 'bot', 'automated-spam',
    'copy-paste', 'plagiarize'
]

# Wisdom patterns from knowledge base
WISDOM_PATTERNS = [
    r'recognition.+generation',
    r'heart.+forward',
    r'data.+sovereignty',
    r'local.+first',
    r'free.+for.+all',
    r'hope.+history.+humanity',
    r'transform.+data',
    r'preserve.+potential',
    r'skills.+extract.+upwards',
    r'infinite.+potential'
]

# Auto-pass threshold (≥80% passes automated verification)
AUTO_PASS_THRESHOLD = 0.80

# Community voting threshold (60% weighted approval)
COMMUNITY_THRESHOLD = 0.60


@dataclass
class VerificationResult:
    """Result of heart-forward verification."""
    passed: bool
    score: float  # 0.0 to 1.0
    tier: str  # 'auto', 'community', 'manual'
    keyword_score: float
    sentiment_score: float
    pattern_score: float
    details: Dict[str, Any]


class HeartForwardVerifier:
    """
    Multi-tier heart-forward verification system.

    Verification flow:
    1. Run automated checks (keyword + sentiment + pattern)
    2. If score ≥ 80%, auto-pass
    3. If score < 80%, queue for community voting
    4. If community score < 60% or flagged, queue for manual review
    """

    def __init__(self, db: MicroTXDatabase = None):
        self.db = db or MicroTXDatabase()

    # ================================================================
    # AUTOMATED VERIFICATION
    # ================================================================

    def verify_automated(self, contribution_id: int) -> VerificationResult:
        """
        Run automated heart-forward verification.

        Analyzes:
        - Keyword presence (positive vs negative)
        - Sentiment indicators
        - Pattern matching against wisdom base
        """
        contribution = self.db.get_contribution(contribution_id)
        if not contribution:
            return VerificationResult(
                passed=False,
                score=0.0,
                tier='auto',
                keyword_score=0.0,
                sentiment_score=0.0,
                pattern_score=0.0,
                details={'error': 'Contribution not found'}
            )

        # Get content for analysis
        content = self._extract_content_text(contribution.content_json)

        # Run analysis
        keyword_score = self._analyze_keywords(content)
        sentiment_score = self._analyze_sentiment(content)
        pattern_score = self._analyze_patterns(content)

        # Calculate weighted score
        # Keywords: 40%, Sentiment: 30%, Pattern: 30%
        final_score = (
            keyword_score * 0.40 +
            sentiment_score * 0.30 +
            pattern_score * 0.30
        )

        # Determine if auto-pass
        passed = final_score >= AUTO_PASS_THRESHOLD

        # Determine result
        if passed:
            result_text = 'pass'
        elif final_score >= 0.5:
            result_text = 'needs_review'
        else:
            result_text = 'fail'

        # Update database
        self.db.update_automated_verification(
            contribution_id,
            keyword_score,
            sentiment_score,
            pattern_score,
            result_text
        )

        return VerificationResult(
            passed=passed,
            score=final_score,
            tier='auto',
            keyword_score=keyword_score,
            sentiment_score=sentiment_score,
            pattern_score=pattern_score,
            details={
                'result': result_text,
                'positive_keywords_found': self._find_keywords(content, POSITIVE_KEYWORDS),
                'negative_keywords_found': self._find_keywords(content, NEGATIVE_KEYWORDS),
                'patterns_matched': self._find_patterns(content)
            }
        )

    def _extract_content_text(self, content_json: str) -> str:
        """Extract text from content JSON."""
        if not content_json:
            return ''

        try:
            content = json.loads(content_json)

            if isinstance(content, str):
                return content

            if isinstance(content, dict):
                # Gather all text fields
                text_parts = []
                for key in ['content', 'text', 'knowledge', 'teaching', 'description', 'message']:
                    if key in content:
                        text_parts.append(str(content[key]))
                return ' '.join(text_parts)

            return str(content)
        except:
            return str(content_json)

    def _analyze_keywords(self, content: str) -> float:
        """
        Analyze keyword presence.

        Returns score from 0.0 (all negative) to 1.0 (all positive).
        """
        content_lower = content.lower()

        positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in content_lower)
        negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in content_lower)

        total = positive_count + negative_count

        if total == 0:
            return 0.5  # Neutral

        # Score: positive / total, penalized by negatives
        raw_score = positive_count / total

        # Apply negative penalty
        if negative_count > 0:
            penalty = min(0.3, negative_count * 0.1)
            raw_score -= penalty

        return max(0.0, min(1.0, raw_score))

    def _find_keywords(self, content: str, keyword_list: List[str]) -> List[str]:
        """Find which keywords are present."""
        content_lower = content.lower()
        return [kw for kw in keyword_list if kw in content_lower]

    def _analyze_sentiment(self, content: str) -> float:
        """
        Simple sentiment analysis.

        Returns score from 0.0 (negative) to 1.0 (positive).
        """
        content_lower = content.lower()

        # Positive sentiment indicators
        positive_indicators = [
            'thank', 'grateful', 'love', 'appreciate', 'wonderful',
            'amazing', 'great', 'excellent', 'beautiful', 'inspiring',
            'helpful', 'valuable', 'important', 'meaningful', 'hope'
        ]

        # Negative sentiment indicators
        negative_indicators = [
            'hate', 'terrible', 'awful', 'bad', 'worst',
            'angry', 'frustrated', 'annoyed', 'disappointed', 'sad',
            'useless', 'worthless', 'waste', 'stupid', 'dumb'
        ]

        pos_count = sum(1 for ind in positive_indicators if ind in content_lower)
        neg_count = sum(1 for ind in negative_indicators if ind in content_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.5  # Neutral

        return pos_count / total

    def _analyze_patterns(self, content: str) -> float:
        """
        Match content against wisdom knowledge base patterns.

        Returns score from 0.0 to 1.0 based on pattern matches.
        """
        content_lower = content.lower()

        matches = 0
        for pattern in WISDOM_PATTERNS:
            if re.search(pattern, content_lower):
                matches += 1

        # Score based on pattern matches (max 5 for full score)
        return min(1.0, matches / 5)

    def _find_patterns(self, content: str) -> List[str]:
        """Find which wisdom patterns are matched."""
        content_lower = content.lower()
        return [p for p in WISDOM_PATTERNS if re.search(p, content_lower)]

    # ================================================================
    # COMMUNITY VERIFICATION
    # ================================================================

    def process_community_vote(
        self,
        contribution_id: int,
        voter_address: str,
        vote_type: str,  # 'for' or 'against'
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Process a community vote on a contribution.

        Returns current voting state.
        """
        # Get voter's stake (based on their ACU-METER score)
        voter = self.db.get_contributor_by_address(voter_address)
        if voter:
            # Stake is proportional to ACU score
            voter_stake = max(1.0, voter.acu_meter_score * 10)
        else:
            voter_stake = 1.0

        # Record vote
        self.db.record_community_vote(
            contribution_id,
            voter_address,
            voter_stake,
            vote_type,
            reason
        )

        # Get current state
        return self.get_community_vote_state(contribution_id)

    def get_community_vote_state(self, contribution_id: int) -> Dict[str, Any]:
        """Get current community voting state."""
        pending = self.db.get_pending_verifications(limit=1000)

        for p in pending:
            if p['id'] == contribution_id:
                votes_for = p.get('community_votes_for', 0)
                votes_against = p.get('community_votes_against', 0)
                total_votes = votes_for + votes_against

                if total_votes > 0:
                    approval_rate = votes_for / total_votes
                else:
                    approval_rate = 0.5

                return {
                    'votes_for': votes_for,
                    'votes_against': votes_against,
                    'total_votes': total_votes,
                    'approval_rate': approval_rate,
                    'passed': approval_rate >= COMMUNITY_THRESHOLD,
                    'needs_more_votes': total_votes < 3  # Minimum 3 votes
                }

        return {
            'votes_for': 0,
            'votes_against': 0,
            'total_votes': 0,
            'approval_rate': 0.5,
            'passed': False,
            'needs_more_votes': True
        }

    def finalize_community_verification(self, contribution_id: int) -> Optional[VerificationResult]:
        """
        Finalize community verification if enough votes.

        Returns VerificationResult if finalized, None if more votes needed.
        """
        state = self.get_community_vote_state(contribution_id)

        if state['needs_more_votes']:
            return None

        passed = state['passed']

        if passed:
            result = 'approved'
        else:
            result = 'rejected'

        return VerificationResult(
            passed=passed,
            score=state['approval_rate'],
            tier='community',
            keyword_score=0.0,  # Not applicable for community
            sentiment_score=0.0,
            pattern_score=0.0,
            details={
                'result': result,
                'votes': state
            }
        )

    # ================================================================
    # MANUAL VERIFICATION
    # ================================================================

    def submit_manual_review(
        self,
        contribution_id: int,
        reviewer: str,
        result: str,  # 'approved' or 'rejected'
        notes: str = None
    ) -> VerificationResult:
        """
        Submit manual review decision.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE verification_queue
            SET manual_reviewer = ?, manual_result = ?, manual_notes = ?
            WHERE contribution_id = ?
        """, (reviewer, result, notes, contribution_id))

        conn.commit()
        conn.close()

        passed = result == 'approved'

        return VerificationResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            tier='manual',
            keyword_score=0.0,
            sentiment_score=0.0,
            pattern_score=0.0,
            details={
                'result': result,
                'reviewer': reviewer,
                'notes': notes
            }
        )

    # ================================================================
    # FULL VERIFICATION PIPELINE
    # ================================================================

    def run_full_verification(self, contribution_id: int) -> VerificationResult:
        """
        Run full verification pipeline.

        1. Try automated verification
        2. If passes (≥80%), return success
        3. If fails (<50%), return failure
        4. If middle (50-80%), needs community/manual review
        """
        # Run automated check
        auto_result = self.verify_automated(contribution_id)

        if auto_result.passed:
            # Auto-approved
            return auto_result

        if auto_result.score < 0.5:
            # Auto-rejected (too low)
            return VerificationResult(
                passed=False,
                score=auto_result.score,
                tier='auto',
                keyword_score=auto_result.keyword_score,
                sentiment_score=auto_result.sentiment_score,
                pattern_score=auto_result.pattern_score,
                details={
                    **auto_result.details,
                    'result': 'fail',
                    'reason': 'Score below minimum threshold (50%)'
                }
            )

        # Middle ground - needs review
        return VerificationResult(
            passed=False,
            score=auto_result.score,
            tier='auto',
            keyword_score=auto_result.keyword_score,
            sentiment_score=auto_result.sentiment_score,
            pattern_score=auto_result.pattern_score,
            details={
                **auto_result.details,
                'result': 'needs_review',
                'reason': f'Score {auto_result.score:.0%} requires community verification'
            }
        )

    def get_verification_status(self, contribution_id: int) -> Dict[str, Any]:
        """Get full verification status for a contribution."""
        contribution = self.db.get_contribution(contribution_id)
        if not contribution:
            return {'error': 'Contribution not found'}

        pending = self.db.get_pending_verifications(limit=1000)
        verification_data = None
        for p in pending:
            if p['id'] == contribution_id:
                verification_data = p
                break

        community_state = self.get_community_vote_state(contribution_id)

        return {
            'contribution_id': contribution_id,
            'current_status': contribution.validation_status,
            'heart_forward_score': contribution.heart_forward_score,
            'automated': {
                'keyword_score': verification_data.get('keyword_score', 0) if verification_data else 0,
                'sentiment_score': verification_data.get('sentiment_score', 0) if verification_data else 0,
                'pattern_score': verification_data.get('pattern_score', 0) if verification_data else 0,
                'result': verification_data.get('automated_result') if verification_data else None
            },
            'community': community_state,
            'final_status': verification_data.get('final_status') if verification_data else contribution.validation_status
        }


# Convenience function
def verify_contribution(contribution_id: int) -> VerificationResult:
    """Run full verification on a contribution."""
    verifier = HeartForwardVerifier()
    return verifier.run_full_verification(contribution_id)
