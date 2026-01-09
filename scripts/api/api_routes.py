#!/usr/bin/env python3
"""
API Routes - Expose API status, configuration, and management endpoints
"""

import os
import json
import logging
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
from dotenv import load_dotenv, set_key

from .api_client import get_api_client, get_quota_status, get_byok_status

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Paths
ENV_PATH = Path(__file__).parent.parent.parent / '.env'
CONFIG_DIR = Path(__file__).parent.parent.parent / 'config'


@api_bp.route('/status')
def api_status():
    """Get overall API status and configuration"""
    client = get_api_client()

    return jsonify({
        'environment': client.environment,
        'dev_mode': client.dev_mode,
        'authenticated': client.is_authenticated(),
        'quota': get_quota_status(),
        'byok': get_byok_status()
    })


@api_bp.route('/quota')
def quota_status():
    """Get current quota usage"""
    return jsonify(get_quota_status())


@api_bp.route('/byok/status')
def byok_status():
    """Get BYOK API configuration status"""
    return jsonify(get_byok_status())


@api_bp.route('/byok/validate', methods=['POST'])
def validate_byok_key():
    """Validate a BYOK API key before saving"""
    data = request.json
    api_name = data.get('api_name')
    key = data.get('key')
    provider = data.get('provider')

    if not api_name or not key:
        return jsonify({'error': 'api_name and key required'}), 400

    client = get_api_client()
    result = client.validate_byok_key(api_name, key, provider)

    return jsonify({
        'success': result.success,
        'error': result.error,
        'data': result.data
    })


@api_bp.route('/byok/save', methods=['POST'])
def save_byok_key():
    """Save a BYOK API key to .env file"""
    data = request.json
    env_var = data.get('env_var')
    value = data.get('value')

    if not env_var or value is None:
        return jsonify({'error': 'env_var and value required'}), 400

    # Security: Only allow known env vars
    allowed_vars = [
        'ALCHEMY_API_KEY', 'INFURA_API_KEY', 'ETHERSCAN_API_KEY',
        'GMAIL_EMAIL', 'GMAIL_APP_PASSWORD', 'ANTHROPIC_API_KEY',
        'PERPLEXITY_API_KEY', 'FLASK_SECRET_KEY'
    ]

    if env_var not in allowed_vars:
        return jsonify({'error': f'Unknown environment variable: {env_var}'}), 400

    try:
        # Ensure .env exists
        if not ENV_PATH.exists():
            ENV_PATH.touch()

        # Update .env file
        set_key(str(ENV_PATH), env_var, value)

        # Reload environment
        load_dotenv(ENV_PATH, override=True)

        logger.info(f"Saved {env_var} to .env")

        return jsonify({
            'success': True,
            'env_var': env_var,
            'message': f'{env_var} saved successfully'
        })

    except Exception as e:
        logger.error(f"Failed to save {env_var}: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/byok/remove', methods=['POST'])
def remove_byok_key():
    """Remove a BYOK API key from .env file"""
    data = request.json
    env_var = data.get('env_var')

    if not env_var:
        return jsonify({'error': 'env_var required'}), 400

    try:
        # Read current .env
        if ENV_PATH.exists():
            with open(ENV_PATH) as f:
                lines = f.readlines()

            # Filter out the variable
            new_lines = [line for line in lines if not line.startswith(f'{env_var}=')]

            with open(ENV_PATH, 'w') as f:
                f.writelines(new_lines)

            # Clear from environment
            if env_var in os.environ:
                del os.environ[env_var]

            logger.info(f"Removed {env_var} from .env")

        return jsonify({
            'success': True,
            'env_var': env_var,
            'message': f'{env_var} removed successfully'
        })

    except Exception as e:
        logger.error(f"Failed to remove {env_var}: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/test/vision', methods=['POST'])
def test_vision():
    """Test vision API with a sample image"""
    from .api_client import vision_analyze

    data = request.json
    image_path = data.get('image_path')

    if not image_path or not Path(image_path).exists():
        return jsonify({'error': 'Valid image_path required'}), 400

    result = vision_analyze(image_path)

    return jsonify({
        'success': result.success,
        'data': result.data,
        'error': result.error,
        'provider': result.provider,
        'quota_remaining': result.quota_remaining
    })


@api_bp.route('/test/search', methods=['POST'])
def test_search():
    """Test search API with a query"""
    from .api_client import search_web

    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({'error': 'query required'}), 400

    result = search_web(query)

    return jsonify({
        'success': result.success,
        'data': result.data,
        'error': result.error,
        'provider': result.provider,
        'quota_remaining': result.quota_remaining
    })


def register_api_routes(app):
    """Register API blueprint with Flask app"""
    app.register_blueprint(api_bp)

    # Also add a simple UI route for API configuration
    @app.route('/settings/api')
    def api_settings():
        """API configuration page"""
        client = get_api_client()
        return render_template('api_settings.html',
            environment=client.environment,
            dev_mode=client.dev_mode,
            authenticated=client.is_authenticated(),
            quota=get_quota_status(),
            byok=get_byok_status()
        )
