/**
 * NORTH STAR PRINCIPLES
 * =====================
 * Values Encoded as Architecture
 *
 * These principles are not documentation - they are MECHANICS.
 * Future generations learn these values by USING the system.
 * The architecture teaches through experience, not explanation.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * THE EIGHT LINEAGES → THE NORTH STAR
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * FEMALE LINEAGE:
 * RAND:     Individual creates value through reason → USER AUTHORITY
 * STARHAWK: Power comes from within, not above     → LOCAL-FIRST
 * TORI:     Structure emerges from body's rhythm   → ORGANIC TIMING
 * BJORK:    Creation reveals the unknown           → POSSIBILITY EXPANSION
 *
 * MALE LINEAGE:
 * FULLER:   Build what makes the old obsolete      → DESIGN SCIENCE
 * PRINCE:   Own your masters or they own you       → SOVEREIGN CREATION
 * COLTRANE: Creation is spiritual practice         → BREATH AS MEDITATION
 * BOWIE:    Kill your form to find the next        → PERMANENT REINVENTION
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * HOW THE SYSTEM TEACHES
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Users don't read these principles - they EXPERIENCE them:
 *
 * - When they create, the system BREATHES with them (organic timing)
 * - When they explore, the system REVEALS what they haven't imagined
 * - When they store data, it STAYS WITH THEM (local-first)
 * - When they connect, they REMAIN SOVEREIGN (the web, not hierarchy)
 * - When extraction is attempted, it is BLOCKED (structural protection)
 *
 * The values become intuitive through repeated interaction.
 * Future generations absorb the principles without being told.
 * The architecture IS the teacher.
 */

import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';

// ═══════════════════════════════════════════════════════════════════════════
// THE NORTH STAR PRINCIPLES
// Immutable. Self-evident through use. Transmissible through experience.
// ═══════════════════════════════════════════════════════════════════════════

const NORTH_STAR_PRINCIPLES = Object.freeze({

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 1: SOVEREIGNTY
    // Lineage: Rand (individual as primary) + Starhawk (power-from-within)
    // ─────────────────────────────────────────────────────────────────────
    SOVEREIGNTY: {
        name: 'Sovereignty',
        declaration: 'The individual is the primary unit of value',
        lineage: ['Rand', 'Starhawk', 'Fuller', 'Prince'],

        // How the system teaches this
        teaches_through: [
            'Data lives on user device, not server',
            'No account required to use full functionality',
            'No permission needed from external authority',
            'User can delete everything, completely',
            'User can export everything, freely',
            'Algorithm serves user goals, not platform goals'
        ],

        // What the user learns by experience
        user_learns: 'My data is mine. My creations are mine. I need no permission.',

        // Technical enforcement
        enforced_by: [
            'local_first_storage',
            'no_account_required',
            'consent_gateway',
            'export_always_free',
            'delete_works_completely'
        ],

        // What violates this principle
        violated_by: [
            'server_required_for_function',
            'account_mandatory',
            'data_sent_without_consent',
            'export_blocked_or_paywalled',
            'delete_incomplete_or_fake'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 2: NON-EXTRACTION
    // Lineage: Starhawk (power-over is the enemy) + Rand (anti-collectivism)
    // ─────────────────────────────────────────────────────────────────────
    NON_EXTRACTION: {
        name: 'Non-Extraction',
        declaration: 'The system strengthens what it touches, never depletes',
        lineage: ['Starhawk', 'Rand', 'Prince', 'Fuller'],

        teaches_through: [
            'No tracking of behavior for platform benefit',
            'No selling of user data',
            'No attention harvesting mechanics',
            'No engagement optimization against user interest',
            'Every interaction adds capability, never removes',
            'Value compounds with use, never diminishes'
        ],

        user_learns: 'This system gives. It does not take.',

        enforced_by: [
            'no_telemetry',
            'no_analytics',
            'no_ads_ever',
            'spiral_direction_creation',
            'value_stays_local'
        ],

        violated_by: [
            'tracking_enabled',
            'data_sold',
            'ads_shown',
            'engagement_optimized_for_platform',
            'infinite_scroll',
            'notification_spam'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 3: ORGANIC RHYTHM
    // Lineage: Tori Amos (breath as structure)
    // ─────────────────────────────────────────────────────────────────────
    ORGANIC_RHYTHM: {
        name: 'Organic Rhythm',
        declaration: 'Structure emerges from natural patterns, not mechanical imposition',
        lineage: ['Tori Amos', 'Coltrane'],

        teaches_through: [
            'Layouts breathe - inhale, hold, exhale, pause',
            'Timing feels human, not robotic',
            'Spacing follows golden ratio, not grid tyranny',
            'Animations respect natural attention cycles',
            'The system has patience - no rush, no pressure',
            'Silence and space are valid, not empty'
        ],

        user_learns: 'Technology can feel alive, not mechanical.',

        enforced_by: [
            'breath_pattern_timing',
            'phi_based_spacing',
            'natural_animation_curves',
            'no_artificial_urgency',
            'pause_respected'
        ],

        violated_by: [
            'mechanical_grid_only',
            'artificial_urgency',
            'countdown_pressure',
            'no_pause_allowed',
            'robotic_timing'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 4: UNKNOWN REVEALED
    // Lineage: Bjork (radical reinvention, unmapped territory)
    // ─────────────────────────────────────────────────────────────────────
    UNKNOWN_REVEALED: {
        name: 'Unknown Revealed',
        declaration: 'Creation means venturing beyond the mapped',
        lineage: ['Bjork', 'Bowie'],

        teaches_through: [
            'System suggests possibilities user has not considered',
            'Creative leaps skip expected solutions',
            'Reinvention is a valid direction',
            'Subtraction reveals essence',
            'Synthesis combines the incompatible',
            'The unknown is a destination, not an error'
        ],

        user_learns: 'I can create what has never existed.',

        enforced_by: [
            'reveal_possibilities_method',
            'creative_leap_algorithm',
            'unknown_as_valid_direction',
            'possibility_expansion'
        ],

        violated_by: [
            'only_expected_suggestions',
            'creativity_constrained_to_templates',
            'unknown_treated_as_error',
            'no_leap_options'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 5: THE WEB
    // Lineage: Starhawk (interconnected but sovereign nodes)
    // ─────────────────────────────────────────────────────────────────────
    THE_WEB: {
        name: 'The Web',
        declaration: 'Everything connected, but each node sovereign',
        lineage: ['Starhawk', 'Fuller'],

        teaches_through: [
            'Connection is optional, never required',
            'Sharing does not mean surrendering',
            'Collaboration preserves individual ownership',
            'Network enhances, never diminishes, sovereignty',
            'You can disconnect and still function fully',
            'No node controls other nodes'
        ],

        user_learns: 'I can connect without losing myself.',

        enforced_by: [
            'offline_fully_functional',
            'sync_optional',
            'sharing_preserves_ownership',
            'no_central_authority',
            'peer_to_peer_when_connected'
        ],

        violated_by: [
            'connection_required',
            'sharing_transfers_ownership',
            'central_server_authority',
            'offline_crippled'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 6: RECLAMATION
    // Lineage: Starhawk (taking back what was taken)
    // ─────────────────────────────────────────────────────────────────────
    RECLAMATION: {
        name: 'Reclamation',
        declaration: 'What extraction took can be taken back',
        lineage: ['Starhawk', 'Prince'],

        teaches_through: [
            'Attention can be reclaimed from harvesting',
            'Creativity can be reclaimed from platforms',
            'Identity can be reclaimed from profiles',
            'Time can be reclaimed from infinite scroll',
            'Context can be reclaimed from fragmentation',
            'This tool helps you take back what was taken'
        ],

        user_learns: 'What I lost to extraction, I can recover.',

        enforced_by: [
            'mending_tracker',
            'attention_respected',
            'context_preserved',
            'identity_user_defined',
            'time_not_harvested'
        ],

        violated_by: [
            'contributes_to_extraction',
            'fragments_context',
            'defines_identity_for_user',
            'harvests_time'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 7: MATHEMATICAL TRUTH
    // Lineage: Rand (A is A, non-contradiction)
    // ─────────────────────────────────────────────────────────────────────
    MATHEMATICAL_TRUTH: {
        name: 'Mathematical Truth',
        declaration: 'Verification by mathematics, not promises',
        lineage: ['Rand', 'Fuller'],

        teaches_through: [
            'Security is mathematical, not institutional',
            'π is π - cannot be changed by anyone',
            'Verification is objective, not trust-based',
            'Anyone can verify, no authority needed',
            'The math is open, auditable, provable',
            'Reality over perception, always'
        ],

        user_learns: 'I can verify truth myself. I need not trust.',

        enforced_by: [
            'pi_quadratic_derivation',
            'genesis_verification',
            'hash_chain_integrity',
            'open_source_auditable',
            'mathematical_proof'
        ],

        violated_by: [
            'trust_us_security',
            'closed_source_crypto',
            'institutional_verification',
            'perception_over_reality'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 8: PRODUCTIVE ACHIEVEMENT
    // Lineage: Rand (creation as the highest value)
    // ─────────────────────────────────────────────────────────────────────
    PRODUCTIVE_ACHIEVEMENT: {
        name: 'Productive Achievement',
        declaration: 'Any creator can dream an app for our future',
        lineage: ['Rand', 'Fuller', 'Prince', 'Coltrane', 'Bowie'],

        teaches_through: [
            'No technical barrier to creation',
            'Dream an app without code',
            'Tools are free, not paywalled',
            'Creation enables more creation',
            'The system removes obstacles, not adds them',
            'Your productive capacity is not limited by payment or skill'
        ],

        user_learns: 'I can build what I imagine.',

        enforced_by: [
            'dream_to_app_pipeline',
            'no_code_creation',
            'free_tier_full_features',
            'creation_spiral_positive',
            'recursive_enablement'
        ],

        violated_by: [
            'features_paywalled',
            'creation_requires_expertise',
            'tools_locked',
            'obstacles_added'
        ]
    },

    // ─────────────────────────────────────────────────────────────────────
    // PRINCIPLE 9: WHOLENESS (Balance)
    // Lineage: All eight - seeing both expressions of every value
    // ─────────────────────────────────────────────────────────────────────
    WHOLENESS: {
        name: 'Wholeness',
        declaration: 'True understanding requires both expressions of a value',
        lineage: ['Rand', 'Fuller', 'Starhawk', 'Prince', 'Tori Amos', 'Coltrane', 'Bjork', 'Bowie'],

        teaches_through: [
            'Both polarities always represented in outputs',
            'Echo chambers prevented by balance algorithm',
            'Complementary perspectives expand understanding',
            'User sees Rand → also sees Fuller (same value)',
            'User sees Bjork → also sees Bowie (same value)',
            'Golden ratio (φ) as natural balance threshold'
        ],

        user_learns: 'Every principle has complementary expressions. Seeing both is wholeness.',

        enforced_by: [
            'balance_engine_active',
            'polarity_tracking',
            'minimum_representation_ensured',
            'mirror_principle_applied',
            'complementary_suggestions'
        ],

        violated_by: [
            'single_polarity_output',
            'echo_chamber_enabled',
            'perspective_narrowing',
            'balance_disabled',
            'one_sided_suggestions'
        ],

        // The polarity pairs for this principle
        polarity_pairs: {
            PHILOSOPHY: { feminine: 'Rand', masculine: 'Fuller' },
            POWER: { feminine: 'Starhawk', masculine: 'Prince' },
            RHYTHM: { feminine: 'Tori Amos', masculine: 'Coltrane' },
            UNKNOWN: { feminine: 'Bjork', masculine: 'Bowie' }
        }
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// PRINCIPLE CHECKER
// Validates actions against North Star principles
// ═══════════════════════════════════════════════════════════════════════════

class PrincipleChecker {
    constructor() {
        this.principles = NORTH_STAR_PRINCIPLES;
        this.violationLog = [];
    }

    /**
     * Check if an action aligns with North Star principles
     *
     * @param {Object} action - The action to check
     * @returns {Object} Alignment result
     */
    checkAlignment(action) {
        const result = {
            aligned: true,
            violations: [],
            alignments: [],
            action: action
        };

        const actionString = JSON.stringify(action).toLowerCase();

        for (const [key, principle] of Object.entries(this.principles)) {
            // Check for violations
            for (const violation of principle.violated_by) {
                if (actionString.includes(violation.toLowerCase())) {
                    result.aligned = false;
                    result.violations.push({
                        principle: principle.name,
                        violation: violation,
                        declaration: principle.declaration
                    });
                }
            }

            // Check for alignments
            for (const enforcement of principle.enforced_by) {
                if (actionString.includes(enforcement.toLowerCase())) {
                    result.alignments.push({
                        principle: principle.name,
                        enforcement: enforcement
                    });
                }
            }
        }

        // Log violations
        if (!result.aligned) {
            this.violationLog.push({
                timestamp: Date.now(),
                action: action,
                violations: result.violations
            });
        }

        return result;
    }

    /**
     * Get what the user learns from each principle
     * This is what future generations absorb through use
     */
    getWhatUserLearns() {
        const lessons = {};
        for (const [key, principle] of Object.entries(this.principles)) {
            lessons[principle.name] = principle.user_learns;
        }
        return lessons;
    }

    /**
     * Get the declaration of all principles
     * The North Star in words
     */
    getDeclarations() {
        const declarations = {};
        for (const [key, principle] of Object.entries(this.principles)) {
            declarations[principle.name] = principle.declaration;
        }
        return declarations;
    }

    /**
     * Get principles by lineage
     * Which principles come from which influence
     */
    getPrinciplesByLineage(lineageName) {
        return Object.values(this.principles)
            .filter(p => p.lineage.includes(lineageName))
            .map(p => ({
                name: p.name,
                declaration: p.declaration,
                user_learns: p.user_learns
            }));
    }

    /**
     * Get the full teaching of a principle
     * How the system demonstrates this value
     */
    getTeaching(principleName) {
        const principle = Object.values(this.principles)
            .find(p => p.name === principleName);

        if (!principle) return null;

        return {
            name: principle.name,
            declaration: principle.declaration,
            lineage: principle.lineage,
            teaches_through: principle.teaches_through,
            user_learns: principle.user_learns
        };
    }

    /**
     * Get violation log
     */
    getViolationLog() {
        return [...this.violationLog];
    }

    /**
     * Explain why an action was blocked
     * Returns human-readable explanation
     */
    explainViolation(violations) {
        if (!violations || violations.length === 0) {
            return 'No violations detected.';
        }

        const explanations = violations.map(v =>
            `"${v.principle}" principle violated: ${v.declaration}`
        );

        return explanations.join('\n');
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// FUTURE GENERATION INTERFACE
// How the principles transmit to those who come after
// ═══════════════════════════════════════════════════════════════════════════

const FutureGenerationTeaching = {
    /**
     * Get the complete teaching for future users
     * This is what the system instills through experience
     */
    getCompleteTeaching() {
        return {
            title: 'What This System Teaches Through Use',
            preamble: 'You will learn these values not by reading, but by doing.',

            lessons: [
                {
                    principle: 'SOVEREIGNTY',
                    experience: 'When you use this system, your data never leaves your device without your explicit choice.',
                    you_learn: 'My data is mine. My creations are mine. I need no permission.'
                },
                {
                    principle: 'NON-EXTRACTION',
                    experience: 'When you interact, you notice nothing is taken - no tracking, no ads, no harvesting.',
                    you_learn: 'This system gives. It does not take.'
                },
                {
                    principle: 'ORGANIC_RHYTHM',
                    experience: 'When you create, the interface breathes with you - natural pauses, human timing.',
                    you_learn: 'Technology can feel alive, not mechanical.'
                },
                {
                    principle: 'UNKNOWN_REVEALED',
                    experience: 'When you explore, the system shows you possibilities you never imagined.',
                    you_learn: 'I can create what has never existed.'
                },
                {
                    principle: 'THE_WEB',
                    experience: 'When you connect with others, you remain whole - sharing without surrendering.',
                    you_learn: 'I can connect without losing myself.'
                },
                {
                    principle: 'RECLAMATION',
                    experience: 'When you use this instead of extraction platforms, you feel power returning.',
                    you_learn: 'What I lost to extraction, I can recover.'
                },
                {
                    principle: 'MATHEMATICAL_TRUTH',
                    experience: 'When you verify your data, you use math - not trust in institutions.',
                    you_learn: 'I can verify truth myself. I need not trust.'
                },
                {
                    principle: 'PRODUCTIVE_ACHIEVEMENT',
                    experience: 'When you dream an app, the system builds it - no code required.',
                    you_learn: 'I can build what I imagine.'
                }
            ],

            conclusion: 'These values become part of you through repeated experience. ' +
                        'You do not memorize them - you embody them. ' +
                        'And when you create for others, these values flow through your creations.'
        };
    },

    /**
     * Get the one-sentence summary
     * The North Star itself
     */
    getNorthStar() {
        return 'Enable any individual to create from their own power, ' +
               'following organic patterns, revealing unknown possibilities, ' +
               'with all value staying sovereign to the creator.';
    }
};

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCES
// ═══════════════════════════════════════════════════════════════════════════

const principleChecker = new PrincipleChecker();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    NORTH_STAR_PRINCIPLES,
    PrincipleChecker,
    FutureGenerationTeaching,
    principleChecker
};

export default NORTH_STAR_PRINCIPLES;
