#!/usr/bin/env python3
"""
NFT/Art Platform Scraper Orchestrator

Intelligent scraper that:
1. Detects which platform/site is being scraped
2. Selects the most advanced specialized scraper for that platform
3. Validates scrape accuracy and completeness
4. Falls back to alternative scrapers if validation fails
5. Normalizes all data into unified knowledge base format

Supported platforms:
- SuperRare (superrare.com)
- Foundation (foundation.app)
- OpenSea (opensea.io)
- Objkt (objkt.com) - Tezos NFTs
- Zora (zora.co)
- Known Origin (knownorigin.io)
- Manifold (gallery.manifold.xyz)
- Generic web pages (fallback)
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple
import yaml

# Import specialized scrapers
try:
    from collectors.superrare_scraper import scrape_superrare_profile, is_nft_artwork_image
    SUPERRARE_AVAILABLE = True
except ImportError:
    SUPERRARE_AVAILABLE = False

# Try to import Selenium for JavaScript-rendered content
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

import requests
from bs4 import BeautifulSoup


# ============================================================================
# PLATFORM DETECTION
# ============================================================================

PLATFORM_PATTERNS = {
    'superrare': {
        'domains': ['superrare.com'],
        'url_patterns': [r'superrare\.com/([^/]+)$', r'superrare\.com/@([^/]+)'],
        'priority': 1,  # 1 = highest priority
        'requires_selenium': True,
        'specialized_scraper': True
    },
    'foundation': {
        'domains': ['foundation.app', 'foundation.xyz'],
        'url_patterns': [r'foundation\.(app|xyz)/([^/]+)', r'foundation\.(app|xyz)/collection/([^/]+)'],
        'priority': 1,
        'requires_selenium': True,
        'specialized_scraper': True
    },
    'opensea': {
        'domains': ['opensea.io'],
        'url_patterns': [r'opensea\.io/([^/]+)$', r'opensea\.io/collection/([^/]+)'],
        'priority': 1,
        'requires_selenium': True,
        'specialized_scraper': True
    },
    'objkt': {
        'domains': ['objkt.com'],
        'url_patterns': [r'objkt\.com/profile/([^/]+)', r'objkt\.com/collection/([^/]+)'],
        'priority': 1,
        'requires_selenium': True,
        'specialized_scraper': True
    },
    'zora': {
        'domains': ['zora.co'],
        'url_patterns': [r'zora\.co/([^/]+)', r'zora\.co/collect/([^/]+)'],
        'priority': 2,
        'requires_selenium': True,
        'specialized_scraper': False  # Will use generic Selenium scraper
    },
    'knownorigin': {
        'domains': ['knownorigin.io'],
        'url_patterns': [r'knownorigin\.io/([^/]+)'],
        'priority': 2,
        'requires_selenium': True,
        'specialized_scraper': False
    },
    'manifold': {
        'domains': ['gallery.manifold.xyz', 'manifold.xyz'],
        'url_patterns': [r'manifold\.xyz/([^/]+)'],
        'priority': 2,
        'requires_selenium': True,
        'specialized_scraper': False
    },
    'generic': {
        'domains': [],  # Fallback for any site
        'url_patterns': [],
        'priority': 10,  # Lowest priority
        'requires_selenium': False,
        'specialized_scraper': False
    }
}


def detect_platform(url: str) -> Tuple[str, Dict]:
    """
    Detect which NFT/art platform the URL belongs to

    Returns:
        Tuple of (platform_name, platform_config)
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')

    # Check each platform
    for platform_name, config in sorted(PLATFORM_PATTERNS.items(), key=lambda x: x[1]['priority']):
        # Check domain match
        if any(d in domain for d in config['domains']):
            print(f"✓ Detected platform: {platform_name.upper()}")
            return platform_name, config

        # Check URL pattern match
        for pattern in config['url_patterns']:
            if re.search(pattern, url, re.IGNORECASE):
                print(f"✓ Detected platform: {platform_name.upper()}")
                return platform_name, config

    # Default to generic
    print(f"⚠ Unknown platform, using generic scraper")
    return 'generic', PLATFORM_PATTERNS['generic']


# ============================================================================
# SCRAPE VALIDATION
# ============================================================================

class ScrapeValidator:
    """Validates scrape results for accuracy and completeness"""

    @staticmethod
    def validate(scrape_result: Dict, platform: str) -> Dict:
        """
        Validate scrape results

        Returns:
            {
                'valid': bool,
                'score': float (0-1),
                'issues': List[str],
                'metrics': Dict
            }
        """
        issues = []
        metrics = {}

        # Extract data
        nfts = scrape_result.get('nfts', [])
        artist = scrape_result.get('artist', '')

        # Metric 1: NFT count
        nft_count = len(nfts)
        metrics['nft_count'] = nft_count

        if nft_count == 0:
            issues.append("No NFTs extracted")
        elif nft_count < 5:
            issues.append(f"Low NFT count: {nft_count} (may be incomplete)")

        # Metric 2: Image quality
        valid_images = 0
        profile_pics = 0
        ui_elements = 0

        for nft in nfts:
            img_url = nft.get('image_url', '')
            title = nft.get('title', '')
            alt_text = nft.get('alt_text', '')

            # Check if image looks like NFT artwork
            if ScrapeValidator.is_valid_nft_image(img_url, title, alt_text, platform):
                valid_images += 1
            else:
                # Check if it looks like profile pic or UI
                if ScrapeValidator.looks_like_profile_pic(img_url, alt_text):
                    profile_pics += 1
                else:
                    ui_elements += 1

        metrics['valid_images'] = valid_images
        metrics['profile_pics'] = profile_pics
        metrics['ui_elements'] = ui_elements

        if profile_pics > 0:
            issues.append(f"Contains {profile_pics} profile pictures/avatars (should be 0)")

        if ui_elements > nft_count * 0.2:  # More than 20% UI elements
            issues.append(f"Contains {ui_elements} UI elements (may be scraping wrong content)")

        # Metric 3: Metadata completeness
        titles_present = sum(1 for nft in nfts if nft.get('title') and len(nft['title']) > 3)
        artwork_urls_present = sum(1 for nft in nfts if nft.get('artwork_url'))

        metrics['titles_present'] = titles_present
        metrics['artwork_urls_present'] = artwork_urls_present

        if titles_present < nft_count * 0.5:  # Less than 50% have titles
            issues.append(f"Only {titles_present}/{nft_count} NFTs have titles")

        # Metric 4: Artist attribution
        if not artist or len(artist) < 2:
            issues.append("No artist name extracted")

        # Calculate score (0-1)
        score = 0.0

        # Weight: NFT count (0-0.3)
        if nft_count >= 10:
            score += 0.3
        elif nft_count >= 5:
            score += 0.2
        elif nft_count >= 1:
            score += 0.1

        # Weight: Image quality (0-0.4)
        if nft_count > 0:
            image_quality_ratio = valid_images / nft_count
            score += image_quality_ratio * 0.4

        # Weight: Metadata completeness (0-0.2)
        if nft_count > 0:
            title_ratio = titles_present / nft_count
            score += title_ratio * 0.2

        # Weight: No profile pics/UI (0-0.1)
        if profile_pics == 0 and ui_elements == 0:
            score += 0.1

        # Valid if score >= 0.7
        valid = score >= 0.7 and len(issues) == 0

        return {
            'valid': valid,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    @staticmethod
    def is_valid_nft_image(img_url: str, title: str, alt_text: str, platform: str) -> bool:
        """Check if image is likely an NFT artwork"""

        url_lower = img_url.lower()

        # Platform-specific patterns
        valid_patterns = {
            'superrare': ['ipfs', 'sr_prod_artworks', 'superrare.myfilebase.com'],
            'foundation': ['ipfs', 'f8n.io', 'foundation.app/img/'],
            'opensea': ['ipfs', 'openseauserdata.com/files', 'seadn.io'],
            'objkt': ['ipfs', 'cloudflare-ipfs.com', 'pinata.cloud'],
            'generic': ['ipfs', 'artwork', 'nft', 'asset']
        }

        patterns = valid_patterns.get(platform, valid_patterns['generic'])

        return any(p in url_lower for p in patterns)

    @staticmethod
    def looks_like_profile_pic(img_url: str, alt_text: str) -> bool:
        """Check if image looks like a profile picture or avatar"""

        url_lower = img_url.lower()
        alt_lower = alt_text.lower() if alt_text else ''

        # URL patterns
        if any(p in url_lower for p in ['avatar', 'profile', 'logo', 'icon', 'badge']):
            return True

        # Alt text patterns
        if alt_text and 'vault' in alt_lower and len(alt_text) < 30:
            return True

        return False


# ============================================================================
# SPECIALIZED SCRAPERS
# ============================================================================

def scrape_with_foundation(url: str) -> Dict:
    """Scrape Foundation.app profile or collection"""
    print(f"\n{'='*70}")
    print(f"Foundation Scraper")
    print(f"{'='*70}")

    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium required for Foundation scraping")

    # Similar structure to SuperRare scraper
    # Foundation uses React with lazy loading
    driver = setup_driver()

    try:
        driver.get(url)
        time.sleep(5)

        # Scroll to load all NFTs
        scroll_to_load_all_nfts(driver, max_scrolls=20)

        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')

        # Foundation-specific selectors
        # NFTs are typically in <a> tags with href="/artwork/..."
        nft_links = soup.find_all('a', href=re.compile(r'/(artwork|nft|token)/'))

        nfts = []
        for link in nft_links[:50]:  # Limit to 50
            img = link.find('img')
            if not img:
                continue

            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # Check if NFT artwork
            if 'ipfs' in img_url.lower() or 'f8n.io' in img_url.lower():
                # Download and store
                try:
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        nfts.append({
                            'image_url': img_url,
                            'image_data': img_response.content,
                            'image_size': len(img_response.content),
                            'title': img.get('alt', f"Artwork {len(nfts) + 1}"),
                            'artwork_url': urljoin(url, link.get('href', '')),
                            'content_type': img_response.headers.get('content-type', 'image/jpeg')
                        })
                except:
                    continue

        # Extract artist from URL
        artist_match = re.search(r'foundation\.(app|xyz)/([^/]+)', url)
        artist = artist_match.group(2) if artist_match else 'unknown'

        return {
            'artist': artist,
            'profile_url': url,
            'nfts': nfts,
            'scraped_at': datetime.now().isoformat(),
            'platform': 'foundation'
        }

    except Exception as e:
        driver.quit()
        raise e


def scrape_with_opensea(url: str) -> Dict:
    """Scrape OpenSea profile or collection"""
    print(f"\n{'='*70}")
    print(f"OpenSea Scraper")
    print(f"{'='*70}")

    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium required for OpenSea scraping")

    # OpenSea is heavily JavaScript-dependent
    driver = setup_driver()

    try:
        driver.get(url)
        time.sleep(8)  # OpenSea needs more time to load

        # Scroll to load all NFTs
        scroll_to_load_all_nfts(driver, max_scrolls=15, scroll_pause=3)

        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')

        # OpenSea-specific selectors
        # Look for asset cards
        nft_cards = soup.find_all(['article', 'div'], class_=re.compile(r'(asset|nft|item).*card', re.I))

        nfts = []
        for card in nft_cards[:50]:
            img = card.find('img')
            if not img:
                continue

            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # OpenSea images are on ipfs or seadn.io
            if 'ipfs' in img_url.lower() or 'seadn.io' in img_url.lower():
                try:
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        # Find title
                        title_elem = card.find(['h3', 'h4', 'h5'])
                        title = title_elem.get_text().strip() if title_elem else f"Artwork {len(nfts) + 1}"

                        # Find link
                        link = card.find('a', href=True)
                        artwork_url = urljoin(url, link['href']) if link else ''

                        nfts.append({
                            'image_url': img_url,
                            'image_data': img_response.content,
                            'image_size': len(img_response.content),
                            'title': title,
                            'artwork_url': artwork_url,
                            'content_type': img_response.headers.get('content-type', 'image/jpeg')
                        })
                except:
                    continue

        # Extract artist/collection from URL
        artist_match = re.search(r'opensea\.io/([^/]+)', url)
        artist = artist_match.group(1) if artist_match else 'unknown'

        return {
            'artist': artist,
            'profile_url': url,
            'nfts': nfts,
            'scraped_at': datetime.now().isoformat(),
            'platform': 'opensea'
        }

    except Exception as e:
        driver.quit()
        raise e


def scrape_with_objkt(url: str) -> Dict:
    """Scrape Objkt.com (Tezos NFT platform)"""
    print(f"\n{'='*70}")
    print(f"Objkt Scraper (Tezos NFTs)")
    print(f"{'='*70}")

    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium required for Objkt scraping")

    driver = setup_driver()

    try:
        driver.get(url)
        time.sleep(5)

        # Scroll to load all NFTs
        scroll_to_load_all_nfts(driver, max_scrolls=20)

        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')

        # Objkt uses IPFS heavily
        images = soup.find_all('img', src=re.compile(r'ipfs|cloudflare-ipfs|pinata'))

        nfts = []
        for img in images[:50]:
            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # Skip small images
            if 'icon' in img_url.lower() or 'avatar' in img_url.lower():
                continue

            try:
                img_response = requests.get(img_url, timeout=15)
                if img_response.status_code == 200 and len(img_response.content) > 20000:  # > 20KB
                    nfts.append({
                        'image_url': img_url,
                        'image_data': img_response.content,
                        'image_size': len(img_response.content),
                        'title': img.get('alt', f"Artwork {len(nfts) + 1}"),
                        'artwork_url': '',
                        'content_type': img_response.headers.get('content-type', 'image/jpeg')
                    })
            except:
                continue

        # Extract artist from URL
        artist_match = re.search(r'objkt\.com/profile/([^/]+)', url)
        artist = artist_match.group(1) if artist_match else 'unknown'

        return {
            'artist': artist,
            'profile_url': url,
            'nfts': nfts,
            'scraped_at': datetime.now().isoformat(),
            'platform': 'objkt'
        }

    except Exception as e:
        driver.quit()
        raise e


def scrape_with_generic_selenium(url: str) -> Dict:
    """Generic Selenium scraper for unknown platforms"""
    print(f"\n{'='*70}")
    print(f"Generic Selenium Scraper")
    print(f"{'='*70}")

    if not SELENIUM_AVAILABLE:
        raise RuntimeError("Selenium required")

    driver = setup_driver()

    try:
        driver.get(url)
        time.sleep(5)

        # Scroll to load content
        scroll_to_load_all_nfts(driver, max_scrolls=10)

        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')

        # Generic: find all images
        images = soup.find_all('img')

        nfts = []
        for img in images[:30]:
            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # Skip obvious UI elements
            if any(p in img_url.lower() for p in ['icon', 'logo', 'avatar', 'badge']):
                continue

            # Make absolute
            img_url = urljoin(url, img_url)

            try:
                img_response = requests.get(img_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                if img_response.status_code == 200 and len(img_response.content) > 10000:
                    nfts.append({
                        'image_url': img_url,
                        'image_data': img_response.content,
                        'image_size': len(img_response.content),
                        'title': img.get('alt', f"Image {len(nfts) + 1}"),
                        'artwork_url': '',
                        'content_type': img_response.headers.get('content-type', 'image/jpeg')
                    })
            except:
                continue

        return {
            'artist': urlparse(url).netloc,
            'profile_url': url,
            'nfts': nfts,
            'scraped_at': datetime.now().isoformat(),
            'platform': 'generic'
        }

    except Exception as e:
        driver.quit()
        raise e


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def setup_driver():
    """Set up Chrome/Brave driver"""
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

    if Path(brave_path).exists():
        options.binary_location = brave_path

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def scroll_to_load_all_nfts(driver, max_scrolls=20, scroll_pause=2):
    """Scroll page to trigger lazy loading"""
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


# ============================================================================
# ORCHESTRATOR
# ============================================================================

def scrape_url_intelligent(url: str, max_attempts: int = 3) -> Dict:
    """
    Intelligently scrape a URL using the best scraper for the platform

    Process:
    1. Detect platform
    2. Try specialized scraper (if available)
    3. Validate results
    4. If validation fails, try fallback scrapers
    5. Return best result

    Returns:
        {
            'platform': str,
            'scrape_data': Dict,
            'validation': Dict,
            'scraper_used': str,
            'attempts': int
        }
    """
    print(f"\n{'='*70}")
    print(f"INTELLIGENT SCRAPER ORCHESTRATOR")
    print(f"URL: {url}")
    print(f"{'='*70}\n")

    # Detect platform
    platform, config = detect_platform(url)

    # Priority order of scrapers to try
    scrapers_to_try = []

    # 1. Platform-specific specialized scraper (highest priority)
    if config['specialized_scraper']:
        if platform == 'superrare' and SUPERRARE_AVAILABLE:
            scrapers_to_try.append(('superrare_specialized', scrape_superrare_profile))
        elif platform == 'foundation':
            scrapers_to_try.append(('foundation_specialized', scrape_with_foundation))
        elif platform == 'opensea':
            scrapers_to_try.append(('opensea_specialized', scrape_with_opensea))
        elif platform == 'objkt':
            scrapers_to_try.append(('objkt_specialized', scrape_with_objkt))

    # 2. Generic Selenium scraper (fallback for JavaScript sites)
    if config['requires_selenium'] and SELENIUM_AVAILABLE:
        scrapers_to_try.append(('generic_selenium', scrape_with_generic_selenium))

    # 3. Generic HTTP scraper (last resort)
    # scrapers_to_try.append(('generic_http', scrape_with_requests))

    if not scrapers_to_try:
        raise RuntimeError("No suitable scrapers available for this URL")

    # Try each scraper in order
    best_result = None
    best_score = 0.0

    for attempt, (scraper_name, scraper_func) in enumerate(scrapers_to_try[:max_attempts], 1):
        print(f"\n→ Attempt {attempt}/{min(max_attempts, len(scrapers_to_try))}: Using {scraper_name}")

        try:
            # Run scraper
            scrape_data = scraper_func(url)

            # Validate results
            print(f"\n→ Validating results...")
            validation = ScrapeValidator.validate(scrape_data, platform)

            print(f"  Score: {validation['score']:.2f}")
            print(f"  Valid: {validation['valid']}")
            print(f"  NFTs: {validation['metrics'].get('nft_count', 0)}")
            print(f"  Issues: {len(validation['issues'])}")

            if validation['issues']:
                for issue in validation['issues']:
                    print(f"    - {issue}")

            # Track best result
            if validation['score'] > best_score:
                best_score = validation['score']
                best_result = {
                    'platform': platform,
                    'scrape_data': scrape_data,
                    'validation': validation,
                    'scraper_used': scraper_name,
                    'attempt': attempt
                }

            # If valid, use this result
            if validation['valid']:
                print(f"\n✓ Validation passed! Using {scraper_name}")
                break

            # If not valid, continue to next scraper
            print(f"\n⚠ Validation failed, trying next scraper...")

        except Exception as e:
            print(f"\n✗ Scraper {scraper_name} failed: {e}")
            continue

    if not best_result:
        raise RuntimeError("All scrapers failed")

    print(f"\n{'='*70}")
    print(f"BEST RESULT")
    print(f"{'='*70}")
    print(f"Platform: {best_result['platform']}")
    print(f"Scraper: {best_result['scraper_used']}")
    print(f"Score: {best_result['validation']['score']:.2f}")
    print(f"NFTs: {best_result['validation']['metrics'].get('nft_count', 0)}")
    print(f"Valid: {best_result['validation']['valid']}")
    print(f"{'='*70}\n")

    return best_result


def save_to_knowledge_base(result: Dict) -> Dict:
    """
    Save orchestrator result to knowledge base

    Unified format for all platforms
    """
    scrape_data = result['scrape_data']
    platform = result['platform']
    validation = result['validation']

    artist = scrape_data.get('artist', 'unknown')
    profile_url = scrape_data.get('profile_url', '')
    nfts = scrape_data.get('nfts', [])

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
    print(f"\n→ Saving {len(nfts)} NFTs...")
    saved_nfts = []

    for idx, nft in enumerate(nfts, 1):
        ext_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        ext = ext_map.get(nft.get('content_type', 'image/jpeg'), '.jpg')

        filename = f"nft_{idx}{ext}"
        img_path = media_dir / filename

        with open(img_path, 'wb') as f:
            f.write(nft['image_data'])

        saved_nfts.append({
            'filename': filename,
            'title': nft.get('title', f"Artwork {idx}"),
            'artist': nft.get('artist', artist),
            'artwork_url': nft.get('artwork_url', ''),
            'description': nft.get('description', ''),
            'original_url': nft.get('image_url', ''),
            'size_bytes': nft.get('image_size', 0)
        })

    # Create frontmatter
    frontmatter = {
        'id': doc_id,
        'source': 'web_import',
        'type': f'{platform}_collection',
        'platform': platform,
        'url': profile_url,
        'domain': urlparse(profile_url).netloc,
        'title': f'{artist} | {platform.title()} Collection',
        'artist': artist,
        'created_at': datetime.now().isoformat(),
        'scraped_date': datetime.now().strftime('%Y-%m-%d'),
        'has_images': True,
        'image_count': len(saved_nfts),
        'nft_count': len(saved_nfts),
        'scraper_used': result['scraper_used'],
        'validation_score': validation['score'],
        'tags': ['web_import', platform, 'nft', 'blockchain', artist.lower()]
    }

    # Create markdown
    markdown = f"""# {artist} | {platform.title()} NFT Collection

**Source:** [{urlparse(profile_url).netloc}]({profile_url})
**Platform:** {platform.title()}
**Imported:** {datetime.now().strftime('%B %d, %Y')}
**NFT Artworks:** {len(saved_nfts)}
**Scraper:** {result['scraper_used']}
**Validation Score:** {validation['score']:.2f}/1.00

## Collection

This collection contains {len(saved_nfts)} NFT artworks by {artist} from their {platform.title()} profile.

---

## NFT Artworks

"""

    for idx, nft in enumerate(saved_nfts, 1):
        markdown += f"""### {idx}. {nft['title']}

![{nft['title']}](../../knowledge_base/media/web_imports/{doc_id}/{nft['filename']})

**Artist:** {nft['artist']}
"""
        if nft['artwork_url']:
            markdown += f"**View on {platform.title()}:** [{nft['title']}]({nft['artwork_url']})\n"

        markdown += f"""
**Metadata:**
- Original URL: {nft['original_url']}
- File Size: {nft['size_bytes']:,} bytes

---

"""

    markdown += f"""
## Scrape Information

- Platform: {platform.title()}
- Scraper Used: {result['scraper_used']}
- Validation Score: {validation['score']:.2f}/1.00
- Valid: {validation['valid']}
- Scraped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Save markdown
    md_filename = f"web_{doc_id}_{timestamp}.md"
    md_path = processed_dir / md_filename

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True))
        f.write('---\n\n')
        f.write(markdown)

    # Save JSON
    json_filename = f"web_{doc_id}_{timestamp}.json"
    json_path = raw_dir / json_filename

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            **frontmatter,
            'nfts': saved_nfts,
            'validation': validation,
            'scrape_metadata': scrape_data
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved markdown: {md_path}")
    print(f"✓ Saved JSON: {json_path}")

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
        print("Usage: python scraper_orchestrator.py <url>")
        print("\nSupported platforms:")
        print("  - SuperRare (superrare.com)")
        print("  - Foundation (foundation.app)")
        print("  - OpenSea (opensea.io)")
        print("  - Objkt (objkt.com) - Tezos")
        print("  - Zora (zora.co)")
        print("  - Known Origin (knownorigin.io)")
        print("  - Manifold (manifold.xyz)")
        print("  - Generic web pages (fallback)")
        print("\nExample:")
        print("  python scripts/collectors/scraper_orchestrator.py http://superrare.com/founder")
        return

    url = sys.argv[1]

    try:
        # Run intelligent scraping
        result = scrape_url_intelligent(url, max_attempts=3)

        # Save to knowledge base
        save_result = save_to_knowledge_base(result)

        print(f"\n{'='*70}")
        print(f"SUCCESS!")
        print(f"{'='*70}")
        print(f"Platform: {result['platform']}")
        print(f"Scraper: {result['scraper_used']}")
        print(f"NFTs: {save_result['nft_count']}")
        print(f"Validation: {result['validation']['score']:.2f}/1.00")
        print(f"Document: {save_result['doc_id']}")
        print(f"\nView in Visual Translator:")
        print(f"  http://localhost:5001/visual-translator")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
