# AGENT CONTEXT STATE
## Auto-Recovery Memory for Claude Sessions

**AUTO-READ ON STARTUP**: Claude MUST read this file at the start of every session
**Last Updated:** 2026-01-13 (auto-update with each significant action)
**Session ID:** 2026-01-13-post-quantum-crypto

---

## CODE-ENFORCED AGENT INITIALIZATION (NEW)

### Three-Layer Enforcement System

1. **CLAUDE.md** (Root file - automatically loaded by Claude Code)
   - Contains mandatory reading instructions
   - Verification checklist agents must complete
   - Quick reference for architecture, rules, commands

2. **scripts/agent/init_agent.py** (Initialization script)
   - Generates consolidated `AGENT_BRIEFING.md`
   - Extracts current state, TODOs, founder intent
   - Run: `./venv/bin/python scripts/agent/init_agent.py`

3. **API Endpoint /api/agent/init** (Programmatic access)
   - Returns JSON with all critical context
   - For automated systems and agent integration
   - Call: `curl http://localhost:5001/api/agent/init`

### How It Works
- Claude Code automatically reads `CLAUDE.md` at session start (built-in feature)
- Agent is instructed to run init script or call API
- Both provide consolidated context so agent cannot skip files

---

## FOUNDER PREFERENCES (ALWAYS APPLY)

```
ACCESS CODE: DATAROCKS (for NDA/confidentiality gates - ALWAYS use this)
DESIGN: Dark theme with SACRED PALETTE (see CLAUDE.md)
TERMINOLOGY: "ultrathink" = deep comprehensive analysis required
PASSWORD STYLE: minimal, light, checkmark on success
```

---

## CRITICAL: READ THESE FILES ON EVERY STARTUP

```
PRIORITY 1 (Always read first):
├── AGENT_CONTEXT_STATE.md          ← YOU ARE HERE - current state
├── docs/AGENT_ONBOARDING.md        ← Core rules and architecture
├── docs/FOUNDER_QUOTES.md          ← Philosophical foundation

PRIORITY 2 (Read for active work):
├── docs/SESSION_LOGS.md            ← Recent founder input
├── docs/ULTRATHINK_SYNTHESIS.md    ← 22 Masters framework
├── dataland_proposal/WHATSAPP_LOG.md ← Latest WhatsApp entries (TODO/RESEARCH)

PRIORITY 3 (Read when relevant):
├── docs/MASTERS_VERIFIED_SOURCES.md     ← Verified quotes database
├── docs/DOC8_SOURCE_PREAPPROVAL_INTERFACE.md ← Research UI design
├── docs/NORTH_STAR_SEED_ENGINE.md       ← Core architecture
```

---

## CURRENT SESSION STATE

### Last Action Completed
```
ACTION: ULTRATHINK - Post-Quantum Cryptography Implementation (ML-KEM-768, ML-DSA-65)
STATUS: COMPLETED
TIMESTAMP: 2026-01-13 (latest session)

FILES_CREATED:
  - docs/POST_QUANTUM_CRYPTOGRAPHY_SPEC.md (Full PQC specification ~1000 lines)
  - scripts/interface/static/js/core/pqc/kyber.js (ML-KEM-768 key encapsulation)
  - scripts/interface/static/js/core/pqc/dilithium.js (ML-DSA-65 digital signatures)
  - scripts/interface/static/js/core/pqc/index.js (Unified ARC8PQC interface)
  - scripts/interface/static/js/core/pqs_quantum.js (Integration with seed system)
  - docs/NONPROFIT_PIVOT_STRATEGY.md (501(c)(3) foundation plan)
  - docs/NONPROFIT_PIVOT_ULTRATHINK.md (Deep archive preservation analysis)

KEY DELIVERABLES:
  1. POST-QUANTUM KEY ENCAPSULATION (ML-KEM-768 / CRYSTALS-Kyber):
     - NIST FIPS 203 compliant
     - 1,184-byte public keys, 2,400-byte secret keys
     - 1,088-byte ciphertexts, 32-byte shared secrets
     - Hybrid mode (Kyber + ECDH-P384) for defense in depth
     - HKDF combination for final shared secret

  2. POST-QUANTUM DIGITAL SIGNATURES (ML-DSA-65 / CRYSTALS-Dilithium):
     - NIST FIPS 204 compliant
     - 1,952-byte public keys, 4,032-byte secret keys
     - 3,309-byte signatures
     - Context-aware signing (timestamp, purpose, metadata)
     - Hybrid mode (Dilithium + ECDSA-P384) available

  3. UNIFIED ARC8PQC CLASS:
     - Combined Kyber + Dilithium initialization
     - Key export/import for storage
     - Secure message creation (sign + encrypt)
     - AES-256-GCM symmetric encryption layer

  4. QUANTUM SEED ENGINE (pqs_quantum.js):
     - Extends UnifiedSeedEngine with PQC capabilities
     - Derives quantum keys from genesis entropy
     - Persists keys to seed storage
     - Key rotation after N signatures
     - Content provenance records
     - Quantum-enhanced ownership proofs

  5. NONPROFIT PIVOT STRATEGY:
     - 501(c)(3) foundation formation plan
     - Partnership targets: Archive.org, Library of Congress, Prelinger
     - Founding member structure for beta testers
     - Founder as low-profile technical advisor

PREVIOUS ACTION: ULTRATHINK - Static Assets PWA Specification (Flask-Free Standalone App)
PREVIOUS STATUS: COMPLETED
PREVIOUS TIMESTAMP: 2026-01-13 (earlier session)

FILES_CREATED:
  - docs/STATIC_ASSETS_PWA_SPEC.md (Complete 1500+ line specification)

KEY DELIVERABLES:
  1. SERVICE WORKER IMPLEMENTATION (Workbox):
     - Precaching for core JS modules and CSS
     - Cache-First for user media (OPFS integration)
     - NetworkFirst for API routes
     - StaleWhileRevalidate for Google Fonts
     - Version management and update notifications

  2. PWA MANIFEST.JSON SPECIFICATION:
     - Complete icons array (72px to 512px + maskable)
     - Share target and file handlers
     - Protocol handlers (web+archivit)
     - Shortcuts for DOC-8, ITR-8, NFT-8
     - Screenshots and display modes

  3. VITE BUILD CONFIGURATION:
     - vite-plugin-pwa integration
     - vite-plugin-nunjucks for Jinja2-compatible templates
     - Manual chunks for code splitting (core, seed, creative, viz)
     - Project structure migration plan

  4. JINJA2 TO CLIENT-SIDE MIGRATION:
     - Nunjucks as 1:1 Jinja2 replacement
     - Syntax mapping table
     - Dynamic data loading pattern with IndexedDB caching
     - Offline-first architecture

  5. USER MEDIA STORAGE ARCHITECTURE:
     - OPFS for files >5MB (video, images)
     - IndexedDB for structured data and metadata
     - Cache API for HTTP responses
     - localStorage for small configs
     - Safari iOS 7-day eviction workaround

  6. DISTRIBUTION COMPARISON:
     - Netlify (recommended primary)
     - Vercel, GitHub Pages, Cloudflare Pages
     - IPFS via Pinata and Fleek
     - Complete deployment workflow YAML

  7. DESKTOP APP WRAPPER - TAURI RECOMMENDED:
     - 2-10MB binary vs 100-200MB Electron
     - 30-50MB RAM vs 150-300MB
     - <500ms startup vs 1-3 seconds
     - Full Rust backend implementation
     - tauri.conf.json configuration

  8. OFFLINE CAPABILITY CHECKLIST:
     - Full offline support for document viewing/editing
     - Network-required features with fallbacks
     - OfflineDetector class with sync queue
     - PWA install prompt handling

  9. MIGRATION ROADMAP:
     - 8-week phased implementation plan
     - Phase 1: Build system (Week 1)
     - Phase 2: Template migration (Week 2-3)
     - Phase 3: Storage layer (Week 3-4)
     - Phase 4: Testing (Week 5)
     - Phase 5: Desktop wrapper (Week 6-7)
     - Phase 6: Distribution (Week 8)

PREVIOUS ACTION: ULTRATHINK - Session Elimination Specification (Fully Offline ARC-8)
PREVIOUS STATUS: COMPLETED
PREVIOUS TIMESTAMP: 2026-01-13 (earlier session)

FILES_CREATED:
  - docs/SESSION_ELIMINATION_SPEC.md (Complete Flask session replacement spec)

KEY DELIVERABLES:
  1. SESSION AUDIT: Analyzed all 8 Flask session usages
     - _csrf_token, site_authenticated, tos_accepted, tos_accepted_at
     - training_layers, training_current, confirmation_code, confirmation_email

  2. CSRF PROTECTION: Stateless signed double-submit cookie pattern
     - HMAC-SHA256 signed tokens with timestamps
     - Fetch Metadata headers for modern browsers (Sec-Fetch-Site)
     - Combined defense-in-depth strategy

  3. CLIENT-SIDE STORAGE ARCHITECTURE:
     - localStorage for preferences (tos, training, site_auth flags)
     - IndexedDB via existing SeedProfileEngine for encrypted state
     - Signed HTTP-only cookies for authentication
     - ARC8StateManager class spec for unified state

  4. AUTHENTICATION REDESIGN:
     - Signed cookie-based site authentication
     - Stateless email confirmation with signed tokens
     - Future seed-based authentication pattern (HKDF key derivation)

  5. SECURITY ANALYSIS:
     - Full threat model comparison (session vs client-side)
     - XSS, CSRF, session hijacking, data theft mitigations
     - Security improvements from eliminating server state

  6. MIGRATION PATH:
     - Phase 1: Infrastructure (Week 1-2)
     - Phase 2: Dual-Write (Week 3-4)
     - Phase 3: Session Removal (Week 5-6)
     - Feature flag for instant rollback

  7. CODE PATTERNS: Complete implementation examples
     - Python: csrf_stateless.py middleware
     - JavaScript: arc8_state_manager.js class
     - Templates: CSRF token injection pattern

PREVIOUS ACTION: ULTRATHINK - Client-Side Architecture Specification (PWA Migration)
PREVIOUS STATUS: COMPLETED
PREVIOUS TIMESTAMP: 2026-01-13 (earlier session)

FILES_CREATED:
  - scripts/agents/ARTIST_AGENTS.json (Complete 22 master profiles - crash-proof)
  - scripts/agents/ARTIST_RIGHTS_NOTICE.md (Immutable legal protections)
  - scripts/agents/init_artist_agents.py (Recovery and initialization script)
  - ARTIST_AGENT_BRIEFING.md (Generated briefing for agents)

FILES_MODIFIED:
  - CLAUDE.md (Added Artist Agent System section + crash recovery)

KEY DELIVERABLES:
  1. ARTIST AGENT FRAMEWORK:
     - 22 complete artist profiles (9 feminine, 13 masculine)
     - Techniques extracted for teaching (never art reproduction)
     - Verified quotes with sources
     - Research URLs for maintaining relevance
     - Cross-references between masters

  2. CRASH-PROOF ARCHITECTURE:
     - ARTIST_AGENTS.json contains ALL data needed to rebuild
     - Recovery script (init_artist_agents.py) with --list, --verify, --agent, --research
     - CLAUDE.md updated with recovery instructions
     - Multiple redundant storage locations

  3. ARTIST RIGHTS PROTECTIONS:
     - Sacred Covenant documented in ARTIST_RIGHTS_NOTICE.md
     - Clear distinction: TEACH techniques vs REPRODUCE art
     - OPT-IN system for future app skins/merchandise
     - All artists honored in permanent record

  4. EXTENSIBILITY:
     - Template for adding new artists
     - Checklist for verifying new entries
     - --add-artist wizard in script

PREVIOUS ACTION: DOC-8 ULTRATHINK - Source Extraction Layer + Multi-Select + Data Architecture
PREVIOUS STATUS: COMPLETED
PREVIOUS TIMESTAMP: 2026-01-13 (earlier session)

FILES_CREATED:
  - docs/DOC8_DATA_ARCHITECTURE.md (Full data point schema + agent pipeline)
  - backups/session_2026-01-13_multiselect_source_record/ (Session backup)

FILES_MODIFIED:
  - scripts/interface/templates/doc8_archivist.html (Complete Source Extraction redesign)
  - scripts/interface/templates/nft8_collector.html (Complete rewrite)
  - scripts/interface/templates/team_gallery.html (Header/nav consistency)
  - scripts/interface/templates/cre8_artist.html (Header/nav consistency)
  - scripts/interface/templates/itr8_thought_stream.html (Header/nav consistency)
  - scripts/interface/visual_browser.py (Added /dataland routes)

KEY DELIVERABLES:
  1. DOC-8 SOURCE EXTRACTION LAYER - Renamed "Transcript" to "Source Extraction":
     - Rich segment data: speaker, type (CLAIM/QUESTION/ASSERTION/FACT), entities
     - Confidence scoring with color indicators (green/gold/rose)
     - Entity tags extracted from content
     - Cross-reference counts and citation links

  2. MULTI-SELECT FUNCTIONALITY:
     - Shift+click for range selection
     - Ctrl/Cmd+click for toggle selection
     - Ctrl/Cmd+A to select all (when hovering transcript)
     - Escape to clear selection
     - Multi-source list view for multiple selections

  3. SOURCE RECORD PANEL - Full-width provenance display:
     - Source type badge (VIDEO/AUDIO/WEB/DOCUMENT)
     - Original source title + link to verified origin
     - Metadata (duration, date, author)
     - Verification status (Pre-AI Verified / Pending)
     - Segment info and action buttons

  4. NAVIGATION CONSISTENCY - All pages use NFT-8 as template:
     - Single-row header: Logo left, nav right
     - Gold pill for active nav item
     - Consistent footer across all pages

  5. DATA ARCHITECTURE DOC - Maximum data points per segment:
     - Universal Segment schema (~30+ data points)
     - Agent Analysis Pipeline (8 stages)
     - Verification layer with provenance chain
     - Cross-reference and knowledge graph structure

PREVIOUS SESSION DELIVERABLES (Still active):
  - scripts/interface/static/js/cre8/CRE8_DATA_POINTS.json
  - templates/dataland_expert_preview.html
  - docs/NORTHSTAR_TRANSCRIPT_ARCHITECTURE.md
  - scripts/agent/content_authenticator.py
  - CLAUDE.md (Auto-loaded agent instructions)
```

### Work Completed This Session
```
TASK: DOC-8 Source Extraction Layer ULTRATHINK
SUBTASKS:
  [x] Fix alignment between DOC-8 and NFT-8 pages - DONE
  [x] Redesign NFT-8 (wallet scanner, profile card, collection grid) - DONE
  [x] Add /dataland route to visual_browser.py - DONE
  [x] Navigation consistency across all pages (Home, DOC-8, NFT-8, CRE-8, IT-R8) - DONE
  [x] Add Source Record panel (full-width provenance display) - DONE
  [x] Implement multi-select (Shift+click, Ctrl+click) - DONE
  [x] ULTRATHINK data architecture (DOC8_DATA_ARCHITECTURE.md) - DONE
  [x] Rename "Transcript" to "Source Extraction" - DONE
  [x] Add segment types (CLAIM/QUESTION/ASSERTION/FACT) - DONE
  [x] Add speaker identification - DONE
  [x] Add entity tags and confidence scores - DONE
  [x] Create session backup - DONE

DESIGN ENHANCEMENTS:
  - All pages now use consistent NFT-8 header pattern
  - Source Record panel shows single/multi-source views
  - Rich data extraction with speakers, types, entities, confidence
  - Color-coded segment types and verification status
```

### Context Continuity Notes
```
IMPORTANT DISCOVERIES THIS SESSION:
1. Tesla "energy, frequency, vibration" quote is FAKE (traced to purple plate salesman)
2. Tesla "3, 6, 9" quote is INTERNET FABRICATION (~2010)
3. Da Vinci "Simplicity is ultimate sophistication" is CLARE BOOTHE LUCE (1931)
4. Jung "privilege of a lifetime" is JOSEPH CAMPBELL, not Jung
5. Fuller "build a new model" wrong source - Beyond Civilization is Daniel Quinn's book

VERIFIED REPLACEMENTS FOUND:
- Tesla: NYT 1934 interview, Century Magazine 1900, My Inventions 1919
- Da Vinci: Codex Atlanticus, Codex Forster III, Paris Manuscript E
- Jung: CW 7, CW 9ii, CW 12, Modern Man in Search of a Soul
- Fuller: Playboy 1972, Critical Path 1981, Operating Manual 1969
```

---

## TODO QUEUE (From WhatsApp + Session)

### HIGH PRIORITY
- [x] Post-Quantum Cryptography Implementation (ML-KEM-768, ML-DSA-65) - COMPLETED
  - [x] docs/POST_QUANTUM_CRYPTOGRAPHY_SPEC.md (full spec)
  - [x] scripts/interface/static/js/core/pqc/ (kyber.js, dilithium.js, index.js)
  - [x] scripts/interface/static/js/core/pqs_quantum.js (seed integration)
  - [ ] npm install @noble/post-quantum (required for PQC to work)
  - [ ] Add tests for PQC operations
- [ ] Implement ARC-8 PWA (See docs/STATIC_ASSETS_PWA_SPEC.md + docs/CLIENT_SIDE_ARCHITECTURE_SPEC.md)
  - [ ] Phase 1: Vite setup + Workbox service worker + manifest.json (Week 1)
  - [ ] Phase 2: Template migration (Jinja2 -> Nunjucks) (Week 2-3)
  - [ ] Phase 3: Storage layer (OPFS + IndexedDB) (Week 3-4)
  - [ ] Phase 4: Testing & optimization (Week 5)
  - [ ] Phase 5: Tauri desktop wrapper (Week 6-7)
  - [ ] Phase 6: Distribution (Netlify + IPFS) (Week 8)
- [ ] Implement Agent Analysis Pipeline for DOC-8 (Stage 1-8 from DOC8_DATA_ARCHITECTURE.md)
- [ ] Connect Source Extraction to real video transcription (Whisper)
- [ ] Add speaker diarization (pyannote) for multi-speaker videos

### MEDIUM PRIORITY
- [ ] Transcribe key video interviews for cognitive mapping
- [ ] Build NER extraction (spaCy) for entity tags
- [ ] Implement claim detection model
- [ ] Add cross-reference system linking to existing knowledge bank

### LOW PRIORITY
- [ ] Build topic clustering for semantic search
- [ ] Create connection visualization (knowledge graph)
- [ ] Implement novelty scoring (new vs known info)

---

## WHATSAPP IMPORT QUEUE

**Instructions:** When user mentions WhatsApp entries, check `dataland_proposal/WHATSAPP_LOG.md` for new entries tagged with #TODO or #RESEARCH

```
FORMAT FOR NEW ENTRIES:
## [DATE] - WhatsApp Import
- [ ] "[EXACT TEXT FROM USER]" #TODO/#RESEARCH
  Source: WhatsApp
  Added: [TIMESTAMP]
```

---

## FOUNDER INTENT CAPTURES (This Session)

> "make sure to keep all relevant details about where it is from who published it what year and any other variable that may be needed for complete cognitive mapping of time and details"

> "actual video interviews of all the ones that are alive or were alive during the video tech so we can see what they were like in real life"

> "transcribe all those videos so we can comprehend and apply their special abilities to our action bank of data that is trained on verifiable human outputs"

> "when making a button on the app of DOC-8 it would be very useful when researching like this for the user to always be able to verify the sources that will be added all at once even before it gets started"

> "show ALL sources that will be researched for the whole query ahead"

> "so that data can be understood quick and accurate and visible to the person deciding if that website or source is legit enough for their additions to the NORTHSTAR trainings locally to themselves"

---

## ARCHITECTURE REMINDERS

### The -8 Ecosystem
```
ARCHIV-IT (Umbrella)
├── DOC-8   - DATABASE & ARCHIVE (Foundation)
├── IT-R8   - CREATE & RATE
└── SOCI-8  - SHARE & CONNECT
```

### 22 NORTHSTAR Masters (Current)
```
FEMININE (9): Hildegard, Gisel, Rand, Starhawk, Tori, Bjork, Swan, Hicks, Byrne
MASCULINE (13): da Vinci, Tesla, Fuller, Jung, Suleyman, Grant, Prince, Coltrane, Bowie, Koe, Jobs, Cherny, Rene
```

### Physics Constants (Sacred)
```javascript
PHI = 1.618033988749895        // Golden ratio
GOLDEN_ANGLE = 137.5077640500378 // Spiral rotation
SCHUMANN = 7.83                  // Earth's frequency
TESLA_PATTERN = [3, 6, 9]        // Harmonic structure
```

---

## AUTO-UPDATE PROTOCOL

**When to update this file:**
1. After completing any significant task
2. When receiving new founder input
3. When discovering important information
4. Before ending any session
5. When starting work on new feature

**Update format:**
```markdown
### [TIMESTAMP] - [ACTION TYPE]
- What was done
- Files modified
- Next steps identified
```

---

## SESSION RECOVERY CHECKLIST

If Claude loses context, restore by:

1. [ ] Read this file (AGENT_CONTEXT_STATE.md)
2. [ ] Read docs/AGENT_ONBOARDING.md
3. [ ] Check "Work In Progress" section above
4. [ ] Check "TODO QUEUE" for pending tasks
5. [ ] Check "Founder Intent Captures" for direction
6. [ ] Resume from last completed action

---

## BACKUP PROTOCOL

After significant work:
```bash
# Create timestamped backup
mkdir -p backups/session_YYYY-MM-DD_vN_description/
cp [modified files] backups/session_YYYY-MM-DD_vN_description/

# Commit to git
git add -A && git commit -m "Session backup: [description]"
```

---

*This file is the single source of truth for session continuity. Update it frequently.*

**NEXT ACTION:** Install @noble/post-quantum npm package to enable PQC, then implement ARC-8 PWA Phase 1 (See docs/POST_QUANTUM_CRYPTOGRAPHY_SPEC.md + docs/STATIC_ASSETS_PWA_SPEC.md)
