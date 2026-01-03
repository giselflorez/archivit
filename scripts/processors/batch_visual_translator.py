#!/usr/bin/env python3
"""
Batch Visual Translator - Process existing images in knowledge base

Scans the knowledge base for images and analyzes them with OCR and vision AI.
Updates existing markdown files with visual analysis results.
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.visual_translator import analyze_image, batch_analyze_images


def find_all_images(base_path: Path = None) -> list:
    """Find all image files in knowledge base media directories"""
    if base_path is None:
        base_path = Path("knowledge_base/media")

    if not base_path.exists():
        print(f"Warning: Media directory not found: {base_path}")
        return []

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    images = []

    for ext in image_extensions:
        images.extend(base_path.rglob(f"*{ext}"))

    return sorted(images)


def find_markdown_for_doc_id(doc_id: str) -> Path:
    """Find markdown file for a given document ID"""
    kb_path = Path("knowledge_base/processed")

    for md_file in kb_path.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if frontmatter.get('id') == doc_id:
                        return md_file
        except Exception as e:
            continue

    return None


def get_doc_id_from_image_path(image_path: Path) -> str:
    """Extract document ID from image path"""
    # Image paths are typically: knowledge_base/media/{source}/{doc_id}/image.jpg
    parts = image_path.parts

    # Find the doc_id (usually the parent directory name)
    if len(parts) >= 2:
        return parts[-2]  # Parent directory

    return None


def update_markdown_with_analysis(md_file: Path, analysis: dict) -> bool:
    """Update markdown file frontmatter with visual analysis"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        if not content.startswith('---'):
            print(f"  Warning: No frontmatter in {md_file.name}")
            return False

        parts = content.split('---', 2)
        if len(parts) < 3:
            return False

        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]

        # Add visual analysis fields
        ocr = analysis.get('ocr', {})
        vision = analysis.get('vision', {})

        if ocr:
            frontmatter['ocr_text'] = ocr.get('text', '')
            frontmatter['ocr_confidence'] = round(ocr.get('confidence', 0), 2)
            frontmatter['has_text'] = ocr.get('has_text', False)

        if vision:
            frontmatter['vision_description'] = vision.get('description', '')
            frontmatter['vision_tags'] = vision.get('tags', [])
            frontmatter['vision_scene_type'] = vision.get('scene_type', '')
            frontmatter['detected_objects'] = vision.get('detected_objects', [])

        frontmatter['visual_analysis_date'] = datetime.now().isoformat()
        frontmatter['visual_analysis_status'] = analysis.get('status', 'success')

        # Reconstruct markdown
        new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---{body}"

        # Write back
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"  Error updating {md_file.name}: {e}")
        return False


def audit_images(verbose: bool = False):
    """Audit existing images and their analysis status"""
    images = find_all_images()
    print(f"\n{'='*60}")
    print(f"Image Audit")
    print(f"{'='*60}\n")

    if not images:
        print("No images found in knowledge base")
        return

    analyzed = 0
    pending = 0
    no_markdown = 0

    for img_path in images:
        doc_id = get_doc_id_from_image_path(img_path)
        if not doc_id:
            continue

        md_file = find_markdown_for_doc_id(doc_id)

        if not md_file:
            no_markdown += 1
            if verbose:
                print(f"❌ {img_path.name} - No markdown file")
            continue

        # Check if already analyzed
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'visual_analysis_date' in content:
            analyzed += 1
            if verbose:
                print(f"✓ {img_path.name} - Analyzed")
        else:
            pending += 1
            if verbose:
                print(f"⏳ {img_path.name} - Pending")

    print(f"\nTotal images: {len(images)}")
    print(f"  ✓ Analyzed: {analyzed}")
    print(f"  ⏳ Pending: {pending}")
    print(f"  ❌ No markdown: {no_markdown}")
    print(f"\n{'='*60}\n")


def process_images(
    folder: str = None,
    limit: int = None,
    skip_vision: bool = False,
    reprocess: bool = False,
    test_mode: bool = False
):
    """Process images with visual translator"""
    # Find images
    if folder:
        base_path = Path(f"knowledge_base/media/{folder}")
        images = find_all_images(base_path)
    else:
        images = find_all_images()

    if not images:
        print("No images found to process")
        return

    # Filter out already processed (unless reprocess=True)
    if not reprocess:
        unprocessed = []
        for img_path in images:
            doc_id = get_doc_id_from_image_path(img_path)
            if doc_id:
                md_file = find_markdown_for_doc_id(doc_id)
                if md_file:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        if 'visual_analysis_date' not in f.read():
                            unprocessed.append(img_path)
                else:
                    unprocessed.append(img_path)
        images = unprocessed

    if not images:
        print("All images already analyzed!")
        return

    # Apply limit
    if limit:
        images = images[:limit]

    print(f"\n{'='*60}")
    print(f"Processing {len(images)} images")
    if test_mode:
        print("TEST MODE - No files will be modified")
    if skip_vision:
        print("OCR Only - Skipping vision analysis")
    print(f"{'='*60}\n")

    # Load config
    config_path = Path("config/settings.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        rate_limit = config.get('visual_translator', {}).get('rate_limit_delay_seconds', 1.0)
    else:
        rate_limit = 1.0

    # Batch analyze
    results = batch_analyze_images(
        images,
        skip_vision=skip_vision,
        rate_limit_delay=rate_limit
    )

    # Update markdown files
    if not test_mode:
        print(f"\nUpdating markdown files...")
        updated = 0

        for img_path, analysis in zip(images, results):
            doc_id = get_doc_id_from_image_path(img_path)
            if not doc_id:
                continue

            md_file = find_markdown_for_doc_id(doc_id)
            if md_file:
                if update_markdown_with_analysis(md_file, analysis):
                    updated += 1
                    print(f"  ✓ Updated: {md_file.name}")

        print(f"\n✓ Updated {updated} markdown files")

        # Remind to re-index
        print(f"\n⚠️  Remember to re-index embeddings:")
        print(f"   python scripts/processors/embeddings_generator.py --rebuild")
    else:
        print("\nTest mode - no files were modified")

    print(f"\n{'='*60}\n")


def main():
    """CLI for batch visual translator"""
    parser = argparse.ArgumentParser(
        description='Batch Visual Translator - Analyze images in knowledge base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Audit current status
  python batch_visual_translator.py --audit

  # Test with first 5 images
  python batch_visual_translator.py --test --limit 5

  # Process all pending images (OCR only, free)
  python batch_visual_translator.py --all --ocr-only

  # Process all with vision AI
  python batch_visual_translator.py --all --vision

  # Process specific folder
  python batch_visual_translator.py --folder instagram

  # Reprocess everything
  python batch_visual_translator.py --all --reprocess
        """
    )

    parser.add_argument('--audit', action='store_true',
                        help='Audit images and show analysis status')
    parser.add_argument('--all', action='store_true',
                        help='Process all images')
    parser.add_argument('--folder', type=str,
                        help='Process images from specific folder (instagram/web_imports/attachments)')
    parser.add_argument('--limit', type=int,
                        help='Limit number of images to process')
    parser.add_argument('--ocr-only', action='store_true', dest='ocr_only',
                        help='Skip vision analysis (OCR only, free)')
    parser.add_argument('--vision', action='store_true',
                        help='Include Claude vision analysis (costs ~$0.024/image)')
    parser.add_argument('--reprocess', action='store_true',
                        help='Reprocess already analyzed images')
    parser.add_argument('--test', action='store_true',
                        help='Test mode - analyze but don\'t update files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    # Audit mode
    if args.audit:
        audit_images(verbose=args.verbose)
        return 0

    # Processing mode
    if args.all or args.folder:
        skip_vision = args.ocr_only or not args.vision

        process_images(
            folder=args.folder,
            limit=args.limit,
            skip_vision=skip_vision,
            reprocess=args.reprocess,
            test_mode=args.test
        )
    else:
        parser.print_help()
        print("\n⚠️  Please specify --audit, --all, or --folder")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
