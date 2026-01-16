#!/usr/bin/env python3
"""
Interactive Search - CLI interface for exploring the knowledge base
"""
import json
from pathlib import Path
from txtai.embeddings import Embeddings
import sys

def load_config():
    """Load configuration"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def load_index(config):
    """Load the txtai index"""
    index_path = Path(config['txtai']['index_path'])

    if not index_path.exists():
        print(f"Error: Index not found at: {index_path}")
        print("Please run: python scripts/processors/embeddings_generator.py --rebuild")
        sys.exit(1)

    embeddings = Embeddings()
    embeddings.load(str(index_path))
    return embeddings

def get_stats(embeddings):
    """Get index statistics"""
    count = embeddings.count()
    return {
        'total_documents': count
    }

def search(query, embeddings, limit=10):
    """Perform search"""
    results = embeddings.search(query, limit=limit)
    return results

def format_result_preview(result, index):
    """Format result for list view"""
    score = result.get('score', 0.0)
    subject = result.get('subject', 'unknown')
    query = result.get('query', result.get('id', ''))

    # Truncate query if too long
    if len(query) > 60:
        query = query[:57] + "..."

    return f"[{index}] [{score:.2f}] {subject}: \"{query}\""

def format_result_detail(result):
    """Format full result details"""
    output = []

    output.append("\n" + "=" * 80)

    # Header
    doc_id = result.get('id', 'unknown')
    score = result.get('score', 0.0)
    output.append(f"Document ID: {doc_id}")
    output.append(f"Relevance Score: {score:.3f}")
    output.append("-" * 80)

    # Metadata
    if 'subject' in result:
        output.append(f"Subject: {result['subject']}")
    if 'source' in result:
        output.append(f"Source: {result['source']}")
    if 'query' in result:
        output.append(f"Original Query: \"{result['query']}\"")
    if 'created_at' in result:
        output.append(f"Created: {result['created_at'][:10]}")
    if 'tags' in result and result['tags']:
        output.append(f"Tags: {', '.join(result['tags'])}")

    output.append("-" * 80)

    # Content
    if 'text' in result:
        output.append("\nContent:")
        output.append(result['text'][:1000])  # First 1000 chars
        if len(result['text']) > 1000:
            output.append(f"\n... ({len(result['text']) - 1000} more characters)")

    # URLs
    if 'urls' in result and result['urls']:
        output.append("\nSources:")
        for i, url in enumerate(result['urls'][:5], 1):
            output.append(f"  {i}. {url}")

    output.append("=" * 80)

    return '\n'.join(output)

def print_help():
    """Print help message"""
    print("""
Interactive Search Commands:
  <query>          - Search for query
  :view <number>   - View full details of result number
  :limit <number>  - Set result limit (default: 10)
  :stats           - Show index statistics
  :help            - Show this help
  :quit or :exit   - Exit

Examples:
  what is founder's art about?
  :view 3
  :limit 20
""")

def interactive_loop(embeddings, config):
    """Main interactive loop"""
    print("\n" + "=" * 80)
    print("Personal Knowledge Base - Interactive Search")
    print("=" * 80)

    # Show stats
    stats = get_stats(embeddings)
    print(f"\nIndex contains {stats['total_documents']} documents")
    print("\nType ':help' for commands or enter a search query\n")

    current_results = []
    result_limit = 10

    while True:
        try:
            # Get input
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith(':'):
                parts = user_input[1:].split()
                command = parts[0].lower()

                if command in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                elif command == 'help':
                    print_help()

                elif command == 'stats':
                    stats = get_stats(embeddings)
                    print(f"\nIndex Statistics:")
                    print(f"  Total documents: {stats['total_documents']}")
                    if current_results:
                        print(f"  Current results: {len(current_results)}")

                elif command == 'limit':
                    if len(parts) < 2:
                        print(f"Current limit: {result_limit}")
                    else:
                        try:
                            result_limit = int(parts[1])
                            print(f"Result limit set to: {result_limit}")
                        except ValueError:
                            print("Invalid number")

                elif command == 'view':
                    if not current_results:
                        print("No search results available. Perform a search first.")
                        continue

                    if len(parts) < 2:
                        print("Usage: :view <number>")
                        continue

                    try:
                        index = int(parts[1]) - 1
                        if 0 <= index < len(current_results):
                            print(format_result_detail(current_results[index]))
                        else:
                            print(f"Invalid index. Use 1-{len(current_results)}")
                    except ValueError:
                        print("Invalid number")

                else:
                    print(f"Unknown command: {command}. Type ':help' for help.")

            else:
                # Perform search
                print(f"\nSearching for: \"{user_input}\"...")
                results = search(user_input, embeddings, limit=result_limit)

                if not results:
                    print("No results found.")
                    current_results = []
                    continue

                current_results = results
                print(f"\nFound {len(results)} results:\n")

                # Display results
                for i, result in enumerate(results, 1):
                    print(format_result_preview(result, i))

                print(f"\nTip: Use ':view <number>' to see full details")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type ':quit' to exit or continue searching.")
        except Exception as e:
            print(f"\nError: {e}")

def main():
    # Load config and index
    config = load_config()
    embeddings = load_index(config)

    # Start interactive loop
    interactive_loop(embeddings, config)

if __name__ == "__main__":
    main()
