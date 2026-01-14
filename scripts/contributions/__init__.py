"""
User Micro TX Protocol - Contribution Tracking for CRE-8 Agent Training

This module implements the heart-forward contribution system that:
1. Captures user contributions (on-chain + off-chain)
2. Validates alignment through multi-tier verification
3. Calculates ACU-METER scores
4. Feeds into agent training via inspiration folder

Components:
- micro_tx_db: Database schema and operations
- contribution_processor: Recognition and validation pipeline
- heart_forward_verifier: Multi-tier verification system
- acu_meter_engine: 4-component score calculation
- on_chain_listener: Blockchain event monitoring
- contribution_routes: Flask API endpoints

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 8
"""

from .micro_tx_db import MicroTXDatabase
from .contribution_processor import ContributionProcessor
from .heart_forward_verifier import HeartForwardVerifier
from .acu_meter_engine import ACUMeterEngine

__all__ = [
    'MicroTXDatabase',
    'ContributionProcessor',
    'HeartForwardVerifier',
    'ACUMeterEngine'
]

# Contribution type weights from protocol
CONTRIBUTION_WEIGHTS = {
    'mint': {'base': 'HIGH', 'numeric': 1.0, 'signal': 'Creative alignment verified'},
    'wisdom_share': {'base': 'HIGH', 'numeric': 1.0, 'signal': 'Knowledge propagation'},
    'curation_vote': {'base': 'MEDIUM', 'numeric': 0.6, 'signal': 'Taste/judgment signal'},
    'archive_action': {'base': 'MEDIUM', 'numeric': 0.6, 'signal': 'Preservation intent'},
    'social_endorsement': {'base': 'LOW', 'numeric': 0.3, 'signal': 'Community trust signal'}
}

# ACU-METER thresholds
ACU_THRESHOLDS = {
    'restricted': {'min_percentile': 0, 'permissions': ['view', 'basic_contribute']},
    'standard': {'min_percentile': 75, 'permissions': ['view', 'contribute', 'vote', 'archive']},
    'elevated': {'min_percentile': 90, 'permissions': ['view', 'contribute', 'vote', 'archive', 'curate', 'moderate']}
}
