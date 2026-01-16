"""
DOC-8 Agent Analysis Pipeline - Stage 4: Segmentation

Handles:
- Split by natural topic boundaries
- Identify key passages
- Mark quotable segments
- Create semantic chunks for embedding
- Generate segment summaries
"""

import re
from typing import List, Optional, Tuple
from collections import defaultdict

from .models import Source, Segment, SegmentType, ProcessingStatus


class SegmentError(Exception):
    """Error during segmentation"""
    pass


class Stage4Segment:
    """
    Stage 4: Topic Segmentation

    Splits content into meaningful topic-based segments.
    Identifies key passages and quotable content.
    """

    def __init__(self, min_segment_length: int = 50, max_segment_length: int = 500):
        """
        Initialize segmentation stage.

        Args:
            min_segment_length: Minimum characters per segment
            max_segment_length: Maximum characters before splitting
        """
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length

        # Quotable indicators
        self.quotable_patterns = [
            r'^"[^"]+"\s*$',  # Quoted text
            r'I believe|I think|In my view|The key is|The important thing',
            r'always|never|must|should|essential|critical|fundamental',
            r'remember|forget|realize|understand|discover',
        ]

        # Topic boundary indicators
        self.boundary_indicators = [
            r'\n\n+',  # Paragraph breaks
            r'(?:Now|Next|Also|Furthermore|However|But|So|Therefore),?\s',
            r'(?:First|Second|Third|Finally|Lastly),?\s',
            r'(?:On the other hand|In contrast|Meanwhile)',
            r'(?:Let me|I want to|I\'d like to)',
        ]

    def segment(self, source: Source) -> Source:
        """
        Perform topic segmentation on source.

        Args:
            source: Source with raw segments

        Returns:
            Source with refined topic-based segments
        """
        source.status = ProcessingStatus.SEGMENTING

        try:
            # Merge and re-segment based on topics
            if source.segments:
                source.segments = self._refine_segments(source.segments)

            # Identify segment types
            for segment in source.segments:
                segment.segment_type = self._classify_segment(segment)

            # Mark quotable segments
            self._mark_quotable(source.segments)

            # Generate summaries
            self._generate_summaries(source.segments)

            # Identify key passages
            self._identify_key_passages(source.segments)

            return source

        except Exception as e:
            source.error_message = str(e)
            source.error_stage = "segment"
            raise SegmentError(f"Segmentation failed: {e}")

    def _refine_segments(self, segments: List[Segment]) -> List[Segment]:
        """Refine segments based on topic boundaries"""
        if not segments:
            return segments

        refined = []
        current_group = []
        current_speaker = None

        for segment in segments:
            # Check for topic boundary
            is_boundary = self._is_topic_boundary(segment, current_group)
            speaker_changed = segment.speaker_id != current_speaker and segment.speaker_id

            if (is_boundary or speaker_changed) and current_group:
                # Merge current group into one segment
                merged = self._merge_segments(current_group)
                if merged:
                    refined.append(merged)
                current_group = []

            current_group.append(segment)
            current_speaker = segment.speaker_id or current_speaker

        # Don't forget last group
        if current_group:
            merged = self._merge_segments(current_group)
            if merged:
                refined.append(merged)

        # Split overly long segments
        final = []
        for segment in refined:
            if len(segment.content_raw) > self.max_segment_length:
                final.extend(self._split_long_segment(segment))
            else:
                final.append(segment)

        return final

    def _is_topic_boundary(self, segment: Segment, current_group: List[Segment]) -> bool:
        """Detect if segment starts a new topic"""
        if not current_group:
            return False

        text = segment.content_raw

        # Check boundary patterns
        for pattern in self.boundary_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Long pause (if temporal data available)
        if segment.time_start and current_group[-1].time_end:
            gap = segment.time_start - current_group[-1].time_end
            if gap > 3.0:  # 3+ second pause
                return True

        return False

    def _merge_segments(self, segments: List[Segment]) -> Optional[Segment]:
        """Merge multiple segments into one"""
        if not segments:
            return None

        if len(segments) == 1:
            return segments[0]

        # Use first segment as base
        merged = Segment(
            source_id=segments[0].source_id,
            time_start=segments[0].time_start,
            time_end=segments[-1].time_end,
            speaker_id=segments[0].speaker_id,
            speaker_name=segments[0].speaker_name,
            speaker_role=segments[0].speaker_role,
            speaker_confidence=sum(s.speaker_confidence for s in segments) / len(segments)
        )

        # Merge content
        merged.content_raw = ' '.join(s.content_raw for s in segments)
        merged.content_normalized = merged.content_raw.lower()

        # Calculate duration
        if merged.time_start is not None and merged.time_end is not None:
            merged.duration = merged.time_end - merged.time_start

        # Merge entities
        seen_entities = set()
        for seg in segments:
            for entity in seg.entities:
                key = (entity.type, entity.value)
                if key not in seen_entities:
                    merged.entities.append(entity)
                    seen_entities.add(key)

        # Merge topics
        merged.topics = list(set(t for seg in segments for t in seg.topics))

        return merged

    def _split_long_segment(self, segment: Segment) -> List[Segment]:
        """Split a long segment at sentence boundaries"""
        text = segment.content_raw
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if len(sentences) <= 1:
            return [segment]

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > self.max_segment_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0

            current_chunk.append(sentence)
            current_length += len(sentence)

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        # Create new segments
        result = []
        for i, chunk in enumerate(chunks):
            new_seg = Segment(
                source_id=segment.source_id,
                speaker_id=segment.speaker_id,
                speaker_name=segment.speaker_name,
                speaker_role=segment.speaker_role,
                content_raw=chunk,
                content_normalized=chunk.lower()
            )
            result.append(new_seg)

        return result

    def _classify_segment(self, segment: Segment) -> SegmentType:
        """Classify segment as question, assertion, fact, etc."""
        text = segment.content_raw.strip()

        # Question detection
        if text.endswith('?'):
            return SegmentType.QUESTION

        # Quote detection
        if re.match(r'^["\'].*["\']$', text):
            return SegmentType.QUOTE

        # Opinion indicators
        opinion_patterns = [
            r'\b(I think|I believe|I feel|In my opinion|seems to me)\b',
            r'\b(probably|maybe|perhaps|possibly|might|could be)\b',
        ]
        for pattern in opinion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return SegmentType.OPINION

        # Fact indicators
        fact_patterns = [
            r'\b(research shows|studies indicate|according to|data suggests)\b',
            r'\b(in \d{4}|on \w+ \d+|percent|million|billion)\b',
            r'\b(is|are|was|were) (the|a|an) \w+\b',
        ]
        for pattern in fact_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return SegmentType.FACT

        # Default to assertion
        return SegmentType.ASSERTION

    def _mark_quotable(self, segments: List[Segment]):
        """Mark segments that are quotable"""
        for segment in segments:
            text = segment.content_raw

            # Check quotable patterns
            is_quotable = False
            for pattern in self.quotable_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    is_quotable = True
                    break

            # Short, punchy statements are quotable
            if 20 <= len(text) <= 150 and text.count(' ') >= 3:
                # Check for strong language
                if re.search(r'\b(always|never|must|key|secret|truth)\b', text, re.IGNORECASE):
                    is_quotable = True

            # Add to training categories if quotable
            if is_quotable:
                if 'quotable' not in segment.training_categories:
                    segment.training_categories.append('quotable')
                segment.training_weight = min(segment.training_weight + 0.2, 2.0)

    def _generate_summaries(self, segments: List[Segment]):
        """Generate one-line summaries for segments"""
        for segment in segments:
            text = segment.content_raw

            # Simple extractive summary: first sentence or truncated
            sentences = re.split(r'(?<=[.!?])\s+', text)
            if sentences:
                summary = sentences[0]
                if len(summary) > 100:
                    summary = summary[:97] + '...'
                segment.content_summary = summary

    def _identify_key_passages(self, segments: List[Segment]):
        """Identify key passages based on various signals"""
        if not segments:
            return

        # Score each segment
        scores = []
        for segment in segments:
            score = 0

            # Length score (medium length is best)
            length = len(segment.content_raw)
            if 50 <= length <= 200:
                score += 2
            elif 200 <= length <= 400:
                score += 1

            # Entity score
            score += min(len(segment.entities), 3)

            # Quotable bonus
            if 'quotable' in segment.training_categories:
                score += 2

            # Question/answer pairs are valuable
            if segment.segment_type == SegmentType.QUESTION:
                score += 1

            scores.append((score, segment))

        # Mark top 20% as key passages
        scores.sort(key=lambda x: x[0], reverse=True)
        top_count = max(1, len(scores) // 5)

        for score, segment in scores[:top_count]:
            if 'key_passage' not in segment.training_categories:
                segment.training_categories.append('key_passage')
            segment.training_weight = min(segment.training_weight + 0.3, 2.0)

    def segment_text(self, text: str, source_id: str) -> List[Segment]:
        """
        Segment raw text into structured segments.

        For documents and web content that don't have timestamps.
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)

        segments = []
        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < self.min_segment_length:
                continue

            segment = Segment(
                source_id=source_id,
                content_raw=para,
                content_normalized=para.lower()
            )

            # Classify and annotate
            segment.segment_type = self._classify_segment(segment)

            segments.append(segment)

        # Apply refinements
        self._mark_quotable(segments)
        self._generate_summaries(segments)
        self._identify_key_passages(segments)

        return segments


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python stage4_segment.py <source_id>")
        sys.exit(1)

    from .orchestrator import PipelineOrchestrator

    orchestrator = PipelineOrchestrator()
    source = orchestrator.get_result(sys.argv[1])

    if not source:
        print(f"Source not found: {sys.argv[1]}")
        sys.exit(1)

    segmenter = Stage4Segment()
    source = segmenter.segment(source)

    print(f"Segmentation complete!")
    print(f"Total segments: {len(source.segments)}")

    # Show segment type distribution
    type_counts = defaultdict(int)
    for seg in source.segments:
        type_counts[seg.segment_type.value] += 1

    print("\nSegment types:")
    for seg_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {seg_type}: {count}")

    # Show key passages
    key_passages = [s for s in source.segments if 'key_passage' in s.training_categories]
    print(f"\nKey passages: {len(key_passages)}")
    for kp in key_passages[:3]:
        print(f"  - {kp.content_summary or kp.content_raw[:80]}...")
