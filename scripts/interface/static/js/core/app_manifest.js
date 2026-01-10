/**
 * APP MANIFEST SYSTEM
 * ===================
 * Enabling Discovery Without Hosting
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * THE ARCHITECTURE OF REACH WITHOUT LIABILITY
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ARCHIVIT creates apps locally.
 * Users publish wherever they choose.
 * Manifests enable discovery without hosting.
 *
 * The manifest is METADATA about the app:
 * - What it is
 * - Who made it (anonymously verifiable)
 * - Where it lives (user fills this in after publishing)
 * - What values it aligns with
 *
 * Discovery apps (dreamed by the community) can index manifests.
 * They POINT TO apps, never HOST them.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * LIABILITY ARCHITECTURE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ARCHIVIT: Creates apps locally (like a word processor)
 *   ↓
 * USER: Exports and publishes wherever they want (their choice)
 *   ↓
 * MANIFEST: Describes the app, points to its location
 *   ↓
 * DISCOVERY: Community apps index manifests (like search engines)
 *
 * No single entity hosts. No single entity gatekeeps.
 * Creation is enabled. Publication is user's choice.
 * Discovery is community-built.
 */

import { PHI } from './pi_quadratic_seed.js';
import { NORTH_STAR_PRINCIPLES } from './north_star_principles.js';

// ═══════════════════════════════════════════════════════════════════════════
// MANIFEST SCHEMA
// ═══════════════════════════════════════════════════════════════════════════

const MANIFEST_VERSION = '1.0.0';

const MANIFEST_SCHEMA = Object.freeze({
    // Required fields
    required: [
        'name',
        'description',
        'creator_proof',
        'created_at',
        'manifest_version'
    ],

    // Optional fields (user fills after publishing)
    optional: [
        'published_locations',
        'category',
        'tags',
        'preview_image',
        'values_alignment'
    ],

    // Categories for discovery
    categories: [
        'creativity',      // Art, music, design tools
        'utility',         // Productivity, organization
        'social',          // Connection, communication
        'education',       // Learning, teaching
        'wellness',        // Health, mindfulness
        'environment',     // Sustainability, nature
        'community',       // Local, neighborhood
        'experimental',    // Unknown territory (Bjork/Bowie domain)
        'infrastructure',  // Tools for building more tools
        'discovery'        // Meta-category: apps that help find apps
    ],

    // Supported publication protocols
    protocols: [
        'https',           // Traditional web hosting
        'ipfs',            // InterPlanetary File System
        'ipns',            // IPFS naming system
        'dat',             // Dat protocol
        'hyper',           // Hypercore protocol
        'file',            // Local file (not public)
        'arweave'          // Permanent storage
    ]
});

// ═══════════════════════════════════════════════════════════════════════════
// MANIFEST GENERATOR
// Creates manifest for any dreamed app
// ═══════════════════════════════════════════════════════════════════════════

class AppManifestGenerator {
    constructor() {
        this.version = MANIFEST_VERSION;
    }

    /**
     * Generate a manifest for a dreamed app
     *
     * @param {Object} app - The app specification from dream pipeline
     * @param {Object} creatorProof - Anonymous but verifiable creator identity
     * @returns {Object} Complete manifest
     */
    generate(app, creatorProof) {
        const manifest = {
            // ─────────────────────────────────────────────────────
            // IDENTITY (Required)
            // ─────────────────────────────────────────────────────
            manifest_version: this.version,
            name: app.name || 'Untitled Dream',
            description: app.description || '',
            created_at: Date.now(),

            // Anonymous but verifiable creator proof
            creator_proof: this._generateCreatorProof(creatorProof),

            // ─────────────────────────────────────────────────────
            // PUBLICATION (User fills after deploying)
            // ─────────────────────────────────────────────────────
            published_locations: [],  // User adds after publishing

            // ─────────────────────────────────────────────────────
            // DISCOVERY (For indexing)
            // ─────────────────────────────────────────────────────
            category: app.category || 'experimental',
            tags: app.tags || [],
            preview_image: null,  // User can add

            // ─────────────────────────────────────────────────────
            // VALUES (North Star alignment)
            // ─────────────────────────────────────────────────────
            values_alignment: this._checkValuesAlignment(app),

            // ─────────────────────────────────────────────────────
            // TECHNICAL
            // ─────────────────────────────────────────────────────
            export_formats: this._getAvailableFormats(),
            dependencies: app.dependencies || [],

            // ─────────────────────────────────────────────────────
            // INTEGRITY
            // ─────────────────────────────────────────────────────
            manifest_hash: null  // Computed after all fields set
        };

        // Compute integrity hash
        manifest.manifest_hash = this._computeHash(manifest);

        return manifest;
    }

    /**
     * Generate anonymous but verifiable creator proof
     * Uses PQS genesis without revealing identity
     */
    _generateCreatorProof(creatorProof) {
        if (!creatorProof) {
            return {
                type: 'anonymous',
                timestamp: Date.now(),
                message: 'Creator chose not to provide proof'
            };
        }

        return {
            type: 'pqs_derived',
            // Hash of genesis, not genesis itself
            genesis_hash: this._hashGenesis(creatorProof.genesis),
            timestamp: creatorProof.timestamp || Date.now(),
            // Signature that proves ownership without revealing identity
            signature: creatorProof.signature || null
        };
    }

    /**
     * Hash genesis for anonymous proof
     */
    _hashGenesis(genesis) {
        if (!genesis) return null;

        // Simple hash for now - production would use proper crypto
        const str = JSON.stringify(genesis);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return 'genesis_' + Math.abs(hash).toString(16);
    }

    /**
     * Check values alignment with North Star principles
     */
    _checkValuesAlignment(app) {
        const alignment = {
            checked: true,
            timestamp: Date.now(),
            results: {}
        };

        // Check against each principle
        for (const [key, principle] of Object.entries(NORTH_STAR_PRINCIPLES)) {
            const result = this._checkPrinciple(app, principle);
            alignment.results[key] = {
                name: principle.name,
                aligned: result.aligned,
                notes: result.notes
            };
        }

        // Overall alignment score
        const principles = Object.values(alignment.results);
        const alignedCount = principles.filter(p => p.aligned).length;
        alignment.overall_score = alignedCount / principles.length;
        alignment.fully_aligned = alignment.overall_score === 1.0;

        return alignment;
    }

    /**
     * Check if app aligns with a specific principle
     */
    _checkPrinciple(app, principle) {
        const appString = JSON.stringify(app).toLowerCase();
        let violations = [];
        let alignments = [];

        // Check for violations
        for (const violation of (principle.violated_by || [])) {
            if (appString.includes(violation.toLowerCase().replace(/_/g, ' '))) {
                violations.push(violation);
            }
        }

        // Check for alignments
        for (const enforcement of (principle.enforced_by || [])) {
            if (appString.includes(enforcement.toLowerCase().replace(/_/g, ' '))) {
                alignments.push(enforcement);
            }
        }

        return {
            aligned: violations.length === 0,
            notes: violations.length > 0
                ? `Potential violations: ${violations.join(', ')}`
                : alignments.length > 0
                    ? `Aligns through: ${alignments.join(', ')}`
                    : 'No specific alignment detected'
        };
    }

    /**
     * Get available export formats
     */
    _getAvailableFormats() {
        return [
            {
                format: 'pwa',
                name: 'Progressive Web App',
                description: 'Works on any device, installable',
                deployable_to: ['https', 'ipfs', 'ipns']
            },
            {
                format: 'static',
                name: 'Static Site',
                description: 'HTML/CSS/JS bundle',
                deployable_to: ['https', 'ipfs', 'arweave', 'file']
            },
            {
                format: 'ipfs_package',
                name: 'IPFS Package',
                description: 'Ready for decentralized deployment',
                deployable_to: ['ipfs', 'ipns']
            },
            {
                format: 'self_contained',
                name: 'Self-Contained HTML',
                description: 'Single file, works offline',
                deployable_to: ['file', 'https']
            }
        ];
    }

    /**
     * Compute manifest hash for integrity
     */
    _computeHash(manifest) {
        const copy = { ...manifest, manifest_hash: null };
        const str = JSON.stringify(copy);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return 'manifest_' + Math.abs(hash).toString(16);
    }

    /**
     * Add a publication location to manifest
     * User calls this after publishing
     */
    addPublicationLocation(manifest, location) {
        const parsed = this._parseLocation(location);
        if (!parsed) {
            return {
                success: false,
                error: 'Invalid location format'
            };
        }

        manifest.published_locations.push({
            protocol: parsed.protocol,
            url: location,
            added_at: Date.now()
        });

        // Recompute hash
        manifest.manifest_hash = this._computeHash(manifest);

        return {
            success: true,
            manifest: manifest
        };
    }

    /**
     * Parse a location URL
     */
    _parseLocation(location) {
        try {
            // Check for IPFS
            if (location.startsWith('ipfs://')) {
                return { protocol: 'ipfs', cid: location.slice(7) };
            }
            if (location.startsWith('ipns://')) {
                return { protocol: 'ipns', name: location.slice(7) };
            }

            // Standard URL
            const url = new URL(location);
            return { protocol: url.protocol.replace(':', ''), host: url.host };
        } catch {
            return null;
        }
    }

    /**
     * Export manifest as shareable format
     */
    exportManifest(manifest) {
        return {
            // JSON for programmatic use
            json: JSON.stringify(manifest, null, 2),

            // Minimal version for embedding
            minimal: {
                name: manifest.name,
                description: manifest.description,
                locations: manifest.published_locations.map(l => l.url),
                values_score: manifest.values_alignment?.overall_score
            },

            // URL-safe encoded version
            encoded: btoa(JSON.stringify(manifest))
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// PUBLICATION GUIDE
// Helps users deploy their apps
// ═══════════════════════════════════════════════════════════════════════════

const PUBLICATION_GUIDES = Object.freeze({
    IPFS: {
        name: 'IPFS (Decentralized)',
        description: 'Censorship-resistant, permanent storage',
        difficulty: 'medium',
        cost: 'free (with pinning service) or self-hosted',
        steps: [
            'Export your app as IPFS Package',
            'Install IPFS Desktop or use a pinning service (Pinata, Infura, web3.storage)',
            'Add your app folder to IPFS',
            'Pin the content to keep it available',
            'Share the CID (Content Identifier)',
            'Update your manifest with the ipfs:// location'
        ],
        links: [
            { name: 'IPFS Desktop', url: 'https://docs.ipfs.io/install/ipfs-desktop/' },
            { name: 'Pinata', url: 'https://pinata.cloud/' },
            { name: 'web3.storage', url: 'https://web3.storage/' }
        ],
        liability_note: 'You are publishing to a decentralized network. Content is your responsibility.'
    },

    VERCEL: {
        name: 'Vercel (Easy Hosting)',
        description: 'Free tier, automatic deploys, global CDN',
        difficulty: 'easy',
        cost: 'free tier available',
        steps: [
            'Export your app as Static Site',
            'Create a Vercel account',
            'Connect your project or drag-drop the export folder',
            'Vercel deploys automatically',
            'Update your manifest with the https:// URL'
        ],
        links: [
            { name: 'Vercel', url: 'https://vercel.com/' }
        ],
        liability_note: 'You are the publisher. Vercel is just the host. Content is your responsibility.'
    },

    NETLIFY: {
        name: 'Netlify (Easy Hosting)',
        description: 'Free tier, drag-and-drop deployment',
        difficulty: 'easy',
        cost: 'free tier available',
        steps: [
            'Export your app as Static Site',
            'Create a Netlify account',
            'Drag-drop your export folder',
            'Get your public URL',
            'Update your manifest with the https:// URL'
        ],
        links: [
            { name: 'Netlify', url: 'https://netlify.com/' }
        ],
        liability_note: 'You are the publisher. Content is your responsibility.'
    },

    GITHUB_PAGES: {
        name: 'GitHub Pages (Developer-Friendly)',
        description: 'Free, version controlled, connected to your code',
        difficulty: 'medium',
        cost: 'free',
        steps: [
            'Export your app as Static Site',
            'Create a GitHub repository',
            'Push your export to the repository',
            'Enable GitHub Pages in settings',
            'Update your manifest with the github.io URL'
        ],
        links: [
            { name: 'GitHub Pages Docs', url: 'https://pages.github.com/' }
        ],
        liability_note: 'You are the publisher. GitHub hosts but you are responsible for content.'
    },

    SELF_HOST: {
        name: 'Self-Hosted (Full Control)',
        description: 'Run on your own server, complete sovereignty',
        difficulty: 'advanced',
        cost: 'varies (server cost)',
        steps: [
            'Export your app as Static Site or PWA',
            'Set up a web server (nginx, Apache, or simple static server)',
            'Deploy your files to the server',
            'Configure your domain (optional)',
            'Update your manifest with your URL'
        ],
        links: [
            { name: 'nginx', url: 'https://nginx.org/' },
            { name: 'Caddy', url: 'https://caddyserver.com/' }
        ],
        liability_note: 'Complete control means complete responsibility. You own it all.'
    },

    ARWEAVE: {
        name: 'Arweave (Permanent)',
        description: 'Pay once, stored forever, truly permanent',
        difficulty: 'medium',
        cost: 'one-time payment based on size',
        steps: [
            'Export your app as Static Site',
            'Use ArDrive or Arweave deploy tools',
            'Pay the one-time storage fee',
            'Your app is permanently stored',
            'Update your manifest with the arweave URL'
        ],
        links: [
            { name: 'ArDrive', url: 'https://ardrive.io/' },
            { name: 'Arweave', url: 'https://arweave.org/' }
        ],
        liability_note: 'Permanent means permanent. Cannot be deleted. Be certain before publishing.'
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// DISCOVERY TEMPLATE
// A template for the community to dream a discovery app
// ═══════════════════════════════════════════════════════════════════════════

const DISCOVERY_APP_TEMPLATE = Object.freeze({
    name: 'Discovery App Template',
    description: 'A template for the community to dream their own app discovery platform',

    concept: `
        This is not an app ARCHIVIT builds.
        This is a DREAM for the community to realize.

        Someone will dream an app that:
        ├── Collects manifests from app creators
        ├── Indexes them for search and browse
        ├── Points users to where apps actually live
        ├── Has community governance
        ├── Is forkable if governance fails
        ├── Replaces centralized app stores
        └── Is the first truly grassroots media platform

        YOU could dream this app.
        The tools are here.
        The world needs it.
    `,

    suggested_features: [
        'Manifest submission (anyone can submit)',
        'Category browsing (creativity, utility, social, etc.)',
        'Search by name, description, tags',
        'Filter by values alignment score',
        'Community voting on featured apps',
        'Report mechanism for problematic apps',
        'Fork button (take the whole index and run your own)',
        'No account required to browse',
        'Decentralized storage of index (IPFS/Arweave)'
    ],

    governance_ideas: [
        'DAO-style voting on curation policies',
        'Reputation based on contributions',
        'Quadratic voting for major decisions',
        'Forking as ultimate governance check',
        'Transparency in all moderation decisions'
    ],

    what_it_is_not: [
        'A hosting platform (apps live elsewhere)',
        'A gatekeeper (manifests are metadata)',
        'Owned by ARCHIVIT (community builds this)',
        'The only discovery option (multiple can exist)'
    ],

    call_to_action: `
        If you're reading this, you might be the one to dream this app.

        The world is waiting for grassroots well-intentioned human beings
        to build the platforms that replace extraction with creation.

        The tools exist. The architecture exists.
        All that's needed is someone to dream it.

        Maybe that's you.
    `
});

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const manifestGenerator = new AppManifestGenerator();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    AppManifestGenerator,
    manifestGenerator,
    MANIFEST_VERSION,
    MANIFEST_SCHEMA,
    PUBLICATION_GUIDES,
    DISCOVERY_APP_TEMPLATE
};

export default manifestGenerator;
