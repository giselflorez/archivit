#!/usr/bin/env python3
"""
Semantic Network Builder - Builds cognitive data relationships
Transforms documents into a semantic point cloud with typed relationships
"""

import os
# Disable parallel processing to prevent multiprocessing issues on macOS
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from urllib.parse import urlparse
from datetime import datetime
import hashlib


def classify_document_cognitive_type(doc: Dict) -> str:
    """
    Classify document into cognitive data block types:
    - blockchain: NFT, IPFS, crypto art platforms
    - web_article: Standard web imports from domains
    - research: Perplexity queries, deep research
    - media: Image-heavy, visual content
    - conversation: AI conversations, emails
    """
    source = doc.get('source', '').lower()
    doc_type = doc.get('type', '').lower()
    title = doc.get('title', '').lower()
    body = doc.get('body', '').lower()
    url = doc.get('url', '')

    # Blockchain indicators
    blockchain_keywords = ['nft', 'ipfs', 'blockchain', 'crypto', 'ethereum', 'token',
                          'opensea', '1stdibs', 'foundation', 'superrare', 'zora']
    blockchain_domains = ['1stdibs.com', 'opensea.io', 'foundation.app', 'superrare.com',
                         'zora.co', 'rarible.com', 'manifold.xyz']

    if any(keyword in title or keyword in body[:500] for keyword in blockchain_keywords):
        return 'blockchain'

    if url and any(domain in url for domain in blockchain_domains):
        return 'blockchain'

    # Research indicators
    if source == 'perplexity' or 'perplexity' in title:
        return 'research'

    # Conversation indicators
    if source == 'email' or doc_type == 'ai_conversation':
        return 'conversation'

    # Media indicators (high image count, low text)
    image_count = doc.get('image_count', 0)
    has_images = doc.get('has_images', False)
    word_count = len(body.split())

    if has_images and image_count >= 3 and word_count < 300:
        return 'media'

    # Web article indicators
    # Any document with a URL or from web sources should be web_article
    if source in ['web_import', 'web', 'article'] or url:
        return 'web_article'

    # If it's an attachment or drive file with a URL, it's web content
    if source in ['attachment', 'google_drive'] and url:
        return 'web_article'

    # Default to web_article for anything else
    # (most documents in knowledge base come from web sources)
    return 'web_article'


def extract_blockchain_metadata(doc: Dict) -> Dict:
    """
    Extract blockchain-specific metadata:
    - IPFS hashes (ipfs:// or Qm... or baf...)
    - NFT marketplace URLs
    - Platform identifiers
    - Token IDs
    - Blockchain addresses (ETH, BTC, Solana)
    - Blockchain network type (Ethereum, Bitcoin, Solana)
    - Original creation dates (IPFS upload, HTML publication)
    """
    body = doc.get('body', '')
    url = doc.get('url', '')
    metadata = {
        'ipfs_hashes': [],
        'platforms': [],
        'token_ids': [],
        'marketplace_urls': [],
        'blockchain_addresses': [],
        'blockchain_network': None,  # 'ethereum', 'bitcoin', 'solana'
        'original_date': None,  # Original creation/publication date
        'explorer_url': None,  # Blockchain explorer link (etherscan, etc.)
        'transaction_hash': None,  # Blockchain transaction hash
        'block_number': None,  # Block number of mint transaction
        'contract_address': None,  # Smart contract address
        'mint_date': None  # Actual mint date from blockchain
    }

    # IPFS hash patterns
    ipfs_pattern = r'(?:ipfs://|Qm[a-zA-Z0-9]{44}|baf[a-zA-Z0-9]+)'
    ipfs_matches = re.findall(ipfs_pattern, body)
    metadata['ipfs_hashes'] = list(set(ipfs_matches))

    # Blockchain explorer URL extraction
    # Look for etherscan, blockchain.com, solscan, etc. links
    explorer_patterns = [
        r'https?://(?:www\.)?etherscan\.io/[^\s]+',
        r'https?://(?:www\.)?blockchain\.com/[^\s]+',
        r'https?://(?:www\.)?solscan\.io/[^\s]+',
        r'https?://(?:www\.)?bscscan\.com/[^\s]+',
        r'https?://(?:www\.)?polygonscan\.com/[^\s]+',
        r'https?://(?:www\.)?explorer\.solana\.com/[^\s]+',
    ]

    # Check URL first (most reliable)
    for pattern in explorer_patterns:
        if url and re.search(pattern, url, re.IGNORECASE):
            metadata['explorer_url'] = url
            break

    # If not found in URL, check body content
    if not metadata['explorer_url']:
        for pattern in explorer_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                metadata['explorer_url'] = match.group(0)
                break

    # Blockchain address patterns
    # Ethereum: 0x followed by 40 hex characters
    eth_pattern = r'0x[a-fA-F0-9]{40}'
    eth_matches = re.findall(eth_pattern, body)

    # Bitcoin: Various formats (P2PKH, P2SH, Bech32)
    btc_pattern = r'\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b'
    btc_matches = re.findall(btc_pattern, body)

    # Solana: Base58 encoded, typically 32-44 characters
    sol_pattern = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'
    # More conservative - only if Solana keywords present
    if 'solana' in body.lower() or 'sol' in body.lower():
        sol_matches = re.findall(sol_pattern, body)
    else:
        sol_matches = []

    # Combine all addresses
    all_addresses = []
    if eth_matches:
        all_addresses.extend([('ethereum', addr) for addr in eth_matches])
        metadata['blockchain_network'] = 'ethereum'
    if btc_matches:
        all_addresses.extend([('bitcoin', addr) for addr in btc_matches])
        if not metadata['blockchain_network']:
            metadata['blockchain_network'] = 'bitcoin'
    if sol_matches:
        all_addresses.extend([('solana', addr) for addr in sol_matches])
        if not metadata['blockchain_network']:
            metadata['blockchain_network'] = 'solana'

    metadata['blockchain_addresses'] = all_addresses

    # Detect blockchain network from platform if not found from addresses
    if not metadata['blockchain_network']:
        # Most NFT marketplaces are Ethereum-based
        eth_platforms = ['opensea', 'foundation', 'superrare', 'zora', 'rarible', '1stdibs']
        sol_platforms = ['magic eden', 'solanart', 'tensor']

        for platform in eth_platforms:
            if platform in url.lower() or platform in body.lower():
                metadata['blockchain_network'] = 'ethereum'
                break

        if not metadata['blockchain_network']:
            for platform in sol_platforms:
                if platform in url.lower() or platform in body.lower():
                    metadata['blockchain_network'] = 'solana'
                    break

    # Platform detection
    platform_map = {
        '1stdibs.com': '1stDibs NFT',
        'opensea.io': 'OpenSea',
        'foundation.app': 'Foundation',
        'superrare.com': 'SuperRare',
        'zora.co': 'Zora',
        'rarible.com': 'Rarible',
        'manifold.xyz': 'Manifold',
        'magiceden.io': 'Magic Eden',
        'solanart.io': 'Solanart'
    }

    if url:
        for domain, platform_name in platform_map.items():
            if domain in url:
                metadata['platforms'].append(platform_name)
                metadata['marketplace_urls'].append(url)

    # Token ID patterns
    token_pattern = r'Token ID[:\s]+(\d+)'
    token_matches = re.findall(token_pattern, body, re.IGNORECASE)
    metadata['token_ids'] = token_matches

    # Extract original creation date from content
    # Look for IPFS upload dates, publication dates, etc.
    date_patterns = [
        r'published[:\s]+(\d{4}-\d{2}-\d{2})',
        r'created[:\s]+(\d{4}-\d{2}-\d{2})',
        r'minted[:\s]+(\d{4}-\d{2}-\d{2})',
        r'uploaded[:\s]+(\d{4}-\d{2}-\d{2})',
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format in content
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            metadata['original_date'] = matches[0]
            break

    # Also check document metadata fields
    if not metadata['original_date']:
        # Check for scraped_date, published_date, etc.
        for field in ['scraped_date', 'published_date', 'minted_date', 'upload_date']:
            if field in doc and doc[field]:
                metadata['original_date'] = doc[field]
                break

    # Extract blockchain transaction data (PRIORITY METADATA)
    # Transaction hash patterns (Ethereum: 0x followed by 64 hex chars)
    tx_pattern = r'(?:transaction|tx)[:\s]*(?:hash)?[:\s]*(0x[a-fA-F0-9]{64})'
    tx_matches = re.findall(tx_pattern, body, re.IGNORECASE)
    if tx_matches:
        metadata['transaction_hash'] = tx_matches[0]
    else:
        # Try direct pattern without labels
        tx_direct = re.findall(r'0x[a-fA-F0-9]{64}', body)
        if tx_direct:
            metadata['transaction_hash'] = tx_direct[0]

    # Block number patterns
    block_pattern = r'(?:block|block number)[:\s]+(\d+)'
    block_matches = re.findall(block_pattern, body, re.IGNORECASE)
    if block_matches:
        metadata['block_number'] = block_matches[0]

    # Contract address (different from wallet addresses - usually labeled)
    contract_pattern = r'(?:contract|contract address)[:\s]+(0x[a-fA-F0-9]{40})'
    contract_matches = re.findall(contract_pattern, body, re.IGNORECASE)
    if contract_matches:
        metadata['contract_address'] = contract_matches[0]

    # Mint date (more specific than original_date)
    mint_date_patterns = [
        r'mint(?:ed)?\s+(?:on|date)[:\s]+(\d{4}-\d{2}-\d{2})',
        r'minted[:\s]+(\d{4}-\d{2}-\d{2})',
        r'mint date[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
    ]
    for pattern in mint_date_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            metadata['mint_date'] = matches[0]
            # Use mint date as original_date if more specific
            if not metadata['original_date']:
                metadata['original_date'] = matches[0]
            break

    return metadata


def extract_domain_from_url(url: str) -> str:
    """Extract base domain from URL"""
    if not url:
        return ''
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ''


def compute_blockchain_relationships(documents: List[Dict]) -> List[Tuple[str, str, Dict]]:
    """
    Create edges between documents sharing blockchain platforms, IPFS content,
    blockchain networks, or addresses
    Returns: [(doc_id_1, doc_id_2, edge_data), ...]
    """
    edges = []

    # Index documents by various blockchain attributes
    platform_index = {}
    ipfs_index = {}
    network_index = {}  # Group by ETH/BTC/Solana
    address_index = {}  # Group by blockchain addresses

    for doc in documents:
        doc_id = doc['id']
        cognitive_type = classify_document_cognitive_type(doc)

        if cognitive_type == 'blockchain':
            metadata = extract_blockchain_metadata(doc)

            # Index by platform
            for platform in metadata['platforms']:
                if platform not in platform_index:
                    platform_index[platform] = []
                platform_index[platform].append(doc_id)

            # Index by IPFS
            for ipfs_hash in metadata['ipfs_hashes']:
                if ipfs_hash not in ipfs_index:
                    ipfs_index[ipfs_hash] = []
                ipfs_index[ipfs_hash].append(doc_id)

            # Index by blockchain network
            if metadata['blockchain_network']:
                network = metadata['blockchain_network']
                if network not in network_index:
                    network_index[network] = []
                network_index[network].append(doc_id)

            # Index by blockchain addresses
            for network, address in metadata['blockchain_addresses']:
                if address not in address_index:
                    address_index[address] = []
                address_index[address].append(doc_id)

    # Create blockchain network edges (ETH/BTC/Solana grouping)
    for network, doc_ids in network_index.items():
        if len(doc_ids) > 1:
            for i, doc_id_1 in enumerate(doc_ids):
                for doc_id_2 in doc_ids[i+1:]:
                    edges.append((doc_id_1, doc_id_2, {
                        'type': 'blockchain_network',
                        'network': network,
                        'strength': 0.7
                    }))

    # Create platform edges
    for platform, doc_ids in platform_index.items():
        for i, doc_id_1 in enumerate(doc_ids):
            for doc_id_2 in doc_ids[i+1:]:
                edges.append((doc_id_1, doc_id_2, {
                    'type': 'blockchain_platform',
                    'platform': platform,
                    'strength': 0.8
                }))

    # Create blockchain address edges (strongest - same wallet/contract)
    for address, doc_ids in address_index.items():
        if len(doc_ids) > 1:
            for i, doc_id_1 in enumerate(doc_ids):
                for doc_id_2 in doc_ids[i+1:]:
                    edges.append((doc_id_1, doc_id_2, {
                        'type': 'blockchain_address',
                        'address': address[:10] + '...' + address[-8:],
                        'strength': 0.98
                    }))

    # Create IPFS content edges (very strong connection)
    for ipfs_hash, doc_ids in ipfs_index.items():
        for i, doc_id_1 in enumerate(doc_ids):
            for doc_id_2 in doc_ids[i+1:]:
                edges.append((doc_id_1, doc_id_2, {
                    'type': 'ipfs_content',
                    'ipfs_hash': ipfs_hash[:20] + '...',
                    'strength': 0.95
                }))

    return edges


def compute_domain_relationships(documents: List[Dict]) -> List[Tuple[str, str, Dict]]:
    """
    Create edges between web articles from the same domain
    Returns: [(doc_id_1, doc_id_2, edge_data), ...]
    """
    edges = []

    # Index documents by domain
    domain_index = {}

    for doc in documents:
        doc_id = doc['id']
        url = doc.get('url', '')
        domain = extract_domain_from_url(url)

        if domain:
            if domain not in domain_index:
                domain_index[domain] = []
            domain_index[domain].append(doc_id)

    # Create domain sibling edges
    for domain, doc_ids in domain_index.items():
        if len(doc_ids) > 1:  # Only if multiple docs from same domain
            for i, doc_id_1 in enumerate(doc_ids):
                for doc_id_2 in doc_ids[i+1:]:
                    edges.append((doc_id_1, doc_id_2, {
                        'type': 'domain_sibling',
                        'domain': domain,
                        'strength': 0.6
                    }))

    return edges


def compute_semantic_relationships(documents: List[Dict], index, top_k: int = 3) -> List[Tuple[str, str, Dict]]:
    """
    Create edges between semantically similar documents using txtai embeddings
    Returns: [(doc_id_1, doc_id_2, edge_data), ...]
    """
    edges = []

    # For each document, find top_k most similar
    for doc in documents:
        doc_id = doc['id']
        query_text = f"{doc.get('title', '')} {doc.get('body', '')[:500]}"

        try:
            # Search for similar documents
            results = index.search(query_text, limit=top_k + 1)  # +1 to exclude self

            for result in results:
                if isinstance(result, dict):
                    similar_id = result.get('id')
                    score = result.get('score', 0)
                elif isinstance(result, tuple):
                    similar_id = result[0]
                    score = result[1] if len(result) > 1 else 0
                else:
                    continue

                # Skip self-matches and low scores
                if similar_id == doc_id or score < 0.3:
                    continue

                # Add edge (only if not already added in reverse)
                edge_exists = any(
                    (e[0] == similar_id and e[1] == doc_id) or
                    (e[0] == doc_id and e[1] == similar_id)
                    for e in edges
                )

                if not edge_exists:
                    edges.append((doc_id, similar_id, {
                        'type': 'semantic_similarity',
                        'score': score,
                        'strength': min(score, 0.9)
                    }))
        except Exception as e:
            print(f"Error computing semantic similarity for {doc_id}: {e}")
            continue

    return edges


def compute_temporal_relationships(documents: List[Dict], days_threshold: int = 7) -> List[Tuple[str, str, Dict]]:
    """
    Create edges between documents created within the same time window.
    Uses both import dates AND original creation dates (IPFS upload, HTML publication, etc.)
    Returns: [(doc_id_1, doc_id_2, edge_data), ...]
    """
    edges = []

    # Parse dates and sort - prioritize original dates over import dates
    dated_docs = []
    original_dated_docs = []

    for doc in documents:
        doc_id = doc['id']

        # Try to get original creation date first (for blockchain/web content)
        original_date = None
        cognitive_type = classify_document_cognitive_type(doc)

        if cognitive_type == 'blockchain':
            metadata = extract_blockchain_metadata(doc)
            if metadata.get('original_date'):
                original_date = metadata['original_date']

        # Also check common date fields in document
        if not original_date:
            for field in ['scraped_date', 'published_date', 'minted_date', 'upload_date']:
                if field in doc and doc[field]:
                    original_date = doc[field]
                    break

        # Parse original date if found
        if original_date:
            try:
                if isinstance(original_date, str):
                    # Try ISO format
                    if 'T' in original_date:
                        date = datetime.fromisoformat(original_date.replace('Z', '+00:00'))
                    else:
                        # Try date-only format
                        date = datetime.strptime(original_date, '%Y-%m-%d')
                else:
                    date = original_date
                original_dated_docs.append((doc_id, date, 'original'))
            except:
                pass

        # Fall back to import date
        created_at = doc.get('created_at') or doc.get('date')
        if created_at:
            try:
                if isinstance(created_at, str):
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    date = created_at
                dated_docs.append((doc_id, date, 'import'))
            except:
                continue

    # Combine both lists, preferring original dates
    all_dated_docs = original_dated_docs + dated_docs

    # Remove duplicates (prefer original date over import date)
    seen_ids = set()
    unique_dated_docs = []
    for doc_id, date, date_type in all_dated_docs:
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_dated_docs.append((doc_id, date, date_type))

    unique_dated_docs.sort(key=lambda x: x[1])

    # Find temporal neighbors
    for i, (doc_id_1, date_1, type_1) in enumerate(unique_dated_docs):
        for doc_id_2, date_2, type_2 in unique_dated_docs[i+1:]:
            days_diff = abs((date_2 - date_1).days)
            if days_diff <= days_threshold:
                # Determine if this is original temporal proximity or import proximity
                proximity_type = 'original' if (type_1 == 'original' and type_2 == 'original') else 'import'

                edges.append((doc_id_1, doc_id_2, {
                    'type': 'temporal_proximity',
                    'proximity_type': proximity_type,
                    'days_apart': days_diff,
                    'strength': 0.4
                }))
            else:
                break  # Sorted, so no more matches

    return edges


def build_semantic_network(documents: List[Dict], index) -> Dict:
    """
    Main function to build the complete semantic network

    Returns:
    {
        'nodes': [
            {
                'id': str,
                'title': str,
                'cognitive_type': str,
                'url': str,
                'tags': [str],
                'image_url': str,
                'created_at': str,
                'metadata': {
                    'blockchain': {...},  # if applicable
                    'domain': str,        # if applicable
                }
            },
            ...
        ],
        'edges': [
            {
                'source': str,
                'target': str,
                'type': str,
                'strength': float,
                'metadata': {...}
            },
            ...
        ]
    }
    """

    # Build nodes with cognitive type classification
    nodes = []
    for doc in documents:
        cognitive_type = classify_document_cognitive_type(doc)

        # Try to find an associated image path
        image_path = None
        if 'image' in doc or 'image_path' in doc:
            image_path = doc.get('image') or doc.get('image_path')
        elif 'body' in doc:
            # Try to extract image path from markdown body
            import re
            img_match = re.search(r'!\[.*?\]\((.*?)\)', doc['body'])
            if img_match:
                img_path = img_match.group(1)
                # Convert to relative path if it's a local file
                if not img_path.startswith('http'):
                    image_path = img_path

        node = {
            'id': doc['id'],
            'title': doc.get('title', 'Untitled'),
            'cognitive_type': cognitive_type,
            'url': doc.get('url', ''),
            'tags': doc.get('tags', []),
            'image_url': doc.get('image_url', ''),
            'image_path': image_path,
            'created_at': doc.get('created_at') or doc.get('date', ''),
            'metadata': {}
        }

        # Add type-specific metadata
        if cognitive_type == 'blockchain':
            node['metadata']['blockchain'] = extract_blockchain_metadata(doc)

        if doc.get('url'):
            node['metadata']['domain'] = extract_domain_from_url(doc['url'])

        nodes.append(node)

    # Compute all relationship types
    all_edges = []

    # 1. Blockchain relationships
    blockchain_edges = compute_blockchain_relationships(documents)
    all_edges.extend(blockchain_edges)

    # 2. Domain relationships
    domain_edges = compute_domain_relationships(documents)
    all_edges.extend(domain_edges)

    # 3. Semantic relationships (using txtai)
    semantic_edges = compute_semantic_relationships(documents, index, top_k=3)
    all_edges.extend(semantic_edges)

    # 4. Temporal relationships - DISABLED (not useful for analysis)
    # temporal_edges = compute_temporal_relationships(documents, days_threshold=7)
    # all_edges.extend(temporal_edges)

    # Convert edges to standard format
    edges = []
    for source, target, data in all_edges:
        edges.append({
            'source': source,
            'target': target,
            'type': data['type'],
            'strength': data['strength'],
            'metadata': {k: v for k, v in data.items() if k not in ['type', 'strength']}
        })

    return {
        'nodes': nodes,
        'edges': edges
    }


def get_mints_by_address(documents: List[Dict], blockchain_address: str) -> List[Dict]:
    """
    Retrieve all NFT mints/documents associated with a specific blockchain address.

    Args:
        documents: List of all documents in the knowledge base
        blockchain_address: Blockchain address to search for (ETH/BTC/Solana)

    Returns:
        List of documents containing the specified address
    """
    matching_docs = []

    for doc in documents:
        cognitive_type = classify_document_cognitive_type(doc)

        if cognitive_type == 'blockchain':
            metadata = extract_blockchain_metadata(doc)

            # Check if this address appears in the document
            for network, address in metadata['blockchain_addresses']:
                if address.lower() == blockchain_address.lower():
                    matching_docs.append({
                        'id': doc['id'],
                        'title': doc.get('title', 'Untitled'),
                        'url': doc.get('url', ''),
                        'blockchain_network': metadata['blockchain_network'],
                        'platforms': metadata['platforms'],
                        'token_ids': metadata['token_ids'],
                        'ipfs_hashes': metadata['ipfs_hashes'],
                        'created_at': doc.get('created_at') or doc.get('date', ''),
                        'original_date': metadata.get('original_date'),
                        'tags': doc.get('tags', [])
                    })
                    break

    return matching_docs


def get_mints_by_network(documents: List[Dict], network: str) -> List[Dict]:
    """
    Retrieve all NFT mints/documents from a specific blockchain network.

    Args:
        documents: List of all documents in the knowledge base
        network: Blockchain network ('ethereum', 'bitcoin', 'solana')

    Returns:
        List of documents on the specified network
    """
    matching_docs = []

    for doc in documents:
        cognitive_type = classify_document_cognitive_type(doc)

        if cognitive_type == 'blockchain':
            metadata = extract_blockchain_metadata(doc)

            if metadata['blockchain_network'] == network.lower():
                matching_docs.append({
                    'id': doc['id'],
                    'title': doc.get('title', 'Untitled'),
                    'url': doc.get('url', ''),
                    'blockchain_network': metadata['blockchain_network'],
                    'platforms': metadata['platforms'],
                    'addresses': metadata['blockchain_addresses'],
                    'token_ids': metadata['token_ids'],
                    'ipfs_hashes': metadata['ipfs_hashes'],
                    'created_at': doc.get('created_at') or doc.get('date', ''),
                    'original_date': metadata.get('original_date'),
                    'tags': doc.get('tags', [])
                })

    return matching_docs


def get_all_blockchain_addresses(documents: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extract and index all blockchain addresses found in the knowledge base.

    Returns:
        Dict mapping addresses to list of documents containing them
        {
            'address1': [{'id': 'doc1', 'title': '...', ...}, ...],
            'address2': [{'id': 'doc2', 'title': '...', ...}, ...],
        }
    """
    address_index = {}

    for doc in documents:
        cognitive_type = classify_document_cognitive_type(doc)

        if cognitive_type == 'blockchain':
            metadata = extract_blockchain_metadata(doc)

            for network, address in metadata['blockchain_addresses']:
                if address not in address_index:
                    address_index[address] = []

                address_index[address].append({
                    'id': doc['id'],
                    'title': doc.get('title', 'Untitled'),
                    'url': doc.get('url', ''),
                    'network': network,
                    'blockchain_network': metadata['blockchain_network'],
                    'platforms': metadata['platforms'],
                    'created_at': doc.get('created_at') or doc.get('date', ''),
                    'tags': doc.get('tags', [])
                })

    return address_index


if __name__ == '__main__':
    # Test classification
    test_docs = [
        {
            'id': 'test1',
            'title': 'GiselFlorez NFT Collection',
            'body': 'IPFS hash: Qm1234... Token ID: 123',
            'url': 'https://www.1stdibs.com/nft/profile/GISELXFLOREZ/',
            'source': 'web_import'
        },
        {
            'id': 'test2',
            'title': 'Article about art',
            'body': 'This is a regular article',
            'url': 'https://example.com/article',
            'source': 'web_import'
        }
    ]

    for doc in test_docs:
        cog_type = classify_document_cognitive_type(doc)
        print(f"{doc['title']}: {cog_type}")

        if cog_type == 'blockchain':
            metadata = extract_blockchain_metadata(doc)
            print(f"  Blockchain metadata: {metadata}")
