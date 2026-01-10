/**
 * NORTH STAR CORE MODULE
 * ======================
 * The Soul of Digital Sovereignty
 *
 * This is the main entry point for the core seed engine.
 * It unifies:
 * - Seed Profile Engine (behavioral storage)
 * - Pi-Quadratic Seed (mathematical encoding)
 * - Unified Integration (the bridge)
 *
 * USAGE:
 * import { NorthStar } from './core/index.js';
 *
 * // Initialize
 * await NorthStar.initialize();
 *
 * // Queue data for consent
 * NorthStar.queueForConsent({
 *     source: 'creation',
 *     patterns: { color_preference: 0.7, time_spent: 120 },
 *     preview: 'Created a blue-themed project'
 * });
 *
 * // Get predictions
 * const predictions = NorthStar.getPredictions();
 */

import { UnifiedSeedEngine, unifiedSeed } from './seed_pqs_integration.js';
import { SeedProfileEngine, SeedCrypto, SEED_VERSION } from './seed_profile.js';
import { PiQuadraticSeed, PHI, GOLDEN_ANGLE, PI_DIGITS } from './pi_quadratic_seed.js';
import { ImmutableCore, immutableCore, MATH_CONSTANTS } from './immutable_core.js';
import { SpiralCompressionEngine, ProgressiveLoader, COMPRESSION_CONFIG } from './spiral_compression.js';
import { IPFSStorage, ipfsStorage, PlatformTierManager, tierManager } from './ipfs_storage.js';
import { KnowledgeUpdater, knowledgeUpdater, AlignmentVerifier } from './knowledge_updater.js';
import {
    PreservationModeManager,
    preservationManager,
    PreservationStatus,
    StatusColors
} from './preservation_mode.js';
import {
    BreathRhythmGenerator,
    CreativeLeapAlgorithm,
    CreativeOutputGenerator,
    initializeCreativeEngine,
    getCreativeEngine,
    BREATH_PATTERNS,
    LEAP_PATTERNS
} from './creative_engine.js';
import {
    AuthorityMatrix,
    ComponentWiringManager,
    authorityMatrix,
    wiringManager,
    AUTHORITY_LEVEL,
    COMPONENT_REGISTRY
} from './authority_matrix.js';
import {
    CreationSpiralEngine,
    MendingTracker,
    creationSpiral,
    mendingTracker,
    SPIRAL_DIRECTION,
    ENERGY_TYPES,
    DREAM_TEMPLATE,
    WHAT_EXTRACTION_BROKE
} from './creation_spiral.js';
import {
    NORTH_STAR_PRINCIPLES,
    PrincipleChecker,
    FutureGenerationTeaching,
    principleChecker
} from './north_star_principles.js';
import {
    ExpansionEngine,
    TrajectoryCalculator,
    expansionEngine,
    EXPANSION_TYPES,
    PURPOSE_TEMPLATE
} from './expansion_engine.js';
import {
    BalanceEngine,
    BalanceTracker,
    balanceEngine,
    POLARITY_PAIRS,
    BALANCE_CONFIG,
    WHOLENESS_PRINCIPLE
} from './balance_principle.js';
import {
    AppManifestGenerator,
    manifestGenerator,
    MANIFEST_SCHEMA,
    PUBLICATION_GUIDES,
    DISCOVERY_APP_TEMPLATE
} from './app_manifest.js';
import {
    EnergeticEngine,
    QuantumProbabilityEngine,
    ResonanceEngine,
    FluidMemoryEngine,
    SpatialWebInterface,
    energeticEngine,
    quantumEngine,
    resonanceEngine,
    fluidMemory,
    spatialWeb,
    TESLA_NUMBERS,
    SCHUMANN_RESONANCE,
    ELECTROMAGNETIC_CONSTANTS,
    WATER_PROPERTIES
} from './energetic_core.js';

// ═══════════════════════════════════════════════════════════════════════════
// NORTH STAR API
// High-level interface for all core functionality
// ═══════════════════════════════════════════════════════════════════════════

const NorthStar = {
    // The unified engine instance
    _engine: unifiedSeed,

    // State
    isReady: false,

    /**
     * Initialize the North Star engine
     * Creates or loads the user's seed with PQS
     */
    async initialize() {
        try {
            await this._engine.initialize();
            this.isReady = true;

            console.log('%c[NorthStar] Initialized', 'color: #00ff88; font-weight: bold');
            console.log('%c[NorthStar] Vertex (optimal state):', 'color: #00ff88',
                this._engine.pqs?.vertex);

            return {
                success: true,
                isNewSeed: this._engine.seedEngine.seed.meta.total_interactions === 0,
                vertex: this._engine.pqs?.vertex
            };
        } catch (error) {
            console.error('[NorthStar] Initialization failed:', error);
            return { success: false, error: error.message };
        }
    },

    /**
     * Create a new seed (for first-time users)
     */
    async createNew() {
        const result = await this._engine.createNew();
        this.isReady = true;
        return result;
    },

    /**
     * Unlock existing seed with key
     */
    async unlock(keyString) {
        const success = await this._engine.unlock(keyString);
        this.isReady = success;
        return success;
    },

    // ═══════════════════════════════════════════════════════════════════
    // CONSENT GATEWAY
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Queue data for user consent
     * NOTHING enters the seed without going through here
     */
    queueForConsent(data) {
        this._checkReady();
        return this._engine.queueForConsent(data);
    },

    /**
     * Get items pending consent
     */
    getPendingItems() {
        this._checkReady();
        return this._engine.seedEngine.getPendingItems();
    },

    /**
     * Approve an item - adds to seed with PQS encoding
     */
    async approve(itemId, modifications = null) {
        this._checkReady();
        return await this._engine.approveItem(itemId, modifications);
    },

    /**
     * Reject an item - never train on this
     */
    reject(itemId, deleteRaw = true) {
        this._checkReady();
        return this._engine.seedEngine.rejectItem(itemId, deleteRaw);
    },

    /**
     * Add auto-approve rule
     */
    addAutoApproveRule(rule) {
        this._checkReady();
        return this._engine.seedEngine.addAutoApproveRule(rule);
    },

    // ═══════════════════════════════════════════════════════════════════
    // PREDICTIONS & RECOMMENDATIONS
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Get predictions for user's optimal path
     */
    getPredictions() {
        this._checkReady();
        return this._engine.getPredictions();
    },

    /**
     * Get personalized recommendations
     */
    getRecommendations() {
        this._checkReady();
        return this._engine.getRecommendations();
    },

    /**
     * Get current mathematical state
     */
    getMathematicalState() {
        this._checkReady();
        return this._engine.getMathematicalState();
    },

    // ═══════════════════════════════════════════════════════════════════
    // ALGORITHM
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Get content ranking weights
     */
    getContentRanking() {
        this._checkReady();
        return this._engine.seedEngine.getContentRanking();
    },

    /**
     * Get PQS-enhanced ranking for specific content
     */
    getRanking(content) {
        this._checkReady();
        return this._engine.getRanking(content);
    },

    /**
     * Update algorithm weights
     */
    updateAlgorithm(weights) {
        this._checkReady();
        return this._engine.seedEngine.updateAlgorithm(weights);
    },

    /**
     * Get topic relevance score
     */
    getTopicRelevance(topics) {
        this._checkReady();
        return this._engine.seedEngine.getTopicRelevance(topics);
    },

    /**
     * Get relationship depth with entity
     */
    getRelationshipDepth(name) {
        this._checkReady();
        return this._engine.seedEngine.getRelationshipDepth(name);
    },

    // ═══════════════════════════════════════════════════════════════════
    // ENCODING (Direct PQS Access)
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Encode a value through PQS
     */
    encode(value, dimension = 'generic') {
        this._checkReady();
        return this._engine.encode(value, dimension);
    },

    /**
     * Decode a value (only works with correct genesis)
     */
    decode(encodedValue) {
        this._checkReady();
        return this._engine.decode(encodedValue);
    },

    // ═══════════════════════════════════════════════════════════════════
    // EXPORT & SOVEREIGNTY
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Export complete state (encrypted)
     */
    async export() {
        this._checkReady();
        return await this._engine.export();
    },

    /**
     * Export plaintext (for transparency)
     */
    exportPlaintext() {
        this._checkReady();
        return this._engine.exportPlaintext();
    },

    /**
     * Generate ownership proof
     */
    generateOwnershipProof() {
        this._checkReady();
        return this._engine.generateOwnershipProof();
    },

    /**
     * Verify ownership proof
     */
    verifyOwnershipProof(proof) {
        this._checkReady();
        return this._engine.verifyOwnershipProof(proof);
    },

    /**
     * Delete everything - the ultimate sovereignty right
     */
    async deleteSeed() {
        await this._engine.deleteSeed();
        this.isReady = false;
    },

    // ═══════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Subscribe to events
     */
    on(event, callback) {
        this._engine.on(event, callback);
    },

    /**
     * Unsubscribe from events
     */
    off(event, callback) {
        this._engine.off(event, callback);
    },

    // ═══════════════════════════════════════════════════════════════════
    // CREATIVE OUTPUT
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Get creative engine instance
     * Uses user's seed offset for personalized generation
     */
    getCreativeEngine() {
        this._checkReady();
        const offset = this._engine.pqs?.genesis?.offset || 0;
        return getCreativeEngine(offset);
    },

    /**
     * Generate a creative layout based on context
     * Uses breath rhythms and creative leaps
     */
    generateCreativeLayout(options = {}) {
        this._checkReady();
        const engine = this.getCreativeEngine();
        return engine.generateLayout(options);
    },

    /**
     * Skip to an unexpected creative solution
     * Applies creative leap algorithms
     */
    creativeSkip(currentLayout, skipType = 'UNKNOWN') {
        this._checkReady();
        const engine = this.getCreativeEngine();
        return engine.skipToUnexpected(currentLayout, skipType);
    },

    /**
     * Reveal unexplored creative possibilities
     * Based on user profile gaps and unknown territories
     */
    revealPossibilities(currentContext = {}) {
        this._checkReady();
        const engine = this.getCreativeEngine();
        const userProfile = this._engine.seedEngine.seed.behaviors;
        return engine.revealUnknown(userProfile, currentContext);
    },

    // ═══════════════════════════════════════════════════════════════════
    // CREATION SPIRAL (Counter-Extraction)
    // Recursive energy generation - creation compounds, extraction depletes
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Process a creator's dream into an app specification
     * Any creator can dream an app - no technical skill required
     * North Star principles are automatically enforced
     *
     * @param {Object} dream - The creator's vision
     * @returns {Object} Processed app specification
     */
    processDream(dream) {
        return creationSpiral.processDream(dream);
    },

    /**
     * Analyze if an app/feature extracts or creates
     * Returns spiral direction and specific points
     */
    analyzeSpiralDirection(appSpec) {
        return creationSpiral.analyzeSpiralDirection(appSpec);
    },

    /**
     * Get the current state of the creation spiral
     * Shows energy compounding, creation count, spiral health
     */
    getSpiralState() {
        return creationSpiral.getSpiralState();
    },

    /**
     * Generate a manifesto for a created app
     * Embeds immutable commitments into the app
     */
    generateManifesto(dreamId) {
        return creationSpiral.generateManifesto(dreamId);
    },

    /**
     * Check if an action would break the creation spiral
     * Used to prevent extraction patterns from entering
     */
    wouldBreakSpiral(action) {
        return creationSpiral.wouldBreakSpiral(action);
    },

    /**
     * Get the mending status
     * What extraction broke, what's being mended
     */
    getMendingStatus() {
        return mendingTracker.getMendingStatus();
    },

    /**
     * Record a mending action
     * Track progress in healing what extraction broke
     */
    recordMending(category, action, impact) {
        return mendingTracker.recordMending(category, action, impact);
    },

    /**
     * Get the dream template
     * Structure for non-technical creators to express visions
     */
    getDreamTemplate() {
        return DREAM_TEMPLATE;
    },

    /**
     * Get what extraction broke
     * Awareness of what needs mending
     */
    getWhatExtractionBroke() {
        return WHAT_EXTRACTION_BROKE;
    },

    // ═══════════════════════════════════════════════════════════════════
    // NORTH STAR PRINCIPLES
    // Values encoded as architecture - learned through use, not reading
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Get all North Star principles
     * The values that future generations learn through use
     */
    getPrinciples() {
        return NORTH_STAR_PRINCIPLES;
    },

    /**
     * Check if an action aligns with North Star principles
     * Returns violations if any
     */
    checkPrincipleAlignment(action) {
        return principleChecker.checkAlignment(action);
    },

    /**
     * Get what users learn from each principle
     * The lessons absorbed through experience
     */
    getWhatUserLearns() {
        return principleChecker.getWhatUserLearns();
    },

    /**
     * Get the declarations of all principles
     * The North Star in words
     */
    getPrincipleDeclarations() {
        return principleChecker.getDeclarations();
    },

    /**
     * Get principles by their lineage (Rand, Starhawk, Tori Amos, Bjork)
     */
    getPrinciplesByLineage(lineageName) {
        return principleChecker.getPrinciplesByLineage(lineageName);
    },

    /**
     * Get the complete teaching for future generations
     * What the system instills through experience
     */
    getFutureGenerationTeaching() {
        return FutureGenerationTeaching.getCompleteTeaching();
    },

    /**
     * Get the North Star itself - the one-sentence summary
     */
    getNorthStar() {
        return FutureGenerationTeaching.getNorthStar();
    },

    /**
     * Explain why an action was blocked (if it violated principles)
     */
    explainViolation(violations) {
        return principleChecker.explainViolation(violations);
    },

    // ═══════════════════════════════════════════════════════════════════
    // EXPANSION ENGINE
    // Prediction for user growth, not extraction
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Initialize expansion engine with user's purpose
     * This trains the system to suggest based on user's trajectory
     *
     * @param {Object} purpose - User's stated purpose (becoming, values, interests)
     */
    initializeExpansion(purpose) {
        this._checkReady();
        const seedData = this._engine.seedEngine.seed;
        return expansionEngine.initialize(purpose, seedData);
    },

    /**
     * Get expansion suggestions based on current context
     * Suggests creators, topics, skills aligned with user's North Star
     *
     * @param {Object} currentContext - What user is currently exploring
     * @param {number} count - Number of suggestions
     */
    getExpansions(currentContext = {}, count = 5) {
        return expansionEngine.getExpansions(currentContext, count);
    },

    /**
     * Record user's response to a suggestion
     * Trains the relevance scoring
     *
     * @param {string} suggestionId - Which suggestion
     * @param {string} response - 'explored', 'saved', 'dismissed', 'loved'
     */
    recordExpansionResponse(suggestionId, response) {
        return expansionEngine.recordResponse(suggestionId, response);
    },

    /**
     * Get user's expansion profile
     * Shows how their interests have grown over time
     */
    getExpansionProfile() {
        return expansionEngine.getExpansionProfile();
    },

    /**
     * Get the purpose template
     * Structure for users to define their North Star
     */
    getPurposeTemplate() {
        return PURPOSE_TEMPLATE;
    },

    /**
     * Export the user's trained inference web
     * User owns their expansion model
     */
    exportExpansionModel() {
        return expansionEngine.exportInferenceWeb();
    },

    /**
     * Import a previously exported expansion model
     */
    importExpansionModel(exported) {
        return expansionEngine.importInferenceWeb(exported);
    },

    // ═══════════════════════════════════════════════════════════════════
    // BALANCE PRINCIPLE (Wholeness Through Complementary Polarities)
    // Ensures BOTH male/female expressions are represented regardless of
    // user preference - prevents echo chambers, enables true understanding
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Apply balance to any set of suggestions/recommendations
     * Ensures both polarities are represented
     *
     * @param {Array} suggestions - Raw suggestions to balance
     * @param {Function} polarityDetector - Function to detect polarity of items
     * @returns {Array} Balanced suggestions
     */
    applyBalance(suggestions, polarityDetector = null) {
        return balanceEngine.ensureBalance(suggestions, polarityDetector);
    },

    /**
     * Get the complement creator for a given creator
     * E.g., Rand → Fuller, Starhawk → Prince, Tori → Coltrane, Bjork → Bowie
     *
     * @param {string} creatorName - Name of creator
     * @returns {Object} Complementary creator with shared value
     */
    getComplement(creatorName) {
        return balanceEngine.getComplement(creatorName);
    },

    /**
     * Get mirror suggestions - both polarities of aligned values
     * Always returns BOTH expressions regardless of user's lean
     *
     * @param {string} interest - User's interest
     * @returns {Object} Mirrored suggestions with both polarities
     */
    getMirrorSuggestions(interest) {
        return balanceEngine.getMirrorSuggestions(interest);
    },

    /**
     * Record consumption for balance tracking
     * Used to detect if user is leaning too far toward one polarity
     *
     * @param {string} item - What was consumed
     * @param {string} polarity - 'feminine', 'masculine', or 'neutral'
     * @param {string} domain - Which domain (PHILOSOPHY, POWER, RHYTHM, UNKNOWN)
     */
    recordBalanceConsumption(item, polarity, domain = null) {
        balanceEngine.recordConsumption(item, polarity, domain);
    },

    /**
     * Get current balance status
     * Shows if user is balanced or leaning toward one polarity
     *
     * @returns {Object} Balance analysis with ratio and recommendations
     */
    getBalanceStatus() {
        return balanceEngine.getBalanceStatus();
    },

    /**
     * Get all polarity pairs - the eight lineages organized by domain
     * PHILOSOPHY: Rand ↔ Fuller
     * POWER: Starhawk ↔ Prince
     * RHYTHM: Tori ↔ Coltrane
     * UNKNOWN: Bjork ↔ Bowie
     */
    getPolarityPairs() {
        return balanceEngine.getPolarityPairs();
    },

    /**
     * Get the wholeness principle - the philosophical foundation
     * Why balance matters: true understanding requires both expressions
     */
    getWholenessPrinciple() {
        return WHOLENESS_PRINCIPLE;
    },

    /**
     * Get balance configuration
     * Thresholds based on golden ratio
     */
    getBalanceConfig() {
        return BALANCE_CONFIG;
    },

    // ═══════════════════════════════════════════════════════════════════
    // APP MANIFEST & PUBLICATION (Reach Without Liability)
    // Creation ≠ Publication. ARCHIVIT creates, user publishes.
    // Manifests enable discovery without hosting.
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Generate a manifest for a dreamed app
     * Manifests are METADATA - they describe the app and where it lives
     * They enable discovery without requiring ARCHIVIT to host anything
     *
     * @param {Object} app - The app specification from dream pipeline
     * @returns {Object} Complete manifest with values alignment check
     */
    generateAppManifest(app) {
        this._checkReady();
        const creatorProof = {
            genesis: this._engine.pqs?.genesis,
            timestamp: Date.now()
        };
        return manifestGenerator.generate(app, creatorProof);
    },

    /**
     * Add a publication location to a manifest
     * User calls this after publishing their app somewhere
     *
     * @param {Object} manifest - The manifest to update
     * @param {string} location - Where the app was published (URL/CID)
     * @returns {Object} Updated manifest
     */
    addPublicationLocation(manifest, location) {
        return manifestGenerator.addPublicationLocation(manifest, location);
    },

    /**
     * Export a manifest in shareable formats
     * JSON, minimal, and URL-encoded versions
     *
     * @param {Object} manifest - The manifest to export
     */
    exportManifest(manifest) {
        return manifestGenerator.exportManifest(manifest);
    },

    /**
     * Get publication guides
     * Instructions for deploying to various platforms
     * ARCHIVIT provides guidance, not hosting
     */
    getPublicationGuides() {
        return PUBLICATION_GUIDES;
    },

    /**
     * Get the manifest schema
     * What fields a manifest can contain
     */
    getManifestSchema() {
        return MANIFEST_SCHEMA;
    },

    /**
     * Get the discovery app template
     * A dream waiting to happen - the community-built app store replacement
     * This is not built by ARCHIVIT. This is an invitation to dream.
     */
    getDiscoveryAppTemplate() {
        return DISCOVERY_APP_TEMPLATE;
    },

    // ═══════════════════════════════════════════════════════════════════
    // ENERGETIC CORE (Physics of Digital Sovereignty)
    // Quantum probability, Tesla resonance, fluid memory, spatial web
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Process input through the full energetic stack
     * Quantum probability + Tesla resonance + Fluid memory + Spatial context
     *
     * @param {Object} input - What we're processing
     * @returns {Object} Energetically processed result with recommendation
     */
    processEnergetically(input) {
        this._checkReady();
        const userContext = {
            values: this._engine.seedEngine.seed.behaviors,
            trajectory: this._engine.pqs?.vertex
        };
        return energeticEngine.process(input, userContext);
    },

    /**
     * Generate probability landscape (quantum superposition)
     * All possibilities exist until observed
     *
     * @param {Array} possibilities - Possible outcomes
     * @returns {Object} Probability landscape
     */
    generateProbabilityLandscape(possibilities) {
        this._checkReady();
        const context = {
            values: this._engine.seedEngine.seed.behaviors
        };
        return quantumEngine.generateProbabilityLandscape(possibilities, context);
    },

    /**
     * Collapse probability to actuality (observation)
     * User's attention creates their reality
     *
     * @param {Object} landscape - The probability landscape
     * @param {string} observationType - 'intention', 'attention', or 'action'
     */
    collapseToReality(landscape, observationType = 'attention') {
        return quantumEngine.collapse(landscape, observationType);
    },

    /**
     * Measure resonance with user's frequency (Tesla)
     *
     * @param {Object} input - What we're checking
     * @returns {Object} Resonance analysis
     */
    measureResonance(input) {
        this._checkReady();
        const userFrequency = this._engine.seedEngine.seed.behaviors;
        return resonanceEngine.measureResonance(input, userFrequency);
    },

    /**
     * Get resonant timing for animations/transitions (Tesla + Heart coherence)
     *
     * @param {string} intensity - 'rest', 'active', 'dramatic'
     * @returns {Object} Timing values that resonate naturally
     */
    getResonantTiming(intensity = 'rest') {
        return resonanceEngine.generateResonantTiming(intensity);
    },

    /**
     * Apply Tesla's 3-6-9 pattern to structure
     *
     * @param {Array} items - Items to organize
     * @returns {Object} Items structured by 3-6-9
     */
    applyTeslaPattern(items) {
        return resonanceEngine.applyTeslaPattern(items);
    },

    /**
     * Imprint pattern into fluid memory (water-like storage)
     *
     * @param {string} key - Pattern identifier
     * @param {Object} pattern - The pattern
     * @param {Object} intention - Optional intention
     */
    imprintMemory(key, pattern, intention = null) {
        fluidMemory.imprint(key, pattern, intention);
    },

    /**
     * Recall from fluid memory (may have shifted)
     *
     * @param {string} key - Pattern to recall
     * @returns {Object} Recalled pattern with decay/context applied
     */
    recallMemory(key) {
        this._checkReady();
        const context = this._engine.seedEngine.seed.behaviors;
        return fluidMemory.recall(key, context);
    },

    /**
     * Create vortex arrangement (water's natural spiral)
     *
     * @param {Array} items - Items to arrange
     * @returns {Array} Items with vortex positions
     */
    createVortex(items) {
        return fluidMemory.createVortex(items);
    },

    /**
     * Initialize spatial domain (Spatial Web)
     * User's sovereign territory in ambient computing
     */
    initializeSpatialDomain() {
        this._checkReady();
        const genesis = this._engine.pqs?.genesis;
        return spatialWeb.initializeDomain(genesis);
    },

    /**
     * Register a digital twin of created app (Spatial Web)
     *
     * @param {Object} app - The app specification
     * @param {Object} manifest - The app manifest
     */
    registerDigitalTwin(app, manifest) {
        return spatialWeb.registerTwin(app, manifest);
    },

    /**
     * Find resonant apps/domains in spatial web
     *
     * @param {Object} query - What we're looking for
     */
    findResonantApps(query) {
        return spatialWeb.findResonant(query);
    },

    /**
     * Get Tesla's sacred numbers
     */
    getTeslaNumbers() {
        return TESLA_NUMBERS;
    },

    /**
     * Get electromagnetic constants (Schumann, brainwaves, etc.)
     */
    getElectromagneticConstants() {
        return ELECTROMAGNETIC_CONSTANTS;
    },

    /**
     * Get water properties (fluid memory parameters)
     */
    getWaterProperties() {
        return WATER_PROPERTIES;
    },

    // ═══════════════════════════════════════════════════════════════════
    // FOUNDER AUTHORITY (Quantum-Proof)
    // These methods require mathematical proof of founder genesis
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Check if current genesis has founder authority
     * This is a MATHEMATICAL check, not a permission lookup
     */
    checkFounderAuthority() {
        this._checkReady();
        const genesis = this._engine.pqs?.genesis;
        return authorityMatrix.verifyFounderAuthority(genesis);
    },

    /**
     * Rewire a component to a different target (FOUNDER ONLY)
     * Example: rewire breath_rhythm from 'layout_spacing' to 'animation_timing'
     *
     * @param {string} component - Component key (e.g., 'breath_rhythm')
     * @param {string} newTarget - New target binding
     * @returns {Object} Result of rewiring attempt
     */
    rewireComponent(component, newTarget) {
        this._checkReady();
        const genesis = this._engine.pqs?.genesis;
        return wiringManager.rewire(component, newTarget, genesis);
    },

    /**
     * Deactivate a component (FOUNDER ONLY)
     * The component still exists but doesn't feed into anything
     *
     * @param {string} component - Component to deactivate
     */
    deactivateComponent(component) {
        this._checkReady();
        const genesis = this._engine.pqs?.genesis;
        return wiringManager.deactivate(component, genesis);
    },

    /**
     * Activate a component (FOUNDER ONLY)
     *
     * @param {string} component - Component to activate
     */
    activateComponent(component) {
        this._checkReady();
        const genesis = this._engine.pqs?.genesis;
        return wiringManager.activate(component, genesis);
    },

    /**
     * Get current component wiring
     */
    getComponentWiring(component) {
        return wiringManager.getWiring(component);
    },

    /**
     * Check if a component should feed into a target
     * Used internally by components to check their wiring
     */
    shouldComponentFeedInto(component, target) {
        return wiringManager.shouldFeedInto(component, target);
    },

    /**
     * Verify system integrity
     * Checks that immutable components haven't been tampered with
     */
    verifySystemIntegrity() {
        return authorityMatrix.verifyIntegrity();
    },

    /**
     * Get modification log (FOUNDER ONLY for full log)
     */
    getModificationLog() {
        this._checkReady();
        const genesis = this._engine.pqs?.genesis;
        const isFounder = authorityMatrix.verifyFounderAuthority(genesis).isFounder;

        if (isFounder) {
            return authorityMatrix.getModificationLog();
        } else {
            // Non-founders only see USER_MUTABLE modifications
            return authorityMatrix.getModificationLog()
                .filter(m => m.authorityLevel === 'USER_MUTABLE');
        }
    },

    // ═══════════════════════════════════════════════════════════════════
    // ADVANCED ACCESS
    // ═══════════════════════════════════════════════════════════════════

    /**
     * Get raw seed data (for debugging/advanced use)
     */
    getSeed() {
        this._checkReady();
        return this._engine.seedEngine.seed;
    },

    /**
     * Get raw PQS engine (for advanced use)
     */
    getPQS() {
        this._checkReady();
        return this._engine.getPQS();
    },

    /**
     * Get unified engine (for advanced use)
     */
    getEngine() {
        return this._engine;
    },

    /**
     * Get authority matrix (for advanced use)
     */
    getAuthorityMatrix() {
        return authorityMatrix;
    },

    /**
     * Get wiring manager (for advanced use)
     */
    getWiringManager() {
        return wiringManager;
    },

    // ═══════════════════════════════════════════════════════════════════
    // INTERNAL
    // ═══════════════════════════════════════════════════════════════════

    _checkReady() {
        if (!this.isReady) {
            throw new Error('NorthStar not initialized. Call NorthStar.initialize() first.');
        }
    }
};

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const NORTH_STAR_VERSION = '1.0.0';

const NORTH_STAR_CONSTANTS = {
    PHI,           // Golden ratio
    GOLDEN_ANGLE,  // 137.5077640500378 degrees
    SEED_VERSION,
    PI_DIGITS_LENGTH: PI_DIGITS.length,
    BREATH_PATTERN_TYPES: Object.keys(BREATH_PATTERNS),
    LEAP_PATTERN_TYPES: Object.keys(LEAP_PATTERNS)
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    // Main API
    NorthStar,

    // Version
    NORTH_STAR_VERSION,

    // Constants
    NORTH_STAR_CONSTANTS,
    COMPRESSION_CONFIG,
    MATH_CONSTANTS,

    // Core Classes
    UnifiedSeedEngine,
    SeedProfileEngine,
    PiQuadraticSeed,
    ImmutableCore,

    // Compression & Storage
    SpiralCompressionEngine,
    ProgressiveLoader,
    IPFSStorage,
    PlatformTierManager,

    // Knowledge & Safety
    KnowledgeUpdater,
    AlignmentVerifier,

    // Creative Engine
    BreathRhythmGenerator,
    CreativeLeapAlgorithm,
    CreativeOutputGenerator,
    initializeCreativeEngine,
    getCreativeEngine,
    BREATH_PATTERNS,
    LEAP_PATTERNS,

    // Authority & Wiring (Quantum-Proof)
    AuthorityMatrix,
    ComponentWiringManager,
    authorityMatrix,
    wiringManager,
    AUTHORITY_LEVEL,
    COMPONENT_REGISTRY,

    // Creation Spiral (Counter-Extraction)
    CreationSpiralEngine,
    MendingTracker,
    creationSpiral,
    mendingTracker,
    SPIRAL_DIRECTION,
    ENERGY_TYPES,
    DREAM_TEMPLATE,
    WHAT_EXTRACTION_BROKE,

    // North Star Principles (Future Generation Teaching)
    NORTH_STAR_PRINCIPLES,
    PrincipleChecker,
    FutureGenerationTeaching,
    principleChecker,

    // Expansion Engine (Prediction for Growth)
    ExpansionEngine,
    TrajectoryCalculator,
    expansionEngine,
    EXPANSION_TYPES,
    PURPOSE_TEMPLATE,

    // Balance Principle (Wholeness Through Complementary Polarities)
    BalanceEngine,
    BalanceTracker,
    balanceEngine,
    POLARITY_PAIRS,
    BALANCE_CONFIG,
    WHOLENESS_PRINCIPLE,

    // App Manifest & Publication (Reach Without Liability)
    AppManifestGenerator,
    manifestGenerator,
    MANIFEST_SCHEMA,
    PUBLICATION_GUIDES,
    DISCOVERY_APP_TEMPLATE,

    // Preservation Mode
    PreservationModeManager,
    preservationManager,
    PreservationStatus,
    StatusColors,

    // Energetic Core (Physics of Digital Sovereignty)
    EnergeticEngine,
    QuantumProbabilityEngine,
    ResonanceEngine,
    FluidMemoryEngine,
    SpatialWebInterface,
    energeticEngine,
    quantumEngine,
    resonanceEngine,
    fluidMemory,
    spatialWeb,
    TESLA_NUMBERS,
    SCHUMANN_RESONANCE,
    ELECTROMAGNETIC_CONSTANTS,
    WATER_PROPERTIES,

    // Singletons
    immutableCore,
    ipfsStorage,
    tierManager,
    knowledgeUpdater,

    // Utilities
    SeedCrypto
};

export default NorthStar;
