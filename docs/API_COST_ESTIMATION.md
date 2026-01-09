# API Cost Estimation Guide

## Overview

The ARCHIV-IT system now includes **automatic cost estimation** for all media processing operations. This helps you understand and control API usage costs before importing content.

## Supported Services & Pricing

### 1. **Vision Analysis** (Claude Haiku Vision API)
- **Service**: Image analysis, object detection, text extraction
- **Cost**: $0.003 per image
- **Use Cases**:
  - Analyzing NFT artwork
  - Extracting text from screenshots
  - Identifying objects in photos
  - Generating image descriptions

### 2. **Audio Transcription** (Whisper API)
- **Service**: Speech-to-text transcription
- **Cost**: $0.006 per minute
- **Use Cases**:
  - Transcribing podcasts
  - Converting voice memos to text
  - Processing audio interviews
  - Meeting recordings

### 3. **Video Frame Analysis** (Claude Vision on sampled frames)
- **Service**: Video content understanding
- **Cost**: $0.003 per frame (typically 10 frames per video)
- **Total**: ~$0.03 per video
- **Use Cases**:
  - Video artwork analysis
  - NFT video understanding
  - Content moderation
  - Scene detection

## How Cost Estimation Works

### Web Import

When you enter a URL in the **Add Content** form:

1. **Automatic Scan**: The system fetches the page and counts:
   - Number of images (excluding icons and tracking pixels)
   - Number of audio files
   - Number of videos

2. **Cost Calculation**:
   - Images: count × $0.003
   - Audio: estimated_minutes × $0.006
   - Video: frame_count × $0.003

3. **Preview Display**: A cost breakdown appears showing:
   ```
   💰 Estimated API Usage & Costs

   🖼️ Image Vision Analysis
   15 images × $0.0030          $0.05

   🎵 Audio Transcription
   2 files (~6 min) × $0.0060   $0.04

   💵 Total Estimated Cost
   17 media assets to process   $0.09
   ```

4. **Site Crawling Multiplier**: If "Crawl entire website" is enabled, costs are multiplied by estimated page count (default: 5 pages)

### File Upload (Coming Soon)

For direct file uploads, the system will:
- Detect file types (images, audio, video, documents)
- Estimate processing requirements
- Show per-file and total costs

## Cost Management Strategies

### 1. **Selective Processing**
- **Disable image extraction** if you only need text content
- **Turn off site crawling** to process single page only
- **Manual content paste** avoids image processing entirely

### 2. **Batch Optimization**
- Import multiple similar items together
- Use semantic search to avoid duplicate processing
- Archive high-value content first

### 3. **Free Alternatives**
- **Text-only imports**: No API costs
- **Manual transcription**: For short audio clips
- **Local OCR**: Use Tesseract (free, open-source) for basic text extraction

### 4. **Budget Alerts**
- **High cost warning**: Appears when estimated cost > $5.00
- **Review before import**: Double-check media count and options
- **Disable unused features**: Turn off vision analysis if not needed

## Pricing Details (Updated January 2025)

| Service | Provider | Model | Cost | Unit |
|---------|----------|-------|------|------|
| Vision Analysis | Anthropic | Claude 3.5 Haiku | $0.003 | per image |
| Audio Transcription | OpenAI | Whisper-1 | $0.006 | per minute |
| Video Analysis | Anthropic | Claude 3.5 Haiku | $0.003 | per frame |
| Text Embeddings | txtai | Local (SentenceTransformers) | **FREE** | unlimited |

## Examples

### Example 1: NFT Artist Portfolio
**Scenario**: Import SuperRare artist page with 20 NFTs
- Images: 20 × $0.003 = **$0.06**
- Total: **$0.06**

### Example 2: Podcast Episode
**Scenario**: Import podcast page with 1 audio file (45 minutes)
- Audio transcription: 45 min × $0.006 = **$0.27**
- Total: **$0.27**

### Example 3: Full Website Crawl
**Scenario**: Import blog with 5 pages, each containing 3 images
- Images: 15 × $0.003 = **$0.05**
- Site crawl enabled: $0.05 × 5 pages = **$0.25**
- Total: **$0.25**

### Example 4: Video NFT Collection
**Scenario**: Import page with 10 video NFTs
- Videos: 10 × 10 frames × $0.003 = **$0.30**
- Total: **$0.30**

### Example 5: Mixed Media Article
**Scenario**: Article with 5 images, 1 podcast (30 min), 2 videos
- Images: 5 × $0.003 = **$0.015**
- Audio: 30 × $0.006 = **$0.180**
- Videos: 2 × 10 × $0.003 = **$0.060**
- Total: **$0.26**

## API Usage Tips

### Maximizing Value

1. **Vision Analysis**:
   - Best for: NFT artwork, complex diagrams, screenshots with text
   - Skip for: Simple logos, profile pictures, decorative images

2. **Audio Transcription**:
   - Best for: Interviews, conversations, educational content
   - Skip for: Music, ambient sound, very short clips (<1 min)

3. **Video Processing**:
   - Best for: Video NFTs, animation artwork, tutorials
   - Skip for: Promotional videos, ads, background loops

### Cost-Free Features

These features use **local processing only** (no API costs):
- ✅ Text content extraction
- ✅ Semantic search and embeddings
- ✅ Markdown file storage
- ✅ Tag generation (basic)
- ✅ Relationship mapping
- ✅ Timeline organization
- ✅ Local OCR (Tesseract, if installed)

## Monitoring Usage

### Built-in Tracking
- Cost estimation appears automatically on URL blur
- Real-time updates when toggling options
- Warning alerts for high-cost imports

### Future Features (Planned)
- [ ] Monthly API cost dashboard
- [ ] Per-document cost tracking
- [ ] Budget limits and alerts
- [ ] Cost analytics and trends
- [ ] Batch processing queue with cost preview

## API Key Setup

To enable AI-powered features:

1. **Claude API** (Vision Analysis)
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. **Whisper API** (Audio Transcription)
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. Add to `.env` file:
   ```env
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-proj-...
   ```

**Note**: Features work with or without API keys:
- **With API keys**: Full vision and transcription capabilities
- **Without API keys**: Text-only processing (free, unlimited)

## Support

For questions about API costs or estimation accuracy:
- Check current pricing: [Anthropic Pricing](https://www.anthropic.com/pricing) | [OpenAI Pricing](https://openai.com/pricing)
- Report estimation issues: [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- Pricing updates are made monthly

---

**Last Updated**: January 3, 2026
**Pricing Source**: Anthropic API Pricing (Claude 3.5 Haiku), OpenAI Whisper API
