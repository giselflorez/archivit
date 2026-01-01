#!/usr/bin/env python3
"""
Collect All - Full pipeline orchestration for knowledge base collection
"""
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.embeddings_generator import rebuild_index, update_index, load_config

def run_command(cmd, description, check=True):
    """Run a shell command and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}", file=sys.stderr)
        if e.output:
            print(e.output, file=sys.stderr)
        return False

def collect_perplexity_data(queries, initial=False):
    """
    Run Perplexity collector for all queries

    Args:
        queries: List of search queries
        initial: Whether this is initial collection

    Returns:
        bool: Success status
    """
    if not queries:
        print("No queries to collect")
        return True

    queries_str = ' '.join(f'"{q}"' for q in queries)
    cmd = f'python3 scripts/collectors/perplexity_collector.py --queries {queries_str}'

    return run_command(
        cmd,
        f"Collecting data from Perplexity ({len(queries)} queries)"
    )

def generate_embeddings(initial=False):
    """
    Generate or update embeddings

    Args:
        initial: Whether to rebuild from scratch

    Returns:
        bool: Success status
    """
    print(f"\n{'='*60}")
    if initial:
        print("Building Initial Embeddings Index")
    else:
        print("Updating Embeddings Index")
    print(f"{'='*60}\n")

    try:
        config = load_config()

        if initial:
            embeddings = rebuild_index(config)
        else:
            embeddings = update_index(config)

        return embeddings is not None
    except Exception as e:
        print(f"Error generating embeddings: {e}", file=sys.stderr)
        return False

def git_commit_changes(message):
    """
    Commit changes to git

    Args:
        message: Commit message

    Returns:
        bool: Success status
    """
    # Check if there are changes
    status_result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True
    )

    if not status_result.stdout.strip():
        print("\nNo changes to commit")
        return True

    # Add knowledge base files
    run_command(
        "git add knowledge_base/",
        "Staging knowledge base files",
        check=False
    )

    # Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{message}\n\nTimestamp: {timestamp}"

    success = run_command(
        f'git commit -m "{full_message}"',
        "Committing changes",
        check=False
    )

    return success

def print_summary(queries_count, success):
    """Print final summary"""
    print(f"\n{'='*60}")
    print("Collection Summary")
    print(f"{'='*60}")
    print(f"Queries processed: {queries_count}")
    print(f"Status: {'✓ Success' if success else '✗ Failed'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description="Run full knowledge base collection pipeline")
    parser.add_argument('--initial', action='store_true', help='Initial collection (rebuild index from scratch)')
    parser.add_argument('--queries', '-q', nargs='+', help='Specific queries to run')
    parser.add_argument('--no-commit', action='store_true', help='Skip git commit')
    parser.add_argument('--no-embeddings', action='store_true', help='Skip embedding generation')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Personal Knowledge Base - Collection Pipeline")
    print("="*60)
    print(f"Mode: {'Initial' if args.initial else 'Incremental'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    # Determine queries
    queries = args.queries
    if not queries:
        # Load default queries from config
        try:
            config = load_config()
            queries = config['perplexity'].get('default_queries', [])
            print(f"Using {len(queries)} default queries from config")
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return 1

    if not queries:
        print("No queries specified. Use --queries or configure default_queries in settings.json")
        return 1

    print(f"\nQueries to process:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")

    # Step 1: Collect data from Perplexity
    if not collect_perplexity_data(queries, initial=args.initial):
        print("\n✗ Failed to collect Perplexity data")
        return 1

    # Step 2: Generate/update embeddings
    if not args.no_embeddings:
        if not generate_embeddings(initial=args.initial):
            print("\n✗ Failed to generate embeddings")
            return 1
    else:
        print("\nSkipping embedding generation (--no-embeddings)")

    # Step 3: Git commit
    if not args.no_commit:
        commit_message = f"{'Initial' if args.initial else 'Update'} knowledge base collection - {len(queries)} queries"
        git_commit_changes(commit_message)
    else:
        print("\nSkipping git commit (--no-commit)")

    # Print summary
    print_summary(len(queries), True)

    print("✓ Collection pipeline completed successfully")
    print("\nNext steps:")
    print("  - Search: python scripts/search/interactive_search.py")
    print("  - Export: python scripts/search/export_context.py --query \"your query\"")
    print("")

    return 0

if __name__ == "__main__":
    sys.exit(main())
