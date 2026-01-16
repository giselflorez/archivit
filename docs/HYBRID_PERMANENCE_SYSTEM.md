# HYBRID PERMANENCE SYSTEM

## IPFS + Arweave Unified Storage

**Created:** 2026-01-16
**Status:** NOVEL INVENTION
**Purpose:** Combine IPFS speed with Arweave permanence

---

## THE PROBLEM

| System | Strength | Weakness |
|--------|----------|----------|
| IPFS | Fast, cheap, scalable | Requires ongoing pinning fees |
| Arweave | Permanent, pay once | Slower, expensive for large files |

Neither is perfect alone.

---

## THE INVENTION: DUAL-LAYER PERMANENCE

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER UPLOADS CONTENT                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: IPFS (SPEED)                        │
│                                                                  │
│  • Immediate upload (< 5 seconds)                               │
│  • Full content stored                                          │
│  • CID generated: bafybeig...                                   │
│  • Pinned to 2+ providers                                       │
│  • Accessible via fast CDN gateways                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 2: ARWEAVE (PERMANENCE)                   │
│                                                                  │
│  • Anchor record (not full content)                             │
│  • Contains: IPFS CID + metadata hash + timestamp               │
│  • Permanent proof of existence                                 │
│  • TX ID: ar://abc123...                                        │
│  • Costs ~$0.0001 per record                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  UNIFIED PROVENANCE PROOF                       │
│                                                                  │
│  {                                                              │
│    "ipfs_cid": "bafybeig...",                                  │
│    "arweave_tx": "abc123...",                                  │
│    "content_hash": "sha384:...",                               │
│    "timestamp": 1705384800,                                    │
│    "permanent": true                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## PERMANENCE TIERS

| Tier | IPFS | Arweave | Cost | Use Case |
|------|------|---------|------|----------|
| **TEMPORARY** | Pinned 30 days | None | Free | Drafts, previews |
| **STANDARD** | Pinned ongoing | Anchor only | $0.40/GB/mo + $0.0001 | Most content |
| **PERMANENT** | Pinned ongoing | Full content | $0.40/GB/mo + $5/GB | Critical records |
| **ARCHIVAL** | Optional | Full + redundant | $10/GB one-time | Museum-grade |

---

## DATA FLOW

### Upload Process

```javascript
class HybridPermanence {

    async upload(content, tier = 'STANDARD') {
        const result = {
            tier,
            ipfs: null,
            arweave: null,
            proof: null
        };

        // Step 1: Always upload to IPFS first (fast)
        const ipfsCid = await this.ipfs.add(content);
        result.ipfs = {
            cid: ipfsCid,
            gateway: `https://gateway.pinata.cloud/ipfs/${ipfsCid}`,
            pinned: true
        };

        // Step 2: Pin to multiple providers
        await this.pinata.pin(ipfsCid);
        await this.web3storage.pin(ipfsCid);

        // Step 3: Arweave based on tier
        if (tier === 'TEMPORARY') {
            // No Arweave
            result.arweave = null;
        }
        else if (tier === 'STANDARD') {
            // Anchor only (small record pointing to IPFS)
            const anchor = {
                type: 'ARC8_ANCHOR',
                version: '1.0',
                ipfs_cid: ipfsCid,
                content_hash: await this.hash(content),
                size: content.length,
                timestamp: Date.now()
            };
            const arTx = await this.arweave.upload(JSON.stringify(anchor));
            result.arweave = {
                tx: arTx,
                type: 'anchor',
                gateway: `https://arweave.net/${arTx}`
            };
        }
        else if (tier === 'PERMANENT' || tier === 'ARCHIVAL') {
            // Full content to Arweave
            const arTx = await this.arweave.upload(content);
            result.arweave = {
                tx: arTx,
                type: 'full',
                gateway: `https://arweave.net/${arTx}`
            };
        }

        // Step 4: Generate unified proof
        result.proof = this.generateProof(result);

        return result;
    }

    generateProof(result) {
        return {
            id: `arc8://${result.ipfs.cid}`,
            ipfs: result.ipfs.cid,
            arweave: result.arweave?.tx || null,
            permanence_tier: result.tier,
            created: Date.now(),
            retrievable_via: [
                result.ipfs.gateway,
                result.arweave?.gateway
            ].filter(Boolean)
        };
    }
}
```

---

## RETRIEVAL STRATEGY

### Fallback Chain

```javascript
async function retrieve(provenanceProof) {
    const sources = [
        // 1. Try IPFS gateways first (fastest)
        () => fetch(`https://gateway.pinata.cloud/ipfs/${provenanceProof.ipfs}`),
        () => fetch(`https://w3s.link/ipfs/${provenanceProof.ipfs}`),
        () => fetch(`https://cloudflare-ipfs.com/ipfs/${provenanceProof.ipfs}`),

        // 2. Try Arweave if IPFS fails (permanent backup)
        () => provenanceProof.arweave
            ? fetch(`https://arweave.net/${provenanceProof.arweave}`)
            : null,

        // 3. Try Arweave gateways
        () => provenanceProof.arweave
            ? fetch(`https://ar-io.net/${provenanceProof.arweave}`)
            : null
    ];

    for (const source of sources) {
        try {
            const response = await source();
            if (response?.ok) return response;
        } catch (e) {
            continue;
        }
    }

    throw new Error('Content unavailable from all sources');
}
```

---

## COST COMPARISON

### Scenario: 1,000 Artists, 100 Records Each

| Approach | Monthly Cost | 10-Year Cost |
|----------|--------------|--------------|
| IPFS only | $250/mo | $30,000 |
| Arweave only | $0 (one-time $500) | $500 |
| **Hybrid (anchors)** | $200/mo + $10 one-time | $24,010 |
| **Hybrid (smart)** | $100/mo + $50 one-time | $12,050 |

### Smart Hybrid Strategy

```
PROVENANCE RECORDS (100KB each):
→ IPFS + Arweave anchor = $0.0001 per record
→ 100,000 records = $10 total, permanent proof

THUMBNAILS (200KB each):
→ IPFS only = included in $200/mo
→ If IPFS fails, regenerate from full image

FULL IMAGES (5MB each):
→ IPFS with 2-provider redundancy
→ Arweave only for ARCHIVAL tier users

VIDEOS:
→ IPFS only (too expensive for Arweave)
→ User responsible for backup
```

---

## ARWEAVE ANCHOR FORMAT

### Schema

```json
{
    "type": "ARC8_PERMANENCE_ANCHOR",
    "version": "1.0.0",
    "content": {
        "ipfs_cid": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        "sha384": "a8b4c5d6e7f8...",
        "size_bytes": 102400,
        "mime_type": "application/json"
    },
    "provenance": {
        "creator_wallet": "0x1234...abcd",
        "created_at": 1705384800,
        "nist_beacon_pulse": 12345678,
        "pqs_vertex": {"x": 0.618, "y": 0.786}
    },
    "signatures": {
        "dilithium": "ML-DSA-65 signature...",
        "traditional": "ECDSA signature (optional)..."
    }
}
```

### Size: ~500 bytes = ~$0.00005 per anchor

---

## VERIFICATION

### Prove Content Exists

```javascript
async function verifyPermanence(proof) {
    const checks = {
        ipfs_available: false,
        arweave_anchored: false,
        hashes_match: false,
        signature_valid: false
    };

    // Check IPFS availability
    try {
        const ipfsContent = await fetchIPFS(proof.ipfs);
        checks.ipfs_available = true;

        // Verify hash
        const hash = await sha384(ipfsContent);
        checks.hashes_match = (hash === proof.content_hash);
    } catch (e) {
        checks.ipfs_available = false;
    }

    // Check Arweave anchor
    if (proof.arweave) {
        try {
            const anchor = await fetchArweave(proof.arweave);
            checks.arweave_anchored = true;

            // Verify anchor points to same IPFS CID
            checks.anchor_valid = (anchor.content.ipfs_cid === proof.ipfs);
        } catch (e) {
            checks.arweave_anchored = false;
        }
    }

    // Verify signature
    if (proof.signatures?.dilithium) {
        checks.signature_valid = await verifyDilithium(
            proof.signatures.dilithium,
            proof
        );
    }

    return {
        verified: checks.ipfs_available &&
                  checks.arweave_anchored &&
                  checks.hashes_match,
        checks
    };
}
```

---

## MIGRATION PATH

### Upgrade Content Permanence

```javascript
async function upgradeToPermanent(ipfsCid) {
    // 1. Fetch content from IPFS
    const content = await fetchIPFS(ipfsCid);

    // 2. Upload full content to Arweave
    const arTx = await arweave.upload(content);

    // 3. Update proof record
    await updateProvenanceRecord(ipfsCid, {
        arweave_tx: arTx,
        permanence_tier: 'PERMANENT',
        upgraded_at: Date.now()
    });

    return arTx;
}
```

---

## UNIQUE IDENTIFIER

### ARC8 URI Format

```
arc8://{ipfs_cid}?ar={arweave_tx}

Example:
arc8://bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi?ar=abc123xyz

Resolution:
1. Parse CID and AR tx from URI
2. Try IPFS first
3. Fall back to Arweave
4. Verify hash matches
```

---

## IMPLEMENTATION

### Dependencies

```bash
npm install @irys/sdk        # Arweave bundler (cheaper uploads)
npm install arweave          # Direct Arweave access
npm install ipfs-http-client # IPFS
```

### Arweave Upload via Irys (Bundlr)

```javascript
import Irys from '@irys/sdk';

class ArweaveService {
    constructor(privateKey) {
        this.irys = new Irys({
            url: 'https://node2.irys.xyz',
            token: 'arweave',
            key: privateKey
        });
    }

    async upload(data, tags = []) {
        // Add ARC8 tags
        const allTags = [
            { name: 'App-Name', value: 'ARC8' },
            { name: 'Content-Type', value: 'application/json' },
            ...tags
        ];

        const tx = await this.irys.upload(data, { tags: allTags });
        return tx.id;
    }

    async getPrice(bytes) {
        const price = await this.irys.getPrice(bytes);
        return this.irys.utils.fromAtomic(price);
    }
}
```

---

## SUMMARY

| Innovation | Description |
|------------|-------------|
| **Dual-layer storage** | IPFS for speed, Arweave for permanence |
| **Anchor records** | Tiny Arweave record points to IPFS content |
| **Permanence tiers** | User chooses: temporary → archival |
| **Unified proof** | Single proof contains both IPFS + Arweave refs |
| **Fallback retrieval** | Try IPFS first, Arweave backup |
| **Cost optimization** | $0.0001 per permanent anchor vs $5/GB full |
| **ARC8 URI scheme** | `arc8://{cid}?ar={tx}` for unified addressing |

### Novel Claims

1. Tiered permanence system combining IPFS + Arweave
2. Anchor record format (~500 bytes) linking IPFS CID to Arweave TX
3. ARC8 URI scheme for unified content addressing
4. Cost-optimized strategy: anchor proofs, not full content
5. Fallback retrieval chain: IPFS → Arweave → redundant gateways

---

*End of specification.*
