"""
DOC-8 Agent Analysis Pipeline - Stage 8: Present

Handles:
- REST API endpoints for pipeline data
- Search API
- Source browsing
- Segment retrieval
- Training data export
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .models import Source, Segment, ProcessingStatus, SourceType
from .stage7_index import Stage7Index
from .stage6_crossref import Stage6CrossRef


class PresentError(Exception):
    """Error during presentation"""
    pass


class Stage8Present:
    """
    Stage 8: Presentation Layer

    Provides API endpoints and data formatting for UI consumption.
    """

    def __init__(self, storage_dir: str = None):
        """
        Initialize presentation stage.

        Args:
            storage_dir: Base storage directory for pipeline data
        """
        self.storage_dir = Path(storage_dir or '~/.arc8/pipeline').expanduser()
        self.results_dir = self.storage_dir / 'results'

        # Initialize search index
        self.indexer = Stage7Index()
        self.crossref = Stage6CrossRef()

    # ==================== Source Endpoints ====================

    def list_sources(self, page: int = 1, per_page: int = 20,
                    source_type: str = None, status: str = None) -> Dict:
        """
        List all processed sources with pagination.

        Returns:
            {sources: [...], total: int, page: int, pages: int}
        """
        if not self.results_dir.exists():
            return {'sources': [], 'total': 0, 'page': 1, 'pages': 0}

        # Collect all sources
        all_sources = []
        for result_file in self.results_dir.glob('*.json'):
            try:
                with open(result_file) as f:
                    data = json.load(f)

                # Apply filters
                if source_type and data.get('source_type') != source_type:
                    continue
                if status and data.get('status') != status:
                    continue

                all_sources.append({
                    'source_id': data['source_id'],
                    'title': data.get('title', 'Untitled'),
                    'author': data.get('author'),
                    'source_type': data.get('source_type'),
                    'status': data.get('status'),
                    'duration': data.get('duration'),
                    'segment_count': data.get('segment_count', len(data.get('segments', []))),
                    'speaker_count': data.get('speaker_count', 0),
                    'imported_date': data.get('imported_date'),
                    'thumbnail': data.get('thumbnail_path'),
                })
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by import date
        all_sources.sort(key=lambda x: x.get('imported_date', ''), reverse=True)

        # Paginate
        total = len(all_sources)
        pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page

        return {
            'sources': all_sources[start:end],
            'total': total,
            'page': page,
            'pages': pages,
        }

    def get_source(self, source_id: str) -> Optional[Dict]:
        """
        Get full source details.

        Returns:
            Source data with segments
        """
        result_file = self.results_dir / f'{source_id}.json'
        if not result_file.exists():
            return None

        with open(result_file) as f:
            data = json.load(f)

        # Format for presentation
        return {
            'source_id': data['source_id'],
            'title': data.get('title', 'Untitled'),
            'author': data.get('author'),
            'source_type': data.get('source_type'),
            'status': data.get('status'),
            'duration': data.get('duration'),
            'duration_formatted': self._format_duration(data.get('duration')),
            'file_size': data.get('file_size'),
            'file_size_formatted': self._format_size(data.get('file_size')),
            'mime_type': data.get('mime_type'),
            'url': data.get('url'),
            'language': data.get('language'),
            'speaker_count': data.get('speaker_count', 0),
            'transcription_confidence': data.get('transcription_confidence'),
            'imported_date': data.get('imported_date'),
            'thumbnail': data.get('thumbnail_path'),
            'segment_count': len(data.get('segments', [])),
            'segments': self._format_segments(data.get('segments', [])),
            'metadata': data.get('metadata', {}),
        }

    def get_source_transcript(self, source_id: str) -> Optional[str]:
        """Get full transcript text for a source"""
        result_file = self.results_dir / f'{source_id}.json'
        if not result_file.exists():
            return None

        with open(result_file) as f:
            data = json.load(f)

        # Combine segment texts
        segments = data.get('segments', [])
        transcript_parts = []

        current_speaker = None
        for seg in segments:
            speaker = seg.get('speaker_name')
            text = seg.get('content_raw', '')

            if speaker and speaker != current_speaker:
                transcript_parts.append(f"\n[{speaker}]")
                current_speaker = speaker

            transcript_parts.append(text)

        return '\n'.join(transcript_parts)

    # ==================== Segment Endpoints ====================

    def get_segment(self, segment_id: str) -> Optional[Dict]:
        """Get single segment with full details"""
        # Search through all sources for segment
        for result_file in self.results_dir.glob('*.json'):
            with open(result_file) as f:
                data = json.load(f)

            for seg in data.get('segments', []):
                if seg.get('segment_id') == segment_id:
                    return self._format_segment_detail(seg, data)

        return None

    def get_segments_by_speaker(self, source_id: str, speaker_name: str) -> List[Dict]:
        """Get all segments by a specific speaker"""
        result_file = self.results_dir / f'{source_id}.json'
        if not result_file.exists():
            return []

        with open(result_file) as f:
            data = json.load(f)

        return [
            self._format_segment_detail(seg, data)
            for seg in data.get('segments', [])
            if seg.get('speaker_name') == speaker_name
        ]

    def get_key_passages(self, source_id: str) -> List[Dict]:
        """Get key passages from a source"""
        result_file = self.results_dir / f'{source_id}.json'
        if not result_file.exists():
            return []

        with open(result_file) as f:
            data = json.load(f)

        return [
            self._format_segment_detail(seg, data)
            for seg in data.get('segments', [])
            if 'key_passage' in seg.get('training_categories', [])
        ]

    def get_quotable_segments(self, source_id: str) -> List[Dict]:
        """Get quotable segments from a source"""
        result_file = self.results_dir / f'{source_id}.json'
        if not result_file.exists():
            return []

        with open(result_file) as f:
            data = json.load(f)

        return [
            self._format_segment_detail(seg, data)
            for seg in data.get('segments', [])
            if 'quotable' in seg.get('training_categories', [])
        ]

    # ==================== Search Endpoints ====================

    def search(self, query: str, source_id: str = None,
               limit: int = 20, offset: int = 0) -> Dict:
        """
        Search across all indexed content.

        Returns:
            {results: [...], total: int, query: str}
        """
        results = self.indexer.search(query, limit=limit + offset, filter_source=source_id)

        return {
            'query': query,
            'results': results[offset:offset + limit],
            'total': len(results),
            'limit': limit,
            'offset': offset,
        }

    def find_related(self, segment_id: str, limit: int = 5) -> List[Dict]:
        """Find segments related to a given segment"""
        return self.indexer.get_similar(segment_id, limit=limit)

    def search_by_entity(self, entity_type: str, entity_value: str,
                        limit: int = 20) -> List[Dict]:
        """Search segments by entity"""
        return self.crossref.find_related(f"{entity_type}:{entity_value}", limit=limit)

    # ==================== Training Data Export ====================

    def export_training_data(self, source_id: str = None,
                            min_weight: float = 0.5,
                            categories: List[str] = None) -> List[Dict]:
        """
        Export segments formatted for training.

        Args:
            source_id: Optional source filter
            min_weight: Minimum training weight
            categories: Filter by training categories

        Returns:
            List of training examples
        """
        training_data = []

        # Collect segments
        if source_id:
            files = [self.results_dir / f'{source_id}.json']
        else:
            files = list(self.results_dir.glob('*.json'))

        for result_file in files:
            if not result_file.exists():
                continue

            with open(result_file) as f:
                data = json.load(f)

            source_title = data.get('title', 'Unknown')
            source_author = data.get('author', 'Unknown')

            for seg in data.get('segments', []):
                weight = seg.get('training_weight', 1.0)
                seg_categories = seg.get('training_categories', [])

                # Apply filters
                if weight < min_weight:
                    continue
                if categories and not any(c in seg_categories for c in categories):
                    continue

                training_data.append({
                    'text': seg.get('content_raw', ''),
                    'source': source_title,
                    'author': source_author,
                    'speaker': seg.get('speaker_name'),
                    'segment_type': seg.get('segment_type'),
                    'weight': weight,
                    'categories': seg_categories,
                    'topics': seg.get('topics', []),
                    'entities': [
                        {'type': e.get('type'), 'value': e.get('value')}
                        for e in seg.get('entities', [])
                    ],
                })

        return training_data

    def export_jsonl(self, output_path: str, source_id: str = None) -> int:
        """
        Export training data as JSONL file.

        Returns:
            Number of examples exported
        """
        data = self.export_training_data(source_id=source_id)

        with open(output_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')

        return len(data)

    # ==================== Statistics Endpoints ====================

    def get_stats(self) -> Dict:
        """Get overall pipeline statistics"""
        sources = self.list_sources(per_page=1000)['sources']

        stats = {
            'total_sources': len(sources),
            'total_segments': sum(s.get('segment_count', 0) for s in sources),
            'total_duration': sum(s.get('duration') or 0 for s in sources),
            'by_type': {},
            'by_status': {},
        }

        for s in sources:
            source_type = s.get('source_type', 'unknown')
            status = s.get('status', 'unknown')

            if source_type not in stats['by_type']:
                stats['by_type'][source_type] = 0
            stats['by_type'][source_type] += 1

            if status not in stats['by_status']:
                stats['by_status'][status] = 0
            stats['by_status'][status] += 1

        # Add index stats
        stats['index'] = self.indexer.get_index_stats()
        stats['knowledge_base'] = self.crossref.get_knowledge_stats()

        return stats

    def get_source_stats(self, source_id: str) -> Optional[Dict]:
        """Get statistics for a specific source"""
        source = self.get_source(source_id)
        if not source:
            return None

        segments = source.get('segments', [])

        # Speaker distribution
        speakers = {}
        for seg in segments:
            speaker = seg.get('speaker') or 'Unknown'
            if speaker not in speakers:
                speakers[speaker] = {'count': 0, 'duration': 0}
            speakers[speaker]['count'] += 1
            speakers[speaker]['duration'] += seg.get('duration') or 0

        # Segment types
        types = {}
        for seg in segments:
            seg_type = seg.get('segment_type', 'unknown')
            types[seg_type] = types.get(seg_type, 0) + 1

        # Entity types
        entity_types = {}
        for seg in segments:
            for ent in seg.get('entities', []):
                ent_type = ent.get('type', 'unknown')
                entity_types[ent_type] = entity_types.get(ent_type, 0) + 1

        return {
            'source_id': source_id,
            'segment_count': len(segments),
            'speakers': speakers,
            'segment_types': types,
            'entity_types': entity_types,
            'key_passages': sum(1 for s in segments
                               if 'key_passage' in s.get('training_categories', [])),
            'quotable': sum(1 for s in segments
                           if 'quotable' in s.get('training_categories', [])),
        }

    # ==================== Helper Methods ====================

    def _format_duration(self, seconds: Optional[float]) -> str:
        """Format duration in human readable form"""
        if not seconds:
            return ''
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _format_size(self, bytes_size: Optional[int]) -> str:
        """Format file size in human readable form"""
        if not bytes_size:
            return ''
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    def _format_segments(self, segments: List[Dict]) -> List[Dict]:
        """Format segments for presentation"""
        return [
            {
                'segment_id': s.get('segment_id'),
                'time_start': s.get('time_start'),
                'time_end': s.get('time_end'),
                'time_formatted': self._format_timestamp(s.get('time_start')),
                'duration': s.get('duration'),
                'speaker': s.get('speaker_name'),
                'text': s.get('content_raw', ''),
                'summary': s.get('content_summary'),
                'segment_type': s.get('segment_type'),
                'sentiment': s.get('sentiment', {}).get('label'),
                'is_quotable': 'quotable' in s.get('training_categories', []),
                'is_key_passage': 'key_passage' in s.get('training_categories', []),
                'entity_count': len(s.get('entities', [])),
                'topic_count': len(s.get('topics', [])),
            }
            for s in segments
        ]

    def _format_segment_detail(self, segment: Dict, source_data: Dict) -> Dict:
        """Format single segment with full details"""
        return {
            'segment_id': segment.get('segment_id'),
            'source_id': source_data.get('source_id'),
            'source_title': source_data.get('title'),
            'time_start': segment.get('time_start'),
            'time_end': segment.get('time_end'),
            'time_formatted': self._format_timestamp(segment.get('time_start')),
            'duration': segment.get('duration'),
            'speaker': segment.get('speaker_name'),
            'speaker_role': segment.get('speaker_role'),
            'speaker_confidence': segment.get('speaker_confidence'),
            'text': segment.get('content_raw', ''),
            'summary': segment.get('content_summary'),
            'segment_type': segment.get('segment_type'),
            'sentiment': segment.get('sentiment'),
            'entities': segment.get('entities', []),
            'topics': segment.get('topics', []),
            'connections': segment.get('connections', []),
            'training_weight': segment.get('training_weight', 1.0),
            'training_categories': segment.get('training_categories', []),
            'verification': segment.get('verification', {}),
        }

    def _format_timestamp(self, seconds: Optional[float]) -> str:
        """Format timestamp for display"""
        if seconds is None:
            return ''
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"


# Flask API Blueprint (optional integration)
def create_api_blueprint():
    """Create Flask blueprint for API endpoints"""
    try:
        from flask import Blueprint, jsonify, request
    except ImportError:
        return None

    api = Blueprint('pipeline_api', __name__, url_prefix='/api/pipeline')
    presenter = Stage8Present()

    @api.route('/sources', methods=['GET'])
    def list_sources():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        source_type = request.args.get('type')
        status = request.args.get('status')
        return jsonify(presenter.list_sources(page, per_page, source_type, status))

    @api.route('/sources/<source_id>', methods=['GET'])
    def get_source(source_id):
        source = presenter.get_source(source_id)
        if source:
            return jsonify(source)
        return jsonify({'error': 'Source not found'}), 404

    @api.route('/sources/<source_id>/transcript', methods=['GET'])
    def get_transcript(source_id):
        transcript = presenter.get_source_transcript(source_id)
        if transcript:
            return jsonify({'transcript': transcript})
        return jsonify({'error': 'Source not found'}), 404

    @api.route('/sources/<source_id>/stats', methods=['GET'])
    def get_source_stats(source_id):
        stats = presenter.get_source_stats(source_id)
        if stats:
            return jsonify(stats)
        return jsonify({'error': 'Source not found'}), 404

    @api.route('/segments/<segment_id>', methods=['GET'])
    def get_segment(segment_id):
        segment = presenter.get_segment(segment_id)
        if segment:
            return jsonify(segment)
        return jsonify({'error': 'Segment not found'}), 404

    @api.route('/search', methods=['GET'])
    def search():
        query = request.args.get('q', '')
        source_id = request.args.get('source')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        return jsonify(presenter.search(query, source_id, limit, offset))

    @api.route('/stats', methods=['GET'])
    def get_stats():
        return jsonify(presenter.get_stats())

    @api.route('/export/training', methods=['GET'])
    def export_training():
        source_id = request.args.get('source')
        min_weight = request.args.get('min_weight', 0.5, type=float)
        categories = request.args.getlist('category')
        return jsonify(presenter.export_training_data(source_id, min_weight, categories or None))

    return api


# CLI for testing
if __name__ == '__main__':
    import sys

    presenter = Stage8Present()

    if len(sys.argv) < 2:
        # Show overall stats
        stats = presenter.get_stats()
        print("Pipeline Statistics:")
        print("-" * 40)
        print(f"Total sources: {stats['total_sources']}")
        print(f"Total segments: {stats['total_segments']}")
        print(f"Total duration: {presenter._format_duration(stats['total_duration'])}")
        print("\nBy type:")
        for t, count in stats['by_type'].items():
            print(f"  {t}: {count}")
        print("\nBy status:")
        for s, count in stats['by_status'].items():
            print(f"  {s}: {count}")

    elif sys.argv[1] == 'list':
        sources = presenter.list_sources()
        print(f"Sources ({sources['total']} total):")
        for s in sources['sources']:
            print(f"  {s['source_id']}: {s['title']} [{s['source_type']}]")

    elif sys.argv[1] == 'get' and len(sys.argv) > 2:
        source = presenter.get_source(sys.argv[2])
        if source:
            print(json.dumps(source, indent=2))
        else:
            print(f"Source not found: {sys.argv[2]}")

    elif sys.argv[1] == 'search' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        results = presenter.search(query)
        print(f"Search results for '{query}':")
        for r in results['results']:
            print(f"\n  [{r['match_type']}] {r['segment_id']} (score: {r['score']:.3f})")
            print(f"    {r.get('text', '')[:100]}...")

    elif sys.argv[1] == 'export' and len(sys.argv) > 2:
        count = presenter.export_jsonl(sys.argv[2])
        print(f"Exported {count} training examples to {sys.argv[2]}")

    else:
        print("Usage:")
        print("  python stage8_present.py              # Show stats")
        print("  python stage8_present.py list         # List sources")
        print("  python stage8_present.py get <id>     # Get source details")
        print("  python stage8_present.py search <q>   # Search content")
        print("  python stage8_present.py export <f>   # Export training data")
