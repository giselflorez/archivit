"""
NFT-8 Minting API Routes

Sovereign minting infrastructure for ARCHIV-IT.
Supports ETH, Polygon, Base, and Tezos minting with IPFS metadata.

Routes:
    POST /api/mint/upload-metadata  - Upload metadata to IPFS via Pinata
    POST /api/mint/eth              - Mint NFT on Ethereum/EVM chains
    POST /api/mint/estimate-gas     - Get gas estimate for minting
    GET  /api/mint/balance/<address> - Get wallet balance
    POST /api/scan/wallet           - Scan wallet for NFTs
    POST /api/scan/super            - Run NFT super scan (collector network)
    GET  /api/scan/status/<job_id>  - Get scan job status
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g

# Create blueprint
minting_bp = Blueprint('minting', __name__, url_prefix='/api/mint')
scanning_bp = Blueprint('scanning', __name__, url_prefix='/api/scan')

# Job storage for async operations
SCAN_JOBS: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# AUTHENTICATION & VALIDATION
# =============================================================================

def require_api_key(f):
    """Decorator to require API key for sensitive operations."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        # In development, allow requests without key
        if current_app.debug:
            return f(*args, **kwargs)

        # In production, validate key
        expected_key = os.getenv('ARCHIVIT_API_KEY', '')
        if not expected_key or api_key != expected_key:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key'
            }), 401

        return f(*args, **kwargs)
    return decorated


def validate_eth_address(address: str) -> bool:
    """Validate Ethereum address format."""
    if not address:
        return False
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


def validate_tezos_address(address: str) -> bool:
    """Validate Tezos address format."""
    if not address:
        return False
    return address.startswith(('tz1', 'tz2', 'tz3', 'KT1'))


# =============================================================================
# IPFS METADATA UPLOAD
# =============================================================================

@minting_bp.route('/upload-metadata', methods=['POST'])
def upload_metadata():
    """
    Upload NFT metadata to IPFS via Pinata.

    Request JSON:
        {
            "name": "Artwork Title",
            "description": "Description of the artwork",
            "image": "ipfs://Qm... or https://...",
            "attributes": [
                {"trait_type": "Artist", "value": "Name"},
                {"trait_type": "Year", "value": "2026"}
            ],
            "external_url": "https://...",
            "animation_url": "ipfs://... (optional)"
        }

    Returns:
        {
            "success": true,
            "cid": "ipfs://Qm...",
            "gateway_url": "https://gateway.pinata.cloud/ipfs/..."
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No metadata provided'
            }), 400

        # Validate required fields
        required = ['name', 'description', 'image']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400

        # Get Pinata credentials
        api_key = os.getenv('PINATA_API_KEY', '')
        secret_key = os.getenv('PINATA_SECRET_KEY', '')

        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'IPFS (Pinata) credentials not configured'
            }), 500

        # Build ERC-721 compliant metadata
        metadata = {
            'name': data['name'],
            'description': data['description'],
            'image': data['image'],
            'attributes': data.get('attributes', []),
        }

        # Optional fields
        if 'external_url' in data:
            metadata['external_url'] = data['external_url']
        if 'animation_url' in data:
            metadata['animation_url'] = data['animation_url']
        if 'background_color' in data:
            metadata['background_color'] = data['background_color']

        # Add ARCHIV-IT provenance
        metadata['properties'] = {
            'created_by': 'ARCHIV-IT',
            'created_at': datetime.utcnow().isoformat(),
            'sovereignty': 'user-owned'
        }

        # Pin to IPFS
        import requests

        url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        headers = {
            'Content-Type': 'application/json',
            'pinata_api_key': api_key,
            'pinata_secret_api_key': secret_key
        }

        payload = {
            'pinataContent': metadata,
            'pinataMetadata': {
                'name': f"nft-metadata-{data['name'][:30]}",
                'keyvalues': {
                    'project': 'ARCHIV-IT',
                    'type': 'nft-metadata'
                }
            },
            'pinataOptions': {
                'cidVersion': 1
            }
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        cid = result['IpfsHash']

        return jsonify({
            'success': True,
            'cid': f'ipfs://{cid}',
            'gateway_url': f'https://gateway.pinata.cloud/ipfs/{cid}',
            'cloudflare_url': f'https://cloudflare-ipfs.com/ipfs/{cid}',
            'metadata': metadata
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'IPFS upload failed: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minting_bp.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Upload a file (image/video/audio) to IPFS via Pinata.

    Request: multipart/form-data with 'file' field

    Returns:
        {
            "success": true,
            "cid": "ipfs://Qm...",
            "gateway_url": "https://..."
        }
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Get Pinata credentials
        api_key = os.getenv('PINATA_API_KEY', '')
        secret_key = os.getenv('PINATA_SECRET_KEY', '')

        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'IPFS (Pinata) credentials not configured'
            }), 500

        import requests

        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {
            'pinata_api_key': api_key,
            'pinata_secret_api_key': secret_key
        }

        # Read file content
        file_content = file.read()

        files = {
            'file': (file.filename, file_content)
        }

        metadata = json.dumps({
            'name': f'archivit-{file.filename}',
            'keyvalues': {
                'project': 'ARCHIV-IT',
                'type': 'nft-asset'
            }
        })

        data = {
            'pinataMetadata': metadata,
            'pinataOptions': json.dumps({'cidVersion': 1})
        }

        response = requests.post(url, files=files, data=data, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()

        cid = result['IpfsHash']

        return jsonify({
            'success': True,
            'cid': f'ipfs://{cid}',
            'gateway_url': f'https://gateway.pinata.cloud/ipfs/{cid}',
            'cloudflare_url': f'https://cloudflare-ipfs.com/ipfs/{cid}',
            'filename': file.filename,
            'size': len(file_content)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# ETH/EVM MINTING
# =============================================================================

@minting_bp.route('/estimate-gas', methods=['POST'])
def estimate_gas():
    """
    Estimate gas for minting operation.

    Request JSON:
        {
            "chain": "ethereum|polygon|base|sepolia",
            "contract_address": "0x...",
            "to_address": "0x...",
            "token_uri": "ipfs://..."
        }

    Returns:
        {
            "success": true,
            "gas_estimate": 150000,
            "gas_price_gwei": 25,
            "total_cost_eth": "0.00375",
            "total_cost_usd": 12.50  (approximate)
        }
    """
    try:
        data = request.get_json()

        chain = data.get('chain', 'ethereum')

        # Import minter
        from scripts.minting.eth_nft_minter import ETHNFTMinter

        minter = ETHNFTMinter(chain)
        gas_info = minter.get_gas_price()

        # Estimate gas for mint (typical ERC-721 mint is ~150k gas)
        estimated_gas = 150000

        gas_price_wei = gas_info.get('gas_price', 0)
        gas_price_gwei = gas_price_wei / 1e9

        total_cost_wei = estimated_gas * gas_price_wei
        total_cost_eth = total_cost_wei / 1e18

        return jsonify({
            'success': True,
            'chain': chain,
            'gas_estimate': estimated_gas,
            'gas_price_gwei': round(gas_price_gwei, 2),
            'total_cost_eth': f'{total_cost_eth:.6f}',
            'gas_info': gas_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minting_bp.route('/balance/<address>', methods=['GET'])
def get_balance(address: str):
    """
    Get wallet balance on specified chain.

    Query params:
        chain: ethereum|polygon|base|sepolia (default: ethereum)

    Returns:
        {
            "success": true,
            "address": "0x...",
            "balance_wei": "1000000000000000000",
            "balance_eth": "1.0",
            "chain": "ethereum"
        }
    """
    try:
        if not validate_eth_address(address):
            return jsonify({
                'success': False,
                'error': 'Invalid Ethereum address'
            }), 400

        chain = request.args.get('chain', 'ethereum')

        from scripts.minting.eth_nft_minter import ETHNFTMinter

        minter = ETHNFTMinter(chain)
        balance = minter.get_balance(address)

        return jsonify({
            'success': True,
            'address': address,
            'balance_wei': str(balance.get('balance_wei', 0)),
            'balance_eth': balance.get('balance_eth', '0'),
            'chain': chain
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minting_bp.route('/eth', methods=['POST'])
@require_api_key
def mint_eth():
    """
    Mint NFT on Ethereum/EVM chain.

    Request JSON:
        {
            "chain": "ethereum|polygon|base|sepolia",
            "contract_address": "0x...",
            "private_key": "0x...",  (or use wallet connection)
            "to_address": "0x...",
            "token_uri": "ipfs://...",
            "token_id": 1  (optional, auto-increment if not specified)
        }

    Returns:
        {
            "success": true,
            "transaction_hash": "0x...",
            "token_id": 1,
            "explorer_url": "https://etherscan.io/tx/..."
        }

    WARNING: This endpoint requires private key.
    In production, use wallet connection (WalletConnect/MetaMask).
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['chain', 'contract_address', 'to_address', 'token_uri']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400

        # Validate addresses
        if not validate_eth_address(data['contract_address']):
            return jsonify({
                'success': False,
                'error': 'Invalid contract address'
            }), 400

        if not validate_eth_address(data['to_address']):
            return jsonify({
                'success': False,
                'error': 'Invalid recipient address'
            }), 400

        # For now, return preparation data
        # Actual minting requires wallet signature
        return jsonify({
            'success': True,
            'status': 'prepared',
            'message': 'Mint transaction prepared. Sign with your wallet to complete.',
            'transaction': {
                'chain': data['chain'],
                'contract': data['contract_address'],
                'to': data['to_address'],
                'token_uri': data['token_uri'],
                'method': 'mint(address,string)'
            },
            'note': 'Use WalletConnect or inject Web3 provider to sign transaction'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# WALLET SCANNING
# =============================================================================

@scanning_bp.route('/wallet', methods=['POST'])
def scan_wallet():
    """
    Scan a wallet for NFTs across chains.

    Request JSON:
        {
            "address": "0x... or tz1...",
            "chains": ["ethereum", "polygon", "tezos"]  (optional, default: auto-detect)
        }

    Returns:
        {
            "success": true,
            "address": "0x...",
            "nfts": [...],
            "total_count": 42
        }
    """
    try:
        data = request.get_json()
        address = data.get('address', '')

        if not address:
            return jsonify({
                'success': False,
                'error': 'No address provided'
            }), 400

        # Detect chain from address format
        if address.startswith('0x'):
            chain_type = 'evm'
        elif address.startswith(('tz1', 'tz2', 'tz3', 'KT1')):
            chain_type = 'tezos'
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported address format'
            }), 400

        # For Tezos, use TzKT API (works without auth)
        if chain_type == 'tezos':
            import requests

            # Get tokens
            url = f"https://api.tzkt.io/v1/tokens/balances?account={address}&limit=100"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            tokens = response.json()

            nfts = []
            for token in tokens:
                if token.get('token', {}).get('standard') == 'fa2':
                    nfts.append({
                        'contract': token['token']['contract']['address'],
                        'token_id': token['token']['tokenId'],
                        'balance': token['balance'],
                        'name': token['token'].get('metadata', {}).get('name', 'Unknown'),
                        'image': token['token'].get('metadata', {}).get('thumbnailUri', '')
                    })

            return jsonify({
                'success': True,
                'address': address,
                'chain': 'tezos',
                'nfts': nfts,
                'total_count': len(nfts)
            })

        # For EVM, use scanner module
        else:
            from scripts.minting.batch_wallet_scanner import BatchWalletScanner

            scanner = BatchWalletScanner()
            results = scanner.scan_wallet(address)

            return jsonify({
                'success': True,
                'address': address,
                'chain': 'ethereum',
                'nfts': results.get('nfts', []),
                'total_count': results.get('total_count', 0)
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scanning_bp.route('/super', methods=['POST'])
def super_scan():
    """
    Run NFT Super Scan - deep collector network analysis.

    Request JSON:
        {
            "address": "0x... or tz1...",
            "depth": 2,  (optional, default: 2)
            "generate_visualization": true  (optional)
        }

    Returns:
        {
            "success": true,
            "job_id": "abc123",
            "status": "processing",
            "message": "Super scan started. Poll /api/scan/status/<job_id> for results."
        }
    """
    try:
        data = request.get_json()
        address = data.get('address', '')

        if not address:
            return jsonify({
                'success': False,
                'error': 'No address provided'
            }), 400

        # Generate job ID
        job_id = secrets.token_hex(8)

        # Store job
        SCAN_JOBS[job_id] = {
            'status': 'processing',
            'address': address,
            'started_at': datetime.utcnow().isoformat(),
            'progress': 0,
            'results': None
        }

        # For now, run synchronously (in production, use Celery/Redis)
        # Detect chain
        if address.startswith(('tz1', 'tz2', 'tz3')):
            from scripts.minting.nft_super_scan import NFTSuperScanner

            scanner = NFTSuperScanner()
            results = scanner.scan_tezos_artist(address)

            SCAN_JOBS[job_id]['status'] = 'completed'
            SCAN_JOBS[job_id]['progress'] = 100
            SCAN_JOBS[job_id]['results'] = results

            return jsonify({
                'success': True,
                'job_id': job_id,
                'status': 'completed',
                'results': results
            })
        else:
            # EVM scan (requires API key for full results)
            SCAN_JOBS[job_id]['status'] = 'completed'
            SCAN_JOBS[job_id]['results'] = {
                'message': 'EVM super scan requires Alchemy API key',
                'address': address
            }

            return jsonify({
                'success': True,
                'job_id': job_id,
                'status': 'completed',
                'results': SCAN_JOBS[job_id]['results']
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scanning_bp.route('/status/<job_id>', methods=['GET'])
def scan_status(job_id: str):
    """Get status of a scan job."""
    if job_id not in SCAN_JOBS:
        return jsonify({
            'success': False,
            'error': 'Job not found'
        }), 404

    job = SCAN_JOBS[job_id]

    return jsonify({
        'success': True,
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'started_at': job['started_at'],
        'results': job['results'] if job['status'] == 'completed' else None
    })


# =============================================================================
# VISUALIZATION GENERATION
# =============================================================================

@scanning_bp.route('/visualize', methods=['POST'])
def generate_visualization():
    """
    Generate 4D collector network visualization from scan results.

    Request JSON:
        {
            "job_id": "abc123",  (from super scan)
            or
            "data": { ... scan results ... }
        }

    Returns:
        {
            "success": true,
            "html_url": "/visualizations/network_abc123.html",
            "cid": "ipfs://..." (if pinned)
        }
    """
    try:
        data = request.get_json()

        # Get scan results
        job_id = data.get('job_id')
        scan_data = data.get('data')

        if job_id and job_id in SCAN_JOBS:
            scan_data = SCAN_JOBS[job_id].get('results')

        if not scan_data:
            return jsonify({
                'success': False,
                'error': 'No scan data provided'
            }), 400

        # Generate visualization
        from scripts.minting.nft_connections_visualizer import generate_connections_html

        html = generate_connections_html(
            scan_data,
            title=f"Collector Network - {scan_data.get('artist', 'Unknown')}"
        )

        # Save to file
        viz_id = job_id or secrets.token_hex(8)
        viz_path = Path(__file__).parent.parent.parent.parent / 'public' / f'network_{viz_id}.html'
        viz_path.parent.mkdir(parents=True, exist_ok=True)

        with open(viz_path, 'w') as f:
            f.write(html)

        return jsonify({
            'success': True,
            'visualization_id': viz_id,
            'html_url': f'/network_{viz_id}.html',
            'file_path': str(viz_path)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# REGISTER BLUEPRINTS
# =============================================================================

def register_minting_routes(app):
    """Register minting blueprints with Flask app."""
    app.register_blueprint(minting_bp)
    app.register_blueprint(scanning_bp)
    print("✓ Minting API routes registered")
    print("  POST /api/mint/upload-metadata")
    print("  POST /api/mint/upload-file")
    print("  POST /api/mint/estimate-gas")
    print("  GET  /api/mint/balance/<address>")
    print("  POST /api/mint/eth")
    print("  POST /api/scan/wallet")
    print("  POST /api/scan/super")
    print("  GET  /api/scan/status/<job_id>")
    print("  POST /api/scan/visualize")
