"""
DOC-8 Agent Analysis Pipeline - Stage 3: Diarization

Handles:
- Identify speaker segments
- Match against known voices (Masters bank)
- Label unknown speakers
- Create speaker timeline
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from collections import defaultdict

from .models import Source, Segment, SourceType, ProcessingStatus


class DiarizeError(Exception):
    """Error during diarization"""
    pass


class Stage3Diarize:
    """
    Stage 3: Speaker Diarization

    Identifies who is speaking when in audio/video content.
    Uses pyannote.audio when available, falls back to heuristics.
    """

    def __init__(self, use_gpu: bool = True):
        """
        Initialize diarization stage.

        Args:
            use_gpu: Whether to use GPU acceleration
        """
        self.use_gpu = use_gpu
        self.pipeline = None
        self._backend = None

        # Known speaker patterns (for heuristic matching)
        self.speaker_patterns = {
            'interviewer': ['interviewer', 'host', 'q:', 'question:'],
            'interviewee': ['guest', 'a:', 'answer:'],
        }

    def _load_pipeline(self):
        """Lazy load diarization pipeline"""
        if self.pipeline is not None:
            return

        # Try pyannote.audio
        try:
            from pyannote.audio import Pipeline
            import torch

            # Check for HuggingFace token
            hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')

            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )

            if self.use_gpu and torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
            elif self.use_gpu and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.pipeline.to(torch.device("mps"))

            self._backend = "pyannote"
            print("[Stage3] Loaded pyannote.audio diarization pipeline")
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"[Stage3] pyannote.audio not available: {e}")

        # Fallback to heuristic mode
        self._backend = "heuristic"
        print("[Stage3] Using heuristic speaker detection (pyannote not available)")

    def diarize(self, source: Source) -> Source:
        """
        Perform speaker diarization on source.

        Args:
            source: Source with transcribed segments

        Returns:
            Source with speaker labels assigned to segments
        """
        if source.source_type not in (SourceType.VIDEO, SourceType.AUDIO):
            # Skip diarization for non-audio sources
            return source

        if not source.segments:
            return source

        source.status = ProcessingStatus.DIARIZING
        self._load_pipeline()

        try:
            if self._backend == "pyannote" and source.file_path:
                return self._diarize_pyannote(source)
            else:
                return self._diarize_heuristic(source)
        except Exception as e:
            source.error_message = str(e)
            source.error_stage = "diarize"
            raise DiarizeError(f"Diarization failed: {e}")

    def _diarize_pyannote(self, source: Source) -> Source:
        """Diarize using pyannote.audio"""
        file_path = Path(source.file_path)

        # Run diarization
        diarization = self.pipeline(str(file_path))

        # Build speaker timeline
        speaker_timeline = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_timeline.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })

        # Assign speakers to segments
        speaker_map = {}
        speaker_counter = 0

        for segment in source.segments:
            if segment.time_start is None:
                continue

            # Find overlapping speaker turn
            best_speaker = None
            best_overlap = 0

            for turn in speaker_timeline:
                overlap = self._calculate_overlap(
                    segment.time_start, segment.time_end or segment.time_start + 1,
                    turn['start'], turn['end']
                )
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = turn['speaker']

            if best_speaker:
                # Map to human-readable name
                if best_speaker not in speaker_map:
                    speaker_counter += 1
                    speaker_map[best_speaker] = f"Speaker {speaker_counter}"

                segment.speaker_id = best_speaker
                segment.speaker_name = speaker_map[best_speaker]
                segment.speaker_confidence = min(best_overlap / (segment.duration or 1), 1.0)

        source.speaker_count = len(speaker_map)
        return source

    def _diarize_heuristic(self, source: Source) -> Source:
        """Diarize using text heuristics"""
        # Analyze text patterns to identify speakers
        speakers_detected = set()

        for segment in source.segments:
            text_lower = segment.content_raw.lower()

            # Check for explicit speaker labels
            if ':' in segment.content_raw[:50]:
                # Might have "Speaker: text" format
                parts = segment.content_raw.split(':', 1)
                if len(parts[0]) < 30:  # Reasonable name length
                    speaker_name = parts[0].strip()
                    segment.speaker_name = speaker_name
                    segment.speaker_id = speaker_name.lower().replace(' ', '_')
                    segment.speaker_confidence = 0.8
                    speakers_detected.add(speaker_name)
                    continue

            # Check for interviewer patterns
            for pattern in self.speaker_patterns['interviewer']:
                if text_lower.startswith(pattern):
                    segment.speaker_name = "Interviewer"
                    segment.speaker_id = "interviewer"
                    segment.speaker_role = "interviewer"
                    segment.speaker_confidence = 0.7
                    speakers_detected.add("Interviewer")
                    break

            # Check for question vs statement
            if segment.content_raw.strip().endswith('?'):
                if not segment.speaker_name:
                    segment.speaker_role = "interviewer"
                    segment.speaker_confidence = 0.5

        # Assign alternating speakers if Q&A pattern detected
        if len(speakers_detected) == 0:
            self._assign_alternating_speakers(source)

        source.speaker_count = max(len(speakers_detected), source.speaker_count)
        return source

    def _assign_alternating_speakers(self, source: Source):
        """Assign speakers in alternating pattern for Q&A content"""
        question_count = sum(1 for s in source.segments if s.content_raw.strip().endswith('?'))

        if question_count < 3:
            # Not enough questions to assume Q&A format
            return

        current_speaker = 1
        last_was_question = False

        for segment in source.segments:
            is_question = segment.content_raw.strip().endswith('?')

            if is_question and not last_was_question:
                current_speaker = 1  # Interviewer asks
            elif not is_question and last_was_question:
                current_speaker = 2  # Interviewee answers

            segment.speaker_id = f"speaker_{current_speaker}"
            segment.speaker_name = "Interviewer" if current_speaker == 1 else "Primary Speaker"
            segment.speaker_role = "interviewer" if current_speaker == 1 else "primary"
            segment.speaker_confidence = 0.4

            last_was_question = is_question

    def _calculate_overlap(self, s1_start: float, s1_end: float,
                          s2_start: float, s2_end: float) -> float:
        """Calculate overlap duration between two time ranges"""
        overlap_start = max(s1_start, s2_start)
        overlap_end = min(s1_end, s2_end)
        return max(0, overlap_end - overlap_start)

    def match_known_speakers(self, source: Source, known_speakers: Dict[str, dict]) -> Source:
        """
        Match detected speakers against known speaker profiles.

        Args:
            source: Source with speaker labels
            known_speakers: Dict of speaker_id -> {name, voice_embedding, etc}

        Returns:
            Source with matched speaker names
        """
        # This would use voice embeddings for matching
        # For now, just match by name patterns
        for segment in source.segments:
            if not segment.speaker_name:
                continue

            name_lower = segment.speaker_name.lower()
            for speaker_id, profile in known_speakers.items():
                known_name = profile.get('name', '').lower()
                if known_name and (known_name in name_lower or name_lower in known_name):
                    segment.speaker_id = speaker_id
                    segment.speaker_name = profile.get('name')
                    segment.speaker_confidence = min(segment.speaker_confidence + 0.2, 1.0)
                    break

        return source


# CLI for testing
if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python stage3_diarize.py <source_id>")
        sys.exit(1)

    from .orchestrator import PipelineOrchestrator

    orchestrator = PipelineOrchestrator()
    source = orchestrator.get_result(sys.argv[1])

    if not source:
        print(f"Source not found: {sys.argv[1]}")
        sys.exit(1)

    diarize = Stage3Diarize()
    source = diarize.diarize(source)

    print(f"Diarization complete!")
    print(f"Speakers detected: {source.speaker_count}")

    # Show speaker distribution
    speaker_counts = defaultdict(int)
    for seg in source.segments:
        speaker_counts[seg.speaker_name or 'Unknown'] += 1

    print("\nSpeaker distribution:")
    for speaker, count in sorted(speaker_counts.items(), key=lambda x: -x[1]):
        print(f"  {speaker}: {count} segments")
