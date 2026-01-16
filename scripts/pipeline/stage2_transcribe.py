"""
DOC-8 Agent Analysis Pipeline - Stage 2: Transcription

Handles:
- Run Whisper ASR
- Detect language
- Generate raw transcript
- Calculate confidence scores
- Estimate speaker count
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import tempfile

from .models import Source, Segment, SourceType, ProcessingStatus


class TranscribeError(Exception):
    """Error during transcription"""
    pass


class Stage2Transcribe:
    """
    Stage 2: Transcription

    Uses OpenAI Whisper for automatic speech recognition.
    Supports multiple Whisper backends (openai-whisper, faster-whisper, whisper.cpp).
    """

    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Initialize transcription stage.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (auto, cpu, cuda, mps)
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self._backend = None

    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is not None:
            return

        # Try faster-whisper first (faster, lower memory)
        try:
            from faster_whisper import WhisperModel
            compute_type = "float16" if self.device != "cpu" else "int8"
            device = "cuda" if self.device == "auto" else self.device
            if device == "mps":
                device = "cpu"  # faster-whisper doesn't support MPS
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type
            )
            self._backend = "faster-whisper"
            print(f"[Stage2] Loaded faster-whisper model: {self.model_size}")
            return
        except ImportError:
            pass

        # Try openai-whisper
        try:
            import whisper
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device = "mps"
            self.model = whisper.load_model(self.model_size, device=device)
            self._backend = "openai-whisper"
            print(f"[Stage2] Loaded openai-whisper model: {self.model_size}")
            return
        except ImportError:
            pass

        raise TranscribeError(
            "No Whisper backend available. Install one of:\n"
            "  pip install faster-whisper\n"
            "  pip install openai-whisper"
        )

    def transcribe(self, source: Source) -> Source:
        """
        Transcribe audio/video source.

        Args:
            source: Source object with file_path

        Returns:
            Source with raw_transcript and segments populated
        """
        if source.source_type not in (SourceType.VIDEO, SourceType.AUDIO):
            raise TranscribeError(f"Cannot transcribe source type: {source.source_type.value}")

        if not source.file_path:
            raise TranscribeError("Source has no file path")

        file_path = Path(source.file_path)
        if not file_path.exists():
            raise TranscribeError(f"File not found: {source.file_path}")

        source.status = ProcessingStatus.TRANSCRIBING
        self._load_model()

        try:
            # Extract audio if needed (for video files)
            audio_path = self._prepare_audio(file_path)

            # Run transcription
            if self._backend == "faster-whisper":
                result = self._transcribe_faster_whisper(audio_path)
            else:
                result = self._transcribe_openai_whisper(audio_path)

            # Cleanup temp audio
            if audio_path != file_path and audio_path.exists():
                audio_path.unlink()

            # Update source
            source.raw_transcript = result['text']
            source.language = result['language']
            source.transcription_confidence = result['confidence']
            source.speaker_count = self._estimate_speaker_count(result['segments'])

            # Create segments
            source.segments = self._create_segments(result['segments'], source.source_id)

            source.status = ProcessingStatus.COMPLETE
            return source

        except Exception as e:
            source.status = ProcessingStatus.FAILED
            source.error_message = str(e)
            source.error_stage = "transcribe"
            raise TranscribeError(f"Transcription failed: {e}")

    def _prepare_audio(self, file_path: Path) -> Path:
        """Extract audio from video if needed"""
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
        if file_path.suffix.lower() not in video_extensions:
            return file_path

        # Extract audio using ffmpeg
        try:
            import subprocess
            audio_path = Path(tempfile.mktemp(suffix='.wav'))
            subprocess.run(
                ['ffmpeg', '-y', '-i', str(file_path),
                 '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                 str(audio_path)],
                capture_output=True, timeout=300, check=True
            )
            return audio_path
        except FileNotFoundError:
            # ffmpeg not available, try moviepy
            try:
                from moviepy.editor import VideoFileClip
                clip = VideoFileClip(str(file_path))
                audio_path = Path(tempfile.mktemp(suffix='.wav'))
                clip.audio.write_audiofile(str(audio_path), fps=16000, logger=None)
                clip.close()
                return audio_path
            except ImportError:
                raise TranscribeError("ffmpeg or moviepy required for video transcription")
        except subprocess.CalledProcessError as e:
            raise TranscribeError(f"Failed to extract audio: {e}")

    def _transcribe_faster_whisper(self, audio_path: Path) -> Dict[str, Any]:
        """Transcribe using faster-whisper"""
        segments_list, info = self.model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segments = []
        full_text = []
        total_confidence = 0
        count = 0

        for segment in segments_list:
            segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'confidence': segment.avg_logprob,
                'words': [
                    {'word': w.word, 'start': w.start, 'end': w.end, 'probability': w.probability}
                    for w in (segment.words or [])
                ]
            })
            full_text.append(segment.text.strip())
            # Convert log prob to probability
            import math
            total_confidence += math.exp(segment.avg_logprob)
            count += 1

        return {
            'text': ' '.join(full_text),
            'language': info.language,
            'confidence': total_confidence / max(count, 1),
            'segments': segments
        }

    def _transcribe_openai_whisper(self, audio_path: Path) -> Dict[str, Any]:
        """Transcribe using openai-whisper"""
        # Note: word_timestamps=True causes MPS float64 error on Apple Silicon
        # Disable it for compatibility
        result = self.model.transcribe(
            str(audio_path),
            verbose=False,
            word_timestamps=False  # Disabled for MPS compatibility
        )

        segments = []
        total_confidence = 0
        count = 0

        for segment in result['segments']:
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': segment.get('avg_logprob', -0.5),
                'words': segment.get('words', [])
            })
            # Convert log prob to probability
            import math
            avg_logprob = segment.get('avg_logprob', -0.5)
            total_confidence += math.exp(avg_logprob)
            count += 1

        return {
            'text': result['text'],
            'language': result.get('language', 'en'),
            'confidence': total_confidence / max(count, 1),
            'segments': segments
        }

    def _estimate_speaker_count(self, segments: List[Dict]) -> int:
        """
        Estimate number of speakers based on transcript patterns.

        This is a simple heuristic - for better results, use Stage 3 Diarization.
        """
        # Look for speaker indicators in text
        speaker_patterns = [
            'interviewer:', 'host:', 'speaker 1:', 'speaker 2:',
            'q:', 'a:', 'question:', 'answer:'
        ]

        text_lower = ' '.join(s.get('text', '').lower() for s in segments)
        speaker_count = 1

        for pattern in speaker_patterns:
            if pattern in text_lower:
                speaker_count = max(speaker_count, 2)
                break

        # If Q&A pattern detected, likely 2 speakers
        if text_lower.count('?') > 5:
            speaker_count = max(speaker_count, 2)

        return speaker_count

    def _create_segments(self, whisper_segments: List[Dict], source_id: str) -> List[Segment]:
        """Convert Whisper segments to DOC-8 Segment objects"""
        segments = []

        for i, ws in enumerate(whisper_segments):
            segment = Segment(
                source_id=source_id,
                time_start=ws['start'],
                time_end=ws['end'],
                duration=ws['end'] - ws['start'],
                content_raw=ws['text'],
                content_normalized=ws['text'].lower().strip(),
                language="en",  # Will be refined in later stages
                language_confidence=0.9
            )

            # Set confidence based on log probability
            import math
            conf = ws.get('confidence', -0.5)
            if conf < 0:  # It's a log probability
                conf = math.exp(conf)
            segment.verification.source_reliability = min(conf, 1.0)

            segments.append(segment)

        return segments

    def transcribe_text(self, text: str, source_id: str) -> List[Segment]:
        """
        Create segments from pre-existing text (for documents, web pages).

        Args:
            text: Raw text content
            source_id: Parent source ID

        Returns:
            List of Segment objects
        """
        # Simple sentence-based segmentation
        import re

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)

        segments = []
        char_pos = 0

        for sentence in sentences:
            if not sentence.strip():
                continue

            segment = Segment(
                source_id=source_id,
                content_raw=sentence.strip(),
                content_normalized=sentence.lower().strip()
            )

            # Update character position
            char_pos += len(sentence) + 1

            segments.append(segment)

        return segments


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python stage2_transcribe.py <audio_or_video_file>")
        sys.exit(1)

    from .stage1_ingest import Stage1Ingest

    # Ingest first
    ingest = Stage1Ingest()
    source = ingest.ingest(sys.argv[1])
    print(f"Ingested: {source.source_id}")

    # Transcribe
    transcribe = Stage2Transcribe(model_size="base")
    try:
        source = transcribe.transcribe(source)
        print(f"\nTranscription complete!")
        print(f"Language: {source.language}")
        print(f"Confidence: {source.transcription_confidence:.2%}")
        print(f"Speakers (estimated): {source.speaker_count}")
        print(f"Segments: {len(source.segments)}")
        print(f"\nFirst 500 chars of transcript:")
        print(source.raw_transcript[:500] + "..." if len(source.raw_transcript) > 500 else source.raw_transcript)
    except TranscribeError as e:
        print(f"Error: {e}")
        sys.exit(1)
