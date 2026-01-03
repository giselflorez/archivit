# Web Scraping with Images & Metadata

Automatically download images from web pages with rich metadata extraction and AI-powered analysis.

---

## Overview

When you import a web page, the system now:

1. **Downloads all images** from the page
2. **Extracts HTML metadata** (alt text, captions, titles)
3. **Validates images** (checks content-type, skips icons/logos)
4. **Analyzes with OCR** (extracts text automatically)
5. **Describes with AI** (optional, using Claude vision)
6. **Stores rich metadata** in markdown files
7. **Makes content searchable** via embeddings

All images are automatically saved, analyzed, and linked to the web page document.

---

## How It Works

### Step 1: Import Web Page with Images

**Via Web Interface:**

1. Navigate to http://localhost:5000
2. Click **+ Import** button
3. Enter URL of web page
4. Check **Extract Images** checkbox
5. Click **Import**

**Example URLs to Try:**
- Article with photos: `https://example.com/article`
- Portfolio page: `https://artist.com/work`
- Blog post with diagrams: `https://tech-blog.com/post`

### Step 2: Automatic Image Processing

The system automatically:

**For Each Image:**
1. Downloads image to `knowledge_base/media/web_imports/{doc_id}/`
2. Extracts metadata from HTML:
   - Alt text (`<img alt="...">`)
   - Title attribute (`<img title="...">`)
   - Figure captions (`<figcaption>`)
3. Validates it's actually an image (checks content-type)
4. Saves with proper file extension (.jpg, .png, .webp, etc.)

**If Visual Translator is Enabled:**
5. Runs OCR to extract text from image
6. Generates AI description (if vision enabled)
7. Stores analysis in frontmatter

### Step 3: Rich Markdown Generation

Creates a markdown file with:

```markdown
---
id: abc123
source: web_import
url: https://example.com/article
title: Amazing Article
image_count: 5
images_with_text: 2
has_text: true
ocr_text: "Extracted text from all images..."
vision_description: "Photo of sunset | Diagram showing workflow"
visual_analysis_date: '2026-01-02T15:30:00'
---

# Amazing Article

## Content
[Article text here]

## Images

### Image 1: image_0.jpg

![Sunset over ocean](../../knowledge_base/media/web_imports/abc123/image_0.jpg)

**Metadata:**

- **Original URL:** https://example.com/photos/sunset.jpg
- **Alt Text:** Sunset over ocean
- **Title:** Beautiful sunset photo
- **Caption:** Captured at Golden Gate Bridge
- **File Size:** 245,678 bytes

**AI Description:**

> A vibrant sunset photograph showing orange and purple hues over the Pacific Ocean, with the Golden Gate Bridge silhouette visible in the foreground.

---

### Image 2: image_1.jpg

![Workflow diagram](../../knowledge_base/media/web_imports/abc123/image_1.jpg)

**Metadata:**

- **Original URL:** https://example.com/diagrams/workflow.png
- **Alt Text:** Workflow diagram
- **File Size:** 123,456 bytes

**Extracted Text (OCR):**

```
Step 1: Collect Data
Step 2: Process
Step 3: Analyze
Step 4: Visualize
```

**AI Description:**

> A technical diagram illustrating a four-step data processing workflow with arrows connecting each stage.

---

## Source
- Original URL: https://example.com/article
- Domain: example.com
- Scraped: 2026-01-02 15:30:00
```

---

## Configuration

### Enable/Disable Auto-Analysis

Edit `config/settings.json`:

```json
"visual_translator": {
  "enabled": true,
  "auto_analyze_on_import": true,    // Analyze images on import
  "ocr_enabled": true,                // Run OCR (FREE)
  "vision_enabled": false,            // Run Claude vision (costs money)
  ...
}
```

**Recommended Settings:**

**For Free Usage (OCR Only):**
```json
"ocr_enabled": true,
"vision_enabled": false
```
- Downloads images ✓
- Extracts metadata ✓
- Runs OCR (free) ✓
- Skips AI descriptions (saves cost)

**For Full Analysis:**
```json
"ocr_enabled": true,
"vision_enabled": true
```
- Everything above ✓
- AI-generated descriptions (~$0.024/image)

---

## What Gets Extracted

### Image Metadata (Always)

From HTML:
- **Alt Text** - `<img alt="description">`
- **Title** - `<img title="tooltip">`
- **Caption** - `<figcaption>` or nearby text
- **Original URL** - Where image was downloaded from
- **File Size** - In bytes
- **Content Type** - image/jpeg, image/png, etc.

### OCR Text (If Enabled)

Using Tesseract OCR:
- **Extracted Text** - All text found in image
- **Confidence Score** - OCR accuracy (0-100%)
- **Language** - Detected language
- **Has Text Flag** - Boolean indicator

### Vision Description (If Enabled)

Using Claude AI:
- **Narrative Description** - What the image shows
- **Scene Type** - photo, sketch, diagram, screenshot
- **Detected Objects** - List of main elements
- **Visual Tags** - Keywords for categorization
- **Text Visibility** - Whether text is visible

---

## Examples

### Example 1: Blog Post with Photos

**URL:** `https://travel-blog.com/paris-trip`

**Downloads:**
- 8 travel photos
- 1 map image
- 2 food photos

**Result:**
- 11 images saved to `knowledge_base/media/web_imports/{doc_id}/`
- Captions extracted from `<figcaption>` tags
- OCR extracts street signs, menu text
- Vision describes scenes: "Eiffel Tower at sunset", "French cafe exterior"
- All searchable: "photos of Paris cafes with menus"

### Example 2: Technical Article with Diagrams

**URL:** `https://dev-blog.com/system-architecture`

**Downloads:**
- 5 architecture diagrams
- 3 code screenshots

**Result:**
- OCR extracts:
  - Labels from diagrams
  - Code from screenshots
  - Component names
- Vision describes:
  - "System architecture diagram showing microservices"
  - "Code snippet in Python showing API endpoint"
- Searchable: "diagrams with database connections"

### Example 3: Portfolio Page

**URL:** `https://artist.com/gallery`

**Downloads:**
- 20 artwork images
- Artist statements in image captions

**Result:**
- Alt text: "Oil painting of abstract landscape"
- Captions: Artist's description of each piece
- Vision AI describes artistic style, colors, composition
- Searchable: "abstract paintings with geometric patterns"

---

## Advanced Features

### Intelligent Image Filtering

Automatically skips:
- Icons and logos (filename contains 'icon' or 'logo')
- Tiny images (data URIs < 1000 bytes)
- Non-image content (checks Content-Type header)
- Duplicate images (same URL)

### Smart Caption Detection

Looks for captions in:
- `<figcaption>` tags (HTML5 standard)
- `<caption>` tags (table captions)
- `<p>` tags inside `<figure>` or parent `<div>`

### Metadata Aggregation

In frontmatter:
- `image_count` - Total images downloaded
- `images_with_text` - Count of images with OCR text
- `has_text` - Boolean, any images have text
- `ocr_text` - Combined text from all images (first 1000 chars)
- `vision_description` - Pipe-separated descriptions

This makes the entire import searchable by image content!

---

## Search Integration

Once images are imported and analyzed, you can search by:

**Image Content:**
```
"diagrams showing database schema"
```

**Extracted Text:**
```
"images with text about API endpoints"
```

**Metadata:**
```
"photos with captions mentioning Paris"
```

**Combined:**
```
"technical diagrams with handwritten annotations"
```

The system indexes:
1. Page content (text)
2. Image metadata (alt, caption, title)
3. OCR text from images
4. Vision descriptions of images

**To Re-Index After Import:**
```bash
python scripts/processors/embeddings_generator.py --rebuild
```

---

## Troubleshooting

### "No images downloaded"

**Causes:**
- Page has no `<img>` tags
- Images are loaded via JavaScript (try manual download)
- All images filtered out (icons/logos)

**Solution:**
- Check page source for `<img>` tags
- Try different URL
- Disable filtering temporarily

### "Images show broken links"

**Check:**
1. Files exist in `knowledge_base/media/web_imports/{doc_id}/`
2. Flask server is running
3. `/media` route is working
4. Paths in markdown are relative

**Fix:**
```bash
# Verify files
ls knowledge_base/media/web_imports/{doc_id}/

# Restart server
python scripts/interface/visual_browser.py
```

### "OCR finds no text"

**Possible reasons:**
- Image has no text
- Text is artistic/stylized
- Image quality is poor
- Language not supported

**Solutions:**
- Enable vision AI for better text detection
- Try image preprocessing
- Use higher quality source images

### "Vision analysis fails"

**Check:**
1. API key is set in `.env`
2. `vision_enabled: true` in config
3. Internet connection
4. API quota not exceeded

---

## Performance & Costs

### Download Speed

- **10 images:** ~10-20 seconds
- **Bottleneck:** Network speed
- **Parallel downloads:** Not implemented (sequential)

### Analysis Speed

**OCR Only (Free):**
- ~1-2 seconds per image
- 10 images: ~20 seconds total

**With Vision AI:**
- ~2-5 seconds per image (API latency)
- 10 images: ~50 seconds total
- Rate limited to 1/second

### Costs

**Free Tier:**
- Image download: FREE
- Metadata extraction: FREE
- OCR: FREE

**Paid (Vision AI):**
- ~$0.024 per image
- 10 images: ~$0.24
- 100 images: ~$2.40

### Optimization Tips

1. **Use OCR-only mode** by default (free)
2. **Enable vision selectively** for important images
3. **Batch analyze later** using Visual Translator panel
4. **Cache results** to avoid re-processing

---

## API Reference

### Web Import Endpoint

**Route:** `/add-content` (POST)

**Form Data:**
- `url` - Web page URL
- `title` - Custom title (optional)
- `notes` - Your notes (optional)
- `source_type` - Default: 'web_import'
- `extract_images` - Checkbox, enable image download

**Backend Function:** `scrape_and_save_url()`

**Parameters:**
```python
def scrape_and_save_url(
    url: str,
    custom_title: Optional[str] = None,
    notes: str = '',
    source_type: str = 'web_import',
    extract_images: bool = True,
    manual_content: str = ''
) -> str:
    """
    Returns: doc_id of created document
    ```

---

## Integration with Other Features

### Google Drive Integration

Images from Google Drive PDFs are automatically:
- Extracted during PDF processing
- Saved to `knowledge_base/media/attachments/`
- Analyzed with Visual Translator (if enabled)

### Twitter/Instagram Integration

Social media posts with images:
- Images saved to `knowledge_base/media/{platform}/`
- Post caption becomes image metadata
- Combined with visual analysis

### Bulk Import

Import multiple URLs:

```python
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

for url in urls:
    scrape_and_save_url(url, extract_images=True)
```

---

## Best Practices

### 1. Source Attribution

Always:
- Keep original URL in metadata
- Preserve alt text and captions
- Credit image sources
- Respect copyright

### 2. Quality Control

- Review imported images in Visual Translator
- Check OCR accuracy
- Verify vision descriptions
- Edit metadata as needed

### 3. Cost Management

- Start with OCR-only
- Enable vision for key images
- Use batch analysis for control
- Monitor API usage

### 4. Organization

- Use meaningful import titles
- Add custom notes
- Tag appropriately
- Group related imports

---

## Future Enhancements

Planned features:

- [ ] Parallel image downloads
- [ ] Image deduplication
- [ ] Custom caption extraction patterns
- [ ] Image compression/optimization
- [ ] Video frame extraction
- [ ] Screenshot capture tool
- [ ] Browser extension for one-click import

---

## Examples of Great Sources

**Technical Documentation:**
- Architecture diagrams
- Code screenshots
- Workflow charts
- API documentation

**Research Papers:**
- Graphs and charts
- Experimental results
- Mathematical formulas
- Figure captions

**Art & Design:**
- Portfolio pieces
- Process photos
- Sketches and concepts
- Exhibition documentation

**Educational Content:**
- Infographics
- Tutorial screenshots
- Annotated images
- Visual guides

---

## Summary

The enhanced web scraping feature gives you:

✅ **Automatic image download** from any web page
✅ **Rich metadata extraction** (alt, caption, title)
✅ **OCR text extraction** (free, unlimited)
✅ **AI-powered descriptions** (optional, ~$0.024/image)
✅ **Full-text search** of image content
✅ **Beautiful markdown** with organized metadata
✅ **Visual Translator integration** for management

Import any web page with images and instantly build a searchable, analyzed visual knowledge base!

---

**Server:** http://localhost:5000
**Import:** Click "+ Import" button
**View Images:** Click "🔍 Visual Translator"

Last updated: 2026-01-02
