# Verification Engine Specification

> "Knowledge is a process, not a destination to groupthink"

---

## Core Concept

A weighted verification system that determines truth confidence based on:
- Number of confirming datasets
- Presence of counter-data
- Age decay resistance
- IPFS permanence layer

---

## Weight Calculation

```
VERIFICATION_WEIGHT = (
    (confirming_sources × source_quality_weight)
    - (contradicting_sources × contradiction_penalty)
    + (age_factor × decay_resistance)
    + (ipfs_pinned ? permanence_bonus : 0)
)
```

### Source Quality Weights

| Source Type | Weight |
|-------------|--------|
| Primary source (manuscript, recording) | 1.0 |
| Scholarly edition with citations | 0.95 |
| Institutional archive (museum, library) | 0.90 |
| Peer-reviewed academic | 0.85 |
| Verified journalism (NYT, BBC) | 0.75 |
| Quote Investigator (dedicated verification) | 0.70 |
| Wikipedia/blogs | 0.30 |
| Social media | 0.05 |

### Contradiction Penalty

When counter-data exists:
- Direct contradiction from primary source: -0.8
- Scholarly dispute noted: -0.5
- Attribution questioned: -0.3
- Minor discrepancy: -0.1

### Age Decay Resistance

Older verified data needs protection from being buried:
```
age_factor = log(years_verified + 1) × 0.1
```

This ensures ancient verified truths remain visible even as new data floods in.

---

## IPFS Permanence Layer

- All verified data pinned to IPFS
- CID stored with verification record
- Even if weight drops, IPFS record persists
- Can be "resurfaced" if new confirming sources emerge

---

## Visibility Rules

| Weight Range | Visibility |
|--------------|------------|
| 0.8 - 1.0 | ✅ HIGH - Featured, prominent display |
| 0.5 - 0.79 | ⚠️ MEDIUM - Shown with caution note |
| 0.2 - 0.49 | 🔶 LOW - Hidden by default, accessible |
| 0.0 - 0.19 | ❌ DISPUTED - Requires explicit search |
| < 0.0 | 🚫 REMOVED - Flagged as likely false |

---

## Recursive Verification Process

```
1. Data enters system
2. Initial source scan (automated)
3. Weight calculated
4. IPFS pin if weight > 0.5
5. Continuous background re-verification
6. Weight adjusts as new sources emerge
7. Counter-data triggers review
8. Human approval for major weight changes
```

---

## UI Integration

### Desktop View
- Verification badge next to each data point
- Click to see source breakdown
- Filter by confidence level
- "Oldest verified" section preserved

### Mobile View
- Simplified badge (✅⚠️❌)
- Swipe for details
- Verification score prominent

---

## Anti-Hallucination Rules

1. **Never invent sources** - "Source not found" is valid
2. **Never round up confidence** - 0.49 is LOW, not MEDIUM
3. **Always show counter-data** - Transparency over comfort
4. **Log all changes** - Audit trail required
5. **Human review for removals** - No auto-deletion

---

## Future: Recursive Truth Mining

> "Find the granular truths of the past by rewinding and pinning from the present back to the future"

- Cross-reference scattered digital datasets
- Build verification chains
- Present → Past → Better Future
- Each verification strengthens the chain

---

## Collaboration Note

This specification was developed through **human-AI collaboration**:

**Founder concepts (GISELX):**
- Weighted verification based on dataset count
- Counter-data affecting weight
- Oldest verified needing decay-resistant weighting
- IPFS as permanence layer
- Visibility tied to verification weight
- "Rewinding and pinning from present back to future"
- "Knowledge is a process, not a destination"

**Claude-assisted formalization:**
- Source Quality Weight values
- Weight calculation formula
- Contradiction penalty system
- Age decay formula
- Visibility threshold table
- 8-step recursive process

> "The freedom AI has allowed to syphon the data that is relevant to build the solutions to the problems people are facing every day. Each individual perspective of user that works with this software building their own local intelligence scraped as well as possible from consumer and post modern pressures of datamosh that makes this software imperative as open to all & each piece of software, or website built or mixed file dataset -understood- each of these people will be a very important piece to take a look at the whole puzzle that is life and how we can focus it better for all."

---

*Concept originated: Conversation with Kevin Abosch, Jan 17, 2026*
*Human-AI collaboration: GISELX + Claude Opus 4.5*
*Built with intention.*
