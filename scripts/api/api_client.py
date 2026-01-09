#!/usr/bin/env python3
"""
ARCHIV-IT API Client - Hybrid API Management

Routes API calls between:
- Managed APIs (through ARCHIV-IT backend with auth/quotas)
- BYOK APIs (user's own credentials, stored locally)
- Local-only services (no network required)
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Config paths
CONFIG_DIR = Path(__file__).parent.parent.parent / 'config'
API_CONFIG_PATH = CONFIG_DIR / 'api_config.json'
AUTH_TOKEN_PATH = CONFIG_DIR / 'archivit_auth.json'
USAGE_DB_PATH = CONFIG_DIR / 'usage_tracking.json'


@dataclass
class UsageQuota:
    """Track API usage against quotas"""
    requests_today: int = 0
    requests_this_month: int = 0
    last_reset_date: str = ""
    last_reset_month: str = ""
    tier: str = "free_tier"


@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    provider: str = ""
    quota_remaining: Optional[int] = None
    cached: bool = False


class ArchivitAPIClient:
    """
    Unified API client for ARCHIV-IT

    Handles:
    - Authentication with ARCHIV-IT backend
    - Managed API routing (vision, search)
    - BYOK credential management
    - Usage tracking and quota enforcement
    - Graceful fallbacks
    """

    def __init__(self, environment: str = None):
        self.config = self._load_config()
        self.environment = environment or self.config.get('environment', 'development')
        self.auth_token = self._load_auth_token()
        self.usage = self._load_usage()

        # Determine if we're in dev mode (use local APIs directly)
        self.dev_mode = self.environment == 'development' and \
                        self.config.get('development', {}).get('bypass_auth', False)

    def _load_config(self) -> Dict:
        """Load API configuration"""
        if API_CONFIG_PATH.exists():
            with open(API_CONFIG_PATH) as f:
                return json.load(f)
        return {}

    def _load_auth_token(self) -> Optional[Dict]:
        """Load cached authentication token"""
        if AUTH_TOKEN_PATH.exists():
            with open(AUTH_TOKEN_PATH) as f:
                token_data = json.load(f)
                # Check if expired
                if token_data.get('expires_at'):
                    expires = datetime.fromisoformat(token_data['expires_at'])
                    if expires > datetime.now():
                        return token_data
        return None

    def _save_auth_token(self, token_data: Dict):
        """Save authentication token"""
        with open(AUTH_TOKEN_PATH, 'w') as f:
            json.dump(token_data, f, indent=2)
        self.auth_token = token_data

    def _load_usage(self) -> UsageQuota:
        """Load usage tracking data"""
        if USAGE_DB_PATH.exists():
            with open(USAGE_DB_PATH) as f:
                data = json.load(f)
                return UsageQuota(**data)
        return UsageQuota()

    def _save_usage(self):
        """Save usage tracking data"""
        with open(USAGE_DB_PATH, 'w') as f:
            json.dump({
                'requests_today': self.usage.requests_today,
                'requests_this_month': self.usage.requests_this_month,
                'last_reset_date': self.usage.last_reset_date,
                'last_reset_month': self.usage.last_reset_month,
                'tier': self.usage.tier
            }, f, indent=2)

    def _check_and_reset_usage(self):
        """Reset usage counters if date/month changed"""
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')

        if self.usage.last_reset_date != today:
            self.usage.requests_today = 0
            self.usage.last_reset_date = today

        if self.usage.last_reset_month != month:
            self.usage.requests_this_month = 0
            self.usage.last_reset_month = month

        self._save_usage()

    def _increment_usage(self, api_name: str):
        """Increment usage counter"""
        self._check_and_reset_usage()
        self.usage.requests_today += 1
        self.usage.requests_this_month += 1
        self._save_usage()
        logger.debug(f"API usage: {api_name} - {self.usage.requests_today} today, {self.usage.requests_this_month} this month")

    def _check_quota(self, api_name: str) -> tuple[bool, Optional[str]]:
        """Check if quota allows request"""
        self._check_and_reset_usage()

        api_config = self.config.get('managed_apis', {}).get(api_name, {})
        quota_config = api_config.get('quota', {}).get(self.usage.tier, {})

        daily_limit = quota_config.get('requests_per_day', float('inf'))
        monthly_limit = quota_config.get('requests_per_month', float('inf'))

        if self.usage.requests_today >= daily_limit:
            return False, f"Daily quota exceeded ({daily_limit} requests/day)"

        if self.usage.requests_this_month >= monthly_limit:
            return False, f"Monthly quota exceeded ({monthly_limit} requests/month)"

        return True, None

    def get_quota_status(self) -> Dict:
        """Get current quota status for all managed APIs"""
        self._check_and_reset_usage()

        status = {
            'tier': self.usage.tier,
            'today': self.usage.requests_today,
            'this_month': self.usage.requests_this_month,
            'apis': {}
        }

        for api_name, api_config in self.config.get('managed_apis', {}).items():
            if api_name.startswith('_'):
                continue
            quota_config = api_config.get('quota', {}).get(self.usage.tier, {})
            status['apis'][api_name] = {
                'daily_limit': quota_config.get('requests_per_day', 0),
                'monthly_limit': quota_config.get('requests_per_month', 0),
                'daily_remaining': max(0, quota_config.get('requests_per_day', 0) - self.usage.requests_today),
                'monthly_remaining': max(0, quota_config.get('requests_per_month', 0) - self.usage.requests_this_month)
            }

        return status

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with ARCHIV-IT backend"""
        if self.dev_mode:
            return True
        return self.auth_token is not None

    def authenticate(self, email: str, password: str) -> APIResponse:
        """Authenticate with ARCHIV-IT backend"""
        if self.dev_mode:
            return APIResponse(success=True, data={'dev_mode': True})

        try:
            login_url = self.config.get('auth', {}).get('login_url')
            response = requests.post(login_url, json={
                'email': email,
                'password': password
            }, timeout=10)

            if response.ok:
                token_data = response.json()
                # Add expiry time
                expiry_hours = self.config.get('auth', {}).get('token_expiry_hours', 24)
                token_data['expires_at'] = (datetime.now() + timedelta(hours=expiry_hours)).isoformat()
                self._save_auth_token(token_data)
                return APIResponse(success=True, data=token_data)
            else:
                return APIResponse(success=False, error=response.json().get('error', 'Authentication failed'))

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return APIResponse(success=False, error=str(e))

    def _get_auth_headers(self) -> Dict:
        """Get authorization headers for managed API calls"""
        if self.dev_mode:
            return {}
        if self.auth_token:
            return {'Authorization': f"Bearer {self.auth_token.get('access_token', '')}"}
        return {}

    # =========================================================================
    # MANAGED APIs (Routed through ARCHIV-IT backend)
    # =========================================================================

    def vision_analyze(self, image_path: str, prompt: str = None) -> APIResponse:
        """
        Analyze image using managed vision API

        In production: Routes through api.archivit.io
        In dev mode: Uses local Anthropic API key
        """
        # Check quota
        allowed, error = self._check_quota('vision')
        if not allowed:
            return APIResponse(success=False, error=error, provider='managed')

        if self.dev_mode:
            # Development: Use local Anthropic key
            return self._vision_analyze_local(image_path, prompt)
        else:
            # Production: Route through backend
            return self._vision_analyze_managed(image_path, prompt)

    def _vision_analyze_local(self, image_path: str, prompt: str = None) -> APIResponse:
        """Direct API call using local credentials (dev mode)"""
        import anthropic
        import base64

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return APIResponse(
                success=False,
                error="ANTHROPIC_API_KEY not set. Add it to .env file.",
                provider='local'
            )

        try:
            client = anthropic.Anthropic(api_key=api_key)

            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')

            # Determine media type
            ext = Path(image_path).suffix.lower()
            media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
            media_type = media_types.get(ext, 'image/jpeg')

            default_prompt = "Describe this image in detail. Include any text visible, artistic style, colors, subjects, and mood."

            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                        {"type": "text", "text": prompt or default_prompt}
                    ]
                }]
            )

            self._increment_usage('vision')

            return APIResponse(
                success=True,
                data={'description': message.content[0].text},
                provider='claude-local',
                quota_remaining=self._get_remaining_quota('vision')
            )

        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return APIResponse(success=False, error=str(e), provider='local')

    def _vision_analyze_managed(self, image_path: str, prompt: str = None) -> APIResponse:
        """Route through ARCHIV-IT backend (production)"""
        endpoint = self.config['managed_apis']['vision']['endpoint']

        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'prompt': prompt} if prompt else {}

                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    headers=self._get_auth_headers(),
                    timeout=30
                )

            if response.ok:
                self._increment_usage('vision')
                result = response.json()
                return APIResponse(
                    success=True,
                    data=result,
                    provider='archivit-managed',
                    quota_remaining=result.get('quota_remaining')
                )
            else:
                return APIResponse(success=False, error=response.json().get('error'), provider='managed')

        except Exception as e:
            logger.error(f"Managed vision API error: {e}")
            return APIResponse(success=False, error=str(e), provider='managed')

    def search_web(self, query: str) -> APIResponse:
        """
        Search web using managed search API

        In production: Routes through api.archivit.io
        In dev mode: Uses local Perplexity API key
        """
        allowed, error = self._check_quota('search')
        if not allowed:
            return APIResponse(success=False, error=error, provider='managed')

        if self.dev_mode:
            return self._search_web_local(query)
        else:
            return self._search_web_managed(query)

    def _search_web_local(self, query: str) -> APIResponse:
        """Direct API call using local credentials (dev mode)"""
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            return APIResponse(
                success=False,
                error="PERPLEXITY_API_KEY not set. Add it to .env file.",
                provider='local'
            )

        try:
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'sonar',
                    'messages': [{'role': 'user', 'content': query}]
                },
                timeout=30
            )

            if response.ok:
                self._increment_usage('search')
                result = response.json()
                return APIResponse(
                    success=True,
                    data={
                        'answer': result['choices'][0]['message']['content'],
                        'citations': result.get('citations', [])
                    },
                    provider='perplexity-local',
                    quota_remaining=self._get_remaining_quota('search')
                )
            else:
                return APIResponse(success=False, error=response.text, provider='local')

        except Exception as e:
            logger.error(f"Search error: {e}")
            return APIResponse(success=False, error=str(e), provider='local')

    def _search_web_managed(self, query: str) -> APIResponse:
        """Route through ARCHIV-IT backend (production)"""
        endpoint = self.config['managed_apis']['search']['endpoint']

        try:
            response = requests.post(
                endpoint,
                json={'query': query},
                headers=self._get_auth_headers(),
                timeout=30
            )

            if response.ok:
                self._increment_usage('search')
                result = response.json()
                return APIResponse(
                    success=True,
                    data=result,
                    provider='archivit-managed',
                    quota_remaining=result.get('quota_remaining')
                )
            else:
                return APIResponse(success=False, error=response.json().get('error'), provider='managed')

        except Exception as e:
            logger.error(f"Managed search API error: {e}")
            return APIResponse(success=False, error=str(e), provider='managed')

    def _get_remaining_quota(self, api_name: str) -> int:
        """Get remaining daily quota for an API"""
        api_config = self.config.get('managed_apis', {}).get(api_name, {})
        quota_config = api_config.get('quota', {}).get(self.usage.tier, {})
        daily_limit = quota_config.get('requests_per_day', 0)
        return max(0, daily_limit - self.usage.requests_today)

    # =========================================================================
    # BYOK APIs (User's own credentials)
    # =========================================================================

    def get_byok_status(self) -> Dict:
        """Check which BYOK APIs are configured"""
        status = {}

        byok_config = self.config.get('byok_apis', {})

        for api_name, api_info in byok_config.items():
            if api_name.startswith('_'):
                continue

            if api_info.get('type') == 'oauth2':
                # Check for token file
                token_file = CONFIG_DIR / api_info.get('token_file', '').replace('config/', '')
                status[api_name] = {
                    'configured': token_file.exists(),
                    'type': 'oauth2',
                    'setup_url': api_info.get('setup_url')
                }

            elif api_info.get('type') == 'api_key':
                # Check for environment variable(s)
                if 'providers' in api_info:
                    # Multiple providers (like blockchain)
                    providers_status = {}
                    any_configured = False
                    for prov_name, prov_info in api_info['providers'].items():
                        env_var = prov_info.get('env_var')
                        is_set = bool(os.getenv(env_var)) if env_var else False
                        providers_status[prov_name] = is_set
                        if is_set:
                            any_configured = True

                    status[api_name] = {
                        'configured': any_configured,
                        'type': 'api_key',
                        'providers': providers_status,
                        'has_fallback': bool(api_info.get('public_fallbacks')),
                        'setup_url': api_info.get('setup_url')
                    }
                else:
                    env_vars = api_info.get('env_vars', [])
                    all_set = all(os.getenv(var) for var in env_vars)
                    status[api_name] = {
                        'configured': all_set,
                        'type': 'api_key',
                        'required_vars': env_vars,
                        'setup_url': api_info.get('setup_url')
                    }

            elif api_info.get('type') == 'app_password':
                env_vars = api_info.get('env_vars', [])
                all_set = all(os.getenv(var) for var in env_vars)
                status[api_name] = {
                    'configured': all_set,
                    'type': 'app_password',
                    'required_vars': env_vars,
                    'setup_url': api_info.get('setup_url')
                }

        return status

    def validate_byok_key(self, api_name: str, key: str, provider: str = None) -> APIResponse:
        """Validate a BYOK API key before saving"""
        validators = {
            'alchemy': self._validate_alchemy_key,
            'infura': self._validate_infura_key,
            'etherscan': self._validate_etherscan_key,
        }

        validator_key = provider or api_name
        if validator_key in validators:
            return validators[validator_key](key)

        # No validator available - assume valid
        return APIResponse(success=True, data={'validated': False, 'message': 'No validator available'})

    def _validate_alchemy_key(self, key: str) -> APIResponse:
        """Validate Alchemy API key"""
        try:
            response = requests.post(
                f'https://eth-mainnet.g.alchemy.com/v2/{key}',
                json={'jsonrpc': '2.0', 'method': 'eth_blockNumber', 'params': [], 'id': 1},
                timeout=10
            )
            if response.ok and 'result' in response.json():
                return APIResponse(success=True, data={'validated': True})
            return APIResponse(success=False, error='Invalid Alchemy API key')
        except Exception as e:
            return APIResponse(success=False, error=str(e))

    def _validate_infura_key(self, key: str) -> APIResponse:
        """Validate Infura API key"""
        try:
            response = requests.post(
                f'https://mainnet.infura.io/v3/{key}',
                json={'jsonrpc': '2.0', 'method': 'eth_blockNumber', 'params': [], 'id': 1},
                timeout=10
            )
            if response.ok and 'result' in response.json():
                return APIResponse(success=True, data={'validated': True})
            return APIResponse(success=False, error='Invalid Infura API key')
        except Exception as e:
            return APIResponse(success=False, error=str(e))

    def _validate_etherscan_key(self, key: str) -> APIResponse:
        """Validate Etherscan API key"""
        try:
            response = requests.get(
                f'https://api.etherscan.io/api?module=stats&action=ethprice&apikey={key}',
                timeout=10
            )
            data = response.json()
            if data.get('status') == '1':
                return APIResponse(success=True, data={'validated': True})
            return APIResponse(success=False, error='Invalid Etherscan API key')
        except Exception as e:
            return APIResponse(success=False, error=str(e))


# Singleton instance
_client: Optional[ArchivitAPIClient] = None

def get_api_client() -> ArchivitAPIClient:
    """Get or create API client singleton"""
    global _client
    if _client is None:
        _client = ArchivitAPIClient()
    return _client


# Convenience functions
def vision_analyze(image_path: str, prompt: str = None) -> APIResponse:
    """Analyze image using managed vision API"""
    return get_api_client().vision_analyze(image_path, prompt)

def search_web(query: str) -> APIResponse:
    """Search web using managed search API"""
    return get_api_client().search_web(query)

def get_quota_status() -> Dict:
    """Get current quota status"""
    return get_api_client().get_quota_status()

def get_byok_status() -> Dict:
    """Get BYOK API configuration status"""
    return get_api_client().get_byok_status()
