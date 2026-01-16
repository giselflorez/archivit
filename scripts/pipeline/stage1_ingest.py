"""
DOC-8 Agent Analysis Pipeline - Stage 1: Ingestion

Handles:
- Accept file/URL
- Validate format
- Create source record
- Generate preview thumbnail
- Queue for processing
"""

import os
import mimetypes
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse
import json

from .models import Source, SourceType, ProcessingStatus


# Supported file types
SUPPORTED_VIDEO = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
SUPPORTED_AUDIO = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
SUPPORTED_DOCUMENT = {'.pdf', '.epub', '.txt', '.md', '.docx', '.doc'}
SUPPORTED_WEB = {'http', 'https'}
SUPPORTED_IMAGE = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}


class IngestError(Exception):
    """Error during ingestion"""
    pass


class Stage1Ingest:
    """
    Stage 1: Raw Ingestion

    Accepts files or URLs, validates format, creates source records,
    and queues for further processing.
    """

    def __init__(self, storage_dir: str = None):
        """
        Initialize ingestion stage.

        Args:
            storage_dir: Directory for storing processed files and metadata
        """
        self.storage_dir = Path(storage_dir or os.path.expanduser('~/.arc8/sources'))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.storage_dir / 'thumbnails').mkdir(exist_ok=True)
        (self.storage_dir / 'metadata').mkdir(exist_ok=True)
        (self.storage_dir / 'queue').mkdir(exist_ok=True)

    def ingest(self, input_path: str, title: str = None, author: str = None) -> Source:
        """
        Ingest a file or URL.

        Args:
            input_path: File path or URL to ingest
            title: Optional title override
            author: Optional author override

        Returns:
            Source object with ingestion metadata
        """
        # Determine if URL or file
        if self._is_url(input_path):
            return self._ingest_url(input_path, title, author)
        else:
            return self._ingest_file(input_path, title, author)

    def _is_url(self, path: str) -> bool:
        """Check if path is a URL"""
        parsed = urlparse(path)
        return parsed.scheme in SUPPORTED_WEB

    def _ingest_file(self, file_path: str, title: str = None, author: str = None) -> Source:
        """Ingest a local file"""
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            raise IngestError(f"File not found: {file_path}")

        # Validate file type
        source_type = self._detect_file_type(path)
        if source_type is None:
            raise IngestError(f"Unsupported file type: {path.suffix}")

        # Get file metadata
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))

        # Create source record
        source = Source(
            source_type=source_type,
            status=ProcessingStatus.INGESTING,
            file_path=str(path.absolute()),
            title=title or path.stem,
            author=author,
            file_size=stat.st_size,
            mime_type=mime_type,
            created_date=datetime.fromtimestamp(stat.st_mtime).isoformat()
        )

        # Get media duration if applicable
        if source_type in (SourceType.VIDEO, SourceType.AUDIO):
            source.duration = self._get_media_duration(path)

        # Generate content hash for deduplication
        content_hash = self._compute_hash(path)
        source.source_id = f"file_{content_hash[:16]}"

        # Generate thumbnail if applicable
        if source_type == SourceType.VIDEO:
            source.thumbnail_path = self._generate_video_thumbnail(path, source.source_id)
        elif source_type == SourceType.DOCUMENT and path.suffix == '.pdf':
            source.thumbnail_path = self._generate_pdf_thumbnail(path, source.source_id)

        # Save metadata
        self._save_source_metadata(source)

        # Queue for processing
        self._queue_source(source)

        source.status = ProcessingStatus.QUEUED
        return source

    def _ingest_url(self, url: str, title: str = None, author: str = None) -> Source:
        """Ingest a web URL"""
        parsed = urlparse(url)

        # Create source record
        source = Source(
            source_type=SourceType.WEB,
            status=ProcessingStatus.INGESTING,
            url=url,
            title=title or parsed.netloc,
            author=author
        )

        # Generate URL hash for ID
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        source.source_id = f"web_{url_hash[:16]}"

        # Save metadata
        self._save_source_metadata(source)

        # Queue for processing
        self._queue_source(source)

        source.status = ProcessingStatus.QUEUED
        return source

    def _detect_file_type(self, path: Path) -> Optional[SourceType]:
        """Detect source type from file extension"""
        suffix = path.suffix.lower()

        if suffix in SUPPORTED_VIDEO:
            return SourceType.VIDEO
        elif suffix in SUPPORTED_AUDIO:
            return SourceType.AUDIO
        elif suffix in SUPPORTED_DOCUMENT:
            return SourceType.DOCUMENT
        elif suffix in SUPPORTED_IMAGE:
            return SourceType.IMAGE
        else:
            return None

    def _compute_hash(self, path: Path, chunk_size: int = 8192) -> str:
        """Compute SHA-256 hash of file content"""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_media_duration(self, path: Path) -> Optional[float]:
        """Get duration of audio/video file"""
        try:
            # Try ffprobe first
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries',
                 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                 str(path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        # Fallback: try moviepy
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip
            if path.suffix.lower() in SUPPORTED_VIDEO:
                clip = VideoFileClip(str(path))
            else:
                clip = AudioFileClip(str(path))
            duration = clip.duration
            clip.close()
            return duration
        except ImportError:
            pass
        except Exception:
            pass

        return None

    def _generate_video_thumbnail(self, path: Path, source_id: str) -> Optional[str]:
        """Generate thumbnail from video"""
        thumbnail_path = self.storage_dir / 'thumbnails' / f"{source_id}.jpg"

        try:
            # Try ffmpeg
            import subprocess
            subprocess.run(
                ['ffmpeg', '-y', '-i', str(path), '-ss', '00:00:05',
                 '-vframes', '1', '-q:v', '2', str(thumbnail_path)],
                capture_output=True, timeout=30
            )
            if thumbnail_path.exists():
                return str(thumbnail_path)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: try moviepy
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(str(path))
            # Get frame at 5 seconds or 10% through
            t = min(5, clip.duration * 0.1)
            frame = clip.get_frame(t)
            clip.close()

            from PIL import Image
            img = Image.fromarray(frame)
            img.thumbnail((320, 180))
            img.save(thumbnail_path, 'JPEG', quality=85)
            return str(thumbnail_path)
        except ImportError:
            pass
        except Exception:
            pass

        return None

    def _generate_pdf_thumbnail(self, path: Path, source_id: str) -> Optional[str]:
        """Generate thumbnail from PDF first page"""
        thumbnail_path = self.storage_dir / 'thumbnails' / f"{source_id}.jpg"

        try:
            from pdf2image import convert_from_path
            images = convert_from_path(str(path), first_page=1, last_page=1)
            if images:
                img = images[0]
                img.thumbnail((320, 450))
                img.save(thumbnail_path, 'JPEG', quality=85)
                return str(thumbnail_path)
        except ImportError:
            pass
        except Exception:
            pass

        return None

    def _save_source_metadata(self, source: Source):
        """Save source metadata to JSON file"""
        metadata_path = self.storage_dir / 'metadata' / f"{source.source_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(source.to_dict(), f, indent=2)

    def _queue_source(self, source: Source):
        """Add source to processing queue"""
        queue_path = self.storage_dir / 'queue' / f"{source.source_id}.json"
        with open(queue_path, 'w') as f:
            json.dump({
                'source_id': source.source_id,
                'source_type': source.source_type.value,
                'queued_at': datetime.utcnow().isoformat(),
                'next_stage': 'transcribe' if source.source_type in (SourceType.VIDEO, SourceType.AUDIO) else 'segment'
            }, f, indent=2)

    def get_queue(self) -> list:
        """Get list of queued sources"""
        queue = []
        queue_dir = self.storage_dir / 'queue'
        for queue_file in queue_dir.glob('*.json'):
            with open(queue_file) as f:
                queue.append(json.load(f))
        return sorted(queue, key=lambda x: x.get('queued_at', ''))

    def get_source(self, source_id: str) -> Optional[Source]:
        """Load source by ID"""
        metadata_path = self.storage_dir / 'metadata' / f"{source_id}.json"
        if not metadata_path.exists():
            return None

        with open(metadata_path) as f:
            data = json.load(f)

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
            thumbnail_path=data.get('thumbnail_path')
        )
        return source

    def validate(self, source: Source) -> Tuple[bool, str]:
        """
        Validate source is ready for processing.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists (for file sources)
        if source.file_path:
            if not Path(source.file_path).exists():
                return False, f"File not found: {source.file_path}"

        # Check URL is accessible (for web sources)
        if source.url:
            try:
                import urllib.request
                urllib.request.urlopen(source.url, timeout=10)
            except Exception as e:
                return False, f"URL not accessible: {e}"

        # Check file size limits (500MB max for now)
        if source.file_size and source.file_size > 500 * 1024 * 1024:
            return False, f"File too large: {source.file_size / (1024*1024):.1f}MB (max 500MB)"

        return True, ""


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python stage1_ingest.py <file_or_url>")
        sys.exit(1)

    ingest = Stage1Ingest()
    try:
        source = ingest.ingest(sys.argv[1])
        print(f"Ingested: {source.source_id}")
        print(f"Type: {source.source_type.value}")
        print(f"Title: {source.title}")
        print(f"Status: {source.status.value}")
        if source.duration:
            print(f"Duration: {source.duration:.1f}s")
        if source.thumbnail_path:
            print(f"Thumbnail: {source.thumbnail_path}")
        print(f"\nQueued for processing.")
    except IngestError as e:
        print(f"Error: {e}")
        sys.exit(1)
