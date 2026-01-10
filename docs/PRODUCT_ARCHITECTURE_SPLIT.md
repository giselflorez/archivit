# ARCHIV-IT vs IT-R8: Product Architecture Split

**Created:** January 10, 2026
**Status:** Core Architecture Decision

---

## THE FUNDAMENTAL SPLIT

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   ARCHIV-IT                              IT-R8                          │
│   ─────────                              ─────                          │
│                                                                         │
│   INPUT / ORGANIZE / ANALYZE      →      OUTPUT / CREATE / GENERATE    │
│                                                                         │
│   "The Archive"                          "The Studio"                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ARCHIV-IT: READ-ONLY ARCHIVE

### Core Principle
**NO asset creation.** ARCHIV-IT is purely for:
- Ingesting data
- Organizing data
- Analyzing data
- Selecting data for export

### Functions

```
┌─────────────────────────────────────────────────────────────┐
│                      ARCHIV-IT                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  IMPORT                                                      │
│  ──────                                                      │
│  • Blockchain scanning (multi-chain)                         │
│  • Cloud imports (Google Drive, Dropbox)                     │
│  • Bulk imports (folders, zip files)                         │
│  • Individual file imports                                   │
│  • Social media data exports (Twitter, Instagram)            │
│  • Web scraping / URL imports                                │
│                                                              │
│  ORGANIZE                                                    │
│  ────────                                                    │
│  • Timeline population (temporal views)                      │
│  • Tag networks                                              │
│  • Semantic relationships                                    │
│  • Collection grouping                                       │
│                                                              │
│  PRESERVE                                                    │
│  ────────                                                    │
│  • IPFS pinning services setup                               │
│  • Arweave permanent storage                                 │
│  • Local backup management                                   │
│  • Version history tracking                                  │
│                                                              │
│  ANALYZE                                                     │
│  ───────                                                     │
│  • View modes (5 paradigms)                                  │
│  • Relationship exploration                                  │
│  • Provenance verification                                   │
│  • Network authenticity scoring                              │
│                                                              │
│  SELECT                                                      │
│  ──────                                                      │
│  • Bubble selection (data clusters)                          │
│  • Filter and facet                                          │
│  • Export preparation                                        │
│  • ──► OUTPUT TO IT-R8 ──►                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## IT-R8: CREATIVE OUTPUT ENGINE

### Core Principle
**Asset CREATION happens here.** IT-R8 receives selected data bubbles and generates outputs.

### Functions

```
┌─────────────────────────────────────────────────────────────┐
│                         IT-R8                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  RECEIVE                                                     │
│  ───────                                                     │
│  • Selected bubbles from ARCHIV-IT                           │
│  • MicroLLM contexts (curated data clusters)                 │
│  • Style references                                          │
│  • Constraint parameters                                     │
│                                                              │
│  GENERATE                                                    │
│  ────────                                                    │
│  • [POPULATE] button activates generation                    │
│  • Design assets from MicroLLM contexts                      │
│  • Style variations                                          │
│  • Desktop themes                                            │
│  • Export packages                                           │
│                                                              │
│  CREATE                                                      │
│  ──────                                                      │
│  • New visual assets                                         │
│  • Press kits                                                │
│  • Portfolio exports                                         │
│  • Marketing materials                                       │
│  • Custom outputs                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## THE BUBBLE → MICROLLM CONCEPT

### What is a Bubble?

A "bubble" is a selected cluster of data from ARCHIV-IT that becomes a **MicroLLM context** for design generation in IT-R8.

```
ARCHIV-IT VIEW
──────────────

     ○ ○ ○           ○ ○
    ○ ○ ○ ○         ○ ○ ○
     ○ ○ ○           ○ ○
                              ○ ○ ○ ○
         ○ ○ ○ ○              ○ ○ ○
          ○ ○ ○

            │
            │  USER SELECTS A CLUSTER
            ▼

    ┌───────────────┐
    │   BUBBLE 1    │     ← "All my fire photography 2019-2021"
    │   ○ ○ ○ ○     │
    │    ○ ○ ○      │
    └───────────────┘

            │
            │  EXPORT TO IT-R8
            ▼

    ┌───────────────────────────────────────┐
    │           MICROLLM CONTEXT            │
    │                                       │
    │  • 47 images                          │
    │  • Color palette: oranges, blacks     │
    │  • Themes: transformation, danger     │
    │  • Style: high contrast, motion blur  │
    │  • Metadata: dates, exhibitions       │
    │                                       │
    └───────────────────────────────────────┘

            │
            │  [POPULATE] BUTTON
            ▼

    ┌───────────────────────────────────────┐
    │           IT-R8 GENERATES             │
    │                                       │
    │  • Desktop wallpaper in fire style    │
    │  • Icon set with flame palette        │
    │  • Press kit with selected works      │
    │  • Portfolio page layout              │
    │                                       │
    └───────────────────────────────────────┘
```

---

## BUBBLE TYPES (MicroLLM Contexts)

| Bubble Type | Selection Method | MicroLLM Use |
|-------------|------------------|--------------|
| **Temporal** | Date range selection | "My style evolution 2020-2022" |
| **Thematic** | Tag/keyword cluster | "All water-related works" |
| **Collection** | Named collection | "SuperRare drops only" |
| **Network** | Collector overlap | "Works owned by top collectors" |
| **Platform** | Source filter | "Foundation pieces" |
| **Custom** | Manual multi-select | "These 12 specific pieces" |

---

## USER FLOW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  1. IMPORT DATA                                                         │
│     └─► ARCHIV-IT ingests blockchain, cloud, local files               │
│                                                                         │
│  2. EXPLORE & ANALYZE                                                   │
│     └─► User navigates views, discovers patterns                       │
│                                                                         │
│  3. SELECT BUBBLE                                                       │
│     └─► User draws selection or applies filters                        │
│     └─► Bubble = data cluster becomes MicroLLM context                 │
│                                                                         │
│  4. CONFIGURE OUTPUT                                                    │
│     └─► User chooses output type (theme, press kit, portfolio)         │
│     └─► User sets constraints (colors, sizes, formats)                 │
│                                                                         │
│  5. [POPULATE] BUTTON                                                   │
│     └─► IT-R8 receives bubble + config                                 │
│     └─► Generation begins                                              │
│                                                                         │
│  6. REVIEW & REFINE                                                     │
│     └─► User reviews generated assets                                  │
│     └─► Iterates with different bubbles or settings                    │
│                                                                         │
│  7. EXPORT                                                              │
│     └─► Final assets saved/published                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## INTERFACE CONCEPT: BUBBLE SELECTION

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ARCHIV-IT                                              [EXPORT BUBBLE] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                    ○ ○                                                  │
│          ○ ○ ○    ○ ○ ○                                                │
│         ○ ○ ○ ○    ○ ○              BUBBLE SELECTED                    │
│          ○ ○ ○                      ───────────────                    │
│                         ┌─────────────────────────┐                    │
│     ○ ○               ╱│  ● ● ●                   │                    │
│    ○ ○ ○             ╱ │   ● ● ● ●                │  23 items          │
│     ○ ○             ╱  │    ● ● ●                 │  Fire series       │
│                    ╱   │                          │  2019-2021         │
│                   ╱    └─────────────────────────┘                     │
│                  ╱              │                                       │
│                 ╱               │                                       │
│    ○ ○ ○ ○ ○   ╱                ▼                                       │
│     ○ ○ ○ ○                                                            │
│      ○ ○ ○              [ANALYZE]  [EXPORT TO IT-R8]                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  FILTERS: [ ] By Date  [ ] By Tag  [ ] By Collection  [ ] By Platform  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ARCHIV-IT DOES NOT:

- Generate new images
- Create derivative works
- Mint NFTs
- Post to social media
- Modify original assets
- Apply AI transformations to content

**ARCHIV-IT is a pure archive + analysis tool.**

---

## IT-R8 DOES:

- Generate new assets from MicroLLM contexts
- Create derivative works
- Apply style transfer
- Build export packages
- Generate marketing materials
- Provide [POPULATE] button for activation

**IT-R8 is the creative output engine.**

---

## BUSINESS MODEL IMPLICATION

```
ARCHIV-IT (Free/Low-cost)          IT-R8 (Premium)
────────────────────────           ───────────────
• Archive management               • Asset generation
• Basic views                      • Advanced MicroLLM
• Local storage                    • Cloud processing
• Manual exports                   • One-click outputs
                                   • Style AI
        │                                  │
        └──────────── GATEWAY ─────────────┘
                         │
              Bubbles selected in ARCHIV-IT
              unlock value in IT-R8
```

---

## IP IMPLICATIONS

This architecture split creates additional patent opportunities:

1. **Bubble Selection Method** - UI/UX for selecting data clusters
2. **MicroLLM Context Generation** - Converting data clusters to AI contexts
3. **Archive-to-Studio Pipeline** - Data handoff between read-only and creative apps

---

*This architectural split ensures ARCHIV-IT remains a trusted, non-destructive archive while IT-R8 handles all creative generation. Users know their archive is safe and unmodified.*
