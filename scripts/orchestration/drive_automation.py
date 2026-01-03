#!/usr/bin/env python3
"""
Drive Automation - Daily Google Drive file collection and processing
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.drive_collector import collect_files
from processors.attachment_processor import process_file
from processors.embeddings_generator import update_index
import subprocess
import json
from datetime import datetime

def load_config():
    """Load configuration"""
    config_path = Path("config/settings.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def process_collected_files(collected_files):
    """Process all collected files through attachment processor"""
    print(f"\n{'='*60}")
    print(f"Processing {len(collected_files)} collected file(s)")
    print(f"{'='*60}\n")

    processed_results = []

    for file_info in collected_files:
        try:
            print(f"\nProcessing: {file_info['filename']}")

            # Process file with attachment processor
            result = process_file(
                file_info['local_path'],
                parent_id=file_info['id']
            )

            if result:
                processed_results.append(result)
                print(f"✓ Successfully processed: {file_info['filename']}")
            else:
                print(f"✗ Failed to process: {file_info['filename']}")

        except Exception as e:
            print(f"Error processing {file_info['filename']}: {e}")
            import traceback
            traceback.print_exc()

    return processed_results

def update_embeddings():
    """Update embeddings index with new files"""
    print(f"\n{'='*60}")
    print("Updating Embeddings Index")
    print(f"{'='*60}\n")

    try:
        config = load_config()
        stats = update_index(config)
        print(f"\n✓ Embeddings updated successfully")
        print(f"  Total documents: {stats.get('total', 'unknown')}")
        return True
    except Exception as e:
        print(f"✗ Failed to update embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False

def git_commit_changes(file_count):
    """Commit changes to git"""
    print(f"\n{'='*60}")
    print("Committing to Git")
    print(f"{'='*60}\n")

    try:
        # Check if there are changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        if not result.stdout.strip():
            print("No changes to commit")
            return True

        # Add knowledge base changes
        subprocess.run(
            ["git", "add", "knowledge_base/"],
            check=True
        )

        # Skip db/ as it's in .gitignore (embeddings are generated, not committed)

        # Commit
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Drive automation: {file_count} new file(s) - {timestamp}"

        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True
        )

        print(f"✓ Committed changes")
        print(f"  Message: {commit_message}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Git commit failed: {e}")
        return False

def run_drive_automation(auto_commit=True):
    """Run full Drive automation pipeline"""
    start_time = datetime.now()

    print(f"\n{'='*70}")
    print(f"GOOGLE DRIVE AUTOMATION - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    # Step 1: Collect files from Google Drive
    print("STEP 1: Collecting files from Google Drive")
    print(f"{'-'*70}")

    collected_files = collect_files()

    if not collected_files:
        print("\nNo files to process. Exiting.")
        return

    print(f"\n✓ Collected {len(collected_files)} file(s)")

    # Step 2: Process files with attachment processor
    print(f"\nSTEP 2: Processing file content")
    print(f"{'-'*70}")

    processed_files = process_collected_files(collected_files)

    print(f"\n✓ Processed {len(processed_files)}/{len(collected_files)} file(s)")

    # Step 3: Update embeddings
    print(f"\nSTEP 3: Updating embeddings index")
    print(f"{'-'*70}")

    embeddings_success = update_embeddings()

    if not embeddings_success:
        print("\n⚠ Warning: Embeddings update failed")

    # Step 4: Git commit (if enabled)
    if auto_commit:
        print(f"\nSTEP 4: Committing to Git")
        print(f"{'-'*70}")

        git_commit_changes(len(processed_files))

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*70}")
    print(f"AUTOMATION COMPLETE")
    print(f"{'='*70}")
    print(f"Files collected: {len(collected_files)}")
    print(f"Files processed: {len(processed_files)}")
    print(f"Embeddings updated: {'Yes' if embeddings_success else 'No'}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"{'='*70}\n")

    return {
        'collected': len(collected_files),
        'processed': len(processed_files),
        'embeddings_updated': embeddings_success,
        'duration': duration
    }

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Google Drive automation pipeline"
    )
    parser.add_argument(
        '--no-commit',
        action='store_true',
        help='Skip git commit step'
    )
    parser.add_argument(
        '--collect-only',
        action='store_true',
        help='Only collect files, skip processing and embeddings'
    )

    args = parser.parse_args()

    if args.collect_only:
        # Just collect files
        files = collect_files()
        print(f"\n✓ Collected {len(files)} file(s)")
        if files:
            print("\nCollected files:")
            for file_info in files:
                print(f"  - {file_info['filename']} → {file_info['local_path']}")
    else:
        # Full automation
        run_drive_automation(auto_commit=not args.no_commit)

if __name__ == "__main__":
    main()
