# DOC-8 SOURCE PRE-APPROVAL INTERFACE
## Transparent Research Verification for NORTHSTAR Knowledge Bank

**Created:** January 12, 2026
**Status:** DESIGN SPECIFICATION
**Priority:** HIGH - User-requested feature for research transparency

---

## THE PROBLEM

When AI agents research topics, users cannot:
1. See which sources will be queried BEFORE research starts
2. Verify if sources are legitimate for their standards
3. Control what enters their NORTHSTAR knowledge bank
4. Understand the full scope of a research query

**Current Flow (Opaque):**
```
User Request → AI Researches (black box) → Results appear
```

**Proposed Flow (Transparent):**
```
User Request → Source List Generated → User Approves → ULTRATHINK Executes → Verified Results
```

---

## THE SOLUTION: SOURCE PRE-APPROVAL FLOW

### Step 1: Query Analysis
When user requests research, DOC-8 first analyzes the query and generates:
- List of ALL potential sources to query
- Type of each source (academic, interview, video, book, etc.)
- Verification status of each source
- Estimated reliability score

### Step 2: Pre-Approval Interface
Clean, calm interface displays:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   RESEARCH QUERY: "Verified Tesla quotes from institutional sources"       │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                             │
│   SOURCES TO BE QUERIED (12 total)                                         │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   [✓] Tesla Universe (teslauniverse.com)                           │  │
│   │       Type: Archive | Reliability: HIGH | Contains: Articles       │  │
│   │                                                                     │  │
│   │   [✓] Quote Investigator (quoteinvestigator.com)                   │  │
│   │       Type: Verification | Reliability: HIGH | Contains: Analysis  │  │
│   │                                                                     │  │
│   │   [✓] Wikiquote (en.wikiquote.org)                                 │  │
│   │       Type: Wiki | Reliability: MEDIUM | Contains: Sourced quotes  │  │
│   │                                                                     │  │
│   │   [✓] Internet Archive (archive.org)                               │  │
│   │       Type: Archive | Reliability: HIGH | Contains: Primary docs   │  │
│   │                                                                     │  │
│   │   [ ] Pinterest (pinterest.com)                                    │  │
│   │       Type: Social | Reliability: LOW | Auto-excluded              │  │
│   │                                                                     │  │
│   │   [✓] Tesla Science Center (teslasciencecenter.org)                │  │
│   │       Type: Institution | Reliability: HIGH | Contains: Research   │  │
│   │                                                                     │  │
│   │   ... (scroll for more)                                            │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                             │
│   QUERY PARAMETERS                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ Depth: [●●●●○] Deep    Time Limit: [○ 30s  ● 2min  ○ 5min]        │  │
│   │ Auto-exclude LOW reliability: [✓]   Include videos: [✓]            │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                             │
│   [SELECT ALL HIGH]  [DESELECT ALL]  [CANCEL]  [▶ START RESEARCH]          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 3: ULTRATHINK Execution
Once sources approved:
- All queries run with Y auto-approval
- Only approved sources are queried
- Progress shown in real-time
- Results tagged with source provenance

### Step 4: Results with Full Provenance
Each result includes:
```json
{
  "quote": "Be alone, that is the secret of invention...",
  "author": "Nikola Tesla",
  "source": {
    "publication": "The New York Times",
    "date": "April 8, 1934",
    "page": "X9",
    "interviewer": "Orrin E. Dunlap Jr.",
    "title": "An Inventor's Seasoned Ideas",
    "verification_url": "quoteinvestigator.com/2021/10/06/invent-alone/",
    "archive_url": "archive.org/details/...",
    "reliability": "HIGH",
    "approved_by_user": true,
    "query_timestamp": "2026-01-12T14:30:00Z"
  }
}
```

---

## SOURCE RELIABILITY CLASSIFICATION

### HIGH Reliability (Auto-approved by default)
- **Academic databases**: JSTOR, Google Scholar, university archives
- **Verification sites**: Quote Investigator, Snopes, Check Your Fact
- **Primary archives**: Internet Archive, Library of Congress, National Archives
- **Official institutions**: Museums, foundations, research centers
- **Published books**: With ISBN, page numbers, verifiable editions

### MEDIUM Reliability (User choice)
- **Wikipedia/Wikiquote**: Requires source citations present
- **News outlets**: Established publications with editorial standards
- **Documentary sources**: With credits and production information
- **Professional interviews**: Published in established media

### LOW Reliability (Auto-excluded by default)
- **Social media**: Pinterest, Facebook, Instagram, TikTok
- **Meme sites**: Quote collections without sources
- **Content farms**: Sites that aggregate without verification
- **User-generated**: Forums, comments, unmoderated wikis
- **Anonymous sources**: No attribution or verification path

---

## UI/UX PRINCIPLES (DOC-8 Design System)

### Visual Language
- **Background**: `#0a0a0f` (void black) - calm, non-distracting
- **Text**: `#faf8f5` (warm white) - easy reading
- **Approved sources**: `#00ff88` (fuller-green) - safe, verified
- **Excluded sources**: `#ff6b6b` (muted red) - warning, excluded
- **Pending**: `#c0c0c0` (moon-silver) - awaiting decision
- **Borders**: `rgba(0,245,255,0.2)` - subtle electric cyan

### Interaction Design
- **Large click targets**: Minimum 44px touch targets
- **Clear checkboxes**: Obvious state (checked/unchecked)
- **Scrollable list**: Smooth scroll, clear scroll indicators
- **Keyboard navigation**: Tab through sources, Space to toggle
- **Batch actions**: Select All High / Deselect All / Invert

### Accessibility
- **High contrast**: All text meets WCAG AA
- **Screen reader**: Full aria labels for all controls
- **Focus indicators**: Clear visible focus ring
- **Reduced motion**: Option to disable animations

---

## DATA FLOW ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOC-8 RESEARCH FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

     USER REQUEST
          │
          ▼
┌─────────────────────┐
│  QUERY ANALYZER     │  ← Parses intent, identifies domains
│  (Local processing) │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  SOURCE GENERATOR   │  ← Generates list of potential sources
│  (Pattern matching) │    based on query type + historical usage
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  RELIABILITY SCORER │  ← Scores each source against database
│  (Local database)   │    of known reliable/unreliable sources
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  PRE-APPROVAL UI    │  ← User reviews and approves sources
│  (Interactive)      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ULTRATHINK ENGINE  │  ← Executes with auto-Y for approved
│  (AI Research)      │    sources only
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  PROVENANCE TAGGER  │  ← Tags all results with full source
│  (Metadata)         │    chain and verification status
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  NORTHSTAR BANK     │  ← Stores verified knowledge with
│  (Local storage)    │    complete provenance trail
└─────────────────────┘
```

---

## INTEGRATION WITH NORTHSTAR KNOWLEDGE BANK

### Storage Structure
```
northstar_knowledge_bank/
├── masters/
│   ├── tesla/
│   │   ├── verified_quotes.json      # All verified quotes
│   │   ├── video_transcripts/        # Transcribed video content
│   │   ├── source_documents/         # Primary source PDFs
│   │   └── provenance_chain.json     # Full verification trail
│   ├── jung/
│   ├── fuller/
│   └── ...
├── research_sessions/
│   ├── 2026-01-12_tesla_quotes/
│   │   ├── approved_sources.json     # Which sources user approved
│   │   ├── query_parameters.json     # Research settings used
│   │   ├── raw_results.json          # All results before filtering
│   │   └── verified_results.json     # Final verified output
│   └── ...
├── source_reputation/
│   ├── high_reliability.json         # Known good sources
│   ├── low_reliability.json          # Known bad sources
│   └── user_preferences.json         # User's custom inclusions/exclusions
└── TODO_RESEARCH.md                  # Queue from WhatsApp imports
```

### #TODO #RESEARCH Tags
Items tagged in WhatsApp automatically queue to:
```markdown
# TODO_RESEARCH.md

## Pending Research Queries

### 2026-01-12 (from WhatsApp)
- [ ] "Find verified Hildegard of Bingen quotes about music"
- [ ] "Research John Coltrane interview transcripts"
- [x] "Verified Tesla quotes" → COMPLETED 2026-01-12

### Sources Auto-Suggested
Based on query patterns, these sources would be pre-approved:
- teslauniverse.com (HIGH)
- quoteinvestigator.com (HIGH)
- archive.org (HIGH)
```

---

## IMPLEMENTATION PHASES

### Phase 1: Source Database
- [ ] Build known-sources database with reliability scores
- [ ] Create source categorization system
- [ ] Implement pattern matching for query → sources

### Phase 2: Pre-Approval UI
- [ ] Design clean scrollable source list
- [ ] Implement toggle controls
- [ ] Add batch selection actions
- [ ] Build query parameter controls

### Phase 3: ULTRATHINK Integration
- [ ] Connect approval flow to research execution
- [ ] Implement auto-Y for approved sources
- [ ] Add real-time progress display

### Phase 4: Provenance Tagging
- [ ] Build metadata attachment system
- [ ] Create provenance chain storage
- [ ] Implement verification trail

### Phase 5: NORTHSTAR Integration
- [ ] Connect to knowledge bank storage
- [ ] Implement WhatsApp → TODO pipeline
- [ ] Build research queue system

---

## USER STORY

> As a researcher building the NORTHSTAR Knowledge Bank, I want to see ALL sources
> that will be queried BEFORE research begins, so I can verify each source meets
> my standards for legitimate information, and ensure only verified knowledge
> enters my local training data.

---

## ALIGNMENT WITH NORTH STAR PRINCIPLES

1. **SOVEREIGNTY**: User controls what sources are queried
2. **VERIFICATION**: All knowledge has provenance trail
3. **TRANSPARENCY**: No black-box research
4. **LOCAL-FIRST**: Source preferences stored locally
5. **CONSENT**: Every source must be explicitly approved

---

*This document specifies the DOC-8 Source Pre-Approval Interface for transparent, user-controlled research.*

**Next Steps:**
1. Build source reliability database
2. Design and implement UI components
3. Integrate with ULTRATHINK research flow
4. Connect to NORTHSTAR Knowledge Bank

---

*"Trust but verify" → "Verify then trust"*
