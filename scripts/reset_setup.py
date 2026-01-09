#!/usr/bin/env python3
"""
Reset Setup - Clear user configuration and optionally reset all data

Run this script to start fresh with the setup wizard
"""

import os
import sys
from pathlib import Path
import argparse

def reset_setup(full_reset=False):
    """Reset setup configuration"""

    print("=" * 60)
    print("ARCHIV-IT - Reset Setup")
    print("=" * 60)

    # Database files
    user_config_db = Path("db/user_config.db")
    blockchain_db = Path("db/blockchain_tracking.db")
    sales_db = Path("db/sales_analytics.db")
    collections_db = Path("db/collections.db")

    # 1. Always delete user config (to trigger setup wizard)
    if user_config_db.exists():
        user_config_db.unlink()
        print("✓ Deleted user configuration database")
    else:
        print("  (No user config found)")

    if full_reset:
        print("\n🔥 FULL RESET MODE - Deleting all data...")

        # 2. Delete blockchain tracking database
        if blockchain_db.exists():
            blockchain_db.unlink()
            print("✓ Deleted blockchain tracking database")

        # 3. Delete sales analytics database
        if sales_db.exists():
            sales_db.unlink()
            print("✓ Deleted sales analytics database")

        # 4. Delete collections database
        if collections_db.exists():
            collections_db.unlink()
            print("✓ Deleted collections database")

        # 5. Delete scraped knowledge base files
        knowledge_base = Path("knowledge_base/processed")
        if knowledge_base.exists():
            import shutil
            file_count = sum(1 for _ in knowledge_base.rglob("*.md"))

            confirm = input(f"\n⚠️  DELETE {file_count} knowledge base files? (yes/no): ")
            if confirm.lower() == 'yes':
                shutil.rmtree(knowledge_base)
                knowledge_base.mkdir(parents=True, exist_ok=True)
                print(f"✓ Deleted {file_count} knowledge base files")
            else:
                print("  Skipped knowledge base deletion")

        # 6. Delete media files
        media_dir = Path("knowledge_base/media")
        if media_dir.exists():
            import shutil
            media_count = sum(1 for _ in media_dir.rglob("*") if _.is_file())

            confirm = input(f"\n⚠️  DELETE {media_count} media files? (yes/no): ")
            if confirm.lower() == 'yes':
                shutil.rmtree(media_dir)
                media_dir.mkdir(parents=True, exist_ok=True)
                print(f"✓ Deleted {media_count} media files")
            else:
                print("  Skipped media deletion")

        # 7. Delete embeddings index
        embeddings_file = Path("knowledge_base/embeddings/faiss_index.pkl")
        if embeddings_file.exists():
            embeddings_file.unlink()
            print("✓ Deleted embeddings index")

    print("\n" + "=" * 60)
    print("Setup reset complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the Flask server: python scripts/interface/visual_browser.py")
    print("2. Visit http://localhost:5000")
    print("3. Complete the setup wizard")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reset ARCHIV-IT setup configuration')
    parser.add_argument('--full', action='store_true',
                       help='Full reset: delete ALL data including knowledge base and media')
    parser.add_argument('--yes', action='store_true',
                       help='Skip confirmation prompts')

    args = parser.parse_args()

    if args.full and not args.yes:
        print("\n⚠️  WARNING: Full reset will delete ALL data!")
        print("This includes:")
        print("  - User configuration")
        print("  - Blockchain tracking database")
        print("  - Sales analytics database")
        print("  - Knowledge base files")
        print("  - Media files")
        print("  - Embeddings index")
        print()
        confirm = input("Are you sure you want to continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Reset cancelled.")
            sys.exit(0)

    reset_setup(full_reset=args.full)
