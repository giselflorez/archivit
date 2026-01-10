/**
 * CREATIVE ENGINE
 * ================
 * Breath-Rhythm Seeds & Creative Leap Algorithms
 *
 * INSPIRATIONAL REFERENCES:
 *
 * BREATH AS STRUCTURE:
 * Tori Amos's live performances demonstrate breath as a structural element -
 * inhales and exhales creating rhythm, pauses creating tension, the organic
 * timing of human respiration as a seed for musical evolution. Her piano
 * improvisations breathe with the performer.
 *
 * CREATIVE LEAPS:
 * Bjork's documented career (Debut 1993 → Utopia 2017) demonstrates
 * radical reinvention across albums - electronic, orchestral, a cappella,
 * nature-technology fusion, custom instruments, app-based music (Biophilia).
 * Each work reveals unknown territories.
 *
 * ARCHITECTURAL APPLICATION:
 * These patterns translate into mechanical functions that:
 * - Use breath-like rhythms to seed layout generation
 * - Apply algorithmic "leaps" to skip expected solutions
 * - Reveal possibilities the user hasn't considered
 * - Expand creative output beyond conventional patterns
 */

import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';
import { wiringManager } from './authority_matrix.js';

// ═══════════════════════════════════════════════════════════════════════════
// BREATH RHYTHM CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const BREATH_PATTERNS = Object.freeze({
    // Natural breathing rhythms (in relative units)
    // Based on documented respiratory patterns in musical performance

    RESTING: {
        inhale: 1.0,
        hold: 0.2,
        exhale: 1.2,
        pause: 0.3,
        cycle: 2.7,
        description: 'Calm, contemplative pacing'
    },

    ACTIVE: {
        inhale: 0.6,
        hold: 0.1,
        exhale: 0.5,
        pause: 0.1,
        cycle: 1.3,
        description: 'Energetic, driving rhythm'
    },

    DRAMATIC: {
        inhale: 1.5,
        hold: 0.8,
        exhale: 2.0,
        pause: 0.5,
        cycle: 4.8,
        description: 'Tension and release'
    },

    WHISPER: {
        inhale: 0.4,
        hold: 0.0,
        exhale: 1.8,
        pause: 0.6,
        cycle: 2.8,
        description: 'Intimate, extended release'
    },

    GASP: {
        inhale: 0.2,
        hold: 0.0,
        exhale: 0.3,
        pause: 1.5,
        cycle: 2.0,
        description: 'Sudden intake, long silence'
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// CREATIVE LEAP PATTERNS
// ═══════════════════════════════════════════════════════════════════════════

const LEAP_PATTERNS = Object.freeze({
    // Inspired by documented career transformations

    REINVENTION: {
        factor: PHI * PHI,  // ~2.618 - major leap
        direction: 'orthogonal',  // Perpendicular to current trajectory
        description: 'Complete creative reset while maintaining identity'
    },

    SYNTHESIS: {
        factor: PHI,  // ~1.618 - golden expansion
        direction: 'convergent',  // Bringing disparate elements together
        description: 'Fusion of seemingly incompatible elements'
    },

    SUBTRACTION: {
        factor: 1 / PHI,  // ~0.618 - golden reduction
        direction: 'inward',  // Stripping to essence
        description: 'Removing until only essential remains'
    },

    NATURE_TECH: {
        factor: Math.sqrt(PHI),  // ~1.272 - organic growth
        direction: 'organic',  // Natural pattern integration
        description: 'Biological patterns in technological contexts'
    },

    UNKNOWN: {
        factor: Math.PI / PHI,  // ~1.941 - irrational exploration
        direction: 'undefined',  // Direction emerges during leap
        description: 'Venturing into unmapped territory'
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// BREATH RHYTHM GENERATOR
// ═══════════════════════════════════════════════════════════════════════════

class BreathRhythmGenerator {
    constructor(seedOffset = 0) {
        this.seedOffset = seedOffset;
        this.currentPhase = 'inhale';
        this.phaseProgress = 0;
        this.cycleCount = 0;
        this.pattern = BREATH_PATTERNS.RESTING;
    }

    /**
     * Set breathing pattern based on context
     *
     * @param {string} context - Query context or mood
     * @returns {Object} Selected pattern
     */
    setPatternFromContext(context) {
        const contextLower = (context || '').toLowerCase();

        if (contextLower.includes('calm') || contextLower.includes('peaceful')) {
            this.pattern = BREATH_PATTERNS.RESTING;
        } else if (contextLower.includes('energy') || contextLower.includes('fast')) {
            this.pattern = BREATH_PATTERNS.ACTIVE;
        } else if (contextLower.includes('dramatic') || contextLower.includes('intense')) {
            this.pattern = BREATH_PATTERNS.DRAMATIC;
        } else if (contextLower.includes('quiet') || contextLower.includes('intimate')) {
            this.pattern = BREATH_PATTERNS.WHISPER;
        } else if (contextLower.includes('surprise') || contextLower.includes('sudden')) {
            this.pattern = BREATH_PATTERNS.GASP;
        } else {
            // Default: blend based on seed
            this.pattern = this._blendPatterns();
        }

        return this.pattern;
    }

    /**
     * Blend patterns based on seed for unique rhythm
     */
    _blendPatterns() {
        const patterns = Object.values(BREATH_PATTERNS);
        const index = this.seedOffset % patterns.length;
        const blend = (this.seedOffset / 1000) % 1;  // 0-1 blend factor

        const base = patterns[index];
        const next = patterns[(index + 1) % patterns.length];

        return {
            inhale: base.inhale * (1 - blend) + next.inhale * blend,
            hold: base.hold * (1 - blend) + next.hold * blend,
            exhale: base.exhale * (1 - blend) + next.exhale * blend,
            pause: base.pause * (1 - blend) + next.pause * blend,
            cycle: base.cycle * (1 - blend) + next.cycle * blend,
            description: `Blended rhythm (${Math.round(blend * 100)}% transition)`
        };
    }

    /**
     * Generate layout spacing based on breath rhythm
     *
     * @param {number} elementCount - Number of elements to space
     * @returns {Array} Array of spacing values
     */
    generateSpacing(elementCount) {
        const spacing = [];
        const phases = ['inhale', 'hold', 'exhale', 'pause'];

        for (let i = 0; i < elementCount; i++) {
            const phaseIndex = i % phases.length;
            const phase = phases[phaseIndex];
            const phaseValue = this.pattern[phase];

            // Apply golden variation within phase
            const variation = 1 + (Math.sin(i * GOLDEN_ANGLE * Math.PI / 180) * 0.2);
            spacing.push(phaseValue * variation);
        }

        return spacing;
    }

    /**
     * Generate timing sequence for animations
     *
     * @param {number} durationMs - Total duration in milliseconds
     * @param {number} keyframeCount - Number of keyframes
     * @returns {Array} Keyframe timing array
     */
    generateTiming(durationMs, keyframeCount) {
        const timing = [];
        const cycleLength = this.pattern.cycle;
        let accumulated = 0;

        for (let i = 0; i < keyframeCount; i++) {
            const phases = ['inhale', 'hold', 'exhale', 'pause'];
            const phase = phases[i % phases.length];
            const phaseDuration = this.pattern[phase] / cycleLength;

            timing.push({
                offset: accumulated,
                duration: phaseDuration,
                phase: phase,
                easing: this._getPhaseEasing(phase)
            });

            accumulated += phaseDuration;
            if (accumulated >= 1) accumulated = 0;
        }

        // Normalize to actual duration
        return timing.map(t => ({
            ...t,
            offsetMs: t.offset * durationMs,
            durationMs: t.duration * durationMs
        }));
    }

    /**
     * Get appropriate easing for each breath phase
     */
    _getPhaseEasing(phase) {
        const easings = {
            inhale: 'cubic-bezier(0.4, 0, 0.2, 1)',   // Ease out - gradual intake
            hold: 'linear',                            // Steady hold
            exhale: 'cubic-bezier(0.4, 0, 0.6, 1)',   // Slow release
            pause: 'cubic-bezier(0.2, 0, 0.4, 1)'     // Gentle return
        };
        return easings[phase] || 'linear';
    }

    /**
     * Generate grid proportions based on breath
     *
     * @param {number} columns - Number of columns
     * @param {number} rows - Number of rows
     * @returns {Object} Grid proportions
     */
    generateGridProportions(columns, rows) {
        const colWidths = [];
        const rowHeights = [];

        // Columns follow inhale-exhale pattern
        for (let c = 0; c < columns; c++) {
            const isInhale = c % 2 === 0;
            const base = isInhale ? this.pattern.inhale : this.pattern.exhale;
            const variation = 1 + (Math.cos(c * GOLDEN_ANGLE * Math.PI / 180) * 0.15);
            colWidths.push(base * variation);
        }

        // Rows follow hold-pause pattern (more subtle)
        for (let r = 0; r < rows; r++) {
            const isHold = r % 2 === 0;
            const base = isHold ? this.pattern.hold + 0.5 : this.pattern.pause + 0.5;
            const variation = 1 + (Math.sin(r * GOLDEN_ANGLE * Math.PI / 180) * 0.1);
            rowHeights.push(base * variation);
        }

        // Normalize to percentages
        const totalWidth = colWidths.reduce((a, b) => a + b, 0);
        const totalHeight = rowHeights.reduce((a, b) => a + b, 0);

        return {
            columns: colWidths.map(w => (w / totalWidth * 100).toFixed(2) + '%'),
            rows: rowHeights.map(h => (h / totalHeight * 100).toFixed(2) + '%'),
            pattern: this.pattern.description
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// CREATIVE LEAP ALGORITHM
// ═══════════════════════════════════════════════════════════════════════════

class CreativeLeapAlgorithm {
    constructor(userProfile = null) {
        this.userProfile = userProfile;
        this.leapHistory = [];
        this.discoveredTerritories = new Set();
    }

    /**
     * Calculate a creative leap from current position
     *
     * @param {Object} currentState - Current creative position
     * @param {string} leapType - Type of leap to attempt
     * @returns {Object} New creative position
     */
    calculateLeap(currentState, leapType = 'UNKNOWN') {
        const pattern = LEAP_PATTERNS[leapType] || LEAP_PATTERNS.UNKNOWN;

        const leap = {
            from: { ...currentState },
            pattern: pattern,
            factor: pattern.factor,
            direction: pattern.direction,
            timestamp: Date.now()
        };

        // Calculate new position based on leap type
        switch (pattern.direction) {
            case 'orthogonal':
                leap.to = this._orthogonalLeap(currentState, pattern.factor);
                break;
            case 'convergent':
                leap.to = this._convergentLeap(currentState, pattern.factor);
                break;
            case 'inward':
                leap.to = this._inwardLeap(currentState, pattern.factor);
                break;
            case 'organic':
                leap.to = this._organicLeap(currentState, pattern.factor);
                break;
            case 'undefined':
            default:
                leap.to = this._unknownLeap(currentState, pattern.factor);
                break;
        }

        this.leapHistory.push(leap);
        return leap;
    }

    /**
     * Orthogonal leap - perpendicular to current trajectory
     * Complete reinvention while maintaining identity core
     */
    _orthogonalLeap(state, factor) {
        const newState = {};

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === 'number') {
                // Rotate 90 degrees in value space
                const angle = Math.PI / 2;  // 90 degrees
                const newValue = value * Math.cos(angle) * factor;
                newState[key] = newValue;
            } else if (Array.isArray(value)) {
                // Reverse and scale
                newState[key] = value.slice().reverse().map(v =>
                    typeof v === 'number' ? v * factor : v
                );
            } else {
                newState[key] = value;
            }
        }

        newState._leapType = 'orthogonal';
        newState._description = 'Complete creative reset - perpendicular trajectory';
        return newState;
    }

    /**
     * Convergent leap - synthesis of disparate elements
     */
    _convergentLeap(state, factor) {
        const newState = {};
        const keys = Object.keys(state).filter(k => typeof state[k] === 'number');

        // Calculate centroid of all numeric values
        const centroid = keys.reduce((sum, k) => sum + state[k], 0) / keys.length;

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === 'number') {
                // Pull toward centroid by factor
                const distance = value - centroid;
                newState[key] = centroid + (distance / factor);
            } else {
                newState[key] = value;
            }
        }

        newState._leapType = 'convergent';
        newState._description = 'Synthesis - bringing elements toward common center';
        return newState;
    }

    /**
     * Inward leap - subtraction to essence
     */
    _inwardLeap(state, factor) {
        const newState = {};

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === 'number') {
                // Reduce by inverse golden ratio
                newState[key] = value * factor;
            } else if (Array.isArray(value)) {
                // Keep only golden ratio portion
                const keepCount = Math.ceil(value.length * factor);
                newState[key] = value.slice(0, keepCount);
            } else {
                newState[key] = value;
            }
        }

        newState._leapType = 'inward';
        newState._description = 'Reduction to essence - removing non-essential';
        return newState;
    }

    /**
     * Organic leap - nature patterns in structure
     */
    _organicLeap(state, factor) {
        const newState = {};

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === 'number') {
                // Apply golden spiral growth
                const theta = value * GOLDEN_ANGLE * Math.PI / 180;
                const r = Math.pow(PHI, theta / (Math.PI * 2));
                newState[key] = r * factor;
            } else if (Array.isArray(value)) {
                // Distribute along golden angle
                newState[key] = value.map((v, i) => {
                    if (typeof v === 'number') {
                        const angle = i * GOLDEN_ANGLE * Math.PI / 180;
                        return v * (1 + Math.sin(angle) * (factor - 1));
                    }
                    return v;
                });
            } else {
                newState[key] = value;
            }
        }

        newState._leapType = 'organic';
        newState._description = 'Natural growth patterns - biological integration';
        return newState;
    }

    /**
     * Unknown leap - venture into unmapped territory
     */
    _unknownLeap(state, factor) {
        const newState = {};

        // Use a combination of all patterns with random weighting
        const weights = this._generateUnknownWeights();

        for (const [key, value] of Object.entries(state)) {
            if (typeof value === 'number') {
                let accumulated = value;

                // Apply weighted combination of all transformations
                accumulated *= Math.cos(Math.PI / 2) * weights.orthogonal;
                accumulated += (value - accumulated) * weights.convergent;
                accumulated *= (1 / PHI) * weights.inward + (1 - weights.inward);
                accumulated *= (1 + Math.sin(GOLDEN_ANGLE * Math.PI / 180) * weights.organic);

                newState[key] = accumulated * factor;
            } else {
                newState[key] = value;
            }
        }

        newState._leapType = 'unknown';
        newState._description = 'Exploration of unmapped creative territory';
        newState._weights = weights;
        return newState;
    }

    /**
     * Generate weights for unknown leap
     */
    _generateUnknownWeights() {
        // Use golden ratio to create non-repeating but deterministic weights
        const seed = Date.now() % 1000 / 1000;

        return {
            orthogonal: (seed * PHI) % 1,
            convergent: ((seed + 0.25) * PHI) % 1,
            inward: ((seed + 0.5) * PHI) % 1,
            organic: ((seed + 0.75) * PHI) % 1
        };
    }

    /**
     * Reveal possibilities the user hasn't considered
     *
     * @param {Object} userState - Current user creative state
     * @param {number} count - Number of possibilities to reveal
     * @returns {Array} Array of unexplored possibilities
     */
    revealPossibilities(userState, count = 5) {
        const possibilities = [];

        // Apply each leap type
        for (const leapType of Object.keys(LEAP_PATTERNS)) {
            if (possibilities.length >= count) break;

            const leap = this.calculateLeap(userState, leapType);

            // Check if this territory has been discovered before
            const territoryKey = this._hashState(leap.to);
            if (!this.discoveredTerritories.has(territoryKey)) {
                this.discoveredTerritories.add(territoryKey);

                possibilities.push({
                    type: leapType,
                    description: LEAP_PATTERNS[leapType].description,
                    result: leap.to,
                    novelty: this._calculateNovelty(leap.to, userState),
                    recommendation: this._generateRecommendation(leapType, leap.to)
                });
            }
        }

        // Sort by novelty
        possibilities.sort((a, b) => b.novelty - a.novelty);

        return possibilities.slice(0, count);
    }

    /**
     * Calculate novelty score of a creative state
     */
    _calculateNovelty(newState, currentState) {
        let distance = 0;
        let count = 0;

        for (const [key, value] of Object.entries(newState)) {
            if (typeof value === 'number' && typeof currentState[key] === 'number') {
                distance += Math.abs(value - currentState[key]);
                count++;
            }
        }

        return count > 0 ? distance / count : 0;
    }

    /**
     * Generate human-readable recommendation
     */
    _generateRecommendation(leapType, result) {
        const recommendations = {
            REINVENTION: 'Consider a complete creative reset - maintain your core identity while exploring a perpendicular direction',
            SYNTHESIS: 'Try bringing together elements that seem incompatible - find the unexpected harmony',
            SUBTRACTION: 'Remove elements until only the essential remains - less can reveal more',
            NATURE_TECH: 'Look to natural patterns - spirals, branches, waves - as structural inspiration',
            UNKNOWN: 'Venture beyond your mapped territory - the unexplored holds discoveries'
        };

        return recommendations[leapType] || 'Explore this creative direction';
    }

    /**
     * Hash state for territory tracking
     */
    _hashState(state) {
        const values = Object.entries(state)
            .filter(([k, v]) => typeof v === 'number' && !k.startsWith('_'))
            .map(([k, v]) => `${k}:${v.toFixed(2)}`)
            .sort()
            .join('|');

        let hash = 0;
        for (let i = 0; i < values.length; i++) {
            hash = ((hash << 5) - hash) + values.charCodeAt(i);
            hash = hash & hash;
        }
        return hash.toString(16);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// CREATIVE OUTPUT GENERATOR
// ═══════════════════════════════════════════════════════════════════════════

class CreativeOutputGenerator {
    constructor(seedOffset = 0) {
        this.breathGenerator = new BreathRhythmGenerator(seedOffset);
        this.leapAlgorithm = new CreativeLeapAlgorithm();
        this.seedOffset = seedOffset;
    }

    /**
     * Check if breath rhythm should apply to a specific target
     * Respects founder wiring configuration
     */
    _shouldApplyBreathRhythm(target) {
        try {
            return wiringManager.shouldFeedInto('breath_rhythm', target);
        } catch (e) {
            // If wiring manager not available, use default behavior
            return target === 'layout_spacing';
        }
    }

    /**
     * Check if creative leap should apply to a specific target
     * Respects founder wiring configuration
     */
    _shouldApplyCreativeLeap(target) {
        try {
            return wiringManager.shouldFeedInto('creative_leap', target);
        } catch (e) {
            // If wiring manager not available, use default behavior
            return target === 'layout_generation';
        }
    }

    /**
     * Get current wiring state for transparency
     */
    getWiringState() {
        try {
            return {
                breath_rhythm: wiringManager.getWiring('breath_rhythm'),
                creative_leap: wiringManager.getWiring('creative_leap'),
                spiral_compression: wiringManager.getWiring('spiral_compression')
            };
        } catch (e) {
            return { error: 'Wiring manager not available' };
        }
    }

    /**
     * Generate a creative layout based on query context
     * Respects wiring configuration - components only apply if wired to layout
     *
     * @param {Object} options - Generation options
     * @returns {Object} Complete layout specification
     */
    generateLayout(options = {}) {
        const {
            context = '',
            elementCount = 12,
            columns = 3,
            rows = 4,
            includeLeaps = true
        } = options;

        // Check wiring - only apply breath rhythm if wired to layout
        const applyBreathToLayout = this._shouldApplyBreathRhythm('layout_spacing');
        const applyLeapsToLayout = this._shouldApplyCreativeLeap('layout_generation');

        // Set breath pattern from context
        const breathPattern = this.breathGenerator.setPatternFromContext(context);

        // Generate base layout
        const layout = {
            // Include breath data regardless (for other uses), but mark if applied to layout
            breath: {
                pattern: breathPattern,
                spacing: this.breathGenerator.generateSpacing(elementCount),
                grid: this.breathGenerator.generateGridProportions(columns, rows),
                timing: this.breathGenerator.generateTiming(3000, elementCount),
                appliedToLayout: applyBreathToLayout
            },
            elements: [],
            timestamp: Date.now(),
            wiring: {
                breathRhythmActive: applyBreathToLayout,
                creativeLeapActive: applyLeapsToLayout
            }
        };

        // Generate elements - use breath-based positioning only if wired
        for (let i = 0; i < elementCount; i++) {
            const row = Math.floor(i / columns);
            const col = i % columns;

            const element = {
                index: i,
                position: {
                    row: row,
                    column: col
                }
            };

            // Only apply breath rhythm to layout if wired
            if (applyBreathToLayout) {
                element.position.spacing = layout.breath.spacing[i];
                element.timing = layout.breath.timing[i % layout.breath.timing.length];
                element.phase = ['inhale', 'hold', 'exhale', 'pause'][i % 4];
            } else {
                // Use uniform spacing when breath not wired to layout
                element.position.spacing = 1.0;
                element.timing = { offset: i / elementCount, duration: 1 / elementCount };
                element.phase = null;
            }

            layout.elements.push(element);
        }

        // Add creative leaps only if wired to layout generation
        if (includeLeaps && applyLeapsToLayout) {
            const currentState = this._layoutToState(layout);
            layout.possibilities = this.leapAlgorithm.revealPossibilities(currentState, 3);
            layout.leapSuggestion = layout.possibilities[0] || null;
        } else {
            layout.possibilities = [];
            layout.leapSuggestion = null;
        }

        return layout;
    }

    /**
     * Convert layout to state object for leap calculations
     */
    _layoutToState(layout) {
        return {
            columns: layout.breath.grid.columns.length,
            rhythmCycle: layout.breath.pattern.cycle,
            inhaleRatio: layout.breath.pattern.inhale / layout.breath.pattern.cycle,
            exhaleRatio: layout.breath.pattern.exhale / layout.breath.pattern.cycle,
            elementCount: layout.elements.length,
            avgSpacing: layout.breath.spacing.reduce((a, b) => a + b, 0) / layout.breath.spacing.length
        };
    }

    /**
     * Skip to an unexpected creative solution
     *
     * @param {Object} currentLayout - Current layout
     * @param {string} skipType - Type of skip (corresponds to leap types)
     * @returns {Object} New unexpected layout
     */
    skipToUnexpected(currentLayout, skipType = 'UNKNOWN') {
        const currentState = this._layoutToState(currentLayout);
        const leap = this.leapAlgorithm.calculateLeap(currentState, skipType);

        // Apply leap results to generate new layout
        const newOptions = {
            context: leap.to._description || '',
            elementCount: Math.max(4, Math.round(leap.to.elementCount || 12)),
            columns: Math.max(1, Math.round(leap.to.columns || 3)),
            rows: Math.max(1, Math.ceil((leap.to.elementCount || 12) / (leap.to.columns || 3))),
            includeLeaps: true
        };

        const newLayout = this.generateLayout(newOptions);
        newLayout._skipApplied = {
            type: skipType,
            from: currentState,
            to: leap.to,
            description: LEAP_PATTERNS[skipType]?.description || 'Creative skip applied'
        };

        return newLayout;
    }

    /**
     * Reveal what the user might want to see but hasn't considered
     *
     * @param {Object} userProfile - User's behavioral profile
     * @param {Object} currentContext - Current creative context
     * @returns {Array} Revealed possibilities
     */
    revealUnknown(userProfile, currentContext) {
        const revelations = [];

        // Analyze user patterns for gaps
        const patterns = this._analyzeUserPatterns(userProfile);

        // Generate possibilities that fill gaps
        for (const gap of patterns.gaps) {
            const state = { ...currentContext, ...gap.suggested };
            const possibilities = this.leapAlgorithm.revealPossibilities(state, 2);

            for (const possibility of possibilities) {
                revelations.push({
                    type: 'gap_fill',
                    gap: gap.description,
                    possibility: possibility,
                    confidence: gap.confidence
                });
            }
        }

        // Add pure unknown exploration
        const unknownLeap = this.leapAlgorithm.calculateLeap(currentContext, 'UNKNOWN');
        revelations.push({
            type: 'exploration',
            description: 'Territory beyond your current creative map',
            possibility: {
                type: 'UNKNOWN',
                result: unknownLeap.to,
                recommendation: 'Venture here to discover new creative language'
            },
            confidence: 0.5  // Unknown by definition
        });

        return revelations;
    }

    /**
     * Analyze user patterns for creative gaps
     */
    _analyzeUserPatterns(userProfile) {
        const gaps = [];

        if (!userProfile) {
            return {
                gaps: [{
                    description: 'No profile yet - all territories are new',
                    suggested: { elementCount: 12, columns: 3 },
                    confidence: 0.3
                }]
            };
        }

        // Check for unexplored breath patterns
        const usedPatterns = userProfile.usedBreathPatterns || [];
        for (const pattern of Object.keys(BREATH_PATTERNS)) {
            if (!usedPatterns.includes(pattern)) {
                gaps.push({
                    description: `Unexplored rhythm: ${BREATH_PATTERNS[pattern].description}`,
                    suggested: { breathPattern: pattern },
                    confidence: 0.7
                });
            }
        }

        // Check for unexplored leap types
        const usedLeaps = userProfile.usedLeapTypes || [];
        for (const leap of Object.keys(LEAP_PATTERNS)) {
            if (!usedLeaps.includes(leap)) {
                gaps.push({
                    description: `Unexplored creative direction: ${LEAP_PATTERNS[leap].description}`,
                    suggested: { leapType: leap },
                    confidence: 0.6
                });
            }
        }

        return { gaps };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCES
// ═══════════════════════════════════════════════════════════════════════════

let creativeEngine = null;

/**
 * Initialize creative engine with user's seed offset
 */
function initializeCreativeEngine(seedOffset) {
    creativeEngine = new CreativeOutputGenerator(seedOffset);
    return creativeEngine;
}

/**
 * Get or create creative engine
 */
function getCreativeEngine(seedOffset = 0) {
    if (!creativeEngine) {
        creativeEngine = new CreativeOutputGenerator(seedOffset);
    }
    return creativeEngine;
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    BreathRhythmGenerator,
    CreativeLeapAlgorithm,
    CreativeOutputGenerator,
    initializeCreativeEngine,
    getCreativeEngine,
    BREATH_PATTERNS,
    LEAP_PATTERNS
};

export default CreativeOutputGenerator;
