#!/usr/bin/env python3
"""
MOONLANGUAGE 968 Subject Intelligence System

Each of the 968 moons becomes a training subject with:
- Media assets (photo, video, audio, ASCII)
- Verified quotes and transcripts
- Metadata integrity verification
- Historical accuracy scoring
- Provenance chain tracking

Storage-aware: Checks disk space before operations
Quality-scored: Every piece of data rated for accuracy/verification
Scientist-grade: Analyze data separate, grouped, or together

Usage:
    # Initialize all 968 subjects
    python subject_intelligence.py --init

    # Check storage requirements before scrape
    python subject_intelligence.py --preflight

    # View subject status
    python subject_intelligence.py --status

    # Analyze data quality
    python subject_intelligence.py --analyze

    # Start the visual browser
    python subject_intelligence.py --browser
"""

import os
import sys
import json
import hashlib
import shutil
import struct
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# CONFIGURATION
# =============================================================================

SUBJECTS_ROOT = PROJECT_ROOT / "data" / "training_subjects"
BACKUP_ROOT = PROJECT_ROOT / "backups" / "training_data"
MANIFEST_FILE = "manifest.json"

# Storage thresholds
MIN_FREE_SPACE_GB = 50  # Minimum free space before warning
BACKUP_THRESHOLD_GB = 100  # Create backup if data exceeds this

# 968 Subjects (MOONLANGUAGE collection)
TOTAL_SUBJECTS = 968

# =============================================================================
# DATA QUALITY ENUMS
# =============================================================================

class VerificationLevel(Enum):
    """How verified is the source?"""
    UNVERIFIED = 0.0
    ATTRIBUTED = 0.3      # Commonly attributed but not confirmed
    SECONDARY = 0.5       # Secondary source (biography, article)
    SCHOLARLY = 0.7       # Academic/scholarly source
    PRIMARY = 0.9         # Primary source (original writing, recording)
    AUTHENTICATED = 1.0   # Cryptographically or institutionally verified


class MetadataIntegrity(Enum):
    """Is the metadata trustworthy?"""
    MISSING = 0.0         # No metadata
    STRIPPED = 0.2        # Metadata was removed
    ALTERED = 0.3         # Signs of tampering
    PARTIAL = 0.5         # Some metadata present
    COMPLETE = 0.8        # Full metadata present
    VERIFIED = 1.0        # Metadata verified against external source


class DateAccuracy(Enum):
    """How confident are we in dates?"""
    UNKNOWN = 0.0
    DECADE = 0.3          # Know the decade
    YEAR = 0.6            # Know the year
    MONTH = 0.8           # Know month and year
    EXACT = 1.0           # Exact date verified


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MediaAsset:
    """A single media file with quality metrics."""
    path: str
    filename: str
    size_bytes: int
    file_type: str  # photo, video, audio, document, ascii
    extension: str

    # Quality metrics
    verification_level: float = 0.0
    metadata_integrity: float = 0.0
    date_accuracy: float = 0.0
    alteration_risk: float = 1.0  # 1.0 = high risk, 0.0 = no risk

    # Metadata
    exif_data: Optional[Dict] = None
    creation_date: Optional[str] = None
    source_url: Optional[str] = None
    source_citation: Optional[str] = None

    # Hashes for integrity
    sha256: Optional[str] = None
    perceptual_hash: Optional[str] = None  # For images

    def to_dict(self):
        return asdict(self)

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)

    @property
    def size_display(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{self.size_bytes / (1024*1024):.1f} MB"
        else:
            return f"{self.size_bytes / (1024*1024*1024):.2f} GB"

    @property
    def quality_score(self) -> float:
        """Combined quality score (0-1)."""
        return (
            self.verification_level * 0.4 +
            self.metadata_integrity * 0.3 +
            self.date_accuracy * 0.2 +
            (1 - self.alteration_risk) * 0.1
        )

    @property
    def quality_grade(self) -> str:
        """Letter grade for quality."""
        score = self.quality_score
        if score >= 0.9: return "A+"
        if score >= 0.8: return "A"
        if score >= 0.7: return "B"
        if score >= 0.6: return "C"
        if score >= 0.5: return "D"
        return "F"


@dataclass
class TrainingSubject:
    """One of 968 training subjects."""
    id: int  # 1-968
    name: str  # Moon identifier
    status: str = "pending"  # pending, partial, complete, verified

    # Assets
    assets: List[MediaAsset] = None

    # Quotes with verification
    quotes: List[Dict] = None

    # Transcripts from media
    transcripts: List[Dict] = None

    # Historical context
    historical_notes: str = ""
    era: str = ""
    related_subjects: List[int] = None

    # Quality metrics (aggregated)
    overall_verification: float = 0.0
    overall_integrity: float = 0.0
    data_completeness: float = 0.0

    # Storage
    total_size_bytes: int = 0

    # Timestamps
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.assets is None:
            self.assets = []
        if self.quotes is None:
            self.quotes = []
        if self.transcripts is None:
            self.transcripts = []
        if self.related_subjects is None:
            self.related_subjects = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        d = asdict(self)
        d['assets'] = [a.to_dict() if isinstance(a, MediaAsset) else a for a in self.assets]
        return d

    @property
    def size_display(self) -> str:
        if self.total_size_bytes < 1024 * 1024:
            return f"{self.total_size_bytes / 1024:.1f} KB"
        elif self.total_size_bytes < 1024 * 1024 * 1024:
            return f"{self.total_size_bytes / (1024*1024):.1f} MB"
        else:
            return f"{self.total_size_bytes / (1024*1024*1024):.2f} GB"

    @property
    def quality_score(self) -> float:
        """Overall quality score for this subject."""
        if not self.assets:
            return 0.0
        asset_scores = [a.quality_score for a in self.assets if isinstance(a, MediaAsset)]
        if not asset_scores:
            return 0.0
        return sum(asset_scores) / len(asset_scores)

    def calculate_completeness(self) -> float:
        """How complete is the data for this subject?"""
        checks = [
            len(self.assets) > 0,              # Has at least one asset
            any(a.file_type == 'photo' for a in self.assets if isinstance(a, MediaAsset)),
            any(a.file_type == 'video' for a in self.assets if isinstance(a, MediaAsset)),
            len(self.quotes) >= 1,             # Has at least one quote
            len(self.transcripts) >= 1,        # Has transcript
            bool(self.historical_notes),       # Has historical context
        ]
        self.data_completeness = sum(checks) / len(checks)
        return self.data_completeness


# =============================================================================
# STORAGE MANAGEMENT
# =============================================================================

class StorageManager:
    """Manage disk space and backups for training data."""

    def __init__(self):
        self.subjects_root = SUBJECTS_ROOT
        self.backup_root = BACKUP_ROOT

    def get_disk_usage(self) -> Dict:
        """Get current disk usage statistics."""
        total, used, free = shutil.disk_usage("/")
        project_size = self._get_dir_size(PROJECT_ROOT)
        training_size = self._get_dir_size(self.subjects_root) if self.subjects_root.exists() else 0

        return {
            "disk_total_gb": total / (1024**3),
            "disk_used_gb": used / (1024**3),
            "disk_free_gb": free / (1024**3),
            "disk_free_percent": (free / total) * 100,
            "project_size_gb": project_size / (1024**3),
            "training_size_gb": training_size / (1024**3),
            "backup_needed": training_size > (BACKUP_THRESHOLD_GB * 1024**3),
            "space_warning": free < (MIN_FREE_SPACE_GB * 1024**3)
        }

    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory."""
        total = 0
        if path.exists():
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        return total

    def estimate_scrape_size(self, subject_count: int = TOTAL_SUBJECTS) -> Dict:
        """
        Estimate storage needed for a scrape.

        Assumptions per subject:
        - Photo: ~5 MB
        - Video: ~50 MB
        - Audio: ~10 MB
        - Transcripts/quotes: ~100 KB
        """
        per_subject_mb = 65  # Conservative estimate
        total_mb = subject_count * per_subject_mb
        total_gb = total_mb / 1024

        disk_info = self.get_disk_usage()

        return {
            "subjects": subject_count,
            "estimated_size_mb": total_mb,
            "estimated_size_gb": total_gb,
            "current_free_gb": disk_info["disk_free_gb"],
            "after_scrape_free_gb": disk_info["disk_free_gb"] - total_gb,
            "can_proceed": disk_info["disk_free_gb"] > (total_gb + MIN_FREE_SPACE_GB),
            "backup_recommended": total_gb > BACKUP_THRESHOLD_GB,
            "warning": None
        }

    def preflight_check(self, subject_count: int = TOTAL_SUBJECTS) -> Tuple[bool, str]:
        """
        Run preflight check before starting scrape.

        Returns (can_proceed, message)
        """
        estimate = self.estimate_scrape_size(subject_count)
        disk = self.get_disk_usage()

        messages = []
        can_proceed = True

        # Check free space
        if disk["space_warning"]:
            messages.append(f"⚠️  LOW DISK SPACE: {disk['disk_free_gb']:.1f} GB free")
            messages.append(f"   Minimum recommended: {MIN_FREE_SPACE_GB} GB")

        if not estimate["can_proceed"]:
            can_proceed = False
            messages.append(f"❌ INSUFFICIENT SPACE for {subject_count} subjects")
            messages.append(f"   Need: {estimate['estimated_size_gb']:.1f} GB")
            messages.append(f"   Have: {disk['disk_free_gb']:.1f} GB")

        # Backup recommendation
        if estimate["backup_recommended"]:
            messages.append(f"📦 BACKUP RECOMMENDED before proceeding")
            messages.append(f"   Training data will exceed {BACKUP_THRESHOLD_GB} GB")

        # Current status
        messages.append(f"\n📊 STORAGE STATUS:")
        messages.append(f"   Disk free: {disk['disk_free_gb']:.1f} GB ({disk['disk_free_percent']:.0f}%)")
        messages.append(f"   Project size: {disk['project_size_gb']:.2f} GB")
        messages.append(f"   Training data: {disk['training_size_gb']:.2f} GB")
        messages.append(f"\n📈 SCRAPE ESTIMATE ({subject_count} subjects):")
        messages.append(f"   Estimated size: {estimate['estimated_size_gb']:.1f} GB")
        messages.append(f"   After scrape: {estimate['after_scrape_free_gb']:.1f} GB free")

        if can_proceed:
            messages.append(f"\n✅ PREFLIGHT CHECK PASSED - Safe to proceed")
        else:
            messages.append(f"\n❌ PREFLIGHT CHECK FAILED - Clear space before proceeding")

        return can_proceed, "\n".join(messages)

    def create_backup(self, description: str = "") -> Optional[Path]:
        """Create backup of training data."""
        if not self.subjects_root.exists():
            print("No training data to backup")
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_name = f"training_backup_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"

        backup_path = self.backup_root / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        print(f"Creating backup: {backup_path}")
        shutil.copytree(self.subjects_root, backup_path / "training_subjects")

        # Write manifest
        manifest = {
            "created": datetime.now().isoformat(),
            "description": description,
            "source": str(self.subjects_root),
            "size_bytes": self._get_dir_size(backup_path)
        }
        with open(backup_path / "backup_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"✓ Backup complete: {backup_path}")
        return backup_path


# =============================================================================
# METADATA INTEGRITY CHECKER
# =============================================================================

class MetadataChecker:
    """Check metadata integrity and detect tampering."""

    @staticmethod
    def check_exif(file_path: Path) -> Dict:
        """
        Extract and analyze EXIF data from image.

        Returns quality metrics and extracted data.
        """
        result = {
            "has_exif": False,
            "integrity_score": 0.0,
            "alteration_risk": 1.0,
            "date_accuracy": 0.0,
            "exif_data": {},
            "warnings": [],
            "verified_fields": []
        }

        if not file_path.exists():
            result["warnings"].append("File not found")
            return result

        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS

            img = Image.open(file_path)
            exif_raw = img._getexif()

            if exif_raw is None:
                result["warnings"].append("No EXIF data found")
                result["integrity_score"] = MetadataIntegrity.MISSING.value
                return result

            result["has_exif"] = True
            exif_data = {}

            for tag_id, value in exif_raw.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='ignore')
                    except:
                        value = str(value)
                exif_data[tag] = value

            result["exif_data"] = exif_data

            # Analyze integrity
            integrity_checks = []

            # Check for date fields
            if "DateTimeOriginal" in exif_data:
                result["verified_fields"].append("DateTimeOriginal")
                result["date_accuracy"] = DateAccuracy.EXACT.value
                integrity_checks.append(True)
            elif "DateTime" in exif_data:
                result["date_accuracy"] = DateAccuracy.EXACT.value
                integrity_checks.append(True)
            else:
                result["warnings"].append("No date in EXIF")
                integrity_checks.append(False)

            # Check for camera info
            if "Make" in exif_data and "Model" in exif_data:
                result["verified_fields"].append("Camera")
                integrity_checks.append(True)
            else:
                integrity_checks.append(False)

            # Check for software (editing indicator)
            if "Software" in exif_data:
                software = str(exif_data["Software"]).lower()
                if any(editor in software for editor in ["photoshop", "lightroom", "gimp", "capture one"]):
                    result["warnings"].append(f"Edited with: {exif_data['Software']}")
                    result["alteration_risk"] = 0.7
                else:
                    result["alteration_risk"] = 0.3

            # Calculate integrity score
            if integrity_checks:
                result["integrity_score"] = sum(integrity_checks) / len(integrity_checks)
                if result["integrity_score"] > 0.8:
                    result["integrity_score"] = MetadataIntegrity.COMPLETE.value
                elif result["integrity_score"] > 0.5:
                    result["integrity_score"] = MetadataIntegrity.PARTIAL.value
                else:
                    result["integrity_score"] = MetadataIntegrity.ALTERED.value

        except ImportError:
            result["warnings"].append("PIL not available for EXIF extraction")
        except Exception as e:
            result["warnings"].append(f"EXIF extraction error: {str(e)}")

        return result

    @staticmethod
    def check_video_metadata(file_path: Path) -> Dict:
        """Extract and analyze video metadata."""
        result = {
            "has_metadata": False,
            "integrity_score": 0.0,
            "alteration_risk": 1.0,
            "date_accuracy": 0.0,
            "metadata": {},
            "warnings": []
        }

        if not file_path.exists():
            result["warnings"].append("File not found")
            return result

        try:
            import subprocess
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
                   "-show_format", "-show_streams", str(file_path)]
            output = subprocess.run(cmd, capture_output=True, text=True)

            if output.returncode == 0:
                data = json.loads(output.stdout)
                result["has_metadata"] = True
                result["metadata"] = data.get("format", {}).get("tags", {})

                # Check creation time
                if "creation_time" in result["metadata"]:
                    result["date_accuracy"] = DateAccuracy.EXACT.value

                result["integrity_score"] = MetadataIntegrity.COMPLETE.value
                result["alteration_risk"] = 0.5

        except FileNotFoundError:
            result["warnings"].append("ffprobe not available")
        except Exception as e:
            result["warnings"].append(f"Metadata extraction error: {str(e)}")

        return result

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file for integrity verification."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# SUBJECT INTELLIGENCE ENGINE
# =============================================================================

class SubjectIntelligence:
    """
    Main engine for 968 training subjects.

    Manages all subjects with:
    - Storage-aware operations
    - Quality scoring
    - Metadata verification
    - Historical analysis
    """

    def __init__(self):
        self.subjects_root = SUBJECTS_ROOT
        self.storage = StorageManager()
        self.metadata_checker = MetadataChecker()
        self.subjects: Dict[int, TrainingSubject] = {}

        # Ensure directories exist
        self.subjects_root.mkdir(parents=True, exist_ok=True)

    def initialize_subjects(self, count: int = TOTAL_SUBJECTS) -> bool:
        """
        Initialize folder structure for all subjects.

        Creates:
        /data/training_subjects/
        ├── subject_001/
        │   ├── manifest.json
        │   ├── media/
        │   ├── quotes/
        │   ├── transcripts/
        │   └── provenance/
        ...
        └── subject_968/
        """
        print(f"\n{'='*60}")
        print(f"INITIALIZING {count} TRAINING SUBJECTS")
        print(f"{'='*60}")

        # Preflight check
        can_proceed, message = self.storage.preflight_check(count)
        print(message)

        if not can_proceed:
            return False

        print(f"\nCreating subject directories...")

        for i in range(1, count + 1):
            subject_id = f"subject_{i:03d}"
            subject_path = self.subjects_root / subject_id

            # Create directory structure
            (subject_path / "media").mkdir(parents=True, exist_ok=True)
            (subject_path / "quotes").mkdir(exist_ok=True)
            (subject_path / "transcripts").mkdir(exist_ok=True)
            (subject_path / "provenance").mkdir(exist_ok=True)

            # Create manifest
            subject = TrainingSubject(
                id=i,
                name=f"Moon {i:03d}",
                status="pending"
            )

            manifest_path = subject_path / MANIFEST_FILE
            with open(manifest_path, "w") as f:
                json.dump(subject.to_dict(), f, indent=2)

            if i % 100 == 0:
                print(f"  Created {i}/{count} subjects...")

        print(f"\n✓ Initialized {count} subjects at {self.subjects_root}")
        return True

    def load_subject(self, subject_id: int) -> Optional[TrainingSubject]:
        """Load a subject from disk."""
        subject_path = self.subjects_root / f"subject_{subject_id:03d}"
        manifest_path = subject_path / MANIFEST_FILE

        if not manifest_path.exists():
            return None

        with open(manifest_path) as f:
            data = json.load(f)

        # Convert assets back to MediaAsset objects
        assets = []
        for a in data.get("assets", []):
            if isinstance(a, dict):
                assets.append(MediaAsset(**a))
            else:
                assets.append(a)

        subject = TrainingSubject(
            id=data.get("id", subject_id),
            name=data.get("name", f"Moon {subject_id:03d}"),
            status=data.get("status", "pending"),
            assets=assets,
            quotes=data.get("quotes", []),
            transcripts=data.get("transcripts", []),
            historical_notes=data.get("historical_notes", ""),
            era=data.get("era", ""),
            related_subjects=data.get("related_subjects", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

        return subject

    def save_subject(self, subject: TrainingSubject) -> bool:
        """Save a subject to disk."""
        subject_path = self.subjects_root / f"subject_{subject.id:03d}"
        manifest_path = subject_path / MANIFEST_FILE

        subject.updated_at = datetime.now().isoformat()

        # Recalculate totals
        subject.total_size_bytes = sum(
            a.size_bytes for a in subject.assets if isinstance(a, MediaAsset)
        )
        subject.calculate_completeness()

        with open(manifest_path, "w") as f:
            json.dump(subject.to_dict(), f, indent=2)

        return True

    def add_media_to_subject(self, subject_id: int, file_path: Path,
                             source_url: str = None, citation: str = None) -> Optional[MediaAsset]:
        """
        Add a media file to a subject with full analysis.
        """
        subject = self.load_subject(subject_id)
        if not subject:
            print(f"Subject {subject_id} not found")
            return None

        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None

        # Determine file type
        ext = file_path.suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".tiff", ".webp"]:
            file_type = "photo"
        elif ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
            file_type = "video"
        elif ext in [".mp3", ".wav", ".m4a", ".flac", ".ogg"]:
            file_type = "audio"
        elif ext in [".pdf", ".txt", ".md", ".doc", ".docx"]:
            file_type = "document"
        elif ext in [".png"] and "ascii" in file_path.name.lower():
            file_type = "ascii"
        else:
            file_type = "other"

        # Get file stats
        stat = file_path.stat()

        # Compute hash
        file_hash = self.metadata_checker.compute_file_hash(file_path)

        # Check metadata based on type
        if file_type == "photo":
            meta_check = self.metadata_checker.check_exif(file_path)
        elif file_type == "video":
            meta_check = self.metadata_checker.check_video_metadata(file_path)
        else:
            meta_check = {
                "integrity_score": 0.5,
                "alteration_risk": 0.5,
                "date_accuracy": 0.0,
                "exif_data": {}
            }

        # Copy file to subject directory
        dest_dir = self.subjects_root / f"subject_{subject_id:03d}" / "media"
        dest_path = dest_dir / file_path.name
        shutil.copy2(file_path, dest_path)

        # Create asset record
        asset = MediaAsset(
            path=str(dest_path.relative_to(self.subjects_root)),
            filename=file_path.name,
            size_bytes=stat.st_size,
            file_type=file_type,
            extension=ext,
            verification_level=VerificationLevel.UNVERIFIED.value,
            metadata_integrity=meta_check.get("integrity_score", 0.0),
            date_accuracy=meta_check.get("date_accuracy", 0.0),
            alteration_risk=meta_check.get("alteration_risk", 1.0),
            exif_data=meta_check.get("exif_data", {}),
            creation_date=meta_check.get("exif_data", {}).get("DateTimeOriginal"),
            source_url=source_url,
            source_citation=citation,
            sha256=file_hash
        )

        subject.assets.append(asset)
        self.save_subject(subject)

        print(f"✓ Added {file_type} to subject {subject_id}")
        print(f"  File: {asset.filename}")
        print(f"  Size: {asset.size_display}")
        print(f"  Quality: {asset.quality_grade} ({asset.quality_score:.2f})")
        print(f"  Integrity: {asset.metadata_integrity:.2f}")
        print(f"  Alteration risk: {asset.alteration_risk:.2f}")

        return asset

    def get_all_subjects_status(self) -> Dict:
        """Get status summary of all subjects."""
        status = {
            "total": 0,
            "pending": 0,
            "partial": 0,
            "complete": 0,
            "verified": 0,
            "total_size_bytes": 0,
            "total_assets": 0,
            "total_quotes": 0,
            "avg_quality": 0.0,
            "subjects": []
        }

        quality_scores = []

        for subject_dir in sorted(self.subjects_root.iterdir()):
            if not subject_dir.is_dir() or not subject_dir.name.startswith("subject_"):
                continue

            subject_id = int(subject_dir.name.split("_")[1])
            subject = self.load_subject(subject_id)

            if subject:
                status["total"] += 1
                status[subject.status] = status.get(subject.status, 0) + 1
                status["total_size_bytes"] += subject.total_size_bytes
                status["total_assets"] += len(subject.assets)
                status["total_quotes"] += len(subject.quotes)

                if subject.quality_score > 0:
                    quality_scores.append(subject.quality_score)

                status["subjects"].append({
                    "id": subject.id,
                    "name": subject.name,
                    "status": subject.status,
                    "assets": len(subject.assets),
                    "quotes": len(subject.quotes),
                    "size": subject.size_display,
                    "quality": subject.quality_score,
                    "completeness": subject.data_completeness
                })

        if quality_scores:
            status["avg_quality"] = sum(quality_scores) / len(quality_scores)

        return status

    def generate_analysis_report(self) -> str:
        """Generate detailed analysis report for scientist-grade review."""
        status = self.get_all_subjects_status()
        disk = self.storage.get_disk_usage()

        lines = [
            "=" * 70,
            "MOONLANGUAGE 968 SUBJECTS - INTELLIGENCE ANALYSIS REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 70,
            "",
            "STORAGE STATUS",
            "-" * 40,
            f"  Disk free: {disk['disk_free_gb']:.1f} GB ({disk['disk_free_percent']:.0f}%)",
            f"  Training data: {disk['training_size_gb']:.2f} GB",
            f"  Backup needed: {'YES' if disk['backup_needed'] else 'NO'}",
            "",
            "SUBJECT STATUS",
            "-" * 40,
            f"  Total subjects: {status['total']} / {TOTAL_SUBJECTS}",
            f"  Pending: {status['pending']}",
            f"  Partial: {status['partial']}",
            f"  Complete: {status['complete']}",
            f"  Verified: {status['verified']}",
            "",
            "DATA QUALITY",
            "-" * 40,
            f"  Total assets: {status['total_assets']}",
            f"  Total quotes: {status['total_quotes']}",
            f"  Average quality score: {status['avg_quality']:.2f}",
            f"  Total data size: {status['total_size_bytes'] / (1024**3):.2f} GB",
            "",
            "VERIFICATION BREAKDOWN",
            "-" * 40,
        ]

        # Count by verification level
        verification_counts = {level.name: 0 for level in VerificationLevel}
        for subj in status["subjects"]:
            subject = self.load_subject(subj["id"])
            if subject:
                for asset in subject.assets:
                    if isinstance(asset, MediaAsset):
                        for level in VerificationLevel:
                            if asset.verification_level >= level.value:
                                verification_counts[level.name] += 1
                                break

        for level_name, count in verification_counts.items():
            lines.append(f"  {level_name}: {count}")

        lines.extend([
            "",
            "TOP 10 SUBJECTS BY DATA COMPLETENESS",
            "-" * 40
        ])

        sorted_subjects = sorted(status["subjects"], key=lambda x: x["completeness"], reverse=True)
        for subj in sorted_subjects[:10]:
            lines.append(f"  {subj['name']}: {subj['completeness']:.0%} complete, {subj['assets']} assets")

        lines.extend([
            "",
            "SUBJECTS NEEDING ATTENTION (Low Quality)",
            "-" * 40
        ])

        low_quality = [s for s in status["subjects"] if s["quality"] < 0.5 and s["quality"] > 0]
        for subj in low_quality[:10]:
            lines.append(f"  {subj['name']}: Quality {subj['quality']:.2f}")

        lines.extend([
            "",
            "=" * 70,
            "END REPORT",
            "=" * 70
        ])

        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="MOONLANGUAGE 968 Subject Intelligence System"
    )
    parser.add_argument("--init", action="store_true",
                        help="Initialize all 968 subject directories")
    parser.add_argument("--preflight", action="store_true",
                        help="Run storage preflight check")
    parser.add_argument("--status", action="store_true",
                        help="Show status of all subjects")
    parser.add_argument("--analyze", action="store_true",
                        help="Generate detailed analysis report")
    parser.add_argument("--add-media", type=str,
                        help="Add media file to subject")
    parser.add_argument("--subject", type=int,
                        help="Subject ID (1-968)")
    parser.add_argument("--backup", action="store_true",
                        help="Create backup of training data")
    parser.add_argument("--browser", action="store_true",
                        help="Start visual browser (opens web interface)")

    args = parser.parse_args()

    engine = SubjectIntelligence()

    if args.init:
        engine.initialize_subjects()

    elif args.preflight:
        can_proceed, message = engine.storage.preflight_check()
        print(message)

    elif args.status:
        status = engine.get_all_subjects_status()
        print(f"\n{'='*60}")
        print("968 SUBJECTS STATUS")
        print(f"{'='*60}")
        print(f"Total: {status['total']} / {TOTAL_SUBJECTS}")
        print(f"Pending: {status['pending']}")
        print(f"Partial: {status['partial']}")
        print(f"Complete: {status['complete']}")
        print(f"Verified: {status['verified']}")
        print(f"Total assets: {status['total_assets']}")
        print(f"Total size: {status['total_size_bytes'] / (1024**3):.2f} GB")
        print(f"Avg quality: {status['avg_quality']:.2f}")

    elif args.analyze:
        report = engine.generate_analysis_report()
        print(report)

        # Also save to file
        report_path = PROJECT_ROOT / "data" / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(report)
        print(f"\nReport saved to: {report_path}")

    elif args.add_media:
        if not args.subject:
            print("ERROR: --subject required")
            return
        engine.add_media_to_subject(args.subject, Path(args.add_media))

    elif args.backup:
        engine.storage.create_backup("manual_backup")

    elif args.browser:
        print("Starting visual browser...")
        print("Visit: http://localhost:5001/training-browser")
        # Would integrate with visual_browser.py

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
