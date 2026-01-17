/**
 * ARC-8 PROGRESSIVE ENHANCEMENT ENGINE
 * ====================================
 * Fibonacci-weighted device detection with Golden Ratio thresholds
 * Aligned with 22 Masters architecture
 *
 * CAPABILITY LEVELS (Golden Ratio Thresholds):
 * - FULL:    φ > 0.618 - WebGL 3D with all effects
 * - MEDIUM:  φ > 0.382 - Canvas 2D with reduced particles
 * - LITE:    φ > 0.236 - Static SVG with CSS animations
 * - MINIMAL: below 0.236 - Text + Images only
 *
 * Created: 2026-01-16
 */

const ARC8_DEVICE_DETECTION = (function() {
    'use strict';

    // Sacred constants
    const PHI = 1.618033988749895;
    const GOLDEN_RATIO_INVERSE = 1 / PHI; // 0.618
    const FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144];

    // Capability thresholds (Golden Ratio derived)
    const THRESHOLDS = {
        FULL: 0.618,     // φ inverse - high capability
        MEDIUM: 0.382,   // φ² inverse - medium capability
        LITE: 0.236,     // φ³ inverse - low capability
        MINIMAL: 0       // below all thresholds
    };

    // Fibonacci weights for scoring (normalized)
    const WEIGHTS = {
        gpu: 21,          // Most important for 3D
        memory: 13,       // RAM availability
        cores: 8,         // CPU cores
        connection: 5,    // Network speed
        screen: 3,        // Screen resolution
        battery: 2,       // Battery status
        touch: 1          // Touch capability
    };

    const TOTAL_WEIGHT = Object.values(WEIGHTS).reduce((a, b) => a + b, 0);

    /**
     * Detect WebGL capability and performance tier
     */
    function detectGPU() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

            if (!gl) return { score: 0, tier: 'none', details: 'No WebGL' };

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            let renderer = 'Unknown';
            let vendor = 'Unknown';

            if (debugInfo) {
                renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            }

            // Check for integrated vs discrete GPU
            const isIntegrated = /intel|integrated|mesa|swiftshader/i.test(renderer);
            const isHighEnd = /nvidia|radeon|rx|rtx|gtx|quadro|firepro/i.test(renderer);
            const isMobile = /adreno|mali|powervr|apple gpu|m1|m2|m3/i.test(renderer);

            // Score GPU capability
            let gpuScore = 0.5; // Default medium

            if (isHighEnd) {
                gpuScore = 1.0;
            } else if (isMobile && /m[123]/i.test(renderer)) {
                gpuScore = 0.9; // Apple Silicon is excellent
            } else if (isMobile) {
                gpuScore = 0.6;
            } else if (isIntegrated) {
                gpuScore = 0.4;
            }

            // Check WebGL2 support
            const hasWebGL2 = !!canvas.getContext('webgl2');
            if (hasWebGL2) gpuScore += 0.1;

            // Check max texture size (indicator of GPU power)
            const maxTexture = gl.getParameter(gl.MAX_TEXTURE_SIZE);
            if (maxTexture >= 16384) gpuScore += 0.1;
            else if (maxTexture >= 8192) gpuScore += 0.05;

            // Check extensions
            const extensions = gl.getSupportedExtensions() || [];
            const goodExtensions = ['OES_texture_float', 'WEBGL_draw_buffers', 'EXT_frag_depth'];
            const extScore = goodExtensions.filter(e => extensions.includes(e)).length / goodExtensions.length;
            gpuScore += extScore * 0.1;

            return {
                score: Math.min(1, gpuScore),
                tier: gpuScore > 0.7 ? 'high' : gpuScore > 0.4 ? 'medium' : 'low',
                details: `${vendor} - ${renderer}`,
                webgl2: hasWebGL2,
                maxTexture
            };
        } catch (e) {
            return { score: 0, tier: 'none', details: e.message };
        }
    }

    /**
     * Detect memory availability
     */
    function detectMemory() {
        const nav = navigator;

        // Device memory API (GB)
        if (nav.deviceMemory) {
            const gb = nav.deviceMemory;
            if (gb >= 8) return { score: 1.0, gb, details: `${gb}GB RAM` };
            if (gb >= 4) return { score: 0.7, gb, details: `${gb}GB RAM` };
            if (gb >= 2) return { score: 0.4, gb, details: `${gb}GB RAM` };
            return { score: 0.2, gb, details: `${gb}GB RAM` };
        }

        // Fallback: estimate from hardware concurrency
        const cores = nav.hardwareConcurrency || 2;
        const estimatedGB = Math.max(2, cores); // Rough estimate
        return {
            score: Math.min(1, estimatedGB / 8),
            gb: estimatedGB,
            details: `~${estimatedGB}GB (estimated)`
        };
    }

    /**
     * Detect CPU cores
     */
    function detectCores() {
        const cores = navigator.hardwareConcurrency || 2;
        let score = 0.3;

        if (cores >= 8) score = 1.0;
        else if (cores >= 6) score = 0.8;
        else if (cores >= 4) score = 0.6;
        else if (cores >= 2) score = 0.4;

        return { score, cores, details: `${cores} cores` };
    }

    /**
     * Detect connection quality
     */
    function detectConnection() {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

        if (!conn) {
            return { score: 0.5, type: 'unknown', details: 'Connection API unavailable' };
        }

        const effectiveType = conn.effectiveType || '4g';
        const downlink = conn.downlink || 10;
        const rtt = conn.rtt || 100;

        let score = 0.5;

        // Effective type scoring
        if (effectiveType === '4g') score = 0.8;
        else if (effectiveType === '3g') score = 0.5;
        else if (effectiveType === '2g') score = 0.2;
        else if (effectiveType === 'slow-2g') score = 0.1;

        // Adjust by downlink
        if (downlink >= 10) score = Math.min(1, score + 0.2);
        else if (downlink < 1.5) score = Math.max(0.1, score - 0.2);

        // Adjust by RTT
        if (rtt < 50) score = Math.min(1, score + 0.1);
        else if (rtt > 300) score = Math.max(0.1, score - 0.1);

        return {
            score,
            type: effectiveType,
            downlink,
            rtt,
            details: `${effectiveType} - ${downlink}Mbps`
        };
    }

    /**
     * Detect screen capability
     */
    function detectScreen() {
        const width = window.screen.width * (window.devicePixelRatio || 1);
        const height = window.screen.height * (window.devicePixelRatio || 1);
        const pixels = width * height;

        let score = 0.5;

        // 4K+ = high, 1080p = medium, below = low
        if (pixels >= 8294400) score = 1.0;      // 4K
        else if (pixels >= 2073600) score = 0.7; // 1080p
        else if (pixels >= 921600) score = 0.5;  // 720p
        else score = 0.3;

        return {
            score,
            width,
            height,
            dpr: window.devicePixelRatio || 1,
            details: `${Math.round(width)}x${Math.round(height)} @${window.devicePixelRatio || 1}x`
        };
    }

    /**
     * Detect battery status
     */
    async function detectBattery() {
        try {
            if (!navigator.getBattery) {
                return { score: 1.0, level: 1, charging: true, details: 'Battery API unavailable' };
            }

            const battery = await navigator.getBattery();
            const level = battery.level;
            const charging = battery.charging;

            let score = level;

            // Boost score if charging
            if (charging) score = Math.min(1, score + 0.3);

            // Penalize low battery
            if (level < 0.2 && !charging) score *= 0.5;

            return {
                score,
                level,
                charging,
                details: `${Math.round(level * 100)}%${charging ? ' (charging)' : ''}`
            };
        } catch (e) {
            return { score: 0.8, level: 0.8, charging: false, details: 'Battery check failed' };
        }
    }

    /**
     * Detect touch capability
     */
    function detectTouch() {
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const isCoarse = window.matchMedia('(pointer: coarse)').matches;

        // Touch devices often have less GPU power (mobile)
        // But this isn't always true (tablets, touch laptops)
        const score = hasTouch && isCoarse ? 0.6 : 1.0;

        return {
            score,
            hasTouch,
            isCoarse,
            details: hasTouch ? 'Touch device' : 'Non-touch'
        };
    }

    /**
     * Calculate overall capability using Fibonacci-weighted scoring
     */
    async function calculateCapability() {
        const gpu = detectGPU();
        const memory = detectMemory();
        const cores = detectCores();
        const connection = detectConnection();
        const screen = detectScreen();
        const battery = await detectBattery();
        const touch = detectTouch();

        // Fibonacci-weighted sum
        const weightedSum =
            gpu.score * WEIGHTS.gpu +
            memory.score * WEIGHTS.memory +
            cores.score * WEIGHTS.cores +
            connection.score * WEIGHTS.connection +
            screen.score * WEIGHTS.screen +
            battery.score * WEIGHTS.battery +
            touch.score * WEIGHTS.touch;

        const normalizedScore = weightedSum / TOTAL_WEIGHT;

        // Determine capability level using Golden Ratio thresholds
        let level, mode, particleLimit, effectsEnabled;

        if (normalizedScore >= THRESHOLDS.FULL) {
            level = 'FULL';
            mode = 'webgl-3d';
            particleLimit = 10000;
            effectsEnabled = ['halos', 'sparks', 'glow', 'connections', 'particles'];
        } else if (normalizedScore >= THRESHOLDS.MEDIUM) {
            level = 'MEDIUM';
            mode = 'canvas-2d';
            particleLimit = 2000;
            effectsEnabled = ['connections', 'glow'];
        } else if (normalizedScore >= THRESHOLDS.LITE) {
            level = 'LITE';
            mode = 'svg-static';
            particleLimit = 100;
            effectsEnabled = ['static'];
        } else {
            level = 'MINIMAL';
            mode = 'text-only';
            particleLimit = 0;
            effectsEnabled = [];
        }

        return {
            score: normalizedScore,
            level,
            mode,
            particleLimit,
            effectsEnabled,
            thresholds: THRESHOLDS,
            details: {
                gpu,
                memory,
                cores,
                connection,
                screen,
                battery,
                touch
            },
            timestamp: Date.now(),
            userAgent: navigator.userAgent
        };
    }

    /**
     * Get rendering configuration based on capability
     */
    function getRenderConfig(capability) {
        const configs = {
            FULL: {
                renderer: 'webgl',
                antialiasing: true,
                shadows: true,
                particles: {
                    spectral: 2500,
                    flow: 1000,
                    timeStreams: 8
                },
                masters: {
                    sphereSegments: 48,
                    haloRings: 5,
                    sparkCount: 40
                },
                effects: {
                    fog: true,
                    bloom: true,
                    motionBlur: false
                },
                pixelRatio: Math.min(window.devicePixelRatio, 2)
            },
            MEDIUM: {
                renderer: 'webgl',
                antialiasing: true,
                shadows: false,
                particles: {
                    spectral: 800,
                    flow: 300,
                    timeStreams: 4
                },
                masters: {
                    sphereSegments: 24,
                    haloRings: 2,
                    sparkCount: 10
                },
                effects: {
                    fog: true,
                    bloom: false,
                    motionBlur: false
                },
                pixelRatio: 1
            },
            LITE: {
                renderer: 'canvas2d',
                antialiasing: false,
                shadows: false,
                particles: {
                    spectral: 100,
                    flow: 0,
                    timeStreams: 0
                },
                masters: {
                    circleMode: true,
                    haloRings: 1,
                    sparkCount: 0
                },
                effects: {
                    fog: false,
                    bloom: false,
                    motionBlur: false
                },
                pixelRatio: 1
            },
            MINIMAL: {
                renderer: 'static',
                antialiasing: false,
                shadows: false,
                particles: {
                    spectral: 0,
                    flow: 0,
                    timeStreams: 0
                },
                masters: {
                    staticMode: true,
                    haloRings: 0,
                    sparkCount: 0
                },
                effects: {
                    fog: false,
                    bloom: false,
                    motionBlur: false
                },
                pixelRatio: 1
            }
        };

        return configs[capability.level] || configs.LITE;
    }

    /**
     * Display capability indicator (optional UI element)
     */
    function createCapabilityIndicator(capability) {
        const indicator = document.createElement('div');
        indicator.id = 'arc8-capability-indicator';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(3, 3, 8, 0.9);
            border: 1px solid rgba(90, 168, 185, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            font-family: -apple-system, sans-serif;
            font-size: 11px;
            color: #f0ece7;
            z-index: 9999;
            backdrop-filter: blur(10px);
        `;

        const levelColors = {
            FULL: '#54a876',
            MEDIUM: '#b9a85a',
            LITE: '#ba6587',
            MINIMAL: '#5a5854'
        };

        indicator.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: ${levelColors[capability.level]};
                    box-shadow: 0 0 10px ${levelColors[capability.level]};
                "></div>
                <div>
                    <div style="font-weight: 500; letter-spacing: 0.1em;">${capability.level} MODE</div>
                    <div style="color: #9a9690; font-size: 10px; margin-top: 2px;">
                        Score: ${(capability.score * 100).toFixed(0)}% (φ threshold: ${(THRESHOLDS[capability.level] * 100).toFixed(0)}%)
                    </div>
                </div>
            </div>
        `;

        return indicator;
    }

    /**
     * Save capability to localStorage for quick subsequent loads
     */
    function cacheCapability(capability) {
        try {
            localStorage.setItem('arc8_device_capability', JSON.stringify({
                ...capability,
                cached: true,
                cachedAt: Date.now()
            }));
        } catch (e) {
            console.warn('Could not cache device capability:', e);
        }
    }

    /**
     * Get cached capability if recent (< 1 hour)
     */
    function getCachedCapability() {
        try {
            const cached = localStorage.getItem('arc8_device_capability');
            if (!cached) return null;

            const data = JSON.parse(cached);
            const age = Date.now() - data.cachedAt;
            const maxAge = 60 * 60 * 1000; // 1 hour

            if (age < maxAge) {
                return data;
            }
        } catch (e) {
            // Ignore cache errors
        }
        return null;
    }

    /**
     * Main detection function
     */
    async function detect(options = {}) {
        const { useCache = true, showIndicator = false } = options;

        // Check cache first
        if (useCache) {
            const cached = getCachedCapability();
            if (cached) {
                console.log('[ARC-8] Using cached device capability:', cached.level);
                if (showIndicator) {
                    document.body.appendChild(createCapabilityIndicator(cached));
                }
                return cached;
            }
        }

        // Run fresh detection
        console.log('[ARC-8] Detecting device capability...');
        const capability = await calculateCapability();

        // Cache result
        cacheCapability(capability);

        // Log details
        console.log('[ARC-8] Device Capability:', {
            level: capability.level,
            score: (capability.score * 100).toFixed(1) + '%',
            mode: capability.mode,
            gpu: capability.details.gpu.details
        });

        // Show indicator if requested
        if (showIndicator) {
            document.body.appendChild(createCapabilityIndicator(capability));
        }

        return capability;
    }

    // Public API
    return {
        detect,
        getRenderConfig,
        THRESHOLDS,
        WEIGHTS,
        createCapabilityIndicator
    };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ARC8_DEVICE_DETECTION;
}

// Auto-detect on load if requested via data attribute
document.addEventListener('DOMContentLoaded', () => {
    const script = document.querySelector('script[data-arc8-autodetect]');
    if (script) {
        const showIndicator = script.dataset.showIndicator === 'true';
        ARC8_DEVICE_DETECTION.detect({ showIndicator }).then(capability => {
            // Dispatch custom event with capability
            window.dispatchEvent(new CustomEvent('arc8-capability-detected', {
                detail: capability
            }));
        });
    }
});
