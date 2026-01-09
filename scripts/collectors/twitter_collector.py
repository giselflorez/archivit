#!/usr/bin/env python3
"""
Twitter Collector - Process Twitter/X archive and add to knowledge base

Extracts and preserves:
- Tweet text and metadata
- Images (photos)
- Videos
- GIFs
- Audio (Twitter Spaces recordings if available)
- All media URLs and local copies
"""
import json
import hashlib
import re
import shutil
import requests
from datetime import datetime
from pathlib import Path
import yaml
import argparse
import logging

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)


def extract_media_from_tweet(tweet: dict, archive_base_path: Path = None) -> dict:
    """
    Extract all media references from a tweet

    Args:
        tweet: Tweet data dict
        archive_base_path: Path to Twitter archive root (for local media files)

    Returns:
        Dict with categorized media info
    """
    media = {
        'images': [],
        'videos': [],
        'gifs': [],
        'audio': [],
        'external_urls': []
    }

    # Check extended_entities (preferred) and entities
    extended = tweet.get('extended_entities', {})
    entities = tweet.get('entities', {})

    # Process media from extended_entities
    for m in extended.get('media', []):
        media_type = m.get('type', 'photo')
        media_url = m.get('media_url_https', m.get('media_url', ''))

        media_info = {
            'id': m.get('id_str', ''),
            'url': media_url,
            'display_url': m.get('display_url', ''),
            'expanded_url': m.get('expanded_url', ''),
            'alt_text': m.get('ext_alt_text', ''),
        }

        if media_type == 'photo':
            # Get highest quality image
            if media_url:
                media_info['url_large'] = f"{media_url}:large"
                media_info['url_orig'] = f"{media_url}:orig"
            media['images'].append(media_info)

        elif media_type == 'video':
            # Get video variants
            video_info = m.get('video_info', {})
            variants = video_info.get('variants', [])
            # Sort by bitrate to get highest quality
            mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
            if mp4_variants:
                best = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
                media_info['video_url'] = best.get('url', '')
                media_info['bitrate'] = best.get('bitrate', 0)
            media_info['duration_ms'] = video_info.get('duration_millis', 0)
            media['videos'].append(media_info)

        elif media_type == 'animated_gif':
            video_info = m.get('video_info', {})
            variants = video_info.get('variants', [])
            if variants:
                media_info['gif_url'] = variants[0].get('url', '')
            media['gifs'].append(media_info)

    # Check for Twitter Spaces / audio
    # Twitter archive may include spaces_metadata
    if 'spaces_metadata' in tweet:
        spaces = tweet['spaces_metadata']
        media['audio'].append({
            'type': 'twitter_space',
            'id': spaces.get('space_id', ''),
            'title': spaces.get('title', ''),
            'url': spaces.get('url', '')
        })

    # External URLs (for linked media)
    for url_entity in entities.get('urls', []):
        expanded = url_entity.get('expanded_url', '')
        if any(ext in expanded.lower() for ext in ['.jpg', '.png', '.gif', '.mp4', '.webp', '.mp3', '.wav']):
            media['external_urls'].append({
                'url': expanded,
                'display': url_entity.get('display_url', '')
            })

    # Check if archive has local media files
    if archive_base_path:
        tweet_id = tweet.get('id_str', tweet.get('id', ''))
        tweet_media_dir = archive_base_path / 'data' / 'tweets_media'
        if tweet_media_dir.exists():
            # Twitter archive stores media as {tweet_id}-{media_id}.{ext}
            for media_file in tweet_media_dir.glob(f"{tweet_id}-*"):
                local_info = {
                    'local_path': str(media_file),
                    'filename': media_file.name
                }
                ext = media_file.suffix.lower()
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    media['images'].append(local_info)
                elif ext in ['.mp4', '.mov']:
                    media['videos'].append(local_info)
                elif ext in ['.gif']:
                    media['gifs'].append(local_info)
                elif ext in ['.mp3', '.m4a', '.wav']:
                    media['audio'].append(local_info)

    return media


def copy_media_to_knowledge_base(media: dict, doc_id: str, archive_base_path: Path = None) -> dict:
    """
    Copy media files to knowledge base media directory

    Args:
        media: Media dict from extract_media_from_tweet
        doc_id: Document ID for organizing media
        archive_base_path: Path to Twitter archive root

    Returns:
        Updated media dict with local paths
    """
    media_dir = Path(f"knowledge_base/media/twitter/{doc_id}")
    media_dir.mkdir(parents=True, exist_ok=True)

    copied_media = {
        'images': [],
        'videos': [],
        'gifs': [],
        'audio': []
    }

    def copy_local_file(info: dict, category: str) -> dict:
        """Copy a local file to knowledge base"""
        if 'local_path' in info:
            src = Path(info['local_path'])
            if src.exists():
                dst = media_dir / src.name
                shutil.copy2(src, dst)
                info['kb_path'] = str(dst)
                logger.info(f"  Copied: {src.name}")
        return info

    # Copy local files from archive
    for img in media.get('images', []):
        copied_media['images'].append(copy_local_file(img, 'images'))

    for vid in media.get('videos', []):
        copied_media['videos'].append(copy_local_file(vid, 'videos'))

    for gif in media.get('gifs', []):
        copied_media['gifs'].append(copy_local_file(gif, 'gifs'))

    for aud in media.get('audio', []):
        copied_media['audio'].append(copy_local_file(aud, 'audio'))

    return copied_media


def get_media_stats(tweets: list, archive_base_path: Path = None) -> dict:
    """Get media statistics for a batch of tweets"""
    stats = {
        'total_tweets': len(tweets),
        'tweets_with_media': 0,
        'images': 0,
        'videos': 0,
        'gifs': 0,
        'audio': 0
    }

    for tweet in tweets:
        media = extract_media_from_tweet(tweet, archive_base_path)
        has_media = False

        if media['images']:
            stats['images'] += len(media['images'])
            has_media = True
        if media['videos']:
            stats['videos'] += len(media['videos'])
            has_media = True
        if media['gifs']:
            stats['gifs'] += len(media['gifs'])
            has_media = True
        if media['audio']:
            stats['audio'] += len(media['audio'])
            has_media = True

        if has_media:
            stats['tweets_with_media'] += 1

    return stats

def generate_id(tweet_id, username):
    """Generate a unique ID based on tweet metadata"""
    content = f"{username}_{tweet_id}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def parse_twitter_archive(archive_path):
    """
    Parse Twitter archive tweets.js file

    Args:
        archive_path: Path to tweets.js or tweet.js file

    Returns:
        List of tweet dictionaries
    """
    print(f"Reading Twitter archive: {archive_path}")

    with open(archive_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Twitter archive format: window.YTD.tweets.part0 = [ ... ]
    # or window.YTD.tweet.part0 = [ ... ]
    # Remove the JavaScript assignment
    content = re.sub(r'^window\.YTD\.(tweets?|tweet)\.part\d+\s*=\s*', '', content)
    content = content.strip()
    if content.endswith(';'):
        content = content[:-1]

    tweets_data = json.loads(content)

    tweets = []
    for item in tweets_data:
        # Archive format has nested structure
        tweet = item.get('tweet', item)
        tweets.append(tweet)

    print(f"Found {len(tweets)} tweets")
    return tweets

def extract_tags_from_tweet(tweet_text):
    """Extract relevant tags from tweet content"""
    tags = ["twitter", "social_media"]

    tweet_lower = tweet_text.lower()

    tag_keywords = {
        'art': ['art', 'artwork', 'creative', 'artist', 'exhibition'],
        'blockchain': ['blockchain', 'crypto', 'nft', 'web3', 'eth', 'ethereum'],
        'digital_identity': ['identity', 'digital', 'online', 'persona'],
        'philosophy': ['philosophy', 'thought', 'concept', 'idea', 'consciousness'],
        'technology': ['tech', 'technology', 'digital', 'innovation'],
        'photography': ['photo', 'photography', 'camera', 'lens', 'capture', 'shoot'],
        'community': ['community', 'together', 'collective', 'woca', 'women'],
        'moonlanguage': ['moon', 'moonlanguage', 'lunar'],
        'light': ['light', 'waves', 'transmissions']
    }

    for tag, keywords in tag_keywords.items():
        if any(keyword in tweet_lower for keyword in keywords):
            tags.append(tag)

    # Extract hashtags
    hashtags = re.findall(r'#(\w+)', tweet_text)
    tags.extend([h.lower() for h in hashtags[:5]])  # Limit hashtags

    return list(set(tags))

def determine_subject(tweet_text):
    """Determine subject category from tweet content"""
    tweet_lower = tweet_text.lower()

    if "giselxflorez" in tweet_lower or "giselxtez" in tweet_lower:
        return "giselxflorez"
    elif "giselx" in tweet_lower:
        return "giselx"
    elif "gisel florez" in tweet_lower or "giselflorez" in tweet_lower:
        return "gisel_florez"
    else:
        return "twitter_general"

def group_tweets_by_month(tweets):
    """Group tweets by year-month for better organization"""
    grouped = {}

    for tweet in tweets:
        created_at = tweet.get('created_at', '')
        try:
            # Parse Twitter date format
            dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
            month_key = dt.strftime('%Y-%m')
        except:
            month_key = 'unknown'

        if month_key not in grouped:
            grouped[month_key] = []

        grouped[month_key].append(tweet)

    return grouped

def create_markdown_for_tweets(tweets, month_key, username, archive_base_path=None, copy_media=True):
    """
    Create markdown document for a group of tweets with linked media

    Args:
        tweets: List of tweet dicts
        month_key: Period identifier (YYYY-MM)
        username: Twitter username
        archive_base_path: Path to Twitter archive root (for local media)
        copy_media: Whether to copy media files to knowledge base

    Returns:
        Tuple of (markdown_content, doc_id, subject_category, media_manifest)
    """
    now = datetime.now()

    # Generate doc ID from month
    doc_id = hashlib.md5(f"{username}_{month_key}".encode()).hexdigest()[:12]

    # Collect all tags from all tweets
    all_tags = set(["twitter", "social_media"])
    for tweet in tweets:
        tweet_text = tweet.get('full_text', tweet.get('text', ''))
        all_tags.update(extract_tags_from_tweet(tweet_text))

    # Determine subject from tweets
    all_text = ' '.join([t.get('full_text', t.get('text', '')) for t in tweets])
    subject_category = determine_subject(all_text)

    # Process media and build manifest
    media_manifest = {
        'doc_id': doc_id,
        'period': month_key,
        'media_dir': f"knowledge_base/media/twitter/{doc_id}",
        'items': [],
        'stats': {'images': 0, 'videos': 0, 'gifs': 0, 'audio': 0}
    }

    # Extract and optionally copy media for all tweets
    tweets_media = {}
    for tweet in tweets:
        tweet_id = tweet.get('id_str', tweet.get('id', ''))
        media = extract_media_from_tweet(tweet, archive_base_path)

        if copy_media and any([media['images'], media['videos'], media['gifs'], media['audio']]):
            copied = copy_media_to_knowledge_base(media, doc_id, archive_base_path)
            tweets_media[tweet_id] = copied

            # Update manifest
            for img in copied['images']:
                if 'kb_path' in img:
                    media_manifest['items'].append({
                        'type': 'image',
                        'source_tweet_id': tweet_id,
                        'path': img['kb_path'],
                        'filename': img.get('filename', ''),
                        'alt_text': img.get('alt_text', '')
                    })
                    media_manifest['stats']['images'] += 1

            for vid in copied['videos']:
                if 'kb_path' in vid:
                    media_manifest['items'].append({
                        'type': 'video',
                        'source_tweet_id': tweet_id,
                        'path': vid['kb_path'],
                        'filename': vid.get('filename', ''),
                        'duration_ms': vid.get('duration_ms', 0)
                    })
                    media_manifest['stats']['videos'] += 1

            for gif in copied['gifs']:
                if 'kb_path' in gif:
                    media_manifest['items'].append({
                        'type': 'gif',
                        'source_tweet_id': tweet_id,
                        'path': gif['kb_path'],
                        'filename': gif.get('filename', '')
                    })
                    media_manifest['stats']['gifs'] += 1

            for aud in copied['audio']:
                if 'kb_path' in aud:
                    media_manifest['items'].append({
                        'type': 'audio',
                        'source_tweet_id': tweet_id,
                        'path': aud['kb_path'],
                        'filename': aud.get('filename', '')
                    })
                    media_manifest['stats']['audio'] += 1
        else:
            tweets_media[tweet_id] = media

    # Create frontmatter with media info
    frontmatter = {
        'id': doc_id,
        'source': 'twitter',
        'type': 'twitter_archive',
        'created_at': now.isoformat(),
        'username': username,
        'period': month_key,
        'tweet_count': len(tweets),
        'media_count': {
            'images': media_manifest['stats']['images'],
            'videos': media_manifest['stats']['videos'],
            'gifs': media_manifest['stats']['gifs'],
            'audio': media_manifest['stats']['audio']
        },
        'media_dir': media_manifest['media_dir'] if any(media_manifest['stats'].values()) else None,
        'tags': sorted(list(all_tags))
    }

    # Create markdown body
    total_media = sum(media_manifest['stats'].values())
    media_summary = ""
    if total_media > 0:
        media_parts = []
        if media_manifest['stats']['images']:
            media_parts.append(f"{media_manifest['stats']['images']} images")
        if media_manifest['stats']['videos']:
            media_parts.append(f"{media_manifest['stats']['videos']} videos")
        if media_manifest['stats']['gifs']:
            media_parts.append(f"{media_manifest['stats']['gifs']} GIFs")
        if media_manifest['stats']['audio']:
            media_parts.append(f"{media_manifest['stats']['audio']} audio files")
        media_summary = f"\n**Media:** {', '.join(media_parts)}"

    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# Twitter Archive: @{username} - {month_key}

## Summary
{len(tweets)} tweets from {month_key}{media_summary}

---

"""

    # Add each tweet with linked media
    for tweet in sorted(tweets, key=lambda t: t.get('created_at', ''), reverse=True):
        tweet_id = tweet.get('id_str', tweet.get('id', 'unknown'))
        tweet_text = tweet.get('full_text', tweet.get('text', ''))
        created_at = tweet.get('created_at', '')

        # Metrics
        retweets = tweet.get('retweet_count', 0)
        favorites = tweet.get('favorite_count', 0)

        # Parse date
        try:
            dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
            date_str = dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            date_str = created_at

        # Extract URLs
        urls = []
        entities = tweet.get('entities', {})
        if 'urls' in entities:
            urls = [u.get('expanded_url', u.get('url', '')) for u in entities['urls']]

        # Build tweet entry
        md_content += f"""### Tweet {tweet_id}
**Date:** {date_str}
**Engagement:** {favorites} likes, {retweets} retweets

{tweet_text}

"""

        # Add linked media section for this tweet
        tweet_media = tweets_media.get(tweet_id, {})
        has_local_media = False

        if tweet_media.get('images'):
            for img in tweet_media['images']:
                if 'kb_path' in img:
                    rel_path = img['kb_path'].replace('knowledge_base/', '')
                    md_content += f"![{img.get('alt_text', 'Image')}](/{rel_path})\n"
                    has_local_media = True
                elif 'url' in img:
                    md_content += f"**Image:** [{img.get('display_url', 'View')}]({img['url']})\n"

        if tweet_media.get('videos'):
            for vid in tweet_media['videos']:
                if 'kb_path' in vid:
                    rel_path = vid['kb_path'].replace('knowledge_base/', '')
                    duration = vid.get('duration_ms', 0) // 1000
                    md_content += f"**Video:** [{vid.get('filename', 'video')}](/{rel_path})"
                    if duration:
                        md_content += f" ({duration}s)"
                    md_content += "\n"
                    has_local_media = True
                elif 'video_url' in vid:
                    md_content += f"**Video:** [View]({vid['video_url']})\n"

        if tweet_media.get('gifs'):
            for gif in tweet_media['gifs']:
                if 'kb_path' in gif:
                    rel_path = gif['kb_path'].replace('knowledge_base/', '')
                    md_content += f"**GIF:** [{gif.get('filename', 'gif')}](/{rel_path})\n"
                    has_local_media = True
                elif 'gif_url' in gif:
                    md_content += f"**GIF:** [View]({gif['gif_url']})\n"

        if tweet_media.get('audio'):
            for aud in tweet_media['audio']:
                if 'kb_path' in aud:
                    rel_path = aud['kb_path'].replace('knowledge_base/', '')
                    md_content += f"**Audio:** [{aud.get('filename', 'audio')}](/{rel_path})\n"
                    has_local_media = True

        if has_local_media:
            md_content += "\n"

        if urls:
            md_content += "**Links:**\n"
            for url in urls:
                md_content += f"- {url}\n"
            md_content += "\n"

        md_content += "---\n\n"

    md_content += f"""## Related Topics
- Search for more about: {subject_category}
- Period: {month_key}
- Total tweets: {len(tweets)}
- Total media files: {total_media}
"""

    # Add media index at the end
    if media_manifest['items']:
        md_content += f"""
## Media Index
All media files for this period are stored in: `{media_manifest['media_dir']}`

| Type | Tweet ID | Filename |
|------|----------|----------|
"""
        for item in media_manifest['items']:
            md_content += f"| {item['type']} | {item['source_tweet_id']} | {item.get('filename', 'N/A')} |\n"

    return md_content, doc_id, subject_category, media_manifest

def save_twitter_content(markdown_content, raw_data, subject_category, doc_id, media_manifest=None):
    """
    Save Twitter content as knowledge base entry

    Args:
        markdown_content: Generated markdown
        raw_data: Raw tweet data
        subject_category: Category for filing
        doc_id: Document ID
        media_manifest: Optional media manifest linking files to tweets

    Returns:
        Path to saved markdown file
    """
    # Save raw data
    raw_dir = Path("knowledge_base/raw/twitter")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"twitter_{doc_id}_{timestamp}.json"
    raw_filepath = raw_dir / raw_filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"  Raw data saved to: {raw_filepath}")

    # Save media manifest if present
    if media_manifest and media_manifest.get('items'):
        manifest_dir = Path(media_manifest['media_dir'])
        manifest_dir.mkdir(parents=True, exist_ok=True)

        manifest_filepath = manifest_dir / "manifest.json"
        with open(manifest_filepath, 'w', encoding='utf-8') as f:
            json.dump(media_manifest, f, indent=2, ensure_ascii=False)

        print(f"  Media manifest saved to: {manifest_filepath}")
        print(f"  Media files: {sum(media_manifest['stats'].values())}")

    # Save processed markdown
    processed_dir = Path(f"knowledge_base/processed/about_{subject_category}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    md_filename = f"twitter_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  Markdown saved to: {md_filepath}")

    return str(md_filepath)

def process_twitter_archive(archive_path, username="giselflorez"):
    """Main processing function"""
    print(f"\n{'='*60}")
    print(f"Processing Twitter Archive: @{username}")
    print(f"{'='*60}\n")

    # Parse tweets
    tweets = parse_twitter_archive(archive_path)

    # Group by month
    grouped = group_tweets_by_month(tweets)

    print(f"\nGrouped into {len(grouped)} periods")

    processed_docs = []

    # Process each month
    for month_key in sorted(grouped.keys(), reverse=True):
        month_tweets = grouped[month_key]

        print(f"\n{'='*60}")
        print(f"Processing {month_key}: {len(month_tweets)} tweets")
        print(f"{'='*60}")

        # Create markdown
        markdown, doc_id, subject_category = create_markdown_for_tweets(
            month_tweets,
            month_key,
            username
        )

        # Save
        filepath = save_twitter_content(
            markdown,
            month_tweets,
            subject_category,
            doc_id
        )

        processed_docs.append({
            'id': doc_id,
            'filepath': filepath,
            'period': month_key,
            'tweet_count': len(month_tweets)
        })

        print(f"✓ Processed {len(month_tweets)} tweets from {month_key}")

    print(f"\n{'='*60}")
    print(f"Twitter Archive Processing Complete")
    print(f"{'='*60}")
    print(f"Total periods: {len(processed_docs)}")
    print(f"Total tweets: {len(tweets)}")
    print(f"{'='*60}\n")

    return processed_docs

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Process Twitter/X archive and add to knowledge base"
    )
    parser.add_argument(
        'archive_path',
        help='Path to tweets.js file from Twitter archive'
    )
    parser.add_argument(
        '--username',
        default='giselflorez',
        help='Twitter username (default: giselflorez)'
    )

    args = parser.parse_args()

    archive_path = Path(args.archive_path)

    if not archive_path.exists():
        print(f"Error: Archive file not found: {archive_path}")
        print("\nTo get your Twitter archive:")
        print("1. Go to: https://twitter.com/settings/download_your_data")
        print("2. Request your archive")
        print("3. Download and extract the ZIP file")
        print("4. Look for: data/tweets.js or data/tweet.js")
        return

    # Process archive
    docs = process_twitter_archive(archive_path, args.username)

    if docs:
        print("\nProcessed periods:")
        for doc in docs:
            print(f"  - {doc['period']}: {doc['tweet_count']} tweets (ID: {doc['id']})")

        print("\n" + "="*60)
        print("Next steps:")
        print("="*60)
        print("1. Update search index:")
        print("   KMP_DUPLICATE_LIB_OK=TRUE python scripts/processors/embeddings_generator.py --update")
        print("")
        print("2. Search your tweets:")
        print("   KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py \"your tweet topic\"")

if __name__ == "__main__":
    main()
