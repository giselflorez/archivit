# How to Export Your Instagram Archive

## Download Your Archive

1. **Open Instagram App** (or web at instagram.com)
   - Go to Settings → Security → Download Data
   - Or on web: Settings → Privacy and Security → Data Download

2. **Request Your Archive:**
   - Enter your email address
   - Select format: JSON (preferred)
   - Click "Request Download"
   - Instagram will email you when it's ready (up to 48 hours)

3. **Download the ZIP File:**
   - Check your email for the download link
   - Click the link and log in to Instagram
   - Download the ZIP file

4. **Extract the Archive:**
   - Unzip the file to a folder (e.g., `~/Downloads/instagram-archive/`)
   - Look for: `content/posts_1.json` (or just `posts_1.json`)

## What's Included

Your archive contains:
- All your posts with captions
- Photos and videos
- Comments
- Stories (if recent)
- Messages
- Profile information
- Account activity

## Process Your Archive

Once you have the archive:

```bash
source venv/bin/activate
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/instagram_collector.py ~/Downloads/instagram-archive/
```

This will:
- Extract all posts with captions
- Copy all images to your knowledge base
- Create searchable markdown files
- Link images with their captions
- Extract hashtags and auto-tag by topic

## Test with Limited Posts

If you have many posts, test with a small batch first:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/collectors/instagram_collector.py ~/Downloads/instagram-archive/ --limit 10
```

## Update Search Index

After processing:

```bash
KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/embeddings_generator.py --update
```

## View in Visual Interface

Launch the web browser:

```bash
python scripts/interface/visual_browser.py
```

Then open: http://localhost:5000

## Troubleshooting

### "posts_1.json not found"

The file might be in different locations depending on Instagram's archive format:
- `content/posts_1.json`
- `posts_1.json`
- `media/posts/posts_1.json`

Check your extracted archive structure and adjust the path accordingly.

### Images not copying

Make sure the media files are in the archive. Instagram usually includes them in:
- `media/posts/`
- `content/posts/`

### Large archive

If you have thousands of posts, processing might take a while. Use `--limit` to process in batches:

```bash
# Process first 100
python scripts/collectors/instagram_collector.py path/to/archive --limit 100

# Update index
python scripts/processors/embeddings_generator.py --update

# Process next batch, etc.
```

## Privacy Note

All data stays on your computer. Nothing is uploaded anywhere. Your Instagram archive is processed locally and added to your private knowledge base.
