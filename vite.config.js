/**
 * ARC-8 PWA Vite Configuration
 * Build system for Progressive Web App
 */

import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  root: '.',
  publicDir: 'public',

  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,

    rollupOptions: {
      input: {
        main: '/index.html',
      },
      output: {
        manualChunks: {
          // Core framework - always loaded
          'core': [
            './scripts/interface/static/js/core/immutable_core.js',
            './scripts/interface/static/js/core/north_star_principles.js',
          ],
          // Seed engine - loaded on demand
          'seed': [
            './scripts/interface/static/js/core/seed_profile.js',
            './scripts/interface/static/js/core/pi_quadratic_seed.js',
          ],
          // PQC modules
          'pqc': [
            './scripts/interface/static/js/core/pqs_quantum.js',
            './scripts/interface/static/js/core/quantum_equilibrium.js',
          ],
        },
      },
    },

    // Asset handling
    assetsInlineLimit: 4096, // Inline assets < 4KB
    cssCodeSplit: true,
  },

  plugins: [
    // PWA Plugin with Workbox
    VitePWA({
      registerType: 'prompt',
      includeAssets: ['favicon.svg', 'robots.txt', 'icons/*.png'],

      manifest: {
        name: 'ARCHIV-IT - Personal Archive for Artists',
        short_name: 'ARC-8',
        description: 'Your Data. Your Output. Take Control.',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        theme_color: '#030308',
        background_color: '#030308',
        categories: ['productivity', 'utilities'],
        lang: 'en-US',

        icons: [
          {
            src: '/icons/icon-72x72.png',
            sizes: '72x72',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/icon-96x96.png',
            sizes: '96x96',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/icon-128x128.png',
            sizes: '128x128',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/icon-144x144.png',
            sizes: '144x144',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/maskable-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],

        shortcuts: [
          {
            name: 'DOC-8 Archive',
            short_name: 'Archive',
            description: 'Access your document archive',
            url: '/doc8',
          },
          {
            name: 'ITR-8 Create',
            short_name: 'Create',
            description: 'Open the thought stream',
            url: '/itr8',
          },
          {
            name: 'NFT-8 Collection',
            short_name: 'NFTs',
            description: 'View your NFT collection',
            url: '/nft8',
          },
        ],
      },

      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        globIgnores: [
          '**/databank_preview.mov',
          '**/media/**/*.{mp4,mov,avi}',
          '**/node_modules/**',
        ],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB max

        runtimeCaching: [
          // Google Fonts stylesheets
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'google-fonts-stylesheets',
            },
          },
          // Google Fonts webfonts
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
          // User media (images, small videos)
          {
            urlPattern: /\/media\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'arc8-user-media',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
              },
            },
          },
          // API routes
          {
            urlPattern: /\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'arc8-api',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 24 * 60 * 60, // 1 day
              },
            },
          },
        ],
      },
    }),
  ],

  // Development server
  server: {
    port: 5001,
    strictPort: true,
    host: true,
  },

  // Preview server (production build)
  preview: {
    port: 5001,
    strictPort: true,
  },
});
