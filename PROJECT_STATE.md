# ARCHIV-IT by WEB3GISEL - Project State & Quick Reference

> **🤖 NEW AGENTS: Read `AGENT_HANDOFF.md` FIRST - it's always current and compact (~100 lines).**
> **Then read `knowledge_base/training_data.json` for artist context.**
> **See `sessions/archive/` for detailed history if needed.**

## Agent Reminders
- **ASK THE USER FIRST** - Don't waste time searching for info the user can quickly provide. They're here. Ask directly.
- **Always remind user about pending tasks** (backups, commits, unfinished work) before ending session
- **Backup location**: `/Users/onthego/ARCHIVIT_01_backup_YYYYMMDD.tar.gz`
- **Last backup**: 2026-01-07 v3 (all fixes complete)
- **Design principle**: "Minimal words, intuitive design. No jargon. Icons > text."
- **Tier system**: SOLO (1) → ENTERPRISE (6) → WHITE GLOVE (unlimited, self-hosted API required - guided setup)
- **Bonuses**: ACU-METER Certified (+2, grants "CERTIFIED" status), Self-hosted API (+2)
- **Examples**: SOLO+ACU-METER=3, SOLO+ACU-METER+Self-hosted=5, ENTERPRISE+ACU-METER=8, ENTERPRISE+ACU-METER+Self-hosted=10
- **Naming**: ACU-METER (with hyphen) for the trust indicator, VERIFIED for the gold badge

## Current Status
- Visual browser running on http://localhost:5001
- Full website crawling implemented and active
- Document editing and image management functional
- Tag network visualization with color extraction working
- Organized dropdown sorting with grouping (Date, Title, Source, Tags)
- Quick tag network navigation from document cards

## Core Components

### 1. Visual Browser (`scripts/interface/visual_browser.py`)
Flask application serving the web interface.

**Key Routes:**
- `/` - Main document gallery
- `/tag-cloud` - Tag network visualization
- `/document/<doc_id>` - Document detail view
- `/add-content` - URL import form
- `/api/document/<doc_id>/delete-images` - Delete selected images
- `/api/document/<doc_id>/update` - Update document content

**Critical Functions:**
```python
def crawl_website(base_url, max_pages=20):
    """Discovers all internal pages on domain"""
    # Returns list of {'url': str, 'soup': BeautifulSoup}

def scrape_and_save_url(url, title=None, manual_content=None, notes=None,
                        source_type='web_import', extract_images=True, crawl_site=False):
    """Scrapes URL or entire site, saves to knowledge base"""
    # If crawl_site=True, aggregates content from all discovered pages
```

### 2. Tag Network Visualization (`scripts/interface/templates/tag_cloud.html`)

**Features:**
- D3.js force-directed graph
- Thumbnail preview on hover with color extraction
- Left sidebar with document details
- Auto-fit all nodes on load
- Keyboard shortcuts

**Keyboard Shortcuts:**
- `0` - Reset view
- `L` - Toggle labels
- `H` - Reheat simulation
- `R` - Toggle recording mode
- `Esc` - Close sidebar

**Key Functions:**
```javascript
function extractDominantColor(imgElement) {
    // Canvas-based color extraction for thumbnail rings
}

function fitToScreen() {
    // Auto-scales to show all nodes on initial load
}

function showDocumentDetails(d) {
    // Displays left sidebar with thumbnails and metadata
}
```

**Styling Notes:**
- Sidebar: `left: 0`, `top: 100px`, `height: calc(100% - 100px)`
- Controls fade to 40% opacity, 100% on hover
- Thumbnail rings use extracted image colors

### 3. Document View (`scripts/interface/templates/document.html`)

**Features:**
- Image selection with checkboxes
- Delete selected images
- Edit mode for content and tags
- Tag add/remove functionality

**Key Functions:**
```javascript
async function deleteSelectedImages() {
    // POST to /api/document/{id}/delete-images with filenames array
}

async function saveDocument() {
    // POST to /api/document/{id}/update with body and tags
}

function toggleEditMode() {
    // Switches between view and edit mode
}
```

### 4. Add Content Form (`scripts/interface/templates/add_content.html`)

**Form Fields:**
- `url` - URL to scrape
- `title` - Optional title override
- `manual_content` - Manual paste for difficult sites
- `notes` - User notes
- `source_type` - web_import | ai_conversation | article | reference
- `extract_images` - Checkbox for image extraction
- `crawl_site` - **NEW** Checkbox to crawl entire website

**Crawl Site Feature:**
When enabled, discovers up to 20 internal pages and aggregates all content and images.

## File Locations

### Templates
```
scripts/interface/templates/
├── base.html              # Base template
├── index.html             # Main gallery
├── tag_cloud.html         # Tag network viz
├── document.html          # Document detail + editing
├── add_content.html       # URL import form
└── tags.html              # Tag browsing
```

### Knowledge Base Structure
```
knowledge_base/
├── processed/
│   ├── perplexity/
│   ├── web_imports/
│   ├── ai_conversations/
│   └── articles/
└── media/
    ├── web_imports/{doc_id}/
    ├── perplexity/{doc_id}/
    └── attachments/{doc_id}/
```

### Media URL Pattern
- Frontend: `/media/knowledge_base/media/{source_type}/{doc_id}/{filename}`
- Backend serves: `knowledge_base/media/{source_type}/{doc_id}/{filename}`

## Key Technical Details

### Document Frontmatter Structure
```yaml
---
id: unique_hash
source: web_import | perplexity | attachment | ai_conversation
type: web_import | article | reference
created_at: ISO8601
title: string
url: string (if applicable)
media_count: int
tags: [array]
---
```

### Image Deletion Flow
1. User checks images in document view
2. Click "Delete Selected" button
3. POST to `/api/document/{id}/delete-images` with `{filenames: []}`
4. Backend deletes files from `knowledge_base/media/{type}/{id}/`
5. Frontend removes DOM elements

### Document Editing Flow
1. Click "Edit Document" button
2. Content becomes textarea, tags become editable
3. Modify content/tags
4. Click "Save Changes"
5. POST to `/api/document/{id}/update` with `{body: str, tags: []}`
6. Backend updates markdown file
7. Page reloads with changes

### Site Crawling Flow
1. User enables "Crawl entire website" checkbox
2. Backend calls `crawl_website(base_url, max_pages=20)`
3. Discovers internal links via BeautifulSoup
4. Extracts content from all pages
5. Aggregates text content
6. Downloads images from all pages (limit: 50)
7. Saves as single document with combined content

## Common Issues & Fixes

### Media Not Displaying
- Check path: must be `/media/knowledge_base/media/{source}/{id}/{file}`
- Backend scans ALL subdirs in `knowledge_base/media/`

### Sidebar Cut Off
- Must use `top: 100px` and `height: calc(100% - 100px)`

### No Images from Scraped Site
- Enable "Crawl entire website" to get images from subpages
- Images may be on different pages than landing page

## Running the Application

### Start Visual Browser
```bash
cd /Users/onthego/+NEWPROJ
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/interface/visual_browser.py
```

Access at: http://localhost:5001

### Background Mode (already running)
Server is running as task b43ca59 in background mode with auto-reload enabled.

## Dependencies

### Core
- Flask - Web framework
- txtai - Embeddings and search
- BeautifulSoup4 - Web scraping
- requests - HTTP client

### Frontend
- D3.js v7 - Force graph visualization
- Vanilla JavaScript - No frameworks

## Next Steps (from plan file)

Email automation system planned but not yet implemented:
- Gmail IMAP collection with subject filter "WEB3GISELAUTOMATE"
- PDF/image attachment processing
- Perplexity space scraping
- Daily automation via cron

See: `/Users/onthego/.claude/plans/golden-growing-hedgehog.md`

## Quick Commands

### Search
```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "query"
```

### Add Content via CLI
Use web interface at http://localhost:5001/add-content

### View Logs
```bash
tail -f /tmp/claude/-Users-onthego/tasks/b43ca59.output
```

## Product Ecosystem

```
╔═══════════════════════════════════════════════════════════════════╗
║                     PRODUCT ECOSYSTEM                             ║
║                                                                   ║
║   ARCHIV-IT                IT-R8                MOONLANGUAGE      ║
║   (Organize)              (Create)              (Experience)      ║
║   Paid Tiers              FREE                  968 Works         ║
║       │                      │                       │            ║
║       │    .archivit files   │                       │            ║
║       └──────────────────────►                       │            ║
║                              │                       │            ║
║              Bubbles imported for spatial design     │            ║
║                              │                       │            ║
║                              └───────────────────────►            ║
║                                                                   ║
║              Outputs can feed MOONLANGUAGE experiences            ║
╚═══════════════════════════════════════════════════════════════════╝
```

### IT-R8 Vision Summary (See: `docs/IT-R8_VISION_NOTES.md`)
- **White canvas** - Inverse of ARCHIV-IT dark aesthetic
- **Bubble datasets** - Mini datasets imported from ARCHIV-IT exports
- **Moldable algorithms** - Slider-based controls (spiral, helix, physics, gravity, flow)
- **Dimensional viewing** - Beyond 2D/3D/4D into spatial dimensions
- **Proprietary format** - Only imports .archivit files (ecosystem lock-in)
- **Ease of use** - As intuitive as Canva/Vercel/Cursor
- **"Making sculptures with trained data bubbles"**

### Legal/IP Documentation
Located at: `../archivit-beta/docs/legal/`
- IP_PROTECTION_ROADMAP.md - Trademark/copyright filing guide
- COMPREHENSIVE_IP_DOCUMENTATION.md - Full legal inventory
- IP_VISUAL_SUMMARY.md - Charts and diagrams

---

## Recent Updates

### 2026-01-03 - Domain-Based Footer with 10-Char Limit & Modal Spacing Fix
Improved domain display and full-size image modal spacing:
- **10-Character Domain Display** - Shows first 10 characters of domain instead of "MEDIA"
  - Example: "SUPERRARE." (truncated from superrare.com)
  - Example: "OPENSEA.IO" (fits within 10 chars)
  - Extracts domain from URL if domain field not set in frontmatter
  - Only shows "MEDIA" as absolute last fallback (no URL at all)
- **Enhanced Domain Extraction** - Improved fallback chain
  - Checks: url → source_url → domain field → URL parsing → "MEDIA"
  - Ensures domain captured even for older imports without domain field
  - Future scrapes will always have domain data
- **Full-Size Modal Spacing** - Fixed top spacing for proper display
  - Added 5vh top padding buffer for clear visibility
  - Reduced max image height to 70vh (from 80vh) to account for padding
  - Image now displays properly without cutting off at top
  - Close button and toolbar remain accessible
- **Future Enhancement Needed** - Duplicate Image Linking
  - TODO: Detect duplicate images across documents
  - TODO: Link duplicates together while preserving unique metadata
  - TODO: Show combined data in hover overlay for each instance

### 2026-01-03 - Circular Action Icons (SOURCE, IPFS, BLOCKCHAIN)
Redesigned clickable elements in Visual Translator hover overlay with clear visual distinction:
- **Circular Action Icons** - Only truly clickable elements are circles with pointer cursor
  - 🔗 SOURCE - Opens original platform (OpenSea, SuperRare, etc.) in new tab
  - 📌 IPFS - Opens content on IPFS gateway (ipfs.io) in new tab
  - ⛓️ BLOCKCHAIN - Opens mint transaction on blockchain explorer (Etherscan/Solscan/etc.)
  - 32px diameter circles with network-specific colors (ETH blue, BTC orange, SOL teal)
  - Scale animation on hover (1.15x) with glow effect
- **Square Information Badges** - Non-clickable metadata shown as squares with default cursor
  - 🏪 Platform names (OpenSea, SuperRare, 1stDibs)
  - 🎫 Token IDs for NFTs
  - No hover effects or cursor changes - purely informational
- **Clear Visual Language**
  - Circles = Actionable (external links)
  - Squares = Informational (metadata display)
  - Metadata grid has default cursor (no false clickability)
- **Network-Specific Explorer Links**
  - ETH → Etherscan transaction verification
  - BTC → Blockchain.com explorer
  - SOL → Solscan mint transaction
  - Each with proper network color coding

### 2026-01-03 - Semantic Filename Generation & Original Dimensions
Added intelligent filename generation and original image size detection in Visual Translator:
- **Semantic Filename Generation** - AI-powered meaningful filenames based on document context
  - Analyzes cognitive type, platform, blockchain data, title, tags, and domain
  - Example: `nft_superrare_token7_eth_mystical_waves.png`
  - Example: `web_nytimes_artificial_intelligence_revolution.jpg`
  - Falls back to extracted original filename from document content if available
  - Shown in gold highlight with current filename in tooltip
- **Original vs Local Dimensions** - Shows both downsampled and source image sizes
  - 📐 Local dimensions (saved/downsampled version in knowledge base)
  - 🖼️ Original dimensions (source size from platform/IPFS) - shown in warm accent
  - Automatically extracts from document metadata patterns
  - Helps identify high-quality originals for promotional use
- **Deep Context Analysis** - Filename generation uses semantic network intelligence:
  - **Blockchain NFTs:** Platform + Token ID + Network + Title
  - **Web Articles:** Domain + Title keywords
  - **Media Files:** Type + Most relevant tags
  - Filters out generic tags, uses only meaningful identifiers
  - Slugifies titles for clean filesystem compatibility
- **IPFS-Ready** - Designed to show original IPFS dimensions when available
  - Parses dimension patterns from scraped content
  - Prioritizes larger dimensions as "original"
  - Future: Direct IPFS metadata queries

### 2026-01-03 - Fixed Cognitive Type Classification for Web Documents
Fixed "unknown" category issue - web-scraped documents now properly classified as "WEB":
- **Source Field Priority** - Now uses document frontmatter source field instead of directory name
  - Fixes mismatch between "web_import" (frontmatter) and "web_imports" (directory)
  - Ensures accurate cognitive type classification
- **Improved Web Detection** - Enhanced classification logic
  - Any document with source `web_import`, `web`, or `article` → WEB
  - Attachments and Drive files with URLs → WEB
  - All scraped website content properly recognized
- **Cleaner Display** - Shows "WEB" instead of "WEB ARTICLE"
  - More concise badge in EXIF footer
  - Matches user mental model (came from web = WEB)
- **Default Fallback** - Unknown types default to "WEB" (most content is web-sourced)

### 2026-01-03 - Clickable Blockchain Network Badges
Enhanced blockchain network badges to link directly to mint transactions for verification:
- **ETH/BTC/SOL Badges Now Clickable** - Click to view mint transaction on blockchain explorer
  - ETH → Opens Etherscan link for transaction verification
  - BTC → Opens blockchain.com explorer link
  - SOL → Opens Solscan explorer link
- **Automatic Explorer URL Detection** - Extracts blockchain explorer links from:
  - Document URL (if from etherscan.io, solscan.io, etc.)
  - Document body content containing explorer links
  - Supports: Etherscan, Blockchain.com, Solscan, BSCScan, Polygonscan
- **Creator Address Verification** - Collectors can verify original creator address
  - View mint transaction details
  - Confirm NFT authenticity on blockchain
  - Check creator wallet address
  - Verify contract address and token ID
- **Visual Feedback** - Hover effects show badges are clickable
  - Slight lift animation on hover
  - Brightness increase for visibility
  - Tooltip shows which explorer will open
  - Links open in new tab without triggering image modal

### 2026-01-03 - Audio/Video Transcription with Local Whisper
Added local transcription feature to extract audio/video content as searchable text in knowledge base:
- **Local Whisper Model** - No cloud APIs, runs completely offline using OpenAI's open-source Whisper
  - Requires ffmpeg (install with `brew install ffmpeg`)
  - Whisper base model provides good balance of speed/accuracy
  - Automatic language detection
  - Supports all major audio/video formats
- **Visual Translator Media Support** - Now shows audio/video files alongside images
  - Video formats: MP4, MOV, AVI, MKV, WebM, M4V
  - Audio formats: MP3, WAV, M4A, AAC, OGG, FLAC
  - Click to play in modal with video/audio player
  - 🎙️ Transcribe button appears only for audio/video files
- **Automatic Transcript Documents** - Saved as new searchable knowledge base entries
  - Source: `transcript` type in `knowledge_base/processed/transcripts/`
  - Metadata includes word count, detected language, transcription model
  - Links back to original source document
  - Auto-tagged with language and content type
  - Embeddings automatically updated for semantic search
- **Use Cases:**
  - Import podcast episodes and make them searchable
  - Transcribe video interviews and presentations
  - Extract spoken content from media files
  - Build training data corpus from audio sources
  - Search across spoken content using semantic search

### 2026-01-03 - Visual Translator: Full-Size Viewer & Platform Links
Enhanced visual translator for promotional asset use with clickable links and full-size image modal:
- **Removed Irrelevant "Pending" Badges** - Cleaned up UI by removing status badges from image cards
- **Clickable Platform & IPFS Links** - Hover overlay now includes direct links
  - 🔗 Source - Opens original platform URL (OpenSea, 1stDibs, etc.) in new tab
  - 📌 IPFS - Opens content on IPFS gateway (ipfs.io) in new tab
  - Links styled with hover effects and color-coding
  - Click events don't trigger image modal (stopPropagation)
- **Full-Size Image Modal** - Click any image to view full resolution
  - Centered modal with dark backdrop and blur effect
  - Max 90vw/80vh sizing for large displays
  - Clean toolbar with action buttons
  - ESC key or click outside to close
- **Promotional Asset Tools** - Designed for marketing/design use
  - 💾 Download - Save image file directly to computer
  - 📋 Copy URL - Copy full image URL to clipboard
  - 📄 View Document - Navigate to source document page
- **Agent-Ready Design** - Optimized for future AI agent access
  - Semantic metadata exposed in hover overlays
  - Direct download functionality for automated workflows
  - Clean URL structure for programmatic image retrieval
  - Structured cognitive data for context-aware selection
- **EXIF-Style Photographer Info Panels** - Hover overlay with condensed metadata
  - **Badge System:**
    - ⛓️ ETH/BTC/SOL blockchain network badges (color-coded)
    - 🏪 Platform badges (OpenSea, 1stDibs, SuperRare, etc.)
    - 📌 IPFS badge if content on IPFS
  - **Metadata Grid:**
    - 📄 Filename
    - 📐 Dimensions (width×height)
    - 💾 File Size (KB/MB)
    - 🏷️ Tag Count
    - 🔗 Relationship Links
    - 🌐 Domain
    - 🎫 Token ID (for NFTs)
    - 💳 Blockchain Addresses Count
    - 📅 Original Creation Date
  - **Cognitive Type Footer** - Color-coded badge showing document type
  - **Vision Description** - AI analysis preview (if available)
  - **Photographer-Style Design:**
    - Monospace fonts for numerical data
    - Small, condensed information density
    - Icon symbols for all metadata categories
    - Dark overlay with blur backdrop
    - Professional EXIF panel aesthetic
- **Icon Symbol Reference:**
  ```
  📄 Filename (Semantic)   📐 Local Size     🖼️ Original Size  💾 File Size
  🏷️ Tags                 🔗 Links          🌐 Domain         🎫 Token
  💳 Addresses             📅 Date           ⛓️ Network        🏪 Platform
  📌 IPFS
  ```

### 2026-01-03 - Semantic Network with Blockchain Intelligence
Transformed tag network into cognitive data point cloud with blockchain network classification:
- **Blockchain Network Detection** - Automatically classifies NFTs by network (Ethereum, Bitcoin, Solana)
  - Pattern detection for ETH (0x...), BTC (1..., 3..., bc1...), and Solana addresses
  - Platform-based inference (OpenSea = Ethereum, Magic Eden = Solana)
  - Network-specific relationship edges connecting all ETH/BTC/Solana documents
- **Blockchain Address Extraction & Indexing**
  - Regex patterns extract wallet/contract addresses from document content
  - Address-based clustering (strongest connection at 98% strength)
  - New API endpoints for mint retrieval:
    - `/api/blockchain/address/<address>` - Get all NFTs from specific address
    - `/api/blockchain/network/<network>` - Get all NFTs on ETH/BTC/Solana
    - `/api/blockchain/addresses` - Index of all addresses in knowledge base
- **Original Date Temporal Proximity**
  - Prioritizes original creation dates (IPFS upload, HTML publication, mint date)
  - Falls back to import dates if original unavailable
  - Extracts dates from content patterns: "published:", "minted:", "uploaded:"
  - Links documents created within 7 days of each other by original date
- **Enhanced Relationship Types**
  - `blockchain_address` (98%) - Same wallet/contract
  - `ipfs_content` (95%) - Shared IPFS hashes
  - `blockchain_platform` (80%) - Same marketplace (OpenSea, 1stDibs, etc.)
  - `blockchain_network` (70%) - Same chain (ETH/BTC/SOL)
  - `domain_sibling` (60%) - Same domain
  - `semantic_similarity` (variable) - AI-powered content similarity
  - `temporal_proximity` (40%) - Created within 7 days (original or import)
- **Visual Enhancements**
  - Network badges in analysis panel (ETH blue, BTC orange, SOL teal)
  - Blockchain metadata display (platform, addresses, tokens, IPFS, dates)
  - Updated legend with network types and relationship strengths
- **Data Structure**
  - Nodes include `blockchain_network` in metadata
  - Blockchain metadata contains: `blockchain_addresses`, `blockchain_network`, `original_date`
  - All blockchain docs auto-classified and indexed for retrieval

### 2026-01-03 - Enhanced Sorting & Tag Network Navigation
Improved document organization and tag network accessibility:
- **Grouped dropdown menu** - Organized sorting options with clear categories
  - 📅 BY DATE: Newest First, Oldest First
  - 🔤 BY TITLE: A → Z, Z → A
  - 📁 BY SOURCE: Group by Source
  - 🏷️ BY TAGS: Most Tagged, Untagged First
- **Visual optgroup styling** - Gold headers with emojis for easy scanning
- **Tag network quick links** - Each document card shows "🕸️ Network" button
  - Click any tag to jump to that tag in the network
  - Click "🕸️ Network" to view document's tag connections
  - Hover effects with warm accent color
  - Tooltips indicate network navigation
- **Inline diff preview** - Drive sync shows differences before comparison
  - Format: "Δ 3d newer, 120KB larger" in metadata row
  - Maintains condensed horizontal layout
  - Color-coded with accent-warm
- **🚫 Ignore Forever** - Permanently exclude files from future sync scans
  - Replaces "Clear Selection" button in action bar
  - Stores ignored file IDs in `config/ignored_drive_files.json`
  - Confirmation dialog shows file names before ignoring
  - Smooth fade-out animation when removing from UI
  - Persists across sync sessions - ignored files never appear again

### 2026-01-03 - Drive Sync Click Comparison Popup
Redesigned similar files comparison with clickable hazard icon:
- **Fixed "NaN% Match" bug** - Handles missing similarity scores
- **Clickable hazard icon ⚠️** - Replaces non-functional "check" badge
- **Click-triggered popup** - Centered comparison modal appears on click
- **Dark backdrop with blur** - Focus on comparison, click outside to dismiss
- **Maintains design aesthetic** - Uses original color palette and styling
- **Bulk actions** - Check All / Uncheck All buttons per section
- **⚠️ Compare Selected button** - Review all selected files with navigation
  - Auto-scrolls to each file in list
  - Previous/Next buttons to navigate between comparisons
  - Shows "X of Y" counter
  - Keyboard shortcuts: ← → ↑ ↓ (navigate), Esc (close)
- **Visual data differences**:
  - Size: `↑ 700 KB larger` / `↓ 200 KB smaller` / `= same size`
  - Date: `↑ 45 days newer` / `↓ 10 days older` / `= same date`
  - Quoted diff box showing all key differences
- **Color-coded hazard icons**:
  - 🔴 Red (80%+) = High match, likely duplicate
  - 🟠 Orange (50-79%) = Medium match, similar
  - 🟢 Green (<50%) = Low match, different
  - ⚪ Gray = Unknown, review needed
- **Quick action buttons** - Skip or Import, auto-closes popup
- **Smart recommendations** - Context-aware guidance per match level
- **Clean list view** - Just shows hazard icon, click to see details

### 2026-01-03 - Google Drive Recursive Sync
- Added recursive subdirectory scanning
- Imported 4 files from WEB3AUTOMATE folder
- Fixed embeddings update in automation script
- Total documents: 24 (was 16)

### 2026-01-03 - Full Website Crawling
Added full website crawling for web scraper
