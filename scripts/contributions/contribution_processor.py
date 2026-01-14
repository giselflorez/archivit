"""
Contribution Processor - Recognition and validation pipeline

Handles:
1. Recognizing contribution types from submissions
2. Mapping contributions to weight categories
3. Preparing contributions for verification pipeline
4. Persisting validated contributions to inspiration folder

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 8
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .micro_tx_db import (
    MicroTXDatabase,
    UserContribution,
    ContributionType,
    ValidationStatus,
    AlignmentLog
)


@dataclass
class ContributionRecognitionResult:
    """Result of contribution recognition."""
    contribution_type: str
    base_weight: str
    numeric_weight: float
    signal_description: str
    is_on_chain: bool
    content_hash: str
    content_summary: str


# Weight mapping from protocol specification
CONTRIBUTION_WEIGHTS = {
    'mint': {
        'base': 'HIGH',
        'numeric': 1.0,
        'signal': 'Creative alignment verified',
        'auto_verify': True  # On-chain mints are pre-verified
    },
    'wisdom_share': {
        'base': 'HIGH',
        'numeric': 1.0,
        'signal': 'Knowledge propagation',
        'auto_verify': False
    },
    'curation_vote': {
        'base': 'MEDIUM',
        'numeric': 0.6,
        'signal': 'Taste/judgment signal',
        'auto_verify': True  # Voting is a clear action
    },
    'archive_action': {
        'base': 'MEDIUM',
        'numeric': 0.6,
        'signal': 'Preservation intent',
        'auto_verify': True
    },
    'social_endorsement': {
        'base': 'LOW',
        'numeric': 0.3,
        'signal': 'Community trust signal',
        'auto_verify': False
    }
}

# Inspiration folder paths
INSPIRATION_BASE = Path(__file__).parent.parent.parent / 'inspiration' / 'user_contributions'


class ContributionProcessor:
    """
    Processes user contributions through the recognition and validation pipeline.

    Flow:
    USER_MICRO_TX → RECOGNIZE → VALIDATE → INTEGRATE → COMPOUND → MANIFEST
    """

    def __init__(self, db: MicroTXDatabase = None):
        self.db = db or MicroTXDatabase()
        self._ensure_folders()

    def _ensure_folders(self):
        """Ensure inspiration folder structure exists."""
        for folder in ['pending', 'verified', 'rejected']:
            (INSPIRATION_BASE / folder).mkdir(parents=True, exist_ok=True)

    def _generate_content_hash(self, content: Any) -> str:
        """Generate hash for content deduplication."""
        if isinstance(content, dict):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)

        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def _generate_summary(self, contribution_type: str, content: Dict) -> str:
        """Generate human-readable summary of contribution."""
        if contribution_type == 'mint':
            return f"Minted NFT: {content.get('token_id', 'unknown')} on {content.get('network', 'ethereum')}"

        elif contribution_type == 'wisdom_share':
            text = content.get('content', content.get('text', ''))
            return text[:100] + '...' if len(text) > 100 else text

        elif contribution_type == 'curation_vote':
            target = content.get('target_id', 'unknown')
            vote = content.get('vote', 'unknown')
            return f"Voted '{vote}' on {target}"

        elif contribution_type == 'archive_action':
            action = content.get('action', 'archive')
            target = content.get('target', 'unknown')
            return f"Archive action: {action} on {target}"

        elif contribution_type == 'social_endorsement':
            target = content.get('target_address', content.get('target', 'unknown'))
            return f"Endorsed: {target}"

        return "Unknown contribution"

    # ================================================================
    # RECOGNITION PHASE
    # ================================================================

    def recognize(self, submission: Dict[str, Any]) -> ContributionRecognitionResult:
        """
        Recognize contribution type from submission.

        Supports both on-chain events and off-chain submissions.
        """
        # Detect if this is an on-chain event
        is_on_chain = bool(submission.get('tx_hash') or submission.get('block_number'))

        # Determine contribution type
        contribution_type = self._detect_contribution_type(submission, is_on_chain)

        # Get weight configuration
        weight_config = CONTRIBUTION_WEIGHTS.get(contribution_type, CONTRIBUTION_WEIGHTS['social_endorsement'])

        # Generate content hash and summary
        content = submission.get('content', submission)
        content_hash = self._generate_content_hash(content)
        content_summary = self._generate_summary(contribution_type, content if isinstance(content, dict) else {'content': content})

        return ContributionRecognitionResult(
            contribution_type=contribution_type,
            base_weight=weight_config['base'],
            numeric_weight=weight_config['numeric'],
            signal_description=weight_config['signal'],
            is_on_chain=is_on_chain,
            content_hash=content_hash,
            content_summary=content_summary
        )

    def _detect_contribution_type(self, submission: Dict, is_on_chain: bool) -> str:
        """Detect contribution type from submission data."""
        # Explicit type provided
        if 'type' in submission:
            contrib_type = submission['type'].lower().replace('-', '_')
            if contrib_type in CONTRIBUTION_WEIGHTS:
                return contrib_type

        # On-chain event detection
        if is_on_chain:
            from_addr = submission.get('from_address', '').lower()
            event_type = submission.get('event_type', '').lower()

            # Mint detection (from null address)
            if from_addr == '0x0000000000000000000000000000000000000000':
                return 'mint'

            # Transfer could be various things
            if event_type == 'transfer':
                return 'archive_action'

        # Off-chain submission detection
        content = submission.get('content', {})

        if isinstance(content, dict):
            # Wisdom share: has text content
            if 'text' in content or 'knowledge' in content or 'teaching' in content:
                return 'wisdom_share'

            # Curation vote: has vote/target
            if 'vote' in content or 'rating' in content:
                return 'curation_vote'

            # Archive action: has archive-related keys
            if 'archive' in content or 'preserve' in content or 'backup' in content:
                return 'archive_action'

        elif isinstance(content, str):
            # Long text is likely wisdom share
            if len(content) > 50:
                return 'wisdom_share'

        # Default
        return 'social_endorsement'

    # ================================================================
    # PROCESS PHASE
    # ================================================================

    def process_submission(
        self,
        address: str,
        submission: Dict[str, Any]
    ) -> Tuple[int, ContributionRecognitionResult]:
        """
        Process a new contribution submission.

        Returns contribution ID and recognition result.
        """
        # Get or create contributor
        contributor = self.db.get_or_create_contributor(address)

        # Recognize contribution
        recognition = self.recognize(submission)

        # Prepare content JSON
        content = submission.get('content', submission)
        content_json = json.dumps(content) if isinstance(content, dict) else json.dumps({'content': content})

        # Determine initial validation status
        weight_config = CONTRIBUTION_WEIGHTS.get(recognition.contribution_type, {})
        if weight_config.get('auto_verify') and recognition.is_on_chain:
            initial_status = ValidationStatus.AUTO_APPROVED.value
        else:
            initial_status = ValidationStatus.PENDING.value

        # Create contribution record
        contribution = UserContribution(
            contributor_id=contributor.id,
            tx_hash=submission.get('tx_hash'),
            contribution_type=recognition.contribution_type,
            content_hash=recognition.content_hash,
            content_summary=recognition.content_summary,
            content_json=content_json,
            validation_status=initial_status,
            base_weight=recognition.base_weight,
            calculated_weight=recognition.numeric_weight if initial_status == 'auto_approved' else 0.0,
            block_number=submission.get('block_number'),
            block_timestamp=submission.get('block_timestamp'),
            network=submission.get('network', 'ethereum')
        )

        contribution_id = self.db.create_contribution(contribution)

        # Create verification queue entry
        self.db.create_verification_entry(contribution_id)

        # Log the submission
        self.db.log_alignment_event(AlignmentLog(
            event_type='contribution',
            contributor_id=contributor.id,
            contribution_id=contribution_id,
            action='submitted',
            new_state=json.dumps({
                'type': recognition.contribution_type,
                'weight': recognition.base_weight,
                'status': initial_status
            }),
            triggered_by='user',
            triggering_entity=address
        ))

        # If auto-approved, persist to verified folder
        if initial_status == ValidationStatus.AUTO_APPROVED.value:
            self._persist_to_inspiration(contribution_id, 'verified')

        return contribution_id, recognition

    # ================================================================
    # VALIDATION UPDATE
    # ================================================================

    def update_validation(
        self,
        contribution_id: int,
        status: ValidationStatus,
        heart_forward_score: float,
        verification_path: str
    ):
        """Update contribution validation status after verification."""
        contribution = self.db.get_contribution(contribution_id)
        if not contribution:
            return

        # Get weight config
        weight_config = CONTRIBUTION_WEIGHTS.get(contribution.contribution_type, {})

        # Calculate final weight based on validation
        if status in [ValidationStatus.AUTO_APPROVED, ValidationStatus.COMMUNITY_VERIFIED, ValidationStatus.MANUAL_APPROVED]:
            calculated_weight = weight_config.get('numeric', 0.3) * heart_forward_score
            folder = 'verified'
        else:
            calculated_weight = 0.0
            folder = 'rejected'

        # Update database
        self.db.update_contribution_validation(
            contribution_id,
            status.value,
            heart_forward_score,
            calculated_weight
        )

        # Finalize verification
        self.db.finalize_verification(contribution_id, status.value, verification_path)

        # Persist to appropriate inspiration folder
        self._persist_to_inspiration(contribution_id, folder)

        # Log the validation
        self.db.log_alignment_event(AlignmentLog(
            event_type='verification',
            contributor_id=contribution.contributor_id,
            contribution_id=contribution_id,
            action='validated',
            previous_state=contribution.validation_status,
            new_state=json.dumps({
                'status': status.value,
                'heart_forward_score': heart_forward_score,
                'calculated_weight': calculated_weight,
                'verification_path': verification_path
            }),
            change_reason=f"Verified via {verification_path}",
            triggered_by=verification_path,
            triggering_entity='system'
        ))

    # ================================================================
    # INSPIRATION FOLDER INTEGRATION
    # ================================================================

    def _persist_to_inspiration(self, contribution_id: int, folder: str):
        """Persist contribution to inspiration folder."""
        contribution = self.db.get_contribution(contribution_id)
        if not contribution:
            return

        contributor = self.db.get_contributor_by_address(
            # Need to get address from contributor_id
            ''  # Will be populated below
        )

        # Build contribution document
        doc = {
            'id': contribution.id,
            'contributor_id': contribution.contributor_id,
            'contribution_type': contribution.contribution_type,
            'content_summary': contribution.content_summary,
            'content': json.loads(contribution.content_json) if contribution.content_json else {},
            'validation_status': contribution.validation_status,
            'heart_forward_score': contribution.heart_forward_score,
            'base_weight': contribution.base_weight,
            'calculated_weight': contribution.calculated_weight,
            'network': contribution.network,
            'tx_hash': contribution.tx_hash,
            'created_at': contribution.created_at,
            'validated_at': contribution.validated_at
        }

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{contribution.id}_{contribution.contribution_type}_{timestamp}.json"

        # Write to folder
        filepath = INSPIRATION_BASE / folder / filename
        with open(filepath, 'w') as f:
            json.dump(doc, f, indent=2, default=str)

        return str(filepath)

    # ================================================================
    # BATCH OPERATIONS
    # ================================================================

    def process_on_chain_event(self, event: Dict[str, Any]) -> Optional[int]:
        """
        Process an on-chain event (from blockchain listener).

        Returns contribution ID if processed, None if skipped.
        """
        # Check if already processed
        tx_hash = event.get('tx_hash')
        if not tx_hash:
            return None

        # Determine the address to credit
        to_address = event.get('to_address')
        if not to_address or to_address == '0x0000000000000000000000000000000000000000':
            return None

        # Process as submission
        contribution_id, recognition = self.process_submission(to_address, event)

        return contribution_id

    def get_contribution_for_display(self, contribution_id: int) -> Optional[Dict]:
        """Get contribution with full details for display."""
        contribution = self.db.get_contribution(contribution_id)
        if not contribution:
            return None

        return {
            'id': contribution.id,
            'type': contribution.contribution_type,
            'summary': contribution.content_summary,
            'status': contribution.validation_status,
            'heart_forward_score': contribution.heart_forward_score,
            'weight': {
                'base': contribution.base_weight,
                'calculated': contribution.calculated_weight
            },
            'on_chain': bool(contribution.tx_hash),
            'network': contribution.network,
            'created_at': contribution.created_at
        }


# Convenience function
def process_contribution(address: str, submission: Dict) -> Tuple[int, Dict]:
    """Process a contribution and return ID and recognition info."""
    processor = ContributionProcessor()
    contribution_id, recognition = processor.process_submission(address, submission)

    return contribution_id, {
        'type': recognition.contribution_type,
        'weight': recognition.base_weight,
        'signal': recognition.signal_description,
        'on_chain': recognition.is_on_chain
    }
