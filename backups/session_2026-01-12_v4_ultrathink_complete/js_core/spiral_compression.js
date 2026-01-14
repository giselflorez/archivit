/**
 * SPIRAL COMPRESSION ENGINE
 * ==========================
 * Golden Ratio-Based Adaptive Data Compression
 *
 * Uses the golden spiral to compress behavioral data while preserving
 * conceptual integrity. The compression ratio follows φ (1.618...) at
 * each level, meaning older/less-accessed data is compressed more while
 * maintaining the ability to expand when needed.
 *
 * PHILOSOPHY:
 * - Compress detail, preserve meaning
 * - Older data = more compressed
 * - Frequently accessed = less compressed
 * - Never delete, only compress
 * - Expand on demand, re-compress when idle
 */

import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const COMPRESSION_CONFIG = Object.freeze({
    // Golden ratio for compression levels
    PHI: PHI,
    PHI_INVERSE: 1 / PHI,  // 0.618...

    // Ring size limits (bytes)
    RING_SIZES: Object.freeze({
        CORE: 50 * 1024,        // 50KB - always loaded
        RING_1: 200 * 1024,     // 200KB - hot cache
        RING_2: 1024 * 1024,    // 1MB - warm storage
        RING_3: 5 * 1024 * 1024 // 5MB - cold storage
        // RING_4+ on IPFS
    }),

    // Platform tier configurations
    TIERS: Object.freeze({
        FULL: {
            name: 'Full',
            maxLocalStorage: Infinity,
            ringsLocal: 7,
            ramBudget: 500 * 1024 * 1024,
            features: 'all'
        },
        STANDARD: {
            name: 'Standard',
            maxLocalStorage: 100 * 1024 * 1024,
            ringsLocal: 3,
            ramBudget: 200 * 1024 * 1024,
            features: 'core'
        },
        LITE: {
            name: 'Lite',
            maxLocalStorage: 20 * 1024 * 1024,
            ringsLocal: 1,
            ramBudget: 50 * 1024 * 1024,
            features: 'essential'
        },
        MICRO: {
            name: 'Micro',
            maxLocalStorage: 5 * 1024 * 1024,
            ringsLocal: 0,
            ramBudget: 20 * 1024 * 1024,
            features: 'minimal'
        }
    }),

    // Behavioral drift thresholds
    DRIFT: Object.freeze({
        CORE_BELIEF_INERTIA: 0.001,     // Very slow change
        PREFERENCE_INERTIA: 0.01,
        INTEREST_INERTIA: 0.05,
        BEHAVIOR_INERTIA: 0.1,
        CONTEXT_INERTIA: 1.0            // Instant
    }),

    // Compression timing
    RECENCY_DECAY_DAYS: 30,
    IDLE_RECOMPRESS_MS: 5 * 60 * 1000,  // 5 minutes

    // IPFS settings
    IPFS_BLOCK_SIZE: 256 * 1024  // 256KB blocks
});

// ═══════════════════════════════════════════════════════════════════════════
// SPIRAL COMPRESSION ENGINE
// ═══════════════════════════════════════════════════════════════════════════

class SpiralCompressionEngine {
    constructor(tier = 'STANDARD') {
        this.tier = COMPRESSION_CONFIG.TIERS[tier] || COMPRESSION_CONFIG.TIERS.STANDARD;
        this.loadedRings = new Map();
        this.compressionCache = new Map();
        this.expansionTimers = new Map();
        this.ipfsGateway = null;

        // Statistics
        this.stats = {
            compressions: 0,
            expansions: 0,
            bytesCompressed: 0,
            bytesExpanded: 0
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // COMPRESSION LEVEL CALCULATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Calculate compression level for a data point
     * Uses golden ratio logarithm
     *
     * @param {Object} metadata - Data point metadata
     * @returns {number} Compression level (0 = full detail, higher = more compressed)
     */
    calculateCompressionLevel(metadata) {
        const {
            age = 0,              // Days since creation
            frequency = 0.5,      // Access frequency (0-1)
            significance = 0.5,   // Importance score (0-1)
            type = 'generic'      // Data type for inertia
        } = metadata;

        // Recency boost (exponential decay)
        const recencyBoost = Math.exp(-age / COMPRESSION_CONFIG.RECENCY_DECAY_DAYS);

        // Combined score
        const retentionScore = frequency * significance * recencyBoost;

        // Prevent division by zero
        if (retentionScore <= 0) return 7;  // Maximum compression

        // Golden ratio logarithm
        // log_φ(age / retention) = ln(age/retention) / ln(φ)
        const ratio = Math.max(1, age) / (retentionScore + 0.01);
        const level = Math.floor(Math.log(ratio) / Math.log(PHI));

        // Clamp to valid range
        return Math.max(0, Math.min(7, level));
    }

    /**
     * Get retention percentage for a compression level
     * Each level retains φ^(-level) of the detail
     *
     * @param {number} level - Compression level
     * @returns {number} Retention percentage (0-1)
     */
    getRetentionPercentage(level) {
        return Math.pow(COMPRESSION_CONFIG.PHI_INVERSE, level);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // COMPRESSION OPERATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Compress data to a specific level
     * Preserves conceptual structure, reduces detail
     *
     * @param {Object} data - Data to compress
     * @param {number} targetLevel - Target compression level
     * @returns {Object} Compressed data
     */
    compress(data, targetLevel) {
        if (targetLevel === 0) return data;  // No compression needed

        const retention = this.getRetentionPercentage(targetLevel);

        const compressed = {
            _compressed: true,
            _level: targetLevel,
            _retention: retention,
            _originalSize: this._estimateSize(data),
            _timestamp: Date.now()
        };

        // Compress based on data type
        if (Array.isArray(data)) {
            compressed.data = this._compressArray(data, retention);
        } else if (typeof data === 'object' && data !== null) {
            compressed.data = this._compressObject(data, retention, targetLevel);
        } else {
            // Primitives don't compress
            compressed.data = data;
        }

        compressed._compressedSize = this._estimateSize(compressed.data);

        this.stats.compressions++;
        this.stats.bytesCompressed += compressed._originalSize - compressed._compressedSize;

        return compressed;
    }

    /**
     * Compress an array by retaining most significant elements
     */
    _compressArray(arr, retention) {
        if (arr.length === 0) return [];

        const keepCount = Math.max(1, Math.ceil(arr.length * retention));

        // If items have significance scores, sort by them
        if (arr[0] && typeof arr[0] === 'object' && 'significance' in arr[0]) {
            const sorted = [...arr].sort((a, b) => b.significance - a.significance);
            return sorted.slice(0, keepCount);
        }

        // Otherwise, use golden angle sampling
        // This preserves distribution while reducing count
        const result = [];
        const step = GOLDEN_ANGLE / 360 * arr.length;

        for (let i = 0; i < keepCount; i++) {
            const index = Math.floor((i * step) % arr.length);
            if (!result.includes(arr[index])) {
                result.push(arr[index]);
            }
        }

        // Fill remaining with sequential if needed
        while (result.length < keepCount) {
            const next = arr.find(item => !result.includes(item));
            if (next) result.push(next);
            else break;
        }

        return result;
    }

    /**
     * Compress an object by reducing nested depth and detail
     */
    _compressObject(obj, retention, level) {
        const result = {};

        // Get keys sorted by importance (if available) or alphabetically
        const keys = Object.keys(obj).sort((a, b) => {
            const aImportance = this._getKeyImportance(a, obj[a]);
            const bImportance = this._getKeyImportance(b, obj[b]);
            return bImportance - aImportance;
        });

        // Keep top keys based on retention
        const keepCount = Math.max(1, Math.ceil(keys.length * retention));
        const keptKeys = keys.slice(0, keepCount);

        for (const key of keptKeys) {
            const value = obj[key];

            if (Array.isArray(value)) {
                result[key] = this._compressArray(value, retention);
            } else if (typeof value === 'object' && value !== null) {
                // Recursive compression with increased level
                result[key] = this._compressObject(value, retention * 0.8, level + 1);
            } else if (typeof value === 'number') {
                // Reduce numeric precision at higher compression
                const precision = Math.max(0, 4 - level);
                result[key] = Number(value.toFixed(precision));
            } else {
                result[key] = value;
            }
        }

        // Add summary of dropped keys
        if (keys.length > keepCount) {
            result._droppedKeys = keys.slice(keepCount).length;
            result._droppedSummary = this._summarizeDropped(obj, keys.slice(keepCount));
        }

        return result;
    }

    /**
     * Get importance score for a key
     */
    _getKeyImportance(key, value) {
        // Priority keys (always important)
        const priorityKeys = ['id', 'type', 'timestamp', 'weight', 'score', 'name'];
        if (priorityKeys.includes(key)) return 100;

        // Genesis/core keys
        if (key.startsWith('genesis') || key.startsWith('core')) return 90;

        // Size-based importance (larger = more important to compress well)
        const size = this._estimateSize(value);
        return Math.min(80, size / 100);
    }

    /**
     * Create summary of dropped data for potential recovery
     */
    _summarizeDropped(obj, droppedKeys) {
        return {
            keys: droppedKeys,
            types: droppedKeys.map(k => typeof obj[k]),
            totalSize: droppedKeys.reduce((sum, k) => sum + this._estimateSize(obj[k]), 0)
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EXPANSION OPERATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Expand compressed data (load from higher detail source)
     *
     * @param {Object} compressed - Compressed data
     * @param {Object} fullSource - Original full data (or IPFS reference)
     * @returns {Object} Expanded data
     */
    async expand(compressed, fullSource = null) {
        if (!compressed._compressed) return compressed;

        let expanded;

        if (fullSource) {
            // Use provided full source
            expanded = fullSource;
        } else if (compressed._ipfsRef) {
            // Load from IPFS
            expanded = await this._loadFromIPFS(compressed._ipfsRef);
        } else {
            // Cannot fully expand, return decompressed approximation
            expanded = this._approximateExpand(compressed);
        }

        this.stats.expansions++;
        this.stats.bytesExpanded += compressed._originalSize || 0;

        // Schedule re-compression after idle
        this._scheduleRecompression(compressed._ipfsRef || 'local', expanded);

        return expanded;
    }

    /**
     * Approximate expansion when full source unavailable
     * Uses interpolation and pattern recognition
     */
    _approximateExpand(compressed) {
        const data = compressed.data;

        if (Array.isArray(data)) {
            // Can't truly expand array, return with marker
            return {
                data: data,
                _approximated: true,
                _originalCount: Math.ceil(data.length / compressed._retention)
            };
        }

        if (typeof data === 'object' && data !== null) {
            const result = { ...data };

            // Restore numeric precision estimate
            for (const [key, value] of Object.entries(result)) {
                if (typeof value === 'number') {
                    // Add small random variation to represent lost precision
                    result[key] = value;  // Can't truly restore, keep as-is
                }
            }

            // Mark as approximated
            result._approximated = true;
            if (data._droppedKeys) {
                result._missingKeys = data._droppedKeys;
            }

            return result;
        }

        return data;
    }

    /**
     * Schedule re-compression after idle period
     */
    _scheduleRecompression(id, data) {
        // Clear existing timer
        if (this.expansionTimers.has(id)) {
            clearTimeout(this.expansionTimers.get(id));
        }

        // Set new timer
        const timer = setTimeout(() => {
            this.expansionTimers.delete(id);
            // Re-compress and store
            const level = this.calculateCompressionLevel({
                age: 0,
                frequency: 0.5,
                significance: 0.5
            });
            const recompressed = this.compress(data, level);
            this.compressionCache.set(id, recompressed);
        }, COMPRESSION_CONFIG.IDLE_RECOMPRESS_MS);

        this.expansionTimers.set(id, timer);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // BEHAVIORAL DRIFT DETECTION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Detect and apply behavioral drift
     *
     * @param {Object} currentPatterns - Recent behavioral patterns
     * @param {Object} storedCentroid - Historical centroid
     * @param {string} layer - Which layer (core_belief, preference, interest, behavior, context)
     * @returns {Object} Updated centroid and drift info
     */
    detectDrift(currentPatterns, storedCentroid, layer = 'interest') {
        // Get inertia for this layer
        const inertiaMap = {
            core_belief: COMPRESSION_CONFIG.DRIFT.CORE_BELIEF_INERTIA,
            preference: COMPRESSION_CONFIG.DRIFT.PREFERENCE_INERTIA,
            interest: COMPRESSION_CONFIG.DRIFT.INTEREST_INERTIA,
            behavior: COMPRESSION_CONFIG.DRIFT.BEHAVIOR_INERTIA,
            context: COMPRESSION_CONFIG.DRIFT.CONTEXT_INERTIA
        };
        const inertia = inertiaMap[layer] || COMPRESSION_CONFIG.DRIFT.INTEREST_INERTIA;

        // Calculate current centroid from patterns
        const currentCentroid = this._calculateCentroid(currentPatterns);

        // Calculate drift vector
        const drift = {};
        let driftMagnitude = 0;

        for (const key of Object.keys(currentCentroid)) {
            const current = currentCentroid[key] || 0;
            const stored = storedCentroid[key] || 0;
            const difference = current - stored;

            drift[key] = difference;
            driftMagnitude += difference * difference;
        }
        driftMagnitude = Math.sqrt(driftMagnitude);

        // Calculate adjustment
        const adjustmentRate = Math.min(driftMagnitude * inertia, inertia);

        // Apply adjustment to create new centroid
        const newCentroid = {};
        for (const key of Object.keys({ ...currentCentroid, ...storedCentroid })) {
            const stored = storedCentroid[key] || 0;
            const driftValue = drift[key] || 0;

            if (driftMagnitude > 0.1) {
                // Significant drift - move toward current
                newCentroid[key] = stored + (driftValue * adjustmentRate);
            } else {
                // Minor drift - slightly reinforce existing
                const current = currentCentroid[key] || 0;
                newCentroid[key] = stored * 0.99 + current * 0.01;
            }
        }

        return {
            newCentroid: newCentroid,
            driftMagnitude: driftMagnitude,
            driftVector: drift,
            adjustmentApplied: adjustmentRate,
            isSignificant: driftMagnitude > 0.1,
            layer: layer,
            inertia: inertia
        };
    }

    /**
     * Calculate centroid from pattern collection
     */
    _calculateCentroid(patterns) {
        if (!patterns || Object.keys(patterns).length === 0) {
            return {};
        }

        const centroid = {};
        let count = 0;

        // Handle array of patterns
        if (Array.isArray(patterns)) {
            for (const pattern of patterns) {
                for (const [key, value] of Object.entries(pattern)) {
                    if (typeof value === 'number') {
                        centroid[key] = (centroid[key] || 0) + value;
                    }
                }
                count++;
            }

            // Average
            for (const key of Object.keys(centroid)) {
                centroid[key] /= count;
            }
        } else {
            // Single pattern object
            for (const [key, value] of Object.entries(patterns)) {
                if (typeof value === 'number') {
                    centroid[key] = value;
                }
            }
        }

        return centroid;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // RING MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Organize data into compression rings
     *
     * @param {Object} seedData - Full seed data
     * @returns {Object} Organized ring structure
     */
    organizeIntoRings(seedData) {
        const rings = {
            core: {},
            ring1: {},
            ring2: {},
            ring3: {},
            ipfs: []
        };

        // CORE: Essential always-loaded data
        rings.core = {
            genesis: seedData.genesis,
            algorithm: seedData.algorithm,
            currentCentroid: this._extractCurrentCentroid(seedData),
            topTopics: this._extractTopTopics(seedData.knowledge?.topics, 10),
            activeConnections: this._extractTopConnections(seedData.knowledge?.entities?.people, 20),
            trajectory: seedData.meta?.pqs_state?.centroid || null
        };

        // RING 1: Hot cache (last 30 days)
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
        rings.ring1 = {
            recentBehavioral: this._filterByTime(seedData.behavioral, thirtyDaysAgo),
            topTopics: this._extractTopTopics(seedData.knowledge?.topics, 50),
            creationDNA: seedData.creation_dna,
            relationships: this._filterByTime(seedData.knowledge?.entities, thirtyDaysAgo)
        };

        // RING 2: Warm storage (90 days, compressed)
        const ninetyDaysAgo = Date.now() - (90 * 24 * 60 * 60 * 1000);
        rings.ring2 = this.compress({
            behavioral: this._filterByTime(seedData.behavioral, ninetyDaysAgo),
            knowledge: seedData.knowledge,
            algorithmHistory: seedData.meta?.algorithmHistory || []
        }, 2);

        // RING 3: Cold storage (all historical, more compressed)
        rings.ring3 = this.compress({
            fullBehavioral: seedData.behavioral,
            fullKnowledge: seedData.knowledge,
            fullHistory: seedData.meta?.consent_log || []
        }, 4);

        // IPFS: Anything beyond Ring 3 limits
        const ring3Size = this._estimateSize(rings.ring3);
        if (ring3Size > COMPRESSION_CONFIG.RING_SIZES.RING_3) {
            const overflow = this.compress(rings.ring3, 6);
            overflow._ipfsCandidate = true;
            rings.ipfs.push(overflow);
            rings.ring3 = { _ipfsRef: 'pending', _summary: overflow._droppedSummary };
        }

        return rings;
    }

    /**
     * Extract current behavioral centroid
     */
    _extractCurrentCentroid(seedData) {
        const behavioral = seedData.behavioral || {};

        return {
            temporalCenter: this._arrayCenter(behavioral.temporal?.active_hours),
            linguisticAvg: behavioral.linguistic?.avg_sentence_length || 0,
            aestheticBrightness: behavioral.aesthetic?.brightness_preference || 0.5,
            socialRole: behavioral.social?.community_role || 'observer'
        };
    }

    /**
     * Extract top N topics by weight
     */
    _extractTopTopics(topics, n) {
        if (!topics || typeof topics !== 'object') return {};

        const sorted = Object.entries(topics)
            .sort((a, b) => (b[1].weight || 0) - (a[1].weight || 0))
            .slice(0, n);

        return Object.fromEntries(sorted);
    }

    /**
     * Extract top N connections by frequency
     */
    _extractTopConnections(people, n) {
        if (!people || typeof people !== 'object') return {};

        const sorted = Object.entries(people)
            .sort((a, b) => (b[1].frequency || 0) - (a[1].frequency || 0))
            .slice(0, n);

        return Object.fromEntries(sorted);
    }

    /**
     * Filter object by timestamp fields
     */
    _filterByTime(obj, since) {
        if (!obj || typeof obj !== 'object') return obj;

        const result = {};
        for (const [key, value] of Object.entries(obj)) {
            if (value && typeof value === 'object') {
                if (value.timestamp && value.timestamp < since) continue;
                if (value.last_touched && value.last_touched < since) continue;
            }
            result[key] = value;
        }
        return result;
    }

    /**
     * Calculate center of numeric array
     */
    _arrayCenter(arr) {
        if (!Array.isArray(arr) || arr.length === 0) return 0;
        const sum = arr.reduce((a, b) => a + b, 0);
        return sum / arr.length;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // IPFS OPERATIONS (Stubs for Integration)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Upload compressed block to IPFS
     *
     * @param {Object} data - Data to upload
     * @returns {string} IPFS CID
     */
    async uploadToIPFS(data) {
        // Stub - would integrate with actual IPFS
        const mockCID = 'Qm' + Math.random().toString(36).substring(2, 15);

        console.log('[SpiralCompression] Would upload to IPFS:', {
            size: this._estimateSize(data),
            cid: mockCID
        });

        return mockCID;
    }

    /**
     * Load compressed block from IPFS
     *
     * @param {string} cid - IPFS CID
     * @returns {Object} Retrieved data
     */
    async _loadFromIPFS(cid) {
        // Stub - would integrate with actual IPFS
        console.log('[SpiralCompression] Would load from IPFS:', cid);

        return {
            _error: 'IPFS not configured',
            _cid: cid
        };
    }

    /**
     * Configure IPFS gateway
     *
     * @param {string} gateway - IPFS gateway URL
     */
    setIPFSGateway(gateway) {
        this.ipfsGateway = gateway;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UTILITIES
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Estimate size of data in bytes
     */
    _estimateSize(data) {
        if (data === null || data === undefined) return 0;
        if (typeof data === 'string') return data.length * 2;
        if (typeof data === 'number') return 8;
        if (typeof data === 'boolean') return 4;

        try {
            return JSON.stringify(data).length * 2;
        } catch {
            return 1000;  // Default estimate
        }
    }

    /**
     * Get compression statistics
     */
    getStats() {
        return {
            ...this.stats,
            tier: this.tier.name,
            loadedRings: this.loadedRings.size,
            cachedCompressions: this.compressionCache.size,
            activeExpansions: this.expansionTimers.size
        };
    }

    /**
     * Detect current platform tier based on device capabilities
     */
    static detectTier() {
        // Check available storage
        if (navigator.storage && navigator.storage.estimate) {
            return navigator.storage.estimate().then(estimate => {
                const availableGB = (estimate.quota || 0) / (1024 * 1024 * 1024);

                if (availableGB > 10) return 'FULL';
                if (availableGB > 1) return 'STANDARD';
                if (availableGB > 0.1) return 'LITE';
                return 'MICRO';
            });
        }

        // Fallback: check device memory
        if (navigator.deviceMemory) {
            if (navigator.deviceMemory >= 8) return Promise.resolve('FULL');
            if (navigator.deviceMemory >= 4) return Promise.resolve('STANDARD');
            if (navigator.deviceMemory >= 2) return Promise.resolve('LITE');
            return Promise.resolve('MICRO');
        }

        // Default to STANDARD
        return Promise.resolve('STANDARD');
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// PROGRESSIVE LOADER
// ═══════════════════════════════════════════════════════════════════════════

class ProgressiveLoader {
    constructor(compressionEngine) {
        this.engine = compressionEngine;
        this.loadedData = new Map();
        this.loadingPromises = new Map();
    }

    /**
     * Load data progressively
     * Returns core immediately, loads rings in background
     */
    async loadProgressive(rings) {
        // Step 1: Load core immediately (blocking)
        this.loadedData.set('core', rings.core);

        // Step 2: Start background loads
        this._backgroundLoad('ring1', rings.ring1);
        this._backgroundLoad('ring2', rings.ring2);
        this._backgroundLoad('ring3', rings.ring3);

        // Return core immediately
        return {
            core: rings.core,
            loading: ['ring1', 'ring2', 'ring3'],
            getAsync: (ring) => this.getRing(ring)
        };
    }

    async _backgroundLoad(name, data) {
        const promise = new Promise(resolve => {
            // Simulate async load with small delay
            setTimeout(() => {
                if (data._compressed) {
                    // Expand if needed
                    this.engine.expand(data).then(expanded => {
                        this.loadedData.set(name, expanded);
                        resolve(expanded);
                    });
                } else {
                    this.loadedData.set(name, data);
                    resolve(data);
                }
            }, 10);
        });

        this.loadingPromises.set(name, promise);
        return promise;
    }

    /**
     * Get a specific ring (waits if still loading)
     */
    async getRing(name) {
        if (this.loadedData.has(name)) {
            return this.loadedData.get(name);
        }

        if (this.loadingPromises.has(name)) {
            return this.loadingPromises.get(name);
        }

        return null;
    }

    /**
     * Check if a ring is loaded
     */
    isLoaded(name) {
        return this.loadedData.has(name);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    SpiralCompressionEngine,
    ProgressiveLoader,
    COMPRESSION_CONFIG
};

export default SpiralCompressionEngine;
