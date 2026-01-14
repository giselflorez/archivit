# ARCHIV-IT Agent Instructions

> **MANDATORY**: This file is automatically loaded by Claude Code at session start.
> **DO NOT SKIP ANY SECTION** - Every section contains critical context.

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

### 22 NORTHSTAR Masters
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

## API ENDPOINT FOR AGENT INITIALIZATION

If you need programmatic context, call:
```bash
curl http://localhost:5001/api/agent/init
```

This returns JSON with all critical context for automated systems.

---

*This file is loaded automatically by Claude Code. Compliance is mandatory.*
*Last updated: 2026-01-12*
