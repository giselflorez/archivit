# ARCHIV-IT by WEB3GISEL

> **🤖 AI AGENTS:** Read `CLAUDE.md` first - it contains mandatory agent instructions.

A **local-first, user-sovereign** data platform. Your data lives on YOUR device. You own your identity.

---

## Recent Achievements (2026-01-14)

### Quantum Containment V2 - Gaming-Resistant Access Control

| Achievement | Status | Details |
|-------------|--------|---------|
| **φ^(-0.5) Threshold Corrected** | ✅ FIXED | 0.854 → 0.786 (mathematical error) |
| **ACU Formula Redesigned** | ✅ COMPLETE | 4-layer equilibrium system prevents gaming |
| **Quantum Checkpoint System** | ✅ COMPLETE | Crash recovery with Fibonacci intervals |
| **Algorithm Proof Framework** | ✅ COMPLETE | Mathematical verification roadmap |

**The Math:**
```
OLD ACU: 2 perfect actions → FULL tier (broken)
NEW ACU: 4-layer verification → gaming-resistant

Layers:
1. Temporal Gate (21 actions minimum)
2. Fibonacci Memory (older actions weight more)
3. Variance Detector (catches oscillation)
4. Equilibrium of Light (positive/total ≥ 0.618)
```

**Verified Thresholds:**
```
φ^(-2)   = 0.236 (BLOCKED)
1-φ^(-1) = 0.382 (DEGRADED)
φ^(-1)   = 0.618 (FULL - THE PHI GATE)
φ^(-0.5) = 0.786 (SOVEREIGN) ← CORRECTED
```

> *"Ancient magic looking to build the future to see the past"*

See: `docs/ACHIEVEMENT_LOG_2026-01-14.md` for full details.

---

## Features

- **Perplexity Integration**: Collect information about you from Perplexity API
- **Twitter/X Archive**: Import and search your entire tweet history
- **Google Drive Automation**: Upload files (PDFs, images, text) via Drive for automatic processing
- **Semantic Search**: Natural language queries powered by sentence transformers
- **File Processing**: Extract text from PDFs and images (OCR), process text files
- **LLM-Ready Export**: Optimized markdown output for Claude conversations
- **Version Controlled**: Git-based backup and change tracking
- **Complete Privacy**: All data stored locally with offline embeddings

## Quick Start

### 1. Initial Setup

The system is already set up with:
- Python virtual environment in `venv/`
- All dependencies installed
- Directory structure created
- Git repository initialized

### 2. Run Initial Collection

Collect information about you from Perplexity:

```bash
source venv/bin/activate
python scripts/orchestration/collect_all.py --initial
```

This will:
1. Query Perplexity for: "gisel florez", "giselx", "giselxflorez", etc.
2. Save raw responses and clean markdown files
3. Build semantic search index
4. Commit to git

### 3. Search Your Knowledge Base

#### Interactive Search
```bash
python scripts/search/interactive_search.py
```

Then type queries like:
```
> what is giselx's work about?
> tell me about giselx art philosophy
> :view 1    # View full details of result #1
> :quit      # Exit
```

#### Command-Line Search
```bash
python scripts/search/semantic_search.py "your query here"
```

### 4. Export for Claude

Export search results as context for Claude conversations:

```bash
python scripts/search/export_context.py \
  --query "summarize giselx's creative philosophy" \
  --output context.md \
  --with-prompt
```

Then paste `context.md` into a Claude conversation!

## Google Drive Automation

Upload files from anywhere (computer, phone) to automatically add them to your knowledge base!

### Setup (One-time)

Follow the complete setup guide: **[docs/GOOGLE_DRIVE_SETUP.md](docs/GOOGLE_DRIVE_SETUP.md)**

Quick version:
1. Set up Google Cloud project and enable Drive API
2. Download OAuth credentials → `config/google_drive_credentials.json`
3. Run test: `python scripts/collectors/drive_collector.py --test`
4. Authenticate in browser

### Daily Usage

1. **Upload files to Google Drive:**
   - Open Google Drive on computer or phone
   - Navigate to "WEB3GISELAUTOMATE" folder
   - Upload PDFs, images (JPG/PNG), or text files

2. **Run automation:**
   ```bash
   source venv/bin/activate
   KMP_DUPLICATE_LIB_OK=TRUE python scripts/orchestration/drive_automation.py
   ```

3. **Search your files:**
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "content from my uploaded file"
   ```

### Supported Files

- **PDFs** - Full text extraction
- **Images** (JPG, PNG) - OCR text extraction (requires Tesseract)
- **Text files** (TXT, MD) - Direct content read
- **Documents** (DOC, DOCX) - Metadata only

### What Happens

1. Downloads files from Drive folder
2. Extracts text content (PDFs, images with OCR, text files)
3. Creates searchable knowledge entries
4. Moves processed files to "Processed" subfolder in Drive
5. Updates embeddings index
6. Commits to git

**Perfect for:** Notes, sketches, screenshots, PDFs, research papers, receipts, inspiration!

## Twitter/X Archive Processing

Add your entire tweet history to your searchable knowledge base!

### Step 1: Request Your Twitter Archive

1. Go to: https://twitter.com/settings/download_your_data
2. Click "Request archive"
3. Wait 24-48 hours for email notification
4. Download and extract the ZIP file

### Step 2: Process Your Tweets

```bash
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/twitter_collector.py path/to/twitter-archive/data/tweets.js
```

This will:
- Group tweets by month
- Extract hashtags and topics
- Create searchable markdown files
- Organize by subject (art, blockchain, photography, etc.)

### Step 3: Update Search Index

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/embeddings_generator.py --update
```

### Step 4: Search Your Tweets

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "moonlanguage project tweets"
```

**What gets indexed:**
- All tweet text
- Dates and timestamps
- Engagement metrics (likes, retweets)
- Hashtags and mentions
- Links shared

See: **[docs/TWITTER_EXPORT_GUIDE.md](docs/TWITTER_EXPORT_GUIDE.md)** for detailed instructions

## Instagram Archive Processing

Import your entire Instagram history with photos linked to captions!

### Step 1: Request Your Instagram Archive

1. Go to Instagram → Settings → Security → Download Data
2. Request archive (JSON format)
3. Wait for email (up to 48 hours)
4. Download and extract the ZIP file

### Step 2: Process Your Instagram Posts

```bash
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/instagram_collector.py ~/Downloads/instagram-archive/
```

This will:
- Import all posts with captions
- Copy photos to your knowledge base
- Link images with their text
- Extract hashtags and auto-categorize
- Make everything searchable

### Step 3: Update Search Index

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/embeddings_generator.py --update
```

### Step 4: Browse Visually

Launch the web interface:

```bash
python scripts/interface/visual_browser.py
```

Open: http://localhost:5000

**What gets indexed:**
- Post captions
- All photos (viewable in interface)
- Hashtags and mentions
- Post dates
- Visual context linked to text

See: **[docs/INSTAGRAM_EXPORT_GUIDE.md](docs/INSTAGRAM_EXPORT_GUIDE.md)** for detailed instructions

## Visual Web Interface

Browse all your content with a beautiful visual interface!

### Launch the Browser

```bash
python scripts/interface/visual_browser.py
```

Then open: **http://localhost:5000**

### Features:

- 🖼️ **Visual Grid View** - See all content with images
- 🔍 **Semantic Search** - Natural language search across everything
- 📂 **Filter by Source** - Instagram, Twitter, PDFs, Research
- 🏷️ **Tag Navigation** - Browse by topic
- 📱 **Responsive Design** - Works on desktop and mobile
- 🎨 **Image Galleries** - View Instagram photos inline

### Browse by Source:

- **All Content** - Everything in one place
- **Instagram** - Visual posts with photos
- **Twitter** - Tweet history
- **Research** - Perplexity queries
- **Files** - Uploaded PDFs and documents
- **Visual Only** - Filter to content with images

### Search Examples:

Visit http://localhost:5000/search and try:
- "moonlanguage project photos"
- "nft exhibition art"
- "manual 4x5 photography techniques"
- "woca women crypto art community"

## Usage Examples

### Add a New Query

```bash
python scripts/collectors/perplexity_collector.py \
  --query "giselx blockchain art 2026"
```

### Update Index with New Content

```bash
python scripts/processors/embeddings_generator.py --update
```

### Weekly/Monthly Updates

```bash
# Add new queries and update index
python scripts/orchestration/collect_all.py --queries \
  "giselx new work" \
  "giselxflorez recent projects"
```

### Search with Filters

```bash
# Search only within giselx subject
python scripts/search/semantic_search.py \
  --subject giselx \
  --limit 5 \
  "digital identity"
```

### View Index Statistics

```bash
python scripts/processors/embeddings_generator.py --stats
```

## Project Structure

```
+NEWPROJ/
├── config/
│   └── settings.json          # Configuration
├── scripts/
│   ├── collectors/
│   │   └── perplexity_collector.py
│   ├── processors/
│   │   ├── text_processor.py
│   │   └── embeddings_generator.py
│   ├── search/
│   │   ├── semantic_search.py
│   │   ├── export_context.py
│   │   └── interactive_search.py
│   └── orchestration/
│       └── collect_all.py
├── knowledge_base/
│   ├── raw/                   # Raw API responses (JSON)
│   └── processed/             # Clean markdown files
│       ├── about_gisel/
│       ├── about_giselx/
│       └── about_giselxflorez/
└── db/
    └── txtai_index/           # Semantic search index
```

## Configuration

Edit `config/settings.json` to customize:

```json
{
  "embedding": {
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "search": {
    "similarity_threshold": 0.7,
    "max_results": 10
  },
  "perplexity": {
    "default_queries": [
      "gisel florez",
      "giselx",
      "giselxflorez"
    ]
  },
  "export": {
    "max_tokens": 50000
  }
}
```

## Git Workflow

### Commit New Knowledge

```bash
git add knowledge_base/
git commit -m "Add new Perplexity queries about X"
```

### Push to GitHub

```bash
# First time
git remote add origin https://github.com/yourusername/personal-kb.git
git branch -M main
git push -u origin main

# Subsequent pushes
git push
```

### Pull on Another Machine

```bash
git clone https://github.com/yourusername/personal-kb.git
cd personal-kb
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Rebuild index from markdown files
python scripts/processors/embeddings_generator.py --rebuild
```

## Data Schema

Each knowledge entry is stored as markdown with YAML frontmatter:

```markdown
---
id: unique_id
source: perplexity
type: query_result
created_at: 2026-01-01T12:00:00Z
query: "original search query"
subject: giselx
tags: [art, digital_identity, philosophy]
urls: [source_url_1, source_url_2]
---

# Title

## Summary
...

## Content
...

## Key Points
- Point 1
- Point 2

## Sources
- [1](url)
```

## Advanced Usage

### Rebuild Index from Scratch

If something goes wrong with the index:

```bash
python scripts/processors/embeddings_generator.py --rebuild
```

### Export All Knowledge About a Subject

```bash
python scripts/search/export_context.py \
  --query "everything about giselx" \
  --limit 50 \
  --max-tokens 100000 \
  --output all_giselx_knowledge.md
```

### Batch Collection

```bash
python scripts/orchestration/collect_all.py --queries \
  "giselx art philosophy" \
  "giselxflorez digital identity" \
  "gisel florez blockchain" \
  "giselx creative process"
```

## Troubleshooting

### "Index not found" error

Run: `python scripts/processors/embeddings_generator.py --rebuild`

### Perplexity API errors

Check that your API key is set in `.env`:
```
PERPLEXITY_API_KEY=pplx-your-key-here
```

### Out of memory during indexing

Reduce batch size in `config/settings.json`:
```json
{
  "search": {
    "batch_size": 16
  }
}
```

## Technology Stack

- **Python 3.14** - Runtime environment
- **txtai** - Semantic search and embeddings (uses FAISS)
- **sentence-transformers** - Text embeddings (all-MiniLM-L6-v2)
- **Perplexity API** - Data source
- **Git** - Version control

## Privacy & Security

- All data stored locally in `knowledge_base/`
- Embeddings generated offline (no API calls for search)
- `.env` file gitignored (API keys never committed)
- Database excluded from git (`db/` in .gitignore)
- Can work completely offline after initial collection

## Next Steps

1. **Customize queries**: Edit `config/settings.json` default queries
2. **Set up GitHub**: Create repo and push for backup
3. **Schedule updates**: Set up cron/scheduled task for weekly collection
4. **Explore interactively**: Try different search queries
5. **Use with Claude**: Export context for deeper conversations

## License

Personal project - not licensed for distribution

---

Built with Claude Code
