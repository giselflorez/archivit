"""
DOC-8 Agent Analysis Pipeline - Data Models

Universal segment and source models for knowledge extraction.
Based on DOC8_DATA_ARCHITECTURE.md specification.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SourceType(Enum):
    """Type of source being processed"""
    VIDEO = "video"
    AUDIO = "audio"
    WEB = "web"
    DOCUMENT = "document"
    IMAGE = "image"


class SegmentType(Enum):
    """Type of content segment"""
    ASSERTION = "assertion"
    QUESTION = "question"
    OPINION = "opinion"
    FACT = "fact"
    QUOTE = "quote"
    NARRATIVE = "narrative"


class VerificationStatus(Enum):
    """Verification status of segment"""
    PENDING = "pending"
    PRE_AI_VERIFIED = "pre_ai_verified"
    USER_VERIFIED = "user_verified"
    DISPUTED = "disputed"


class ProcessingStatus(Enum):
    """Processing pipeline status"""
    QUEUED = "queued"
    INGESTING = "ingesting"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    SEGMENTING = "segmenting"
    EXTRACTING = "extracting"
    INDEXING = "indexing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Entity:
    """Named entity extracted from content"""
    type: str  # PERSON, PLACE, DATE, ORGANIZATION, CONCEPT
    value: str
    confidence: float = 0.0
    start_char: Optional[int] = None
    end_char: Optional[int] = None


@dataclass
class Claim:
    """Claim or assertion extracted from content"""
    statement: str
    type: SegmentType = SegmentType.ASSERTION
    verifiable: bool = False
    cross_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Sentiment:
    """Sentiment analysis result"""
    overall: str = "neutral"
    valence: float = 0.0  # -1 to 1
    arousal: float = 0.0  # 0 to 1
    confidence: float = 0.0


@dataclass
class ProvenanceStep:
    """Step in provenance chain"""
    step: str
    date: str
    medium: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None


@dataclass
class Verification:
    """Verification status and provenance"""
    status: VerificationStatus = VerificationStatus.PENDING
    verified_by: Optional[str] = None
    verified_date: Optional[str] = None
    source_reliability: float = 0.5
    provenance_chain: List[ProvenanceStep] = field(default_factory=list)


@dataclass
class Connection:
    """Relationship between segments"""
    type: str  # responds_to, contradicts, supports, quotes
    target_segment_id: str
    confidence: float = 0.0


@dataclass
class Annotation:
    """User annotation on segment"""
    user_id: str
    note: str
    tags: List[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SourceMeta:
    """Source-specific metadata"""
    # Video/Audio
    visual_description: Optional[str] = None
    scene_type: Optional[str] = None
    camera_angle: Optional[str] = None
    audio_quality: Optional[float] = None
    background_noise: Optional[str] = None

    # Web
    page_section: Optional[str] = None
    surrounding_context: Optional[str] = None

    # Document
    page_number: Optional[int] = None
    chapter: Optional[str] = None
    footnote_refs: List[int] = field(default_factory=list)


@dataclass
class Segment:
    """Universal segment - applies to ALL source types"""
    # Identity
    segment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    timestamp_created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Temporal
    time_start: Optional[float] = None
    time_end: Optional[float] = None
    duration: Optional[float] = None

    # Content
    content_raw: str = ""
    content_normalized: str = ""
    content_summary: str = ""
    language: str = "en"
    language_confidence: float = 1.0

    # Speaker/Author
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    speaker_confidence: float = 0.0
    speaker_role: str = "primary"  # primary, interviewer, narrator

    # Semantic extraction
    entities: List[Entity] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    sentiment: Sentiment = field(default_factory=Sentiment)
    segment_type: SegmentType = SegmentType.NARRATIVE

    # Verification
    verification: Verification = field(default_factory=Verification)

    # Relationships
    connections: List[Connection] = field(default_factory=list)

    # Source-specific metadata
    source_meta: SourceMeta = field(default_factory=SourceMeta)

    # User annotations
    annotations: List[Annotation] = field(default_factory=list)

    # Training flags
    include_in_bank: bool = True
    training_weight: float = 1.0
    training_categories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'segment_id': self.segment_id,
            'source_id': self.source_id,
            'timestamp_created': self.timestamp_created,
            'time_start': self.time_start,
            'time_end': self.time_end,
            'duration': self.duration,
            'content_raw': self.content_raw,
            'content_normalized': self.content_normalized,
            'content_summary': self.content_summary,
            'language': self.language,
            'language_confidence': self.language_confidence,
            'speaker_id': self.speaker_id,
            'speaker_name': self.speaker_name,
            'speaker_confidence': self.speaker_confidence,
            'speaker_role': self.speaker_role,
            'entities': [{'type': e.type, 'value': e.value, 'confidence': e.confidence}
                        for e in self.entities],
            'topics': self.topics,
            'claims': [{'statement': c.statement, 'type': c.type.value,
                       'verifiable': c.verifiable, 'confidence': c.confidence}
                      for c in self.claims],
            'sentiment': {
                'overall': self.sentiment.overall,
                'valence': self.sentiment.valence,
                'arousal': self.sentiment.arousal,
                'confidence': self.sentiment.confidence
            },
            'segment_type': self.segment_type.value,
            'verification': {
                'status': self.verification.status.value,
                'verified_by': self.verification.verified_by,
                'source_reliability': self.verification.source_reliability
            },
            'connections': [{'type': c.type, 'target': c.target_segment_id}
                          for c in self.connections],
            'include_in_bank': self.include_in_bank,
            'training_weight': self.training_weight,
            'training_categories': self.training_categories
        }


@dataclass
class Source:
    """Source document being processed"""
    source_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: SourceType = SourceType.DOCUMENT
    status: ProcessingStatus = ProcessingStatus.QUEUED

    # Location
    file_path: Optional[str] = None
    url: Optional[str] = None

    # Metadata
    title: str = ""
    author: Optional[str] = None
    created_date: Optional[str] = None
    imported_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Media info
    duration: Optional[float] = None  # seconds for audio/video
    file_size: Optional[int] = None  # bytes
    mime_type: Optional[str] = None
    thumbnail_path: Optional[str] = None

    # Processing
    segments: List[Segment] = field(default_factory=list)
    raw_transcript: Optional[str] = None
    speaker_count: int = 0
    language: str = "en"

    # Quality metrics
    transcription_confidence: float = 0.0
    extraction_confidence: float = 0.0

    # Error handling
    error_message: Optional[str] = None
    error_stage: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'source_id': self.source_id,
            'source_type': self.source_type.value,
            'status': self.status.value,
            'file_path': self.file_path,
            'url': self.url,
            'title': self.title,
            'author': self.author,
            'created_date': self.created_date,
            'imported_date': self.imported_date,
            'duration': self.duration,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'thumbnail_path': self.thumbnail_path,
            'segment_count': len(self.segments),
            'segments': [s.to_dict() for s in self.segments],
            'speaker_count': self.speaker_count,
            'language': self.language,
            'transcription_confidence': self.transcription_confidence,
            'extraction_confidence': self.extraction_confidence,
            'error_message': self.error_message,
            'error_stage': self.error_stage
        }
