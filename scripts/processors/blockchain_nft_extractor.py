#!/usr/bin/env python3
"""
Blockchain & IPFS NFT Extractor

Extracts NFT metadata from IPFS, downloads original images, and links
blockchain data to the knowledge base.
"""
import re
import json
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# IPFS Gateway options (in order of preference)
IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://gateway.pinata.cloud/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://dweb.link/ipfs/",
]


def detect_ipfs_hashes(text: str) -> List[str]:
    """
    Detect IPFS hashes in text content

    Supports:
    - CIDv0: Qm... (46 characters, base58)
    - CIDv1: bafybei... (starts with bafy)
    """
    ipfs_hashes = []

    # CIDv0 pattern (Qm followed by 44 base58 characters)
    cidv0_pattern = r'\b(Qm[1-9A-HJ-NP-Za-km-z]{44})\b'
    ipfs_hashes.extend(re.findall(cidv0_pattern, text))

    # CIDv1 pattern (bafy followed by base32 characters)
    cidv1_pattern = r'\b(bafy[a-z2-7]{50,})\b'
    ipfs_hashes.extend(re.findall(cidv1_pattern, text))

    return list(set(ipfs_hashes))  # Remove duplicates


def detect_ipfs_urls(text: str) -> List[str]:
    """
    Detect IPFS URLs in various formats:
    - ipfs://Qm...
    - https://ipfs.io/ipfs/Qm...
    - https://gateway.pinata.cloud/ipfs/Qm...
    - etc.
    """
    ipfs_urls = []

    # Direct ipfs:// protocol
    ipfs_protocol_pattern = r'ipfs://([Qm][1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]{50,})'
    matches = re.findall(ipfs_protocol_pattern, text)
    ipfs_urls.extend([f"ipfs://{match}" for match in matches])

    # IPFS gateway URLs
    gateway_pattern = r'https?://[^/]+/ipfs/([Qm][1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]{50,})(?:/[^\s]*)?'
    gateway_matches = re.findall(gateway_pattern, text)
    ipfs_urls.extend(gateway_matches)

    return list(set(ipfs_urls))


def detect_nft_metadata(text: str) -> List[Dict]:
    """
    Detect structured NFT metadata from scraped content

    Looks for patterns like:
    - Token ID: 249
    - Token: ContractName
    - Token Metadata: IPFS
    - Edition: 1/1
    """
    nfts = []

    # Pattern: Multi-line NFT metadata blocks
    # Example: "Moments in Journey - Phoenix\nedition: 1/1\nΞ 2.0000\n$6,348.54 Sold Price\nToken:1stDibs.1\nToken ID:249\nToken Metadata:IPFS"

    # Split into potential NFT blocks
    blocks = text.split('\n\n')

    for block in blocks:
        nft_data = {}

        # Extract Token ID
        token_id_match = re.search(r'Token ID[:\s]+(\d+)', block, re.IGNORECASE)
        if token_id_match:
            nft_data['token_id'] = token_id_match.group(1)

        # Extract Token contract/name
        token_match = re.search(r'Token[:\s]+([^\n]+?)(?:\n|Token ID)', block, re.IGNORECASE)
        if token_match and 'ID' not in token_match.group(1):
            nft_data['contract'] = token_match.group(1).strip()

        # Extract Edition
        edition_match = re.search(r'edition[:\s]+([\d/]+)', block, re.IGNORECASE)
        if edition_match:
            nft_data['edition'] = edition_match.group(1)

        # Extract Title (usually the first line before "edition:")
        lines = block.split('\n')
        if len(lines) > 0 and 'edition' in block.lower():
            # Title is likely the line before "edition:"
            for i, line in enumerate(lines):
                if 'edition' in line.lower() and i > 0:
                    nft_data['title'] = lines[i-1].strip()
                    break

        # Check if metadata is on IPFS
        if 'IPFS' in block:
            nft_data['metadata_location'] = 'IPFS'

        # Only add if we found at least token ID or contract
        if 'token_id' in nft_data or 'contract' in nft_data:
            nfts.append(nft_data)

    return nfts


def fetch_ipfs_content(ipfs_hash: str, timeout: int = 30) -> Optional[bytes]:
    """
    Fetch content from IPFS using multiple gateways

    Tries each gateway in order until one succeeds
    """
    # Remove ipfs:// prefix if present
    if ipfs_hash.startswith('ipfs://'):
        ipfs_hash = ipfs_hash.replace('ipfs://', '')

    # Remove any path after the hash
    ipfs_hash = ipfs_hash.split('/')[0]

    for gateway in IPFS_GATEWAYS:
        url = f"{gateway}{ipfs_hash}"

        try:
            print(f"  → Trying IPFS gateway: {gateway}")
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0'
            })

            if response.status_code == 200:
                print(f"  ✓ Success via {gateway}")
                return response.content

        except Exception as e:
            print(f"  ✗ Failed: {gateway} - {e}")
            continue

    print(f"  ✗ All gateways failed for {ipfs_hash}")
    return None


def fetch_ipfs_json(ipfs_hash: str) -> Optional[Dict]:
    """Fetch JSON metadata from IPFS"""
    content = fetch_ipfs_content(ipfs_hash)

    if content:
        try:
            return json.loads(content.decode('utf-8'))
        except Exception as e:
            print(f"  ✗ Failed to parse JSON: {e}")
            return None

    return None


def extract_ipfs_hash_from_url(url: str) -> Optional[str]:
    """Extract IPFS hash from various URL formats"""
    # ipfs:// protocol
    if url.startswith('ipfs://'):
        return url.replace('ipfs://', '').split('/')[0]

    # Gateway URLs
    match = re.search(r'/ipfs/([Qm][1-9A-HJ-NP-Za-km-z]{44}|bafy[a-z2-7]{50,})', url)
    if match:
        return match.group(1)

    return None


def process_nft_metadata(nft_data: Dict, doc_id: str) -> Optional[Dict]:
    """
    Process a single NFT's metadata

    Returns enriched metadata with IPFS content if available
    """
    print(f"\n→ Processing NFT: {nft_data.get('title', 'Untitled')}")

    enriched = nft_data.copy()

    # If we have an IPFS metadata URL, fetch it
    if 'metadata_uri' in nft_data:
        ipfs_hash = extract_ipfs_hash_from_url(nft_data['metadata_uri'])

        if ipfs_hash:
            print(f"  → Fetching metadata from IPFS: {ipfs_hash}")
            metadata = fetch_ipfs_json(ipfs_hash)

            if metadata:
                # Standard NFT metadata fields
                enriched['ipfs_metadata'] = metadata
                enriched['name'] = metadata.get('name')
                enriched['description'] = metadata.get('description')
                enriched['image_ipfs'] = metadata.get('image')
                enriched['attributes'] = metadata.get('attributes', [])

                # Download preview image from IPFS (resized to reasonable resolution)
                if metadata.get('image'):
                    image_hash = extract_ipfs_hash_from_url(metadata['image'])

                    if image_hash:
                        print(f"  → Downloading preview from IPFS: {image_hash}")
                        image_content = fetch_ipfs_content(image_hash)

                        if image_content:
                            # Resize to reasonable resolution (max 1200px) to save space
                            from PIL import Image
                            from io import BytesIO

                            try:
                                # Open image
                                img = Image.open(BytesIO(image_content))
                                original_size = img.size
                                original_bytes = len(image_content)

                                # Resize if larger than max dimension
                                max_dimension = 1200
                                if max(img.size) > max_dimension:
                                    # Calculate new size maintaining aspect ratio
                                    ratio = max_dimension / max(img.size)
                                    new_size = tuple(int(dim * ratio) for dim in img.size)
                                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                                    print(f"  → Resized from {original_size} to {new_size}")

                                # Save to knowledge base
                                nft_dir = Path("knowledge_base/media/nft") / doc_id
                                nft_dir.mkdir(parents=True, exist_ok=True)

                                # Determine file format
                                file_ext = '.jpg'
                                save_format = 'JPEG'
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    file_ext = '.png'
                                    save_format = 'PNG'

                                filename = f"nft_{nft_data.get('token_id', 'unknown')}_preview{file_ext}"
                                filepath = nft_dir / filename

                                # Save with optimization
                                output = BytesIO()
                                if save_format == 'JPEG':
                                    # Convert RGBA to RGB for JPEG
                                    if img.mode in ('RGBA', 'LA', 'P'):
                                        img = img.convert('RGB')
                                    img.save(output, format=save_format, quality=85, optimize=True)
                                else:
                                    img.save(output, format=save_format, optimize=True)

                                preview_bytes = output.getvalue()

                                with open(filepath, 'wb') as f:
                                    f.write(preview_bytes)

                                enriched['preview_image_path'] = str(filepath)
                                enriched['preview_image_size'] = len(preview_bytes)
                                enriched['original_ipfs_size'] = original_bytes

                                # Calculate space savings
                                savings_pct = ((original_bytes - len(preview_bytes)) / original_bytes) * 100

                                print(f"  ✓ Saved preview: {filename}")
                                print(f"    Original: {original_bytes:,} bytes → Preview: {len(preview_bytes):,} bytes")
                                print(f"    Space saved: {savings_pct:.1f}%")

                            except Exception as e:
                                print(f"  ✗ Failed to resize image: {e}")
                                # Fallback: save original if resize fails
                                filename = f"nft_{nft_data.get('token_id', 'unknown')}_preview.png"
                                filepath = nft_dir / filename
                                with open(filepath, 'wb') as f:
                                    f.write(image_content)
                                enriched['preview_image_path'] = str(filepath)
                                enriched['preview_image_size'] = len(image_content)

    return enriched


def extract_blockchain_data_from_document(md_file_path: Path) -> Dict:
    """
    Extract blockchain/NFT data from an existing markdown document

    Returns:
    - IPFS hashes found
    - IPFS URLs found
    - NFT metadata detected
    - Enriched NFT data (with IPFS content)
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter and body
    parts = content.split('---', 2)
    if len(parts) >= 3:
        import yaml
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
    else:
        frontmatter = {}
        body = content

    doc_id = frontmatter.get('id', 'unknown')

    print(f"\n{'='*60}")
    print(f"Analyzing document: {md_file_path.name}")
    print(f"Doc ID: {doc_id}")
    print(f"{'='*60}")

    # Detect all blockchain data
    ipfs_hashes = detect_ipfs_hashes(body)
    ipfs_urls = detect_ipfs_urls(body)
    nft_metadata = detect_nft_metadata(body)

    print(f"\n📊 Detection Results:")
    print(f"  - IPFS Hashes: {len(ipfs_hashes)}")
    print(f"  - IPFS URLs: {len(ipfs_urls)}")
    print(f"  - NFT Metadata: {len(nft_metadata)}")

    # Process each NFT
    enriched_nfts = []
    for nft in nft_metadata:
        enriched = process_nft_metadata(nft, doc_id)
        if enriched:
            enriched_nfts.append(enriched)

    return {
        'doc_id': doc_id,
        'ipfs_hashes': ipfs_hashes,
        'ipfs_urls': ipfs_urls,
        'nfts_detected': nft_metadata,
        'nfts_enriched': enriched_nfts
    }


def update_document_with_blockchain_data(md_file_path: Path, blockchain_data: Dict):
    """
    Update the markdown document with enriched blockchain data

    Adds to frontmatter:
    - nft_count
    - blockchain_linked
    - ipfs_content_downloaded

    Adds to body:
    - NFT metadata section
    - Links to IPFS content
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse existing frontmatter
    parts = content.split('---', 2)
    if len(parts) >= 3:
        import yaml
        frontmatter = yaml.safe_load(parts[1]) or {}
        body = parts[2]
    else:
        frontmatter = {}
        body = content

    # Update frontmatter
    frontmatter['nft_count'] = len(blockchain_data['nfts_enriched'])
    frontmatter['blockchain_linked'] = True
    frontmatter['ipfs_content_downloaded'] = any(
        'original_image_path' in nft for nft in blockchain_data['nfts_enriched']
    )
    frontmatter['blockchain_analysis_date'] = datetime.now().isoformat()

    # Add NFT metadata section to body
    nft_section = "\n\n## Blockchain NFTs\n\n"

    for idx, nft in enumerate(blockchain_data['nfts_enriched'], 1):
        nft_section += f"### NFT {idx}: {nft.get('title', 'Untitled')}\n\n"

        # Basic info
        if nft.get('token_id'):
            nft_section += f"**Token ID:** {nft['token_id']}\n\n"
        if nft.get('contract'):
            nft_section += f"**Contract:** {nft['contract']}\n\n"
        if nft.get('edition'):
            nft_section += f"**Edition:** {nft['edition']}\n\n"

        # IPFS metadata
        if nft.get('description'):
            nft_section += f"**Description:** {nft['description']}\n\n"

        # Attributes
        if nft.get('attributes'):
            nft_section += "**Attributes:**\n\n"
            for attr in nft['attributes']:
                trait = attr.get('trait_type', 'Property')
                value = attr.get('value', 'N/A')
                nft_section += f"- **{trait}:** {value}\n"
            nft_section += "\n"

        # Preview image (optimized from IPFS)
        if nft.get('preview_image_path'):
            img_path = Path(nft['preview_image_path'])
            rel_path = img_path.relative_to(Path.cwd()) if img_path.is_absolute() else img_path

            nft_section += f"**Preview Image:**\n\n"
            nft_section += f"![{nft.get('name', 'NFT Image')}](../../{rel_path})\n\n"

            # Show size savings
            preview_size = nft.get('preview_image_size', 0)
            original_size = nft.get('original_ipfs_size', preview_size)

            if original_size > preview_size:
                savings_pct = ((original_size - preview_size) / original_size) * 100
                nft_section += f"*Optimized preview: {preview_size:,} bytes (saved {savings_pct:.0f}% vs. original {original_size:,} bytes)*\n\n"
            else:
                nft_section += f"*Preview: {preview_size:,} bytes*\n\n"

        # IPFS links for pulling originals
        if nft.get('image_ipfs'):
            nft_section += f"**Full Resolution (IPFS):** `{nft['image_ipfs']}`\n\n"

            # Add helpful note about accessing original
            image_hash = extract_ipfs_hash_from_url(nft['image_ipfs'])
            if image_hash:
                nft_section += f"*Access original: [ipfs.io](https://ipfs.io/ipfs/{image_hash}) | "
                nft_section += f"[Pinata](https://gateway.pinata.cloud/ipfs/{image_hash})*\n\n"

        nft_section += "---\n\n"

    # Reconstruct document
    import yaml
    new_content = "---\n"
    new_content += yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    new_content += "---"
    new_content += body
    new_content += nft_section

    # Write back
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✓ Updated document with blockchain data")


def main():
    """Main execution: Process all web imports for blockchain data"""
    import sys

    if len(sys.argv) > 1:
        # Process specific document
        md_file = Path(sys.argv[1])
        if md_file.exists():
            blockchain_data = extract_blockchain_data_from_document(md_file)

            if blockchain_data['nfts_enriched']:
                update_document_with_blockchain_data(md_file, blockchain_data)
                print(f"\n✓ Processed {len(blockchain_data['nfts_enriched'])} NFTs")
            else:
                print("\n✗ No NFT metadata found in document")
        else:
            print(f"✗ File not found: {md_file}")
    else:
        # Process all web imports
        kb_path = Path("knowledge_base/processed/about_web_imports")

        if not kb_path.exists():
            print("✗ No web imports found")
            return

        for md_file in kb_path.glob("*.md"):
            try:
                blockchain_data = extract_blockchain_data_from_document(md_file)

                if blockchain_data['nfts_enriched']:
                    update_document_with_blockchain_data(md_file, blockchain_data)
            except Exception as e:
                print(f"✗ Error processing {md_file.name}: {e}")


if __name__ == "__main__":
    main()
