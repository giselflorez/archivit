/**
 * CREATION SPIRAL ENGINE
 * ======================
 * Recursive Energy Generation for Counter-Extraction
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * PHILOSOPHICAL LINEAGE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * This architecture draws from "The Spiral Dance" by Starhawk (1979),
 * a foundational text on power, interconnection, and reclamation.
 *
 * CORE DISTINCTION - TWO KINDS OF POWER:
 *
 *   POWER-OVER (Dominator/Extraction Model)
 *   ├── Control flows from top down
 *   ├── Value extracted from many to few
 *   ├── Scarcity maintained to preserve hierarchy
 *   ├── Individuals reduced to resources
 *   └── System depletes what it touches
 *
 *   POWER-FROM-WITHIN (Sovereignty/Creation Model)
 *   ├── Power inherent in each individual
 *   ├── Value stays with the creator
 *   ├── Abundance through sharing
 *   ├── Individuals as sovereign nodes
 *   └── System strengthens what it touches
 *
 * THE SPIRAL:
 *
 * Not linear progress, but spiral return - each cycle deeper than the last.
 * The golden ratio (φ) is this spiral made mathematical.
 * Growth that circles back while moving forward.
 * Patterns that compound through repetition with variation.
 *
 * IMMANENCE:
 *
 * Value is not "up there" to be extracted down.
 * Value is HERE - in the user's data, creations, relationships.
 * The sacred (the valuable) is immanent, not transcendent.
 * This is why local-first matters: value stays where it lives.
 *
 * THE WEB:
 *
 * Everything connected, but each node sovereign.
 * Not a hierarchy where power flows up.
 * Not isolation where nothing connects.
 * A web where each point has integrity AND relationship.
 *
 * RECLAIMING:
 *
 * What extraction systems took can be taken back.
 * Attention, creativity, identity, sovereignty - reclaimable.
 * This architecture is a tool of reclamation.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * TECHNICAL EXPRESSION
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * THE DOWNWARD SPIRAL (Extraction/Entropy):
 *
 * Systems built on power-over follow a predictable path:
 * Take → Deplete → Concentrate → Collapse
 * Each extraction weakens the source. Entropy wins.
 *
 * THE UPWARD SPIRAL (Creation/Negentropy):
 *
 * Systems built on power-from-within follow the inverse:
 * Give → Compound → Distribute → Flourish
 * Each creation strengthens the whole. Negentropy wins.
 *
 * THE RECURSIVE BOOST:
 *
 * 1. A creator dreams an app (no technical barrier)
 * 2. The app is born with sovereignty principles immutable
 * 3. The app enables others to create
 * 4. Each creation adds to a commons of non-extractive tools
 * 5. Each tool inspires more dreams
 * 6. The energy COMPOUNDS instead of depletes
 *
 * This is negentropy - building order against the current of extraction.
 *
 * INTENT:
 * Direct counterweight to corruption encrusted in current systems.
 * Mending what has been broken by enabling any creator to dream.
 */

import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';
import { AUTHORITY_LEVEL, COMPONENT_REGISTRY } from './authority_matrix.js';

// ═══════════════════════════════════════════════════════════════════════════
// SPIRAL DIRECTION CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const SPIRAL_DIRECTION = Object.freeze({
    EXTRACTION: -1,  // Downward spiral - depletes
    NEUTRAL: 0,      // No spiral - static
    CREATION: 1      // Upward spiral - generates
});

// ═══════════════════════════════════════════════════════════════════════════
// ENERGY TYPES
// What flows in each direction
// ═══════════════════════════════════════════════════════════════════════════

const ENERGY_TYPES = Object.freeze({
    // Extraction takes these FROM users
    EXTRACTION_TARGETS: [
        'attention',
        'behavioral_data',
        'context',
        'identity',
        'time',
        'cognitive_sovereignty',
        'creative_output',
        'social_graph',
        'future_predictions'
    ],

    // Creation returns these TO users
    CREATION_RETURNS: [
        'capability',
        'sovereignty',
        'preserved_context',
        'expanded_potential',
        'tools_for_others',
        'inspiration',
        'ownership',
        'privacy',
        'future_possibility'
    ]
});

// ═══════════════════════════════════════════════════════════════════════════
// DREAM TEMPLATE
// Structure for non-technical creators to express app visions
// ═══════════════════════════════════════════════════════════════════════════

const DREAM_TEMPLATE = Object.freeze({
    // What the creator wants to enable
    enables: {
        type: 'array',
        description: 'What does this app let people DO?',
        examples: ['create music', 'preserve memories', 'connect with family', 'learn new skills']
    },

    // What the creator wants to protect
    protects: {
        type: 'array',
        description: 'What does this app PROTECT for users?',
        examples: ['privacy', 'ownership', 'attention', 'context']
    },

    // What the creator refuses to do
    refuses: {
        type: 'array',
        description: 'What will this app NEVER do?',
        examples: ['sell data', 'show ads', 'track behavior', 'require accounts'],
        defaults: [
            'extract_without_consent',
            'sell_user_data',
            'optimize_for_platform',
            'break_context',
            'harvest_attention'
        ]
    },

    // Who this is for
    for_whom: {
        type: 'string',
        description: 'Who is this app FOR?',
        examples: ['artists who want to share without platforms taking cuts',
                   'families who want to preserve memories privately',
                   'students who want to learn without being tracked']
    },

    // The dream itself
    vision: {
        type: 'string',
        description: 'In your own words, what future does this app help create?'
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// CREATION SPIRAL ENGINE
// ═══════════════════════════════════════════════════════════════════════════

class CreationSpiralEngine {
    constructor() {
        this.creationsGenerated = 0;
        this.energyCompounded = 0;
        this.spiralHistory = [];
        this.dreamRegistry = new Map();
    }

    /**
     * Analyze an app/feature for spiral direction
     * Does it extract or create? Deplete or generate?
     *
     * @param {Object} appSpec - Specification of the app/feature
     * @returns {Object} Spiral analysis
     */
    analyzeSpiralDirection(appSpec) {
        const analysis = {
            direction: SPIRAL_DIRECTION.NEUTRAL,
            score: 0,
            extractionPoints: [],
            creationPoints: [],
            warnings: [],
            recommendations: []
        };

        // Check for extraction patterns
        for (const target of ENERGY_TYPES.EXTRACTION_TARGETS) {
            if (this._detectsExtraction(appSpec, target)) {
                analysis.extractionPoints.push(target);
                analysis.score -= 1;
            }
        }

        // Check for creation patterns
        for (const returns of ENERGY_TYPES.CREATION_RETURNS) {
            if (this._detectsCreation(appSpec, returns)) {
                analysis.creationPoints.push(returns);
                analysis.score += 1;
            }
        }

        // Determine direction
        if (analysis.score < 0) {
            analysis.direction = SPIRAL_DIRECTION.EXTRACTION;
            analysis.warnings.push('This design extracts more than it creates');
            analysis.recommendations.push('Consider: what does the user GET from this interaction?');
        } else if (analysis.score > 0) {
            analysis.direction = SPIRAL_DIRECTION.CREATION;
        }

        // Check for North Star principle violations
        const violations = this._checkPrincipleViolations(appSpec);
        if (violations.length > 0) {
            analysis.warnings.push(...violations);
            analysis.direction = SPIRAL_DIRECTION.EXTRACTION; // Any violation = extraction
        }

        return analysis;
    }

    /**
     * Detect extraction patterns in app spec
     */
    _detectsExtraction(appSpec, target) {
        const extractionSignals = {
            attention: ['infinite_scroll', 'autoplay', 'notifications_default_on', 'no_stopping_point'],
            behavioral_data: ['tracking', 'analytics', 'behavior_logging', 'pattern_extraction'],
            context: ['fragment', 'decontextualize', 'viral_optimize', 'engagement_maximize'],
            identity: ['profile_required', 'real_name', 'social_graph_access', 'contact_upload'],
            time: ['time_on_app_metric', 'session_length_optimize', 'retention_hooks'],
            cognitive_sovereignty: ['algorithm_hidden', 'filter_bubble', 'recommendation_opaque'],
            creative_output: ['platform_owns', 'license_grab', 'cant_export', 'cant_delete'],
            social_graph: ['contact_mining', 'relationship_mapping', 'influence_scoring'],
            future_predictions: ['predictive_modeling', 'behavior_forecasting', 'intent_prediction']
        };

        const signals = extractionSignals[target] || [];
        const specString = JSON.stringify(appSpec).toLowerCase();

        return signals.some(signal => specString.includes(signal.toLowerCase()));
    }

    /**
     * Detect creation patterns in app spec
     */
    _detectsCreation(appSpec, returns) {
        const creationSignals = {
            capability: ['enables', 'allows', 'empowers', 'tools_for', 'create', 'build'],
            sovereignty: ['user_owns', 'local_first', 'no_account_required', 'self_hosted'],
            preserved_context: ['context_preserved', 'history_intact', 'lineage_tracked'],
            expanded_potential: ['possibilities', 'exploration', 'discovery', 'growth'],
            tools_for_others: ['shareable', 'open_source', 'enables_creation', 'template'],
            inspiration: ['creative', 'artistic', 'expressive', 'imaginative'],
            ownership: ['export_free', 'delete_works', 'user_data_belongs_to_user'],
            privacy: ['no_tracking', 'local_storage', 'encrypted', 'private_by_default'],
            future_possibility: ['future_proof', 'extensible', 'evolvable', 'open_ended']
        };

        const signals = creationSignals[returns] || [];
        const specString = JSON.stringify(appSpec).toLowerCase();

        return signals.some(signal => specString.includes(signal.toLowerCase()));
    }

    /**
     * Check for North Star principle violations
     */
    _checkPrincipleViolations(appSpec) {
        const violations = [];
        const specString = JSON.stringify(appSpec).toLowerCase();

        // Check each immutable principle
        const principles = COMPONENT_REGISTRY['north_star_principles'];
        if (!principles) return violations;

        // Consent gateway check
        if (specString.includes('auto_collect') || specString.includes('implicit_consent')) {
            violations.push('VIOLATION: Consent gateway bypassed');
        }

        // Local-first check
        if (specString.includes('server_required') || specString.includes('cloud_only')) {
            violations.push('VIOLATION: Local-first principle broken');
        }

        // Export freedom check
        if (specString.includes('no_export') || specString.includes('locked_in')) {
            violations.push('VIOLATION: Export freedom denied');
        }

        // No tracking check
        if (specString.includes('telemetry') || specString.includes('analytics_required')) {
            violations.push('VIOLATION: No-tracking principle violated');
        }

        return violations;
    }

    /**
     * Process a creator's dream into an app specification
     * This is the "any type of creator can dream an app" interface
     *
     * @param {Object} dream - The creator's vision using DREAM_TEMPLATE
     * @returns {Object} App specification with North Star principles enforced
     */
    processDream(dream) {
        const timestamp = Date.now();
        const dreamId = `dream_${timestamp}_${Math.random().toString(36).substr(2, 9)}`;

        // Start with North Star defaults (immutable)
        const appSpec = {
            id: dreamId,
            created: timestamp,
            source: 'creator_dream',

            // From the dream
            enables: dream.enables || [],
            protects: dream.protects || [],
            for_whom: dream.for_whom || 'anyone who needs this',
            vision: dream.vision || '',

            // Enforced refusals (North Star + creator's own)
            refuses: [
                ...DREAM_TEMPLATE.refuses.defaults,
                ...(dream.refuses || [])
            ],

            // North Star principles (immutable, cannot be overridden)
            north_star: {
                consent_gateway: true,
                local_first: true,
                export_free: true,
                delete_works: true,
                no_tracking: true,
                user_authority: true,
                math_verification: true
            },

            // Spiral direction (must be CREATION)
            spiral: SPIRAL_DIRECTION.CREATION
        };

        // Analyze the dream
        const analysis = this.analyzeSpiralDirection(appSpec);

        // If dream somehow creates extraction, warn creator
        if (analysis.direction === SPIRAL_DIRECTION.EXTRACTION) {
            return {
                success: false,
                dreamId: dreamId,
                error: 'Dream contains extraction patterns',
                analysis: analysis,
                suggestion: 'Consider how this serves the user rather than extracts from them'
            };
        }

        // Register the dream
        this.dreamRegistry.set(dreamId, {
            dream: dream,
            spec: appSpec,
            analysis: analysis,
            created: timestamp
        });

        // Compound the energy
        this._compoundEnergy(appSpec);

        return {
            success: true,
            dreamId: dreamId,
            spec: appSpec,
            analysis: analysis,
            message: 'Dream processed. North Star principles enforced. Spiral direction: CREATION.'
        };
    }

    /**
     * Compound energy from creation
     * This is the recursive boost mechanism
     */
    _compoundEnergy(appSpec) {
        // Each creation adds to the commons
        this.creationsGenerated++;

        // Energy compounds using golden ratio
        // Each creation multiplies the potential for next creation
        const baseEnergy = 1;
        const compoundFactor = Math.pow(PHI, 1 / this.creationsGenerated);
        const newEnergy = baseEnergy * compoundFactor;

        this.energyCompounded += newEnergy;

        // Record in spiral history
        this.spiralHistory.push({
            timestamp: Date.now(),
            type: 'creation',
            energy: newEnergy,
            total: this.energyCompounded,
            creationCount: this.creationsGenerated
        });
    }

    /**
     * Get the current state of the creation spiral
     */
    getSpiralState() {
        return {
            direction: SPIRAL_DIRECTION.CREATION,
            creationsGenerated: this.creationsGenerated,
            energyCompounded: this.energyCompounded,
            dreamCount: this.dreamRegistry.size,
            compoundRate: this.creationsGenerated > 0
                ? this.energyCompounded / this.creationsGenerated
                : 0,
            history: this.spiralHistory.slice(-10)  // Last 10 events
        };
    }

    /**
     * Generate a creation manifesto for an app
     * This is what gets embedded in every created app
     */
    generateManifesto(dreamId) {
        const dreamData = this.dreamRegistry.get(dreamId);
        if (!dreamData) return null;

        const { dream, spec } = dreamData;

        return {
            // What this app stands for
            purpose: spec.vision || 'To serve creators, not extract from them',

            // Immutable commitments (cannot be changed even by founder)
            commitments: [
                'This app will NEVER extract data without explicit consent',
                'This app will NEVER sell user data',
                'This app will NEVER optimize for platform benefit over user benefit',
                'This app will ALWAYS allow data export',
                'This app will ALWAYS allow complete deletion',
                'This app will ALWAYS work offline',
                'This app will ALWAYS be auditable'
            ],

            // What it enables
            enables: spec.enables,

            // What it protects
            protects: spec.protects,

            // Who it serves
            serves: spec.for_whom,

            // Mathematical verification
            verification: 'These commitments are enforced by mathematical architecture, not promises.',

            // Lineage
            lineage: {
                created: spec.created,
                dreamId: dreamId,
                spiralDirection: 'CREATION',
                northStarVersion: '1.0.0'
            }
        };
    }

    /**
     * Check if an action would break the spiral
     * Used to prevent extraction patterns from entering
     */
    wouldBreakSpiral(action) {
        const extractionActions = [
            'collect_without_consent',
            'send_to_server_without_asking',
            'track_behavior',
            'optimize_engagement',
            'prevent_export',
            'prevent_delete',
            'require_account',
            'show_ads',
            'sell_data',
            'phone_home'
        ];

        const actionLower = action.toLowerCase();
        const wouldBreak = extractionActions.some(ea => actionLower.includes(ea));

        return {
            wouldBreak: wouldBreak,
            action: action,
            reason: wouldBreak
                ? 'This action would convert creation energy to extraction'
                : 'Action is compatible with creation spiral'
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// MENDING TRACKER
// Track what has been broken and what is being mended
// ═══════════════════════════════════════════════════════════════════════════

class MendingTracker {
    constructor() {
        this.brokenThings = new Map();
        this.mendingProgress = new Map();
    }

    /**
     * Register something that extraction has broken
     */
    registerBroken(category, description) {
        if (!this.brokenThings.has(category)) {
            this.brokenThings.set(category, []);
        }
        this.brokenThings.get(category).push({
            description: description,
            registered: Date.now(),
            mendingStarted: null,
            mended: false
        });
    }

    /**
     * Record mending progress
     */
    recordMending(category, action, impact) {
        if (!this.mendingProgress.has(category)) {
            this.mendingProgress.set(category, []);
        }
        this.mendingProgress.get(category).push({
            action: action,
            impact: impact,
            timestamp: Date.now()
        });
    }

    /**
     * Get mending status
     */
    getMendingStatus() {
        const status = {};

        for (const [category, broken] of this.brokenThings) {
            const mending = this.mendingProgress.get(category) || [];
            status[category] = {
                broken: broken.length,
                mendingActions: mending.length,
                totalImpact: mending.reduce((sum, m) => sum + (m.impact || 0), 0)
            };
        }

        return status;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// PRE-REGISTERED BROKEN THINGS
// What extraction architecture has broken in society
// ═══════════════════════════════════════════════════════════════════════════

const WHAT_EXTRACTION_BROKE = Object.freeze({
    ATTENTION: [
        'Ability to focus for extended periods',
        'Natural stopping points in media consumption',
        'Intentional engagement vs reactive scrolling'
    ],
    CONTEXT: [
        'Understanding of full picture before reacting',
        'Historical context of events and ideas',
        'Nuance in complex discussions'
    ],
    TRUST: [
        'Trust in institutions that adopted extraction',
        'Trust in authenticity of content',
        'Trust that services serve users'
    ],
    IDENTITY: [
        'Self-definition independent of algorithmic profile',
        'Privacy of inner life',
        'Ownership of personal narrative'
    ],
    CREATIVITY: [
        'Creation for its own sake vs engagement metrics',
        'Long-form and slow creative work',
        'Art that challenges rather than confirms'
    ],
    RELATIONSHIPS: [
        'Deep connection vs surface-level networking',
        'Private relationships without platform mediation',
        'Organic community vs algorithmic grouping'
    ],
    SHARED_REALITY: [
        'Common factual baseline',
        'Ability to disagree on values while agreeing on facts',
        'Collective memory not filtered by engagement'
    ]
});

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCES
// ═══════════════════════════════════════════════════════════════════════════

const creationSpiral = new CreationSpiralEngine();
const mendingTracker = new MendingTracker();

// Pre-register what's broken
for (const [category, items] of Object.entries(WHAT_EXTRACTION_BROKE)) {
    for (const item of items) {
        mendingTracker.registerBroken(category, item);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    CreationSpiralEngine,
    MendingTracker,
    creationSpiral,
    mendingTracker,
    SPIRAL_DIRECTION,
    ENERGY_TYPES,
    DREAM_TEMPLATE,
    WHAT_EXTRACTION_BROKE
};

export default creationSpiral;
