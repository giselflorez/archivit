#!/usr/bin/env python3
"""
Badge Integrity System

Ensures trust indicator badges cannot be forged or tampered with.

Security measures:
1. Cryptographic signatures on all badge URLs
2. Server-side only rendering
3. Verification endpoints for third-party validation
4. Time-limited signatures that expire and regenerate
5. Rate limiting on badge requests
"""

import hmac
import hashlib
import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Secret key for signing - in production, this should be in environment variables
# This is generated once and stored securely
SECRET_KEY_FILE = Path("config/badge_secret.key")


def get_or_create_secret_key() -> bytes:
    """Get or create the secret signing key"""
    SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if SECRET_KEY_FILE.exists():
        with open(SECRET_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        # Generate a new 32-byte secret key
        key = os.urandom(32)
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(key)
        # Set restrictive permissions
        os.chmod(SECRET_KEY_FILE, 0o600)
        logger.info("Generated new badge signing key")
        return key


SECRET_KEY = get_or_create_secret_key()


class BadgeIntegrity:
    """
    Handles badge signing and verification.

    Each badge URL contains:
    - username
    - timestamp (for expiration)
    - signature (HMAC-SHA256)

    Format: /badge/{username}/{timestamp}.{signature}.svg
    """

    # Signature valid for 24 hours - badges auto-refresh
    SIGNATURE_VALIDITY_HOURS = 24

    @classmethod
    def generate_signature(cls, username: str, timestamp: str) -> str:
        """
        Generate HMAC signature for a badge

        Args:
            username: User identifier
            timestamp: ISO timestamp string

        Returns:
            Base64-encoded signature (URL-safe)
        """
        message = f"{username}:{timestamp}".encode('utf-8')
        signature = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()
        # Use URL-safe base64, truncated for cleaner URLs
        return base64.urlsafe_b64encode(signature)[:12].decode('ascii')

    @classmethod
    def verify_signature(cls, username: str, timestamp: str, signature: str) -> Tuple[bool, str]:
        """
        Verify a badge signature

        Args:
            username: User identifier
            timestamp: ISO timestamp from URL
            signature: Signature from URL

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check timestamp isn't too old
        try:
            ts = datetime.fromisoformat(timestamp)
            if datetime.now() - ts > timedelta(hours=cls.SIGNATURE_VALIDITY_HOURS):
                return False, "signature_expired"
        except ValueError:
            return False, "invalid_timestamp"

        # Verify signature
        expected = cls.generate_signature(username, timestamp)
        if not hmac.compare_digest(signature, expected):
            return False, "invalid_signature"

        return True, "valid"

    @classmethod
    def generate_badge_url(cls, username: str, base_url: str = "https://archivit.web3photo.com") -> str:
        """
        Generate a signed badge URL

        Args:
            username: User identifier
            base_url: Base URL for badge service

        Returns:
            Full signed badge URL
        """
        timestamp = datetime.now().isoformat()
        signature = cls.generate_signature(username, timestamp)

        # URL encode timestamp for safety
        ts_encoded = base64.urlsafe_b64encode(timestamp.encode()).decode('ascii')

        return f"{base_url}/badge/{username}/{ts_encoded}.{signature}.svg"

    @classmethod
    def parse_badge_url(cls, url_path: str) -> Optional[Dict]:
        """
        Parse a badge URL path and extract components

        Args:
            url_path: Path portion of badge URL (e.g., /badge/username/timestamp.signature.svg)

        Returns:
            Dict with username, timestamp, signature or None if invalid format
        """
        try:
            # Expected format: /badge/{username}/{timestamp}.{signature}.svg
            parts = url_path.strip('/').split('/')
            if len(parts) != 3 or parts[0] != 'badge':
                return None

            username = parts[1]
            file_parts = parts[2].replace('.svg', '').split('.')
            if len(file_parts) != 2:
                return None

            ts_encoded, signature = file_parts
            timestamp = base64.urlsafe_b64decode(ts_encoded).decode('utf-8')

            return {
                'username': username,
                'timestamp': timestamp,
                'signature': signature
            }
        except Exception:
            return None


class BadgeRenderer:
    """
    Server-side badge rendering.

    Generates SVG badges that cannot be forged because:
    1. Score is calculated server-side from real data
    2. SVG includes embedded verification info
    3. Style/colors come from server, not client
    """

    COLORS = {
        'critical': {'fill': '#e53e3e', 'glow': 'rgba(229, 62, 62, 0.5)'},
        'low': {'fill': '#ed8936', 'glow': 'rgba(237, 137, 54, 0.4)'},
        'moderate': {'fill': '#d4a574', 'glow': 'rgba(212, 165, 116, 0.4)'},
        'good': {'fill': '#48bb78', 'glow': 'rgba(72, 187, 120, 0.4)'},
        'excellent': {'fill': '#68d391', 'glow': 'rgba(104, 211, 145, 0.5)'}
    }

    @classmethod
    def score_to_level(cls, score: int) -> str:
        """Convert score to level"""
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

    @classmethod
    def render_badge_svg(cls, username: str, score: int, size: int = 64) -> str:
        """
        Render a badge as SVG

        Args:
            username: User identifier
            score: Trust score 0-100
            size: Badge size in pixels

        Returns:
            SVG string
        """
        level = cls.score_to_level(score)
        colors = cls.COLORS[level]
        fill_height = (score / 100) * size * 0.8  # 80% of size for fill area

        # Generate verification hash embedded in SVG
        verify_hash = BadgeIntegrity.generate_signature(username, datetime.now().isoformat())

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <linearGradient id="fill-gradient" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" style="stop-color:{colors['fill']};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{colors['fill']};stop-opacity:0.7"/>
    </linearGradient>
    <clipPath id="orb-clip">
      <circle cx="32" cy="32" r="28"/>
    </clipPath>
  </defs>

  <!-- Background orb -->
  <circle cx="32" cy="32" r="28" fill="#1a1a24" stroke="{colors['fill']}" stroke-width="2" filter="url(#glow)" style="filter: drop-shadow(0 0 4px {colors['glow']})"/>

  <!-- Liquid fill -->
  <g clip-path="url(#orb-clip)">
    <rect x="0" y="{64 - fill_height}" width="64" height="{fill_height}" fill="url(#fill-gradient)">
      <animate attributeName="y" values="{64 - fill_height};{64 - fill_height - 2};{64 - fill_height}" dur="3s" repeatCount="indefinite"/>
    </rect>
    <!-- Wave effect -->
    <ellipse cx="32" cy="{64 - fill_height}" rx="35" ry="4" fill="{colors['fill']}" opacity="0.6">
      <animate attributeName="rx" values="35;38;35" dur="2s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="{64 - fill_height};{64 - fill_height - 2};{64 - fill_height}" dur="3s" repeatCount="indefinite"/>
    </ellipse>
  </g>

  <!-- Verification watermark (hidden but present for validation) -->
  <metadata>
    <archivit:verification xmlns:archivit="https://archivit.web3photo.com/ns">
      <archivit:user>{username}</archivit:user>
      <archivit:score>{score}</archivit:score>
      <archivit:hash>{verify_hash}</archivit:hash>
      <archivit:generated>{datetime.now().isoformat()}</archivit:generated>
    </archivit:verification>
  </metadata>
</svg>'''

        return svg

    @classmethod
    def render_badge_with_label_svg(cls, username: str, score: int, label: str = None) -> str:
        """
        Render a wider badge with label

        Args:
            username: User identifier
            score: Trust score 0-100
            label: Optional label (defaults to level name)

        Returns:
            SVG string
        """
        level = cls.score_to_level(score)
        colors = cls.COLORS[level]
        label = label or level.capitalize()

        fill_height = (score / 100) * 24

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="32" viewBox="0 0 120 32">
  <defs>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#1a1a24"/>
      <stop offset="100%" style="stop-color:#12121a"/>
    </linearGradient>
    <clipPath id="orb-clip-sm">
      <circle cx="16" cy="16" r="12"/>
    </clipPath>
  </defs>

  <!-- Background -->
  <rect width="120" height="32" rx="16" fill="url(#bg-grad)" stroke="{colors['fill']}" stroke-width="1" stroke-opacity="0.5"/>

  <!-- Orb -->
  <circle cx="16" cy="16" r="12" fill="#0a0a0f" stroke="{colors['fill']}" stroke-width="1.5"/>
  <g clip-path="url(#orb-clip-sm)">
    <rect x="4" y="{28 - fill_height}" width="24" height="{fill_height}" fill="{colors['fill']}" opacity="0.9">
      <animate attributeName="y" values="{28 - fill_height};{28 - fill_height - 1};{28 - fill_height}" dur="2s" repeatCount="indefinite"/>
    </rect>
  </g>

  <!-- Label -->
  <text x="36" y="20" font-family="system-ui, sans-serif" font-size="11" font-weight="600" fill="#e8e6e3">{label}</text>

  <!-- Score -->
  <text x="108" y="20" font-family="monospace" font-size="10" fill="{colors['fill']}" text-anchor="end">{score}%</text>
</svg>'''

        return svg


def verify_badge_request(username: str, timestamp: str, signature: str) -> Dict:
    """
    API handler for badge verification requests

    Args:
        username: User from badge URL
        timestamp: Timestamp from badge URL
        signature: Signature from badge URL

    Returns:
        Verification result dict
    """
    is_valid, reason = BadgeIntegrity.verify_signature(username, timestamp, signature)

    if is_valid:
        # Get current trust score
        try:
            from trust_system import get_trust_score_for_display
            score_data = get_trust_score_for_display()
        except:
            score_data = {'trust_score': 0, 'level': 'unknown'}

        return {
            'valid': True,
            'username': username,
            'score': score_data.get('trust_score', 0),
            'level': score_data.get('level', 'unknown'),
            'verified_at': datetime.now().isoformat()
        }
    else:
        return {
            'valid': False,
            'reason': reason,
            'message': 'This badge could not be verified. It may be expired or forged.'
        }


# Rate limiting for badge requests
class RateLimiter:
    """Simple in-memory rate limiter for badge requests"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # ip -> [(timestamp, count)]

    def is_allowed(self, ip: str) -> bool:
        """Check if request from IP is allowed"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Clean old entries
        if ip in self.requests:
            self.requests[ip] = [
                (ts, count) for ts, count in self.requests[ip]
                if ts > cutoff
            ]

        # Count recent requests
        recent_count = sum(count for _, count in self.requests.get(ip, []))

        if recent_count >= self.max_requests:
            return False

        # Record this request
        if ip not in self.requests:
            self.requests[ip] = []
        self.requests[ip].append((now, 1))

        return True


# Global rate limiter instance
badge_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
