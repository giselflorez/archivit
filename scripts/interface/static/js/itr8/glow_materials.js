/**
 * IT-R8 GLOW & NEON MATERIAL SYSTEM
 * =================================
 * Extreme neon glow effects for the social timeline
 * Light beams, volumetric fog, electricity pulses, HDR bloom
 */

// Color palette - bright social on dark void
const ITR8_COLORS = {
    VOID: new THREE.Color(0x050508),
    CORE_CYAN: new THREE.Color(0x00f5ff),
    SECONDARY_MAGENTA: new THREE.Color(0xff00ff),
    TERTIARY_GOLD: new THREE.Color(0xffaa00),

    // Living beings (warm)
    LIVING_PINK: new THREE.Color(0xff6b9d),
    LIVING_GOLD: new THREE.Color(0xffaa00),
    LIVING_CORAL: new THREE.Color(0xff7744),

    // Legacy/Art (cool)
    LEGACY_CYAN: new THREE.Color(0x00f5ff),
    LEGACY_VIOLET: new THREE.Color(0xa855f7),
    LEGACY_SILVER: new THREE.Color(0xc0c0c0),

    // Sparks
    HOT_PINK: new THREE.Color(0xff1493),
    ELECTRIC_YELLOW: new THREE.Color(0xffff00),
    BRIGHT_CYAN: new THREE.Color(0x00ffff)
};

/**
 * Create glowing cable material for the spiral backbone
 */
function createCableMaterial(colors = {}) {
    const uniforms = {
        uTime: { value: 0 },
        uIntensity: { value: 1.0 },
        uPulseSpeed: { value: 0.5 },
        uPulseWidth: { value: 0.15 },
        uBloomPower: { value: 2.5 },
        uColorCore: { value: colors.core || ITR8_COLORS.CORE_CYAN },
        uColorSecondary: { value: colors.secondary || ITR8_COLORS.SECONDARY_MAGENTA },
        uColorTertiary: { value: colors.tertiary || ITR8_COLORS.TERTIARY_GOLD },
        uFogDensity: { value: 0.02 },
        uFogStart: { value: 0 },
        uFogEnd: { value: 100 }
    };

    const vertexShader = `
        precision highp float;

        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vWorldPosition;
        varying vec2 vUv;
        varying float vArcProgress;
        varying float vPulseIntensity;
        varying float vFresnel;

        uniform float uTime;
        uniform float uPulseSpeed;
        uniform float uPulseWidth;

        attribute float arcProgress;

        void main() {
            vUv = uv;
            vArcProgress = arcProgress;
            vNormal = normalize(normalMatrix * normal);

            // Calculate pulse intensity
            float pulsePhase = uTime * uPulseSpeed;
            float pulsePattern = 0.0;

            for (float i = 0.0; i < 5.0; i++) {
                float offset = i / 5.0;
                float pulse = fract(pulsePhase * (0.5 + offset * 0.5) + offset);
                float dist = abs(arcProgress - pulse);
                dist = min(dist, 1.0 - dist);
                pulsePattern += smoothstep(uPulseWidth, 0.0, dist) * (1.0 - i * 0.15);
            }
            vPulseIntensity = clamp(pulsePattern, 0.0, 1.0);

            // Wiggle animation
            vec3 displaced = position;
            float wiggle = sin(arcProgress * 20.0 + uTime * 2.0) * 0.02;
            displaced += normal * wiggle * (0.5 + vPulseIntensity * 0.5);

            vec4 worldPos = modelMatrix * vec4(displaced, 1.0);
            vWorldPosition = worldPos.xyz;

            vec4 mvPosition = viewMatrix * worldPos;
            vPosition = mvPosition.xyz;

            // Fresnel
            vec3 worldNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);
            vec3 viewDir = normalize(cameraPosition - worldPos.xyz);
            vFresnel = pow(1.0 - max(dot(worldNormal, viewDir), 0.0), 2.5);

            gl_Position = projectionMatrix * mvPosition;
        }
    `;

    const fragmentShader = `
        precision highp float;

        uniform float uTime;
        uniform float uIntensity;
        uniform float uBloomPower;
        uniform vec3 uColorCore;
        uniform vec3 uColorSecondary;
        uniform vec3 uColorTertiary;
        uniform float uFogDensity;

        varying vec3 vNormal;
        varying vec3 vPosition;
        varying vec3 vWorldPosition;
        varying vec2 vUv;
        varying float vArcProgress;
        varying float vPulseIntensity;
        varying float vFresnel;

        // Simplex noise for electricity
        vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
        vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

        float snoise(vec3 v) {
            const vec2 C = vec2(1.0/6.0, 1.0/3.0);
            const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
            vec3 i = floor(v + dot(v, C.yyy));
            vec3 x0 = v - i + dot(i, C.xxx);
            vec3 g = step(x0.yzx, x0.xyz);
            vec3 l = 1.0 - g;
            vec3 i1 = min(g.xyz, l.zxy);
            vec3 i2 = max(g.xyz, l.zxy);
            vec3 x1 = x0 - i1 + C.xxx;
            vec3 x2 = x0 - i2 + C.yyy;
            vec3 x3 = x0 - D.yyy;
            i = mod289(i);
            vec4 p = permute(permute(permute(
                i.z + vec4(0.0, i1.z, i2.z, 1.0))
                + i.y + vec4(0.0, i1.y, i2.y, 1.0))
                + i.x + vec4(0.0, i1.x, i2.x, 1.0));
            float n_ = 0.142857142857;
            vec3 ns = n_ * D.wyz - D.xzx;
            vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
            vec4 x_ = floor(j * ns.z);
            vec4 y_ = floor(j - 7.0 * x_);
            vec4 x = x_ * ns.x + ns.yyyy;
            vec4 y = y_ * ns.x + ns.yyyy;
            vec4 h = 1.0 - abs(x) - abs(y);
            vec4 b0 = vec4(x.xy, y.xy);
            vec4 b1 = vec4(x.zw, y.zw);
            vec4 s0 = floor(b0) * 2.0 + 1.0;
            vec4 s1 = floor(b1) * 2.0 + 1.0;
            vec4 sh = -step(h, vec4(0.0));
            vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
            vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
            vec3 p0 = vec3(a0.xy, h.x);
            vec3 p1 = vec3(a0.zw, h.y);
            vec3 p2 = vec3(a1.xy, h.z);
            vec3 p3 = vec3(a1.zw, h.w);
            vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
            p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
            vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
            m = m * m;
            return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
        }

        vec3 getGradientColor(float t, float pulse) {
            float cycleT = fract(t + uTime * 0.1);
            vec3 color;
            if (cycleT < 0.33) {
                color = mix(uColorCore, uColorSecondary, cycleT * 3.0);
            } else if (cycleT < 0.66) {
                color = mix(uColorSecondary, uColorTertiary, (cycleT - 0.33) * 3.0);
            } else {
                color = mix(uColorTertiary, uColorCore, (cycleT - 0.66) * 3.0);
            }
            color = mix(color, vec3(1.0), pulse * 0.6);
            return color;
        }

        float getElectricity(float progress, float time) {
            float freq1 = snoise(vec3(progress * 100.0, time * 10.0, 0.0));
            float freq2 = snoise(vec3(progress * 200.0, time * 20.0, 1.0));
            float freq3 = snoise(vec3(progress * 400.0, time * 40.0, 2.0));
            float electricity = freq1 * 0.5 + freq2 * 0.3 + freq3 * 0.2;
            return pow(max(electricity, 0.0), 2.0);
        }

        vec3 applyBloom(vec3 color, float intensity) {
            float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
            float bloomAmount = max(luminance - 0.8, 0.0) * uBloomPower;
            vec3 bloom = color * bloomAmount;
            vec3 result = color + bloom;
            result = result / (1.0 + result); // Tone mapping
            return result * intensity;
        }

        void main() {
            vec3 baseColor = getGradientColor(vArcProgress, vPulseIntensity);
            float electricity = getElectricity(vArcProgress, uTime);

            float coreIntensity = 1.0 + vPulseIntensity * 2.0 + electricity * 1.5;
            vec3 coreGlow = baseColor * coreIntensity;

            // Fresnel rim
            vec3 rimColor = mix(uColorCore, uColorSecondary, sin(uTime * 2.0) * 0.5 + 0.5);
            vec3 rimGlow = rimColor * vFresnel * 3.0;

            vec3 totalGlow = coreGlow + rimGlow;

            // Outer glow
            float outerGlow = smoothstep(0.0, 1.0, vFresnel) * 0.5;
            totalGlow += baseColor * outerGlow;

            // Bloom
            totalGlow = applyBloom(totalGlow, uIntensity);

            // Fog scattering
            float depth = length(vPosition);
            float fogFactor = 1.0 - exp(-pow(depth * uFogDensity, 2.0));
            vec3 fogColor = mix(uColorCore, uColorSecondary, 0.3) * 0.1;
            totalGlow = mix(totalGlow, fogColor, fogFactor * 0.3);

            float alpha = 0.9 + vPulseIntensity * 0.1;
            alpha = clamp(alpha + vFresnel * 0.3, 0.0, 1.0);

            gl_FragColor = vec4(totalGlow, alpha);
        }
    `;

    return new THREE.ShaderMaterial({
        uniforms,
        vertexShader,
        fragmentShader,
        transparent: true,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
        depthWrite: false
    });
}

/**
 * Create glowing halo material for photo nodes
 */
function createNodeGlowMaterial(color = ITR8_COLORS.LIVING_PINK, intensity = 1.0) {
    const uniforms = {
        uTime: { value: 0 },
        uIntensity: { value: intensity },
        uColor: { value: color },
        uScale: { value: 1.0 },
        uRingCount: { value: 4.0 },
        uRingSpeed: { value: 0.5 }
    };

    const vertexShader = `
        varying vec2 vUv;
        varying float vFresnel;

        uniform float uTime;
        uniform float uScale;

        void main() {
            vUv = uv;

            float pulse = 1.0 + sin(uTime * 3.0) * 0.05;
            vec3 scaled = position * uScale * pulse;

            vec4 worldPos = modelMatrix * vec4(scaled, 1.0);
            vec4 mvPosition = viewMatrix * worldPos;

            vec3 worldNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);
            vec3 viewDir = normalize(cameraPosition - worldPos.xyz);
            vFresnel = pow(1.0 - max(dot(worldNormal, viewDir), 0.0), 3.0);

            gl_Position = projectionMatrix * mvPosition;
        }
    `;

    const fragmentShader = `
        uniform float uTime;
        uniform float uIntensity;
        uniform vec3 uColor;
        uniform float uRingCount;
        uniform float uRingSpeed;

        varying vec2 vUv;
        varying float vFresnel;

        void main() {
            vec2 centered = vUv - 0.5;
            float dist = length(centered);

            // Animated rings
            float rings = 0.0;
            for (float i = 0.0; i < 4.0; i++) {
                float ringDist = fract(dist * uRingCount - uTime * uRingSpeed * (1.0 + i * 0.2) + i * 0.25);
                float ring = smoothstep(0.0, 0.1, ringDist) * smoothstep(0.3, 0.1, ringDist);
                rings += ring * (1.0 - i * 0.2);
            }

            // White-hot core
            float core = 1.0 - smoothstep(0.0, 0.5, dist);
            core = pow(core, 2.0);

            float intensity = (core + rings * 0.5 + vFresnel * 2.0) * uIntensity;
            vec3 color = mix(uColor, vec3(1.0), core * 0.7);
            color *= intensity;

            float alpha = smoothstep(0.6, 0.0, dist);
            alpha = max(alpha, vFresnel * 0.5);

            gl_FragColor = vec4(color, alpha * 0.9);
        }
    `;

    return new THREE.ShaderMaterial({
        uniforms,
        vertexShader,
        fragmentShader,
        transparent: true,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
        depthWrite: false
    });
}

/**
 * Create spark particle material
 */
function createSparkMaterial(color = ITR8_COLORS.HOT_PINK) {
    return new THREE.ShaderMaterial({
        uniforms: {
            uColor: { value: color },
            uTime: { value: 0 },
            uPixelRatio: { value: window.devicePixelRatio }
        },
        vertexShader: `
            attribute float size;
            attribute float life;

            uniform float uTime;
            uniform float uPixelRatio;

            varying float vLife;

            void main() {
                vLife = life;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                float sizeAttenuation = 300.0 / length(mvPosition.xyz);
                gl_PointSize = size * sizeAttenuation * uPixelRatio;
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform vec3 uColor;
            uniform float uTime;

            varying float vLife;

            void main() {
                vec2 center = gl_PointCoord - 0.5;
                float dist = length(center);
                if (dist > 0.5) discard;

                float glow = 1.0 - smoothstep(0.0, 0.5, dist);
                glow = pow(glow, 1.5);

                float flicker = 0.7 + 0.3 * sin(vLife * 50.0 + uTime * 20.0);
                float lifeFade = 1.0 - vLife;

                vec3 color = uColor * glow * flicker * lifeFade * 3.0;
                float alpha = glow * lifeFade;

                gl_FragColor = vec4(color, alpha);
            }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });
}

/**
 * Create volumetric fog material
 */
function createFogMaterial() {
    return new THREE.ShaderMaterial({
        uniforms: {
            uTime: { value: 0 },
            uDensity: { value: 0.5 },
            uColorPrimary: { value: ITR8_COLORS.CORE_CYAN },
            uColorSecondary: { value: ITR8_COLORS.SECONDARY_MAGENTA },
            uNoiseScale: { value: 2.0 },
            uFlowSpeed: { value: 0.2 }
        },
        vertexShader: `
            varying vec2 vUv;
            varying float vDepth;

            void main() {
                vUv = uv;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                vDepth = -mvPosition.z;
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform float uTime;
            uniform float uDensity;
            uniform vec3 uColorPrimary;
            uniform vec3 uColorSecondary;
            uniform float uNoiseScale;
            uniform float uFlowSpeed;

            varying vec2 vUv;
            varying float vDepth;

            float random(vec2 st) {
                return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
            }

            float noise(vec2 st) {
                vec2 i = floor(st);
                vec2 f = fract(st);
                float a = random(i);
                float b = random(i + vec2(1.0, 0.0));
                float c = random(i + vec2(0.0, 1.0));
                float d = random(i + vec2(1.0, 1.0));
                vec2 u = f * f * (3.0 - 2.0 * f);
                return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
            }

            float fbm(vec2 st) {
                float value = 0.0;
                float amplitude = 0.5;
                for (int i = 0; i < 5; i++) {
                    value += amplitude * noise(st);
                    st *= 2.0;
                    amplitude *= 0.5;
                }
                return value;
            }

            void main() {
                vec2 flowUv = vUv * uNoiseScale;
                flowUv.x += uTime * uFlowSpeed * 0.3;
                flowUv.y += sin(uTime * 0.5) * 0.1;

                float fog = fbm(flowUv);
                fog = fog * 0.5 + 0.5;

                float depthFade = 1.0 - exp(-vDepth * uDensity * 0.01);
                fog *= depthFade;

                float colorMix = sin(fog * 3.14159 + uTime * 0.5) * 0.5 + 0.5;
                vec3 fogColor = mix(uColorPrimary, uColorSecondary, colorMix);

                float alpha = fog * 0.15 * uDensity;

                gl_FragColor = vec4(fogColor * fog, alpha);
            }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide
    });
}

/**
 * Create selection aura material
 */
function createAuraMaterial(color = ITR8_COLORS.CORE_CYAN) {
    return new THREE.ShaderMaterial({
        uniforms: {
            uTime: { value: 0 },
            uIntensity: { value: 1.0 },
            uColor: { value: color },
            uExpand: { value: 0.1 },
            uPulseSpeed: { value: 2.0 }
        },
        vertexShader: `
            uniform float uTime;
            uniform float uExpand;

            varying float vFresnel;

            void main() {
                float breathe = 1.0 + sin(uTime * 2.0) * 0.1;
                vec3 expanded = position + normal * uExpand * breathe;

                vec4 worldPos = modelMatrix * vec4(expanded, 1.0);
                vec4 mvPosition = viewMatrix * worldPos;

                vec3 worldNormal = normalize((modelMatrix * vec4(normal, 0.0)).xyz);
                vec3 viewDir = normalize(cameraPosition - worldPos.xyz);
                vFresnel = pow(1.0 - max(dot(worldNormal, viewDir), 0.0), 2.0);

                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform float uTime;
            uniform float uIntensity;
            uniform vec3 uColor;
            uniform float uPulseSpeed;

            varying float vFresnel;

            void main() {
                float aura = 0.0;
                for (float i = 0.0; i < 3.0; i++) {
                    float phase = uTime * uPulseSpeed * (1.0 + i * 0.3);
                    float layer = sin(phase + i * 1.047) * 0.5 + 0.5;
                    aura += layer * (1.0 - i * 0.25);
                }
                aura /= 2.0;

                float edgeGlow = vFresnel * 2.0;
                float totalIntensity = (aura + edgeGlow) * uIntensity;

                vec3 color = uColor * totalIntensity;
                color = mix(color, vec3(1.0), edgeGlow * 0.3);

                float alpha = vFresnel * 0.8 * aura;

                gl_FragColor = vec4(color, alpha);
            }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.BackSide
    });
}

/**
 * Material presets for quick access
 */
const MaterialPresets = {
    livingNode: () => createNodeGlowMaterial(ITR8_COLORS.LIVING_PINK, 1.0),
    legacyNode: () => createNodeGlowMaterial(ITR8_COLORS.LEGACY_CYAN, 0.8),
    mainCable: () => createCableMaterial(),
    selectionAura: () => createAuraMaterial(ITR8_COLORS.ELECTRIC_YELLOW),
    ambientFog: () => createFogMaterial()
};

/**
 * Material update manager - call in animation loop
 */
class MaterialUpdateManager {
    constructor() {
        this.materials = new Set();
        this.time = 0;
    }

    register(material) {
        this.materials.add(material);
    }

    unregister(material) {
        this.materials.delete(material);
    }

    update(deltaTime) {
        this.time += deltaTime;

        for (const material of this.materials) {
            if (material.uniforms && material.uniforms.uTime) {
                material.uniforms.uTime.value = this.time;
            }
        }
    }

    dispose() {
        this.materials.clear();
    }
}

// Singleton instance
const materialManager = new MaterialUpdateManager();

export {
    ITR8_COLORS,
    createCableMaterial,
    createNodeGlowMaterial,
    createSparkMaterial,
    createFogMaterial,
    createAuraMaterial,
    MaterialPresets,
    MaterialUpdateManager,
    materialManager
};

export default {
    colors: ITR8_COLORS,
    cable: createCableMaterial,
    nodeGlow: createNodeGlowMaterial,
    spark: createSparkMaterial,
    fog: createFogMaterial,
    aura: createAuraMaterial,
    presets: MaterialPresets,
    manager: materialManager
};
