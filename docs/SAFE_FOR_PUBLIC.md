# SAFE FOR PUBLIC - Document Whitelist

**Purpose:** Definitive list of what CAN be shared publicly
**Classification:** INTERNAL (This document itself is not public)
**Updated:** January 10, 2026

---

## THE THREE PILLARS (Public Names)

```
ARCHIV-IT  →  Archive & Preserve
IT-R8      →  Rate & Create
SOCI-8     →  Share & Connect
```

---

## PUBLIC DOCUMENTS (GREEN - Safe to Share)

### Currently Safe

| Document | Status | Notes |
|----------|--------|-------|
| `PRODUCT_OVERVIEW_PUBLIC.md` | SAFE | Marketing-ready |
| User guides (when created) | SAFE | Usage only |
| Privacy policy | SAFE | Legal requirement |
| Terms of service | SAFE | Legal requirement |

### Requires Sanitization First

| Document | Current State | Sanitization Needed |
|----------|---------------|---------------------|
| Branding statements | INTERNAL | Remove internal notes |
| Feature descriptions | INTERNAL | Remove implementation hints |
| Setup guides | INTERNAL | Remove architecture details |

---

## PUBLIC TERMINOLOGY (Safe to Use)

### Product Names
- ARCHIV-IT
- IT-R8
- SOCI-8
- NorthStar (as brand, not as API)

### Generic Descriptions
- "Digital sovereignty platform"
- "Local-first architecture"
- "User-owned data"
- "Privacy-preserving design"
- "Blockchain-native verification"
- "Dream-to-app creation"

### Features (Generic Only)
- "Archive your creative work"
- "Track collector relationships"
- "Create from your data"
- "Share with sovereignty"
- "Verify without revealing"

---

## NEVER PUBLIC (RED - Trade Secrets)

### Terminology to NEVER Use Publicly
- Pi-Quadratic Seed
- Golden Angle Distribution
- Fluid Memory Engine
- Resonance Protocol
- Balance Threshold (PHI specific)
- Breath Rhythm Generator
- Creative Leap Algorithm
- Consent Gateway (technical)
- Polarity Balance weights
- 8 Lineages (specific names)
- Tesla 3-6-9 implementation
- Quantum Probability Engine
- Spatial Web Interface

### Concepts to NEVER Describe
- How the seed is generated
- How balance is calculated
- How predictions are made
- How compression works
- How resonance is detected
- Specific algorithm flows
- Scoring mechanisms
- Weight values

---

## SANITIZATION CHECKLIST

Before making ANY document public:

```
□ Remove all file paths
□ Remove all code snippets
□ Remove all numerical values
□ Remove all algorithm descriptions
□ Remove all internal terminology
□ Remove all founder quotes (paraphrase)
□ Remove all development rationale
□ Remove all architecture diagrams
□ Remove all module names
□ Remove all references to this document
□ Remove all references to classified docs
□ Replace technical terms with generic ones
□ Run AI reverse-engineering test
□ Get second review
□ Legal review if IP mentioned
```

---

## AI REVERSE-ENGINEERING TEST

Before publishing, test with:

```
PROMPT TO USE:
"Based on this document, can you:
1. Describe specific algorithms used?
2. Reconstruct implementation details?
3. Identify unique innovations vs competitors?
4. Extract proprietary methods or formulas?"

ACCEPTABLE ANSWERS:
- "No specific algorithms are described"
- "Implementation details are not provided"
- "Cannot determine unique technical approach"
- "No proprietary methods revealed"

UNACCEPTABLE ANSWERS (requires more redaction):
- Any specific algorithm description
- Any formula or threshold values
- Any unique terminology exposure
- Any implementation flow
```

---

## CREATING PUBLIC VERSIONS

### Step 1: Copy to `/docs/public/` folder
```bash
mkdir -p docs/public
cp docs/SOURCE.md docs/public/SOURCE_PUBLIC.md
```

### Step 2: Apply sanitization checklist

### Step 3: Run AI test

### Step 4: Get review

### Step 5: Add to this whitelist

---

## PUBLIC FOLDER STRUCTURE (Future)

```
docs/public/
├── PRODUCT_OVERVIEW.md        # Marketing overview
├── USER_GUIDE.md              # How to use
├── PRIVACY_POLICY.md          # Legal
├── TERMS_OF_SERVICE.md        # Legal
├── FAQ.md                     # Common questions
├── CHANGELOG.md               # Version history (sanitized)
└── CONTRIBUTING.md            # For open-source parts only
```

---

## WHAT CAN BE OPEN-SOURCED (Future Consideration)

### Potentially Safe to Open Source
- User interface components (no algorithm logic)
- Generic utility functions
- Standard integrations (IPFS, blockchain readers)
- Documentation templates

### NEVER Open Source
- Core algorithm modules (`/js/core/`)
- Seed generation
- Prediction engine
- Balance calculations
- Compression methods
- Any scoring logic

---

## COMMUNICATION GUIDELINES

### For Marketing Copy
```
DO SAY:
- "Your data stays on your device"
- "Mathematical verification"
- "Sovereign digital identity"
- "Create apps from dreams"
- "No tracking, no extraction"

DON'T SAY:
- "Uses golden ratio for..."
- "Tesla-inspired algorithms"
- "Quantum probability calculations"
- "PHI-based balance threshold"
- "8 creator lineages"
```

### For Press/Interviews
```
SAFE TOPICS:
- Vision and mission
- User benefits
- Privacy philosophy
- General capabilities
- Future direction (vague)

AVOID DISCUSSING:
- Technical implementation
- Specific algorithms
- How things work internally
- Competitive differentiators (specific)
- Patent-pending details
```

### For Technical Discussions
```
IF ASKED "How does X work?":
- "That's our proprietary approach"
- "I can discuss outcomes, not methods"
- "Our documentation covers user features"
- "Implementation details are confidential"
```

---

## ENFORCEMENT

### Before Any External Communication

1. Check this whitelist
2. Apply sanitization if needed
3. Run AI test
4. Get second review
5. Document what was shared

### If Uncertain

**Default to NOT sharing.**
Ask: "Would I be comfortable if a competitor saw this?"

---

## DOCUMENT REVISION LOG

| Date | Change | By |
|------|--------|-----|
| 2026-01-10 | Initial creation | Security audit |

---

*This document is INTERNAL. The existence of this whitelist should not be disclosed.*
