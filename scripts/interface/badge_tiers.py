#!/usr/bin/env python3
"""
Badge Tier System

DESIGN PRINCIPLE: Minimal words, intuitive design.
All UI text must be short and instantly understandable.
No jargon. No long explanations. Icons > text where possible.

Base Tiers (3 tiers):
- SOLO (1 wallet): Private, local only
- ENTERPRISE (6 wallets): Enterprise agreement
- WHITE GLOVE (unlimited): Self-hosted API required (guided setup available)

Bonuses (additive):
- ACU-METER Certified NFT: +2 wallets (also grants "CERTIFIED" status)
- Self-hosted API: +2 wallets

Examples:
- SOLO = 1
- SOLO + ACU-METER = 3 (certified)
- SOLO + ACU-METER + Self-hosted = 5
- ENTERPRISE = 6
- ENTERPRISE + ACU-METER = 8 (certified)
- ENTERPRISE + ACU-METER + Self-hosted = 10
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BadgeTierSystem:
    """
    Manages badge tiers and bonuses.

    Base Tiers (3):
        0: SOLO (1 wallet)
        1: ENTERPRISE (6 wallets)
        2: WHITE GLOVE (unlimited)

    Bonuses (additive):
        ACU-METER Certified: +2 wallets (grants "CERTIFIED" status)
        Self-hosted API: +2 wallets
    """

    TIERS_FILE = Path("knowledge_base/badge_tiers.json")

    # Bonus values
    ACCUMETER_BONUS = 2
    SELF_HOSTED_BONUS = 2

    TIERS = {
        0: {
            'name': 'Solo',
            'label': 'SOLO',
            'wallet_limit': 1,
            'features': [
                'Single wallet tracking',
                'Private knowledge base'
            ],
            'requirements': []
        },
        1: {
            'name': 'Enterprise',
            'label': 'ENTERPRISE',
            'wallet_limit': 6,
            'features': [
                'Up to 6 wallet addresses',
                'Enterprise support'
            ],
            'requirements': [
                'Enterprise agreement'
            ]
        },
        2: {
            'name': 'White Glove',
            'label': 'WHITE GLOVE',
            'wallet_limit': -1,  # Unlimited
            'features': [
                'Unlimited wallet addresses',
                'Full data sovereignty',
                'Custom integration support'
            ],
            'requirements': [
                'Self-hosted API (guided setup available)'
            ]
        }
    }

    def __init__(self):
        self._load_tiers()

    def _load_tiers(self):
        """Load tier registry"""
        self.TIERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.TIERS_FILE.exists():
            try:
                with open(self.TIERS_FILE, 'r') as f:
                    self.registry = json.load(f)
            except:
                self.registry = {'users': {}}
        else:
            self.registry = {'users': {}}

    def _save_tiers(self):
        """Save tier registry"""
        with open(self.TIERS_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def get_user_tier(self, user_id: str) -> Dict:
        """Get user's current tier info"""
        user_data = self.registry['users'].get(user_id, {
            'tier': 0,
            'upgraded_at': None,
            'verification_method': None
        })

        tier_level = user_data.get('tier', 0)
        tier_info = self.TIERS.get(tier_level, self.TIERS[0])

        return {
            'tier': tier_level,
            'tier_name': tier_info['name'],
            'tier_label': tier_info['label'],
            'wallet_limit': tier_info['wallet_limit'],
            'features': tier_info['features'],
            'upgraded_at': user_data.get('upgraded_at'),
            'verification_method': user_data.get('verification_method')
        }

    def activate_accumeter(self, user_id: str, nft_registration: Dict) -> Dict:
        """
        Activate Accumeter Certified bonus (+3 wallets) via NFT mint.
        Does NOT change tier - adds bonus to current tier.

        Args:
            user_id: User identifier
            nft_registration: Dict with chain, token_id, wallet_address, tx_hash

        Returns:
            Activation result
        """
        if user_id not in self.registry['users']:
            self.registry['users'][user_id] = {'tier': 0}

        # Add Accumeter certification (bonus, not tier change)
        self.registry['users'][user_id]['accumeter_certified'] = True
        self.registry['users'][user_id]['accumeter_activated_at'] = datetime.now().isoformat()
        self.registry['users'][user_id]['nft_chain'] = nft_registration.get('chain')
        self.registry['users'][user_id]['nft_token_id'] = nft_registration.get('token_id')
        self.registry['users'][user_id]['nft_wallet'] = nft_registration.get('wallet_address')
        self.registry['users'][user_id]['nft_tx_hash'] = nft_registration.get('tx_hash')

        self._save_tiers()

        new_limit = self.get_wallet_limit(user_id)
        logger.info(f"User {user_id} activated Accumeter (+3 wallets)")

        return {
            'success': True,
            'bonus': self.ACCUMETER_BONUS,
            'wallet_limit': new_limit,
            'message': 'ACU-METER ACTIVATED'
        }

    # Keep old function name for backward compatibility with routes
    def upgrade_to_ultra(self, user_id: str, nft_registration: Dict) -> Dict:
        """Alias for activate_accumeter (backward compatibility)"""
        return self.activate_accumeter(user_id, nft_registration)

    def is_accumeter_certified(self, user_id: str) -> bool:
        """Check if user has Accumeter NFT bonus"""
        user_data = self.registry['users'].get(user_id, {})
        return user_data.get('accumeter_certified', False)

    def get_wallet_limit(self, user_id: str) -> int:
        """
        Get total wallet limit for user.
        Base tier + Accumeter bonus (+3) + Self-hosted bonus (+2)
        """
        tier_info = self.get_user_tier(user_id)
        base_limit = tier_info['wallet_limit']

        # Unlimited stays unlimited
        if base_limit == -1:
            return -1

        total = base_limit

        # Add +3 bonus for ACU-METER Certified
        if self.is_accumeter_certified(user_id):
            total += self.ACCUMETER_BONUS

        # Add +2 bonus for self-hosted users
        if self.is_self_hosted(user_id):
            total += self.SELF_HOSTED_BONUS

        return total

    def is_self_hosted(self, user_id: str) -> bool:
        """Check if user is using self-hosted API"""
        user_data = self.registry['users'].get(user_id, {})
        return user_data.get('self_hosted', False)

    def set_self_hosted(self, user_id: str, enabled: bool, api_endpoint: str = None) -> Dict:
        """
        Enable/disable self-hosted API for user

        Self-hosting is available for ANY tier - user provides their own API
        endpoint and doesn't use the shared ARCHIV-IT API.
        """
        if user_id not in self.registry['users']:
            self.registry['users'][user_id] = {'tier': 0}

        self.registry['users'][user_id]['self_hosted'] = enabled
        self.registry['users'][user_id]['api_endpoint'] = api_endpoint if enabled else None

        self._save_tiers()

        return {
            'success': True,
            'self_hosted': enabled,
            'api_endpoint': api_endpoint,
            'message': 'Self-hosted API enabled' if enabled else 'Using shared API'
        }

    def get_api_endpoint(self, user_id: str) -> str:
        """Get API endpoint for user (custom if self-hosted, default otherwise)"""
        user_data = self.registry['users'].get(user_id, {})
        if user_data.get('self_hosted') and user_data.get('api_endpoint'):
            return user_data['api_endpoint']
        return None  # Use default shared API

    def can_add_wallet(self, user_id: str, current_wallet_count: int) -> Dict:
        """Check if user can add another wallet"""
        tier_info = self.get_user_tier(user_id)
        limit = tier_info['wallet_limit']

        if limit == -1:  # Unlimited
            return {'allowed': True, 'reason': 'White Glove - unlimited wallets'}

        if current_wallet_count < limit:
            return {'allowed': True, 'remaining': limit - current_wallet_count}

        # At limit - suggest upgrade
        next_tier = tier_info['tier'] + 1
        if next_tier in self.TIERS:
            return {
                'allowed': False,
                'reason': f"Wallet limit reached ({limit})",
                'suggestion': f"Upgrade to {self.TIERS[next_tier]['name']} for more wallets",
                'next_tier': next_tier,
                'next_tier_limit': self.TIERS[next_tier]['wallet_limit']
            }

        return {'allowed': False, 'reason': 'Maximum tier reached'}


def get_tier_comparison() -> Dict:
    """Get comparison data for tiers and bonuses (for UI display)"""
    return {
        'tiers': [
            {'tier': 0, 'name': 'SOLO', 'wallets': 1},
            {'tier': 1, 'name': 'ENTERPRISE', 'wallets': 6},
            {'tier': 2, 'name': 'WHITE GLOVE', 'wallets': 'Unlimited'}
        ],
        'bonuses': [
            {'name': 'ACU-METER Certified', 'bonus': '+2', 'unlock': 'Mint NFT', 'note': 'Grants CERTIFIED status'},
            {'name': 'Self-hosted API', 'bonus': '+2', 'unlock': 'Your infrastructure'}
        ],
        'examples': [
            {'combo': 'SOLO', 'total': 1},
            {'combo': 'SOLO + ACU-METER', 'total': 3, 'label': 'SOLO CERTIFIED'},
            {'combo': 'SOLO + ACU-METER + Self-hosted', 'total': 5},
            {'combo': 'ENTERPRISE', 'total': 6},
            {'combo': 'ENTERPRISE + ACU-METER', 'total': 8, 'label': 'ENTERPRISE CERTIFIED'},
            {'combo': 'ENTERPRISE + ACU-METER + Self-hosted', 'total': 10},
            {'combo': 'WHITE GLOVE', 'total': 'Unlimited'}
        ]
    }
