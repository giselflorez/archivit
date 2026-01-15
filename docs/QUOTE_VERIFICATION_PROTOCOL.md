# QUOTE VERIFICATION PROTOCOL
## Institutional-Grade Research Methodology for ARCHIV-IT
### Version 1.0 - January 2026

---

## THE PROBLEM WE'RE SOLVING

> "Most 'famous quotes' online are misattributed or fabricated."

The internet is polluted with fake quotes. This damages:
- Historical accuracy
- Trust in knowledge systems
- The legacy of great thinkers
- Anyone trying to learn from the past

**Our mission:** Build a VERIFIED knowledge base that can be trusted.

---

## CORE PRINCIPLES

### 1. NO HALLUCINATION POLICY
```
IF source_not_found:
    RETURN "Quote source not verified - cannot confirm attribution"
    LOG error to ERROR_LOG.md
    DO NOT fabricate a source
```

### 2. PRIMARY SOURCE HIERARCHY

| Trust Level | Source Type | Example | Weight |
|-------------|-------------|---------|--------|
| **TIER 1** | Original manuscript/recording | da Vinci's notebooks at Biblioteca Ambrosiana | 1.0 |
| **TIER 2** | Scholarly edition with page numbers | Richter's "Literary Works of Leonardo da Vinci" | 0.95 |
| **TIER 3** | Institutional archive | Library of Congress, British Library, Getty | 0.90 |
| **TIER 4** | Peer-reviewed academic source | JSTOR, university press publications | 0.85 |
| **TIER 5** | Verified journalism | NYT, BBC with date/page | 0.75 |
| **TIER 6** | Quote verification sites | Quote Investigator (with methodology) | 0.70 |
| **TIER 7** | General web sources | Wikipedia, blogs | 0.30 |
| **TIER 8** | Social media attribution | Pinterest, Instagram quotes | 0.05 |

### 3. VERIFICATION REQUIREMENTS

**MINIMUM for VERIFIED status:**
- At least ONE Tier 1-4 source
- Full citation (author, title, year, page/paragraph)
- Cross-reference with at least one other source

**ATTRIBUTED status (use with caution):**
- Commonly attributed but no primary source found
- Must note "Source unverified" in record

**FAKE/MISATTRIBUTED status:**
- Proven to be fabricated or said by someone else
- Document the investigation that proved it false

---

## RESEARCH METHODOLOGY

### Phase 1: Initial Search
```
1. Search Quote Investigator first (they do rigorous work)
2. Check Wikiquote (look at "Disputed" and "Misattributed" sections)
3. Search Google Books for exact phrase in quotes
4. Search JSTOR/academic databases
5. Check Internet Archive for original publications
```

### Phase 2: Source Verification
```
1. Trace quote to earliest known appearance
2. Verify the publication actually exists
3. Check page numbers match content
4. Look for scholarly commentary on the quote
5. Check if the person was alive when allegedly said
```

### Phase 3: Cross-Reference
```
1. Find at least 2 independent sources
2. Check if sources cite each other (avoid circular verification)
3. Prefer sources that disagree on interpretation but agree on text
4. Note any variations in wording between sources
```

### Phase 4: Documentation
```
1. Record full citation in standardized format
2. Note verification date and method
3. Assign trust level based on source hierarchy
4. Add to VERIFIED_QUOTES_DB with unique ID
5. Log any difficulties or uncertainties in ERROR_LOG.md
```

---

## INSTITUTIONAL ARCHIVES TO PRIORITIZE

### For Historical Figures

| Institution | Specialty | Access |
|-------------|-----------|--------|
| **Library of Congress** | American history, recordings | loc.gov |
| **British Library** | Historical manuscripts | bl.uk |
| **Internet Archive** | Historical publications | archive.org |
| **Gutenberg Project** | Public domain texts | gutenberg.org |
| **HathiTrust** | Academic book digitization | hathitrust.org |
| **JSTOR** | Academic journals | jstor.org |
| **Google Books** | Searchable book text | books.google.com |

### For Specific Masters

| Person | Primary Archive | Notes |
|--------|-----------------|-------|
| **Tesla** | Tesla Museum Belgrade, Smithsonian | Most quotes need verification |
| **da Vinci** | Biblioteca Ambrosiana, V&A Museum | Codex digitization projects |
| **Jung** | ETH Zurich, Jung Institute | Collected Works (CW) references |
| **Fuller** | Stanford Libraries, BFI | Extensive lecture recordings |
| **Coltrane** | Smithsonian Jazz, Coltrane Home | Limited interviews exist |
| **Hildegard** | Rupertsberger Codex, scholarly editions | Latin originals, translations vary |

### For Moon-Specific Research

| Source Type | Examples |
|-------------|----------|
| **Space Agency Archives** | NASA History Office, ESA Archives |
| **Astronaut Oral Histories** | Johnson Space Center Oral History Project |
| **Poetry Archives** | Poetry Foundation, Academy of American Poets |
| **Indigenous Knowledge** | Smithsonian Center for Folklife, tribal archives |
| **Scientific Literature** | Nature, Science (historical astronomy) |
| **Religious/Spiritual Texts** | Verified translations with scholarly apparatus |

---

## ERROR PREVENTION CHECKLIST

Before adding any quote to the database:

- [ ] Is the person actually known to have said/written this?
- [ ] Does the quote appear in a primary or scholarly source?
- [ ] Have I checked if this is a known misattribution?
- [ ] Is the wording exactly as in the source, or paraphrased?
- [ ] Could this be a translation issue? (Note original language)
- [ ] Is the date/context plausible for this person?
- [ ] Have I avoided "quote aggregator" sites as sole sources?
- [ ] Have I logged any uncertainties in ERROR_LOG.md?

---

## QUOTE RECORD FORMAT

```yaml
id: [CATEGORY]-[PERSON]-[NUMBER]
quote: "Exact text in quotes"
attribution: Full Name (Birth-Death)
status: VERIFIED | ATTRIBUTED | PARAPHRASE | DISPUTED | FAKE
source:
  type: [Tier 1-8]
  title: "Publication/Document Name"
  author: Editor/Compiler if applicable
  year: YYYY
  page: Page number or paragraph reference
  location: Archive/Library holding original
  url: Digital access URL if available
verification:
  date: YYYY-MM-DD
  method: How verified
  cross_references:
    - Additional source 1
    - Additional source 2
  notes: Any caveats or context
original_language: If not English
translation_source: If translated
tags:
  - thematic tags
  - topic tags
```

---

## AGENT STARTUP PROTOCOL

**On every session start, the agent MUST:**

1. Read `QUOTE_VERIFICATION_PROTOCOL.md` (this file)
2. Read `ERROR_LOG.md` to learn from past mistakes
3. Check `VERIFIED_QUOTES_DB/` for existing verified quotes
4. Never repeat a documented error
5. Log new learnings before session end

---

## CONTINUOUS IMPROVEMENT

### After Each Research Session:
1. Update ERROR_LOG.md with any new fake quotes discovered
2. Add verified quotes to database
3. Note which sources were most/least useful
4. Refine search methodology based on experience

### Monthly Review:
1. Audit random sample of "verified" quotes
2. Check if any new scholarship has emerged
3. Update source hierarchy based on reliability experience
4. Document methodology improvements

---

## THE GOAL

Build a knowledge base where:
- **Every quote can be traced to its source**
- **Fake quotes are explicitly documented as fake**
- **Uncertainty is acknowledged, not hidden**
- **The agent gets smarter with each session**
- **Future generations can trust what we've built**

---

*Protocol Created: January 15, 2026*
*Purpose: Enable rigorous, institutional-grade quote verification*
*Mandate: No hallucinations. Only verified knowledge.*

**SO MOTE IT BE**
