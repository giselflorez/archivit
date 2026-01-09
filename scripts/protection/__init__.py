"""
ARCHIV-IT - Code Protection Module
Hardware-bound licensing and code obfuscation
"""

from .license_manager import LicenseManager, require_valid_license

__all__ = ['LicenseManager', 'require_valid_license']
