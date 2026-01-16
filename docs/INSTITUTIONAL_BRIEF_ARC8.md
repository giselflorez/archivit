# ARC-8: Digital Archive Infrastructure
## Institutional Brief for Cultural Organizations

**Prepared for:** Museum Directors, Archive Administrators, Cultural Institution Leadership
**Document Type:** Technical and Strategic Overview
**Classification:** Public

---

## EXECUTIVE SUMMARY

ARC-8 is open-source software infrastructure for digital archive preservation. It addresses three documented problems facing cultural institutions:

1. **Single points of failure** in centralized storage systems
2. **Cryptographic obsolescence** due to quantum computing advances
3. **Vendor dependency** in commercial preservation solutions

The system uses established mathematical principles and NIST-standardized cryptography to enable distributed, long-term preservation of digital cultural assets.

---

## THE PROBLEM

### Documented Archive Failures (2020-2026)

| Year | Institution | Event | Impact |
|------|-------------|-------|--------|
| 2021 | National Archives of Brazil | Fire | 20 million documents destroyed |
| 2022 | Internet Archive | Lawsuit (Hachette) | $19M+ liability, service disruption |
| 2023 | British Library | Ransomware attack | Systems down for months, £7M+ recovery |
| 2024 | Various universities | Budget cuts | Reduced digital preservation staff |

**Pattern:** Centralized systems create single points of failure. Legal, physical, and cyber attacks can destroy irreplaceable cultural assets.

### The Quantum Computing Timeline

Current encryption standards (RSA, ECDSA) will be broken by quantum computers. NIST and NSA have documented this threat:

| Source | Statement | Date |
|--------|-----------|------|
| NIST | Published post-quantum cryptography standards (FIPS 203/204) | August 2024 |
| NSA CNSA 2.0 | Requires agencies to migrate to PQC by 2035 | September 2022 |
| IBM | Roadmap to 100,000+ qubits by 2033 | Ongoing |

**Risk:** Data encrypted today with current standards can be stored by adversaries and decrypted when quantum computers arrive ("harvest now, decrypt later").

---

## THE SOLUTION

### Architecture Overview

ARC-8 implements three design principles:

**1. Local-First Storage**
- Data remains on institution's own infrastructure
- No mandatory cloud dependency
- Full control over access and deletion

**2. Distributed Redundancy**
- Optional IPFS integration for geographic distribution
- Multiple copies across independent systems
- No single point of failure

**3. Quantum-Safe Cryptography**
- NIST FIPS 203 (ML-KEM-768) for key exchange
- NIST FIPS 204 (ML-DSA-65) for digital signatures
- Hybrid mode combines classical and post-quantum algorithms

### Technical Specifications

| Component | Implementation | Standard |
|-----------|----------------|----------|
| Key Exchange | ML-KEM-768 (CRYSTALS-Kyber) | NIST FIPS 203 |
| Digital Signatures | ML-DSA-65 (CRYSTALS-Dilithium) | NIST FIPS 204 |
| Symmetric Encryption | AES-256-GCM | NIST FIPS 197 |
| Hash Function | SHA-384 | NIST FIPS 180-4 |
| Storage | Local + optional IPFS | W3C, Protocol Labs |

### Provenance System

Every archived item receives a cryptographic provenance record:

```
PROVENANCE RECORD STRUCTURE:
├── Content hash (SHA-384)
├── Creator identifier (public key fingerprint)
├── Timestamp (ISO 8601)
├── Metadata (Dublin Core compatible)
├── Digital signature (ML-DSA-65)
└── Verification chain (parent records)
```

This provides:
- **Authenticity verification** - Mathematical proof of origin
- **Tamper detection** - Any modification invalidates signature
- **Chain of custody** - Complete transfer history
- **Long-term validity** - Signatures remain valid for 50+ years

---

## USE CASES

### Museum Collections

**Application:** Digital surrogates of physical works, born-digital acquisitions, artist archives

**Benefits:**
- Provenance records link to physical catalog entries
- Distributed storage protects against facility loss
- Quantum-safe signatures ensure long-term authenticity

### University Archives

**Application:** Research data, institutional records, special collections digitization

**Benefits:**
- Local-first respects data sovereignty requirements
- IPFS distribution enables collaboration without centralization
- Access controls support FERPA/HIPAA compliance

### Artist Estates

**Application:** Managing digital assets across distributed family members, galleries, foundations

**Benefits:**
- Mathematically verifiable chain of custody
- No dependency on single commercial platform
- Export in standard formats (JSON, Dublin Core XML)

---

## COMPARISON WITH EXISTING SOLUTIONS

| Feature | DSpace | LOCKSS | Arweave | ARC-8 |
|---------|--------|--------|---------|-------|
| Local-first | No | Yes | No | Yes |
| Distributed | No | Yes | Yes | Yes |
| Quantum-safe | No | No | No | Yes |
| Delete capability | Yes | Yes | No | Yes |
| Open source | Yes | Yes | Yes | Yes |
| Cloud dependency | Optional | No | Required | No |
| NIST compliance | Partial | Partial | No | Full |

**Differentiation:** ARC-8 is the only solution combining local-first architecture with NIST-standardized post-quantum cryptography.

---

## IMPLEMENTATION

### Deployment Options

**Option A: Standalone Installation**
- Single institution deployment
- All data on local infrastructure
- No external dependencies

**Option B: Consortium Model**
- Multiple institutions share IPFS pinning
- Geographic redundancy across members
- Shared infrastructure costs

**Option C: Hybrid**
- Local primary storage
- Selective IPFS distribution for high-value items
- Cloud backup as tertiary option

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Storage | 100 GB | 1 TB+ |
| RAM | 4 GB | 16 GB |
| CPU | 2 cores | 8 cores |
| Network | 10 Mbps | 100 Mbps |
| Browser | Chrome 90+, Firefox 88+, Safari 14+ | Latest versions |

### Migration Path

1. **Assessment** - Inventory existing digital assets
2. **Pilot** - Test with subset of collection (100-1000 items)
3. **Integration** - Connect to existing catalog systems via API
4. **Migration** - Gradual transfer with verification
5. **Validation** - Confirm all provenance records

---

## GOVERNANCE

### Nonprofit Structure

ARC-8 is developed under a 501(c)(3) nonprofit foundation model:

- **Board oversight** - Cultural institution representatives
- **Open source license** - MIT (permissive, no vendor lock-in)
- **No token/cryptocurrency** - Standard fiat funding
- **Mission protection** - Bylaws prevent commercial acquisition

### Standards Compliance

| Standard | Status |
|----------|--------|
| NIST Post-Quantum Cryptography | Compliant (FIPS 203/204) |
| Dublin Core Metadata | Compatible |
| OAIS Reference Model | Aligned |
| NDSA Levels of Preservation | Level 3-4 capable |
| PREMIS | Metadata mapping available |

---

## COST STRUCTURE

### Software

- **License:** Free (MIT open source)
- **Updates:** Free (community maintained)
- **Support:** Community forums + optional paid support contracts

### Infrastructure

| Deployment | Estimated Annual Cost |
|------------|----------------------|
| Small (10,000 items) | $2,000-5,000 (hosting) |
| Medium (100,000 items) | $10,000-25,000 |
| Large (1M+ items) | $50,000-100,000 |

Costs are infrastructure only. No per-seat licensing. No subscription fees.

### Comparison

| Solution | 100K Items/Year | Notes |
|----------|-----------------|-------|
| ARC-8 | ~$15,000 | Infrastructure only |
| Preservica | $50,000-100,000 | Enterprise pricing |
| Archive-It | $20,000-50,000 | Subscription model |
| DSpace + AWS | $25,000-40,000 | Hosting + maintenance |

---

## TIMELINE

### Current Status (Q1 2026)

- Core cryptography: Implemented
- Provenance system: Implemented
- Local storage: Implemented
- IPFS integration: Beta
- API: In development
- Documentation: Comprehensive

### Roadmap

| Phase | Target | Deliverable |
|-------|--------|-------------|
| Q2 2026 | Pilot program | 5-10 institutional testers |
| Q3 2026 | API release | REST API for catalog integration |
| Q4 2026 | Consortium tools | Multi-institution IPFS coordination |
| Q1 2027 | NDSA certification | Third-party preservation audit |

---

## CONTACT

**Technical inquiries:** [GitHub repository]
**Partnership discussions:** [Foundation contact]
**Pilot program applications:** [Application process]

---

## APPENDIX A: CRYPTOGRAPHIC SPECIFICATIONS

### ML-KEM-768 (Key Encapsulation)

```
Algorithm:        CRYSTALS-Kyber
Security Level:   NIST Level 3 (AES-192 equivalent)
Public Key:       1,184 bytes
Secret Key:       2,400 bytes
Ciphertext:       1,088 bytes
Shared Secret:    32 bytes
Standard:         NIST FIPS 203 (August 2024)
```

### ML-DSA-65 (Digital Signatures)

```
Algorithm:        CRYSTALS-Dilithium
Security Level:   NIST Level 3 (AES-192 equivalent)
Public Key:       1,952 bytes
Secret Key:       4,032 bytes
Signature:        3,309 bytes
Standard:         NIST FIPS 204 (August 2024)
```

### Why These Algorithms?

NIST conducted an 8-year evaluation process (2016-2024) testing hundreds of candidate algorithms. Kyber and Dilithium were selected as primary standards based on:

- Security analysis by international cryptographic community
- Performance benchmarks across platforms
- Implementation simplicity
- Resistance to known attack vectors

---

## APPENDIX B: MATHEMATICAL FOUNDATIONS

### Access Control Thresholds

The system uses ratio-based thresholds derived from the golden ratio (φ = 1.618...) for tiered access control:

| Tier | Formula | Value | Access Level |
|------|---------|-------|--------------|
| Blocked | φ^(-2) | 0.236 | No access |
| Limited | 1 - φ^(-1) | 0.382 | Read-only |
| Standard | φ^(-1) | 0.618 | Full access |
| Administrative | φ^(-0.5) | 0.786 | System configuration |

**Rationale:** These thresholds create mathematically consistent boundaries that resist gaming through their irrational values. The golden ratio has documented applications in optimization theory and is used here for its computational properties, not aesthetic associations.

### Verification Formula

Provenance authenticity is verified through:

```
VERIFY(record, signature, publicKey) → boolean

Where:
- record = SHA-384(content || metadata || timestamp)
- signature = ML-DSA-65.sign(secretKey, record)
- publicKey = corresponding ML-DSA-65 public key

Returns TRUE if signature was created by holder of corresponding secret key
Returns FALSE if content, metadata, or timestamp have been modified
```

---

## APPENDIX C: REFERENCES

### Standards Documents

1. NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (2024)
2. NIST FIPS 204: Module-Lattice-Based Digital Signature Standard (2024)
3. NSA CNSA 2.0: Commercial National Security Algorithm Suite 2.0 (2022)
4. OAIS: Reference Model for an Open Archival Information System (ISO 14721:2012)
5. PREMIS: Data Dictionary for Preservation Metadata (v3.0)

### Technical Resources

1. NIST Post-Quantum Cryptography Project: https://csrc.nist.gov/projects/post-quantum-cryptography
2. CRYSTALS-Kyber: https://pq-crystals.org/kyber/
3. CRYSTALS-Dilithium: https://pq-crystals.org/dilithium/
4. IPFS Documentation: https://docs.ipfs.tech/

---

*Document version: 1.0*
*Last updated: 2026-01-15*
*Prepared by: ARCHIV-IT Foundation*
