# MOONLANGUAGE VIEWER DESIGN GUIDE
## For Website Collectors - Start Here

---

**Document Version:** 1.0
**Created:** January 11, 2026
**Status:** Architecture documented, implementation pending

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GALAXY VIEW                                   │
│         968 moons in golden spiral formation                        │
│                                                                      │
│   Uses: /scripts/interface/static/js/itr8/spiral_geometry.js        │
│   Math: r = a × e^(b×θ)  |  φ = 1.618033988749895                   │
│                                                                      │
│   Behaviors:                                                         │
│   • Nodes float and move fluidly                                    │
│   • Click and drag to navigate                                      │
│   • Intricate spiral pattern (see existing charts)                  │
│   • #SPIRALHASHUNIVERSE                                             │
│                                                                      │
│                          ↓ CLICK ON MOON                            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   ONE MOON ANALYSIS WINDOW                          │
│                                                                      │
│   Template: /design_templates/ONE_MOON_ANALYSIS_WINDOW.html         │
│   Status: SAVED - bring back only when working on this feature      │
│                                                                      │
│   3 Interaction States:                                             │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │ DEFAULT     │ Photo displays (static)                   │       │
│   ├─────────────┼───────────────────────────────────────────┤       │
│   │ HOVER       │ Video plays with audio                    │       │
│   │             │ → returns to photo when complete          │       │
│   ├─────────────┼───────────────────────────────────────────┤       │
│   │ CLICK+HOLD  │ ASCII layer (easter egg)                  │       │
│   │             │ → release returns to previous state       │       │
│   └─────────────┴───────────────────────────────────────────┘       │
│                                                                      │
│   Metadata displayed: EXIF, blockchain, file info                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## SAVED TEMPLATE LOCATION

**ONE MOON ANALYSIS WINDOW:**
```
/design_templates/ONE_MOON_ANALYSIS_WINDOW.html
```

**When to load:** Only when user says they want to work on the one-moon view.

**What it contains:**
- 3-panel layout (metadata | viewer | asset status)
- State machine (photo → video → ASCII)
- Placeholder slots for real assets
- No hallucinated data

---

## GALAXY VIEW REQUIREMENTS (From User)

**Documented from user description - NOT YET IMPLEMENTED:**

| Requirement | Description | Source |
|-------------|-------------|--------|
| Spiral pattern | Intricate spiral following golden ratio | User + existing spiral_geometry.js |
| Fluid motion | Nodes move, everything fluid | User description |
| Floating assets | Moons float in space | User description |
| Click + drag | Navigate the galaxy | User description |
| 968 moons | Complete collection | MOONLANGUAGE spec |
| Node structure | Loosely structured with nodes | User description |

**Existing Code Reference:**
```
/scripts/interface/static/js/itr8/spiral_geometry.js
/scripts/interface/static/js/core/creation_spiral.js
```

**Mathematical Foundation (from spiral_geometry.js):**
```javascript
const PHI = 1.618033988749895;  // Golden ratio
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));  // 137.5°

// Logarithmic spiral: r = a × e^(b×θ)
calculateRadius(theta) {
    return this.config.a * Math.exp(this.config.b * theta);
}
```

**User Quotes (from WhatsApp):**
- "enriched strain of spiral data. Will it populate the spiral by floating around it?"
- "#SPIRALHASHUNIVERSE"
- "Visual node editor"
- "their own #SpiralData on blockchain"

---

## ASSET STRUCTURE (Per Moon)

```
/assets/moon_XXX/
├── photo.jpg       # Static photograph (DEFAULT state)
├── video.mp4       # Animation with audio (HOVER state)
├── ascii.png       # ASCII art version (CLICK+HOLD easter egg)
└── quote.json      # Historical moon quote with verified source
```

### Quote Data Structure (quote.json)

```json
{
  "moon_number": 001,
  "quote": "[ACTUAL HISTORICAL QUOTE]",
  "author": "[VERIFIED AUTHOR NAME]",
  "source": {
    "title": "[BOOK/TEACHING/RECORDING TITLE]",
    "year": "[YEAR IF KNOWN]",
    "type": "book|speech|recording|poem|scripture",
    "verification": "[HOW TO VERIFY - ISBN, archive link, etc.]"
  },
  "status": "pending|verified|final"
}
```

**CRITICAL: NO HALLUCINATED QUOTES**
- All quotes must be real historical statements
- Must have verifiable source (book, teaching, recording)
- User has research in Google Drive to import
- Each quote will be manually verified before final

**Blockchain Mapping:**
| Asset | Chain | Purpose |
|-------|-------|---------|
| photo.jpg + video.mp4 | ETH | Dynamic webGL-HTML, interactive |
| ascii.png | BTC Ordinals | Immutable ASCII inscription |
| quote.json | Metadata | #COSMICDOWNLOAD - blends with moon |

---

## VIEWER STATES DETAIL

### State: PHOTO (Default)

```
Trigger: None (initial state)
Display: Static photograph
Audio: Silent
Returns: N/A
```

### State: VIDEO (Hover)

```
Trigger: Mouse hover over moon
Display: Video plays with audio (432Hz)
Audio: Yes - Plutonic Mind compositions
Returns: To PHOTO when video completes
```

### State: ASCII (Click + Hold)

```
Trigger: Mouse down on moon
Display: ASCII art version (secret easter egg)
Audio: Silent
Returns: To previous state on mouse release
Duration: As long as user holds click
```

**Easter Egg Note:** The ASCII reveal is unexpected - users discover it by accident. This connects to the BTC Ordinals inscription layer.

---

## WHAT NEEDS TO BE BUILT

### Phase 1: Galaxy View
- [ ] Load 968 moon thumbnails
- [ ] Position using spiral_geometry.js math
- [ ] Implement fluid motion/floating
- [ ] Add click+drag navigation
- [ ] Connect to One Moon Analysis on moon click

### Phase 2: One Moon Analysis (Template Ready)
- [ ] Wire template to receive moon selection
- [ ] Load actual assets from folder structure
- [ ] Parse EXIF from photos
- [ ] Connect blockchain data

### Phase 3: Asset Pipeline
- [ ] Create folder structure for all 968 moons
- [ ] Populate with photo/video/ascii assets
- [ ] Verify audio in videos

---

## PATTERNS & CHARTS REFERENCE

**User has existing patterns/charts to study:**
- Location: [USER TO PROVIDE]
- Purpose: Defines the spiral mechanics for galaxy view

**#AGENTNOTE:** Before building Galaxy View, ask user for location of pattern/chart documents they drew to explain the mechanics.

---

## NO HALLUCINATIONS RULE

This design guide documents ONLY:
1. What the user explicitly described
2. What exists in the codebase (spiral_geometry.js)
3. Template files that were created and saved

**NOT documented here (because not yet designed):**
- Galaxy View visual styling (user decides)
- Animation specifics (user decides)
- UI elements beyond what was described

**When in doubt:** ASK user, don't invent.

---

## HOW TO USE THIS GUIDE

1. **Starting Galaxy View work:** Read this guide, then ask for pattern/chart documents
2. **Starting One Moon work:** Load `/design_templates/ONE_MOON_ANALYSIS_WINDOW.html`
3. **Adding assets:** Follow folder structure in this guide
4. **Adding features:** Ask user first, document after

---

*Guide created: January 11, 2026*
*Template saved: ONE_MOON_ANALYSIS_WINDOW.html*
*Galaxy View: Architecture documented, awaiting implementation*
