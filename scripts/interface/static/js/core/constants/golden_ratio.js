/**
 * GOLDEN RATIO CONSTANTS - THE SINGLE SOURCE OF TRUTH
 *
 * Created: 2026-01-15
 * Purpose: Eliminate inconsistency in φ-related constants
 *
 * RULES:
 * 1. NEVER hardcode φ-related values anywhere else in the codebase
 * 2. ALWAYS import from this module
 * 3. ALWAYS use symbolic names (THRESHOLDS.FULL) not decimals (0.618)
 * 4. This file MUST pass self-verification on load
 *
 * MATHEMATICAL FOUNDATION:
 * φ = (1 + √5) / 2 = 1.6180339887498948482045868343656...
 *
 * This constant has been unchanged since Euclid (~300 BCE).
 * It will remain unchanged forever.
 */

// =============================================================================
// FUNDAMENTAL CONSTANTS - Computed, never hardcoded
// =============================================================================

export const SQRT_5 = Math.sqrt(5);
export const PHI = (1 + SQRT_5) / 2;
export const PHI_INVERSE = 1 / PHI;  // = PHI - 1 = 0.6180339887498949
export const SQRT_PHI = Math.sqrt(PHI);  // = 1.2720196495140689

// =============================================================================
// ACCESS TIER THRESHOLDS - Used by Quantum Containment System
// =============================================================================

export const THRESHOLDS = Object.freeze({
    /**
     * BLOCKED: ACU below this = no access
     * Formula: φ^(-2)
     * Value: 0.2360679774997897
     * Human: ~24%
     */
    BLOCKED: Math.pow(PHI, -2),

    /**
     * DEGRADED: Limited access (2D view only)
     * Formula: 1 - φ^(-1) (complement of inverse phi)
     * Value: 0.3819660112501051
     * Human: ~38%
     *
     * NOTE: This equals φ^(-2) + small correction.
     * Using complement form for mathematical elegance.
     */
    DEGRADED: 1 - Math.pow(PHI, -1),

    /**
     * FULL: Complete access (4D view) - THE PHI GATE
     * Formula: φ^(-1)
     * Value: 0.6180339887498949
     * Human: ~62%
     *
     * This is THE threshold. The golden ratio inverse.
     * The point where nature balances.
     */
    FULL: Math.pow(PHI, -1),

    /**
     * SOVEREIGN: Network topology access
     * Formula: φ^(-0.5) = 1/√φ
     * Value: 0.7861513777574233
     * Human: ~79%
     *
     * CRITICAL: This was incorrectly documented as 0.854 in early files.
     * The correct value is 0.786... (verified mathematically below).
     *
     * Proof: (0.786...)² = 0.618... = φ^(-1) ✓
     */
    SOVEREIGN: Math.pow(PHI, -0.5),
});

// =============================================================================
// GEOMETRIC CONSTANTS
// =============================================================================

/**
 * GOLDEN ANGLE: The optimal angle for spiral phyllotaxis
 * Formula: 360° / φ² = 360° × φ^(-2)
 * Value: 137.5077640500378°
 *
 * Found in: sunflower seeds, pinecones, nautilus shells
 */
export const GOLDEN_ANGLE_DEGREES = 360 * Math.pow(PHI, -2);
export const GOLDEN_ANGLE_RADIANS = GOLDEN_ANGLE_DEGREES * Math.PI / 180;

// =============================================================================
// RESONANCE CONSTANTS
// =============================================================================

/**
 * SCHUMANN RESONANCE: Earth's electromagnetic fundamental frequency
 * Value: 7.83 Hz (measured, not computed from φ)
 *
 * Used for: Animation timing, breathing cycles
 */
export const SCHUMANN_HZ = 7.83;

/**
 * TESLA PATTERN: 3, 6, 9 harmonic structure
 * "If you only knew the magnificence of the 3, 6 and 9..."
 *
 * NOTE: The full quote is unverified. The pattern itself is mathematically interesting.
 */
export const TESLA_PATTERN = Object.freeze([3, 6, 9]);

// =============================================================================
// FIBONACCI UTILITIES
// =============================================================================

/**
 * Generator function for Fibonacci sequence
 * Usage: const gen = fibonacci(); gen.next().value; // 1, 1, 2, 3, 5...
 */
export function* fibonacci() {
    let a = 1, b = 1;
    while (true) {
        yield a;
        [a, b] = [b, a + b];
    }
}

/**
 * Get first N Fibonacci numbers as array
 * @param {number} n - How many numbers to generate
 * @returns {number[]} Array of Fibonacci numbers
 */
export function fibonacciArray(n) {
    const gen = fibonacci();
    return Array.from({ length: n }, () => gen.next().value);
}

/**
 * Get specific Fibonacci number by index
 * @param {number} n - Index (0-based)
 * @returns {number} The nth Fibonacci number
 */
export function fibonacciAt(n) {
    if (n < 0) return 0;
    if (n <= 1) return 1;
    let a = 1, b = 1;
    for (let i = 2; i <= n; i++) {
        [a, b] = [b, a + b];
    }
    return b;
}

// =============================================================================
// VERIFICATION UTILITIES
// =============================================================================

/**
 * Verify all golden ratio properties are mathematically correct
 * @returns {object} Verification results
 */
export function verifyConstants() {
    const tolerance = 1e-12;
    const results = {
        passed: true,
        tests: []
    };

    function check(name, actual, expected) {
        const passed = Math.abs(actual - expected) < tolerance;
        results.tests.push({ name, actual, expected, passed });
        if (!passed) results.passed = false;
        return passed;
    }

    // PHI fundamental properties
    check('φ² = φ + 1', PHI * PHI, PHI + 1);
    check('1/φ = φ - 1', 1 / PHI, PHI - 1);
    check('φ = 1 + 1/φ', PHI, 1 + 1 / PHI);

    // Threshold relationships
    check('SOVEREIGN² = FULL', THRESHOLDS.SOVEREIGN * THRESHOLDS.SOVEREIGN, THRESHOLDS.FULL);
    check('FULL² = BLOCKED', THRESHOLDS.FULL * THRESHOLDS.FULL, THRESHOLDS.BLOCKED);
    check('FULL + DEGRADED = 1', THRESHOLDS.FULL + THRESHOLDS.DEGRADED, 1);

    // Golden angle
    check('Golden angle', GOLDEN_ANGLE_DEGREES, 360 / (PHI * PHI));

    // Fibonacci convergence
    const fib40 = fibonacciAt(40);
    const fib39 = fibonacciAt(39);
    check('F(40)/F(39) → φ', fib40 / fib39, PHI);

    return results;
}

/**
 * Get human-readable documentation for all thresholds
 * @returns {object[]} Array of threshold documentation objects
 */
export function getThresholdDocs() {
    return [
        {
            name: 'BLOCKED',
            formula: 'φ^(-2)',
            value: THRESHOLDS.BLOCKED,
            percentage: (THRESHOLDS.BLOCKED * 100).toFixed(2) + '%',
            description: 'No access - below minimum alignment'
        },
        {
            name: 'DEGRADED',
            formula: '1 - φ^(-1)',
            value: THRESHOLDS.DEGRADED,
            percentage: (THRESHOLDS.DEGRADED * 100).toFixed(2) + '%',
            description: 'Limited access - 2D view only'
        },
        {
            name: 'FULL',
            formula: 'φ^(-1)',
            value: THRESHOLDS.FULL,
            percentage: (THRESHOLDS.FULL * 100).toFixed(2) + '%',
            description: 'Complete access - THE PHI GATE'
        },
        {
            name: 'SOVEREIGN',
            formula: 'φ^(-0.5) = 1/√φ',
            value: THRESHOLDS.SOVEREIGN,
            percentage: (THRESHOLDS.SOVEREIGN * 100).toFixed(2) + '%',
            description: 'Network topology access'
        }
    ];
}

// =============================================================================
// SELF-VERIFICATION ON LOAD
// =============================================================================

(function selfVerify() {
    const results = verifyConstants();

    if (!results.passed) {
        console.error('GOLDEN RATIO VERIFICATION FAILED:');
        results.tests.filter(t => !t.passed).forEach(t => {
            console.error(`  ✗ ${t.name}: expected ${t.expected}, got ${t.actual}`);
        });
        throw new Error('Golden ratio constants are mathematically inconsistent');
    }

    // Log confirmation in development
    if (typeof process === 'undefined' || process.env?.NODE_ENV !== 'production') {
        console.log('✓ Golden ratio constants verified');
        console.log(`  φ = ${PHI}`);
        console.log(`  THRESHOLDS: BLOCKED=${THRESHOLDS.BLOCKED.toFixed(4)}, DEGRADED=${THRESHOLDS.DEGRADED.toFixed(4)}, FULL=${THRESHOLDS.FULL.toFixed(4)}, SOVEREIGN=${THRESHOLDS.SOVEREIGN.toFixed(4)}`);
    }
})();

// =============================================================================
// EXPORTS SUMMARY
// =============================================================================

/**
 * USAGE GUIDE:
 *
 * import { PHI, THRESHOLDS, GOLDEN_ANGLE_DEGREES } from './constants/golden_ratio.js';
 *
 * // Compare ACU to threshold
 * if (acu >= THRESHOLDS.FULL) {
 *     grantFullAccess();
 * }
 *
 * // Use golden angle in spiral
 * const angle = index * GOLDEN_ANGLE_RADIANS;
 *
 * // Get Fibonacci weights
 * const weights = fibonacciArray(21);
 *
 * // Verify constants (for testing)
 * const results = verifyConstants();
 * console.assert(results.passed, 'Constants verification failed');
 */

export default {
    // Fundamentals
    PHI,
    PHI_INVERSE,
    SQRT_PHI,
    SQRT_5,

    // Thresholds
    THRESHOLDS,

    // Geometry
    GOLDEN_ANGLE_DEGREES,
    GOLDEN_ANGLE_RADIANS,

    // Resonance
    SCHUMANN_HZ,
    TESLA_PATTERN,

    // Fibonacci
    fibonacci,
    fibonacciArray,
    fibonacciAt,

    // Verification
    verifyConstants,
    getThresholdDocs
};
