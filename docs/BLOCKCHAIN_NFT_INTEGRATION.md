# Blockchain & IPFS NFT Integration

Automatically detect, extract, and link your NFT metadata and IPFS content to your knowledge base.

---

## Overview

The blockchain integration system:

1. **Detects NFT references** in scraped web pages
2. **Extracts blockchain metadata** (contract, token ID, edition)
3. **Fetches IPFS metadata** (JSON files with full attributes)
4. **Downloads original IPFS images** (full-resolution, not CDN thumbnails)
5. **Links NFTs** bidirectionally to web pages
6. **Enriches search** with blockchain attributes

---

## Features

### ✅ What It Does

**Automatic Detection:**
- NFT contract addresses
- Token IDs
- Edition numbers (e.g., 1/1, 5/100)
- IPFS hashes (CIDv0: Qm..., CIDv1: bafy...)
- IPFS URLs (ipfs://, ipfs.io, pinata, etc.)

**IPFS Content Fetching:**
- Tries multiple IPFS gateways for reliability
- Downloads **optimized preview images** (max 1200px, 85% quality)
- Fetches JSON metadata with attributes
- Keeps IPFS URIs for accessing originals anytime
- Saves 70-90% storage space vs. full resolution

**Metadata Enrichment:**
- NFT name and description
- Attributes (traits, properties)
- Original IPFS image (not compressed CDN version)
- Blockchain provenance
- Links back to source page

---

## How It Works

### Step 1: Web Scraping Detects NFTs

When you import a web page (like your 1stDibs profile), the system:

1. Scrapes the page content
2. Detects NFT-related patterns:
   - "Token ID: 249"
   - "Contract: 1stDibs.1"
   - "Edition: 1/1"
   - "Token Metadata: IPFS"

### Step 2: Blockchain Extractor Processes

The blockchain extractor (`blockchain_nft_extractor.py`):

1. Parses NFT metadata from document
2. Creates a "Blockchain NFTs" section
3. Links token IDs to contracts
4. Adds to frontmatter for search indexing

**Example Output:**

```markdown
## Blockchain NFTs

### NFT 1: Moments in Journey - Phoenix

**Token ID:** 249
**Contract:** 1stDibs.1
**Edition:** 1/1

**Description:** Photographic exploration of light and movement...

**Attributes:**
- **Medium:** Digital Photography
- **Blockchain:** Ethereum
- **Year:** 2022

**Preview Image:**

![Moments in Journey - Phoenix](../../knowledge_base/media/nft/b83efdaa502f/nft_249_preview.jpg)

*Optimized preview: 245,789 bytes (saved 90% vs. original 2,457,893 bytes)*

**Full Resolution (IPFS):** `ipfs://QmXyZ123...`

*Access original: [ipfs.io](https://ipfs.io/ipfs/QmXyZ123...) | [Pinata](https://gateway.pinata.cloud/ipfs/QmXyZ123...)*

---
```

### Step 3: Deep Scraping for IPFS URIs

If the initial scrape doesn't contain IPFS hashes, use the deep scraper:

```bash
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/nft_deep_scraper.py \
  knowledge_base/processed/about_web_imports/web_b83efdaa502f_20260103_010848.md
```

This will:
1. Find individual NFT page links
2. Scrape each NFT page for IPFS metadata URI
3. Fetch the full metadata from IPFS
4. Download original images
5. Update the document

---

## Usage

### Automatic Processing (Recommended)

**1. Import web page with NFTs:**

Via web interface:
```
http://localhost:5000
→ Click "+ Import"
→ Enter NFT profile URL (e.g., 1stDibs, OpenSea, Foundation)
→ Check "Extract Images"
→ Click "Import"
```

**2. Extract blockchain data:**

```bash
source venv/bin/activate

# Process specific document
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/blockchain_nft_extractor.py \
  knowledge_base/processed/about_web_imports/web_XXXXX.md

# Or process all web imports
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/blockchain_nft_extractor.py
```

**3. (Optional) Deep scrape for IPFS URIs:**

If IPFS metadata isn't automatically detected:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/nft_deep_scraper.py \
  knowledge_base/processed/about_web_imports/web_XXXXX.md
```

---

## Supported Platforms

### Currently Supported

- **1stDibs NFT** - Profile pages with multiple NFTs
- **Generic IPFS** - Any page with IPFS hashes or URLs
- **Direct IPFS links** - ipfs://, https://ipfs.io/ipfs/, etc.

### Planned Support

- [ ] OpenSea (via API)
- [ ] Foundation
- [ ] SuperRare
- [ ] Rarible
- [ ] Manifold
- [ ] Zora
- [ ] Direct blockchain querying (Etherscan, Alchemy)

---

## File Structure

**NFT Images Storage:**
```
knowledge_base/
  media/
    nft/
      {doc_id}/
        nft_249_preview.jpg     # Optimized preview (max 1200px, 85% quality)
        nft_247_preview.jpg     # Optimized preview
        nft_248_preview.png     # Optimized preview (PNG if transparency needed)
```

*Note: Full-resolution originals are accessible via IPFS URIs stored in metadata*

**Metadata in Markdown:**
```
knowledge_base/
  processed/
    about_web_imports/
      web_b83efdaa502f_20260103_010848.md
        → Frontmatter:
          - nft_count: 3
          - blockchain_linked: true
          - ipfs_content_downloaded: true
        → Body:
          - ## Blockchain NFTs section
```

---

## IPFS Gateways

The system tries multiple IPFS gateways in order:

1. **ipfs.io** - Official IPFS gateway
2. **Pinata** - Fast, reliable gateway
3. **Cloudflare IPFS** - CDN-backed gateway
4. **dweb.link** - Distributed web gateway

If one fails, it automatically tries the next until success.

---

## Search Integration

Once NFTs are extracted, you can search by:

**Blockchain attributes:**
```
"NFTs with edition 1/1"
"1stDibs contract tokens"
```

**NFT content:**
```
"Moments in Journey Phoenix"
"photographic expressionism NFTs"
```

**IPFS content:**
```
"original IPFS images"
"blockchain linked art"
```

---

## Examples

### Example 1: Your 1stDibs Profile

**URL:** https://www.1stdibs.com/nft/profile/GISELXFLOREZ/

**What was extracted:**
- ✓ 3 NFTs detected
- ✓ Token IDs: 249, 247, 248
- ✓ Contract: 1stDibs.1
- ✓ Editions: 1/1 for all

**To get full IPFS content:**
```bash
# Deep scrape for IPFS URIs
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/nft_deep_scraper.py \
  knowledge_base/processed/about_web_imports/web_b83efdaa502f_20260103_010848.md
```

This will:
1. Visit each NFT's individual page
2. Extract the IPFS metadata URI
3. Download the full JSON metadata from IPFS
4. Download optimized preview images (max 1200px, saves 70-90% space)
5. Store IPFS URIs for accessing full-resolution originals anytime
6. Add attributes to the document

### Example 2: Direct IPFS Link

If you have a direct IPFS link:

```
ipfs://QmXyZ123.../metadata.json
```

Or:

```
https://ipfs.io/ipfs/QmXyZ123.../metadata.json
```

The blockchain extractor will:
1. Auto-detect the IPFS hash
2. Fetch the metadata JSON
3. Download the image referenced in the JSON
4. Store everything locally

---

## Advanced Features

### Custom IPFS Gateway

Edit `scripts/processors/blockchain_nft_extractor.py`:

```python
IPFS_GATEWAYS = [
    "https://your-custom-gateway.com/ipfs/",
    "https://ipfs.io/ipfs/",
    # ... other gateways
]
```

### Blockchain API Integration (Planned)

Future versions will support querying blockchain directly:

```python
# Query Ethereum contract for token metadata URI
contract_address = "0x..."
token_id = 249
metadata_uri = get_token_uri(contract_address, token_id)
```

This will enable automatic metadata fetching without scraping.

---

## Troubleshooting

### "No IPFS metadata URI found"

**Causes:**
- Page uses JavaScript to load NFT data
- IPFS URI is in API response, not HTML
- Need to click through to individual NFT pages

**Solutions:**
1. Use deep scraper (requires Selenium)
2. Manually find IPFS URI and add to frontmatter
3. Query blockchain API directly

### "All IPFS gateways failed"

**Causes:**
- IPFS hash is not pinned
- Temporary gateway outages
- Network issues

**Solutions:**
1. Try again later (IPFS content may be propagating)
2. Use alternative gateway
3. Pin content yourself to IPFS

### Want higher resolution than preview?

**By design:**
- System downloads optimized previews (max 1200px) to save space
- Previews are 70-90% smaller than originals

**To access full resolution:**
1. Click the IPFS links in your document (ipfs.io or Pinata)
2. Original images available anytime from IPFS
3. If you need to store full-res locally, modify `max_dimension = 1200` in `blockchain_nft_extractor.py` (increase to 2400 or 4000)

---

## Future Enhancements

Planned features:

- [ ] **Blockchain querying** - Direct smart contract calls
- [ ] **Multi-chain support** - Ethereum, Polygon, Tezos, Solana
- [ ] **NFT metadata standards** - ERC-721, ERC-1155
- [ ] **Provenance tracking** - Sales history, previous owners
- [ ] **Rarity scoring** - Attribute rarity calculations
- [ ] **Collection grouping** - Auto-group NFTs by collection
- [ ] **Price tracking** - Historical price data
- [ ] **Wallet integration** - Auto-import from your wallet

---

## API Reference

### blockchain_nft_extractor.py

**Main Functions:**

```python
# Detect IPFS hashes in text
detect_ipfs_hashes(text: str) -> List[str]

# Detect IPFS URLs
detect_ipfs_urls(text: str) -> List[str]

# Detect NFT metadata blocks
detect_nft_metadata(text: str) -> List[Dict]

# Fetch content from IPFS
fetch_ipfs_content(ipfs_hash: str) -> Optional[bytes]

# Fetch JSON metadata
fetch_ipfs_json(ipfs_hash: str) -> Optional[Dict]

# Process NFT metadata
process_nft_metadata(nft_data: Dict, doc_id: str) -> Dict

# Update document with blockchain data
update_document_with_blockchain_data(md_file: Path, blockchain_data: Dict)
```

### nft_deep_scraper.py

**Main Functions:**

```python
# Find NFT links in profile page
find_nft_links_in_page(url: str, soup: BeautifulSoup) -> List[str]

# Scrape individual NFT page for IPFS URI
scrape_ipfs_metadata_uri_from_nft_page(url: str) -> Optional[str]

# Find IPFS links in HTML
find_ipfs_in_html(soup: BeautifulSoup, page_source: str) -> Optional[str]

# Enhance document with deep NFT data
enhance_document_with_deep_nft_data(md_file: Path)
```

---

## Storage Optimization

The system uses **smart previews** instead of full-resolution files:

**Preview Image Settings:**
- **Max dimension:** 1200px (configurable)
- **JPEG quality:** 85% (optimized for web)
- **PNG:** Used when transparency is needed
- **Space savings:** 70-90% vs. original

**Why Previews?**
- ✅ Fast loading in your knowledge base
- ✅ Reasonable resolution for browsing/viewing
- ✅ Keeps your database lean
- ✅ Full originals always accessible via IPFS
- ✅ No re-downloading when you need the original

**Example Savings:**
- Original NFT: 2.4 MB (4000x4000px)
- Preview: 245 KB (1200x1200px)
- **Saved: 90%**

**Accessing Originals:**
Every NFT includes clickable IPFS links:
- [ipfs.io](https://ipfs.io/ipfs/QmXyZ...)
- [Pinata](https://gateway.pinata.cloud/ipfs/QmXyZ...)

Open in browser to download full resolution anytime!

---

## Summary

The blockchain/IPFS integration transforms your knowledge base into a **Web3-native archive**:

✅ **Auto-detects** NFT metadata from web pages
✅ **Fetches optimized** IPFS previews and metadata
✅ **Links blockchain** provenance to your art
✅ **Enriches search** with NFT attributes
✅ **Preserves** IPFS URIs for full-resolution access
✅ **Decentralized** storage via IPFS
✅ **Space-efficient** with 70-90% storage savings

Your NFTs are now **permanently linked** to your personal knowledge vault!

---

**Last updated:** 2026-01-03
