# Full Conversation Backup - 2026-01-03

## Session Context
Visual browser project with tag network visualization, document editing, and web scraping capabilities.

## Chronological Development

### 1. Tag Network Sidebar Visibility
**Issue:** Menu on left too high, not fully visible
**Fix:** Changed sidebar `top: 0` → `top: 100px`, `height: calc(100% - 100px)`

### 2. Minimal Hover/Click Interface
**Request:** Make interactions non-distracting
**Implementation:**
- Controls fade to 40% opacity
- Compact sidebar design
- Subtle hover (1.15x scale)
- Fast transitions (150ms)

### 3. Detail Sidebar Positioning
**Change:** Moved sidebar from right to left to avoid covering controls
**Added:** Thumbnail preview on hover with circular overlay

### 4. Image Color Extraction
**Feature:** Thumbnail ring border uses dominant color from image
**Implementation:**
```javascript
function extractDominantColor(imgElement) {
    colorExtractCanvas.width = imgElement.width || 100;
    colorExtractCanvas.height = imgElement.height || 100;
    colorExtractCtx.drawImage(imgElement, 0, 0, colorExtractCanvas.width, colorExtractCanvas.height);
    const imageData = colorExtractCtx.getImageData(0, 0, colorExtractCanvas.width, colorExtractCanvas.height);
    const data = imageData.data;

    // Color quantization and frequency counting
    const colorCounts = {};
    for (let i = 0; i < data.length; i += 4) {
        const r = Math.floor(data[i] / 32) * 32;
        const g = Math.floor(data[i + 1] / 32) * 32;
        const b = Math.floor(data[i + 2] / 32) * 32;
        const key = `${r},${g},${b}`;
        colorCounts[key] = (colorCounts[key] || 0) + 1;
    }

    let maxCount = 0;
    let dominantColor = 'rgb(100, 100, 100)';
    for (const color in colorCounts) {
        if (colorCounts[color] > maxCount) {
            maxCount = colorCounts[color];
            dominantColor = `rgb(${color})`;
        }
    }

    return dominantColor;
}
```

### 5. Media Path Fix
**Issue:** Thumbnails not loading, 404 errors
**Root Cause:** Wrong media URL paths
**Fix:**
- Changed `/media/{file}` → `/media/knowledge_base/media/{source}/{doc_id}/{file}`
- Backend updated to scan ALL media subdirectories

### 6. Auto-Fit Nodes on Load
**Feature:** Show all nodes in viewport on initial load
**Implementation:**
```javascript
function fitToScreen() {
    if (nodes.length === 0) return;

    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;

    nodes.forEach(d => {
        const r = d.radius || 5;
        minX = Math.min(minX, d.x - r);
        maxX = Math.max(maxX, d.x + r);
        minY = Math.min(minY, d.y - r);
        maxY = Math.max(maxY, d.y + r);
    });

    const graphWidth = maxX - minX;
    const graphHeight = maxY - minY;
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    const scale = Math.min(
        width / (graphWidth * 1.2),
        height / (graphHeight * 1.2),
        2
    );

    const translateX = width / 2 - centerX * scale;
    const translateY = height / 2 - centerY * scale;

    svg.transition().duration(1000).call(
        zoom.transform,
        d3.zoomIdentity.translate(translateX, translateY).scale(scale)
    );
}
```

### 7. Keyboard Shortcuts
**Added shortcuts with tooltips:**
- `0` - Reset view to fit all nodes
- `L` - Toggle labels on/off
- `H` - Reheat simulation
- `R` - Toggle recording mode
- `Esc` - Close sidebar

### 8. Document Image Management
**Features:**
- Select images with checkboxes
- Delete selected images
- Visual feedback (gold outline when selected)

**Backend endpoint:**
```python
@app.route('/api/document/<doc_id>/delete-images', methods=['POST'])
def delete_document_images(doc_id):
    data = request.get_json()
    filenames = data.get('filenames', [])

    media_base = Path("knowledge_base/media")
    deleted_count = 0

    for media_type_dir in media_base.iterdir():
        if not media_type_dir.is_dir():
            continue

        doc_media_dir = media_type_dir / doc_id
        if not doc_media_dir.exists():
            continue

        for filename in filenames:
            file_path = doc_media_dir / filename
            if file_path.exists():
                file_path.unlink()
                deleted_count += 1

    return jsonify({'success': True, 'deleted': deleted_count})
```

### 9. Document Editing
**Features:**
- Edit document content (markdown)
- Add/remove tags
- Save changes to frontmatter and body

**Backend endpoint:**
```python
@app.route('/api/document/<doc_id>/update', methods=['POST'])
def update_document(doc_id):
    data = request.get_json()
    new_body = data.get('body', '')
    new_tags = data.get('tags', [])

    # Find and update document
    for source_dir in Path("knowledge_base/processed").iterdir():
        if not source_dir.is_dir():
            continue

        for doc_path in source_dir.glob("*.md"):
            content = doc_path.read_text(encoding='utf-8')
            if '---' in content:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if frontmatter.get('id') == doc_id:
                        # Update frontmatter
                        frontmatter['tags'] = new_tags

                        # Write updated document
                        new_content = f"---\n{yaml.dump(frontmatter)}---\n{new_body}"
                        doc_path.write_text(new_content, encoding='utf-8')

                        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Document not found'})
```

### 10. Full Website Crawling
**Issue:** Single page scrape missing content from subpages
**Solution:** Implemented site crawler

**Implementation:**
```python
def crawl_website(base_url, max_pages=20):
    """Crawl a website and discover all internal pages"""
    visited = set()
    to_visit = {base_url}
    discovered_pages = []

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop()

        if current_url in visited:
            continue

        try:
            print(f"Crawling: {current_url}")
            visited.add(current_url)

            response = requests.get(current_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            })

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            discovered_pages.append({
                'url': current_url,
                'soup': soup
            })

            # Find all internal links
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Convert relative to absolute
                if href.startswith('/'):
                    href = f"{parsed_base.scheme}://{base_domain}{href}"
                elif not href.startswith('http'):
                    href = urljoin(current_url, href)

                # Only add if same domain
                parsed_href = urlparse(href)
                if parsed_href.netloc == base_domain:
                    # Remove fragments
                    clean_url = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
                    if parsed_href.query:
                        clean_url += f"?{parsed_href.query}"

                    if clean_url not in visited:
                        to_visit.add(clean_url)

        except Exception as e:
            print(f"Error crawling {current_url}: {e}")
            continue

    print(f"Discovered {len(discovered_pages)} pages")
    return discovered_pages
```

**Modified scrape function:**
```python
def scrape_and_save_url(url, title=None, manual_content=None, notes=None,
                        source_type='web_import', extract_images=True, crawl_site=False):

    if crawl_site:
        print(f"Starting full site crawl for: {url}")
        pages = crawl_website(url, max_pages=20)

        if not pages:
            # Fallback to single page
            response = requests.get(url, timeout=10, headers={...})
            soup = BeautifulSoup(response.text, 'html.parser')
            pages = [{'url': url, 'soup': soup}]

        # Aggregate content from all pages
        all_text = []
        all_images = []

        for page_data in pages:
            page_soup = page_data['soup']
            page_url = page_data['url']

            # Extract text
            for tag in page_soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()

            text = page_soup.get_text(separator='\n', strip=True)
            if text:
                all_text.append(f"\n## Content from: {page_url}\n\n{text}")

            # Extract images
            if extract_images:
                for img in page_soup.find_all('img'):
                    img_url = img.get('src', '')
                    if img_url:
                        absolute_img_url = urljoin(page_url, img_url)
                        all_images.append(absolute_img_url)

        content = '\n\n'.join(all_text)

        # Download images (limit 50 for site crawl)
        if extract_images:
            all_images = list(set(all_images))[:50]
            # Download logic...
    else:
        # Single page scrape logic...
```

## Files Modified

1. `/Users/onthego/+NEWPROJ/scripts/interface/templates/tag_cloud.html`
   - Sidebar positioning
   - Color extraction
   - Keyboard shortcuts
   - Auto-fit function

2. `/Users/onthego/+NEWPROJ/scripts/interface/templates/document.html`
   - Image selection checkboxes
   - Delete functionality
   - Edit mode implementation

3. `/Users/onthego/+NEWPROJ/scripts/interface/visual_browser.py`
   - Site crawling function
   - Delete images endpoint
   - Update document endpoint
   - Media path scanning

4. `/Users/onthego/+NEWPROJ/scripts/interface/templates/add_content.html`
   - Crawl site checkbox

## Current State

- Visual browser running on http://localhost:5001 (task b43ca59)
- Flask auto-reload enabled
- All features functional and tested
- Total documents: 16
- Visual documents: 1

## Environment

- Python 3.14
- Flask development server
- Working directory: /Users/onthego/+NEWPROJ
- Git repo: No
- Platform: macOS (Darwin 24.6.0)
