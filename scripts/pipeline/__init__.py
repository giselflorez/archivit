"""
DOC-8 Agent Analysis Pipeline

8-stage knowledge extraction pipeline:
1. INGEST - Accept file/URL, validate, create source record
2. TRANSCRIBE - Whisper ASR for audio/video
3. DIARIZE - Speaker identification
4. SEGMENT - Topic-based segmentation
5. EXTRACT - NER, claims, sentiment
6. CROSS-REFERENCE - Match to existing knowledge
7. INDEX - Embeddings, search index
8. PRESENT - API endpoints for UI
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
from .stage3_diarize import Stage3Diarize, DiarizeError
from .stage4_segment import Stage4Segment, SegmentError
from .stage5_extract import Stage5Extract, ExtractError
from .stage6_crossref import Stage6CrossRef, CrossRefError
from .stage7_index import Stage7Index, IndexError
from .stage8_present import Stage8Present, PresentError
from .orchestrator import PipelineOrchestrator

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
    'Stage3Diarize',
    'Stage4Segment',
    'Stage5Extract',
    'Stage6CrossRef',
    'Stage7Index',
    'Stage8Present',
    # Orchestrator
    'PipelineOrchestrator',
    # Errors
    'IngestError',
    'TranscribeError',
    'DiarizeError',
    'SegmentError',
    'ExtractError',
    'CrossRefError',
    'IndexError',
    'PresentError',
]

__version__ = '2.0.0'
