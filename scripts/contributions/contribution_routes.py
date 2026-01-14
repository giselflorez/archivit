"""
Contribution Routes - Flask API endpoints for User Micro TX Protocol

Endpoints:
- POST /api/v1/contributions/submit - Submit new contribution
- GET  /api/v1/contributions/history - Get user's contribution history
- GET  /api/v1/contributions/acu-score - Get ACU-METER score
- GET  /api/v1/contributions/acu-score/history - Get score history
- POST /api/v1/contributions/verify/:id - Cast community vote
- GET  /api/v1/contributions/verify/:id/status - Get verification status
- GET  /api/v1/contributions/pending - Get pending verifications
- GET  /api/v1/contributions/leaderboard - Get top contributors
- GET  /api/v1/contributions/stats - Get system statistics

Created: Jan 11, 2026
Protocol: WISDOM_KNOWLEDGE_BASE.md Section 8
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json

from .micro_tx_db import MicroTXDatabase, ValidationStatus
from .contribution_processor import ContributionProcessor
from .heart_forward_verifier import HeartForwardVerifier
from .acu_meter_engine import ACUMeterEngine


# Create Blueprint
contributions_bp = Blueprint('contributions', __name__, url_prefix='/api/v1/contributions')

# Initialize components
db = MicroTXDatabase()
processor = ContributionProcessor(db)
verifier = HeartForwardVerifier(db)
engine = ACUMeterEngine(db)


# ================================================================
# SUBMISSION ENDPOINTS
# ================================================================

@contributions_bp.route('/submit', methods=['POST'])
def submit_contribution():
    """
    Submit a new contribution.

    Request body:
    {
        "address": "0x...",  // Required: contributor wallet address
        "type": "wisdom_share",  // Required: contribution type
        "content": {...},  // Required: contribution content
        "tx_hash": "0x...",  // Optional: on-chain transaction hash
        "network": "ethereum"  // Optional: blockchain network
    }

    Returns:
    {
        "success": true,
        "contribution_id": 123,
        "recognition": {
            "type": "wisdom_share",
            "weight": "HIGH",
            "signal": "Knowledge propagation"
        },
        "verification_status": "pending"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        address = data.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        content = data.get('content')
        contribution_type = data.get('type')

        if not content and not contribution_type:
            return jsonify({'error': 'Content or type is required'}), 400

        # Prepare submission
        submission = {
            'type': contribution_type,
            'content': content,
            'tx_hash': data.get('tx_hash'),
            'network': data.get('network', 'ethereum')
        }

        # Process contribution
        contribution_id, recognition = processor.process_submission(address, submission)

        # Run verification
        verification_result = verifier.run_full_verification(contribution_id)

        # Update validation based on verification
        if verification_result.passed:
            processor.update_validation(
                contribution_id,
                ValidationStatus.AUTO_APPROVED,
                verification_result.score,
                'auto'
            )

        # Recalculate ACU-METER score
        contributor = db.get_contributor_by_address(address)
        if contributor:
            engine.calculate_score(contributor.id)

        return jsonify({
            'success': True,
            'contribution_id': contribution_id,
            'recognition': {
                'type': recognition.contribution_type,
                'weight': recognition.base_weight,
                'signal': recognition.signal_description,
                'on_chain': recognition.is_on_chain
            },
            'verification': {
                'status': 'approved' if verification_result.passed else 'pending',
                'score': verification_result.score,
                'tier': verification_result.tier,
                'details': verification_result.details
            }
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# HISTORY ENDPOINTS
# ================================================================

@contributions_bp.route('/history', methods=['GET'])
def get_contribution_history():
    """
    Get contribution history for an address.

    Query params:
    - address: wallet address (required)
    - limit: max results (default 50)
    - offset: pagination offset (default 0)

    Returns:
    {
        "contributions": [...],
        "total": 100,
        "address": "0x..."
    }
    """
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        contributor = db.get_contributor_by_address(address)
        if not contributor:
            return jsonify({
                'contributions': [],
                'total': 0,
                'address': address
            })

        contributions = db.get_contributions_by_contributor(contributor.id, limit=limit + offset)

        # Apply offset
        contributions = contributions[offset:offset + limit]

        return jsonify({
            'contributions': [
                processor.get_contribution_for_display(c.id)
                for c in contributions
            ],
            'total': len(contributions),
            'address': address
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# ACU-METER ENDPOINTS
# ================================================================

@contributions_bp.route('/acu-score', methods=['GET'])
def get_acu_score():
    """
    Get ACU-METER score for an address.

    Query params:
    - address: wallet address (required)

    Returns:
    {
        "address": "0x...",
        "scores": {
            "intent": 0.85,
            "wisdom": 0.72,
            "application": 0.90,
            "legacy": 0.65
        },
        "weighted_total": 0.78,
        "percentage": 78.0,
        "percentile_rank": 85.5,
        "access_level": "standard",
        "threshold_met": true
    }
    """
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        result = engine.get_score(address)

        if not result:
            # Return default for new address
            return jsonify({
                'address': address,
                'scores': {
                    'intent': 0.0,
                    'wisdom': 0.0,
                    'application': 0.0,
                    'legacy': 0.0
                },
                'weighted_total': 0.0,
                'percentage': 0.0,
                'percentile_rank': 0.0,
                'access_level': 'restricted',
                'threshold_met': False,
                'is_new': True
            })

        return jsonify({
            'address': address,
            'scores': {
                'intent': result.intent_score,
                'wisdom': result.wisdom_score,
                'application': result.application_score,
                'legacy': result.legacy_score
            },
            'weights': result.weights,
            'weighted_total': result.weighted_total,
            'percentage': result.percentage,
            'percentile_rank': result.percentile_rank,
            'access_level': result.access_level,
            'threshold_met': result.threshold_met,
            'details': result.calculation_details
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contributions_bp.route('/acu-score/history', methods=['GET'])
def get_acu_score_history():
    """
    Get ACU-METER score history for an address.

    Query params:
    - address: wallet address (required)
    - days: number of days of history (default 30)
    """
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        days = int(request.args.get('days', 30))

        contributor = db.get_contributor_by_address(address)
        if not contributor:
            return jsonify({'history': [], 'address': address})

        # Get score history from database
        conn = db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM acu_meter_scores
            WHERE contributor_id = ?
            ORDER BY calculated_at DESC
            LIMIT ?
        """, (contributor.id, days))

        rows = cursor.fetchall()
        conn.close()

        history = [
            {
                'date': row['calculated_at'],
                'scores': {
                    'intent': row['intent_score'],
                    'wisdom': row['wisdom_score'],
                    'application': row['application_score'],
                    'legacy': row['legacy_score']
                },
                'weighted_total': row['weighted_total'],
                'percentile_rank': row['percentile_rank'],
                'access_level': row['access_level']
            }
            for row in rows
        ]

        return jsonify({
            'history': history,
            'address': address
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# VERIFICATION ENDPOINTS
# ================================================================

@contributions_bp.route('/verify/<int:contribution_id>', methods=['POST'])
def cast_vote(contribution_id):
    """
    Cast a community vote on a contribution.

    Request body:
    {
        "voter_address": "0x...",
        "vote": "for" | "against",
        "reason": "optional reason"
    }

    Returns:
    {
        "success": true,
        "vote_state": {...}
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        voter_address = data.get('voter_address')
        vote_type = data.get('vote')

        if not voter_address:
            return jsonify({'error': 'Voter address is required'}), 400

        if vote_type not in ['for', 'against']:
            return jsonify({'error': 'Vote must be "for" or "against"'}), 400

        reason = data.get('reason')

        # Process vote
        vote_state = verifier.process_community_vote(
            contribution_id,
            voter_address,
            vote_type,
            reason
        )

        # Check if we can finalize
        finalization = verifier.finalize_community_verification(contribution_id)

        if finalization:
            # Update contribution status
            status = ValidationStatus.COMMUNITY_VERIFIED if finalization.passed else ValidationStatus.REJECTED
            processor.update_validation(
                contribution_id,
                status,
                finalization.score,
                'community'
            )

        return jsonify({
            'success': True,
            'vote_state': vote_state,
            'finalized': finalization is not None,
            'finalization_result': finalization.details if finalization else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contributions_bp.route('/verify/<int:contribution_id>/status', methods=['GET'])
def get_verification_status(contribution_id):
    """
    Get verification status for a contribution.

    Returns:
    {
        "contribution_id": 123,
        "current_status": "pending",
        "automated": {...},
        "community": {...},
        "final_status": "pending"
    }
    """
    try:
        status = verifier.get_verification_status(contribution_id)
        return jsonify(status)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contributions_bp.route('/pending', methods=['GET'])
def get_pending_verifications():
    """
    Get contributions pending verification.

    Query params:
    - limit: max results (default 50)

    Returns:
    {
        "pending": [...],
        "total": 10
    }
    """
    try:
        limit = int(request.args.get('limit', 50))

        pending = db.get_pending_verifications(limit)

        return jsonify({
            'pending': [
                {
                    'id': p['id'],
                    'type': p['contribution_type'],
                    'summary': p['content_summary'],
                    'created_at': p['created_at'],
                    'automated_result': p.get('automated_result'),
                    'community_votes_for': p.get('community_votes_for', 0),
                    'community_votes_against': p.get('community_votes_against', 0)
                }
                for p in pending
            ],
            'total': len(pending)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# LEADERBOARD & STATS
# ================================================================

@contributions_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Get top contributors by ACU-METER score.

    Query params:
    - limit: max results (default 10)

    Returns:
    {
        "rankings": [
            {
                "rank": 1,
                "address": "0x...",
                "display_name": "Artist",
                "acu_score": 0.95,
                "percentile": 99.5,
                "access_level": "elevated",
                "contribution_count": 42
            },
            ...
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 10))

        leaders = engine.get_leaderboard(limit)

        return jsonify({
            'rankings': [
                {
                    'rank': i + 1,
                    'address': l['primary_address'],
                    'display_name': l.get('display_name'),
                    'acu_score': l['acu_meter_score'],
                    'percentile': l['percentile_rank'],
                    'access_level': l['access_level'],
                    'contribution_count': l['contribution_count']
                }
                for i, l in enumerate(leaders)
            ]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contributions_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get system-wide contribution statistics.

    Returns:
    {
        "total_contributors": 100,
        "total_contributions": 500,
        "by_type": {...},
        "by_status": {...},
        "avg_acu_score": 0.72,
        "access_distribution": {...}
    }
    """
    try:
        stats = db.get_contribution_stats()

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# QUANTUM STATE
# ================================================================

@contributions_bp.route('/quantum-state', methods=['GET'])
def get_quantum_state():
    """
    Get current quantum state snapshot.

    Returns current system perspective including metrics,
    weights, and thresholds.
    """
    try:
        snapshot = engine.update_quantum_state()
        return jsonify(snapshot)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# ACCESS CHECK
# ================================================================

@contributions_bp.route('/check-access', methods=['GET'])
def check_access():
    """
    Check if an address has required access level.

    Query params:
    - address: wallet address (required)
    - level: required level (default "standard")

    Returns:
    {
        "address": "0x...",
        "required_level": "standard",
        "has_access": true,
        "current_level": "elevated"
    }
    """
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({'error': 'Address is required'}), 400

        required_level = request.args.get('level', 'standard')

        has_access = engine.check_access(address, required_level)

        contributor = db.get_contributor_by_address(address)
        current_level = contributor.access_level if contributor else 'restricted'

        return jsonify({
            'address': address,
            'required_level': required_level,
            'has_access': has_access,
            'current_level': current_level
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# BLUEPRINT REGISTRATION HELPER
# ================================================================

def register_contribution_routes(app):
    """Register contribution routes with Flask app."""
    app.register_blueprint(contributions_bp)
    print("Registered contribution routes at /api/v1/contributions/")
