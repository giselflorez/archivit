# Deduplication System - Implementation Complete

## What Was Built

An intelligent deduplication system that automatically merges duplicate queries across different sources while preserving all metadata and displaying multiple source type badges on a single query card.

## The Problem You Identified

> "I notice there are doubles in this database... some are doubled but one is part of the website and the other is the NFT. I'd like situations like this to be condensed into one query automatically but make sure all metadatas are combined and if they were scraped from different times just have both scrape metadatas attached... show it as the same query block square (if multiple articles or categories like (audio file)(web)(NFT) if it is all three they all could appear in the overview thumb if they are condensing into one query block"

## The Solution

### 1. **Intelligent Duplicate Detection**

**Multiple Detection Methods:**
- **Image Similarity** - Perceptual hashing (pHash) finds visually similar images
- **Blockchain Matching** - Same token ID + contract address
- **Title Matching** - Fuzzy matching (85% similarity)
- **URL Matching** - Same source URL

**Configurable Sensitivity:**
```bash
# Strict (only near-identical)
./deduplicate-kb --threshold 3

# Balanced (recommended)
./deduplicate-kb --threshold 5

# Lenient (catch more duplicates)
./deduplicate-kb --threshold 10
```

### 2. **Complete Metadata Preservation**

When merging duplicates, the system:
- ✅ Preserves ALL metadata from ALL sources
- ✅ Combines all tags (union)
- ✅ Links all images from different imports
- ✅ Stores complete scrape history with timestamps
- ✅ Keeps all URLs from different sources
- ✅ Chooses best title (longest/most detailed)
- ✅ Preserves blockchain data if available

**Example Merged Metadata:**
```yaml
---
id: abc123
sources: [web_import, blockchain, file_upload]
source_types: [web-scrape, blockchain, file-upload]
is_merged: true
merged_from: [def456, ghi789]
merge_date: 2026-01-04T20:00:00

scrape_history:
  - doc_id: abc123
    source: web_import
    scraped_at: 2026-01-02T10:00:00  ← First scrape
    url: http://superrare.com/artwork/...

  - doc_id: def456
    source: blockchain
    scraped_at: 2026-01-03T14:30:00  ← Second scrape
    platform: ethereum

  - doc_id: ghi789
    source: file_upload
    scraped_at: 2026-01-04T09:15:00  ← Third scrape

tags: [web_import, superrare, nft, blockchain, portfolio, giselx]  ← All tags combined
urls: [http://superrare.com/..., https://artist-website.com/...]  ← All URLs
images: [...12 images from all sources...]  ← All images linked
---
```

### 3. **Multi-Source Badge Display**

**Before (3 separate cards):**
```
┌────────────┐  ┌────────────┐  ┌────────────┐
│ 🌐 Web     │  │ ⛓️ NFT     │  │ 📁 Upload  │
│ Artwork    │  │ Artwork    │  │ Artwork    │
└────────────┘  └────────────┘  └────────────┘
```

**After (1 unified card with stacked badges):**
```
┌────────────┐
│ 🌐 Web     │  ← All badges on one card
│ ⛓️ NFT     │
│ 📁 Upload  │
│            │
│ Artwork    │
│ All data   │
└────────────┘
```

**Hover Interaction:**
- Normal: Badges slightly overlap (compact)
- Hover: Badges expand with full spacing
- Each badge maintains its color/glow

### 4. **Safe Dry-Run Mode**

Always preview before making changes:
```bash
./deduplicate-kb  # Shows what would be merged

Output:
==================================================================
DUPLICATE SUMMARY
==================================================================
Total duplicate groups: 15
Total documents to merge: 45
Documents to be archived: 30
==================================================================

1. Duplicate Group:
   Canonical: Luminous Portrait #5 (web_import)
   Duplicate:  Luminous Portrait #5 (blockchain)
   Duplicate:  LuminousPortrait5.jpg (file_upload)

...

DRY RUN - No changes made
Run with --execute to perform deduplication
==================================================================
```

## How to Use

### 1. Preview Duplicates

```bash
./deduplicate-kb
```

This shows what would be merged without making any changes.

### 2. Execute Deduplication

```bash
./deduplicate-kb --execute
```

This actually merges the duplicates.

### 3. View Results

Open Visual Translator:
```
http://localhost:5001/visual-translator
```

Look for cards with multiple stacked badges - those are merged queries!

### 4. Adjust Sensitivity

If you see too many or too few duplicates:
```bash
# More strict (fewer duplicates)
./deduplicate-kb --threshold 3

# More lenient (more duplicates)
./deduplicate-kb --threshold 10
```

## What Gets Merged

### Image-Based Duplicates

Images are considered duplicates if they're visually similar:
- **Hamming distance ≤ 5** (default threshold)
- Works even with different:
  - File formats (JPG vs PNG)
  - Resolutions
  - Compression levels
  - Minor edits

### Metadata-Based Duplicates

Documents are considered duplicates if they have:
- **Same blockchain token ID + contract**
- **Similar titles** (85%+ match)
- **Same source URL**

## Example Scenarios

### Scenario 1: NFT scraped from website + blockchain

**Before:**
- Card 1: 🌐 Web - "Artwork from SuperRare"
- Card 2: ⛓️ NFT - "Token #123 on Ethereum"

**After:**
- Single Card: 🌐 Web + ⛓️ NFT - "Artwork from SuperRare"
  - Has both SuperRare URL AND blockchain data
  - Both scrape timestamps preserved
  - Combined tags from both sources

### Scenario 2: Audio file + transcript + web article

**Before:**
- Card 1: 🎙️ Audio - "Interview.mp3"
- Card 2: ✍️ Text - "Interview transcript"
- Card 3: 🌐 Web - "Published interview"

**After:**
- Single Card: 🎙️ Audio + ✍️ Text + 🌐 Web - "Interview"
  - Links to audio file, transcript, and web article
  - All 3 scrape dates shown
  - All metadata combined

### Scenario 3: Same artwork from 2 different websites

**Before:**
- Card 1: 🌐 Web - "Portfolio piece" (artist website)
- Card 2: 🌐 Web - "Luminous Portrait" (SuperRare)

**After:**
- Single Card: 🌐 Web - "Luminous Portrait"
  - Both URLs linked
  - Better title chosen (SuperRare's detailed title)
  - Combined tags from both sites

## Files Created

### Core System
1. **`scripts/processors/deduplicator.py`** (800+ lines)
   - Image hashing with perceptual hashing (pHash)
   - Metadata matching with fuzzy logic
   - Intelligent merge algorithm
   - Scrape history preservation

2. **`deduplicate-kb`** - Simple command wrapper

### Visual Translator Updates
3. **`templates/visual_translator.html`**
   - Multi-badge container
   - Stacked badge CSS
   - Hover expansion effect

4. **`visual_browser.py`**
   - Reads `source_types` from merged documents
   - Passes multiple badges to template
   - Backward compatible with non-merged queries

### Documentation
5. **`docs/DEDUPLICATION_SYSTEM.md`** - Complete technical guide
6. **`DEDUPLICATION_COMPLETE.md`** (this file) - Implementation summary

## Technical Details

### Dependencies Installed
```bash
✓ Pillow (image processing)
✓ imagehash (perceptual hashing)
✓ PyYAML (YAML parsing)
✓ difflib (fuzzy matching) - built-in
```

### How Image Similarity Works

```python
# 1. Calculate perceptual hash
hash1 = pHash(image1)  # e.g., "a1b2c3d4e5f6..."
hash2 = pHash(image2)  # e.g., "a1b2c3d4f7g8..."

# 2. Calculate Hamming distance (how many bits differ)
distance = count_different_bits(hash1, hash2)  # e.g., 4

# 3. If distance ≤ threshold, they're duplicates
if distance <= 5:
    mark_as_duplicate()
```

**Distance Interpretation:**
- `0-2`: Near identical
- `3-5`: Very similar (default catches these)
- `6-10`: Somewhat similar
- `>10`: Different images

### Archive Location

Merged duplicates are moved to:
```
knowledge_base/archived/duplicates/20260104_200000/
├── web_def456_20260103.md
├── web_ghi789_20260102.md
└── ...
```

Can be recovered if needed, but won't appear in Visual Translator.

## Workflow Recommendation

### Daily Use
1. Import content normally (scrapers, uploads, etc.)
2. Don't worry about duplicates initially

### Weekly/Monthly Cleanup
1. Run dry run: `./deduplicate-kb`
2. Review duplicate groups
3. Adjust threshold if needed
4. Execute: `./deduplicate-kb --execute`
5. Restart server: `./start-server`
6. Verify in Visual Translator

### Before Presentations
Run deduplication to clean up database before showing to clients/collectors.

## Benefits

### For You
✅ **Clean database** - No duplicate clutter
✅ **Complete context** - All sources visible at once
✅ **Traceability** - Full scrape history preserved
✅ **Flexibility** - Adjustable sensitivity

### For Viewers
✅ **Clearer overview** - Multiple badges show complete picture
✅ **Less scrolling** - Fewer cards to browse
✅ **Better organization** - Related content grouped

### For Automation
✅ **Rich metadata** - All sources combined
✅ **Structured history** - Scrape timestamps for tracking
✅ **Unified queries** - Easier for AI agents to process

## Next Steps

### Try It Now

1. **Preview what would be merged:**
   ```bash
   ./deduplicate-kb
   ```

2. **If it looks good, execute:**
   ```bash
   ./deduplicate-kb --execute
   ```

3. **Restart server to see changes:**
   ```bash
   # Stop server (Ctrl+C if running)
   ./start-server
   ```

4. **Open Visual Translator:**
   ```
   http://localhost:5001/visual-translator
   ```

5. **Look for stacked badges!**
   - Hover over badges to see them expand
   - Click card to see full scrape history
   - Check metadata includes all sources

### If You Need Different Sensitivity

```bash
# Your database may have many duplicates from old scraper
# Start strict, then increase if needed

./deduplicate-kb --threshold 3  # Very strict
./deduplicate-kb --threshold 5  # Balanced (default)
./deduplicate-kb --threshold 8  # More lenient
```

## Summary

The deduplication system provides:

✅ **Automatic duplicate detection** via image similarity + metadata matching
✅ **Intelligent merging** that preserves ALL data from ALL sources
✅ **Multi-source visualization** with stacked badges on one card
✅ **Complete scrape history** showing all import timestamps
✅ **Configurable sensitivity** to match your needs
✅ **Safe dry-run mode** to preview before executing

**Result:** Same artwork appears once with all its sources (🌐 Web + ⛓️ NFT + 📁 Upload + 🎙️ Audio) stacked on a single card, with complete metadata and scrape history from all sources preserved.

---

**Created:** January 4, 2026
**Status:** Ready to Use
**Command:** `./deduplicate-kb`
