# Archival Video Viewer Redesign
*For Master Architect Review*
*Created: 2026-01-16*

---

## Current Layout
```
┌─────────────────────────────────────────────────────────┐
│ HEADER: DOC-8 | NFT-8 | CRE-8 | SOCI-8 | Semantic | Arc │
├─────────────────────────────────────────────────────────┤
│ [Search Bar] [Paste URL] [Upload] [Paste Text] [Video]  │
├───────────────────────────┬─────────────────────────────┤
│                           │  SOURCE EXTRACTION          │
│     VIDEO PLAYER          │  ─────────────────────      │
│     (Play Button)         │  0:00 CARL JUNG             │
│                           │  "The meeting with oneself" │
│                           │  ─────────────────────      │
│                           │  0:15 JOHN FREEMAN          │
│                           │  "Do you believe..."        │
└───────────────────────────┴─────────────────────────────┘
```

---

## Proposed Layout (3-Column)
```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER: DOC-8 | NFT-8 | CRE-8 | SOCI-8 | Semantic | Archive    │
├─────────────────────────────────────────────────────────────────┤
│ [Search Bar] [Paste URL] [Upload File] [Paste Text] [Video]    │
├────────────┬──────────────────────────┬─────────────────────────┤
│ CATEGORIES │                          │  SOURCE EXTRACTION      │
│ ────────── │      VIDEO PLAYER        │  ───────────────────    │
│            │                          │                         │
│ ▼ VISUAL   │      [Play Button]       │  0:00 CARL JUNG         │
│   □ Jung   │                          │  ASSERTION: "The        │
│   □ Blake  │                          │  meeting with oneself"  │
│            │                          │  [Shadow] [Self]        │
│ ▼ MUSICIAN │                          │  Conf: 98%              │
│   □ Coltrane│                         │  ───────────────────    │
│   □ Mozart │                          │  0:32 CARL JUNG         │
│            │                          │  CLAIM: "I don't need   │
│ ▼ SPIRITUAL│                          │  to believe, I know."   │
│   □ Buddha │                          │  [Epistemology] [Gnosis]│
│   □ El Gorila                         │  Conf: 99%              │
│            │                          │                         │
│ ▼ WRITER   │                          │                         │
│ ▼ POET     │                          │                         │
│ ▼ MATH     │                          │                         │
│ ▼ DESIGNER │                          │                         │
│ ▼ PERFORMER│                          │                         │
│            │                          │                         │
│ ────────── │                          │                         │
│ [+ Add]    │  [Timeline Controls]     │  [Export] [Verify]      │
└────────────┴──────────────────────────┴─────────────────────────┘
```

---

## Left Sidebar Specifications

### Width
- **Desktop**: 220px fixed
- **Tablet**: Collapsible (icon-only mode)
- **Mobile**: Hidden, hamburger menu

### Categories (8 Domains)
```
VISUAL ARTIST    (90)
MUSICIAN         (10)
WRITER           (5)
POET             (2)
MATHEMATICIAN    (6)
SPIRITUALIST     (6)
DESIGNER         (0)
PERFORMER        (0)
```

### File List Behavior
- Collapsible accordions per category
- Checkbox selection for batch operations
- Search/filter within category
- Drag to reorder
- Right-click context menu

### Visual Style (Sacred Palette)
```css
.sidebar {
    width: 220px;
    background: var(--cosmic);      /* #0a0a12 */
    border-right: 1px solid var(--border);
}

.category-header {
    color: var(--gold);             /* #d4a574 */
    font-size: var(--fs-xs);        /* 11px */
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.file-item {
    color: var(--text-dim);         /* #9a9690 */
    font-size: var(--fs-sm);        /* 12px */
}

.file-item.selected {
    background: var(--gold-muted);  /* rgba(212,165,116,0.15) */
    color: var(--text);
}
```

---

## Interaction Flow

1. **Select Category** → Expands file list
2. **Select File(s)** → Loads into video player
3. **Play Video** → Source extraction begins
4. **Click Quote** → Jumps to timestamp
5. **Batch Select** → Enable multi-file operations

---

## Grid Update

Change from 2-column to 3-column:

```css
/* CURRENT */
.video-content {
    display: grid;
    grid-template-columns: 1.3fr 1fr;
}

/* PROPOSED */
.main-content {
    display: grid;
    grid-template-columns: 220px 1.3fr 1fr;
}

@media (max-width: 1200px) {
    .main-content {
        grid-template-columns: 60px 1fr 1fr;  /* Collapsed sidebar */
    }
}

@media (max-width: 900px) {
    .main-content {
        grid-template-columns: 1fr;  /* Stack vertically */
    }
}
```

---

## Data Source

Connect sidebar to `candidates.json`:
```javascript
async function loadCategories() {
    const response = await fetch('/api/artist-candidates');
    const data = await response.json();

    Object.entries(data.domains).forEach(([domain, info]) => {
        const artists = getAllArtists(info.candidates);
        renderCategory(domain, artists);
    });
}
```

---

## Implementation Priority

1. **Phase 1**: Static sidebar with categories
2. **Phase 2**: File selection & loading
3. **Phase 3**: Batch operations
4. **Phase 4**: Search/filter
5. **Phase 5**: Drag reorder

---

## Files to Modify

| File | Changes |
|------|---------|
| `doc8_archivist.html` | Add sidebar HTML, update grid |
| `visual_browser.py` | Add `/api/artist-candidates` endpoint |
| `candidates.json` | Data source (already exists) |

---

*Awaiting Master Architect approval to proceed.*
