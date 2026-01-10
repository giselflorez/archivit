/**
 * IT-R8 SPIRAL GEOMETRY ENGINE
 * ============================
 * The mathematical foundation of the social timeline algorithm
 *
 * Uses logarithmic spiral mathematics: r = a × e^(b×θ)
 * Golden ratio (φ = 1.618033988749895) creates organic, nature-inspired spirals
 *
 * This is the heart of how content flows through time.
 */

// Mathematical constants
const PHI = 1.618033988749895;  // Golden ratio
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));  // 137.5077640500378 degrees in radians
const GOLDEN_SPIRAL_B = Math.log(PHI) / (Math.PI / 2);  // ~0.306

// LOD thresholds for performance
const LOD_THRESHOLDS = {
    ULTRA: { distance: 50, segments: 64, nodeDetail: 32 },
    HIGH: { distance: 150, segments: 32, nodeDetail: 24 },
    MEDIUM: { distance: 300, segments: 16, nodeDetail: 16 },
    LOW: { distance: 500, segments: 8, nodeDetail: 8 },
    MINIMAL: { distance: Infinity, segments: 4, nodeDetail: 6 }
};

// Exponential cache for performance
const expCache = new Map();
const EXP_CACHE_SIZE = 10000;

function cachedExp(x) {
    const key = Math.round(x * 10000);
    if (expCache.has(key)) {
        return expCache.get(key);
    }
    const result = Math.exp(x);
    if (expCache.size >= EXP_CACHE_SIZE) {
        const firstKey = expCache.keys().next().value;
        expCache.delete(firstKey);
    }
    expCache.set(key, result);
    return result;
}

// Catmull-Rom spline for smooth curves
function catmullRom(p0, p1, p2, p3, t) {
    const t2 = t * t;
    const t3 = t2 * t;
    return 0.5 * (
        (2 * p1) +
        (-p0 + p2) * t +
        (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
        (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    );
}

// Easing functions
const Easing = {
    easeInOutCubic: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
    easeOutBounce: (t) => {
        const n1 = 7.5625;
        const d1 = 2.75;
        if (t < 1 / d1) return n1 * t * t;
        if (t < 2 / d1) return n1 * (t -= 1.5 / d1) * t + 0.75;
        if (t < 2.5 / d1) return n1 * (t -= 2.25 / d1) * t + 0.9375;
        return n1 * (t -= 2.625 / d1) * t + 0.984375;
    },
    easeOutElastic: (t) => {
        const c4 = (2 * Math.PI) / 3;
        return t === 0 ? 0 : t === 1 ? 1 :
            Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
    },
    easeGolden: (t) => 1 - Math.pow(1 - t, PHI)
};

/**
 * SpiralGeometry - The Core Algorithm
 *
 * This class generates the mathematical spiral that content follows.
 * The spiral descends through time (Y-axis) while rotating (X/Z plane).
 * Each photo node sits at a position determined by the logarithmic formula.
 */
class SpiralGeometry {
    constructor(config = {}) {
        this.config = {
            // Core spiral parameters
            a: config.a ?? 50,                              // Base radius
            b: config.b ?? 0.1,                             // Growth rate
            thetaIncrement: config.thetaIncrement ?? (Math.PI / 8),  // 22.5° per node
            verticalSpacing: config.verticalSpacing ?? 15,  // Y-axis descent
            verticalDirection: config.verticalDirection ?? -1, // Time flows DOWN

            // Golden spiral mode
            useGoldenSpiral: config.useGoldenSpiral ?? true,

            // Tube geometry for light cable
            tubeRadius: config.tubeRadius ?? 0.5,
            tubeSegments: config.tubeSegments ?? 8,
            pathSegments: config.pathSegments ?? 64,

            // Performance
            enableLOD: config.enableLOD ?? true,
            maxCachedPositions: config.maxCachedPositions ?? 2000,

            // Visual tweaks
            spiralTightness: config.spiralTightness ?? 1.0,
            verticalCompression: config.verticalCompression ?? 1.0,

            // Seashell sub-spiral config
            subSpiralArms: config.subSpiralArms ?? 5,
            subSpiralRevolutions: config.subSpiralRevolutions ?? 3
        };

        // Use golden ratio if requested
        if (this.config.useGoldenSpiral) {
            this.config.b = GOLDEN_SPIRAL_B * this.config.spiralTightness;
        }

        // Precomputed trig tables
        this._precomputed = {
            cosCache: new Float32Array(360),
            sinCache: new Float32Array(360)
        };
        for (let i = 0; i < 360; i++) {
            const rad = (i * Math.PI) / 180;
            this._precomputed.cosCache[i] = Math.cos(rad);
            this._precomputed.sinCache[i] = Math.sin(rad);
        }

        // Position cache
        this._positionCache = new Map();
        this._pathPoints = [];
        this._curve = null;
        this._tubeGeometry = null;
        this._currentLOD = 'HIGH';

        // Metrics
        this._metrics = {
            lastGenerationTime: 0,
            totalNodesGenerated: 0,
            cacheHits: 0,
            cacheMisses: 0
        };
    }

    /**
     * Calculate radius at angle using r = a × e^(b×θ)
     */
    calculateRadius(theta) {
        return this.config.a * cachedExp(this.config.b * theta);
    }

    /**
     * Get 3D position for a node at given index
     */
    getNodePosition(index) {
        if (this._positionCache.has(index)) {
            this._metrics.cacheHits++;
            return this._positionCache.get(index).clone();
        }

        this._metrics.cacheMisses++;

        const theta = index * this.config.thetaIncrement;
        const r = this.calculateRadius(theta);

        const x = r * Math.cos(theta);
        const z = r * Math.sin(theta);
        const y = index * this.config.verticalSpacing *
                  this.config.verticalDirection *
                  this.config.verticalCompression;

        const position = new THREE.Vector3(x, y, z);

        if (this._positionCache.size < this.config.maxCachedPositions) {
            this._positionCache.set(index, position.clone());
        }

        return position;
    }

    /**
     * Generate positions for multiple nodes
     * This is THE core method for placing photos on the timeline
     */
    generatePath(nodeCount, options = {}) {
        const startTime = performance.now();
        const startIndex = options.startIndex ?? 0;
        const includeMetadata = options.includeMetadata ?? false;

        const positions = [];

        for (let i = 0; i < nodeCount; i++) {
            const index = startIndex + i;
            const position = this.getNodePosition(index);

            if (includeMetadata) {
                const theta = index * this.config.thetaIncrement;
                positions.push({
                    position: position,
                    index: index,
                    theta: theta,
                    radius: this.calculateRadius(theta),
                    normalizedProgress: i / (nodeCount - 1 || 1)
                });
            } else {
                positions.push(position);
            }
        }

        this._pathPoints = positions;
        this._metrics.lastGenerationTime = performance.now() - startTime;
        this._metrics.totalNodesGenerated += nodeCount;

        return positions;
    }

    /**
     * Get interpolated position at any time t (0-1)
     * For smooth camera paths through the timeline
     */
    getPositionAtTime(t, totalNodes = 100) {
        t = Math.max(0, Math.min(1, t));

        const floatIndex = t * (totalNodes - 1);
        const lowerIndex = Math.floor(floatIndex);
        const upperIndex = Math.ceil(floatIndex);
        const fraction = floatIndex - lowerIndex;

        const p0 = this.getNodePosition(Math.max(0, lowerIndex - 1));
        const p1 = this.getNodePosition(lowerIndex);
        const p2 = this.getNodePosition(Math.min(totalNodes - 1, upperIndex));
        const p3 = this.getNodePosition(Math.min(totalNodes - 1, upperIndex + 1));

        return new THREE.Vector3(
            catmullRom(p0.x, p1.x, p2.x, p3.x, fraction),
            catmullRom(p0.y, p1.y, p2.y, p3.y, fraction),
            catmullRom(p0.z, p1.z, p2.z, p3.z, fraction)
        );
    }

    /**
     * Get tangent vector at time t for camera orientation
     */
    getTangentAtTime(t, totalNodes = 100) {
        const epsilon = 0.001;
        const p1 = this.getPositionAtTime(Math.max(0, t - epsilon), totalNodes);
        const p2 = this.getPositionAtTime(Math.min(1, t + epsilon), totalNodes);
        return p2.sub(p1).normalize();
    }

    /**
     * Generate tube geometry for the light cable backbone
     */
    getCurveGeometry(nodeCount = 100, options = {}) {
        if (this._pathPoints.length === 0 || this._pathPoints.length !== nodeCount) {
            this.generatePath(nodeCount);
        }

        const points = this._pathPoints.map(p => p.position ? p.position : p);
        this._curve = new THREE.CatmullRomCurve3(points, false, 'centripetal', 0.5);

        const lodSettings = LOD_THRESHOLDS[this._currentLOD];
        const tubeRadius = options.radius ?? this.config.tubeRadius;
        const radialSegments = options.radialSegments ?? lodSettings.segments;
        const tubularSegments = nodeCount * this.config.pathSegments;

        if (this._tubeGeometry) {
            this._tubeGeometry.dispose();
        }

        this._tubeGeometry = new THREE.TubeGeometry(
            this._curve,
            tubularSegments,
            tubeRadius,
            radialSegments,
            false
        );

        return this._tubeGeometry;
    }

    getCurve() {
        return this._curve;
    }

    /**
     * Animate nodes to new positions with easing
     */
    updateNodePositions(nodes, options = {}) {
        const animate = options.animate ?? true;
        const duration = options.duration ?? 1000;
        const easingName = options.easing ?? 'easeGolden';
        const easingFn = Easing[easingName] || Easing.easeGolden;

        if (!animate) {
            nodes.forEach((node, index) => {
                if (node.mesh) {
                    const position = this.getNodePosition(index);
                    node.mesh.position.copy(position);
                    node.targetPosition = position;
                }
            });
            return Promise.resolve();
        }

        nodes.forEach((node, index) => {
            if (node.mesh) {
                node.startPosition = node.mesh.position.clone();
                node.targetPosition = this.getNodePosition(index);
            }
        });

        return new Promise((resolve) => {
            const startTime = performance.now();

            const animateFrame = () => {
                const elapsed = performance.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easedProgress = easingFn(progress);

                nodes.forEach((node) => {
                    if (node.mesh && node.startPosition && node.targetPosition) {
                        node.mesh.position.lerpVectors(
                            node.startPosition,
                            node.targetPosition,
                            easedProgress
                        );
                    }
                });

                if (progress < 1) {
                    requestAnimationFrame(animateFrame);
                } else {
                    resolve();
                }
            };

            requestAnimationFrame(animateFrame);
        });
    }

    /**
     * Generate seashell sub-spiral for spark/comment emissions
     * Uses Golden Angle (137.5°) for natural nautilus distribution
     */
    generateSeashellSubSpiral(center, pointCount = 21, maxRadius = 5, options = {}) {
        const points = [];
        const arms = options.arms ?? this.config.subSpiralArms;
        const verticalSpread = options.verticalSpread ?? 2;

        for (let arm = 0; arm < arms; arm++) {
            const armOffset = (arm / arms) * Math.PI * 2;

            for (let i = 0; i < pointCount; i++) {
                // Golden angle distribution - nature's pattern
                const goldenTheta = i * GOLDEN_ANGLE + armOffset;

                // Fermat spiral radius (sqrt creates sunflower pattern)
                const normalizedIndex = i / pointCount;
                const r = maxRadius * Math.sqrt(normalizedIndex);

                const x = center.x + r * Math.cos(goldenTheta);
                const z = center.z + r * Math.sin(goldenTheta);
                const y = center.y + (Math.random() - 0.5) * verticalSpread * normalizedIndex;

                points.push(new THREE.Vector3(x, y, z));
            }
        }

        return points;
    }

    /**
     * Batch generate emission points for particle system
     * Returns Float32Array for direct GPU upload
     */
    generateBatchEmissionPoints(nodePositions, pointsPerNode = 13, emissionRadius = 3) {
        const totalPoints = nodePositions.length * pointsPerNode * this.config.subSpiralArms;
        const positions = new Float32Array(totalPoints * 3);

        let offset = 0;

        nodePositions.forEach((center) => {
            const subPoints = this.generateSeashellSubSpiral(
                center,
                pointsPerNode,
                emissionRadius,
                { arms: this.config.subSpiralArms }
            );

            subPoints.forEach(point => {
                positions[offset++] = point.x;
                positions[offset++] = point.y;
                positions[offset++] = point.z;
            });
        });

        return positions;
    }

    /**
     * Update LOD based on camera distance
     */
    updateLOD(cameraDistance) {
        let newLOD = 'MINIMAL';

        for (const [level, settings] of Object.entries(LOD_THRESHOLDS)) {
            if (cameraDistance <= settings.distance) {
                newLOD = level;
                break;
            }
        }

        if (newLOD !== this._currentLOD) {
            this._currentLOD = newLOD;
            this._positionCache.clear();
        }

        return this._currentLOD;
    }

    getLODSettings() {
        return LOD_THRESHOLDS[this._currentLOD];
    }

    updateConfig(newConfig, clearCache = true) {
        Object.assign(this.config, newConfig);

        if (this.config.useGoldenSpiral) {
            this.config.b = GOLDEN_SPIRAL_B * this.config.spiralTightness;
        }

        if (clearCache) {
            this._positionCache.clear();
            this._pathPoints = [];
            if (this._tubeGeometry) {
                this._tubeGeometry.dispose();
                this._tubeGeometry = null;
            }
            this._curve = null;
        }
    }

    getConfig() {
        return { ...this.config };
    }

    getMetrics() {
        return {
            ...this._metrics,
            cacheSize: this._positionCache.size,
            cacheHitRate: this._metrics.cacheHits /
                         (this._metrics.cacheHits + this._metrics.cacheMisses || 1)
        };
    }

    clearCache() {
        this._positionCache.clear();
        this._pathPoints = [];
        expCache.clear();
        if (this._tubeGeometry) {
            this._tubeGeometry.dispose();
            this._tubeGeometry = null;
        }
        this._curve = null;
        this._metrics.cacheHits = 0;
        this._metrics.cacheMisses = 0;
    }

    dispose() {
        this.clearCache();
    }

    // Factory methods for different spiral styles

    static createGoldenSpiral(nodeCount = 100) {
        return new SpiralGeometry({
            useGoldenSpiral: true,
            a: 30,
            verticalSpacing: 12,
            thetaIncrement: GOLDEN_ANGLE / 5,
            spiralTightness: 1.0
        });
    }

    static createDramaticSpiral(nodeCount = 100) {
        return new SpiralGeometry({
            useGoldenSpiral: false,
            a: 80,
            b: 0.15,
            verticalSpacing: 25,
            thetaIncrement: Math.PI / 6,
            spiralTightness: 1.5
        });
    }

    static createCompactSpiral(nodeCount = 100) {
        return new SpiralGeometry({
            useGoldenSpiral: true,
            a: 20,
            verticalSpacing: 8,
            thetaIncrement: Math.PI / 12,
            spiralTightness: 0.7,
            verticalCompression: 0.6
        });
    }

    static createDoubleHelix(nodeCount = 100) {
        const baseConfig = {
            useGoldenSpiral: false,
            a: 40,
            b: 0.05,
            verticalSpacing: 10,
            thetaIncrement: Math.PI / 8
        };

        return {
            strand1: new SpiralGeometry(baseConfig),
            strand2: new SpiralGeometry({
                ...baseConfig,
                thetaIncrement: Math.PI / 8 + Math.PI
            })
        };
    }
}

// Export constants
export { PHI, GOLDEN_ANGLE, GOLDEN_SPIRAL_B, LOD_THRESHOLDS, Easing };
export { catmullRom, cachedExp };
export { SpiralGeometry };
export default SpiralGeometry;
