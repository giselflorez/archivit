#!/usr/bin/env python3
"""
Semantic Search - Query the knowledge base using natural language
"""
import json
from pathlib import Path
from txtai.embeddings import Embeddings
import argparse

def load_config():
    """Load configuration"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def load_index(config):
    """Load the txtai index"""
    index_path = Path(config['txtai']['index_path'])

    if not index_path.exists():
        raise FileNotFoundError(f"Index not found at: {index_path}. Run embeddings_generator.py first.")

    embeddings = Embeddings()
    embeddings.load(str(index_path))
    return embeddings

def search(query, embeddings, config, limit=None, filters=None):
    """
    Perform semantic search

    Args:
        query: Search query string
        embeddings: txtai Embeddings instance
        config: Configuration dict
        limit: Maximum number of results
        filters: Optional filters dict (e.g., {'subject': 'founder'})

    Returns:
        list: Search results
    """
    max_results = limit or config['search'].get('max_results', 10)

    # Build filter query if needed
    # txtai supports SQL-like WHERE clauses
    where = None
    if filters:
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            else:
                conditions.append(f"{key} = {value}")
        if conditions:
            where = " AND ".join(conditions)

    # Perform search
    results = embeddings.search(query, limit=max_results, weights=None)

    return results

def format_result(result, show_content=True, max_content_length=500):
    """Format a single search result for display"""
    output = []

    # Score and ID
    score = result.get('score', 0.0)
    doc_id = result.get('id', 'unknown')
    output.append(f"[{score:.3f}] ID: {doc_id}")

    # Metadata
    if 'subject' in result:
        output.append(f"  Subject: {result['subject']}")
    if 'source' in result:
        output.append(f"  Source: {result['source']}")
    if 'query' in result:
        output.append(f"  Original Query: \"{result['query']}\"")
    if 'created_at' in result:
        created = result['created_at'][:10]  # Just the date
        output.append(f"  Created: {created}")
    if 'tags' in result:
        tags = result.get('tags', [])
        if tags:
            output.append(f"  Tags: {', '.join(tags)}")

    # Content preview
    if show_content and 'text' in result:
        text = result['text']
        if len(text) > max_content_length:
            text = text[:max_content_length] + "..."
        output.append(f"  Preview: {text}")

    # URLs
    if 'urls' in result and result['urls']:
        urls = result['urls'][:3]  # Show first 3 URLs
        output.append(f"  Sources: {', '.join(urls)}")

    return '\n'.join(output)

def print_results(results, show_content=True):
    """Print search results"""
    if not results:
        print("No results found")
        return

    print(f"\nFound {len(results)} results:\n")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {format_result(result, show_content)}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Search the knowledge base")
    parser.add_argument('query', type=str, help='Search query')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Maximum results')
    parser.add_argument('--subject', '-s', type=str, help='Filter by subject')
    parser.add_argument('--source', type=str, help='Filter by source')
    parser.add_argument('--no-content', action='store_true', help='Hide content preview')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Load config and index
    config = load_config()
    embeddings = load_index(config)

    # Build filters
    filters = {}
    if args.subject:
        filters['subject'] = args.subject
    if args.source:
        filters['source'] = args.source

    # Search
    results = search(args.query, embeddings, config, limit=args.limit, filters=filters or None)

    # Output
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_results(results, show_content=not args.no_content)

if __name__ == "__main__":
    main()
