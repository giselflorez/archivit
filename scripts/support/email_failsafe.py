"""
MOONSTONE Email Failsafe Support System

Provides email-based support when users can't access the app directly.
Uses special subject line tags for tracking and security validation.

Contact: info@web3photo.com (displayed with anti-bot obfuscation)

Security Hierarchy:
1. Pattern detection for malicious requests
2. Rate limiting per sender
3. Content validation against known attack vectors
4. Queue for human approval before implementation
5. Auto-reply only for SAFE questions
"""

import os
import re
import json
import hashlib
import imaplib
import smtplib
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPPORT_EMAIL = "info@web3photo.com"
SUBJECT_TAG_PREFIX = "[MOONSTONE-"
SUBJECT_TAG_PATTERN = r'\[MOONSTONE-([A-Z0-9]{6})\]'

# Rate limiting
MAX_REQUESTS_PER_DAY = 10
MAX_REQUESTS_PER_HOUR = 3

# Paths
QUEUE_DIR = Path(__file__).parent / "queue"
PROCESSED_DIR = Path(__file__).parent / "processed"
BLOCKED_DIR = Path(__file__).parent / "blocked"
LOG_FILE = Path(__file__).parent / "support_log.json"

# =============================================================================
# SECURITY PATTERNS - BLOCK THESE
# =============================================================================

MALICIOUS_PATTERNS = [
    # Code injection attempts
    r'(?i)(exec|eval|system|shell|subprocess|os\.)',
    r'(?i)(import\s+os|import\s+subprocess|import\s+sys)',
    r'(?i)(__import__|globals|locals|builtins)',

    # SQL injection
    r'(?i)(drop\s+table|delete\s+from|truncate|union\s+select)',
    r'(?i)(;\s*--|;\s*#|1=1|or\s+1=1)',

    # Path traversal
    r'\.\./|\.\.\\',
    r'(?i)(etc/passwd|etc/shadow|\.ssh/)',

    # XSS attempts
    r'<script[^>]*>|javascript:|on\w+\s*=',

    # Credential harvesting
    r'(?i)(password|api.?key|secret|private.?key|wallet.?seed)',
    r'(?i)(send\s+me|give\s+me|share).*(credential|password|key)',

    # Wallet/crypto scams
    r'(?i)(send\s+\d+\s*(eth|btc|xtz|crypto))',
    r'(?i)(validate|verify)\s+wallet',
    r'(?i)(airdrop|giveaway|free\s+crypto)',

    # Social engineering
    r'(?i)(urgent|immediate|account.*(suspend|terminat))',
    r'(?i)(click\s+here|verify\s+now|confirm\s+identity)',
]

# Keywords requiring human review (not blocked, just flagged)
REVIEW_KEYWORDS = [
    r'(?i)(implement|deploy|execute|run|install)',
    r'(?i)(change|modify|update|delete|remove)\s+(file|code|data)',
    r'(?i)(database|server|production|live)',
    r'(?i)(admin|root|sudo|permission)',
    r'(?i)(backup|restore|migrate)',
]

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class CautionLevel(Enum):
    SAFE = "safe"           # Auto-reply allowed
    REVIEW = "review"       # Needs human approval
    BLOCKED = "blocked"     # Rejected, logged for security

@dataclass
class SupportRequest:
    ticket_id: str
    sender_email: str
    subject: str
    body: str
    timestamp: str
    caution_level: str
    flags: List[str]
    local_response: Optional[str] = None
    human_approved: bool = False
    processed: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

# =============================================================================
# SECURITY VALIDATION
# =============================================================================

def generate_ticket_id() -> str:
    """Generate a unique 6-character ticket ID."""
    timestamp = datetime.now().isoformat()
    hash_input = f"{timestamp}-{os.urandom(8).hex()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:6].upper()


def validate_request(subject: str, body: str, sender: str) -> Tuple[CautionLevel, List[str]]:
    """
    Validate incoming request for security threats.

    Returns:
        Tuple of (CautionLevel, list of flags/reasons)
    """
    flags = []
    full_text = f"{subject} {body}".lower()

    # Check for malicious patterns - BLOCK
    for pattern in MALICIOUS_PATTERNS:
        if re.search(pattern, full_text):
            flags.append(f"BLOCKED: Malicious pattern detected - {pattern[:30]}...")
            return CautionLevel.BLOCKED, flags

    # Check for review keywords - REVIEW
    for pattern in REVIEW_KEYWORDS:
        if re.search(pattern, full_text):
            flags.append(f"REVIEW: Implementation request detected - {pattern[:30]}...")

    # Check sender reputation (basic - could expand with database)
    if sender.endswith('.ru') or sender.endswith('.cn'):
        flags.append("REVIEW: Geographic flag")

    if '+' in sender.split('@')[0]:  # Plus-addressing often used for testing/spam
        flags.append("REVIEW: Plus-addressed email")

    # Determine final caution level
    if flags:
        return CautionLevel.REVIEW, flags

    return CautionLevel.SAFE, ["OK: No security concerns detected"]


def check_rate_limit(sender: str) -> Tuple[bool, str]:
    """
    Check if sender has exceeded rate limits.

    Returns:
        Tuple of (is_allowed, reason)
    """
    if not LOG_FILE.exists():
        return True, "OK"

    try:
        with open(LOG_FILE) as f:
            log = json.load(f)
    except:
        return True, "OK"

    sender_requests = [
        r for r in log.get('requests', [])
        if r.get('sender') == sender
    ]

    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    requests_last_hour = sum(
        1 for r in sender_requests
        if datetime.fromisoformat(r['timestamp']) > hour_ago
    )

    requests_last_day = sum(
        1 for r in sender_requests
        if datetime.fromisoformat(r['timestamp']) > day_ago
    )

    if requests_last_hour >= MAX_REQUESTS_PER_HOUR:
        return False, f"Rate limit: {MAX_REQUESTS_PER_HOUR} requests/hour exceeded"

    if requests_last_day >= MAX_REQUESTS_PER_DAY:
        return False, f"Rate limit: {MAX_REQUESTS_PER_DAY} requests/day exceeded"

    return True, "OK"

# =============================================================================
# LOCAL KNOWLEDGE BASE (Same as ai_routes.py)
# =============================================================================

def load_northstar_masters():
    """Load the 22 NORTHSTAR Masters from local JSON."""
    masters_path = Path(__file__).parent.parent / 'agents' / 'ARTIST_AGENTS.json'

    masters = {}

    if masters_path.exists():
        try:
            with open(masters_path) as f:
                data = json.load(f)

            agents = data.get('agents', {})
            for polarity in ['feminine', 'masculine']:
                for agent in agents.get(polarity, []):
                    master_id = agent.get('id', '').lower()
                    if master_id:
                        quotes = [q.get('quote', '') for q in agent.get('verified_quotes', [])]
                        masters[master_id] = {
                            'name': agent.get('name', master_id),
                            'domain': agent.get('domain', ''),
                            'quotes': quotes,
                            'teachings': agent.get('teaching_points', [])
                        }

            if masters:
                return masters
        except Exception as e:
            print(f"Warning: Could not load ARTIST_AGENTS.json: {e}")

    # Fallback
    return {
        "tesla": {"name": "Nikola Tesla", "domain": "Energy", "quotes": [], "teachings": []},
        "fuller": {"name": "Buckminster Fuller", "domain": "Systems", "quotes": [], "teachings": []}
    }


# Troubleshooting patterns (same as ai_routes.py)
TROUBLESHOOTING = {
    r"ipfs|pinata|upload|pin": {
        "topic": "IPFS Upload",
        "response": "IPFS uploads use Pinata. Ensure PINATA_API_KEY is set in .env. Endpoint: POST /api/mint/upload-metadata"
    },
    r"scan|wallet|nft": {
        "topic": "Wallet Scanning",
        "response": "Scan wallets via POST /api/scan/wallet. Tezos works immediately, ETH needs Alchemy key."
    },
    r"mint|eth|polygon": {
        "topic": "NFT Minting",
        "response": "Minting flow: 1) Upload to IPFS 2) Create metadata 3) Estimate gas 4) Mint with wallet"
    },
    r"server|port|5001": {
        "topic": "Server Setup",
        "response": "Start server: python visual_browser.py --port 5001 (port 5000 blocked by macOS)"
    },
    r"sovereign|local|data": {
        "topic": "Sovereignty",
        "response": "ARCHIV-IT is sovereign-first. Your data lives on YOUR device. You own your seed."
    }
}


def generate_local_response(question: str) -> Optional[str]:
    """Generate response using LOCAL knowledge only."""
    question_lower = question.lower()

    # Check troubleshooting patterns
    for pattern, data in TROUBLESHOOTING.items():
        if re.search(pattern, question_lower):
            return f"**{data['topic']}**\n\n{data['response']}"

    # Search masters
    masters = load_northstar_masters()
    for master_id, master in masters.items():
        if master_id in question_lower or master.get('name', '').lower() in question_lower:
            response = f"**{master['name']}** - {master['domain']}\n\n"
            if master.get('quotes'):
                response += f'*"{master["quotes"][0]}"*\n\n'
            if master.get('teachings'):
                response += f"Teaching: {master['teachings'][0]}"
            return response

    return None

# =============================================================================
# EMAIL PROCESSING
# =============================================================================

def process_incoming_email(sender: str, subject: str, body: str) -> SupportRequest:
    """
    Process an incoming support email.

    Creates a SupportRequest with security validation.
    """
    # Generate ticket ID
    ticket_id = generate_ticket_id()

    # Check rate limit
    rate_ok, rate_reason = check_rate_limit(sender)
    if not rate_ok:
        return SupportRequest(
            ticket_id=ticket_id,
            sender_email=sender,
            subject=subject,
            body=body,
            timestamp=datetime.now().isoformat(),
            caution_level=CautionLevel.BLOCKED.value,
            flags=[rate_reason],
            processed=False
        )

    # Validate content
    caution_level, flags = validate_request(subject, body, sender)

    # Try to generate local response for SAFE requests
    local_response = None
    if caution_level == CautionLevel.SAFE:
        local_response = generate_local_response(body)

    request = SupportRequest(
        ticket_id=ticket_id,
        sender_email=sender,
        subject=subject,
        body=body,
        timestamp=datetime.now().isoformat(),
        caution_level=caution_level.value,
        flags=flags,
        local_response=local_response,
        processed=False
    )

    # Save to appropriate queue
    save_to_queue(request)

    return request


def save_to_queue(request: SupportRequest):
    """Save request to appropriate queue directory."""
    # Ensure directories exist
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    BLOCKED_DIR.mkdir(parents=True, exist_ok=True)

    # Choose directory based on caution level
    if request.caution_level == CautionLevel.BLOCKED.value:
        target_dir = BLOCKED_DIR
    else:
        target_dir = QUEUE_DIR

    # Save request
    filepath = target_dir / f"{request.ticket_id}.json"
    with open(filepath, 'w') as f:
        json.dump(request.to_dict(), f, indent=2)

    # Log the request
    log_request(request)


def log_request(request: SupportRequest):
    """Append request to log file."""
    log = {'requests': []}

    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f:
                log = json.load(f)
        except:
            pass

    log['requests'].append({
        'ticket_id': request.ticket_id,
        'sender': request.sender_email,
        'timestamp': request.timestamp,
        'caution_level': request.caution_level
    })

    # Keep only last 1000 entries
    log['requests'] = log['requests'][-1000:]

    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

# =============================================================================
# EMAIL SENDING (Templates)
# =============================================================================

def create_auto_reply(request: SupportRequest) -> str:
    """Create auto-reply for SAFE requests with local response."""
    return f"""
Thank you for contacting MOONSTONE Support.

Your ticket ID: {SUBJECT_TAG_PREFIX}{request.ticket_id}]

{request.local_response or "We've received your question and will respond shortly."}

---
This response was generated locally from our NORTHSTAR Masters knowledge base.
No external AI was used.

For urgent matters, please include your ticket ID in the subject line.

Stay sovereign,
MOONSTONE Support
"""


def create_review_notification(request: SupportRequest) -> str:
    """Create notification for REVIEW requests (sent to admin)."""
    return f"""
NEW SUPPORT REQUEST REQUIRING REVIEW

Ticket: {request.ticket_id}
From: {request.sender_email}
Time: {request.timestamp}
Caution Level: {request.caution_level}

FLAGS:
{chr(10).join(f'  - {flag}' for flag in request.flags)}

SUBJECT:
{request.subject}

BODY:
{request.body}

---
To approve: Move {request.ticket_id}.json from queue/ to processed/
To block: Move to blocked/

Local response (if approved):
{request.local_response or "[No auto-response available - manual reply needed]"}
"""


def create_blocked_notification(request: SupportRequest) -> str:
    """Create notification for BLOCKED requests (security alert)."""
    return f"""
⚠️ SECURITY ALERT - BLOCKED REQUEST

Ticket: {request.ticket_id}
From: {request.sender_email}
Time: {request.timestamp}

SECURITY FLAGS:
{chr(10).join(f'  🚫 {flag}' for flag in request.flags)}

SUBJECT:
{request.subject}

BODY (first 500 chars):
{request.body[:500]}

---
This request was automatically blocked. Logged in blocked/ directory.
Review if you believe this was a false positive.
"""

# =============================================================================
# ANTI-BOT EMAIL DISPLAY
# =============================================================================

def get_obfuscated_email_html() -> str:
    """
    Return HTML that displays email in anti-bot way.
    Uses CSS rollover reveal.
    """
    # Split email for obfuscation
    parts = SUPPORT_EMAIL.split('@')
    user = parts[0]  # info
    domain = parts[1]  # web3photo.com

    return f'''
<style>
.email-protect {{
    display: inline-block;
    cursor: pointer;
    color: var(--gold, #d4a574);
    border-bottom: 1px dotted;
}}
.email-protect .hidden {{
    display: none;
}}
.email-protect:hover .hidden {{
    display: inline;
}}
.email-protect:hover .visible {{
    display: none;
}}
.email-protect::after {{
    content: " (hover to reveal)";
    font-size: 0.7em;
    opacity: 0.5;
}}
.email-protect:hover::after {{
    content: "";
}}
</style>
<span class="email-protect">
    <span class="visible">support [at] ···</span>
    <span class="hidden">{user}@{domain}</span>
</span>
'''


def get_obfuscated_email_js() -> str:
    """
    Return JavaScript that decodes email on click.
    More secure than plain text.
    """
    # Encode email parts
    import base64
    encoded = base64.b64encode(SUPPORT_EMAIL.encode()).decode()

    return f'''
<span id="email-reveal"
      onclick="this.textContent=atob('{encoded}')"
      style="cursor:pointer; color:var(--gold,#d4a574); border-bottom:1px dotted;">
    Click to reveal support email
</span>
'''

# =============================================================================
# CLI INTERFACE
# =============================================================================

def list_pending_requests():
    """List all pending requests in queue."""
    if not QUEUE_DIR.exists():
        print("No queue directory found.")
        return []

    requests = []
    for filepath in QUEUE_DIR.glob("*.json"):
        try:
            with open(filepath) as f:
                data = json.load(f)
                requests.append(SupportRequest.from_dict(data))
        except:
            pass

    return requests


def approve_request(ticket_id: str) -> bool:
    """Approve a request and move to processed."""
    source = QUEUE_DIR / f"{ticket_id}.json"
    if not source.exists():
        print(f"Ticket {ticket_id} not found in queue.")
        return False

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / f"{ticket_id}.json"

    # Update status
    with open(source) as f:
        data = json.load(f)

    data['human_approved'] = True
    data['processed'] = True

    with open(dest, 'w') as f:
        json.dump(data, f, indent=2)

    source.unlink()
    print(f"✓ Approved ticket {ticket_id}")
    return True


def block_request(ticket_id: str, reason: str = "Manual block") -> bool:
    """Block a request and move to blocked."""
    source = QUEUE_DIR / f"{ticket_id}.json"
    if not source.exists():
        print(f"Ticket {ticket_id} not found in queue.")
        return False

    BLOCKED_DIR.mkdir(parents=True, exist_ok=True)
    dest = BLOCKED_DIR / f"{ticket_id}.json"

    # Update status
    with open(source) as f:
        data = json.load(f)

    data['flags'].append(f"MANUAL BLOCK: {reason}")
    data['caution_level'] = CautionLevel.BLOCKED.value

    with open(dest, 'w') as f:
        json.dump(data, f, indent=2)

    source.unlink()
    print(f"✗ Blocked ticket {ticket_id}")
    return True


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("MOONSTONE Email Failsafe Support System")
    print("=" * 60)
    print(f"Support email: {SUPPORT_EMAIL}")
    print(f"Queue directory: {QUEUE_DIR}")
    print()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            requests = list_pending_requests()
            if requests:
                print(f"Pending requests: {len(requests)}")
                for r in requests:
                    print(f"  [{r.ticket_id}] {r.caution_level}: {r.subject[:40]}...")
            else:
                print("No pending requests.")

        elif command == "approve" and len(sys.argv) > 2:
            approve_request(sys.argv[2])

        elif command == "block" and len(sys.argv) > 2:
            reason = sys.argv[3] if len(sys.argv) > 3 else "Manual block"
            block_request(sys.argv[2], reason)

        elif command == "test":
            # Test with sample request
            print("\nTesting with sample request...")
            test_request = process_incoming_email(
                sender="artist@example.com",
                subject="Help with IPFS upload",
                body="How do I upload my artwork to IPFS using Pinata?"
            )
            print(f"Ticket: {test_request.ticket_id}")
            print(f"Caution: {test_request.caution_level}")
            print(f"Flags: {test_request.flags}")
            if test_request.local_response:
                print(f"\nAuto-response:\n{test_request.local_response}")

        elif command == "html":
            print("\nAnti-bot HTML for email display:")
            print(get_obfuscated_email_html())

        elif command == "js":
            print("\nAnti-bot JavaScript for email display:")
            print(get_obfuscated_email_js())

        else:
            print("Usage:")
            print("  python email_failsafe.py list      - List pending requests")
            print("  python email_failsafe.py approve ID - Approve a request")
            print("  python email_failsafe.py block ID   - Block a request")
            print("  python email_failsafe.py test       - Test with sample")
            print("  python email_failsafe.py html       - Get anti-bot HTML")
            print("  python email_failsafe.py js         - Get anti-bot JS")
    else:
        print("Usage: python email_failsafe.py [list|approve|block|test|html|js]")
