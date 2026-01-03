# GiselX Knowledge Base - Project State & Quick Reference

## Current Status
- Visual browser running on http://localhost:5001
- Full website crawling implemented and active
- Document editing and image management functional
- Tag network visualization with color extraction working

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

## Recent Updates

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
