# WHATSAPP → NORTHSTAR AUTO-PIPELINE
## Automatic Import of Ideas, TODOs, and Research from WhatsApp

**Created:** January 12, 2026
**Status:** DESIGN SPECIFICATION
**Purpose:** Auto-capture WhatsApp entries to NORTHSTAR Knowledge Bank

---

## THE PROBLEM

The founder captures ideas, TODOs, and research notes in WhatsApp messages.
These need to automatically flow into the NORTHSTAR Knowledge Bank without manual copying.

**Current Flow (Manual):**
```
WhatsApp Message → Manual Copy → Paste to docs → Organize
```

**Proposed Flow (Automatic):**
```
WhatsApp Message → Export → Auto-Parse Tags → Route to Correct Queue → Available in Claude Context
```

---

## HASHTAG TAXONOMY (From WhatsApp Analysis)

### ACTION TAGS (Route to TODO Queue)
| Tag | Meaning | Destination |
|-----|---------|-------------|
| `#ACTION` | Immediate task | TODO_IMMEDIATE.md |
| `#TODO` | Future task | TODO_QUEUE.md |
| `#REQUEST` | Feature request | FEATURE_REQUESTS.md |
| `#MANDATE` | Non-negotiable | MANDATES.md (highest priority) |

### RESEARCH TAGS (Route to Research Queue)
| Tag | Meaning | Destination |
|-----|---------|-------------|
| `#research` | Investigation needed | RESEARCH_QUEUE.md |
| `#NEWIDEA` | Concept capture | IDEAS_BANK.md |
| `#CONCEPT` | Abstract idea | IDEAS_BANK.md |
| `#influences` | Inspiration sources | INFLUENCES.md |
| `#USECASE` | Application scenario | USE_CASES.md |

### AGENT TAGS (Route to Agent Context)
| Tag | Meaning | Destination |
|-----|---------|-------------|
| `#AGENT` | AI directive | AGENT_CONTEXT_STATE.md |
| `#AGENTNOTES` | Documentation note | AGENT_CONTEXT_STATE.md |
| `#DONTYOUDAREHALLUCINATE` | Accuracy mandate | AGENT_CONTEXT_STATE.md |
| `#remembereverythingieversaid` | Context retention | AGENT_CONTEXT_STATE.md |

### SYSTEM TAGS (Metadata)
| Tag | Meaning | Usage |
|-----|---------|-------|
| `[VERIFIED]` | Authenticated content | Mark as verified |
| `[ACTION]` | Executable command | Highlight for action |
| `[INSERT]` | Placeholder | Needs content |
| `[CREDIT]` | Attribution | Add credit |

---

## FILE STRUCTURE

```
northstar_knowledge_bank/
├── imports/
│   └── whatsapp/
│       ├── raw/                      # Raw WhatsApp exports
│       │   └── 2026-01-12_export.txt
│       └── parsed/                   # Parsed and categorized
│           └── 2026-01-12_parsed.json
│
├── queues/
│   ├── TODO_IMMEDIATE.md             # #ACTION items
│   ├── TODO_QUEUE.md                 # #TODO items
│   ├── RESEARCH_QUEUE.md             # #research items
│   ├── FEATURE_REQUESTS.md           # #REQUEST items
│   └── MANDATES.md                   # #MANDATE items (never delete)
│
├── banks/
│   ├── IDEAS_BANK.md                 # #NEWIDEA #CONCEPT
│   ├── INFLUENCES.md                 # #influences
│   ├── USE_CASES.md                  # #USECASE
│   └── MASTERS_VERIFIED_SOURCES.md   # Verified quotes
│
└── context/
    └── AGENT_CONTEXT_STATE.md        # Current session state
```

---

## PARSING RULES

### Rule 1: Tag Extraction
```
Input: "ultrathink the whole thing #research #TODO"
Output: {
  text: "ultrathink the whole thing",
  tags: ["#research", "#TODO"],
  routes: ["RESEARCH_QUEUE.md", "TODO_QUEUE.md"]
}
```

### Rule 2: Priority Levels
```
CRITICAL:  #MANDATE, #ACTION
HIGH:      #TODO, #REQUEST
MEDIUM:    #research, #NEWIDEA
LOW:       #CONCEPT, #influences
```

### Rule 3: Date Extraction
```
- Messages include timestamp from WhatsApp export
- Store original timestamp for temporal mapping
- Allow filtering by date range
```

### Rule 4: Founder Intent Preservation
```
- Keep exact wording including typos
- Preserve original hashtags
- Note line number from export for reference
```

---

## IMPORT PROTOCOL

### Step 1: Export from WhatsApp
```
1. Open WhatsApp chat
2. Settings → Export Chat → Without Media
3. Save to imports/whatsapp/raw/YYYY-MM-DD_export.txt
```

### Step 2: Parse Export
```
Claude reads raw export and:
1. Identifies messages with hashtags
2. Extracts text, tags, timestamp
3. Categorizes by destination file
4. Saves parsed JSON to imports/whatsapp/parsed/
```

### Step 3: Route to Queues
```
For each parsed message:
1. Check tags against taxonomy
2. Append to appropriate queue file
3. Mark as imported in parsed JSON
4. Update AGENT_CONTEXT_STATE.md with new items
```

### Step 4: Claude Context Update
```
New entries automatically visible when Claude reads:
- AGENT_CONTEXT_STATE.md (startup)
- Relevant queue files (when working on tasks)
```

---

## QUEUE FILE FORMAT

### TODO_QUEUE.md
```markdown
# TODO QUEUE
## Auto-imported from WhatsApp

### 2026-01-12 Imports
- [ ] "ultrathink the whole thing" #research
  Source: WhatsApp Line 267
  Added: 2026-01-12 14:30
  Priority: MEDIUM

- [ ] "release the #SWARM of 8" #ACTION
  Source: WhatsApp Line 461
  Added: 2026-01-12 14:30
  Priority: CRITICAL

### Completed
- [x] "verified quotes for masters" #TODO
  Completed: 2026-01-12
  Result: See MASTERS_VERIFIED_SOURCES.md
```

### RESEARCH_QUEUE.md
```markdown
# RESEARCH QUEUE
## Topics requiring investigation

### Pending Research
- [ ] Video interviews of masters (Jung BBC, Fuller lectures)
  Tags: #research #NORTHSTAR
  Source: Session 2026-01-12
  Priority: HIGH

- [ ] Transcribe key videos for cognitive mapping
  Tags: #research
  Source: WhatsApp
  Priority: MEDIUM

### Completed Research
- [x] Verified Tesla quotes
  Completed: 2026-01-12
  Result: docs/MASTERS_VERIFIED_SOURCES.md
```

---

## INTEGRATION WITH CLAUDE STARTUP

### Auto-Read Sequence (Updated)
```
1. AGENT_CONTEXT_STATE.md        ← Session state + recent imports
2. queues/TODO_IMMEDIATE.md      ← Critical items
3. queues/RESEARCH_QUEUE.md      ← Research needed
4. docs/AGENT_ONBOARDING.md      ← Core rules
```

### New Entries Alert
When new WhatsApp entries are imported, AGENT_CONTEXT_STATE.md shows:
```markdown
## NEW WHATSAPP IMPORTS (Since Last Session)
- 3 new #TODO items
- 1 new #MANDATE
- 2 new #research items

See queues/ folder for details.
```

---

## MANUAL QUICK-ADD (For Claude)

If user mentions "from WhatsApp" or pastes WhatsApp content:

```markdown
### Quick-Add Protocol
1. Identify hashtags in user message
2. Route to appropriate queue
3. Update AGENT_CONTEXT_STATE.md
4. Confirm: "Added to [QUEUE_NAME] with tags: [TAGS]"
```

---

## EXAMPLE WORKFLOW

**User sends:**
> "just sent this to whatsapp: research all John Coltrane interviews about spirituality #research #NORTHSTAR"

**Claude action:**
1. Parse: text="research all John Coltrane interviews about spirituality", tags=[#research, #NORTHSTAR]
2. Add to RESEARCH_QUEUE.md:
```markdown
- [ ] "research all John Coltrane interviews about spirituality"
  Tags: #research #NORTHSTAR
  Source: WhatsApp (user reported)
  Added: 2026-01-12
  Priority: MEDIUM
```
3. Update AGENT_CONTEXT_STATE.md work queue
4. Respond: "Added to RESEARCH_QUEUE.md with tags: #research #NORTHSTAR"

---

## MANDATES PRESERVATION

`#MANDATE` items are NEVER deleted, only marked complete:

```markdown
# MANDATES.md
## Non-Negotiable Requirements

### Active Mandates
- "NO HALLUCINATIONS - all quotes must be verified" #MANDATE
  Source: WhatsApp Line 349
  Status: ACTIVE (permanent)

- "data sovereignty - local-first always" #MANDATE
  Source: Core Philosophy
  Status: ACTIVE (permanent)

### Fulfilled Mandates (Preserved)
- "verify all Tesla quotes" #MANDATE
  Fulfilled: 2026-01-12
  Result: MASTERS_VERIFIED_SOURCES.md
```

---

## BENEFITS

1. **Nothing lost**: All WhatsApp ideas captured
2. **Auto-organized**: Tags route to correct queues
3. **Context ready**: Claude sees new items on startup
4. **Traceable**: Source line numbers preserved
5. **Prioritized**: Hashtag taxonomy sets priority
6. **Sovereign**: All data stays local

---

*This pipeline ensures every idea captured in WhatsApp flows automatically into the NORTHSTAR Knowledge Bank.*
