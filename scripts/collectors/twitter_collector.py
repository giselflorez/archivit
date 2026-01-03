#!/usr/bin/env python3
"""
Twitter Collector - Process Twitter/X archive and add to knowledge base
"""
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
import yaml
import argparse

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

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

def create_markdown_for_tweets(tweets, month_key, username):
    """Create markdown document for a group of tweets"""
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

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'twitter',
        'type': 'twitter_archive',
        'created_at': now.isoformat(),
        'username': username,
        'period': month_key,
        'tweet_count': len(tweets),
        'tags': sorted(list(all_tags))
    }

    # Create markdown body
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# Twitter Archive: @{username} - {month_key}

## Summary
{len(tweets)} tweets from {month_key}

---

"""

    # Add each tweet
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
"""

    return md_content, doc_id, subject_category

def save_twitter_content(markdown_content, raw_data, subject_category, doc_id):
    """Save Twitter content as knowledge base entry"""
    # Save raw data
    raw_dir = Path("knowledge_base/raw/twitter")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"twitter_{doc_id}_{timestamp}.json"
    raw_filepath = raw_dir / raw_filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"  Raw data saved to: {raw_filepath}")

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
