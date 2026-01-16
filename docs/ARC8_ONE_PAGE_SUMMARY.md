# ARC-8
## Quantum-Safe Digital Archive Infrastructure

---

### What It Is

Open-source software for preserving digital cultural assets with:
- **Local storage** (your infrastructure, your control)
- **Distributed backup** (optional IPFS redundancy)
- **Quantum-safe cryptography** (NIST FIPS 203/204 compliant)

---

### The Problem It Solves

| Risk | Recent Example | ARC-8 Response |
|------|----------------|----------------|
| Physical loss | Brazil National Archives fire (2021) | Distributed copies |
| Cyber attack | British Library ransomware (2023) | Local-first, encrypted |
| Vendor failure | Google Domains shutdown (2024) | No vendor dependency |
| Quantum threat | NSA: Migrate by 2035 | Already quantum-safe |

---

### How It Works

```
ARCHIVE ITEM
    ↓
[Hash + Metadata + Timestamp]
    ↓
[Quantum-Safe Signature]
    ↓
PROVENANCE RECORD
    ↓
[Local Storage] + [Optional IPFS Distribution]
```

Every item gets a cryptographic proof of authenticity that remains valid for 50+ years.

---

### Technical Compliance

- **NIST FIPS 203** (ML-KEM-768 key exchange)
- **NIST FIPS 204** (ML-DSA-65 digital signatures)
- **Dublin Core** metadata compatibility
- **OAIS** reference model alignment
- **NDSA** Levels 3-4 capable

---

### Cost

| Item | Cost |
|------|------|
| Software license | Free (MIT open source) |
| Infrastructure (100K items) | ~$15,000/year |
| Subscription fees | None |
| Per-seat licensing | None |

---

### Differentiation

Only solution combining:
1. Local-first architecture (data sovereignty)
2. NIST post-quantum standards (future-proof)
3. No cloud dependency (institutional control)
4. Delete capability (legal compliance)

---

### Current Status

| Component | Status |
|-----------|--------|
| Core cryptography | Complete |
| Provenance system | Complete |
| Local storage | Complete |
| IPFS integration | Beta |
| API | In development |
| Pilot program | Accepting applications |

---

### Contact

**Pilot Program:** [Application link]
**Technical:** [GitHub]
**Partnership:** [Foundation contact]

---

*ARCHIV-IT Foundation | 501(c)(3) Nonprofit*
*No tokens. No subscriptions. No vendor lock-in.*
