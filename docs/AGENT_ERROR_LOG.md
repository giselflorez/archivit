# AGENT ERROR LOG
## Persistent Memory for Learning from Mistakes
### Never Repeat a Documented Error

---

## PURPOSE

This file is **MANDATORY READING** on every agent session start.

It documents:
1. **Hallucinations** - Quotes or facts I fabricated
2. **Misattributions** - Quotes assigned to wrong person
3. **Failed Verifications** - Quotes that seemed real but weren't
4. **Methodology Failures** - Research approaches that didn't work
5. **Corrections** - How errors were discovered and fixed

**The goal:** Each error makes the agent SMARTER, not dumber.

---

## ERROR FORMAT

```yaml
error_id: ERR-YYYY-MM-DD-NNN
date_discovered: YYYY-MM-DD
error_type: HALLUCINATION | MISATTRIBUTION | FAILED_VERIFICATION | METHODOLOGY
severity: CRITICAL | HIGH | MEDIUM | LOW
description: What went wrong
incorrect_claim: "The false information"
correct_information: "The truth (if known)"
how_discovered: How the error was caught
prevention: How to avoid this in future
sources_that_failed: Which sources were unreliable
sources_that_worked: Which sources revealed the truth
lesson_learned: Key takeaway for future sessions
```

---

# DOCUMENTED ERRORS

## ERR-2026-01-15-001: Tesla "Energy, Frequency, Vibration"
```yaml
error_id: ERR-2026-01-15-001
date_discovered: 2026-01-12
error_type: MISATTRIBUTION
severity: CRITICAL
description: Commonly circulated quote has no primary source
incorrect_claim: "Tesla said 'If you want to find the secrets of the universe, think in terms of energy, frequency and vibration.'"
correct_information: Quote traced to Ralph Bergstresser (1940s) who CLAIMED Tesla told him this. No contemporary documentation exists.
how_discovered: Quote Investigator research, Wikiquote flagging
prevention: Always verify Tesla quotes - most popular ones are fake
sources_that_failed: Pinterest, Instagram quote images, most websites
sources_that_worked: Quote Investigator, Tesla Museum archives, Wikiquote disputed section
lesson_learned: Tesla is one of the most misquoted figures in history. Assume any Tesla quote is fake until proven otherwise with primary source.
```

---

## ERR-2026-01-15-002: Tesla "3, 6, 9 Magnificence"
```yaml
error_id: ERR-2026-01-15-002
date_discovered: 2026-01-12
error_type: HALLUCINATION (internet fabrication)
severity: CRITICAL
description: Quote is complete fabrication, appeared online ~2010
incorrect_claim: "Tesla said 'If you only knew the magnificence of the 3, 6 and 9, then you would have the key to the universe.'"
correct_information: This quote does not appear in any Tesla writing, interview, or documented speech. It's a numerology community creation.
how_discovered: Wikiquote explicitly lists as unsourced, no appearance in any Tesla archive
prevention: Numerology/mystical Tesla quotes are almost always fake
sources_that_failed: Every website that shares this quote
sources_that_worked: Wikiquote, Tesla Museum Belgrade (confirmed not in archives)
lesson_learned: If a quote sounds too mystical/spiritual for a scientist, it's probably fake or paraphrased from something mundane.
```

---

## ERR-2026-01-15-003: Da Vinci "Simplicity is Ultimate Sophistication"
```yaml
error_id: ERR-2026-01-15-003
date_discovered: 2026-01-12
error_type: MISATTRIBUTION
severity: HIGH
description: Quote is from Clare Boothe Luce (1931), not da Vinci
incorrect_claim: "Leonardo da Vinci said 'Simplicity is the ultimate sophistication.'"
correct_information: Earliest verified use is Clare Boothe Luce's "Stuffed Shirts" (1931). First attributed to da Vinci in a Campari ad in The New Yorker (2000).
how_discovered: Quote Investigator, Check Your Fact
prevention: Apple's use of this quote (attributed to da Vinci) made it viral - be skeptical of quotes popularized by marketing
sources_that_failed: Most design blogs, Apple marketing materials
sources_that_worked: Quote Investigator, da Vinci notebook digitization projects (quote absent)
lesson_learned: Corporate marketing is not a reliable source for historical quotes.
```

---

## ERR-2026-01-15-004: Jung "Privilege of a Lifetime"
```yaml
error_id: ERR-2026-01-15-004
date_discovered: 2026-01-12
error_type: MISATTRIBUTION
severity: HIGH
description: Quote is from Joseph Campbell, not Carl Jung
incorrect_claim: "Jung said 'The privilege of a lifetime is to become who you truly are.'"
correct_information: Source is Joseph Campbell, "A Joseph Campbell Companion: Reflections on the Art of Living"
how_discovered: Carl Jung Depth Psychology Site explicitly states Jung never said this
prevention: Jung and Campbell are frequently confused - verify with CW (Collected Works) references
sources_that_failed: Goodreads quote pages (initially), Pinterest
sources_that_worked: Carl Jung Depth Psychology Site, Campbell's published works
lesson_learned: Jung quotes MUST have CW (Collected Works) paragraph references to be trusted.
```

---

## ERR-2026-01-15-005: Fuller "Build a New Model" (Wrong Source)
```yaml
error_id: ERR-2026-01-15-005
date_discovered: 2026-01-12
error_type: FAILED_VERIFICATION
severity: MEDIUM
description: Quote is real but commonly cited with wrong source
incorrect_claim: "Fuller said this in 'Beyond Civilization (1999)'"
correct_information: "Beyond Civilization" is by Daniel Quinn, not Fuller. Verified Fuller version is from Mike Vance interview (pre-1983), published in "Think Out of the Box" (1995), page 138.
how_discovered: Quote Investigator traced actual source
prevention: Always verify the book/publication actually exists and was written by the attributed person
sources_that_failed: Websites that copied the wrong citation
sources_that_worked: Quote Investigator, Buckminster Fuller Institute
lesson_learned: Even when a quote is real, the citation can be fabricated. Verify the publication exists.
```

---

## ERR-2026-01-02-006: Moon Quotes Collection Attempt
```yaml
error_id: ERR-2026-01-02-006
date_discovered: 2026-01-02
error_type: METHODOLOGY
severity: HIGH
description: Attempted to generate 1000 verified moon quotes, produced hallucinations
incorrect_claim: Multiple fabricated quotes attributed to historical figures (including a fabricated Anne Frank quote)
correct_information: Verifiable moon quotes from history likely number 100-300, not 1000. Quality over quantity.
how_discovered: User caught altered Anne Frank quote, requested verification
prevention: Never promise a specific number of verified quotes before research. Verify FIRST, count SECOND.
sources_that_failed: AI-generated lists without verification
sources_that_worked: (None used properly - that was the problem)
lesson_learned: |
  1. Don't commit to quantity before verification
  2. Real verified quotes are RARE - expect 100-300 not 1000
  3. Always show verification methodology
  4. If user asks for 1000, explain why that's unlikely and offer verified subset
```

---

# PATTERN RECOGNITION

## Most Misquoted Figures (HIGH ALERT)

| Person | Fake Quote Rate | Why |
|--------|-----------------|-----|
| **Nikola Tesla** | ~90% | Mysticism community fabrications |
| **Albert Einstein** | ~80% | Used to add credibility to any idea |
| **Buddha** | ~85% | New Age appropriation |
| **Mark Twain** | ~70% | Witty quotes get attributed to him |
| **Abraham Lincoln** | ~75% | Moral authority borrowing |
| **Marilyn Monroe** | ~80% | Inspirational quote culture |
| **Winston Churchill** | ~60% | Clever sayings attribution |

## Red Flags for Fake Quotes

1. **Too perfect** - Sounds like a motivational poster
2. **Too modern** - Uses contemporary language for historical figure
3. **No source ever cited** - Just the name
4. **Circulates only on social media** - No book/article reference
5. **Contradicts person's actual views** - Einstein on mysticism, etc.
6. **Round numbers in lists** - "100 quotes by X" (padded with fakes)

## Reliable Verification Sources

| Source | Reliability | Use For |
|--------|-------------|---------|
| Quote Investigator | HIGH | First check for any suspicious quote |
| Wikiquote (Disputed section) | HIGH | Identifying known fakes |
| Google Books (exact phrase) | HIGH | Finding original publications |
| JSTOR | HIGH | Academic verification |
| Internet Archive | HIGH | Historical publications |
| Pinterest/Instagram | NEVER | Source of most fakes |

---

# SESSION STARTUP CHECKLIST

**Before researching ANY quote:**

- [ ] Have I read this error log?
- [ ] Is this person on the "Most Misquoted" list?
- [ ] Am I seeing any red flags for fake quotes?
- [ ] Will I verify BEFORE committing to a number?
- [ ] Will I log any new errors discovered?

---

*Error Log Created: January 15, 2026*
*Last Updated: January 15, 2026*
*Errors Documented: 6*
*Purpose: Persistent learning across sessions*

**NEVER REPEAT A DOCUMENTED ERROR**
