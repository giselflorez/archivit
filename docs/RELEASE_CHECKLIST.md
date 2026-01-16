# RELEASE CHECKLIST
## Items to Verify Before Public Release

**Created:** January 10, 2026
**Purpose:** Fact-check documents, identify potential issues, ensure accuracy
**Classification:** INTERNAL - Pre-release review

---

## DOCUMENT REVIEW: LEGAL_COUNSEL_BRIEFING.md

### VERIFIED ACCURATE

| Item | Status | Notes |
|------|--------|-------|
| First commit date (Jan 1, 2026) | ✅ VERIFIED | Git history confirms `e0b25ff 2026-01-01` |
| AI-assisted development method | ✅ ACCURATE | Claude Opus 4.5 via VS Code terminal |
| Local-first architecture | ✅ ACCURATE | Core design principle throughout |
| Three-app ecosystem | ✅ ACCURATE | DOC-8, IT-R8, SOCI-8 |

### NEEDS VERIFICATION BY FOUNDER

| Item | Issue | Action Required |
|------|-------|-----------------|
| **Entity Name** | Document states "The Founder Studio Inc." | ⚠️ VERIFY: Is this the correct legal entity name? Is it incorporated? |
| **Trademark "NorthStar"** | Common term, may face challenges | ⚠️ VERIFY: Consider trademark search before claiming |
| **Open Source Licenses** | Claimed "all permissive (MIT, Apache 2.0)" | ⚠️ VERIFY: Run full license audit (see below) |

### POTENTIAL INACCURACIES TO CORRECT

| Item | Issue | Recommendation |
|------|-------|----------------|
| **Copyright Office statement** (line 84) | "US Copyright Office currently requires human authorship" | ADD: "This area of law is evolving rapidly and should be discussed with counsel" |
| **Anthropic ToS claim** (line 80) | "Has no ownership claims (per Anthropic's terms)" | VERIFY: Check actual Anthropic Terms of Service before relying on this |

### STATEMENTS THAT ARE LEGAL ADVICE (Flag for Counsel)

These statements should be reviewed/confirmed by actual legal counsel:
- GDPR compliance claims (lines 191-194)
- CCPA compliance claims (lines 196-199)
- NY SHIELD Act interpretation (lines 201-204)
- Money transmitter classification (lines 228-231)

---

## DOCUMENT REVIEW: FOR_THE_PEOPLE.md

### VERIFIED ACCURATE

| Item | Status | Notes |
|------|--------|-------|
| Three apps (DOC-8, IT-R8, SOCI-8) | ✅ ACCURATE | Matches ecosystem structure |
| Local-first principle | ✅ ACCURATE | Core architecture |
| -8 naming convention | ✅ ACCURATE | Infinity symbol meaning documented |

### POTENTIAL HALLUCINATIONS / INACCURACIES

| Item | Issue | Recommendation |
|------|-------|----------------|
| **"Local AI that runs on your device"** (line 121) | ⚠️ POTENTIALLY MISLEADING | Current system uses **external API calls** (OpenAI, Anthropic) for AI features. Data stays local, but AI processing happens externally. REVISE to: "Local-first data with AI assistance" or clarify that some features use external APIs |
| **"Discover through resonance, not algorithms"** (line 97) | ⚠️ MISLEADING | Resonance IS an algorithm. REVISE to: "Discover through algorithms that serve you, not advertisers" |

### STRONG COMMITMENTS TO REVIEW

These are binding promises - ensure founder is prepared to maintain them:

| Promise | Location | Risk |
|---------|----------|------|
| "We will never sell your data" | line 153 | LOW - Aligned with architecture |
| "We will never show advertisements" | line 154 | MEDIUM - Requires sustainable business model |
| "We will never track your behavior" | line 155 | LOW - Aligned with local-first |
| "We will never train AI on your content without permission" | line 156 | MEDIUM - Verify no analytics/telemetry |
| "It's Truly Free... No catch" | line 107-108 | MEDIUM - Must ensure premium tier doesn't gate essential features |

### FOUNDER QUOTE VERIFICATION

**Line 248-249:**
> "I don't want the human population dependent on my software, but I do want it to be a fair and free portal breaking bit by bit into an independent sovereignty of everyone's digital identities and data constructs."

⚠️ **VERIFY:** Is this the exact quote you want publicly attributed? It was extracted from session logs with original spelling preserved.

---

## LICENSE AUDIT REQUIRED

### Current Dependencies (requirements-full.txt)

| Package | Likely License | Risk |
|---------|---------------|------|
| Flask | BSD-3-Clause | ✅ Permissive |
| PyTorch | BSD-3-Clause | ✅ Permissive (CUDA components separate) |
| transformers | Apache 2.0 | ✅ Permissive |
| numpy | BSD-3-Clause | ✅ Permissive |
| Pillow | PIL License | ✅ Permissive |
| web3 | MIT | ✅ Permissive |
| anthropic | Check ToS | ⚠️ VERIFY |
| bitsandbytes | MIT | ✅ Permissive |
| sentence-transformers | Apache 2.0 | ✅ Permissive |

### Action Required

```bash
# Run full license check before release
pip-licenses --format=markdown > THIRD_PARTY_LICENSES.md
```

**Key Question:** Are there any GPL/LGPL/AGPL components that would require source disclosure?

---

## TRADEMARK SEARCH REQUIRED

Before filing, search for existing marks:

| Mark | Potential Conflicts | Priority |
|------|---------------------|----------|
| ARCHIV-IT | May conflict with "Archive-It" (Internet Archive service) | ⚠️ HIGH - Search required |
| DOC-8 | Search required | MEDIUM |
| IT-R8 | Similar to "iterate" - may be generic | MEDIUM |
| SOCI-8 | Search required | MEDIUM |
| NorthStar | VERY common term - many existing marks | ⚠️ HIGH - Likely conflicts |

**Recommendation:** Trademark attorney should run full search before filing.

---

## TECHNICAL CLAIMS TO VERIFY

### "No Telemetry" Claim

Verify these are NOT present in codebase:
- [ ] Google Analytics
- [ ] Mixpanel or similar
- [ ] Sentry error reporting (may send data)
- [ ] Any phone-home functionality
- [ ] Usage statistics collection

### "Works Offline" Claim

Verify functionality without internet:
- [ ] Core DOC-8 features work offline
- [ ] Data access doesn't require connection
- [ ] Only optional features need internet

### "Delete Means Delete" Claim

Verify:
- [ ] No hidden data retention
- [ ] No cloud backups that persist after deletion
- [ ] Local deletion is complete

---

## CORRECTIONS TO MAKE

### LEGAL_COUNSEL_BRIEFING.md

**Change line 84 from:**
> "Copyright: US Copyright Office currently requires human authorship for registration. The founder provided substantial creative input and direction."

**To:**
> "Copyright: US Copyright Office guidance on AI-generated works is evolving. The founder provided substantial creative direction, specification, and review of all code. This should be discussed with counsel regarding current requirements."

### FOR_THE_PEOPLE.md

**Change line 121 from:**
> "Local AI that runs on your device"

**To:**
> "Privacy-preserving architecture where your data stays on your device"

**Change line 97 from:**
> "Discover through resonance, not algorithms"

**To:**
> "Discover through algorithms designed to serve you, not advertisers"

---

## PRE-RELEASE CHECKLIST

### Before Lawyer Meeting
- [ ] Verify entity name is correct
- [ ] Review and accept all "strong commitments" in FOR_THE_PEOPLE.md
- [ ] Confirm founder quote is desired public attribution
- [ ] Check Anthropic ToS for IP ownership clarity

### Before Public Release
- [ ] Run full license audit
- [ ] Trademark search completed
- [ ] Technical claims verified (offline, no telemetry, deletion)
- [ ] Apply corrections noted above
- [ ] Legal review of Terms of Service
- [ ] Legal review of Privacy Policy
- [ ] Apply document corrections

### Before Beta Launch
- [ ] Beta tester agreement drafted
- [ ] Support email configured
- [ ] Bug reporting system ready
- [ ] Feedback collection compliant with privacy promises

---

## SUMMARY OF ISSUES FOUND

### Critical (Must Fix Before Release)
1. ⚠️ "Local AI" claim may mislead - AI uses external APIs
2. ⚠️ Entity name needs verification
3. ⚠️ "Archive-It" trademark conflict potential

### Important (Should Fix)
1. Copyright Office language should note evolving law
2. "Resonance not algorithms" is technically inaccurate
3. License audit should be completed

### Minor (Recommended)
1. NorthStar trademark likely unavailable
2. Anthropic ToS should be verified
3. Technical claims should be tested

---

**Document Status:** Ready for founder review
**Next Step:** Founder verifies entity name, approves commitments, confirms quote
