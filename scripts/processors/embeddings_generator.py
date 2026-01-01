#!/usr/bin/env python3
"""
Embeddings Generator - Create and manage txtai index for semantic search
"""
import os
import json
from pathlib import Path
from txtai.embeddings import Embeddings
from datetime import datetime
import yaml

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("config/settings.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)

def extract_frontmatter(markdown_content):
    """Extract YAML frontmatter from markdown"""
    if not markdown_content.startswith('---'):
        return {}, markdown_content

    parts = markdown_content.split('---', 2)
    if len(parts) < 3:
        return {}, markdown_content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter, body
    except yaml.YAMLError as e:
        print(f"Error parsing frontmatter: {e}")
        return {}, markdown_content

def load_markdown_files(knowledge_base_path="knowledge_base/processed"):
    """
    Load all markdown files from knowledge base

    Returns:
        list: List of dicts with 'id', 'text', and 'metadata'
    """
    documents = []
    base_path = Path(knowledge_base_path)

    if not base_path.exists():
        print(f"Knowledge base path does not exist: {base_path}")
        return documents

    # Find all markdown files
    md_files = list(base_path.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files")

    for filepath in md_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter and body
            frontmatter, body = extract_frontmatter(content)

            # Create document entry
            # Convert metadata to JSON-serializable format
            metadata = {}
            for key, value in frontmatter.items():
                if isinstance(value, (list, dict)):
                    metadata[key] = json.dumps(value)
                else:
                    metadata[key] = str(value) if value is not None else ''

            metadata['filepath'] = str(filepath)
            metadata['filename'] = filepath.name

            doc = {
                'id': frontmatter.get('id', filepath.stem),
                'text': body,  # Body is what gets embedded
                'metadata': metadata
            }

            documents.append(doc)

        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            continue

    print(f"Successfully loaded {len(documents)} documents")
    return documents

def create_embeddings_index(documents, config):
    """
    Create txtai embeddings index

    Args:
        documents: List of document dicts
        config: Configuration dictionary

    Returns:
        Embeddings: txtai Embeddings instance
    """
    print("Creating embeddings index...")

    # Create embeddings instance
    embeddings = Embeddings({
        "path": config['embedding']['path'],
        "content": True,  # Store content for retrieval
        "batch": config['search'].get('batch_size', 32)
    })

    # Index documents - txtai expects (uid, text, None) format for simple indexing
    # We'll store metadata as JSON in the text itself for now
    data = []
    for doc in documents:
        # Combine metadata into the text for searching
        text_with_meta = f"{doc['text']}\n\n__METADATA__\n{json.dumps(doc['metadata'])}"
        data.append((doc['id'], text_with_meta, None))

    print(f"Indexing {len(data)} documents...")
    embeddings.index(data)

    print("✓ Index created successfully")
    return embeddings

def save_index(embeddings, config):
    """Save the txtai index to disk"""
    index_path = Path(config['txtai']['index_path'])
    index_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Saving index to: {index_path}")
    embeddings.save(str(index_path))
    print("✓ Index saved successfully")

def load_index(config):
    """Load existing txtai index from disk"""
    index_path = Path(config['txtai']['index_path'])

    if not index_path.exists():
        print(f"No existing index found at: {index_path}")
        return None

    print(f"Loading index from: {index_path}")
    embeddings = Embeddings()
    embeddings.load(str(index_path))
    print("✓ Index loaded successfully")
    return embeddings

def update_index_incremental(embeddings, new_documents, config):
    """
    Add new documents to existing index

    Args:
        embeddings: Existing Embeddings instance
        new_documents: List of new document dicts
        config: Configuration dictionary
    """
    if not new_documents:
        print("No new documents to add")
        return

    print(f"Adding {len(new_documents)} new documents to index...")

    # Prepare data
    data = [
        (doc['id'], doc['text'], doc['metadata'])
        for doc in new_documents
    ]

    # Upsert (update or insert)
    embeddings.upsert(data)

    print("✓ Index updated successfully")

def get_index_stats(embeddings):
    """Get statistics about the index"""
    if embeddings is None:
        return {"total_documents": 0}

    count = embeddings.count()
    return {
        "total_documents": count,
        "indexed": count > 0
    }

def rebuild_index(config):
    """
    Rebuild the entire index from scratch

    Returns:
        Embeddings: New embeddings instance
    """
    print("\n" + "="*60)
    print("Rebuilding Index from Scratch")
    print("="*60 + "\n")

    # Load all markdown files
    documents = load_markdown_files()

    if not documents:
        print("No documents found to index")
        return None

    # Create new index
    embeddings = create_embeddings_index(documents, config)

    # Save index
    save_index(embeddings, config)

    # Print stats
    stats = get_index_stats(embeddings)
    print(f"\nIndex Statistics:")
    print(f"  Total documents: {stats['total_documents']}")

    print("\n" + "="*60)
    print("Index Rebuild Complete")
    print("="*60 + "\n")

    return embeddings

def update_index(config):
    """
    Update existing index with new documents

    Returns:
        Embeddings: Updated embeddings instance
    """
    print("\n" + "="*60)
    print("Updating Index")
    print("="*60 + "\n")

    # Load existing index
    embeddings = load_index(config)

    if embeddings is None:
        print("No existing index found. Building new index...")
        return rebuild_index(config)

    # Load all documents
    all_documents = load_markdown_files()

    # Get existing doc IDs
    existing_ids = set()
    try:
        # Search for all documents to get IDs
        results = embeddings.search("*", limit=10000)
        existing_ids = {r['id'] for r in results}
    except:
        pass

    # Find new documents
    new_documents = [doc for doc in all_documents if doc['id'] not in existing_ids]

    if not new_documents:
        print("No new documents to add")
        print("\n" + "="*60)
        return embeddings

    # Update index
    update_index_incremental(embeddings, new_documents, config)

    # Save updated index
    save_index(embeddings, config)

    # Print stats
    stats = get_index_stats(embeddings)
    print(f"\nIndex Statistics:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  New documents added: {len(new_documents)}")

    print("\n" + "="*60)
    print("Index Update Complete")
    print("="*60 + "\n")

    return embeddings

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate and manage embeddings index")
    parser.add_argument('--rebuild', action='store_true', help='Rebuild index from scratch')
    parser.add_argument('--update', action='store_true', help='Update index with new documents')
    parser.add_argument('--stats', action='store_true', help='Show index statistics')

    args = parser.parse_args()

    # Load config
    config = load_config()

    if args.rebuild:
        rebuild_index(config)
    elif args.update:
        update_index(config)
    elif args.stats:
        embeddings = load_index(config)
        stats = get_index_stats(embeddings)
        print(f"\nIndex Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("No action specified. Use --rebuild, --update, or --stats")
        parser.print_help()

if __name__ == "__main__":
    main()
