"""
ARCHIV-IT API Module

Provides unified API client for hybrid managed/BYOK API access.
"""

from .api_client import (
    ArchivitAPIClient,
    APIResponse,
    get_api_client,
    vision_analyze,
    search_web,
    get_quota_status,
    get_byok_status
)

__all__ = [
    'ArchivitAPIClient',
    'APIResponse',
    'get_api_client',
    'vision_analyze',
    'search_web',
    'get_quota_status',
    'get_byok_status'
]
