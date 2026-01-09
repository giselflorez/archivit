# ARCHIV-IT Dark Mode Design System

## PRIMARY DESIGN SYSTEM

**This is the default design system for ARCHIV-IT. Consider this FIRST for all interface work.**

For light/white background contexts (PDF exports, print, external docs), see: `/docs/LIGHT_MODE_DESIGN_SYSTEM.md`

---

## Reference Implementation
**Location:** `/scripts/interface/templates/assessment_report.html`

## Historical Context
This design system evolved through multiple sessions of refinement. For learning about design decisions and iterations, see:
- `/docs/BRANDING_STATEMENT_ITERATIONS.md` — Copy/messaging exploration
- `/docs/DESIGN_SYSTEM.md` — Additional UI specifications
- `/docs/branding_preview.html` — Light mode template (derived from this system)

---

## Design Philosophy

### Core Principles
1. **Data Feels Precious** — Dark, careful, intentional aesthetic that honors the archive
2. **Single Viewport** — No scrolling for primary content; information density over sprawl
3. **Visual First** — Color and shape communicate before text is read
4. **Progressive Disclosure** — Summary visible → hover reveals detail → click navigates
5. **Quiet Until Needed** — Subtle defaults, reveal on interaction

### Signature Element: The Liquid Badge
The animated liquid-filled badge is the visual signature of ARCHIV-IT. It represents:
- **Verification level** through fill height
- **Life/activity** through gentle jiggle animation
- **Depth** through rising bubbles
- **Status** through color (green → lime → yellow → red spectrum)

---

## CSS Variables (Dark Mode)

```css
:root {
    /* Background layers - darkest to lightest */
    --bg-primary: #0a0a0f;      /* Page background */
    --bg-secondary: #12121a;     /* Cards, elevated surfaces */
    --bg-tertiary: #1a1a24;      /* Nested elements, inputs */

    /* Text hierarchy - lightest to most muted */
    --text-primary: #e8e6e3;                    /* Headlines, important */
    --text-secondary: rgba(232, 230, 227, 0.7); /* Body text */
    --text-muted: rgba(232, 230, 227, 0.4);     /* Captions, metadata */

    /* Borders */
    --border-color: rgba(255, 255, 255, 0.08);  /* Default */
    --border-hover: rgba(255, 255, 255, 0.15);  /* Hover state */

    /* Accent */
    --accent-gold: #d4a574;                      /* Primary accent, CTAs */
    --accent-gold-glow: rgba(212, 165, 116, 0.5); /* Glow effects */

    /* Status colors - verification spectrum */
    --status-verified: #22c55e;     /* Green - excellent (85%+) */
    --status-established: #84cc16;  /* Lime - good (65-84%) */
    --status-emerging: #eab308;     /* Yellow - developing (40-64%) */
    --status-uncertain: #ef4444;    /* Red - needs work (<40%) */

    /* Category colors */
    --source-blockchain: #8b5cf6;   /* Purple - blockchain data */
    --color-network: #3b82f6;       /* Blue - network/social */
    --color-timeline: #f59e0b;      /* Amber - temporal data */
}
```

---

## Typography

### Font Stack
```css
/* UI text, body, labels */
font-family: 'Inter', -apple-system, sans-serif;

/* Numbers, data, monospace */
font-family: 'JetBrains Mono', monospace;
```

### Type Scale (Compact)

| Element | Size | Weight | Spacing | Color | Font |
|---------|------|--------|---------|-------|------|
| Page title | 1.1rem | 600 | -0.01em | --text-primary | Inter |
| Section header | 0.85rem | 600 | normal | --text-primary | Inter |
| Body text | 0.75rem | 400 | normal | --text-secondary | Inter |
| Labels | 0.65-0.7rem | 500 | 0.05-0.12em | --text-secondary | Inter |
| Data values | 0.75rem | 600 | normal | --text-primary | JetBrains Mono |
| Tiny/meta | 0.6rem | 400 | normal | --text-muted | Inter |
| Buttons | 0.85rem | 600 | normal | --bg-primary | Inter |

### Typography Rules
- **Numbers ALWAYS in JetBrains Mono** — Creates data credibility
- **Uppercase labels get letter-spacing** — 0.05em to 0.15em
- **Sizes are intentionally small** — 0.6rem to 1.1rem range only
- **Never use font sizes larger than 1.1rem** in interface

---

## Color System

### Background Hierarchy
```
Page (#0a0a0f) → Card (#12121a) → Nested (#1a1a24)
```
Each level is slightly lighter, creating depth without borders.

### Status Color Definitions

| Status | Color | Light Variant | Dark Variant | Glow | Use When |
|--------|-------|---------------|--------------|------|----------|
| Verified | #22c55e | #4ade80 | #15803d | rgba(34,197,94,0.5) | Score 85%+ |
| Established | #84cc16 | #a3e635 | #65a30d | rgba(132,204,22,0.4) | Score 65-84% |
| Emerging | #eab308 | #facc15 | #ca8a04 | rgba(234,179,8,0.3) | Score 40-64% |
| Uncertain | #ef4444 | #f87171 | #b91c1c | rgba(239,68,68,0.2) | Score <40% |

### Score Bar Gradients
```css
.vitality    { background: linear-gradient(90deg, #22c55e, #4ade80); }
.network     { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.transaction { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.timeline    { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
```

---

## The Liquid Badge System

### Structure
```html
<div class="badge-container badge-verified">
    <div class="badge-glow"></div>
    <div class="badge-circle">
        <div class="badge-liquid" style="height: 85%"></div>
        <div class="badge-bubbles">
            <div class="bubble"></div>
            <div class="bubble"></div>
            <div class="bubble"></div>
        </div>
    </div>
</div>
```

### CSS Implementation
```css
.badge-container {
    position: relative;
    width: 80px;
    height: 80px;
}

.badge-glow {
    position: absolute;
    inset: -8px;
    border-radius: 50%;
    background: var(--badge-glow);
    filter: blur(16px);
    opacity: 0.6;
    animation: glowPulse 2.5s ease-in-out infinite;
}

.badge-circle {
    position: relative;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: var(--bg-tertiary);
    border: 3px solid var(--badge-color);
    overflow: hidden;
}

.badge-liquid {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(180deg,
        var(--badge-color-light) 0%,
        var(--badge-color) 50%,
        var(--badge-color-dark) 100%
    );
    animation: liquidJiggle 3s ease-in-out infinite;
    border-radius: 0 0 36px 36px;
}

/* Bubbles */
.bubble {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%,
        rgba(255,255,255,0.8),
        rgba(255,255,255,0.2)
    );
    animation: bubbleRise 4s ease-in-out infinite;
}

.bubble:nth-child(1) { width: 6px; height: 6px; left: 25%; animation-delay: 0s; }
.bubble:nth-child(2) { width: 4px; height: 4px; left: 50%; animation-delay: 1.3s; }
.bubble:nth-child(3) { width: 5px; height: 5px; left: 70%; animation-delay: 2.6s; }
```

### Badge Animations
```css
@keyframes liquidJiggle {
    0%, 100% { transform: translateY(0) scaleX(1); }
    25% { transform: translateY(-2px) scaleX(1.03); }
    50% { transform: translateY(1px) scaleX(0.97); }
    75% { transform: translateY(-1px) scaleX(1.01); }
}

@keyframes glowPulse {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.05); }
}

@keyframes bubbleRise {
    0% { bottom: 5%; opacity: 0; transform: scale(0.5); }
    15% { opacity: 0.8; transform: scale(1); }
    85% { opacity: 0.5; }
    100% { bottom: 85%; opacity: 0; transform: scale(0.3); }
}
```

### Badge Fill Levels
| Status | Fill Height | Color Class |
|--------|-------------|-------------|
| Verified | 85% | .badge-verified |
| Established | 65% | .badge-established |
| Emerging | 40% | .badge-emerging |
| Uncertain | 15% | .badge-uncertain |

---

## Component Patterns

### Cards
```css
.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 12px 16px;
}

.card:hover {
    border-color: var(--border-hover);
}
```

### Chips/Tags
```css
.chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    font-size: 0.7rem;
    transition: all 0.15s ease;
}

.chip:hover {
    background: var(--bg-primary);
}

/* Status indicator */
.chip.positive { border-left: 2px solid #22c55e; }
.chip.neutral { border-left: 2px solid #3b82f6; }
.chip.warning { border-left: 2px solid #f59e0b; }
```

### Score Bars
```css
.score-bar {
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
    overflow: hidden;
}

.score-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease;
}
```

### Primary Button
```css
.btn-primary {
    display: block;
    width: 100%;
    padding: 14px 24px;
    background: var(--accent-gold);
    color: var(--bg-primary);
    border: none;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
}
```

### Tooltips
```css
.tooltip {
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 10px 12px;
    width: 240px;
    font-size: 0.7rem;
    line-height: 1.5;
    color: var(--text-secondary);
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s ease;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    z-index: 100;
}

.parent:hover .tooltip {
    opacity: 1;
    visibility: visible;
}
```

### Gold Accent Border
```css
.accent-border {
    border-left: 2px solid var(--accent-gold);
    padding-left: 12px;
}
```

---

## Spacing System

| Name | Value | Usage |
|------|-------|-------|
| xs | 4px | Icon gaps, tight elements |
| sm | 8px | Chip gaps, related items |
| md | 12px | Card padding, section gaps |
| lg | 16px | Major section spacing |
| xl | 20-24px | Page sections |
| 2xl | 28px | Major breaks |

---

## Animation Guidelines

| Property | Duration | Easing | Usage |
|----------|----------|--------|-------|
| Hover states | 0.15s | ease | Buttons, chips, cards |
| Transitions | 0.2s | ease | Color changes, transforms |
| Reveals | 0.3s | ease | Tooltips, expandables |
| Score bars | 0.8s | ease | Data visualization |
| Badge jiggle | 3s | ease-in-out | Liquid motion (infinite) |
| Glow pulse | 2.5s | ease-in-out | Badge glow (infinite) |
| Bubbles | 4s | ease-in-out | Rising bubbles (infinite) |

**Rules:**
- Maximum 2-3 infinite animations per view
- All other animations are triggered by interaction
- Prefer transform and opacity for performance
- Never animate layout properties (width, height, margin)

---

## Layout Principles

### Single Viewport Rule
```css
body {
    height: 100vh;
    overflow: hidden;
}
```
Primary content must fit without scrolling. Use progressive disclosure for details.

### Container Sizing
```css
.container {
    max-width: 640px;  /* Focused views */
    padding: 24px;
}
```

### Grid Patterns
```css
/* Two-column scores */
.scores-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 24px;
}

/* Chip flow */
.chips-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
```

---

## Implementation Checklist

When creating new dark-mode pages:

- [ ] Import Inter (300-700) and JetBrains Mono (400,500)
- [ ] Set body background to #0a0a0f
- [ ] Use CSS variables for all colors
- [ ] Numbers in JetBrains Mono
- [ ] Font sizes in 0.6-1.1rem range only
- [ ] Gold accent (#d4a574) for primary CTAs only
- [ ] Hover feedback on all interactive elements
- [ ] Tooltips instead of visible descriptions
- [ ] No emojis
- [ ] Single viewport, no scrolling for primary content
- [ ] Animations 0.15-0.3s for interactions
- [ ] Maximum 2-3 infinite animations

---

## Do NOT

- Use font sizes larger than 1.1rem
- Use pure white (#ffffff) for text
- Use pure black borders
- Add decorative animations
- Create scrolling layouts for primary content
- Use emojis anywhere
- Mix hex and rgba inconsistently
- Forget JetBrains Mono for numbers

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-08 | Documentation formalized from assessment_report.html reference |
| 2026-01-07 | Design system established (Session 12) |

---

*This is the PRIMARY design system for ARCHIV-IT. All in-app interfaces should follow this specification. For white-background contexts, see LIGHT_MODE_DESIGN_SYSTEM.md*
