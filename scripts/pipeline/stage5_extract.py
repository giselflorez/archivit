"""
DOC-8 Agent Analysis Pipeline - Stage 5: Extraction

Handles:
- Named Entity Recognition (NER)
- Claim extraction
- Sentiment analysis
- Keyword extraction
- Reference detection
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

from .models import (
    Source, Segment, Entity, Claim, Sentiment,
    SegmentType, ProcessingStatus
)
# Note: SegmentType is used for Claim type classification


class ExtractError(Exception):
    """Error during extraction"""
    pass


class Stage5Extract:
    """
    Stage 5: Information Extraction

    Extracts structured information from segments:
    - Named entities (people, places, organizations, dates)
    - Claims and assertions
    - Sentiment indicators
    - Keywords and topics
    """

    def __init__(self, use_spacy: bool = True):
        """
        Initialize extraction stage.

        Args:
            use_spacy: Whether to use spaCy for NER (if available)
        """
        self.use_spacy = use_spacy
        self.nlp = None
        self._backend = None

        # Regex patterns for entity extraction (fallback)
        self.entity_patterns = {
            'person': [
                r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # First Last
                r'\b(Dr\.|Mr\.|Mrs\.|Ms\.) ([A-Z][a-z]+)\b',  # Title Name
            ],
            'date': [
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{4}\b',  # Year
                r'\b(19|20)\d{2}s?\b',  # Decade
            ],
            'organization': [
                r'\b([A-Z][A-Za-z]+ (?:Inc\.|Corp\.|LLC|Ltd\.|Foundation|Institute|University|College))\b',
                r'\b([A-Z]{2,})\b',  # Acronyms
            ],
            'location': [
                r'\b(New York|Los Angeles|Chicago|San Francisco|London|Paris|Tokyo|Berlin)\b',
                r'\b([A-Z][a-z]+ City)\b',
            ],
            'money': [
                r'\$[\d,]+(?:\.\d{2})?',
                r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|USD|euros|EUR)\b',
            ],
            'url': [
                r'https?://[^\s<>"{}|\\^`\[\]]+',
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
        }

        # Claim indicators
        self.claim_patterns = [
            (r'\b(I believe|I think|In my opinion|I feel)\b', 'opinion'),
            (r'\b(research shows|studies indicate|data suggests|evidence shows)\b', 'factual'),
            (r'\b(always|never|all|none|every|no one)\b', 'absolute'),
            (r'\b(should|must|need to|have to|ought to)\b', 'prescriptive'),
            (r'\b(will|going to|predict|expect)\b', 'predictive'),
        ]

        # Sentiment indicators
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'happy', 'joy', 'beautiful', 'brilliant', 'success',
            'best', 'perfect', 'awesome', 'incredible', 'outstanding'
        }
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'sad', 'angry',
            'worst', 'failure', 'disaster', 'ugly', 'stupid', 'wrong',
            'problem', 'issue', 'difficult', 'hard', 'struggle'
        }

    def _load_nlp(self):
        """Lazy load NLP pipeline"""
        if self.nlp is not None or not self.use_spacy:
            return

        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self._backend = "spacy"
                print("[Stage5] Loaded spaCy NER pipeline")
            except OSError:
                # Model not downloaded
                print("[Stage5] spaCy model not found, using regex fallback")
                self._backend = "regex"
        except ImportError:
            print("[Stage5] spaCy not available, using regex fallback")
            self._backend = "regex"

    def extract(self, source: Source) -> Source:
        """
        Extract entities, claims, and sentiment from source.

        Args:
            source: Source with segments

        Returns:
            Source with extraction results
        """
        source.status = ProcessingStatus.EXTRACTING
        self._load_nlp()

        try:
            for segment in source.segments:
                # Extract named entities
                segment.entities = self._extract_entities(segment.content_raw)

                # Extract claims
                claims = self._extract_claims(segment)
                # Store claims in segment metadata
                if claims:
                    segment.topics.extend([c.type.value for c in claims])

                # Analyze sentiment
                segment.sentiment = self._analyze_sentiment(segment.content_raw)

                # Extract keywords
                keywords = self._extract_keywords(segment.content_raw)
                segment.topics = list(set(segment.topics + keywords))

            # Cross-segment analysis
            self._analyze_entity_frequency(source)
            self._identify_key_entities(source)

            return source

        except Exception as e:
            source.error_message = str(e)
            source.error_stage = "extract"
            raise ExtractError(f"Extraction failed: {e}")

    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text"""
        entities = []

        if self._backend == "spacy" and self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                entity = Entity(
                    type=ent.label_.lower(),
                    value=ent.text,
                    confidence=0.85,  # spaCy doesn't provide confidence
                    start_char=ent.start_char,
                    end_char=ent.end_char
                )
                entities.append(entity)
        else:
            # Regex fallback
            entities = self._extract_entities_regex(text)

        return entities

    def _extract_entities_regex(self, text: str) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        seen = set()

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    value = match.group(0).strip()
                    if value and value not in seen and len(value) > 1:
                        entity = Entity(
                            type=entity_type,
                            value=value,
                            confidence=0.6,  # Lower confidence for regex
                            start_char=match.start(),
                            end_char=match.end()
                        )
                        entities.append(entity)
                        seen.add(value)

        return entities

    def _extract_claims(self, segment: Segment) -> List[Claim]:
        """Extract claims from segment"""
        claims = []
        text = segment.content_raw

        for pattern, claim_type in self.claim_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                claim = Claim(
                    statement=text[:200],  # Truncate for storage
                    type=SegmentType.ASSERTION if claim_type == 'factual' else SegmentType.OPINION,
                    verifiable=(claim_type == 'factual'),
                    confidence=0.7
                )
                claims.append(claim)

        return claims

    def _analyze_sentiment(self, text: str) -> Sentiment:
        """Analyze sentiment of text"""
        words = set(text.lower().split())

        positive_count = len(words & self.positive_words)
        negative_count = len(words & self.negative_words)
        total = positive_count + negative_count

        if total == 0:
            polarity = 0.0
            label = "neutral"
        else:
            polarity = (positive_count - negative_count) / total
            if polarity > 0.2:
                label = "positive"
            elif polarity < -0.2:
                label = "negative"
            else:
                label = "neutral"

        # Subjectivity based on opinion indicators
        subjectivity = 0.5
        opinion_patterns = [
            r'\b(I think|I believe|I feel|in my opinion|seems to me)\b',
            r'\b(probably|maybe|perhaps|might|could be)\b',
        ]
        for pattern in opinion_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                subjectivity += 0.2

        return Sentiment(
            overall=label,
            valence=polarity,
            arousal=min(subjectivity, 1.0)
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction based on frequency and position
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())

        # Filter stop words
        stop_words = {
            'that', 'this', 'with', 'from', 'they', 'have', 'been', 'were',
            'said', 'each', 'which', 'their', 'will', 'would', 'could',
            'about', 'there', 'when', 'what', 'just', 'also', 'more',
            'some', 'into', 'than', 'then', 'only', 'come', 'made',
            'find', 'here', 'thing', 'know', 'want', 'give', 'take',
            'very', 'after', 'most', 'make', 'like', 'being', 'other'
        }

        filtered = [w for w in words if w not in stop_words]

        # Count frequency
        freq = defaultdict(int)
        for word in filtered:
            freq[word] += 1

        # Return top keywords
        sorted_words = sorted(freq.items(), key=lambda x: -x[1])
        return [word for word, count in sorted_words[:10] if count >= 2]

    def _analyze_entity_frequency(self, source: Source):
        """Analyze entity frequency across all segments"""
        entity_counts = defaultdict(int)
        entity_segments = defaultdict(list)

        for segment in source.segments:
            for entity in segment.entities:
                key = (entity.type, entity.value.lower())
                entity_counts[key] += 1
                entity_segments[key].append(segment.segment_id)

        # Update entity importance based on frequency
        for segment in source.segments:
            for entity in segment.entities:
                key = (entity.type, entity.value.lower())
                count = entity_counts[key]
                # Boost confidence for frequently mentioned entities
                if count >= 3:
                    entity.confidence = min(entity.confidence + 0.1, 1.0)

    def _identify_key_entities(self, source: Source):
        """Identify key entities for the source"""
        # Collect all entities
        all_entities = []
        for segment in source.segments:
            all_entities.extend(segment.entities)

        # Count by type and value
        type_counts = defaultdict(lambda: defaultdict(int))
        for entity in all_entities:
            type_counts[entity.type][entity.value.lower()] += 1

        # Mark segments with key entities for higher training weight
        key_entities = set()
        for entity_type, values in type_counts.items():
            # Top 3 of each type are "key"
            sorted_values = sorted(values.items(), key=lambda x: -x[1])[:3]
            for value, count in sorted_values:
                if count >= 2:
                    key_entities.add((entity_type, value))

        for segment in source.segments:
            has_key_entity = any(
                (e.type, e.value.lower()) in key_entities
                for e in segment.entities
            )
            if has_key_entity:
                if 'key_entity' not in segment.training_categories:
                    segment.training_categories.append('key_entity')
                segment.training_weight = min(segment.training_weight + 0.15, 2.0)

    def extract_from_text(self, text: str) -> Dict:
        """
        Extract information from raw text.

        Utility method for standalone extraction.
        """
        self._load_nlp()

        entities = self._extract_entities(text)
        sentiment = self._analyze_sentiment(text)
        keywords = self._extract_keywords(text)

        return {
            'entities': [
                {'type': e.type, 'value': e.value, 'confidence': e.confidence}
                for e in entities
            ],
            'sentiment': {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'label': sentiment.label
            },
            'keywords': keywords
        }


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        # Demo mode
        demo_text = """
        John Smith, CEO of Acme Corp, announced on January 15, 2024 that the company
        would invest $5 million in AI research. "I believe this is the future," he said.
        The New York-based company has been struggling with recent challenges, but
        experts think this move could turn things around. Dr. Jane Doe from MIT
        called it "a brilliant strategic decision."
        """
        print("Demo extraction:")
        print("-" * 40)

        extractor = Stage5Extract()
        result = extractor.extract_from_text(demo_text)

        print("\nEntities:")
        for e in result['entities']:
            print(f"  [{e['type']}] {e['value']} ({e['confidence']:.0%})")

        print(f"\nSentiment: {result['sentiment']['label']} "
              f"(polarity: {result['sentiment']['polarity']:.2f})")

        print(f"\nKeywords: {', '.join(result['keywords'])}")
    else:
        from .orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()
        source = orchestrator.get_result(sys.argv[1])

        if not source:
            print(f"Source not found: {sys.argv[1]}")
            sys.exit(1)

        extractor = Stage5Extract()
        source = extractor.extract(source)

        print(f"Extraction complete!")
        print(f"Total segments: {len(source.segments)}")

        # Show entity summary
        entity_types = defaultdict(int)
        for seg in source.segments:
            for ent in seg.entities:
                entity_types[ent.type] += 1

        print("\nEntity types found:")
        for ent_type, count in sorted(entity_types.items(), key=lambda x: -x[1]):
            print(f"  {ent_type}: {count}")
