#!/usr/bin/env python3
"""
Instagram Collector - Process Instagram archive and add to knowledge base
"""
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
import yaml
import argparse

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def generate_id(post_timestamp, username):
    """Generate a unique ID based on post metadata"""
    content = f"{username}_{post_timestamp}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def parse_instagram_archive(archive_dir):
    """
    Parse Instagram archive

    Args:
        archive_dir: Path to extracted Instagram archive directory

    Returns:
        List of post dictionaries with media
    """
    archive_path = Path(archive_dir)

    # Instagram archive locations
    posts_file = archive_path / "content" / "posts_1.json"
    if not posts_file.exists():
        # Try alternative location
        posts_file = archive_path / "posts_1.json"

    if not posts_file.exists():
        raise FileNotFoundError(
            f"Could not find posts_1.json in {archive_path}\n"
            "Expected location: content/posts_1.json"
        )

    print(f"Reading Instagram archive: {posts_file}")

    with open(posts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    posts = []

    # Instagram archive format varies, try different structures
    if isinstance(data, list):
        posts = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ['posts', 'media', 'content']:
            if key in data:
                posts = data[key]
                break

    print(f"Found {len(posts)} Instagram posts")
    return posts, archive_path

def extract_tags_from_caption(caption):
    """Extract relevant tags from Instagram caption"""
    tags = ["instagram", "social_media"]

    caption_lower = caption.lower()

    tag_keywords = {
        'art': ['art', 'artwork', 'creative', 'artist', 'exhibition'],
        'blockchain': ['blockchain', 'crypto', 'nft', 'web3', 'eth', 'ethereum'],
        'digital_identity': ['identity', 'digital', 'online', 'persona'],
        'philosophy': ['philosophy', 'thought', 'concept', 'idea', 'consciousness'],
        'technology': ['tech', 'technology', 'digital', 'innovation'],
        'photography': ['photo', 'photography', 'camera', 'lens', 'capture', 'shoot', '4x5'],
        'community': ['community', 'together', 'collective', 'woca', 'women'],
        'moonlanguage': ['moon', 'moonlanguage', 'lunar'],
        'light': ['light', 'waves', 'transmissions', 'lightform']
    }

    for tag, keywords in tag_keywords.items():
        if any(keyword in caption_lower for keyword in keywords):
            tags.append(tag)

    # Extract hashtags
    import re
    hashtags = re.findall(r'#(\w+)', caption)
    tags.extend([h.lower() for h in hashtags[:10]])

    return list(set(tags))

def determine_subject(caption):
    """Determine subject category from caption content"""
    caption_lower = caption.lower()

    if "giselxflorez" in caption_lower or "giselxtez" in caption_lower:
        return "giselxflorez"
    elif "giselx" in caption_lower:
        return "giselx"
    elif "gisel florez" in caption_lower or "giselflorez" in caption_lower:
        return "gisel_florez"
    else:
        return "instagram_general"

def copy_media_files(post, archive_path, doc_id):
    """Copy Instagram media files to knowledge base"""
    media_dir = Path("knowledge_base/media/instagram") / doc_id
    media_dir.mkdir(parents=True, exist_ok=True)

    saved_media = []

    # Get media from post
    media_list = post.get('media', [])
    if not isinstance(media_list, list):
        media_list = [media_list]

    for idx, media_item in enumerate(media_list):
        # Try different possible keys for media path
        media_uri = media_item.get('uri', media_item.get('path', ''))

        if not media_uri:
            continue

        # Find the actual file in archive
        source_file = archive_path / media_uri

        if not source_file.exists():
            # Try removing leading path components
            source_file = archive_path / Path(media_uri).name

        if source_file.exists():
            # Copy to media directory
            dest_file = media_dir / source_file.name
            shutil.copy2(source_file, dest_file)

            saved_media.append({
                'filename': source_file.name,
                'path': str(dest_file),
                'size': dest_file.stat().st_size,
                'type': 'image' if source_file.suffix.lower() in ['.jpg', '.jpeg', '.png'] else 'video'
            })

            print(f"    Copied media: {source_file.name}")

    return saved_media

def create_markdown_for_post(post, username, archive_path):
    """Create markdown document for an Instagram post"""
    now = datetime.now()

    # Extract post data
    caption = ""
    media_items = post.get('media', [])

    # Try to get caption from different possible locations
    if 'title' in post:
        caption = post['title']
    elif 'caption' in post:
        caption = post['caption']
    elif media_items and isinstance(media_items, list) and len(media_items) > 0:
        caption = media_items[0].get('title', '')

    # Get timestamp
    timestamp = post.get('creation_timestamp', post.get('taken_at', 0))
    if timestamp:
        post_date = datetime.fromtimestamp(timestamp)
        date_str = post_date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        post_date = datetime.now()
        date_str = "Unknown"

    # Generate doc ID
    doc_id = generate_id(str(timestamp), username)

    # Extract tags
    tags = extract_tags_from_caption(caption)
    tags.append('instagram')
    tags.append('visual')

    # Determine subject
    subject_category = determine_subject(caption)

    # Copy media files
    saved_media = copy_media_files(post, archive_path, doc_id)

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'instagram',
        'type': 'instagram_post',
        'created_at': now.isoformat(),
        'post_date': date_str,
        'username': username,
        'media_count': len(saved_media),
        'has_images': any(m['type'] == 'image' for m in saved_media),
        'has_video': any(m['type'] == 'video' for m in saved_media),
        'tags': sorted(list(set(tags)))
    }

    # Create markdown body
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# Instagram Post: @{username}

**Date:** {date_str}

## Caption

{caption if caption else '*No caption*'}

## Media

"""

    # Add media references
    if saved_media:
        for idx, media in enumerate(saved_media, 1):
            md_content += f"### Media {idx}: {media['filename']}\n"
            md_content += f"- **Type:** {media['type']}\n"
            md_content += f"- **Size:** {media['size']:,} bytes\n"
            md_content += f"- **Path:** `{media['path']}`\n\n"

            # Add image reference for markdown viewers
            if media['type'] == 'image':
                # Relative path from knowledge base root
                rel_path = Path(media['path']).relative_to(Path.cwd())
                md_content += f"![{media['filename']}](../../{rel_path})\n\n"
    else:
        md_content += "*No media files found*\n\n"

    md_content += f"""## Related Topics
- Search for more about: {subject_category}
- Visual content from Instagram
"""

    return md_content, doc_id, subject_category, saved_media

def save_instagram_content(markdown_content, raw_data, subject_category, doc_id):
    """Save Instagram content as knowledge base entry"""
    # Save raw data
    raw_dir = Path("knowledge_base/raw/instagram")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"instagram_{doc_id}_{timestamp}.json"
    raw_filepath = raw_dir / raw_filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

    # Save processed markdown
    processed_dir = Path(f"knowledge_base/processed/about_{subject_category}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    md_filename = f"instagram_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return str(md_filepath)

def process_instagram_archive(archive_dir, username="giselxflorez", limit=None):
    """Main processing function"""
    print(f"\n{'='*60}")
    print(f"Processing Instagram Archive: @{username}")
    print(f"{'='*60}\n")

    # Parse posts
    posts, archive_path = parse_instagram_archive(archive_dir)

    # Limit if specified
    if limit:
        posts = posts[:limit]
        print(f"Processing first {limit} posts (limited)")

    processed_docs = []

    # Process each post
    for idx, post in enumerate(posts, 1):
        try:
            print(f"\n{'='*60}")
            print(f"Processing post {idx}/{len(posts)}")
            print(f"{'='*60}")

            # Create markdown
            markdown, doc_id, subject_category, saved_media = create_markdown_for_post(
                post,
                username,
                archive_path
            )

            # Save
            filepath = save_instagram_content(
                markdown,
                post,
                subject_category,
                doc_id
            )

            processed_docs.append({
                'id': doc_id,
                'filepath': filepath,
                'media_count': len(saved_media)
            })

            print(f"  ✓ Processed post (ID: {doc_id})")
            print(f"  ✓ Media files: {len(saved_media)}")

        except Exception as e:
            print(f"  ✗ Error processing post: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*60}")
    print(f"Instagram Archive Processing Complete")
    print(f"{'='*60}")
    print(f"Total posts processed: {len(processed_docs)}")
    total_media = sum(d['media_count'] for d in processed_docs)
    print(f"Total media files: {total_media}")
    print(f"{'='*60}\n")

    return processed_docs

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Process Instagram archive and add to knowledge base"
    )
    parser.add_argument(
        'archive_dir',
        help='Path to extracted Instagram archive directory'
    )
    parser.add_argument(
        '--username',
        default='giselxflorez',
        help='Instagram username (default: giselxflorez)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of posts to process (for testing)'
    )

    args = parser.parse_args()

    archive_dir = Path(args.archive_dir)

    if not archive_dir.exists():
        print(f"Error: Archive directory not found: {archive_dir}")
        print("\nTo get your Instagram archive:")
        print("1. Go to: Instagram app → Settings → Security → Download Data")
        print("2. Request your archive")
        print("3. Wait for email (can take up to 48 hours)")
        print("4. Download and extract the ZIP file")
        print("5. Point this script to the extracted folder")
        return

    # Process archive
    docs = process_instagram_archive(archive_dir, args.username, args.limit)

    if docs:
        print("\nProcessed posts:")
        for doc in docs[:10]:  # Show first 10
            print(f"  - ID: {doc['id']}, Media: {doc['media_count']}")

        if len(docs) > 10:
            print(f"  ... and {len(docs) - 10} more")

        print("\n" + "="*60)
        print("Next steps:")
        print("="*60)
        print("1. Update search index:")
        print("   KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/embeddings_generator.py --update")
        print("")
        print("2. Search your Instagram posts:")
        print("   KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py \"your topic\"")
        print("")
        print("3. View visual interface:")
        print("   python scripts/interface/visual_browser.py")

if __name__ == "__main__":
    main()
