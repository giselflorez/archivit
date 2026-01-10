/**
 * SEED-PQS INTEGRATION MODULE
 * ============================
 * The Bridge Between Soul and Mathematics
 *
 * This module unifies the SeedProfileEngine with the PiQuadraticSeed,
 * ensuring ALL behavioral data flows through the π-quadratic transform
 * before storage. This creates ecosystem-locked encoding that can only
 * be decoded with the user's genesis offset.
 *
 * ARCHITECTURE:
 * ┌─────────────────────────────────────────────────────────────┐
 * │                     USER INTERACTION                        │
 * │                          │                                  │
 * │                          ▼                                  │
 * │                  ┌───────────────┐                          │
 * │                  │    CONSENT    │                          │
 * │                  │    GATEWAY    │                          │
 * │                  └───────┬───────┘                          │
 * │                          │                                  │
 * │                          ▼                                  │
 * │           ┌──────────────────────────────┐                  │
 * │           │      PQS ENCODING LAYER      │                  │
 * │           │   (π-Quadratic Transform)    │                  │
 * │           │                              │                  │
 * │           │  raw → normalize → rotate    │                  │
 * │           │    → quadratic → compress    │                  │
 * │           └──────────────┬───────────────┘                  │
 * │                          │                                  │
 * │                          ▼                                  │
 * │                  ┌───────────────┐                          │
 * │                  │     SEED      │                          │
 * │                  │   (Encoded)   │                          │
 * │                  └───────────────┘                          │
 * │                          │                                  │
 * │              ┌───────────┴───────────┐                      │
 * │              │                       │                      │
 * │              ▼                       ▼                      │
 * │    ┌─────────────────┐     ┌─────────────────┐              │
 * │    │   PREDICTIONS   │     │   ALGORITHM     │              │
 * │    │  (Optimal Path) │     │   (Ranking)     │              │
 * │    └─────────────────┘     └─────────────────┘              │
 * └─────────────────────────────────────────────────────────────┘
 */

import { SeedProfileEngine, SeedCrypto, SEED_VERSION } from './seed_profile.js';
import { PiQuadraticSeed, PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';

/**
 * UNIFIED SEED ENGINE
 * Combines SeedProfile + PQS into a single sovereign data structure
 */
class UnifiedSeedEngine {
    constructor() {
        // Core components
        this.seedEngine = new SeedProfileEngine();
        this.pqs = null;

        // State
        this.isInitialized = false;
        this.isPQSLinked = false;

        // Configuration
        this.config = {
            encodeAllBehavioral: true,      // Encode all behavioral data through PQS
            storeRawAlongside: false,        // Keep raw values (disable for max privacy)
            predictionThreshold: 10,         // Min data points for predictions
            autoOptimizeAlgorithm: true      // Auto-adjust algorithm based on predictions
        };

        // Event listeners
        this.listeners = new Map();

        // Bind seed engine events
        this._bindSeedEvents();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Initialize the unified engine
     * Creates or loads seed, then links PQS
     */
    async initialize() {
        // Initialize base seed engine
        await this.seedEngine.initialize();

        // Link PQS using genesis entropy as offset
        await this._linkPQS();

        this.isInitialized = true;
        this._emit('initialized', {
            seed: this.seedEngine.seed,
            pqs: {
                offset: this.pqs.offset,
                vertex: this.pqs.vertex,
                coefficients: this.pqs.coefficients
            }
        });

        return this;
    }

    /**
     * Create new seed with PQS integration
     */
    async createNew() {
        const result = await this.seedEngine.createNewSeed();
        await this._linkPQS();

        // Store PQS genesis in seed for recovery
        this.seedEngine.seed.genesis.pqs_offset = this.pqs.offset;
        await this.seedEngine._saveToStorage();

        this._emit('created', {
            key: result.key,
            pqsVertex: this.pqs.vertex
        });

        return result;
    }

    /**
     * Unlock existing seed and restore PQS state
     */
    async unlock(keyString) {
        const success = await this.seedEngine.unlock(keyString);

        if (success) {
            // Restore PQS from genesis
            const storedOffset = this.seedEngine.seed.genesis.pqs_offset;
            this.pqs = new PiQuadraticSeed(storedOffset);
            this.isPQSLinked = true;

            // Restore encoding history if available
            if (this.seedEngine.seed.meta.pqs_state) {
                this._restorePQSState(this.seedEngine.seed.meta.pqs_state);
            }

            this._emit('unlocked', { pqsRestored: true });
        }

        return success;
    }

    /**
     * Link PQS to seed using genesis entropy
     */
    async _linkPQS() {
        if (!this.seedEngine.seed) {
            throw new Error('Seed must be initialized before linking PQS');
        }

        // Check if PQS offset already exists in genesis
        if (this.seedEngine.seed.genesis.pqs_offset) {
            this.pqs = new PiQuadraticSeed(this.seedEngine.seed.genesis.pqs_offset);
        } else {
            // Derive PQS offset from entropy seed
            const entropyHash = this._hashEntropy(this.seedEngine.seed.genesis.entropy_seed);
            this.pqs = new PiQuadraticSeed(entropyHash);

            // Store in genesis (only writable before lock)
            this.seedEngine.seed.genesis.pqs_offset = this.pqs.offset;
        }

        this.isPQSLinked = true;

        // Initialize PQS state storage in meta
        if (!this.seedEngine.seed.meta.pqs_state) {
            this.seedEngine.seed.meta.pqs_state = {
                centroid: null,
                vectorCount: 0,
                lastPrediction: null
            };
        }
    }

    _hashEntropy(entropy) {
        let hash = 0;
        for (let i = 0; i < entropy.length; i++) {
            const char = entropy.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        // Limit to valid PQS offset range
        return Math.abs(hash) % 900;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // CONSENT GATEWAY (With PQS Encoding)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Queue data for consent with PQS preview
     * Shows user what their data would look like encoded
     */
    queueForConsent(data) {
        // Generate PQS preview (what encoding would produce)
        const pqsPreview = this._generatePQSPreview(data);

        // Add preview to data
        const enrichedData = {
            ...data,
            pqs_preview: pqsPreview,
            preview: {
                ...data.preview,
                encoded_summary: pqsPreview.summary,
                distance_from_optimal: pqsPreview.avgVertexDistance
            }
        };

        return this.seedEngine.queueForConsent(enrichedData);
    }

    /**
     * Generate preview of PQS encoding without committing
     */
    _generatePQSPreview(data) {
        if (!this.isPQSLinked) return null;

        const patterns = data.patterns || {};
        const previews = [];
        let totalVertexDistance = 0;
        let count = 0;

        // Encode each pattern dimension
        for (const [dim, value] of Object.entries(patterns)) {
            if (typeof value === 'number') {
                const encoded = this.pqs.encode(value, dim);
                previews.push({
                    dimension: dim,
                    original: value,
                    encoded_magnitude: encoded.compressed.magnitude,
                    vertex_distance: encoded.vertexDistance,
                    trajectory: encoded.trajectory
                });
                totalVertexDistance += encoded.vertexDistance;
                count++;
            }
        }

        return {
            previews: previews,
            avgVertexDistance: count > 0 ? totalVertexDistance / count : null,
            summary: this._generateEncodingSummary(previews),
            prediction: this.pqs.encodingHistory.length >= this.config.predictionThreshold
                ? this.pqs.predictOptimalPath()
                : null
        };
    }

    _generateEncodingSummary(previews) {
        if (previews.length === 0) return 'No encodable patterns detected';

        const approaching = previews.filter(p => p.trajectory === 'approaching_optimal').length;
        const departing = previews.filter(p => p.trajectory === 'departing_optimal').length;

        if (approaching > departing) {
            return `Moving toward optimal state (${approaching}/${previews.length} dimensions improving)`;
        } else if (departing > approaching) {
            return `Moving away from optimal (${departing}/${previews.length} dimensions declining)`;
        } else {
            return `Stable state (balanced trajectory)`;
        }
    }

    /**
     * Approve item and encode through PQS
     */
    async approveItem(itemId, modifications = null) {
        const item = this.seedEngine.pendingQueue.find(i => i.id === itemId);
        if (!item) return false;

        // Encode patterns through PQS before storage
        if (this.config.encodeAllBehavioral && item.extracted_patterns) {
            item.extracted_patterns = this._encodePatterns(item.extracted_patterns);
        }

        const success = await this.seedEngine.approveItem(itemId, modifications);

        if (success) {
            // Update PQS state in meta
            this._savePQSState();

            // Check if we should auto-optimize algorithm
            if (this.config.autoOptimizeAlgorithm) {
                await this._autoOptimizeAlgorithm();
            }

            this._emit('approved_with_encoding', {
                itemId,
                encodingCount: this.pqs.encodingHistory.length,
                currentVertex: this.pqs.behaviorAccumulator.centroid
            });
        }

        return success;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PQS ENCODING
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Encode patterns through PQS
     */
    _encodePatterns(patterns) {
        const encoded = {};

        for (const [key, value] of Object.entries(patterns)) {
            if (typeof value === 'number') {
                const pqsResult = this.pqs.encode(value, key);
                encoded[key] = this.config.storeRawAlongside
                    ? { raw: value, encoded: pqsResult }
                    : pqsResult;
            } else if (Array.isArray(value)) {
                encoded[key] = value.map((v, i) => {
                    if (typeof v === 'number') {
                        return this.pqs.encode(v, `${key}_${i}`);
                    }
                    return v;
                });
            } else if (typeof value === 'object' && value !== null) {
                encoded[key] = this._encodePatterns(value);
            } else {
                encoded[key] = value;
            }
        }

        return encoded;
    }

    /**
     * Manually encode a value (for direct API use)
     */
    encode(value, dimension = 'generic') {
        if (!this.isPQSLinked) {
            throw new Error('PQS must be linked before encoding');
        }
        return this.pqs.encode(value, dimension);
    }

    /**
     * Decode a value (only works with correct genesis)
     */
    decode(encodedValue) {
        if (!this.isPQSLinked) {
            throw new Error('PQS must be linked before decoding');
        }
        return this.pqs.decode(encodedValue);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PREDICTIONS & RECOMMENDATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get predictions for optimal path
     */
    getPredictions() {
        if (!this.isPQSLinked) return null;

        const prediction = this.pqs.predictOptimalPath();

        // Store prediction in meta
        this.seedEngine.seed.meta.pqs_state.lastPrediction = {
            timestamp: Date.now(),
            confidence: prediction.confidence,
            recommendations: prediction.recommendations?.length || 0
        };

        return prediction;
    }

    /**
     * Get personalized recommendations based on behavioral trajectory
     */
    getRecommendations() {
        const prediction = this.getPredictions();

        if (!prediction || prediction.confidence < 0.3) {
            return {
                available: false,
                reason: 'Insufficient behavioral data for recommendations',
                dataNeeded: this.config.predictionThreshold - this.pqs.encodingHistory.length
            };
        }

        return {
            available: true,
            recommendations: prediction.recommendations,
            optimalState: prediction.optimalState,
            currentDistance: this._calculateCurrentDistance(),
            trajectory: prediction.trajectory
        };
    }

    _calculateCurrentDistance() {
        const centroid = this.pqs.behaviorAccumulator.centroid;
        const vertex = this.pqs.vertex;

        if (!centroid) return null;

        return Math.sqrt(
            Math.pow(centroid.x - vertex.x, 2) +
            Math.pow(centroid.y - vertex.y, 2)
        );
    }

    /**
     * Auto-optimize algorithm weights based on predictions
     */
    async _autoOptimizeAlgorithm() {
        const prediction = this.getPredictions();

        if (!prediction || prediction.confidence < 0.5) return;

        // Analyze which content types lead toward optimal
        const trajectory = prediction.trajectory;

        if (trajectory.angleToOptimal !== undefined) {
            const angleDiff = Math.abs(trajectory.angleToOptimal - trajectory.angle);

            // If user is moving away from optimal, adjust discovery mode
            if (angleDiff > 0.5) {
                const currentMode = this.seedEngine.seed.algorithm.discovery_mode;

                // Suggest more exploration if stuck
                if (currentMode === 'familiar' && angleDiff > 1.0) {
                    this._emit('algorithm_suggestion', {
                        type: 'discovery_mode',
                        current: currentMode,
                        suggested: 'balanced',
                        reason: 'Behavioral patterns suggest exploration could help'
                    });
                }
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // ALGORITHM INTEGRATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get content ranking with PQS-enhanced relevance
     */
    getRanking(content) {
        const baseRanking = this.seedEngine.getContentRanking();

        if (!this.isPQSLinked || !content.features) {
            return baseRanking;
        }

        // Encode content features
        const encodedFeatures = {};
        for (const [key, value] of Object.entries(content.features)) {
            if (typeof value === 'number') {
                encodedFeatures[key] = this.pqs.encode(value, key);
            }
        }

        // Calculate proximity to user's optimal state
        const optimalProximity = this._calculateOptimalProximity(encodedFeatures);

        return {
            ...baseRanking,
            pqs_enhanced: true,
            optimal_proximity: optimalProximity,
            // Boost content that moves user toward optimal
            optimal_boost: optimalProximity < 0.5 ? 1.0 + (0.5 - optimalProximity) : 1.0
        };
    }

    _calculateOptimalProximity(encodedFeatures) {
        const centroid = this.pqs.behaviorAccumulator.centroid;
        const vertex = this.pqs.vertex;

        if (!centroid) return 1.0;

        let totalDistance = 0;
        let count = 0;

        for (const encoded of Object.values(encodedFeatures)) {
            if (encoded && encoded.piRotated !== undefined) {
                const contentPoint = { x: encoded.piRotated, y: encoded.quadratic };
                const distToVertex = Math.sqrt(
                    Math.pow(contentPoint.x - vertex.x, 2) +
                    Math.pow(contentPoint.y - vertex.y, 2)
                );
                totalDistance += distToVertex;
                count++;
            }
        }

        return count > 0 ? totalDistance / count : 1.0;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // STATE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════

    _savePQSState() {
        if (!this.seedEngine.seed) return;

        this.seedEngine.seed.meta.pqs_state = {
            centroid: this.pqs.behaviorAccumulator.centroid,
            vectorCount: this.pqs.behaviorAccumulator.vectors.length,
            lastPrediction: this.seedEngine.seed.meta.pqs_state?.lastPrediction || null,
            encodingHistorySnapshot: this.pqs.encodingHistory.slice(-20)
        };

        this.seedEngine._saveToStorage();
    }

    _restorePQSState(state) {
        if (state.centroid) {
            this.pqs.behaviorAccumulator.centroid = state.centroid;
        }

        if (state.encodingHistorySnapshot) {
            this.pqs.encodingHistory = state.encodingHistorySnapshot;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EXPORT & SOVEREIGNTY
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Export complete state (seed + PQS)
     */
    async export() {
        const seedExport = await this.seedEngine.exportSeed();
        const pqsExport = this.pqs.export();

        return {
            version: SEED_VERSION,
            exported_at: Date.now(),
            seed: seedExport,
            pqs: pqsExport,
            unified: true
        };
    }

    /**
     * Export plaintext for full transparency
     */
    exportPlaintext() {
        return {
            seed: this.seedEngine.exportSeedPlaintext(),
            pqs: {
                offset: this.pqs.offset,
                coefficients: this.pqs.coefficients,
                vertex: this.pqs.vertex,
                encodingHistory: this.pqs.encodingHistory,
                behaviorCentroid: this.pqs.behaviorAccumulator.centroid
            }
        };
    }

    /**
     * Generate ownership proof
     */
    generateOwnershipProof() {
        return {
            seed: {
                genesis_hash: this.seedEngine.seed.genesis.root_signature,
                created_at: this.seedEngine.seed.genesis.created_at,
                interactions: this.seedEngine.seed.meta.total_interactions
            },
            pqs: this.pqs.generateOwnershipProof(),
            combined_timestamp: Date.now()
        };
    }

    /**
     * Verify ownership proof
     */
    verifyOwnershipProof(proof) {
        return this.pqs.verifyOwnershipProof(proof.pqs);
    }

    /**
     * Delete everything - true sovereignty
     */
    async deleteSeed() {
        await this.seedEngine.deleteSeed();
        this.pqs = null;
        this.isPQSLinked = false;
        this.isInitialized = false;

        this._emit('deleted', {});
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════════

    _bindSeedEvents() {
        // Forward seed events
        const events = ['created', 'loaded', 'unlocked', 'approved', 'rejected', 'genesis_locked'];
        events.forEach(event => {
            this.seedEngine.on(event, (data) => this._emit(`seed_${event}`, data));
        });
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (!this.listeners.has(event)) return;
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }

    _emit(event, data) {
        if (!this.listeners.has(event)) return;
        this.listeners.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (e) {
                console.error(`Error in ${event} listener:`, e);
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // DIRECT ACCESS (for advanced use)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get raw seed engine (for advanced operations)
     */
    getSeedEngine() {
        return this.seedEngine;
    }

    /**
     * Get PQS engine (for advanced operations)
     */
    getPQS() {
        return this.pqs;
    }

    /**
     * Get current mathematical state
     */
    getMathematicalState() {
        if (!this.isPQSLinked) return null;

        return {
            coefficients: this.pqs.coefficients,
            vertex: this.pqs.vertex,
            centroid: this.pqs.behaviorAccumulator.centroid,
            trajectory: this.pqs.behaviorAccumulator.trajectory.slice(-10),
            goldenRatio: PHI,
            goldenAngle: GOLDEN_ANGLE,
            encodingCount: this.pqs.encodingHistory.length
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const unifiedSeed = new UnifiedSeedEngine();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export { UnifiedSeedEngine, unifiedSeed };
export default unifiedSeed;
