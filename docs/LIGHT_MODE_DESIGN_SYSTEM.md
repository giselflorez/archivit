# ARCHIV-IT Light Mode Design System

## SECONDARY DESIGN SYSTEM

**For white-background contexts only. Read the PRIMARY system first:**
**`/docs/DARK_MODE_DESIGN_SYSTEM.md`**

---

## Reference Template
**Location:** `/docs/branding_preview.html`

## Source Reference
**Dark theme origin:** `/scripts/interface/templates/assessment_report.html`
**Dark theme docs:** `/docs/DARK_MODE_DESIGN_SYSTEM.md`

This light mode system is the chromatic inverse of the established dark theme, maintaining identical structural DNA while adapting for light backgrounds.

---

## Design Philosophy

### Core Principles
1. **Chromatic Inversion** — Not a separate design, but the dark theme reflected through a light lens
2. **Single Signature Animation** — One purposeful motion element (glow pulse), never decorative chaos
3. **Gold as Constant** — The accent gold (#d4a574) remains unchanged across light/dark modes
4. **Opacity as Hierarchy** — Text importance communicated through transparency, not just size
5. **Archival Authority** — Professional, quiet confidence; neither corporate nor whimsical

### What This Design Is NOT
- Not "accounting software" (no hard boxes, no sterile grids)
- Not "ethereal crypto" (no floating particles, ambient orbs, excessive animation)
- Not "marketing material" (no gradients for gradients' sake, no visual noise)

---

## CSS Variables (Light Mode)

```css
:root {
    /* Background layers */
    --bg-primary: #fafafa;        /* Page background - warm white */
    --bg-secondary: #ffffff;       /* Card/elevated surfaces */
    --bg-tertiary: #f5f5f4;        /* Nested elements, subtle depth */

    /* Text hierarchy - dark on light */
    --text-primary: #1a1a1f;                    /* Headlines, wordmark */
    --text-secondary: rgba(26, 26, 31, 0.7);   /* Body text */
    --text-muted: rgba(26, 26, 31, 0.45);      /* Captions, metadata */

    /* Borders */
    --border-color: rgba(0, 0, 0, 0.08);

    /* Accent - IDENTICAL to dark theme */
    --accent-gold: #d4a574;                     /* Solid gold */
    --accent-gold-soft: rgba(212, 165, 116, 0.6);   /* 60% gold */
    --accent-gold-glow: rgba(212, 165, 116, 0.3);   /* Glow effect */
}
```

### Color Relationships

| Element | Light Mode | Dark Mode Equivalent |
|---------|------------|---------------------|
| Background | #fafafa | #0a0a0f |
| Surface | #ffffff | #12121a |
| Nested | #f5f5f4 | #1a1a24 |
| Text Primary | #1a1a1f | #e8e6e3 |
| Text Secondary | rgba(26,26,31,0.7) | rgba(232,230,227,0.7) |
| Text Muted | rgba(26,26,31,0.45) | rgba(232,230,227,0.4) |
| Gold Accent | #d4a574 | #d4a574 (unchanged) |

---

## Typography

### Font Stack
```css
/* Wordmark, subtitles */
font-family: 'Cormorant Garamond', Georgia, serif;

/* Body, UI, taglines */
font-family: 'Inter', -apple-system, sans-serif;
```

### Type Scale

| Element | Font | Size | Weight | Letter-Spacing | Color |
|---------|------|------|--------|----------------|-------|
| Wordmark | Cormorant | 44px | 400 | 10px | --text-primary |
| Subtitle | Cormorant | 16px | 400 | 0.3px | --text-muted |
| Body | Inter | 15px | 400 | normal | --text-secondary |
| Tagline | Inter | 10px | 600 | 2px | --text-muted |

### Typography Rationale
- **Cormorant Garamond** for brand elements: Elegant, timeless, archival weight
- **Inter** for functional text: Clean, highly legible, professional
- **Letter-spacing on wordmark (10px)**: Creates breath, authority, permanence
- **Letter-spacing on tagline (2px)**: Uppercase legibility, modern contrast

---

## The Accent Line (Signature Element)

The gold accent line is the ONLY animated element. It serves as the visual bridge between the dark and light systems.

### Structure
```css
.accent-line {
    position: relative;
    height: 2px;
    margin-bottom: 16px;
    overflow: visible;
}

/* The visible line - gradient fade */
.accent-line::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg,
        var(--accent-gold) 0%,           /* Full gold at start */
        var(--accent-gold-soft) 60%,     /* Fades to 60% */
        transparent 100%                  /* Disappears at end */
    );
}

/* The glow - soft pulse */
.accent-line::after {
    content: '';
    position: absolute;
    left: 0;
    top: -4px;
    width: 40%;
    height: 10px;
    background: var(--accent-gold-glow);
    filter: blur(8px);
    animation: glowPulse 3s ease-in-out infinite;
}
```

### Animation Specification
```css
@keyframes glowPulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 0.8; }
}
```

**Duration:** 3 seconds
**Easing:** ease-in-out
**Behavior:** Infinite, subtle breathing
**Purpose:** Indicates life without demanding attention

---

## Spacing System

| Relationship | Value | Usage |
|--------------|-------|-------|
| Wordmark → Line | 12px | Tight coupling |
| Line → Subtitle | 16px | Breathing room |
| Subtitle → Description | 40px | Section break |
| Description → Tagline | 32px | Hierarchical pause |
| Left indent (description + tagline) | 20px | Alignment with accent |

---

## Description Block

```css
.description-block {
    padding-left: 20px;
    border-left: 2px solid var(--accent-gold-soft);
    margin-bottom: 32px;
}

.description-block p {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 400;
    line-height: 1.75;
    color: var(--text-secondary);
}
```

**Key Details:**
- Border uses `--accent-gold-soft` (60% opacity) — present but not aggressive
- Line-height 1.75 — generous breathing for readability
- No background color — floats on page surface
- Left padding creates visual indent aligned with border

---

## When to Use Light vs Dark

### Use Light Mode For:
- PDF exports and print materials
- External documentation
- Public-facing landing pages
- Branding previews
- White-label contexts
- Daytime/high-ambient-light viewing

### Use Dark Mode For:
- In-app interface (primary)
- Assessment reports
- Data visualization
- Extended work sessions
- Archive browsing
- Low-light environments

---

## Implementation Checklist

When creating new light-mode pages:

- [ ] Import both Cormorant Garamond (300,400,500) and Inter (300,400,500,600)
- [ ] Set background to #fafafa, not pure white
- [ ] Use rgba opacity values for text, not hex colors
- [ ] Gold accent (#d4a574) unchanged from dark theme
- [ ] Maximum ONE animated element per view
- [ ] Animation duration 3s minimum, ease-in-out
- [ ] Left-aligned content with 20px accent indent
- [ ] Wordmark letter-spacing: 10px
- [ ] Tagline: uppercase, 10px, weight 600, spacing 2px

---

## Full Template Reference

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCHIV-IT</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Cormorant+Garamond:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #fafafa;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f5f5f4;
            --text-primary: #1a1a1f;
            --text-secondary: rgba(26, 26, 31, 0.7);
            --text-muted: rgba(26, 26, 31, 0.45);
            --border-color: rgba(0, 0, 0, 0.08);
            --accent-gold: #d4a574;
            --accent-gold-soft: rgba(212, 165, 116, 0.6);
            --accent-gold-glow: rgba(212, 165, 116, 0.3);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 48px 24px;
        }

        .container { max-width: 600px; width: 100%; }

        .wordmark {
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 44px;
            font-weight: 400;
            letter-spacing: 10px;
            color: var(--text-primary);
            margin-bottom: 12px;
        }

        .accent-line {
            position: relative;
            height: 2px;
            margin-bottom: 16px;
            overflow: visible;
        }

        .accent-line::before {
            content: '';
            position: absolute;
            left: 0; top: 0;
            width: 100%; height: 2px;
            background: linear-gradient(90deg,
                var(--accent-gold) 0%,
                var(--accent-gold-soft) 60%,
                transparent 100%
            );
        }

        .accent-line::after {
            content: '';
            position: absolute;
            left: 0; top: -4px;
            width: 40%; height: 10px;
            background: var(--accent-gold-glow);
            filter: blur(8px);
            animation: glowPulse 3s ease-in-out infinite;
        }

        @keyframes glowPulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 0.8; }
        }

        .subtitle {
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 16px;
            font-weight: 400;
            color: var(--text-muted);
            letter-spacing: 0.3px;
            margin-bottom: 40px;
        }

        .description-block {
            padding-left: 20px;
            border-left: 2px solid var(--accent-gold-soft);
            margin-bottom: 32px;
        }

        .description-block p {
            font-family: 'Inter', sans-serif;
            font-size: 15px;
            font-weight: 400;
            line-height: 1.75;
            color: var(--text-secondary);
        }

        .tagline {
            font-family: 'Inter', sans-serif;
            font-size: 10px;
            font-weight: 600;
            color: var(--text-muted);
            letter-spacing: 2px;
            text-transform: uppercase;
            padding-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="wordmark">ARCHIV-IT</h1>
        <div class="accent-line"></div>
        <p class="subtitle">Personal Archive System for Artists</p>
        <div class="description-block">
            <p>[Content here]</p>
        </div>
        <p class="tagline">[Tagline here]</p>
    </div>
</body>
</html>
```

---

## Version History

| Date | Change |
|------|--------|
| 2026-01-08 | Initial light mode system established from branding exploration |

---

*This document is the authoritative reference for ARCHIV-IT light mode design. Future agents should consult this before creating any white-background materials.*
