# DOC-8 Source Cartography Release
## January 12, 2026

### Overview
Complete implementation of the DOC-8 Source Cartography interface with dual-view modes, comprehensive data bank, 4D analysis visualization, and video preview page.

---

### Files Included

| File | Description |
|------|-------------|
| `doc8_source_approval.html` | Main DOC-8 interface with all features |
| `in_testing_databank.html` | Video preview page for beta testers |
| `visual_browser.py` | Flask routes (modified) |
| `databank_preview.mov` | 100 Truths Inner World preview video |

---

### DOC-8 Features

#### Dual View Modes
- **Archivist View**: Professional paper texture, table-based layout
- **Artist View**: Constellation grid with glowing nodes, ambient effects

#### Four Tabs (Both Views)
1. **Sources** - Select verification sources (LOC, JSTOR, Smithsonian, etc.)
2. **Links** - Source URLs for manual verification
3. **Queries** - Complete data bank of all callback items
4. **Output** - 4D Analysis visualization (Archivist only)

#### Data Bank Features
- 20 demo items (documents, images, text, video, audio)
- Sortable by: Date, Name, Size, Reliability, Type, Source, Creator
- Trash functionality with confirmation dialog
- Reliability color spectrum:
  - Green (85%+): High reliability
  - Lime (70-84%): Good reliability
  - Orange (50-69%): Caution/Warning
  - Red (<50%): Low reliability

#### 4D Analysis Output Modules
1. **Temporal Flow** - Timeline with reliability as height
2. **Reliability Matrix** - Heatmap (Source vs Type)
3. **Source Network** - Constellation graph of sources
4. **4D Dimensional Scatter** - X:Time, Y:Reliability, Size:Volume, Color:Source
5. **Comparison Engine** - Side-by-side analysis with insights

#### Pattern Recognition Insight Panel
- Dynamic analysis based on compared items
- Tags: Reliability Match, Cross-Reference, Same Provenance, Type Match

---

### Routes Added

```python
/doc8                 # DOC-8 Source Cartography
/in-testing           # IN-TESTING DATABANK video preview
/databank-preview     # Alias for /in-testing
```

---

### Test Site URLs
- Local: http://localhost:5001
- Network: http://192.168.50.18:5001

---

### Data Accuracy Notes
All data bank items are **demonstration placeholders** representing what a real system would show. No real documents are referenced. Source reliability scores reflect institutional trust levels:
- Institutional (LOC, JSTOR, Smithsonian): 90-98%
- Archive (Internet Archive): 70-90%
- Verification (Quote Investigator): 75-90%
- Community (Wikiquote, Goodreads): 45-75%

---

### Copyright
ARCHIV-IT by Gisel Florez Studio Inc.
All Rights Reserved 2024-2026
