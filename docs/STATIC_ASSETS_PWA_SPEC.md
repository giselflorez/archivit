# ARC-8 Standalone Application Specification

## Static Assets & PWA Architecture

> **Document Version**: 1.0.0
> **Created**: 2026-01-13
> **Status**: Technical Specification
> **Author**: Claude Opus 4.5 (Ultrathink Analysis)

---

## Executive Summary

This specification defines the architecture for transforming ARC-8 from a Flask-dependent web application into a fully standalone Progressive Web App (PWA) that works offline, can be installed on desktop/mobile, and maintains the sacred dark palette design system.

### Current State Analysis

| Component | Current State | Target State |
|-----------|---------------|--------------|
| Static Assets | Flask `/static/*` routes | Service Worker cached |
| Templates | Jinja2 server-rendered | Client-side templating |
| User Media | Flask `/media/*` routes | OPFS + IndexedDB |
| API Calls | Flask endpoints | Local-first with optional sync |
| Distribution | Python server required | Static hosting + PWA install |

### Asset Inventory

```
scripts/interface/static/
├── js/core/      ~400KB (18 ES modules)
├── js/itr8/      ~56KB (3 modules)
├── css/itr8/     ~14KB
├── js/cre8/      ~6KB (JSON data)
└── media/        ~463MB (video preview)

templates/        54 Jinja2 templates
```

---

## 1. Service Worker Implementation

### 1.1 Strategy Selection

Based on ARC-8's requirements for offline-first operation with intelligent updates:

| Asset Type | Strategy | Rationale |
|------------|----------|-----------|
| Core JS Modules | **Precache** | Critical for app function, versioned |
| CSS Files | **Precache** | Required for sacred palette |
| HTML Shell | **Precache** | App shell architecture |
| User Media | **Cache-First** | Large files, user-owned |
| API Responses | **Network-First** | Freshness matters |
| Large Video | **Runtime Cache** | 463MB too large for precache |
| Fonts (CDN) | **Stale-While-Revalidate** | Balance freshness/speed |

### 1.2 Workbox Implementation

```javascript
// sw.js - Service Worker with Workbox

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { CacheFirst, NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// ═══════════════════════════════════════════════════════════════════
// PRECACHE MANIFEST (Generated at build time)
// ═══════════════════════════════════════════════════════════════════

precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// ═══════════════════════════════════════════════════════════════════
// APP SHELL (Cache-First Navigation)
// ═══════════════════════════════════════════════════════════════════

const navigationHandler = createHandlerBoundToURL('/index.html');
const navigationRoute = new NavigationRoute(navigationHandler, {
  denylist: [
    /\/api\//,     // Exclude API routes
    /\.json$/,     // Exclude JSON data files
  ],
});
registerRoute(navigationRoute);

// ═══════════════════════════════════════════════════════════════════
// CORE JS MODULES (Precached via manifest)
// Already handled by precacheAndRoute above
// ═══════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════
// USER MEDIA FILES (Cache-First with size limits)
// ═══════════════════════════════════════════════════════════════════

registerRoute(
  ({ request, url }) => {
    // Match user media files (images, small videos)
    const isMedia = request.destination === 'image' ||
                    request.destination === 'video' ||
                    url.pathname.startsWith('/media/');
    return isMedia;
  },
  new CacheFirst({
    cacheName: 'arc8-user-media-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        purgeOnQuotaError: true, // Auto-cleanup if quota exceeded
      }),
    ],
  })
);

// ═══════════════════════════════════════════════════════════════════
// LARGE VIDEO PREVIEW (Runtime cache, NOT precached)
// ═══════════════════════════════════════════════════════════════════

registerRoute(
  ({ url }) => url.pathname.includes('databank_preview.mov'),
  new CacheFirst({
    cacheName: 'arc8-large-media-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 5, // Keep very few large files
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
        purgeOnQuotaError: true,
      }),
    ],
  })
);

// ═══════════════════════════════════════════════════════════════════
// GOOGLE FONTS (Stale-While-Revalidate)
// ═══════════════════════════════════════════════════════════════════

registerRoute(
  ({ url }) => url.origin === 'https://fonts.googleapis.com' ||
               url.origin === 'https://fonts.gstatic.com',
  new StaleWhileRevalidate({
    cacheName: 'arc8-fonts-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 20,
        maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
      }),
    ],
  })
);

// ═══════════════════════════════════════════════════════════════════
// API ROUTES (Network-First for freshness)
// ═══════════════════════════════════════════════════════════════════

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'arc8-api-v1',
    networkTimeoutSeconds: 5, // Fallback to cache after 5s
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 24 * 60 * 60, // 1 day
      }),
    ],
  })
);

// ═══════════════════════════════════════════════════════════════════
// OFFLINE FALLBACK
// ═══════════════════════════════════════════════════════════════════

import { offlineFallback } from 'workbox-recipes';

offlineFallback({
  pageFallback: '/offline.html',
  imageFallback: '/img/offline-placeholder.svg',
});

// ═══════════════════════════════════════════════════════════════════
// VERSION MANAGEMENT
// ═══════════════════════════════════════════════════════════════════

const CACHE_VERSION = 'arc8-v1.0.0';

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_VERSION });
  }
});

// Broadcast update available
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    clients.claim().then(() => {
      // Notify all clients of update
      clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'SW_UPDATED', version: CACHE_VERSION });
        });
      });
    })
  );
});
```

### 1.3 Build-Time Precache Manifest Generation

```javascript
// vite.config.js
import { VitePWA } from 'vite-plugin-pwa';

export default {
  plugins: [
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.js',
      injectManifest: {
        globPatterns: [
          '**/*.{js,css,html,svg,png,ico,woff,woff2}',
        ],
        // Exclude large video from precache
        globIgnores: [
          '**/databank_preview.mov',
          '**/media/**/*.{mp4,mov,avi}',
        ],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB max
      },
    }),
  ],
};
```

---

## 2. PWA Manifest Specification

### 2.1 Complete manifest.json

```json
{
  "$schema": "https://json.schemastore.org/web-manifest-combined.json",
  "name": "ARCHIV-IT - Personal Archive for Artists",
  "short_name": "ARC-8",
  "description": "Your Data. Your Output. Take Control. Navigate your body of work with sovereign data ownership.",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "display_override": ["window-controls-overlay", "standalone", "minimal-ui"],
  "orientation": "any",
  "theme_color": "#030308",
  "background_color": "#030308",
  "categories": ["productivity", "utilities", "finance"],
  "lang": "en-US",
  "dir": "ltr",

  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/maskable-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],

  "screenshots": [
    {
      "src": "/screenshots/desktop-dashboard.png",
      "sizes": "1920x1080",
      "type": "image/png",
      "form_factor": "wide",
      "label": "ARC-8 Dashboard - Dark sacred palette"
    },
    {
      "src": "/screenshots/mobile-archive.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Mobile archive view"
    }
  ],

  "shortcuts": [
    {
      "name": "DOC-8 Archive",
      "short_name": "Archive",
      "description": "Access your document archive",
      "url": "/doc8",
      "icons": [{ "src": "/icons/shortcut-doc8.png", "sizes": "96x96" }]
    },
    {
      "name": "ITR-8 Thought Stream",
      "short_name": "Create",
      "description": "Open the thought stream",
      "url": "/itr8/stream",
      "icons": [{ "src": "/icons/shortcut-itr8.png", "sizes": "96x96" }]
    },
    {
      "name": "NFT-8 Collection",
      "short_name": "NFTs",
      "description": "View your NFT collection",
      "url": "/nft8",
      "icons": [{ "src": "/icons/shortcut-nft8.png", "sizes": "96x96" }]
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
      "action": "/open-document",
      "accept": {
        "application/pdf": [".pdf"],
        "text/markdown": [".md", ".markdown"],
        "application/json": [".json"],
        "image/*": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]
      }
    }
  ],

  "protocol_handlers": [
    {
      "protocol": "web+archivit",
      "url": "/protocol?uri=%s"
    }
  ],

  "launch_handler": {
    "client_mode": "navigate-existing"
  },

  "edge_side_panel": {
    "preferred_width": 400
  },

  "related_applications": [],
  "prefer_related_applications": false
}
```

### 2.2 Icon Generation Requirements

| Size | Purpose | Platform |
|------|---------|----------|
| 72x72 | App icon | Android (ldpi) |
| 96x96 | App icon | Android (mdpi), Shortcuts |
| 128x128 | App icon | Chrome Web Store |
| 144x144 | App icon | Android (xhdpi), Windows tiles |
| 152x152 | App icon | iOS (iPad) |
| 180x180 | Apple touch icon | iOS (iPhone) |
| 192x192 | App icon | Android (xxhdpi), PWA install |
| 384x384 | App icon | Android (xxxhdpi) |
| 512x512 | App icon | PWA install, Google Play |
| 512x512 (maskable) | Adaptive icon | Android 8.0+ |

**Maskable Icon Safe Zone**: 80% inner circle (410x410px in 512x512 canvas)

### 2.3 HTML Meta Tags

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">

  <!-- PWA Meta Tags -->
  <meta name="theme-color" content="#030308" media="(prefers-color-scheme: dark)">
  <meta name="theme-color" content="#030308" media="(prefers-color-scheme: light)">
  <meta name="color-scheme" content="dark">

  <!-- Apple PWA Support -->
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="ARC-8">
  <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">

  <!-- Microsoft PWA Support -->
  <meta name="msapplication-TileColor" content="#030308">
  <meta name="msapplication-config" content="/browserconfig.xml">

  <!-- Manifest Link -->
  <link rel="manifest" href="/manifest.json">

  <!-- Favicon -->
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/icons/favicon-16x16.png">

  <title>ARCHIV-IT - Your Data. Your Output. Take Control.</title>
</head>
```

---

## 3. Asset Bundling Strategy

### 3.1 Build Tool Selection: **Vite**

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **Vite** | Fast HMR, native ESM, PWA plugin | Newer ecosystem | **Selected** |
| esbuild | Fastest bundling | Less mature plugin system | Alternative |
| Parcel | Zero-config | Larger bundle sizes | Rejected |
| Webpack | Most mature | Slower, complex config | Legacy |

### 3.2 Vite Configuration

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';
import nunjucks from 'vite-plugin-nunjucks';

export default defineConfig({
  root: 'src',
  publicDir: '../public',

  build: {
    outDir: '../dist',
    emptyOutDir: true,
    sourcemap: true,

    rollupOptions: {
      input: {
        main: '/index.html',
        doc8: '/doc8/index.html',
        itr8: '/itr8/index.html',
        nft8: '/nft8/index.html',
        offline: '/offline.html',
      },
      output: {
        manualChunks: {
          // Core framework always loaded
          'core': [
            './js/core/index.js',
            './js/core/immutable_core.js',
            './js/core/north_star_principles.js',
          ],
          // Seed engine loaded on demand
          'seed': [
            './js/core/seed_profile.js',
            './js/core/pi_quadratic_seed.js',
            './js/core/seed_pqs_integration.js',
          ],
          // Creative engine loaded on demand
          'creative': [
            './js/core/creative_engine.js',
            './js/core/creation_spiral.js',
            './js/core/expansion_engine.js',
          ],
          // Visualization modules
          'viz': [
            './js/itr8/spiral_geometry.js',
            './js/itr8/spark_system.js',
            './js/itr8/glow_materials.js',
          ],
          // Third-party (if any)
          'vendor': [],
        },
      },
    },

    // Asset handling
    assetsInlineLimit: 4096, // Inline assets < 4KB
    cssCodeSplit: true,

    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },

  plugins: [
    // PWA Plugin
    VitePWA({
      registerType: 'prompt',
      includeAssets: ['favicon.svg', 'robots.txt', 'icons/*.png'],

      manifest: false, // Use external manifest.json

      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        globIgnores: ['**/databank_preview.mov'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'google-fonts-stylesheets',
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-webfonts',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
              },
            },
          },
        ],
      },
    }),

    // Nunjucks templating (Jinja2-compatible)
    nunjucks({
      templatesDir: './templates',
      variables: {
        // Global template variables
        APP_NAME: 'ARCHIV-IT',
        SACRED_PALETTE: {
          void: '#030308',
          cosmic: '#0a0a12',
          panel: '#0e0e18',
          border: 'rgba(255,255,255,0.06)',
          gold: '#d4a574',
          emerald: '#54a876',
          rose: '#ba6587',
          violet: '#7865ba',
          text: '#f0ece7',
          textDim: '#9a9690',
          textMuted: '#5a5854',
        },
      },
    }),
  ],

  // Development server
  server: {
    port: 5001, // Match current Flask port
    strictPort: true,
    host: true,
  },

  // Preview server (production build)
  preview: {
    port: 5001,
    strictPort: true,
  },
});
```

### 3.3 Project Structure After Migration

```
arc8-pwa/
├── public/
│   ├── manifest.json
│   ├── robots.txt
│   ├── favicon.svg
│   └── icons/
│       ├── icon-72x72.png
│       ├── icon-96x96.png
│       ├── icon-128x128.png
│       ├── icon-144x144.png
│       ├── icon-152x152.png
│       ├── icon-192x192.png
│       ├── icon-384x384.png
│       ├── icon-512x512.png
│       ├── maskable-512x512.png
│       └── apple-touch-icon.png
├── src/
│   ├── index.html
│   ├── offline.html
│   ├── sw.js (service worker source)
│   ├── js/
│   │   ├── core/ (migrated from scripts/interface/static/js/core)
│   │   ├── itr8/
│   │   └── app.js (main entry point)
│   ├── css/
│   │   ├── sacred-palette.css
│   │   └── itr8/
│   ├── templates/ (Nunjucks templates)
│   │   ├── base.njk
│   │   ├── partials/
│   │   │   ├── nav.njk
│   │   │   ├── header.njk
│   │   │   └── footer.njk
│   │   └── pages/
│   │       ├── doc8/
│   │       ├── itr8/
│   │       └── nft8/
│   └── data/
│       └── masters.json
├── dist/ (build output)
├── vite.config.js
├── package.json
└── tsconfig.json (optional)
```

---

## 4. Template Migration (Jinja2 to Client-Side)

### 4.1 Migration Strategy

**Approach**: Hybrid - Pre-render static pages, client-side for dynamic

| Template Type | Current | Target | Strategy |
|---------------|---------|--------|----------|
| Base layout | Jinja2 `{% extends %}` | Nunjucks `{% extends %}` | 1:1 migration |
| Static pages | Server render | Build-time render | SSG |
| Dynamic lists | Jinja2 loops | JavaScript + JSON | Client-side |
| Forms | Server action | Fetch API | Client-side |
| Conditionals | Jinja2 `{% if %}` | Nunjucks/JS | Depends on data source |

### 4.2 Template Syntax Mapping

```
Jinja2                          Nunjucks (Client-Side)
─────────────────────────────   ─────────────────────────────
{% extends "base.html" %}       {% extends "base.njk" %}
{% block content %}             {% block content %}
{{ variable }}                  {{ variable }}
{{ var|safe }}                  {{ var|safe }}
{% for item in items %}         {% for item in items %}
{% if condition %}              {% if condition %}
{{ loop.index }}                {{ loop.index }}
{% include "partial.html" %}    {% include "partial.njk" %}
{{ url_for('route') }}          /route (hardcoded or JS router)
```

### 4.3 Dynamic Data Loading Pattern

```javascript
// pages/doc8/archive.js
import { NorthStar } from '../../js/core/index.js';

class ArchiveController {
  constructor() {
    this.container = document.getElementById('archive-grid');
    this.data = null;
  }

  async init() {
    // Load from local storage first (offline-first)
    this.data = await this.loadFromCache();
    if (this.data) {
      this.render(this.data);
    }

    // Then fetch fresh data if online
    if (navigator.onLine) {
      try {
        const fresh = await this.fetchFromAPI();
        if (fresh) {
          await this.saveToCache(fresh);
          this.data = fresh;
          this.render(this.data);
        }
      } catch (e) {
        console.warn('Offline or API unavailable');
      }
    }
  }

  async loadFromCache() {
    const db = await this.openDB();
    return await db.get('archive', 'documents');
  }

  async saveToCache(data) {
    const db = await this.openDB();
    await db.put('archive', data, 'documents');
  }

  async openDB() {
    return await idb.openDB('arc8-data', 1, {
      upgrade(db) {
        db.createObjectStore('archive');
        db.createObjectStore('user-media');
        db.createObjectStore('settings');
      },
    });
  }

  render(data) {
    this.container.innerHTML = data.documents.map(doc => `
      <article class="doc-card" data-id="${doc.id}">
        <div class="doc-thumbnail">
          ${doc.thumbnail
            ? `<img src="${doc.thumbnail}" alt="${doc.title}" loading="lazy">`
            : '<div class="doc-placeholder"></div>'
          }
        </div>
        <h3 class="doc-title">${doc.title}</h3>
        <p class="doc-meta">${doc.created_at}</p>
        <div class="doc-tags">
          ${doc.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}
        </div>
      </article>
    `).join('');
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  new ArchiveController().init();
});
```

---

## 5. User Media Storage Architecture

### 5.1 Storage Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│                        STORAGE HIERARCHY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐                                       │
│  │   OPFS (Primary)      │  Files > 5MB, binary data            │
│  │   Origin Private FS   │  Video, images, PDFs                 │
│  │   Quota: ~1GB-50%disk │  Best performance for large files    │
│  └──────────────────────┘                                       │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────┐                                       │
│  │   IndexedDB           │  Structured data, metadata           │
│  │   Key-Value Store     │  Document records, tags, settings    │
│  │   Quota: Shared       │  Fast queries, indexes               │
│  └──────────────────────┘                                       │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────┐                                       │
│  │   Cache API           │  HTTP responses                      │
│  │   Service Worker      │  API data, assets                    │
│  │   Quota: Shared       │  Managed by Workbox                  │
│  └──────────────────────┘                                       │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────┐                                       │
│  │   LocalStorage        │  Small config only                   │
│  │   5MB limit           │  Theme, last route, session          │
│  └──────────────────────┘                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 OPFS Implementation

```javascript
// storage/opfs-manager.js

export class OPFSManager {
  constructor() {
    this.root = null;
    this.initialized = false;
  }

  async init() {
    if (this.initialized) return;

    // Check OPFS support
    if (!navigator.storage?.getDirectory) {
      throw new Error('OPFS not supported in this browser');
    }

    this.root = await navigator.storage.getDirectory();
    this.initialized = true;

    // Request persistent storage
    if (navigator.storage?.persist) {
      const isPersisted = await navigator.storage.persist();
      console.log(`Storage ${isPersisted ? 'is' : 'is not'} persisted`);
    }
  }

  /**
   * Store a file in OPFS
   * @param {string} category - 'images', 'videos', 'documents'
   * @param {string} filename - Unique filename
   * @param {Blob|ArrayBuffer|ReadableStream} data - File data
   */
  async writeFile(category, filename, data) {
    await this.init();

    // Create category directory if needed
    const categoryDir = await this.root.getDirectoryHandle(category, { create: true });

    // Create file
    const fileHandle = await categoryDir.getFileHandle(filename, { create: true });

    // Write using synchronous access (better for large files)
    const writable = await fileHandle.createWritable();
    await writable.write(data);
    await writable.close();

    return { category, filename, size: data.size || data.byteLength };
  }

  /**
   * Read a file from OPFS
   * @returns {File} The file object
   */
  async readFile(category, filename) {
    await this.init();

    const categoryDir = await this.root.getDirectoryHandle(category);
    const fileHandle = await categoryDir.getFileHandle(filename);
    return await fileHandle.getFile();
  }

  /**
   * Create URL for OPFS file (for <img>, <video> src)
   * @returns {string} Object URL (must be revoked when done)
   */
  async getFileURL(category, filename) {
    const file = await this.readFile(category, filename);
    return URL.createObjectURL(file);
  }

  /**
   * Delete a file from OPFS
   */
  async deleteFile(category, filename) {
    await this.init();

    const categoryDir = await this.root.getDirectoryHandle(category);
    await categoryDir.removeEntry(filename);
  }

  /**
   * List all files in a category
   */
  async listFiles(category) {
    await this.init();

    const files = [];
    const categoryDir = await this.root.getDirectoryHandle(category, { create: true });

    for await (const [name, handle] of categoryDir.entries()) {
      if (handle.kind === 'file') {
        const file = await handle.getFile();
        files.push({
          name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
        });
      }
    }

    return files;
  }

  /**
   * Get storage usage
   */
  async getUsage() {
    const estimate = await navigator.storage.estimate();
    return {
      usage: estimate.usage,
      quota: estimate.quota,
      usagePercent: ((estimate.usage / estimate.quota) * 100).toFixed(2),
    };
  }

  /**
   * Clear all user media (with confirmation)
   */
  async clearAll() {
    await this.init();

    for await (const [name, handle] of this.root.entries()) {
      if (handle.kind === 'directory') {
        await this.root.removeEntry(name, { recursive: true });
      }
    }
  }
}

// Singleton
export const opfsManager = new OPFSManager();
```

### 5.3 IndexedDB Schema

```javascript
// storage/idb-schema.js
import { openDB } from 'idb';

export const DB_NAME = 'arc8-database';
export const DB_VERSION = 1;

export async function initDatabase() {
  return await openDB(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion, newVersion, transaction) {
      // Documents store
      if (!db.objectStoreNames.contains('documents')) {
        const docStore = db.createObjectStore('documents', { keyPath: 'id' });
        docStore.createIndex('by-created', 'created_at');
        docStore.createIndex('by-type', 'type');
        docStore.createIndex('by-source', 'source');
      }

      // Tags store (for fast tag lookup)
      if (!db.objectStoreNames.contains('tags')) {
        const tagStore = db.createObjectStore('tags', { keyPath: 'name' });
        tagStore.createIndex('by-count', 'count');
      }

      // Media metadata (references OPFS files)
      if (!db.objectStoreNames.contains('media')) {
        const mediaStore = db.createObjectStore('media', { keyPath: 'id' });
        mediaStore.createIndex('by-document', 'documentId');
        mediaStore.createIndex('by-type', 'mimeType');
        mediaStore.createIndex('by-opfs-path', 'opfsPath');
      }

      // User settings
      if (!db.objectStoreNames.contains('settings')) {
        db.createObjectStore('settings', { keyPath: 'key' });
      }

      // Offline queue (for sync when back online)
      if (!db.objectStoreNames.contains('sync-queue')) {
        const syncStore = db.createObjectStore('sync-queue', {
          keyPath: 'id',
          autoIncrement: true
        });
        syncStore.createIndex('by-timestamp', 'timestamp');
        syncStore.createIndex('by-status', 'status');
      }

      // Seed data (user's mathematical identity)
      if (!db.objectStoreNames.contains('seed')) {
        db.createObjectStore('seed', { keyPath: 'id' });
      }
    },
  });
}
```

### 5.4 Safari iOS 7-Day Limitation Workaround

```javascript
// storage/persistence-guard.js

/**
 * Safari iOS has a 7-day eviction policy for storage unless:
 * 1. PWA is installed to home screen
 * 2. User interacts with the site
 *
 * This module ensures data persistence.
 */

export class PersistenceGuard {
  constructor() {
    this.HEARTBEAT_KEY = 'arc8_last_interaction';
    this.WARNING_THRESHOLD = 5 * 24 * 60 * 60 * 1000; // 5 days
  }

  async check() {
    const lastInteraction = localStorage.getItem(this.HEARTBEAT_KEY);
    const now = Date.now();

    if (lastInteraction) {
      const elapsed = now - parseInt(lastInteraction, 10);

      if (elapsed > this.WARNING_THRESHOLD) {
        // Approaching 7-day limit - prompt user
        this.showPersistenceWarning();
      }
    }

    // Update heartbeat
    this.updateHeartbeat();

    // Request persistent storage
    await this.requestPersistence();
  }

  updateHeartbeat() {
    localStorage.setItem(this.HEARTBEAT_KEY, Date.now().toString());
  }

  async requestPersistence() {
    if (navigator.storage?.persist) {
      const isPersisted = await navigator.storage.persisted();

      if (!isPersisted) {
        const granted = await navigator.storage.persist();
        if (granted) {
          console.log('Persistent storage granted');
        } else {
          console.warn('Persistent storage denied - data may be evicted');
        }
      }
    }
  }

  showPersistenceWarning() {
    // Check if PWA is installed
    const isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
                        window.navigator.standalone === true;

    if (!isInstalled) {
      // Show install prompt to prevent data loss
      const event = new CustomEvent('show-install-prompt', {
        detail: {
          reason: 'data-persistence',
          message: 'Install ARC-8 to prevent your data from being cleared by Safari.',
        },
      });
      window.dispatchEvent(event);
    }
  }
}

// Initialize on app start
export const persistenceGuard = new PersistenceGuard();
```

---

## 6. Distribution Options Comparison

### 6.1 Static Hosting Comparison

| Platform | Pros | Cons | Cost | Verdict |
|----------|------|------|------|---------|
| **Netlify** | Free tier, auto-deploy, CDN | 100GB bandwidth/mo free | Free/Pro | **Recommended** |
| **Vercel** | Fast edge network, preview URLs | 100GB bandwidth/mo free | Free/Pro | Excellent |
| **GitHub Pages** | Free, simple | No server functions, 1GB limit | Free | Good for MVP |
| **Cloudflare Pages** | Unlimited bandwidth, fast | Newer platform | Free | Excellent |
| **IPFS (Pinata)** | Decentralized, censorship-resistant | Slower, requires gateway | $20/mo+ | For Web3 users |
| **IPFS (Fleek)** | Auto-deploy to IPFS + ENS | More complex setup | Free tier | For Web3 users |

### 6.2 IPFS Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IPFS DEPLOYMENT FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   GitHub Repo                                                    │
│        │                                                         │
│        │ Push                                                    │
│        ▼                                                         │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│   │  Fleek   │────▶│   Build  │────▶│   Pin    │               │
│   │  CI/CD   │     │   Vite   │     │  to IPFS │               │
│   └──────────┘     └──────────┘     └──────────┘               │
│                                           │                      │
│                                           │ CID                  │
│                                           ▼                      │
│   ┌──────────────────────────────────────────────────┐         │
│   │              IPFS Network                         │         │
│   │   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐        │         │
│   │   │Node │───│Node │───│Node │───│Node │        │         │
│   │   └─────┘   └─────┘   └─────┘   └─────┘        │         │
│   └──────────────────────────────────────────────────┘         │
│                           │                                      │
│                           │ Gateway                              │
│                           ▼                                      │
│   ┌──────────────────────────────────────────────────┐         │
│   │                    DNS                            │         │
│   │   archivit.app ──▶ IPNS/DNSLink ──▶ CID         │         │
│   │   archivit.eth ──▶ ENS ──▶ CID (decentralized)  │         │
│   └──────────────────────────────────────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Recommended Deployment Strategy

```yaml
# .github/workflows/deploy.yml

name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build PWA
        run: npm run build
        env:
          NODE_ENV: production

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dist

  deploy-netlify:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/download-artifact@v4

      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v3
        with:
          publish-dir: './dist'
          production-deploy: true
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}

  deploy-ipfs:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/download-artifact@v4

      - name: Pin to Pinata
        uses: aquiladev/ipfs-action@v0.3.1
        with:
          path: ./dist
          service: pinata
          pinataKey: ${{ secrets.PINATA_API_KEY }}
          pinataSecret: ${{ secrets.PINATA_API_SECRET }}
```

---

## 7. Desktop App Wrapper Recommendation

### 7.1 Framework Comparison

| Aspect | Tauri | Electron |
|--------|-------|----------|
| **Binary Size** | 2-10 MB | 100-200+ MB |
| **Memory Usage** | 30-50 MB | 150-300+ MB |
| **Startup Time** | <500ms | 1-3 seconds |
| **Backend Language** | Rust | Node.js |
| **WebView** | System (WebKit/WebView2) | Bundled Chromium |
| **Cross-Browser Consistency** | Lower (varies by OS) | High (same everywhere) |
| **Learning Curve** | Higher (Rust) | Lower (JavaScript) |
| **Native API Access** | Excellent | Good |
| **File System Access** | Full | Full |
| **Auto-Update** | Built-in | electron-updater |
| **Code Signing** | Supported | Supported |
| **Maturity** | Growing (2.0 in 2024) | Mature (10+ years) |

### 7.2 Recommendation: **Tauri**

Given ARC-8's requirements for:
- Offline-first operation
- Local data sovereignty
- Performance (3D visualizations)
- Small installation size
- Cross-platform (macOS, Windows, Linux)

**Tauri is the recommended choice** because:

1. **Philosophy alignment**: User sovereignty, local-first
2. **Performance**: Critical for 3D point cloud visualizations
3. **Size**: Users won't wait for 200MB downloads
4. **Memory**: Low footprint allows complex visualizations
5. **Security**: Rust's memory safety, minimal attack surface

### 7.3 Tauri Implementation

```rust
// src-tauri/src/main.rs
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::{CustomMenuItem, Menu, MenuItem, Submenu, WindowEvent};

fn main() {
    // Build menu
    let file_menu = Submenu::new(
        "File",
        Menu::new()
            .add_item(CustomMenuItem::new("import", "Import...").accelerator("CmdOrCtrl+I"))
            .add_item(CustomMenuItem::new("export", "Export...").accelerator("CmdOrCtrl+E"))
            .add_native_item(MenuItem::Separator)
            .add_native_item(MenuItem::Quit),
    );

    let edit_menu = Submenu::new(
        "Edit",
        Menu::new()
            .add_native_item(MenuItem::Undo)
            .add_native_item(MenuItem::Redo)
            .add_native_item(MenuItem::Separator)
            .add_native_item(MenuItem::Cut)
            .add_native_item(MenuItem::Copy)
            .add_native_item(MenuItem::Paste)
            .add_native_item(MenuItem::SelectAll),
    );

    let menu = Menu::new()
        .add_submenu(file_menu)
        .add_submenu(edit_menu);

    tauri::Builder::default()
        .menu(menu)
        .on_menu_event(|event| {
            match event.menu_item_id() {
                "import" => {
                    event.window().emit("menu-import", {}).unwrap();
                }
                "export" => {
                    event.window().emit("menu-export", {}).unwrap();
                }
                _ => {}
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_data_dir,
            read_user_file,
            write_user_file,
            list_user_files,
            delete_user_file,
        ])
        .on_window_event(|event| {
            match event.event() {
                WindowEvent::CloseRequested { .. } => {
                    // Save state before closing
                    event.window().emit("app-closing", {}).unwrap();
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// Command: Get platform-specific data directory
#[tauri::command]
fn get_data_dir() -> Result<String, String> {
    tauri::api::path::data_dir()
        .map(|p| p.join("ARC-8").to_string_lossy().to_string())
        .ok_or_else(|| "Could not determine data directory".to_string())
}

// Command: Read a file from user's data directory
#[tauri::command]
fn read_user_file(filename: &str) -> Result<Vec<u8>, String> {
    let data_dir = tauri::api::path::data_dir()
        .ok_or("Could not determine data directory")?;
    let file_path = data_dir.join("ARC-8").join(filename);

    std::fs::read(&file_path)
        .map_err(|e| format!("Failed to read file: {}", e))
}

// Command: Write a file to user's data directory
#[tauri::command]
fn write_user_file(filename: &str, data: Vec<u8>) -> Result<(), String> {
    let data_dir = tauri::api::path::data_dir()
        .ok_or("Could not determine data directory")?;
    let arc8_dir = data_dir.join("ARC-8");

    // Ensure directory exists
    std::fs::create_dir_all(&arc8_dir)
        .map_err(|e| format!("Failed to create directory: {}", e))?;

    let file_path = arc8_dir.join(filename);
    std::fs::write(&file_path, data)
        .map_err(|e| format!("Failed to write file: {}", e))
}

// Command: List files in user's data directory
#[tauri::command]
fn list_user_files(subdirectory: Option<&str>) -> Result<Vec<String>, String> {
    let data_dir = tauri::api::path::data_dir()
        .ok_or("Could not determine data directory")?;
    let mut target_dir = data_dir.join("ARC-8");

    if let Some(sub) = subdirectory {
        target_dir = target_dir.join(sub);
    }

    if !target_dir.exists() {
        return Ok(vec![]);
    }

    let entries = std::fs::read_dir(&target_dir)
        .map_err(|e| format!("Failed to read directory: {}", e))?;

    let files: Vec<String> = entries
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_file())
        .filter_map(|e| e.file_name().into_string().ok())
        .collect();

    Ok(files)
}

// Command: Delete a file from user's data directory
#[tauri::command]
fn delete_user_file(filename: &str) -> Result<(), String> {
    let data_dir = tauri::api::path::data_dir()
        .ok_or("Could not determine data directory")?;
    let file_path = data_dir.join("ARC-8").join(filename);

    std::fs::remove_file(&file_path)
        .map_err(|e| format!("Failed to delete file: {}", e))
}
```

### 7.4 Tauri Configuration

```json
// src-tauri/tauri.conf.json
{
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev",
    "devPath": "http://localhost:5001",
    "distDir": "../dist"
  },
  "package": {
    "productName": "ARC-8",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "dialog": {
        "all": true
      },
      "fs": {
        "all": false,
        "readFile": true,
        "writeFile": true,
        "readDir": true,
        "createDir": true,
        "removeFile": true,
        "scope": ["$DATA/ARC-8/**"]
      },
      "path": {
        "all": true
      },
      "window": {
        "all": true
      },
      "clipboard": {
        "all": true
      }
    },
    "bundle": {
      "active": true,
      "category": "Productivity",
      "copyright": "WEB3GISEL 2026",
      "deb": {
        "depends": []
      },
      "externalBin": [],
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ],
      "identifier": "app.archivit.arc8",
      "longDescription": "Your Data. Your Output. Take Control. A personal archive system for artists.",
      "macOS": {
        "entitlements": null,
        "exceptionDomain": "",
        "frameworks": [],
        "providerShortName": null,
        "signingIdentity": null
      },
      "resources": [],
      "shortDescription": "Personal Archive for Artists",
      "targets": "all",
      "windows": {
        "certificateThumbprint": null,
        "digestAlgorithm": "sha256",
        "timestampUrl": ""
      }
    },
    "security": {
      "csp": "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'"
    },
    "updater": {
      "active": true,
      "endpoints": [
        "https://releases.archivit.app/{{target}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXkK..."
    },
    "windows": [
      {
        "fullscreen": false,
        "height": 900,
        "width": 1400,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "title": "ARC-8",
        "transparent": false,
        "decorations": true
      }
    ]
  }
}
```

---

## 8. Complete Offline Capability Checklist

### 8.1 Core Functionality

| Feature | Offline Support | Implementation |
|---------|-----------------|----------------|
| View existing documents | YES | IndexedDB + OPFS |
| Create new documents | YES | IndexedDB, sync queue |
| Edit documents | YES | IndexedDB, sync queue |
| View images/media | YES | OPFS |
| Search documents | YES | Client-side search (Fuse.js) |
| Tag management | YES | IndexedDB |
| 3D visualizations | YES | Precached JS modules |
| User seed/identity | YES | IndexedDB (encrypted) |
| Settings/preferences | YES | IndexedDB + LocalStorage |

### 8.2 Features Requiring Network

| Feature | Online Requirement | Fallback |
|---------|-------------------|----------|
| Blockchain data sync | YES | Show cached data with "stale" indicator |
| NFT price updates | YES | Show last known price |
| AI-powered features | YES | Disable with "offline" message |
| Share to social | YES | Queue for later |
| Cloud backup | YES | Queue for later |
| IPFS pinning | YES | Queue for later |

### 8.3 Offline Detection & UI

```javascript
// offline/detector.js

export class OfflineDetector {
  constructor() {
    this.isOnline = navigator.onLine;
    this.listeners = new Set();

    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }

  handleOnline() {
    this.isOnline = true;
    this.notify('online');
    this.processSyncQueue();
  }

  handleOffline() {
    this.isOnline = false;
    this.notify('offline');
    this.showOfflineIndicator();
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  notify(status) {
    this.listeners.forEach(cb => cb(status));
  }

  showOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator') ||
      this.createIndicator();
    indicator.classList.add('visible');
  }

  hideOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator');
    if (indicator) indicator.classList.remove('visible');
  }

  createIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'offline-indicator';
    indicator.innerHTML = `
      <span class="offline-icon">&#x2022;</span>
      <span class="offline-text">OFFLINE MODE</span>
    `;
    indicator.style.cssText = `
      position: fixed;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      background: var(--rose, #ba6587);
      color: var(--text, #f0ece7);
      padding: 4px 12px;
      font-size: 0.7rem;
      letter-spacing: 0.1em;
      border-radius: 0 0 4px 4px;
      z-index: 9999;
      opacity: 0;
      transition: opacity 0.3s ease;
    `;
    document.body.appendChild(indicator);
    return indicator;
  }

  async processSyncQueue() {
    // Process queued operations when back online
    const db = await initDatabase();
    const queue = await db.getAllFromIndex('sync-queue', 'by-status', 'pending');

    for (const item of queue) {
      try {
        await this.processQueueItem(item);
        await db.put('sync-queue', { ...item, status: 'completed' });
      } catch (e) {
        console.error('Sync failed:', e);
        await db.put('sync-queue', { ...item, status: 'failed', error: e.message });
      }
    }
  }

  async processQueueItem(item) {
    // Implement based on item type
    switch (item.type) {
      case 'api-call':
        return fetch(item.url, item.options);
      case 'ipfs-pin':
        return this.pinToIPFS(item.data);
      default:
        console.warn('Unknown queue item type:', item.type);
    }
  }
}

export const offlineDetector = new OfflineDetector();
```

### 8.4 PWA Install Prompt

```javascript
// pwa/install-prompt.js

let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent Chrome's default prompt
  e.preventDefault();
  deferredPrompt = e;

  // Show custom install button
  showInstallButton();
});

window.addEventListener('appinstalled', () => {
  deferredPrompt = null;
  hideInstallButton();

  // Track installation
  console.log('ARC-8 installed');
});

function showInstallButton() {
  const button = document.getElementById('pwa-install-btn');
  if (button) button.classList.add('visible');
}

function hideInstallButton() {
  const button = document.getElementById('pwa-install-btn');
  if (button) button.classList.remove('visible');
}

async function promptInstall() {
  if (!deferredPrompt) return;

  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;

  console.log(`User ${outcome} the installation`);
  deferredPrompt = null;
}

// Export for use in UI
window.promptInstall = promptInstall;
```

---

## 9. Migration Roadmap

### Phase 1: Build System Setup (Week 1)

1. Initialize Vite project structure
2. Configure Workbox service worker
3. Create manifest.json with icons
4. Migrate core JS modules (no changes needed - already ES modules)
5. Test precaching with localhost

### Phase 2: Template Migration (Week 2-3)

1. Install vite-plugin-nunjucks
2. Convert base.html to base.njk
3. Create reusable partials (nav, header, footer)
4. Migrate page templates one by one
5. Implement client-side data loading

### Phase 3: Storage Layer (Week 3-4)

1. Implement OPFS manager
2. Design IndexedDB schema
3. Create migration script from Flask's data
4. Implement offline detection
5. Build sync queue system

### Phase 4: Testing & Optimization (Week 5)

1. Lighthouse PWA audit (target: 100)
2. Performance testing (Core Web Vitals)
3. Cross-browser testing (Safari focus)
4. Offline mode testing
5. Install flow testing

### Phase 5: Desktop Wrapper (Week 6-7)

1. Set up Tauri project
2. Implement native file system commands
3. Build menu system
4. Configure auto-updater
5. Code signing (macOS, Windows)

### Phase 6: Distribution (Week 8)

1. Deploy to Netlify (primary)
2. Deploy to IPFS via Pinata
3. Publish Tauri builds
4. Update documentation
5. Announce release

---

## 10. Technical References

### Sources

- [Workbox Caching Strategies](https://developer.chrome.com/docs/workbox/caching-strategies-overview)
- [PWA Minimal Requirements](https://vite-pwa-org.netlify.app/guide/pwa-minimal-requirements.html)
- [Origin Private File System](https://web.dev/articles/origin-private-file-system)
- [Tauri vs Electron Comparison](https://www.raftlabs.com/blog/tauri-vs-electron-pros-cons/)
- [Storage Quotas and Eviction](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria)
- [IPFS Static Site Deployment](https://pinata.cloud/blog/how-to-ship-a-static-website-to-ipfs-with-pinata/)
- [Vite Static Deploy](https://vite.dev/guide/static-deploy)

### Related ARC-8 Documents

- `/docs/DOC8_DATA_ARCHITECTURE.md` - Data flow architecture
- `/docs/FOUR_MODE_ARCHITECTURE.md` - System modes
- `/scripts/interface/static/js/core/index.js` - NorthStar API

---

*Document generated as part of ARCHIV-IT Ultrathink analysis.*
*Your Data. Your Output. Take Control.*
