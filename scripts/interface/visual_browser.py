#!/usr/bin/env python3
"""
Visual Browser - Web interface for exploring knowledge base with images
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for
import json
import re
import hashlib
import yaml
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time

# Selenium imports for JavaScript-rendered pages
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. JavaScript-rendered pages may not scrape correctly.")

# Import search functionality
from processors.embeddings_generator import load_index

# Import visual translator
try:
    from processors.visual_translator import analyze_image, load_cached_analysis
    VISUAL_TRANSLATOR_AVAILABLE = True
except ImportError:
    VISUAL_TRANSLATOR_AVAILABLE = False
    print("Warning: Visual translator not available")

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Load embeddings index
embeddings = None

def get_global_source_counts():
    """Get source counts for all documents (used in navigation)"""
    try:
        all_documents = get_all_documents(limit=1000, filter_type='all')
        source_counts = {}
        visual_count = 0

        for doc in all_documents:
            source = doc['source']
            source_counts[source] = source_counts.get(source, 0) + 1
            if doc.get('has_visual'):
                visual_count += 1

        # Add total and visual counts
        source_counts['all'] = len(all_documents)
        source_counts['visual'] = visual_count

        return source_counts
    except Exception as e:
        print(f"Warning: Could not get source counts: {e}")
        return {}

@app.context_processor
def inject_global_counts():
    """Make source counts available to all templates"""
    return {
        'source_counts': get_global_source_counts()
    }

def init_embeddings():
    """Initialize embeddings index"""
    global embeddings
    try:
        config_path = Path("config/settings.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        embeddings = load_index(config)
        print("✓ Embeddings index loaded")
    except Exception as e:
        print(f"Warning: Could not load embeddings: {e}")
        embeddings = None

def parse_markdown_file(filepath):
    """Parse markdown file and extract frontmatter and content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            import yaml
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()

    return frontmatter, body

def search_knowledge_base(query, limit=20):
    """Search knowledge base and return results with images"""
    if not embeddings or not query:
        return []

    try:
        # Search using txtai
        results = embeddings.search(query, limit=limit)

        enriched_results = []

        for score, doc_id in results:
            # Find the markdown file for this doc_id
            kb_path = Path("knowledge_base/processed")
            for md_file in kb_path.rglob("*.md"):
                frontmatter, body = parse_markdown_file(md_file)

                if frontmatter.get('id') == doc_id:
                    # Extract images from the markdown
                    images = re.findall(r'!\[.*?\]\((.*?)\)', body)

                    # Get media files from all possible media directories
                    media_files = []
                    media_dirs = [
                        Path("knowledge_base/media/instagram") / doc_id,
                        Path("knowledge_base/media/web_imports") / doc_id,
                        Path("knowledge_base/media/attachments") / doc_id
                    ]

                    for media_dir in media_dirs:
                        if media_dir.exists():
                            for img_file in media_dir.glob("*"):
                                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                    media_files.append(str(img_file))

                    # Get preview text
                    preview = body[:300].replace('\n', ' ').strip()

                    enriched_results.append({
                        'id': doc_id,
                        'score': float(score),
                        'source': frontmatter.get('source', 'unknown'),
                        'type': frontmatter.get('type', 'unknown'),
                        'title': get_title_from_markdown(body),
                        'preview': preview,
                        'date': frontmatter.get('created_at', frontmatter.get('post_date', '')),
                        'tags': frontmatter.get('tags', []),
                        'images': images,
                        'media_files': media_files,
                        'filepath': str(md_file),
                        'has_visual': len(images) > 0 or len(media_files) > 0
                    })
                    break

        return enriched_results

    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_title_from_markdown(markdown_text):
    """Extract title from markdown"""
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"

def get_all_documents(limit=50, filter_type=None, sort_by=None):
    """Get all documents from knowledge base"""
    kb_path = Path("knowledge_base/processed")
    documents = []

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)

            doc_type = frontmatter.get('type', 'unknown')
            source = frontmatter.get('source', 'unknown')

            # Apply filter
            if filter_type and filter_type != 'all':
                if filter_type == 'visual':
                    # Check if has images
                    images = re.findall(r'!\[.*?\]\((.*?)\)', body)
                    media_dir = Path("knowledge_base/media/instagram") / frontmatter.get('id', '')
                    has_media = media_dir.exists() and any(media_dir.glob("*"))
                    if not (images or has_media):
                        continue
                elif source != filter_type:
                    continue

            # Extract images
            images = re.findall(r'!\[.*?\]\((.*?)\)', body)

            # Get media files from all possible media directories
            media_files = []
            doc_id = frontmatter.get('id', '')
            media_dirs = [
                Path("knowledge_base/media/instagram") / doc_id,
                Path("knowledge_base/media/web_imports") / doc_id,
                Path("knowledge_base/media/attachments") / doc_id
            ]

            for media_dir in media_dirs:
                if media_dir.exists():
                    for img_file in media_dir.glob("*"):
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            media_files.append(str(img_file))

            preview = body[:300].replace('\n', ' ').strip()

            # Extract marketplace/IPFS links from body
            marketplace_url = frontmatter.get('url', '')
            ipfs_links = re.findall(r'(ipfs://[^\s\)]+)', body)
            ipfs_gateways = re.findall(r'(https://(?:ipfs\.io|gateway\.pinata\.cloud)/ipfs/[^\s\)]+)', body)

            # Extract original image URLs from markdown (handle both formats)
            image_urls = []
            image_url_matches = re.findall(r'\*\*Original URL:\*\* (https?://[^\n]+)', body)
            image_urls.extend(image_url_matches)
            # Also try alternate format
            alt_matches = re.findall(r'Original URL: (https?://[^\n]+)', body)
            image_urls.extend(alt_matches)

            documents.append({
                'id': frontmatter.get('id', ''),
                'source': source,
                'type': doc_type,
                'title': get_title_from_markdown(body),
                'preview': preview,
                'date': frontmatter.get('created_at', frontmatter.get('post_date', '')),
                'tags': frontmatter.get('tags', []),
                'images': images,
                'media_files': media_files,
                'filepath': str(md_file),
                'has_visual': len(images) > 0 or len(media_files) > 0,
                'marketplace_url': marketplace_url,
                'ipfs_links': ipfs_links,
                'ipfs_gateways': ipfs_gateways,
                'image_urls': image_urls,
                'domain': frontmatter.get('domain', '')
            })

        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            continue

    # Apply sorting
    if sort_by == 'date_desc' or not sort_by:
        # Default: newest first
        documents.sort(key=lambda x: x.get('date', ''), reverse=True)
    elif sort_by == 'date_asc':
        # Oldest first
        documents.sort(key=lambda x: x.get('date', ''), reverse=False)
    elif sort_by == 'title_asc':
        # Title A-Z
        documents.sort(key=lambda x: x.get('title', '').lower())
    elif sort_by == 'title_desc':
        # Title Z-A
        documents.sort(key=lambda x: x.get('title', '').lower(), reverse=True)
    elif sort_by == 'source':
        # Group by source
        documents.sort(key=lambda x: (x.get('source', ''), x.get('date', '')), reverse=True)
    elif sort_by == 'tags':
        # Most tagged first (by tag count, then date)
        documents.sort(key=lambda x: (len(x.get('tags', [])), x.get('date', '')), reverse=True)
    elif sort_by == 'untagged':
        # Untagged first (by tag count ascending, then date)
        documents.sort(key=lambda x: (len(x.get('tags', [])), x.get('date', '')), reverse=False)

    return documents[:limit]

@app.route('/')
def index():
    """Main page"""
    filter_type = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'date_desc')
    documents = get_all_documents(limit=100, filter_type=filter_type, sort_by=sort_by)

    # source_counts now available globally via context processor

    return render_template('index.html',
                         documents=documents,
                         current_filter=filter_type,
                         current_sort=sort_by)

@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    results = []

    if query:
        results = search_knowledge_base(query, limit=50)

    return render_template('search.html', query=query, results=results)

@app.route('/document/<doc_id>')
def document_detail(doc_id):
    """View full document"""
    kb_path = Path("knowledge_base/processed")

    for md_file in kb_path.rglob("*.md"):
        frontmatter, body = parse_markdown_file(md_file)

        if frontmatter.get('id') == doc_id:
            # Get media files from all possible media directories
            media_files = []
            model_files = []
            media_dirs = [
                Path("knowledge_base/media/instagram") / doc_id,
                Path("knowledge_base/media/web_imports") / doc_id,
                Path("knowledge_base/media/attachments") / doc_id,
                Path("knowledge_base/media/google_drive") / doc_id,
                Path("knowledge_base/attachments") / doc_id
            ]

            for media_dir in media_dirs:
                if media_dir.exists():
                    for file in media_dir.glob("*"):
                        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            media_files.append({
                                'filename': file.name,
                                'path': str(file)  # Relative path from project root
                            })
                        elif file.suffix.lower() in ['.glb', '.gltf']:
                            model_files.append({
                                'filename': file.name,
                                'path': str(file),
                                'type': file.suffix.lower()[1:]  # 'glb' or 'gltf'
                            })

            return render_template('document.html',
                                 frontmatter=frontmatter,
                                 body=body,
                                 media_files=media_files,
                                 model_files=model_files)

    return "Document not found", 404

@app.route('/api/document/<doc_id>/delete-images', methods=['POST'])
def delete_document_images(doc_id):
    """Delete specific images from a document"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])

        if not filenames:
            return jsonify({'error': 'No filenames provided'}), 400

        # Find all media directories for this document
        media_base = Path("knowledge_base/media")
        deleted_count = 0

        if media_base.exists():
            for media_type_dir in media_base.iterdir():
                if media_type_dir.is_dir():
                    doc_media_dir = media_type_dir / doc_id
                    if doc_media_dir.exists():
                        for filename in filenames:
                            file_path = doc_media_dir / filename
                            if file_path.exists():
                                file_path.unlink()
                                deleted_count += 1

        return jsonify({'success': True, 'deleted': deleted_count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/<doc_id>/update', methods=['POST'])
def update_document(doc_id):
    """Update document content and tags"""
    try:
        data = request.get_json()
        new_body = data.get('body', '')
        new_tags = data.get('tags', [])

        kb_path = Path("knowledge_base/processed")

        for md_file in kb_path.rglob("*.md"):
            frontmatter, body = parse_markdown_file(md_file)

            if frontmatter.get('id') == doc_id:
                # Update frontmatter
                frontmatter['tags'] = new_tags

                # Write back to file
                new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---\n\n{new_body}"

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return jsonify({'success': True})

        return jsonify({'error': 'Document not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/media/<path:filepath>')
def serve_media(filepath):
    """Serve media files securely"""
    # Get absolute path to project root
    project_root = Path(__file__).parent.parent.parent

    # Construct full path and resolve it to prevent directory traversal
    full_path = (project_root / filepath).resolve()

    # Security check: ensure the resolved path is within project root
    try:
        full_path.relative_to(project_root)
    except ValueError:
        return "Access denied", 403

    # Check if file exists
    if not full_path.is_file():
        return "File not found", 404

    # Serve the file
    return send_from_directory(full_path.parent, full_path.name)

@app.route('/api/stats')
def api_stats():
    """Get knowledge base statistics"""
    kb_path = Path("knowledge_base/processed")
    total_docs = len(list(kb_path.rglob("*.md")))

    # Count by source
    sources = {}
    visual_count = 0

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            source = frontmatter.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            # Check if has visual content
            images = re.findall(r'!\[.*?\]\((.*?)\)', body)
            media_dir = Path("knowledge_base/media/instagram") / frontmatter.get('id', '')
            if images or (media_dir.exists() and any(media_dir.glob("*"))):
                visual_count += 1
        except:
            continue

    return jsonify({
        'total_documents': total_docs,
        'visual_documents': visual_count,
        'sources': sources
    })

@app.route('/add-content', methods=['GET', 'POST'])
def add_content():
    """Add content from URL"""
    if request.method == 'POST':
        url = request.form.get('url')
        title = request.form.get('title')
        notes = request.form.get('notes', '')
        manual_content = request.form.get('manual_content', '')
        source_type = request.form.get('source_type', 'web_import')
        extract_images = request.form.get('extract_images') == 'on'
        crawl_site = request.form.get('crawl_site') == 'on'

        try:
            # Scrape the URL
            doc_id = scrape_and_save_url(url, title, notes, source_type, extract_images, manual_content, crawl_site)

            return render_template('add_content.html', success=True, doc_id=doc_id)
        except Exception as e:
            return render_template('add_content.html', error=str(e))

    return render_template('add_content.html')

@app.route('/api/preview-url')
def preview_url():
    """Preview a URL before importing"""
    url = request.args.get('url')

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get title
        title = ''
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()

        # Get preview text
        preview = ''
        for p in soup.find_all('p')[:3]:
            preview += p.get_text().strip() + ' '

        return jsonify({
            'title': title,
            'preview': preview[:200]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def requires_javascript_rendering(url):
    """Check if URL requires JavaScript rendering (like Claude, ChatGPT, NFT platforms, etc.)"""
    js_heavy_domains = [
        # AI Chat platforms
        'claude.ai',
        'chat.openai.com',
        'chatgpt.com',
        'bard.google.com',
        'gemini.google.com',
        'perplexity.ai',
        'character.ai',
        # NFT Marketplaces (heavily JavaScript-rendered)
        'foundation.app',
        'opensea.io',
        'rarible.com',
        'superrare.com',
        'zora.co',
        'manifold.xyz',
        'exchange.art',
        'objkt.com',
        'fxhash.xyz',
    ]

    domain = urlparse(url).netloc.lower()
    return any(js_domain in domain for js_domain in js_heavy_domains)

def scrape_with_selenium(url, wait_time=5):
    """Use Selenium to scrape JavaScript-rendered pages"""
    if not SELENIUM_AVAILABLE:
        raise Exception("Selenium not available. Install with: pip install selenium webdriver-manager")

    # Set up Brave/Chrome options
    chrome_options = Options()

    # Point to Brave browser binary
    chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Initialize driver with Brave using manually downloaded ChromeDriver
    import os
    chromedriver_path = os.path.expanduser("~/chromedriver/chromedriver-mac-arm64/chromedriver")

    if os.path.exists(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        # Fallback to webdriver-manager
        try:
            service = Service(ChromeDriverManager(driver_version="latest").install())
        except Exception as e:
            print(f"Warning: Could not auto-install driver: {e}")
            service = Service()

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Loading page with Selenium: {url}")
        driver.get(url)

        # Wait for content to load
        time.sleep(wait_time)

        # For NFT platforms, scroll to load images and wait longer
        if any(nft_site in url for nft_site in ['foundation.app', 'opensea.io', 'rarible.com', 'superrare.com']):
            try:
                # Scroll to bottom to trigger lazy-loaded images
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                # Scroll back to top
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                # Wait for images to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )
                print("  → Scrolled page and waited for NFT images to load")
            except:
                print("  → Timeout waiting for images, proceeding with available content")
                pass

        # For Claude conversations, wait for specific elements
        elif 'claude.ai' in url:
            try:
                # Wait for conversation content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except:
                pass

        # Get page title
        title = driver.title

        # Get page source after JavaScript execution
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Extract text content
        content_text = ''
        seen_text = set()  # Track seen text to avoid duplicates

        # For Claude conversations, look for specific content structure
        if 'claude.ai' in url:
            # Try to find conversation messages
            messages = soup.find_all(['div', 'article'], class_=re.compile('message|content|conversation', re.I))

            if messages:
                for msg in messages:
                    text = msg.get_text(separator='\n', strip=True)
                    if text and len(text) > 10 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)
            else:
                # Fallback: get all paragraphs and text blocks
                for element in soup.find_all(['p', 'div', 'article', 'section']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)

        # For NFT platforms, extract structured data
        elif any(nft_site in url for nft_site in ['foundation.app', 'opensea.io', 'rarible.com', 'superrare.com']):
            # Extract bio/description
            bio_selectors = ['p', 'div[class*="bio"]', 'div[class*="description"]']
            for selector in bio_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    # Only add substantial, unique text
                    if text and len(text) > 30 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)

            # Extract NFT titles and metadata
            nft_titles = soup.find_all(['h1', 'h2', 'h3'], class_=re.compile('title|name', re.I))
            for title_elem in nft_titles:
                text = title_elem.get_text(strip=True)
                if text and len(text) > 3 and text not in seen_text:
                    content_text += f"**{text}**\n\n"
                    seen_text.add(text)

        else:
            # Generic extraction for other JS-heavy sites
            main_content = soup.find('main') or soup.find('article') or soup.body
            if main_content:
                for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20 and text not in seen_text:
                        content_text += text + '\n\n'
                        seen_text.add(text)

        print(f"✓ Extracted {len(content_text)} characters with Selenium")

        return title, content_text, soup

    finally:
        driver.quit()

def crawl_website(base_url, max_pages=20):
    """Crawl a website and discover all internal pages"""
    from urllib.parse import urljoin, urlparse

    visited = set()
    to_visit = {base_url}
    discovered_pages = []
    base_domain = urlparse(base_url).netloc

    print(f"Starting site crawl of {base_domain}...")

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop()

        if current_url in visited:
            continue

        visited.add(current_url)
        print(f"  Crawling [{len(visited)}/{max_pages}]: {current_url}")

        try:
            response = requests.get(current_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            discovered_pages.append({
                'url': current_url,
                'soup': soup
            })

            # Find all links on this page
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Make absolute URL
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)

                # Only follow internal links on same domain
                if parsed.netloc == base_domain:
                    # Remove fragments
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"

                    # Skip certain file types and duplicates
                    if not any(ext in clean_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip']):
                        if clean_url not in visited:
                            to_visit.add(clean_url)

        except Exception as e:
            print(f"  Error crawling {current_url}: {e}")
            continue

    print(f"✓ Discovered {len(discovered_pages)} pages")
    return discovered_pages

def scrape_and_save_url(url, custom_title=None, notes='', source_type='web_import', extract_images=True, manual_content='', crawl_site=False):
    """Scrape URL and save to knowledge base"""

    # If crawl_site is enabled, crawl all pages
    all_pages = []
    all_images = []

    if crawl_site and not manual_content.strip():
        pages = crawl_website(url, max_pages=20)
        all_pages = pages

        # Aggregate content from all pages
        content_text = ''
        title = custom_title or urlparse(url).netloc

        for idx, page_data in enumerate(pages):
            page_url = page_data['url']
            soup = page_data['soup']

            # Get page title if not set
            if idx == 0 and not custom_title:
                if soup.title:
                    title = soup.title.string.strip()
                elif soup.find('h1'):
                    title = soup.find('h1').get_text().strip()

            # Add page heading
            page_title = ''
            if soup.title:
                page_title = soup.title.string.strip()
            elif soup.find('h1'):
                page_title = soup.find('h1').get_text().strip()
            else:
                page_title = urlparse(page_url).path or 'Home'

            content_text += f"\n## Page: {page_title}\n"
            content_text += f"URL: {page_url}\n\n"

            # Extract content from this page
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))

            if main_content:
                for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                    text = element.get_text().strip()
                    if text:
                        content_text += text + '\n\n'
            else:
                for p in soup.find_all('p'):
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        content_text += text + '\n\n'

            content_text += "\n---\n\n"

        soup = all_pages[0]['soup'] if all_pages else None

    # If manual content provided, use it
    elif manual_content.strip():
        title = custom_title or urlparse(url).netloc
        content_text = manual_content
        soup = None
    # Check if URL requires JavaScript rendering
    elif requires_javascript_rendering(url):
        print(f"Detected JavaScript-heavy site, using Selenium...")
        title, content_text, soup = scrape_with_selenium(url)

        # Override with custom title if provided
        if custom_title:
            title = custom_title
    else:
        # Fetch the page with standard HTTP request
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        if custom_title:
            title = custom_title
        elif soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        else:
            title = urlparse(url).netloc

        # Extract main content
        content_text = ''

        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))

        if main_content:
            # Get all text from main content
            for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                text = element.get_text().strip()
                if text:
                    content_text += text + '\n\n'
        else:
            # Fallback: get all paragraphs
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short paragraphs
                    content_text += text + '\n\n'

    # Generate doc ID
    doc_id = hashlib.md5(f"{url}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]

    # Extract images if requested (only if we scraped the page)
    saved_images = []
    if extract_images:
        media_dir = Path("knowledge_base/media/web_imports") / doc_id
        media_dir.mkdir(parents=True, exist_ok=True)

        # Collect images from all pages if we crawled the site
        all_img_tags = []
        if crawl_site and all_pages:
            print(f"Extracting images from {len(all_pages)} pages...")
            for page_data in all_pages:
                page_soup = page_data['soup']
                all_img_tags.extend(page_soup.find_all('img'))
        elif soup:
            all_img_tags = soup.find_all('img')

        print(f"Found {len(all_img_tags)} total images, downloading...")

        # Increase limit when crawling entire site
        img_limit = 50 if crawl_site else 10
        unique_img_urls = set()  # Track to avoid duplicates

        for idx, img in enumerate(all_img_tags):
            if len(saved_images) >= img_limit:
                break

            img_url = img.get('src') or img.get('data-src')
            if not img_url:
                continue

            # Make absolute URL
            img_url = urljoin(url, img_url)

            # Skip duplicates
            if img_url in unique_img_urls:
                continue
            unique_img_urls.add(img_url)

            # Skip small images (likely icons/logos)
            if 'icon' in img_url.lower() or 'logo' in img_url.lower():
                continue

            # Skip data URIs that are too small
            if img_url.startswith('data:') and len(img_url) < 1000:
                continue

            try:
                # Download image
                img_response = requests.get(img_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': url
                })

                # Check if actually an image
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    continue

                # Get file extension from content-type or URL
                img_ext = Path(urlparse(img_url).path).suffix
                if not img_ext or img_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    # Determine from content-type
                    ext_map = {
                        'image/jpeg': '.jpg',
                        'image/png': '.png',
                        'image/gif': '.gif',
                        'image/webp': '.webp'
                    }
                    img_ext = ext_map.get(content_type, '.jpg')

                # Extract metadata from HTML
                img_alt = img.get('alt', '')
                img_title = img.get('title', '')
                img_caption = ''

                # Try to find caption (common patterns)
                parent = img.find_parent(['figure', 'div'])
                if parent:
                    caption_elem = parent.find(['figcaption', 'caption', 'p'])
                    if caption_elem:
                        img_caption = caption_elem.get_text().strip()

                # Save image
                img_filename = f"image_{idx}{img_ext}"
                img_path = media_dir / img_filename

                with open(img_path, 'wb') as f:
                    f.write(img_response.content)

                print(f"  ✓ Downloaded: {img_filename} ({len(img_response.content)} bytes)")

                saved_images.append({
                    'filename': img_filename,
                    'path': str(img_path),
                    'original_url': img_url,
                    'alt_text': img_alt,
                    'title': img_title,
                    'caption': img_caption,
                    'size_bytes': len(img_response.content)
                })

                # Auto-analyze with visual translator if enabled
                if VISUAL_TRANSLATOR_AVAILABLE:
                    config_path = Path("config/settings.json")
                    if config_path.exists():
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                        vt_config = config.get('visual_translator', {})

                        if vt_config.get('enabled') and vt_config.get('auto_analyze_on_import'):
                            print(f"  → Analyzing image with Visual Translator...")
                            try:
                                # Skip vision to avoid costs by default, can be enabled
                                skip_vision = not vt_config.get('vision_enabled', False)
                                analysis = analyze_image(img_path, skip_vision=skip_vision)

                                # Store analysis in saved_images metadata
                                if analysis.get('ocr'):
                                    saved_images[-1]['ocr_text'] = analysis['ocr'].get('text', '')
                                    saved_images[-1]['has_text'] = analysis['ocr'].get('has_text', False)
                                if analysis.get('vision'):
                                    saved_images[-1]['vision_description'] = analysis['vision'].get('description', '')

                                print(f"  ✓ Analysis complete")
                            except Exception as e:
                                print(f"  ✗ Analysis failed: {e}")

            except Exception as e:
                print(f"  ✗ Failed to download {img_url}: {e}")
                continue

        print(f"✓ Saved {len(saved_images)} images")

    # Extract tags
    tags = [source_type, 'web_import']

    # Auto-tag based on content
    content_lower = (title + ' ' + content_text).lower()
    tag_keywords = {
        'art': ['art', 'artwork', 'creative', 'artist'],
        'blockchain': ['blockchain', 'crypto', 'nft', 'web3'],
        'technology': ['tech', 'technology', 'digital'],
        'photography': ['photo', 'photography', 'camera'],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)

    # Aggregate image analysis data
    images_with_text = [img for img in saved_images if img.get('has_text')]
    all_ocr_text = '\n\n'.join([img.get('ocr_text', '') for img in images_with_text if img.get('ocr_text')])
    all_vision_descs = [img.get('vision_description', '') for img in saved_images if img.get('vision_description')]

    # Create frontmatter
    now = datetime.now()
    frontmatter = {
        'id': doc_id,
        'source': source_type,
        'type': 'web_import',
        'created_at': now.isoformat(),
        'url': url,
        'title': title,
        'domain': urlparse(url).netloc,
        'scraped_date': now.strftime('%Y-%m-%d'),
        'image_count': len(saved_images),
        'has_images': len(saved_images) > 0,
        'images_with_text': len(images_with_text),
        'tags': list(set(tags))
    }

    # Add visual analysis fields if available
    if all_ocr_text:
        frontmatter['ocr_text'] = all_ocr_text[:1000]  # First 1000 chars for search
        frontmatter['has_text'] = True
    if all_vision_descs:
        frontmatter['vision_description'] = ' | '.join(all_vision_descs)
        frontmatter['visual_analysis_date'] = now.isoformat()

    # Create markdown
    md_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# {title}

**Source:** [{urlparse(url).netloc}]({url})
**Imported:** {now.strftime('%B %d, %Y')}

"""

    if notes:
        md_content += f"""## Your Notes

{notes}

"""

    md_content += f"""## Content

{content_text}

"""

    # Add images section with rich metadata
    if saved_images:
        md_content += "## Images\n\n"
        for idx, img in enumerate(saved_images, 1):
            # Handle both absolute and relative paths
            img_path = Path(img['path'])
            if img_path.is_absolute():
                rel_path = img_path.relative_to(Path.cwd())
            else:
                rel_path = img_path

            md_content += f"### Image {idx}: {img['filename']}\n\n"
            md_content += f"![{img.get('alt_text', img['filename'])}](../../{rel_path})\n\n"

            # Add metadata table
            md_content += "**Metadata:**\n\n"
            md_content += f"- **Original URL:** {img.get('original_url', 'N/A')}\n"
            if img.get('alt_text'):
                md_content += f"- **Alt Text:** {img['alt_text']}\n"
            if img.get('title'):
                md_content += f"- **Title:** {img['title']}\n"
            if img.get('caption'):
                md_content += f"- **Caption:** {img['caption']}\n"
            md_content += f"- **File Size:** {img.get('size_bytes', 0):,} bytes\n"

            # Add OCR results if available
            if img.get('has_text') and img.get('ocr_text'):
                md_content += f"\n**Extracted Text (OCR):**\n\n"
                md_content += f"```\n{img['ocr_text'][:500]}\n```\n"
                if len(img['ocr_text']) > 500:
                    md_content += f"\n*(Showing first 500 characters of {len(img['ocr_text'])} total)*\n"

            # Add vision description if available
            if img.get('vision_description'):
                md_content += f"\n**AI Description:**\n\n"
                md_content += f"> {img['vision_description']}\n"

            md_content += "\n---\n\n"

    md_content += f"""## Source
- Original URL: {url}
- Domain: {urlparse(url).netloc}
- Scraped: {now.strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Save to knowledge base
    subject = 'web_imports'
    processed_dir = Path(f"knowledge_base/processed/about_{subject}")
    processed_dir.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    md_filename = f"web_{doc_id}_{timestamp}.md"
    md_filepath = processed_dir / md_filename

    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Save raw data
    raw_dir = Path("knowledge_base/raw/web_imports")
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_data = {
        'url': url,
        'title': title,
        'content': content_text[:1000],  # Preview only
        'images': saved_images,
        'scraped_at': now.isoformat()
    }

    raw_filepath = raw_dir / f"web_{doc_id}_{timestamp}.json"
    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved web import: {title} (ID: {doc_id})")

    return doc_id

@app.route('/api/delete-documents', methods=['POST'])
def delete_documents():
    """Delete multiple documents"""
    try:
        data = request.get_json()
        doc_ids = data.get('doc_ids', [])

        if not doc_ids:
            return jsonify({'success': False, 'error': 'No document IDs provided'}), 400

        kb_path = Path("knowledge_base/processed")
        deleted_count = 0
        errors = []

        for doc_id in doc_ids:
            try:
                # Find and delete markdown file
                for md_file in kb_path.rglob("*.md"):
                    frontmatter, _ = parse_markdown_file(md_file)

                    if frontmatter.get('id') == doc_id:
                        # Delete the markdown file
                        md_file.unlink()
                        deleted_count += 1

                        # Delete associated media directory if exists
                        media_paths = [
                            Path("knowledge_base/media/instagram") / doc_id,
                            Path("knowledge_base/media/web_imports") / doc_id,
                            Path("knowledge_base/attachments") / doc_id
                        ]

                        for media_path in media_paths:
                            if media_path.exists():
                                import shutil
                                shutil.rmtree(media_path)

                        # Delete raw data if exists
                        raw_paths = [
                            Path("knowledge_base/raw/web_imports"),
                            Path("knowledge_base/raw/perplexity"),
                            Path("knowledge_base/raw/attachments")
                        ]

                        for raw_path in raw_paths:
                            if raw_path.exists():
                                for raw_file in raw_path.glob(f"*{doc_id}*"):
                                    raw_file.unlink()

                        break
            except Exception as e:
                errors.append(f"Error deleting {doc_id}: {str(e)}")

        # Update embeddings index after deletion
        if deleted_count > 0:
            try:
                # Reload the embeddings to reflect deletions
                init_embeddings()
            except Exception as e:
                print(f"Warning: Could not update embeddings: {e}")

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors if errors else None
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/visual-translator')
def visual_translator():
    """Visual translator panel - shows all images with analysis status"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return "Visual Translator not available. Install required packages.", 503

    # Find all images in media directories
    media_base = Path("knowledge_base/media")
    all_images = []

    if media_base.exists():
        for source_dir in media_base.iterdir():
            if source_dir.is_dir():
                for doc_dir in source_dir.iterdir():
                    if doc_dir.is_dir():
                        doc_id = doc_dir.name
                        source = source_dir.name

                        # Find markdown file for this doc
                        md_file = None
                        kb_path = Path("knowledge_base/processed")
                        for md in kb_path.rglob("*.md"):
                            try:
                                frontmatter, _ = parse_markdown_file(md)
                                if frontmatter.get('id') == doc_id:
                                    md_file = md
                                    break
                            except:
                                continue

                        # Get images in this doc directory
                        for img_file in doc_dir.glob("*"):
                            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                # Check if analyzed
                                analyzed = False
                                has_text = False
                                vision_desc = None

                                if md_file:
                                    frontmatter, _ = parse_markdown_file(md_file)
                                    analyzed = 'visual_analysis_date' in frontmatter
                                    has_text = frontmatter.get('has_text', False)
                                    vision_desc = frontmatter.get('vision_description', '')

                                all_images.append({
                                    'path': str(img_file),
                                    'filename': img_file.name,
                                    'doc_id': doc_id,
                                    'source': source,
                                    'analyzed': analyzed,
                                    'has_text': has_text,
                                    'vision_desc': vision_desc[:100] if vision_desc else None
                                })

    # Get filter from query string
    filter_type = request.args.get('filter', 'all')

    # Apply filter
    if filter_type == 'analyzed':
        all_images = [img for img in all_images if img['analyzed']]
    elif filter_type == 'pending':
        all_images = [img for img in all_images if not img['analyzed']]
    elif filter_type == 'has_text':
        all_images = [img for img in all_images if img['has_text']]

    # Calculate stats
    total = len([img for img in all_images if filter_type == 'all' or True])
    analyzed = len([img for img in all_images if img['analyzed']])
    pending = total - analyzed
    with_text = len([img for img in all_images if img['has_text']])

    return render_template('visual_translator.html',
                         images=all_images,
                         total=total,
                         analyzed=analyzed,
                         pending=pending,
                         with_text=with_text,
                         current_filter=filter_type)

@app.route('/visual-translator/image/<doc_id>')
def visual_translator_image(doc_id):
    """Detailed view of single image analysis"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return "Visual Translator not available", 503

    # Find markdown file
    kb_path = Path("knowledge_base/processed")
    for md_file in kb_path.rglob("*.md"):
        frontmatter, body = parse_markdown_file(md_file)

        if frontmatter.get('id') == doc_id:
            # Find image files
            media_dirs = [
                Path("knowledge_base/media/instagram") / doc_id,
                Path("knowledge_base/media/web_imports") / doc_id,
                Path("knowledge_base/media/attachments") / doc_id
            ]

            images = []
            for media_dir in media_dirs:
                if media_dir.exists():
                    for img_file in media_dir.glob("*"):
                        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            images.append(str(img_file))

            return render_template('visual_translator_detail.html',
                                 frontmatter=frontmatter,
                                 doc_id=doc_id,
                                 images=images)

    return "Document not found", 404

@app.route('/api/analyze-image', methods=['POST'])
def api_analyze_image():
    """API endpoint to analyze a single image"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Visual translator not available'}), 503

    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        skip_vision = data.get('skip_vision', False)

        if not doc_id:
            return jsonify({'error': 'No doc_id provided'}), 400

        # Find image file
        media_dirs = [
            Path("knowledge_base/media/instagram") / doc_id,
            Path("knowledge_base/media/web_imports") / doc_id,
            Path("knowledge_base/media/attachments") / doc_id
        ]

        image_path = None
        for media_dir in media_dirs:
            if media_dir.exists():
                for img_file in media_dir.glob("*"):
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        image_path = img_file
                        break
                if image_path:
                    break

        if not image_path:
            return jsonify({'error': 'No image found for this document'}), 404

        # Analyze image
        analysis = analyze_image(image_path, skip_vision=skip_vision)

        # Update markdown file
        kb_path = Path("knowledge_base/processed")
        for md_file in kb_path.rglob("*.md"):
            frontmatter, body = parse_markdown_file(md_file)

            if frontmatter.get('id') == doc_id:
                # Update frontmatter
                ocr = analysis.get('ocr', {})
                vision = analysis.get('vision', {})

                if ocr:
                    frontmatter['ocr_text'] = ocr.get('text', '')
                    frontmatter['ocr_confidence'] = round(ocr.get('confidence', 0), 2)
                    frontmatter['has_text'] = ocr.get('has_text', False)

                if vision:
                    frontmatter['vision_description'] = vision.get('description', '')
                    frontmatter['vision_tags'] = vision.get('tags', [])
                    frontmatter['vision_scene_type'] = vision.get('scene_type', '')
                    frontmatter['detected_objects'] = vision.get('detected_objects', [])

                frontmatter['visual_analysis_date'] = datetime.now().isoformat()

                # Write back
                new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---{body}"
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return jsonify({
                    'success': True,
                    'analysis': analysis
                })

        return jsonify({'error': 'Markdown file not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visual-stats')
def api_visual_stats():
    """Get visual translator statistics"""
    if not VISUAL_TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Visual translator not available'}), 503

    # Count images
    media_base = Path("knowledge_base/media")
    total_images = 0
    analyzed_images = 0
    with_text = 0

    if media_base.exists():
        for source_dir in media_base.iterdir():
            if source_dir.is_dir():
                for doc_dir in source_dir.iterdir():
                    if doc_dir.is_dir():
                        doc_id = doc_dir.name

                        # Count images
                        for img_file in doc_dir.glob("*"):
                            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                total_images += 1

                        # Check if analyzed
                        kb_path = Path("knowledge_base/processed")
                        for md_file in kb_path.rglob("*.md"):
                            try:
                                frontmatter, _ = parse_markdown_file(md_file)
                                if frontmatter.get('id') == doc_id:
                                    if 'visual_analysis_date' in frontmatter:
                                        analyzed_images += 1
                                    if frontmatter.get('has_text'):
                                        with_text += 1
                            except:
                                continue

    return jsonify({
        'total_images': total_images,
        'analyzed': analyzed_images,
        'pending': total_images - analyzed_images,
        'with_text': with_text
    })

@app.route('/sync-drive')
def sync_drive():
    """Show Google Drive sync interface"""
    return render_template('sync_drive.html')

@app.route('/api/check-drive-files')
def api_check_drive_files():
    """Check for new files in Google Drive without downloading"""
    try:
        # Import drive collector
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.drive_collector import get_drive_service, find_folder, list_files_in_folder, load_config

        # Load config
        config = load_config()
        drive_config = config.get('google_drive', {})

        if not drive_config.get('enabled', False):
            return jsonify({'error': 'Google Drive integration is disabled'}), 400

        # Get Drive service
        service = get_drive_service()

        # Find watch folder
        folder_name = drive_config.get('watch_folder_name', 'WEB3AUTOMATE')
        folder_id = drive_config.get('watch_folder_id')

        if not folder_id:
            folder_id = find_folder(service, folder_name)
            if not folder_id:
                return jsonify({'error': f'Folder "{folder_name}" not found in Google Drive'}), 404

        # List files
        supported_types = drive_config.get('supported_file_types', ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'md'])
        files = list_files_in_folder(service, folder_id, supported_types)

        # Load ignored files
        ignored_files_path = Path("config/ignored_drive_files.json")
        ignored_file_ids = set()
        if ignored_files_path.exists():
            try:
                with open(ignored_files_path, 'r') as f:
                    ignored_data = json.load(f)
                    ignored_file_ids = set(ignored_data.get('ignored_file_ids', []))
            except:
                pass

        # Filter out ignored files
        files = [f for f in files if f['id'] not in ignored_file_ids]

        # Check which files already exist
        kb_path = Path("knowledge_base/processed")
        existing_drive_ids = set()
        existing_filenames = {}

        for md_file in kb_path.rglob("*.md"):
            try:
                frontmatter, _ = parse_markdown_file(md_file)
                if frontmatter.get('source') == 'google_drive':
                    # Store drive file ID if available
                    if 'drive_file_id' in frontmatter:
                        existing_drive_ids.add(frontmatter['drive_file_id'])
                    # Store filename for similarity check
                    filename = frontmatter.get('filename', '')
                    if filename:
                        existing_filenames[filename.lower()] = {
                            'id': frontmatter.get('id'),
                            'title': frontmatter.get('filename'),
                            'created_at': frontmatter.get('created_at'),
                            'size': frontmatter.get('file_size', 0),
                            'source': frontmatter.get('source', 'google_drive')
                        }
            except:
                continue

        # Categorize files
        new_files = []
        duplicate_files = []
        similar_files = []

        for file_data in files:
            file_id = file_data['id']
            filename = file_data['name']
            filename_lower = filename.lower()

            # Check for exact duplicate (by file ID)
            if file_id in existing_drive_ids:
                duplicate_files.append({
                    'id': file_id,
                    'name': filename,
                    'size': file_data.get('size', 0),
                    'modified': file_data.get('modifiedTime', ''),
                    'reason': 'Already imported (same file ID)'
                })
            # Check for similar filename
            elif filename_lower in existing_filenames:
                similar_files.append({
                    'id': file_id,
                    'name': filename,
                    'size': file_data.get('size', 0),
                    'modified': file_data.get('modifiedTime', ''),
                    'existing': existing_filenames[filename_lower],
                    'reason': f'Similar to existing: {existing_filenames[filename_lower]["title"]}'
                })
            else:
                # Check for partial filename match (similarity)
                is_similar = False
                for existing_name, existing_data in existing_filenames.items():
                    # Simple similarity: check if 70% of words match
                    name_words = set(filename_lower.replace('.', ' ').split())
                    existing_words = set(existing_name.replace('.', ' ').split())

                    if name_words and existing_words:
                        common_words = name_words.intersection(existing_words)
                        similarity = len(common_words) / max(len(name_words), len(existing_words))

                        if similarity > 0.7:
                            similar_files.append({
                                'id': file_id,
                                'name': filename,
                                'size': file_data.get('size', 0),
                                'modified': file_data.get('modifiedTime', ''),
                                'existing': existing_data,
                                'reason': f'Possibly similar to: {existing_data["title"]} ({int(similarity*100)}% match)',
                                'similarity': similarity
                            })
                            is_similar = True
                            break

                if not is_similar:
                    new_files.append({
                        'id': file_id,
                        'name': filename,
                        'size': file_data.get('size', 0),
                        'modified': file_data.get('modifiedTime', ''),
                        'mime_type': file_data.get('mimeType', '')
                    })

        return jsonify({
            'success': True,
            'new_files': new_files,
            'similar_files': similar_files,
            'duplicate_files': duplicate_files,
            'total_checked': len(files)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-drive-files', methods=['POST'])
def api_import_drive_files():
    """Import selected files from Google Drive, merging with existing files when appropriate"""
    try:
        data = request.get_json()
        files = data.get('files', [])

        # Backward compatibility with old format
        if not files:
            file_ids = data.get('file_ids', [])
            files = [{'file_id': fid, 'merge': False, 'existing_id': None} for fid in file_ids]

        if not files:
            return jsonify({'error': 'No files selected'}), 400

        # Import drive collector
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from collectors.drive_collector import (
            get_drive_service, download_file, create_markdown,
            generate_id, determine_subject, load_config, move_file, find_folder
        )

        # Import processors
        from processors.attachment_processor import process_attachment

        # Load config
        config = load_config()
        drive_config = config.get('google_drive', {})
        service = get_drive_service()

        imported = []
        merged_count = 0
        errors = []

        for file_info in files:
            file_id = file_info['file_id']
            should_merge = file_info.get('merge', False)
            existing_id = file_info.get('existing_id')
            try:
                # Get file metadata
                file_data = service.files().get(
                    fileId=file_id,
                    fields='id, name, mimeType, modifiedTime, size'
                ).execute()

                filename = file_data['name']

                # Check if we should merge with existing file
                if should_merge and existing_id:
                    # Find existing markdown file
                    kb_path = Path("knowledge_base/processed")
                    existing_md_path = None

                    for md_file in kb_path.rglob("*.md"):
                        try:
                            frontmatter_data, _ = parse_markdown_file(md_file)
                            if frontmatter_data.get('id') == existing_id:
                                existing_md_path = md_file
                                break
                        except:
                            continue

                    if existing_md_path and existing_md_path.exists():
                        # Download new file to temp location
                        from datetime import datetime
                        temp_dir = Path('temp_downloads')
                        temp_dir.mkdir(exist_ok=True)
                        temp_file = temp_dir / filename

                        if download_file(service, file_id, temp_file):
                            # Extract new content based on file type
                            new_content_text = ""

                            if filename.lower().endswith('.pdf'):
                                try:
                                    import PyPDF2
                                    with open(temp_file, 'rb') as pdf_file:
                                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                                        new_content_text = "\n\n".join([page.extract_text() for page in pdf_reader.pages])
                                except:
                                    new_content_text = "[Could not extract PDF content]"
                            elif filename.lower().endswith(('.txt', '.md')):
                                with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    new_content_text = f.read()
                            else:
                                new_content_text = "[Binary file - content not extracted]"

                            # Read existing markdown
                            with open(existing_md_path, 'r', encoding='utf-8') as f:
                                existing_content = f.read()

                            # Parse existing markdown
                            if existing_content.startswith('---'):
                                parts = existing_content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter_data = yaml.safe_load(parts[1])
                                    existing_body = parts[2].strip()

                                    # Update frontmatter
                                    frontmatter_data['updated_at'] = datetime.now().isoformat()
                                    frontmatter_data['file_size'] = file_data.get('size', 0)
                                    frontmatter_data['drive_file_id'] = file_id

                                    # Append new content as amendment
                                    amendment_date = datetime.now().strftime("%Y-%m-%d")
                                    merged_body = f"{existing_body}\n\n---\n\n## Amendment - {amendment_date}\n\n**Source:** Updated version from Google Drive ({filename})\n\n{new_content_text}"

                                    # Write merged content
                                    merged_content = f"---\n{yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)}---\n{merged_body}"

                                    with open(existing_md_path, 'w', encoding='utf-8') as f:
                                        f.write(merged_content)

                                    merged_count += 1
                                    imported.append({
                                        'id': file_id,
                                        'name': filename,
                                        'doc_id': existing_id,
                                        'merged': True
                                    })

                            # Clean up temp file
                            temp_file.unlink()
                        else:
                            errors.append(f"Failed to download: {filename}")
                    else:
                        errors.append(f"Existing file not found for merge: {existing_id}")
                else:
                    # Standard import (new file)
                    doc_id = generate_id(filename, file_data['modifiedTime'])

                    # Download file
                    save_dir = Path(drive_config.get('save_files_dir', 'knowledge_base/attachments')) / doc_id
                    save_dir.mkdir(parents=True, exist_ok=True)
                    file_path = save_dir / filename

                    if download_file(service, file_id, file_path):
                        # Process attachment (extracts images, PDFs, etc.)
                        subject = determine_subject(filename)
                        md_path = process_attachment(file_path, subject, doc_id)

                        # Update frontmatter with drive file ID for duplicate detection
                        if md_path and md_path.exists():
                            with open(md_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            if content.startswith('---'):
                                parts = content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter_data = yaml.safe_load(parts[1])
                                    frontmatter_data['drive_file_id'] = file_id
                                    frontmatter_data['source'] = 'google_drive'

                                    new_content = f"---\n{yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)}---{parts[2]}"
                                    with open(md_path, 'w', encoding='utf-8') as f:
                                        f.write(new_content)

                        # Move to processed folder if configured
                        if drive_config.get('move_processed_files', False):
                            processed_folder_name = drive_config.get('processed_folder_name', 'Processed')
                            processed_folder_id = find_folder(service, processed_folder_name)

                            if not processed_folder_id:
                                from collectors.drive_collector import create_folder
                                processed_folder_id = create_folder(service, processed_folder_name)

                            if processed_folder_id:
                                watch_folder_id = drive_config.get('watch_folder_id')
                                move_file(service, file_id, processed_folder_id, watch_folder_id)

                        imported.append({
                            'id': file_id,
                            'name': filename,
                            'doc_id': doc_id,
                            'merged': False
                        })
                    else:
                        errors.append(f"Failed to download: {filename}")

            except Exception as e:
                errors.append(f"Error importing {file_id}: {str(e)}")
                import traceback
                traceback.print_exc()

        return jsonify({
            'success': True,
            'imported': imported,
            'merged': merged_count,
            'errors': errors
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ignore-drive-files', methods=['POST'])
def api_ignore_drive_files():
    """Add Drive file IDs to permanent ignore list"""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])

        if not file_ids:
            return jsonify({'error': 'No file IDs provided'}), 400

        # Load existing ignored files
        ignored_files_path = Path("config/ignored_drive_files.json")
        ignored_file_ids = []

        if ignored_files_path.exists():
            try:
                with open(ignored_files_path, 'r') as f:
                    ignored_data = json.load(f)
                    ignored_file_ids = ignored_data.get('ignored_file_ids', [])
            except:
                pass

        # Add new file IDs
        for file_id in file_ids:
            if file_id not in ignored_file_ids:
                ignored_file_ids.append(file_id)

        # Save updated list
        ignored_files_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ignored_files_path, 'w') as f:
            json.dump({
                'ignored_file_ids': ignored_file_ids,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

        return jsonify({
            'success': True,
            'ignored_count': len(file_ids),
            'total_ignored': len(ignored_file_ids)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/tags')
def tag_cloud():
    """Tag cloud visualization page"""
    # Gather all tags from all documents
    kb_path = Path("knowledge_base/processed")
    tag_counts = {}
    tag_to_docs = {}  # Map tags to document IDs
    tag_connections = {}  # Map tag relationships

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, _ = parse_markdown_file(md_file)
            doc_id = frontmatter.get('id', '')
            tags = frontmatter.get('tags', [])

            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                if tag not in tag_to_docs:
                    tag_to_docs[tag] = []
                tag_to_docs[tag].append(doc_id)

                # Build tag connections (tags that appear together)
                if tag not in tag_connections:
                    tag_connections[tag] = {}
                for other_tag in tags:
                    if other_tag != tag:
                        tag_connections[tag][other_tag] = tag_connections[tag].get(other_tag, 0) + 1
        except:
            continue

    # Sort tags by frequency
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    return render_template('tag_cloud.html',
                         tags=sorted_tags,
                         tag_to_docs=tag_to_docs,
                         tag_connections=tag_connections,
                         total_tags=len(tag_counts))

@app.route('/api/documents-by-tag/<tag>')
def documents_by_tag(tag):
    """Get all documents with a specific tag"""
    kb_path = Path("knowledge_base/processed")
    documents = []

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            tags = frontmatter.get('tags', [])

            if tag in tags:
                # Extract images
                images = re.findall(r'!\[.*?\]\((.*?)\)', body)
                media_files = []

                doc_id = frontmatter.get('id', '')
                # Check all possible media directories
                media_base = Path("knowledge_base/media")
                if media_base.exists():
                    for media_type_dir in media_base.iterdir():
                        if media_type_dir.is_dir():
                            media_type = media_type_dir.name
                            doc_media_dir = media_type_dir / doc_id
                            if doc_media_dir.exists():
                                for img in doc_media_dir.glob("*"):
                                    if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                        media_files.append(f"{media_type}/{doc_id}/{img.name}")

                documents.append({
                    'id': doc_id,
                    'title': frontmatter.get('title', 'Untitled'),
                    'source': frontmatter.get('source', 'unknown'),
                    'date': frontmatter.get('created_at', ''),
                    'tags': tags,
                    'images': images,
                    'media_files': media_files
                })
        except:
            continue

    return jsonify({'tag': tag, 'documents': documents, 'count': len(documents)})

def get_stats_direct():
    """Get stats without Flask context"""
    kb_path = Path("knowledge_base/processed")
    total_docs = len(list(kb_path.rglob("*.md")))

    sources = {}
    visual_count = 0

    for md_file in kb_path.rglob("*.md"):
        try:
            frontmatter, body = parse_markdown_file(md_file)
            source = frontmatter.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            images = re.findall(r'!\[.*?\]\((.*?)\)', body)
            media_dir = Path("knowledge_base/media/instagram") / frontmatter.get('id', '')
            if images or (media_dir.exists() and any(media_dir.glob("*"))):
                visual_count += 1
        except:
            continue

    return {
        'total_documents': total_docs,
        'visual_documents': visual_count,
        'sources': sources
    }

def main():
    """Run the visual browser"""
    print("\n" + "="*60)
    print("GiselX Knowledge Base - Visual Browser")
    print("="*60)

    # Initialize embeddings
    init_embeddings()

    # Get stats
    stats = get_stats_direct()
    print(f"\nTotal documents: {stats['total_documents']}")
    print(f"Visual documents: {stats['visual_documents']}")
    print("\nSources:")
    for source, count in stats['sources'].items():
        print(f"  - {source}: {count}")

    print("\n" + "="*60)
    print("Starting web server...")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5001")
    print("Press Ctrl+C to stop\n")

    app.run(debug=True, port=5001)

if __name__ == "__main__":
    main()
