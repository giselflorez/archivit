#!/usr/bin/env python3
"""
Foundation.app NFT Scraper

Specialized scraper for Foundation NFT platform profiles with full Selenium support.
"""
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def scrape_foundation_profile(url: str):
    """
    Scrape a Foundation.app profile page with Selenium

    Foundation is heavily JavaScript-rendered, requiring browser automation.
    """
    print(f"\n{'='*60}")
    print(f"Foundation.app NFT Scraper")
    print(f"{'='*60}")
    print(f"Profile URL: {url}\n")

    # Set up Chrome/Brave options
    options = Options()
    options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    # Run headless for faster scraping
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

    # Use local ChromeDriver
    chromedriver_path = Path.home() / "chromedriver/chromedriver-mac-arm64/chromedriver"

    if chromedriver_path.exists():
        service = Service(str(chromedriver_path))
    else:
        print("Warning: ChromeDriver not found at ~/chromedriver/")
        print("Using system chromedriver...")
        service = Service()

    driver = webdriver.Chrome(service=service, options=options)

    try:
        print("→ Loading page with Selenium...")
        driver.get(url)

        # Wait for initial load
        print("→ Waiting for page to load...")
        time.sleep(5)

        # Scroll to trigger lazy-loaded images
        print("→ Scrolling to load all images...")
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, {(i+1) * 1000});")
            time.sleep(2)

        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        print("→ Extracting page content...")

        # Get page title
        title = driver.title
        print(f"  Title: {title}")

        # Get page source
        html = driver.page_source

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract bio/description
        description = ""
        bio_selectors = [
            'div[class*="bio"]',
            'div[class*="description"]',
            'p[class*="bio"]',
            'section[class*="profile"]',
        ]

        for selector in bio_selectors:
            bio_elem = soup.select_one(selector)
            if bio_elem:
                description = bio_elem.get_text(strip=True)
                break

        if not description:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all('p')
            if paragraphs:
                description = '\n\n'.join([p.get_text(strip=True) for p in paragraphs[:3] if p.get_text(strip=True)])

        print(f"  Description: {description[:100]}..." if description else "  Description: Not found")

        # Find all images
        images = soup.find_all('img')
        print(f"\n✓ Found {len(images)} <img> tags")

        # Filter NFT images (skip profile pics, icons, etc.)
        nft_images = []

        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')

            if not src:
                continue

            # Skip if icon/avatar/logo
            if any(skip in src.lower() for skip in ['icon', 'avatar', 'logo', 'profile']):
                continue

            # Skip tiny images
            if 'resize=w:50' in src or 'resize=w:100' in src:
                continue

            # Get metadata
            alt = img.get('alt', '')
            title_attr = img.get('title', '')

            nft_images.append({
                'src': src,
                'alt': alt,
                'title': title_attr
            })

        print(f"✓ Filtered to {len(nft_images)} potential NFT images")

        # Display found images
        if nft_images:
            print("\nFound NFT images:")
            for i, img in enumerate(nft_images[:10], 1):
                print(f"  {i}. {img['src'][:80]}...")
                if img['alt']:
                    print(f"     Alt: {img['alt']}")
        else:
            print("\n⚠ No NFT images found!")
            print("\nDebugging: All images on page:")
            for i, img in enumerate(images[:20], 1):
                src = img.get('src', 'NO SRC')
                alt = img.get('alt', 'NO ALT')
                print(f"  {i}. {src[:100]}")
                print(f"     Alt: {alt}")

        # Save screenshot for debugging
        screenshot_path = Path("debug_foundation_screenshot.png")
        driver.save_screenshot(str(screenshot_path))
        print(f"\n→ Screenshot saved to: {screenshot_path}")

        # Save HTML for debugging
        html_path = Path("debug_foundation.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"→ HTML saved to: {html_path}")

        return {
            'title': title,
            'description': description,
            'images': nft_images,
            'total_img_tags': len(images)
        }

    finally:
        driver.quit()


def main():
    """Main execution"""
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default: your Foundation profile
        url = "https://foundation.app/@founder"

    result = scrape_foundation_profile(url)

    print(f"\n{'='*60}")
    print(f"Scraping Results:")
    print(f"{'='*60}")
    print(f"Title: {result['title']}")
    print(f"Description: {result['description'][:200]}..." if result['description'] else "Description: None")
    print(f"Total <img> tags: {result['total_img_tags']}")
    print(f"NFT images found: {len(result['images'])}")

    if result['images']:
        print(f"\n✓ Successfully found NFT images!")
        print(f"\nCheck debug_foundation.html and debug_foundation_screenshot.png for details")
    else:
        print(f"\n✗ No NFT images found")
        print(f"Check debug files to see what the page looks like")


if __name__ == "__main__":
    main()
