"""
ARCHIV-IT API Routes

Modular route blueprints for the visual browser.
"""

from .minting_routes import minting_bp, scanning_bp, register_minting_routes
from .ai_routes import ai_bp, register_ai_routes

__all__ = [
    'minting_bp',
    'scanning_bp',
    'register_minting_routes',
    'ai_bp',
    'register_ai_routes'
]
