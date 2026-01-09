# ARCHIV-IT Design System
## WEB3GISEL Visual Language Specification

This document defines the complete visual language for ARCHIV-IT. All future interfaces, components, and views MUST follow these specifications to maintain consistency.

---

## 1. CORE PHILOSOPHY

```
PRINCIPLE 1: Single Viewport
─────────────────────────────
Every view should fit within one screen. No scrolling required for primary content.
If content exceeds viewport, it belongs in a different view or behind a hover/expand.

PRINCIPLE 2: Visual First
─────────────────────────────
The most important information should be communicated visually (color, size, fill level)
before the user needs to read text. Text explains; visuals communicate instantly.

PRINCIPLE 3: Progressive Disclosure
─────────────────────────────
Show summary → hover reveals detail → click navigates to full view.
Never dump all information at once. Layer it.

PRINCIPLE 4: Quiet Until Relevant
─────────────────────────────
UI elements should be subtle/muted until the user needs them.
Hover states reveal actions. Default state is calm.

PRINCIPLE 5: Data Feels Precious
─────────────────────────────
This is an archive for artists. The aesthetic should feel like handling
valuable artifacts - dark, careful, intentional. Not playful or casual.
```

---

## 2. COLOR SYSTEM

### 2.1 Background Layers
```css
--bg-primary: #0a0a0f;      /* Deepest black - page background */
--bg-secondary: #12121a;    /* Cards, containers */
--bg-tertiary: #1a1a24;     /* Nested elements, inputs, hover states */
```

### 2.2 Text Hierarchy
```css
--text-primary: #e8e6e3;                    /* Headlines, important data */
--text-secondary: rgba(232, 230, 227, 0.7); /* Body text, descriptions */
--text-muted: rgba(232, 230, 227, 0.4);     /* Labels, hints, timestamps */
```

### 2.3 Accent Colors
```css
--accent-gold: #d4a574;        /* Primary accent - CTAs, links, highlights */
--accent-gold-light: #e0b989;  /* Hover state for gold */
--accent-gold-dark: #b8956a;   /* Active/pressed state */
```

### 2.4 Border & Dividers
```css
--border-color: rgba(255, 255, 255, 0.08);  /* Subtle, almost invisible */
--border-hover: rgba(255, 255, 255, 0.15);  /* Slightly more visible on hover */
```

### 2.5 Status Colors (Green-to-Red Spectrum)
```css
/* VERIFIED - Excellent */
--status-verified: #22c55e;
--status-verified-light: #4ade80;
--status-verified-dark: #15803d;
--status-verified-glow: rgba(34, 197, 94, 0.5);

/* ESTABLISHED - Good */
--status-established: #84cc16;
--status-established-light: #a3e635;
--status-established-dark: #65a30d;
--status-established-glow: rgba(132, 204, 22, 0.4);

/* EMERGING - Caution */
--status-emerging: #eab308;
--status-emerging-light: #facc15;
--status-emerging-dark: #ca8a04;
--status-emerging-glow: rgba(234, 179, 8, 0.3);

/* UNCERTAIN - Warning */
--status-uncertain: #ef4444;
--status-uncertain-light: #f87171;
--status-uncertain-dark: #b91c1c;
--status-uncertain-glow: rgba(239, 68, 68, 0.2);
```

### 2.6 Category/Source Colors
```css
--source-blockchain: #8b5cf6;  /* Purple */
--source-twitter: #1da1f2;     /* Twitter blue */
--source-superrare: #ef4444;   /* Red */
--source-foundation: #22c55e;  /* Green */
--source-opensea: #3b82f6;     /* Blue */
```

---

## 3. TYPOGRAPHY

### 3.1 Font Families
```css
/* Primary UI Font */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Monospace for Data/Numbers */
font-family: 'JetBrains Mono', 'SF Mono', 'Monaco', monospace;
```

### 3.2 Font Sizes (rem-based, compact)
```css
--text-xs: 0.6rem;    /* 9.6px - Tiny labels, footnotes */
--text-sm: 0.7rem;    /* 11.2px - Labels, meta info */
--text-base: 0.8rem;  /* 12.8px - Body text, descriptions */
--text-md: 0.85rem;   /* 13.6px - Important body, buttons */
--text-lg: 1.1rem;    /* 17.6px - Section headers */
--text-xl: 1.4rem;    /* 22.4px - Page titles */
```

### 3.3 Font Weights
```css
--weight-light: 300;    /* Rarely used */
--weight-normal: 400;   /* Body text */
--weight-medium: 500;   /* Labels, emphasis */
--weight-semibold: 600; /* Headers, important */
--weight-bold: 700;     /* Numbers, key data */
```

### 3.4 Letter Spacing
```css
/* Uppercase labels get wide spacing */
text-transform: uppercase;
letter-spacing: 0.1em;  /* Standard for labels */
letter-spacing: 0.15em; /* Extra wide for branding */
letter-spacing: 0.05em; /* Subtle for small caps */

/* Normal text: default or slightly tight */
letter-spacing: -0.01em; /* Headlines can be slightly tight */
```

### 3.5 Line Heights
```css
line-height: 1;     /* Numbers, single-line labels */
line-height: 1.3;   /* Compact multi-line */
line-height: 1.5;   /* Body text, descriptions */
```

---

## 4. SPACING SYSTEM

### 4.1 Base Unit
```
4px base unit. All spacing should be multiples of 4.
```

### 4.2 Spacing Scale
```css
--space-1: 4px;   /* Tight: between related elements */
--space-2: 8px;   /* Close: icon to text, tag gaps */
--space-3: 12px;  /* Normal: component internal padding */
--space-4: 16px;  /* Standard: card padding */
--space-5: 20px;  /* Comfortable: section gaps */
--space-6: 24px;  /* Spacious: major section padding */
--space-7: 28px;  /* Large: between major sections */
--space-8: 32px;  /* Extra: page margins on larger screens */
```

### 4.3 Component Padding Patterns
```css
/* Buttons */
padding: 10px 24px;  /* Comfortable click target */
padding: 14px 24px;  /* Large/primary buttons */
padding: 6px 10px;   /* Small/chip buttons */

/* Cards/Containers */
padding: 16px 20px;  /* Standard card */
padding: 12px 16px;  /* Compact card */
padding: 24px;       /* Full page container */

/* Chips/Tags */
padding: 2px 6px;    /* Inline tags */
padding: 6px 10px;   /* Interactive chips */
```

---

## 5. COMPONENT PATTERNS

### 5.1 Cards/Containers
```css
.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px 20px;
}

.card:hover {
    border-color: var(--border-hover);
}
```

### 5.2 Buttons
```css
/* Primary Button (Gold) */
.btn-primary {
    background: var(--accent-gold);
    color: var(--bg-primary);
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
}

/* Secondary Button (Outline) */
.btn-secondary {
    background: transparent;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 0.8rem;
    font-weight: 500;
}

.btn-secondary:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-hover);
}
```

### 5.3 Score/Progress Bars
```css
.score-bar-container {
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, <color>, <color-light>);
    transition: width 0.8s ease;
}
```

### 5.4 Chips/Tags
```css
/* Status Chip with Left Border */
.chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    border-left: 2px solid <status-color>;
    font-size: 0.7rem;
}

/* Inline Tag */
.tag {
    font-size: 0.55rem;
    padding: 1px 5px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    color: var(--text-secondary);
}
```

### 5.5 Tooltips
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
    width: 220px;
    font-size: 0.7rem;
    line-height: 1.5;
    color: var(--text-secondary);
    opacity: 0;
    visibility: hidden;
    transition: all 0.2s ease;
    z-index: 100;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.parent:hover .tooltip {
    opacity: 1;
    visibility: visible;
}
```

---

## 6. ANIMATIONS

### 6.1 Timing Functions
```css
/* Standard easing */
transition-timing-function: ease;

/* For organic/liquid motion */
transition-timing-function: ease-in-out;

/* For snappy UI responses */
transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
```

### 6.2 Duration Scale
```css
--duration-fast: 0.15s;    /* Hover states, micro-interactions */
--duration-normal: 0.2s;   /* Standard transitions */
--duration-slow: 0.3s;     /* Modal open/close, page transitions */
--duration-glacial: 0.8s;  /* Progress bars, data loading */
```

### 6.3 Signature Animations

#### Liquid Jiggle (for liquid-filled elements)
```css
@keyframes liquidJiggle {
    0%, 100% { transform: translateY(0) scaleX(1); }
    25% { transform: translateY(-2px) scaleX(1.03); }
    50% { transform: translateY(1px) scaleX(0.97); }
    75% { transform: translateY(-1px) scaleX(1.01); }
}
/* Usage: animation: liquidJiggle 3s ease-in-out infinite; */
```

#### Glow Pulse (for status indicators)
```css
@keyframes glowPulse {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.05); }
}
/* Usage: animation: glowPulse 2.5s ease-in-out infinite; */
```

#### Bubble Rise (for liquid containers)
```css
@keyframes bubbleRise {
    0% { bottom: 5%; opacity: 0; transform: scale(0.5); }
    15% { opacity: 0.8; transform: scale(1); }
    85% { opacity: 0.5; }
    100% { bottom: 85%; opacity: 0; transform: scale(0.3); }
}
/* Usage: animation: bubbleRise 4s ease-in-out infinite; */
/* Stagger multiple bubbles with animation-delay: 0s, 1.3s, 2.6s */
```

#### Fade In (for page/modal entry)
```css
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
/* Usage: animation: fadeIn 0.3s ease forwards; */
```

### 6.4 Hover States
```css
/* Subtle lift */
transform: translateY(-1px);

/* Brightness boost */
filter: brightness(1.1);

/* Background shift */
background: var(--bg-tertiary);  /* from bg-secondary */

/* Opacity reveal */
opacity: 1;  /* from 0 */
```

---

## 7. LAYOUT PATTERNS

### 7.1 Page Container
```css
.page-container {
    width: 100%;
    max-width: 640px;  /* Comfortable reading width */
    margin: 0 auto;
    padding: 24px;
}

/* For wider layouts */
max-width: 1200px;

/* For narrow/focused layouts */
max-width: 480px;
```

### 7.2 Grid Patterns
```css
/* 2x2 Grid (score bars, stats) */
display: grid;
grid-template-columns: 1fr 1fr;
gap: 12px 24px;

/* 4-column summary */
display: flex;
justify-content: space-between;

/* 3-column card grid */
display: grid;
grid-template-columns: repeat(3, 1fr);
gap: 16px;
```

### 7.3 Flex Patterns
```css
/* Header with icon + text */
display: flex;
align-items: center;
gap: 20px;

/* Space between (label + value) */
display: flex;
justify-content: space-between;
align-items: baseline;

/* Inline chips/tags */
display: flex;
gap: 4px;
flex-wrap: wrap;
```

---

## 8. THE LIQUID BADGE COMPONENT

This is the signature visual element. Use it for status indication.

### 8.1 Structure
```html
<div class="badge-container badge-{state}">
    <div class="badge-glow"></div>
    <div class="badge-circle">
        <div class="badge-liquid" style="height: {fill_percent}%;"></div>
        <div class="badge-bubbles">
            <div class="bubble"></div>
            <div class="bubble"></div>
            <div class="bubble"></div>
        </div>
    </div>
</div>
```

### 8.2 Size Variants
```css
/* Small (inline, navigation) */
width: 32px; height: 32px;

/* Medium (cards, lists) */
width: 48px; height: 48px;

/* Large (headers, hero) */
width: 80px; height: 80px;

/* Extra Large (focal point) */
width: 120px; height: 120px;
```

### 8.3 Fill Levels
```
VERIFIED:    85% fill
ESTABLISHED: 65% fill
EMERGING:    40% fill
UNCERTAIN:   15% fill
```

### 8.4 Complete CSS
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
    width: 100%;
    height: 100%;
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
    border-radius: 0 0 50% 50%;
}

.badge-bubbles {
    position: absolute;
    inset: 0;
    overflow: hidden;
    border-radius: 50%;
}

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

---

## 9. ICON STYLE

### 9.1 Icon Source
Use inline SVGs with `stroke` style (not fill). This allows color inheritance.

### 9.2 Default Properties
```html
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <!-- paths -->
</svg>
```

### 9.3 Sizes
```css
/* Tiny (in text) */
width: 12px; height: 12px;

/* Small (chips, buttons) */
width: 14px; height: 14px;

/* Normal (navigation, cards) */
width: 16px; height: 16px;

/* Medium (feature icons) */
width: 20px; height: 20px;

/* Large (empty states, heroes) */
width: 24px; height: 24px;
```

---

## 10. BRANDING ELEMENTS

### 10.1 Logo Text
```css
.brand-text {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    text-align: center;
}
/* Content: "ARCHIV-IT by WEB3GISEL" */
```

### 10.2 Header Bar
```css
.header-brand {
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    color: var(--text-primary);
}
```

---

## 11. RESPONSIVE BEHAVIOR

### 11.1 Breakpoints
```css
/* Mobile */
@media (max-width: 480px) { }

/* Tablet */
@media (max-width: 768px) { }

/* Desktop */
@media (min-width: 769px) { }
```

### 11.2 Mobile Adjustments
```css
/* Reduce max-width */
max-width: 100%;
padding: 16px;

/* Stack grids */
grid-template-columns: 1fr;

/* Increase touch targets */
min-height: 44px;
padding: 12px 16px;
```

---

## 12. DO's AND DON'Ts

### DO:
- Use the status color spectrum (green → yellow → red) for any quality/health metric
- Keep text small and let visuals dominate
- Use hover states to reveal secondary information
- Maintain high contrast between bg-primary and text-primary
- Use the gold accent sparingly for CTAs and emphasis
- Add subtle glow effects for important status indicators

### DON'T:
- Use emojis anywhere in the interface
- Create pages that require scrolling for primary content
- Use more than 2 font families
- Add borders thicker than 3px
- Use pure white (#ffffff) for text
- Create modals within modals
- Use animation durations longer than 4 seconds
- Add sound effects or notifications

---

## 13. EXAMPLE: CREATING A NEW VIEW

When building a new view, follow this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[View Name] - ARCHIV-IT</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a24;
            --text-primary: #e8e6e3;
            --text-secondary: rgba(232, 230, 227, 0.7);
            --text-muted: rgba(232, 230, 227, 0.4);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent-gold: #d4a574;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .container {
            width: 100%;
            max-width: 640px;
            padding: 24px;
        }

        /* Component styles... */
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with visual focal point -->
        <!-- Score/status section -->
        <!-- Data summary -->
        <!-- Primary CTA -->
        <!-- Brand footer -->
    </div>
</body>
</html>
```

---

## 14. AGENT INSTRUCTIONS

When an agent is asked to create or modify UI for ARCHIV-IT:

1. **Read this document first** - `/docs/DESIGN_SYSTEM.md`
2. **Reference assessment_report.html** as the gold standard implementation
3. **Never extend base.html for focused flows** - Create standalone pages
4. **Ask about the primary visual element** - What should catch the eye first?
5. **Confirm viewport fit** - Will this fit in one screen without scrolling?
6. **Check animations are subtle** - No jarring transitions
7. **Verify no emojis** - Use SVG icons with stroke style only
8. **Test hover states** - All interactive elements need visual feedback

---

*Last updated: 2026-01-07*
*Reference implementation: `/scripts/interface/templates/assessment_report.html`*
