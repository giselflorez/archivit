/**
 * EXPANSION ENGINE
 * =================
 * Prediction Algorithm for User Growth, Not Extraction
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * THE CORE DIFFERENCE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * EXTRACTION ALGORITHM asks: "What keeps them engaged longer?"
 * → Serves platform metrics
 * → Optimizes for time-on-app
 * → Creates dependency
 *
 * EXPANSION ALGORITHM asks: "What helps them become who they're becoming?"
 * → Serves user's stated purpose
 * → Optimizes for trajectory toward their vertex (optimal state)
 * → Creates capability
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * HOW IT WORKS
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * 1. User trains the system through interests, topics, era, context
 * 2. System builds inference web of adjacent possibilities
 * 3. Suggestions filtered through user's North Star (stated purpose)
 * 4. Only outputs that serve their trajectory are surfaced
 * 5. Relevance grows through use - spiral expands
 *
 * The architecture is IMMUTABLE (cannot extract)
 * The experience is CUSTOMIZABLE (trained to user)
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * EXAMPLE: WHAT JUST HAPPENED
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * User's seed contained:
 * - Interest in sovereignty, individual power
 * - Appreciation for female creators who rejected narratives
 * - Values: breath, organic rhythm, unknown revealed, reclamation
 *
 * System inferred:
 * - "User values creators who demonstrate sovereignty through work"
 * - "User responds to those who rejected extraction systems"
 * - Adjacent male creators with same values: Fuller, Prince, Coltrane, Bowie
 *
 * Result:
 * - User discovers new influences aligned with existing values
 * - Understanding expands without values being violated
 * - User is excited to explore, not manipulated to scroll
 */

import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';
import { NORTH_STAR_PRINCIPLES } from './north_star_principles.js';
import { balanceEngine, POLARITY_PAIRS, BALANCE_CONFIG } from './balance_principle.js';

// ═══════════════════════════════════════════════════════════════════════════
// INFERENCE TYPES
// What kinds of expansions can the system suggest
// ═══════════════════════════════════════════════════════════════════════════

const EXPANSION_TYPES = Object.freeze({
    // Adjacent creators who share values
    CREATOR_ADJACENT: {
        type: 'creator',
        description: 'Creators who share your values but you may not know',
        weight: PHI  // High relevance
    },

    // Topics that connect to current interests
    TOPIC_BRIDGE: {
        type: 'topic',
        description: 'Topics that bridge your current interests to new territory',
        weight: 1 / PHI  // Medium relevance
    },

    // Historical context for current interests
    ERA_CONTEXT: {
        type: 'era',
        description: 'Historical context that deepens understanding',
        weight: 1.0
    },

    // Practical skills aligned with purpose
    SKILL_EXPANSION: {
        type: 'skill',
        description: 'Skills that serve your stated purpose',
        weight: PHI
    },

    // Philosophical connections
    PHILOSOPHY_ADJACENT: {
        type: 'philosophy',
        description: 'Philosophical frameworks aligned with your values',
        weight: 1 / PHI
    },

    // Unknown territory that aligns with trajectory
    UNKNOWN_ALIGNED: {
        type: 'unknown',
        description: 'Unexplored territory that serves your becoming',
        weight: Math.PI / PHI  // Special weight for the unknown
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// USER PURPOSE STRUCTURE
// How the user defines their North Star
// ═══════════════════════════════════════════════════════════════════════════

const PURPOSE_TEMPLATE = Object.freeze({
    // What the user is trying to become
    becoming: {
        type: 'string',
        description: 'Who are you trying to become?',
        example: 'A creator who helps others reclaim sovereignty'
    },

    // Core values (from the eight lineages or their own)
    values: {
        type: 'array',
        description: 'What values guide your path?',
        examples: ['sovereignty', 'organic_rhythm', 'unknown_revealed', 'reclamation']
    },

    // Current interests
    interests: {
        type: 'array',
        description: 'What topics/creators/ideas currently resonate?',
        examples: ['Bjork', 'architecture', 'sacred geometry', 'underground music']
    },

    // Era affinity
    era_affinity: {
        type: 'array',
        description: 'What time periods speak to you?',
        examples: ['1970s experimental', '1990s electronic', 'ancient philosophy']
    },

    // What they want to avoid
    not_this: {
        type: 'array',
        description: 'What do you explicitly NOT want suggested?',
        examples: ['mainstream pop', 'corporate art', 'extraction apologists']
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// EXPANSION ENGINE
// ═══════════════════════════════════════════════════════════════════════════

class ExpansionEngine {
    constructor() {
        this.userPurpose = null;
        this.inferenceWeb = new Map();
        this.expansionHistory = [];
        this.relevanceScores = new Map();
    }

    /**
     * Initialize with user's purpose and seed data
     *
     * @param {Object} purpose - User's stated purpose using PURPOSE_TEMPLATE
     * @param {Object} seedData - User's behavioral seed data
     */
    initialize(purpose, seedData) {
        this.userPurpose = purpose;
        this.seedData = seedData;

        // Build initial inference web from purpose
        this._buildInferenceWeb();

        return {
            initialized: true,
            purpose: this.userPurpose.becoming,
            values: this.userPurpose.values,
            inferenceNodes: this.inferenceWeb.size
        };
    }

    /**
     * Build the inference web from user's purpose and interests
     */
    _buildInferenceWeb() {
        if (!this.userPurpose) return;

        // Add values as core nodes
        for (const value of (this.userPurpose.values || [])) {
            this._addNode(value, 'value', PHI);
        }

        // Add interests as connected nodes
        for (const interest of (this.userPurpose.interests || [])) {
            this._addNode(interest, 'interest', 1.0);

            // Connect interests to values
            for (const value of (this.userPurpose.values || [])) {
                this._addConnection(interest, value, 0.5);
            }
        }

        // Add era context
        for (const era of (this.userPurpose.era_affinity || [])) {
            this._addNode(era, 'era', 1 / PHI);
        }
    }

    /**
     * Add a node to the inference web
     */
    _addNode(name, type, weight) {
        const key = name.toLowerCase().replace(/\s+/g, '_');
        this.inferenceWeb.set(key, {
            name: name,
            type: type,
            weight: weight,
            connections: [],
            exploredCount: 0,
            lastExplored: null
        });
    }

    /**
     * Add a connection between nodes
     */
    _addConnection(from, to, strength) {
        const fromKey = from.toLowerCase().replace(/\s+/g, '_');
        const toKey = to.toLowerCase().replace(/\s+/g, '_');

        const fromNode = this.inferenceWeb.get(fromKey);
        if (fromNode) {
            fromNode.connections.push({ to: toKey, strength: strength });
        }
    }

    /**
     * Get expansion suggestions based on user's current state
     *
     * @param {Object} currentContext - What the user is currently exploring
     * @param {number} count - Number of suggestions to return
     * @returns {Array} Expansion suggestions
     */
    getExpansions(currentContext = {}, count = 5) {
        if (!this.userPurpose) {
            return {
                error: 'Purpose not initialized. Call initialize() first.',
                suggestions: []
            };
        }

        const suggestions = [];

        // Get expansions of each type
        for (const [typeName, typeConfig] of Object.entries(EXPANSION_TYPES)) {
            const expansion = this._generateExpansion(typeName, typeConfig, currentContext);
            if (expansion) {
                suggestions.push(expansion);
            }
        }

        // Filter through North Star alignment
        const aligned = suggestions.filter(s => this._checkNorthStarAlignment(s));

        // Filter out explicit "not_this" items
        const filtered = aligned.filter(s => !this._isExcluded(s));

        // Sort by relevance to user's trajectory
        filtered.sort((a, b) => b.trajectoryScore - a.trajectoryScore);

        // Apply golden ratio distribution to results
        const distributed = this._applyGoldenDistribution(filtered, count);

        // BALANCE PRINCIPLE: Ensure both polarities are represented
        // This prevents echo chambers and ensures wholeness
        const balanced = this._applyBalancePrinciple(distributed);

        // Log expansion for learning
        this._logExpansion(balanced);

        return {
            purpose: this.userPurpose.becoming,
            currentContext: currentContext,
            suggestions: balanced,
            totalConsidered: suggestions.length,
            alignedCount: aligned.length,
            balanceApplied: true,
            balanceStatus: balanceEngine.getBalanceStatus()
        };
    }

    /**
     * Generate an expansion suggestion of a specific type
     */
    _generateExpansion(typeName, typeConfig, currentContext) {
        // This would connect to actual knowledge bases in production
        // For now, return structure showing what would be suggested

        const expansion = {
            type: typeName,
            typeDescription: typeConfig.description,
            weight: typeConfig.weight,
            suggestion: null,
            reason: null,
            trajectoryScore: 0,
            explorationPath: []
        };

        // Calculate trajectory score based on:
        // 1. Alignment with values
        // 2. Distance from current interests (not too far, not too close)
        // 3. Freshness (not recently explored)

        const valueAlignment = this._calculateValueAlignment(currentContext);
        const noveltyScore = this._calculateNovelty(currentContext);
        const trajectoryFit = this._calculateTrajectoryFit(currentContext);

        expansion.trajectoryScore = (
            valueAlignment * PHI +
            noveltyScore * (1 / PHI) +
            trajectoryFit
        ) / 3;

        return expansion;
    }

    /**
     * Calculate how well something aligns with user's values
     */
    _calculateValueAlignment(context) {
        if (!this.userPurpose || !this.userPurpose.values) return 0.5;

        // In production, this would do semantic matching
        // For now, return base alignment
        return 0.7;
    }

    /**
     * Calculate novelty - how new is this to the user
     */
    _calculateNovelty(context) {
        // Check if context items exist in inference web
        // Higher novelty = less explored
        const contextKey = JSON.stringify(context).toLowerCase();

        let exploredCount = 0;
        for (const [key, node] of this.inferenceWeb) {
            if (contextKey.includes(key)) {
                exploredCount += node.exploredCount;
            }
        }

        // Novelty decreases with exploration, but never to zero
        return Math.max(0.2, 1 - (exploredCount * 0.1));
    }

    /**
     * Calculate how well this serves the user's trajectory toward becoming
     */
    _calculateTrajectoryFit(context) {
        if (!this.userPurpose || !this.userPurpose.becoming) return 0.5;

        // In production, this would use the PQS vertex as target
        // and calculate distance from current state to optimal state
        return 0.6;
    }

    /**
     * Check if suggestion aligns with North Star principles
     */
    _checkNorthStarAlignment(suggestion) {
        // Suggestion must not violate any North Star principle

        // Check for extraction patterns
        const suggestionString = JSON.stringify(suggestion).toLowerCase();

        const extractionPatterns = [
            'engagement_optimize',
            'attention_harvest',
            'data_extract',
            'platform_benefit'
        ];

        for (const pattern of extractionPatterns) {
            if (suggestionString.includes(pattern)) {
                return false;
            }
        }

        return true;
    }

    /**
     * Check if suggestion is in user's "not_this" list
     */
    _isExcluded(suggestion) {
        if (!this.userPurpose || !this.userPurpose.not_this) return false;

        const suggestionString = JSON.stringify(suggestion).toLowerCase();

        for (const excluded of this.userPurpose.not_this) {
            if (suggestionString.includes(excluded.toLowerCase())) {
                return true;
            }
        }

        return false;
    }

    /**
     * Apply balance principle to ensure both polarities are represented
     * This is the MIRROR PRINCIPLE - true understanding requires both
     *
     * @param {Array} suggestions - Suggestions to balance
     * @returns {Array} Balanced suggestions with both polarities
     */
    _applyBalancePrinciple(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            return suggestions;
        }

        // Detect polarity based on suggestion content
        const polarityDetector = (suggestion) => {
            const content = JSON.stringify(suggestion).toLowerCase();

            // Check against known feminine lineage names
            const feminineMarkers = ['rand', 'starhawk', 'tori', 'amos', 'bjork'];
            // Check against known masculine lineage names
            const masculineMarkers = ['fuller', 'prince', 'coltrane', 'bowie'];

            for (const marker of feminineMarkers) {
                if (content.includes(marker)) return 'feminine';
            }
            for (const marker of masculineMarkers) {
                if (content.includes(marker)) return 'masculine';
            }

            // Check for theme-based polarity detection
            // This expands beyond the eight lineages
            const feminineThemes = ['intuition', 'receptive', 'cyclical', 'web', 'spiral'];
            const masculineThemes = ['rational', 'projective', 'linear', 'structure', 'geometry'];

            for (const theme of feminineThemes) {
                if (content.includes(theme)) return 'feminine';
            }
            for (const theme of masculineThemes) {
                if (content.includes(theme)) return 'masculine';
            }

            return 'neutral';
        };

        // Apply balance through the balance engine
        const balanced = balanceEngine.ensureBalance(suggestions, polarityDetector);

        // Add mirror suggestions if imbalanced
        if (balanced.balanceNote) {
            // The balance is skewed - add mirror information
            const balanceStatus = balanceEngine.getBalanceStatus();
            balanced.mirrorReminder = {
                message: balanced.balanceNote,
                currentRatio: balanceStatus.overall.ratio,
                threshold: BALANCE_CONFIG.IMBALANCE_THRESHOLD,
                principle: 'Wholeness through complementary polarities'
            };
        }

        return balanced;
    }

    /**
     * Apply golden ratio distribution to results
     * More relevant items get more "space"
     */
    _applyGoldenDistribution(items, count) {
        const result = [];
        let remaining = items.slice();

        for (let i = 0; i < count && remaining.length > 0; i++) {
            // Golden angle determines selection pattern
            const angle = (i * GOLDEN_ANGLE) % 360;
            const index = Math.floor((angle / 360) * remaining.length);

            result.push(remaining[index]);
            remaining.splice(index, 1);
        }

        return result;
    }

    /**
     * Log expansion for learning
     */
    _logExpansion(suggestions) {
        this.expansionHistory.push({
            timestamp: Date.now(),
            suggestions: suggestions.map(s => ({
                type: s.type,
                trajectoryScore: s.trajectoryScore
            }))
        });

        // Update explored counts
        for (const suggestion of suggestions) {
            const key = (suggestion.suggestion || '').toLowerCase().replace(/\s+/g, '_');
            const node = this.inferenceWeb.get(key);
            if (node) {
                node.exploredCount++;
                node.lastExplored = Date.now();
            }
        }
    }

    /**
     * Record user's response to a suggestion
     * This trains the relevance scoring
     *
     * @param {string} suggestionId - Which suggestion
     * @param {string} response - 'explored', 'saved', 'dismissed', 'loved'
     */
    recordResponse(suggestionId, response) {
        const weights = {
            explored: 0.3,
            saved: 0.7,
            dismissed: -0.3,
            loved: 1.0
        };

        const weight = weights[response] || 0;

        // Update relevance score
        const currentScore = this.relevanceScores.get(suggestionId) || 0.5;
        const newScore = Math.max(0, Math.min(1,
            currentScore + (weight * (1 / PHI))
        ));

        this.relevanceScores.set(suggestionId, newScore);

        // If loved, strengthen connections in inference web
        if (response === 'loved') {
            this._strengthenConnections(suggestionId);
        }

        // If dismissed, weaken but don't sever
        if (response === 'dismissed') {
            this._weakenConnections(suggestionId);
        }

        return {
            suggestionId: suggestionId,
            response: response,
            newRelevanceScore: newScore
        };
    }

    /**
     * Strengthen connections to a loved suggestion
     */
    _strengthenConnections(suggestionId) {
        const key = suggestionId.toLowerCase().replace(/\s+/g, '_');
        const node = this.inferenceWeb.get(key);

        if (node) {
            // Increase weight
            node.weight = Math.min(PHI * PHI, node.weight * PHI);

            // Strengthen all connections
            for (const conn of node.connections) {
                conn.strength = Math.min(1.0, conn.strength * PHI);
            }
        }
    }

    /**
     * Weaken connections to a dismissed suggestion
     */
    _weakenConnections(suggestionId) {
        const key = suggestionId.toLowerCase().replace(/\s+/g, '_');
        const node = this.inferenceWeb.get(key);

        if (node) {
            // Decrease weight but never below minimum
            node.weight = Math.max(0.1, node.weight / PHI);

            // Weaken connections but don't sever
            for (const conn of node.connections) {
                conn.strength = Math.max(0.1, conn.strength / PHI);
            }
        }
    }

    /**
     * Get user's expansion profile
     * Shows how their interests have grown
     */
    getExpansionProfile() {
        return {
            purpose: this.userPurpose?.becoming,
            values: this.userPurpose?.values,
            inferenceWebSize: this.inferenceWeb.size,
            expansionCount: this.expansionHistory.length,
            topRelevanceScores: Array.from(this.relevanceScores.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10),
            recentExpansions: this.expansionHistory.slice(-5)
        };
    }

    /**
     * Export the trained inference web
     * User owns their expansion model
     */
    exportInferenceWeb() {
        return {
            purpose: this.userPurpose,
            web: Array.from(this.inferenceWeb.entries()),
            relevanceScores: Array.from(this.relevanceScores.entries()),
            history: this.expansionHistory,
            exportedAt: Date.now()
        };
    }

    /**
     * Import a previously exported inference web
     */
    importInferenceWeb(exported) {
        this.userPurpose = exported.purpose;
        this.inferenceWeb = new Map(exported.web);
        this.relevanceScores = new Map(exported.relevanceScores);
        this.expansionHistory = exported.history || [];

        return {
            imported: true,
            nodes: this.inferenceWeb.size,
            scores: this.relevanceScores.size
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// TRAJECTORY CALCULATOR
// Calculates user's path toward their vertex (optimal state)
// ═══════════════════════════════════════════════════════════════════════════

class TrajectoryCalculator {
    constructor(pqsEngine) {
        this.pqs = pqsEngine;
    }

    /**
     * Calculate how a suggestion serves the user's trajectory
     *
     * @param {Object} suggestion - The expansion suggestion
     * @param {Object} currentState - User's current state
     * @param {Object} vertex - User's optimal state (from PQS)
     * @returns {number} Trajectory score (0-1)
     */
    calculateTrajectoryFit(suggestion, currentState, vertex) {
        if (!vertex) return 0.5;

        // In the PQS model, the vertex is the optimal state
        // We want suggestions that move the user TOWARD the vertex

        // Calculate current distance from vertex
        const currentDistance = this._distanceFromVertex(currentState, vertex);

        // Estimate distance after exploring suggestion
        const projectedState = this._projectState(currentState, suggestion);
        const projectedDistance = this._distanceFromVertex(projectedState, vertex);

        // Good suggestions reduce distance to vertex
        if (projectedDistance < currentDistance) {
            return Math.min(1.0, (currentDistance - projectedDistance) / currentDistance + 0.5);
        } else {
            // Suggestions that move away from vertex still get some score
            // (exploration has value), but less
            return Math.max(0.2, 0.5 - (projectedDistance - currentDistance) / currentDistance);
        }
    }

    /**
     * Calculate distance from vertex in behavioral space
     */
    _distanceFromVertex(state, vertex) {
        // Simplified distance calculation
        // In production, this would use the full PQS mathematical model
        let distance = 0;
        let count = 0;

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === 'number' && vertex[key] !== undefined) {
                distance += Math.abs(value - vertex[key]);
                count++;
            }
        }

        return count > 0 ? distance / count : 1;
    }

    /**
     * Project what the state would be after exploring a suggestion
     */
    _projectState(currentState, suggestion) {
        // Simplified projection
        // In production, this would model the behavioral change
        return {
            ...currentState,
            exploration_depth: (currentState.exploration_depth || 0) + 0.1,
            value_alignment: (currentState.value_alignment || 0.5) + (suggestion.trajectoryScore * 0.1)
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCES
// ═══════════════════════════════════════════════════════════════════════════

const expansionEngine = new ExpansionEngine();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    ExpansionEngine,
    TrajectoryCalculator,
    expansionEngine,
    EXPANSION_TYPES,
    PURPOSE_TEMPLATE
};

export default expansionEngine;
