#!/usr/bin/env python3
"""
NORTHSTAR Content Authenticator
================================
Protects the databank from AI-era content contamination.

Content with metadata from 2024+ is flagged for review.
Pre-2024 content is considered "gold standard" - authentic human output.

Usage:
    from content_authenticator import authenticate_content
    result = authenticate_content(filepath)
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import json
import hashlib

# AI Era starts January 1, 2024 (when AI video/audio generation became widespread)
AI_ERA_START = datetime(2024, 1, 1)

# Trusted source domains (whitelist)
TRUSTED_SOURCES = [
    'archive.org',
    'youtube.com',
    'bbc.co.uk',
    'bbc.com',
    'pbs.org',
    'npr.org',
    'c-span.org',
    'smithsonian.edu',
    'loc.gov',  # Library of Congress
    'nationalarchives.gov.uk',
    'openculture.com',
]

# Allowed file extensions
ALLOWED_VIDEO = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v', '.wmv'}
ALLOWED_AUDIO = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
ALLOWED_MEDIA = ALLOWED_VIDEO | ALLOWED_AUDIO


def get_file_metadata(filepath):
    """Extract metadata from file using ffprobe"""
    filepath = Path(filepath)

    if not filepath.exists():
        return {'error': f'File not found: {filepath}'}

    metadata = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'extension': filepath.suffix.lower(),
        'size_bytes': filepath.stat().st_size,
        'file_created': None,
        'file_modified': None,
        'content_date': None,
        'duration': None,
        'format': None,
    }

    # Get file system dates
    stat = filepath.stat()
    metadata['file_modified'] = datetime.fromtimestamp(stat.st_mtime)
    metadata['file_created'] = datetime.fromtimestamp(stat.st_ctime)

    # Try to get media metadata using ffprobe
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(filepath)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            ffprobe_data = json.loads(result.stdout)

            # Extract format info
            fmt = ffprobe_data.get('format', {})
            metadata['duration'] = float(fmt.get('duration', 0))
            metadata['format'] = fmt.get('format_name')

            # Look for creation date in tags
            tags = fmt.get('tags', {})
            for date_key in ['creation_time', 'date', 'TDAT', 'TDRC', 'DATE']:
                if date_key in tags:
                    try:
                        date_str = tags[date_key]
                        # Try various date formats
                        for fmt_str in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%Y']:
                            try:
                                metadata['content_date'] = datetime.strptime(date_str[:len(fmt_str.replace('%', ''))], fmt_str)
                                break
                            except:
                                continue
                    except:
                        pass
                    break

    except Exception as e:
        metadata['ffprobe_error'] = str(e)

    return metadata


def calculate_file_hash(filepath):
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def authenticate_content(filepath, source_url=None, claimed_date=None):
    """
    Authenticate content for NORTHSTAR databank.

    Returns:
        dict with:
        - authenticated: bool (True if trusted)
        - flags: list of issues found
        - trust_level: 0-100
        - destination: 'verified/' or 'flagged/'
        - recommendations: list of suggested actions
    """

    filepath = Path(filepath)
    flags = []
    recommendations = []

    # Basic file checks
    if not filepath.exists():
        return {
            'authenticated': False,
            'flags': [{'type': 'FILE_NOT_FOUND', 'severity': 'CRITICAL'}],
            'trust_level': 0,
            'destination': 'rejected/',
            'recommendations': ['File does not exist']
        }

    # Check file extension
    if filepath.suffix.lower() not in ALLOWED_MEDIA:
        flags.append({
            'type': 'UNSUPPORTED_FORMAT',
            'severity': 'HIGH',
            'reason': f'File type {filepath.suffix} not in allowed list',
            'action': 'REJECT'
        })
        return {
            'authenticated': False,
            'flags': flags,
            'trust_level': 0,
            'destination': 'rejected/',
            'recommendations': ['Only video/audio files are accepted']
        }

    # Get metadata
    metadata = get_file_metadata(filepath)

    # Check source URL against whitelist
    if source_url:
        is_trusted_source = any(domain in source_url.lower() for domain in TRUSTED_SOURCES)
        if not is_trusted_source:
            flags.append({
                'type': 'UNTRUSTED_SOURCE',
                'severity': 'MEDIUM',
                'reason': f'Source {source_url} not in trusted whitelist',
                'action': 'REQUIRE_DOCUMENTATION'
            })
            recommendations.append('Provide documentation verifying source authenticity')

    # === DATE-BASED AUTHENTICATION ===

    dates = {
        'file_created': metadata.get('file_created'),
        'file_modified': metadata.get('file_modified'),
        'content_date': metadata.get('content_date') or claimed_date,
    }

    # Flag 1: Recent modification on supposedly old content
    if dates['content_date'] and dates['content_date'] < AI_ERA_START:
        if dates['file_modified'] and dates['file_modified'] >= AI_ERA_START:
            flags.append({
                'type': 'RECENT_MODIFICATION',
                'severity': 'HIGH',
                'reason': f"Pre-AI content ({dates['content_date'].year}) modified in AI era ({dates['file_modified'].strftime('%Y-%m-%d')})",
                'action': 'MANUAL_REVIEW_REQUIRED'
            })
            recommendations.append('Verify this is the original file, not AI-modified')

    # Flag 2: No original/content date
    if not dates['content_date']:
        flags.append({
            'type': 'NO_ORIGIN_DATE',
            'severity': 'MEDIUM',
            'reason': 'Cannot verify when content was originally created',
            'action': 'REQUIRE_SOURCE_DOCUMENTATION'
        })
        recommendations.append('Provide documentation of original creation/recording date')

    # Flag 3: All dates are in AI era
    known_dates = [d for d in dates.values() if d is not None]
    if known_dates and all(d >= AI_ERA_START for d in known_dates):
        flags.append({
            'type': 'AI_ERA_CONTENT',
            'severity': 'HIGH',
            'reason': 'All metadata dates are in AI era (2024+)',
            'action': 'DEEP_AUTHENTICATION_REQUIRED'
        })
        recommendations.append('This content may be AI-generated. Provide provenance documentation.')

    # Flag 4: Content claims to be very old but file is very new
    if dates['content_date'] and dates['file_created']:
        age_gap = (dates['file_created'] - dates['content_date']).days
        if dates['content_date'].year < 2000 and dates['file_created'] >= AI_ERA_START:
            if age_gap > 365 * 25:  # More than 25 years gap
                flags.append({
                    'type': 'SUSPICIOUS_AGE_GAP',
                    'severity': 'MEDIUM',
                    'reason': f'Content claims to be from {dates["content_date"].year} but file created recently',
                    'action': 'VERIFY_DIGITIZATION_SOURCE'
                })
                recommendations.append('Verify this is from a legitimate digitization/archive project')

    # Calculate trust level
    trust_level = calculate_trust_level(flags)

    # Determine destination
    if trust_level >= 80:
        destination = 'verified/'
    elif trust_level >= 50:
        destination = 'flagged/'
    else:
        destination = 'rejected/'

    # Generate file hash for integrity tracking
    file_hash = calculate_file_hash(filepath)

    return {
        'authenticated': len([f for f in flags if f['severity'] in ['HIGH', 'CRITICAL']]) == 0,
        'flags': flags,
        'trust_level': trust_level,
        'destination': destination,
        'recommendations': recommendations,
        'metadata': metadata,
        'file_hash': file_hash,
        'dates': {k: v.isoformat() if v else None for k, v in dates.items()}
    }


def calculate_trust_level(flags):
    """Calculate trust level 0-100 based on flags"""
    if not flags:
        return 100

    severity_scores = {
        'CRITICAL': 100,
        'HIGH': 40,
        'MEDIUM': 20,
        'LOW': 10
    }

    penalty = sum(severity_scores.get(f.get('severity', 'LOW'), 0) for f in flags)
    return max(0, 100 - penalty)


def authenticate_batch(filepaths, source_info=None):
    """Authenticate multiple files"""
    results = []
    for fp in filepaths:
        info = source_info.get(fp, {}) if source_info else {}
        result = authenticate_content(
            fp,
            source_url=info.get('source_url'),
            claimed_date=info.get('claimed_date')
        )
        results.append({
            'filepath': str(fp),
            **result
        })
    return results


# === CLI INTERFACE ===

def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python content_authenticator.py <filepath> [source_url] [claimed_date]")
        print("\nExample:")
        print("  python content_authenticator.py video.mp4 https://archive.org/... 1959-10-22")
        sys.exit(1)

    filepath = sys.argv[1]
    source_url = sys.argv[2] if len(sys.argv) > 2 else None
    claimed_date = None

    if len(sys.argv) > 3:
        try:
            claimed_date = datetime.strptime(sys.argv[3], '%Y-%m-%d')
        except:
            print(f"Warning: Could not parse date '{sys.argv[3]}', expected YYYY-MM-DD")

    print("=" * 60)
    print("NORTHSTAR CONTENT AUTHENTICATOR")
    print("=" * 60)
    print()

    result = authenticate_content(filepath, source_url, claimed_date)

    print(f"File: {filepath}")
    print(f"Trust Level: {result['trust_level']}%")
    print(f"Authenticated: {'YES' if result['authenticated'] else 'NO'}")
    print(f"Destination: {result['destination']}")
    print()

    if result['flags']:
        print("FLAGS:")
        for flag in result['flags']:
            print(f"  [{flag['severity']}] {flag['type']}")
            print(f"      {flag['reason']}")
        print()

    if result['recommendations']:
        print("RECOMMENDATIONS:")
        for rec in result['recommendations']:
            print(f"  - {rec}")
        print()

    print("DATES:")
    for key, value in result['dates'].items():
        print(f"  {key}: {value or 'Unknown'}")

    print()
    print(f"File Hash (SHA256): {result['file_hash'][:16]}...")

    return 0 if result['authenticated'] else 1


if __name__ == "__main__":
    sys.exit(main())
