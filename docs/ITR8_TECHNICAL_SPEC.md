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
