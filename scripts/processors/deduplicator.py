#!/usr/bin/env python3
"""
Knowledge Base Deduplicator

Intelligently merges duplicate queries across different sources while preserving all metadata.

Features:
1. Image similarity detection (perceptual hashing)
2. Metadata-based matching (title, URL, blockchain ID)
3. Multi-source merging (web + NFT + audio, etc.)
4. Scrape history preservation
5. Unified query blocks with multiple source badges

Duplicate detection methods:
- Perceptual image hashing (pHash) - finds visually similar images
- Exact image hash (MD5) - finds identical files
- Title matching with fuzzy logic
- Blockchain token ID matching
- URL matching for web imports
"""

import hashlib
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import shutil

# Image similarity
try:
    from PIL import Image
    import imagehash
    IMAGE_HASH_AVAILABLE = True
except ImportError:
    IMAGE_HASH_AVAILABLE = False
    print("Warning: PIL/imagehash not available. Install with: pip install pillow imagehash")

# Fuzzy string matching
try:
    from difflib import SequenceMatcher
    FUZZY_MATCH_AVAILABLE = True
except ImportError:
    FUZZY_MATCH_AVAILABLE = False


class QueryDeduplicator:
    """Deduplicates and merges queries from different sources"""

    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.kb_path = Path(knowledge_base_path)
        self.media_path = self.kb_path / "media"
        self.processed_path = self.kb_path / "processed"

        # Caches
        self.image_hashes = {}  # path -> perceptual hash
        self.exact_hashes = {}  # path -> MD5 hash
        self.documents = {}     # doc_id -> document data
        self.duplicates = defaultdict(list)  # canonical_id -> [duplicate_ids]

    def calculate_image_hash(self, img_path: Path) -> Optional[str]:
        """Calculate perceptual hash of an image"""
        if not IMAGE_HASH_AVAILABLE:
            return None

        try:
            img = Image.open(img_path)
            # Use perceptual hash (pHash) - detects similar images even with slight differences
            phash = imagehash.phash(img, hash_size=16)
            return str(phash)
        except Exception as e:
            print(f"  ✗ Error hashing {img_path}: {e}")
            return None

    def calculate_exact_hash(self, img_path: Path) -> Optional[str]:
        """Calculate exact MD5 hash of file"""
        try:
            with open(img_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"  ✗ Error hashing {img_path}: {e}")
            return None

    def fuzzy_match_titles(self, title1: str, title2: str, threshold: float = 0.85) -> bool:
        """Check if two titles are similar using fuzzy matching"""
        if not title1 or not title2:
            return False

        # Normalize
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        if t1 == t2:
            return True

        if not FUZZY_MATCH_AVAILABLE:
            return False

        ratio = SequenceMatcher(None, t1, t2).ratio()
        return ratio >= threshold

    def find_duplicates_by_image(self, hamming_threshold: int = 5) -> Dict[str, List[str]]:
        """
        Find duplicate images using perceptual hashing

        Args:
            hamming_threshold: Max Hamming distance for images to be considered duplicates
                              Lower = more strict, Higher = more lenient
                              0 = exact match, 5 = very similar, 10 = somewhat similar

        Returns:
            Dict of canonical_image_path -> [duplicate_image_paths]
        """
        if not IMAGE_HASH_AVAILABLE:
            print("⚠ Image hashing not available, skipping image-based deduplication")
            return {}

        print(f"\n→ Calculating image hashes...")

        # Find all images in media directories
        image_paths = []
        for source_dir in self.media_path.iterdir():
            if source_dir.is_dir():
                for doc_dir in source_dir.iterdir():
                    if doc_dir.is_dir():
                        for img_file in doc_dir.iterdir():
                            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                image_paths.append(img_file)

        print(f"  Found {len(image_paths)} images")

        # Calculate hashes
        for img_path in image_paths:
            phash = self.calculate_image_hash(img_path)
            if phash:
                self.image_hashes[str(img_path)] = imagehash.hex_to_hash(phash)

        print(f"  Calculated {len(self.image_hashes)} perceptual hashes")

        # Find duplicates by comparing hashes
        print(f"\n→ Finding duplicates (Hamming distance ≤ {hamming_threshold})...")

        duplicates = defaultdict(list)
        processed = set()

        hash_to_path = {hash_val: path for path, hash_val in self.image_hashes.items()}

        for path1, hash1 in self.image_hashes.items():
            if path1 in processed:
                continue

            # Find all images with similar hashes
            similar = []
            for path2, hash2 in self.image_hashes.items():
                if path1 == path2:
                    continue

                # Calculate Hamming distance
                distance = hash1 - hash2

                if distance <= hamming_threshold:
                    similar.append(path2)
                    processed.add(path2)

            if similar:
                duplicates[path1] = similar
                processed.add(path1)

        print(f"  ✓ Found {len(duplicates)} groups of duplicate images")

        return dict(duplicates)

    def find_duplicates_by_metadata(self) -> Dict[str, List[str]]:
        """
        Find duplicate documents by metadata matching

        Checks:
        - Same blockchain token ID + contract
        - Same title (fuzzy match)
        - Same source URL
        """
        print(f"\n→ Finding duplicates by metadata...")

        # Load all documents
        for subject_dir in self.processed_path.iterdir():
            if subject_dir.is_dir():
                for md_file in subject_dir.glob("*.md"):
                    doc_data = self.load_document(md_file)
                    if doc_data:
                        self.documents[doc_data['id']] = doc_data

        print(f"  Loaded {len(self.documents)} documents")

        # Group by different criteria
        by_blockchain_id = defaultdict(list)
        by_title = defaultdict(list)
        by_url = defaultdict(list)

        for doc_id, doc in self.documents.items():
            # Blockchain matching
            if doc.get('blockchain_token_id') and doc.get('blockchain_contract'):
                key = f"{doc['blockchain_contract']}:{doc['blockchain_token_id']}"
                by_blockchain_id[key].append(doc_id)

            # Title matching
            if doc.get('title'):
                # Normalize title for grouping
                normalized = doc['title'].lower().strip()
                by_title[normalized].append(doc_id)

            # URL matching
            if doc.get('url'):
                by_url[doc['url']].append(doc_id)

        # Find duplicates
        duplicates = defaultdict(set)

        # Blockchain duplicates (exact match)
        for token_key, doc_ids in by_blockchain_id.items():
            if len(doc_ids) > 1:
                canonical = doc_ids[0]
                for dup_id in doc_ids[1:]:
                    duplicates[canonical].add(dup_id)

        # URL duplicates (exact match)
        for url, doc_ids in by_url.items():
            if len(doc_ids) > 1:
                canonical = doc_ids[0]
                for dup_id in doc_ids[1:]:
                    duplicates[canonical].add(dup_id)

        # Title duplicates (fuzzy match)
        title_groups = list(by_title.values())
        for i, group1 in enumerate(title_groups):
            for group2 in title_groups[i+1:]:
                # Check if titles are similar
                if group1 and group2:
                    doc1 = self.documents[group1[0]]
                    doc2 = self.documents[group2[0]]

                    if self.fuzzy_match_titles(doc1.get('title', ''), doc2.get('title', '')):
                        # Merge groups
                        canonical = group1[0]
                        for dup_id in group2:
                            duplicates[canonical].add(dup_id)

        # Convert sets to lists
        duplicates = {k: list(v) for k, v in duplicates.items() if v}

        print(f"  ✓ Found {len(duplicates)} groups of metadata duplicates")

        return duplicates

    def load_document(self, md_path: Path) -> Optional[Dict]:
        """Load a markdown document with frontmatter"""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter
            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2]

            return {
                'id': frontmatter.get('id'),
                'path': str(md_path),
                'frontmatter': frontmatter,
                'body': body,
                'title': frontmatter.get('title', ''),
                'url': frontmatter.get('url', ''),
                'source': frontmatter.get('source', ''),
                'type': frontmatter.get('type', ''),
                'blockchain_token_id': frontmatter.get('blockchain_token_id'),
                'blockchain_contract': frontmatter.get('blockchain_contract'),
                'tags': frontmatter.get('tags', []),
                'created_at': frontmatter.get('created_at', ''),
                'images': frontmatter.get('images', [])
            }
        except Exception as e:
            print(f"  ✗ Error loading {md_path}: {e}")
            return None

    def merge_documents(self, canonical_id: str, duplicate_ids: List[str]) -> Dict:
        """
        Merge duplicate documents into a single unified document

        Strategy:
        1. Use canonical document as base
        2. Combine all source types (web, nft, audio, etc.)
        3. Merge all metadata fields
        4. Preserve all scrape timestamps
        5. Combine all tags
        6. Link all images
        """
        canonical_doc = self.documents[canonical_id]
        duplicate_docs = [self.documents[dup_id] for dup_id in duplicate_ids]

        print(f"\n→ Merging {len(duplicate_ids) + 1} documents:")
        print(f"  Canonical: {canonical_id} ({canonical_doc.get('source')})")
        for dup_doc in duplicate_docs:
            print(f"  Duplicate: {dup_doc['id']} ({dup_doc.get('source')})")

        # Merged frontmatter
        merged = canonical_doc['frontmatter'].copy()

        # Collect all source types
        all_sources = [canonical_doc.get('source')]
        all_source_types = [canonical_doc.get('type')]

        for dup_doc in duplicate_docs:
            if dup_doc.get('source') and dup_doc['source'] not in all_sources:
                all_sources.append(dup_doc['source'])
            if dup_doc.get('type') and dup_doc['type'] not in all_source_types:
                all_source_types.append(dup_doc['type'])

        # Multi-source metadata
        merged['sources'] = all_sources
        merged['source_types'] = all_source_types
        merged['is_merged'] = True
        merged['merged_from'] = duplicate_ids
        merged['merge_date'] = datetime.now().isoformat()

        # Combine scrape history
        scrape_history = []
        for doc in [canonical_doc] + duplicate_docs:
            scrape_history.append({
                'doc_id': doc['id'],
                'source': doc.get('source'),
                'type': doc.get('type'),
                'scraped_at': doc.get('created_at'),
                'url': doc.get('url'),
                'platform': doc.get('platform')
            })
        merged['scrape_history'] = scrape_history

        # Merge tags (union)
        all_tags = set(canonical_doc.get('tags', []))
        for dup_doc in duplicate_docs:
            all_tags.update(dup_doc.get('tags', []))
        merged['tags'] = sorted(list(all_tags))

        # Merge blockchain metadata (prefer most complete)
        if not merged.get('blockchain_token_id'):
            for dup_doc in duplicate_docs:
                if dup_doc['frontmatter'].get('blockchain_token_id'):
                    merged['blockchain_token_id'] = dup_doc['frontmatter']['blockchain_token_id']
                    merged['blockchain_contract'] = dup_doc['frontmatter'].get('blockchain_contract')
                    merged['blockchain_network'] = dup_doc['frontmatter'].get('blockchain_network')
                    break

        # Merge URLs (collect all)
        all_urls = []
        for doc in [canonical_doc] + duplicate_docs:
            url = doc.get('url')
            if url and url not in all_urls:
                all_urls.append(url)
        if all_urls:
            merged['urls'] = all_urls
            merged['url'] = all_urls[0]  # Keep first as primary

        # Collect all images from all sources
        all_images = []
        for doc in [canonical_doc] + duplicate_docs:
            doc_images = doc.get('images', [])
            if isinstance(doc_images, list):
                all_images.extend(doc_images)

        # Deduplicate images by path
        unique_images = []
        seen_paths = set()
        for img in all_images:
            if isinstance(img, dict):
                img_path = img.get('path', '')
                if img_path and img_path not in seen_paths:
                    unique_images.append(img)
                    seen_paths.add(img_path)

        merged['images'] = unique_images
        merged['image_count'] = len(unique_images)
        merged['has_images'] = len(unique_images) > 0

        # Use longest/best title
        all_titles = [canonical_doc.get('title', '')]
        for dup_doc in duplicate_docs:
            if dup_doc.get('title'):
                all_titles.append(dup_doc['title'])

        # Pick best title (longest non-generic one)
        best_title = canonical_doc.get('title', '')
        for title in all_titles:
            # Prefer titles that aren't generic "Image 1" patterns
            if not re.match(r'^(Image|Artwork|NFT)\s+\d+$', title, re.I):
                if len(title) > len(best_title):
                    best_title = title

        merged['title'] = best_title

        # Combine body content
        merged_body = canonical_doc['body']
        merged_body += "\n\n---\n\n## Merged Sources\n\n"
        merged_body += f"This query has been merged from {len(duplicate_ids) + 1} sources:\n\n"

        for doc in [canonical_doc] + duplicate_docs:
            merged_body += f"- **{doc.get('source', 'unknown')}** ({doc.get('type', 'unknown')}) - {doc.get('created_at', 'unknown date')}\n"

        merged_body += f"\n**Merge Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return {
            'frontmatter': merged,
            'body': merged_body,
            'canonical_id': canonical_id,
            'duplicate_ids': duplicate_ids
        }

    def save_merged_document(self, merged_doc: Dict, output_dir: Path):
        """Save merged document and mark duplicates as archived"""

        canonical_id = merged_doc['canonical_id']
        frontmatter = merged_doc['frontmatter']
        body = merged_doc['body']

        # Determine output path (use canonical document's location)
        canonical_path = Path(self.documents[canonical_id]['path'])
        output_path = output_dir / canonical_path.name

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write merged document
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('---\n')
            f.write(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True))
            f.write('---\n\n')
            f.write(body)

        print(f"  ✓ Saved merged document: {output_path}")

        # Archive duplicate documents
        archive_dir = self.kb_path / "archived" / "duplicates" / datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_dir.mkdir(parents=True, exist_ok=True)

        for dup_id in merged_doc['duplicate_ids']:
            dup_path = Path(self.documents[dup_id]['path'])
            archive_path = archive_dir / dup_path.name

            # Move to archive
            shutil.move(str(dup_path), str(archive_path))
            print(f"  ✓ Archived duplicate: {dup_path.name}")

        return output_path

    def deduplicate_knowledge_base(self, dry_run: bool = True, hamming_threshold: int = 5):
        """
        Main deduplication process

        Args:
            dry_run: If True, only report duplicates without making changes
            hamming_threshold: Image similarity threshold (0-10, lower = more strict)
        """
        print(f"\n{'='*70}")
        print(f"KNOWLEDGE BASE DEDUPLICATOR")
        print(f"Mode: {'DRY RUN' if dry_run else 'ACTIVE DEDUPLICATION'}")
        print(f"{'='*70}\n")

        # Find duplicates by different methods
        image_duplicates = self.find_duplicates_by_image(hamming_threshold=hamming_threshold)
        metadata_duplicates = self.find_duplicates_by_metadata()

        # Combine duplicate groups
        all_duplicates = defaultdict(set)

        # Add image duplicates
        for canonical, dups in image_duplicates.items():
            # Map image path to document ID
            canonical_doc_id = self.get_doc_id_from_image_path(canonical)
            if canonical_doc_id:
                for dup_path in dups:
                    dup_doc_id = self.get_doc_id_from_image_path(dup_path)
                    if dup_doc_id:
                        all_duplicates[canonical_doc_id].add(dup_doc_id)

        # Add metadata duplicates
        for canonical, dups in metadata_duplicates.items():
            all_duplicates[canonical].update(dups)

        # Convert to lists
        all_duplicates = {k: list(v) for k, v in all_duplicates.items() if v}

        print(f"\n{'='*70}")
        print(f"DUPLICATE SUMMARY")
        print(f"{'='*70}")
        print(f"Total duplicate groups: {len(all_duplicates)}")
        print(f"Total documents to merge: {sum(len(v) + 1 for v in all_duplicates.values())}")
        print(f"Documents to be archived: {sum(len(v) for v in all_duplicates.values())}")
        print(f"{'='*70}\n")

        if not all_duplicates:
            print("✓ No duplicates found!")
            return

        # Show duplicates
        for i, (canonical_id, dup_ids) in enumerate(all_duplicates.items(), 1):
            canonical_doc = self.documents.get(canonical_id)
            if not canonical_doc:
                continue

            print(f"\n{i}. Duplicate Group:")
            print(f"   Canonical: {canonical_doc.get('title', 'Untitled')} ({canonical_doc.get('source')})")

            for dup_id in dup_ids:
                dup_doc = self.documents.get(dup_id)
                if dup_doc:
                    print(f"   Duplicate:  {dup_doc.get('title', 'Untitled')} ({dup_doc.get('source')})")

        if dry_run:
            print(f"\n{'='*70}")
            print(f"DRY RUN - No changes made")
            print(f"Run with --execute to perform deduplication")
            print(f"{'='*70}\n")
            return

        # Perform deduplication
        print(f"\n{'='*70}")
        print(f"MERGING DUPLICATES")
        print(f"{'='*70}\n")

        output_dir = self.processed_path
        merged_count = 0

        for canonical_id, dup_ids in all_duplicates.items():
            merged_doc = self.merge_documents(canonical_id, dup_ids)
            self.save_merged_document(merged_doc, output_dir)
            merged_count += 1

        print(f"\n{'='*70}")
        print(f"DEDUPLICATION COMPLETE")
        print(f"{'='*70}")
        print(f"Merged: {merged_count} groups")
        print(f"Archived: {sum(len(v) for v in all_duplicates.values())} duplicates")
        print(f"{'='*70}\n")

    def get_doc_id_from_image_path(self, img_path: str) -> Optional[str]:
        """Extract document ID from image path"""
        # Path format: knowledge_base/media/<source>/<doc_id>/<image_file>
        parts = Path(img_path).parts

        if 'media' in parts:
            media_idx = parts.index('media')
            if len(parts) > media_idx + 2:
                return parts[media_idx + 2]  # doc_id is 2 levels after media

        return None


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Deduplicate knowledge base queries')
    parser.add_argument('--execute', action='store_true', help='Actually perform deduplication (default: dry run)')
    parser.add_argument('--threshold', type=int, default=5, help='Image similarity threshold (0-10, default: 5)')
    parser.add_argument('--kb-path', type=str, default='knowledge_base', help='Path to knowledge base')

    args = parser.parse_args()

    deduplicator = QueryDeduplicator(knowledge_base_path=args.kb_path)
    deduplicator.deduplicate_knowledge_base(
        dry_run=not args.execute,
        hamming_threshold=args.threshold
    )


if __name__ == "__main__":
    main()
