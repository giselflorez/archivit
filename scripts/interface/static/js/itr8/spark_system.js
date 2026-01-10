/**
 * IT-R8 SEASHELL SPARK PARTICLE SYSTEM
 * ====================================
 * Comments, reactions, and tags fly out in golden angle formations
 * Like seeds in a sunflower or chambers in a nautilus shell
 */

// Golden angle in radians - 137.5077640500378 degrees
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
const LOG_SPIRAL_GROWTH = 0.1;

// Vibrant social app colors
const COLORS = {
    HOT_PINK: new THREE.Color(0xff1493),
    ELECTRIC_YELLOW: new THREE.Color(0xffff00),
    CYAN: new THREE.Color(0x00ffff),
    MAGENTA: new THREE.Color(0xff00ff),
    ELECTRIC_ORANGE: new THREE.Color(0xff6600),
    PLASMA_BLUE: new THREE.Color(0x0099ff)
};

const COLOR_ARRAY = Object.values(COLORS);

// GPU Shaders for sparks
const SPARK_VERTEX_SHADER = `
    precision highp float;

    attribute vec3 instancePosition;
    attribute vec3 instanceVelocity;
    attribute vec4 instanceColor;
    attribute float instanceSize;
    attribute float instanceLife;
    attribute float instanceMaxLife;
    attribute float instanceSpiralAngle;
    attribute float instanceSpiralRadius;

    uniform float uTime;
    uniform float uIntensity;
    uniform vec2 uResolution;

    varying vec4 vColor;
    varying float vLife;
    varying float vSize;

    void main() {
        float lifeRatio = instanceLife / instanceMaxLife;

        // Seashell spiral trajectory: r = a * e^(b * theta)
        float spiralProgress = lifeRatio * 3.14159 * 2.0;
        float theta = instanceSpiralAngle + spiralProgress * 2.0;
        float radius = instanceSpiralRadius * exp(${LOG_SPIRAL_GROWTH.toFixed(4)} * spiralProgress * 10.0);

        // Position along spiral
        vec3 spiralOffset = vec3(
            cos(theta) * radius,
            sin(theta) * radius * 0.5 + lifeRatio * instanceVelocity.y * 2.0,
            sin(theta * 0.5) * radius * 0.3
        );

        vec3 pos = instancePosition + spiralOffset + instanceVelocity * lifeRatio * 3.0;

        // Organic wobble
        pos.x += sin(uTime * 3.0 + instanceSpiralAngle * 5.0) * 0.1 * (1.0 - lifeRatio);
        pos.y += cos(uTime * 2.5 + instanceSpiralAngle * 3.0) * 0.08 * (1.0 - lifeRatio);

        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;

        // Size with distance attenuation
        float sizeAttenuation = 300.0 / length(mvPosition.xyz);
        float lifeFade = 1.0 - lifeRatio * lifeRatio;
        gl_PointSize = instanceSize * sizeAttenuation * lifeFade * uIntensity;

        // Pass to fragment
        vColor = instanceColor;
        vLife = lifeRatio;
        vSize = instanceSize;
    }
`;

const SPARK_FRAGMENT_SHADER = `
    precision highp float;

    uniform float uTime;
    uniform float uIntensity;

    varying vec4 vColor;
    varying float vLife;
    varying float vSize;

    void main() {
        vec2 center = gl_PointCoord - vec2(0.5);
        float dist = length(center);

        if (dist > 0.5) discard;

        // Hot white core transitioning to color
        float core = 1.0 - smoothstep(0.0, 0.15, dist);
        float glow = 1.0 - smoothstep(0.0, 0.5, dist);
        glow = pow(glow, 1.5);

        // Chromatic shimmer
        float shimmer = sin(uTime * 20.0 + vLife * 50.0) * 0.15 + 0.85;

        // Color: white core -> vibrant color
        vec3 coreColor = vec3(1.0);
        vec3 sparkColor = mix(vColor.rgb * 2.0, coreColor, core);
        sparkColor *= glow * shimmer;

        // Life fade
        float alpha = glow * (1.0 - vLife * vLife) * uIntensity;

        gl_FragColor = vec4(sparkColor, alpha);
    }
`;

// Spark data structure
class Spark {
    constructor() {
        this.position = new THREE.Vector3();
        this.velocity = new THREE.Vector3();
        this.color = new THREE.Color();
        this.size = 1.0;
        this.life = 0;
        this.maxLife = 1;
        this.spiralAngle = 0;
        this.spiralRadius = 0;
        this.importance = 1.0;
        this.active = false;
        this.text = null;
        this.trail = [];
    }

    reset() {
        this.position.set(0, 0, 0);
        this.velocity.set(0, 0, 0);
        this.life = 0;
        this.active = false;
        this.text = null;
        this.trail.length = 0;
    }
}

// Trail point for glowing trails
class TrailPoint {
    constructor(position, color, alpha, size) {
        this.position = position.clone();
        this.color = color.clone();
        this.alpha = alpha;
        this.size = size;
        this.life = 1.0;
    }
}

/**
 * SparkSystem - GPU-instanced particle engine
 */
class SparkSystem {
    constructor(scene, config = {}) {
        this.scene = scene;

        this.config = {
            maxParticles: config.maxParticles || 10000,
            maxTrailPoints: config.maxTrailPoints || 50000,
            trailLength: config.trailLength || 20,
            trailDecay: config.trailDecay || 0.92,
            sparkLifetime: config.sparkLifetime || 3.0,
            sparkSpeed: config.sparkSpeed || 2.0,
            spiralTightness: config.spiralTightness || 0.3,
            wobbleAmount: config.wobbleAmount || 0.15,
            ...config
        };

        this.intensity = 1.0;
        this.time = 0;
        this.sparkIndex = 0;

        // Object pools
        this.sparks = [];
        this.activeSparks = [];
        this.trailData = [];

        // Text labels
        this.textLabels = new Map();

        this._initializePools();
        this._createSparkSystem();
        this._createTrailSystem();

        this.scene.add(this.sparkPoints);
        this.scene.add(this.trailPointsMesh);

        console.log('[SparkSystem] Initialized with', this.config.maxParticles, 'particle capacity');
    }

    _initializePools() {
        for (let i = 0; i < this.config.maxParticles; i++) {
            this.sparks.push(new Spark());
        }
    }

    _createSparkSystem() {
        const geometry = new THREE.BufferGeometry();

        geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));

        // Instance attributes
        const count = this.config.maxParticles;
        this.instancePositionAttr = new THREE.InstancedBufferAttribute(new Float32Array(count * 3), 3);
        this.instanceVelocityAttr = new THREE.InstancedBufferAttribute(new Float32Array(count * 3), 3);
        this.instanceColorAttr = new THREE.InstancedBufferAttribute(new Float32Array(count * 4), 4);
        this.instanceSizeAttr = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
        this.instanceLifeAttr = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
        this.instanceMaxLifeAttr = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
        this.instanceSpiralAngleAttr = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
        this.instanceSpiralRadiusAttr = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);

        // Dynamic updates
        this.instancePositionAttr.setUsage(THREE.DynamicDrawUsage);
        this.instanceVelocityAttr.setUsage(THREE.DynamicDrawUsage);
        this.instanceColorAttr.setUsage(THREE.DynamicDrawUsage);
        this.instanceSizeAttr.setUsage(THREE.DynamicDrawUsage);
        this.instanceLifeAttr.setUsage(THREE.DynamicDrawUsage);

        geometry.setAttribute('instancePosition', this.instancePositionAttr);
        geometry.setAttribute('instanceVelocity', this.instanceVelocityAttr);
        geometry.setAttribute('instanceColor', this.instanceColorAttr);
        geometry.setAttribute('instanceSize', this.instanceSizeAttr);
        geometry.setAttribute('instanceLife', this.instanceLifeAttr);
        geometry.setAttribute('instanceMaxLife', this.instanceMaxLifeAttr);
        geometry.setAttribute('instanceSpiralAngle', this.instanceSpiralAngleAttr);
        geometry.setAttribute('instanceSpiralRadius', this.instanceSpiralRadiusAttr);

        const material = new THREE.ShaderMaterial({
            vertexShader: SPARK_VERTEX_SHADER,
            fragmentShader: SPARK_FRAGMENT_SHADER,
            uniforms: {
                uTime: { value: 0 },
                uIntensity: { value: 1.0 },
                uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) }
            },
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            depthTest: true
        });

        this.sparkGeometry = geometry;
        this.sparkMaterial = material;
        this.sparkPoints = new THREE.Points(geometry, material);
        this.sparkPoints.frustumCulled = false;
        geometry.instanceCount = 0;
    }

    _createTrailSystem() {
        const geometry = new THREE.BufferGeometry();
        const count = this.config.maxTrailPoints;

        this.trailPositionAttr = new THREE.BufferAttribute(new Float32Array(count * 3), 3);
        this.trailColorAttr = new THREE.BufferAttribute(new Float32Array(count * 4), 4);
        this.trailAlphaAttr = new THREE.BufferAttribute(new Float32Array(count), 1);
        this.trailSizeAttr = new THREE.BufferAttribute(new Float32Array(count), 1);

        this.trailPositionAttr.setUsage(THREE.DynamicDrawUsage);
        this.trailColorAttr.setUsage(THREE.DynamicDrawUsage);

        geometry.setAttribute('position', this.trailPositionAttr);
        geometry.setAttribute('instanceColor', this.trailColorAttr);

        const material = new THREE.PointsMaterial({
            size: 2,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            vertexColors: true
        });

        this.trailGeometry = geometry;
        this.trailMaterial = material;
        this.trailPointsMesh = new THREE.Points(geometry, material);
        this.trailPointsMesh.frustumCulled = false;
    }

    _getInactiveSpark() {
        for (let i = 0; i < this.sparks.length; i++) {
            const idx = (this.sparkIndex + i) % this.sparks.length;
            if (!this.sparks[idx].active) {
                this.sparkIndex = (idx + 1) % this.sparks.length;
                return this.sparks[idx];
            }
        }
        // Recycle oldest
        const oldest = this.activeSparks.shift();
        if (oldest) {
            oldest.reset();
            return oldest;
        }
        return null;
    }

    /**
     * Emit sparks in seashell formation from a position
     */
    emitSparks(position, count = 50, color = null) {
        const baseColor = color ? new THREE.Color(color) : null;

        for (let i = 0; i < count; i++) {
            const spark = this._getInactiveSpark();
            if (!spark) continue;

            // Golden angle distribution
            const goldenIndex = this.activeSparks.length + i;
            const spiralAngle = goldenIndex * GOLDEN_ANGLE;

            // Fibonacci radius
            const fibRadius = Math.sqrt(goldenIndex) * this.config.spiralTightness;

            spark.position.copy(position);

            // Velocity along spiral tangent
            const tangentAngle = spiralAngle + Math.PI / 2;
            const speed = this.config.sparkSpeed * (0.5 + Math.random() * 0.5);
            spark.velocity.set(
                Math.cos(tangentAngle) * speed,
                Math.sin(tangentAngle) * speed * 0.7 + Math.random() * speed * 0.5,
                (Math.random() - 0.5) * speed * 0.3
            );

            // Color
            if (baseColor) {
                spark.color.copy(baseColor);
                spark.color.offsetHSL((Math.random() - 0.5) * 0.1, 0, 0);
            } else {
                spark.color.copy(COLOR_ARRAY[Math.floor(Math.random() * COLOR_ARRAY.length)]);
            }

            spark.size = 8 + Math.random() * 12;
            spark.life = 0;
            spark.maxLife = this.config.sparkLifetime * (0.7 + Math.random() * 0.6);
            spark.spiralAngle = spiralAngle;
            spark.spiralRadius = fibRadius * 0.1;
            spark.importance = 0.5 + Math.random() * 0.5;
            spark.active = true;
            spark.trail = [];

            this.activeSparks.push(spark);
        }

        this._updateBuffers();
    }

    /**
     * Emit a spark with text label (for comments)
     */
    emitComment(position, text, color = 0xffff00) {
        const spark = this._getInactiveSpark();
        if (!spark) return;

        const goldenIndex = this.activeSparks.length;
        const spiralAngle = goldenIndex * GOLDEN_ANGLE;

        spark.position.copy(position);

        const tangentAngle = spiralAngle + Math.PI / 2;
        const speed = this.config.sparkSpeed * 0.7;
        spark.velocity.set(
            Math.cos(tangentAngle) * speed,
            Math.sin(tangentAngle) * speed * 0.5 + 0.5,
            (Math.random() - 0.5) * speed * 0.2
        );

        spark.color.set(color);
        spark.size = 15 + text.length * 0.5;
        spark.life = 0;
        spark.maxLife = this.config.sparkLifetime * 1.5;
        spark.spiralAngle = spiralAngle;
        spark.spiralRadius = 0.15;
        spark.importance = 1.0;
        spark.active = true;
        spark.text = text;
        spark.trail = [];

        this.activeSparks.push(spark);
        this._createTextLabel(spark, text);
        this._updateBuffers();
    }

    _createTextLabel(spark, text) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        const fontSize = 24;
        context.font = 'bold ' + fontSize + 'px Arial, sans-serif';
        const metrics = context.measureText(text);

        canvas.width = Math.min(metrics.width + 20, 512);
        canvas.height = fontSize + 16;

        context.font = 'bold ' + fontSize + 'px Arial, sans-serif';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.shadowColor = '#' + spark.color.getHexString();
        context.shadowBlur = 10;
        context.fillStyle = '#ffffff';
        context.fillText(text, canvas.width / 2, canvas.height / 2);

        const texture = new THREE.CanvasTexture(canvas);
        texture.needsUpdate = true;

        const spriteMaterial = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.scale.set(canvas.width / 50, canvas.height / 50, 1);
        sprite.position.copy(spark.position);

        this.scene.add(sprite);
        this.textLabels.set(spark, sprite);
    }

    /**
     * Update all particles - call every frame
     */
    update(deltaTime) {
        this.time += deltaTime;

        this.sparkMaterial.uniforms.uTime.value = this.time;
        this.sparkMaterial.uniforms.uIntensity.value = this.intensity;

        const stillActive = [];

        for (const spark of this.activeSparks) {
            spark.life += deltaTime;

            if (spark.life >= spark.maxLife) {
                spark.active = false;

                const label = this.textLabels.get(spark);
                if (label) {
                    this.scene.remove(label);
                    label.material.map.dispose();
                    label.material.dispose();
                    this.textLabels.delete(spark);
                }

                spark.reset();
            } else {
                stillActive.push(spark);

                const lifeRatio = spark.life / spark.maxLife;
                const spiralProgress = lifeRatio * Math.PI * 2;
                const theta = spark.spiralAngle + spiralProgress * 2.0;
                const radius = spark.spiralRadius * Math.exp(LOG_SPIRAL_GROWTH * spiralProgress * 10.0);

                const currentPos = new THREE.Vector3(
                    spark.position.x + Math.cos(theta) * radius + spark.velocity.x * lifeRatio * 3.0,
                    spark.position.y + Math.sin(theta) * radius * 0.5 + lifeRatio * spark.velocity.y * 2.0,
                    spark.position.z + Math.sin(theta * 0.5) * radius * 0.3 + spark.velocity.z * lifeRatio * 3.0
                );

                // Trail
                if (spark.trail.length < this.config.trailLength) {
                    const trailAlpha = (1.0 - lifeRatio) * spark.importance;
                    const trailSize = spark.size * 0.6 * (1.0 - lifeRatio);
                    spark.trail.push(new TrailPoint(currentPos, spark.color, trailAlpha, trailSize));
                }

                // Update text label
                const label = this.textLabels.get(spark);
                if (label) {
                    label.position.copy(currentPos);
                    label.position.y += 0.5;
                    label.material.opacity = 1.0 - lifeRatio * lifeRatio;
                }
            }
        }

        this.activeSparks = stillActive;
        this._updateTrails(deltaTime);
        this._updateBuffers();
    }

    _updateTrails(deltaTime) {
        this.trailData = [];

        for (const spark of this.activeSparks) {
            for (let i = spark.trail.length - 1; i >= 0; i--) {
                const trail = spark.trail[i];
                trail.life *= this.config.trailDecay;
                trail.alpha *= this.config.trailDecay;

                if (trail.alpha < 0.01) {
                    spark.trail.splice(i, 1);
                } else {
                    this.trailData.push(trail);
                }
            }
        }

        if (this.trailData.length > this.config.maxTrailPoints) {
            this.trailData = this.trailData.slice(-this.config.maxTrailPoints);
        }
    }

    _updateBuffers() {
        const positions = this.instancePositionAttr.array;
        const velocities = this.instanceVelocityAttr.array;
        const colors = this.instanceColorAttr.array;
        const sizes = this.instanceSizeAttr.array;
        const lives = this.instanceLifeAttr.array;
        const maxLives = this.instanceMaxLifeAttr.array;
        const spiralAngles = this.instanceSpiralAngleAttr.array;
        const spiralRadii = this.instanceSpiralRadiusAttr.array;

        for (let i = 0; i < this.activeSparks.length; i++) {
            const spark = this.activeSparks[i];
            const i3 = i * 3;
            const i4 = i * 4;

            positions[i3] = spark.position.x;
            positions[i3 + 1] = spark.position.y;
            positions[i3 + 2] = spark.position.z;

            velocities[i3] = spark.velocity.x;
            velocities[i3 + 1] = spark.velocity.y;
            velocities[i3 + 2] = spark.velocity.z;

            colors[i4] = spark.color.r;
            colors[i4 + 1] = spark.color.g;
            colors[i4 + 2] = spark.color.b;
            colors[i4 + 3] = 1.0;

            sizes[i] = spark.size * spark.importance;
            lives[i] = spark.life;
            maxLives[i] = spark.maxLife;
            spiralAngles[i] = spark.spiralAngle;
            spiralRadii[i] = spark.spiralRadius;
        }

        this.sparkGeometry.instanceCount = this.activeSparks.length;

        this.instancePositionAttr.needsUpdate = true;
        this.instanceVelocityAttr.needsUpdate = true;
        this.instanceColorAttr.needsUpdate = true;
        this.instanceSizeAttr.needsUpdate = true;
        this.instanceLifeAttr.needsUpdate = true;

        this._updateTrailBuffers();
    }

    _updateTrailBuffers() {
        const positions = this.trailPositionAttr.array;
        const colors = this.trailColorAttr.array;
        const count = Math.min(this.trailData.length, this.config.maxTrailPoints);

        for (let i = 0; i < count; i++) {
            const trail = this.trailData[i];
            const i3 = i * 3;
            const i4 = i * 4;

            positions[i3] = trail.position.x;
            positions[i3 + 1] = trail.position.y;
            positions[i3 + 2] = trail.position.z;

            colors[i4] = trail.color.r;
            colors[i4 + 1] = trail.color.g;
            colors[i4 + 2] = trail.color.b;
            colors[i4 + 3] = trail.alpha;
        }

        this.trailGeometry.setDrawRange(0, count);
        this.trailPositionAttr.needsUpdate = true;
        this.trailColorAttr.needsUpdate = true;
    }

    setIntensity(level) {
        this.intensity = Math.max(0, Math.min(1, level));
    }

    getParticleCount() {
        return this.activeSparks.length;
    }

    getTrailCount() {
        return this.trailData.length;
    }

    clear() {
        for (const spark of this.activeSparks) {
            const label = this.textLabels.get(spark);
            if (label) {
                this.scene.remove(label);
                label.material.map.dispose();
                label.material.dispose();
            }
            spark.reset();
        }
        this.activeSparks = [];
        this.trailData = [];
        this.textLabels.clear();
        this._updateBuffers();
    }

    dispose() {
        this.clear();
        this.scene.remove(this.sparkPoints);
        this.scene.remove(this.trailPointsMesh);
        this.sparkGeometry.dispose();
        this.trailGeometry.dispose();
        this.sparkMaterial.dispose();
        this.trailMaterial.dispose();
        this.sparks = [];
        this.activeSparks = [];
        this.trailData = [];
        console.log('[SparkSystem] Disposed');
    }
}

export { SparkSystem, COLORS as SparkColors };
export const GOLDEN_ANGLE_DEGREES = 137.5077640500378;
export default SparkSystem;
