/**
 * BALANCE PRINCIPLE
 * ==================
 * Wholeness Through Complementary Polarities
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * THE CORE INSIGHT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * True understanding requires seeing BOTH expressions of a principle.
 *
 * Sovereignty is expressed by both Rand AND Fuller.
 * Breath is expressed by both Tori AND Coltrane.
 * Unknown is expressed by both Bjork AND Bowie.
 * Reclamation is expressed by both Starhawk AND Prince.
 *
 * If a user only sees one polarity, they have HALF the picture.
 * The algorithm must ensure BOTH sides are represented.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * WHAT THIS PREVENTS
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * WITHOUT balance principle:
 * - User interested in female creators → only sees female creators
 * - Echo chamber of perspective forms
 * - Understanding becomes lopsided
 * - Half the wisdom is invisible
 * - Confirmation bias in discovery
 *
 * WITH balance principle:
 * - User interested in female creators → sees aligned male creators too
 * - Complementary perspectives expand understanding
 * - Both polarities of each value are visible
 * - Wholeness through balance
 * - Discovery remains open
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * THE MIRROR PRINCIPLE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Every principle has complementary expressions.
 * The system MIRRORS back both expressions regardless of user's initial lean.
 *
 * This is NOT about:
 * - Forcing "both sides" of debates
 * - False equivalence
 * - Neutrality for its own sake
 *
 * This IS about:
 * - Showing sovereignty expressed through different lenses
 * - Revealing the same value in complementary forms
 * - Expanding understanding, not flattening it
 * - Wholeness, not fragmentation
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * POLARITY PAIRS IN THIS ARCHITECTURE
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * DOMAIN          FEMALE              MALE               SHARED VALUE
 * ──────────────────────────────────────────────────────────────────────────
 * Philosophy      Ayn Rand            Buckminster Fuller Individual as designer
 * Power           Starhawk            Prince             Power-from-within
 * Rhythm          Tori Amos           John Coltrane      Breath as structure
 * Unknown         Bjork               David Bowie        Reinvention/revelation
 *
 * The VALUE is the same. The EXPRESSION is complementary.
 * Both are needed for wholeness.
 */

import { PHI } from './pi_quadratic_seed.js';

// ═══════════════════════════════════════════════════════════════════════════
// POLARITY DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════

const POLARITY_PAIRS = Object.freeze({
    // The eight lineages organized by shared value
    PHILOSOPHY: {
        value: 'Individual as primary designer of reality',
        polarities: {
            feminine: {
                name: 'Ayn Rand',
                expression: 'Through reason and non-contradiction',
                works: ['Atlas Shrugged', 'The Fountainhead', 'The Virtue of Selfishness']
            },
            masculine: {
                name: 'Buckminster Fuller',
                expression: 'Through design science and geometry',
                works: ['Operating Manual for Spaceship Earth', 'Synergetics']
            }
        }
    },

    POWER: {
        value: 'Power-from-within defeats extraction',
        polarities: {
            feminine: {
                name: 'Starhawk',
                expression: 'Through the web and reclamation',
                works: ['The Spiral Dance', 'Dreaming the Dark']
            },
            masculine: {
                name: 'Prince',
                expression: 'Through ownership and prolific creation',
                works: ['Purple Rain', 'Sign o\' the Times', 'The symbol period']
            }
        }
    },

    RHYTHM: {
        value: 'Breath/body as source of creative structure',
        polarities: {
            feminine: {
                name: 'Tori Amos',
                expression: 'Through piano and vocal breath patterns',
                works: ['Little Earthquakes', 'Boys for Pele', 'Live performances']
            },
            masculine: {
                name: 'John Coltrane',
                expression: 'Through saxophone as spiritual practice',
                works: ['A Love Supreme', 'Giant Steps', 'Ascension']
            }
        }
    },

    UNKNOWN: {
        value: 'Reinvention into unmapped territory',
        polarities: {
            feminine: {
                name: 'Bjork',
                expression: 'Through genre fusion and nature-technology synthesis',
                works: ['Homogenic', 'Vespertine', 'Biophilia', 'Medúlla']
            },
            masculine: {
                name: 'David Bowie',
                expression: 'Through character death and permanent becoming',
                works: ['Ziggy Stardust', 'Low', 'Blackstar']
            }
        }
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// BALANCE THRESHOLDS
// When to intervene to restore balance
// ═══════════════════════════════════════════════════════════════════════════

const BALANCE_CONFIG = Object.freeze({
    // If consumption skews beyond this ratio, introduce balance
    IMBALANCE_THRESHOLD: PHI,  // ~1.618 - golden ratio as natural balance point

    // Minimum representation of minority polarity
    MINIMUM_REPRESENTATION: 1 / (PHI + 1),  // ~38.2% - golden ratio complement

    // How strongly to weight balancing suggestions
    BALANCE_WEIGHT: 1 / PHI,  // ~0.618 - gentle, not forced

    // Don't balance within this many interactions (let preferences establish)
    GRACE_PERIOD: 5
});

// ═══════════════════════════════════════════════════════════════════════════
// BALANCE TRACKER
// ═══════════════════════════════════════════════════════════════════════════

class BalanceTracker {
    constructor() {
        this.consumption = {
            feminine: 0,
            masculine: 0,
            neutral: 0
        };
        this.history = [];
        this.byDomain = new Map();
    }

    /**
     * Record consumption of content/creator with polarity
     *
     * @param {string} item - What was consumed
     * @param {string} polarity - 'feminine', 'masculine', or 'neutral'
     * @param {string} domain - Which domain (PHILOSOPHY, POWER, RHYTHM, UNKNOWN)
     */
    recordConsumption(item, polarity, domain = null) {
        // Update overall count
        if (this.consumption[polarity] !== undefined) {
            this.consumption[polarity]++;
        }

        // Update domain-specific count
        if (domain) {
            if (!this.byDomain.has(domain)) {
                this.byDomain.set(domain, { feminine: 0, masculine: 0, neutral: 0 });
            }
            const domainCount = this.byDomain.get(domain);
            if (domainCount[polarity] !== undefined) {
                domainCount[polarity]++;
            }
        }

        // Record in history
        this.history.push({
            item: item,
            polarity: polarity,
            domain: domain,
            timestamp: Date.now()
        });
    }

    /**
     * Get current balance ratio
     *
     * @returns {Object} Balance analysis
     */
    getBalanceRatio() {
        const total = this.consumption.feminine + this.consumption.masculine;
        if (total === 0) return { balanced: true, ratio: 1, dominantPolarity: null };

        const ratio = Math.max(this.consumption.feminine, this.consumption.masculine) /
                     Math.max(1, Math.min(this.consumption.feminine, this.consumption.masculine));

        const dominantPolarity = this.consumption.feminine > this.consumption.masculine
            ? 'feminine'
            : this.consumption.masculine > this.consumption.feminine
                ? 'masculine'
                : null;

        return {
            balanced: ratio <= BALANCE_CONFIG.IMBALANCE_THRESHOLD,
            ratio: ratio,
            dominantPolarity: dominantPolarity,
            minorityPolarity: dominantPolarity === 'feminine' ? 'masculine' : 'feminine',
            feminine: this.consumption.feminine,
            masculine: this.consumption.masculine,
            total: total
        };
    }

    /**
     * Get balance ratio for a specific domain
     */
    getDomainBalance(domain) {
        const domainCount = this.byDomain.get(domain);
        if (!domainCount) return { balanced: true, ratio: 1 };

        const total = domainCount.feminine + domainCount.masculine;
        if (total === 0) return { balanced: true, ratio: 1 };

        const ratio = Math.max(domainCount.feminine, domainCount.masculine) /
                     Math.max(1, Math.min(domainCount.feminine, domainCount.masculine));

        return {
            balanced: ratio <= BALANCE_CONFIG.IMBALANCE_THRESHOLD,
            ratio: ratio,
            domain: domain,
            feminine: domainCount.feminine,
            masculine: domainCount.masculine
        };
    }

    /**
     * Check if within grace period
     */
    inGracePeriod() {
        const total = this.consumption.feminine + this.consumption.masculine;
        return total < BALANCE_CONFIG.GRACE_PERIOD;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// BALANCE ENGINE
// ═══════════════════════════════════════════════════════════════════════════

class BalanceEngine {
    constructor() {
        this.tracker = new BalanceTracker();
    }

    /**
     * Apply balance to a list of suggestions
     * Ensures both polarities are represented
     *
     * @param {Array} suggestions - Raw suggestions from expansion engine
     * @param {Object} options - Balance options
     * @returns {Array} Balanced suggestions
     */
    applyBalance(suggestions, options = {}) {
        // Don't balance during grace period (let preferences establish)
        if (this.tracker.inGracePeriod()) {
            return suggestions;
        }

        const balance = this.tracker.getBalanceRatio();

        // If already balanced, return as-is
        if (balance.balanced) {
            return suggestions;
        }

        // Need to boost minority polarity
        const minorityPolarity = balance.minorityPolarity;

        return this._boostMinorityPolarity(suggestions, minorityPolarity);
    }

    /**
     * Boost suggestions of the minority polarity
     */
    _boostMinorityPolarity(suggestions, minorityPolarity) {
        // Separate by polarity
        const minority = suggestions.filter(s => s.polarity === minorityPolarity);
        const majority = suggestions.filter(s => s.polarity !== minorityPolarity);

        // Calculate target ratio
        const targetMinorityCount = Math.ceil(
            suggestions.length * BALANCE_CONFIG.MINIMUM_REPRESENTATION
        );

        // Ensure minimum representation
        const result = [];

        // Add minority suggestions first (up to target)
        for (let i = 0; i < Math.min(targetMinorityCount, minority.length); i++) {
            result.push({
                ...minority[i],
                balanceBoost: true,
                boostReason: `Ensuring ${minorityPolarity} perspective is represented`
            });
        }

        // Fill rest with majority
        const remainingSlots = suggestions.length - result.length;
        for (let i = 0; i < Math.min(remainingSlots, majority.length); i++) {
            result.push(majority[i]);
        }

        // If we don't have enough minority suggestions, note it
        if (minority.length < targetMinorityCount) {
            result.balanceNote = `Consider exploring more ${minorityPolarity} creators in this domain`;
        }

        return result;
    }

    /**
     * Get the complementary creator for a given creator
     *
     * @param {string} creatorName - Name of creator
     * @returns {Object} Complementary creator info
     */
    getComplement(creatorName) {
        const nameLower = creatorName.toLowerCase();

        for (const [domain, pair] of Object.entries(POLARITY_PAIRS)) {
            // Check feminine
            if (pair.polarities.feminine.name.toLowerCase().includes(nameLower)) {
                return {
                    original: pair.polarities.feminine,
                    complement: pair.polarities.masculine,
                    domain: domain,
                    sharedValue: pair.value,
                    reason: `${pair.polarities.masculine.name} expresses the same value (${pair.value}) through ${pair.polarities.masculine.expression}`
                };
            }

            // Check masculine
            if (pair.polarities.masculine.name.toLowerCase().includes(nameLower)) {
                return {
                    original: pair.polarities.masculine,
                    complement: pair.polarities.feminine,
                    domain: domain,
                    sharedValue: pair.value,
                    reason: `${pair.polarities.feminine.name} expresses the same value (${pair.value}) through ${pair.polarities.feminine.expression}`
                };
            }
        }

        return null;
    }

    /**
     * Get mirror suggestions for any input
     * Always returns both polarities of aligned values
     *
     * @param {string} interest - User's interest
     * @returns {Object} Mirrored suggestions
     */
    getMirrorSuggestions(interest) {
        const mirrors = [];

        // Check if interest aligns with any of our polarity pairs
        const interestLower = interest.toLowerCase();

        for (const [domain, pair] of Object.entries(POLARITY_PAIRS)) {
            // Check if interest relates to this domain's value
            const valueWords = pair.value.toLowerCase().split(' ');
            const isRelated = valueWords.some(word =>
                word.length > 3 && interestLower.includes(word)
            );

            if (isRelated) {
                mirrors.push({
                    domain: domain,
                    value: pair.value,
                    feminine: {
                        ...pair.polarities.feminine,
                        polarity: 'feminine'
                    },
                    masculine: {
                        ...pair.polarities.masculine,
                        polarity: 'masculine'
                    },
                    reason: `Both express "${pair.value}" through complementary lenses`
                });
            }
        }

        return {
            interest: interest,
            mirrors: mirrors,
            principle: 'True understanding requires seeing both expressions of a value'
        };
    }

    /**
     * Ensure balanced output for any recommendation
     * This is the main method other modules should call
     *
     * @param {Array} recommendations - Any list of recommendations
     * @param {Function} polarityDetector - Function to detect polarity of an item
     * @returns {Array} Balanced recommendations
     */
    ensureBalance(recommendations, polarityDetector) {
        if (!recommendations || recommendations.length === 0) {
            return recommendations;
        }

        // Detect polarities
        const withPolarity = recommendations.map(rec => ({
            ...rec,
            polarity: polarityDetector ? polarityDetector(rec) : 'neutral'
        }));

        // Apply balance
        return this.applyBalance(withPolarity);
    }

    /**
     * Record that user consumed something (for tracking)
     */
    recordConsumption(item, polarity, domain) {
        this.tracker.recordConsumption(item, polarity, domain);
    }

    /**
     * Get current balance status
     */
    getBalanceStatus() {
        const overall = this.tracker.getBalanceRatio();
        const byDomain = {};

        for (const domain of Object.keys(POLARITY_PAIRS)) {
            byDomain[domain] = this.tracker.getDomainBalance(domain);
        }

        return {
            overall: overall,
            byDomain: byDomain,
            inGracePeriod: this.tracker.inGracePeriod(),
            config: BALANCE_CONFIG,
            principle: 'Wholeness through complementary polarities'
        };
    }

    /**
     * Get all polarity pairs
     */
    getPolarityPairs() {
        return POLARITY_PAIRS;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// WHOLENESS PRINCIPLE
// The philosophical foundation
// ═══════════════════════════════════════════════════════════════════════════

const WHOLENESS_PRINCIPLE = Object.freeze({
    name: 'Wholeness Through Complementary Polarities',

    declaration: 'True understanding requires seeing both expressions of a value',

    prevents: [
        'Echo chambers of perspective',
        'Lopsided understanding',
        'Missing half the picture',
        'Confirmation bias in discovery',
        'Fragmented worldview'
    ],

    enables: [
        'Complete understanding of principles',
        'Complementary perspectives',
        'Both polarities visible',
        'Wholeness through balance',
        'Open discovery'
    ],

    implementation: {
        tracking: 'Monitor consumption by polarity',
        threshold: 'Golden ratio as natural balance point',
        intervention: 'Gentle boost to minority polarity when imbalanced',
        respect: 'Never force, always ensure representation'
    },

    notAbout: [
        'Forcing "both sides" of debates',
        'False equivalence',
        'Neutrality for its own sake',
        'Erasing preferences'
    ],

    isAbout: [
        'Showing values expressed through different lenses',
        'Revealing the same principle in complementary forms',
        'Expanding understanding, not flattening it',
        'Wholeness, not fragmentation'
    ]
});

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const balanceEngine = new BalanceEngine();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    BalanceEngine,
    BalanceTracker,
    balanceEngine,
    POLARITY_PAIRS,
    BALANCE_CONFIG,
    WHOLENESS_PRINCIPLE
};

export default balanceEngine;
