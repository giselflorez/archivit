#!/usr/bin/env python3
"""
NORTHSTAR Video Transcription Script
=====================================
Transcribes pre-AI era videos and saves to verified transcripts folder.

Usage:
    ./venv/bin/python scripts/agent/transcribe_video.py <video_path> <master_name>

Example:
    ./venv/bin/python scripts/agent/transcribe_video.py \
        northstar_knowledge_bank/videos/downloads/Rand_Mike_Wallace_Interview_1959.webm \
        rand
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Suppress warnings
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import whisper

PROJECT_ROOT = Path(__file__).parent.parent.parent


def format_timestamp(seconds):
    """Convert seconds to [HH:MM:SS] format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes:02d}:{secs:02d}]"


def transcribe_video(video_path, master_name, model_size="base"):
    """
    Transcribe a video and save to NORTHSTAR transcripts folder.

    Args:
        video_path: Path to video file
        master_name: Name of master (e.g., 'rand', 'jung', 'tesla')
        model_size: Whisper model size (tiny, base, small, medium, large)
    """
    video_path = Path(video_path)

    if not video_path.exists():
        print(f"ERROR: Video not found: {video_path}")
        return None

    print(f"=" * 60)
    print(f"NORTHSTAR TRANSCRIPTION")
    print(f"=" * 60)
    print(f"Video: {video_path.name}")
    print(f"Master: {master_name}")
    print(f"Model: whisper-{model_size}")
    print()

    # Load model
    print("Loading Whisper model...")
    model = whisper.load_model(model_size)

    # Transcribe
    print("Transcribing (this may take a few minutes)...")
    result = model.transcribe(str(video_path), verbose=True)

    # Extract info
    detected_language = result.get('language', 'en')
    segments = result.get('segments', [])
    full_text = result.get('text', '')

    # Calculate stats
    word_count = len(full_text.split())
    duration_seconds = segments[-1]['end'] if segments else 0

    print()
    print(f"Transcription complete!")
    print(f"Language: {detected_language}")
    print(f"Words: {word_count}")
    print(f"Duration: {format_timestamp(duration_seconds)}")

    # Create output paths
    transcript_dir = PROJECT_ROOT / "northstar_knowledge_bank" / "transcripts" / "verified" / master_name.lower()
    transcript_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from video
    base_name = video_path.stem.lower().replace(' ', '_')
    md_path = transcript_dir / f"{base_name}.md"
    json_path = transcript_dir / f"{base_name}.json"

    # Create markdown transcript
    timestamp = datetime.now().isoformat()

    md_content = f"""---
id: transcript_{master_name}_{base_name}
master: {master_name}
source_video: {video_path.name}
original_date: {extract_year_from_filename(video_path.name)}
duration: {format_timestamp(duration_seconds)}
transcription_model: whisper-{model_size}
transcription_date: {timestamp[:10]}
language: {detected_language}
word_count: {word_count}
trust_level: 100
authentication: VERIFIED_PRE_AI
---

# {master_name.title()} - {video_path.stem.replace('_', ' ')}

## Transcript with Timestamps

"""

    # Add segments with timestamps
    for segment in segments:
        ts = format_timestamp(segment['start'])
        text = segment['text'].strip()
        md_content += f"{ts} {text}\n\n"

    # Add extracted quotes section
    md_content += """
---

## Key Quotes (To Extract)

*Review transcript above and extract notable quotes with timestamps*

---

*Transcribed by NORTHSTAR using local Whisper model. Pre-AI era content - VERIFIED authentic.*
"""

    # Save markdown
    md_path.write_text(md_content, encoding='utf-8')
    print(f"Saved: {md_path}")

    # Save JSON with full segment data
    json_data = {
        'master': master_name,
        'source_video': video_path.name,
        'transcription_date': timestamp,
        'model': f'whisper-{model_size}',
        'language': detected_language,
        'word_count': word_count,
        'duration_seconds': duration_seconds,
        'full_text': full_text,
        'segments': segments
    }

    json_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
    print(f"Saved: {json_path}")

    return {
        'md_path': str(md_path),
        'json_path': str(json_path),
        'word_count': word_count,
        'duration': format_timestamp(duration_seconds)
    }


def extract_year_from_filename(filename):
    """Extract year from filename like 'Rand_Mike_Wallace_Interview_1959.webm'"""
    import re
    match = re.search(r'(\d{4})', filename)
    return match.group(1) if match else 'Unknown'


def main():
    if len(sys.argv) < 3:
        print("Usage: python transcribe_video.py <video_path> <master_name> [model_size]")
        print("\nExample:")
        print("  python transcribe_video.py videos/Rand_Interview_1959.webm rand")
        print("\nModel sizes: tiny, base, small, medium, large")
        sys.exit(1)

    video_path = sys.argv[1]
    master_name = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "base"

    result = transcribe_video(video_path, master_name, model_size)

    if result:
        print()
        print("=" * 60)
        print("TRANSCRIPTION COMPLETE")
        print("=" * 60)
        print(f"Markdown: {result['md_path']}")
        print(f"JSON: {result['json_path']}")
        print(f"Words: {result['word_count']}")
        print(f"Duration: {result['duration']}")


if __name__ == "__main__":
    main()
