# Visual Translator - Image Analysis & OCR

Automatically extract text from images and generate AI-powered descriptions using OCR and Claude's vision capabilities.

---

## Overview

The Visual Translator feature adds powerful image analysis to your knowledge base:

- **OCR (Optical Character Recognition)** - Extract text from images using Tesseract
- **Vision AI** - Generate detailed descriptions using Claude's vision API
- **Search Integration** - Search by image content and extracted text
- **Batch Processing** - Analyze all existing images at once
- **Auto-Processing** - Analyze new images automatically on import

---

## Setup

### 1. Install System Dependencies

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Install Python Dependencies

Already included in requirements.txt:
```bash
pip install anthropic pytesseract Pillow
```

### 3. Get Anthropic API Key

1. Sign up at https://console.anthropic.com
2. Create an API key
3. Add to your `.env` file:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

---

## Usage

### Web Interface

**Access Visual Translator:**
1. Navigate to http://localhost:5000
2. Click **🔍 Visual Translator** in the navigation bar
3. View all images with their analysis status

**Features:**
- **Grid View** - See all images with status badges
- **Filters** - All / Analyzed / Pending / With Text
- **Stats** - Total images, analyzed count, pending count
- **Analyze** - Click any image to analyze it

**Status Badges:**
- ✓ Analyzed - Image has been processed
- Pending - Awaiting analysis
- 📝 Text Detected - OCR found text in image

### Command Line Tools

#### 1. Analyze Single Image

```bash
python scripts/processors/visual_translator.py path/to/image.jpg
```

**Options:**
- `--skip-vision` - OCR only, skip Claude API (free)
- `--no-cache` - Force re-analysis

**Example:**
```bash
python scripts/processors/visual_translator.py knowledge_base/media/web_imports/abc123/image.jpg
```

#### 2. Batch Process Images

**Audit current status:**
```bash
python scripts/processors/batch_visual_translator.py --audit
```

**Test with first 5 images:**
```bash
python scripts/processors/batch_visual_translator.py --test --limit 5
```

**Process all images (OCR only, FREE):**
```bash
python scripts/processors/batch_visual_translator.py --all --ocr-only
```

**Process all with vision AI:**
```bash
python scripts/processors/batch_visual_translator.py --all --vision
```

**Process specific folder:**
```bash
python scripts/processors/batch_visual_translator.py --folder instagram
python scripts/processors/batch_visual_translator.py --folder web_imports
python scripts/processors/batch_visual_translator.py --folder attachments
```

**Reprocess everything:**
```bash
python scripts/processors/batch_visual_translator.py --all --reprocess
```

---

## How It Works

### Analysis Pipeline

1. **Image Input** - Image file from knowledge base
2. **OCR Processing** (pytesseract)
   - Extract text from image
   - Calculate confidence score
   - Detect language
3. **Vision Analysis** (Claude API)
   - Generate detailed description
   - Identify objects and scene type
   - Extract visual tags
   - Detect if text is visible
4. **Cache Results** - Save to avoid re-processing
5. **Update Markdown** - Add analysis to frontmatter
6. **Index** - Update search embeddings

### Data Storage

Analysis results are stored in the document's frontmatter:

```yaml
---
id: abc123
source: attachment
# ... existing fields ...

# OCR Results
ocr_text: "handwritten notes about digital identity"
ocr_confidence: 87.5
has_text: true

# Vision Analysis
vision_description: "A pencil sketch showing abstract geometric forms..."
vision_tags: ['sketch', 'handwriting', 'abstract', 'geometric']
vision_scene_type: 'sketch'
detected_objects: ['pencil sketch', 'geometric shapes', 'handwritten notes']

visual_analysis_date: '2026-01-02T12:00:00'
visual_analysis_status: 'success'
---
```

### Caching

- Results cached in `db/visual_cache/`
- Cache key: SHA256 hash of image file
- Default TTL: 90 days
- Prevents duplicate API calls
- Automatic cache invalidation on re-analysis

---

## Configuration

Edit `config/settings.json`:

```json
"visual_translator": {
  "enabled": true,
  "auto_analyze_on_import": true,
  "ocr_enabled": true,
  "vision_enabled": true,
  "claude_api_model": "claude-3-5-sonnet-20241022",
  "cache_analyses": true,
  "cache_duration_days": 90,
  "supported_formats": ["jpg", "jpeg", "png", "gif", "webp"],
  "ocr_languages": ["eng"],
  "batch_size": 10,
  "rate_limit_delay_seconds": 1.0,
  "max_image_dimension": 2048
}
```

**Key Settings:**
- `enabled` - Enable/disable visual translator
- `auto_analyze_on_import` - Process new images automatically
- `ocr_enabled` - Enable OCR (free)
- `vision_enabled` - Enable Claude vision (costs money)
- `cache_analyses` - Cache results to avoid re-processing
- `rate_limit_delay_seconds` - Delay between API calls

---

## API Reference

### Flask Endpoints

#### GET /visual-translator
Main visual translator panel

**Query Parameters:**
- `filter` - all | analyzed | pending | has_text

#### GET /visual-translator/image/<doc_id>
Detailed view of single image analysis

#### POST /api/analyze-image
Analyze a single image

**Request Body:**
```json
{
  "doc_id": "abc123",
  "skip_vision": false
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "ocr": { ... },
    "vision": { ... }
  }
}
```

#### GET /api/visual-stats
Get visual translator statistics

**Response:**
```json
{
  "total_images": 100,
  "analyzed": 45,
  "pending": 55,
  "with_text": 23
}
```

---

## Cost & Performance

### OCR (Tesseract)
- **Cost:** FREE (local processing)
- **Speed:** ~1-2 seconds per image
- **Quality:** Good for printed text, decent for handwriting

### Vision AI (Claude)
- **Cost:** ~$0.024 per image (1000 tokens @ $24/M tokens)
- **Speed:** ~2-5 seconds per image
- **Quality:** Excellent detailed descriptions

### Batch Processing Estimates
- 100 images (OCR only): FREE, ~5 minutes
- 100 images (with vision): ~$2.40, ~10 minutes
- 1000 images (with vision): ~$24, ~2 hours

### Cost Controls
- **OCR-only mode** - Set `vision_enabled: false`
- **Caching** - Prevents re-processing
- **Rate limiting** - Respects API limits
- **Manual triggers** - Only analyze when needed

---

## Troubleshooting

### "Tesseract not found" Error
**Solution:** Install Tesseract OCR
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
```

### "No API key provided" Error
**Solution:** Add API key to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Poor OCR Quality
**Solutions:**
1. Check image quality (resolution, contrast)
2. Try different OCR language: `--lang spa` for Spanish
3. Enable image preprocessing in config
4. Use vision API for handwriting

### API Rate Limit Errors
**Solution:** Increase delay in config:
```json
"rate_limit_delay_seconds": 2.0
```

### Images Not Showing in Grid
**Check:**
1. Media files exist in `knowledge_base/media/`
2. Markdown files have correct `id` field
3. Browser console for errors
4. Image file extensions are supported

---

## Search Integration

Once images are analyzed, you can search for:

**Search by OCR text:**
```
"handwritten notes about blockchain"
```

**Search by visual content:**
```
"geometric sketches"
"photos of architecture"
```

**Combined search:**
```
"images with text about art"
```

The OCR text and vision descriptions are automatically included in the search index.

**Re-index after batch processing:**
```bash
python scripts/processors/embeddings_generator.py --rebuild
```

---

## Examples

### Example 1: Process New Attachment

Upload a PDF with images → Images auto-extracted → Automatically analyzed → Searchable

### Example 2: Batch Analyze Existing Library

```bash
# Audit current state
python scripts/processors/batch_visual_translator.py --audit

# Output:
# Total images: 47
#   ✓ Analyzed: 0
#   ⏳ Pending: 47
#   ❌ No markdown: 0

# Process with OCR only (free)
python scripts/processors/batch_visual_translator.py --all --ocr-only

# Add vision descriptions
python scripts/processors/batch_visual_translator.py --all --vision

# Re-index for search
python scripts/processors/embeddings_generator.py --rebuild
```

### Example 3: Search for Images

```bash
python scripts/search/semantic_search.py "sketches with geometric patterns"
```

Results will include images where:
- Vision AI detected "geometric patterns"
- OCR extracted text mentioning "geometric"
- Markdown content references sketches

---

## Future Enhancements

Potential improvements:

- [ ] Multiple language OCR support
- [ ] Custom vision prompts per image type
- [ ] Image similarity search
- [ ] Auto-tagging based on visual content
- [ ] Bulk edit OCR results
- [ ] Export analysis reports
- [ ] Mobile upload + instant analysis
- [ ] Video frame extraction

---

## Technical Details

### Supported Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### Image Preprocessing
- Auto-resize to max 2048px dimension
- Convert to RGB/grayscale
- Contrast enhancement for OCR
- Maintains original files

### Error Handling
- Graceful failure on OCR errors
- Retry logic for API failures (3 attempts)
- Partial results if vision fails
- Detailed error logging

### Security
- Images processed locally
- API key never logged
- No external storage
- Cached data encrypted at rest

---

## Support

**Issues:**
- Check logs in terminal output
- Enable verbose mode: `--verbose`
- Test with single image first
- Verify API key and Tesseract installation

**Questions:**
- See main README.md
- Check configuration in settings.json
- Review Claude API documentation

---

## Credits

- **OCR:** Tesseract OCR engine
- **Vision AI:** Claude 3.5 Sonnet by Anthropic
- **Image Processing:** Pillow (PIL)
- **Framework:** Flask

---

Last updated: 2026-01-02
