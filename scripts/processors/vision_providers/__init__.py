#!/usr/bin/env python3
"""
Vision Providers Module
Factory for creating vision analysis providers
"""

import logging
from typing import Optional, Dict
from pathlib import Path
import json

from .base import VisionProvider, VisionProviderNotAvailableError

logger = logging.getLogger(__name__)


def load_config() -> Dict:
    """Load visual translator configuration from settings.json"""
    config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'settings.json'

    if config_path.exists():
        with open(config_path, 'r') as f:
            settings = json.load(f)
            return settings.get('visual_translator', {})

    # Return default configuration
    return {
        'enabled': True,
        'default_provider': 'auto',
        'providers': {
            'local': {
                'enabled': False,
                'priority': 1,
                'default_model': 'moondream-2b'
            },
            'claude': {
                'enabled': True,
                'priority': 2,
                'default_model': 'claude-3-5-haiku-20241022'
            }
        }
    }


def get_vision_provider(
    provider_name: str = 'auto',
    model_name: str = 'auto',
    config: Optional[Dict] = None
) -> VisionProvider:
    """
    Factory for vision providers

    Args:
        provider_name: 'claude', 'local', 'auto' (default: 'auto')
        model_name: Specific model or 'auto' (default: 'auto')
        config: Override settings (optional)

    Returns:
        Configured VisionProvider instance

    Raises:
        VisionProviderNotAvailableError: If no providers are available

    Auto mode priority:
    1. Local (if available and enabled in config)
    2. Claude (fallback if API key present)
    3. Raise error if neither available
    """
    # Load configuration
    if config is None:
        config = load_config()

    providers_config = config.get('providers', {})

    # Auto mode: try providers by priority
    if provider_name == 'auto':
        # Sort providers by priority
        providers_by_priority = sorted(
            providers_config.items(),
            key=lambda x: x[1].get('priority', 999)
        )

        for prov_name, prov_config in providers_by_priority:
            if not prov_config.get('enabled', False):
                continue

            try:
                provider = _create_provider(prov_name, prov_config, model_name)
                if provider and provider.is_available():
                    logger.info(f"Using {prov_name} provider (auto mode)")
                    return provider
            except Exception as e:
                logger.warning(f"Provider {prov_name} not available: {e}")
                continue

        raise VisionProviderNotAvailableError(
            "No vision providers available. Enable local models or set ANTHROPIC_API_KEY."
        )

    # Specific provider requested
    prov_config = providers_config.get(provider_name)
    if not prov_config:
        raise VisionProviderNotAvailableError(
            f"Provider '{provider_name}' not found in configuration"
        )

    if not prov_config.get('enabled', False):
        raise VisionProviderNotAvailableError(
            f"Provider '{provider_name}' is disabled in configuration"
        )

    provider = _create_provider(provider_name, prov_config, model_name)

    if not provider or not provider.is_available():
        raise VisionProviderNotAvailableError(
            f"Provider '{provider_name}' is not available"
        )

    return provider


def _create_provider(
    provider_name: str,
    provider_config: Dict,
    model_name: str = 'auto'
) -> Optional[VisionProvider]:
    """
    Create a specific provider instance

    Args:
        provider_name: Provider name ('claude', 'local')
        provider_config: Provider configuration dict
        model_name: Model name or 'auto'

    Returns:
        VisionProvider instance or None if creation fails
    """
    # Determine model to use
    if model_name == 'auto':
        model_name = provider_config.get('default_model', '')

    try:
        if provider_name == 'claude':
            from .claude_provider import ClaudeProvider
            return ClaudeProvider(model=model_name, config=provider_config)

        elif provider_name == 'local':
            from .local_provider import LocalProvider
            return LocalProvider(model=model_name, config=provider_config)

        else:
            logger.error(f"Unknown provider: {provider_name}")
            return None

    except ImportError as e:
        logger.error(f"Failed to import provider {provider_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create provider {provider_name}: {e}")
        return None


# Convenience function for backward compatibility
def analyze_image(image_path: Path, provider: str = 'auto', prompt: Optional[str] = None) -> Dict:
    """
    Analyze an image using the specified provider

    Args:
        image_path: Path to image file
        provider: Provider name or 'auto'
        prompt: Optional custom prompt

    Returns:
        Analysis results dict
    """
    vision_provider = get_vision_provider(provider)
    return vision_provider.analyze_image(image_path, prompt)


__all__ = [
    'VisionProvider',
    'get_vision_provider',
    'analyze_image',
    'load_config'
]
