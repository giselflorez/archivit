# IT-R8 TECHNICAL SPECIFICATION
## Advanced GLB Rendering Pipeline with IPFS Integration

**Created:** January 10, 2026
**Status:** Architecture Specification
**Connection:** Brown University VR Research (2001-2004) → Spatial Computing 2026

---

## CORE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           IT-R8 PIPELINE                                 │
└─────────────────────────────────────────────────────────────────────────┘

     ARCHIV-IT                    IT-R8                      OUTPUT
     ─────────                    ─────                      ──────

  ┌─────────────┐          ┌─────────────────┐         ┌─────────────────┐
  │   BUBBLES   │          │  TRAINING DATA  │         │   GLB RENDER    │
  │  (selected  │    →     │   PROCESSOR     │    →    │   (3D depth)    │
  │   groups)   │          │                 │         │                 │
  └─────────────┘          └─────────────────┘         └─────────────────┘
                                   │
                                   ▼
                           ┌─────────────────┐
                           │  IPFS PIPELINE  │
                           │  + RESIZE LAYER │
                           └─────────────────┘
```

---

## IPFS-DIRECT PIPELINE

### No Centralized Server

```
TRADITIONAL (Centralized)           IT-R8 (Decentralized)
─────────────────────────           ─────────────────────

User Request                        User Request
     │                                   │
     ▼                                   ▼
┌──────────┐                        ┌──────────┐
│  SERVER  │                        │   IPFS   │
│ (single  │                        │ GATEWAY  │
│  point)  │                        │ (multi)  │
└──────────┘                        └──────────┘
     │                                   │
     ▼                                   ▼
   Asset                            Asset (from nearest node)


ADVANTAGES:
• No single point of failure
• Assets persist independently
• Censorship resistant
• User owns their data pipeline
```

### IPFS Gateway Failover

```
PRIMARY          SECONDARY        TERTIARY         FALLBACK
───────          ─────────        ────────         ────────

ipfs.io     →    dweb.link   →   gateway.pinata  →  localhost:8080
    │                │                │                  │
    └────────────────┴────────────────┴──────────────────┘
                              │
                    Automatic failover
                    if gateway unavailable
```

---

## RESIZE CONSTRAINT LAYER

### The Problem

```
FULL QUALITY (IPFS)                    DISPLAY NEED
───────────────────                    ────────────

8000 x 8000 px                         Variable viewport
50+ MB                                 Fast loading needed
     │                                      │
     └──────── GAP ─────────────────────────┘

     Slow load times kill UX
     But downsampling loses quality
```

### The Solution: Intermediate Resize Constraint

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESIZE CONSTRAINT LAYER                               │
└─────────────────────────────────────────────────────────────────────────┘

IPFS ORIGINAL              CONSTRAINT LAYER              DISPLAY
─────────────              ────────────────              ───────

┌───────────┐             ┌───────────────┐            ┌─────────┐
│           │             │               │            │         │
│  8000px   │      →      │   OPTIMIZED   │     →      │ VIEWPORT│
│  50 MB    │             │   INTERMEDIATE│            │ (fast)  │
│           │             │               │            │         │
└───────────┘             └───────────────┘            └─────────┘
                                 │
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │ THUMBNAIL│      │  MEDIUM  │      │   FULL   │
        │  256px   │      │  1024px  │      │  (lazy)  │
        │  fast    │      │  balanced│      │  on zoom │
        └──────────┘      └──────────┘      └──────────┘
```

### Progressive Loading

```
TIME ──────────────────────────────────────────────────────►

t=0          t=100ms        t=500ms         t=2s+
───          ───────        ───────         ────

┌─────┐      ┌─────┐        ┌─────┐         ┌─────┐
│░░░░░│  →   │▒▒▒▒▒│   →    │▓▓▓▓▓│    →    │█████│
│░░░░░│      │▒▒▒▒▒│        │▓▓▓▓▓│         │█████│
└─────┘      └─────┘        └─────┘         └─────┘
 blur         thumb          medium          full
 placeholder  (fast)         (clear)         (crisp)
```

### Lossless Upscale on Demand

```
USER ZOOMS IN
─────────────

Current view: 1024px intermediate
     │
     │  User zooms to 200%
     ▼
┌─────────────────────────────────────┐
│         UPSCALE ENGINE              │
│                                     │
│  Option A: Fetch full from IPFS     │
│            (if available)           │
│                                     │
│  Option B: AI upscale               │
│            (Real-ESRGAN / similar)  │
│            No quality loss          │
│                                     │
│  Option C: Vector reconstruction    │
│            (for compatible assets)  │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
Display at 2048px+ without artifacts
```

---

## GLB DEPTH FRAMEWORK

### Why GLB (glTF Binary)

```
FORMAT COMPARISON
─────────────────

│ Format │ 3D │ Web-Ready │ Compressed │ Animation │ PBR Materials │
│────────│────│───────────│────────────│───────────│───────────────│
│ PNG    │ ✗  │ ✓         │ ✗          │ ✗         │ ✗             │
│ JPEG   │ ✗  │ ✓         │ ✓          │ ✗         │ ✗             │
│ OBJ    │ ✓  │ ✗         │ ✗          │ ✗         │ ✗             │
│ FBX    │ ✓  │ ✗         │ ✗          │ ✓         │ ✓             │
│ GLB    │ ✓  │ ✓         │ ✓          │ ✓         │ ✓             │ ◄── IT-R8
```

### Depth Generation from 2D

```
2D INPUT                    DEPTH ESTIMATION              GLB OUTPUT
────────                    ────────────────              ──────────

┌─────────────┐            ┌─────────────┐            ┌─────────────┐
│             │            │             │            │  ╱╲         │
│   FLAT      │     →      │   DEPTH     │     →      │ ╱  ╲  3D    │
│   IMAGE     │            │   MAP       │            │╱    ╲       │
│             │            │ (estimated) │            │      MESH   │
└─────────────┘            └─────────────┘            └─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
              MiDaS / ZoeDepth           Custom trained
              (general depth)            (art-specific)
```

### GLB Scene Structure

```
GLB FILE STRUCTURE
──────────────────

my_artwork.glb
├── scene
│   ├── mesh (depth-displaced plane or 3D geometry)
│   ├── material
│   │   ├── baseColorTexture (original image)
│   │   ├── normalMap (surface detail)
│   │   └── metallicRoughness
│   └── animations (optional)
│       ├── camera_orbit
│       ├── parallax_shift
│       └── depth_pulse
├── textures (embedded, optimized)
└── metadata
    ├── ipfs_source_cid
    ├── archivit_bubble_id
    └── generation_params
```

---

## WEBGL FALLBACK SYSTEM (CRITICAL)

### The Reality: WebGL Not Universal

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WEBGL SUPPORT REALITY (2026)                          │
└─────────────────────────────────────────────────────────────────────────┘

SUPPORTED                              NOT SUPPORTED / LIMITED
─────────                              ───────────────────────

• Modern desktop browsers              • Older mobile devices
• Recent iOS Safari                    • Some Android WebViews
• Chrome/Firefox/Edge                  • Corporate locked browsers
• Most gaming devices                  • Low-power tablets
                                       • Accessibility readers
                                       • Some embedded browsers
                                       • Privacy-focused configs

           ▼                                    ▼
     GLB/3D works                      MUST STILL WORK
                                       (no errors, similar effect)
```

### PARAMOUNT RULE: NEVER ERROR, ALWAYS FALLBACK

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   IF WEBGL FAILS → GRACEFUL DEGRADATION → SIMILAR VISUAL EFFECT         │
│                                                                         │
│   NEVER:                                                                │
│   • Show blank screen                                                   │
│   • Display error message                                               │
│   • Break the layout                                                    │
│   • Require user action to fix                                          │
│                                                                         │
│   ALWAYS:                                                               │
│   • Detect capability BEFORE attempting render                          │
│   • Switch to fallback SILENTLY                                         │
│   • Maintain visual intent                                              │
│   • Preserve interactivity where possible                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### FALLBACK DETECTION FLOW

```
PAGE LOAD
    │
    ▼
┌─────────────────────┐
│  DETECT WEBGL       │
│  CAPABILITY         │
└─────────────────────┘
    │
    ├──► WebGL 2.0 available?
    │         │
    │         ├── YES → TIER 1: Full GLB + depth
    │         │
    │         └── NO ──┐
    │                  │
    ├──► WebGL 1.0 available?
    │         │        │
    │         ├── YES ─┴─► TIER 2: Simplified 3D
    │         │
    │         └── NO ──┐
    │                  │
    ├──► Canvas 2D available?
    │         │        │
    │         ├── YES ─┴─► TIER 3: CSS parallax + canvas
    │         │
    │         └── NO ──┐
    │                  │
    └──► Basic HTML    │
              │        │
              └────────┴─► TIER 4: Static image + CSS effects
```

---

### TIER SYSTEM: GRACEFUL DEGRADATION

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TIER 1: FULL WEBGL 2.0                                                 │
│  ───────────────────────                                                │
│                                                                         │
│  • Full GLB rendering with Three.js                                     │
│  • Real-time depth displacement                                         │
│  • PBR materials and lighting                                           │
│  • Orbit controls, zoom, pan                                            │
│  • WebXR ready                                                          │
│                                                                         │
│  Visual: ████████████████████████████████████████ 100% intended effect  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (if unavailable)
┌─────────────────────────────────────────────────────────────────────────┐
│  TIER 2: WEBGL 1.0 SIMPLIFIED                                           │
│  ────────────────────────────                                           │
│                                                                         │
│  • Basic WebGL plane with texture                                       │
│  • Pre-baked depth as normal map                                        │
│  • Simplified shaders                                                   │
│  • Mouse-based parallax only                                            │
│  • No orbit, limited zoom                                               │
│                                                                         │
│  Visual: ██████████████████████████████░░░░░░░░░░ 75% intended effect   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (if unavailable)
┌─────────────────────────────────────────────────────────────────────────┐
│  TIER 3: CSS + CANVAS 2D                                                │
│  ───────────────────────                                                │
│                                                                         │
│  • Layered images (foreground/midground/background)                     │
│  • CSS transform3d for parallax                                         │
│  • Canvas 2D for dynamic effects                                        │
│  • Mouse tracking for layer movement                                    │
│  • CSS filters for depth-of-field simulation                            │
│                                                                         │
│  Visual: ████████████████████░░░░░░░░░░░░░░░░░░░░ 50% intended effect   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (if unavailable)
┌─────────────────────────────────────────────────────────────────────────┐
│  TIER 4: STATIC FALLBACK                                                │
│  ───────────────────────                                                │
│                                                                         │
│  • High-quality static render (pre-generated)                           │
│  • CSS hover effects (scale, shadow)                                    │
│  • Optional: animated GIF/APNG for motion hint                          │
│  • Blur vignette for depth suggestion                                   │
│  • Still looks intentional, not broken                                  │
│                                                                         │
│  Visual: ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25% intended effect   │
│          (but ZERO errors, still beautiful)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### FALLBACK EFFECT MAPPING

| GLB Effect | Tier 2 Fallback | Tier 3 Fallback | Tier 4 Fallback |
|------------|-----------------|-----------------|-----------------|
| **Depth displacement** | Normal map shader | Layered images + CSS translate | Pre-rendered depth image |
| **Parallax on mouse** | Simple vertex offset | CSS transform3d layers | CSS hover scale |
| **Orbit rotation** | Limited Y-axis only | CSS perspective rotate | Static angle render |
| **Zoom interaction** | Texture scale | CSS scale transform | Lightbox popup |
| **PBR lighting** | Basic diffuse | CSS gradients/shadows | Baked lighting in image |
| **Animation loops** | Reduced framerate | CSS animation | Animated GIF/APNG |
| **Depth of field** | Blur shader | CSS blur filter | Pre-blurred layers |

---

### ASSET GENERATION: ALWAYS INCLUDE FALLBACKS

```
IT-R8 OUTPUT PACKAGE
────────────────────

artwork_001/
├── primary/
│   └── artwork.glb              ← Full 3D (Tier 1)
│
├── fallback_tier2/
│   ├── texture.webp             ← Base image
│   ├── normal.webp              ← Normal map for fake depth
│   └── shader_config.json       ← Simplified shader params
│
├── fallback_tier3/
│   ├── layer_bg.webp            ← Background layer
│   ├── layer_mid.webp           ← Midground layer
│   ├── layer_fg.webp            ← Foreground layer
│   └── parallax_config.json     ← Layer offsets
│
├── fallback_tier4/
│   ├── static.webp              ← High-quality static render
│   ├── static_hover.webp        ← Alternate state
│   └── preview.gif              ← Optional motion hint
│
└── manifest.json                ← Describes all tiers + detection
```

---

### DETECTION CODE PATTERN

```javascript
// IT-R8 RENDERER INITIALIZATION (Pseudocode)

function initRenderer(container, assetManifest) {
  const capability = detectCapability();

  // NEVER throw errors - always have a path forward
  switch(capability.tier) {
    case 1:
      return new GLBRenderer(container, assetManifest.primary);
    case 2:
      return new SimplifiedWebGLRenderer(container, assetManifest.fallback_tier2);
    case 3:
      return new CSSParallaxRenderer(container, assetManifest.fallback_tier3);
    case 4:
    default:
      return new StaticImageRenderer(container, assetManifest.fallback_tier4);
  }
}

function detectCapability() {
  // Check WebGL 2
  const canvas = document.createElement('canvas');
  const gl2 = canvas.getContext('webgl2');
  if (gl2) return { tier: 1, context: gl2 };

  // Check WebGL 1
  const gl1 = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (gl1) return { tier: 2, context: gl1 };

  // Check Canvas 2D
  const ctx2d = canvas.getContext('2d');
  if (ctx2d) return { tier: 3, context: ctx2d };

  // Fallback to static
  return { tier: 4, context: null };
}
```

---

### CSS PARALLAX FALLBACK (Tier 3 Detail)

```css
/* Layered parallax without WebGL */

.parallax-container {
  perspective: 1000px;
  transform-style: preserve-3d;
  overflow: hidden;
}

.parallax-layer {
  position: absolute;
  width: 100%;
  height: 100%;
  transition: transform 0.1s ease-out;
}

.layer-bg {
  transform: translateZ(-100px) scale(1.1);
  filter: blur(2px);  /* Depth of field simulation */
}

.layer-mid {
  transform: translateZ(-50px) scale(1.05);
}

.layer-fg {
  transform: translateZ(0px);
}

/* Mouse tracking via CSS custom properties (set by JS) */
.parallax-container {
  --mouse-x: 0.5;
  --mouse-y: 0.5;
}

.layer-bg {
  transform:
    translateZ(-100px)
    translateX(calc((var(--mouse-x) - 0.5) * -30px))
    translateY(calc((var(--mouse-y) - 0.5) * -30px));
}

.layer-fg {
  transform:
    translateX(calc((var(--mouse-x) - 0.5) * 15px))
    translateY(calc((var(--mouse-y) - 0.5) * 15px));
}
```

---

### STATIC FALLBACK STRATEGY (Tier 4 Detail)

```
PRE-RENDER MULTIPLE ANGLES
──────────────────────────

Generate at build time:

┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│  1  │  │  2  │  │  3  │  │  4  │  │  5  │
│ -10°│  │ -5° │  │  0° │  │ +5° │  │+10° │
└─────┘  └─────┘  └─────┘  └─────┘  └─────┘

On mouse move: swap images for pseudo-rotation
Or: CSS crossfade between angles

RESULT: Feels interactive even without WebGL
```

---

### ERROR BOUNDARY WRAPPER

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ERROR BOUNDARY                                   │
│                                                                         │
│   TRY {                                                                 │
│       Render at detected tier                                           │
│   }                                                                     │
│   CATCH (any error) {                                                   │
│       Log error silently (analytics)                                    │
│       Downgrade to next tier                                            │
│       Retry render                                                      │
│   }                                                                     │
│   FINALLY {                                                             │
│       ALWAYS show something                                             │
│       NEVER blank screen                                                │
│       NEVER error modal                                                 │
│   }                                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### TESTING REQUIREMENTS

Before any IT-R8 release:

| Test Scenario | Expected Result |
|---------------|-----------------|
| Chrome latest | Tier 1 renders |
| Firefox latest | Tier 1 renders |
| Safari iOS | Tier 1 or 2 renders |
| WebGL disabled in flags | Tier 3 renders |
| Canvas disabled | Tier 4 renders |
| Very old Android | Tier 4 renders |
| Screen reader active | Static + alt text |
| JavaScript disabled | Static image visible |

**ZERO scenarios should show errors or blank content.**

---

## SPATIAL VIEWING MODES

### Mode 1: Parallax Depth

```
USER HEAD MOVEMENT / MOUSE
──────────────────────────

         ◄──────────────────►
                  │
                  ▼
         ┌───────────────┐
         │    ╱    ╲     │
         │   ╱      ╲    │    Layers shift based on
         │  ╱        ╲   │    viewing angle
         │ ╱          ╲  │
         │╱            ╲ │
         └───────────────┘

Foreground moves more than background
Creates depth illusion
```

### Mode 2: Orbit View

```
         ┌─────────────────┐
         │                 │
     ◄───│    3D ARTWORK   │───►
         │                 │
         └─────────────────┘
                 │
                 ▼
         User can rotate around
         the depth-enhanced artwork
```

### Mode 3: VR/AR Ready

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   GLB format is native to:                                              │
│                                                                         │
│   • WebXR (browser VR/AR)                                               │
│   • Apple Vision Pro                                                    │
│   • Meta Quest                                                          │
│   • Three.js / Babylon.js                                               │
│   • Unity / Unreal (import)                                             │
│                                                                         │
│   IT-R8 outputs are SPATIAL-READY out of the box                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## COMPLETE PIPELINE FLOW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        IT-R8 COMPLETE PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────┘

1. RECEIVE TRAINING DATA (from ARCHIV-IT bubbles)
   │
   ▼
2. FETCH ASSETS FROM IPFS
   │
   ├──► ipfs://Qm... (original high-res)
   │
   ▼
3. RESIZE CONSTRAINT LAYER
   │
   ├──► Generate optimized intermediates
   ├──► Cache locally
   │
   ▼
4. PROCESS TRAINING CONTEXT
   │
   ├──► Extract style features
   ├──► Build MicroLLM context
   │
   ▼
5. [POPULATE] - USER TRIGGERS GENERATION
   │
   ▼
6. GENERATE ASSETS
   │
   ├──► Apply style to new outputs
   ├──► Generate depth maps
   │
   ▼
7. BUILD GLB
   │
   ├──► Combine texture + depth + materials
   ├──► Embed IPFS references in metadata
   ├──► Optimize for web delivery
   │
   ▼
8. OUTPUT
   │
   ├──► GLB file (spatial-ready)
   ├──► Preview renders (2D fallback)
   ├──► IPFS pin (permanent storage)
   │
   ▼
9. DISPLAY
   │
   ├──► Progressive loading (blur → thumb → full)
   ├──► Depth interaction (parallax / orbit)
   └──► Lossless upscale on zoom
```

---

## TECHNICAL STACK

```
LAYER               TECHNOLOGY                 PURPOSE
─────               ──────────                 ───────

Storage             IPFS / Filecoin            Decentralized asset storage
                    Arweave                    Permanent storage option

Gateway             Multiple failover          IPFS retrieval
                    Local node option

Resize              Sharp.js / libvips         Fast image processing
                    Real-ESRGAN                AI upscaling

Depth               MiDaS / ZoeDepth           Monocular depth estimation
                    Custom models              Art-specific training

3D                  Three.js                   WebGL rendering
                    glTF-Transform             GLB optimization

Viewer              WebXR                      VR/AR support
                    Model-viewer               Simple embeds
```

---

## IP IMPLICATIONS

### Patentable Innovations

1. **IPFS-to-GLB Pipeline**
   - Method for generating spatial 3D assets from decentralized storage

2. **Resize Constraint Layer**
   - System for fast loading with lossless on-demand upscaling from IPFS sources

3. **Training-to-Depth Pipeline**
   - Method for generating depth-enhanced 3D outputs from curated 2D training data

4. **Decentralized Spatial Asset Generation**
   - System combining IPFS storage, AI depth estimation, and GLB output

---

## CONNECTION TO ORIGINS

```
2001-2004: Brown University "Cave" VR Research
           │
           │  Spatial computing before the term existed
           │  Medical Artery V.R. visualization
           │
           ▼
2026:      IT-R8 GLB Pipeline
           │
           │  Web-native spatial computing
           │  Decentralized infrastructure
           │  AI-enhanced depth
           │
           ▼
           FULL CIRCLE: Spatial computing democratized
```

---

*This specification establishes the technical architecture for IT-R8's advanced rendering capabilities. The IPFS-direct pipeline with resize constraints and GLB depth output represents a novel approach to decentralized spatial asset generation.*

**Document Date:** January 10, 2026
