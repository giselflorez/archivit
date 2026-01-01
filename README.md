# Personal Knowledge Base

A local semantic search system for collecting and exploring information about gisel florez / giselx / giselxflorez from Perplexity API.

## Features

- **Perplexity Integration**: Collect information about you from Perplexity API
- **Semantic Search**: Natural language queries powered by sentence transformers
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
