#!/usr/bin/env python3
"""
Visual Browser - Web interface for exploring knowledge base with images
"""
import os
import sys
from pathlib import Path

# Prevent multiprocessing issues on macOS - MUST be set before any other imports
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

# Suppress multiprocessing warnings
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='multiprocessing.resource_tracker')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for
import json
import re
import hashlib
import yaml
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Whisper for local transcription
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: Whisper not available. Transcription features disabled.")

# Selenium imports for JavaScript-rendered pages
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. JavaScript-rendered pages may not scrape correctly.")

# Import search functionality
from processors.embeddings_generator import load_index

# Import visual translator
try:
    from processors.visual_translator import analyze_image, load_cached_analysis
    VISUAL_TRANSLATOR_AVAILABLE = True
except ImportError:
    VISUAL_TRANSLATOR_AVAILABLE = False
    print("Warning: Visual translator not available")

# Import semantic network builder
from interface.semantic_network_builder import (
    build_semantic_network,
    get_mints_by_address,
    get_mints_by_network,
    get_all_blockchain_addresses,
    classify_document_cognitive_type,
    extract_blockchain_metadata,
    extract_domain_from_url
)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Set secret key for sessions - SECURITY: Generate random key if not provided
import secrets as _secrets
_flask_secret = os.getenv('FLASK_SECRET_KEY')
if not _flask_secret:
    # Generate a secure random key for this session
    # WARNING: This will invalidate sessions on restart - set FLASK_SECRET_KEY in .env for persistence
    _flask_secret = _secrets.token_hex(32)
    print("WARNING: FLASK_SECRET_KEY not set - using random key (sessions will not persist across restarts)")
app.secret_key = _flask_secret

# Import user configuration database
from interface.user_config_db import UserConfigDB
from interface.setup_routes import register_setup_routes

# Register setup routes
register_setup_routes(app)

# Import and register API routes
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from api.api_routes import register_api_routes
    register_api_routes(app)
except ImportError as e:
    print(f"Warning: Could not load API routes: {e}")

# Import and register Contribution routes (User Micro TX Protocol)
try:
    from contributions.contribution_routes import register_contribution_routes
    register_contribution_routes(app)
except ImportError as e:
    print(f"Warning: Could not load contribution routes: {e}")

# Import and register NFT-8 Minting routes
try:
    from routes.minting_routes import register_minting_routes
    register_minting_routes(app)
except ImportError as e:
    print(f"Warning: Could not load minting routes: {e}")

# Import and register MOONSTONE AI routes
try:
    from routes.ai_routes import register_ai_routes
    register_ai_routes(app)
except ImportError as e:
    print(f"Warning: Could not load AI routes: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# SECURITY: URL Validation and Content Security Policy
# Protects against SSRF, XSS, and malicious redirects
# ═══════════════════════════════════════════════════════════════════════════
import ipaddress
import socket

def is_safe_url(url):
    """
    Validate URL to prevent SSRF attacks.
    Returns (is_safe, error_message)
    """
    if not url:
        return False, "URL is empty"

    try:
        parsed = urlparse(url)

        # Only allow http and https schemes
        if parsed.scheme not in ('http', 'https'):
            return False, f"Invalid scheme: {parsed.scheme}. Only http/https allowed."

        # Must have a hostname
        if not parsed.netloc:
            return False, "URL must have a hostname"

        hostname = parsed.hostname
        if not hostname:
            return False, "Could not parse hostname"

        # Block private/internal IP ranges
        try:
            # Try to resolve hostname to IP
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)

            # Block private, loopback, link-local, and reserved addresses
            if ip_obj.is_private:
                return False, "Private IP addresses are not allowed"
            if ip_obj.is_loopback:
                return False, "Loopback addresses are not allowed"
            if ip_obj.is_link_local:
                return False, "Link-local addresses are not allowed"
            if ip_obj.is_reserved:
                return False, "Reserved addresses are not allowed"

            # Block cloud metadata endpoints
            if ip == '169.254.169.254':
                return False, "Cloud metadata endpoint blocked"

        except socket.gaierror:
            # Hostname resolution failed - could be valid external host
            pass
        except ValueError:
            # Not a valid IP - that's fine for hostnames
            pass

        # Block common internal hostnames
        blocked_hosts = [
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            'metadata.google.internal', 'metadata.google.com',
            '169.254.169.254', 'metadata'
        ]
        if hostname.lower() in blocked_hosts:
            return False, f"Blocked hostname: {hostname}"

        return True, None

    except Exception as e:
        return False, f"URL parsing error: {str(e)}"

# ============================================================================
# SECURITY: Global Rate Limiting
# Prevents abuse and DoS attacks on API endpoints
# ============================================================================

from datetime import timedelta
from collections import defaultdict

class GlobalRateLimiter:
    """
    Global rate limiter for all API endpoints.
    Tracks requests per IP and returns 429 when limit exceeded.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # ip -> [timestamps]
        self._last_cleanup = datetime.now()

    def _cleanup_old_entries(self):
        """Periodically clean up old entries to prevent memory bloat"""
        now = datetime.now()
        # Only cleanup every minute
        if (now - self._last_cleanup).seconds < 60:
            return

        cutoff = now - timedelta(seconds=self.window_seconds)
        ips_to_remove = []

        for ip, timestamps in self.requests.items():
            self.requests[ip] = [ts for ts in timestamps if ts > cutoff]
            if not self.requests[ip]:
                ips_to_remove.append(ip)

        for ip in ips_to_remove:
            del self.requests[ip]

        self._last_cleanup = now

    def is_allowed(self, ip: str) -> bool:
        """Check if request from IP is allowed"""
        self._cleanup_old_entries()

        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Filter to recent requests only
        self.requests[ip] = [ts for ts in self.requests[ip] if ts > cutoff]

        if len(self.requests[ip]) >= self.max_requests:
            return False

        self.requests[ip].append(now)
        return True

# Global rate limiter: 100 requests per minute per IP
global_rate_limiter = GlobalRateLimiter(max_requests=100, window_seconds=60)

@app.before_request
def check_rate_limit():
    """
    SECURITY: Apply rate limiting to all API endpoints.
    Exempt static files and certain routes for usability.
    """
    # Exempt static files
    if request.path.startswith('/static/') or request.path.startswith('/media/'):
        return None

    # Exempt favicon
    if request.path == '/favicon.ico':
        return None

    # Exempt local AI and moonstone (local-first, no external API)
    if request.path.startswith('/moonstone') or request.path.startswith('/api/ai/'):
        return None

    client_ip = request.remote_addr

    if not global_rate_limiter.is_allowed(client_ip):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please wait before trying again.',
            'retry_after': 60
        }), 429

    return None

# ============================================================================
# SECURITY: CSRF Protection for POST/PUT/DELETE requests
# ============================================================================

from flask import session

def generate_csrf_token():
    """Generate a CSRF token and store in session"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = _secrets.token_hex(32)
    return session['_csrf_token']

# Make CSRF token available to all templates
app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def check_csrf_token():
    """
    SECURITY: Validate CSRF token for state-changing requests.
    Requires X-CSRF-Token header or _csrf_token form field.
    """
    # Only check POST, PUT, DELETE, PATCH methods
    if request.method not in ('POST', 'PUT', 'DELETE', 'PATCH'):
        return None

    # Exempt certain API routes that use other auth mechanisms
    exempt_paths = [
        '/api/badge/verify',  # Uses signature verification
        '/setup/scan-status',  # Read-only status polling
        '/login',  # Entry point before session exists
        '/api/agent/init',  # Agent initialization - read-only context
    ]

    for exempt in exempt_paths:
        if request.path.startswith(exempt):
            return None

    # Check if this is a JSON API request (CORS preflight handles CSRF for APIs)
    if request.is_json and request.headers.get('Content-Type', '').startswith('application/json'):
        # For JSON APIs, require Origin header to match host (SameSite defense)
        origin = request.headers.get('Origin')
        if origin:
            host = request.headers.get('Host', '')
            if not (origin.endswith(host) or origin.endswith('localhost:5001')):
                return jsonify({'error': 'Invalid origin'}), 403
        return None

    # For form submissions, check CSRF token
    token = request.headers.get('X-CSRF-Token') or request.form.get('_csrf_token')
    session_token = session.get('_csrf_token')

    if not token or not session_token or token != session_token:
        return jsonify({
            'error': 'CSRF validation failed',
            'message': 'Missing or invalid CSRF token'
        }), 403

    return None

# ============================================================================
# SECURITY: Simple Site Password Protection
# Set SITE_PASSWORD in .env to enable. Leave empty for no password.
# ============================================================================

SITE_PASSWORD = os.getenv('SITE_PASSWORD', '')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Simple password login page"""
    if not SITE_PASSWORD:
        return redirect('/')

    error = None
    if request.method == 'POST':
        entered_password = request.form.get('password', '')
        if entered_password == SITE_PASSWORD:
            session['site_authenticated'] = True
            return redirect('/')
        else:
            error = 'Incorrect password'

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ARCHIV-IT - Login</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background: #0a0a0f;
                color: #e8e6e3;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .login-box {{
                background: #12121a;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
                padding: 3rem;
                max-width: 400px;
                width: 90%;
                text-align: center;
            }}
            h1 {{
                color: #d4a574;
                font-size: 1.8rem;
                margin-bottom: 0.5rem;
            }}
            p {{
                color: rgba(232, 230, 227, 0.6);
                font-size: 0.85rem;
                margin-bottom: 2rem;
            }}
            input {{
                width: 100%;
                padding: 1rem;
                background: #1a1a24;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                color: #e8e6e3;
                font-size: 1rem;
                margin-bottom: 1rem;
            }}
            input:focus {{
                outline: none;
                border-color: #d4a574;
            }}
            button {{
                width: 100%;
                padding: 1rem;
                background: #d4a574;
                border: none;
                border-radius: 6px;
                color: #0a0a0f;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
            }}
            button:hover {{
                background: #e8b88a;
            }}
            .error {{
                color: #ef4444;
                font-size: 0.85rem;
                margin-bottom: 1rem;
            }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>ARCHIV-IT</h1>
            <p>Beta Tester Access</p>
            {"<div class='error'>" + error + "</div>" if error else ""}
            <form method="POST">
                <input type="password" name="password" placeholder="Enter password" autofocus>
                <button type="submit">Enter</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.before_request
def check_site_password():
    """Require password if SITE_PASSWORD is set"""
    if not SITE_PASSWORD:
        return None

    # Allow login page, static files, agent init, API routes, and test pages
    allowed_paths = ['/login', '/favicon.ico', '/api/agent/init', '/test', '/doc8', '/doc8/', '/itr8', '/itr8/', '/itr8/stream', '/in-testing', '/in-testing/', '/databank-preview', '/masters-v2', '/masters-spectral', '/confidentiality', '/nft8', '/cre8', '/moonstone']
    if request.path in allowed_paths or request.path.startswith('/static/') or request.path.startswith('/api/') or request.path.startswith('/doc8') or request.path.startswith('/itr8') or request.path.startswith('/in-testing') or request.path.startswith('/masters') or request.path.startswith('/nft8') or request.path.startswith('/cre8') or request.path.startswith('/moonstone'):
        return None

    # Check if authenticated
    if not session.get('site_authenticated'):
        return redirect('/login')

    return None

# Content Security Policy - prevents XSS and injection attacks
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # Content Security Policy
    # NOTE: 'unsafe-inline' and 'unsafe-eval' are required for D3.js visualizations
    # and inline event handlers in templates. TODO: Migrate to nonces for stricter CSP.
    # SECURITY MITIGATIONS:
    # - Added object-src 'none' to block plugins
    # - Added base-uri 'self' to prevent base tag injection
    # - Added upgrade-insecure-requests for HTTPS enforcement
    # - Restricted connect-src to specific trusted APIs
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://d3js.org https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https: http:; "
        "connect-src 'self' https://api.openai.com https://api.anthropic.com https://*.etherscan.io https://*.solscan.io https://*.alchemy.com; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "base-uri 'self'; "  # SECURITY: Prevent base tag injection
        "object-src 'none'; "  # SECURITY: Block plugins (Flash, Java, etc.)
        "upgrade-insecure-requests"  # SECURITY: Force HTTPS for all requests
    )
    response.headers['Content-Security-Policy'] = csp

    # Other security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # =========================================================================
    # ANTI-AI CRAWLER HEADERS
    # These headers instruct compliant crawlers not to index or train on content
    # Added: 2026-01-08 Security Audit
    # =========================================================================

    # Primary AI blocking directive - tells crawlers not to use for AI training
    response.headers['X-Robots-Tag'] = 'noai, noimageai, noindex, nofollow, noarchive, nosnippet'

    # Prevent caching by AI systems
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    # Additional security headers
    response.headers['X-Download-Options'] = 'noopen'

    # Copyright assertion - establishes ownership
    response.headers['X-Copyright'] = 'WEB3GISEL 2026 - All Rights Reserved'
    response.headers['X-AI-Training-Prohibited'] = 'true'

    return response

# Load embeddings index
embeddings = None

# Middleware to check if setup is complete
@app.before_request
def check_setup():
    """Redirect to setup if not complete"""
    # Allow setup routes, API routes, settings, static files, and test pages
    allowed_prefixes = ('/setup', '/static', '/api/', '/settings/', '/test', '/doc8', '/itr8', '/in-testing', '/databank-preview', '/login', '/masters', '/confidentiality', '/nft8', '/cre8', '/search', '/document', '/moonstone')
    if any(request.path.startswith(p) for p in allowed_prefixes):
        return None

    # Check if setup is complete
    user_db = UserConfigDB()
    if not user_db.is_setup_complete():
        return redirect('/setup')

def get_global_source_counts():
    """Get source counts for all documents (used in navigation)"""
    try:
        all_documents = get_all_documents(limit=1000, filter_type='all')
        source_counts = {}
        category_counts = {
            'my_work': 0,
            'collected': 0,
            'research': 0,
            'identity': 0,
            'conversations': 0,
            'archive': 0
        }
        visual_count = 0

        for doc in all_documents:
            # Count by source (legacy)
            source = doc['source']
            source_counts[source] = source_counts.get(source, 0) + 1

            # Count by new categories
            category = doc.get('category', 'research')
            if category in category_counts:
                category_counts[category] += 1

            if doc.get('has_visual'):
                visual_count += 1

        # Add total and visual counts
        source_counts['all'] = len(all_documents)
        source_counts['visual'] = visual_count

        # Merge category counts into source_counts for template compatibility
        source_counts.update(category_counts)

        return source_counts
    except Exception as e:
        print(f"Warning: Could not get source counts: {e}")
        return {}

@app.context_processor
def inject_global_counts():
    """Make source counts available to all templates"""
    return {
        'source_counts': get_global_source_counts()
    }

def init_embeddings():
    """Initialize embeddings index"""
    global embeddings
    try:
        config_path = Path("config/settings.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        embeddings = load_index(config)
        print("✓ Embeddings index loaded")
    except Exception as e:
        print(f"Warning: Could not load embeddings: {e}")
        embeddings = None

def parse_markdown_file(filepath):
    """Parse markdown file and extract frontmatter and content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            import yaml
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()

    return frontmatter, body

def generate_semantic_filename(current_filename, frontmatter, cognitive_type, blockchain_metadata, body):
    """
    Generate intelligent filename based on semantic network context
    Uses deep analysis of metadata, tags, blockchain info, and content
    to create meaningful filenames when original is not available
    """
    # First, try to extract original filename from document content
    original_patterns = [
        r'(?:original|source)\s*(?:filename|file)[:\s]+([^\s\n]+\.[a-z]{3,4})',
        r'filename[:\s]+([^\s\n]+\.[a-z]{3,4})',
        r'image[:\s]+([^\s\n]+\.[a-z]{3,4})',
    ]

    for pattern in original_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            original_name = match.group(1).strip()
            # Clean up and return if it looks valid
            if len(original_name) > 3 and '.' in original_name:
                return original_name

    # If not found, generate intelligent name based on context
    parts = []

    # 1. Cognitive type prefix
    type_map = {
        'blockchain': 'nft',
        'web_article': 'web',
        'media': 'media',
        'research': 'research',
        'conversation': 'chat'
    }
    parts.append(type_map.get(cognitive_type, cognitive_type))

    # 2. Platform/source identifier
    if blockchain_metadata:
        platforms = blockchain_metadata.get('platforms', [])
        if platforms:
            # Use first platform, clean it up
            platform = platforms[0].lower().replace(' ', '').replace('nft', '')
            parts.append(platform)

        # Add token ID if available
        token_ids = blockchain_metadata.get('token_ids', [])
        if token_ids:
            parts.append(f"token{token_ids[0]}")

        # Add blockchain network
        network = blockchain_metadata.get('blockchain_network')
        if network:
            network_short = {'ethereum': 'eth', 'bitcoin': 'btc', 'solana': 'sol'}
            parts.append(network_short.get(network, network))

    # 3. Domain for web articles
    if cognitive_type == 'web_article':
        domain = frontmatter.get('domain', '')
        if domain:
            # Extract main part (e.g., 'nytimes' from 'nytimes.com')
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                parts.append(domain_parts[0])

    # 4. Title slugification (most important semantic identifier)
    title = frontmatter.get('title', '')
    if title:
        # Clean and slugify title
        title_slug = re.sub(r'[^\w\s-]', '', title.lower())
        title_slug = re.sub(r'[-\s]+', '_', title_slug)
        # Take first 4 meaningful words
        words = [w for w in title_slug.split('_') if len(w) > 2][:4]
        if words:
            parts.extend(words)

    # 5. Add most relevant tag if title not available or too short
    if len(parts) < 3:
        tags = frontmatter.get('tags', [])
        # Filter out generic tags
        generic_tags = {'web_import', 'blockchain', 'nft', 'import', 'article'}
        meaningful_tags = [t for t in tags if t.lower() not in generic_tags and len(t) > 2]
        if meaningful_tags:
            # Add first meaningful tag
            tag_slug = meaningful_tags[0].lower().replace(' ', '_')
            parts.append(tag_slug)

    # 6. Get file extension from current filename
    ext = Path(current_filename).suffix
    if not ext:
        ext = '.png'  # Default to PNG

    # Construct final filename
    # Limit total length and join parts
    filename_base = '_'.join(parts)[:80]  # Max 80 chars before extension
    suggested = f"{filename_base}{ext}"

    # Fallback if somehow we ended up with nothing
    if len(filename_base) < 5:
        doc_id = frontmatter.get('id', 'unknown')
        suggested = f"{cognitive_type}_{doc_id}{ext}"

    return suggested

def search_knowledge_base(query, limit=20):
    """Search knowledge base and return results with images"""
    if not embeddings or not query:
        return []

    try:
        # Search using txtai
        results = embeddings.search(query, limit=limit)

        enriched_results = []

        for score, doc_id in results:
            # Find the markdown file for this doc_id
            kb_path = Path("knowledge_base/processed")
            for md_file in kb_path.rglob("*.md"):
                frontmatter, body = parse_markdown_file(md_file)

                if frontmatter.get('id') == doc_id:
                    # Extract images from the markdown
                    images = re.findall(r'!\[.*?\]\((.*?)\)', body)

                    # Get media files from all possible media directories
                    media_files = []
                    media_dirs = [
                        Path("knowledge_base/media/instagram") / doc_id,
                        Path("knowledge_base/media/web_imports") / doc_id,
                        Path("knowledge_base/media/attachments") / doc_id
                    ]

                    for media_dir in media_dirs:
                        if media_dir.exists():
                            for img_file in media_dir.glob("*"):
                                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                    media_files.append(str(img_file))

                    # Get preview text
                    preview = body[:300].replace('\n', ' ').strip()

                    enriched_results.append({
                        'id': doc_id,
                        'score': float(score),
                        'source': frontmatter.get('source', 'unknown'),
                        'type': frontmatter.get('type', 'unknown'),
                        'title': get_title_from_markdown(body),
                        'preview': preview,
                        'date': frontmatter.get('created_at', frontmatter.get('post_date', '')),
                        'tags': frontmatter.get('tags', []),
                        'images': images,
                        'media_files': media_files,
                        'filepath': str(md_file),
                        'has_visual': len(images) > 0 or len(media_files) > 0
                    })
                    break

        return enriched_results

    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_title_from_markdown(markdown_text):
    """Extract title from markdown"""
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"

def categorize_document(frontmatter, body, source, doc_type):
    """Categorize document into meaningful knowledge vault categories"""
    tags = frontmatter.get('tags', [])
    tags_lower = [tag.lower() for tag in tags]
    title = frontmatter.get('title', '').lower()
    body_lower = body.lower()

    # MY WORK: Original creations by Gisel
    my_work_keywords = ['giselx', 'gisel florez', 'my work', 'my art', 'my nft']
    if any(keyword in tags_lower for keyword in my_work_keywords):
        return 'my_work'
    if any(keyword in title for keyword in my_work_keywords):
        return 'my_work'
    if 'creator' in frontmatter and 'gisel' in frontmatter.get('creator', '').lower():
        return 'my_work'

    # IDENTITY: Professional materials (CV, bio, artist statement)
    identity_keywords = ['cv', 'resume', 'bio', 'artist statement', 'professional', 'portfolio']
    if source == 'attachment' and any(keyword in title for keyword in identity_keywords):
        return 'identity'
    if any(keyword in tags_lower for keyword in identity_keywords):
        return 'identity'

    # CONVERSATIONS: Social interactions and AI discussions
    if source in ['ai_conversation', 'twitter', 'discord']:
        return 'conversations'
    if doc_type == 'conversation' or 'conversation' in tags_lower:
        return 'conversations'

    # RESEARCH: Learning materials, articles, documentation
    if source == 'perplexity':
        return 'research'
    if doc_type in ['web_article', 'research']:
        return 'research'
    research_keywords = ['tutorial', 'documentation', 'guide', 'how to', 'research', 'article']
    if any(keyword in tags_lower for keyword in research_keywords):
        return 'research'

    # COLLECTED: Saved NFTs, artwork from others, visual references
    if source in ['instagram', 'web_import']:
        # If it's blockchain content but not tagged as "my work", it's collected
        if frontmatter.get('blockchain_metadata') and 'my_work' not in tags_lower:
            return 'collected'
        # Instagram saves are typically collected inspiration
        if source == 'instagram':
            return 'collected'
    if 'collected' in tags_lower or 'saved' in tags_lower or 'inspiration' in tags_lower:
        return 'collected'

    # ARCHIVE: Explicitly tagged or old content
    if 'archive' in tags_lower or 'archived' in tags_lower:
        return 'archive'

    # Default: If it has blockchain metadata, assume it's collected NFTs
    if frontmatter.get('blockchain_metadata'):
        return 'collected'

    # Default fallback to research for uncategorized content
    return 'research'

def get_all_documents(limit=50, filter_type=None, sort_by=None):
    """Get all documents from knowledge base"""
    kb_path = Path("knowledge_base/processed")
    documents = []

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)

            doc_type = frontmatter.get('type', 'unknown')
            source = frontmatter.get('source', 'unknown')

            # Categorize document into meaningful knowledge vault categories
            category = categorize_document(frontmatter, body, source, doc_type)

            # Apply filter
            if filter_type and filter_type != 'all':
                # New category-based filtering
                if filter_type in ['my_work', 'collected', 'research', 'identity', 'conversations', 'archive']:
                    if category != filter_type:
                        continue
                # Legacy source-based filtering (for backwards compatibility)
                elif filter_type == 'visual':
                    # Check if has images
                    images = re.findall(r'!\[.*?\]\((.*?)\)', body)
                    media_dir = Path("knowledge_base/media/instagram") / frontmatter.get('id', '')
                    has_media = media_dir.exists() and any(media_dir.glob("*"))
                    if not (images or has_media):
                        continue
                elif source != filter_type:
                    continue

            # Extract images
            images = re.findall(r'!\[.*?\]\((.*?)\)', body)

            # Get media files from all possible media directories
            media_files = []
            doc_id = frontmatter.get('id', '')
            media_dirs = [
                Path("knowledge_base/media/instagram") / doc_id,
                Path("knowledge_base/media/web_imports") / doc_id,
                Path("knowledge_base/media/attachments") / doc_id
            ]

            for media_dir in media_dirs:
                if media_dir.exists():
                    for img_file in media_dir.glob("*"):
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            media_files.append(str(img_file))

            preview = body[:300].replace('\n', ' ').strip()

            # Extract marketplace/IPFS links from body
            marketplace_url = frontmatter.get('url', '')
            ipfs_links = re.findall(r'(ipfs://[^\s\)]+)', body)
            ipfs_gateways = re.findall(r'(https://(?:ipfs\.io|gateway\.pinata\.cloud)/ipfs/[^\s\)]+)', body)

            # Extract original image URLs from markdown (handle both formats)
            image_urls = []
            image_url_matches = re.findall(r'\*\*Original URL:\*\* (https?://[^\n]+)', body)
            image_urls.extend(image_url_matches)
            # Also try alternate format
            alt_matches = re.findall(r'Original URL: (https?://[^\n]+)', body)
            image_urls.extend(alt_matches)

            documents.append({
                'id': frontmatter.get('id', ''),
                'source': source,
                'type': doc_type,
                'category': category,  # New meaningful category
                'title': get_title_from_markdown(body),
                'preview': preview,
                'date': frontmatter.get('created_at', frontmatter.get('post_date', '')),
                'tags': frontmatter.get('tags', []),
                'images': images,
                'media_files': media_files,
                'filepath': str(md_file),
                'has_visual': len(images) > 0 or len(media_files) > 0,
                'marketplace_url': marketplace_url,
                'ipfs_links': ipfs_links,
                'ipfs_gateways': ipfs_gateways,
                'image_urls': image_urls,
                'domain': frontmatter.get('domain', ''),
                'cognitive_type': frontmatter.get('cognitive_type', ''),
                'blockchain_network': frontmatter.get('blockchain_metadata', {}).get('blockchain_network', '') if frontmatter.get('blockchain_metadata') else '',
                'platform': frontmatter.get('blockchain_metadata', {}).get('platforms', [''])[0] if frontmatter.get('blockchain_metadata', {}).get('platforms') else ''
            })

        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            continue

    # Apply sorting
    if sort_by == 'date_desc' or not sort_by:
        # Default: newest first
        documents.sort(key=lambda x: x.get('date', ''), reverse=True)
    elif sort_by == 'date_asc':
        # Oldest first
        documents.sort(key=lambda x: x.get('date', ''), reverse=False)
    elif sort_by == 'title_asc':
        # Title A-Z
        documents.sort(key=lambda x: x.get('title', '').lower())
    elif sort_by == 'title_desc':
        # Title Z-A
        documents.sort(key=lambda x: x.get('title', '').lower(), reverse=True)
    elif sort_by == 'source':
        # Group by source
        documents.sort(key=lambda x: (x.get('source', ''), x.get('date', '')), reverse=True)
    elif sort_by == 'tags':
        # Most tagged first (by tag count, then date)
        documents.sort(key=lambda x: (len(x.get('tags', [])), x.get('date', '')), reverse=True)
    elif sort_by == 'untagged':
        # Untagged first (by tag count ascending, then date)
        documents.sort(key=lambda x: (len(x.get('tags', [])), x.get('date', '')), reverse=False)

    return documents[:limit]

@app.route('/')
def index():
    """Main landing page - light paper theme with WebGL showcases"""
    return render_template('team_gallery.html')

@app.route('/archive')
def archive():
    """Full archive page - dark theme"""
    filter_type = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'date_desc')
    documents = get_all_documents(limit=100, filter_type=filter_type, sort_by=sort_by)

    # source_counts now available globally via context processor

    return render_template('index.html',
                         documents=documents,
                         current_filter=filter_type,
                         current_sort=sort_by)

@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    results = []

    if query:
        results = search_knowledge_base(query, limit=50)

    return render_template('search.html', query=query, results=results)

@app.route('/terms-of-service')
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms_of_service.html')

@app.route('/twitter-verify')
def twitter_verify():
    """Twitter verification page"""
    return render_template('twitter_verify.html')

@app.route('/archive-views')
@app.route('/spatial-vision')
def archive_views():
    """Spatial Vision - Descriptors for new understandings"""
    return render_template('visualizer_overview.html')

@app.route('/test')
def test_page():
    """Test/development page"""
    return render_template('team_gallery.html')

@app.route('/moonstone')
def moonstone_demo():
    """MOONSTONE AI Brain demo page"""
    return render_template('moonstone_demo.html')

@app.route('/setup/accept-terms', methods=['POST'])
def accept_terms():
    """Process ToS acceptance"""
    from flask import session

    # Verify all checkboxes were checked
    agree_terms = request.form.get('agree_terms')
    agree_no_copycat = request.form.get('agree_no_copycat')
    agree_revocation = request.form.get('agree_revocation')

    if agree_terms and agree_no_copycat and agree_revocation:
        # Store acceptance in session and user config
        session['tos_accepted'] = True
        session['tos_accepted_at'] = datetime.now().isoformat()

        # Also store in user config DB if available
        try:
            from interface.user_config_db import UserConfigDB
            user_db = UserConfigDB()
            user = user_db.get_any_user()
            if user:
                conn = user_db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_config
                    SET tos_accepted = 1, tos_accepted_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), user['id']))
                conn.commit()
                conn.close()
        except:
            pass

        # Go to setup wizard first (email, wallet input, etc.)
        # Training layers come after setup is complete
        return redirect(url_for('setup_wizard'))
    else:
        return redirect(url_for('terms_of_service'))

@app.route('/setup/declined')
def setup_declined():
    """User declined ToS"""
    return '''
    <html>
    <head><title>ARCHIV-IT | Terms Declined</title></head>
    <body style="background: #0a0a0f; color: #e8e6e3; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
        <div style="text-align: center; max-width: 400px;">
            <h1 style="font-weight: 300; letter-spacing: 0.1em;">ARCHIV-IT</h1>
            <p style="color: rgba(232,230,227,0.5);">You must accept the Terms of Service to use ARCHIV-IT.</p>
            <a href="/terms-of-service" style="color: #d4a574;">Return to Terms</a>
        </div>
    </body>
    </html>
    '''

@app.route('/api/trust-score')
def get_trust_score():
    """Get current user's trust score for the indicator"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from trust_system import get_trust_score_for_display

        result = get_trust_score_for_display()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'trust_score': 0,
            'level': 'critical',
            'breakdown': {},
            'recommendations': ['Complete setup to build your trust score'],
            'error': str(e)
        })

@app.route('/training-layers')
def training_layers():
    """Training layers selection - build your dataspace"""
    return render_template('training_layers.html')

@app.route('/setup/training', methods=['POST'])
def setup_training():
    """Process selected training layers and redirect to first layer form"""
    selected_layers = request.form.getlist('layers')
    if selected_layers:
        # Store selected layers in session for multi-step form
        from flask import session
        session['training_layers'] = selected_layers
        session['training_current'] = 0
        # Redirect to first layer form
        return redirect(url_for('training_layer_form', layer=selected_layers[0]))
    return redirect(url_for('training_layers'))

@app.route('/training/<layer>')
def training_layer_form(layer):
    """Individual layer training form"""
    from flask import session
    selected_layers = session.get('training_layers', [])
    current_idx = session.get('training_current', 0)

    if layer not in selected_layers:
        return redirect(url_for('training_layers'))

    # Update current index based on layer position
    try:
        current_idx = selected_layers.index(layer)
        session['training_current'] = current_idx
    except ValueError:
        pass

    # Layer metadata for form rendering
    layer_info = {
        'identity': {'title': 'Identity Foundation', 'fields': ['professional_name', 'wallet_addresses', 'platform_profiles', 'social_handles']},
        'throughline': {'title': 'Artistic Throughline', 'fields': ['origin_philosophy', 'evolution_points', 'techniques', 'recurring_themes', 'signature_elements']},
        'works': {'title': 'Body of Work', 'fields': ['series', 'collections', 'individual_works']},
        'collaborations': {'title': 'Collaboration Network', 'fields': ['active_collaborations', 'historical_projects', 'collaborator_roles']},
        'roles': {'title': 'Roles & Positions', 'fields': ['founder', 'advisor', 'curator', 'ambassador', 'board_positions']},
        'exhibitions': {'title': 'Exhibition History', 'fields': ['physical_shows', 'virtual_exhibitions', 'speaking', 'performances']},
        'recognition': {'title': 'Recognition & Press', 'fields': ['awards', 'press_features', 'museum_collections', 'interviews']},
        'collectors': {'title': 'Collector Network', 'fields': ['notable_collectors', 'relationships', 'patronage']},
        'platforms': {'title': 'Platform Layer', 'fields': ['primary_platforms', 'contracts', 'platform_roles', 'platform_health']},
        'temporal': {'title': 'Temporal / Living Works', 'fields': ['interactive_works', 'programmable_works', 'scheduled_events']},
        'preservation': {'title': 'Preservation & Risk', 'fields': ['platform_dependency', 'revival_solutions', 'backups', 'legal_ip']},
        'collection': {'title': 'Collection Layer', 'fields': ['holdings_by_chain', 'holdings_by_artist', 'holdings_by_theme', 'value_trajectory']},
        'artist_relationships': {'title': 'Artist Relationships', 'fields': ['depth_per_artist', 'first_acquisitions', 'irl_connections']},
        'community': {'title': 'Community Layer', 'fields': ['daos', 'collector_circles', 'co_collecting', 'exhibition_loans']},
        # Social Archive Imports
        'twitter_archive': {'title': 'Twitter/X Archive Import', 'fields': ['archive_path', 'username'], 'is_import': True},
        'instagram_archive': {'title': 'Instagram Archive Import', 'fields': ['archive_path', 'username'], 'is_import': True}
    }

    info = layer_info.get(layer, {'title': layer.title(), 'fields': []})
    progress = ((current_idx + 1) / len(selected_layers)) * 100 if selected_layers else 0

    return render_template('training_layer_form.html',
                         layer=layer,
                         layer_info=info,
                         current_idx=current_idx,
                         total_layers=len(selected_layers),
                         progress=progress,
                         selected_layers=selected_layers)

@app.route('/training/<layer>/save', methods=['POST'])
def save_training_layer(layer):
    """Save training layer data and advance to next"""
    from flask import session
    import json

    selected_layers = session.get('training_layers', [])
    current_idx = session.get('training_current', 0)

    # Get all form data
    layer_data = {}
    for key, value in request.form.items():
        if value.strip():  # Only save non-empty values
            layer_data[key] = value.strip()

    # Save to local training data file
    training_file = Path("knowledge_base/training_data.json")
    training_file.parent.mkdir(parents=True, exist_ok=True)

    existing_data = {}
    if training_file.exists():
        try:
            with open(training_file, 'r') as f:
                existing_data = json.load(f)
        except:
            existing_data = {}

    existing_data[layer] = layer_data

    with open(training_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

    # Advance to next layer or complete
    try:
        layer_idx = selected_layers.index(layer)
        if layer_idx < len(selected_layers) - 1:
            # Go to next layer
            next_layer = selected_layers[layer_idx + 1]
            session['training_current'] = layer_idx + 1
            return redirect(url_for('training_layer_form', layer=next_layer))
        else:
            # Training complete
            session.pop('training_layers', None)
            session.pop('training_current', None)
            return redirect('/')
    except ValueError:
        return redirect(url_for('training_layers'))

# =============================================================================
# Scrape Queue API Routes
# =============================================================================

@app.route('/api/scrape-queue/status')
def scrape_queue_status():
    """Get scrape queue status and resumable jobs"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.scrape_queue_manager import ScrapeQueueManager

        qm = ScrapeQueueManager()
        status = qm.get_queue_status()
        resumable = qm.get_resumable_jobs()

        return jsonify({
            'status': status,
            'resumable_jobs': resumable
        })
    except Exception as e:
        return jsonify({'error': str(e), 'resumable_jobs': []})

@app.route('/api/scrape-queue/estimate', methods=['POST'])
def scrape_queue_estimate():
    """Estimate cost for a scrape job"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.scrape_queue_manager import ScrapeQueueManager

        data = request.get_json()
        source_type = data.get('source_type', 'twitter_archive')
        source_path = data.get('source_path', '')
        include_embeddings = data.get('include_embeddings', True)
        include_vision = data.get('include_vision', False)

        qm = ScrapeQueueManager()

        # Count items first
        item_count = qm._count_items(source_type, source_path)

        # Get estimate
        estimate = qm.estimate_cost(
            source_type,
            item_count,
            include_embeddings,
            include_vision
        )

        return jsonify(estimate)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/scrape-queue/create', methods=['POST'])
def scrape_queue_create():
    """Create a new scrape job"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.scrape_queue_manager import ScrapeQueueManager

        data = request.get_json()
        source_type = data.get('source_type')
        source_path = data.get('source_path')
        username = data.get('username', 'unknown')
        options = data.get('options', {})

        qm = ScrapeQueueManager()
        job = qm.create_job(source_type, source_path, username, options)

        return jsonify(job)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/scrape-queue/resume/<job_id>', methods=['POST'])
def scrape_queue_resume(job_id):
    """Resume a paused scrape job"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.scrape_queue_manager import ScrapeQueueManager

        qm = ScrapeQueueManager()
        resume_data = qm.resume_job(job_id)

        if resume_data:
            return jsonify({
                'success': True,
                'job_id': job_id,
                'checkpoint': resume_data['checkpoint']
            })
        else:
            return jsonify({'error': 'Job not found or cannot be resumed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/scrape-queue/pause/<job_id>', methods=['POST'])
def scrape_queue_pause(job_id):
    """Pause a running scrape job"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.scrape_queue_manager import ScrapeQueueManager

        data = request.get_json() or {}
        checkpoint_data = data.get('checkpoint_data')

        qm = ScrapeQueueManager()
        success = qm.pause_job(job_id, checkpoint_data)

        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/scrape-queue/job/<job_id>')
def scrape_queue_job(job_id):
    """Get job details"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.scrape_queue_manager import ScrapeQueueManager

        qm = ScrapeQueueManager()
        job = qm.get_job(job_id)

        if job:
            return jsonify(job)
        else:
            return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/document/<doc_id>')
def document_detail(doc_id):
    """View full document"""
    kb_path = Path("knowledge_base/processed")

    for md_file in kb_path.rglob("*.md"):
        frontmatter, body = parse_markdown_file(md_file)

        if frontmatter.get('id') == doc_id:
            # Get media files from all possible media directories
            media_files = []
            model_files = []
            media_dirs = [
                Path("knowledge_base/media/instagram") / doc_id,
                Path("knowledge_base/media/web_imports") / doc_id,
                Path("knowledge_base/media/attachments") / doc_id,
                Path("knowledge_base/media/google_drive") / doc_id,
                Path("knowledge_base/attachments") / doc_id
            ]

            for media_dir in media_dirs:
                if media_dir.exists():
                    for file in media_dir.glob("*"):
                        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            media_files.append({
                                'filename': file.name,
                                'path': str(file)  # Relative path from project root
                            })
                        elif file.suffix.lower() in ['.glb', '.gltf']:
                            model_files.append({
                                'filename': file.name,
                                'path': str(file),
                                'type': file.suffix.lower()[1:]  # 'glb' or 'gltf'
                            })

            return render_template('document.html',
                                 frontmatter=frontmatter,
                                 body=body,
                                 media_files=media_files,
                                 model_files=model_files)

    return "Document not found", 404

@app.route('/api/document/<doc_id>/delete-images', methods=['POST'])
def delete_document_images(doc_id):
    """Delete specific images from a document"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])

        if not filenames:
            return jsonify({'error': 'No filenames provided'}), 400

        # Find all media directories for this document
        media_base = Path("knowledge_base/media")
        deleted_count = 0

        if media_base.exists():
            for media_type_dir in media_base.iterdir():
                if media_type_dir.is_dir():
                    doc_media_dir = media_type_dir / doc_id
                    if doc_media_dir.exists():
                        for filename in filenames:
                            file_path = doc_media_dir / filename
                            if file_path.exists():
                                file_path.unlink()
                                deleted_count += 1

        return jsonify({'success': True, 'deleted': deleted_count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/<doc_id>/update', methods=['POST'])
def update_document(doc_id):
    """Update document content and tags"""
    try:
        data = request.get_json()
        new_body = data.get('body', '')
        new_tags = data.get('tags', [])

        kb_path = Path("knowledge_base/processed")

        for md_file in kb_path.rglob("*.md"):
            frontmatter, body = parse_markdown_file(md_file)

            if frontmatter.get('id') == doc_id:
                # Update frontmatter
                frontmatter['tags'] = new_tags

                # Write back to file
                new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---\n\n{new_body}"

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return jsonify({'success': True})

        return jsonify({'error': 'Document not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/media/<path:filepath>')
def serve_media(filepath):
    """Serve media files securely"""
    # Get absolute path to project root
    project_root = Path(__file__).parent.parent.parent

    # Construct full path and resolve it to prevent directory traversal
    full_path = (project_root / filepath).resolve()

    # Security check: ensure the resolved path is within project root
    try:
        full_path.relative_to(project_root)
    except ValueError:
        return "Access denied", 403

    # Check if file exists
    if not full_path.is_file():
        return "File not found", 404

    # Serve the file
    return send_from_directory(full_path.parent, full_path.name)

@app.route('/api/stats')
def api_stats():
    """Get knowledge base statistics"""
    kb_path = Path("knowledge_base/processed")
    total_docs = len(list(kb_path.rglob("*.md")))

    # Count by source
    sources = {}
    visual_count = 0

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            source = frontmatter.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            # Check if has visual content
            images = re.findall(r'!\[.*?\]\((.*?)\)', body)
            media_dir = Path("knowledge_base/media/instagram") / frontmatter.get('id', '')
            if images or (media_dir.exists() and any(media_dir.glob("*"))):
                visual_count += 1
        except:
            continue

    return jsonify({
        'total_documents': total_docs,
        'visual_documents': visual_count,
        'sources': sources
    })

@app.route('/api/agent/init')
def api_agent_init():
    """
    Agent Initialization Endpoint
    =============================
    Returns critical context that AI agents MUST read before doing work.

    This endpoint consolidates:
    - Current state from AGENT_CONTEXT_STATE.md
    - TODO queue
    - Architecture overview
    - Critical rules
    - Founder terminology

    Usage: curl http://localhost:5001/api/agent/init
    """
    from pathlib import Path
    import yaml

    project_root = Path(__file__).parent.parent.parent

    def read_file(filepath):
        full_path = project_root / filepath
        if full_path.exists():
            return full_path.read_text(encoding='utf-8')
        return None

    def extract_todos(content):
        if not content:
            return []
        todos = []
        lines = content.split('\n')
        for line in lines:
            if '- [ ]' in line:
                todos.append(line.strip().replace('- [ ]', '').strip())
        return todos[:10]  # Top 10

    # Read context state
    context = read_file("AGENT_CONTEXT_STATE.md")
    onboarding = read_file("docs/AGENT_ONBOARDING.md")

    # Extract last action
    last_action = None
    if context:
        import re
        match = re.search(r'ACTION:\s*(.+?)(?:\n|STATUS)', context, re.DOTALL)
        if match:
            last_action = match.group(1).strip()

    # Extract TODOs
    todos = extract_todos(context)

    # Build response
    response = {
        'initialized': True,
        'timestamp': datetime.now().isoformat(),
        'project': 'ARCHIV-IT',

        'current_state': {
            'last_action': last_action,
            'todo_queue': todos,
            'server_url': 'http://localhost:5001'
        },

        'architecture': {
            'ecosystem': {
                'DOC-8': 'DATABASE & ARCHIVE (Foundation - current focus)',
                'IT-R8': 'CREATE & RATE (spatial design tool)',
                'SOCI-8': 'SHARE & CONNECT (future)'
            },
            'northstar_masters': {
                'feminine': ['Hildegard', 'Gisel', 'Rand', 'Starhawk', 'Tori', 'Bjork', 'Swan', 'Hicks', 'Byrne'],
                'masculine': ['da Vinci', 'Tesla', 'Fuller', 'Jung', 'Suleyman', 'Grant', 'Prince', 'Coltrane', 'Bowie', 'Koe', 'Jobs', 'Cherny', 'Rene']
            },
            'physics_constants': {
                'PHI': 1.618033988749895,
                'GOLDEN_ANGLE': 137.5077640500378,
                'SCHUMANN': 7.83,
                'TESLA_PATTERN': [3, 6, 9]
            }
        },

        'rules': {
            'non_negotiables': [
                'User owns their seed (mathematical identity)',
                'No tracking without explicit consent',
                'All data transformations are reversible',
                'Local-first, cloud-optional',
                'Balance polarity in all outputs (PHI threshold)'
            ],
            'terminology': {
                'ultrathink': 'Deep comprehensive analysis required',
                'seed': 'User\'s mathematical identity (local, sovereign)',
                'vertex': 'User\'s optimal state/position',
                'spiral': 'Natural flow pattern (creation direction)'
            }
        },

        'files_to_read': [
            'AGENT_CONTEXT_STATE.md',
            'docs/AGENT_ONBOARDING.md',
            'docs/FOUNDER_QUOTES.md',
            'docs/ULTRATHINK_SYNTHESIS.md'
        ],

        'commands': {
            'start_server': 'KMP_DUPLICATE_LIB_OK=TRUE ./venv/bin/python scripts/interface/visual_browser.py',
            'init_agent': './venv/bin/python scripts/agent/init_agent.py',
            'search': 'KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "query"'
        },

        'session_end_protocol': [
            'Update AGENT_CONTEXT_STATE.md with last action',
            'Create backup if significant work done',
            'Do NOT leave work incomplete without documenting'
        ]
    }

    return jsonify(response)


@app.route('/api/document-content')
def api_document_content():
    """Get full document content for attachments and other documents"""
    filepath = request.args.get('filepath')

    if not filepath:
        return jsonify({'success': False, 'error': 'No filepath provided'})

    try:
        # Parse the markdown file
        frontmatter, body = parse_markdown_file(filepath)

        # Extract links from the body
        http_links = re.findall(r'https?://[^\s\)\]]+', body)
        ipfs_links = re.findall(r'ipfs://[^\s\)\]]+', body)
        all_links = list(set(http_links + ipfs_links))  # Remove duplicates

        # Clean the body content - remove frontmatter formatting if present
        clean_body = body.strip()

        # Remove excessive newlines
        clean_body = re.sub(r'\n{3,}', '\n\n', clean_body)

        return jsonify({
            'success': True,
            'body': clean_body,
            'type': frontmatter.get('type', 'document'),
            'date': frontmatter.get('created_at', frontmatter.get('post_date', '')),
            'tags': frontmatter.get('tags', []),
            'links': all_links,
            'source': frontmatter.get('source', 'unknown')
        })

    except Exception as e:
        print(f"Error loading document content: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add-content', methods=['GET', 'POST'])
def add_content():
    """Add content from URL"""
    if request.method == 'POST':
        url = request.form.get('url')
        title = request.form.get('title')
        notes = request.form.get('notes', '')
        manual_content = request.form.get('manual_content', '')
        source_type = request.form.get('source_type', 'web_import')
        extract_images = request.form.get('extract_images') == 'on'
        crawl_site = request.form.get('crawl_site') == 'on'

        try:
            # Scrape the URL
            doc_id = scrape_and_save_url(url, title, notes, source_type, extract_images, manual_content, crawl_site)

            return render_template('add_content.html', success=True, doc_id=doc_id)
        except Exception as e:
            return render_template('add_content.html', error=str(e))

    return render_template('add_content.html')

@app.route('/api/preview-url')
def preview_url():
    """Preview a URL before importing"""
    url = request.args.get('url')

    # SECURITY: Validate URL to prevent SSRF attacks
    is_safe, error_msg = is_safe_url(url)
    if not is_safe:
        return jsonify({'error': f'Invalid URL: {error_msg}'}), 400

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get title
        title = ''
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()

        # Get preview text
        preview = ''
        for p in soup.find_all('p')[:3]:
            preview += p.get_text().strip() + ' '

        return jsonify({
            'title': title,
            'preview': preview[:200]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def requires_javascript_rendering(url):
    """Check if URL requires JavaScript rendering (like Claude, ChatGPT, NFT platforms, etc.)"""
    js_heavy_domains = [
        # AI Chat platforms
        'claude.ai',
        'chat.openai.com',
        'chatgpt.com',
        'bard.google.com',
        'gemini.google.com',
        'perplexity.ai',
        'character.ai',
        # NFT Marketplaces (heavily JavaScript-rendered)
        'foundation.app',
        'opensea.io',
        'rarible.com',
        'superrare.com',
        'zora.co',
        'manifold.xyz',
        'exchange.art',
        'objkt.com',
        'fxhash.xyz',
    ]

    domain = urlparse(url).netloc.lower()
    return any(js_domain in domain for js_domain in js_heavy_domains)

def scrape_with_selenium(url, wait_time=5):
    """Use Selenium to scrape JavaScript-rendered pages"""
    if not SELENIUM_AVAILABLE:
        raise Exception("Selenium not available. Install with: pip install selenium webdriver-manager")

    # Set up Brave/Chrome options
    chrome_options = Options()

    # Point to Brave browser binary
    chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Initialize driver with Brave using manually downloaded ChromeDriver
    import os
    chromedriver_path = os.path.expanduser("~/chromedriver/chromedriver-mac-arm64/chromedriver")

    if os.path.exists(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        # Fallback to webdriver-manager
        try:
            service = Service(ChromeDriverManager(driver_version="latest").install())
        except Exception as e:
            print(f"Warning: Could not auto-install driver: {e}")
            service = Service()

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Loading page with Selenium: {url}")
        driver.get(url)

        # Wait for content to load
        time.sleep(wait_time)

        # For NFT platforms, scroll to load images and wait longer
        if any(nft_site in url for nft_site in ['foundation.app', 'opensea.io', 'rarible.com', 'superrare.com']):
            try:
                # Scroll to bottom to trigger lazy-loaded images
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                # Scroll back to top
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                # Wait for images to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )
                print("  → Scrolled page and waited for NFT images to load")
            except:
                print("  → Timeout waiting for images, proceeding with available content")
                pass

        # For Claude conversations, wait for specific elements
        elif 'claude.ai' in url:
            try:
                # Wait for conversation content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except:
                pass

        # Get page title
        title = driver.title

        # Get page source after JavaScript execution
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Extract text content
        content_text = ''
        seen_text = set()  # Track seen text to avoid duplicates

        # For Claude conversations, look for specific content structure
        if 'claude.ai' in url:
            # Try to find conversation messages
            messages = soup.find_all(['div', 'article'], class_=re.compile('message|content|conversation', re.I))

            if messages:
                for msg in messages:
                    text = msg.get_text(separator='\n', strip=True)
                    if text and len(text) > 10 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)
            else:
                # Fallback: get all paragraphs and text blocks
                for element in soup.find_all(['p', 'div', 'article', 'section']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)

        # For NFT platforms, extract structured data with priority on artwork descriptions
        elif any(nft_site in url for nft_site in ['foundation.app', 'opensea.io', 'rarible.com', 'superrare.com']):
            print("  → Extracting NFT-specific content...")

            # Priority 1: Extract artwork titles (most important)
            nft_titles = soup.find_all(['h1', 'h2'], class_=re.compile('title|name|artwork', re.I))
            for title_elem in nft_titles:
                text = title_elem.get_text(strip=True)
                if text and len(text) > 2 and text not in seen_text:
                    # Skip navigation/button text
                    if not any(skip in text.lower() for skip in ['menu', 'profile', 'wallet', 'connect', 'sign in', 'explore']):
                        content_text += f"**{text}**\n\n"
                        seen_text.add(text)
                        print(f"  → Found NFT title: {text[:50]}")

            # Priority 2: Extract NFT descriptions (artist statements, artwork details)
            # SuperRare-specific: Look for description sections
            description_selectors = [
                'div[class*="description"]',
                'div[class*="about"]',
                'div[class*="details"]',
                'p[class*="description"]',
                'section[class*="description"]',
                'div[data-testid*="description"]',
                'div[aria-label*="description"]'
            ]

            for selector in description_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    # NFT descriptions are usually substantial
                    if text and len(text) > 50 and text not in seen_text:
                        # Filter out navigation, headers, footers
                        if not any(skip in text.lower() for skip in [
                            'connect wallet', 'sign in', 'marketplace', 'trending', 'cookies',
                            'privacy policy', 'terms of service', '©', 'all rights reserved',
                            'follow us', 'newsletter', 'discord', 'twitter'
                        ]):
                            content_text += text + '\n\n'
                            seen_text.add(text)
                            print(f"  → Found NFT description: {text[:80]}...")

            # Priority 3: Extract artist bio/statement (contextual)
            bio_selectors = [
                'div[class*="bio"]',
                'div[class*="artist"]',
                'section[class*="about"]',
                'p[class*="bio"]'
            ]

            for selector in bio_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 40 and text not in seen_text:
                        if not any(skip in text.lower() for skip in ['connect wallet', 'marketplace', 'trending', 'newsletter']):
                            content_text += text + '\n\n'
                            seen_text.add(text)
                            print(f"  → Found artist bio: {text[:60]}...")

            # Priority 4: Extract metadata (medium, edition, date, etc.)
            metadata_selectors = [
                'div[class*="metadata"]',
                'div[class*="properties"]',
                'div[class*="details"]',
                'dl',  # Definition lists often contain metadata
                'span[class*="edition"]',
                'span[class*="medium"]'
            ]

            for selector in metadata_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10 and text not in seen_text:
                        # Metadata is usually concise key-value pairs
                        if any(meta_key in text.lower() for meta_key in ['edition', 'medium', 'created', 'minted', 'owner', 'creator', 'size', 'year']):
                            content_text += text + '\n\n'
                            seen_text.add(text)
                            print(f"  → Found metadata: {text[:50]}")

            # Priority 5: Extract any remaining paragraphs (fallback for content we might have missed)
            remaining_paragraphs = soup.find_all('p')
            for p in remaining_paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 30 and text not in seen_text:
                    # More aggressive filtering for generic paragraphs
                    if not any(skip in text.lower() for skip in [
                        'connect', 'wallet', 'sign in', 'menu', 'explore', 'marketplace',
                        'cookies', 'privacy', 'terms', 'newsletter', 'follow', 'discord',
                        'twitter', 'instagram', 'rights reserved', '©'
                    ]):
                        content_text += text + '\n\n'
                        seen_text.add(text)

            # Clean up content - remove technical metadata that might have slipped through
            lines_to_remove = []
            for line in content_text.split('\n'):
                # Skip lines with file paths, URLs, or technical metadata
                if any(tech in line.lower() for tech in [
                    'knowledge_base/', 'media/web_imports/', 'http://', 'https://',
                    '**source:**', '**imported:**', '**metadata:**', '**original url:**',
                    'avatar', 'image_', '.jpg', '.png', '.jpeg', 'storage.googleapis',
                    'pixura.imgix.net', 'ipfs://', 'cloudfront.net'
                ]):
                    lines_to_remove.append(line)
                # Skip very short lines (likely navigation or labels)
                elif len(line.strip()) < 15:
                    lines_to_remove.append(line)

            # Remove unwanted lines
            for line in lines_to_remove:
                content_text = content_text.replace(line, '')

            # Clean up excessive whitespace
            content_text = '\n'.join(line for line in content_text.split('\n') if line.strip())
            content_text = '\n\n'.join(content_text.split('\n\n'))

            print(f"  ✓ Extracted {len(content_text)} characters of meaningful NFT content")

        else:
            # Generic extraction for other JS-heavy sites
            main_content = soup.find('main') or soup.find('article') or soup.body
            if main_content:
                for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)

        print(f"✓ Extracted {len(content_text)} characters with Selenium")

        return title, content_text, soup

    finally:
        driver.quit()

def crawl_website(base_url, max_pages=20):
    """Crawl a website and discover all internal pages"""
    from urllib.parse import urljoin, urlparse

    visited = set()
    to_visit = {base_url}
    discovered_pages = []
    base_domain = urlparse(base_url).netloc

    print(f"Starting site crawl of {base_domain}...")

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop()

        if current_url in visited:
            continue

        visited.add(current_url)
        print(f"  Crawling [{len(visited)}/{max_pages}]: {current_url}")

        try:
            response = requests.get(current_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            discovered_pages.append({
                'url': current_url,
                'soup': soup
            })

            # Find all links on this page
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Make absolute URL
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)

                # Only follow internal links on same domain
                if parsed.netloc == base_domain:
                    # Remove fragments
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"

                    # Skip certain file types and duplicates
                    if not any(ext in clean_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip']):
                        if clean_url not in visited:
                            to_visit.add(clean_url)

        except Exception as e:
            print(f"  Error crawling {current_url}: {e}")
            continue

    print(f"✓ Discovered {len(discovered_pages)} pages")
    return discovered_pages

def scrape_and_save_url(url, custom_title=None, notes='', source_type='web_import', extract_images=True, manual_content='', crawl_site=False):
    """Scrape URL and save to knowledge base"""

    # If crawl_site is enabled, crawl all pages
    all_pages = []
    all_images = []

    if crawl_site and not manual_content.strip():
        pages = crawl_website(url, max_pages=20)
        all_pages = pages

        # Aggregate content from all pages
        content_text = ''
        title = custom_title or urlparse(url).netloc

        for idx, page_data in enumerate(pages):
            page_url = page_data['url']
            soup = page_data['soup']

            # Get page title if not set
            if idx == 0 and not custom_title:
                if soup.title:
                    title = soup.title.string.strip()
                elif soup.find('h1'):
                    title = soup.find('h1').get_text().strip()

            # Add page heading
            page_title = ''
            if soup.title:
                page_title = soup.title.string.strip()
            elif soup.find('h1'):
                page_title = soup.find('h1').get_text().strip()
            else:
                page_title = urlparse(page_url).path or 'Home'

            content_text += f"\n## Page: {page_title}\n"
            content_text += f"URL: {page_url}\n\n"

            # Extract content from this page
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))

            if main_content:
                for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                    text = element.get_text().strip()
                    if text:
                        content_text += text + '\n\n'
            else:
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_text += text + '\n\n'

            content_text += "\n---\n\n"

        soup = all_pages[0]['soup'] if all_pages else None

    # If manual content provided, use it
    elif manual_content.strip():
        title = custom_title or urlparse(url).netloc
        content_text = manual_content
        soup = None
    # Check if URL requires JavaScript rendering
    elif requires_javascript_rendering(url):
        print(f"Detected JavaScript-heavy site, using Selenium...")
        title, content_text, soup = scrape_with_selenium(url)

        # Override with custom title if provided
        if custom_title:
            title = custom_title
    else:
        # Fetch the page with standard HTTP request
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        if custom_title:
            title = custom_title
        elif soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        else:
            title = urlparse(url).netloc

        # Extract main content
        content_text = ''

        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))

        if main_content:
            # Get all text from main content
            for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                text = element.get_text().strip()
                if text:
                    content_text += text + '\n\n'
        else:
            # Fallback: get all paragraphs
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short paragraphs
                    content_text += text + '\n\n'

    # Generate doc ID
    doc_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]

    # Extract images if requested (only if we scraped the page)
    saved_images = []
    if extract_images:
        media_dir = Path("knowledge_base/media/web_imports") / doc_id
        media_dir.mkdir(parents=True, exist_ok=True)

        # Collect images from all pages if we crawled the site
        all_img_tags = []
        if crawl_site and all_pages:
            print(f"Extracting images from {len(all_pages)} pages...")
            for page_data in all_pages:
                page_soup = page_data['soup']
                all_img_tags.extend(page_soup.find_all('img'))
        elif soup:
            all_img_tags = soup.find_all('img')

        print(f"Found {len(all_img_tags)} total images, downloading...")

        # Increase limit when crawling entire site
        img_limit = 50 if crawl_site else 10
        unique_img_urls = set()  # Track to avoid duplicates

        for idx, img in enumerate(all_img_tags):
            if len(saved_images) >= img_limit:
                break

            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # Make absolute URL
            img_url = urljoin(url, img_url)

            # Skip duplicates
            if img_url in unique_img_urls:
                continue
            unique_img_urls.add(img_url)

            # Skip small images (likely icons/logos)
            if 'icon' in img_url.lower() or 'logo' in img_url.lower():
                continue

            # Skip data URIs that are too small
            if img_url.startswith('data:') and len(img_url) < 1000:
                continue

            try:
                # Download image
                img_response = requests.get(img_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': url
                })

                # Check if actually an image
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    continue

                # Get file extension from content-type or URL
                img_ext = Path(urlparse(img_url).path).suffix
                if not img_ext or img_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    # Determine from content-type
                    ext_map = {
                        'image/jpeg': '.jpg',
                        'image/png': '.png',
                        'image/gif': '.gif',
                        'image/webp': '.webp'
                    }
                    img_ext = ext_map.get(content_type, '.jpg')

                # Extract metadata from HTML
                img_alt = img.get('alt', '')
                img_title = img.get('title', '')
                img_caption = ''

                # Try to find caption (common patterns)
                parent = img.find_parent(['figure', 'div'])
                if parent:
                    caption_elem = parent.find(['figcaption', 'caption', 'p'])
                    if caption_elem:
                        img_caption = caption_elem.get_text().strip()

                # Save image
                img_filename = f"image_{idx}{img_ext}"
                img_path = media_dir / img_filename

                with open(img_path, 'wb') as f:
                    f.write(img_response.content)

                print(f"  ✓ Downloaded: {img_filename} ({len(img_response.content)} bytes)")

                saved_images.append({
                    'filename': img_filename,
                    'path': str(img_path),
                    'original_url': img_url,
                    'alt_text': img_alt,
                    'title': img_title,
                    'caption': img_caption,
                    'size_bytes': len(img_response.content)
                })

                # Auto-analyze with visual translator if enabled
                if VISUAL_TRANSLATOR_AVAILABLE:
                    config_path = Path("config/settings.json")
                    if config_path.exists():
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                        vt_config = config.get('visual_translator', {})

                        if vt_config.get('enabled') and vt_config.get('auto_analyze_on_import'):
                            print(f"  → Analyzing image with Visual Translator...")
                            try:
                                # Skip vision to avoid costs by default, can be enabled
                                skip_vision = not vt_config.get('vision_enabled', False)
                                analysis = analyze_image(img_path, skip_vision=skip_vision)

                                # Store analysis in saved_images metadata
                                if analysis.get('ocr'):
                                    saved_images[-1]['ocr_text'] = analysis['ocr'].get('text', '')
                                    saved_images[-1]['has_text'] = analysis['ocr'].get('has_text', False)
                                if analysis.get('vision'):
                                    saved_images[-1]['vision_description'] = analysis['vision'].get('description', '')

                                print(f"  ✓ Analysis complete")
                            except Exception as e:
                                print(f"  ✗ Analysis failed: {e}")

            except Exception as e:
                print(f"  ✗ Failed to download {img_url}: {e}")
                continue

        print(f"✓ Saved {len(saved_images)} images")

    # Extract tags
    tags = [source_type, 'web_import']

    # Auto-tag based on content
    content_lower = (title + ' ' + content_text).lower()
    tag_keywords = {
        'art': ['art', 'artwork', 'creative', 'artist'],
        'blockchain': ['blockchain', 'crypto', 'nft', 'web3'],
        'technology': ['tech', 'technology', 'digital'],
        'photography': ['photo', 'photography', 'camera'],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)

    # Aggregate image analysis data
    images_with_text = [img for img in saved_images if img.get('has_text')]
    all_ocr_text = '\n\n'.join([img.get('ocr_text', '') for img in images_with_text if img.get('ocr_text')])
    all_vision_descs = [img.get('vision_description', '') for img in saved_images if img.get('vision_description')]

    # Create frontmatter
    now = datetime.now()
    frontmatter = {
        'id': doc_id,
        'source': source_type,
        'type': 'web_import',
        'created_at': now.isoformat(),
        'url': url,
        'title': title,
        'domain': urlparse(url).netloc,
        'scraped_date': now.strftime('%Y-%m-%d'),
        'image_count': len(saved_images),
        'has_images': len(saved_images) > 0,
        'images_with_text': len(images_with_text),
        'tags': list(set(tags))
    }

    # Add visual analysis fields if available
    if all_ocr_text:
        frontmatter['ocr_text'] = all_ocr_text[:1000]  # First 1000 chars for search
        frontmatter['has_text'] = True
    if all_vision_descs:
        frontmatter['vision_description'] = ' | '.join(all_vision_descs)
        frontmatter['visual_analysis_date'] = now.isoformat()

    # Create markdown
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# {title}

**Source:** [{urlparse(url).netloc}]({url})
**Imported:** {now.strftime('%B %d, %Y')}

"""

    if notes:
        md_content += f"""## Your Notes

{notes}

"""

    md_content += f"""## Content

{content_text}

"""

    # Add images section with rich metadata
    if saved_images:
        md_content += "## Images\n\n"
        for idx, img in enumerate(saved_images, 1):
            # Handle both absolute and relative paths
            img_path = Path(img['path'])
            if img_path.is_absolute():
                rel_path = img_path.relative_to(Path.cwd())
            else:
                rel_path = img_path

            md_content += f"### Image {idx}: {img['filename']}\n\n"
            md_content += f"![{img.get('alt_text', img['filename'])}](../../{rel_path})\n\n"

            # Add metadata table
            md_content += "**Metadata:**\n\n"
            md_content += f"- **Original URL:** {img.get('original_url', 'N/A')}\n"
            if img.get('alt_text'):
                md_content += f"- **Alt Text:** {img['alt_text']}\n"
            if img.get('title'):
                md_content += f"- **Title:** {img['title']}\n"
            if img.get('caption'):
                md_content += f"- **Caption:** {img['caption']}\n"
            md_content += f"- **File Size:** {img.get('size_bytes', 0):,} bytes\n"

            # Add OCR results if available
            if img.get('has_text') and img.get('ocr_text'):
                md_content += f"\n**Extracted Text (OCR):**\n\n"
                md_content += f"```\n{img['ocr_text'][:500]}\n```\n"
                if len(img['ocr_text']) > 500:
                    md_content += f"\n*(Showing first 500 characters of {len(img['ocr_text'])} total)*\n"

            # Add vision description if available
            if img.get('vision_description'):
                md_content += f"\n**AI Description:**\n\n"
                md_content += f"> {img['vision_description']}\n"

            md_content += "\n---\n\n"

    md_content += f"""## Source
- Original URL: {url}
- Domain: {urlparse(url).netloc}
- Scraped: {now.strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Save to knowledge base
    subject = 'web_imports'
    processed_dir = Path(f"knowledge_base/processed/about_{subject}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    md_filename = f"web_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Save raw data
    raw_dir = Path("knowledge_base/raw/web_imports")
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_data = {
        'url': url,
        'title': title,
        'content': content_text[:1000],  # Preview only
        'images': saved_images,
        'scraped_at': now.isoformat()
    }

    raw_filepath = raw_dir / f"web_{doc_id}_{timestamp}.json"
    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved web import: {title} (ID: {doc_id})")

    return doc_id


# ============================================================================
# DATA SOURCE MANAGER
# ============================================================================

@app.route('/data-source-manager')
def data_source_manager():
    """Data Source Manager - utility view for managing raw data sources"""
    return render_template('data_source_manager.html')


@app.route('/api/data-sources')
def api_data_sources():
    """API endpoint for Data Source Manager - returns all data sources with metadata"""
    try:
        sources = []
        stats = {
            'blockchain': 0,
            'web_import': 0,
            'attachment': 0,
            'google_drive': 0,
            'perplexity': 0,
            'ai_conversation': 0,
            'other': 0,
            'partial': 0,
            'broken': 0
        }

        kb_path = Path("knowledge_base/processed")
        media_base = Path("knowledge_base/media")

        if kb_path.exists():
            for md_file in kb_path.rglob("*.md"):
                try:
                    frontmatter, body = parse_markdown_file(md_file)
                    doc_id = frontmatter.get('id', '')
                    source = frontmatter.get('source', 'unknown')
                    title = frontmatter.get('title', '')

                    # Classify cognitive type
                    cognitive_type = classify_document_cognitive_type({
                        'title': title,
                        'source': source,
                        'tags': frontmatter.get('tags', []),
                        'has_images': frontmatter.get('has_images', False),
                        'image_count': frontmatter.get('image_count', 0),
                        'word_count': len(body.split()) if body else 0,
                        'domain': frontmatter.get('domain', ''),
                        'body': body[:500] if body else ''
                    })

                    # Check if has media
                    has_media = False
                    for media_dir in media_base.iterdir() if media_base.exists() else []:
                        if (media_dir / doc_id).exists():
                            has_media = True
                            break

                    # Calculate completeness
                    completeness = 0
                    if title: completeness += 25
                    if body and len(body) > 50: completeness += 25
                    if frontmatter.get('url'): completeness += 25
                    if has_media: completeness += 25

                    source_entry = {
                        'doc_id': doc_id,
                        'title': title,
                        'filename': md_file.name,
                        'source': source,
                        'cognitive_type': cognitive_type,
                        'url': frontmatter.get('url', ''),
                        'created_at': frontmatter.get('created_at', ''),
                        'has_media': has_media,
                        'is_text_only': not has_media,
                        'completeness': completeness,
                        'doc_frontmatter': frontmatter,
                        'doc_body': body[:200] if body else '',
                        'vision_desc': frontmatter.get('visual_description', '')[:100] if frontmatter.get('visual_description') else ''
                    }

                    sources.append(source_entry)

                    # Update stats by source type
                    if cognitive_type == 'blockchain':
                        stats['blockchain'] += 1
                    elif source == 'web_import':
                        stats['web_import'] += 1
                    elif source == 'attachment':
                        stats['attachment'] += 1
                    elif source == 'google_drive':
                        stats['google_drive'] += 1
                    elif source == 'perplexity':
                        stats['perplexity'] += 1
                    elif source == 'ai_conversation':
                        stats['ai_conversation'] += 1
                    else:
                        stats['other'] += 1

                    # Track data health
                    if completeness < 50:
                        stats['broken'] += 1
                    elif completeness < 75:
                        stats['partial'] += 1

                except Exception as e:
                    continue

        return jsonify({
            'sources': sources,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': str(e), 'sources': [], 'stats': {}}), 500


@app.route('/api/delete-documents', methods=['POST'])
def delete_documents():
    """Delete multiple documents"""
    try:
        data = request.get_json()
        doc_ids = data.get('doc_ids', [])

        if not doc_ids:
            return jsonify({'success': False, 'error': 'No document IDs provided'}), 400

        kb_path = Path("knowledge_base/processed")
        deleted_count = 0
        errors = []

        for doc_id in doc_ids:
            try:
                # Find and delete markdown file
                for md_file in kb_path.rglob("*.md"):
                    frontmatter, _ = parse_markdown_file(md_file)

                    if frontmatter.get('id') == doc_id:
                        # Delete the markdown file
                        md_file.unlink()
                        deleted_count += 1

                        # Delete associated media directory if exists
                        media_paths = [
                            Path("knowledge_base/media/instagram") / doc_id,
                            Path("knowledge_base/media/web_imports") / doc_id,
                            Path("knowledge_base/attachments") / doc_id
                        ]

                        for media_path in media_paths:
                            if media_path.exists():
                                import shutil
                                shutil.rmtree(media_path)

                        # Delete raw data if exists
                        raw_paths = [
                            Path("knowledge_base/raw/web_imports"),
                            Path("knowledge_base/raw/perplexity"),
                            Path("knowledge_base/raw/attachments")
                        ]

                        for raw_path in raw_paths:
                            if raw_path.exists():
                                for raw_file in raw_path.glob(f"*{doc_id}*"):
                                    raw_file.unlink()

                        break
            except Exception as e:
                errors.append(f"Error deleting {doc_id}: {str(e)}")

        # Update embeddings index after deletion
        if deleted_count > 0:
            try:
                # Reload the embeddings to reflect deletions
                init_embeddings()
            except Exception as e:
                print(f"Warning: Could not update embeddings: {e}")

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors if errors else None
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/visual-translator')
def visual_translator():
    """Visual translator panel - shows all images with analysis status"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return "Visual Translator not available. Install required packages.", 503

    # Helper function for file size formatting
    def format_bytes(bytes_size):
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"

    # Find all images in media directories
    media_base = Path("knowledge_base/media")
    all_images = []

    # Cache for cognitive type classification (one per document)
    cognitive_cache = {}

    if media_base.exists():
        for source_dir in media_base.iterdir():
            if source_dir.is_dir():
                for doc_dir in source_dir.iterdir():
                    if doc_dir.is_dir():
                        doc_id = doc_dir.name
                        source = source_dir.name

                        # Find markdown file for this doc
                        md_file = None
                        kb_path = Path("knowledge_base/processed")
                        for md in kb_path.rglob("*.md"):
                            try:
                                frontmatter, body = parse_markdown_file(md)
                                if frontmatter.get('id') == doc_id:
                                    md_file = md
                                    break
                            except:
                                continue

                        # Get images and media files in this doc directory
                        for img_file in doc_dir.glob("*"):
                            # Support images, videos, and audio files
                            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp',
                                                           '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v',
                                                           '.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']:
                                # Initialize image data
                                # Determine source type for visual distinctions
                                source_type = None
                                automation_ready = False
                                file_ext = img_file.suffix.lower()

                                # Audio files
                                if file_ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']:
                                    source_type = 'audio'
                                    automation_ready = True  # Audio transcripts are automation-ready

                                # Video files
                                elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']:
                                    source_type = 'video'

                                # Image files - need more context
                                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                    # Check source directory
                                    if 'web' in source.lower() or 'import' in source.lower():
                                        source_type = 'web-scrape'
                                    elif 'manual' in source.lower() or 'upload' in source.lower():
                                        source_type = 'file-upload'
                                    else:
                                        # Default for images
                                        source_type = 'visual-ai'  # Assume visual content

                                img_data = {
                                    'path': str(img_file),
                                    'filename': img_file.name,
                                    'doc_id': doc_id,
                                    'source': source,
                                    'source_type': source_type,
                                    'source_types': None,  # For merged documents with multiple sources
                                    'is_merged': False,
                                    'automation_ready': automation_ready,
                                    'analyzed': False,
                                    'has_text': False,
                                    'vision_desc': None,
                                    'cognitive_type': 'unknown',
                                    'blockchain_metadata': None,
                                    'domain': None,
                                    'file_size': 0,
                                    'file_size_human': '0 B',
                                    'dimensions': None,
                                    'width': 0,
                                    'height': 0,
                                    'relationship_count': 0,
                                    'doc_frontmatter': {},
                                    'original_date': None,
                                    'created_at': None,
                                    'doc_body': None,
                                    'source_urls': []  # Track all source URLs with metadata
                                }

                                if md_file:
                                    frontmatter, body = parse_markdown_file(md_file)

                                    # Check if this is a merged document (multiple sources)
                                    if frontmatter.get('is_merged') and frontmatter.get('source_types'):
                                        img_data['is_merged'] = True
                                        img_data['source_types'] = frontmatter['source_types']
                                        # Also keep single source_type for backward compatibility
                                        # Use first source type as primary
                                        img_data['source_type'] = frontmatter['source_types'][0] if frontmatter['source_types'] else source_type

                                    # FIX: Document-level analysis applies to ALL images
                                    doc_analyzed = 'visual_analysis_date' in frontmatter
                                    doc_has_text = frontmatter.get('has_text', False)
                                    doc_vision_desc = frontmatter.get('vision_description', '')

                                    img_data['analyzed'] = doc_analyzed
                                    img_data['has_text'] = doc_has_text
                                    img_data['vision_desc'] = doc_vision_desc[:100] if doc_vision_desc else None
                                    img_data['doc_frontmatter'] = frontmatter

                                    # Extract document body text for context in hover overlay
                                    # Limit to first 300 characters to keep hover overlay concise
                                    if body and len(body.strip()) > 0:
                                        clean_body = body.strip()

                                        # Remove markdown headers and extra whitespace
                                        import re
                                        clean_body = re.sub(r'^#+\s+', '', clean_body, flags=re.MULTILINE)
                                        clean_body = re.sub(r'\n\n+', ' ', clean_body)

                                        # Filter out technical metadata from body text
                                        lines = clean_body.split('\n')
                                        filtered_lines = []
                                        for line in lines:
                                            # Skip technical metadata, file paths, URLs
                                            if not any(tech in line.lower() for tech in [
                                                'knowledge_base/', 'media/web_imports/', 'http://', 'https://',
                                                '**source:**', '**imported:**', '**metadata:**', '**original url:**',
                                                'avatar', 'image_', '.jpg', '.png', '.jpeg', 'storage.googleapis',
                                                'pixura.imgix.net', 'ipfs://', 'cloudfront.net', '../', './',
                                                '[avatar]', '(http'
                                            ]):
                                                # Skip very short lines (navigation/labels)
                                                if len(line.strip()) >= 20:
                                                    filtered_lines.append(line.strip())

                                        clean_body = ' '.join(filtered_lines)

                                        # Only save if we have meaningful content
                                        if len(clean_body) > 50:
                                            img_data['doc_body'] = clean_body[:300] if len(clean_body) > 300 else clean_body

                                    # Classify cognitive type (cached per document)
                                    if doc_id not in cognitive_cache:
                                        doc = {
                                            'id': doc_id,
                                            'source': frontmatter.get('source', source),  # Use frontmatter source, fallback to directory
                                            'type': frontmatter.get('type', ''),
                                            'title': frontmatter.get('title', ''),
                                            'body': body[:1000],  # First 1000 chars for classification
                                            'url': frontmatter.get('url', ''),
                                            'tags': frontmatter.get('tags', []),
                                            'created_at': frontmatter.get('created_at', ''),
                                            'image_count': frontmatter.get('image_count', 0),
                                            'has_images': frontmatter.get('has_images', False),
                                        }

                                        cognitive_type = classify_document_cognitive_type(doc)
                                        blockchain_meta = None

                                        if cognitive_type == 'blockchain':
                                            blockchain_meta = extract_blockchain_metadata(doc)

                                        cognitive_cache[doc_id] = {
                                            'type': cognitive_type,
                                            'blockchain': blockchain_meta
                                        }

                                    img_data['cognitive_type'] = cognitive_cache[doc_id]['type']
                                    img_data['blockchain_metadata'] = cognitive_cache[doc_id]['blockchain']

                                    # Always fetch current owner for ALL blockchain NFTs
                                    img_data['is_collected'] = False
                                    img_data['current_owner'] = None
                                    img_data['creator_address'] = None

                                    if cognitive_cache[doc_id]['blockchain'] and cognitive_cache[doc_id]['type'] == 'blockchain':
                                        blockchain_meta = cognitive_cache[doc_id]['blockchain']

                                        # Get creator addresses (your minting addresses from user config)
                                        creator_addresses = set()
                                        try:
                                            user_config_db = UserConfigDB()
                                            user = user_config_db.get_primary_user()
                                            if user:
                                                minting_addrs = user_config_db.get_minting_addresses(user['id'])
                                                creator_addresses = {addr['address'].lower() for addr in minting_addrs}
                                        except:
                                            pass

                                        # Fallback: Use blockchain addresses found in document as creator
                                        if not creator_addresses:
                                            blockchain_addrs = blockchain_meta.get('blockchain_addresses', [])
                                            for network, addr in blockchain_addrs:
                                                creator_addresses.add(addr.lower())

                                        # Set creator address for display
                                        if creator_addresses:
                                            img_data['creator_address'] = list(creator_addresses)[0]

                                        # ALWAYS query blockchain for current owner on browser reload
                                        contract_addr = blockchain_meta.get('contract_address')
                                        token_ids = blockchain_meta.get('token_ids', [])
                                        network = blockchain_meta.get('blockchain_network', 'ethereum')

                                        if contract_addr and token_ids and network == 'ethereum':
                                            token_id = str(token_ids[0])

                                            # Try Alchemy API first (more reliable for current owner)
                                            alchemy_key = os.getenv('ALCHEMY_API_KEY', '')
                                            if alchemy_key:
                                                try:
                                                    import requests
                                                    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{alchemy_key}/getOwnersForToken"
                                                    params = {
                                                        'contractAddress': contract_addr,
                                                        'tokenId': token_id
                                                    }
                                                    response = requests.get(url, params=params, timeout=3)
                                                    if response.status_code == 200:
                                                        data = response.json()
                                                        owners = data.get('owners', [])
                                                        if owners:
                                                            img_data['current_owner'] = owners[0].lower()
                                                except:
                                                    pass

                                            # Fallback to Etherscan API
                                            if not img_data['current_owner']:
                                                etherscan_key = os.getenv('ETHERSCAN_API_KEY', '')
                                                if etherscan_key:
                                                    try:
                                                        import requests
                                                        url = f"https://api.etherscan.io/api?module=account&action=tokennfttx&contractaddress={contract_addr}&page=1&offset=1&sort=desc&apikey={etherscan_key}"
                                                        response = requests.get(url, timeout=3)
                                                        if response.status_code == 200:
                                                            data = response.json()
                                                            if data.get('status') == '1' and data.get('result'):
                                                                for tx in data['result']:
                                                                    if tx.get('tokenID') == token_id:
                                                                        img_data['current_owner'] = tx.get('to', '').lower()
                                                                        break
                                                    except:
                                                        pass

                                        # Final fallback: Check document metadata for owner
                                        if not img_data['current_owner']:
                                            if frontmatter.get('current_owner'):
                                                img_data['current_owner'] = frontmatter['current_owner'].lower()
                                            elif blockchain_meta.get('blockchain_addresses'):
                                                # Use first blockchain address as assumed owner
                                                img_data['current_owner'] = blockchain_meta['blockchain_addresses'][0][1].lower()

                                        # Mark as "collected" ONLY if current owner != creator
                                        if img_data['current_owner'] and img_data['current_owner'] not in creator_addresses:
                                            img_data['is_collected'] = True

                                    # Refine source type based on metadata
                                    # Blockchain NFTs override other types
                                    if cognitive_cache[doc_id]['blockchain'] and cognitive_cache[doc_id]['type'] == 'blockchain':
                                        img_data['source_type'] = 'blockchain'
                                        img_data['automation_ready'] = True  # Blockchain data is verified

                                    # AI-analyzed images
                                    if doc_analyzed and img_data['source_type'] == 'visual-ai':
                                        img_data['automation_ready'] = True  # AI-analyzed images are automation-ready

                                    # Written content (no images, text-only)
                                    if frontmatter.get('type') == 'note' or frontmatter.get('type') == 'article':
                                        if not frontmatter.get('has_images'):
                                            img_data['source_type'] = 'written'

                                    # Extract domain for web articles (always try to get it)
                                    url_to_parse = frontmatter.get('url') or frontmatter.get('source_url')
                                    if url_to_parse:
                                        img_data['domain'] = extract_domain_from_url(url_to_parse)
                                    elif not img_data['domain']:
                                        # Fallback: Try to extract from document domain field
                                        img_data['domain'] = frontmatter.get('domain', '')

                                    # Relationship count (use tag count as proxy)
                                    img_data['relationship_count'] = len(frontmatter.get('tags', []))

                                    # Extract timeline dates (original_date from blockchain metadata, created_at from frontmatter)
                                    if img_data['blockchain_metadata'] and img_data['blockchain_metadata'].get('original_date'):
                                        img_data['original_date'] = img_data['blockchain_metadata']['original_date']

                                    img_data['created_at'] = frontmatter.get('created_at') or frontmatter.get('date')

                                # Get file metadata
                                try:
                                    stat = img_file.stat()
                                    img_data['file_size'] = stat.st_size
                                    img_data['file_size_human'] = format_bytes(stat.st_size)
                                except:
                                    pass

                                # Get image dimensions (current downsampled version)
                                try:
                                    from PIL import Image as PILImage
                                    with PILImage.open(img_file) as pil_img:
                                        img_data['dimensions'] = f"{pil_img.width}×{pil_img.height}"
                                        img_data['width'] = pil_img.width
                                        img_data['height'] = pil_img.height
                                except:
                                    pass

                                # Extract original dimensions from document metadata
                                img_data['original_dimensions'] = None
                                img_data['original_width'] = None
                                img_data['original_height'] = None
                                img_data['suggested_filename'] = None

                                if md_file:
                                    # Look for original dimensions in document body
                                    # Common patterns: "1920x1080", "width: 1920, height: 1080", "dimensions: 1920×1080"
                                    dimension_patterns = [
                                        r'(?:original|source)?\s*(?:dimension|size|resolution)[:\s]+(\d{3,5})\s*[x×]\s*(\d{3,5})',
                                        r'width[:\s]+(\d{3,5})[,\s]+height[:\s]+(\d{3,5})',
                                        r'(\d{3,5})\s*[x×]\s*(\d{3,5})\s*(?:px|pixels)',
                                    ]

                                    for pattern in dimension_patterns:
                                        match = re.search(pattern, body, re.IGNORECASE)
                                        if match:
                                            orig_w, orig_h = int(match.group(1)), int(match.group(2))
                                            # Only accept if larger than current (original should be bigger)
                                            if orig_w > img_data.get('width', 0) or orig_h > img_data.get('height', 0):
                                                img_data['original_dimensions'] = f"{orig_w}×{orig_h}"
                                                img_data['original_width'] = orig_w
                                                img_data['original_height'] = orig_h
                                                break

                                    # Generate intelligent filename based on semantic context
                                    img_data['suggested_filename'] = generate_semantic_filename(
                                        img_file.name,
                                        frontmatter,
                                        img_data.get('cognitive_type', 'unknown'),
                                        img_data.get('blockchain_metadata'),
                                        body
                                    )

                                    # Extract source URLs from document metadata
                                    source_urls = []

                                    # Method 1: Check frontmatter URLs
                                    if frontmatter.get('url'):
                                        source_urls.append({
                                            'url': frontmatter['url'],
                                            'domain': extract_domain_from_url(frontmatter['url'])[:10] if extract_domain_from_url(frontmatter['url']) else 'unknown',
                                            'is_highres': False,
                                            'type': 'document'
                                        })

                                    # Method 2: Check merged document URLs
                                    if frontmatter.get('urls'):
                                        for idx, url in enumerate(frontmatter['urls']):
                                            if url not in [s['url'] for s in source_urls]:
                                                source_urls.append({
                                                    'url': url,
                                                    'domain': extract_domain_from_url(url)[:10] if extract_domain_from_url(url) else 'unknown',
                                                    'is_highres': False,
                                                    'type': 'merged'
                                                })

                                    # Method 3: Parse image metadata from markdown body - SKIP image CDN URLs
                                    # We don't want direct image hosting URLs (pixura.img, CDN buckets, etc.)
                                    # Only include platform URLs (SuperRare, Foundation, etc.) which come from frontmatter

                                    # Method 4: Check blockchain IPFS URLs
                                    if img_data.get('blockchain_metadata'):
                                        ipfs_hashes = img_data['blockchain_metadata'].get('ipfs_hashes', [])
                                        for ipfs_hash in ipfs_hashes[:2]:  # Max 2 IPFS links
                                            ipfs_url = f"https://ipfs.io/ipfs/{ipfs_hash.replace('ipfs://', '')}"
                                            if ipfs_url not in [s['url'] for s in source_urls]:
                                                source_urls.append({
                                                    'url': ipfs_url,
                                                    'domain': 'ipfs.io',
                                                    'is_highres': True,  # IPFS is typically high-res original
                                                    'type': 'ipfs'
                                                })

                                    img_data['source_urls'] = source_urls

                                all_images.append(img_data)

    # === FIX: Include documents WITHOUT media files ===
    # Scan knowledge_base/processed/ for documents not already in all_images
    existing_doc_ids = set(img['doc_id'] for img in all_images)
    kb_path = Path("knowledge_base/processed")

    if kb_path.exists():
        for md_file in kb_path.rglob("*.md"):
            try:
                frontmatter, body = parse_markdown_file(md_file)
                doc_id = frontmatter.get('id')

                # Skip if this document already has media entries
                if doc_id and doc_id not in existing_doc_ids:
                    # Create a text-only entry for documents without media
                    source = frontmatter.get('source', 'unknown')

                    # Classify cognitive type
                    if doc_id not in cognitive_cache:
                        cognitive_cache[doc_id] = {
                            'type': classify_document_cognitive_type({
                                'title': frontmatter.get('title', ''),
                                'source': source,
                                'tags': frontmatter.get('tags', []),
                                'has_images': frontmatter.get('has_images', False),
                                'image_count': frontmatter.get('image_count', 0),
                                'word_count': len(body.split()) if body else 0,
                                'domain': frontmatter.get('domain', ''),
                                'body': body[:500] if body else ''
                            }),
                            'blockchain': False
                        }

                    # Create text-only document entry
                    text_entry = {
                        'path': str(md_file),
                        'filename': f"{frontmatter.get('title', 'Untitled')[:30]}...",
                        'doc_id': doc_id,
                        'source': source,
                        'source_type': 'written',
                        'source_types': None,
                        'is_merged': frontmatter.get('is_merged', False),
                        'automation_ready': False,
                        'analyzed': 'visual_analysis_date' in frontmatter,
                        'has_text': True,
                        'vision_desc': frontmatter.get('vision_description', '')[:100] if frontmatter.get('vision_description') else None,
                        'cognitive_type': cognitive_cache[doc_id]['type'],
                        'blockchain_metadata': None,
                        'domain': frontmatter.get('domain'),
                        'file_size': 0,
                        'file_size_human': '0 B',
                        'dimensions': None,
                        'width': 0,
                        'height': 0,
                        'relationship_count': 0,
                        'doc_frontmatter': frontmatter,
                        'original_date': frontmatter.get('original_date'),
                        'created_at': frontmatter.get('created_at'),
                        'doc_body': body[:300] if body else None,
                        'source_urls': [],
                        'is_text_only': True  # Flag for template to handle differently
                    }

                    all_images.append(text_entry)
                    existing_doc_ids.add(doc_id)

            except Exception as e:
                continue
    # === END FIX ===

    # Calculate stats BEFORE filtering
    total = len(all_images)
    analyzed = len([img for img in all_images if img['analyzed']])
    pending = total - analyzed
    with_text = len([img for img in all_images if img['has_text']])

    # Count assets per platform/network/type/quality for filter visibility
    platform_counts = {}
    network_counts = {}
    type_counts = {}
    quality_counts = {'high': 0, 'medium': 0, 'low': 0}

    for img in all_images:
        # Count platforms
        if img.get('blockchain_metadata'):
            platforms = img['blockchain_metadata'].get('platforms', [])
            for platform in platforms:
                platform_counts[platform] = platform_counts.get(platform, 0) + 1

            # Count networks
            network = img['blockchain_metadata'].get('blockchain_network')
            if network:
                network_counts[network] = network_counts.get(network, 0) + 1

        # Count content types
        ctype = img.get('cognitive_type')
        if ctype:
            type_counts[ctype] = type_counts.get(ctype, 0) + 1

        # Count quality levels
        width = img.get('width', 0)
        height = img.get('height', 0)
        if width >= 1920 or height >= 1920:
            quality_counts['high'] += 1
        elif (1024 <= width < 1920) or (1024 <= height < 1920):
            quality_counts['medium'] += 1
        elif width < 1024 and height < 1024:
            quality_counts['low'] += 1

    # Get filter parameters from query string
    filter_type = request.args.get('filter', 'all')  # existing filter
    network_filter = request.args.get('network', 'all')
    platform_filter = request.args.get('platform', 'all')
    quality_filter = request.args.get('quality', 'all')
    type_filter = request.args.get('type', 'all')

    # Apply existing filter AFTER stats calculated
    if filter_type == 'analyzed':
        all_images = [img for img in all_images if img['analyzed']]
    elif filter_type == 'pending':
        all_images = [img for img in all_images if not img['analyzed']]
    elif filter_type == 'has_text':
        all_images = [img for img in all_images if img['has_text']]

    # Apply Tier 1: Blockchain Network filter
    if network_filter != 'all':
        if network_filter == 'none':
            # Show only non-blockchain content
            all_images = [img for img in all_images if not img.get('blockchain_metadata')]
        else:
            # Show only specific blockchain network (ethereum, bitcoin, solana)
            all_images = [img for img in all_images
                         if img.get('blockchain_metadata')
                         and img['blockchain_metadata'].get('blockchain_network') == network_filter]

    # Apply Tier 2: Platform filter
    if platform_filter != 'all':
        all_images = [img for img in all_images
                     if img.get('blockchain_metadata')
                     and platform_filter in img['blockchain_metadata'].get('platforms', [])]

    # Apply Tier 3: Quality/Resolution filter
    if quality_filter != 'all':
        if quality_filter == 'high':
            # High-res: ≥1920px on either dimension
            all_images = [img for img in all_images
                         if img.get('width', 0) >= 1920 or img.get('height', 0) >= 1920]
        elif quality_filter == 'medium':
            # Medium-res: 1024-1919px on either dimension
            all_images = [img for img in all_images
                         if (1024 <= img.get('width', 0) < 1920) or (1024 <= img.get('height', 0) < 1920)]
        elif quality_filter == 'low':
            # Low-res: <1024px on both dimensions
            all_images = [img for img in all_images
                         if img.get('width', 0) < 1024 and img.get('height', 0) < 1024]

    # Apply Tier 4: Cognitive Type filter
    if type_filter != 'all':
        all_images = [img for img in all_images if img.get('cognitive_type') == type_filter]

    # Apply timeline sorting
    sort_by = request.args.get('sort', 'default')
    if sort_by == 'original_date':
        # Sort by original date (IPFS upload, mint date, etc.) - newest first
        all_images = sorted(all_images, key=lambda x: x.get('original_date') or x.get('created_at') or '1970-01-01', reverse=True)
    elif sort_by == 'created_date':
        # Sort by import/created date - newest first
        all_images = sorted(all_images, key=lambda x: x.get('created_at') or '1970-01-01', reverse=True)
    elif sort_by == 'oldest_first':
        # Sort by original date - oldest first (for timeline view)
        all_images = sorted(all_images, key=lambda x: x.get('original_date') or x.get('created_at') or '2999-01-01', reverse=False)

    return render_template('visual_translator.html',
                         images=all_images,
                         total=total,
                         analyzed=analyzed,
                         pending=pending,
                         with_text=with_text,
                         current_filter=filter_type,
                         network_filter=network_filter,
                         platform_filter=platform_filter,
                         quality_filter=quality_filter,
                         type_filter=type_filter,
                         sort_by=sort_by,
                         platform_counts=platform_counts,
                         network_counts=network_counts,
                         type_counts=type_counts,
                         quality_counts=quality_counts)

@app.route('/api/estimate-costs', methods=['POST'])
def api_estimate_costs():
    """API endpoint to estimate costs for processing media - Deep Analysis Version"""
    try:
        from cost_manager import cost_manager

        data = request.get_json()
        url = data.get('url')
        extract_images = data.get('extract_images', True)
        crawl_site = data.get('crawl_site', False)

        # Service toggles
        enable_vision = data.get('enable_vision', True)
        enable_transcription = data.get('enable_transcription', True)
        enable_video = data.get('enable_video', True)

        # Model selection
        vision_model = data.get('vision_model', 'haiku')  # haiku, sonnet, or opus

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Fetch the page to count media
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            return jsonify({
                'error': f'Failed to fetch URL: {str(e)}',
                'image_count': 0,
                'audio_count': 0,
                'video_count': 0,
                'total_cost': 0.0
            }), 200

        # Count images
        image_count = 0
        if extract_images and enable_vision:
            img_tags = soup.find_all('img', src=True)
            # Filter out tiny images (icons, tracking pixels)
            image_count = len([img for img in img_tags
                             if 'data:image' not in img.get('src', '')
                             and not any(x in img.get('src', '').lower() for x in ['icon', 'logo', 'pixel', 'tracker'])])

        # Count and analyze audio files
        audio_files = []
        if enable_transcription:
            # Audio tags
            for audio_tag in soup.find_all('audio'):
                duration = audio_tag.get('duration', 0)
                audio_files.append({
                    'url': audio_tag.get('src', ''),
                    'estimated_duration_minutes': float(duration) / 60 if duration else 3
                })

            # Audio sources
            for source in soup.find_all('source', type=lambda x: x and 'audio' in x):
                audio_files.append({
                    'url': source.get('src', ''),
                    'estimated_duration_minutes': 3  # Default estimate
                })

            # Audio links
            for link in soup.find_all('a', href=lambda x: x and any(x.endswith(ext) for ext in ['.mp3', '.wav', '.m4a', '.aac'])):
                audio_files.append({
                    'url': link.get('href', ''),
                    'estimated_duration_minutes': 3  # Default estimate
                })

        # Count and analyze video files
        video_files = []
        if enable_video:
            # Video tags
            for video_tag in soup.find_all('video'):
                duration = video_tag.get('duration', 0)
                video_files.append({
                    'url': video_tag.get('src', ''),
                    'estimated_duration_seconds': float(duration) if duration else 10
                })

            # Video sources
            for source in soup.find_all('source', type=lambda x: x and 'video' in x):
                video_files.append({
                    'url': source.get('src', ''),
                    'estimated_duration_seconds': 10  # Default estimate
                })

            # Video links
            for link in soup.find_all('a', href=lambda x: x and any(x.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv'])):
                video_files.append({
                    'url': link.get('href', ''),
                    'estimated_duration_seconds': 10  # Default estimate
                })

        # Use cost manager for deep estimation
        estimate = cost_manager.estimate_web_import(
            url=url,
            image_count=image_count,
            audio_files=audio_files,
            video_files=video_files,
            vision_model=vision_model,
            enable_vision=enable_vision and extract_images,
            enable_transcription=enable_transcription,
            enable_video=enable_video
        )

        # Apply site crawl multiplier if enabled
        if crawl_site:
            estimated_pages = 5
            estimate['total_cost'] *= estimated_pages
            estimate['total_items'] *= estimated_pages

            for est in estimate['estimates']:
                est['total_cost'] *= estimated_pages
                est['item_count'] *= estimated_pages
                if est.get('details'):
                    est['details']['page_multiplier'] = estimated_pages

            estimate['crawl_multiplier'] = estimated_pages

        estimate['crawl_site'] = crawl_site
        estimate['settings'] = {
            'vision_model': vision_model,
            'enable_vision': enable_vision,
            'enable_transcription': enable_transcription,
            'enable_video': enable_video,
            'extract_images': extract_images
        }

        return jsonify(estimate)

    except Exception as e:
        import traceback
        print(f"Cost estimation error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-image', methods=['POST'])
def api_analyze_image():
    """API endpoint to analyze a single image"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Visual translator not available'}), 503

    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        skip_vision = data.get('skip_vision', False)

        if not doc_id:
            return jsonify({'error': 'No doc_id provided'}), 400

        # Find image file
        media_dirs = [
            Path("knowledge_base/media/instagram") / doc_id,
            Path("knowledge_base/media/web_imports") / doc_id,
            Path("knowledge_base/media/attachments") / doc_id
        ]

        image_path = None
        for media_dir in media_dirs:
            if media_dir.exists():
                for img_file in media_dir.glob("*"):
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        image_path = img_file
                        break
                if image_path:
                    break

        if not image_path:
            return jsonify({'error': 'No image found for this document'}), 404

        # Analyze image
        analysis = analyze_image(image_path, skip_vision=skip_vision)

        # Update markdown file
        kb_path = Path("knowledge_base/processed")
        for md_file in kb_path.rglob("*.md"):
            frontmatter, body = parse_markdown_file(md_file)

            if frontmatter.get('id') == doc_id:
                # Update frontmatter
                ocr = analysis.get('ocr', {})
                vision = analysis.get('vision', {})

                if ocr:
                    frontmatter['ocr_text'] = ocr.get('text', '')
                    frontmatter['ocr_confidence'] = round(ocr.get('confidence', 0), 2)
                    frontmatter['has_text'] = ocr.get('has_text', False)

                if vision:
                    frontmatter['vision_description'] = vision.get('description', '')
                    frontmatter['vision_tags'] = vision.get('tags', [])
                    frontmatter['vision_scene_type'] = vision.get('scene_type', '')
                    frontmatter['detected_objects'] = vision.get('detected_objects', [])

                frontmatter['visual_analysis_date'] = datetime.now().isoformat()

                # Write back
                new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---{body}"
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return jsonify({
                    'success': True,
                    'analysis': analysis
                })

        return jsonify({'error': 'Markdown file not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe-media', methods=['POST'])
def api_transcribe_media():
    """API endpoint to transcribe audio/video files and save to knowledge base"""
    if not WHISPER_AVAILABLE:
        return jsonify({'error': 'Whisper transcription not available. Install ffmpeg and openai-whisper.'}), 503

    try:
        data = request.get_json()
        media_path = data.get('media_path', '').replace('/media/', '')
        filename = data.get('filename', '')
        source_doc_id = data.get('doc_id', '')

        if not media_path or not filename:
            return jsonify({'error': 'Missing media_path or filename'}), 400

        # Construct full path
        full_path = Path(media_path)
        if not full_path.exists():
            return jsonify({'error': f'Media file not found: {media_path}'}), 404

        # Load Whisper model (base model - good balance of speed/accuracy)
        print(f"Loading Whisper model...")
        model = whisper.load_model("base")

        # Transcribe audio/video
        print(f"Transcribing {filename}...")
        result = model.transcribe(str(full_path))

        transcript_text = result["text"]
        detected_language = result.get("language", "unknown")
        word_count = len(transcript_text.split())

        # Generate new document ID
        new_doc_id = hashlib.md5(f"{filename}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        # Determine source type based on original document
        kb_path = Path("knowledge_base/processed")
        source_type = "transcripts"
        original_title = ""
        original_url = ""

        # Find original document to link to
        for md_file in kb_path.rglob("*.md"):
            frontmatter, _ = parse_markdown_file(md_file)
            if frontmatter.get('id') == source_doc_id:
                source_type = frontmatter.get('type', 'transcripts')
                original_title = frontmatter.get('title', '')
                original_url = frontmatter.get('url', '')
                break

        # Create transcript document title
        title = f"Transcript: {original_title or filename}"

        # Create frontmatter
        frontmatter_data = {
            'id': new_doc_id,
            'source': 'transcript',
            'type': 'transcript',
            'created_at': datetime.now().isoformat(),
            'title': title,
            'original_filename': filename,
            'source_document_id': source_doc_id,
            'original_url': original_url,
            'media_path': media_path,
            'word_count': word_count,
            'detected_language': detected_language,
            'transcription_model': 'whisper-base',
            'tags': ['transcript', 'audio', detected_language]
        }

        # Create markdown content
        markdown_content = f"""---
{yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)}---

# {title}

## Metadata
- **Original File:** {filename}
- **Language:** {detected_language}
- **Word Count:** {word_count:,}
- **Transcribed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Source Document:** [{original_title or source_doc_id}](/document/{source_doc_id})

## Transcript

{transcript_text}

---

*Transcribed using Whisper (local model) - automatic speech recognition*
"""

        # Save to knowledge base
        output_dir = Path(f"knowledge_base/processed/transcripts")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{new_doc_id}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"✓ Transcript saved: {output_file}")

        # Update embeddings index
        try:
            from processors.embeddings_generator import update_index
            update_index()
            print("✓ Embeddings updated")
        except Exception as e:
            print(f"Warning: Could not update embeddings: {e}")

        return jsonify({
            'success': True,
            'title': title,
            'word_count': word_count,
            'new_doc_id': new_doc_id,
            'language': detected_language,
            'transcript': transcript_text
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visual-stats')
def api_visual_stats():
    """Get visual translator statistics"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Visual translator not available'}), 503

    # Count images
    media_base = Path("knowledge_base/media")
    total_images = 0
    analyzed_images = 0
    with_text = 0

    if media_base.exists():
        for source_dir in media_base.iterdir():
            if source_dir.is_dir():
                for doc_dir in source_dir.iterdir():
                    if doc_dir.is_dir():
                        doc_id = doc_dir.name

                        # Count images
                        for img_file in doc_dir.glob("*"):
                            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                total_images += 1

                        # Check if analyzed
                        kb_path = Path("knowledge_base/processed")
                        for md_file in kb_path.rglob("*.md"):
                            try:
                                frontmatter, _ = parse_markdown_file(md_file)
                                if frontmatter.get('id') == doc_id:
                                    if 'visual_analysis_date' in frontmatter:
                                        analyzed_images += 1
                                    if frontmatter.get('has_text'):
                                        with_text += 1
                            except:
                                continue

    return jsonify({
        'total_images': total_images,
        'analyzed': analyzed_images,
        'pending': total_images - analyzed_images,
        'with_text': with_text
    })

@app.route('/visual-translator-v2')
def visual_translator_v2():
    """New Lightroom-style visual translator with thumbnail grid"""
    return render_template('visual_translator_v2.html')

@app.route('/api/visual-translator/queries')
def api_visual_translator_queries():
    """Get all visual translator queries with metadata for thumbnail grid"""
    try:
        queries = []
        media_base = Path("knowledge_base/media")

        if media_base.exists():
            for source_dir in media_base.iterdir():
                if source_dir.is_dir():
                    for doc_dir in source_dir.iterdir():
                        if doc_dir.is_dir():
                            doc_id = doc_dir.name
                            source = source_dir.name

                            # Find markdown file for this doc
                            md_file = None
                            kb_path = Path("knowledge_base/processed")
                            for md in kb_path.rglob("*.md"):
                                try:
                                    frontmatter, body = parse_markdown_file(md)
                                    if frontmatter.get('id') == doc_id:
                                        md_file = md
                                        break
                                except:
                                    continue

                            if not md_file:
                                continue

                            # Find images in this doc directory
                            for img_file in doc_dir.glob("*"):
                                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                    # Get frontmatter and metadata
                                    try:
                                        frontmatter, body = parse_markdown_file(md_file)

                                        # Determine category (cognitive type)
                                        category = classify_document_cognitive_type(frontmatter, body)

                                        # Extract blockchain metadata
                                        blockchain_metadata = extract_blockchain_metadata(frontmatter, body)
                                        network = blockchain_metadata.get('network')

                                        # Determine status
                                        status = 'analyzed' if 'visual_analysis_date' in frontmatter else 'pending'

                                        # Get visual analysis if available
                                        description = frontmatter.get('visual_description', '')
                                        if not description and body:
                                            # Extract first paragraph as description
                                            lines = [l for l in body.split('\n') if l.strip() and not l.startswith('#')]
                                            if lines:
                                                description = lines[0][:200]

                                        query = {
                                            'id': f"{doc_id}_{img_file.name}",
                                            'title': frontmatter.get('title', img_file.name),
                                            'image_url': f"/media/{source}/{doc_id}/{img_file.name}",
                                            'category': category,
                                            'network': network,
                                            'status': status,
                                            'created_at': frontmatter.get('created_at', ''),
                                            'source_url': frontmatter.get('url', ''),
                                            'description': description,
                                            'blockchain_data': blockchain_metadata if blockchain_metadata.get('has_blockchain_data') else None
                                        }

                                        queries.append(query)

                                    except Exception as e:
                                        print(f"Error processing {img_file}: {e}")
                                        continue

        return jsonify({
            'success': True,
            'queries': queries,
            'total': len(queries)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visual-translator/analyze/<query_id>', methods=['POST'])
def api_visual_translator_analyze(query_id):
    """Analyze a single query"""
    try:
        # Parse query_id to get doc_id and image_filename
        parts = query_id.rsplit('_', 1)
        if len(parts) != 2:
            return jsonify({'error': 'Invalid query ID'}), 400

        doc_id, img_filename = parts

        # Find the image file
        media_base = Path("knowledge_base/media")
        img_file = None

        for source_dir in media_base.iterdir():
            if source_dir.is_dir():
                doc_dir = source_dir / doc_id
                if doc_dir.exists():
                    potential_img = doc_dir / img_filename
                    if potential_img.exists():
                        img_file = potential_img
                        break

        if not img_file:
            return jsonify({'error': 'Image not found'}), 404

        # Analyze the image
        if VISUAL_TRANSLATOR_AVAILABLE:
            analysis = analyze_image(str(img_file))

            # Update markdown file with analysis
            kb_path = Path("knowledge_base/processed")
            for md in kb_path.rglob("*.md"):
                try:
                    frontmatter, body = parse_markdown_file(md)
                    if frontmatter.get('id') == doc_id:
                        # Update frontmatter with analysis
                        frontmatter['visual_analysis_date'] = datetime.now().isoformat()
                        frontmatter['visual_description'] = analysis.get('description', '')
                        frontmatter['has_text'] = analysis.get('has_text', False)

                        # Write back
                        with open(md, 'w') as f:
                            f.write('---\n')
                            yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
                            f.write('---\n\n')
                            f.write(body)

                        break
                except:
                    continue

            return jsonify({
                'success': True,
                'analysis': analysis
            })
        else:
            return jsonify({'error': 'Visual translator not available'}), 503

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visual-translator/analyze-batch', methods=['POST'])
def api_visual_translator_analyze_batch():
    """Analyze multiple queries in batch"""
    try:
        data = request.json
        query_ids = data.get('ids', [])

        if not query_ids:
            return jsonify({'error': 'No query IDs provided'}), 400

        results = []
        for query_id in query_ids:
            # Call the single analyze endpoint
            try:
                # Parse query_id
                parts = query_id.rsplit('_', 1)
                if len(parts) != 2:
                    results.append({'id': query_id, 'success': False, 'error': 'Invalid ID'})
                    continue

                doc_id, img_filename = parts

                # Find and analyze image
                media_base = Path("knowledge_base/media")
                for source_dir in media_base.iterdir():
                    if source_dir.is_dir():
                        doc_dir = source_dir / doc_id
                        if doc_dir.exists():
                            potential_img = doc_dir / img_filename
                            if potential_img.exists() and VISUAL_TRANSLATOR_AVAILABLE:
                                analysis = analyze_image(str(potential_img))

                                # Update markdown
                                kb_path = Path("knowledge_base/processed")
                                for md in kb_path.rglob("*.md"):
                                    try:
                                        frontmatter, body = parse_markdown_file(md)
                                        if frontmatter.get('id') == doc_id:
                                            frontmatter['visual_analysis_date'] = datetime.now().isoformat()
                                            frontmatter['visual_description'] = analysis.get('description', '')
                                            frontmatter['has_text'] = analysis.get('has_text', False)

                                            with open(md, 'w') as f:
                                                f.write('---\n')
                                                yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
                                                f.write('---\n\n')
                                                f.write(body)

                                            break
                                    except:
                                        continue

                                results.append({'id': query_id, 'success': True})
                                break

            except Exception as e:
                results.append({'id': query_id, 'success': False, 'error': str(e)})

        return jsonify({
            'success': True,
            'results': results,
            'total': len(query_ids),
            'succeeded': sum(1 for r in results if r.get('success'))
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/sync-drive')
def sync_drive():
    """Show Google Drive sync interface"""
    return render_template('sync_drive.html')

@app.route('/api/check-drive-files')
def api_check_drive_files():
    """Check for new files in Google Drive without downloading"""
    try:
        # Import drive collector
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.drive_collector import get_drive_service, find_folder, list_files_in_folder, load_config

        # Load config
        config = load_config()
        drive_config = config.get('google_drive', {})

        if not drive_config.get('enabled', False):
            return jsonify({'error': 'Google Drive integration is disabled'}), 400

        # Get Drive service
        service = get_drive_service()

        # Find watch folder
        folder_name = drive_config.get('watch_folder_name', 'WEB3AUTOMATE')
        folder_id = drive_config.get('watch_folder_id')

        if not folder_id:
            folder_id = find_folder(service, folder_name)
            if not folder_id:
                return jsonify({'error': f'Folder "{folder_name}" not found in Google Drive'}), 404

        # List files
        supported_types = drive_config.get('supported_file_types', ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'md'])
        files = list_files_in_folder(service, folder_id, supported_types)

        # Load ignored files
        ignored_files_path = Path("config/ignored_drive_files.json")
        ignored_file_ids = set()
        if ignored_files_path.exists():
            try:
                with open(ignored_files_path, 'r') as f:
                    ignored_data = json.load(f)
                    ignored_file_ids = set(ignored_data.get('ignored_file_ids', []))
            except:
                pass

        # Filter out ignored files
        files = [f for f in files if f['id'] not in ignored_file_ids]

        # Check which files already exist
        kb_path = Path("knowledge_base/processed")
        existing_drive_ids = set()
        existing_filenames = {}

        for md_file in kb_path.rglob("*.md"):
            try:
                frontmatter, _ = parse_markdown_file(md_file)
                if frontmatter.get('source') == 'google_drive':
                    # Store drive file ID if available
                    if 'drive_file_id' in frontmatter:
                        existing_drive_ids.add(frontmatter['drive_file_id'])
                    # Store filename for similarity check
                    filename = frontmatter.get('filename', '')
                    if filename:
                        existing_filenames[filename.lower()] = {
                            'id': frontmatter.get('id'),
                            'title': frontmatter.get('filename'),
                            'created_at': frontmatter.get('created_at'),
                            'size': frontmatter.get('file_size', 0),
                            'source': frontmatter.get('source', 'google_drive')
                        }
            except:
                continue

        # Categorize files
        new_files = []
        duplicate_files = []
        similar_files = []

        for file_data in files:
            file_id = file_data['id']
            filename = file_data['name']
            filename_lower = filename.lower()

            # Check for exact duplicate (by file ID)
            if file_id in existing_drive_ids:
                duplicate_files.append({
                    'id': file_id,
                    'name': filename,
                    'size': file_data.get('size', 0),
                    'modified': file_data.get('modifiedTime', ''),
                    'reason': 'Already imported (same file ID)'
                })
            # Check for similar filename
            elif filename_lower in existing_filenames:
                similar_files.append({
                    'id': file_id,
                    'name': filename,
                    'size': file_data.get('size', 0),
                    'modified': file_data.get('modifiedTime', ''),
                    'existing': existing_filenames[filename_lower],
                    'reason': f'Similar to existing: {existing_filenames[filename_lower]["title"]}'
                })
            else:
                # Check for partial filename match (similarity)
                is_similar = False
                for existing_name, existing_data in existing_filenames.items():
                    # Simple similarity: check if 70% of words match
                    name_words = set(filename_lower.replace('.', ' ').split())
                    existing_words = set(existing_name.replace('.', ' ').split())

                    if name_words and existing_words:
                        common_words = name_words.intersection(existing_words)
                        similarity = len(common_words) / max(len(name_words), len(existing_words))

                        if similarity > 0.7:
                            similar_files.append({
                                'id': file_id,
                                'name': filename,
                                'size': file_data.get('size', 0),
                                'modified': file_data.get('modifiedTime', ''),
                                'existing': existing_data,
                                'reason': f'Possibly similar to: {existing_data["title"]} ({int(similarity*100)}% match)',
                                'similarity': similarity
                            })
                            is_similar = True
                            break

                if not is_similar:
                    new_files.append({
                        'id': file_id,
                        'name': filename,
                        'size': file_data.get('size', 0),
                        'modified': file_data.get('modifiedTime', ''),
                        'mime_type': file_data.get('mimeType', '')
                    })

        return jsonify({
            'success': True,
            'new_files': new_files,
            'similar_files': similar_files,
            'duplicate_files': duplicate_files,
            'total_checked': len(files)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-drive-files', methods=['POST'])
def api_import_drive_files():
    """Import selected files from Google Drive, merging with existing files when appropriate"""
    try:
        data = request.get_json()
        files = data.get('files', [])

        # Backward compatibility with old format
        if not files:
            file_ids = data.get('file_ids', [])
            files = [{'file_id': fid, 'merge': False, 'existing_id': None} for fid in file_ids]

        if not files:
            return jsonify({'error': 'No files selected'}), 400

        # Import drive collector
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.drive_collector import (
            get_drive_service, download_file, create_markdown,
            generate_id, determine_subject, load_config, move_file, find_folder
        )

        # Import processors
        from processors.attachment_processor import process_attachment

        # Load config
        config = load_config()
        drive_config = config.get('google_drive', {})
        service = get_drive_service()

        imported = []
        merged_count = 0
        errors = []

        for file_info in files:
            file_id = file_info['file_id']
            should_merge = file_info.get('merge', False)
            existing_id = file_info.get('existing_id')
            try:
                # Get file metadata
                file_data = service.files().get(
                    fileId=file_id,
                    fields='id, name, mimeType, modifiedTime, size'
                ).execute()

                filename = file_data['name']

                # Check if we should merge with existing file
                if should_merge and existing_id:
                    # Find existing markdown file
                    kb_path = Path("knowledge_base/processed")
                    existing_md_path = None

                    for md_file in kb_path.rglob("*.md"):
                        try:
                            frontmatter_data, _ = parse_markdown_file(md_file)
                            if frontmatter_data.get('id') == existing_id:
                                existing_md_path = md_file
                                break
                        except:
                            continue

                    if existing_md_path and existing_md_path.exists():
                        # Download new file to temp location
                        from datetime import datetime
                        temp_dir = Path('temp_downloads')
                        temp_dir.mkdir(exist_ok=True)
                        temp_file = temp_dir / filename

                        if download_file(service, file_id, temp_file):
                            # Extract new content based on file type
                            new_content_text = ""

                            if filename.lower().endswith('.pdf'):
                                try:
                                    import PyPDF2
                                    with open(temp_file, 'rb') as pdf_file:
                                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                                        new_content_text = "\n\n".join([page.extract_text() for page in pdf_reader.pages])
                                except:
                                    new_content_text = "[Could not extract PDF content]"
                            elif filename.lower().endswith(('.txt', '.md')):
                                with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    new_content_text = f.read()
                            else:
                                new_content_text = "[Binary file - content not extracted]"

                            # Read existing markdown
                            with open(existing_md_path, 'r', encoding='utf-8') as f:
                                existing_content = f.read()

                            # Parse existing markdown
                            if existing_content.startswith('---'):
                                parts = existing_content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter_data = yaml.safe_load(parts[1])
                                    existing_body = parts[2].strip()

                                    # Update frontmatter
                                    frontmatter_data['updated_at'] = datetime.now().isoformat()
                                    frontmatter_data['file_size'] = file_data.get('size', 0)
                                    frontmatter_data['drive_file_id'] = file_id

                                    # Append new content as amendment
                                    amendment_date = datetime.now().strftime("%Y-%m-%d")
                                    merged_body = f"{existing_body}\n\n---\n\n## Amendment - {amendment_date}\n\n**Source:** Updated version from Google Drive ({filename})\n\n{new_content_text}"

                                    # Write merged content
                                    merged_content = f"---\n{yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)}---\n{merged_body}"

                                    with open(existing_md_path, 'w', encoding='utf-8') as f:
                                        f.write(merged_content)

                                    merged_count += 1
                                    imported.append({
                                        'id': file_id,
                                        'name': filename,
                                        'doc_id': existing_id,
                                        'merged': True
                                    })

                            # Clean up temp file
                            temp_file.unlink()
                        else:
                            errors.append(f"Failed to download: {filename}")
                    else:
                        errors.append(f"Existing file not found for merge: {existing_id}")
                else:
                    # Standard import (new file)
                    doc_id = generate_id(filename, file_data['modifiedTime'])

                    # Download file
                    save_dir = Path(drive_config.get('save_files_dir', 'knowledge_base/attachments')) / doc_id
                    save_dir.mkdir(parents=True, exist_ok=True)
                    file_path = save_dir / filename

                    if download_file(service, file_id, file_path):
                        # Process attachment (extracts images, PDFs, etc.)
                        subject = determine_subject(filename)
                        md_path = process_attachment(file_path, subject, doc_id)

                        # Update frontmatter with drive file ID for duplicate detection
                        if md_path and md_path.exists():
                            with open(md_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            if content.startswith('---'):
                                parts = content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter_data = yaml.safe_load(parts[1])
                                    frontmatter_data['drive_file_id'] = file_id
                                    frontmatter_data['source'] = 'google_drive'

                                    new_content = f"---\n{yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)}---{parts[2]}"
                                    with open(md_path, 'w', encoding='utf-8') as f:
                                        f.write(new_content)

                        # Move to processed folder if configured
                        if drive_config.get('move_processed_files', False):
                            processed_folder_name = drive_config.get('processed_folder_name', 'Processed')
                            processed_folder_id = find_folder(service, processed_folder_name)

                            if not processed_folder_id:
                                from collectors.drive_collector import create_folder
                                processed_folder_id = create_folder(service, processed_folder_name)

                            if processed_folder_id:
                                watch_folder_id = drive_config.get('watch_folder_id')
                                move_file(service, file_id, processed_folder_id, watch_folder_id)

                        imported.append({
                            'id': file_id,
                            'name': filename,
                            'doc_id': doc_id,
                            'merged': False
                        })
                    else:
                        errors.append(f"Failed to download: {filename}")

            except Exception as e:
                errors.append(f"Error importing {file_id}: {str(e)}")
                import traceback
                traceback.print_exc()

        return jsonify({
            'success': True,
            'imported': imported,
            'merged': merged_count,
            'errors': errors
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ignore-drive-files', methods=['POST'])
def api_ignore_drive_files():
    """Add Drive file IDs to permanent ignore list"""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])

        if not file_ids:
            return jsonify({'error': 'No file IDs provided'}), 400

        # Load existing ignored files
        ignored_files_path = Path("config/ignored_drive_files.json")
        ignored_file_ids = []

        if ignored_files_path.exists():
            try:
                with open(ignored_files_path, 'r') as f:
                    ignored_data = json.load(f)
                    ignored_file_ids = ignored_data.get('ignored_file_ids', [])
            except:
                pass

        # Add new file IDs
        for file_id in file_ids:
            if file_id not in ignored_file_ids:
                ignored_file_ids.append(file_id)

        # Save updated list
        ignored_files_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ignored_files_path, 'w') as f:
            json.dump({
                'ignored_file_ids': ignored_file_ids,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

        return jsonify({
            'success': True,
            'ignored_count': len(file_ids),
            'total_ignored': len(ignored_file_ids)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Email Collector API Routes
# =============================================================================

@app.route('/api/email/sync', methods=['POST'])
def api_email_sync():
    """
    Trigger Gmail email sync to collect attachments.
    Searches for emails with subject filter and processes attachments.
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.email_collector import EmailCollector, GMAIL_OAUTH_AVAILABLE

        if not GMAIL_OAUTH_AVAILABLE:
            return jsonify({
                'error': 'Gmail OAuth libraries not available',
                'install_command': 'pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client'
            }), 400

        # Get optional parameters from request
        data = request.get_json() or {}
        subject_filter = data.get('subject_filter')
        max_results = data.get('max_results')

        # Initialize collector
        collector = EmailCollector()

        # Run sync
        results = collector.sync(
            subject_filter=subject_filter,
            max_results=max_results
        )

        return jsonify({
            'success': True,
            'attachments_processed': len(results),
            'results': results,
            'stats': collector.sync_stats
        })

    except FileNotFoundError as e:
        return jsonify({
            'error': 'Gmail credentials not configured',
            'details': str(e),
            'setup_required': True
        }), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/status')
def api_email_status():
    """
    Get Gmail sync status including last sync time and statistics.
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.email_collector import EmailCollector, GMAIL_OAUTH_AVAILABLE

        if not GMAIL_OAUTH_AVAILABLE:
            return jsonify({
                'configured': False,
                'oauth_available': False,
                'error': 'Gmail OAuth libraries not installed'
            })

        collector = EmailCollector()
        status = collector.get_status()

        # Check if credentials exist
        credentials_exist = collector.credentials_path.exists()
        token_exists = collector.token_path.exists()

        return jsonify({
            'configured': credentials_exist,
            'authenticated': token_exists,
            'oauth_available': True,
            'subject_filter': collector.subject_filter,
            'last_sync': status.get('last_sync'),
            'stats': status.get('stats', {})
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'configured': False,
            'error': str(e)
        })


@app.route('/api/email/test', methods=['POST'])
def api_email_test():
    """
    Test Gmail OAuth connection.
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.email_collector import EmailCollector, GMAIL_OAUTH_AVAILABLE

        if not GMAIL_OAUTH_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Gmail OAuth libraries not available',
                'install_command': 'pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client'
            }), 400

        collector = EmailCollector()
        result = collector.test_connection()

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/email/config', methods=['GET', 'POST'])
def api_email_config():
    """
    Get or update Gmail collector configuration.
    """
    try:
        config_path = Path("config/settings.json")

        if request.method == 'GET':
            # Return current Gmail config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                gmail_config = config.get('gmail', {})
                # Remove sensitive paths from response
                safe_config = {
                    'enabled': gmail_config.get('enabled', False),
                    'subject_filter': gmail_config.get('subject_filter', 'WEB3GISELAUTOMATE'),
                    'max_results': gmail_config.get('max_results', 50),
                    'save_attachments_dir': gmail_config.get('save_attachments_dir', 'knowledge_base/media/email_attachments')
                }
                return jsonify(safe_config)
            else:
                return jsonify({
                    'enabled': False,
                    'subject_filter': 'WEB3GISELAUTOMATE',
                    'max_results': 50
                })

        elif request.method == 'POST':
            # Update Gmail config
            data = request.get_json() or {}

            # Load existing config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            # Update gmail section
            if 'gmail' not in config:
                config['gmail'] = {}

            if 'enabled' in data:
                config['gmail']['enabled'] = data['enabled']
            if 'subject_filter' in data:
                config['gmail']['subject_filter'] = data['subject_filter']
            if 'max_results' in data:
                config['gmail']['max_results'] = int(data['max_results'])

            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            return jsonify({
                'success': True,
                'message': 'Gmail configuration updated'
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/email-setup')
def email_setup():
    """Gmail OAuth setup page"""
    return render_template('email_setup.html')


@app.route('/api/email/credentials', methods=['POST'])
def api_email_credentials():
    """
    Save Gmail OAuth credentials file.
    """
    try:
        data = request.get_json()
        credentials = data.get('credentials')

        if not credentials:
            return jsonify({'error': 'No credentials provided'}), 400

        # Validate credentials format
        if not credentials.get('installed') and not credentials.get('web'):
            return jsonify({'error': 'Invalid credentials format'}), 400

        # Save credentials to file
        credentials_path = Path("config/gmail_credentials.json")
        credentials_path.parent.mkdir(parents=True, exist_ok=True)

        with open(credentials_path, 'w') as f:
            json.dump(credentials, f, indent=2)

        return jsonify({
            'success': True,
            'message': 'Gmail credentials saved successfully'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/tags')
def tag_cloud():
    """Tag cloud visualization page"""
    # Gather all tags from all documents
    kb_path = Path("knowledge_base/processed")
    tag_counts = {}
    tag_to_docs = {}  # Map tags to document IDs
    tag_connections = {}  # Map tag relationships

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, _ = parse_markdown_file(md_file)
            doc_id = frontmatter.get('id', '')
            tags = frontmatter.get('tags', [])

            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                if tag not in tag_to_docs:
                    tag_to_docs[tag] = []
                tag_to_docs[tag].append(doc_id)

                # Build tag connections (tags that appear together)
                if tag not in tag_connections:
                    tag_connections[tag] = {}
                for other_tag in tags:
                    if other_tag != tag:
                        tag_connections[tag][other_tag] = tag_connections[tag].get(other_tag, 0) + 1
        except:
            continue

    # Sort tags by frequency
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    return render_template('tag_cloud.html',
                         tags=sorted_tags,
                         tag_to_docs=tag_to_docs,
                         tag_connections=tag_connections,
                         total_tags=len(tag_counts))

@app.route('/semantic-network')
def semantic_network():
    """Semantic network visualization page"""
    return render_template('semantic_network.html')

@app.route('/confidentiality')
def confidentiality_gate():
    """Confidentiality agreement gate for proprietary previews"""
    return render_template('confidentiality_gate.html')

@app.route('/api/nda/accept', methods=['POST'])
def record_nda_acceptance():
    """Record NDA acceptance for legal tracking"""
    try:
        data = request.get_json()
        acceptance_record = {
            'name': data.get('name'),
            'timestamp': data.get('timestamp'),
            'user_agent': data.get('userAgent'),
            'target_page': data.get('targetPage'),
            'ip_address': request.remote_addr,
            'recorded_at': datetime.now().isoformat()
        }

        # Store in a JSON file for record keeping
        nda_file = DATA_DIR / 'nda_acceptances.json'
        acceptances = []
        if nda_file.exists():
            try:
                acceptances = json.loads(nda_file.read_text())
            except:
                acceptances = []

        acceptances.append(acceptance_record)
        nda_file.write_text(json.dumps(acceptances, indent=2))

        return jsonify({'status': 'recorded', 'id': len(acceptances)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nda/records')
def get_nda_records():
    """Get all NDA acceptance records (admin only)"""
    nda_file = DATA_DIR / 'nda_acceptances.json'
    if nda_file.exists():
        try:
            acceptances = json.loads(nda_file.read_text())
            return jsonify({'acceptances': acceptances, 'count': len(acceptances)})
        except:
            return jsonify({'acceptances': [], 'count': 0})
    return jsonify({'acceptances': [], 'count': 0})

@app.route('/masters-spectral')
def masters_spectral():
    """NORTHSTAR 4D Spectral - 22 Masters visualization with halos and sparks"""
    return render_template('masters_point_cloud_v3_spectral.html')

@app.route('/masters-compare')
def masters_compare():
    """Masters comparison - V2 vs V3 spectral side-by-side"""
    return render_template('masters_point_cloud_compare.html')

@app.route('/masters-v2')
def masters_v2():
    """Masters V2 - Original electric glow visualization"""
    return render_template('masters_point_cloud_v2.html')

# ============================================
# ARC-8 FOUR MODE INTERFACES
# ============================================
# The Ark - Four modes: DOC-8, NFT-8, CRE-8, SOCI-8

@app.route('/doc8')
@app.route('/doc8/')
def doc8_archivist():
    """DOC-8 ARCHIVIST - Source Pre-Approval & Knowledge Bank"""
    return render_template('doc8_archivist.html')

@app.route('/nft8')
@app.route('/nft8/')
def nft8_collector():
    """NFT-8 COLLECTOR - Multi-chain NFT Portfolio & Provenance"""
    return render_template('nft8_collector.html')

@app.route('/cre8')
@app.route('/cre8/')
def cre8_artist():
    """CRE-8 ARTIST - Creative Generation from Data Bubbles"""
    return render_template('cre8_artist.html')

@app.route('/soci8')
@app.route('/soci8/')
def soci8_social():
    """SOCI-8 SOCIAL - Community, Sharing & Reputation"""
    return render_template('soci8_social.html')

@app.route('/itr8')
@app.route('/itr8/')
@app.route('/itr8/stream')
def itr8_thought_stream():
    """IT-R8 Thought Stream - Legacy redirect to CRE-8"""
    return render_template('cre8_artist.html')

@app.route('/in-testing')
@app.route('/in-testing/')
@app.route('/databank-preview')
def in_testing_databank():
    """IN-TESTING DATABANK - Preview of interconnected data visualization"""
    return render_template('in_testing_databank.html')

@app.route('/dataland')
@app.route('/dataland/')
@app.route('/dataland-preview')
@app.route('/moonlanguage-4d')
def dataland_preview():
    """DATALAND - 4D MOONLANGUAGE Symphony visualization"""
    return render_template('dataland_expert_preview.html')

@app.route('/api/doc8/research', methods=['POST'])
def doc8_research():
    """Execute research with pre-approved sources"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        sources = data.get('sources', [])
        depth = data.get('depth', 3)
        time_limit = data.get('timeLimit', 120)

        # Log research request
        research_log = {
            'query': query,
            'sources': sources,
            'depth': depth,
            'time_limit': time_limit,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr
        }

        # Store research log
        research_file = DATA_DIR / 'doc8_research_log.json'
        logs = []
        if research_file.exists():
            try:
                logs = json.loads(research_file.read_text())
            except:
                logs = []
        logs.append(research_log)
        research_file.write_text(json.dumps(logs, indent=2))

        # Return placeholder - actual research would be executed here
        return jsonify({
            'status': 'queued',
            'query': query,
            'sources_count': len(sources),
            'message': 'Research request logged. Full ULTRATHINK integration coming soon.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/module-sandbox')
def module_sandbox():
    """Module sandbox - testing environment for data visualization modules"""
    return render_template('module_sandbox.html')

@app.route('/point-cloud')
@app.route('/point-cloud/')
def point_cloud_index():
    """Point cloud paradigms selector"""
    return render_template('point_cloud/index.html')

@app.route('/point-cloud/<paradigm>')
def point_cloud_paradigm(paradigm):
    """Individual point cloud paradigm visualization"""
    valid_paradigms = ['temporal', 'conceptual', 'stewardship', 'river', 'resonance']
    if paradigm in valid_paradigms:
        return render_template(f'point_cloud/{paradigm}.html')
    return redirect('/point-cloud')

# ============================================
# IT-R8 SPATIAL CANVAS (Preview/Prototype)
# ============================================

@app.route('/spatial-canvas')
@app.route('/spatial-canvas/')
def spatial_canvas():
    """IT-R8 Spatial Canvas prototype - 3D bubble visualization"""
    return render_template('spatial_canvas.html')

@app.route('/api/export/itr8')
def export_itr8():
    """
    Export archive data as .itr8 format for IT-R8 Spatial Canvas.
    Returns JSON file download.
    """
    from datetime import datetime

    try:
        docs = get_all_documents()

        bubbles = []
        total_images = 0

        for doc in docs:
            bubble = {
                'id': doc.get('id', ''),
                'title': doc.get('title', 'Untitled'),
                'tags': doc.get('tags', []),
                'first_image': doc.get('first_image', ''),
                'media_count': doc.get('media_count', 0),
                'source': doc.get('source', 'unknown'),
                'url': doc.get('url', ''),
                'created_at': doc.get('created_at', '')
            }
            bubbles.append(bubble)
            total_images += doc.get('media_count', 0)

        export_data = {
            'name': 'ARCHIV-IT Export',
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'source': 'ARCHIV-IT',
            'bubbles': bubbles,
            'metadata': {
                'artist': 'Gisel Florez',
                'total_bubbles': len(bubbles),
                'total_images': total_images,
                'exported_from': 'http://localhost:5001'
            }
        }

        response = make_response(json.dumps(export_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=archivit-export-{datetime.now().strftime("%Y%m%d")}.itr8'

        return response

    except Exception as e:
        logger.error(f"Error exporting .itr8: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/point-cloud/data')
def api_point_cloud_data():
    """
    Return point cloud network data with temporal enrichment.
    Used by the temporal existence visualization.
    Merges blockchain data with knowledge base documents.
    """
    try:
        # Get blockchain network data
        blockchain_nodes = []
        blockchain_edges = []
        try:
            from collectors.network_data_builder import NetworkDataBuilder
            builder = NetworkDataBuilder(include_temporal=True)
            data = builder.build_from_database()
            blockchain_nodes = data.get('nodes', [])
            blockchain_edges = data.get('edges', [])
        except Exception as e:
            logger.warning(f"Could not load blockchain data: {e}")

        # Get knowledge base documents and add as nodes
        kb_documents = get_all_documents(limit=500, filter_type='all')
        kb_nodes = []
        kb_edges = []

        # Type colors for document nodes
        type_colors = {
            'blockchain': '#627EEA',
            'web_article': '#22c55e',
            'research': '#8b5cf6',
            'media': '#f59e0b',
            'conversation': '#3b82f6'
        }

        for doc in kb_documents:
            cognitive_type = doc.get('cognitive_type', 'web_article')
            color = type_colors.get(cognitive_type, '#22c55e')

            node = {
                'id': f"doc_{doc.get('id', '')}",
                'type': 'document',
                'identifier': doc.get('id', ''),
                'size': 12 if doc.get('has_visual') else 8,
                'color': color,
                'shape': 'sphere',
                'connections': len(doc.get('tags', [])),
                'data': {
                    'title': doc.get('title', 'Untitled'),
                    'source': doc.get('source', ''),
                    'tags': doc.get('tags', []),
                    'cognitive_type': cognitive_type,
                    'has_image': doc.get('has_visual', False),
                    'url': doc.get('marketplace_url', ''),
                    'created_at': doc.get('date', '')
                }
            }
            kb_nodes.append(node)

            # Create tag-based connections between documents
            for tag in doc.get('tags', []):
                for other_doc in kb_documents:
                    if other_doc.get('id') != doc.get('id') and tag in other_doc.get('tags', []):
                        edge = {
                            'source': f"doc_{doc.get('id', '')}",
                            'target': f"doc_{other_doc.get('id', '')}",
                            'type': 'same_tag',
                            'weight': 0.5,
                            'data': {'tag': tag}
                        }
                        kb_edges.append(edge)

        # Merge all nodes and edges
        all_nodes = blockchain_nodes + kb_nodes
        all_edges = blockchain_edges + kb_edges

        return jsonify({
            'success': True,
            'nodes': all_nodes,
            'edges': all_edges,
            'stats': {
                'total_nodes': len(all_nodes),
                'total_edges': len(all_edges),
                'nft_count': len([n for n in all_nodes if n.get('type') == 'nft']),
                'document_count': len(kb_nodes),
                'living_count': len([n for n in all_nodes if n.get('temporal', {}).get('is_living')])
            }
        })
    except Exception as e:
        logger.error(f"Error building point cloud data: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'nodes': [],
            'edges': []
        })

@app.route('/api/documents')
def api_documents():
    """Get all documents from knowledge base as JSON for visualizers.
    Used by spatial_canvas.html and other visualizers that need document data."""
    filter_type = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'date_desc')
    limit = request.args.get('limit', 200, type=int)

    documents = get_all_documents(limit=limit, filter_type=filter_type, sort_by=sort_by)

    # Enrich documents with first image for spatial visualizer
    for doc in documents:
        # Get first image from media_files or images list
        first_image = None
        if doc.get('media_files'):
            first_image = doc['media_files'][0]
        elif doc.get('images'):
            first_image = doc['images'][0]
        elif doc.get('image_urls'):
            first_image = doc['image_urls'][0]
        doc['first_image'] = first_image
        doc['media_count'] = len(doc.get('media_files', [])) + len(doc.get('images', []))

    return jsonify({
        'success': True,
        'documents': documents,
        'total': len(documents)
    })

@app.route('/api/documents-by-tag/<tag>')
def documents_by_tag(tag):
    """Get all documents with a specific tag"""
    kb_path = Path("knowledge_base/processed")
    documents = []

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            tags = frontmatter.get('tags', [])

            if tag in tags:
                # Extract images
                images = re.findall(r'!\[.*?\]\((.*?)\)', body)
                media_files = []

                doc_id = frontmatter.get('id', '')
                # Check all possible media directories
                media_base = Path("knowledge_base/media")
                if media_base.exists():
                    for media_type_dir in media_base.iterdir():
                        if media_type_dir.is_dir():
                            media_type = media_type_dir.name
                            doc_media_dir = media_type_dir / doc_id
                            if doc_media_dir.exists():
                                for img in doc_media_dir.glob("*"):
                                    if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                        media_files.append(f"{media_type}/{doc_id}/{img.name}")

                documents.append({
                    'id': doc_id,
                    'title': frontmatter.get('title', 'Untitled'),
                    'source': frontmatter.get('source', 'unknown'),
                    'date': frontmatter.get('created_at', ''),
                    'tags': tags,
                    'images': images,
                    'media_files': media_files
                })
        except:
            continue

    return jsonify({'tag': tag, 'documents': documents, 'count': len(documents)})

@app.route('/api/semantic-network')
def semantic_network_api():
    """
    Build and return semantic network graph data
    Returns nodes and edges representing cognitive data relationships
    """
    import gc
    import warnings

    # Suppress multiprocessing warnings that cause crashes on macOS
    warnings.filterwarnings('ignore', category=UserWarning, module='multiprocessing.resource_tracker')

    try:
        # Get all documents
        all_documents = get_all_documents(limit=1000, filter_type='all')

        # Use embeddings index for semantic similarity
        if not embeddings:
            return jsonify({
                'error': 'Embeddings not initialized',
                'nodes': [],
                'edges': []
            }), 500

        # Build semantic network with resource cleanup
        network = build_semantic_network(all_documents, embeddings)

        # Force garbage collection to clean up multiprocessing resources
        gc.collect()

        return jsonify(network)

    except Exception as e:
        print(f"Error building semantic network: {e}")
        import traceback
        traceback.print_exc()
        # Force cleanup on error
        gc.collect()
        return jsonify({
            'error': str(e),
            'nodes': [],
            'edges': []
        }), 500

@app.route('/api/blockchain/address/<address>')
def get_mints_by_address_api(address):
    """
    Get all NFT mints/documents associated with a blockchain address
    """
    try:
        all_documents = get_all_documents(limit=1000, filter_type='all')
        mints = get_mints_by_address(all_documents, address)

        return jsonify({
            'address': address,
            'count': len(mints),
            'mints': mints
        })
    except Exception as e:
        print(f"Error retrieving mints by address: {e}")
        return jsonify({'error': str(e), 'mints': []}), 500

@app.route('/api/blockchain/network/<network>')
def get_mints_by_network_api(network):
    """
    Get all NFT mints/documents from a specific blockchain network (ethereum/bitcoin/solana)
    """
    try:
        all_documents = get_all_documents(limit=1000, filter_type='all')
        mints = get_mints_by_network(all_documents, network)

        return jsonify({
            'network': network,
            'count': len(mints),
            'mints': mints
        })
    except Exception as e:
        print(f"Error retrieving mints by network: {e}")
        return jsonify({'error': str(e), 'mints': []}), 500

@app.route('/api/blockchain/addresses')
def get_all_addresses_api():
    """
    Get index of all blockchain addresses found in the knowledge base
    """
    try:
        all_documents = get_all_documents(limit=1000, filter_type='all')
        address_index = get_all_blockchain_addresses(all_documents)

        # Convert to list format for easier display
        addresses_list = []
        for address, docs in address_index.items():
            addresses_list.append({
                'address': address,
                'network': docs[0]['network'] if docs else 'unknown',
                'document_count': len(docs),
                'documents': docs
            })

        return jsonify({
            'total_addresses': len(addresses_list),
            'addresses': addresses_list
        })
    except Exception as e:
        print(f"Error retrieving blockchain addresses: {e}")
        return jsonify({'error': str(e), 'addresses': []}), 500

# ============================================================================
# NEW FEATURES - Blockchain Tracker, Sales Analytics, Collections, Press Kit
# ============================================================================

# Import new feature modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'collectors'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'analytics'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'export'))

from collectors.address_registry import AddressRegistry
from collectors.ethereum_tracker import EthereumTracker
from analytics.sales_db import get_sales_db
try:
    from export.press_kit_generator import PressKitGenerator
except ImportError:
    PressKitGenerator = None  # WeasyPrint not available

# Import collections_db directly to avoid conflict with built-in collections module
import importlib.util
collections_module_path = Path(__file__).parent.parent / 'collections' / 'collections_db.py'
spec = importlib.util.spec_from_file_location("collections_db", collections_module_path)
collections_db_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collections_db_module)
get_collections_db = collections_db_module.get_collections_db

# Initialize feature modules
address_registry = AddressRegistry()
eth_tracker = EthereumTracker()
sales_db = get_sales_db()
collections_db = get_collections_db()
press_kit_gen = PressKitGenerator()

# ============================================================================
# BLOCKCHAIN ADDRESS TRACKER ROUTES
# ============================================================================

@app.route('/blockchain-tracker')
def blockchain_tracker_ui():
    """Blockchain address tracker dashboard"""
    try:
        tracked_addresses = address_registry.get_all_addresses()
        stats = {
            'total_addresses': len(tracked_addresses),
            'by_network': {}
        }

        for addr in tracked_addresses:
            network = addr['network']
            stats['by_network'][network] = stats['by_network'].get(network, 0) + 1

        return render_template('blockchain_tracker.html',
                             addresses=tracked_addresses,
                             stats=stats)
    except Exception as e:
        return f"Error loading blockchain tracker: {e}", 500

@app.route('/api/tracker/addresses', methods=['GET', 'POST'])
def tracker_addresses_api():
    """Get or add tracked addresses"""
    if request.method == 'POST':
        data = request.json
        result = address_registry.add_address(
            address=data.get('address'),
            network=data.get('network'),
            label=data.get('label'),
            address_type=data.get('address_type', 'wallet'),
            notes=data.get('notes')
        )
        return jsonify(result)
    else:
        network = request.args.get('network')
        addresses = address_registry.get_all_addresses(network=network)
        return jsonify({'addresses': addresses})

@app.route('/api/tracker/addresses/<int:address_id>', methods=['GET', 'PUT', 'DELETE'])
def tracker_address_api(address_id):
    """Get, update, or delete a tracked address"""
    if request.method == 'GET':
        address = address_registry.get_address_by_id(address_id)
        return jsonify(address if address else {'error': 'Not found'}), 200 if address else 404

    elif request.method == 'PUT':
        data = request.json
        result = address_registry.update_address(
            address_id,
            label=data.get('label'),
            notes=data.get('notes'),
            sync_enabled=data.get('sync_enabled')
        )
        return jsonify(result)

    elif request.method == 'DELETE':
        result = address_registry.delete_address(address_id)
        return jsonify(result)

@app.route('/api/tracker/addresses/<int:address_id>/sync', methods=['POST'])
def tracker_sync_address(address_id):
    """Trigger sync for a specific address"""
    try:
        address_data = address_registry.get_address_by_id(address_id)

        if not address_data:
            return jsonify({'error': 'Address not found'}), 404

        if address_data['network'] == 'ethereum':
            result = eth_tracker.sync_address(
                address_id,
                address_data['address'],
                full_sync=request.json.get('full_sync', False)
            )
            return jsonify(result)
        else:
            return jsonify({'error': f"Network {address_data['network']} not yet supported"}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tracker/nfts')
def tracker_nfts_api():
    """Get all NFTs from tracked addresses"""
    try:
        from collectors.blockchain_db import get_db
        db = get_db()

        nfts = db.execute('''
            SELECT nm.*, ta.address, ta.label, ta.network
            FROM nft_mints nm
            JOIN tracked_addresses ta ON nm.address_id = ta.id
            ORDER BY nm.mint_timestamp DESC
            LIMIT 100
        ''')

        return jsonify({'nfts': nfts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SALES ANALYTICS ROUTES
# ============================================================================

@app.route('/sales-analytics')
def sales_analytics_ui():
    """Sales analytics dashboard"""
    try:
        stats = sales_db.get_stats()
        return render_template('sales_analytics.html', stats=stats)
    except Exception as e:
        return f"Error loading sales analytics: {e}", 500

@app.route('/api/sales/stats')
def sales_stats_api():
    """Get sales statistics"""
    try:
        stats = sales_db.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/nft/<contract>/<token_id>')
def sales_for_nft_api(contract, token_id):
    """Get cumulative sales for a specific NFT"""
    try:
        sales_data = sales_db.get_cumulative_sales_for_nft(contract, token_id)
        return jsonify(sales_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/collection/<contract>')
def sales_for_collection_api(contract):
    """Get cumulative sales for entire collection"""
    try:
        sales_data = sales_db.get_cumulative_sales_for_collection(contract)
        return jsonify(sales_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales/tracked-address/<int:address_id>')
def sales_for_tracked_address_api(address_id):
    """Get sales for NFTs from a tracked address"""
    try:
        sales = sales_db.get_sales_for_tracked_address(address_id)
        return jsonify({'sales': sales})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HISTORICAL PURCHASE ANALYSIS ROUTES
# ============================================================================

@app.route('/api/analytics/nft-history/<contract>/<token_id>')
def nft_history_api(contract, token_id):
    """Get full history and analysis for a specific NFT"""
    try:
        from analytics.historical_purchase_analyzer import HistoricalPurchaseAnalyzer
        analyzer = HistoricalPurchaseAnalyzer()
        history = analyzer.analyze_nft_full_history(contract, token_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/collection-buyers/<contract>')
def collection_buyers_api(contract):
    """Analyze all collectors for a collection"""
    try:
        from analytics.historical_purchase_analyzer import HistoricalPurchaseAnalyzer
        analyzer = HistoricalPurchaseAnalyzer()

        min_purchases = request.args.get('min_purchases', type=int, default=1)
        analysis = analyzer.analyze_collection_buyers(contract, min_purchases=min_purchases)

        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/collector-report/<address>')
def collector_report_api(address):
    """Generate detailed collector report for a buyer address"""
    try:
        from analytics.historical_purchase_analyzer import HistoricalPurchaseAnalyzer
        analyzer = HistoricalPurchaseAnalyzer()
        report = analyzer.generate_collector_report(address)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# EDITION CONSTELLATION ROUTES
# ============================================================================

@app.route('/edition-constellation')
def edition_constellation_ui():
    """Edition constellation visualization - collector distribution for multi-edition works"""
    return render_template('edition_constellation.html')

@app.route('/api/edition-works')
def edition_works_api():
    """Get all tracked edition works"""
    try:
        from analytics.edition_tracker import EditionTracker
        tracker = EditionTracker()
        editions = tracker.get_edition_works()

        # If no editions tracked yet, return sample data structure
        if not editions:
            # Check if we have any ERC-1155 tokens in the knowledge base
            sample_editions = []

            return jsonify({
                'editions': sample_editions,
                'message': 'No editions tracked yet. Use /api/edition-works/track to add one.'
            })

        return jsonify({'editions': editions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edition-works/track', methods=['POST'])
def track_edition_work_api():
    """Track a new edition work"""
    try:
        from analytics.edition_tracker import EditionTracker
        tracker = EditionTracker()

        data = request.json
        contract = data.get('contract')
        token_id = data.get('token_id')
        title = data.get('title')

        if not contract or token_id is None:
            return jsonify({'error': 'contract and token_id required'}), 400

        result = tracker.track_edition_work(contract, int(token_id), title)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edition-constellation/<contract>/<int:token_id>')
def edition_constellation_api(contract, token_id):
    """Get constellation visualization data for an edition"""
    try:
        from analytics.edition_tracker import EditionTracker
        tracker = EditionTracker()
        data = tracker.get_constellation_data(contract, token_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collector-network/<address>')
def collector_network_api(address):
    """Get a collector's network - other collectors they share editions with"""
    try:
        from analytics.edition_tracker import EditionTracker
        tracker = EditionTracker()
        data = tracker.get_collector_network(address)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PROVENANCE ARTERIES - Blockchain Flow Visualization
# ============================================================================

@app.route('/provenance-arteries')
def provenance_arteries_ui():
    """
    Provenance Arteries - Visualize blockchain transactions as circulatory system.
    Demonstrates PyTorch+WebGPU architecture concept with real blockchain data.
    """
    import sqlite3
    import json
    from datetime import datetime, timedelta

    db_path = 'db/blockchain_tracking.db'

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get collector statistics
        cursor.execute('''
            SELECT
                collector_address as address,
                COUNT(*) as count,
                SUM(purchase_price_native) as total_value,
                MAX(purchase_timestamp) as last_active
            FROM collectors
            GROUP BY collector_address
            ORDER BY count DESC
            LIMIT 50
        ''')
        collectors_raw = cursor.fetchall()

        # Process collectors
        collectors = []
        now = datetime.now()
        for row in collectors_raw:
            # Determine if active (activity within 90 days)
            active = False
            if row['last_active']:
                try:
                    last_dt = datetime.fromisoformat(row['last_active'].replace('Z', '+00:00'))
                    active = (now - last_dt.replace(tzinfo=None)).days < 90
                except:
                    active = False

            collectors.append({
                'address': row['address'],
                'count': row['count'],
                'total_value': row['total_value'] or 0,
                'active': active
            })

        # Get flow data (transactions grouped by collector)
        cursor.execute('''
            SELECT
                collector_address as to_addr,
                COUNT(*) as volume,
                SUM(purchase_price_native) as value,
                MAX(purchase_timestamp) as recent
            FROM collectors
            GROUP BY collector_address
            ORDER BY volume DESC
            LIMIT 50
        ''')
        flows_raw = cursor.fetchall()

        flows = []
        for row in flows_raw:
            # Calculate recency score (0-1)
            recency = 0.5
            if row['recent']:
                try:
                    last_dt = datetime.fromisoformat(row['recent'].replace('Z', '+00:00'))
                    days_ago = (now - last_dt.replace(tzinfo=None)).days
                    recency = max(0, 1 - (days_ago / 365))
                except:
                    recency = 0.5

            flows.append({
                'to': row['to_addr'],
                'volume': row['volume'],
                'value': row['value'] or 0,
                'recency': recency
            })

        # Get overall stats
        cursor.execute('SELECT COUNT(DISTINCT collector_address) FROM collectors')
        total_collectors = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_transactions = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM nft_mints')
        total_works = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(purchase_price_native) FROM collectors')
        total_flow = cursor.fetchone()[0] or 0

        conn.close()

        graph_data = {
            'collectors': collectors,
            'flows': flows
        }

        stats = {
            'collectors': total_collectors,
            'transactions': total_transactions,
            'works': total_works,
            'total_flow': total_flow
        }

        return render_template('provenance_arteries.html',
                               graph_data=json.dumps(graph_data),
                               stats=stats)

    except Exception as e:
        # Return with empty data if database not available
        graph_data = {'collectors': [], 'flows': []}
        stats = {'collectors': 0, 'transactions': 0, 'works': 0, 'total_flow': 0}
        return render_template('provenance_arteries.html',
                               graph_data=json.dumps(graph_data),
                               stats=stats)


@app.route('/verified-social')
def verified_social_ui():
    """
    Verified Social - Social network prototype with blockchain-verified trust.
    Demonstrates the Recursive Cross-Platform Verification System concept.
    """
    # Team data - pulled from team gallery for prototype
    artists = [
        {
            'name': 'Gisel Florez',
            'avatar': 'https://unavatar.io/twitter/web3gisel',
            'role': 'Creator · ARCHIV-IT Founder',
            'trust_score': 94
        },
        {
            'name': 'TokenFox',
            'avatar': 'https://unavatar.io/twitter/TokenFoxNFT',
            'role': 'Ordinals · Inscriptions',
            'trust_score': 91
        },
        {
            'name': 'Oona',
            'avatar': 'https://unavatar.io/twitter/madebyoona',
            'role': 'Performance Art',
            'trust_score': 89
        },
        {
            'name': 'Rare Scrilla',
            'avatar': 'https://unavatar.io/twitter/ScrillaVentura',
            'role': 'Audio NFT Pioneer',
            'trust_score': 96
        },
        {
            'name': 'XCOPY',
            'avatar': 'https://unavatar.io/twitter/XCOPYART',
            'role': 'Digital Artist',
            'trust_score': 99
        },
        {
            'name': 'Josie Bellini',
            'avatar': 'https://unavatar.io/twitter/josiebellini',
            'role': 'Artist · Multi-Chain',
            'trust_score': 93
        },
        {
            'name': 'Delta Sauce',
            'avatar': 'https://unavatar.io/twitter/deltasauceart',
            'role': 'Base · AI Art',
            'trust_score': 88
        },
        {
            'name': 'Lirona',
            'avatar': 'https://unavatar.io/twitter/laboratoireun',
            'role': 'Identity · Performance',
            'trust_score': 90
        }
    ]

    # Sample posts with provenance chains
    posts = [
        {
            'name': 'Gisel Florez',
            'avatar': 'https://unavatar.io/twitter/web3gisel',
            'timestamp': '2h ago',
            'trust_score': 94,
            'trust_level': 'VERIFIED',
            'text': 'Excited to share ARCHIV-IT - a new way to explore your creative history through deep provenance. Every connection tells a story.',
            'artwork': {
                'icon': '⬡',
                'platform': 'ARCHIV-IT',
                'chain': 'Multi-Chain'
            },
            'provenance': [
                {'label': 'Creator', 'type': 'creator'},
                {'label': 'Minted', 'type': ''},
                {'label': 'Current', 'type': 'current'}
            ],
            'likes': 47,
            'comments': 12
        },
        {
            'name': 'Rare Scrilla',
            'avatar': 'https://unavatar.io/twitter/ScrillaVentura',
            'timestamp': '4h ago',
            'trust_score': 96,
            'trust_level': 'VERIFIED',
            'text': 'The first collectible Audio NFT was minted on Bitcoin in 2016. The journey from then to the Ghostface Killah collab has been wild.',
            'artwork': {
                'icon': '🎵',
                'platform': 'Ordinals',
                'chain': 'Bitcoin'
            },
            'provenance': [
                {'label': 'Scrilla', 'type': 'creator'},
                {'label': 'RarePepe', 'type': ''},
                {'label': 'Ghostface', 'type': ''},
                {'label': 'Holder', 'type': 'current'}
            ],
            'likes': 234,
            'comments': 45
        },
        {
            'name': 'XCOPY',
            'avatar': 'https://unavatar.io/twitter/XCOPYART',
            'timestamp': '6h ago',
            'trust_score': 99,
            'trust_level': 'VERIFIED',
            'text': 'Death is inevitable. Art remains. The glitch persists.',
            'artwork': {
                'icon': '💀',
                'platform': 'SuperRare',
                'chain': 'Ethereum'
            },
            'provenance': [
                {'label': 'XCOPY', 'type': 'creator'},
                {'label': 'Cozomo', 'type': ''},
                {'label': 'Punks', 'type': ''},
                {'label': 'Current', 'type': 'current'}
            ],
            'likes': 892,
            'comments': 156
        },
        {
            'name': 'Oona',
            'avatar': 'https://unavatar.io/twitter/madebyoona',
            'timestamp': '8h ago',
            'trust_score': 89,
            'trust_level': 'VERIFIED',
            'text': 'Look, Touch, Own at Art Basel Miami - 300 touches generated live NFTs. The boundary between viewer and creator dissolves.',
            'artwork': {
                'icon': '👁',
                'platform': 'Art Basel',
                'chain': 'Live Performance'
            },
            'provenance': [
                {'label': 'Oona', 'type': 'creator'},
                {'label': 'Touch #1', 'type': ''},
                {'label': 'Touch #300', 'type': 'current'}
            ],
            'likes': 167,
            'comments': 34
        }
    ]

    return render_template('verified_social.html',
                           artists=artists,
                           posts=posts)


# ============================================================================
# COLLECTIONS & CREATIVE PERIODS ROUTES
# ============================================================================

@app.route('/collections')
def collections_ui():
    """Collections and creative periods dashboard"""
    try:
        stats = collections_db.get_stats()

        # Get recent collections
        conn = collections_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collections ORDER BY created_at DESC LIMIT 10')
        recent_collections = [dict(row) for row in cursor.fetchall()]

        # Get creative periods
        cursor.execute('SELECT * FROM creative_periods ORDER BY start_date DESC')
        periods = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return render_template('collections.html',
                             stats=stats,
                             collections=recent_collections,
                             periods=periods)
    except Exception as e:
        return f"Error loading collections: {e}", 500

@app.route('/api/collections', methods=['GET', 'POST'])
def collections_api():
    """Get or create collections"""
    if request.method == 'POST':
        data = request.json
        result = collections_db.create_collection(
            name=data.get('name'),
            description=data.get('description'),
            creator_address=data.get('creator_address'),
            collection_type=data.get('type', 'custom'),
            tags=data.get('tags', [])
        )
        return jsonify(result)
    else:
        conn = collections_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collections ORDER BY created_at DESC')
        collections = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'collections': collections})

@app.route('/api/collections/<int:collection_id>/works')
def collection_works_api(collection_id):
    """Get all works in a collection"""
    try:
        conn = collections_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT w.*,
                   (SELECT COUNT(*) FROM cross_references WHERE work_id = w.id) as ref_count
            FROM works w
            WHERE w.collection_id = ?
            ORDER BY w.creation_date DESC
        ''', (collection_id,))
        works = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({'works': works})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/works/<int:work_id>')
def work_detail_api(work_id):
    """Get work with all cross-references"""
    try:
        work_data = collections_db.get_work_with_references(work_id)
        return jsonify(work_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/periods', methods=['GET', 'POST'])
def periods_api():
    """Get or create creative periods"""
    if request.method == 'POST':
        data = request.json
        result = collections_db.create_creative_period(
            name=data.get('name'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            description=data.get('description'),
            auto_detected=data.get('auto_detected', False),
            dominant_subjects=data.get('dominant_subjects', []),
            dominant_tones=data.get('dominant_tones', []),
            dominant_mediums=data.get('dominant_mediums', [])
        )
        return jsonify(result)
    else:
        conn = collections_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM creative_periods ORDER BY start_date DESC')
        periods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'periods': periods})

@app.route('/api/periods/<int:period_id>/works')
def period_works_api(period_id):
    """Get all works in a creative period"""
    try:
        conn = collections_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT w.*, pw.confidence
            FROM works w
            JOIN period_works pw ON w.id = pw.work_id
            WHERE pw.period_id = ?
            ORDER BY w.creation_date
        ''', (period_id,))
        works = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({'works': works})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PRESS KIT EXPORT ROUTES
# ============================================================================

@app.route('/api/export/press-kit', methods=['POST'])
def export_press_kit_api():
    """Generate press kit PDF"""
    try:
        data = request.json

        # Generate press kit
        pdf_path = press_kit_gen.generate_pdf(
            title=data.get('title', 'Press Kit'),
            description=data.get('description', ''),
            works=data.get('works', []),
            artist_bio=data.get('artist_bio'),
            contact_info=data.get('contact_info')
        )

        if pdf_path:
            return jsonify({
                'success': True,
                'pdf_path': str(pdf_path),
                'download_url': f'/api/export/download/{pdf_path.name}'
            })
        else:
            return jsonify({'success': False, 'error': 'PDF generation failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/download/<filename>')
def download_press_kit(filename):
    """Download generated press kit"""
    try:
        return send_from_directory(
            press_kit_gen.output_dir,
            filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# ============================================================================

def get_stats_direct():
    """Get stats without Flask context"""
    kb_path = Path("knowledge_base/processed")
    total_docs = len(list(kb_path.rglob("*.md")))

    sources = {}
    visual_count = 0

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            source = frontmatter.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            images = re.findall(r'!\[.*?\]\((.*?)\)', body)
            media_dir = Path("knowledge_base/media/instagram") / frontmatter.get('id', '')
            if images or (media_dir.exists() and any(media_dir.glob("*"))):
                visual_count += 1
        except:
            continue

    return {
        'total_documents': total_docs,
        'visual_documents': visual_count,
        'sources': sources
    }

# ============================================================================
# OWNER-ONLY: ADMIN ROUTES (exclude from distributed builds)
# SECURITY: Protected by localhost-only access and optional token auth
# ============================================================================

from functools import wraps

def admin_required(f):
    """
    SECURITY: Decorator to protect admin routes.
    Requires EITHER:
    1. Request from localhost (127.0.0.1 or ::1)
    2. Valid ADMIN_TOKEN in Authorization header
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if request is from localhost
        remote_addr = request.remote_addr
        is_localhost = remote_addr in ('127.0.0.1', '::1', 'localhost')

        # Check for admin token
        admin_token = os.getenv('ADMIN_TOKEN')
        auth_header = request.headers.get('Authorization', '')
        has_valid_token = admin_token and auth_header == f'Bearer {admin_token}'

        if not is_localhost and not has_valid_token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Admin routes require localhost access or valid ADMIN_TOKEN'
            }), 403

        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/contacts')
@admin_required
def admin_contacts():
    """View all signup contacts - OWNER ONLY"""
    try:
        conn = sqlite3.connect('db/user_config.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT email, marketing_opt_in, email_confirmed, created_at, confirmed_at
            FROM user_config
            ORDER BY created_at DESC
        ''')
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'total': len(contacts),
            'opted_in': sum(1 for c in contacts if c.get('marketing_opt_in')),
            'confirmed': sum(1 for c in contacts if c.get('email_confirmed')),
            'contacts': contacts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/contacts/export')
@admin_required
def admin_contacts_export():
    """Export contacts as CSV - OWNER ONLY"""
    try:
        import csv
        from io import StringIO

        conn = sqlite3.connect('db/user_config.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT email, marketing_opt_in, email_confirmed, created_at, confirmed_at
            FROM user_config
            WHERE marketing_opt_in = 1
            ORDER BY created_at DESC
        ''')
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['email', 'marketing_opt_in', 'email_confirmed', 'created_at', 'confirmed_at'])
        writer.writeheader()
        writer.writerows(contacts)

        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=archiveit_contacts.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BADGE NFT & TRUST VERIFICATION SYSTEM
# ============================================================================

@app.route('/badge/<username>/<path:filename>')
def serve_badge(username, filename):
    """
    Serve signed badge SVG with verification

    URL format: /badge/{username}/{timestamp_b64}.{signature}.svg
    """
    from interface.badge_integrity import BadgeIntegrity, BadgeRenderer, badge_rate_limiter

    # Rate limiting
    client_ip = request.remote_addr
    if not badge_rate_limiter.is_allowed(client_ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    # Parse the signed URL
    url_path = f"/badge/{username}/{filename}"
    parsed = BadgeIntegrity.parse_badge_url(url_path)

    if not parsed:
        return jsonify({'error': 'Invalid badge URL format'}), 400

    # Verify signature
    is_valid, reason = BadgeIntegrity.verify_signature(
        parsed['username'],
        parsed['timestamp'],
        parsed['signature']
    )

    if not is_valid:
        # Return a "verification failed" badge
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1a1a24" stroke="#e53e3e" stroke-width="2"/>
            <text x="32" y="36" text-anchor="middle" fill="#e53e3e" font-size="10">INVALID</text>
        </svg>'''
        response = app.response_class(svg, mimetype='image/svg+xml')
        response.headers['X-Badge-Status'] = reason
        return response

    # Get user's trust score
    try:
        from interface.trust_system import get_trust_score_for_display
        score_data = get_trust_score_for_display()
        score = score_data.get('trust_score', 0)
    except:
        score = 0

    # Render the badge
    svg = BadgeRenderer.render_badge_svg(username, score)

    response = app.response_class(svg, mimetype='image/svg+xml')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['X-Badge-Status'] = 'valid'
    response.headers['X-Trust-Score'] = str(score)
    return response

@app.route('/badge/<username>/nft.svg')
def serve_nft_badge(username):
    """Serve badge for NFT metadata without signature requirement"""
    from interface.badge_integrity import BadgeRenderer
    from interface.badge_nft_system import AccumeterNFT

    # Check if user has registered NFT badge
    nft_system = AccumeterNFT()
    badge = nft_system.get_user_badge(username)

    if not badge:
        # Return placeholder for users without badge
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="28" fill="#1a1a24" stroke="#666" stroke-width="2"/>
            <text x="32" y="36" text-anchor="middle" fill="#666" font-size="8">NO BADGE</text>
        </svg>'''
        return app.response_class(svg, mimetype='image/svg+xml')

    # Get trust score
    try:
        from interface.trust_system import get_trust_score_for_display
        score_data = get_trust_score_for_display()
        score = score_data.get('trust_score', 0)
    except:
        score = 0

    svg = BadgeRenderer.render_badge_svg(username, score, size=512)
    response = app.response_class(svg, mimetype='image/svg+xml')
    response.headers['Cache-Control'] = 'public, max-age=300'  # 5 min cache for NFT
    return response

@app.route('/api/nft/metadata/<int:token_id>')
def nft_metadata(token_id):
    """
    ERC-721 tokenURI endpoint - returns NFT metadata JSON

    This is what the NFT contract's tokenURI() function points to.
    """
    from interface.badge_nft_system import AccumeterNFT

    nft_system = AccumeterNFT()

    # Find user by token ID
    for chain_key, reg in nft_system.registry.get('nfts', {}).items():
        if reg.get('token_id') == token_id:
            user_id = reg['user_id']

            # Get current trust score
            try:
                from interface.trust_system import get_trust_score_for_display
                score_data = get_trust_score_for_display()
                score = score_data.get('trust_score', 0)
                level = score_data.get('level', 'critical')
            except:
                score = 0
                level = 'critical'

            metadata = nft_system.generate_token_metadata(user_id, score, level)
            return jsonify(metadata)

    return jsonify({'error': 'Token not found'}), 404

@app.route('/api/badge/register', methods=['POST'])
def register_badge_nft():
    """Register a minted badge NFT"""
    from interface.badge_nft_system import AccumeterNFT

    data = request.get_json()
    required = ['user_id', 'wallet_address', 'chain', 'token_id', 'tx_hash']

    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    nft_system = AccumeterNFT()
    result = nft_system.register_accumeter_nft(
        user_id=data['user_id'],
        wallet_address=data['wallet_address'],
        chain=data['chain'],
        token_id=data['token_id'],
        tx_hash=data['tx_hash']
    )

    return jsonify(result)

@app.route('/api/badge/verify', methods=['POST'])
def verify_badge_ownership():
    """Verify wallet owns badge NFT for user"""
    from interface.badge_nft_system import AccumeterNFT

    data = request.get_json()
    if not data.get('user_id') or not data.get('wallet_address'):
        return jsonify({'error': 'user_id and wallet_address required'}), 400

    nft_system = AccumeterNFT()
    result = nft_system.verify_nft_ownership(
        data['user_id'],
        data['wallet_address']
    )

    return jsonify(result)

@app.route('/api/badge/generate', methods=['POST'])
def generate_verified_badge():
    """
    Full badge generation with dual verification

    Verifies NFT ownership + server registration before
    generating badge with IPFS audit trail.
    """
    from interface.badge_nft_system import DualVerificationSystem

    data = request.get_json()
    required = ['user_id', 'wallet_address']

    if not all(k in data for k in required):
        return jsonify({'error': 'user_id and wallet_address required'}), 400

    # Get current trust score
    try:
        from interface.trust_system import get_trust_score_for_display
        score_data = get_trust_score_for_display()
        score = score_data.get('trust_score', 0)
        level = score_data.get('level', 'critical')
        breakdown = score_data.get('breakdown', {})
    except:
        score = 0
        level = 'critical'
        breakdown = {}

    dual_system = DualVerificationSystem()
    result = dual_system.verify_and_generate_badge(
        user_id=data['user_id'],
        wallet_address=data['wallet_address'],
        trust_score=score,
        trust_level=level,
        breakdown=breakdown
    )

    return jsonify(result)

@app.route('/verify/<badge_id>')
def public_verification_page(badge_id):
    """
    Public verification page for badge

    Third parties can visit this to verify a badge is real.
    """
    from interface.badge_nft_system import AccumeterNFT, IPFSAuditTrail

    nft_system = AccumeterNFT()
    ipfs_audit = IPFSAuditTrail()

    # Find badge by ID
    badge_info = None
    user_id = None

    for uid, reg in nft_system.registry.get('users', {}).items():
        if reg.get('badge_id') == badge_id:
            badge_info = reg
            user_id = uid
            break

    if not badge_info:
        return render_template('verification_result.html',
                               verified=False,
                               message='Badge not found')

    # Get trust score history
    history = ipfs_audit.get_user_history(user_id, limit=10)

    # Get current score
    try:
        from interface.trust_system import get_trust_score_for_display
        score_data = get_trust_score_for_display()
    except:
        score_data = {'trust_score': 0, 'level': 'critical'}

    return render_template('verification_result.html',
                           verified=True,
                           badge_id=badge_id,
                           user_id=user_id,
                           chain=badge_info.get('chain'),
                           token_id=badge_info.get('token_id'),
                           registered_at=badge_info.get('registered_at'),
                           current_score=score_data.get('trust_score', 0),
                           current_level=score_data.get('level', 'critical'),
                           history_count=len(history),
                           explorer_url=nft_system.SUPPORTED_CHAINS.get(badge_info.get('chain'), {}).get('explorer', ''))

@app.route('/u/<username>')
def public_profile(username):
    """
    Public profile page showing trust badge

    This is what users link to from their Twitter bio.
    """
    from interface.badge_nft_system import DualVerificationSystem
    from interface.badge_integrity import BadgeIntegrity

    dual_system = DualVerificationSystem()
    public_info = dual_system.get_public_verification(username)

    # Generate signed badge URL
    badge_url = BadgeIntegrity.generate_badge_url(username,
                                                   base_url=request.host_url.rstrip('/'))

    # Get current trust score
    try:
        from interface.trust_system import get_trust_score_for_display
        score_data = get_trust_score_for_display()
    except:
        score_data = {'trust_score': 0, 'level': 'critical'}

    return render_template('public_profile.html',
                           username=username,
                           has_badge=public_info.get('has_badge', False),
                           badge_info=public_info,
                           badge_url=badge_url,
                           trust_score=score_data.get('trust_score', 0),
                           trust_level=score_data.get('level', 'critical'))

@app.route('/api/badge/url')
def get_badge_url():
    """Get a signed badge URL for embedding"""
    from interface.badge_integrity import BadgeIntegrity

    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400

    base_url = request.host_url.rstrip('/')
    url = BadgeIntegrity.generate_badge_url(username, base_url)

    return jsonify({
        'url': url,
        'embed_code': f'<img src="{url}" alt="ACU-METER" />',
        'markdown': f'![ACU-METER]({url})',
        'expires_in': '24 hours'
    })

@app.route('/api/ipfs/snapshot', methods=['POST'])
def create_ipfs_snapshot():
    """Create an IPFS snapshot of current trust score"""
    from interface.badge_nft_system import IPFSAuditTrail

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    # Get current trust data
    try:
        from interface.trust_system import get_trust_score_for_display
        score_data = get_trust_score_for_display()
    except:
        return jsonify({'error': 'Could not get trust score'}), 500

    ipfs_audit = IPFSAuditTrail()
    snapshot = ipfs_audit.create_snapshot(
        user_id=user_id,
        trust_score=score_data.get('trust_score', 0),
        trust_level=score_data.get('level', 'critical'),
        breakdown=score_data.get('breakdown', {})
    )

    return jsonify({
        'success': True,
        'snapshot': snapshot,
        'message': 'Snapshot created (local storage - IPFS pinning requires service integration)'
    })

@app.route('/api/ipfs/history/<user_id>')
def get_ipfs_history(user_id):
    """Get trust score history from IPFS snapshots"""
    from interface.badge_nft_system import IPFSAuditTrail

    limit = request.args.get('limit', 30, type=int)

    ipfs_audit = IPFSAuditTrail()
    history = ipfs_audit.get_user_history(user_id, limit=limit)

    return jsonify({
        'user_id': user_id,
        'snapshots': history,
        'count': len(history)
    })

# ============================================================================
# BADGE TIER UPGRADE ROUTES
# ============================================================================

@app.route('/upgrade-badge')
def badge_upgrade_page():
    """Badge tier selection and upgrade page"""
    from interface.badge_tiers import BadgeTierSystem, get_tier_comparison

    # Get current user info
    user_db = UserConfigDB()
    user = user_db.get_primary_user()
    artist = user_db.get_current_artist() if user else None
    user_id = artist.get('display_name', 'user') if artist else 'user'

    tier_system = BadgeTierSystem()
    current_tier_info = tier_system.get_user_tier(user_id)

    # Count current wallets from artist's minting addresses
    wallets_used = 1
    if artist:
        addresses = user_db.get_minting_addresses(user.get('id'))
        wallets_used = len(addresses) if addresses else 1

    return render_template('badge_upgrade.html',
                           current_tier=current_tier_info['tier'],
                           current_tier_name=current_tier_info['tier_name'],
                           wallet_limit=current_tier_info['wallet_limit'],
                           wallets_used=wallets_used,
                           tier_comparison=get_tier_comparison())

@app.route('/setup/unlock-standard')
def unlock_standard_page():
    """Standard tier unlock flow - add link to Twitter bio"""
    user_db = UserConfigDB()
    artist = user_db.get_current_artist()
    username = artist.get('display_name', 'your-username') if artist else 'your-username'

    # Generate the profile URL they need to add
    profile_url = f"{request.host_url.rstrip('/')}/u/{username}"

    return render_template('public_profile_unlock.html',
                           username=username,
                           profile_url=profile_url,
                           tier='standard')

@app.route('/setup/unlock-ultra')
def unlock_ultra_page():
    """Accumeter Certified unlock flow - mint NFT"""
    from interface.badge_nft_system import AccumeterNFT

    user_db = UserConfigDB()
    user = user_db.get_primary_user()
    artist = user_db.get_current_artist()
    username = artist.get('display_name', 'user') if artist else 'user'

    # Get first wallet address
    wallet = None
    if user:
        addresses = user_db.get_minting_addresses(user.get('id'))
        if addresses:
            wallet = addresses[0].get('address')

    nft_system = AccumeterNFT()

    return render_template('unlock_ultra.html',
                           username=username,
                           wallet_address=wallet,
                           supported_chains=nft_system.SUPPORTED_CHAINS)

@app.route('/setup/upgrade-enterprise', methods=['GET', 'POST'])
def upgrade_enterprise_page():
    """Enterprise tier upgrade - contact/agreement form"""
    from interface.badge_tiers import BadgeTierSystem

    user_db = UserConfigDB()
    user = user_db.get_primary_user()
    user_email = user.get('email') if user else None

    submitted = False

    if request.method == 'POST':
        # Process contact form submission
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        company = request.form.get('company', '').strip()
        message = request.form.get('message', '').strip()

        if name and email:
            # Log enterprise inquiry (in production, send email/store in DB)
            logger.info(f"Enterprise inquiry: {name} ({email}) - {company}")

            # Store inquiry locally for now
            inquiry_file = Path("knowledge_base/enterprise_inquiries.json")
            inquiry_file.parent.mkdir(parents=True, exist_ok=True)

            inquiries = []
            if inquiry_file.exists():
                try:
                    with open(inquiry_file, 'r') as f:
                        inquiries = json.load(f)
                except:
                    inquiries = []

            inquiries.append({
                'name': name,
                'email': email,
                'company': company,
                'message': message,
                'submitted_at': datetime.now().isoformat()
            })

            with open(inquiry_file, 'w') as f:
                json.dump(inquiries, f, indent=2)

            submitted = True

    return render_template('upgrade_enterprise.html',
                           user_email=user_email,
                           submitted=submitted)

@app.route('/setup/upgrade-whiteglove')
def upgrade_whiteglove_page():
    """White Glove tier - redirects to self-hosted setup (required)"""
    # White Glove requires self-hosted API, so we show info page
    # that links to the self-hosted setup wizard
    return render_template('upgrade_whiteglove.html')

@app.route('/setup/self-hosted')
def self_hosted_setup_page():
    """Self-hosted API setup flow"""
    from interface.badge_tiers import BadgeTierSystem

    user_db = UserConfigDB()
    artist = user_db.get_current_artist()
    user_id = artist.get('display_name', 'user') if artist else 'user'

    tier_system = BadgeTierSystem()
    is_self_hosted = tier_system.is_self_hosted(user_id)
    current_endpoint = tier_system.get_api_endpoint(user_id)

    return render_template('self_hosted_setup.html',
                           is_self_hosted=is_self_hosted,
                           current_endpoint=current_endpoint)

@app.route('/api/self-hosted/test', methods=['POST'])
def api_self_hosted_test():
    """Test self-hosted API endpoint connectivity"""
    import requests

    data = request.get_json()
    endpoint = data.get('endpoint', '').strip()

    if not endpoint:
        return jsonify({'success': False, 'error': 'Endpoint required'}), 400

    # Validate URL format
    if not endpoint.startswith('https://'):
        return jsonify({'success': False, 'error': 'HTTPS required'}), 400

    # Test endpoint connectivity
    try:
        test_url = endpoint.rstrip('/') + '/health'
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Connection successful'})
        else:
            return jsonify({'success': False, 'error': f'Status {response.status_code}'})
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Connection timeout'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot reach endpoint'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/self-hosted/activate', methods=['POST'])
def api_self_hosted_activate():
    """Activate or deactivate self-hosted API"""
    from interface.badge_tiers import BadgeTierSystem

    data = request.get_json()
    endpoint = data.get('endpoint', '').strip()
    enabled = data.get('enabled', True)

    if enabled and not endpoint:
        return jsonify({'success': False, 'error': 'Endpoint required'}), 400

    user_db = UserConfigDB()
    artist = user_db.get_current_artist()
    user_id = artist.get('display_name', 'user') if artist else 'user'

    tier_system = BadgeTierSystem()
    result = tier_system.set_self_hosted(user_id, enabled, endpoint if enabled else None)

    return jsonify(result)

@app.route('/api/tier/upgrade-standard', methods=['POST'])
def api_upgrade_standard():
    """Verify Twitter bio and upgrade to Standard tier"""
    from interface.badge_tiers import BadgeTierSystem

    data = request.get_json()
    twitter_handle = data.get('twitter_handle')

    if not twitter_handle:
        return jsonify({'error': 'twitter_handle required'}), 400

    user_db = UserConfigDB()
    artist = user_db.get_current_artist()
    user_id = artist.get('display_name', 'user') if artist else 'user'
    expected_url = f"{request.host_url.rstrip('/')}/u/{user_id}"

    # In production, we'd actually check Twitter API
    # For now, we trust the client's verification claim
    verification_proof = {
        'twitter_handle': twitter_handle,
        'expected_url': expected_url,
        'verified_at': datetime.now().isoformat(),
        'method': 'manual_claim'  # Would be 'api_verified' in production
    }

    tier_system = BadgeTierSystem()
    result = tier_system.upgrade_to_standard(user_id, verification_proof)

    return jsonify(result)

@app.route('/api/tier/upgrade-ultra', methods=['POST'])
def api_upgrade_ultra():
    """Register NFT and upgrade to Accumeter Certified"""
    from interface.badge_tiers import BadgeTierSystem
    from interface.badge_nft_system import AccumeterNFT

    data = request.get_json()
    required = ['wallet_address', 'chain', 'token_id', 'tx_hash']

    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    user_db = UserConfigDB()
    artist = user_db.get_current_artist()
    user_id = artist.get('display_name', 'user') if artist else 'user'

    # Register NFT first
    nft_system = AccumeterNFT()
    nft_result = nft_system.register_accumeter_nft(
        user_id=user_id,
        wallet_address=data['wallet_address'],
        chain=data['chain'],
        token_id=data['token_id'],
        tx_hash=data['tx_hash']
    )

    if nft_result.get('error'):
        return jsonify(nft_result), 400

    # Upgrade tier
    tier_system = BadgeTierSystem()
    result = tier_system.upgrade_to_ultra(user_id, data)

    result['badge_id'] = nft_result.get('badge_id')
    return jsonify(result)

@app.route('/api/tier/current')
def api_current_tier():
    """Get current user's tier info"""
    from interface.badge_tiers import BadgeTierSystem

    user_db = UserConfigDB()
    user = user_db.get_primary_user()
    artist = user_db.get_current_artist()
    user_id = artist.get('display_name', 'user') if artist else 'user'

    tier_system = BadgeTierSystem()
    tier_info = tier_system.get_user_tier(user_id)

    # Add wallet count from minting addresses
    wallets_used = 1
    if user:
        addresses = user_db.get_minting_addresses(user.get('id'))
        wallets_used = len(addresses) if addresses else 1

    tier_info['wallets_used'] = wallets_used
    tier_info['can_add_wallet'] = tier_system.can_add_wallet(
        user_id,
        wallets_used
    )

    return jsonify(tier_info)

@app.route('/api/tier/comparison')
def api_tier_comparison():
    """Get tier comparison data for display"""
    from interface.badge_tiers import get_tier_comparison
    return jsonify(get_tier_comparison())

# ============================================================================
# LIVING WORKS API - Temporal NFT Tracking Endpoints
# ============================================================================

def _get_living_works_analyzer():
    """
    Get or initialize the LivingWorksAnalyzer.
    Returns None if initialization fails.
    """
    try:
        from collectors.living_works_tracker import LivingWorksAnalyzer
        return LivingWorksAnalyzer()
    except Exception as e:
        logger.error(f"Failed to initialize LivingWorksAnalyzer: {e}")
        return None

def _get_nft_id_from_contract_token(contract: str, token_id: str):
    """
    Look up the internal nft_id from contract address and token_id.
    Returns None if not found.
    """
    try:
        from collectors.blockchain_db import get_db
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM nft_mints
            WHERE contract_address = ? AND token_id = ?
        ''', (contract, str(token_id)))
        result = cursor.fetchone()
        conn.close()
        return result['id'] if result else None
    except Exception as e:
        logger.error(f"Error looking up NFT ID: {e}")
        return None

@app.route('/api/nft/<contract>/<token_id>/history')
def api_nft_history(contract, token_id):
    """
    Get historical states of an NFT.

    Returns all tokenURI changes, reveals, and metadata updates over time.
    Uses HistoricalStateTracker.get_token_uri_history()

    Response: {success, states: [{block, timestamp, uri, metadata}]}
    """
    try:
        from collectors.living_works_tracker import HistoricalStateTracker

        tracker = HistoricalStateTracker()

        # Convert token_id to int
        try:
            token_id_int = int(token_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid token_id - must be an integer'
            }), 400

        # Get historical states
        history = tracker.get_token_uri_history(contract, token_id_int)

        # Format response
        states = []
        for state in history:
            states.append({
                'block': state.get('block_number'),
                'timestamp': state.get('timestamp'),
                'uri': state.get('token_uri'),
                'metadata': state.get('metadata'),
                'image': state.get('image'),
                'state_type': state.get('state_type'),
                'state_number': state.get('state_number')
            })

        return jsonify({
            'success': True,
            'contract': contract,
            'token_id': token_id,
            'states': states,
            'total_states': len(states),
            'is_mutable': len(states) > 1
        })

    except Exception as e:
        logger.error(f"Error fetching NFT history for {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nft/<contract>/<token_id>/events')
def api_nft_events(contract, token_id):
    """
    Get future scheduled events for an NFT.

    Detects timed reveals, phase changes, expirations, etc.
    Uses FutureEventDetector.build_event_calendar() filtered to this NFT.

    Response: {success, events: [{type, date, description}]}
    """
    try:
        from collectors.living_works_tracker import FutureEventDetector

        detector = FutureEventDetector()

        # Convert token_id to int
        try:
            token_id_int = int(token_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid token_id - must be an integer'
            }), 400

        # Analyze contract for time-based logic
        contract_events = detector.analyze_contract_for_time_logic(contract)

        # Get metadata from database to check for metadata-based events
        metadata = {}
        try:
            from collectors.blockchain_db import get_db
            db = get_db()
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT metadata_json FROM nft_mints
                WHERE contract_address = ? AND token_id = ?
            ''', (contract, str(token_id)))
            result = cursor.fetchone()
            conn.close()
            if result and result['metadata_json']:
                metadata = json.loads(result['metadata_json'])
        except Exception as e:
            logger.debug(f"Could not fetch metadata for event detection: {e}")

        # Extract metadata events
        metadata_events = detector.extract_metadata_time_events(metadata)

        # Combine and filter to future events
        events = []

        # Add contract-level future events
        for event in contract_events.get('future_events', []):
            events.append({
                'type': event.get('event_type', 'scheduled_time'),
                'date': event.get('scheduled_time'),
                'timestamp': event.get('timestamp'),
                'description': f"Contract scheduled event at slot {event.get('slot', 'unknown')}",
                'source': 'contract',
                'countdown_seconds': event.get('countdown_seconds')
            })

        # Add metadata-level future events
        for event in metadata_events:
            if event.get('is_future'):
                events.append({
                    'type': event.get('event_type', 'scheduled_event'),
                    'date': event.get('date'),
                    'timestamp': event.get('timestamp'),
                    'description': f"Metadata event: {event.get('field', 'unknown')}",
                    'source': 'metadata'
                })

        # Sort by timestamp
        events.sort(key=lambda x: x.get('timestamp', 0))

        return jsonify({
            'success': True,
            'contract': contract,
            'token_id': token_id,
            'has_time_logic': contract_events.get('has_time_logic', False),
            'events': events,
            'total_events': len(events)
        })

    except Exception as e:
        logger.error(f"Error fetching NFT events for {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nft/<contract>/<token_id>/live')
def api_nft_live_state(contract, token_id):
    """
    Get current live state for reactive/living NFTs.

    Captures current state including oracle values, chain state, and metadata.
    Uses LiveWorkTracker.capture_live_state()

    Response: {success, state: {timestamp, metadata, inputs, screenshot_cid}}
    """
    try:
        from collectors.living_works_tracker import LiveWorkTracker

        tracker = LiveWorkTracker()

        # Convert token_id to int
        try:
            token_id_int = int(token_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid token_id - must be an integer'
            }), 400

        # Identify reactivity type first
        reactivity = tracker.identify_reactivity_type(contract)

        # Capture current live state
        capture = tracker.capture_live_state(contract, token_id_int, trigger='api_request')

        # Format response
        state = {
            'timestamp': capture.get('captured_at'),
            'block_height': capture.get('block_height'),
            'metadata': capture.get('metadata_snapshot'),
            'token_uri': capture.get('token_uri'),
            'inputs': {
                'chain_state': capture.get('chain_state', {}),
                'oracle_values': capture.get('oracle_values', {})
            },
            'capture_id': capture.get('capture_id'),
            'screenshot_cid': None  # Would be populated if screenshot capture is implemented
        }

        return jsonify({
            'success': True,
            'contract': contract,
            'token_id': token_id,
            'is_reactive': reactivity.get('is_reactive', False),
            'reactivity_types': reactivity.get('types', []),
            'update_frequency': reactivity.get('update_frequency'),
            'data_sources': reactivity.get('data_sources', []),
            'state': state
        })

    except Exception as e:
        logger.error(f"Error fetching live state for {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/calendar')
def api_nft_calendar():
    """
    Get all upcoming events across all tracked NFTs.

    Builds a calendar of scheduled reveals, phase changes, expirations, etc.
    Uses FutureEventDetector.build_event_calendar()

    Response: {success, events: [{nft_id, contract, token_id, type, date, description}]}
    """
    try:
        from collectors.living_works_tracker import FutureEventDetector

        detector = FutureEventDetector()

        # Get optional query parameters
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        contracts_param = request.args.get('contracts')
        contracts = contracts_param.split(',') if contracts_param else None

        # Build event calendar
        calendar = detector.build_event_calendar(
            contracts=contracts,
            include_past=include_past
        )

        # Flatten calendar into events list
        events = []
        for date, date_events in calendar.items():
            for item in date_events:
                nft = item.get('nft', {})
                event = item.get('event', {})
                events.append({
                    'nft_id': None,  # Would need DB lookup
                    'contract': nft.get('contract'),
                    'token_id': nft.get('token_id'),
                    'nft_name': nft.get('name'),
                    'type': event.get('event_type', 'unknown'),
                    'date': date,
                    'timestamp': event.get('timestamp'),
                    'description': event.get('description') or f"{event.get('event_type', 'Event')} for {nft.get('name', 'NFT')}",
                    'source': event.get('source', 'unknown')
                })

        # Sort by timestamp
        events.sort(key=lambda x: x.get('timestamp', 0))

        # Group by date for display
        events_by_date = {}
        for event in events:
            date = event.get('date', 'unknown')
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)

        return jsonify({
            'success': True,
            'events': events,
            'events_by_date': events_by_date,
            'total_events': len(events),
            'date_count': len(events_by_date)
        })

    except Exception as e:
        logger.error(f"Error building event calendar: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nft/<contract>/<token_id>/capture', methods=['POST'])
def api_nft_capture(contract, token_id):
    """
    Trigger a manual capture of current NFT state.

    Captures and stores the current live state for archival purposes.
    Uses LiveWorkTracker.capture_live_state() and stores result in nft_live_captures table.

    Response: {success, capture_id, cid}
    """
    try:
        from collectors.living_works_tracker import LiveWorkTracker

        tracker = LiveWorkTracker()

        # Convert token_id to int
        try:
            token_id_int = int(token_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid token_id - must be an integer'
            }), 400

        # Get optional trigger description from request body
        data = request.get_json() or {}
        trigger = data.get('trigger', 'manual_api')

        # Capture current state
        capture = tracker.capture_live_state(contract, token_id_int, trigger=trigger)

        # Look up internal NFT ID for database storage
        nft_id = _get_nft_id_from_contract_token(contract, token_id)

        # Store capture in database
        capture_db_id = None
        if nft_id:
            try:
                capture_db_id = tracker.save_live_capture(nft_id, capture)
            except Exception as e:
                logger.warning(f"Could not save capture to database: {e}")

        # Generate a pseudo-CID (in production, this would be IPFS)
        import hashlib
        capture_json = json.dumps(capture, sort_keys=True, default=str)
        pseudo_cid = 'bafk' + hashlib.sha256(capture_json.encode()).hexdigest()[:52]

        return jsonify({
            'success': True,
            'contract': contract,
            'token_id': token_id,
            'capture_id': capture.get('capture_id'),
            'db_id': capture_db_id,
            'cid': pseudo_cid,
            'captured_at': capture.get('captured_at'),
            'block_height': capture.get('block_height'),
            'trigger': trigger
        })

    except Exception as e:
        logger.error(f"Error capturing state for {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nft/<contract>/<token_id>/temporal')
def api_nft_temporal_analysis(contract, token_id):
    """
    Get complete temporal analysis of an NFT.

    Comprehensive analysis including past states, current reactivity, and future events.
    Uses LivingWorksAnalyzer.analyze_nft()

    Response: Full temporal analysis including past, present, future data
    """
    try:
        analyzer = _get_living_works_analyzer()

        if not analyzer:
            return jsonify({
                'success': False,
                'error': 'LivingWorksAnalyzer not available'
            }), 500

        # Convert token_id to int
        try:
            token_id_int = int(token_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid token_id - must be an integer'
            }), 400

        # Run complete temporal analysis
        analysis = analyzer.analyze_nft(contract, token_id_int)

        return jsonify({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"Error analyzing NFT temporally {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nft/<contract>/<token_id>/captures')
def api_nft_capture_history(contract, token_id):
    """
    Get capture history for an NFT.

    Returns all previously captured live states.

    Response: {success, captures: [...]}
    """
    try:
        from collectors.living_works_tracker import LiveWorkTracker

        tracker = LiveWorkTracker()

        # Look up internal NFT ID
        nft_id = _get_nft_id_from_contract_token(contract, token_id)

        if not nft_id:
            return jsonify({
                'success': True,
                'contract': contract,
                'token_id': token_id,
                'captures': [],
                'message': 'NFT not found in database'
            })

        # Get limit from query params
        limit = request.args.get('limit', 100, type=int)

        # Get capture history
        captures = tracker.get_capture_history(nft_id, limit=limit)

        return jsonify({
            'success': True,
            'contract': contract,
            'token_id': token_id,
            'nft_id': nft_id,
            'captures': captures,
            'total': len(captures)
        })

    except Exception as e:
        logger.error(f"Error fetching capture history for {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# PROVENANCE CERTIFICATION API ENDPOINTS
# ============================================================================

# Try to import ProvenanceCertifier
try:
    from collectors.provenance_certifier import ProvenanceCertifier
    PROVENANCE_CERTIFIER_AVAILABLE = True
except ImportError:
    PROVENANCE_CERTIFIER_AVAILABLE = False
    print("Warning: ProvenanceCertifier not available")


@app.route('/api/nft/<contract>/<token_id>/certify')
def api_nft_certify(contract, token_id):
    """
    Get provenance certification for an NFT.

    Checks:
    - Mint origin (registered artist?)
    - Platform verification (curated?)
    - Registry match (in catalog?)

    Response: {
        success: bool,
        status: "VERIFIED" | "LIKELY" | "UNVERIFIED",
        score: 0-100,
        factors: [...],
        cached: bool,
        cached_at: timestamp
    }
    """
    if not PROVENANCE_CERTIFIER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'ProvenanceCertifier not available',
            'status': 'UNVERIFIED',
            'score': 0,
            'factors': []
        }), 503

    try:
        from collectors.blockchain_db import get_db

        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        # Check cache first (24 hour expiry)
        cache_key = f"{contract.lower()}:{token_id}"
        cursor.execute('''
            SELECT certification_data, cached_at
            FROM certification_cache
            WHERE cache_key = ?
            AND datetime(cached_at, '+24 hours') > datetime('now')
        ''', (cache_key,))

        cached = cursor.fetchone()
        if cached:
            cert_data = json.loads(cached['certification_data'])
            conn.close()
            return jsonify({
                'success': True,
                'status': cert_data.get('certification_level', 'UNVERIFIED'),
                'score': cert_data.get('total_score', 0),
                'factors': cert_data.get('factors', []),
                'cached': True,
                'cached_at': cached['cached_at']
            })

        conn.close()

        # Run certification
        certifier = ProvenanceCertifier()
        cert = certifier.certify_nft(contract, int(token_id))

        # Cache the result
        conn = db.get_connection()
        cursor = conn.cursor()

        # Ensure cache table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certification_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                contract_address TEXT,
                token_id TEXT,
                certification_data TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cert_cache_key
            ON certification_cache(cache_key)
        ''')

        # Store in cache
        cursor.execute('''
            INSERT OR REPLACE INTO certification_cache
            (cache_key, contract_address, token_id, certification_data, cached_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (cache_key, contract.lower(), str(token_id), json.dumps(cert)))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'status': cert.get('certification_level', 'UNVERIFIED'),
            'score': cert.get('total_score', 0),
            'factors': cert.get('factors', []),
            'cached': False,
            'cached_at': datetime.utcnow().isoformat()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'UNVERIFIED',
            'score': 0,
            'factors': []
        }), 500


@app.route('/api/document/<doc_id>/certify')
def api_document_certify(doc_id):
    """
    Get provenance certification for a document by its doc_id.

    Extracts blockchain metadata from the document and runs certification.

    Response: Same as /api/nft/<contract>/<token_id>/certify
    """
    try:
        # Find the document
        kb_path = Path("knowledge_base/processed")

        doc_file = None
        doc_frontmatter = None

        for md_file in kb_path.rglob("*.md"):
            try:
                frontmatter, _ = parse_markdown_file(md_file)
                if frontmatter.get('id') == doc_id:
                    doc_file = md_file
                    doc_frontmatter = frontmatter
                    break
            except:
                continue

        if not doc_frontmatter:
            return jsonify({
                'success': False,
                'message': 'Document not found',
                'status': 'UNVERIFIED',
                'score': 0,
                'factors': []
            })

        # Extract blockchain metadata
        blockchain_meta = extract_blockchain_metadata(doc_frontmatter)

        if not blockchain_meta or not blockchain_meta.get('contract_address'):
            return jsonify({
                'success': False,
                'message': 'No blockchain metadata found in document',
                'status': 'UNVERIFIED',
                'score': 0,
                'factors': []
            })

        contract = blockchain_meta['contract_address']
        token_ids = blockchain_meta.get('token_ids', [])

        if not token_ids:
            return jsonify({
                'success': False,
                'message': 'No token ID found in document',
                'status': 'UNVERIFIED',
                'score': 0,
                'factors': []
            })

        # Use first token ID
        token_id = token_ids[0]

        # Redirect to the main certification endpoint
        return api_nft_certify(contract, str(token_id))

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'UNVERIFIED',
            'score': 0,
            'factors': []
        }), 500


@app.route('/api/certification/invalidate', methods=['POST'])
def api_invalidate_certification_cache():
    """
    Invalidate certification cache for an NFT or all NFTs.

    Request body:
    - contract: Optional contract address
    - token_id: Optional token ID
    - all: If true, clears entire cache

    Response: {success, cleared_count}
    """
    try:
        data = request.get_json() or {}

        from collectors.blockchain_db import get_db

        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        if data.get('all'):
            cursor.execute('DELETE FROM certification_cache')
            cleared = cursor.rowcount
        elif data.get('contract'):
            if data.get('token_id'):
                cache_key = f"{data['contract'].lower()}:{data['token_id']}"
                cursor.execute(
                    'DELETE FROM certification_cache WHERE cache_key = ?',
                    (cache_key,)
                )
            else:
                cursor.execute(
                    'DELETE FROM certification_cache WHERE contract_address = ?',
                    (data['contract'].lower(),)
                )
            cleared = cursor.rowcount
        else:
            return jsonify({
                'success': False,
                'error': 'Must specify contract, contract+token_id, or all=true'
            }), 400

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'cleared_count': cleared
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# NFT TEMPORAL DETAIL VIEW - Living Works UI
# ============================================================================

@app.route('/nft/<contract>/<token_id>/temporal')
def nft_temporal_detail(contract, token_id):
    """
    Temporal detail view for an NFT.

    Shows:
    - Timeline of past states and future events
    - State comparison view
    - Live feed display for reactive works
    - Reactivity profile and scheduled events
    """
    try:
        from collectors.living_works_tracker import (
            LivingWorksAnalyzer,
            HistoricalStateTracker,
            FutureEventDetector,
            LiveWorkTracker
        )
        from collectors.blockchain_db import get_db

        # Convert token_id to int
        try:
            token_id_int = int(token_id)
        except ValueError:
            return "Invalid token ID", 400

        # Get NFT data from database
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nm.*, ta.address, ta.label, ta.network
            FROM nft_mints nm
            LEFT JOIN tracked_addresses ta ON nm.address_id = ta.id
            WHERE nm.contract_address = ? AND nm.token_id = ?
        ''', (contract, str(token_id)))
        nft_row = cursor.fetchone()
        conn.close()

        if not nft_row:
            # Try to create a minimal NFT object
            nft = {
                'contract': contract,
                'token_id': token_id_int,
                'name': f'NFT #{token_id}',
                'description': None,
                'image': None,
                'token_uri': None,
                'network': 'ethereum',
                'is_living': False,
                'reactivity_types': []
            }
        else:
            # Parse metadata if available
            metadata = {}
            if nft_row.get('metadata_json'):
                try:
                    metadata = json.loads(nft_row['metadata_json'])
                except:
                    pass

            nft = {
                'contract': contract,
                'token_id': token_id_int,
                'name': metadata.get('name') or nft_row.get('name') or f"NFT #{token_id}",
                'description': metadata.get('description') or nft_row.get('description'),
                'image': metadata.get('image') or nft_row.get('image_url'),
                'token_uri': nft_row.get('token_uri'),
                'network': nft_row.get('network', 'ethereum'),
                'is_living': False,
                'reactivity_types': []
            }

        # Get historical states
        history = []
        try:
            tracker = HistoricalStateTracker()
            history_raw = tracker.get_token_uri_history(contract, token_id_int)
            for state in history_raw:
                history.append({
                    'state_number': state.get('state_number', 0),
                    'state_type': state.get('state_type', 'unknown'),
                    'timestamp': state.get('timestamp'),
                    'image': state.get('image'),
                    'token_uri': state.get('token_uri'),
                    'metadata': state.get('metadata', {})
                })
        except Exception as e:
            logger.debug(f"Could not fetch history: {e}")

        # Get future events
        events = []
        try:
            detector = FutureEventDetector()
            contract_events = detector.analyze_contract_for_time_logic(contract)

            for event in contract_events.get('future_events', []):
                scheduled_time = event.get('date') or event.get('scheduled_time')
                if scheduled_time:
                    # Calculate countdown days
                    from datetime import datetime
                    if isinstance(scheduled_time, str):
                        try:
                            event_date = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                            countdown_days = (event_date - datetime.now(event_date.tzinfo)).days
                        except:
                            countdown_days = 0
                    else:
                        countdown_days = 0

                    events.append({
                        'event_type': event.get('event_type', event.get('type', 'scheduled')),
                        'scheduled_time': scheduled_time,
                        'description': event.get('description'),
                        'countdown_days': max(0, countdown_days)
                    })
        except Exception as e:
            logger.debug(f"Could not fetch events: {e}")

        # Check if this is a living work
        live_data = None
        try:
            live_tracker = LiveWorkTracker()
            reactivity = live_tracker.identify_reactivity_type(contract, nft.get('metadata', {}))
            nft['is_living'] = reactivity.get('is_reactive', False)
            nft['reactivity_types'] = reactivity.get('types', [])

            if nft['is_living']:
                # Get current live state
                live_state = live_tracker.capture_live_state(contract, token_id_int)
                live_data = {
                    'last_capture': live_state.get('captured_at'),
                    'feeds': [
                        {
                            'name': 'ETH Price',
                            'type': 'price',
                            'value': live_state.get('chain_state', {}).get('eth_price', '--'),
                            'unit': 'USD',
                            'change': 0,
                            'active': True
                        },
                        {
                            'name': 'Gas Price',
                            'type': 'gas',
                            'value': live_state.get('chain_state', {}).get('gas_price', '--'),
                            'unit': 'gwei',
                            'change': 0,
                            'active': True
                        },
                        {
                            'name': 'Block Height',
                            'type': 'block',
                            'value': live_state.get('block_height', '--'),
                            'unit': '',
                            'change': 0,
                            'active': True
                        }
                    ]
                }
        except Exception as e:
            logger.debug(f"Could not check reactivity: {e}")

        return render_template('nft_temporal_detail.html',
                             nft=nft,
                             history=history,
                             events=events,
                             live_data=live_data)

    except ImportError as e:
        logger.warning(f"Living works tracker not available: {e}")
        # Provide minimal fallback data
        nft = {
            'contract': contract,
            'token_id': int(token_id) if token_id.isdigit() else 0,
            'name': f'NFT #{token_id}',
            'description': 'Living works tracker not available',
            'image': None,
            'token_uri': None,
            'network': 'ethereum',
            'is_living': False,
            'reactivity_types': []
        }
        return render_template('nft_temporal_detail.html',
                             nft=nft,
                             history=[],
                             events=[],
                             live_data=None)

    except Exception as e:
        logger.error(f"Error loading temporal view for {contract}/{token_id}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading temporal view: {e}", 500


# ============================================================================

def main():
    """Run the visual browser"""
    print("\n" + "="*60)
    print("ARCHIV-IT by WEB3GISEL - Visual Browser")
    print("="*60)

    # Initialize embeddings
    init_embeddings()

    # Get stats
    stats = get_stats_direct()
    print(f"\nTotal documents: {stats['total_documents']}")
    print(f"Visual documents: {stats['visual_documents']}")
    print("\nSources:")
    for source, count in stats['sources'].items():
        print(f"  - {source}: {count}")

    print("\n" + "="*60)
    print("Starting web server...")
    print("="*60)

    # Get local IP for network access (iPad, etc.)
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "your-local-ip"

    print(f"\n  LOCAL:   http://localhost:5001")
    print(f"  NETWORK: http://{local_ip}:5001  (iPad/other devices)")
    print("\nPress Ctrl+C to stop\n")

    app.run(debug=True, port=5001, host='0.0.0.0')

if __name__ == "__main__":
    main()
