# CLIENT-SIDE ARCHITECTURE SPECIFICATION
## ARC-8 Offline-First Progressive Web Application

> **Status**: Technical Specification
> **Version**: 1.0.0
> **Date**: 2026-01-13
> **Author**: Claude Agent (Ultrathink Analysis)

---

## EXECUTIVE SUMMARY

This specification details the migration of ARC-8 from a Flask server-dependent application to a fully offline-capable Progressive Web Application (PWA). The goal is to enable all core features to work without `python visual_browser.py` while maintaining optional server connectivity for advanced features.

### Key Outcomes
- **Core features work 100% offline** (viewing, searching, visualization)
- **No server required** for daily use
- **PWA installable** on desktop and mobile
- **Optional server** for sync, web scraping, and external APIs
- **Data sovereignty preserved** - all data stays local

---

## PART 1: CURRENT ARCHITECTURE ANALYSIS

### 1.1 Flask Routes Inventory (100+ Routes)

| Category | Count | Examples | Migration Complexity |
|----------|-------|----------|---------------------|
| **Page Routes** | 45 | `/`, `/doc8`, `/nft8`, `/cre8`, `/itr8` | LOW |
| **API - Data Read** | 28 | `/api/documents`, `/api/stats`, `/api/point-cloud/data` | MEDIUM |
| **API - Data Write** | 15 | `/api/document/<id>/update`, `/api/collections` | MEDIUM |
| **API - External** | 12 | `/api/scrape-queue/*`, `/api/email/*`, `/api/analyze-image` | SERVER-ONLY |
| **Media Serving** | 3 | `/media/<path>`, `/static/<path>`, `/badge/<username>` | LOW |
| **Authentication** | 5 | `/login`, `/api/nda/accept`, `/setup/*` | LOW |

### 1.2 Database Layer

**Current**: SQLite databases via Python
```
db/
├── user_config.db      # User settings, artist profiles, minting addresses
├── collections.db      # Collections and periods
├── blockchain.db       # Blockchain tracking data
├── sales_analytics.db  # NFT sales history
├── edition_tracking.db # Edition constellation data
└── reputation_scores.db # Collector reputation
```

**Knowledge Base**: Markdown files with YAML frontmatter
```
knowledge_base/
├── processed/
│   ├── about_web_imports/*.md
│   ├── about_gisel_florez/*.md
│   └── ...
└── media/
    ├── images/
    ├── video/
    └── audio/
```

### 1.3 Existing Client-Side Infrastructure

**STRONG FOUNDATION EXISTS:**

```javascript
// scripts/interface/static/js/core/
├── index.js              // NorthStar API - unified interface
├── pi_quadratic_seed.js  // PQS mathematical encoding
├── seed_profile.js       // Behavioral storage engine
├── spiral_compression.js // Golden ratio compression
├── ipfs_storage.js       // IPFS integration (partially stubbed)
├── immutable_core.js     // Sacred constants (PHI, GOLDEN_ANGLE)
├── creative_engine.js    // Breath rhythms, creative leaps
├── balance_principle.js  // Polarity balance
├── expansion_engine.js   // Growth predictions
├── energetic_core.js     // Tesla patterns, quantum probability
└── app_manifest.js       // Publication system
```

The NorthStar system already provides:
- Local storage via `localStorage` and `IndexedDB`
- IPFS integration architecture (needs completion)
- Encryption/decryption utilities
- Platform tier detection (FULL, STANDARD, LITE, MICRO)

---

## PART 2: NEW ARCHITECTURE DESIGN

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARC-8 PWA (Client)                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │
│  │   UI Layer  │  │  Router      │  │  Service Worker             │ │
│  │  (HTML/CSS) │  │  (History)   │  │  (Caching, Offline)         │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    NorthStar Core Engine                         │ │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌────────────────────┐   │ │
│  │  │   PQS   │ │  Seed   │ │  Spiral  │ │  Creative/Balance  │   │ │
│  │  │ Encoder │ │ Profile │ │ Compress │ │     Engines        │   │ │
│  │  └─────────┘ └─────────┘ └──────────┘ └────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     Data Layer                                   │ │
│  │  ┌──────────────┐  ┌────────────┐  ┌─────────────────────────┐ │ │
│  │  │  IndexedDB   │  │   IPFS     │  │  File System Access     │ │ │
│  │  │  (Primary)   │  │  (Backup)  │  │  API (Media)            │ │ │
│  │  └──────────────┘  └────────────┘  └─────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │    OPTIONAL: Sync Server    │
                    │  ┌────────┐ ┌────────────┐ │
                    │  │ Scrape │ │ External   │ │
                    │  │ Engine │ │ APIs       │ │
                    │  └────────┘ └────────────┘ │
                    └─────────────────────────────┘
```

### 2.2 Client-Side Router

**Technology Choice**: Vanilla JavaScript History API

Rationale: No external dependencies, full control, small footprint.

```javascript
// scripts/interface/static/js/router/arc8_router.js

const ARC8Router = {
    routes: new Map(),

    // Route registration
    register(path, handler, options = {}) {
        this.routes.set(path, { handler, ...options });
    },

    // Navigate to route
    navigate(path, state = {}) {
        history.pushState(state, '', path);
        this._handleRoute(path);
    },

    // Handle current route
    async _handleRoute(path) {
        // Match route (supports dynamic segments like /document/:id)
        const match = this._matchRoute(path);
        if (match) {
            const { handler, params } = match;
            await handler(params);
        } else {
            this._handle404();
        }
    },

    // Initialize
    init() {
        window.addEventListener('popstate', () => {
            this._handleRoute(window.location.pathname);
        });

        // Intercept link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.hasAttribute('data-external')) {
                e.preventDefault();
                this.navigate(link.getAttribute('href'));
            }
        });

        // Handle initial route
        this._handleRoute(window.location.pathname);
    }
};
```

**Route Definitions:**

```javascript
// All page routes become client-side handlers
ARC8Router.register('/', handlers.home);
ARC8Router.register('/doc8', handlers.doc8Archivist);
ARC8Router.register('/nft8', handlers.nft8Collector);
ARC8Router.register('/cre8', handlers.cre8Artist);
ARC8Router.register('/soci8', handlers.soci8Social);
ARC8Router.register('/itr8', handlers.itr8ThoughtStream);
ARC8Router.register('/document/:id', handlers.documentDetail);
ARC8Router.register('/search', handlers.search);
ARC8Router.register('/collections', handlers.collections);
ARC8Router.register('/blockchain-tracker', handlers.blockchainTracker);
ARC8Router.register('/masters-spectral', handlers.mastersSpectral);
// ... etc
```

### 2.3 IndexedDB Schema Design

Replace SQLite with IndexedDB for browser-native storage:

```javascript
// scripts/interface/static/js/data/arc8_database.js

const ARC8Database = {
    DB_NAME: 'arc8_knowledge_base',
    DB_VERSION: 1,

    stores: {
        // Core document store (replaces knowledge_base/*.md)
        documents: {
            keyPath: 'id',
            indexes: [
                { name: 'by_date', keyPath: 'created_at' },
                { name: 'by_source', keyPath: 'source' },
                { name: 'by_cognitive_type', keyPath: 'cognitive_type' },
                { name: 'by_tags', keyPath: 'tags', multiEntry: true }
            ]
        },

        // User configuration (replaces user_config.db)
        user_config: {
            keyPath: 'key',
            indexes: []
        },

        // Artist profiles
        artist_profiles: {
            keyPath: 'id',
            autoIncrement: true,
            indexes: [
                { name: 'by_folder', keyPath: 'folder_name', unique: true },
                { name: 'by_current', keyPath: 'is_current' }
            ]
        },

        // Minting addresses
        minting_addresses: {
            keyPath: 'id',
            autoIncrement: true,
            indexes: [
                { name: 'by_address', keyPath: 'address' },
                { name: 'by_network', keyPath: 'network' },
                { name: 'by_artist', keyPath: 'artist_profile_id' }
            ]
        },

        // Collections (replaces collections.db)
        collections: {
            keyPath: 'id',
            autoIncrement: true,
            indexes: [
                { name: 'by_name', keyPath: 'name' }
            ]
        },

        // Blockchain tracking (replaces blockchain.db)
        blockchain_tracking: {
            keyPath: 'id',
            autoIncrement: true,
            indexes: [
                { name: 'by_address', keyPath: 'address' },
                { name: 'by_network', keyPath: 'network' },
                { name: 'by_contract', keyPath: 'contract' }
            ]
        },

        // Media blobs (for offline media access)
        media_blobs: {
            keyPath: 'path',
            indexes: [
                { name: 'by_document', keyPath: 'document_id' },
                { name: 'by_type', keyPath: 'mime_type' }
            ]
        },

        // Search index (pre-computed for fast search)
        search_index: {
            keyPath: 'term',
            indexes: []
        },

        // Sync queue (for offline-to-online sync)
        sync_queue: {
            keyPath: 'id',
            autoIncrement: true,
            indexes: [
                { name: 'by_operation', keyPath: 'operation' },
                { name: 'by_timestamp', keyPath: 'timestamp' }
            ]
        }
    },

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                for (const [storeName, config] of Object.entries(this.stores)) {
                    if (!db.objectStoreNames.contains(storeName)) {
                        const store = db.createObjectStore(storeName, {
                            keyPath: config.keyPath,
                            autoIncrement: config.autoIncrement || false
                        });

                        for (const index of config.indexes || []) {
                            store.createIndex(
                                index.name,
                                index.keyPath,
                                { unique: index.unique || false, multiEntry: index.multiEntry || false }
                            );
                        }
                    }
                }
            };

            request.onsuccess = () => {
                this.db = request.result;
                resolve(this);
            };

            request.onerror = () => reject(request.error);
        });
    },

    // CRUD operations
    async get(store, key) {
        return this._transaction(store, 'readonly', s => s.get(key));
    },

    async getAll(store, index = null, query = null) {
        return this._transaction(store, 'readonly', s => {
            if (index && query) {
                return s.index(index).getAll(query);
            }
            return s.getAll();
        });
    },

    async put(store, value) {
        return this._transaction(store, 'readwrite', s => s.put(value));
    },

    async delete(store, key) {
        return this._transaction(store, 'readwrite', s => s.delete(key));
    },

    async _transaction(storeName, mode, operation) {
        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(storeName, mode);
            const store = tx.objectStore(storeName);
            const request = operation(store);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
};
```

### 2.4 Service Worker Implementation

```javascript
// scripts/interface/static/sw.js

const CACHE_NAME = 'arc8-v1';
const STATIC_ASSETS = [
    '/',
    '/doc8',
    '/nft8',
    '/cre8',
    '/itr8',
    '/soci8',
    '/static/css/sacred-palette.css',
    '/static/js/core/index.js',
    '/static/js/core/pi_quadratic_seed.js',
    '/static/js/core/seed_profile.js',
    '/static/js/core/spiral_compression.js',
    '/static/js/core/ipfs_storage.js',
    '/static/js/router/arc8_router.js',
    '/static/js/data/arc8_database.js',
    // Three.js and D3 from CDN cached
    'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
    'https://d3js.org/d3.v7.min.js'
];

// Install - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch - network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API requests - try network first, fall back to cached response
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(event.request));
        return;
    }

    // Media files - cache with background update
    if (url.pathname.startsWith('/media/')) {
        event.respondWith(staleWhileRevalidate(event.request));
        return;
    }

    // Static assets - cache first
    event.respondWith(cacheFirstStrategy(event.request));
});

async function networkFirstStrategy(request) {
    try {
        const response = await fetch(request);
        // Cache successful API responses
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Fall back to cache
        const cached = await caches.match(request);
        if (cached) return cached;

        // Return offline API response
        return new Response(
            JSON.stringify({
                offline: true,
                message: 'You are offline. Data may be stale.'
            }),
            {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

async function cacheFirstStrategy(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
        return response;
    } catch (error) {
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/offline.html');
        }
        throw error;
    }
}

async function staleWhileRevalidate(request) {
    const cached = await caches.match(request);

    const fetchPromise = fetch(request).then((response) => {
        const cache = caches.open(CACHE_NAME);
        cache.then(c => c.put(request, response.clone()));
        return response;
    });

    return cached || fetchPromise;
}

// Background sync for offline operations
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-documents') {
        event.waitUntil(syncDocuments());
    }
});

async function syncDocuments() {
    // Read from sync_queue in IndexedDB and push to server
    const db = await openDatabase();
    const tx = db.transaction('sync_queue', 'readonly');
    const store = tx.objectStore('sync_queue');
    const pending = await store.getAll();

    for (const item of pending) {
        try {
            await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item)
            });

            // Remove from queue on success
            const deleteTx = db.transaction('sync_queue', 'readwrite');
            deleteTx.objectStore('sync_queue').delete(item.id);
        } catch (error) {
            console.warn('Sync failed for item:', item.id);
        }
    }
}
```

### 2.5 PWA Manifest

```json
// scripts/interface/static/manifest.json
{
    "name": "ARC-8 - Personal Archive for Artists",
    "short_name": "ARC-8",
    "description": "Your Data. Your Output. Take Control.",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#030308",
    "theme_color": "#d4a574",
    "orientation": "any",
    "icons": [
        {
            "src": "/static/icons/arc8-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/static/icons/arc8-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ],
    "categories": ["productivity", "utilities", "lifestyle"],
    "screenshots": [
        {
            "src": "/static/screenshots/doc8-desktop.png",
            "sizes": "1280x720",
            "type": "image/png",
            "form_factor": "wide"
        },
        {
            "src": "/static/screenshots/doc8-mobile.png",
            "sizes": "390x844",
            "type": "image/png",
            "form_factor": "narrow"
        }
    ],
    "share_target": {
        "action": "/share-target",
        "method": "POST",
        "enctype": "multipart/form-data",
        "params": {
            "title": "title",
            "text": "text",
            "url": "url",
            "files": [
                {
                    "name": "media",
                    "accept": ["image/*", "video/*", "audio/*", "application/pdf"]
                }
            ]
        }
    },
    "file_handlers": [
        {
            "action": "/open-file",
            "accept": {
                "application/json": [".itr8", ".arc8"],
                "text/markdown": [".md"]
            }
        }
    ],
    "protocol_handlers": [
        {
            "protocol": "web+arc8",
            "url": "/protocol?q=%s"
        }
    ]
}
```

---

## PART 3: ROUTE-BY-ROUTE MIGRATION PLAN

### 3.1 Phase 1: Core Pages (Week 1)

**Convert to static HTML with client-side rendering:**

| Flask Route | Client Handler | Data Source |
|-------------|----------------|-------------|
| `/` | `handlers.home()` | IndexedDB: `documents` |
| `/doc8` | `handlers.doc8Archivist()` | IndexedDB: `documents` |
| `/nft8` | `handlers.nft8Collector()` | IndexedDB: `blockchain_tracking` |
| `/cre8` | `handlers.cre8Artist()` | IndexedDB: `documents`, NorthStar |
| `/itr8` | `handlers.itr8ThoughtStream()` | IndexedDB: `documents`, NorthStar |
| `/soci8` | `handlers.soci8Social()` | IndexedDB: `user_config` |
| `/search` | `handlers.search()` | IndexedDB: `search_index` |

**Implementation Pattern:**

```javascript
// Example: DOC-8 handler
handlers.doc8Archivist = async () => {
    // Load template (cached in service worker)
    const template = await loadTemplate('doc8_archivist.html');

    // Fetch data from IndexedDB
    const documents = await ARC8Database.getAll('documents');
    const stats = await calculateStats(documents);

    // Render with client-side templating
    const rendered = renderTemplate(template, { documents, stats });
    document.getElementById('app').innerHTML = rendered;

    // Initialize interactive components
    initializeTranscriptViewer();
    initializeSourceRecord();
};
```

### 3.2 Phase 2: API Endpoints (Week 2)

**Replace Flask APIs with client-side equivalents:**

| Flask API | Client Implementation |
|-----------|----------------------|
| `/api/documents` | `ARC8Database.getAll('documents')` |
| `/api/stats` | `calculateStatsFromIndexedDB()` |
| `/api/documents-by-tag/<tag>` | `ARC8Database.getAll('documents', 'by_tags', tag)` |
| `/api/point-cloud/data` | `buildPointCloudFromIndexedDB()` |
| `/api/semantic-network` | Client-side TF-IDF + cosine similarity |
| `/api/collections` | `ARC8Database.getAll('collections')` |

**Client-side search implementation:**

```javascript
// scripts/interface/static/js/search/client_search.js

class ClientSearchEngine {
    constructor(db) {
        this.db = db;
        this.index = new Map(); // term -> [doc_ids]
    }

    async buildIndex() {
        const documents = await this.db.getAll('documents');

        for (const doc of documents) {
            const terms = this.tokenize(doc.title + ' ' + doc.content);
            for (const term of terms) {
                if (!this.index.has(term)) {
                    this.index.set(term, []);
                }
                this.index.get(term).push(doc.id);
            }
        }

        // Persist index to IndexedDB for fast reload
        await this.db.put('search_index', {
            term: '_full_index',
            data: Object.fromEntries(this.index)
        });
    }

    async search(query, limit = 50) {
        const queryTerms = this.tokenize(query);
        const scores = new Map();

        for (const term of queryTerms) {
            const docIds = this.index.get(term) || [];
            for (const docId of docIds) {
                scores.set(docId, (scores.get(docId) || 0) + 1);
            }
        }

        // Sort by score and return top results
        const results = Array.from(scores.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit);

        // Fetch full documents
        return Promise.all(
            results.map(([id]) => this.db.get('documents', id))
        );
    }

    tokenize(text) {
        return text.toLowerCase()
            .replace(/[^\w\s]/g, '')
            .split(/\s+/)
            .filter(t => t.length > 2);
    }
}
```

### 3.3 Phase 3: Media Handling (Week 3)

**Two-tier approach:**

1. **Small media (< 5MB)**: Store in IndexedDB as blobs
2. **Large media (> 5MB)**: Use File System Access API or external reference

```javascript
// scripts/interface/static/js/media/media_manager.js

class MediaManager {
    constructor(db) {
        this.db = db;
        this.BLOB_SIZE_LIMIT = 5 * 1024 * 1024; // 5MB
    }

    async storeMedia(file, documentId) {
        if (file.size <= this.BLOB_SIZE_LIMIT) {
            // Store in IndexedDB
            const arrayBuffer = await file.arrayBuffer();
            await this.db.put('media_blobs', {
                path: `media/${documentId}/${file.name}`,
                document_id: documentId,
                mime_type: file.type,
                size: file.size,
                data: arrayBuffer,
                stored_at: Date.now()
            });
            return `indexeddb://media/${documentId}/${file.name}`;
        } else {
            // Use File System Access API (if available)
            if ('showSaveFilePicker' in window) {
                return this.storeWithFileSystemAPI(file, documentId);
            }
            // Fallback: keep reference only
            return file.name;
        }
    }

    async getMedia(path) {
        // Try IndexedDB first
        const blob = await this.db.get('media_blobs', path);
        if (blob) {
            return new Blob([blob.data], { type: blob.mime_type });
        }

        // Try File System Access API
        if (this.fileHandles.has(path)) {
            const handle = this.fileHandles.get(path);
            return await handle.getFile();
        }

        // Try network (if online)
        if (navigator.onLine) {
            const response = await fetch(`/${path}`);
            if (response.ok) {
                return response.blob();
            }
        }

        return null;
    }

    async storeWithFileSystemAPI(file, documentId) {
        try {
            const dirHandle = await window.showDirectoryPicker({
                mode: 'readwrite',
                startIn: 'documents'
            });

            const subDir = await dirHandle.getDirectoryHandle('arc8-media', { create: true });
            const fileHandle = await subDir.getFileHandle(file.name, { create: true });

            const writable = await fileHandle.createWritable();
            await writable.write(file);
            await writable.close();

            // Store handle reference
            this.fileHandles.set(`media/${documentId}/${file.name}`, fileHandle);

            return `filesystem://arc8-media/${file.name}`;
        } catch (error) {
            console.warn('File System Access API failed:', error);
            return file.name;
        }
    }
}
```

### 3.4 Phase 4: Server-Only Features (Ongoing)

**Features that REQUIRE server (cannot be client-side):**

| Feature | Why Server Required | Offline Behavior |
|---------|---------------------|------------------|
| **Web Scraping** | SSRF protection, headless browser | Queue for later, show placeholder |
| **Email Sync** | IMAP/SMTP protocols | Disabled, show "requires connection" |
| **Vision API** | External API (Anthropic, OpenAI) | Queue for later, show "pending analysis" |
| **Blockchain Live** | RPC calls to nodes | Use cached data, show "last updated" |
| **Whisper Transcription** | GPU-intensive processing | Queue for later, show progress |
| **Badge Generation** | Dynamic SVG server-side | Use cached badge or placeholder |

**Graceful degradation pattern:**

```javascript
// Feature detection and fallback
async function scrapeUrl(url) {
    if (navigator.onLine && await serverAvailable()) {
        // Use server
        return fetch('/api/scrape', {
            method: 'POST',
            body: JSON.stringify({ url })
        }).then(r => r.json());
    } else {
        // Queue for later
        await ARC8Database.put('sync_queue', {
            operation: 'scrape',
            data: { url },
            timestamp: Date.now()
        });

        return {
            queued: true,
            message: 'URL queued for scraping when online'
        };
    }
}
```

---

## PART 4: DATA MIGRATION STRATEGY

### 4.1 Initial Import: SQLite to IndexedDB

```javascript
// scripts/interface/static/js/migration/sqlite_import.js

class SQLiteToIndexedDBMigrator {

    async migrateFromExport(sqliteExportJson) {
        const data = JSON.parse(sqliteExportJson);

        // Migrate user_config
        if (data.user_config) {
            for (const row of data.user_config) {
                await ARC8Database.put('user_config', {
                    key: row.email,
                    ...row
                });
            }
        }

        // Migrate artist_profiles
        if (data.artist_profiles) {
            for (const row of data.artist_profiles) {
                await ARC8Database.put('artist_profiles', row);
            }
        }

        // Migrate collections
        if (data.collections) {
            for (const row of data.collections) {
                await ARC8Database.put('collections', row);
            }
        }

        // ... etc
    }

    async migrateMarkdownFiles(fileList) {
        for (const file of fileList) {
            const content = await file.text();
            const { frontmatter, body } = parseMarkdown(content);

            await ARC8Database.put('documents', {
                id: frontmatter.id || generateId(),
                title: frontmatter.title,
                source: frontmatter.source,
                url: frontmatter.url,
                tags: frontmatter.tags || [],
                cognitive_type: frontmatter.cognitive_type,
                created_at: frontmatter.created_at,
                content: body,
                file_path: file.name
            });
        }
    }
}
```

### 4.2 Export Server Endpoint (One-time migration tool)

Add this route to Flask for exporting data:

```python
# scripts/interface/visual_browser.py

@app.route('/api/export/full-database')
def export_full_database():
    """Export all databases for client-side import"""
    from interface.user_config_db import UserConfigDB
    from analytics.sales_db import get_sales_db

    export = {
        'version': '1.0.0',
        'exported_at': datetime.now().isoformat()
    }

    # Export user config
    user_db = UserConfigDB()
    conn = user_db.get_connection()
    export['user_config'] = [dict(row) for row in conn.execute('SELECT * FROM user_config').fetchall()]
    export['artist_profiles'] = [dict(row) for row in conn.execute('SELECT * FROM artist_profiles').fetchall()]
    export['minting_addresses'] = [dict(row) for row in conn.execute('SELECT * FROM minting_addresses').fetchall()]
    conn.close()

    # Export knowledge base documents
    kb_path = Path('knowledge_base/processed')
    documents = []
    for md_file in kb_path.rglob('*.md'):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            documents.append({
                'id': frontmatter.get('id'),
                'title': frontmatter.get('title'),
                'source': frontmatter.get('source'),
                'tags': frontmatter.get('tags', []),
                'content': body,
                'file_path': str(md_file.relative_to(kb_path))
            })
        except:
            continue
    export['documents'] = documents

    return jsonify(export)
```

---

## PART 5: DEPLOYMENT OPTIONS

### 5.1 Option A: Static File Hosting (Recommended)

Host compiled HTML/JS/CSS on any static host:
- GitHub Pages
- Netlify
- Cloudflare Pages
- Self-hosted nginx

**Build process:**

```bash
# build.sh
#!/bin/bash

# 1. Bundle JavaScript
npx esbuild scripts/interface/static/js/core/index.js \
    --bundle \
    --outfile=dist/js/arc8-core.bundle.js \
    --format=esm \
    --minify

# 2. Copy static assets
cp -r scripts/interface/static/css dist/css
cp -r scripts/interface/static/icons dist/icons
cp scripts/interface/static/manifest.json dist/
cp scripts/interface/static/sw.js dist/

# 3. Build HTML pages (inline templates)
python scripts/build/compile_templates.py

# 4. Generate app shell
python scripts/build/generate_app_shell.py

echo "Build complete: dist/"
```

### 5.2 Option B: Electron Wrapper

For desktop app distribution:

```javascript
// electron/main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        titleBarStyle: 'hiddenInset',
        backgroundColor: '#030308'
    });

    win.loadFile('dist/index.html');
}

app.whenReady().then(createWindow);
```

### 5.3 Option C: Hybrid Mode (Current + PWA)

Keep Flask server running but make it optional:

```javascript
// scripts/interface/static/js/hybrid_mode.js

const HybridMode = {
    serverUrl: null,
    isServerAvailable: false,

    async detectServer() {
        try {
            const response = await fetch('http://localhost:5001/api/stats', {
                method: 'HEAD',
                timeout: 2000
            });
            this.isServerAvailable = response.ok;
            this.serverUrl = 'http://localhost:5001';
        } catch {
            this.isServerAvailable = false;
        }
        return this.isServerAvailable;
    },

    async request(endpoint, options = {}) {
        if (this.isServerAvailable) {
            // Use server
            return fetch(`${this.serverUrl}${endpoint}`, options);
        } else {
            // Use client-side
            return ClientAPI.handle(endpoint, options);
        }
    }
};
```

---

## PART 6: RECOMMENDED TECH STACK

### 6.1 Core Stack (Vanilla - No Framework)

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Routing** | History API | Native, no dependencies |
| **State** | NorthStar (existing) | Already built, comprehensive |
| **Storage** | IndexedDB | Browser-native, large capacity |
| **Caching** | Service Worker | Offline-first, background sync |
| **Build** | esbuild | Fast, simple, ES modules |

### 6.2 Optional Enhancements

| Feature | Library | Size | Purpose |
|---------|---------|------|---------|
| Templating | lit-html | 3KB | Efficient HTML updates |
| Markdown | marked | 8KB | Parse knowledge base files |
| Date handling | dayjs | 2KB | Lightweight date formatting |
| Crypto | Web Crypto API | Native | Encryption (already used) |

### 6.3 Why NOT a Framework

1. **NorthStar already exists** - Comprehensive client-side engine
2. **Bundle size** - React/Vue/Svelte add 30-100KB+
3. **Control** - Full ownership of routing, state, rendering
4. **Offline-first** - Frameworks assume online connectivity
5. **Philosophy** - ARCHIV-IT values sovereignty over dependencies

---

## PART 7: IMPLEMENTATION TIMELINE

### Week 1: Foundation
- [ ] Create `arc8_router.js` with History API routing
- [ ] Create `arc8_database.js` IndexedDB wrapper
- [ ] Create `manifest.json` and basic `sw.js`
- [ ] Convert `/doc8` page to client-side rendering

### Week 2: Core Pages
- [ ] Convert all mode pages (NFT-8, CRE-8, SOCI-8, IT-R8)
- [ ] Implement client-side search engine
- [ ] Create data migration export endpoint
- [ ] Test offline functionality

### Week 3: Media & Visualization
- [ ] Implement MediaManager with File System Access API
- [ ] Convert visualizations (Three.js, D3) to use IndexedDB
- [ ] Implement stale-while-revalidate caching
- [ ] Add PWA install prompt

### Week 4: Sync & Polish
- [ ] Implement background sync for offline operations
- [ ] Add hybrid mode for optional server connectivity
- [ ] Performance optimization
- [ ] Documentation and testing

---

## PART 8: REFERENCE IMPLEMENTATIONS

### 8.1 Similar Successful Projects

| App | Architecture | Relevant Learning |
|-----|--------------|-------------------|
| **Obsidian** | Electron + local files | File System Access API patterns |
| **Notion** | Hybrid PWA | Offline-first sync strategies |
| **Figma** | WebAssembly + IndexedDB | Large file handling |
| **Excalidraw** | Pure client + optional collab | No-server default mode |
| **Standard Notes** | Client-side encryption | E2E encryption patterns |

### 8.2 Key APIs to Leverage

```javascript
// Feature detection
const features = {
    serviceWorker: 'serviceWorker' in navigator,
    indexedDB: 'indexedDB' in window,
    fileSystemAccess: 'showOpenFilePicker' in window,
    persistentStorage: 'storage' in navigator && 'persist' in navigator.storage,
    backgroundSync: 'serviceWorker' in navigator && 'sync' in window.SyncManager,
    shareTarget: 'share' in navigator
};

console.log('ARC-8 Feature Support:', features);
```

---

## APPENDIX A: FILE STRUCTURE

```
scripts/interface/static/
├── js/
│   ├── core/                  # Existing NorthStar modules
│   │   ├── index.js
│   │   ├── pi_quadratic_seed.js
│   │   └── ...
│   ├── router/                # NEW: Client-side routing
│   │   └── arc8_router.js
│   ├── data/                  # NEW: IndexedDB layer
│   │   └── arc8_database.js
│   ├── search/                # NEW: Client-side search
│   │   └── client_search.js
│   ├── media/                 # NEW: Media management
│   │   └── media_manager.js
│   ├── migration/             # NEW: Data migration
│   │   └── sqlite_import.js
│   └── hybrid/                # NEW: Hybrid mode
│       └── hybrid_mode.js
├── css/
│   └── sacred-palette.css     # Design system
├── icons/
│   ├── arc8-192.png
│   └── arc8-512.png
├── manifest.json              # NEW: PWA manifest
├── sw.js                      # NEW: Service worker
└── offline.html               # NEW: Offline fallback page
```

---

## APPENDIX B: SACRED CONSTANTS (DO NOT MODIFY)

```javascript
// These must remain identical in client-side implementation
const SACRED_CONSTANTS = {
    PHI: 1.618033988749895,
    GOLDEN_ANGLE: 137.5077640500378,
    SCHUMANN: 7.83,
    TESLA_PATTERN: [3, 6, 9]
};
```

---

## CONCLUSION

This specification provides a complete roadmap for migrating ARC-8 from Flask-dependent to a fully offline-capable PWA while:

1. **Preserving** the existing NorthStar client-side engine
2. **Maintaining** the sacred design system and constants
3. **Enabling** true data sovereignty (no server required)
4. **Supporting** progressive enhancement (server optional)
5. **Following** the 11 Non-Negotiables

The migration can be done incrementally, page by page, with the hybrid mode allowing both architectures to coexist during transition.

---

*Document generated by Claude Agent (Ultrathink Analysis)*
*Last updated: 2026-01-13*
