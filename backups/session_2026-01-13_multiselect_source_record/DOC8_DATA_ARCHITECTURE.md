# DOC-8 Data Architecture
## ULTRATHINK: Maximum Data Point Extraction

---

## Core Concept Reframe

The "Transcript Panel" is actually the **SOURCE EXTRACTION LAYER** - a unified view of parsed data from ANY input type (video, audio, web, document, image).

```
INPUT SOURCE                    EXTRACTION LAYER                 KNOWLEDGE BANK
─────────────                   ────────────────                 ──────────────
Video/Audio  ──┐
Web Page     ──┼──▶  Agent Parser  ──▶  Structured Segments  ──▶  Verified Data
Document     ──┤                                                    Points
Image        ──┘
```

---

## Data Point Schema (Maximum Complexity)

### Universal Segment (applies to ALL source types)

```javascript
{
  // IDENTITY
  segment_id: "uuid",
  source_id: "uuid",           // Parent source reference
  timestamp_created: "ISO8601",

  // TEMPORAL
  time_start: 0.0,             // Seconds (or null for non-temporal)
  time_end: 15.5,
  duration: 15.5,

  // CONTENT
  content_raw: "exact verbatim text",
  content_normalized: "cleaned text for search",
  content_summary: "AI-generated 1-line summary",
  language: "en",
  language_confidence: 0.98,

  // SPEAKER/AUTHOR
  speaker_id: "uuid",          // Links to Masters or user-defined
  speaker_name: "Carl Jung",
  speaker_confidence: 0.95,    // Voice/style recognition
  speaker_role: "primary",     // primary, interviewer, narrator

  // SEMANTIC EXTRACTION
  entities: [
    { type: "PERSON", value: "Sigmund Freud", confidence: 0.99 },
    { type: "CONCEPT", value: "collective unconscious", confidence: 0.97 },
    { type: "DATE", value: "1912", confidence: 0.85 },
    { type: "PLACE", value: "Vienna", confidence: 0.92 }
  ],

  topics: ["psychology", "archetypes", "dreams"],

  claims: [
    {
      statement: "The unconscious contains universal patterns",
      type: "assertion",      // assertion, question, opinion, fact
      verifiable: true,
      cross_refs: ["source_id_1", "source_id_2"]
    }
  ],

  sentiment: {
    overall: "contemplative",
    valence: 0.3,             // -1 to 1
    arousal: 0.4,             // 0 to 1
    confidence: 0.88
  },

  // VERIFICATION
  verification: {
    status: "pre_ai_verified", // pre_ai_verified, user_verified, pending, disputed
    verified_by: "user_id",
    verified_date: "ISO8601",
    source_reliability: 0.95,  // 0-1 based on source type
    provenance_chain: [
      { step: "original_broadcast", date: "1959-10-22", medium: "BBC Television" },
      { step: "archive_org_upload", date: "2008-03-15", url: "..." },
      { step: "user_import", date: "2026-01-12", method: "video_import" }
    ]
  },

  // RELATIONSHIPS
  connections: [
    { type: "responds_to", target_segment_id: "uuid" },
    { type: "contradicts", target_segment_id: "uuid" },
    { type: "supports", target_segment_id: "uuid" },
    { type: "quotes", target_segment_id: "uuid" }
  ],

  // SOURCE-SPECIFIC METADATA
  source_meta: {
    // Video-specific
    visual_description: "Close-up of Jung speaking, bookshelves in background",
    scene_type: "interview",
    camera_angle: "medium_close",

    // Audio-specific
    audio_quality: 0.7,
    background_noise: "minimal",

    // Web-specific
    page_section: "paragraph_3",
    surrounding_context: "...",

    // Document-specific
    page_number: 47,
    chapter: "Chapter 3: The Archetypes",
    footnote_refs: [12, 13]
  },

  // USER ANNOTATIONS
  annotations: [
    {
      user_id: "uuid",
      note: "Key insight on shadow integration",
      tags: ["shadow", "integration", "therapeutic"],
      created: "ISO8601"
    }
  ],

  // TRAINING FLAGS
  training: {
    include_in_bank: true,
    weight: 1.0,              // Importance multiplier
    categories: ["philosophy", "psychology", "wisdom"]
  }
}
```

---

## Source Types & Extraction Pipeline

### 1. VIDEO Source

```
┌─────────────────────────────────────────────────────────────┐
│  VIDEO INPUT                                                │
│  ───────────                                                │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Whisper  │───▶│ Diarize  │───▶│ Segment  │             │
│  │ ASR      │    │ Speakers │    │ by Topic │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │              │               │                     │
│       ▼              ▼               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Raw Text │    │ Speaker  │    │ Topic    │             │
│  │          │    │ IDs      │    │ Clusters │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │              │               │                     │
│       └──────────────┼───────────────┘                     │
│                      ▼                                     │
│              ┌──────────────┐                              │
│              │ NER + Claims │                              │
│              │ Extraction   │                              │
│              └──────────────┘                              │
│                      │                                     │
│                      ▼                                     │
│              ┌──────────────┐                              │
│              │ Structured   │                              │
│              │ Segments     │                              │
│              └──────────────┘                              │
└─────────────────────────────────────────────────────────────┘

Data Points Extracted:
- Timestamped speech segments
- Speaker identification + voice fingerprint
- Topic segmentation (natural breakpoints)
- Named entities (people, places, dates, concepts)
- Claims and assertions
- Cross-references to existing knowledge
- Visual scene descriptions (optional, via vision model)
- Audio quality metrics
```

### 2. WEB Source

```
┌─────────────────────────────────────────────────────────────┐
│  WEB INPUT                                                  │
│  ─────────                                                  │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Fetch +  │───▶│ Extract  │───▶│ Segment  │             │
│  │ Archive  │    │ Content  │    │ Passages │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │              │               │                     │
│       ▼              ▼               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Wayback  │    │ Clean    │    │ Quote    │             │
│  │ Snapshot │    │ Markdown │    │ Blocks   │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│                                                            │
│  Additional Extraction:                                    │
│  - Author attribution                                      │
│  - Publication date                                        │
│  - Domain authority score                                  │
│  - Citation/reference links                                │
│  - Schema.org metadata                                     │
│  - Social proof (shares, citations)                        │
└─────────────────────────────────────────────────────────────┘
```

### 3. DOCUMENT Source

```
┌─────────────────────────────────────────────────────────────┐
│  DOCUMENT INPUT (PDF, EPUB, scanned image)                  │
│  ──────────────                                             │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ OCR if   │───▶│ Structure│───▶│ Extract  │             │
│  │ needed   │    │ Detection│    │ Passages │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │              │               │                     │
│       ▼              ▼               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Clean    │    │ Chapters │    │ Notable  │             │
│  │ Text     │    │ Sections │    │ Quotes   │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│                                                            │
│  Additional Extraction:                                    │
│  - ISBN/DOI                                                │
│  - Page numbers                                            │
│  - Footnotes/endnotes                                      │
│  - Bibliography entries                                    │
│  - Figure/table references                                 │
│  - Marginalia (handwritten notes if present)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Analysis Pipeline (First Use)

When user imports a new source, the DOC-8 agent performs:

```
STAGE 1: INGEST
├── Accept file/URL
├── Validate format
├── Create source record
├── Generate preview thumbnail
└── Queue for processing

STAGE 2: TRANSCRIBE (if audio/video)
├── Run Whisper ASR
├── Detect language
├── Generate raw transcript
├── Calculate confidence scores
└── Estimate speaker count

STAGE 3: DIARIZE (if multiple speakers)
├── Identify speaker segments
├── Match against known voices (Masters bank)
├── Label unknown speakers
└── Create speaker timeline

STAGE 4: SEGMENT
├── Split by natural topic boundaries
├── Identify key passages
├── Mark quotable segments
├── Create semantic chunks for embedding
└── Generate segment summaries

STAGE 5: EXTRACT
├── Named Entity Recognition (NER)
│   ├── People
│   ├── Places
│   ├── Dates
│   ├── Organizations
│   └── Concepts
├── Claim Detection
│   ├── Assertions
│   ├── Questions
│   ├── Opinions
│   └── Verifiable facts
├── Sentiment Analysis
└── Topic Classification

STAGE 6: CROSS-REFERENCE
├── Match entities to existing knowledge bank
├── Find supporting/contradicting sources
├── Link to NORTHSTAR Masters if relevant
├── Calculate novelty score (new vs known info)
└── Suggest related content

STAGE 7: INDEX
├── Generate embeddings for semantic search
├── Add to full-text search index
├── Update topic clusters
├── Refresh knowledge graph
└── Calculate source authority score

STAGE 8: PRESENT
├── Display in Source Extraction panel
├── Show confidence indicators
├── Highlight key insights
├── Enable user verification
└── Offer export options
```

---

## UI Component: Source Extraction Panel (Redesigned)

```
┌─────────────────────────────────────────────────────────────────────┐
│  SOURCE EXTRACTION                                    [Processing]  │
│  ─────────────────                                                  │
│                                                                     │
│  ┌─ FILTERS ──────────────────────────────────────────────────────┐ │
│  │ [All] [Speakers ▼] [Topics ▼] [Verified Only] [Claims] [Q&A]  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ EXTRACTION LIST ──────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 0:00 │ CARL JUNG                              [VERIFIED] │  │ │
│  │  │      │ "The meeting with oneself is, at first, the       │  │ │
│  │  │      │ meeting with one's own shadow..."                 │  │ │
│  │  │      │                                                    │  │ │
│  │  │      │ ○ ASSERTION  ○ Archetype  ○ Shadow  ○ Self        │  │ │
│  │  │      │ Confidence: 98%  │  3 cross-refs                  │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 0:32 │ INTERVIEWER (John Freeman)              [PENDING] │  │ │
│  │  │      │ "Do you believe that was a genuine               │  │ │
│  │  │      │ supernatural experience?"                         │  │ │
│  │  │      │                                                    │  │ │
│  │  │      │ ○ QUESTION  ○ Supernatural  ○ Belief              │  │ │
│  │  │      │ Confidence: 95%  │  Response at 0:45              │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 0:45 │ CARL JUNG                              [VERIFIED] │  │ │
│  │  │      │ "I don't need to believe, I know."               │  │ │
│  │  │      │                                                    │  │ │
│  │  │      │ ○ CLAIM  ○ Epistemology  ○ Gnosis  ★ QUOTABLE     │  │ │
│  │  │      │ Confidence: 99%  │  12 external citations         │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ EXTRACTION SUMMARY ───────────────────────────────────────────┐ │
│  │ 47 segments │ 2 speakers │ 12 claims │ 8 questions │ 156 refs  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Core Extraction (Current Sprint)
- [ ] Rename "Transcript" to "Source Extraction"
- [ ] Add segment type indicators (CLAIM, QUESTION, ASSERTION)
- [ ] Add speaker identification display
- [ ] Show confidence scores
- [ ] Basic entity highlighting

### Phase 2: Agent Pipeline
- [ ] Integrate Whisper for transcription
- [ ] Add speaker diarization (pyannote)
- [ ] Implement NER extraction (spaCy)
- [ ] Add claim detection model
- [ ] Build cross-reference system

### Phase 3: Knowledge Graph
- [ ] Link segments to Masters
- [ ] Build topic clusters
- [ ] Create connection visualization
- [ ] Implement semantic search
- [ ] Add novelty scoring

### Phase 4: Verification Layer
- [ ] User verification workflow
- [ ] Dispute resolution
- [ ] Source reliability scoring
- [ ] Provenance chain tracking
- [ ] Export with citations

---

## Key Insight

The "transcript" is NOT just text-from-audio. It's a **Structured Knowledge Extraction** that:

1. **Preserves provenance** - Every segment links to exact source moment
2. **Identifies speakers** - Who said what, with voice fingerprints
3. **Extracts claims** - Separates facts from opinions from questions
4. **Cross-references** - Links to existing verified knowledge
5. **Enables verification** - User can approve/dispute each segment
6. **Feeds the NORTHSTAR** - Verified segments become training data

This transforms DOC-8 from a "video viewer with transcript" into a **Knowledge Extraction Engine**.

---

*Last updated: 2026-01-13*
*Architecture version: 2.0*
