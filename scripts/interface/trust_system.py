#!/usr/bin/env python3
"""
Trust System - Data Consistency & Community Reporting

Calculates trust scores based on data alignment across sources.
Handles community reports and appeal processes.

This is a TRANSPARENT system - users can see their own scores
and understand how they're calculated.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TrustScoreCalculator:
    """
    Calculates data consistency scores by comparing:
    - Blockchain activity (mints, sales, collections)
    - Social media posts (Twitter, Instagram archives)
    - Claimed identity information

    Higher scores = better alignment = more trustworthy archive
    Lower scores = gaps or inconsistencies that users should address
    """

    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.kb_path = Path(knowledge_base_path)

    def calculate_score(self, user_id: str = None) -> Dict:
        """
        Calculate overall trust score for user's archive

        Returns:
            Dict with score (0-100), breakdown, and recommendations
        """
        scores = {
            'identity_completeness': self._score_identity_completeness(),
            'blockchain_activity': self._score_blockchain_activity(),
            'social_data_coverage': self._score_social_coverage(),
            'temporal_consistency': self._score_temporal_consistency(),
            'cross_reference_alignment': self._score_cross_references()
        }

        # Weighted average
        weights = {
            'identity_completeness': 0.15,
            'blockchain_activity': 0.25,
            'social_data_coverage': 0.20,
            'temporal_consistency': 0.15,
            'cross_reference_alignment': 0.25
        }

        overall = sum(scores[k] * weights[k] for k in scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(scores)

        return {
            'overall_score': round(overall),
            'level': self._score_to_level(overall),
            'breakdown': scores,
            'recommendations': recommendations,
            'calculated_at': datetime.now().isoformat()
        }

    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to level"""
        if score < 20:
            return 'critical'
        elif score < 40:
            return 'low'
        elif score < 60:
            return 'moderate'
        elif score < 85:
            return 'good'
        else:
            return 'excellent'

    def _score_identity_completeness(self) -> float:
        """Score based on how complete the identity layer is"""
        training_file = self.kb_path / "training_data.json"
        if not training_file.exists():
            return 0

        try:
            with open(training_file, 'r') as f:
                data = json.load(f)

            identity = data.get('identity', {})

            # Check for key identity fields
            fields = [
                'professional_names',
                'wallet_1',  # At least one wallet
                'platform_profiles',
                'social_handles'
            ]

            filled = sum(1 for f in fields if identity.get(f))
            return (filled / len(fields)) * 100

        except Exception as e:
            logger.error(f"Error scoring identity: {e}")
            return 0

    def _score_blockchain_activity(self) -> float:
        """Score based on blockchain data presence"""
        blockchain_db = self.kb_path.parent / "db" / "blockchain.db"
        raw_blockchain = self.kb_path / "raw" / "blockchain"

        score = 0

        # Check for blockchain database
        if blockchain_db.exists():
            score += 40

        # Check for raw blockchain data
        if raw_blockchain.exists() and any(raw_blockchain.iterdir()):
            score += 30

        # Check for minting addresses in config
        training_file = self.kb_path / "training_data.json"
        if training_file.exists():
            try:
                with open(training_file, 'r') as f:
                    data = json.load(f)
                if data.get('identity', {}).get('wallet_1'):
                    score += 30
            except:
                pass

        return min(100, score)

    def _score_social_coverage(self) -> float:
        """Score based on social media data imports"""
        score = 0

        # Check for Twitter data
        twitter_raw = self.kb_path / "raw" / "twitter"
        twitter_processed = list(self.kb_path.glob("processed/**/twitter_*.md"))
        if twitter_raw.exists() or twitter_processed:
            score += 50

        # Check for Instagram data
        instagram_raw = self.kb_path / "raw" / "instagram"
        instagram_processed = list(self.kb_path.glob("processed/**/instagram_*.md"))
        if instagram_raw.exists() or instagram_processed:
            score += 30

        # Check for other social data
        other_social = list(self.kb_path.glob("processed/about_social_media/*.md"))
        if other_social:
            score += 20

        return min(100, score)

    def _score_temporal_consistency(self) -> float:
        """
        Score based on timeline consistency
        - Do claimed start dates align with earliest blockchain activity?
        - Are there unexplained gaps?
        """
        # This would require more sophisticated analysis
        # For now, return moderate score if data exists
        training_file = self.kb_path / "training_data.json"
        if training_file.exists():
            try:
                with open(training_file, 'r') as f:
                    data = json.load(f)
                # Check for throughline data (evolution points, etc.)
                if data.get('throughline'):
                    return 70
                return 40
            except:
                pass
        return 20

    def _score_cross_references(self) -> float:
        """
        Score based on cross-referencing data sources
        - Do Twitter posts mention NFT drops that appear on-chain?
        - Do claimed collections match blockchain records?
        """
        score = 0

        # Check if both blockchain and social data exist
        has_blockchain = (self.kb_path.parent / "db" / "blockchain.db").exists()
        has_twitter = (self.kb_path / "raw" / "twitter").exists() or list(self.kb_path.glob("processed/**/twitter_*.md"))

        if has_blockchain and has_twitter:
            score = 60  # Base score for having both sources
            # More sophisticated cross-referencing would improve this
        elif has_blockchain or has_twitter:
            score = 30  # Only one source

        return score

    def _generate_recommendations(self, scores: Dict) -> List[str]:
        """Generate actionable recommendations based on scores"""
        recs = []

        if scores['identity_completeness'] < 50:
            recs.append("Complete your Identity layer with professional names and wallet addresses")

        if scores['blockchain_activity'] < 40:
            recs.append("Add minting addresses to connect your blockchain activity")

        if scores['social_data_coverage'] < 30:
            recs.append("Import your Twitter or Instagram archive to build social context")

        if scores['temporal_consistency'] < 50:
            recs.append("Add your Artistic Throughline to document your creative evolution")

        if scores['cross_reference_alignment'] < 50:
            recs.append("Having both blockchain and social data helps verify your history")

        if not recs:
            recs.append("Your archive is well-documented. Keep it updated!")

        return recs


def get_trust_score_for_display(user_id: str = None) -> Dict:
    """
    Get trust score formatted for UI display

    Returns ready-to-render data for trust_indicator component
    """
    calculator = TrustScoreCalculator()
    result = calculator.calculate_score(user_id)

    return {
        'trust_score': result['overall_score'],
        'level': result['level'],
        'breakdown': result['breakdown'],
        'recommendations': result['recommendations']
    }
