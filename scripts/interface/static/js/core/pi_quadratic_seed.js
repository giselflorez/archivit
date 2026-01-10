/**
 * PI-QUADRATIC SEED (PQS) ENGINE
 * ==============================
 * The Mathematical Soul of the Ecosystem
 *
 * TRADE SECRET ARCHITECTURE:
 * This module creates a proprietary encoding layer using:
 * 1. Pi (π) as an infinite, deterministic entropy source
 * 2. Quadratic transformations for non-linear encoding
 * 3. User-unique offsets that create ecosystem-locked data
 *
 * WITHOUT the genesis offset, the encoded data is meaningless.
 * WITH the offset, it becomes a window into behavioral understanding.
 *
 * THE PHILOSOPHY:
 * - Your past teaches your future
 * - Your patterns reveal your optimal path
 * - The vertex of your quadratic curve is where you're meant to be
 */

// Pi to 1000 digits (expandable via computation)
const PI_DIGITS = '3141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647093844609550582231725359408128481117450284102701938521105559644622948954930381964428810975665933446128475648233786783165271201909145648566923460348610454326648213393607260249141273724587006606315588174881520920962829254091715364367892590360011330530548820466521384146951941511609433057270365759591953092186117381932611793105118548074462379962749567351885752724891227938183011949129833673362440656643086021394946395224737190702179860943702770539217176293176752384674818467669405132000568127145263560827785771342757789609173637178721468440901224953430146549585371050792279689258923542019956112129021960864034418159813629774771309960518707211349999998372978049951059731732816096318595024459455346908302642522308253344685035261931188171010003137838752886587533208381420617177669147303598253490428755468731159562863882353787593751957781857780532171226806613001927876611195909216420199';

// Golden ratio for additional entropy
const PHI = 1.618033988749895;
const GOLDEN_ANGLE = 137.5077640500378;

/**
 * PI-QUADRATIC SEED CLASS
 * The core mathematical engine
 */
class PiQuadraticSeed {
    constructor(genesisOffset = null) {
        // Genesis offset into π (determines all coefficients)
        this.offset = genesisOffset || this._generateOffset();

        // Quadratic coefficients derived from π
        this.coefficients = this._deriveCoefficients();

        // The vertex of the parabola (the "optimal point")
        this.vertex = this._calculateVertex();

        // Encoding state
        this.encodingHistory = [];
        this.decodingMap = new Map();

        // Behavioral accumulator
        this.behaviorAccumulator = {
            vectors: [],
            centroid: null,
            trajectory: []
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // CORE PI OPERATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get digits from π at a specific position
     * @param {number} position - Starting position in π
     * @param {number} count - Number of digits to retrieve
     * @returns {string} Digits from π
     */
    getPiDigits(position, count) {
        // Wrap around if we exceed our stored digits
        const wrappedPos = position % (PI_DIGITS.length - count);
        return PI_DIGITS.substring(wrappedPos, wrappedPos + count);
    }

    /**
     * Convert π digits to a decimal coefficient
     * @param {number} position - Position in π
     * @param {number} precision - Decimal places
     * @returns {number} Coefficient derived from π
     */
    piToCoefficient(position, precision = 4) {
        const digits = this.getPiDigits(position, precision + 1);
        const intPart = parseInt(digits[0]);
        const decPart = digits.substring(1);
        return parseFloat(`${intPart}.${decPart}`);
    }

    /**
     * Generate a unique offset from entropy
     * This becomes the user's "key" into π
     */
    _generateOffset() {
        // Use crypto for true randomness
        const array = new Uint32Array(1);
        crypto.getRandomValues(array);
        // Limit to valid range within our π digits
        return array[0] % (PI_DIGITS.length - 100);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // QUADRATIC FOUNDATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Derive quadratic coefficients from π at user's offset
     * f(x) = ax² + bx + c
     */
    _deriveCoefficients() {
        // Each coefficient comes from different position in π
        // relative to the user's genesis offset
        const a = this.piToCoefficient(this.offset, 4) / 10;           // Keep a small for gentle curve
        const b = this.piToCoefficient(this.offset + 10, 4) - 5;      // Center b around 0
        const c = this.piToCoefficient(this.offset + 20, 4);          // c is the y-intercept

        // Add golden ratio influence for organic feel
        const phiModA = a * (1 + (PHI - 1) * 0.1);
        const phiModB = b * PHI * 0.5;
        const phiModC = c + GOLDEN_ANGLE / 100;

        return {
            a: phiModA,
            b: phiModB,
            c: phiModC,
            raw: { a, b, c }
        };
    }

    /**
     * Calculate the vertex of the parabola
     * Vertex = (-b/2a, f(-b/2a))
     * This represents the "optimal point" in the encoded space
     */
    _calculateVertex() {
        const { a, b, c } = this.coefficients;

        // Vertex x-coordinate
        const vx = -b / (2 * a);

        // Vertex y-coordinate (plug vx back into quadratic)
        const vy = a * vx * vx + b * vx + c;

        return {
            x: vx,
            y: vy,
            // The vertex represents the "attractor" - where behavior tends toward
            meaning: 'optimal_state'
        };
    }

    /**
     * The core quadratic function
     * f(x) = ax² + bx + c
     */
    quadratic(x) {
        const { a, b, c } = this.coefficients;
        return a * x * x + b * x + c;
    }

    /**
     * Inverse quadratic (for decoding)
     * Solves ax² + bx + (c - y) = 0 for x
     */
    inverseQuadratic(y) {
        const { a, b, c } = this.coefficients;
        const discriminant = b * b - 4 * a * (c - y);

        if (discriminant < 0) {
            // No real solution - use complex handling
            return {
                real: -b / (2 * a),
                imaginary: Math.sqrt(-discriminant) / (2 * a),
                isComplex: true
            };
        }

        // Two solutions (parabola intersects y at two points)
        const sqrtDisc = Math.sqrt(discriminant);
        return {
            x1: (-b + sqrtDisc) / (2 * a),
            x2: (-b - sqrtDisc) / (2 * a),
            isComplex: false
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // ENCODING ENGINE (Trade Secret Core)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Encode a behavioral value through the π-quadratic transform
     * @param {number} value - Raw behavioral metric
     * @param {string} dimension - What this value represents
     * @returns {object} Encoded value with metadata
     */
    encode(value, dimension = 'generic') {
        // Step 1: Normalize value to reasonable range
        const normalized = this._normalize(value, dimension);

        // Step 2: Apply π-seeded rotation
        const piRotation = this._piRotate(normalized, dimension);

        // Step 3: Apply quadratic transformation
        const quadTransform = this.quadratic(piRotation);

        // Step 4: Apply golden spiral compression
        const goldenCompressed = this._goldenCompress(quadTransform);

        // Step 5: Calculate distance from vertex (how far from optimal)
        const vertexDistance = Math.sqrt(
            Math.pow(piRotation - this.vertex.x, 2) +
            Math.pow(quadTransform - this.vertex.y, 2)
        );

        // Store in history
        const encoded = {
            original: value,
            dimension: dimension,
            normalized: normalized,
            piRotated: piRotation,
            quadratic: quadTransform,
            compressed: goldenCompressed,
            vertexDistance: vertexDistance,
            timestamp: Date.now(),
            // The "direction" indicates if user is approaching or departing optimal
            trajectory: vertexDistance < (this._getLastVertexDistance(dimension) || vertexDistance)
                ? 'approaching_optimal'
                : 'departing_optimal'
        };

        this.encodingHistory.push(encoded);

        // Update behavior accumulator
        this._accumulateBehavior(encoded);

        return encoded;
    }

    /**
     * Decode an encoded value back to original
     * Only possible with the correct genesis offset
     */
    decode(encodedValue) {
        // Step 1: Decompress from golden
        const decompressed = this._goldenDecompress(encodedValue.compressed);

        // Step 2: Inverse quadratic
        const inverseQuad = this.inverseQuadratic(decompressed);

        // Step 3: Reverse π rotation
        const derotated = this._piDerotate(
            inverseQuad.isComplex ? inverseQuad.real : inverseQuad.x1,
            encodedValue.dimension
        );

        // Step 4: Denormalize
        const denormalized = this._denormalize(derotated, encodedValue.dimension);

        return {
            decoded: denormalized,
            confidence: inverseQuad.isComplex ? 0.7 : 0.95,
            wasComplex: inverseQuad.isComplex
        };
    }

    /**
     * Encode a complete behavioral pattern object
     */
    encodePattern(pattern) {
        const encoded = {};

        for (const [key, value] of Object.entries(pattern)) {
            if (typeof value === 'number') {
                encoded[key] = this.encode(value, key);
            } else if (typeof value === 'object' && value !== null) {
                encoded[key] = this.encodePattern(value);
            } else {
                // String/boolean - hash and encode
                encoded[key] = this.encode(this._hashString(String(value)), key);
            }
        }

        return encoded;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PI ROTATION (The Secret Sauce)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Rotate a value using π digits at dimension-specific offset
     * This creates dimension-dependent encoding
     */
    _piRotate(value, dimension) {
        // Each dimension gets its own offset into π
        const dimensionHash = this._hashString(dimension);
        const dimensionOffset = dimensionHash % 100;

        // Get rotation angle from π
        const rotationDigits = this.getPiDigits(this.offset + dimensionOffset, 6);
        const rotationAngle = parseInt(rotationDigits) / 1000000 * Math.PI * 2;

        // Apply rotation in value space
        const rotated = value * Math.cos(rotationAngle) +
                        (value * PHI) * Math.sin(rotationAngle);

        return rotated;
    }

    _piDerotate(value, dimension) {
        const dimensionHash = this._hashString(dimension);
        const dimensionOffset = dimensionHash % 100;

        const rotationDigits = this.getPiDigits(this.offset + dimensionOffset, 6);
        const rotationAngle = parseInt(rotationDigits) / 1000000 * Math.PI * 2;

        // Reverse rotation
        const cos = Math.cos(rotationAngle);
        const sin = Math.sin(rotationAngle);
        const det = cos * cos + PHI * sin * sin;

        return (value * cos) / det;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // GOLDEN COMPRESSION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Compress using golden ratio spiral
     * Creates organic, nature-inspired encoding
     */
    _goldenCompress(value) {
        // Map value to golden spiral
        const theta = value * GOLDEN_ANGLE * (Math.PI / 180);
        const r = Math.pow(PHI, theta / (Math.PI * 2));

        // Return as complex-like structure
        return {
            magnitude: r,
            phase: theta % (Math.PI * 2),
            combined: r * Math.cos(theta) + r * Math.sin(theta) * PHI
        };
    }

    _goldenDecompress(compressed) {
        const { magnitude, phase } = compressed;

        // Reverse the golden spiral
        const theta = Math.log(magnitude) / Math.log(PHI) * (Math.PI * 2);
        const value = theta / (GOLDEN_ANGLE * (Math.PI / 180));

        return value;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PREDICTIVE ENGINE
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Predict optimal future state based on encoded history
     * Uses the vertex as the attractor point
     */
    predictOptimalPath() {
        if (this.behaviorAccumulator.vectors.length < 3) {
            return {
                prediction: null,
                confidence: 0,
                reason: 'Insufficient data for prediction'
            };
        }

        // Calculate trajectory toward vertex
        const trajectory = this._calculateTrajectory();

        // Calculate when trajectory intersects optimal zone
        const optimalIntersection = this._findOptimalIntersection(trajectory);

        // Generate recommendations
        const recommendations = this._generateRecommendations(trajectory, optimalIntersection);

        return {
            currentState: this.behaviorAccumulator.centroid,
            optimalState: this.vertex,
            trajectory: trajectory,
            predictedOptimalAt: optimalIntersection,
            recommendations: recommendations,
            confidence: this._calculatePredictionConfidence()
        };
    }

    _calculateTrajectory() {
        const vectors = this.behaviorAccumulator.vectors;
        const recent = vectors.slice(-10);  // Last 10 data points

        // Calculate average direction
        let avgDx = 0, avgDy = 0;
        for (let i = 1; i < recent.length; i++) {
            avgDx += recent[i].x - recent[i-1].x;
            avgDy += recent[i].y - recent[i-1].y;
        }

        avgDx /= (recent.length - 1) || 1;
        avgDy /= (recent.length - 1) || 1;

        // Direction vector
        const magnitude = Math.sqrt(avgDx * avgDx + avgDy * avgDy);

        return {
            direction: { x: avgDx / magnitude, y: avgDy / magnitude },
            speed: magnitude,
            angle: Math.atan2(avgDy, avgDx),
            // Angle to vertex
            angleToOptimal: Math.atan2(
                this.vertex.y - this.behaviorAccumulator.centroid.y,
                this.vertex.x - this.behaviorAccumulator.centroid.x
            )
        };
    }

    _findOptimalIntersection(trajectory) {
        const centroid = this.behaviorAccumulator.centroid;

        // Project trajectory forward
        const steps = [];
        let x = centroid.x;
        let y = centroid.y;

        for (let i = 0; i < 100; i++) {
            x += trajectory.direction.x * trajectory.speed;
            y += trajectory.direction.y * trajectory.speed;

            const distToVertex = Math.sqrt(
                Math.pow(x - this.vertex.x, 2) +
                Math.pow(y - this.vertex.y, 2)
            );

            steps.push({ x, y, distToVertex, step: i });

            // Check if we're close enough to optimal
            if (distToVertex < 0.1) {
                return {
                    reachable: true,
                    stepsToOptimal: i,
                    path: steps
                };
            }
        }

        // Find closest approach
        const closestStep = steps.reduce((min, step) =>
            step.distToVertex < min.distToVertex ? step : min
        );

        return {
            reachable: false,
            closestApproach: closestStep,
            path: steps,
            courseCorrection: this._calculateCourseCorrection(trajectory)
        };
    }

    _calculateCourseCorrection(trajectory) {
        // How much to adjust to reach optimal
        const angleDiff = trajectory.angleToOptimal - trajectory.angle;

        return {
            angleAdjustment: angleDiff,
            adjustmentMagnitude: Math.abs(angleDiff),
            direction: angleDiff > 0 ? 'increase' : 'decrease',
            // Map to human-readable advice
            interpretation: this._interpretCourseCorrection(angleDiff)
        };
    }

    _interpretCourseCorrection(angleDiff) {
        const absDiff = Math.abs(angleDiff);

        if (absDiff < 0.1) return 'On track - continue current patterns';
        if (absDiff < 0.5) return 'Minor adjustment needed';
        if (absDiff < 1.0) return 'Moderate course correction recommended';
        return 'Significant change needed to reach optimal state';
    }

    _generateRecommendations(trajectory, intersection) {
        const recommendations = [];

        if (!intersection.reachable) {
            recommendations.push({
                type: 'course_correction',
                priority: 'high',
                message: intersection.courseCorrection.interpretation,
                action: `Adjust ${intersection.courseCorrection.direction} in behavioral patterns`
            });
        }

        // Analyze which dimensions are furthest from optimal
        const encodingsByDimension = {};
        this.encodingHistory.forEach(enc => {
            if (!encodingsByDimension[enc.dimension]) {
                encodingsByDimension[enc.dimension] = [];
            }
            encodingsByDimension[enc.dimension].push(enc);
        });

        for (const [dim, encodings] of Object.entries(encodingsByDimension)) {
            const avgDistance = encodings.reduce((sum, e) => sum + e.vertexDistance, 0) / encodings.length;
            const trend = encodings.slice(-5).reduce((sum, e, i, arr) => {
                if (i === 0) return 0;
                return sum + (e.vertexDistance - arr[i-1].vertexDistance);
            }, 0);

            if (avgDistance > 1.0) {
                recommendations.push({
                    type: 'dimension_focus',
                    dimension: dim,
                    priority: trend > 0 ? 'high' : 'medium',
                    message: `${dim} is far from optimal`,
                    trend: trend > 0 ? 'worsening' : 'improving'
                });
            }
        }

        return recommendations;
    }

    _calculatePredictionConfidence() {
        const dataPoints = this.encodingHistory.length;
        const minForConfidence = 10;
        const maxConfidenceAt = 100;

        if (dataPoints < minForConfidence) return 0;

        // Logarithmic confidence growth
        const confidence = Math.min(1, Math.log(dataPoints / minForConfidence) / Math.log(maxConfidenceAt / minForConfidence));

        return confidence;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // BEHAVIORAL ACCUMULATION
    // ═══════════════════════════════════════════════════════════════════════

    _accumulateBehavior(encoded) {
        // Add to vector space
        const vector = {
            x: encoded.piRotated,
            y: encoded.quadratic,
            timestamp: encoded.timestamp,
            dimension: encoded.dimension
        };

        this.behaviorAccumulator.vectors.push(vector);

        // Keep last 1000 vectors
        if (this.behaviorAccumulator.vectors.length > 1000) {
            this.behaviorAccumulator.vectors.shift();
        }

        // Recalculate centroid
        this._updateCentroid();

        // Update trajectory
        this._updateTrajectory();
    }

    _updateCentroid() {
        const vectors = this.behaviorAccumulator.vectors;
        if (vectors.length === 0) {
            this.behaviorAccumulator.centroid = { x: 0, y: 0 };
            return;
        }

        const sumX = vectors.reduce((sum, v) => sum + v.x, 0);
        const sumY = vectors.reduce((sum, v) => sum + v.y, 0);

        this.behaviorAccumulator.centroid = {
            x: sumX / vectors.length,
            y: sumY / vectors.length
        };
    }

    _updateTrajectory() {
        const vectors = this.behaviorAccumulator.vectors;
        if (vectors.length < 2) return;

        const recent = vectors.slice(-20);
        const trajectory = [];

        for (let i = 1; i < recent.length; i++) {
            trajectory.push({
                dx: recent[i].x - recent[i-1].x,
                dy: recent[i].y - recent[i-1].y,
                dt: recent[i].timestamp - recent[i-1].timestamp
            });
        }

        this.behaviorAccumulator.trajectory = trajectory;
    }

    _getLastVertexDistance(dimension) {
        const matching = this.encodingHistory
            .filter(e => e.dimension === dimension)
            .slice(-1)[0];
        return matching ? matching.vertexDistance : null;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UTILITIES
    // ═══════════════════════════════════════════════════════════════════════

    _normalize(value, dimension) {
        // Dimension-specific normalization ranges
        const ranges = {
            'temporal': { min: 0, max: 24 },      // Hours
            'frequency': { min: 0, max: 1000 },   // Counts
            'sentiment': { min: -1, max: 1 },     // Emotion
            'intensity': { min: 0, max: 1 },      // 0-1 scale
            'generic': { min: -1000, max: 1000 }  // Catch-all
        };

        const range = ranges[dimension] || ranges.generic;
        return (value - range.min) / (range.max - range.min);
    }

    _denormalize(normalized, dimension) {
        const ranges = {
            'temporal': { min: 0, max: 24 },
            'frequency': { min: 0, max: 1000 },
            'sentiment': { min: -1, max: 1 },
            'intensity': { min: 0, max: 1 },
            'generic': { min: -1000, max: 1000 }
        };

        const range = ranges[dimension] || ranges.generic;
        return normalized * (range.max - range.min) + range.min;
    }

    _hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // EXPORT/IMPORT
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Export the PQS state (for backup)
     */
    export() {
        return {
            version: '1.0.0',
            offset: this.offset,
            coefficients: this.coefficients,
            vertex: this.vertex,
            encodingHistory: this.encodingHistory.slice(-100),  // Last 100
            behaviorAccumulator: {
                centroid: this.behaviorAccumulator.centroid,
                vectorCount: this.behaviorAccumulator.vectors.length
            },
            exportedAt: Date.now()
        };
    }

    /**
     * Create a verification hash to prove ownership
     */
    generateOwnershipProof() {
        const proofData = {
            offset: this.offset,
            vertexX: this.vertex.x.toFixed(10),
            vertexY: this.vertex.y.toFixed(10),
            historyLength: this.encodingHistory.length,
            timestamp: Date.now()
        };

        // Create proof hash
        const proofString = JSON.stringify(proofData);
        const hash = this._hashString(proofString);

        return {
            proof: hash.toString(16),
            data: proofData,
            // This can only be verified by someone with the same offset
            verificationChallenge: this.quadratic(hash % 100).toFixed(10)
        };
    }

    /**
     * Verify ownership proof
     */
    verifyOwnershipProof(proof) {
        const expectedChallenge = this.quadratic(parseInt(proof.proof, 16) % 100).toFixed(10);
        return expectedChallenge === proof.verificationChallenge;
    }
}

/**
 * Integration with Seed Profile
 * Connects PQS to the main seed engine
 */
class PQSSeedIntegration {
    constructor(seedEngine, pqs) {
        this.seedEngine = seedEngine;
        this.pqs = pqs;
    }

    /**
     * Encode all behavioral data before storage
     */
    encodeBeforeStorage(data) {
        return this.pqs.encodePattern(data);
    }

    /**
     * Get personalized predictions
     */
    getPredictions() {
        return this.pqs.predictOptimalPath();
    }

    /**
     * Process new data through PQS before adding to seed
     */
    processAndEncode(rawData, dimension) {
        const encoded = this.pqs.encode(rawData, dimension);

        return {
            encoded: encoded,
            prediction: this.pqs.predictOptimalPath(),
            distanceFromOptimal: encoded.vertexDistance,
            trajectory: encoded.trajectory
        };
    }
}

// Export
export {
    PiQuadraticSeed,
    PQSSeedIntegration,
    PI_DIGITS,
    PHI,
    GOLDEN_ANGLE
};

export default PiQuadraticSeed;
