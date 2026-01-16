/**
 * QUANTUM PROVENANCE MODEL
 * ========================
 *
 * A novel approach to provenance that uses quantum mechanics concepts
 * to model DISPUTED or UNCERTAIN ownership/creation claims.
 *
 * PHILOSOPHY:
 * ───────────
 * Traditional provenance is CLASSICAL - an artwork has ONE history.
 * But real-world provenance is often disputed, uncertain, or partial.
 *
 * Quantum provenance models artwork history as a SUPERPOSITION of
 * possible states until "measured" (verified by authoritative source).
 *
 * KEY CONCEPTS:
 * ─────────────
 * 1. SUPERPOSITION: Multiple provenance claims coexist with amplitudes
 * 2. AMPLITUDE: Mathematical weight of each claim (√probability)
 * 3. COLLAPSE: When verified, state collapses to most probable claim
 * 4. ENTANGLEMENT: Related artworks share correlated provenance states
 * 5. INTERFERENCE: Claims can reinforce or cancel each other
 *
 * MATHEMATICAL MODEL:
 * ───────────────────
 * |ψ⟩ = Σᵢ αᵢ|claimᵢ⟩
 *
 * where:
 * - |ψ⟩ is the provenance state
 * - αᵢ is the amplitude (complex number, |αᵢ|² = probability)
 * - |claimᵢ⟩ is a basis state (single provenance claim)
 *
 * Normalization: Σᵢ|αᵢ|² = 1
 *
 * @module quantum_provenance
 * @version 1.0.0
 */

import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';

/**
 * Evidence types and their base amplitudes
 */
const EVIDENCE_AMPLITUDES = {
    // Strongest evidence
    ORIGINAL_DOCUMENT: 0.95,     // Original signed document/contract
    BLOCKCHAIN_MINT: 0.90,      // On-chain minting transaction
    INSTITUTIONAL_RECORD: 0.85, // Museum/gallery documentation
    AUTHENTICATED_VIDEO: 0.80,  // Video of creation with verification

    // Medium evidence
    EXPERT_ATTRIBUTION: 0.70,   // Art expert's formal attribution
    CATALOG_LISTING: 0.65,      // Published catalog entry
    PRESS_COVERAGE: 0.60,       // Contemporary press about creation
    TESTIMONY: 0.55,            // Witness testimony

    // Weak evidence
    SOCIAL_MEDIA: 0.40,         // Social media posts
    SELF_ATTESTATION: 0.35,     // Creator's own unverified claim
    HEARSAY: 0.20,              // Second-hand information
    ANONYMOUS_TIP: 0.10,        // Anonymous/unverifiable source

    // Default
    UNKNOWN: 0.30
};

/**
 * Claim status (before collapse)
 */
const CLAIM_STATUS = {
    SUPERPOSED: 'superposed',       // Active, uncollapsed claim
    COLLAPSED_TO: 'collapsed_to',   // This claim was verified
    COLLAPSED_AWAY: 'collapsed_away', // Eliminated by verification
    ENTANGLED: 'entangled'          // Linked to another work's state
};

/**
 * A single provenance claim in the quantum model
 */
class ProvenanceClaim {
    constructor({
        claimant,           // Who is making the claim
        claimType,          // 'creator', 'owner', 'collaborator', 'derivative'
        description,        // Human-readable description
        evidence = [],      // Array of evidence objects
        timestamp = Date.now()
    }) {
        this.id = this._generateId();
        this.claimant = claimant;
        this.claimType = claimType;
        this.description = description;
        this.evidence = evidence;
        this.timestamp = timestamp;
        this.status = CLAIM_STATUS.SUPERPOSED;

        // Calculated amplitude based on evidence
        this.amplitude = this._calculateAmplitude();
    }

    /**
     * Generate unique claim ID
     * @private
     */
    _generateId() {
        return 'claim_' + Date.now().toString(36) +
               '_' + Math.random().toString(36).substring(2, 9);
    }

    /**
     * Calculate amplitude from evidence
     * Uses quantum interference - multiple strong sources reinforce
     * @private
     */
    _calculateAmplitude() {
        if (this.evidence.length === 0) {
            return EVIDENCE_AMPLITUDES.UNKNOWN;
        }

        // Get base amplitudes for all evidence
        const amplitudes = this.evidence.map(e =>
            EVIDENCE_AMPLITUDES[e.type] || EVIDENCE_AMPLITUDES.UNKNOWN
        );

        // Quantum interference model:
        // Multiple sources can reinforce (constructive) or conflict (destructive)
        // We model constructive interference for consistent evidence

        // Base: highest single evidence
        const maxAmplitude = Math.max(...amplitudes);

        // Reinforcement: each additional piece adds diminishing contribution
        // Using golden ratio for natural diminishing returns
        let reinforcement = 0;
        const sorted = amplitudes.sort((a, b) => b - a);
        for (let i = 1; i < sorted.length; i++) {
            // Each subsequent piece contributes 1/φⁱ of its amplitude
            reinforcement += sorted[i] * Math.pow(1/PHI, i);
        }

        // Combine with cap at 0.99 (never 100% certain until collapsed)
        const combined = Math.min(0.99, maxAmplitude + reinforcement * 0.1);

        return combined;
    }

    /**
     * Add new evidence and recalculate amplitude
     * @param {Object} newEvidence
     */
    addEvidence(newEvidence) {
        this.evidence.push({
            ...newEvidence,
            addedAt: Date.now()
        });
        this.amplitude = this._calculateAmplitude();
    }

    /**
     * Get probability (amplitude squared)
     */
    getProbability() {
        return this.amplitude * this.amplitude;
    }

    /**
     * Export claim data
     */
    export() {
        return {
            id: this.id,
            claimant: this.claimant,
            claimType: this.claimType,
            description: this.description,
            evidence: this.evidence,
            timestamp: this.timestamp,
            status: this.status,
            amplitude: this.amplitude,
            probability: this.getProbability()
        };
    }
}

/**
 * Quantum Provenance State
 * Manages superposition of multiple provenance claims for a single artwork
 */
class QuantumProvenanceState {
    constructor(artworkId, metadata = {}) {
        this.artworkId = artworkId;
        this.metadata = metadata;
        this.claims = [];
        this.collapsed = false;
        this.collapsedTo = null;
        this.collapseEvent = null;
        this.entanglements = [];
        this.history = [];
        this.createdAt = Date.now();
    }

    /**
     * Add a new claim to the superposition
     * @param {Object} claimData
     * @returns {ProvenanceClaim}
     */
    addClaim(claimData) {
        if (this.collapsed) {
            throw new Error('Cannot add claims to collapsed state');
        }

        const claim = new ProvenanceClaim(claimData);
        this.claims.push(claim);

        // Normalize amplitudes
        this._normalize();

        // Record history
        this.history.push({
            action: 'claim_added',
            claimId: claim.id,
            timestamp: Date.now()
        });

        return claim;
    }

    /**
     * Normalize amplitudes so probabilities sum to 1
     * @private
     */
    _normalize() {
        if (this.claims.length === 0) return;

        // Calculate sum of probability (amplitude²)
        const sumProbability = this.claims.reduce(
            (sum, claim) => sum + claim.getProbability(),
            0
        );

        // Normalize amplitudes
        const normFactor = 1 / Math.sqrt(sumProbability);
        this.claims.forEach(claim => {
            claim.amplitude *= normFactor;
        });
    }

    /**
     * Apply interference between claims
     * Consistent evidence reinforces, contradictory evidence cancels
     * @param {string} claimId1
     * @param {string} claimId2
     * @param {string} interferenceType - 'constructive' or 'destructive'
     */
    applyInterference(claimId1, claimId2, interferenceType) {
        const claim1 = this.claims.find(c => c.id === claimId1);
        const claim2 = this.claims.find(c => c.id === claimId2);

        if (!claim1 || !claim2) {
            throw new Error('Claims not found');
        }

        if (interferenceType === 'constructive') {
            // Claims reinforce each other
            const combinedAmplitude = Math.sqrt(
                claim1.amplitude ** 2 + claim2.amplitude ** 2 +
                2 * claim1.amplitude * claim2.amplitude * 0.5 // cos(θ) = 0.5
            );
            claim1.amplitude = combinedAmplitude * 0.7;
            claim2.amplitude = combinedAmplitude * 0.7;
        } else if (interferenceType === 'destructive') {
            // Claims cancel each other out
            const diff = Math.abs(claim1.amplitude - claim2.amplitude);
            claim1.amplitude = diff * 0.5;
            claim2.amplitude = diff * 0.5;
        }

        this._normalize();

        this.history.push({
            action: 'interference_applied',
            type: interferenceType,
            claims: [claimId1, claimId2],
            timestamp: Date.now()
        });
    }

    /**
     * Collapse the superposition to a single verified state
     * @param {Object} verificationEvent
     * @returns {Object} Collapse result
     */
    collapse(verificationEvent) {
        if (this.collapsed) {
            return {
                success: false,
                error: 'Already collapsed',
                collapsedTo: this.collapsedTo
            };
        }

        if (this.claims.length === 0) {
            return {
                success: false,
                error: 'No claims to collapse'
            };
        }

        // Sort by probability (descending)
        const sorted = [...this.claims].sort(
            (a, b) => b.getProbability() - a.getProbability()
        );

        // Collapse to highest probability claim
        const winner = sorted[0];

        // Update statuses
        winner.status = CLAIM_STATUS.COLLAPSED_TO;
        sorted.slice(1).forEach(claim => {
            claim.status = CLAIM_STATUS.COLLAPSED_AWAY;
        });

        this.collapsed = true;
        this.collapsedTo = winner;
        this.collapseEvent = {
            ...verificationEvent,
            collapsedAt: Date.now(),
            winningProbability: winner.getProbability(),
            totalClaims: this.claims.length
        };

        // Record history
        this.history.push({
            action: 'collapsed',
            verificationEvent,
            winnerId: winner.id,
            winningProbability: winner.getProbability(),
            timestamp: Date.now()
        });

        // Propagate to entangled states
        this._propagateCollapse();

        return {
            success: true,
            collapsedTo: winner.export(),
            probability: winner.getProbability(),
            eliminatedClaims: sorted.slice(1).map(c => c.export()),
            verificationEvent: this.collapseEvent
        };
    }

    /**
     * Create entanglement with another artwork's provenance
     * @param {QuantumProvenanceState} otherState
     * @param {string} relationshipType
     */
    entangle(otherState, relationshipType) {
        const entanglement = {
            artworkId: otherState.artworkId,
            type: relationshipType,  // 'same_series', 'same_artist', 'derivative'
            correlation: this._calculateCorrelation(otherState),
            createdAt: Date.now()
        };

        this.entanglements.push(entanglement);

        // Bidirectional entanglement
        otherState.entanglements.push({
            artworkId: this.artworkId,
            type: relationshipType,
            correlation: entanglement.correlation,
            createdAt: Date.now()
        });

        this.history.push({
            action: 'entangled',
            with: otherState.artworkId,
            type: relationshipType,
            correlation: entanglement.correlation,
            timestamp: Date.now()
        });

        return entanglement;
    }

    /**
     * Calculate correlation coefficient between two provenance states
     * @private
     */
    _calculateCorrelation(otherState) {
        // Find common claimants
        const thisClaimants = new Set(this.claims.map(c => c.claimant));
        const otherClaimants = new Set(otherState.claims.map(c => c.claimant));

        const intersection = [...thisClaimants].filter(c => otherClaimants.has(c));
        const union = new Set([...thisClaimants, ...otherClaimants]);

        // Jaccard similarity as correlation proxy
        const correlation = intersection.length / union.size;

        return correlation;
    }

    /**
     * Propagate collapse to entangled states
     * @private
     */
    _propagateCollapse() {
        // In a full implementation, this would update correlated states
        // For now, we just record the propagation intent
        this.history.push({
            action: 'collapse_propagated',
            entanglements: this.entanglements.length,
            timestamp: Date.now()
        });
    }

    /**
     * Get current state summary
     */
    getStateSummary() {
        if (this.collapsed) {
            return {
                status: 'collapsed',
                artworkId: this.artworkId,
                verifiedProvenance: this.collapsedTo.export(),
                collapseEvent: this.collapseEvent,
                eliminatedClaimsCount: this.claims.length - 1,
                entanglements: this.entanglements.length
            };
        }

        // Superposed state
        const probabilities = this.claims.map(c => ({
            claimId: c.id,
            claimant: c.claimant,
            claimType: c.claimType,
            probability: c.getProbability(),
            amplitude: c.amplitude,
            evidenceCount: c.evidence.length
        }));

        probabilities.sort((a, b) => b.probability - a.probability);

        return {
            status: 'superposed',
            artworkId: this.artworkId,
            totalClaims: this.claims.length,
            claims: probabilities,
            dominantClaim: probabilities[0] || null,
            entropyLevel: this._calculateEntropy(),
            entanglements: this.entanglements.length,
            needsResolution: this._needsResolution()
        };
    }

    /**
     * Calculate Shannon entropy of the state (uncertainty measure)
     * @private
     */
    _calculateEntropy() {
        if (this.claims.length === 0) return 0;

        const entropy = -this.claims.reduce((sum, claim) => {
            const p = claim.getProbability();
            if (p === 0) return sum;
            return sum + p * Math.log2(p);
        }, 0);

        return entropy;
    }

    /**
     * Determine if state needs resolution
     * @private
     */
    _needsResolution() {
        if (this.collapsed) return false;
        if (this.claims.length <= 1) return false;

        // Needs resolution if top two claims are close in probability
        const sorted = [...this.claims].sort(
            (a, b) => b.getProbability() - a.getProbability()
        );

        if (sorted.length < 2) return false;

        const topProb = sorted[0].getProbability();
        const secondProb = sorted[1].getProbability();

        // If ratio is less than golden ratio, claims are too close
        const ratio = topProb / secondProb;
        return ratio < PHI;
    }

    /**
     * Export full state
     */
    export() {
        return {
            artworkId: this.artworkId,
            metadata: this.metadata,
            collapsed: this.collapsed,
            collapsedTo: this.collapsedTo?.export() || null,
            collapseEvent: this.collapseEvent,
            claims: this.claims.map(c => c.export()),
            entanglements: this.entanglements,
            history: this.history,
            createdAt: this.createdAt,
            summary: this.getStateSummary()
        };
    }
}

/**
 * Quantum Provenance Registry
 * Manages provenance states for multiple artworks
 */
class QuantumProvenanceRegistry {
    constructor() {
        this.states = new Map(); // artworkId -> QuantumProvenanceState
        this.globalHistory = [];
    }

    /**
     * Create or get provenance state for artwork
     * @param {string} artworkId
     * @param {Object} metadata
     * @returns {QuantumProvenanceState}
     */
    getOrCreateState(artworkId, metadata = {}) {
        if (!this.states.has(artworkId)) {
            const state = new QuantumProvenanceState(artworkId, metadata);
            this.states.set(artworkId, state);

            this.globalHistory.push({
                action: 'state_created',
                artworkId,
                timestamp: Date.now()
            });
        }

        return this.states.get(artworkId);
    }

    /**
     * Add a claim to an artwork's provenance
     * @param {string} artworkId
     * @param {Object} claimData
     * @returns {ProvenanceClaim}
     */
    addClaim(artworkId, claimData) {
        const state = this.getOrCreateState(artworkId);
        return state.addClaim(claimData);
    }

    /**
     * Collapse an artwork's provenance with verification
     * @param {string} artworkId
     * @param {Object} verificationEvent
     * @returns {Object}
     */
    collapseProvenance(artworkId, verificationEvent) {
        const state = this.states.get(artworkId);
        if (!state) {
            return { success: false, error: 'Artwork not found' };
        }

        const result = state.collapse(verificationEvent);

        this.globalHistory.push({
            action: 'provenance_collapsed',
            artworkId,
            result: result.success,
            timestamp: Date.now()
        });

        return result;
    }

    /**
     * Create entanglement between two artworks
     * @param {string} artworkId1
     * @param {string} artworkId2
     * @param {string} relationshipType
     */
    createEntanglement(artworkId1, artworkId2, relationshipType) {
        const state1 = this.states.get(artworkId1);
        const state2 = this.states.get(artworkId2);

        if (!state1 || !state2) {
            return { success: false, error: 'One or both artworks not found' };
        }

        const entanglement = state1.entangle(state2, relationshipType);

        this.globalHistory.push({
            action: 'entanglement_created',
            artworks: [artworkId1, artworkId2],
            type: relationshipType,
            correlation: entanglement.correlation,
            timestamp: Date.now()
        });

        return { success: true, entanglement };
    }

    /**
     * Get all artworks needing resolution (disputed provenance)
     * @returns {Array}
     */
    getDisputedArtworks() {
        const disputed = [];

        for (const [artworkId, state] of this.states) {
            const summary = state.getStateSummary();
            if (summary.status === 'superposed' && summary.needsResolution) {
                disputed.push({
                    artworkId,
                    summary,
                    entropy: summary.entropyLevel
                });
            }
        }

        // Sort by entropy (most uncertain first)
        disputed.sort((a, b) => b.entropy - a.entropy);

        return disputed;
    }

    /**
     * Get registry statistics
     */
    getStatistics() {
        let collapsed = 0;
        let superposed = 0;
        let totalClaims = 0;
        let totalEntanglements = 0;

        for (const state of this.states.values()) {
            if (state.collapsed) {
                collapsed++;
            } else {
                superposed++;
            }
            totalClaims += state.claims.length;
            totalEntanglements += state.entanglements.length;
        }

        return {
            totalArtworks: this.states.size,
            collapsed,
            superposed,
            disputed: this.getDisputedArtworks().length,
            totalClaims,
            totalEntanglements: totalEntanglements / 2, // Counted twice (bidirectional)
            globalHistoryLength: this.globalHistory.length
        };
    }

    /**
     * Export all states
     */
    exportAll() {
        const exports = {};
        for (const [artworkId, state] of this.states) {
            exports[artworkId] = state.export();
        }
        return {
            states: exports,
            statistics: this.getStatistics(),
            globalHistory: this.globalHistory,
            exportedAt: Date.now()
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const quantumProvenanceRegistry = new QuantumProvenanceRegistry();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    ProvenanceClaim,
    QuantumProvenanceState,
    QuantumProvenanceRegistry,
    quantumProvenanceRegistry,
    EVIDENCE_AMPLITUDES,
    CLAIM_STATUS
};

export default quantumProvenanceRegistry;
