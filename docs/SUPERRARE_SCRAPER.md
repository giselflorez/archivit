# SuperRare NFT Collection Scraper

## Problem Solved

The original web scraper had issues with SuperRare profiles:

1. **Hallucinated metadata** - Scraped profile pictures of other users (e.g., "danseungvault") and included their usernames as metadata
2. **Incomplete collections** - Missed many NFTs due to lazy loading (SuperRare doesn't load all images at once)
3. **No context** - Couldn't distinguish between NFT artwork and UI elements like avatars, badges, icons

## Solution

The specialized SuperRare scraper (`superrare_scraper.py`) fixes these issues:

### 1. Lazy Loading Support
- Uses Selenium to scroll through the entire page
- Triggers lazy loading of all NFT images
- Ensures complete collection capture

### 2. Intelligent Image Filtering
- Identifies NFT artworks by URL patterns (IPFS, artwork CDN)
- Excludes profile pictures, avatars, badges, and UI elements
- Filters by image size and DOM structure

### 3. Accurate Metadata Extraction
- Extracts NFT titles from card structure
- Gets artwork URLs for each piece
- Captures descriptions and pricing when available
- Attributes everything to the correct artist

## Usage

### Basic Usage

```bash
source venv/bin/activate
python scripts/collectors/superrare_scraper.py http://superrare.com/founder
```

### What It Does

1. **Loads the SuperRare profile** using Selenium
2. **Scrolls down the page** up to 20 times to trigger lazy loading
3. **Extracts NFT cards** from the page structure
4. **Filters images** to only actual NFT artworks (ignores profile pics, avatars, etc.)
5. **Downloads each NFT artwork** with proper metadata
6. **Saves to knowledge base** in the same format as web imports

### Output Structure

```
knowledge_base/
├── processed/about_web_imports/
│   └── web_<doc_id>_<timestamp>.md       # Markdown with frontmatter
├── media/web_imports/<doc_id>/
│   ├── nft_1.jpg                          # NFT artwork 1
│   ├── nft_2.png                          # NFT artwork 2
│   └── ...                                # More NFT artworks
└── raw/web_imports/
    └── web_<doc_id>_<timestamp>.json     # Raw JSON data
```

## Image Filtering Logic

### ✅ Included (NFT Artworks)

Images are included if they match these patterns:

- **IPFS storage**: `ipfs://` or `ipfs.io/ipfs/`
- **SuperRare artwork CDN**: `storage.googleapis.com/sr_prod_artworks_bucket`
- **SuperRare IPFS gateway**: `superrare.myfilebase.com/ipfs/`
- **Proxied artwork**: `pixura.imgix.net/https%3a%2f%2fstorage.googleapis.com%2fsr_prod_artworks`

### ❌ Excluded (UI Elements)

Images are excluded if they match these patterns:

- **Profile pictures**: URL contains `avatar`, `profile`, `/profile-`
- **UI elements**: URL contains `logo`, `icon`, `badge`, `banner`
- **Vault names in alt text**: Alt text like "danseungvault" (short username patterns)
- **Avatar CSS classes**: Class names containing `avatar`, `profile`, `user-img`

## Example Output

### Markdown Frontmatter

```yaml
---
id: e0be96e0652f
source: web_import
type: superrare_collection
url: http://superrare.com/founder
domain: superrare.com
title: 'founder | SuperRare NFT Collection'
artist: founder
created_at: '2026-01-04T20:00:00.000000'
scraped_date: '2026-01-04'
has_images: true
image_count: 24
nft_count: 24
tags:
- web_import
- superrare
- nft
- blockchain
- founder
---
```

### Markdown Content

```markdown
# founder | SuperRare NFT Collection

**Source:** [superrare.com](http://superrare.com/founder)
**Imported:** January 04, 2026
**NFT Artworks:** 24

## Collection

This collection contains 24 NFT artworks by founder from their SuperRare profile.

---

## NFT Artworks

### 1. Artwork Title Here

![Artwork Title](../../knowledge_base/media/web_imports/e0be96e0652f/nft_1.jpg)

**Artist:** founder
**View on SuperRare:** [Artwork Title](http://superrare.com/artwork/...)

**Metadata:**
- Original URL: https://pixura.imgix.net/https%3A%2F%2Fstorage.googleapis.com%2F...
- File Size: 2,348,999 bytes
- Filename: nft_1.jpg
```

## Comparison: Old vs New Scraper

| Feature | Old Scraper | New SuperRare Scraper |
|---------|-------------|----------------------|
| **Lazy Loading** | ❌ No - misses most NFTs | ✅ Yes - scrolls to load all |
| **Image Filtering** | ❌ No - grabs everything | ✅ Yes - only NFT artworks |
| **Profile Picture Filtering** | ❌ No - includes "danseungvault" etc. | ✅ Yes - excludes avatars |
| **Metadata Accuracy** | ❌ Low - uses alt text blindly | ✅ High - extracts from card structure |
| **NFT Titles** | ❌ No - just "Image 1, Image 2" | ✅ Yes - actual artwork titles |
| **Artwork URLs** | ❌ No | ✅ Yes - links to each NFT page |
| **Collection Completeness** | ⚠️ Partial - ~10 items | ✅ Complete - all artworks |

## Requirements

```bash
pip install selenium webdriver-manager beautifulsoup4 requests pyyaml
```

## Browser Setup

The scraper works with:
- **Brave Browser** (preferred) - detected automatically at `/Applications/Brave Browser.app`
- **Chrome** - downloaded automatically via webdriver-manager

### Headless Mode

By default, the scraper runs with the browser visible (for debugging). To enable headless mode (background):

Edit `superrare_scraper.py` line ~43:
```python
options.add_argument('--headless')  # Uncomment this line
```

## Troubleshooting

### "No NFT cards found"

**Cause:** SuperRare changed their HTML structure

**Solution:**
1. Run with browser visible (comment out `--headless`)
2. Check what class names SuperRare uses for NFT cards
3. Update the `extract_nft_cards()` function with new patterns

### "Selenium not available"

**Cause:** Missing dependencies

**Solution:**
```bash
pip install selenium webdriver-manager
```

### "ChromeDriver not found"

**Cause:** webdriver-manager can't download ChromeDriver

**Solution:**
1. Ensure you have Chrome or Brave installed
2. Check internet connection (ChromeDriver downloads automatically)
3. Manually install ChromeDriver: `brew install chromedriver`

### Images still showing "danseungvault"

**Cause:** False positive - the actual NFT artwork has that in the alt text

**Solution:**
1. Check the image URL - if it contains `/sr_prod_artworks_bucket/`, it's a real NFT
2. The alt text may be user-provided and coincidentally contain that word
3. If it's truly a profile picture, add more filtering patterns

## Next Steps

After scraping:

1. **View in Visual Translator**: http://localhost:5001/visual-translator
2. **Analyze images** with AI vision (optional):
   ```bash
   python scripts/processors/vision_providers/local_provider.py <doc_id>
   ```
3. **Link to blockchain data** (if you have contract addresses):
   ```bash
   python scripts/collectors/nft_deep_scraper.py knowledge_base/processed/about_web_imports/web_<doc_id>_<timestamp>.md
   ```

## Future Enhancements

- [ ] Extract token IDs and contract addresses from artwork pages
- [ ] Automatic IPFS metadata fetching
- [ ] Support for other NFT platforms (Foundation, OpenSea, Objkt)
- [ ] Detect duplicate artworks across platforms
- [ ] Extract collection/series groupings
- [ ] Track minting dates and edition numbers

---

**Created:** January 4, 2026
**Status:** Production Ready
