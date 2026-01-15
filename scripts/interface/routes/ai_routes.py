"""
MOONSTONE AI Chat API Routes - LOCAL-FIRST

Uses the NORTHSTAR Masters knowledge base LOCALLY.
No external API required for most queries.

Sovereignty hierarchy:
1. Search local ARTIST_AGENTS.json (22 Masters)
2. Search local training_data.json (knowledge base)
3. Pattern match common troubleshooting
4. ONLY use external API if user explicitly consents
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# =============================================================================
# LOCAL KNOWLEDGE BASE - SOVEREIGN
# =============================================================================

def load_northstar_masters():
    """Load the 22 NORTHSTAR Masters from local JSON."""
    masters_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'agents' / 'ARTIST_AGENTS.json'

    masters = {}

    if masters_path.exists():
        try:
            with open(masters_path) as f:
                data = json.load(f)

            # Parse the actual structure - agents.feminine + agents.masculine
            agents = data.get('agents', {})
            for polarity in ['feminine', 'masculine']:
                for agent in agents.get(polarity, []):
                    master_id = agent.get('id', '').lower()
                    if master_id:
                        # Extract quotes as simple strings
                        quotes = [q.get('quote', '') for q in agent.get('verified_quotes', [])]
                        masters[master_id] = {
                            'name': agent.get('name', master_id),
                            'domain': agent.get('domain', ''),
                            'polarity': agent.get('polarity', polarity),
                            'era': agent.get('era', ''),
                            'techniques': agent.get('techniques', []),
                            'philosophies': agent.get('philosophies', []),
                            'quotes': quotes,
                            'teachings': agent.get('teaching_points', []),
                            'skill_command': agent.get('skill_command', '')
                        }

            if masters:
                return {'masters': masters}
        except Exception as e:
            print(f"Warning: Could not load ARTIST_AGENTS.json: {e}")

    # Fallback to embedded core knowledge
    return {
        "masters": {
            "tesla": {
                "name": "Nikola Tesla",
                "domain": "Energy + Frequency + Vibration",
                "teachings": ["Energy, frequency, vibration are keys to universe", "Solitude births invention"],
                "quotes": ["If you want to find the secrets of the universe, think in terms of energy, frequency and vibration."]
            },
            "fuller": {
                "name": "Buckminster Fuller",
                "domain": "Systems Thinking",
                "teachings": ["Make things obsolete through superior technology", "We are verbs not nouns"],
                "quotes": ["You never change things by fighting the existing reality. To change something, build a new model that makes the existing model obsolete."]
            },
            "jung": {
                "name": "Carl Jung",
                "domain": "Shadow Integration",
                "teachings": ["Make the unconscious conscious", "Integrate the shadow"],
                "quotes": ["Until you make the unconscious conscious, it will direct your life and you will call it fate."]
            },
            "jobs": {
                "name": "Steve Jobs",
                "domain": "Design Thinking",
                "teachings": ["Design is how it works", "Stay hungry stay foolish"],
                "quotes": ["Design is not just what it looks like and feels like. Design is how it works."]
            },
            "prince": {
                "name": "Prince",
                "domain": "Creative Sovereignty",
                "teachings": ["Own your masters", "Create from nothing"],
                "quotes": ["If you don't own your masters, your master owns you."]
            }
        }
    }


def load_knowledge_base():
    """Load the training data knowledge base."""
    kb_path = Path(__file__).parent.parent.parent.parent / 'knowledge_base' / 'training_data.json'

    if kb_path.exists():
        try:
            with open(kb_path) as f:
                return json.load(f)
        except:
            pass
    return {}


# Troubleshooting patterns - LOCAL
TROUBLESHOOTING = {
    # IPFS / Pinata
    r"ipfs|pinata|upload|pin": {
        "topic": "IPFS Upload",
        "response": """**IPFS Upload via Pinata:**

1. Ensure Pinata credentials in `.env`:
   ```
   PINATA_API_KEY=your_key
   PINATA_SECRET_KEY=your_secret
   ```

2. API endpoint: `POST /api/mint/upload-metadata`

3. Example:
   ```bash
   curl -X POST http://localhost:5001/api/mint/upload-metadata \\
     -H "Content-Type: application/json" \\
     -d '{"name":"Art","description":"...","image":"ipfs://..."}'
   ```

Files are pinned with content-addressed CIDs - immutable and sovereign."""
    },

    # Wallet scanning
    r"scan|wallet|nft|collector": {
        "topic": "Wallet Scanning",
        "response": """**Wallet Scanning:**

- Tezos: Works immediately (TzKT API is open)
- Ethereum: Requires Alchemy API key for full history

API endpoint: `POST /api/scan/wallet`

```bash
curl -X POST http://localhost:5001/api/scan/wallet \\
  -H "Content-Type: application/json" \\
  -d '{"address":"tz1... or 0x..."}'
```

For deep collector network analysis: `POST /api/scan/super`"""
    },

    # Minting
    r"mint|eth|polygon|base|erc721": {
        "topic": "NFT Minting",
        "response": """**NFT Minting Process:**

1. Upload artwork to IPFS: `POST /api/mint/upload-file`
2. Create metadata with image CID: `POST /api/mint/upload-metadata`
3. Estimate gas: `POST /api/mint/estimate-gas`
4. Mint with wallet signature: `POST /api/mint/eth`

Supported chains: Ethereum, Polygon, Base, Sepolia (testnet)

*Note: Actual minting requires wallet connection (MetaMask/WalletConnect)*"""
    },

    # Visualization
    r"visual|3d|4d|three|load|slow": {
        "topic": "4D Visualization",
        "response": """**4D Visualization:**

Three.js is loaded from IPFS (sovereign, version-locked):
- `ipfs://bafybeifgqkm4cy23uh3bj5mo2igkz2xpuxfqzhwftglwulebvohfsgd3ly`

If loading slow:
1. Check internet connection to IPFS gateway
2. Run local server: `python -m http.server 8080`
3. Particle count has been optimized (50% reduction)

The visualization uses PHI-based orbital mechanics (φ = 1.618033988749895)."""
    },

    # Server / Port
    r"server|port|5001|5000|start": {
        "topic": "Server Setup",
        "response": """**Starting the Server:**

```bash
cd scripts/interface
KMP_DUPLICATE_LIB_OK=TRUE ../../venv/bin/python visual_browser.py --port 5001
```

**Port 5000 is blocked** by macOS AirPlay - always use 5001.

Access at: http://localhost:5001"""
    },

    # API / Routes
    r"api|route|endpoint|curl": {
        "topic": "API Endpoints",
        "response": """**Available API Routes:**

**Minting:**
- `POST /api/mint/upload-metadata` - Upload NFT metadata to IPFS
- `POST /api/mint/upload-file` - Upload artwork to IPFS
- `POST /api/mint/estimate-gas` - Get gas estimate
- `GET /api/mint/balance/<address>` - Check wallet balance

**Scanning:**
- `POST /api/scan/wallet` - Scan wallet for NFTs
- `POST /api/scan/super` - Deep collector network scan
- `POST /api/scan/visualize` - Generate 4D visualization

All routes return JSON. No authentication required for reads."""
    },

    # Sovereignty
    r"sovereign|local|decentralized|own": {
        "topic": "Data Sovereignty",
        "response": """**ARCHIV-IT Sovereignty Principles:**

✓ Your data lives on YOUR device
✓ Your seed = your mathematical identity (YOU own it)
✓ Your creations belong to YOU
✓ Export anytime, any format
✓ When you delete, it's GONE

We are **SOVEREIGN-FIRST**, not decentralized-first.
External systems (blockchains, IPFS) are optional connections.

*"If you don't own your masters, your master owns you."* - Prince"""
    }
}


def search_masters(query):
    """Search NORTHSTAR Masters for relevant wisdom."""
    masters_data = load_northstar_masters()
    query_lower = query.lower()

    results = []

    masters = masters_data.get('masters', masters_data)
    for master_id, master in masters.items():
        if isinstance(master, dict):
            # Check if query relates to this master's domain
            name = master.get('name', master_id).lower()
            domain = master.get('domain', '').lower()

            if any(word in name or word in domain for word in query_lower.split()):
                quotes = master.get('quotes', [])
                teachings = master.get('teachings', [])

                results.append({
                    'master': master.get('name', master_id),
                    'domain': master.get('domain', ''),
                    'quote': quotes[0] if quotes else None,
                    'teaching': teachings[0] if teachings else None
                })

    return results


def search_troubleshooting(query):
    """Match query against troubleshooting patterns."""
    query_lower = query.lower()

    for pattern, data in TROUBLESHOOTING.items():
        if re.search(pattern, query_lower):
            return data

    return None


def generate_local_response(message, context):
    """Generate response using LOCAL knowledge only."""

    # 1. Check troubleshooting patterns first
    troubleshoot = search_troubleshooting(message)
    if troubleshoot:
        return {
            'success': True,
            'response': troubleshoot['response'],
            'source': 'local_troubleshooting',
            'topic': troubleshoot['topic']
        }

    # 2. Search NORTHSTAR Masters
    masters_results = search_masters(message)
    if masters_results:
        master = masters_results[0]
        response = f"""**From the NORTHSTAR Masters:**

**{master['master']}** - {master['domain']}

"""
        if master.get('quote'):
            response += f'*"{master["quote"]}"*\n\n'
        if master.get('teaching'):
            response += f"Teaching: {master['teaching']}"

        return {
            'success': True,
            'response': response,
            'source': 'northstar_masters',
            'master': master['master']
        }

    # 3. Default helpful response
    return {
        'success': True,
        'response': """I searched the local NORTHSTAR Masters knowledge base but didn't find a specific match for your question.

**Try asking about:**
- IPFS uploads and pinning
- Wallet scanning (Tezos/ETH)
- NFT minting process
- 4D visualization
- Server setup
- API endpoints
- Data sovereignty

Or invoke a specific Master: "What would Tesla say about..."

*This response was generated locally - no external API used.*""",
        'source': 'local_fallback'
    }


# =============================================================================
# API ROUTES
# =============================================================================

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """
    LOCAL-FIRST chat endpoint.

    Uses NORTHSTAR Masters knowledge base.
    No external API unless explicitly requested.
    """
    try:
        data = request.get_json()

        message = data.get('message', '').strip()
        context = data.get('context', 'default')
        use_external_api = data.get('use_external_api', False)

        if not message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400

        # LOCAL-FIRST: Try local knowledge base
        result = generate_local_response(message, context)

        # Only use external API if:
        # 1. User explicitly requested it
        # 2. Local response was fallback
        if use_external_api and result.get('source') == 'local_fallback':
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
            if api_key:
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system="You are Moonstone, AI assistant for ARCHIV-IT. Be concise and helpful.",
                        messages=[{"role": "user", "content": message}]
                    )

                    return jsonify({
                        'success': True,
                        'response': response.content[0].text,
                        'source': 'external_api',
                        'note': 'External API was used (with your consent)'
                    })
                except Exception as e:
                    result['api_error'] = str(e)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/masters', methods=['GET'])
def list_masters():
    """List all NORTHSTAR Masters (local knowledge)."""
    masters_data = load_northstar_masters()

    masters_list = []
    masters = masters_data.get('masters', masters_data)

    for master_id, master in masters.items():
        if isinstance(master, dict):
            masters_list.append({
                'id': master_id,
                'name': master.get('name', master_id),
                'domain': master.get('domain', '')
            })

    return jsonify({
        'success': True,
        'masters': masters_list,
        'count': len(masters_list),
        'source': 'local'
    })


@ai_bp.route('/ask/<master_id>', methods=['POST'])
def ask_master(master_id):
    """Ask a specific NORTHSTAR Master."""
    masters_data = load_northstar_masters()
    masters = masters_data.get('masters', masters_data)

    if master_id not in masters:
        return jsonify({
            'success': False,
            'error': f'Master "{master_id}" not found'
        }), 404

    master = masters[master_id]
    data = request.get_json() or {}
    question = data.get('question', 'What wisdom do you offer?')

    quotes = master.get('quotes', [])
    teachings = master.get('teachings', [])

    response = f"""**{master.get('name', master_id)}** speaks on "{question}":

Domain: {master.get('domain', 'Universal Wisdom')}

"""

    if quotes:
        response += f'*"{quotes[0]}"*\n\n'

    if teachings:
        response += "Teachings:\n"
        for t in teachings[:3]:
            response += f"• {t}\n"

    return jsonify({
        'success': True,
        'master': master.get('name', master_id),
        'response': response,
        'source': 'local_northstar'
    })


def register_ai_routes(app):
    """Register AI chat blueprint with Flask app."""
    app.register_blueprint(ai_bp)
    print("✓ MOONSTONE AI routes registered (LOCAL-FIRST)")
    print("  POST /api/ai/chat        - Local knowledge search")
    print("  GET  /api/ai/masters     - List NORTHSTAR Masters")
    print("  POST /api/ai/ask/<master> - Ask specific Master")
