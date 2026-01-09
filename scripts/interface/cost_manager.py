#!/usr/bin/env python3
"""
Cost Management System for ARCHIV-IT

Comprehensive API usage tracking, estimation, and budget management for:
- Vision Analysis (Claude Vision API)
- Audio Transcription (Whisper API)
- Video Processing (Frame-by-frame analysis)
- Document Processing (PDF, DOCX with embedded media)
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

# Pricing constants (updated 2025-01-03)
class ServiceType(Enum):
    VISION_HAIKU = "vision_haiku"
    VISION_SONNET = "vision_sonnet"
    VISION_OPUS = "vision_opus"
    TRANSCRIPTION_WHISPER = "transcription_whisper"
    VIDEO_ANALYSIS = "video_analysis"
    EMBEDDINGS = "embeddings"  # Free - local processing

# API Pricing per service
PRICING = {
    # Vision API costs (per image)
    ServiceType.VISION_HAIKU: {
        'cost_per_image': 0.003,
        'cost_per_1k_tokens': 0.001,
        'max_tokens_per_image': 1600,  # Typical for high-res
        'name': 'Claude 3.5 Haiku Vision'
    },
    ServiceType.VISION_SONNET: {
        'cost_per_image': 0.015,
        'cost_per_1k_tokens': 0.003,
        'max_tokens_per_image': 1600,
        'name': 'Claude 3.5 Sonnet Vision'
    },
    ServiceType.VISION_OPUS: {
        'cost_per_image': 0.075,
        'cost_per_1k_tokens': 0.015,
        'max_tokens_per_image': 1600,
        'name': 'Claude 3 Opus Vision'
    },
    # Audio transcription (per minute)
    ServiceType.TRANSCRIPTION_WHISPER: {
        'cost_per_minute': 0.006,
        'name': 'Whisper API'
    },
    # Video analysis (per frame)
    ServiceType.VIDEO_ANALYSIS: {
        'cost_per_frame': 0.003,
        'default_frames_per_video': 10,
        'max_frames_per_video': 60,
        'name': 'Video Frame Analysis'
    },
    # Embeddings (free - local)
    ServiceType.EMBEDDINGS: {
        'cost_per_document': 0.0,
        'name': 'Local Embeddings (Free)'
    }
}

@dataclass
class CostEstimate:
    """Cost estimation for a processing job"""
    service_type: str
    item_count: int
    unit_cost: float
    total_cost: float
    units: str  # 'images', 'minutes', 'frames', etc.
    details: Dict = None

@dataclass
class ProcessingJob:
    """Record of actual API usage"""
    job_id: str
    timestamp: datetime
    service_type: str
    item_count: int
    actual_cost: float
    document_id: Optional[str] = None
    metadata: Dict = None

class CostManager:
    """Manages API cost tracking, estimation, and budget enforcement"""

    def __init__(self, db_path: str = "db/cost_tracking.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize cost tracking database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Jobs table - actual API usage
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                service_type TEXT NOT NULL,
                item_count INTEGER NOT NULL,
                actual_cost REAL NOT NULL,
                document_id TEXT,
                metadata TEXT
            )
        ''')

        # Budget table - user-defined budgets
        c.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                period TEXT PRIMARY KEY,  -- 'daily', 'weekly', 'monthly'
                limit_amount REAL NOT NULL,
                alert_threshold REAL DEFAULT 0.8,
                created_at TEXT NOT NULL
            )
        ''')

        # Cache table - track processed items to avoid reprocessing
        c.execute('''
            CREATE TABLE IF NOT EXISTS processed_cache (
                content_hash TEXT PRIMARY KEY,
                service_type TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                document_id TEXT,
                cost REAL
            )
        ''')

        conn.commit()
        conn.close()

    def estimate_web_import(self,
                           url: str,
                           image_count: int,
                           audio_files: List[Dict],
                           video_files: List[Dict],
                           vision_model: str = 'haiku',
                           enable_vision: bool = True,
                           enable_transcription: bool = True,
                           enable_video: bool = True) -> Dict:
        """
        Deep cost estimation for web import

        Args:
            url: URL being imported
            image_count: Number of images found
            audio_files: List of {url, estimated_duration_minutes}
            video_files: List of {url, estimated_duration_seconds}
            vision_model: 'haiku', 'sonnet', or 'opus'
            enable_vision: Process images with vision API
            enable_transcription: Transcribe audio files
            enable_video: Analyze video frames

        Returns:
            Detailed cost breakdown with optimization suggestions
        """
        estimates = []
        total_cost = 0.0

        # Vision API costs
        if enable_vision and image_count > 0:
            service_key = ServiceType[f'VISION_{vision_model.upper()}']
            pricing = PRICING[service_key]

            # Check cache for already-processed images
            cached_count = self._count_cached_images(url)
            new_images = max(0, image_count - cached_count)

            cost = new_images * pricing['cost_per_image']

            estimates.append(CostEstimate(
                service_type=service_key.value,
                item_count=new_images,
                unit_cost=pricing['cost_per_image'],
                total_cost=cost,
                units='images',
                details={
                    'model': pricing['name'],
                    'total_images': image_count,
                    'cached_images': cached_count,
                    'new_images': new_images,
                    'cache_savings': cached_count * pricing['cost_per_image']
                }
            ))
            total_cost += cost

        # Audio transcription costs
        if enable_transcription and audio_files:
            pricing = PRICING[ServiceType.TRANSCRIPTION_WHISPER]
            total_minutes = sum(f.get('estimated_duration_minutes', 3) for f in audio_files)
            cost = total_minutes * pricing['cost_per_minute']

            estimates.append(CostEstimate(
                service_type=ServiceType.TRANSCRIPTION_WHISPER.value,
                item_count=len(audio_files),
                unit_cost=pricing['cost_per_minute'],
                total_cost=cost,
                units='minutes',
                details={
                    'total_minutes': total_minutes,
                    'avg_minutes_per_file': total_minutes / len(audio_files) if audio_files else 0,
                    'file_count': len(audio_files)
                }
            ))
            total_cost += cost

        # Video analysis costs
        if enable_video and video_files:
            pricing = PRICING[ServiceType.VIDEO_ANALYSIS]
            frames_per_video = pricing['default_frames_per_video']
            total_frames = len(video_files) * frames_per_video
            cost = total_frames * pricing['cost_per_frame']

            estimates.append(CostEstimate(
                service_type=ServiceType.VIDEO_ANALYSIS.value,
                item_count=len(video_files),
                unit_cost=pricing['cost_per_frame'],
                total_cost=cost,
                units='frames',
                details={
                    'total_frames': total_frames,
                    'frames_per_video': frames_per_video,
                    'video_count': len(video_files)
                }
            ))
            total_cost += cost

        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(estimates, total_cost)

        # Check budget status
        budget_status = self._check_budget_status(total_cost)

        return {
            'estimates': [asdict(e) for e in estimates],
            'total_cost': total_cost,
            'total_items': sum(e.item_count for e in estimates),
            'suggestions': suggestions,
            'budget_status': budget_status,
            'timestamp': datetime.now().isoformat()
        }

    def estimate_file_upload(self, files: List[Dict]) -> Dict:
        """
        Estimate costs for direct file uploads

        Args:
            files: List of {path, type, size_bytes, duration_seconds (for audio/video)}

        Returns:
            Cost breakdown
        """
        estimates = []
        total_cost = 0.0

        for file_info in files:
            file_type = file_info.get('type', '').lower()
            size_bytes = file_info.get('size_bytes', 0)

            if file_type in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                # Image file
                pricing = PRICING[ServiceType.VISION_HAIKU]
                # Adjust cost based on resolution/size
                resolution_multiplier = self._estimate_resolution_multiplier(size_bytes)
                cost = pricing['cost_per_image'] * resolution_multiplier

                estimates.append(CostEstimate(
                    service_type=ServiceType.VISION_HAIKU.value,
                    item_count=1,
                    unit_cost=cost,
                    total_cost=cost,
                    units='images',
                    details={
                        'filename': file_info.get('filename'),
                        'size_mb': size_bytes / (1024 * 1024),
                        'resolution_multiplier': resolution_multiplier
                    }
                ))
                total_cost += cost

            elif file_type in ['mp3', 'wav', 'm4a', 'aac', 'ogg']:
                # Audio file
                pricing = PRICING[ServiceType.TRANSCRIPTION_WHISPER]
                duration_minutes = file_info.get('duration_seconds', 0) / 60
                # If duration unknown, estimate from file size (rough: 1MB ≈ 1 min for compressed)
                if duration_minutes == 0:
                    duration_minutes = (size_bytes / (1024 * 1024))

                cost = duration_minutes * pricing['cost_per_minute']

                estimates.append(CostEstimate(
                    service_type=ServiceType.TRANSCRIPTION_WHISPER.value,
                    item_count=1,
                    unit_cost=pricing['cost_per_minute'],
                    total_cost=cost,
                    units='minutes',
                    details={
                        'filename': file_info.get('filename'),
                        'duration_minutes': duration_minutes,
                        'size_mb': size_bytes / (1024 * 1024),
                        'estimated': file_info.get('duration_seconds') == 0
                    }
                ))
                total_cost += cost

            elif file_type in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
                # Video file
                pricing = PRICING[ServiceType.VIDEO_ANALYSIS]
                duration_seconds = file_info.get('duration_seconds', 10)
                # Sample 1 frame per second, max 60 frames
                frames = min(duration_seconds, pricing['max_frames_per_video'])
                cost = frames * pricing['cost_per_frame']

                estimates.append(CostEstimate(
                    service_type=ServiceType.VIDEO_ANALYSIS.value,
                    item_count=1,
                    unit_cost=pricing['cost_per_frame'],
                    total_cost=cost,
                    units='frames',
                    details={
                        'filename': file_info.get('filename'),
                        'duration_seconds': duration_seconds,
                        'frames_to_analyze': frames,
                        'size_mb': size_bytes / (1024 * 1024)
                    }
                ))
                total_cost += cost

        suggestions = self._generate_optimization_suggestions(estimates, total_cost)
        budget_status = self._check_budget_status(total_cost)

        return {
            'estimates': [asdict(e) for e in estimates],
            'total_cost': total_cost,
            'total_items': len(files),
            'suggestions': suggestions,
            'budget_status': budget_status,
            'timestamp': datetime.now().isoformat()
        }

    def record_job(self, service_type: str, item_count: int, cost: float,
                   document_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Record actual API usage for tracking"""
        job_id = hashlib.md5(f"{datetime.now().isoformat()}{service_type}".encode()).hexdigest()[:12]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO jobs (job_id, timestamp, service_type, item_count, actual_cost, document_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, datetime.now().isoformat(), service_type, item_count, cost, document_id,
              json.dumps(metadata) if metadata else None))
        conn.commit()
        conn.close()

    def get_usage_stats(self, period: str = 'monthly') -> Dict:
        """Get usage statistics for a period"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Calculate date range
        now = datetime.now()
        if period == 'daily':
            start_date = now - timedelta(days=1)
        elif period == 'weekly':
            start_date = now - timedelta(weeks=1)
        else:  # monthly
            start_date = now - timedelta(days=30)

        c.execute('''
            SELECT service_type, COUNT(*), SUM(actual_cost), SUM(item_count)
            FROM jobs
            WHERE timestamp >= ?
            GROUP BY service_type
        ''', (start_date.isoformat(),))

        results = c.fetchall()
        conn.close()

        stats = {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': now.isoformat(),
            'by_service': {},
            'total_cost': 0.0,
            'total_jobs': 0
        }

        for service, job_count, total_cost, item_count in results:
            stats['by_service'][service] = {
                'job_count': job_count,
                'total_cost': total_cost,
                'item_count': item_count
            }
            stats['total_cost'] += total_cost
            stats['total_jobs'] += job_count

        return stats

    def set_budget(self, period: str, limit: float, alert_threshold: float = 0.8):
        """Set budget limit for a period"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO budgets (period, limit_amount, alert_threshold, created_at)
            VALUES (?, ?, ?, ?)
        ''', (period, limit, alert_threshold, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def _check_budget_status(self, estimated_cost: float) -> Dict:
        """Check if operation fits within budget"""
        stats = self.get_usage_stats('monthly')

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT limit_amount, alert_threshold FROM budgets WHERE period = ?', ('monthly',))
        result = c.fetchone()
        conn.close()

        if not result:
            return {
                'has_budget': False,
                'within_budget': True,
                'message': 'No budget set'
            }

        limit, threshold = result
        current_spent = stats['total_cost']
        projected_total = current_spent + estimated_cost

        return {
            'has_budget': True,
            'limit': limit,
            'current_spent': current_spent,
            'estimated_cost': estimated_cost,
            'projected_total': projected_total,
            'remaining': limit - projected_total,
            'within_budget': projected_total <= limit,
            'approaching_limit': projected_total >= (limit * threshold),
            'percent_used': (projected_total / limit) * 100,
            'message': self._generate_budget_message(projected_total, limit, threshold)
        }

    def _generate_budget_message(self, projected: float, limit: float, threshold: float) -> str:
        """Generate human-readable budget status message"""
        percent = (projected / limit) * 100

        if projected > limit:
            return f"⚠️ Budget exceeded! ${projected:.2f} > ${limit:.2f} limit"
        elif projected >= (limit * threshold):
            return f"⚡ Approaching budget limit: ${projected:.2f} / ${limit:.2f} ({percent:.1f}%)"
        else:
            return f"✓ Within budget: ${projected:.2f} / ${limit:.2f} ({percent:.1f}%)"

    def _generate_optimization_suggestions(self, estimates: List[CostEstimate], total_cost: float) -> List[str]:
        """Generate cost optimization suggestions"""
        suggestions = []

        # Suggest cheaper vision model if using Opus/Sonnet
        vision_estimates = [e for e in estimates if 'vision' in e.service_type.lower()]
        if vision_estimates:
            for est in vision_estimates:
                if 'opus' in est.service_type.lower():
                    haiku_cost = est.item_count * PRICING[ServiceType.VISION_HAIKU]['cost_per_image']
                    savings = est.total_cost - haiku_cost
                    suggestions.append(
                        f"💡 Switch to Haiku model for vision: Save ${savings:.2f} ({est.item_count} images)"
                    )
                elif 'sonnet' in est.service_type.lower():
                    haiku_cost = est.item_count * PRICING[ServiceType.VISION_HAIKU]['cost_per_image']
                    savings = est.total_cost - haiku_cost
                    if savings > 0.10:  # Only suggest if significant savings
                        suggestions.append(
                            f"💡 Consider Haiku model for simpler images: Save ${savings:.2f}"
                        )

        # Suggest batch processing for large jobs
        if total_cost > 10.0:
            suggestions.append(
                "📦 Consider batch processing: Queue large jobs during off-peak hours to monitor costs"
            )

        # Suggest cache benefits
        for est in estimates:
            if est.details and est.details.get('cached_images', 0) > 0:
                savings = est.details['cache_savings']
                suggestions.append(
                    f"✨ Cache saved ${savings:.2f} on {est.details['cached_images']} already-processed images"
                )

        return suggestions

    def _count_cached_images(self, url: str) -> int:
        """Count how many images from this URL are already processed"""
        # This would check the processed_cache table
        # For now, return 0 (not implemented)
        return 0

    def _estimate_resolution_multiplier(self, size_bytes: int) -> float:
        """Estimate resolution multiplier based on file size"""
        # Higher resolution images have more tokens = higher cost
        size_mb = size_bytes / (1024 * 1024)

        if size_mb < 0.5:
            return 0.8  # Small image, fewer tokens
        elif size_mb < 2:
            return 1.0  # Normal size
        elif size_mb < 5:
            return 1.2  # Large image, more tokens
        else:
            return 1.5  # Very large, maximum tokens


# Global instance
cost_manager = CostManager()
