# CLIENT-SIDE SEMANTIC SEARCH SPECIFICATION
## ARC-8 Offline Vector Search Architecture

> **Status**: Technical Specification (ULTRATHINK Analysis)
> **Version**: 1.0.0
> **Date**: 2026-01-13
> **Author**: Claude Agent (Opus 4.5)

---

## EXECUTIVE SUMMARY

This specification details the migration of ARC-8's semantic search from server-side txtai to a fully client-side implementation using browser-native technologies. The goal is to enable vector/semantic search without requiring `python visual_browser.py` while maintaining search quality comparable to the current txtai implementation.

### Current State
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Backend**: txtai with FAISS index
- **Storage**: `db/txtai_index/` on filesystem
- **Query Processing**: Server-side Python

### Target State
- **Model**: `Xenova/all-MiniLM-L6-v2` (ONNX, same 384 dimensions)
- **Backend**: EdgeVec (Rust/WASM) or Orama (JS)
- **Storage**: IndexedDB with persistence
- **Query Processing**: Client-side Web Worker

### Key Constraints Met
- Fully offline operation
- No cloud API calls for embeddings
- Index stored in browser (IndexedDB)
- Fast enough for real-time search (<100ms)
- Handles 1000+ documents
- Maintains semantic search quality

---

## PART 1: TECHNOLOGY SELECTION

### 1.1 Client-Side Embedding Models

| Model | Size | Dimensions | Speed (CPU) | Quality | Browser Support |
|-------|------|------------|-------------|---------|-----------------|
| **all-MiniLM-L6-v2** | 22MB | 384 | 5-14k sent/sec | 84-85% STS | Excellent |
| all-mpnet-base-v2 | 420MB | 768 | 1-3k sent/sec | 87-88% STS | Good |
| gte-small | 30MB | 384 | 4-8k sent/sec | 86% STS | Good |
| bge-small-en-v1.5 | 33MB | 384 | 4-8k sent/sec | 85% STS | Good |

**RECOMMENDATION: `Xenova/all-MiniLM-L6-v2`**

Rationale:
1. **Direct parity** with current txtai model (same dimensions, same embeddings)
2. **Smallest size** (22MB) - fast initial download
3. **Fastest inference** - 5-14k sentences/second on CPU
4. **ONNX optimized** - Transformers.js compatible
5. **Quantization available** - q4/q8 variants reduce to ~6MB

### 1.2 Client-Side Vector Search Libraries

| Library | Type | Size | Speed (100k vectors) | Features | Persistence |
|---------|------|------|---------------------|----------|-------------|
| **EdgeVec** | WASM/Rust | 148KB | 0.23ms | HNSW, quantization, metadata | IndexedDB |
| Orama | Pure JS | <2KB | ~88ms (10k docs) | Full-text + vector, hybrid | Memory/export |
| Voy | WASM/Rust | ~100KB | 5.5ms | k-d tree | Memory only |
| client-vector-search | JS | ~50KB | ~10ms (1k) | Simple cosine | localStorage |
| Vector-Storage | JS | ~15KB | ~20ms (1k) | localStorage | localStorage |

**RECOMMENDATION: EdgeVec (Primary) + Orama (Fallback)**

Rationale for EdgeVec:
1. **24x faster than Voy** - sub-millisecond search at 100k vectors
2. **HNSW indexing** - O(log n) approximate nearest neighbor
3. **Built-in IndexedDB persistence** - survives page refreshes
4. **SQ8 quantization** - 3.6x memory reduction
5. **SIMD acceleration** - 2x+ faster on modern browsers
6. **Metadata filtering** - category/tag filters at search time

Rationale for Orama fallback:
1. **Hybrid search** - combines full-text and vector for best results
2. **Tiny size** - <2KB, good for low-powered devices
3. **Pure JavaScript** - no WASM dependency
4. **Built-in embeddings plugin** - can generate embeddings directly

### 1.3 Architecture Decision Matrix

| Requirement | EdgeVec | Orama | Voy | client-vector-search |
|-------------|---------|-------|-----|---------------------|
| Offline | Yes | Yes | Yes | Yes |
| No API calls | Yes | Yes* | Yes | Yes* |
| IndexedDB storage | Yes | Export/import | No | localStorage |
| 1000+ docs | Yes | Yes | Yes | Limited |
| <100ms search | Yes (0.23ms) | Yes (~88ms) | Yes (5.5ms) | Marginal |
| Semantic quality | Depends on embeddings | Depends on embeddings | Depends on embeddings | Uses gte-small |
| Memory efficient | Yes (SQ8) | Moderate | Moderate | Low |

*Can use built-in embedding generation

---

## PART 2: RECOMMENDED ARCHITECTURE

### 2.1 High-Level Architecture

```
                     ARC-8 CLIENT-SIDE SEARCH

+------------------------------------------------------------------+
|                         MAIN THREAD                               |
|  +------------------+  +------------------+  +------------------+ |
|  |   Search UI      |  |   Document       |  |   Results        | |
|  |   Component      |  |   Viewer         |  |   Display        | |
|  +--------+---------+  +------------------+  +--------+---------+ |
|           |                                           ^           |
|           | postMessage                               |           |
|           v                                           |           |
+------------------------------------------------------------------+
            |                                           ^
            v                                           |
+------------------------------------------------------------------+
|                      SEARCH WEB WORKER                            |
|  +------------------+  +------------------+  +------------------+ |
|  |  Transformers.js |  |    EdgeVec       |  |   Query          | |
|  |  Embedding       |  |    Vector        |  |   Processor      | |
|  |  Pipeline        |  |    Index         |  |                  | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                     |                     ^           |
|           |   embed(text)       |   search(vec,k)     |           |
|           v                     v                     |           |
|  +------------------+  +------------------+           |           |
|  |   ONNX Runtime   |  |   WASM Runtime   |           |           |
|  |   (WebGPU/WASM)  |  |   (SIMD)         |           |           |
|  +------------------+  +------------------+           |           |
+------------------------------------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------+
|                         IndexedDB                                 |
|  +------------------+  +------------------+  +------------------+ |
|  |   documents      |  |   embeddings     |  |   search_meta    | |
|  |   (content)      |  |   (vectors)      |  |   (stats)        | |
|  +------------------+  +------------------+  +------------------+ |
+------------------------------------------------------------------+
```

### 2.2 Component Specifications

#### 2.2.1 Embedding Pipeline (Transformers.js)

```javascript
// scripts/interface/static/js/search/embedding_worker.js

import { pipeline, env } from '@huggingface/transformers';

// Configure for browser
env.allowLocalModels = false;
env.useBrowserCache = true;

class EmbeddingPipeline {
    static instance = null;
    static MODEL_ID = 'Xenova/all-MiniLM-L6-v2';

    static async getInstance(progressCallback = null) {
        if (this.instance === null) {
            // Detect best execution backend
            const device = await this.detectDevice();

            this.instance = await pipeline(
                'feature-extraction',
                this.MODEL_ID,
                {
                    device: device,
                    dtype: 'q8',  // 8-bit quantization for smaller size
                    progress_callback: progressCallback
                }
            );
        }
        return this.instance;
    }

    static async detectDevice() {
        // Try WebGPU first (40-75x speedup on supported hardware)
        if (typeof navigator !== 'undefined' && 'gpu' in navigator) {
            try {
                const adapter = await navigator.gpu.requestAdapter();
                if (adapter) {
                    console.log('[Search] Using WebGPU acceleration');
                    return 'webgpu';
                }
            } catch (e) {
                console.log('[Search] WebGPU not available, falling back to WASM');
            }
        }
        return 'wasm';
    }

    static async embed(texts) {
        const extractor = await this.getInstance();

        // Handle single text or array
        const input = Array.isArray(texts) ? texts : [texts];

        // Generate embeddings with mean pooling and normalization
        const output = await extractor(input, {
            pooling: 'mean',
            normalize: true
        });

        // Convert to array of Float32Arrays
        return output.tolist();
    }

    static async embedBatch(texts, batchSize = 32, progressCallback = null) {
        const results = [];
        const total = texts.length;

        for (let i = 0; i < total; i += batchSize) {
            const batch = texts.slice(i, i + batchSize);
            const embeddings = await this.embed(batch);
            results.push(...embeddings);

            if (progressCallback) {
                progressCallback({
                    current: Math.min(i + batchSize, total),
                    total: total,
                    percent: Math.round(((i + batchSize) / total) * 100)
                });
            }
        }

        return results;
    }
}

export { EmbeddingPipeline };
```

#### 2.2.2 Vector Index (EdgeVec)

```javascript
// scripts/interface/static/js/search/vector_index.js

import init, { EdgeVec, EdgeVecConfig } from 'edgevec';

class VectorIndex {
    static instance = null;
    static INDEX_NAME = 'arc8-search-index';
    static DIMENSIONS = 384;  // Must match MiniLM-L6-v2

    static async getInstance() {
        if (this.instance === null) {
            await init();  // Initialize WASM

            // Try to load existing index from IndexedDB
            try {
                this.instance = await EdgeVec.load(this.INDEX_NAME);
                console.log('[Search] Loaded existing index from IndexedDB');
            } catch (e) {
                // Create new index
                const config = new EdgeVecConfig(this.DIMENSIONS);
                config.quantized = true;  // Enable SQ8 for 4x memory reduction
                config.distance = 'cosine';

                this.instance = new EdgeVec(config);
                console.log('[Search] Created new vector index');
            }
        }
        return this.instance;
    }

    static async insert(id, embedding, metadata = {}) {
        const index = await this.getInstance();

        // Convert to Float32Array if needed
        const vector = embedding instanceof Float32Array
            ? embedding
            : new Float32Array(embedding);

        // Insert with metadata
        index.insertWithMetadata(vector, {
            doc_id: id,
            ...metadata
        });
    }

    static async insertBatch(documents, embeddings, progressCallback = null) {
        const index = await this.getInstance();
        const total = documents.length;

        for (let i = 0; i < total; i++) {
            const vector = new Float32Array(embeddings[i]);
            index.insertWithMetadata(vector, {
                doc_id: documents[i].id,
                source: documents[i].source || 'unknown',
                type: documents[i].type || 'document',
                title: documents[i].title || '',
                tags: JSON.stringify(documents[i].tags || [])
            });

            if (progressCallback && i % 100 === 0) {
                progressCallback({
                    current: i,
                    total: total,
                    percent: Math.round((i / total) * 100)
                });
            }
        }

        // Persist to IndexedDB
        await index.save(this.INDEX_NAME);
        console.log(`[Search] Indexed ${total} documents`);
    }

    static async search(queryEmbedding, k = 20, filter = null) {
        const index = await this.getInstance();

        const vector = queryEmbedding instanceof Float32Array
            ? queryEmbedding
            : new Float32Array(queryEmbedding);

        let results;
        if (filter) {
            // Search with metadata filter
            // Filter syntax: 'source = "instagram" AND type = "post"'
            results = index.searchWithFilter(vector, filter, k);
        } else {
            results = index.search(vector, k);
        }

        return results.map(r => ({
            id: r.metadata.doc_id,
            score: 1 - r.score,  // Convert distance to similarity
            metadata: r.metadata
        }));
    }

    static async remove(id) {
        const index = await this.getInstance();
        // EdgeVec uses soft delete
        index.delete(id);
        await index.save(this.INDEX_NAME);
    }

    static async clear() {
        const index = await this.getInstance();
        // Create fresh index
        const config = new EdgeVecConfig(this.DIMENSIONS);
        config.quantized = true;
        this.instance = new EdgeVec(config);
        await this.instance.save(this.INDEX_NAME);
    }

    static async getStats() {
        const index = await this.getInstance();
        return {
            count: index.len(),
            dimensions: this.DIMENSIONS,
            quantized: true,
            indexName: this.INDEX_NAME
        };
    }

    static async persist() {
        const index = await this.getInstance();
        await index.save(this.INDEX_NAME);
    }
}

export { VectorIndex };
```

#### 2.2.3 Search Service (Unified API)

```javascript
// scripts/interface/static/js/search/search_service.js

import { EmbeddingPipeline } from './embedding_worker.js';
import { VectorIndex } from './vector_index.js';

class SearchService {
    static isInitialized = false;
    static initPromise = null;

    /**
     * Initialize the search system
     * Downloads model and prepares index
     */
    static async initialize(progressCallback = null) {
        if (this.isInitialized) return;
        if (this.initPromise) return this.initPromise;

        this.initPromise = (async () => {
            console.log('[Search] Initializing client-side search...');

            // Initialize embedding pipeline (downloads model if needed)
            await EmbeddingPipeline.getInstance((progress) => {
                if (progressCallback) {
                    progressCallback({
                        stage: 'model',
                        ...progress
                    });
                }
            });

            // Initialize vector index
            await VectorIndex.getInstance();

            this.isInitialized = true;
            console.log('[Search] Client-side search ready');
        })();

        return this.initPromise;
    }

    /**
     * Index a single document
     */
    static async indexDocument(document) {
        await this.initialize();

        // Generate embedding for searchable content
        const searchableText = this.buildSearchableText(document);
        const [embedding] = await EmbeddingPipeline.embed(searchableText);

        // Store in vector index
        await VectorIndex.insert(document.id, embedding, {
            source: document.source,
            type: document.cognitive_type || document.type,
            title: document.title,
            tags: document.tags
        });
    }

    /**
     * Index multiple documents (bulk operation)
     */
    static async indexDocuments(documents, progressCallback = null) {
        await this.initialize();

        console.log(`[Search] Indexing ${documents.length} documents...`);

        // Build searchable text for all documents
        const texts = documents.map(doc => this.buildSearchableText(doc));

        // Generate embeddings in batches
        const embeddings = await EmbeddingPipeline.embedBatch(texts, 32, (progress) => {
            if (progressCallback) {
                progressCallback({
                    stage: 'embedding',
                    ...progress
                });
            }
        });

        // Insert into vector index
        await VectorIndex.insertBatch(documents, embeddings, (progress) => {
            if (progressCallback) {
                progressCallback({
                    stage: 'indexing',
                    ...progress
                });
            }
        });

        console.log(`[Search] Indexing complete`);
    }

    /**
     * Search for documents
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Array} Search results with scores
     */
    static async search(query, options = {}) {
        await this.initialize();

        const {
            limit = 20,
            minScore = 0.3,
            filter = null,
            includeMetadata = true
        } = options;

        // Generate query embedding
        const [queryEmbedding] = await EmbeddingPipeline.embed(query);

        // Search vector index
        const results = await VectorIndex.search(queryEmbedding, limit * 2, filter);

        // Filter by minimum score and limit
        const filtered = results
            .filter(r => r.score >= minScore)
            .slice(0, limit);

        // Optionally fetch full document data
        if (includeMetadata) {
            return this.enrichResults(filtered);
        }

        return filtered;
    }

    /**
     * Hybrid search: combines semantic and keyword matching
     */
    static async hybridSearch(query, options = {}) {
        const {
            limit = 20,
            semanticWeight = 0.7,
            keywordWeight = 0.3
        } = options;

        // Semantic search
        const semanticResults = await this.search(query, {
            limit: limit * 2,
            minScore: 0.2
        });

        // Keyword search (simple but effective)
        const keywordResults = await this.keywordSearch(query, limit * 2);

        // Merge and re-rank
        const combined = this.mergeResults(
            semanticResults,
            keywordResults,
            semanticWeight,
            keywordWeight
        );

        return combined.slice(0, limit);
    }

    /**
     * Simple keyword search fallback
     */
    static async keywordSearch(query, limit = 20) {
        const db = await this.getDatabase();
        const documents = await db.getAll('documents');

        const queryTerms = query.toLowerCase().split(/\s+/);
        const results = [];

        for (const doc of documents) {
            const content = this.buildSearchableText(doc).toLowerCase();
            let score = 0;

            for (const term of queryTerms) {
                if (content.includes(term)) {
                    score += 1;
                }
            }

            if (score > 0) {
                results.push({
                    id: doc.id,
                    score: score / queryTerms.length,
                    metadata: {
                        doc_id: doc.id,
                        title: doc.title,
                        source: doc.source
                    }
                });
            }
        }

        return results
            .sort((a, b) => b.score - a.score)
            .slice(0, limit);
    }

    /**
     * Build searchable text from document
     */
    static buildSearchableText(document) {
        const parts = [
            document.title || '',
            document.content || document.body || '',
            (document.tags || []).join(' '),
            document.source || '',
            document.description || ''
        ];

        return parts
            .filter(Boolean)
            .join('\n\n')
            .substring(0, 8192);  // MiniLM max is ~256 tokens, but we truncate
    }

    /**
     * Enrich results with full document data
     */
    static async enrichResults(results) {
        const db = await this.getDatabase();

        const enriched = await Promise.all(
            results.map(async (result) => {
                const doc = await db.get('documents', result.id);
                if (doc) {
                    return {
                        ...result,
                        document: doc
                    };
                }
                return result;
            })
        );

        return enriched.filter(r => r.document);
    }

    /**
     * Merge semantic and keyword results
     */
    static mergeResults(semantic, keyword, semWeight, keyWeight) {
        const scores = new Map();

        for (const r of semantic) {
            scores.set(r.id, {
                ...r,
                combinedScore: r.score * semWeight
            });
        }

        for (const r of keyword) {
            const existing = scores.get(r.id);
            if (existing) {
                existing.combinedScore += r.score * keyWeight;
            } else {
                scores.set(r.id, {
                    ...r,
                    combinedScore: r.score * keyWeight
                });
            }
        }

        return Array.from(scores.values())
            .sort((a, b) => b.combinedScore - a.combinedScore);
    }

    /**
     * Get database instance
     */
    static async getDatabase() {
        // Use the ARC8Database from client-side architecture
        if (typeof window !== 'undefined' && window.ARC8Database) {
            return window.ARC8Database;
        }
        // Import dynamically if needed
        const { ARC8Database } = await import('../data/arc8_database.js');
        return ARC8Database;
    }

    /**
     * Get index statistics
     */
    static async getStats() {
        await this.initialize();
        return VectorIndex.getStats();
    }

    /**
     * Rebuild entire index from documents
     */
    static async rebuildIndex(progressCallback = null) {
        await this.initialize();

        // Clear existing index
        await VectorIndex.clear();

        // Load all documents
        const db = await this.getDatabase();
        const documents = await db.getAll('documents');

        if (documents.length === 0) {
            console.log('[Search] No documents to index');
            return;
        }

        // Re-index all documents
        await this.indexDocuments(documents, progressCallback);
    }
}

export { SearchService };
```

---

## PART 3: IndexedDB SCHEMA

### 3.1 Schema Definition

```javascript
// Extended from arc8_database.js for search

const SEARCH_STORES = {
    // Vector embeddings store (separate for performance)
    embeddings: {
        keyPath: 'doc_id',
        indexes: [
            { name: 'by_source', keyPath: 'source' },
            { name: 'by_indexed_at', keyPath: 'indexed_at' }
        ]
    },

    // Search metadata and statistics
    search_meta: {
        keyPath: 'key',
        indexes: []
    },

    // Query cache (optional, for frequent queries)
    query_cache: {
        keyPath: 'query_hash',
        indexes: [
            { name: 'by_timestamp', keyPath: 'timestamp' }
        ]
    }
};

// Embedding record structure
const EmbeddingRecord = {
    doc_id: 'string',           // Primary key, matches document ID
    embedding: 'Float32Array',  // 384-dimensional vector
    source: 'string',           // Document source for filtering
    type: 'string',             // Cognitive type
    indexed_at: 'number',       // Timestamp
    version: 'number'           // For reindexing detection
};

// Search metadata structure
const SearchMeta = {
    key: 'string',              // e.g., 'index_stats', 'last_rebuild'
    value: 'any',               // Flexible value
    updated_at: 'number'        // Timestamp
};
```

### 3.2 Storage Size Estimates

For 1000 documents with 384-dimensional embeddings:

| Component | Size per doc | Total (1000 docs) |
|-----------|--------------|-------------------|
| Embedding (f32) | 1.5 KB | 1.5 MB |
| Embedding (SQ8) | 384 B | 375 KB |
| Metadata | ~200 B | 200 KB |
| Index overhead | ~100 B | 100 KB |
| **Total (f32)** | | **~2 MB** |
| **Total (SQ8)** | | **~700 KB** |

**With EdgeVec SQ8 quantization, 10,000 documents = ~7MB**

IndexedDB limits:
- Chrome: 60GB per origin (plenty of headroom)
- Firefox: 10GB per origin
- Safari: 1GB per origin (still fits 1M+ documents)

---

## PART 4: EMBEDDING GENERATION STRATEGY

### 4.1 Strategies Comparison

| Strategy | Pros | Cons | Use Case |
|----------|------|------|----------|
| **On-demand** | No upfront cost, always fresh | Slow first search | Small (<100 docs) |
| **Background** | Non-blocking UX | Complex state management | Medium (100-1000) |
| **Batch import** | Efficient, one-time cost | Blocking during import | Large (>1000 docs) |
| **Progressive** | Best UX, starts fast | Complex implementation | All sizes |

### 4.2 Recommended: Progressive Indexing

```javascript
// scripts/interface/static/js/search/progressive_indexer.js

class ProgressiveIndexer {
    static BATCH_SIZE = 50;
    static IDLE_DELAY = 100;  // ms between batches when idle

    constructor(searchService) {
        this.searchService = searchService;
        this.queue = [];
        this.isRunning = false;
        this.priority = new Set();  // High-priority document IDs
    }

    /**
     * Queue documents for indexing
     */
    enqueue(documents) {
        for (const doc of documents) {
            if (!this.queue.find(d => d.id === doc.id)) {
                this.queue.push(doc);
            }
        }
        this.startIfIdle();
    }

    /**
     * Prioritize specific documents (e.g., currently visible)
     */
    prioritize(docIds) {
        for (const id of docIds) {
            this.priority.add(id);
        }
        // Re-sort queue to put priority items first
        this.queue.sort((a, b) => {
            const aPriority = this.priority.has(a.id) ? 1 : 0;
            const bPriority = this.priority.has(b.id) ? 1 : 0;
            return bPriority - aPriority;
        });
    }

    /**
     * Start processing if not already running
     */
    startIfIdle() {
        if (!this.isRunning && this.queue.length > 0) {
            this.run();
        }
    }

    /**
     * Process queue in batches during idle time
     */
    async run() {
        this.isRunning = true;

        while (this.queue.length > 0) {
            // Take a batch
            const batch = this.queue.splice(0, this.BATCH_SIZE);

            try {
                await this.searchService.indexDocuments(batch);
                console.log(`[Indexer] Indexed ${batch.length} documents, ${this.queue.length} remaining`);
            } catch (error) {
                console.error('[Indexer] Batch failed:', error);
                // Re-queue failed batch at end
                this.queue.push(...batch);
            }

            // Yield to main thread
            await this.waitForIdle();
        }

        this.isRunning = false;
    }

    /**
     * Wait for browser idle time
     */
    waitForIdle() {
        return new Promise(resolve => {
            if ('requestIdleCallback' in window) {
                requestIdleCallback(() => resolve(), { timeout: 1000 });
            } else {
                setTimeout(resolve, this.IDLE_DELAY);
            }
        });
    }

    /**
     * Get indexing progress
     */
    getProgress() {
        return {
            queued: this.queue.length,
            isRunning: this.isRunning
        };
    }
}

export { ProgressiveIndexer };
```

### 4.3 Web Worker Integration

To avoid blocking the main thread:

```javascript
// scripts/interface/static/js/search/search_worker.js

import { SearchService } from './search_service.js';

// Handle messages from main thread
self.onmessage = async (event) => {
    const { type, payload, id } = event.data;

    try {
        let result;

        switch (type) {
            case 'initialize':
                await SearchService.initialize((progress) => {
                    self.postMessage({ type: 'progress', id, progress });
                });
                result = { success: true };
                break;

            case 'search':
                result = await SearchService.search(payload.query, payload.options);
                break;

            case 'hybridSearch':
                result = await SearchService.hybridSearch(payload.query, payload.options);
                break;

            case 'indexDocuments':
                await SearchService.indexDocuments(payload.documents, (progress) => {
                    self.postMessage({ type: 'progress', id, progress });
                });
                result = { success: true };
                break;

            case 'rebuildIndex':
                await SearchService.rebuildIndex((progress) => {
                    self.postMessage({ type: 'progress', id, progress });
                });
                result = { success: true };
                break;

            case 'getStats':
                result = await SearchService.getStats();
                break;

            default:
                throw new Error(`Unknown message type: ${type}`);
        }

        self.postMessage({ type: 'result', id, result });

    } catch (error) {
        self.postMessage({
            type: 'error',
            id,
            error: error.message
        });
    }
};

// Worker initialization
SearchService.initialize().catch(console.error);
```

```javascript
// scripts/interface/static/js/search/search_client.js

class SearchClient {
    constructor() {
        this.worker = new Worker(
            new URL('./search_worker.js', import.meta.url),
            { type: 'module' }
        );
        this.pending = new Map();
        this.messageId = 0;

        this.worker.onmessage = (event) => {
            const { type, id, result, error, progress } = event.data;

            if (type === 'progress') {
                const handler = this.pending.get(id);
                if (handler?.onProgress) {
                    handler.onProgress(progress);
                }
                return;
            }

            const handler = this.pending.get(id);
            if (handler) {
                this.pending.delete(id);
                if (type === 'error') {
                    handler.reject(new Error(error));
                } else {
                    handler.resolve(result);
                }
            }
        };
    }

    send(type, payload = {}, onProgress = null) {
        const id = this.messageId++;

        return new Promise((resolve, reject) => {
            this.pending.set(id, { resolve, reject, onProgress });
            this.worker.postMessage({ type, payload, id });
        });
    }

    async initialize(onProgress) {
        return this.send('initialize', {}, onProgress);
    }

    async search(query, options = {}) {
        return this.send('search', { query, options });
    }

    async hybridSearch(query, options = {}) {
        return this.send('hybridSearch', { query, options });
    }

    async indexDocuments(documents, onProgress) {
        return this.send('indexDocuments', { documents }, onProgress);
    }

    async rebuildIndex(onProgress) {
        return this.send('rebuildIndex', {}, onProgress);
    }

    async getStats() {
        return this.send('getStats');
    }
}

// Singleton instance
const searchClient = new SearchClient();
export { searchClient, SearchClient };
```

---

## PART 5: SEARCH API DESIGN

### 5.1 API Compatibility with Flask `/search`

The client-side API mirrors the current Flask endpoint:

```javascript
// Current Flask endpoint (for reference)
// GET /search?q=<query>&limit=50

// Client-side equivalent
async function search(query, limit = 50) {
    const results = await searchClient.search(query, {
        limit,
        minScore: 0.3,
        includeMetadata: true
    });

    return {
        query,
        results: results.map(r => ({
            id: r.id,
            score: r.score,
            source: r.document?.source || r.metadata?.source,
            type: r.document?.type || r.metadata?.type,
            title: r.document?.title || r.metadata?.title,
            preview: r.document?.content?.substring(0, 300) || '',
            date: r.document?.created_at,
            tags: r.document?.tags || [],
            images: r.document?.images || [],
            media_files: r.document?.media_files || [],
            filepath: r.document?.file_path,
            has_visual: (r.document?.images?.length > 0) ||
                       (r.document?.media_files?.length > 0)
        }))
    };
}
```

### 5.2 Route Handler

```javascript
// scripts/interface/static/js/handlers/search_handler.js

import { searchClient } from '../search/search_client.js';

handlers.search = async (params) => {
    const query = new URLSearchParams(window.location.search).get('q') || '';

    // Show loading state
    const container = document.getElementById('app');
    container.innerHTML = await loadTemplate('search.html', {
        query,
        loading: true,
        results: []
    });

    if (query) {
        try {
            // Perform search
            const response = await searchClient.hybridSearch(query, {
                limit: 50,
                semanticWeight: 0.7,
                keywordWeight: 0.3
            });

            // Update UI with results
            container.innerHTML = await loadTemplate('search.html', {
                query,
                loading: false,
                results: response
            });

            // Initialize result interactions
            initializeSearchResults();

        } catch (error) {
            console.error('[Search] Error:', error);
            container.innerHTML = await loadTemplate('search.html', {
                query,
                loading: false,
                error: error.message,
                results: []
            });
        }
    }
};
```

---

## PART 6: MIGRATION PATH FROM TXTAI

### 6.1 Migration Overview

```
Phase 1: Export (Server-side)
    txtai index + documents -> JSON export

Phase 2: Import (Client-side)
    JSON import -> IndexedDB documents
    Re-generate embeddings -> EdgeVec index

Phase 3: Validation
    Compare search results
    Verify quality metrics

Phase 4: Cutover
    Disable server search
    Enable client search
```

### 6.2 Export Endpoint (Server)

```python
# Add to visual_browser.py

@app.route('/api/export/search-migration')
def export_search_migration():
    """
    Export data for client-side search migration
    """
    from pathlib import Path
    import json

    export = {
        'version': '1.0.0',
        'model': 'all-MiniLM-L6-v2',
        'dimensions': 384,
        'exported_at': datetime.now().isoformat(),
        'documents': []
    }

    # Load all documents from knowledge base
    kb_path = Path('knowledge_base/processed')
    for md_file in kb_path.rglob('*.md'):
        try:
            frontmatter, body = parse_markdown_file(md_file)

            export['documents'].append({
                'id': frontmatter.get('id'),
                'title': get_title_from_markdown(body),
                'content': body,
                'source': frontmatter.get('source', 'unknown'),
                'type': frontmatter.get('type', 'document'),
                'cognitive_type': frontmatter.get('cognitive_type'),
                'tags': frontmatter.get('tags', []),
                'created_at': frontmatter.get('created_at'),
                'file_path': str(md_file.relative_to(kb_path))
            })
        except Exception as e:
            print(f"Error exporting {md_file}: {e}")
            continue

    # Include test queries for validation
    export['test_queries'] = [
        'digital art blockchain',
        'photography techniques',
        'creative process',
        'NFT marketplace',
        'artistic vision'
    ]

    return jsonify(export)
```

### 6.3 Import Process (Client)

```javascript
// scripts/interface/static/js/migration/search_migration.js

import { searchClient } from '../search/search_client.js';

class SearchMigration {

    async migrate(progressCallback = null) {
        // Phase 1: Fetch export from server
        if (progressCallback) progressCallback({ phase: 'fetch', percent: 0 });

        const response = await fetch('/api/export/search-migration');
        const exportData = await response.json();

        if (progressCallback) progressCallback({ phase: 'fetch', percent: 100 });

        // Phase 2: Store documents in IndexedDB
        if (progressCallback) progressCallback({ phase: 'store', percent: 0 });

        const db = await this.getDatabase();
        const documents = exportData.documents;

        for (let i = 0; i < documents.length; i++) {
            await db.put('documents', documents[i]);

            if (progressCallback && i % 50 === 0) {
                progressCallback({
                    phase: 'store',
                    percent: Math.round((i / documents.length) * 100)
                });
            }
        }

        // Phase 3: Generate embeddings and build index
        if (progressCallback) progressCallback({ phase: 'index', percent: 0 });

        await searchClient.indexDocuments(documents, (progress) => {
            if (progressCallback) {
                progressCallback({
                    phase: 'index',
                    percent: progress.percent
                });
            }
        });

        // Phase 4: Validate
        if (progressCallback) progressCallback({ phase: 'validate', percent: 0 });

        const validation = await this.validateMigration(exportData.test_queries);

        if (progressCallback) progressCallback({
            phase: 'complete',
            percent: 100,
            validation
        });

        return validation;
    }

    async validateMigration(testQueries) {
        const results = {
            passed: 0,
            failed: 0,
            details: []
        };

        for (const query of testQueries) {
            try {
                const searchResults = await searchClient.search(query, { limit: 5 });

                if (searchResults.length > 0 && searchResults[0].score > 0.3) {
                    results.passed++;
                    results.details.push({
                        query,
                        status: 'passed',
                        topScore: searchResults[0].score,
                        resultCount: searchResults.length
                    });
                } else {
                    results.failed++;
                    results.details.push({
                        query,
                        status: 'failed',
                        reason: 'No high-confidence results'
                    });
                }
            } catch (error) {
                results.failed++;
                results.details.push({
                    query,
                    status: 'error',
                    reason: error.message
                });
            }
        }

        return results;
    }

    async getDatabase() {
        if (typeof window !== 'undefined' && window.ARC8Database) {
            return window.ARC8Database;
        }
        const { ARC8Database } = await import('../data/arc8_database.js');
        await ARC8Database.init();
        return ARC8Database;
    }
}

export { SearchMigration };
```

---

## PART 7: PERFORMANCE BENCHMARKS

### 7.1 Target Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Model download | <10s (first load) | <30s |
| Model load (cached) | <2s | <5s |
| Single embedding | <50ms | <100ms |
| Batch embedding (32) | <500ms | <1s |
| Search (1k docs) | <10ms | <50ms |
| Search (10k docs) | <50ms | <100ms |
| Index rebuild (1k) | <30s | <60s |

### 7.2 Benchmark Script

```javascript
// scripts/interface/static/js/search/search_benchmark.js

class SearchBenchmark {

    async runAll() {
        console.log('=== Search Performance Benchmark ===\n');

        const results = {};

        // 1. Model loading
        results.modelLoad = await this.benchmarkModelLoad();

        // 2. Single embedding
        results.singleEmbed = await this.benchmarkSingleEmbed();

        // 3. Batch embedding
        results.batchEmbed = await this.benchmarkBatchEmbed(32);

        // 4. Search latency
        results.searchLatency = await this.benchmarkSearch();

        // 5. Index operations
        results.indexOps = await this.benchmarkIndexOps();

        console.log('\n=== Results Summary ===');
        console.table(results);

        return results;
    }

    async benchmarkModelLoad() {
        const start = performance.now();
        await searchClient.initialize();
        const elapsed = performance.now() - start;

        console.log(`Model load: ${elapsed.toFixed(2)}ms`);
        return { elapsed, status: elapsed < 5000 ? 'PASS' : 'WARN' };
    }

    async benchmarkSingleEmbed() {
        const text = 'This is a test sentence for embedding generation.';

        const start = performance.now();
        await searchClient.search(text, { limit: 1 });
        const elapsed = performance.now() - start;

        console.log(`Single query: ${elapsed.toFixed(2)}ms`);
        return { elapsed, status: elapsed < 100 ? 'PASS' : 'WARN' };
    }

    async benchmarkBatchEmbed(batchSize) {
        const texts = Array(batchSize).fill('Test sentence for batch embedding.');

        const start = performance.now();
        // Simulate batch by doing sequential searches
        for (const text of texts) {
            await searchClient.search(text, { limit: 1 });
        }
        const elapsed = performance.now() - start;
        const perItem = elapsed / batchSize;

        console.log(`Batch (${batchSize}): ${elapsed.toFixed(2)}ms (${perItem.toFixed(2)}ms/item)`);
        return { elapsed, perItem, status: perItem < 50 ? 'PASS' : 'WARN' };
    }

    async benchmarkSearch() {
        const queries = [
            'digital art',
            'blockchain technology',
            'creative process inspiration',
            'photography techniques lighting',
            'NFT marketplace collectors'
        ];

        const times = [];
        for (const query of queries) {
            const start = performance.now();
            await searchClient.search(query, { limit: 20 });
            times.push(performance.now() - start);
        }

        const avg = times.reduce((a, b) => a + b, 0) / times.length;
        const max = Math.max(...times);

        console.log(`Search avg: ${avg.toFixed(2)}ms, max: ${max.toFixed(2)}ms`);
        return { avg, max, status: avg < 100 ? 'PASS' : 'WARN' };
    }

    async benchmarkIndexOps() {
        const stats = await searchClient.getStats();
        console.log(`Index stats:`, stats);
        return stats;
    }
}

export { SearchBenchmark };
```

---

## PART 8: FALLBACK STRATEGY

### 8.1 Device Capability Detection

```javascript
// scripts/interface/static/js/search/capability_detector.js

class CapabilityDetector {

    static async detect() {
        const capabilities = {
            indexedDB: 'indexedDB' in window,
            webWorker: 'Worker' in window,
            webAssembly: 'WebAssembly' in window,
            webGPU: await this.checkWebGPU(),
            simd: await this.checkSIMD(),
            memory: await this.checkMemory(),
            storage: await this.checkStorage()
        };

        // Determine tier
        if (capabilities.webGPU && capabilities.simd && capabilities.memory > 4) {
            capabilities.tier = 'HIGH';
            capabilities.strategy = 'full';
        } else if (capabilities.webAssembly && capabilities.memory > 2) {
            capabilities.tier = 'MEDIUM';
            capabilities.strategy = 'full';
        } else if (capabilities.indexedDB) {
            capabilities.tier = 'LOW';
            capabilities.strategy = 'keyword-only';
        } else {
            capabilities.tier = 'UNSUPPORTED';
            capabilities.strategy = 'server-fallback';
        }

        return capabilities;
    }

    static async checkWebGPU() {
        if (!('gpu' in navigator)) return false;
        try {
            const adapter = await navigator.gpu.requestAdapter();
            return adapter !== null;
        } catch {
            return false;
        }
    }

    static async checkSIMD() {
        try {
            const code = new Uint8Array([
                0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
                0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7b, 0x03,
                0x02, 0x01, 0x00, 0x07, 0x08, 0x01, 0x04, 0x74,
                0x65, 0x73, 0x74, 0x00, 0x00, 0x0a, 0x0a, 0x01,
                0x08, 0x00, 0xfd, 0x0c, 0x00, 0x00, 0x00, 0x00,
                0x0b
            ]);
            await WebAssembly.instantiate(code);
            return true;
        } catch {
            return false;
        }
    }

    static async checkMemory() {
        if ('deviceMemory' in navigator) {
            return navigator.deviceMemory;
        }
        return 4; // Assume 4GB if unknown
    }

    static async checkStorage() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate();
            return {
                quota: estimate.quota,
                usage: estimate.usage,
                available: estimate.quota - estimate.usage
            };
        }
        return null;
    }
}

export { CapabilityDetector };
```

### 8.2 Fallback Implementations

```javascript
// scripts/interface/static/js/search/search_fallback.js

class SearchFallback {

    /**
     * Keyword-only search for low-powered devices
     */
    static async keywordSearch(query, documents, limit = 20) {
        const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
        const results = [];

        for (const doc of documents) {
            const text = `${doc.title} ${doc.content}`.toLowerCase();
            let score = 0;

            for (const term of terms) {
                const regex = new RegExp(term, 'gi');
                const matches = text.match(regex);
                if (matches) {
                    score += matches.length;
                }
            }

            if (score > 0) {
                results.push({
                    id: doc.id,
                    score: score / terms.length,
                    document: doc
                });
            }
        }

        return results
            .sort((a, b) => b.score - a.score)
            .slice(0, limit);
    }

    /**
     * Server fallback for unsupported browsers
     */
    static async serverSearch(query, limit = 20) {
        const response = await fetch(`/search?q=${encodeURIComponent(query)}&limit=${limit}`);
        if (!response.ok) {
            throw new Error('Server search failed');
        }
        return response.json();
    }

    /**
     * Orama fallback (pure JS, no WASM)
     */
    static async oramaSearch(db, query, limit = 20) {
        const { search } = await import('@orama/orama');

        const results = await search(db, {
            term: query,
            limit: limit,
            boost: {
                title: 2,
                content: 1
            }
        });

        return results.hits.map(hit => ({
            id: hit.id,
            score: hit.score,
            document: hit.document
        }));
    }
}

export { SearchFallback };
```

### 8.3 Unified Search Router

```javascript
// scripts/interface/static/js/search/search_router.js

import { searchClient } from './search_client.js';
import { SearchFallback } from './search_fallback.js';
import { CapabilityDetector } from './capability_detector.js';

class SearchRouter {
    static capabilities = null;
    static strategy = null;

    static async initialize() {
        this.capabilities = await CapabilityDetector.detect();
        this.strategy = this.capabilities.strategy;

        console.log(`[Search] Device tier: ${this.capabilities.tier}`);
        console.log(`[Search] Strategy: ${this.strategy}`);

        if (this.strategy === 'full') {
            await searchClient.initialize();
        }
    }

    static async search(query, options = {}) {
        switch (this.strategy) {
            case 'full':
                return searchClient.hybridSearch(query, options);

            case 'keyword-only':
                const db = await this.getDatabase();
                const documents = await db.getAll('documents');
                return SearchFallback.keywordSearch(query, documents, options.limit);

            case 'server-fallback':
                return SearchFallback.serverSearch(query, options.limit);

            default:
                throw new Error(`Unknown search strategy: ${this.strategy}`);
        }
    }

    static async getDatabase() {
        if (typeof window !== 'undefined' && window.ARC8Database) {
            return window.ARC8Database;
        }
        const { ARC8Database } = await import('../data/arc8_database.js');
        await ARC8Database.init();
        return ARC8Database;
    }
}

export { SearchRouter };
```

---

## PART 9: IMPLEMENTATION CHECKLIST

### Phase 1: Foundation (Days 1-3)
- [ ] Install Transformers.js: `npm install @huggingface/transformers`
- [ ] Install EdgeVec: `npm install edgevec`
- [ ] Create `embedding_worker.js` with singleton pipeline
- [ ] Create `vector_index.js` with EdgeVec wrapper
- [ ] Create `search_service.js` unified API
- [ ] Test basic embedding generation
- [ ] Test basic vector search

### Phase 2: Integration (Days 4-6)
- [ ] Create `search_worker.js` Web Worker
- [ ] Create `search_client.js` main thread client
- [ ] Create `progressive_indexer.js` for background indexing
- [ ] Integrate with ARC8Database IndexedDB schema
- [ ] Add search route handler
- [ ] Test end-to-end search flow

### Phase 3: Migration (Days 7-9)
- [ ] Add `/api/export/search-migration` endpoint
- [ ] Create `search_migration.js` import script
- [ ] Implement validation test suite
- [ ] Run migration on test dataset
- [ ] Compare results with txtai baseline
- [ ] Document any quality differences

### Phase 4: Fallbacks (Days 10-12)
- [ ] Create `capability_detector.js`
- [ ] Implement keyword-only fallback
- [ ] Implement server fallback
- [ ] Create `search_router.js` unified router
- [ ] Test on low-powered devices
- [ ] Test in Safari (iOS no SIMD)

### Phase 5: Optimization (Days 13-15)
- [ ] Implement query caching
- [ ] Add model quantization (q4/q8)
- [ ] Optimize batch sizes
- [ ] Profile memory usage
- [ ] Run benchmark suite
- [ ] Document performance results

---

## APPENDIX A: PACKAGE.JSON ADDITIONS

```json
{
  "dependencies": {
    "@huggingface/transformers": "^3.8.1",
    "edgevec": "^0.7.0",
    "@orama/orama": "^3.0.0"
  }
}
```

---

## APPENDIX B: BROWSER COMPATIBILITY

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| IndexedDB | Yes | Yes | Yes | Yes |
| Web Workers | Yes | Yes | Yes | Yes |
| WebAssembly | Yes | Yes | Yes | Yes |
| WASM SIMD | Yes | Yes | **No** | Yes |
| WebGPU | Yes | Flag | **No** | Yes |
| ES Modules | Yes | Yes | Yes | Yes |

**Safari note**: WASM SIMD not supported. EdgeVec auto-falls back to scalar (~2x slower but functional).

---

## APPENDIX C: SACRED CONSTANTS PRESERVATION

```javascript
// Search uses these for polarity balance in results ranking
const SACRED_CONSTANTS = {
    PHI: 1.618033988749895,
    GOLDEN_ANGLE: 137.5077640500378,
    SCHUMANN: 7.83,
    TESLA_PATTERN: [3, 6, 9]
};

// Apply golden ratio to result scoring (optional enhancement)
function applyGoldenRanking(results) {
    return results.map((r, i) => ({
        ...r,
        adjustedScore: r.score * Math.pow(SACRED_CONSTANTS.PHI, -i * 0.1)
    }));
}
```

---

## CONCLUSION

This specification provides a complete path to client-side semantic search that:

1. **Maintains quality** - Same embedding model as current txtai
2. **Works offline** - No server or API calls required
3. **Performs well** - Sub-100ms search on 1000+ documents
4. **Scales appropriately** - Handles 10k+ documents with quantization
5. **Degrades gracefully** - Fallbacks for low-powered devices
6. **Preserves philosophy** - Data sovereignty, local-first, user-owned

The migration can be done incrementally with hybrid mode during transition.

---

## SOURCES REFERENCED

- [Xenova/all-MiniLM-L6-v2 on HuggingFace](https://huggingface.co/Xenova/all-MiniLM-L6-v2)
- [Transformers.js v3 with WebGPU](https://huggingface.co/blog/transformersjs-v3)
- [EdgeVec on GitHub](https://github.com/matte1782/edgevec)
- [EdgeVec on npm](https://www.npmjs.com/package/edgevec)
- [Orama on GitHub](https://github.com/oramasearch/orama)
- [Orama Documentation](https://docs.orama.com/open-source/usage/create/)
- [IndexedDB Storage Limits](https://rxdb.info/articles/indexeddb-max-storage-limit.html)
- [MDN Storage Quotas](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)
- [Voy WASM Vector Search](https://www.npmjs.com/package/voy-search)
- [client-vector-search](https://github.com/yusufhilmi/client-vector-search)
- [Obsidian Vector Search Plugin](https://github.com/ashwin271/obsidian-vector-search)

---

*Document generated by Claude Agent (Opus 4.5 - Ultrathink Analysis)*
*Last updated: 2026-01-13*
