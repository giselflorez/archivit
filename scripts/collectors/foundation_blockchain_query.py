#!/usr/bin/env python3
"""
Foundation Blockchain Query Tool

Queries Ethereum blockchain to get actual IPFS metadata URIs for Foundation NFTs.
Uses Alchemy API for fast, reliable blockchain access.
"""
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os

load_dotenv()

# Alchemy API key (free tier: 300M compute units/month)
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY', '')

# Foundation NFT contract addresses
FOUNDATION_CONTRACTS = {
    'FND_V1': '0x3B3ee1931Dc30C1957379FAc9aba94D1C48a5405',  # Foundation V1
    'FND_V2': '0x8740EEf45Def23A94Bed5b9793c6d1A9b7dC1ebf',  # Foundation V2 (World)
}

# ERC721 tokenURI function signature
TOKEN_URI_SIGNATURE = '0xc87b56dd'  # tokenURI(uint256)


def get_alchemy_url(network='mainnet'):
    """Get Alchemy RPC URL for Ethereum mainnet"""
    if not ALCHEMY_API_KEY:
        print("⚠️  No ALCHEMY_API_KEY found in .env")
        print("   Get a free API key at: https://www.alchemy.com/")
        print("   Add to .env: ALCHEMY_API_KEY=your-key-here")
        return None

    return f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"


def eth_call(contract_address: str, function_signature: str, token_id: int) -> Optional[str]:
    """
    Call Ethereum smart contract function

    Args:
        contract_address: Contract address (0x...)
        function_signature: Function signature (0x...)
        token_id: Token ID to query

    Returns:
        Hex-encoded response data
    """
    url = get_alchemy_url()
    if not url:
        return None

    # Encode token ID as 32-byte hex (padded)
    token_id_hex = f"{token_id:064x}"

    # Build call data: function signature + token ID
    data = function_signature + token_id_hex

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": contract_address,
            "data": data
        }, "latest"],
        "id": 1
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        if 'result' in result:
            return result['result']
        elif 'error' in result:
            print(f"  ✗ Blockchain error: {result['error'].get('message', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"  ✗ Request error: {e}")
        return None


def decode_string_from_hex(hex_data: str) -> Optional[str]:
    """
    Decode string from Ethereum hex response

    Ethereum returns strings as:
    - 32 bytes: offset to string data
    - 32 bytes: length of string
    - N bytes: actual string data (padded to 32-byte chunks)
    """
    if not hex_data or hex_data == '0x':
        return None

    try:
        # Remove '0x' prefix
        hex_data = hex_data[2:] if hex_data.startswith('0x') else hex_data

        # Skip first 64 chars (offset)
        # Next 64 chars are length (in hex)
        length_hex = hex_data[64:128]
        length = int(length_hex, 16)

        # Remaining data is the actual string (hex-encoded)
        string_hex = hex_data[128:128 + (length * 2)]

        # Decode hex to bytes, then to string
        decoded = bytes.fromhex(string_hex).decode('utf-8')

        return decoded

    except Exception as e:
        print(f"  ✗ Decode error: {e}")
        return None


def get_token_uri(contract_address: str, token_id: int) -> Optional[str]:
    """
    Get tokenURI for an NFT from Ethereum blockchain

    Args:
        contract_address: NFT contract address
        token_id: Token ID

    Returns:
        Token URI (usually IPFS URI)
    """
    print(f"  → Querying blockchain for token #{token_id}...")

    hex_response = eth_call(contract_address, TOKEN_URI_SIGNATURE, token_id)

    if hex_response:
        token_uri = decode_string_from_hex(hex_response)

        if token_uri:
            print(f"  ✓ Token URI: {token_uri[:80]}...")
            return token_uri
        else:
            print(f"  ✗ Could not decode token URI")
            return None
    else:
        print(f"  ✗ No response from blockchain")
        return None


def extract_contract_and_token_from_url(url: str) -> Optional[tuple]:
    """
    Extract contract address and token ID from Foundation URL

    Examples:
    - foundation.app/collections/glitter-of-hard-knocks
    - foundation.app/@founder/~/123
    """
    # For now, return Foundation V2 contract as default
    # In production, would parse URL or query Foundation API
    return (FOUNDATION_CONTRACTS['FND_V2'], None)


def query_foundation_nft(contract_address: str, token_id: int, doc_id: str) -> Dict:
    """
    Query Foundation NFT from blockchain and fetch IPFS metadata

    Args:
        contract_address: NFT contract address
        token_id: Token ID
        doc_id: Document ID for saving images

    Returns:
        Dict with NFT metadata
    """
    print(f"\n{'='*60}")
    print(f"Querying Foundation NFT from Blockchain")
    print(f"{'='*60}")
    print(f"Contract: {contract_address}")
    print(f"Token ID: {token_id}")

    # Get tokenURI from blockchain
    token_uri = get_token_uri(contract_address, token_id)

    if not token_uri:
        print("✗ Could not fetch token URI from blockchain")
        return {}

    # Fetch IPFS metadata
    print(f"\n→ Fetching IPFS metadata...")

    # Import blockchain extractor utilities
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from processors.blockchain_nft_extractor import (
        fetch_ipfs_json,
        extract_ipfs_hash_from_url,
        fetch_ipfs_content
    )

    ipfs_hash = extract_ipfs_hash_from_url(token_uri)

    if not ipfs_hash:
        print(f"  ✗ No IPFS hash in token URI: {token_uri}")
        return {'token_uri': token_uri}

    metadata = fetch_ipfs_json(ipfs_hash)

    if not metadata:
        print(f"  ✗ Could not fetch metadata from IPFS")
        return {'token_uri': token_uri}

    print(f"  ✓ Metadata fetched!")
    print(f"    Name: {metadata.get('name', 'Unknown')}")
    print(f"    Description: {metadata.get('description', 'N/A')[:80]}...")

    # Download preview image
    if metadata.get('image'):
        from PIL import Image
        from io import BytesIO

        image_ipfs = metadata['image']
        image_hash = extract_ipfs_hash_from_url(image_ipfs)

        if image_hash:
            print(f"\n→ Downloading preview image from IPFS...")
            image_content = fetch_ipfs_content(image_hash)

            if image_content:
                # Resize to preview (max 1200px)
                try:
                    img = Image.open(BytesIO(image_content))
                    original_size = img.size
                    original_bytes = len(image_content)

                    max_dimension = 1200
                    if max(img.size) > max_dimension:
                        ratio = max_dimension / max(img.size)
                        new_size = tuple(int(dim * ratio) for dim in img.size)
                        img = img.resize(new_size, Image.Resampling.LANCZOS)

                    # Save preview
                    nft_dir = Path("knowledge_base/media/nft") / doc_id
                    nft_dir.mkdir(parents=True, exist_ok=True)

                    file_ext = '.jpg'
                    save_format = 'JPEG'
                    if img.mode in ('RGBA', 'LA', 'P'):
                        file_ext = '.png'
                        save_format = 'PNG'

                    filename = f"nft_{token_id}_preview{file_ext}"
                    filepath = nft_dir / filename

                    output = BytesIO()
                    if save_format == 'JPEG':
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        img.save(output, format=save_format, quality=85, optimize=True)
                    else:
                        img.save(output, format=save_format, optimize=True)

                    preview_bytes = output.getvalue()

                    with open(filepath, 'wb') as f:
                        f.write(preview_bytes)

                    savings_pct = ((original_bytes - len(preview_bytes)) / original_bytes) * 100

                    print(f"  ✓ Saved preview: {filename}")
                    print(f"    Original: {original_bytes:,} bytes → Preview: {len(preview_bytes):,} bytes")
                    print(f"    Space saved: {savings_pct:.1f}%")

                    metadata['preview_image_path'] = str(filepath)
                    metadata['preview_image_size'] = len(preview_bytes)
                    metadata['original_ipfs_size'] = original_bytes

                except Exception as e:
                    print(f"  ✗ Failed to process image: {e}")

    return {
        'token_id': token_id,
        'contract': contract_address,
        'token_uri': token_uri,
        'name': metadata.get('name'),
        'description': metadata.get('description'),
        'image_ipfs': metadata.get('image'),
        'attributes': metadata.get('attributes', []),
        'preview_image_path': metadata.get('preview_image_path'),
        'preview_image_size': metadata.get('preview_image_size'),
        'original_ipfs_size': metadata.get('original_ipfs_size'),
    }


def enhance_foundation_document_with_blockchain_data(md_file_path: Path):
    """
    Enhance Foundation web import with blockchain-queried IPFS data

    This is for Foundation-specific NFTs where we need to query the blockchain
    directly to get tokenURI and IPFS metadata.
    """
    print(f"\n{'='*60}")
    print(f"Enhancing Foundation Document with Blockchain Data")
    print(f"{'='*60}")
    print(f"Document: {md_file_path.name}\n")

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

    doc_id = frontmatter.get('id', 'unknown')

    # For demonstration, query a known Foundation NFT
    # In production, would extract from page content or user input

    print("📝 Note: Foundation NFT detection from page content")
    print("   Current implementation requires manual token ID input")
    print("   Future: Auto-detect from Foundation page structure\n")

    # Example: Query Foundation World contract
    contract = FOUNDATION_CONTRACTS['FND_V2']

    # Prompt for token ID (or detect from content)
    print("Enter token ID to query (or press Enter to skip):")
    token_id_input = input("> ").strip()

    if not token_id_input:
        print("Skipping blockchain query")
        return

    try:
        token_id = int(token_id_input)
    except ValueError:
        print(f"✗ Invalid token ID: {token_id_input}")
        return

    # Query blockchain
    nft_data = query_foundation_nft(contract, token_id, doc_id)

    if not nft_data:
        print("✗ No data retrieved from blockchain")
        return

    # Add to document
    print(f"\n→ Updating document with blockchain data...")

    # Update frontmatter
    frontmatter['nft_count'] = 1
    frontmatter['blockchain_linked'] = True
    frontmatter['blockchain_contract'] = contract
    frontmatter['blockchain_network'] = 'ethereum-mainnet'

    # Add NFT section to body
    nft_section = "\n\n## Blockchain NFT\n\n"
    nft_section += f"### {nft_data.get('name', 'Foundation NFT')}\n\n"
    nft_section += f"**Contract:** `{contract}`\n\n"
    nft_section += f"**Token ID:** {token_id}\n\n"
    nft_section += f"**Network:** Ethereum Mainnet\n\n"

    if nft_data.get('description'):
        nft_section += f"**Description:** {nft_data['description']}\n\n"

    # Attributes
    if nft_data.get('attributes'):
        nft_section += "**Attributes:**\n\n"
        for attr in nft_data['attributes']:
            trait = attr.get('trait_type', 'Property')
            value = attr.get('value', 'N/A')
            nft_section += f"- **{trait}:** {value}\n"
        nft_section += "\n"

    # Preview image
    if nft_data.get('preview_image_path'):
        img_path = Path(nft_data['preview_image_path'])
        rel_path = img_path.relative_to(Path.cwd()) if img_path.is_absolute() else img_path

        nft_section += f"**Preview Image:**\n\n"
        nft_section += f"![{nft_data.get('name', 'NFT')}](../../{rel_path})\n\n"

        preview_size = nft_data.get('preview_image_size', 0)
        original_size = nft_data.get('original_ipfs_size', preview_size)

        if original_size > preview_size:
            savings_pct = ((original_size - preview_size) / original_size) * 100
            nft_section += f"*Optimized preview: {preview_size:,} bytes (saved {savings_pct:.0f}% vs. original {original_size:,} bytes)*\n\n"

    # IPFS links
    if nft_data.get('image_ipfs'):
        from processors.blockchain_nft_extractor import extract_ipfs_hash_from_url

        nft_section += f"**Full Resolution (IPFS):** `{nft_data['image_ipfs']}`\n\n"

        image_hash = extract_ipfs_hash_from_url(nft_data['image_ipfs'])
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

    print(f"✓ Document updated with blockchain NFT data!")
    print(f"\n✓ View document at: {md_file_path}")


def main():
    """Main execution"""
    import sys

    if not ALCHEMY_API_KEY:
        print("\n⚠️  Setup Required: Alchemy API Key")
        print("="*60)
        print("\nTo query Ethereum blockchain, you need a free Alchemy API key:")
        print("\n1. Visit: https://www.alchemy.com/")
        print("2. Sign up (free)")
        print("3. Create an app (Ethereum Mainnet)")
        print("4. Copy API key")
        print("5. Add to .env file:")
        print("   ALCHEMY_API_KEY=your-key-here")
        print("\nFree tier: 300M compute units/month (plenty for NFT queries)")
        print("="*60)
        return

    if len(sys.argv) > 1:
        md_file = Path(sys.argv[1])
        if md_file.exists():
            enhance_foundation_document_with_blockchain_data(md_file)
        else:
            print(f"✗ File not found: {md_file}")
    else:
        print("Usage: python foundation_blockchain_query.py <markdown_file>")
        print("\nExample:")
        print("  python scripts/collectors/foundation_blockchain_query.py \\")
        print("    knowledge_base/processed/about_web_imports/web_af21bdaef6e4_*.md")


if __name__ == "__main__":
    main()
