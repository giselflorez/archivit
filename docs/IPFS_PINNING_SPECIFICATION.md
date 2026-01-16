# IPFS PINNING SPECIFICATION

## Heavy-Use Architecture

**Created:** 2026-01-16
**Status:** SPECIFICATION
**Target:** 10,000+ concurrent users, 1TB+ storage

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER DEVICE                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Local Store  │  │ IPFS Node    │  │ Pin Queue    │          │
│  │ (IndexedDB)  │  │ (js-ipfs)    │  │ (Background) │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PINNING LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Pinata       │  │ Web3.Storage │  │ Filebase     │          │
│  │ (Primary)    │  │ (Backup)     │  │ (Redundant)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      IPFS NETWORK                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Distributed Hash Table (DHT)                 │  │
│  │              Content-Addressed Storage                    │  │
│  │              Global P2P Network                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PINNING PROVIDERS

### Primary: Pinata

| Feature | Value |
|---------|-------|
| Free tier | 1 GB storage, 100 pins |
| Paid tier | $20/mo = 50 GB, unlimited pins |
| API rate limit | 180 req/min |
| Redundancy | 3x replication |
| Uptime SLA | 99.9% |

### Backup: Web3.Storage

| Feature | Value |
|---------|-------|
| Free tier | 5 GB storage |
| Paid tier | Pay per GB |
| Filecoin backing | Yes (long-term) |
| API rate limit | 30 req/min |

### Redundant: Filebase

| Feature | Value |
|---------|-------|
| Free tier | 5 GB storage |
| S3-compatible | Yes |
| Geo-redundancy | 3 regions |

---

## DATA STRUCTURE

### Content Types & Sizes

| Type | Avg Size | Pin Priority |
|------|----------|--------------|
| Provenance record (JSON) | 2-10 KB | HIGH |
| Thumbnail image | 50-200 KB | MEDIUM |
| Full-res image | 2-10 MB | LOW |
| Video preview | 10-50 MB | LOW |
| Full video | 100 MB - 2 GB | OPTIONAL |

### CID Format

```
Standard: CIDv1 (base32)
Example: bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi

Directory structure on IPFS:
/archivit/{user_seed_hash}/
  ├── provenance/
  │   ├── {record_id}.json
  │   └── ...
  ├── thumbnails/
  │   ├── {asset_id}_thumb.jpg
  │   └── ...
  └── assets/
      ├── {asset_id}_full.{ext}
      └── ...
```

---

## PINNING STRATEGY

### Tier-Based Pinning

| User Tier | Local | Pinata | Web3.Storage | Filebase |
|-----------|-------|--------|--------------|----------|
| BLOCKED | Yes | No | No | No |
| OBSERVER | Yes | No | No | No |
| PARTICIPANT | Yes | Provenance only | No | No |
| CREATOR | Yes | All | Provenance | No |
| SOVEREIGN | Yes | All | All | All |

### Pin Priority Queue

```javascript
const PIN_PRIORITY = {
    PROVENANCE_RECORD: 1,    // Highest - always pin first
    OWNERSHIP_PROOF: 2,
    THUMBNAIL: 3,
    METADATA: 4,
    FULL_IMAGE: 5,
    VIDEO_PREVIEW: 6,
    FULL_VIDEO: 7            // Lowest - optional
};
```

### Batch Pinning (Heavy Load)

```javascript
class PinQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
        this.BATCH_SIZE = 50;
        this.RATE_LIMIT_MS = 350; // ~170 req/min (under 180 limit)
    }

    async add(cid, priority, metadata) {
        this.queue.push({ cid, priority, metadata, attempts: 0 });
        this.queue.sort((a, b) => a.priority - b.priority);
        this.process();
    }

    async process() {
        if (this.processing) return;
        this.processing = true;

        while (this.queue.length > 0) {
            const batch = this.queue.splice(0, this.BATCH_SIZE);

            for (const item of batch) {
                try {
                    await this.pinToPinata(item.cid, item.metadata);
                    await this.delay(this.RATE_LIMIT_MS);
                } catch (error) {
                    if (item.attempts < 3) {
                        item.attempts++;
                        this.queue.push(item); // Re-queue with retry
                    } else {
                        this.logFailure(item);
                    }
                }
            }
        }

        this.processing = false;
    }
}
```

---

## API IMPLEMENTATION

### Pinata Integration

```javascript
class PinataService {
    constructor(apiKey, secretKey) {
        this.baseUrl = 'https://api.pinata.cloud';
        this.headers = {
            'pinata_api_key': apiKey,
            'pinata_secret_api_key': secretKey
        };
    }

    // Pin JSON data directly
    async pinJSON(data, name) {
        const response = await fetch(`${this.baseUrl}/pinning/pinJSONToIPFS`, {
            method: 'POST',
            headers: {
                ...this.headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pinataContent: data,
                pinataMetadata: { name }
            })
        });

        const result = await response.json();
        return result.IpfsHash; // CID
    }

    // Pin file from browser
    async pinFile(file, name) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('pinataMetadata', JSON.stringify({ name }));

        const response = await fetch(`${this.baseUrl}/pinning/pinFileToIPFS`, {
            method: 'POST',
            headers: this.headers,
            body: formData
        });

        const result = await response.json();
        return result.IpfsHash;
    }

    // Pin by CID (already on IPFS)
    async pinByCID(cid, name) {
        const response = await fetch(`${this.baseUrl}/pinning/pinByHash`, {
            method: 'POST',
            headers: {
                ...this.headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hashToPin: cid,
                pinataMetadata: { name }
            })
        });

        return response.json();
    }

    // Unpin
    async unpin(cid) {
        const response = await fetch(`${this.baseUrl}/pinning/unpin/${cid}`, {
            method: 'DELETE',
            headers: this.headers
        });

        return response.ok;
    }

    // List pins
    async listPins(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(
            `${this.baseUrl}/data/pinList?${params}`,
            { headers: this.headers }
        );

        return response.json();
    }
}
```

### Web3.Storage Integration

```javascript
class Web3StorageService {
    constructor(token) {
        this.baseUrl = 'https://api.web3.storage';
        this.headers = {
            'Authorization': `Bearer ${token}`
        };
    }

    async upload(file) {
        const response = await fetch(`${this.baseUrl}/upload`, {
            method: 'POST',
            headers: this.headers,
            body: file
        });

        const result = await response.json();
        return result.cid;
    }

    async uploadCAR(carFile) {
        const response = await fetch(`${this.baseUrl}/car`, {
            method: 'POST',
            headers: {
                ...this.headers,
                'Content-Type': 'application/vnd.ipld.car'
            },
            body: carFile
        });

        return response.json();
    }

    async status(cid) {
        const response = await fetch(
            `${this.baseUrl}/status/${cid}`,
            { headers: this.headers }
        );

        return response.json();
    }
}
```

---

## REDUNDANCY SYSTEM

### Multi-Provider Pinning

```javascript
class RedundantPinning {
    constructor(pinata, web3storage, filebase) {
        this.providers = { pinata, web3storage, filebase };
        this.MIN_REDUNDANCY = 2; // At least 2 providers
    }

    async pinWithRedundancy(cid, data, priority) {
        const results = {
            cid,
            pins: [],
            errors: []
        };

        // Always pin to Pinata (primary)
        try {
            await this.providers.pinata.pinByCID(cid);
            results.pins.push('pinata');
        } catch (e) {
            results.errors.push({ provider: 'pinata', error: e.message });
        }

        // High priority = pin to all providers
        if (priority <= 2) {
            try {
                await this.providers.web3storage.upload(data);
                results.pins.push('web3storage');
            } catch (e) {
                results.errors.push({ provider: 'web3storage', error: e.message });
            }

            try {
                await this.providers.filebase.upload(data);
                results.pins.push('filebase');
            } catch (e) {
                results.errors.push({ provider: 'filebase', error: e.message });
            }
        }

        // Verify minimum redundancy
        results.redundant = results.pins.length >= this.MIN_REDUNDANCY;

        return results;
    }

    async verifyPins(cid) {
        const status = {
            cid,
            providers: {}
        };

        for (const [name, provider] of Object.entries(this.providers)) {
            try {
                const pinned = await provider.isPinned(cid);
                status.providers[name] = pinned;
            } catch (e) {
                status.providers[name] = false;
            }
        }

        status.totalPinned = Object.values(status.providers).filter(Boolean).length;
        status.healthy = status.totalPinned >= this.MIN_REDUNDANCY;

        return status;
    }
}
```

---

## HEAVY LOAD HANDLING

### Rate Limiting

| Provider | Limit | Strategy |
|----------|-------|----------|
| Pinata | 180 req/min | 350ms delay between requests |
| Web3.Storage | 30 req/min | 2000ms delay, batch uploads |
| Filebase | 100 req/min | 600ms delay |

### Queue Management

```javascript
class HeavyLoadPinManager {
    constructor() {
        this.queues = {
            high: [],    // Provenance, ownership
            medium: [],  // Thumbnails, metadata
            low: []      // Full assets
        };
        this.stats = {
            pinned: 0,
            failed: 0,
            pending: 0
        };
    }

    // Process queues with priority
    async processQueues() {
        // High priority: immediate
        while (this.queues.high.length > 0) {
            await this.processItem(this.queues.high.shift());
        }

        // Medium priority: 1 per 500ms
        if (this.queues.medium.length > 0) {
            await this.processItem(this.queues.medium.shift());
            await this.delay(500);
        }

        // Low priority: 1 per 2000ms (background)
        if (this.queues.low.length > 0) {
            await this.processItem(this.queues.low.shift());
            await this.delay(2000);
        }
    }

    getStats() {
        return {
            ...this.stats,
            pending: this.queues.high.length +
                     this.queues.medium.length +
                     this.queues.low.length
        };
    }
}
```

### Concurrent User Scaling

| Users | Pins/Hour | Strategy |
|-------|-----------|----------|
| 100 | ~500 | Single queue, no throttle |
| 1,000 | ~5,000 | Priority queue, rate limit |
| 10,000 | ~50,000 | Multi-provider, batch processing |
| 100,000 | ~500,000 | Dedicated infrastructure needed |

---

## STORAGE COSTS (Estimated)

### Per User

| Tier | Monthly Storage | Monthly Cost |
|------|-----------------|--------------|
| PARTICIPANT | ~100 MB | Free |
| CREATOR | ~1 GB | ~$0.40 |
| SOVEREIGN | ~10 GB | ~$4.00 |

### Platform Total (10,000 users)

| Metric | Value |
|--------|-------|
| Total storage | ~5 TB |
| Monthly cost (Pinata) | ~$200 |
| Monthly cost (Web3.Storage) | ~$50 |
| Total monthly | ~$250 |

---

## RETRIEVAL

### Gateway URLs

```javascript
const GATEWAYS = [
    'https://gateway.pinata.cloud/ipfs/',
    'https://w3s.link/ipfs/',
    'https://ipfs.io/ipfs/',
    'https://cloudflare-ipfs.com/ipfs/',
    'https://dweb.link/ipfs/'
];

async function fetchWithFallback(cid) {
    for (const gateway of GATEWAYS) {
        try {
            const response = await fetch(`${gateway}${cid}`, {
                timeout: 10000
            });
            if (response.ok) return response;
        } catch (e) {
            continue;
        }
    }
    throw new Error('All gateways failed');
}
```

### Local Caching

```javascript
class IPFSCache {
    constructor() {
        this.cache = new Map();
        this.MAX_SIZE = 100 * 1024 * 1024; // 100 MB
        this.currentSize = 0;
    }

    async get(cid) {
        if (this.cache.has(cid)) {
            return this.cache.get(cid);
        }

        const data = await fetchWithFallback(cid);
        this.set(cid, data);
        return data;
    }

    set(cid, data) {
        const size = data.byteLength || data.length;

        // Evict if needed
        while (this.currentSize + size > this.MAX_SIZE) {
            const oldest = this.cache.keys().next().value;
            this.currentSize -= this.cache.get(oldest).byteLength;
            this.cache.delete(oldest);
        }

        this.cache.set(cid, data);
        this.currentSize += size;
    }
}
```

---

## DATABASE SCHEMA

```sql
ipfs_pins:
  - cid (primary)
  - user_wallet
  - content_type (provenance/thumbnail/asset)
  - size_bytes
  - created_at
  - pinata_status (pending/pinned/failed)
  - web3storage_status
  - filebase_status
  - last_verified

pin_queue:
  - id (auto)
  - cid
  - priority (1-7)
  - attempts
  - status (queued/processing/complete/failed)
  - created_at
  - processed_at
  - error_message
```

---

## MONITORING

### Health Checks

```javascript
async function healthCheck() {
    const status = {
        timestamp: Date.now(),
        providers: {},
        queue: {}
    };

    // Check each provider
    for (const [name, provider] of Object.entries(providers)) {
        try {
            const start = Date.now();
            await provider.ping();
            status.providers[name] = {
                healthy: true,
                latency: Date.now() - start
            };
        } catch (e) {
            status.providers[name] = {
                healthy: false,
                error: e.message
            };
        }
    }

    // Queue stats
    status.queue = pinManager.getStats();

    return status;
}
```

### Alerts

| Condition | Action |
|-----------|--------|
| Provider down > 5 min | Switch to backup |
| Queue > 10,000 items | Increase rate limit |
| Failed pins > 100/hour | Notify admin |
| Storage > 80% quota | Upgrade plan |

---

## IMPLEMENTATION PHASES

### Phase 1: Basic Pinning (Week 1)
- [ ] Pinata API integration
- [ ] Pin provenance records only
- [ ] Basic queue system

### Phase 2: Multi-Provider (Week 2)
- [ ] Web3.Storage integration
- [ ] Redundancy checks
- [ ] Fallback logic

### Phase 3: Heavy Load (Week 3)
- [ ] Priority queues
- [ ] Rate limiting
- [ ] Batch processing

### Phase 4: Monitoring (Week 4)
- [ ] Health dashboard
- [ ] Alert system
- [ ] Cost tracking

---

## ENVIRONMENT VARIABLES

```bash
# Pinata
PINATA_API_KEY=your_api_key
PINATA_SECRET_KEY=your_secret_key

# Web3.Storage
WEB3STORAGE_TOKEN=your_token

# Filebase
FILEBASE_ACCESS_KEY=your_access_key
FILEBASE_SECRET_KEY=your_secret_key
FILEBASE_BUCKET=archivit
```

---

## SUMMARY

| Component | Implementation |
|-----------|----------------|
| Primary provider | Pinata (180 req/min, 99.9% uptime) |
| Backup providers | Web3.Storage, Filebase |
| Redundancy | Minimum 2 providers for high-priority |
| Queue | Priority-based (1-7), batch processing |
| Rate limiting | 350ms delay Pinata, 2000ms Web3.Storage |
| Cost (10K users) | ~$250/month |
| Scaling | Up to 100K users with current architecture |

---

*End of specification.*
