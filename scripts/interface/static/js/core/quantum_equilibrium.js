/**
 * QUANTUM EQUILIBRIUM ENGINE V2
 * Gaming-resistant access control using Fibonacci-weighted behavioral analysis
 *
 * Fixes ACU V1 vulnerability: V1 allowed tier manipulation in 2-3 actions
 * V2 requires sustained consistent behavior over 21+ actions
 */

export class QuantumEquilibriumEngine {
    constructor() {
        // Mathematical constants
        this.PHI = 1.618033988749895;
        this.PHI_INVERSE = 0.6180339887498949;

        // Access tier thresholds (golden ratio powers)
        this.THRESHOLDS = {
            BLOCKED:   0.236,  // φ^(-2)
            DEGRADED:  0.382,  // 1 - φ^(-1)
            PARTIAL:   0.500,  // neutral
            FULL:      0.618,  // φ^(-1)
            SOVEREIGN: 0.786   // φ^(-0.5)
        };

        // Anti-gaming parameters
        this.MIN_HISTORY = 21;           // Fibonacci F(8) - minimum actions before tier calculation
        this.VARIANCE_THRESHOLD = 0.25;  // Max allowed variance (detects oscillation)
        this.LIGHT_RATIO_MIN = 0.618;    // Min positive/total ratio for advanced tiers

        // Pre-compute Fibonacci weights (up to 55 actions)
        this.fibWeights = this._generateFibonacci(55);
    }

    /**
     * Calculate equilibrium-based ACU score
     * @param {Array} actionHistory - Array of {score: 0-1, timestamp: ms}
     * @returns {Object} - ACU result with tier and diagnostics
     */
    calculateEquilibriumACU(actionHistory) {
        const result = {
            acu: 0.5,
            tier: 2,
            tierName: 'PARTIAL',
            gated: false,
            diagnostics: {}
        };

        // Layer 1: History gate
        if (actionHistory.length < this.MIN_HISTORY) {
            result.gated = true;
            result.diagnostics.historyGate = {
                required: this.MIN_HISTORY,
                current: actionHistory.length,
                remaining: this.MIN_HISTORY - actionHistory.length
            };
            return result;
        }

        // Layer 2: Fibonacci-weighted ACU
        const fibACU = this._calculateFibonacciACU(actionHistory);
        result.acu = fibACU;
        result.diagnostics.fibonacciACU = fibACU;

        // Layer 3: Variance check (anti-oscillation)
        const recentActions = actionHistory.slice(-13); // Last 13 (Fibonacci)
        const variance = this._calculateVariance(recentActions);
        result.diagnostics.variance = variance;

        let effectiveACU = fibACU;
        if (variance > this.VARIANCE_THRESHOLD) {
            // Penalize high variance (oscillating behavior)
            effectiveACU = fibACU * (1 - variance);
            result.diagnostics.variancePenalty = true;
            result.diagnostics.penalizedACU = effectiveACU;
        }

        // Layer 4: Light equilibrium
        const lightRatio = this._calculateLightRatio(actionHistory);
        result.diagnostics.lightRatio = lightRatio;

        // Determine tier from effective ACU
        let tier = this._getTierFromACU(effectiveACU);
        let tierCapped = false;

        // Cap tier if light ratio insufficient for advanced tiers
        if (tier >= 3 && lightRatio < this.LIGHT_RATIO_MIN) {
            tier = 2; // Cap at PARTIAL
            tierCapped = true;
            result.diagnostics.lightRatioCap = true;
        }

        result.tier = tier;
        result.tierName = this._getTierName(tier);
        result.effectiveACU = effectiveACU;

        return result;
    }

    /**
     * Fibonacci-weighted ACU calculation
     * Key insight: OLDER actions contribute MORE than recent actions
     * This rewards sustained consistency over gaming bursts
     */
    _calculateFibonacciACU(history) {
        let weightedSum = 0;
        let totalWeight = 0;

        for (let i = 0; i < history.length; i++) {
            // Age: oldest action = highest index
            const age = history.length - 1 - i;

            // Weight: Fibonacci number for this age (capped at 55th)
            const weight = this.fibWeights[Math.min(age, 54)];

            // Score: action score (0-1)
            const score = typeof history[i] === 'object'
                ? history[i].score
                : history[i];

            weightedSum += score * weight;
            totalWeight += weight;
        }

        return totalWeight > 0 ? weightedSum / totalWeight : 0.5;
    }

    /**
     * Calculate variance of action scores
     * High variance indicates oscillating good/bad pattern (gaming)
     */
    _calculateVariance(actions) {
        if (actions.length < 2) return 0;

        const scores = actions.map(a => typeof a === 'object' ? a.score : a);
        const mean = scores.reduce((sum, s) => sum + s, 0) / scores.length;
        const squaredDiffs = scores.map(s => Math.pow(s - mean, 2));

        return squaredDiffs.reduce((sum, d) => sum + d, 0) / scores.length;
    }

    /**
     * Calculate light ratio (positive actions / total actions)
     */
    _calculateLightRatio(actions) {
        const scores = actions.map(a => typeof a === 'object' ? a.score : a);
        const positiveCount = scores.filter(s => s > 0.5).length;

        return positiveCount / scores.length;
    }

    /**
     * Determine tier from ACU score
     */
    _getTierFromACU(acu) {
        if (acu < this.THRESHOLDS.BLOCKED) return 0;   // BLOCKED
        if (acu < this.THRESHOLDS.DEGRADED) return 1;  // DEGRADED
        if (acu < this.THRESHOLDS.FULL) return 2;      // PARTIAL
        if (acu < this.THRESHOLDS.SOVEREIGN) return 3; // FULL
        return 4; // SOVEREIGN
    }

    /**
     * Get tier name from tier number
     */
    _getTierName(tier) {
        return ['BLOCKED', 'DEGRADED', 'PARTIAL', 'FULL', 'SOVEREIGN'][tier] || 'UNKNOWN';
    }

    /**
     * Generate Fibonacci sequence
     */
    _generateFibonacci(n) {
        const fib = [1, 1];
        for (let i = 2; i < n; i++) {
            fib.push(fib[i - 1] + fib[i - 2]);
        }
        return fib;
    }

    /**
     * Simulate gaming attack to verify resistance
     * @param {number} badActions - Number of bad actions in history
     * @param {number} goodActions - Number of perfect actions to attempt
     * @returns {Object} - Simulation result
     */
    simulateGamingAttack(badActions = 50, goodActions = 21) {
        // Build history: badActions bad (0.1), then goodActions perfect (1.0)
        const history = [];

        for (let i = 0; i < badActions; i++) {
            history.push({ score: 0.1, timestamp: Date.now() - (badActions - i) * 3600000 });
        }

        for (let i = 0; i < goodActions; i++) {
            history.push({ score: 1.0, timestamp: Date.now() - (goodActions - i) * 60000 });
        }

        const result = this.calculateEquilibriumACU(history);

        return {
            scenario: `${badActions} bad actions + ${goodActions} perfect actions`,
            result: result,
            gamingSuccess: result.tier >= 3, // Did attacker reach FULL?
            analysis: result.tier >= 3
                ? 'VULNERABILITY: Gaming succeeded'
                : 'PROTECTED: Gaming failed'
        };
    }

    /**
     * Estimate actions needed to reach target tier
     * @param {number} currentACU - Current ACU score
     * @param {number} targetTier - Target tier (0-4)
     * @returns {Object} - Estimation
     */
    estimateActionsToTier(currentACU, targetTier) {
        const targetACU = [
            this.THRESHOLDS.BLOCKED,
            this.THRESHOLDS.DEGRADED,
            this.THRESHOLDS.FULL,
            this.THRESHOLDS.SOVEREIGN,
            1.0
        ][targetTier];

        if (currentACU >= targetACU) {
            return { actionsNeeded: 0, note: 'Already at or above target tier' };
        }

        // Rough estimate based on Fibonacci weighting
        // With perfect actions (1.0), convergence is slow due to old history weight
        const gap = targetACU - currentACU;
        const estimatedActions = Math.ceil(gap * 50); // Rough heuristic

        return {
            currentACU,
            targetTier: this._getTierName(targetTier),
            targetACU,
            estimatedActions,
            note: 'Estimate assumes perfect (1.0) scores. Actual time varies.'
        };
    }
}

// Export singleton instance
export const quantumEquilibrium = new QuantumEquilibriumEngine();

// Run self-test if executed directly
if (typeof window === 'undefined' && typeof process !== 'undefined') {
    const engine = new QuantumEquilibriumEngine();

    console.log('=== Quantum Equilibrium V2 Self-Test ===\n');

    // Test 1: History gate
    console.log('Test 1: History gate (< 21 actions)');
    const shortHistory = Array(10).fill({ score: 1.0 });
    const gatedResult = engine.calculateEquilibriumACU(shortHistory);
    console.log(`  Actions: 10, Gated: ${gatedResult.gated}, Tier: ${gatedResult.tierName}`);
    console.log(`  Result: ${gatedResult.gated ? 'PASS' : 'FAIL'}\n`);

    // Test 2: Gaming attack simulation
    console.log('Test 2: Gaming attack (50 bad + 21 perfect)');
    const attackResult = engine.simulateGamingAttack(50, 21);
    console.log(`  Scenario: ${attackResult.scenario}`);
    console.log(`  ACU: ${attackResult.result.acu.toFixed(4)}`);
    console.log(`  Tier: ${attackResult.result.tierName}`);
    console.log(`  Analysis: ${attackResult.analysis}`);
    console.log(`  Result: ${!attackResult.gamingSuccess ? 'PASS' : 'FAIL'}\n`);

    // Test 3: Legitimate user
    console.log('Test 3: Legitimate user (50 consistent good actions)');
    const goodHistory = Array(50).fill({ score: 0.85 });
    const goodResult = engine.calculateEquilibriumACU(goodHistory);
    console.log(`  Actions: 50 @ 0.85 score`);
    console.log(`  ACU: ${goodResult.acu.toFixed(4)}`);
    console.log(`  Tier: ${goodResult.tierName}`);
    console.log(`  Result: ${goodResult.tier >= 3 ? 'PASS' : 'FAIL'}\n`);

    // Test 4: Oscillation detection
    console.log('Test 4: Oscillation detection (alternating 0/1)');
    const oscillatingHistory = [];
    for (let i = 0; i < 30; i++) {
        oscillatingHistory.push({ score: i % 2 });
    }
    const oscillateResult = engine.calculateEquilibriumACU(oscillatingHistory);
    console.log(`  Pattern: 0,1,0,1,0,1...`);
    console.log(`  Variance: ${oscillateResult.diagnostics.variance.toFixed(4)}`);
    console.log(`  Penalty applied: ${oscillateResult.diagnostics.variancePenalty || false}`);
    console.log(`  Tier: ${oscillateResult.tierName}`);
    console.log(`  Result: ${oscillateResult.diagnostics.variancePenalty ? 'PASS' : 'FAIL'}\n`);

    console.log('=== Self-Test Complete ===');
}
