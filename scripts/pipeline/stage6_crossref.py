"""
DOC-8 Agent Analysis Pipeline - Stage 6: Cross-Reference

Handles:
- Match segments against existing knowledge base
- Identify connections between sources
- Detect duplicate or related content
- Build knowledge graph connections
- Verify claims against known facts
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from .models import (
    Source, Segment, Entity, Connection,
    VerificationStatus, ProcessingStatus
)


class CrossRefError(Exception):
    """Error during cross-referencing"""
    pass


@dataclass
class KnowledgeEntry:
    """An entry in the knowledge base"""
    entry_id: str
    source_id: str
    content: str
    content_hash: str
    entities: List[Dict] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    speaker: Optional[str] = None


class Stage6CrossRef:
    """
    Stage 6: Cross-Reference

    Matches new content against existing knowledge base.
    Builds connections between sources and identifies duplicates.
    """

    def __init__(self, knowledge_base_path: str = None):
        """
        Initialize cross-reference stage.

        Args:
            knowledge_base_path: Path to knowledge base directory
        """
        self.kb_path = Path(knowledge_base_path or '~/.arc8/knowledge_base').expanduser()
        self.kb_path.mkdir(parents=True, exist_ok=True)

        # In-memory index for fast lookup
        self.content_hashes: Dict[str, List[str]] = {}  # hash -> [entry_ids]
        self.entity_index: Dict[str, List[str]] = {}    # entity -> [entry_ids]
        self.topic_index: Dict[str, List[str]] = {}     # topic -> [entry_ids]
        self.speaker_index: Dict[str, List[str]] = {}   # speaker -> [entry_ids]

        self._loaded = False

    def _load_knowledge_base(self):
        """Load knowledge base into memory"""
        if self._loaded:
            return

        index_file = self.kb_path / 'index.json'
        if index_file.exists():
            with open(index_file) as f:
                data = json.load(f)
                self.content_hashes = data.get('content_hashes', {})
                self.entity_index = data.get('entity_index', {})
                self.topic_index = data.get('topic_index', {})
                self.speaker_index = data.get('speaker_index', {})

        self._loaded = True
        print(f"[Stage6] Loaded knowledge base: {len(self.content_hashes)} content hashes")

    def _save_index(self):
        """Save knowledge base index"""
        index_file = self.kb_path / 'index.json'
        with open(index_file, 'w') as f:
            json.dump({
                'content_hashes': self.content_hashes,
                'entity_index': self.entity_index,
                'topic_index': self.topic_index,
                'speaker_index': self.speaker_index,
            }, f)

    def crossref(self, source: Source) -> Source:
        """
        Cross-reference source against knowledge base.

        Args:
            source: Source with extracted entities

        Returns:
            Source with connections populated
        """
        source.status = ProcessingStatus.CROSSREFERENCING
        self._load_knowledge_base()

        try:
            for segment in source.segments:
                # Check for duplicate content
                duplicates = self._find_duplicates(segment)
                if duplicates:
                    self._handle_duplicates(segment, duplicates)

                # Find related content by entities
                entity_matches = self._find_by_entities(segment)
                for match in entity_matches:
                    self._create_connection(segment, match, 'shared_entity')

                # Find related content by topics
                topic_matches = self._find_by_topics(segment)
                for match in topic_matches:
                    if match not in entity_matches:  # Avoid duplicates
                        self._create_connection(segment, match, 'shared_topic')

                # Find related content by speaker
                if segment.speaker_name:
                    speaker_matches = self._find_by_speaker(segment)
                    for match in speaker_matches:
                        self._create_connection(segment, match, 'same_speaker')

            # Add source to knowledge base
            self._add_to_knowledge_base(source)

            # Calculate connection statistics
            self._calculate_connection_stats(source)

            return source

        except Exception as e:
            source.error_message = str(e)
            source.error_stage = "crossref"
            raise CrossRefError(f"Cross-referencing failed: {e}")

    def _content_hash(self, text: str) -> str:
        """Generate content hash for deduplication"""
        # Normalize text before hashing
        normalized = ' '.join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _find_duplicates(self, segment: Segment) -> List[str]:
        """Find duplicate or near-duplicate content"""
        content_hash = self._content_hash(segment.content_raw)

        # Exact match
        if content_hash in self.content_hashes:
            return self.content_hashes[content_hash]

        return []

    def _handle_duplicates(self, segment: Segment, duplicate_ids: List[str]):
        """Handle duplicate content detection"""
        # Mark segment as potential duplicate
        segment.verification.status = VerificationStatus.NEEDS_REVIEW
        segment.verification.verification_notes = f"Potential duplicate of: {', '.join(duplicate_ids[:3])}"

        # Reduce training weight for duplicates
        segment.training_weight = max(segment.training_weight - 0.3, 0.1)

        if 'duplicate' not in segment.training_categories:
            segment.training_categories.append('duplicate')

    def _find_by_entities(self, segment: Segment) -> List[str]:
        """Find related content by shared entities"""
        matches = set()

        for entity in segment.entities:
            key = f"{entity.type}:{entity.value.lower()}"
            if key in self.entity_index:
                matches.update(self.entity_index[key])

        # Remove self-references
        matches.discard(segment.segment_id)
        return list(matches)[:10]  # Limit results

    def _find_by_topics(self, segment: Segment) -> List[str]:
        """Find related content by shared topics"""
        matches = set()

        for topic in segment.topics:
            topic_lower = topic.lower()
            if topic_lower in self.topic_index:
                matches.update(self.topic_index[topic_lower])

        matches.discard(segment.segment_id)
        return list(matches)[:10]

    def _find_by_speaker(self, segment: Segment) -> List[str]:
        """Find content from same speaker"""
        if not segment.speaker_name:
            return []

        speaker_key = segment.speaker_name.lower()
        if speaker_key in self.speaker_index:
            matches = set(self.speaker_index[speaker_key])
            matches.discard(segment.segment_id)
            return list(matches)[:20]

        return []

    def _create_connection(self, segment: Segment, related_id: str, connection_type: str):
        """Create a connection between segments"""
        connection = Connection(
            source_segment_id=segment.segment_id,
            target_segment_id=related_id,
            connection_type=connection_type,
            strength=0.5  # Base strength
        )

        # Adjust strength based on type
        if connection_type == 'same_speaker':
            connection.strength = 0.7
        elif connection_type == 'shared_entity':
            connection.strength = 0.6

        segment.connections.append(connection)

    def _add_to_knowledge_base(self, source: Source):
        """Add source segments to knowledge base"""
        for segment in source.segments:
            entry_id = segment.segment_id

            # Add content hash
            content_hash = self._content_hash(segment.content_raw)
            if content_hash not in self.content_hashes:
                self.content_hashes[content_hash] = []
            if entry_id not in self.content_hashes[content_hash]:
                self.content_hashes[content_hash].append(entry_id)

            # Add to entity index
            for entity in segment.entities:
                key = f"{entity.type}:{entity.value.lower()}"
                if key not in self.entity_index:
                    self.entity_index[key] = []
                if entry_id not in self.entity_index[key]:
                    self.entity_index[key].append(entry_id)

            # Add to topic index
            for topic in segment.topics:
                topic_lower = topic.lower()
                if topic_lower not in self.topic_index:
                    self.topic_index[topic_lower] = []
                if entry_id not in self.topic_index[topic_lower]:
                    self.topic_index[topic_lower].append(entry_id)

            # Add to speaker index
            if segment.speaker_name:
                speaker_key = segment.speaker_name.lower()
                if speaker_key not in self.speaker_index:
                    self.speaker_index[speaker_key] = []
                if entry_id not in self.speaker_index[speaker_key]:
                    self.speaker_index[speaker_key].append(entry_id)

        # Save updated index
        self._save_index()

    def _calculate_connection_stats(self, source: Source):
        """Calculate connection statistics for source"""
        total_connections = 0
        connection_types = defaultdict(int)

        for segment in source.segments:
            total_connections += len(segment.connections)
            for conn in segment.connections:
                connection_types[conn.connection_type] += 1

        # Store in source metadata
        source.metadata['connection_count'] = total_connections
        source.metadata['connection_types'] = dict(connection_types)

    def find_related(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find related content for a query string.

        Utility method for search integration.
        """
        self._load_knowledge_base()
        results = []

        # Search by content similarity (basic keyword matching)
        query_words = set(query.lower().split())

        # Search topics
        for topic, entry_ids in self.topic_index.items():
            if any(word in topic for word in query_words):
                for entry_id in entry_ids[:limit]:
                    results.append({
                        'entry_id': entry_id,
                        'match_type': 'topic',
                        'matched_value': topic
                    })

        # Search entities
        for entity_key, entry_ids in self.entity_index.items():
            entity_type, entity_value = entity_key.split(':', 1)
            if any(word in entity_value for word in query_words):
                for entry_id in entry_ids[:limit]:
                    results.append({
                        'entry_id': entry_id,
                        'match_type': 'entity',
                        'entity_type': entity_type,
                        'matched_value': entity_value
                    })

        # Deduplicate and limit
        seen = set()
        unique_results = []
        for r in results:
            if r['entry_id'] not in seen:
                seen.add(r['entry_id'])
                unique_results.append(r)
                if len(unique_results) >= limit:
                    break

        return unique_results

    def get_knowledge_stats(self) -> Dict:
        """Get knowledge base statistics"""
        self._load_knowledge_base()

        return {
            'unique_content_hashes': len(self.content_hashes),
            'total_entries': sum(len(v) for v in self.content_hashes.values()),
            'unique_entities': len(self.entity_index),
            'unique_topics': len(self.topic_index),
            'unique_speakers': len(self.speaker_index),
        }


# CLI for testing
if __name__ == '__main__':
    import sys

    crossref = Stage6CrossRef()

    if len(sys.argv) < 2:
        # Show stats
        stats = crossref.get_knowledge_stats()
        print("Knowledge Base Statistics:")
        print("-" * 40)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif sys.argv[1] == 'search':
        if len(sys.argv) < 3:
            print("Usage: python stage6_crossref.py search <query>")
            sys.exit(1)
        query = ' '.join(sys.argv[2:])
        results = crossref.find_related(query)
        print(f"Found {len(results)} related entries for '{query}':")
        for r in results:
            print(f"  [{r['match_type']}] {r['entry_id']}: {r.get('matched_value', '')}")
    else:
        from .orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()
        source = orchestrator.get_result(sys.argv[1])

        if not source:
            print(f"Source not found: {sys.argv[1]}")
            sys.exit(1)

        source = crossref.crossref(source)

        print(f"Cross-referencing complete!")
        print(f"Total connections: {source.metadata.get('connection_count', 0)}")
        print("\nConnection types:")
        for conn_type, count in source.metadata.get('connection_types', {}).items():
            print(f"  {conn_type}: {count}")
