# ARC-8 GLOSSARY
## Technical Terms in Plain Language

**Purpose:** Explain what all the technical terms mean so anyone can understand
**Audience:** Everyone - no computer science degree required

---

## THE BIG PICTURE

**"Ancient magic of the past, establishing new keys to the future."**

ARC-8 uses mathematical patterns that have existed since the beginning of time (golden ratio, spirals, Fibonacci numbers) combined with cutting-edge cryptography to create a system where:
- **You own your data** (it never leaves your device without permission)
- **Your identity is mathematical** (derived from your unique seed)
- **Your archives are quantum-proof** (protected against future supercomputers)

---

## CRYPTOGRAPHY (The Locks & Keys)

### What is Cryptography?

The science of keeping information secret. Like a lock on a diary, but mathematical.

### ML-KEM-768 (Kyber)

**What it is:** A way to securely share a secret key with someone over the internet.

**Plain English:** Imagine you want to send someone a locked box, but you've never met them. How do you give them the key without someone stealing it? ML-KEM is a mathematical trick that lets two people create a shared secret without ever sending the actual secret.

**Why "ML-KEM"?**
- ML = Module Lattice (a type of math problem)
- KEM = Key Encapsulation Mechanism (wrapping a key safely)
- 768 = Security level (higher = more secure)

**Why it matters:** Regular encryption (RSA, ECDH) can be broken by quantum computers. ML-KEM cannot.

**Analogy:** It's like having a special kind of lock where you can create a key together with someone else, without either of you ever seeing the actual key until it's done.

---

### ML-DSA-65 (Dilithium)

**What it is:** A way to digitally sign something so everyone knows it came from you and hasn't been tampered with.

**Plain English:** Like signing your name on a document, but mathematical. Anyone can verify the signature is real, but no one can forge it.

**Why "ML-DSA"?**
- ML = Module Lattice (same math family as Kyber)
- DSA = Digital Signature Algorithm
- 65 = Security parameter

**Why it matters:** If someone changes even one letter of what you signed, the signature becomes invalid. And unlike handwritten signatures, quantum computers can't forge these.

**Analogy:** Imagine a wax seal that's impossible to duplicate and that magically breaks if anyone tampers with the letter inside.

---

### Post-Quantum Cryptography (PQC)

**What it is:** Encryption that can't be broken by quantum computers.

**Why it matters:**

```
TODAY'S ENCRYPTION          QUANTUM COMPUTER
─────────────────           ─────────────────
🔒 RSA-2048                 💥 Broken in hours
🔒 ECDSA                    💥 Broken in hours
🔒 Regular HTTPS            💥 Broken in hours

POST-QUANTUM ENCRYPTION     QUANTUM COMPUTER
───────────────────────     ─────────────────
🔒 ML-KEM-768               ✓ Still secure
🔒 ML-DSA-65                ✓ Still secure
```

**The threat:** Governments are recording encrypted internet traffic TODAY. When quantum computers arrive (2030-2035), they'll decrypt everything they saved. This is called "harvest now, decrypt later."

**ARC-8's protection:** Your archives are encrypted with algorithms that will still be secure in 50 years.

---

### NIST FIPS 203/204

**What it is:** The official U.S. government stamp of approval for post-quantum cryptography.

**Plain English:** The National Institute of Standards and Technology (NIST) spent 8 years testing hundreds of algorithms. In 2024, they chose the winners:
- FIPS 203 = ML-KEM (what we use for key exchange)
- FIPS 204 = ML-DSA (what we use for signatures)

**Why it matters:** These aren't experimental. They're the official standard that banks, governments, and militaries will use.

---

### Hybrid Mode

**What it is:** Using BOTH old encryption AND new encryption together.

**Plain English:** Belt AND suspenders. If one fails, the other still works.

```
HYBRID ENCRYPTION
─────────────────
Classical (ECDH)  ──┐
                    ├──→ Combined Secret
Quantum (ML-KEM) ──┘

To break this, attacker needs to break BOTH.
```

**Why we use it:** Post-quantum cryptography is new. What if there's a bug we haven't found? By combining with battle-tested classical crypto, we're protected either way.

---

## MATHEMATICAL FOUNDATIONS

### φ (Phi) - The Golden Ratio

**What it is:** A number that appears everywhere in nature: 1.618033988749895...

**Where it appears:**
- Sunflower seed spirals
- Nautilus shell chambers
- Galaxy arm curves
- DNA helix proportions
- The Parthenon's dimensions

**How ARC-8 uses it:**
- **Access tiers:** You need 61.8% alignment (φ^-1) to reach FULL access
- **History weighting:** Recent vs old actions balanced by phi
- **Spiral compression:** Data stored in golden spiral patterns

**Plain English:** Nature figured out the optimal ratio billions of years ago. We use the same ratio to determine trust.

---

### Fibonacci Sequence

**What it is:** A sequence where each number is the sum of the two before it.

```
1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144...
```

**The magic:** Divide any Fibonacci number by the one before it, and you get closer and closer to phi (1.618...).

**How ARC-8 uses it:**
- **History weighting:** Older actions weighted by Fibonacci numbers
- **Minimum actions:** 21 actions required before tier calculation (21 is F(8))
- **Time gates:** Fibonacci-timed checkpoints

---

### Golden Angle (137.5°)

**What it is:** The angle that creates optimal packing in spirals.

**Plain English:** If you're a sunflower placing seeds, rotating 137.5° between each seed gives the most efficient arrangement. No wasted space. No overlap.

**How ARC-8 uses it:**
- Positioning nodes in visualizations
- Distributing data points in spirals
- Creating efficient storage patterns

---

## IDENTITY & SOVEREIGNTY

### Seed

**What it is:** The root of your digital identity in ARC-8.

**Plain English:** A secret number that only you have, stored only on your device. Everything about your identity (keys, signatures, fingerprint) is mathematically derived from this seed.

**Like a seed in nature:** From one seed, an entire tree grows. From your digital seed, your entire identity grows.

**Critical:** If you lose your seed, you lose your identity. If someone steals your seed, they become you.

---

### Genesis Entropy

**What it is:** The original randomness used to create your seed.

**Plain English:** When you first set up ARC-8, your device gathers randomness (mouse movements, timing, hardware noise) to create something truly unpredictable. This becomes the foundation of your seed.

**Why it matters:** If the starting randomness is weak, everything built on it is weak. We use multiple sources of randomness combined together.

---

### Local-First

**What it is:** Your data stays on YOUR device unless YOU choose to share it.

**The opposite:** Cloud-first (Google, Facebook) where your data lives on their servers.

```
CLOUD-FIRST                 LOCAL-FIRST
───────────                 ───────────
Your photos on              Your photos on
Google's servers            YOUR device

Google can see them         Only YOU can see them
Google can lose them        Only YOU can lose them
Google can sell them        Only YOU can share them
```

**ARC-8's promise:** We literally cannot see your data. It's encrypted on your device with keys only you have.

---

### Sovereign

**What it is:** Having complete control over something.

**Plain English:** A sovereign nation makes its own laws. A sovereign user controls their own data.

**In ARC-8:** You are sovereign over your:
- Seed (identity)
- Data (archives)
- Keys (encryption)
- Sharing (who sees what)

---

## ACCESS CONTROL

### ACU (Alignment Credibility Unit)

**What it is:** A score from 0 to 1 measuring how aligned your behavior is with positive creation.

**Plain English:** Are you contributing to the archive or extracting from it? Creating or exploiting? The math tracks this and adjusts your access accordingly.

**How it's calculated:**
- Every action gets a score (creating content = 0.9, spam = 0.15)
- Your history is weighted by Fibonacci numbers
- Recent actions can't override bad history quickly
- The final ACU determines your access tier

---

### Access Tiers

**What they are:** Levels of access based on your ACU score.

```
TIER 0: BLOCKED     (ACU < 24%)   - No access
TIER 1: DEGRADED    (ACU < 38%)   - Limited 2D view
TIER 2: PARTIAL     (ACU < 62%)   - 3D view, standard features
TIER 3: FULL        (ACU ≥ 62%)   - 4D view, all features
TIER 4: SOVEREIGN   (ACU ≥ 79%)   - Network topology, advanced
```

**Why 62%?** That's φ^(-1), the golden ratio inverse. Nature's threshold.

---

### Quantum Containment

**What it is:** The system that prevents bad actors from gaming their way to high access.

**Plain English:** Scammers can't just do a few good actions to unlock everything. The system:
- Requires minimum history (21 actions)
- Weights old actions MORE than new ones
- Detects oscillating behavior (good/bad/good/bad)
- Checks overall positive ratio

**The philosophy:** "The math decides, not admins."

---

## STORAGE & PRESERVATION

### IPFS (InterPlanetary File System)

**What it is:** A way to store files across many computers instead of one server.

**Plain English:** Instead of your file living on one company's server (which can fail, be hacked, or go bankrupt), it lives on a network of computers around the world. As long as ANY of them has a copy, your file survives.

**How ARC-8 uses it:** Optional backup for your archives. Your data stays local, but you can choose to pin copies on IPFS for redundancy.

---

### Spiral Compression

**What it is:** A way to compress data using golden spiral mathematics.

**Plain English:** Regular compression (ZIP) uses pattern matching. Spiral compression uses the same mathematical patterns found in seashells. The goal: store more data efficiently while preserving fidelity.

**Status:** Theoretical - needs benchmarking against standard compression.

---

### Provenance

**What it is:** The complete history of where something came from.

**Plain English:** For a painting, provenance is: who created it, who owned it, where it's been. For digital content, provenance is cryptographic proof of the same.

**ARC-8's provenance includes:**
- Creator's seed fingerprint
- Timestamp of creation
- Quantum-safe signature
- Hash of the content

**Why it matters:** In an age of deepfakes, proving something is authentic matters.

---

## THE -8 ECOSYSTEM

### DOC-8

**What it is:** The DATABASE & ARCHIVE module.

**Purpose:** Store, verify, and preserve content with full provenance.

**Features:**
- Source Cartography (mapping where information comes from)
- Verification status tracking
- Transcript extraction
- Cross-referencing

---

### IT-R8 (pronounced "iterate")

**What it is:** The CREATE & RATE module.

**Purpose:** Spatial design tool for organizing thoughts and creating new content.

**Features:**
- Thought Stream
- Drag-and-connect interface
- Tagging system
- Spatial canvas

---

### SOCI-8 (pronounced "sociate")

**What it is:** The SHARE & CONNECT module (future).

**Purpose:** Social features built on sovereignty - you control what you share.

---

## VISUALIZATION

### 4D Visualization

**What it is:** Seeing data in four dimensions: X, Y, Z, and TIME.

**Plain English:** Regular 3D shows where things are in space. 4D shows how they change over time. In ARC-8, this means watching your network of connections evolve.

**Access requirement:** FULL tier (ACU ≥ 62%)

---

### Point Cloud

**What it is:** A visualization where each data point is a dot in 3D space.

**In ARC-8:** The 22 NORTHSTAR Masters appear as a point cloud, positioned according to their philosophical relationships.

---

## ACRONYMS QUICK REFERENCE

| Acronym | Full Name | Plain English |
|---------|-----------|---------------|
| ACU | Alignment Credibility Unit | Your trust score |
| AES | Advanced Encryption Standard | Standard encryption (symmetric) |
| ECDH | Elliptic Curve Diffie-Hellman | Old key exchange (quantum-vulnerable) |
| ECDSA | Elliptic Curve Digital Signature | Old signatures (quantum-vulnerable) |
| FIPS | Federal Information Processing Standard | US government approval |
| HKDF | HMAC-based Key Derivation Function | Making keys from secrets |
| IPFS | InterPlanetary File System | Distributed storage |
| KEM | Key Encapsulation Mechanism | Wrapping keys safely |
| ML-DSA | Module Lattice Digital Signature Algorithm | Quantum-safe signatures |
| ML-KEM | Module Lattice Key Encapsulation Mechanism | Quantum-safe key exchange |
| NIST | National Institute of Standards and Technology | US standards body |
| PQC | Post-Quantum Cryptography | Quantum-proof encryption |
| PQS | Pi-Quadratic Seed | Behavioral fingerprinting system |
| PWA | Progressive Web App | Website that works like an app |
| φ (Phi) | Golden Ratio | 1.618... - nature's number |

---

## STILL CONFUSED?

That's okay. Here's the essential truth:

**ARC-8 is a system where:**
1. Your data stays on YOUR device
2. Your identity comes from a secret only YOU have
3. Everything is protected by math so strong that even future supercomputers can't break it
4. The golden ratio - the same pattern in sunflowers and galaxies - decides who gets access
5. You are sovereign

**"Ancient magic of the past, establishing new keys to the future."**

---

*Last updated: 2026-01-15*
