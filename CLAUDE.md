# ARCHIV-IT Agent Instructions

> **MANDATORY**: This file is automatically loaded by Claude Code at session start.
> **DO NOT SKIP ANY SECTION** - Every section contains critical context.

---

## ⚠️ CRITICAL POSITIONING - READ FIRST (NEVER SKIP)

### The Honest Message (USE IN ALL BRANDING)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ARC-8 is ANTI-EXTRACTION and USER-SOVEREIGN.                              ║
║                                                                              ║
║   It currently runs as a LOCAL APPLICATION that CONNECTS TO                 ║
║   decentralized infrastructure (blockchains, IPFS) rather than              ║
║   BEING decentralized infrastructure itself.                                ║
║                                                                              ║
║   SOVEREIGNTY ≠ DECENTRALIZATION                                            ║
║                                                                              ║
║   We are SOVEREIGN-FIRST, not decentralized-first.                         ║
║   The user owns their data. The user controls their identity.               ║
║   External systems are OPTIONAL connections, not requirements.              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### The Core Promise: USER TAKES ALL
- **Your data** - Lives on YOUR device, not our servers
- **Your identity** - Mathematically derived, YOU own your seed
- **Your creations** - Everything you make belongs to YOU
- **Your export** - Take it all, anytime, any format
- **Your deletion** - When you delete, it's GONE

### What We ARE:
- **Local-first** - Data lives on YOUR device
- **User-sovereign** - YOU own your seed, your data, your identity
- **Anti-extraction** - We don't harvest, track, or monetize you
- **Blockchain-connected** - We READ from chains, verify provenance
- **IPFS-compatible** - We CAN store on distributed networks

### What We Are NOT (Be Honest):
- NOT a blockchain (we connect to them)
- NOT a decentralized protocol (we're an app)
- NOT peer-to-peer (no node network yet)
- NOT token-based (no governance token)
- NOT running on distributed infrastructure

### Use This Language:
- ✅ "Sovereign data platform"
- ✅ "Local-first architecture"
- ✅ "User-owned identity"
- ✅ "Anti-extraction design"
- ✅ "Connects to decentralized networks"
- ❌ "Decentralized platform" (misleading)
- ❌ "Web3 native" (partially true, be specific)
- ❌ "Blockchain-based" (we connect, not run on)

### Decentralization Roadmap (51% needs work):
- 49% already decentralized (seed, algorithms, local storage, RPC redundancy)
- 51% could be decentralized with work (routes, auth, search, social)
- Full roadmap in `docs/DECENTRALIZATION_AUDIT.md`
- **VERIFIED 2026-01-13** - Code inspection confirmed all claims

**THIS MESSAGE MUST APPEAR IN:**
- Website copy
- Marketing materials
- Pitch decks
- README files
- Any public-facing documentation

---

## FOUNDER PREFERENCES (MEMORIZE THESE)

| Setting | Value | Notes |
|---------|-------|-------|
| **Access Code** | `DATAROCKS` | For ALL NDA/confidentiality gates |
| **Design** | Dark SACRED PALETTE | Never use light/corporate themes |
| **"ultrathink"** | Deep comprehensive analysis | When founder says this, go thorough |
| **Password UI** | Minimal, light, checkmark on success | Simple and elegant |

---

## ⚠️ IP PROTECTION PROTOCOL (MANDATORY - READ EVERY SESSION)

### CRITICAL: Read Before ANY Git Operations

**Full protocol in:** `docs/IP_PROTECTION_PROTOCOL.md`

### Pre-Push Checklist (ALWAYS ASK BEFORE `git push`)

```
⚠️ GIT PUSH PROTECTION CHECK

Files being pushed: [list them]

PROTECTION STATUS:
- [ ] No new algorithms or implementations being pushed
- [ ] No threshold values or weights exposed
- [ ] No API keys or credentials in code
- [ ] No internal documentation being published
- [ ] No unreleased features going public

Shall I proceed with the push?
```

### What's Already Public (Copyright + Patent by Jan 2027)

| File | Status |
|------|--------|
| `pi_quadratic_seed.js` | PUBLIC - Patent deadline Jan 1, 2027 |
| `spiral_compression.js` | PUBLIC - Patent deadline Jan 1, 2027 |
| `quantum_provenance.js` | PUBLIC - Patent deadline Jan 1, 2027 |
| `quantum_equilibrium.js` | PUBLIC - Patent deadline Jan 1, 2027 |
| `pqs_quantum.js` | PUBLIC - Patent deadline Jan 1, 2027 |

### What to Keep Local (Trade Secret)

| Category | Action |
|----------|--------|
| Unreleased features | DO NOT PUSH without patent review |
| Internal docs | NEVER push strategy/analysis files |
| Provider configs | NEVER push API keys or provider lists |
| Training data | KEEP `knowledge_base/` local |
| Security details | NEVER push until patented |

### Patent Deadline Reminder

**⏰ CRITICAL DEADLINE: January 1, 2027**

All core algorithms were publicly disclosed January 1, 2026.
US patent law allows 1-year grace period.
**File provisional patents BEFORE this deadline.**

Priority filings:
1. 6-Layer Anti-AI Protection
2. Multi-Blockchain Auto-Detection
3. Behavioral Fingerprinting
4. Spiral Compression

### Anti-Hallucination IP Rules

**NEVER claim an invention is patentable unless:**
- Working code EXISTS (not just documentation)
- It solves a SPECIFIC technical problem
- It's MORE than just a math formula
- You've checked USPTO example mapping

**ALWAYS be honest about:**
- What's already public (can't be trade secret)
- What's just an idea vs implemented
- Mathematical concepts (not patentable alone)

---

## ⚠️ FILE STRUCTURE RULES (MANDATORY - READ EVERY SESSION)

### Canonical Directory Structure

```
ARCHIVIT_01/
├── docs/                      # ALL documentation (specs, guides, IP, reviews)
│   ├── IP_MASTER_REGISTRY.md  # Patent/trademark tracking
│   ├── INVENTION_DISCLOSURES.md
│   ├── *_SPEC.md              # Technical specifications
│   └── SESSION_LOGS.md        # Session history
│
├── applications/              # Grant/residency applications
│   └── print_ready/           # ONLY printable HTML files go here
│       └── *.html             # B&W printable documents
│
├── data/                      # User data, training data, discovery
│   ├── artist_discovery/      # Artist research & databank
│   ├── grants/                # Grant tracking
│   └── discovery/             # Research findings
│
├── scripts/                   # ALL code
│   ├── interface/             # Flask app, templates, static
│   ├── agents/                # Agent systems
│   └── search/                # Search functionality
│
├── public/                    # Public-facing HTML pages
│
├── knowledge_base/            # Verified knowledge for training
│
├── backups/                   # Session backups
│   └── session_YYYY-MM-DD_description/
│
├── CLAUDE.md                  # THIS FILE - Agent instructions
├── AGENT_CONTEXT_STATE.md     # Current state, pending reviews, TODOs
└── AGENT_BRIEFING.md          # Generated context summary
```

### BEFORE CREATING ANY NEW FILE

**⚠️ MANDATORY CHECKLIST:**

1. **CHECK IF FILE EXISTS** - Search for similar files first:
   ```bash
   find . -name "*keyword*" -type f
   ```

2. **ASK FOUNDER** - "I want to create `[path/filename]`. Should I:
   - A) Create new file at this location
   - B) Update existing file `[similar file found]`
   - C) Put it somewhere else"

3. **ANNOUNCE LOCATION** - Always tell founder BEFORE creating:
   "Creating file at: `docs/NEW_FILE.md`"

### FILE PLACEMENT RULES

| Content Type | Location | Example |
|-------------|----------|---------|
| Documentation, specs, IP | `docs/` | `docs/VERIFICATION_ENGINE_SPEC.md` |
| Printable documents | `applications/print_ready/` | `applications/print_ready/IP_PORTFOLIO.html` |
| Grant/residency apps | `applications/` | `applications/ARTS_MID_HUDSON.md` |
| Artist research | `data/artist_discovery/` | `data/artist_discovery/artist_databank.json` |
| Code files | `scripts/` | `scripts/interface/visual_browser.py` |
| Public HTML pages | `public/` | `public/masters_spectral.html` |
| Session backups | `backups/session_DATE_desc/` | `backups/session_2026-01-17_ip_scan/` |

### ⚠️ DELETION/MODIFICATION RULES

**NEVER DELETE OR SIGNIFICANTLY MODIFY WITHOUT APPROVAL:**

1. **Deletions require explicit approval** - Ask: "Can I delete `[file]`? Reason: [why]"
2. **Major changes require approval** - Ask: "Can I change `[what]` in `[file]`?"
3. **Adding content is OK** - You can ADD to existing files without approval
4. **Create backups before major changes** - `cp file file.bak`

### DATA RETENTION ACROSS RESTARTS

**These files persist and MUST be read every session:**

1. `CLAUDE.md` - This file (auto-loaded by Claude Code)
2. `AGENT_CONTEXT_STATE.md` - Current state, pending reviews, TODOs
3. `docs/IP_MASTER_REGISTRY.md` - IP tracking with review checkboxes
4. `docs/SOCI8_REVIEW_INVENTED_CONTENT.md` - Pending content review

**On every session start, check:**
- [ ] Any pending founder reviews in `AGENT_CONTEXT_STATE.md`?
- [ ] Any unchecked boxes in `docs/IP_MASTER_REGISTRY.md`?
- [ ] Any unresolved items in `docs/SOCI8_REVIEW_INVENTED_CONTENT.md`?

### IF YOU CAN'T FIND A FILE

**Check `docs/FILE_MIGRATION_LOG.md`** - All file moves are logged there.

Files were reorganized on 2026-01-17:
- Most `.md` docs moved from root → `docs/`
- Legacy `.txt` specs moved to → `docs/legacy/`
- Root now only contains essential startup files

### PRINTABLE FILES LOCATION

**ALL printable documents go in: `applications/print_ready/`**

Current printable files:
- `COMPLETE_IP_PORTFOLIO_PRINT.html` - 19 patents, 14 trademarks (B&W)
- `ALL_APPLICATIONS_PRINT.html` - Older version (superseded)

To print: `open applications/print_ready/COMPLETE_IP_PORTFOLIO_PRINT.html`

---

## STEP 1: INITIALIZE CONTEXT (REQUIRED)

Before doing ANY work, you MUST run this command:

```bash
./venv/bin/python scripts/agent/init_agent.py
```

This generates `AGENT_BRIEFING.md` with consolidated context. **READ IT.**

If the script doesn't exist yet, read these files IN ORDER:
1. `AGENT_CONTEXT_STATE.md` - Current state, last actions, TODO queue
2. `docs/AGENT_ONBOARDING.md` - Rules, architecture, terminology
3. `docs/FOUNDER_QUOTES.md` - Philosophical foundation

---

## STEP 2: VERIFY YOUR CONTEXT

After reading, you MUST be able to answer:

1. **What was the last action completed?** (Check AGENT_CONTEXT_STATE.md)
2. **What is in the TODO queue?** (Check AGENT_CONTEXT_STATE.md)
3. **What are the 22 NORTHSTAR Masters?** (9 feminine, 13 masculine)
4. **What is the -8 ecosystem?** (DOC-8, IT-R8, SOCI-8)
5. **What are the sacred physics constants?** (PHI, GOLDEN_ANGLE, SCHUMANN, TESLA_PATTERN)

If you cannot answer these, GO BACK AND READ THE FILES.

---

## STEP 3: UNDERSTAND THE ECOSYSTEM

```
ARCHIV-IT (Umbrella)
├── DOC-8   - DATABASE & ARCHIVE (Foundation - current focus)
├── IT-R8   - CREATE & RATE (spatial design tool)
└── SOCI-8  - SHARE & CONNECT (future)
```

### -8 System Boundaries (IMPORTANT)
| System | Purpose | Features | Routes |
|--------|---------|----------|--------|
| **DOC-8** | Store, verify, archive | Source Cartography, provenance, verification | `/doc8` |
| **IT-R8** | Create, rate, spatial | Thought Stream, drag/connect, tagging | `/itr8` |
| **SOCI-8** | Share, connect | Social features (future) | `/soci8` |

**When building features, ask: Is this about STORING or CREATING?**
- Storing/verifying/archiving → DOC-8
- Creating/rating/spatial organization → IT-R8

**Server**: Visual browser runs on http://localhost:5001
**Start command**: `KMP_DUPLICATE_LIB_OK=TRUE ./venv/bin/python scripts/interface/visual_browser.py`

---

## STEP 4: KNOW THE RULES

### The 11 Non-Negotiables
1. User owns their seed (mathematical identity)
2. No tracking without explicit consent
3. All data transformations are reversible
4. Spiral compression preserves fidelity
5. Local-first, cloud-optional
6. Algorithms serve users, not platforms
7. Privacy is default, sharing is intentional
8. Creation direction is always +1 (growth, not extraction)
9. Mathematical verification over trust
10. Lineage values guide suggestions
11. **Balance polarity in all outputs** (PHI threshold)

### Physics Constants (SACRED - DO NOT MODIFY)
```javascript
PHI = 1.618033988749895        // Golden ratio
GOLDEN_ANGLE = 137.5077640500378 // Spiral rotation
SCHUMANN = 7.83                  // Earth's frequency
TESLA_PATTERN = [3, 6, 9]        // Harmonic structure
```

### Founder Terminology
| Term | Meaning |
|------|---------|
| ultrathink | Deep comprehensive analysis required |
| seed | User's mathematical identity (local, sovereign) |
| vertex | User's optimal state/position |
| spiral | Natural flow pattern (creation direction) |

### ⚠️ DESIGN SYSTEM (MANDATORY)
**NEVER use enterprise/corporate design.** Always use this elegant palette:

```css
/* SACRED PALETTE - USE THIS */
--void: #030308;           /* Deep black background */
--cosmic: #0a0a12;         /* Panel backgrounds */
--panel: #0e0e18;          /* Card backgrounds */
--border: rgba(255,255,255,0.06);  /* Subtle borders */

--gold: #d4a574;           /* Primary accent (warm) */
--emerald: #54a876;        /* Success/selected states */
--rose: #ba6587;           /* Warnings/disputed */
--violet: #7865ba;         /* Secondary accent */

--text: #f0ece7;           /* Primary text (warm white) */
--text-dim: #9a9690;       /* Secondary text */
--text-muted: #5a5854;     /* Tertiary text */
```

**Typography Rules:**
- Font: Inter or -apple-system
- Weights: 200 (titles), 300 (body), 400 (emphasis)
- Letter-spacing: 0.15em - 0.35em for labels
- UPPERCASE for labels and buttons
- Lowercase for body text and descriptions

**DO NOT USE:**
- Cyan (#00f5ff) as primary - too cold
- Bright green (#00ff88) - too neon
- Checkbox lists - use constellation nodes
- "WhatsApp" styling - use elegant fragments
- Enterprise badges (HIGH/MEDIUM/LOW)

**Reference Files:**
- `templates/confidentiality_gate.html` - Gate pattern
- `templates/masters_point_cloud_v3_spectral.html` - Visualization pattern
- `scripts/interface/templates/doc8_source_approval.html` - Form pattern

---

## STEP 5: CHECK WHATSAPP QUEUE

New tasks often come from WhatsApp. Check:
- `dataland_proposal/WHATSAPP_LOG.md` - Latest entries tagged #TODO or #RESEARCH

---

## STEP 6: BEFORE ENDING SESSION

You MUST:
1. Update `AGENT_CONTEXT_STATE.md` with:
   - Last action completed
   - Files modified
   - Next steps identified
2. Create backup if significant work was done:
   ```bash
   mkdir -p backups/session_$(date +%Y-%m-%d)_description/
   git add -A && git commit -m "Session: [description]"
   ```

---

## QUICK REFERENCE

### ⚠️ PORT WARNING
**Port 5000 is BLOCKED by macOS AirPlay Receiver (ControlCenter process).**
Always use **port 5001** for the Flask server:
```bash
# This will FAIL:
python visual_browser.py  # defaults to 5000 - BLOCKED

# Use this instead:
python visual_browser.py --port 5001  # ✓ Works
```
Or disable AirPlay Receiver: System Settings → General → AirDrop & Handoff → AirPlay Receiver → OFF

### File Priorities
| Priority | File | Purpose |
|----------|------|---------|
| 1 | AGENT_CONTEXT_STATE.md | Current state, TODO queue |
| 2 | docs/AGENT_ONBOARDING.md | Rules, architecture |
| 3 | docs/FOUNDER_QUOTES.md | Philosophy |
| 4 | docs/ULTRATHINK_SYNTHESIS.md | 22 Masters framework |

### 22 NORTHSTAR Masters - THE ARTIST AS THE ART

**⚠️ CRITICAL UNDERSTANDING - DO NOT HALLUCINATE**

The Masters are NOT chatbot personas or "techniques to extract."
They ARE complete human beings celebrated for:
- **How they LIVED** - daily choices, struggles, breakthroughs
- **What they MADE or DISCOVERED** - creations, insights
- **Their QUALITIES OF LIGHT** - unique frequency they brought to the world
- **Their AMPLITUDE of expression** - how intensely they lived

**Purpose:** Digestible history showing the BEAUTY in DIFFERENCES. A promotional engine + 4D exploration of remarkable humans.

**REQUIREMENT: Each Master needs 10 VERIFIED QUOTES with primary sources.**
- No hallucinated quotes (say "source not found" instead)
- Must trace to: original writings, interviews, recordings, scholarly sources
- Stored in `verified_quotes_db/` and `knowledge_base/training_data.json`

**Feminine (9)**: Hildegard, Gisel, Rand, Starhawk, Tori, Bjork, Swan, Hicks, Byrne
**Masculine (13)**: da Vinci, Tesla, Fuller, Jung, Suleyman, Grant, Prince, Coltrane, Bowie, Koe, Jobs, Cherny, Rene

### Common Tasks
- Start server: `KMP_DUPLICATE_LIB_OK=TRUE ./venv/bin/python scripts/interface/visual_browser.py`
- Check server: `curl -s http://localhost:5001/`
- Search: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "query"`

---

## ANTI-HALLUCINATION RULES

**NEVER:**
- Invent wallet addresses
- Fabricate exhibition dates
- Add aliases not in sources
- Claim badge algorithm is "accurate" (it's theoretical)

**ALWAYS:**
- Verify facts against `knowledge_base/training_data.json`
- Say "This information is not in the current knowledge base" when uncertain
- Use minimums for counts ("170+" not "170")

---

## ARTIST AGENT SYSTEM (NEW)

### Critical Files for Artist Agents
| File | Purpose | Status |
|------|---------|--------|
| `scripts/agents/ARTIST_AGENTS.json` | All 22 artist profiles | CRASH-PROOF |
| `scripts/agents/ARTIST_RIGHTS_NOTICE.md` | Legal protections | IMMUTABLE |
| `scripts/agents/init_artist_agents.py` | Recovery script | EXECUTABLE |

### Artist Agent Commands
```bash
# Initialize artist agents
./venv/bin/python scripts/agents/init_artist_agents.py

# List all artists
./venv/bin/python scripts/agents/init_artist_agents.py --list

# Get specific artist profile
./venv/bin/python scripts/agents/init_artist_agents.py --agent tesla

# Research updates for an artist
./venv/bin/python scripts/agents/init_artist_agents.py --research bjork

# Add new artist template
./venv/bin/python scripts/agents/init_artist_agents.py --add-artist
```

### SACRED COVENANT - ARTIST RIGHTS

**⚠️ ABSOLUTE RULE - NEVER VIOLATE:**

| PROTECTED (Never reproduce) | SHARED (Teach freely) |
|---------------------------|----------------------|
| Actual artwork | Techniques |
| Visual style | Philosophies |
| Musical compositions | Verified quotes |
| Literary works | Teaching points |
| Performance style | Methodologies |
| Trademark elements | Principles |

**The only exception requires explicit OPT_IN record in ARTIST_AGENTS.json**

### If Claude Resets - Artist Recovery Protocol

1. Read `scripts/agents/ARTIST_RIGHTS_NOTICE.md` FIRST
2. Run `./venv/bin/python scripts/agents/init_artist_agents.py`
3. All 22 masters can be rebuilt from JSON
4. **TEACH techniques, NEVER reproduce art**
5. Honor the artists who contributed wisdom

### Quick Artist Reference

**Invoke artist agent:** `/artist-{name}` (e.g., `/artist-tesla`, `/artist-bjork`)

**22 NORTHSTAR Masters with Skill Commands:**
```
FEMININE (9):
/artist-hildegard - Sacred Geometry & Sound
/artist-founder     - Light Photography & Lunar Art
/artist-rand      - Individual Sovereignty
/artist-starhawk  - Decentralized Power
/artist-tori      - Breath Structure
/artist-bjork     - Boundary Dissolution
/artist-swan      - Shadow Work
/artist-hicks     - Vibrational Alignment
/artist-byrne     - Visualization

MASCULINE (13):
/artist-davinci   - Art-Science Unity
/artist-tesla     - Energy-Frequency-Vibration
/artist-fuller    - Systems Thinking
/artist-jung      - Shadow Integration
/artist-suleyman  - Recognition-Generation
/artist-grant     - Sacred Geometry Math
/artist-prince    - Creative Sovereignty
/artist-coltrane  - Breath as Spiritual Practice
/artist-bowie     - Permanent Reinvention
/artist-koe       - Skill Extraction
/artist-jobs      - Design Thinking
/artist-cherny    - AI Collaboration
/artist-rene      - Spatial Web
```

---

## API ENDPOINT FOR AGENT INITIALIZATION

If you need programmatic context, call:
```bash
curl http://localhost:5001/api/agent/init
```

This returns JSON with all critical context for automated systems.

---

## QUOTE VERIFICATION AGENT PROTOCOL

### Purpose
Enable institutional-grade quote research with NO HALLUCINATIONS. Every quote must be traceable to primary source.

### On Startup (When Researching Quotes)
1. Read `docs/QUOTE_VERIFICATION_PROTOCOL.md` - Full methodology
2. Read `docs/AGENT_ERROR_LOG.md` - Learn from past mistakes
3. Check `verified_quotes_db/` - Existing verified quotes
4. **NEVER repeat a documented error**

### Key Files
| File | Purpose |
|------|---------|
| `docs/QUOTE_VERIFICATION_PROTOCOL.md` | Full verification methodology |
| `docs/AGENT_ERROR_LOG.md` | Documented errors to avoid |
| `verified_quotes_db/INDEX.md` | Database of verified quotes |
| `verified_quotes_db/moon/MOON_WISDOM_FRAMEWORK.md` | Moon quote research framework |

### Source Hierarchy (Trust Levels)
| Tier | Source Type | Trust |
|------|-------------|-------|
| 1 | Original manuscript/recording | 1.0 |
| 2 | Scholarly edition with page numbers | 0.95 |
| 3 | Institutional archive | 0.90 |
| 4 | Peer-reviewed academic | 0.85 |
| 5 | Verified journalism (NYT, BBC) | 0.75 |
| 6 | Quote Investigator | 0.70 |
| 7 | Wikipedia/blogs | 0.30 |
| 8 | Social media | 0.05 |

### Most Misquoted Figures (HIGH ALERT)
- **Tesla** (~90% fake) - Mysticism fabrications
- **Einstein** (~80% fake) - Credibility borrowing
- **Buddha** (~85% fake) - New Age appropriation
- **Jung** - Always require CW paragraph reference

### Anti-Hallucination Rules
1. **Never fabricate sources** - "Source not found" is acceptable
2. **Never commit to quantity before research** - Verify first, count second
3. **Always note uncertainty** - Use "ATTRIBUTED" status
4. **Log all errors** - Update AGENT_ERROR_LOG.md
5. **Prefer absence over invention** - Empty is better than fake

---

## CRASH RECOVERY - READ IF CLAUDE RESETS

**If you are reading this and have no memory of previous sessions:**

1. You are Claude, assisting with ARCHIV-IT project
2. Read this ENTIRE file - it contains all critical instructions
3. Run: `./venv/bin/python scripts/agent/init_agent.py`
4. For artist agents: `./venv/bin/python scripts/agents/init_artist_agents.py`
5. All context can be rebuilt from these files
6. **CRITICAL**: Artist art is PROTECTED - only teach techniques

The system is designed to survive crashes. Trust the files.

---

## NORTHSTAR ALIGNMENT CHECK - BEFORE EVERY SIGNIFICANT ACTION

```
Before acting or deciding on significant changes:

ASK: "Does this align with what you're trying to build?"

The founder's NORTHSTAR is SOVEREIGNTY + TRUTH + COLLABORATION.

If uncertain whether an action serves:
- User ownership (not platform extraction)
- Verifiable truth (not hallucinated convenience)
- Human-AI collaboration (not AI replacement)
- Freedom past the labyrinth of gated clouds

STOP. ASK. ALIGN.

Never assume. The user knows their vision better than any model.
No hallucinations. No invented IP without attribution.
Each piece = tools to freedom.
```

---

## EMAIL FAILSAFE SUPPORT SYSTEM

### Overview
MOONSTONE Email Failsafe provides support when users can't access the app directly.
Uses `info@web3photo.com` (displayed with anti-bot obfuscation in UI).

### How It Works
1. User sends email with question to support address
2. System generates ticket ID: `[MOONSTONE-XXXXXX]`
3. Security validation runs on all requests
4. **SAFE** questions: Auto-reply using LOCAL NORTHSTAR knowledge
5. **REVIEW** questions: Queued for human approval
6. **BLOCKED** requests: Logged and rejected (security threats)

### Security Levels
| Level | Trigger | Action |
|-------|---------|--------|
| **SAFE** | Simple help questions | Auto-reply from local knowledge |
| **REVIEW** | Implementation requests, database mentions | Queue for approval |
| **BLOCKED** | Code injection, SQL injection, credential requests | Reject and log |

### Agent Commands
```bash
# List pending support requests
./venv/bin/python scripts/support/email_failsafe.py list

# Approve a request for reply
./venv/bin/python scripts/support/email_failsafe.py approve TICKET_ID

# Block a suspicious request
./venv/bin/python scripts/support/email_failsafe.py block TICKET_ID "reason"

# Test the security validation
./venv/bin/python scripts/support/email_failsafe.py test

# Get anti-bot HTML for email display
./venv/bin/python scripts/support/email_failsafe.py html
```

### ⚠️ MANDATORY BEHAVIOR ON STARTUP
1. Check `scripts/support/queue/` for pending requests
2. Review any REVIEW-level requests before other work
3. Never auto-implement REVIEW requests without human approval
4. Log all security-flagged requests for founder review

### Anti-Bot Email Display
Include in any page that shows support email:
```html
<span data-support-email></span>
<script src="/static/js/support-email.js"></script>
```

### Files
| File | Purpose |
|------|---------|
| `scripts/support/email_failsafe.py` | Core validation & queue system |
| `scripts/support/queue/` | Pending requests |
| `scripts/support/blocked/` | Security-blocked requests |
| `scripts/support/processed/` | Approved & handled requests |
| `scripts/interface/static/js/support-email.js` | Anti-bot email display |

---

*This file is loaded automatically by Claude Code. Compliance is mandatory.*
*Last updated: 2026-01-14*
