#!/usr/bin/env python3
"""
Export Context - Format search results as optimized markdown for Claude conversations
"""
import json
import argparse
from pathlib import Path
from txtai.embeddings import Embeddings
from datetime import datetime

def load_config():
    """Load configuration"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def load_index(config):
    """Load the txtai index"""
    index_path = Path(config['txtai']['index_path'])

    if not index_path.exists():
        raise FileNotFoundError(f"Index not found at: {index_path}")

    embeddings = Embeddings()
    embeddings.load(str(index_path))
    return embeddings

def search(query, embeddings, limit=10):
    """Perform semantic search"""
    results = embeddings.search(query, limit=limit)
    return results

def estimate_tokens(text):
    """Rough token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4

def format_for_claude(results, query, max_tokens=50000, include_metadata=True):
    """
    Format search results as optimized markdown for Claude

    Args:
        results: Search results list
        query: Original query
        max_tokens: Maximum tokens to include
        include_metadata: Include source attribution

    Returns:
        str: Formatted markdown
    """
    output = []

    # Header
    output.append(f"# Knowledge Base Context: {query}")
    output.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"Results: {len(results)}\n")
    output.append("---\n")

    current_tokens = estimate_tokens('\n'.join(output))
    included_results = 0

    # Add results
    for result in results:
        # Format result
        result_text = format_result(result, include_metadata)
        result_tokens = estimate_tokens(result_text)

        # Check if we have space
        if current_tokens + result_tokens > max_tokens:
            output.append(f"\n*Note: Truncated. {len(results) - included_results} additional results omitted due to token limit.*\n")
            break

        output.append(result_text)
        output.append("\n---\n")
        current_tokens += result_tokens
        included_results += 1

    # Footer
    output.append(f"\n## Summary")
    output.append(f"- Total results found: {len(results)}")
    output.append(f"- Results included: {included_results}")
    output.append(f"- Estimated tokens: ~{current_tokens:,}")

    return '\n'.join(output)

def format_result(result, include_metadata=True):
    """Format a single result as markdown"""
    output = []

    # Title
    title = result.get('query', result.get('id', 'Document'))
    score = result.get('score', 0.0)
    output.append(f"## {title}")
    output.append(f"**Relevance:** {score:.3f}\n")

    # Metadata
    if include_metadata:
        metadata_items = []
        if 'subject' in result:
            metadata_items.append(f"**Subject:** {result['subject']}")
        if 'source' in result:
            metadata_items.append(f"**Source:** {result['source']}")
        if 'created_at' in result:
            date = result['created_at'][:10]
            metadata_items.append(f"**Date:** {date}")
        if 'tags' in result and result['tags']:
            tags = ', '.join(result['tags'])
            metadata_items.append(f"**Tags:** {tags}")

        if metadata_items:
            output.append(' | '.join(metadata_items))
            output.append("")

    # Content
    if 'text' in result:
        output.append("### Content\n")
        output.append(result['text'])

    # Sources
    if 'urls' in result and result['urls']:
        output.append("\n### Sources")
        for i, url in enumerate(result['urls'][:5], 1):
            output.append(f"{i}. {url}")

    return '\n'.join(output)

def create_conversation_starter(query, results_count):
    """Create a prompt to start the conversation"""
    return f"""I've provided {results_count} relevant documents from my personal knowledge base about: "{query}"

Please analyze this information and:
1. Summarize the main themes and insights
2. Identify any patterns or connections
3. Highlight key points that represent my voice and perspective

Feel free to ask clarifying questions about anything in this context.
"""

def main():
    parser = argparse.ArgumentParser(description="Export search results for Claude")
    parser.add_argument('--query', '-q', type=str, required=True, help='Search query')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Maximum results')
    parser.add_argument('--output', '-o', type=str, help='Output file (default: stdout)')
    parser.add_argument('--max-tokens', '-t', type=int, default=50000, help='Max tokens')
    parser.add_argument('--no-metadata', action='store_true', help='Exclude metadata')
    parser.add_argument('--with-prompt', action='store_true', help='Include conversation starter')

    args = parser.parse_args()

    # Load config and index
    config = load_config()
    embeddings = load_index(config)

    # Get max tokens from config or arg
    max_tokens = args.max_tokens or config['export'].get('max_tokens', 50000)
    include_metadata = not args.no_metadata and config['export'].get('include_metadata', True)

    # Search
    print(f"Searching for: {args.query}", end="...")
    results = search(args.query, embeddings, limit=args.limit)
    print(f" found {len(results)} results")

    # Format for Claude
    print("Formatting context...")
    context = format_for_claude(results, args.query, max_tokens, include_metadata)

    # Add conversation starter if requested
    if args.with_prompt:
        prompt = create_conversation_starter(args.query, len(results))
        context = f"{context}\n\n---\n\n# Conversation Starter\n\n{prompt}"

    # Output
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(context)
        print(f"✓ Context exported to: {output_path}")
        print(f"  Estimated tokens: ~{estimate_tokens(context):,}")
    else:
        print("\n" + "=" * 80)
        print(context)
        print("=" * 80)

if __name__ == "__main__":
    main()
