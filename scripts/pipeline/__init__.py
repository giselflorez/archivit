"""
DOC-8 Agent Analysis Pipeline

8-stage knowledge extraction pipeline:
1. INGEST - Accept file/URL, validate, create source record
2. TRANSCRIBE - Whisper ASR for audio/video
3. DIARIZE - Speaker identification (future)
4. SEGMENT - Topic-based segmentation (future)
5. EXTRACT - NER, claims, sentiment (future)
6. CROSS-REFERENCE - Match to existing knowledge (future)
7. INDEX - Embeddings, search index (future)
8. PRESENT - Display in UI (future)
"""

from .models import (
    Source,
    Segment,
    Entity,
    Claim,
    Sentiment,
    Verification,
    Connection,
    SourceType,
    SegmentType,
    VerificationStatus,
    ProcessingStatus
)

from .stage1_ingest import Stage1Ingest, IngestError
from .stage2_transcribe import Stage2Transcribe, TranscribeError

__all__ = [
    # Models
    'Source',
    'Segment',
    'Entity',
    'Claim',
    'Sentiment',
    'Verification',
    'Connection',
    'SourceType',
    'SegmentType',
    'VerificationStatus',
    'ProcessingStatus',
    # Stages
    'Stage1Ingest',
    'Stage2Transcribe',
    # Errors
    'IngestError',
    'TranscribeError',
]

__version__ = '1.0.0'
