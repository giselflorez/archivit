# SESSION ELIMINATION SPECIFICATION

## ARC-8 Fully Offline Architecture

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** TECHNICAL SPECIFICATION
**Author:** Claude Code Agent (Ultrathink Analysis)

---

## Executive Summary

This document specifies the complete elimination of Flask server-side sessions to achieve a fully offline, user-sovereign ARC-8 application. All 11 current session usages will be replaced with client-side cryptographic storage using the existing PQS seed system, IndexedDB, localStorage, and stateless security patterns.

**Core Principle:** The server becomes a stateless API layer. All user state lives on the client, encrypted with user-controlled keys.

---

## Table of Contents

1. [Current Session Usage Audit](#1-current-session-usage-audit)
2. [Replacement Architecture](#2-replacement-architecture)
3. [CSRF Protection Without Sessions](#3-csrf-protection-without-sessions)
4. [Client-Side State Storage](#4-client-side-state-storage)
5. [Authentication Redesign](#5-authentication-redesign)
6. [Email Confirmation Flow](#6-email-confirmation-flow)
7. [Security Analysis](#7-security-analysis)
8. [Migration Path](#8-migration-path)
9. [Code Patterns](#9-code-patterns)
10. [Recommended Libraries](#10-recommended-libraries)

---

## 1. Current Session Usage Audit

### 1.1 Complete List of Session Variables

| Session Key | Location | Purpose | Security Level |
|-------------|----------|---------|----------------|
| `_csrf_token` | `visual_browser.py:285-286` | CSRF protection | HIGH |
| `site_authenticated` | `visual_browser.py:352` | Site password gate | MEDIUM |
| `tos_accepted` | `visual_browser.py:1020` | Terms acceptance flag | LOW |
| `tos_accepted_at` | `visual_browser.py:1021` | Acceptance timestamp | LOW |
| `training_layers` | `visual_browser.py:1094` | Selected layer list | LOW |
| `training_current` | `visual_browser.py:1095,1113,1187` | Current layer index | LOW |
| `confirmation_code` | `setup_routes.py:81` | Email verification code | HIGH |
| `confirmation_email` | `setup_routes.py:82` | Email being verified | MEDIUM |

### 1.2 Session Dependency Analysis

```
Server Session Dependencies:
├── Security Critical (Must maintain protection)
│   ├── _csrf_token (form/request validation)
│   └── confirmation_code (email verification)
│
├── Authentication State (Can move to client with signatures)
│   ├── site_authenticated
│   └── confirmation_email
│
└── User Preferences (Pure client-side)
    ├── tos_accepted
    ├── tos_accepted_at
    ├── training_layers
    └── training_current
```

---

## 2. Replacement Architecture

### 2.1 Architectural Principles

```
BEFORE (Server-Stateful):
┌─────────┐       ┌─────────────────┐
│ Browser │ ───── │ Flask + Session │
└─────────┘       │   (State Here)  │
                  └─────────────────┘

AFTER (Client-Sovereign):
┌─────────────────────────────────┐
│ Browser                         │
│ ┌─────────────────────────────┐ │       ┌───────────────┐
│ │ IndexedDB (encrypted seed)  │ │ ───── │ Flask (API)   │
│ │ localStorage (preferences)  │ │       │ (Stateless)   │
│ │ Signed Cookies (CSRF)       │ │       └───────────────┘
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### 2.2 State Ownership Matrix

| State Type | Storage Location | Encryption | Server Access |
|------------|------------------|------------|---------------|
| User Identity | IndexedDB (SeedProfileDB) | AES-256-GCM | None |
| Preferences | localStorage | None (non-sensitive) | None |
| Auth Tokens | Signed Cookie | HMAC-SHA256 | Read-only verify |
| CSRF Protection | Signed Cookie + Header | HMAC-SHA256 | Verify only |
| TOS Acceptance | localStorage + DB | None | Optional sync |
| Training State | localStorage | None | None |
| Email Confirmation | Client + One-Time Server Token | Signed | Verify once |

---

## 3. CSRF Protection Without Sessions

### 3.1 Signed Double-Submit Cookie Pattern

The OWASP-recommended pattern for stateless CSRF protection.

**How It Works:**
1. Server generates a signed token containing: `timestamp + random + HMAC(secret, timestamp+random)`
2. Token is set as both a cookie AND included in forms/headers
3. Server validates signature without storing state

```
                     ┌───────────────────┐
   Request           │ Cookie: csrf=X    │
   ─────────────────►│ Header: X-CSRF=X  │
                     │ Body: _csrf=X     │
                     └────────┬──────────┘
                              │
                     ┌────────▼──────────┐
                     │ Verify Signature  │
                     │ Check Expiry      │
                     │ Compare Values    │
                     └───────────────────┘
```

### 3.2 Implementation Pattern

```python
# Server-side (Flask)
import hmac
import time
import base64
import os

# SECRET_KEY loaded from environment, NEVER exposed to client
SECRET_KEY = os.getenv('CSRF_SECRET_KEY', os.urandom(32))

def generate_csrf_token():
    """Generate stateless signed CSRF token"""
    timestamp = int(time.time())
    random_bytes = os.urandom(16).hex()
    message = f"{timestamp}:{random_bytes}"
    signature = hmac.new(
        SECRET_KEY.encode() if isinstance(SECRET_KEY, str) else SECRET_KEY,
        message.encode(),
        'sha256'
    ).hexdigest()
    token = base64.urlsafe_b64encode(
        f"{message}:{signature}".encode()
    ).decode()
    return token

def verify_csrf_token(token, max_age=3600):
    """Verify stateless CSRF token without session lookup"""
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        timestamp_str, random_bytes, signature = decoded.rsplit(':', 2)
        timestamp = int(timestamp_str)

        # Check expiry
        if time.time() - timestamp > max_age:
            return False

        # Verify signature
        message = f"{timestamp_str}:{random_bytes}"
        expected = hmac.new(
            SECRET_KEY.encode() if isinstance(SECRET_KEY, str) else SECRET_KEY,
            message.encode(),
            'sha256'
        ).hexdigest()

        return hmac.compare_digest(signature, expected)
    except Exception:
        return False
```

### 3.3 Alternative: Fetch Metadata Headers

Modern browsers send `Sec-Fetch-*` headers that can detect cross-origin requests:

```python
@app.before_request
def csrf_protection_fetch_metadata():
    """CSRF protection using Fetch Metadata (no tokens needed)"""
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return None  # Safe methods

    # Check Fetch Metadata headers
    sec_fetch_site = request.headers.get('Sec-Fetch-Site', '')
    sec_fetch_mode = request.headers.get('Sec-Fetch-Mode', '')

    # Allow same-origin requests
    if sec_fetch_site == 'same-origin':
        return None

    # Allow direct navigation (user typing URL)
    if sec_fetch_mode == 'navigate' and request.method == 'GET':
        return None

    # Block cross-origin state-changing requests
    if sec_fetch_site in ('cross-site', 'same-site'):
        return jsonify({'error': 'CSRF blocked'}), 403

    # Fallback for older browsers: require Origin header
    origin = request.headers.get('Origin', '')
    host = request.headers.get('Host', '')
    if origin and not origin.endswith(host):
        return jsonify({'error': 'Invalid origin'}), 403

    return None
```

### 3.4 Combined Defense Strategy (Recommended)

```python
@app.before_request
def combined_csrf_protection():
    """Defense in depth: Fetch Metadata + Signed Token fallback"""
    if request.method not in ('POST', 'PUT', 'DELETE', 'PATCH'):
        return None

    # 1. First line: Fetch Metadata (modern browsers)
    sec_fetch_site = request.headers.get('Sec-Fetch-Site')
    if sec_fetch_site == 'same-origin':
        return None  # Trusted same-origin request

    # 2. Second line: Signed token for older browsers or explicit verification
    token_header = request.headers.get('X-CSRF-Token', '')
    token_cookie = request.cookies.get('csrf_token', '')
    token_form = request.form.get('_csrf_token', '')

    # Must have matching tokens
    token = token_header or token_form
    if not token or token != token_cookie:
        return jsonify({'error': 'CSRF token mismatch'}), 403

    # Verify signature
    if not verify_csrf_token(token):
        return jsonify({'error': 'Invalid CSRF token'}), 403

    return None
```

---

## 4. Client-Side State Storage

### 4.1 Storage Strategy by Data Type

```javascript
// CLIENT-SIDE STATE ARCHITECTURE

const StateStorage = {
    // Critical encrypted data → IndexedDB via SeedProfileEngine
    seed: 'IndexedDB:SeedProfileDB',

    // Preferences and flags → localStorage (plaintext OK)
    preferences: {
        'arc8_tos_accepted': 'boolean',
        'arc8_tos_accepted_at': 'ISO timestamp',
        'arc8_nda_accepted': 'boolean',
        'arc8_training_layers': 'JSON array',
        'arc8_training_current': 'integer index',
        'arc8_site_unlocked': 'boolean',
        'arc8_site_unlocked_at': 'ISO timestamp'
    },

    // Session tokens → Signed HTTP-only cookies
    csrf: 'Cookie:csrf_token (signed, HTTP-only)',

    // Temporary verification → localStorage with expiry
    email_verification: 'localStorage:arc8_email_pending (expires in 1 hour)'
};
```

### 4.2 LocalStorage Schema

```javascript
/**
 * ARC-8 LocalStorage Schema
 * All keys prefixed with 'arc8_' for namespace isolation
 */

const ARC8_STORAGE = {
    // Terms of Service
    'arc8_tos': {
        accepted: true,
        accepted_at: '2026-01-13T12:00:00Z',
        version: '1.0'
    },

    // Site Authentication (password-protected content)
    'arc8_site_auth': {
        unlocked: true,
        unlocked_at: '2026-01-13T12:00:00Z',
        // No password stored - just the unlock state
        // Re-verification required on new browser session
    },

    // Training State
    'arc8_training': {
        selected_layers: ['identity', 'works', 'collectors'],
        current_index: 1,
        completed_layers: ['identity'],
        started_at: '2026-01-13T12:00:00Z'
    },

    // Email Verification (temporary, with expiry)
    'arc8_email_pending': {
        email: 'user@example.com',
        expires_at: '2026-01-13T13:00:00Z',  // 1 hour from request
        // Code NOT stored client-side - verified server-side
    }
};

// Helper class for localStorage with automatic JSON parsing
class ARC8Storage {
    static get(key) {
        try {
            const item = localStorage.getItem(`arc8_${key}`);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.warn(`[ARC8Storage] Failed to get ${key}:`, e);
            return null;
        }
    }

    static set(key, value) {
        try {
            localStorage.setItem(`arc8_${key}`, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn(`[ARC8Storage] Failed to set ${key}:`, e);
            return false;
        }
    }

    static remove(key) {
        localStorage.removeItem(`arc8_${key}`);
    }

    static clear() {
        Object.keys(localStorage)
            .filter(k => k.startsWith('arc8_'))
            .forEach(k => localStorage.removeItem(k));
    }
}
```

### 4.3 IndexedDB Integration with Existing Seed Engine

```javascript
/**
 * Extend SeedProfileEngine for app-wide state
 * Leverages existing encryption infrastructure
 */

class ARC8StateEngine extends SeedProfileEngine {
    constructor() {
        super();
        this.APP_STATE_KEY = 'arc8_app_state';
    }

    /**
     * Store sensitive app state in the encrypted seed
     * This data is protected by the user's seed key
     */
    async saveSecureState(stateKey, data) {
        if (!this.isInitialized) {
            throw new Error('Seed must be unlocked to save secure state');
        }

        // Add to seed's knowledge layer (persists across sessions)
        if (!this.seed.app_state) {
            this.seed.app_state = {};
        }

        this.seed.app_state[stateKey] = {
            data: data,
            updated_at: Date.now(),
            version: '1.0'
        };

        await this._saveToStorage();
        this._emit('state_updated', { key: stateKey });
    }

    /**
     * Retrieve sensitive app state
     */
    getSecureState(stateKey) {
        if (!this.isInitialized || !this.seed?.app_state) {
            return null;
        }
        return this.seed.app_state[stateKey]?.data;
    }

    /**
     * Store TOS acceptance with cryptographic proof
     */
    async acceptTerms(version = '1.0') {
        const proof = {
            accepted: true,
            version: version,
            timestamp: Date.now(),
            device_hash: this.seed.genesis.device_fingerprint,
            // Sign with seed entropy for non-repudiation
            signature: await this._signData(`tos_accepted:${version}:${Date.now()}`)
        };

        await this.saveSecureState('tos_acceptance', proof);

        // Also store in localStorage for quick access
        ARC8Storage.set('tos', {
            accepted: true,
            accepted_at: new Date().toISOString(),
            version: version
        });

        return proof;
    }

    /**
     * Verify TOS was accepted
     */
    hasAcceptedTerms(requiredVersion = '1.0') {
        // Quick check from localStorage
        const quick = ARC8Storage.get('tos');
        if (!quick?.accepted) return false;

        // Deep check from encrypted seed (authoritative)
        const proof = this.getSecureState('tos_acceptance');
        if (!proof?.accepted) return false;

        // Version check
        return proof.version >= requiredVersion;
    }

    async _signData(data) {
        const encoder = new TextEncoder();
        const key = await crypto.subtle.importKey(
            'raw',
            encoder.encode(this.seed.genesis.entropy_seed),
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        const signature = await crypto.subtle.sign(
            'HMAC',
            key,
            encoder.encode(data)
        );
        return Array.from(new Uint8Array(signature))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
}

// Export singleton
export const arc8State = new ARC8StateEngine();
```

---

## 5. Authentication Redesign

### 5.1 Site Password Authentication (Stateless)

Replace `session['site_authenticated']` with a signed cookie approach:

```python
# Server-side
from itsdangerous import URLSafeTimedSerializer

SITE_PASSWORD = os.getenv('SITE_PASSWORD', '')
SECRET_KEY = os.getenv('SECRET_KEY')

serializer = URLSafeTimedSerializer(SECRET_KEY)

@app.route('/login', methods=['POST'])
def login_page():
    entered_password = request.form.get('password', '')

    if entered_password == SITE_PASSWORD:
        # Generate signed token
        token = serializer.dumps({
            'authenticated': True,
            'authenticated_at': time.time()
        }, salt='site-auth')

        response = redirect('/')
        response.set_cookie(
            'arc8_auth',
            token,
            httponly=True,
            secure=True,  # HTTPS only
            samesite='Strict',
            max_age=86400 * 7  # 7 days
        )
        return response

    return render_template('login.html', error='Incorrect password')

@app.before_request
def check_site_auth():
    """Verify site authentication from signed cookie"""
    if not SITE_PASSWORD:
        return None  # No password required

    # Allow login page
    if request.path in ['/login', '/static']:
        return None

    token = request.cookies.get('arc8_auth')
    if not token:
        return redirect('/login')

    try:
        data = serializer.loads(token, salt='site-auth', max_age=86400 * 7)
        if data.get('authenticated'):
            return None  # Allowed
    except Exception:
        pass

    return redirect('/login')
```

```javascript
// Client-side (for UI state only)
document.addEventListener('DOMContentLoaded', () => {
    // Store unlock state for UI (the actual auth is in the cookie)
    const authCookie = document.cookie.includes('arc8_auth=');
    if (authCookie) {
        ARC8Storage.set('site_auth', {
            unlocked: true,
            unlocked_at: new Date().toISOString()
        });
    }
});
```

### 5.2 Seed-Based Authentication (Future Enhancement)

For full offline capability, authentication can be entirely seed-based:

```javascript
/**
 * Seed-Based Authentication
 * User unlocks their seed → all app features available
 * No server authentication needed for local data
 */

class SeedAuthenticator {
    constructor(seedEngine) {
        this.seedEngine = seedEngine;
        this.isAuthenticated = false;
    }

    /**
     * Authenticate by unlocking seed with user's key
     */
    async authenticate(seedKey) {
        const success = await this.seedEngine.unlock(seedKey);
        if (success) {
            this.isAuthenticated = true;

            // Derive session tokens for server communication
            await this._deriveSessionTokens();

            return true;
        }
        return false;
    }

    /**
     * Derive cryptographic tokens for server requests
     * These prove identity without exposing the seed key
     */
    async _deriveSessionTokens() {
        const encoder = new TextEncoder();
        const seed = this.seedEngine.seed;

        // Derive API authentication token
        const apiKey = await crypto.subtle.importKey(
            'raw',
            encoder.encode(seed.genesis.entropy_seed),
            { name: 'HKDF' },
            false,
            ['deriveKey']
        );

        // Derive specific tokens for different purposes
        this.apiToken = await this._deriveToken(apiKey, 'api-auth');
        this.csrfToken = await this._deriveToken(apiKey, 'csrf-token');
    }

    async _deriveToken(baseKey, context) {
        const encoder = new TextEncoder();
        const derivedKey = await crypto.subtle.deriveKey(
            {
                name: 'HKDF',
                salt: encoder.encode(context),
                info: encoder.encode('arc8-v1'),
                hash: 'SHA-256'
            },
            baseKey,
            { name: 'HMAC', hash: 'SHA-256', length: 256 },
            true,
            ['sign']
        );

        const exported = await crypto.subtle.exportKey('raw', derivedKey);
        return Array.from(new Uint8Array(exported))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    logout() {
        this.isAuthenticated = false;
        this.apiToken = null;
        this.csrfToken = null;
        this.seedEngine.lock();  // Clears decryption key from memory
    }
}
```

---

## 6. Email Confirmation Flow

### 6.1 Current Problem

The current flow stores `confirmation_code` and `confirmation_email` in server session, which:
- Breaks if server restarts
- Requires sticky sessions in multi-server deployments
- Doesn't work offline

### 6.2 Stateless Email Confirmation

```python
# Server-side: Stateless email confirmation

from itsdangerous import URLSafeTimedSerializer
import hashlib

serializer = URLSafeTimedSerializer(SECRET_KEY)

def send_confirmation_email(email):
    """
    Generate a stateless confirmation token.
    Token contains encrypted email + code, verified without session.
    """
    # Generate confirmation code
    confirmation_code = secrets.token_hex(4).upper()  # 8 chars

    # Create signed token containing email + code hash
    code_hash = hashlib.sha256(confirmation_code.encode()).hexdigest()[:16]

    token_data = {
        'email': email,
        'code_hash': code_hash,
        'created_at': time.time()
    }

    signed_token = serializer.dumps(token_data, salt='email-confirm')

    # Set token in response cookie (not session!)
    # The code is sent to user's email, token in cookie
    # User submits code, server verifies against token

    return confirmation_code, signed_token

def verify_confirmation(submitted_code, signed_token):
    """
    Verify confirmation code against signed token.
    No session lookup required.
    """
    try:
        # Decode token (expires after 1 hour)
        data = serializer.loads(signed_token, salt='email-confirm', max_age=3600)

        # Hash submitted code
        submitted_hash = hashlib.sha256(submitted_code.upper().encode()).hexdigest()[:16]

        # Compare hashes
        if hmac.compare_digest(data['code_hash'], submitted_hash):
            return True, data['email']

        return False, None
    except Exception:
        return False, None

# Routes
@app.route('/setup/email', methods=['POST'])
def setup_email():
    email = request.form.get('email', '').strip()

    # Generate code and token
    code, token = send_confirmation_email(email)

    # Send email (existing logic)
    # ...

    # Set token in cookie
    response = make_response(redirect('/setup/verify'))
    response.set_cookie(
        'arc8_email_token',
        token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=3600  # 1 hour
    )

    return response

@app.route('/setup/verify', methods=['POST'])
def verify_email():
    submitted_code = request.form.get('confirmation_code', '')
    token = request.cookies.get('arc8_email_token')

    if not token:
        return redirect('/setup/email')

    success, email = verify_confirmation(submitted_code, token)

    if success:
        # Confirm email in database
        user_db = UserConfigDB()
        user = user_db.get_user_by_email(email)
        if user:
            user_db.confirm_email(user['confirmation_token'])

        # Clear the token cookie
        response = redirect('/setup/wallet')
        response.delete_cookie('arc8_email_token')
        return response

    return render_template('verify.html', error='Invalid code')
```

### 6.3 Client-Side Email State

```javascript
// Client stores only the pending email (no code!)
class EmailVerification {
    static setPending(email) {
        ARC8Storage.set('email_pending', {
            email: email,
            started_at: new Date().toISOString(),
            expires_at: new Date(Date.now() + 3600000).toISOString()  // 1 hour
        });
    }

    static getPending() {
        const data = ARC8Storage.get('email_pending');
        if (!data) return null;

        // Check expiry
        if (new Date(data.expires_at) < new Date()) {
            this.clearPending();
            return null;
        }

        return data;
    }

    static clearPending() {
        ARC8Storage.remove('email_pending');
    }
}
```

---

## 7. Security Analysis

### 7.1 Security Comparison Matrix

| Aspect | Server Sessions | Client-Side (Proposed) | Delta |
|--------|-----------------|------------------------|-------|
| CSRF Protection | Token stored in session | Signed double-submit | **Equivalent** |
| Session Fixation | Vulnerable | Not applicable | **Improved** |
| Session Hijacking | Cookie theft = full access | Cookie theft = limited | **Improved** |
| Offline Capability | None | Full | **Major improvement** |
| Scalability | Requires sticky sessions | Stateless, any server | **Improved** |
| User Sovereignty | Server controls state | User controls state | **Major improvement** |
| Data Recovery | Lost if server clears | User can backup seed | **Improved** |

### 7.2 Threat Model

```
THREAT: XSS (Cross-Site Scripting)
├── Server Sessions: Attacker can steal session cookie
├── Client-Side: Attacker can access localStorage
├── Mitigation: CSP headers, input sanitization
└── Note: Both are vulnerable to XSS; client-side slightly worse
         for localStorage data, equivalent for cookies

THREAT: CSRF (Cross-Site Request Forgery)
├── Server Sessions: Protected by session token
├── Client-Side: Protected by signed double-submit
├── Mitigation: Fetch Metadata headers (modern browsers)
└── Note: Equivalent protection, no regression

THREAT: Data Theft (Physical Device Access)
├── Server Sessions: Browser cookies readable
├── Client-Side: IndexedDB encrypted with user key
├── Mitigation: Seed encryption key never stored
└── Note: Client-side is MORE secure due to encryption

THREAT: Server Compromise
├── Server Sessions: All sessions exposed
├── Client-Side: Only signing keys exposed
├── Mitigation: Key rotation, signed tokens expire
└── Note: Client-side significantly more secure

THREAT: Man-in-the-Middle
├── Both: Protected by HTTPS
└── Note: No change
```

### 7.3 Risks of Client-Side Approach

| Risk | Severity | Mitigation |
|------|----------|------------|
| XSS exposes localStorage | MEDIUM | CSP, sanitization, encrypt sensitive data |
| User clears browser data | LOW | Seed backup/export feature |
| Malware/Infostealers | HIGH | Use non-extractable CryptoKeys, encrypt at rest |
| Old browsers lack Fetch Metadata | LOW | Fallback to signed tokens |
| Token expiry sync issues | LOW | Generous expiry + refresh mechanism |

### 7.4 Security Enhancements

```javascript
// Enhanced security measures

const SecurityEnhancements = {
    // 1. Use non-extractable CryptoKeys (cannot be stolen by JS)
    async createNonExtractableKey() {
        return await crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            false,  // extractable = false
            ['encrypt', 'decrypt']
        );
    },

    // 2. Request persistent storage (survives browser cleanup)
    async requestPersistence() {
        if (navigator.storage?.persist) {
            return await navigator.storage.persist();
        }
        return false;
    },

    // 3. Clear sensitive data on page unload (optional paranoid mode)
    enableParanoidMode() {
        window.addEventListener('beforeunload', () => {
            // Clear any in-memory sensitive data
            // Note: This breaks "remember me" functionality
        });
    }
};
```

---

## 8. Migration Path

### 8.1 Phase 1: Add Client-Side Infrastructure (Non-Breaking)

```
Week 1-2: Infrastructure
├── [ ] Add ARC8Storage helper class
├── [ ] Add arc8_state.js extending SeedProfileEngine
├── [ ] Add signed token generation to Flask
├── [ ] Add Fetch Metadata CSRF checking (parallel to existing)
└── [ ] Add localStorage fallbacks for all session reads
```

### 8.2 Phase 2: Dual-Write Period (Backward Compatible)

```
Week 3-4: Dual-Write
├── [ ] Write to both session AND client-side storage
├── [ ] Read from client-side with session fallback
├── [ ] Add cookie-based auth alongside session auth
├── [ ] Add signed email confirmation tokens
└── [ ] Monitor for any issues

Code pattern:
def accept_terms():
    # DUAL WRITE: Session (old) + Cookie (new)
    session['tos_accepted'] = True  # Old
    response.set_cookie('arc8_tos', ...)  # New
```

### 8.3 Phase 3: Cut Over (Remove Sessions)

```
Week 5-6: Session Removal
├── [ ] Remove session reads (use client-side only)
├── [ ] Remove session writes
├── [ ] Remove Flask-Session dependency
├── [ ] Update all templates for client-side state
├── [ ] Test offline functionality
└── [ ] Performance testing (should be faster!)
```

### 8.4 Rollback Plan

```python
# Feature flag for instant rollback
USE_CLIENT_SIDE_STATE = os.getenv('USE_CLIENT_SIDE_STATE', 'true') == 'true'

def get_tos_accepted():
    if USE_CLIENT_SIDE_STATE:
        return verify_signed_cookie('arc8_tos')
    else:
        return session.get('tos_accepted', False)
```

---

## 9. Code Patterns

### 9.1 Flask: Stateless CSRF Middleware

```python
# csrf_stateless.py
import hmac
import time
import base64
import os
from functools import wraps
from flask import request, jsonify, make_response

SECRET_KEY = os.getenv('CSRF_SECRET_KEY', os.urandom(32))
CSRF_COOKIE_NAME = 'arc8_csrf'
CSRF_HEADER_NAME = 'X-CSRF-Token'
TOKEN_MAX_AGE = 3600 * 4  # 4 hours

def generate_csrf_token():
    """Generate a signed, timestamped CSRF token"""
    timestamp = str(int(time.time()))
    random_part = os.urandom(16).hex()
    message = f"{timestamp}.{random_part}"

    key = SECRET_KEY if isinstance(SECRET_KEY, bytes) else SECRET_KEY.encode()
    signature = hmac.new(key, message.encode(), 'sha256').hexdigest()

    return f"{message}.{signature}"

def verify_csrf_token(token):
    """Verify CSRF token signature and expiry"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False

        timestamp_str, random_part, signature = parts
        timestamp = int(timestamp_str)

        # Check expiry
        if time.time() - timestamp > TOKEN_MAX_AGE:
            return False

        # Verify signature
        message = f"{timestamp_str}.{random_part}"
        key = SECRET_KEY if isinstance(SECRET_KEY, bytes) else SECRET_KEY.encode()
        expected = hmac.new(key, message.encode(), 'sha256').hexdigest()

        return hmac.compare_digest(signature, expected)
    except Exception:
        return False

def csrf_protect(f):
    """Decorator for CSRF-protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check Fetch Metadata first (modern browsers)
        sec_fetch_site = request.headers.get('Sec-Fetch-Site', '')
        if sec_fetch_site == 'same-origin':
            return f(*args, **kwargs)

        # Fall back to token verification
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME, '')
        header_token = request.headers.get(CSRF_HEADER_NAME, '')
        form_token = request.form.get('_csrf_token', '')

        submitted_token = header_token or form_token

        # Token must match cookie AND be valid signature
        if not submitted_token or submitted_token != cookie_token:
            return jsonify({'error': 'CSRF token mismatch'}), 403

        if not verify_csrf_token(submitted_token):
            return jsonify({'error': 'Invalid CSRF token'}), 403

        return f(*args, **kwargs)
    return decorated

def set_csrf_cookie(response):
    """Add CSRF cookie to response"""
    token = generate_csrf_token()
    response.set_cookie(
        CSRF_COOKIE_NAME,
        token,
        httponly=False,  # Must be readable by JS
        secure=True,
        samesite='Strict',
        max_age=TOKEN_MAX_AGE
    )
    return response
```

### 9.2 JavaScript: State Manager

```javascript
// arc8_state_manager.js

/**
 * ARC-8 Client-Side State Manager
 * Replaces all server session dependencies
 */

class ARC8StateManager {
    constructor() {
        this.initialized = false;
        this.seedEngine = null;
    }

    async initialize(seedEngine) {
        this.seedEngine = seedEngine;
        this.initialized = true;

        // Migrate any existing session data on first load
        await this._migrateFromSession();
    }

    // ════════════════════════════════════════════════════════════════
    // TOS ACCEPTANCE
    // ════════════════════════════════════════════════════════════════

    hasAcceptedTOS(requiredVersion = '1.0') {
        const data = this._get('tos');
        return data?.accepted && data?.version >= requiredVersion;
    }

    async acceptTOS(version = '1.0') {
        const acceptance = {
            accepted: true,
            version: version,
            accepted_at: new Date().toISOString(),
            device_id: await this._getDeviceId()
        };

        this._set('tos', acceptance);

        // Also store in seed for backup
        if (this.seedEngine?.isInitialized) {
            await this.seedEngine.saveSecureState('tos', acceptance);
        }

        return acceptance;
    }

    // ════════════════════════════════════════════════════════════════
    // SITE AUTHENTICATION
    // ════════════════════════════════════════════════════════════════

    isSiteUnlocked() {
        // Check for auth cookie
        return document.cookie.includes('arc8_auth=');
    }

    // ════════════════════════════════════════════════════════════════
    // TRAINING STATE
    // ════════════════════════════════════════════════════════════════

    getTrainingState() {
        return this._get('training') || {
            layers: [],
            current: 0,
            completed: []
        };
    }

    setTrainingLayers(layers) {
        const state = this.getTrainingState();
        state.layers = layers;
        state.current = 0;
        state.started_at = new Date().toISOString();
        this._set('training', state);
    }

    advanceTraining() {
        const state = this.getTrainingState();
        if (state.current < state.layers.length - 1) {
            state.completed.push(state.layers[state.current]);
            state.current++;
            this._set('training', state);
            return state.layers[state.current];
        }
        return null;  // Training complete
    }

    completeTraining() {
        this._remove('training');
    }

    // ════════════════════════════════════════════════════════════════
    // CSRF TOKEN
    // ════════════════════════════════════════════════════════════════

    getCSRFToken() {
        // Read from cookie
        const match = document.cookie.match(/arc8_csrf=([^;]+)/);
        return match ? match[1] : null;
    }

    // ════════════════════════════════════════════════════════════════
    // PRIVATE METHODS
    // ════════════════════════════════════════════════════════════════

    _get(key) {
        try {
            const item = localStorage.getItem(`arc8_${key}`);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.warn(`[ARC8State] Failed to get ${key}:`, e);
            return null;
        }
    }

    _set(key, value) {
        try {
            localStorage.setItem(`arc8_${key}`, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn(`[ARC8State] Failed to set ${key}:`, e);
            return false;
        }
    }

    _remove(key) {
        localStorage.removeItem(`arc8_${key}`);
    }

    async _getDeviceId() {
        // Use cached device ID or generate new
        let deviceId = localStorage.getItem('arc8_device_id');
        if (!deviceId) {
            const data = new Uint8Array(16);
            crypto.getRandomValues(data);
            deviceId = Array.from(data, b => b.toString(16).padStart(2, '0')).join('');
            localStorage.setItem('arc8_device_id', deviceId);
        }
        return deviceId;
    }

    async _migrateFromSession() {
        // One-time migration from any existing session data
        // This runs once when user first hits the new code
        if (localStorage.getItem('arc8_migrated')) return;

        // Check for server-rendered session hints
        const sessionHints = window.__ARC8_SESSION_HINTS__;
        if (sessionHints) {
            if (sessionHints.tos_accepted) {
                this._set('tos', {
                    accepted: true,
                    version: '1.0',
                    accepted_at: sessionHints.tos_accepted_at || new Date().toISOString(),
                    migrated: true
                });
            }

            if (sessionHints.training_layers) {
                this._set('training', {
                    layers: sessionHints.training_layers,
                    current: sessionHints.training_current || 0,
                    completed: [],
                    migrated: true
                });
            }
        }

        localStorage.setItem('arc8_migrated', 'true');
    }
}

// Singleton export
export const arc8State = new ARC8StateManager();
export default arc8State;
```

### 9.3 Template Integration

```html
<!-- Base template updates -->
<!DOCTYPE html>
<html>
<head>
    <meta name="csrf-token" content="{{ csrf_token() }}">

    <!-- Inject session hints for migration -->
    <script>
        window.__ARC8_SESSION_HINTS__ = {
            tos_accepted: {{ 'true' if session.get('tos_accepted') else 'false' }},
            tos_accepted_at: "{{ session.get('tos_accepted_at', '') }}",
            training_layers: {{ session.get('training_layers', [])|tojson }},
            training_current: {{ session.get('training_current', 0) }}
        };
    </script>
</head>
<body>
    <!-- Content -->

    <script type="module">
        import { arc8State } from '/static/js/core/arc8_state_manager.js';

        // Initialize state manager
        arc8State.initialize();

        // Add CSRF token to all fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const token = arc8State.getCSRFToken();
            if (token && options.method && options.method !== 'GET') {
                options.headers = options.headers || {};
                options.headers['X-CSRF-Token'] = token;
            }
            return originalFetch(url, options);
        };
    </script>
</body>
</html>
```

---

## 10. Recommended Libraries

### 10.1 Python (Server-Side)

| Library | Purpose | Installation |
|---------|---------|--------------|
| `itsdangerous` | Signed tokens/cookies | `pip install itsdangerous` |
| `PyJWT` | JWT tokens (if needed) | `pip install pyjwt` |

**Note:** Minimal new dependencies. `itsdangerous` is already a Flask dependency.

### 10.2 JavaScript (Client-Side)

| Library | Purpose | CDN/Install |
|---------|---------|-------------|
| Native Web Crypto | Encryption | Built-in (no install) |
| Native IndexedDB | Storage | Built-in (no install) |
| Existing `seed_profile.js` | Seed management | Already in codebase |

**Note:** No new JavaScript dependencies required. All functionality uses native Web APIs already available in the codebase.

### 10.3 Optional Enhancements

| Library | Purpose | When to Add |
|---------|---------|-------------|
| `@localfirst/auth` | Full decentralized auth | If adding team features |
| `Dexie.js` | Better IndexedDB API | If storage gets complex |
| `crypto-pouch` | Encrypted PouchDB | If adding sync features |

---

## Appendix A: Session Removal Checklist

### Files to Modify

```
scripts/interface/visual_browser.py
├── [ ] Line 280-286: Replace generate_csrf_token()
├── [ ] Line 291-333: Replace check_csrf_token()
├── [ ] Line 342-356: Replace login_page() session usage
├── [ ] Line 1008-1046: Replace accept_terms() session usage
├── [ ] Line 1087-1098: Replace setup_training() session usage
├── [ ] Line 1100-1147: Replace training_layer_form() session usage
├── [ ] Line 1149-1195: Replace save_training_layer() session usage

scripts/interface/setup_routes.py
├── [ ] Line 72-141: Replace send_confirmation_email() session usage
├── [ ] Line 415-605: Replace setup_wizard() session usage

templates/
├── [ ] All forms: Add CSRF token from cookie
├── [ ] Base template: Add state manager initialization
└── [ ] JavaScript: Replace session checks with localStorage
```

### Testing Checklist

```
Functionality Tests:
├── [ ] CSRF protection works with new tokens
├── [ ] Login/logout works with signed cookies
├── [ ] TOS acceptance persists across sessions
├── [ ] Training progress persists across browser restarts
├── [ ] Email confirmation works with stateless tokens
├── [ ] All forms submit successfully

Offline Tests:
├── [ ] App loads without server (cached)
├── [ ] Previously accepted TOS still valid
├── [ ] Training progress maintained offline
├── [ ] CSRF tokens work after reconnection

Security Tests:
├── [ ] CSRF attack blocked
├── [ ] Cross-origin requests blocked
├── [ ] Expired tokens rejected
├── [ ] Invalid signatures rejected
├── [ ] XSS cannot steal auth cookies (httpOnly)
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Double-Submit Cookie** | CSRF pattern where token is in both cookie and request body |
| **Signed Token** | Token with cryptographic signature proving authenticity |
| **Fetch Metadata** | Browser headers (`Sec-Fetch-*`) indicating request context |
| **SameSite Cookie** | Cookie attribute preventing cross-site transmission |
| **Seed** | User's encrypted identity stored in IndexedDB |
| **PQS** | Personal Quantum Seed - the user's cryptographic identity |

---

## Appendix C: References

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Symfony 7.2 Stateless CSRF](https://symfony.com/blog/new-in-symfony-7-2-stateless-csrf)
- [@localfirst/auth - Decentralized Auth](https://github.com/local-first-web/auth)
- [Encryption-At-Rest for Offline Apps](https://www.linkedin.com/pulse/encryption-at-rest-web-apps-offline-capabilities-hamish-sadler)
- [secure-webstore - IndexedDB Encryption](https://github.com/AKASHAorg/secure-webstore)
- [Better CSRF Protection](https://www.nedmcclain.com/better-csrf-protection/)
- [CSRF Protection Without Tokens](https://blog.miguelgrinberg.com/post/csrf-protection-without-tokens-or-hidden-form-fields)

---

*Document generated by Claude Code Agent - Ultrathink Analysis*
*Date: 2026-01-13*
*Version: 1.0.0*
