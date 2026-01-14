# QUANTUM CONTAINMENT SYSTEM
## ULTRATHINK: ACU-Gated 4D Blockchain Access with Golden Mean Balance

**Created:** 2026-01-13
**Status:** Architecture Design
**Core Principle:** Mathematical truth as access control

---

## EXECUTIVE VISION

> "The best quantum containment away from scammers is to make the code itself weigh the balance"
> — Founder

Instead of traditional permission systems (admin decides who's good), this architecture uses **mathematical truth** derived from user behavior to automatically gate access to sensitive visualizations. Users aligned with NORTHSTAR principals can see the full 4D blockchain; those who violate alignment see a degraded or blocked view.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QUANTUM CONTAINMENT                                 │
│                     "The Math Decides, Not Admins"                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   USER BEHAVIOR                                                             │
│       │                                                                     │
│       ▼                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    RECURSIVE ACU CALCULATION                        │   │
│   │                    ═══════════════════════════                      │   │
│   │    ACU(t) = φ · ACU(t-1) + (1-φ) · current_action_score            │   │
│   │                                                                     │   │
│   │    Where:                                                           │   │
│   │    • φ = 0.618... (Golden Ratio inverse)                           │   │
│   │    • Historical behavior weighted by golden spiral                  │   │
│   │    • New actions contribute (1-φ) ≈ 0.382                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    NORTHSTAR ALIGNMENT CHECK                        │   │
│   │                    ═════════════════════════════                    │   │
│   │    Verify against 11 Non-Negotiables                               │   │
│   │    Calculate alignment_score (0.0 - 1.0)                           │   │
│   │    PHI_THRESHOLD = 0.618                                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ├─── alignment >= PHI ────▶ FULL 4D BLOCKCHAIN ACCESS               │
│       │                                                                     │
│       └─── alignment < PHI ─────▶ DEGRADED/BLOCKED VIEW                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. THE 11 NON-NEGOTIABLES (NORTHSTAR PRINCIPALS)

Every user action is scored against these principals:

| # | Principal | Detection Method | Weight |
|---|-----------|------------------|--------|
| 1 | User owns their seed | Local storage only | 1.0 |
| 2 | No tracking without consent | Consent log present | 0.9 |
| 3 | Data transformations reversible | Export capability used | 0.8 |
| 4 | Spiral compression preserves fidelity | Lossless verified | 0.7 |
| 5 | Local-first, cloud-optional | Offline usage patterns | 0.9 |
| 6 | Algorithms serve users | No dark patterns detected | 0.8 |
| 7 | Privacy is default | Minimal permissions | 0.9 |
| 8 | Creation direction = +1 | Net positive contributions | 1.0 |
| 9 | Mathematical verification | Provenance signatures valid | 0.9 |
| 10 | Lineage values guide suggestions | Source attribution present | 0.8 |
| 11 | **Balance polarity** | PHI threshold maintained | 1.0 |

---

## 2. RECURSIVE ACU CALCULATION

### 2.1 The Golden Spiral Accumulator

```javascript
/**
 * RECURSIVE ACU ENGINE
 * Uses golden mean for weighted historical balance
 */
class RecursiveACUEngine {
    constructor() {
        this.PHI = 1.618033988749895;           // Golden ratio
        this.PHI_INVERSE = 0.6180339887498949;  // φ^(-1) = φ - 1
        this.GOLDEN_ANGLE = 137.5077640500378;  // Degrees

        // Historical weights follow Fibonacci spiral
        this.fibonacciWeights = this._generateFibonacciWeights(21);
    }

    /**
     * Calculate current ACU using recursive golden mean
     * ACU(t) = φ^(-1) · ACU(t-1) + (1 - φ^(-1)) · current_score
     */
    calculateACU(history, currentAction) {
        if (history.length === 0) {
            return this._scoreAction(currentAction);
        }

        // Recursive calculation
        const previousACU = this.calculateACU(
            history.slice(0, -1),
            history[history.length - 1]
        );

        const currentScore = this._scoreAction(currentAction);

        // Golden mean weighted combination
        return (this.PHI_INVERSE * previousACU) +
               ((1 - this.PHI_INVERSE) * currentScore);
    }

    /**
     * Alternative: Iterative with Fibonacci weights
     * More efficient for long histories
     */
    calculateACUIterative(actionHistory) {
        if (actionHistory.length === 0) return 0.5; // Neutral

        let weightedSum = 0;
        let totalWeight = 0;

        // Apply Fibonacci-weighted importance
        // Recent actions weighted by F(n), older by F(n-1), etc.
        for (let i = 0; i < actionHistory.length; i++) {
            const age = actionHistory.length - 1 - i;
            const weight = this._fibonacciWeight(age);
            const score = this._scoreAction(actionHistory[i]);

            weightedSum += score * weight;
            totalWeight += weight;
        }

        return weightedSum / totalWeight;
    }

    /**
     * Generate Fibonacci weights
     * F(0)=1, F(1)=1, F(n)=F(n-1)+F(n-2)
     */
    _generateFibonacciWeights(n) {
        const weights = [1, 1];
        for (let i = 2; i < n; i++) {
            weights.push(weights[i-1] + weights[i-2]);
        }
        return weights;
    }

    _fibonacciWeight(age) {
        if (age >= this.fibonacciWeights.length) {
            return this.fibonacciWeights[this.fibonacciWeights.length - 1];
        }
        return this.fibonacciWeights[age];
    }
}
```

### 2.2 Action Scoring

```javascript
/**
 * Score an individual action against NORTHSTAR principals
 */
_scoreAction(action) {
    const scores = {
        // POSITIVE ACTIONS (toward +1 creation direction)
        'create_content':        +0.8,
        'verify_source':         +0.9,
        'share_with_attribution':+0.7,
        'contribute_to_archive': +1.0,
        'generate_provenance':   +0.9,
        'consent_granted':       +0.5,
        'offline_usage':         +0.6,
        'export_data':           +0.4,

        // NEUTRAL ACTIONS
        'view_content':          +0.0,
        'search':                +0.0,

        // WARNING ACTIONS (toward -1 extraction)
        'excessive_downloads':   -0.3,
        'rapid_scraping':        -0.5,
        'consent_denied':        -0.2,
        'provenance_skip':       -0.4,

        // VIOLATION ACTIONS (malicious patterns)
        'malicious_upload':      -1.0,  // Virus detected
        'fake_provenance':       -0.9,  // Forged signatures
        'spam_content':          -0.7,
        'impersonation':         -0.8,
        'extraction_pattern':    -0.6   // Taking without giving
    };

    // Normalize to [0, 1] range
    const rawScore = scores[action.type] || 0;
    return (rawScore + 1) / 2;  // -1..+1 → 0..1
}
```

---

## 3. MALICIOUS BEHAVIOR DETECTION

### 3.1 Pattern Recognition Engine

```javascript
/**
 * MALICIOUS PATTERN DETECTOR
 * Identifies scammers before they see sensitive data
 */
class MaliciousPatternDetector {
    constructor() {
        this.patterns = {
            // Extraction patterns (taking without giving)
            extraction: {
                threshold: 10,        // Downloads without contributions
                window: 3600000,      // 1 hour
                weight: -0.5
            },

            // Rapid scraping (automated attacks)
            scraping: {
                threshold: 100,       // Requests per minute
                window: 60000,        // 1 minute
                weight: -0.8
            },

            // Fake provenance attempts
            forgery: {
                signaturesFailedRatio: 0.3,  // >30% invalid = suspicious
                weight: -0.9
            },

            // Malicious output detection
            malware: {
                virusSignatures: [],  // Updated from network
                weight: -1.0
            }
        };

        this.userActivity = new Map();  // userId → activity log
    }

    /**
     * Analyze user behavior for malicious patterns
     * @returns {Object} { isMalicious, confidence, patterns }
     */
    analyzeUser(userId, recentActions) {
        const detectedPatterns = [];
        let maliciousScore = 0;

        // Check extraction pattern
        const downloads = recentActions.filter(a => a.type === 'download');
        const contributions = recentActions.filter(a =>
            ['create_content', 'verify_source', 'share_with_attribution'].includes(a.type)
        );

        if (downloads.length > this.patterns.extraction.threshold &&
            contributions.length === 0) {
            detectedPatterns.push('EXTRACTION_PATTERN');
            maliciousScore += this.patterns.extraction.weight;
        }

        // Check scraping pattern
        const requestsPerMinute = this._calculateRequestRate(recentActions);
        if (requestsPerMinute > this.patterns.scraping.threshold) {
            detectedPatterns.push('AUTOMATED_SCRAPING');
            maliciousScore += this.patterns.scraping.weight;
        }

        // Check signature forgery attempts
        const signatureAttempts = recentActions.filter(a =>
            a.type === 'verify_signature'
        );
        const failedSignatures = signatureAttempts.filter(a => !a.valid);

        if (signatureAttempts.length > 0) {
            const failRatio = failedSignatures.length / signatureAttempts.length;
            if (failRatio > this.patterns.forgery.signaturesFailedRatio) {
                detectedPatterns.push('FORGERY_ATTEMPTS');
                maliciousScore += this.patterns.forgery.weight * failRatio;
            }
        }

        // Check for malware in uploads
        const uploads = recentActions.filter(a => a.type === 'upload');
        for (const upload of uploads) {
            if (this._containsMalware(upload.content)) {
                detectedPatterns.push('MALWARE_UPLOAD');
                maliciousScore += this.patterns.malware.weight;
            }
        }

        // Normalize to confidence score
        const confidence = Math.abs(maliciousScore) / 3;  // Max 3 patterns

        return {
            isMalicious: maliciousScore < -0.5,
            confidence: Math.min(1, confidence),
            patterns: detectedPatterns,
            rawScore: maliciousScore
        };
    }
}
```

### 3.2 Virus Scanning Integration

```javascript
/**
 * NETWORK-UPDATED VIRUS SCANNER
 * Signatures distributed via IPFS for decentralized updates
 */
class NetworkVirusScanner {
    constructor() {
        this.signatureIPFSHash = null;  // Latest signatures CID
        this.localSignatures = [];
        this.lastUpdate = null;
    }

    /**
     * Fetch latest virus signatures from IPFS
     */
    async updateSignatures() {
        try {
            // Fetch signature index from known gateway
            const response = await fetch(
                `https://ipfs.io/ipfs/${this.signatureIPFSHash}`
            );
            const signatures = await response.json();

            this.localSignatures = signatures;
            this.lastUpdate = Date.now();

            console.log(`[Scanner] Updated ${signatures.length} signatures`);
        } catch (e) {
            console.warn('[Scanner] Could not update signatures, using cached');
        }
    }

    /**
     * Scan content for known malicious patterns
     */
    async scanContent(content) {
        const contentHash = await this._hashContent(content);

        // Check against known malicious hashes
        for (const sig of this.localSignatures) {
            if (sig.type === 'hash' && sig.value === contentHash) {
                return { clean: false, threat: sig.name };
            }

            if (sig.type === 'pattern' && content.includes(sig.value)) {
                return { clean: false, threat: sig.name };
            }
        }

        return { clean: true, scannedAt: Date.now() };
    }
}
```

---

## 4. 4D BLOCKCHAIN VISUALIZATION GATING

### 4.1 Access Tiers Based on Alignment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       4D VISUALIZATION ACCESS TIERS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   TIER 0: BLOCKED (ACU < 0.236)                                            │
│   ═══════════════════════════════                                          │
│   • Cannot see blockchain at all                                           │
│   • Shows "Access requires alignment with NORTHSTAR principals"            │
│   • Redirect to principals documentation                                    │
│   • 🔴 Red indicator                                                        │
│                                                                             │
│   TIER 1: DEGRADED (0.236 ≤ ACU < 0.382)                                   │
│   ═════════════════════════════════════                                    │
│   • 2D flat view only (no depth)                                           │
│   • Limited transaction history (last 100)                                 │
│   • No time-dimension animation                                            │
│   • 🟠 Orange indicator                                                     │
│                                                                             │
│   TIER 2: PARTIAL (0.382 ≤ ACU < 0.618)                                    │
│   ═════════════════════════════════════                                    │
│   • 3D view (x, y, z spatial)                                              │
│   • Full transaction history                                               │
│   • No time dimension (static snapshot)                                    │
│   • 🟡 Yellow indicator                                                     │
│                                                                             │
│   TIER 3: FULL (ACU ≥ 0.618 = φ^(-1))                                      │
│   ═════════════════════════════════════                                    │
│   • Full 4D view (x, y, z, time)                                           │
│   • Animated transaction flow                                              │
│   • Predictive path visualization                                          │
│   • Inter-archive connections                                              │
│   • 🟢 Green indicator                                                      │
│                                                                             │
│   TIER 4: SOVEREIGN (ACU ≥ 0.854 = φ^(-0.5))                               │
│   ═══════════════════════════════════════════                              │
│   • All Tier 3 features                                                    │
│   • Can view other users' provenance chains                                │
│   • Network topology visualization                                         │
│   • Contribution to signature verification network                         │
│   • 🔵 Blue indicator (NORTHSTAR aligned)                                  │
│                                                                             │
│   THRESHOLDS (Golden Ratio Powers):                                        │
│   ─────────────────────────────────                                        │
│   φ^(-2) = 0.236...  (Blocked threshold)                                   │
│   φ^(-1.5) = 0.382... (Degraded threshold)                                 │
│   φ^(-1) = 0.618...  (Full access threshold - THE PHI GATE)                │
│   φ^(-0.5) = 0.854... (Sovereign threshold)                                │
│   φ^(0) = 1.0        (Perfect alignment - theoretical maximum)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Implementation

```javascript
/**
 * 4D BLOCKCHAIN VISUALIZATION GATING
 * Access determined by golden ratio thresholds
 */
class QuantumContainmentGate {
    constructor() {
        this.PHI = 1.618033988749895;

        // Golden ratio power thresholds
        this.THRESHOLDS = {
            BLOCKED:   Math.pow(this.PHI, -2),    // 0.236
            DEGRADED:  Math.pow(this.PHI, -1.5),  // 0.382
            PARTIAL:   Math.pow(this.PHI, -1),    // 0.618
            FULL:      Math.pow(this.PHI, -1),    // 0.618 (THE PHI GATE)
            SOVEREIGN: Math.pow(this.PHI, -0.5)   // 0.854
        };

        this.acuEngine = new RecursiveACUEngine();
        this.malwareDetector = new MaliciousPatternDetector();
    }

    /**
     * Determine user's visualization access tier
     */
    async determineAccessTier(userId, userHistory) {
        // Step 1: Check for malicious patterns (instant block)
        const maliciousCheck = this.malwareDetector.analyzeUser(userId, userHistory);

        if (maliciousCheck.isMalicious) {
            return {
                tier: 0,
                name: 'BLOCKED',
                reason: `Malicious patterns detected: ${maliciousCheck.patterns.join(', ')}`,
                acuScore: 0,
                features: this._getTierFeatures(0),
                indicator: '🔴',
                canAppeal: true,
                appealPath: '/appeal/malicious-detection'
            };
        }

        // Step 2: Calculate ACU using recursive golden mean
        const acuScore = this.acuEngine.calculateACUIterative(userHistory);

        // Step 3: Determine tier based on golden ratio thresholds
        let tier, tierName;

        if (acuScore < this.THRESHOLDS.BLOCKED) {
            tier = 0;
            tierName = 'BLOCKED';
        } else if (acuScore < this.THRESHOLDS.DEGRADED) {
            tier = 1;
            tierName = 'DEGRADED';
        } else if (acuScore < this.THRESHOLDS.FULL) {
            tier = 2;
            tierName = 'PARTIAL';
        } else if (acuScore < this.THRESHOLDS.SOVEREIGN) {
            tier = 3;
            tierName = 'FULL';
        } else {
            tier = 4;
            tierName = 'SOVEREIGN';
        }

        return {
            tier,
            name: tierName,
            acuScore,
            nextThreshold: this._getNextThreshold(tier),
            actionsToAdvance: this._calculateActionsToAdvance(acuScore, tier),
            features: this._getTierFeatures(tier),
            indicator: this._getTierIndicator(tier)
        };
    }

    /**
     * Get features available at each tier
     */
    _getTierFeatures(tier) {
        const features = {
            0: {
                viewDimensions: 0,
                transactionHistory: 0,
                timeAnimation: false,
                interArchive: false,
                networkTopology: false
            },
            1: {
                viewDimensions: 2,
                transactionHistory: 100,
                timeAnimation: false,
                interArchive: false,
                networkTopology: false
            },
            2: {
                viewDimensions: 3,
                transactionHistory: Infinity,
                timeAnimation: false,
                interArchive: false,
                networkTopology: false
            },
            3: {
                viewDimensions: 4,
                transactionHistory: Infinity,
                timeAnimation: true,
                interArchive: true,
                networkTopology: false
            },
            4: {
                viewDimensions: 4,
                transactionHistory: Infinity,
                timeAnimation: true,
                interArchive: true,
                networkTopology: true,
                verificationNetwork: true
            }
        };

        return features[tier] || features[0];
    }

    _getTierIndicator(tier) {
        return ['🔴', '🟠', '🟡', '🟢', '🔵'][tier] || '⚪';
    }
}
```

---

## 5. IPFS BLOCKCHAIN INTEGRATION

### 5.1 4D Spatial Existence on IPFS

```javascript
/**
 * 4D BLOCKCHAIN SPATIAL MAPPER
 * Maps transactions to 4D coordinates for visualization
 */
class BlockchainSpatialMapper {
    constructor() {
        this.PHI = 1.618033988749895;
        this.GOLDEN_ANGLE = 137.5077640500378;
    }

    /**
     * Map transaction to 4D coordinates
     * x: Account cluster (golden spiral)
     * y: Transaction type (vertical axis)
     * z: Value magnitude (depth)
     * t: Timestamp (time dimension)
     */
    mapTransaction(tx) {
        const index = tx.nonce || tx.index;

        // X: Golden spiral positioning for accounts
        const theta = (index * this.GOLDEN_ANGLE) * (Math.PI / 180);
        const r = Math.sqrt(index) * 10;
        const x = r * Math.cos(theta);

        // Y: Transaction type vertical separation
        const typeOffsets = {
            'provenance_create': 0,
            'provenance_verify': 1,
            'content_archive':   2,
            'contribution':      3,
            'transfer':          4
        };
        const y = (typeOffsets[tx.type] || 0) * 50;

        // Z: Value magnitude (log scale)
        const z = tx.value ? Math.log10(tx.value + 1) * 20 : 0;

        // T: Normalized time (0 = genesis, 1 = now)
        const genesisTime = 1704067200000;  // Jan 1, 2024
        const now = Date.now();
        const t = (tx.timestamp - genesisTime) / (now - genesisTime);

        return {
            x, y, z, t,
            color: this._getTransactionColor(tx),
            size: this._getTransactionSize(tx),
            ipfsHash: tx.contentCID,
            metadata: tx.metadata
        };
    }

    /**
     * Generate 4D point cloud for IPFS content
     */
    async generatePointCloud(transactions, accessTier) {
        const points = transactions.map(tx => this.mapTransaction(tx));

        // Apply tier-based visibility
        const visiblePoints = this._applyTierFilter(points, accessTier);

        // Store on IPFS for decentralized access
        const pointCloudCID = await this._storeOnIPFS({
            points: visiblePoints,
            generatedAt: Date.now(),
            dimensions: accessTier.features.viewDimensions,
            metadata: {
                totalTransactions: transactions.length,
                visibleTransactions: visiblePoints.length,
                tierApplied: accessTier.name
            }
        });

        return {
            cid: pointCloudCID,
            points: visiblePoints,
            accessTier: accessTier.name
        };
    }

    /**
     * Apply tier-based filtering to point cloud
     */
    _applyTierFilter(points, accessTier) {
        const features = accessTier.features;

        if (features.viewDimensions === 0) {
            return [];  // Blocked - no points
        }

        let filtered = points;

        // Limit history for lower tiers
        if (features.transactionHistory < Infinity) {
            filtered = filtered.slice(-features.transactionHistory);
        }

        // Remove time dimension for tiers < 3
        if (!features.timeAnimation) {
            filtered = filtered.map(p => ({ ...p, t: 0 }));
        }

        // Flatten to 2D for tier 1
        if (features.viewDimensions === 2) {
            filtered = filtered.map(p => ({ ...p, z: 0, t: 0 }));
        }

        return filtered;
    }
}
```

---

## 6. FAILSAFE MECHANISMS

### 6.1 Identified Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ACU manipulation (fake positive actions) | High | Actions require quantum signature + external verification |
| False positive malware detection | Medium | Appeal process + human review for edge cases |
| Threshold gaming (hover just above) | Low | Fibonacci-weighted history prevents sudden jumps |
| Network partition (offline users) | Medium | Cached tier, re-verify on reconnect |
| Sybil attack (multiple accounts) | High | Device fingerprint + behavioral biometrics |
| Key compromise | Critical | Automatic key rotation + seed derivation |

### 6.2 Appeal Process

```javascript
/**
 * CONTAINMENT APPEAL SYSTEM
 * Users can appeal tier decisions with evidence
 */
class ContainmentAppeal {
    async submitAppeal(userId, currentTier, evidence) {
        const appeal = {
            id: crypto.randomUUID(),
            userId,
            currentTier,
            requestedTier: currentTier + 1,
            evidence,
            submittedAt: Date.now(),
            status: 'pending',

            // Evidence requirements
            evidenceTypes: {
                'false_positive': {
                    required: ['explanation', 'activity_context'],
                    reviewType: 'automated'
                },
                'malware_false_positive': {
                    required: ['file_hash', 'independent_scan'],
                    reviewType: 'manual'
                },
                'threshold_recalculation': {
                    required: ['additional_contributions'],
                    reviewType: 'automated'
                }
            }
        };

        // Store appeal on IPFS for transparency
        appeal.ipfsCID = await this._storeOnIPFS(appeal);

        return appeal;
    }
}
```

### 6.3 Recursive Verification Chain

```javascript
/**
 * RECURSIVE VERIFICATION
 * Each verification is verified by the previous
 */
class RecursiveVerificationChain {
    constructor() {
        this.PHI = 1.618033988749895;
    }

    /**
     * Verify action with recursive chain depth
     * depth = log_φ(importance) where importance ∈ [1, ∞)
     */
    async verifyWithChain(action, importance = 1) {
        // Calculate required verification depth
        const depth = Math.ceil(Math.log(importance) / Math.log(this.PHI));

        let verification = await this._singleVerify(action);
        let chainDepth = 0;

        // Recursively verify until depth reached
        while (chainDepth < depth && verification.valid) {
            const parentVerification = verification;
            verification = await this._verifyVerification(parentVerification);
            verification.parent = parentVerification;
            chainDepth++;
        }

        return {
            valid: verification.valid,
            chainDepth,
            requiredDepth: depth,
            chainComplete: chainDepth >= depth,
            verificationChain: verification
        };
    }
}
```

---

## 7. VISUAL DESIGN

### 7.1 Tier Indicator UI

```css
/* QUANTUM CONTAINMENT TIER INDICATORS */

.tier-indicator {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    position: relative;
}

.tier-indicator::after {
    content: attr(data-acu);
    position: absolute;
    bottom: -20px;
    font-size: 10px;
    color: var(--text-dim);
}

.tier-0 { background: radial-gradient(circle, #ff4444, #880000); }
.tier-1 { background: radial-gradient(circle, #ffaa44, #884400); }
.tier-2 { background: radial-gradient(circle, #ffff44, #888800); }
.tier-3 { background: radial-gradient(circle, #44ff44, #008800); }
.tier-4 { background: radial-gradient(circle, #4444ff, #000088);
          box-shadow: 0 0 20px rgba(100, 100, 255, 0.5); }

/* Pulsing animation for tier progression opportunity */
.tier-indicator.can-advance {
    animation: pulse-advance 2s infinite;
}

@keyframes pulse-advance {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}
```

### 7.2 4D Visualization Degradation

```
TIER 4 (SOVEREIGN):
┌─────────────────────────────────────────┐
│ ╱╲    4D: Full time animation          │
│╱──╲   Network topology visible          │
│╲──╱   All archives interconnected       │
│ ╲╱    Verification node status          │
└─────────────────────────────────────────┘

TIER 3 (FULL):
┌─────────────────────────────────────────┐
│ ╱╲    4D: Time animation enabled        │
│╱──╲   Predictive paths visible          │
│╲──╱   Inter-archive connections         │
│ ╲╱                                      │
└─────────────────────────────────────────┘

TIER 2 (PARTIAL):
┌─────────────────────────────────────────┐
│ ╱╲    3D: Static snapshot              │
│╱  ╲   No time dimension                │
│╲  ╱   Full history but frozen          │
│ ╲╱                                      │
└─────────────────────────────────────────┘

TIER 1 (DEGRADED):
┌─────────────────────────────────────────┐
│╱────╲  2D: Flat view only              │
│╲────╱  Last 100 transactions           │
│        Limited context                  │
└─────────────────────────────────────────┘

TIER 0 (BLOCKED):
┌─────────────────────────────────────────┐
│  ⊘    "Access requires alignment"       │
│       with NORTHSTAR principals         │
│       [Learn More]                      │
└─────────────────────────────────────────┘
```

---

## 8. QUESTIONS FOR FOUNDER

1. **Tier Thresholds**: Should we use the proposed golden ratio powers (0.236, 0.382, 0.618, 0.854) or different values?

2. **Appeal Process**: Should appeals be automated (re-run ACU with new evidence) or require manual review?

3. **Malware Signatures**: Should we maintain our own IPFS-distributed signature database or integrate with existing services (VirusTotal API)?

4. **Sybil Protection**: How aggressive should device fingerprinting be? (Privacy tradeoff)

5. **Recovery Path**: Should blocked users be able to recover by positive actions, or require appeal?

6. **Network Verification**: Should NORTHSTAR-aligned users (Tier 4) participate in verification consensus for detecting malicious actors?

---

## APPENDIX: GOLDEN RATIO MATHEMATICS

### Why Golden Ratio for Security?

```
φ = (1 + √5) / 2 = 1.618033988749895...

PROPERTIES:
• Self-similar: φ² = φ + 1
• Recursive:    φⁿ = φⁿ⁻¹ + φⁿ⁻²
• Optimal:      Most irrational number (hardest to approximate)

SECURITY APPLICATION:
• Fibonacci weighting prevents gaming (no round numbers)
• Golden spiral distribution prevents clustering attacks
• Phi thresholds create natural "resonance" points
• Impossible to predict exact threshold crossing

The golden ratio appears throughout nature because it optimizes
distribution and growth. We use it to optimize trust distribution.
```

---

*This architecture makes the math decide who can be trusted.*
*Scammers can't game what they can't predict.*
*NORTHSTAR alignment is measured, not declared.*
