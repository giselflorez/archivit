"""
DOC-8 Agent Analysis Pipeline - Orchestrator

Coordinates the full pipeline from ingestion to presentation.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable

from .models import Source, SourceType, ProcessingStatus
from .stage1_ingest import Stage1Ingest, IngestError
from .stage2_transcribe import Stage2Transcribe, TranscribeError


class PipelineOrchestrator:
    """
    Orchestrates the DOC-8 Agent Analysis Pipeline.

    Manages the flow of sources through all processing stages.
    """

    def __init__(self, storage_dir: str = None, whisper_model: str = "base"):
        """
        Initialize pipeline orchestrator.

        Args:
            storage_dir: Base directory for pipeline storage
            whisper_model: Whisper model size for transcription
        """
        self.storage_dir = Path(storage_dir or '~/.arc8/pipeline').expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize stages
        self.stage1 = Stage1Ingest(storage_dir=str(self.storage_dir / 'sources'))
        self.stage2 = Stage2Transcribe(model_size=whisper_model)

        # Progress callback
        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates: callback(stage, progress, message)"""
        self._progress_callback = callback

    def _report_progress(self, stage: str, progress: float, message: str):
        """Report progress to callback if set"""
        if self._progress_callback:
            self._progress_callback(stage, progress, message)
        print(f"[{stage}] {progress:.0%} - {message}")

    def process(self, input_path: str, title: str = None, author: str = None) -> Source:
        """
        Process a file or URL through the full pipeline.

        Args:
            input_path: File path or URL to process
            title: Optional title override
            author: Optional author override

        Returns:
            Fully processed Source object
        """
        # Stage 1: Ingest
        self._report_progress("INGEST", 0.0, f"Starting ingestion: {input_path}")
        try:
            source = self.stage1.ingest(input_path, title, author)
            self._report_progress("INGEST", 1.0, f"Ingested: {source.source_id}")
        except IngestError as e:
            self._report_progress("INGEST", 1.0, f"Failed: {e}")
            raise

        # Stage 2: Transcribe (if audio/video)
        if source.source_type in (SourceType.VIDEO, SourceType.AUDIO):
            self._report_progress("TRANSCRIBE", 0.0, "Starting transcription...")
            try:
                source = self.stage2.transcribe(source)
                self._report_progress("TRANSCRIBE", 1.0,
                    f"Transcribed: {len(source.segments)} segments, "
                    f"confidence: {source.transcription_confidence:.0%}")
            except TranscribeError as e:
                self._report_progress("TRANSCRIBE", 1.0, f"Failed: {e}")
                raise

        # Future stages would go here:
        # Stage 3: Diarize
        # Stage 4: Segment
        # Stage 5: Extract
        # Stage 6: Cross-reference
        # Stage 7: Index
        # Stage 8: Present

        # Save final result
        self._save_result(source)

        return source

    def process_queue(self) -> List[Source]:
        """Process all queued sources"""
        queue = self.stage1.get_queue()
        results = []

        for item in queue:
            source_id = item['source_id']
            source = self.stage1.get_source(source_id)
            if source:
                try:
                    # Continue processing from where it left off
                    if source.status == ProcessingStatus.QUEUED:
                        if source.source_type in (SourceType.VIDEO, SourceType.AUDIO):
                            source = self.stage2.transcribe(source)
                    results.append(source)

                    # Remove from queue
                    queue_file = self.storage_dir / 'sources' / 'queue' / f"{source_id}.json"
                    if queue_file.exists():
                        queue_file.unlink()

                except Exception as e:
                    print(f"Error processing {source_id}: {e}")
                    source.status = ProcessingStatus.FAILED
                    source.error_message = str(e)
                    results.append(source)

        return results

    def _save_result(self, source: Source):
        """Save processed source result"""
        results_dir = self.storage_dir / 'results'
        results_dir.mkdir(exist_ok=True)

        result_path = results_dir / f"{source.source_id}.json"
        with open(result_path, 'w') as f:
            json.dump(source.to_dict(), f, indent=2)

    def get_result(self, source_id: str) -> Optional[Source]:
        """Load processed result by source ID"""
        result_path = self.storage_dir / 'results' / f"{source_id}.json"
        if not result_path.exists():
            return None

        with open(result_path) as f:
            data = json.load(f)

        # Reconstruct Source object
        source = Source(
            source_id=data['source_id'],
            source_type=SourceType(data['source_type']),
            status=ProcessingStatus(data['status']),
            file_path=data.get('file_path'),
            url=data.get('url'),
            title=data.get('title', ''),
            author=data.get('author'),
            duration=data.get('duration'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            thumbnail_path=data.get('thumbnail_path'),
            speaker_count=data.get('speaker_count', 0),
            language=data.get('language', 'en'),
            transcription_confidence=data.get('transcription_confidence', 0),
            error_message=data.get('error_message'),
            error_stage=data.get('error_stage')
        )

        # Reconstruct segments
        from .models import Segment, Verification, VerificationStatus
        for seg_data in data.get('segments', []):
            segment = Segment(
                segment_id=seg_data['segment_id'],
                source_id=seg_data['source_id'],
                time_start=seg_data.get('time_start'),
                time_end=seg_data.get('time_end'),
                duration=seg_data.get('duration'),
                content_raw=seg_data.get('content_raw', ''),
                content_normalized=seg_data.get('content_normalized', ''),
                speaker_name=seg_data.get('speaker_name'),
                speaker_confidence=seg_data.get('speaker_confidence', 0)
            )
            source.segments.append(segment)

        return source

    def list_results(self) -> List[dict]:
        """List all processed results"""
        results_dir = self.storage_dir / 'results'
        if not results_dir.exists():
            return []

        results = []
        for result_file in results_dir.glob('*.json'):
            with open(result_file) as f:
                data = json.load(f)
                results.append({
                    'source_id': data['source_id'],
                    'title': data.get('title', ''),
                    'source_type': data['source_type'],
                    'status': data['status'],
                    'segment_count': data.get('segment_count', 0),
                    'duration': data.get('duration'),
                    'imported_date': data.get('imported_date')
                })

        return sorted(results, key=lambda x: x.get('imported_date', ''), reverse=True)


# CLI interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description='DOC-8 Agent Analysis Pipeline')
    parser.add_argument('command', choices=['process', 'queue', 'list', 'get'],
                       help='Command to run')
    parser.add_argument('input', nargs='?', help='File path, URL, or source ID')
    parser.add_argument('--title', help='Title for the source')
    parser.add_argument('--author', help='Author for the source')
    parser.add_argument('--model', default='base',
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model size')

    args = parser.parse_args()

    orchestrator = PipelineOrchestrator(whisper_model=args.model)

    if args.command == 'process':
        if not args.input:
            parser.error('process requires input file or URL')
        source = orchestrator.process(args.input, args.title, args.author)
        print(f"\nProcessing complete!")
        print(f"Source ID: {source.source_id}")
        print(f"Status: {source.status.value}")
        print(f"Segments: {len(source.segments)}")

    elif args.command == 'queue':
        results = orchestrator.process_queue()
        print(f"Processed {len(results)} sources from queue")

    elif args.command == 'list':
        results = orchestrator.list_results()
        if not results:
            print("No processed sources found")
        else:
            print(f"{'ID':<20} {'Title':<30} {'Type':<10} {'Segments':<10}")
            print("-" * 70)
            for r in results:
                print(f"{r['source_id']:<20} {r['title'][:28]:<30} "
                      f"{r['source_type']:<10} {r['segment_count']:<10}")

    elif args.command == 'get':
        if not args.input:
            parser.error('get requires source ID')
        source = orchestrator.get_result(args.input)
        if source:
            print(json.dumps(source.to_dict(), indent=2))
        else:
            print(f"Source not found: {args.input}")


if __name__ == '__main__':
    main()
