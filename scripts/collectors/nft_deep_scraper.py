#!/usr/bin/env python3
"""
NFT Deep Scraper

Scrapes individual NFT pages to extract IPFS metadata URIs,
then fetches and links the full blockchain data.
"""
import re
import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional

# Try to import Selenium for JavaScript-rendered pages
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. JavaScript-rendered content may be missed.")


def find_nft_links_in_page(url: str, soup: BeautifulSoup) -> List[str]:
    """
    Find links to individual NFT pages

    For 1stDibs: /nft/creation/GISELXFLOREZ/...
    """
    nft_links = []

    # Find all links
    for link in soup.find_all('a', href=True):
        href = link['href']

        # 1stDibs NFT pattern
        if '/nft/creation/' in href or '/nft/GISELXFLOREZ/' in href:
            full_url = urljoin(url, href)
            nft_links.append(full_url)

    return list(set(nft_links))  # Remove duplicates


def scrape_ipfs_metadata_uri_from_nft_page(url: str) -> Optional[str]:
    """
    Scrape an individual NFT page to find the IPFS metadata URI

    Looks for:
    - IPFS links in the HTML
    - Metadata embedded in JavaScript
    - API endpoints
    """
    print(f"\n→ Scraping NFT page: {url}")

    try:
        # Use Selenium if available (for JavaScript-rendered content)
        if SELENIUM_AVAILABLE:
            return scrape_with_selenium(url)
        else:
            return scrape_with_requests(url)

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def scrape_with_requests(url: str) -> Optional[str]:
    """Scrape using requests (for static HTML)"""
    response = requests.get(url, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0'
    })

    if response.status_code != 200:
        print(f"  ✗ Failed to fetch: HTTP {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Look for IPFS links in the page
    ipfs_uri = find_ipfs_in_html(soup, response.text)

    if ipfs_uri:
        print(f"  ✓ Found IPFS URI: {ipfs_uri}")
        return ipfs_uri

    print(f"  ✗ No IPFS metadata URI found")
    return None


def scrape_with_selenium(url: str) -> Optional[str]:
    """Scrape using Selenium (for JavaScript-rendered content)"""
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    # Try Brave browser first (user preference)
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

    if Path(brave_path).exists():
        options.binary_location = brave_path

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(url)

        # Wait for page to load
        time.sleep(5)

        # Get page source after JavaScript execution
        page_source = driver.page_source

        # Close browser
        driver.quit()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Look for IPFS links
        ipfs_uri = find_ipfs_in_html(soup, page_source)

        if ipfs_uri:
            print(f"  ✓ Found IPFS URI: {ipfs_uri}")
            return ipfs_uri

    except Exception as e:
        print(f"  ✗ Selenium error: {e}")

    print(f"  ✗ No IPFS metadata URI found")
    return None


def find_ipfs_in_html(soup: BeautifulSoup, page_source: str) -> Optional[str]:
    """
    Find IPFS metadata URI in HTML content

    Looks for:
    - ipfs:// URIs
    - IPFS gateway URLs
    - Metadata embedded in <meta> tags
    - JavaScript data objects
    """
    # Pattern 1: Direct ipfs:// links
    ipfs_protocol_match = re.search(r'ipfs://([Qm][1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]{50,})', page_source)
    if ipfs_protocol_match:
        return f"ipfs://{ipfs_protocol_match.group(1)}"

    # Pattern 2: IPFS gateway URLs
    ipfs_gateway_match = re.search(r'https?://[^/]+/ipfs/([Qm][1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]{50,})', page_source)
    if ipfs_gateway_match:
        return f"ipfs://{ipfs_gateway_match.group(1)}"

    # Pattern 3: Metadata in <meta> tags
    meta_tags = soup.find_all('meta', attrs={'property': re.compile('og:|twitter:')})
    for meta in meta_tags:
        content = meta.get('content', '')
        if 'ipfs' in content.lower():
            ipfs_match = re.search(r'(ipfs://[Qm][1-9A-HJ-NP-Za-km-z]{44}|ipfs://bafy[a-z2-7]{50,})', content)
            if ipfs_match:
                return ipfs_match.group(1)

    # Pattern 4: JavaScript data (e.g., window.__INITIAL_STATE__)
    script_tags = soup.find_all('script')
    for script in script_tags:
        if script.string:
            ipfs_match = re.search(r'ipfs://([Qm][1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]{50,})', script.string)
            if ipfs_match:
                return f"ipfs://{ipfs_match.group(1)}"

    return None


def enhance_document_with_deep_nft_data(md_file_path: Path):
    """
    Enhance an existing web import document by scraping individual NFT pages
    to get IPFS metadata URIs
    """
    print(f"\n{'='*60}")
    print(f"Deep scraping NFT data for: {md_file_path.name}")
    print(f"{'='*60}")

    # Read document
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter
    parts = content.split('---', 2)
    if len(parts) >= 3:
        import yaml
        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2]
    else:
        print("✗ Could not parse frontmatter")
        return

    doc_url = frontmatter.get('url')
    if not doc_url:
        print("✗ No URL in frontmatter")
        return

    # Fetch the profile page again
    print(f"\n→ Fetching profile page: {doc_url}")
    response = requests.get(doc_url, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0'
    })

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all NFT links
    nft_links = find_nft_links_in_page(doc_url, soup)

    print(f"\n✓ Found {len(nft_links)} NFT links")

    if not nft_links:
        print("✗ No NFT links found on profile page")
        return

    # Scrape each NFT page
    nft_metadata_uris = {}

    for nft_url in nft_links[:10]:  # Limit to 10 NFTs
        ipfs_uri = scrape_ipfs_metadata_uri_from_nft_page(nft_url)

        if ipfs_uri:
            # Try to match NFT URL to token ID from the document
            # Extract token ID from URL or page
            token_id_match = re.search(r'/(\d+)/?$', nft_url)
            if token_id_match:
                token_id = token_id_match.group(1)
                nft_metadata_uris[token_id] = ipfs_uri

        time.sleep(2)  # Be polite to the server

    # Update the document with metadata URIs
    if nft_metadata_uris:
        print(f"\n✓ Found IPFS metadata URIs for {len(nft_metadata_uris)} NFTs")

        # Store in frontmatter
        frontmatter['nft_metadata_uris'] = nft_metadata_uris

        # Reconstruct and save
        import yaml
        new_content = "---\n"
        new_content += yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        new_content += "---"
        new_content += body

        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✓ Updated document with IPFS metadata URIs")

        # Now run the blockchain extractor to fetch IPFS content
        print(f"\n→ Running blockchain extractor to fetch IPFS content...")
        import subprocess
        subprocess.run([
            'python',
            'scripts/processors/blockchain_nft_extractor.py',
            str(md_file_path)
        ])

    else:
        print("✗ No IPFS metadata URIs found")


def main():
    """Main execution"""
    import sys

    if len(sys.argv) > 1:
        md_file = Path(sys.argv[1])
        if md_file.exists():
            enhance_document_with_deep_nft_data(md_file)
        else:
            print(f"✗ File not found: {md_file}")
    else:
        print("Usage: python nft_deep_scraper.py <markdown_file>")
        print("\nExample:")
        print("  python scripts/collectors/nft_deep_scraper.py knowledge_base/processed/about_web_imports/web_b83efdaa502f_20260103_010848.md")


if __name__ == "__main__":
    main()
