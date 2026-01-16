#!/usr/bin/env python3
"""
SuperRare NFT Scraper

Specialized scraper for SuperRare artist profiles that:
- Uses Selenium for lazy loading support
- Filters images to only grab actual NFT artworks
- Extracts NFT titles, descriptions, and metadata
- Ignores profile pictures, avatars, and UI elements
"""
import re
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
import yaml

# Selenium for JavaScript-rendered content
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("ERROR: Selenium not available. Install with: pip install selenium webdriver-manager")
    exit(1)

from bs4 import BeautifulSoup


def setup_driver():
    """Set up Chrome/Brave driver with optimal settings for scraping"""

    # Try Brave browser first (user preference)
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    options = ChromeOptions()
    # Don't use headless mode initially to debug
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    if Path(brave_path).exists():
        options.binary_location = brave_path

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        return driver
    except Exception as e:
        print(f"ERROR: Could not initialize Chrome driver: {e}")
        exit(1)


def scroll_to_load_all_nfts(driver, max_scrolls=20, scroll_pause=2):
    """
    Scroll down the page to trigger lazy loading of all NFT images

    Args:
        driver: Selenium WebDriver instance
        max_scrolls: Maximum number of scroll attempts
        scroll_pause: Seconds to wait after each scroll

    Returns:
        int: Number of scrolls performed
    """
    print(f"\n→ Scrolling to load all NFTs (max {max_scrolls} scrolls)...")

    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0

    for i in range(max_scrolls):
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for new content to load
        time.sleep(scroll_pause)

        # Calculate new scroll height and compare
        new_height = driver.execute_script("return document.body.scrollHeight")

        scrolls += 1
        print(f"  Scroll {scrolls}/{max_scrolls} - Page height: {new_height}px")

        # If height hasn't changed, we've reached the bottom
        if new_height == last_height:
            print(f"  ✓ Reached bottom of page after {scrolls} scrolls")
            break

        last_height = new_height

    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    return scrolls


def extract_nft_cards(soup):
    """
    Extract NFT card elements from SuperRare page

    SuperRare NFTs are typically in:
    - <a> tags with specific class patterns
    - Nested within grid/collection containers
    - Have specific data attributes

    Returns:
        List of NFT card elements
    """
    nft_cards = []

    # Pattern 1: Look for links to individual NFT pages (/artwork/...)
    artwork_links = soup.find_all('a', href=re.compile(r'/artwork/'))

    # Pattern 2: Look for common NFT card containers
    # SuperRare often uses specific class names like 'nft-card', 'artwork-card', etc.
    card_containers = soup.find_all(['div', 'article'], class_=re.compile(r'(card|artwork|nft|piece|item)', re.I))

    # Combine and deduplicate
    all_candidates = artwork_links + card_containers

    # Filter to only elements that likely contain NFT data
    for elem in all_candidates:
        # Must have an image child
        img = elem.find('img')
        if not img:
            continue

        # Must have a link to artwork page
        link = elem.find('a', href=re.compile(r'/artwork/'))
        if not link and not (elem.name == 'a' and '/artwork/' in elem.get('href', '')):
            continue

        nft_cards.append(elem)

    # Deduplicate by href
    unique_cards = {}
    for card in nft_cards:
        link = card if card.name == 'a' else card.find('a', href=re.compile(r'/artwork/'))
        href = link.get('href', '') if link else ''
        if href and href not in unique_cards:
            unique_cards[href] = card

    return list(unique_cards.values())


def is_nft_artwork_image(img, img_url):
    """
    Determine if an image is an NFT artwork (not a profile pic, avatar, or UI element)

    Criteria:
    - URL contains 'ipfs' or specific CDN patterns for artwork
    - Image is reasonably large (>20KB typically)
    - Not in common avatar/icon patterns
    - Has proper parent container structure

    Args:
        img: BeautifulSoup img element
        img_url: Full URL of the image

    Returns:
        bool: True if likely an NFT artwork
    """

    # Check URL patterns
    url_lower = img_url.lower()

    # Positive signals (likely NFT artwork)
    if any(pattern in url_lower for pattern in [
        'ipfs',  # IPFS storage
        'storage.googleapis.com/sr_prod_artworks',  # SuperRare artwork storage
        'superrare.myfilebase.com',  # SuperRare IPFS gateway
        'pixura.imgix.net/https%3a%2f%2fstorage.googleapis.com%2fsr_prod_artworks',  # Proxied artwork
    ]):
        print(f"    ✓ NFT artwork detected (IPFS/artwork CDN): {img_url[:80]}...")
        return True

    # Negative signals (likely profile pic or UI)
    if any(pattern in url_lower for pattern in [
        'avatar',
        'profile',
        '/profile-',  # Profile images
        'logo',
        'icon',
        'badge',
        'banner',
    ]):
        print(f"    ✗ Skipping UI element: {img_url[:80]}...")
        return False

    # Check alt text - skip if it looks like a username/vault name
    alt = img.get('alt', '').lower()
    if alt and 'vault' in alt and len(alt) < 30:
        print(f"    ✗ Skipping vault/profile image (alt='{alt}')")
        return False

    # Check image classes - skip avatar patterns
    img_classes = ' '.join(img.get('class', [])).lower()
    if any(pattern in img_classes for pattern in ['avatar', 'profile', 'user-img']):
        print(f"    ✗ Skipping avatar/profile (class='{img_classes}')")
        return False

    return True


def extract_nft_metadata(nft_card_element):
    """
    Extract metadata from an NFT card element

    Returns:
        dict: NFT metadata including title, artist, link, etc.
    """
    metadata = {
        'title': '',
        'artist': '',
        'url': '',
        'description': '',
        'price': '',
        'edition': ''
    }

    # Extract artwork link
    link = nft_card_element if nft_card_element.name == 'a' else nft_card_element.find('a', href=re.compile(r'/artwork/'))
    if link:
        metadata['url'] = link.get('href', '')

    # Extract title - common patterns
    title_elem = (
        nft_card_element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'(title|name)', re.I)) or
        nft_card_element.find('a', href=re.compile(r'/artwork/'))
    )
    if title_elem:
        metadata['title'] = title_elem.get_text().strip()

    # Extract artist - look for creator/artist links
    artist_elem = nft_card_element.find('a', href=re.compile(r'/@|/creator/'))
    if artist_elem:
        metadata['artist'] = artist_elem.get_text().strip()

    # Extract description if visible
    desc_elem = nft_card_element.find(['p', 'div'], class_=re.compile(r'(description|desc)', re.I))
    if desc_elem:
        metadata['description'] = desc_elem.get_text().strip()

    # Extract price if visible
    price_elem = nft_card_element.find(text=re.compile(r'ETH|Ξ'))
    if price_elem:
        metadata['price'] = price_elem.strip()

    return metadata


def scrape_superrare_profile(url, artist_name=None):
    """
    Scrape a SuperRare artist profile page

    Args:
        url: SuperRare profile URL (e.g., http://superrare.com/founder)
        artist_name: Optional artist name to filter (extracted from URL if not provided)

    Returns:
        dict: Scraped data including NFTs, images, and metadata
    """
    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium is required for SuperRare scraping")

    # Extract artist name from URL if not provided
    if not artist_name:
        # URL format: http://superrare.com/founder or http://superrare.com/@founder
        path = urlparse(url).path
        artist_name = path.strip('/').replace('@', '')

    print(f"\n{'='*70}")
    print(f"SuperRare Scraper - Artist: {artist_name}")
    print(f"URL: {url}")
    print(f"{'='*70}")

    # Set up driver
    driver = setup_driver()

    try:
        # Load the page
        print(f"\n→ Loading SuperRare profile...")
        driver.get(url)

        # Wait for page to load
        print(f"→ Waiting for page to load...")
        time.sleep(5)

        # Scroll to load all NFTs
        scrolls = scroll_to_load_all_nfts(driver, max_scrolls=20, scroll_pause=2)

        # Get final page source
        print(f"\n→ Extracting HTML...")
        page_source = driver.page_source

        # Close browser
        driver.quit()

        # Parse with BeautifulSoup
        print(f"→ Parsing HTML...")
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract NFT cards
        print(f"\n→ Extracting NFT cards...")
        nft_cards = extract_nft_cards(soup)
        print(f"✓ Found {len(nft_cards)} potential NFT cards")

        # Extract images and metadata from each NFT card
        print(f"\n→ Processing NFT artworks...")
        nfts = []

        for idx, card in enumerate(nft_cards, 1):
            print(f"\n  NFT {idx}/{len(nft_cards)}:")

            # Find image in card
            img = card.find('img')
            if not img:
                print(f"    ✗ No image found in card")
                continue

            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                print(f"    ✗ No image URL found")
                continue

            # Make absolute URL
            img_url = urljoin(url, img_url)

            # Check if this is an NFT artwork (not profile pic)
            if not is_nft_artwork_image(img, img_url):
                continue

            # Extract metadata
            metadata = extract_nft_metadata(card)

            # Download image
            try:
                img_response = requests.get(img_url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': url
                })

                if img_response.status_code != 200:
                    print(f"    ✗ Failed to download (HTTP {img_response.status_code})")
                    continue

                # Check if actually an image
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"    ✗ Not an image (content-type: {content_type})")
                    continue

                # Store NFT data
                nft_data = {
                    'image_url': img_url,
                    'image_data': img_response.content,
                    'image_size': len(img_response.content),
                    'title': metadata['title'] or f"Artwork {idx}",
                    'artist': metadata['artist'] or artist_name,
                    'artwork_url': urljoin(url, metadata['url']) if metadata['url'] else '',
                    'description': metadata['description'],
                    'price': metadata['price'],
                    'content_type': content_type
                }

                nfts.append(nft_data)

                print(f"    ✓ '{nft_data['title']}' ({nft_data['image_size']} bytes)")
                if nft_data['artwork_url']:
                    print(f"      URL: {nft_data['artwork_url']}")

            except Exception as e:
                print(f"    ✗ Error processing image: {e}")
                continue

        print(f"\n{'='*70}")
        print(f"✓ Successfully scraped {len(nfts)} NFT artworks from {artist_name}'s profile")
        print(f"{'='*70}\n")

        return {
            'artist': artist_name,
            'profile_url': url,
            'nfts': nfts,
            'total_cards_found': len(nft_cards),
            'artworks_extracted': len(nfts),
            'scraped_at': datetime.now().isoformat()
        }

    except Exception as e:
        driver.quit()
        raise e


def save_to_knowledge_base(scrape_data):
    """
    Save scraped SuperRare data to knowledge base

    Creates:
    - Markdown file with frontmatter in knowledge_base/processed/about_web_imports/
    - Images in knowledge_base/media/web_imports/<doc_id>/
    - Raw JSON in knowledge_base/raw/web_imports/
    """

    artist = scrape_data['artist']
    profile_url = scrape_data['profile_url']
    nfts = scrape_data['nfts']

    # Generate doc ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    doc_id = hashlib.md5(f"{profile_url}_{timestamp}".encode()).hexdigest()[:12]

    # Create directories
    media_dir = Path("knowledge_base/media/web_imports") / doc_id
    media_dir.mkdir(parents=True, exist_ok=True)

    processed_dir = Path("knowledge_base/processed/about_web_imports")
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = Path("knowledge_base/raw/web_imports")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Save images
    print(f"\n→ Saving {len(nfts)} NFT images...")
    saved_nfts = []

    for idx, nft in enumerate(nfts, 1):
        # Determine file extension
        ext_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        ext = ext_map.get(nft['content_type'], '.jpg')

        # Save image file
        filename = f"nft_{idx}{ext}"
        img_path = media_dir / filename

        with open(img_path, 'wb') as f:
            f.write(nft['image_data'])

        print(f"  ✓ Saved: {filename} ({nft['image_size']} bytes)")

        # Store metadata for markdown
        saved_nfts.append({
            'filename': filename,
            'title': nft['title'],
            'artist': nft['artist'],
            'artwork_url': nft['artwork_url'],
            'description': nft['description'],
            'price': nft['price'],
            'original_url': nft['image_url'],
            'size_bytes': nft['image_size']
        })

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'web_import',
        'type': 'superrare_collection',
        'url': profile_url,
        'domain': 'superrare.com',
        'title': f'{artist} | SuperRare NFT Collection',
        'artist': artist,
        'created_at': datetime.now().isoformat(),
        'scraped_date': datetime.now().strftime('%Y-%m-%d'),
        'has_images': True,
        'image_count': len(saved_nfts),
        'nft_count': len(saved_nfts),
        'tags': ['web_import', 'superrare', 'nft', 'blockchain', artist.lower()]
    }

    # Create markdown content
    markdown = f"""# {artist} | SuperRare NFT Collection

**Source:** [superrare.com]({profile_url})
**Imported:** {datetime.now().strftime('%B %d, %Y')}
**NFT Artworks:** {len(saved_nfts)}

## Collection

This collection contains {len(saved_nfts)} NFT artworks by {artist} from their SuperRare profile.

---

## NFT Artworks

"""

    # Add each NFT
    for idx, nft in enumerate(saved_nfts, 1):
        markdown += f"""### {idx}. {nft['title']}

![{nft['title']}](../../knowledge_base/media/web_imports/{doc_id}/{nft['filename']})

**Artist:** {nft['artist']}
"""

        if nft['artwork_url']:
            markdown += f"**View on SuperRare:** [{nft['title']}]({nft['artwork_url']})\n"

        if nft['description']:
            markdown += f"\n**Description:** {nft['description']}\n"

        if nft['price']:
            markdown += f"**Price:** {nft['price']}\n"

        markdown += f"""
**Metadata:**
- Original URL: {nft['original_url']}
- File Size: {nft['size_bytes']:,} bytes
- Filename: {nft['filename']}

---

"""

    markdown += f"""
## Source
- Original URL: {profile_url}
- Domain: superrare.com
- Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Save markdown file
    md_filename = f"web_{doc_id}_{timestamp}.md"
    md_path = processed_dir / md_filename

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True))
        f.write('---\n\n')
        f.write(markdown)

    print(f"\n✓ Saved markdown: {md_path}")

    # Save raw JSON
    json_filename = f"web_{doc_id}_{timestamp}.json"
    json_path = raw_dir / json_filename

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            **frontmatter,
            'nfts': saved_nfts,
            'scrape_metadata': scrape_data
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved raw JSON: {json_path}")

    return {
        'doc_id': doc_id,
        'markdown_path': str(md_path),
        'json_path': str(json_path),
        'media_dir': str(media_dir),
        'nft_count': len(saved_nfts)
    }


def main():
    """Main execution"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python superrare_scraper.py <superrare_profile_url>")
        print("\nExample:")
        print("  python scripts/collectors/superrare_scraper.py http://superrare.com/founder")
        return

    url = sys.argv[1]

    # Validate URL
    if 'superrare.com' not in url.lower():
        print("ERROR: URL must be a SuperRare profile page")
        print("Example: http://superrare.com/founder")
        return

    try:
        # Scrape SuperRare profile
        scrape_data = scrape_superrare_profile(url)

        # Save to knowledge base
        result = save_to_knowledge_base(scrape_data)

        print(f"\n{'='*70}")
        print(f"SUCCESS!")
        print(f"{'='*70}")
        print(f"Document ID: {result['doc_id']}")
        print(f"NFTs saved: {result['nft_count']}")
        print(f"Markdown: {result['markdown_path']}")
        print(f"Media: {result['media_dir']}")
        print(f"\n✓ Import complete. View in Visual Translator at:")
        print(f"  http://localhost:5001/visual-translator")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
