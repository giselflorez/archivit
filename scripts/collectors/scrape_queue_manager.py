#!/usr/bin/env python3
"""
Scrape Queue Manager - Handle large scraping jobs with pause/resume capability

Supports:
- Twitter archive processing (scroll back to earliest posts)
- Social media timeline scraping
- Cost estimation and warnings
- Pause/resume at any point
- Buffer management for API rate limits
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ScrapeQueueManager:
    """Manages scraping queues with pause/resume capability"""

    QUEUE_FILE = Path("knowledge_base/scrape_queue.json")

    # Cost estimates per operation (in API calls or processing units)
    COST_ESTIMATES = {
        'twitter_archive_month': 0.01,      # Per month of tweets
        'twitter_api_page': 0.05,           # Per API call (if using API)
        'embedding_generation': 0.001,      # Per document embedded
        'image_analysis': 0.02,             # Per image analyzed with vision
    }

    # Rate limits and buffer settings
    RATE_LIMITS = {
        'twitter_archive': {
            'items_per_batch': 500,         # Process 500 tweets per batch
            'pause_after_batches': 10,      # Pause checkpoint every 10 batches
            'cooldown_seconds': 0,          # No cooldown for local archive
        },
        'twitter_api': {
            'items_per_batch': 100,
            'pause_after_batches': 5,
            'cooldown_seconds': 60,         # Rate limit cooldown
        },
        'default': {
            'items_per_batch': 100,
            'pause_after_batches': 5,
            'cooldown_seconds': 30,
        }
    }

    def __init__(self):
        self.queue_file = self.QUEUE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_queue()

    def _load_queue(self):
        """Load existing queue from disk"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    self.queue_data = json.load(f)
            except:
                self.queue_data = {'jobs': {}, 'history': []}
        else:
            self.queue_data = {'jobs': {}, 'history': []}

    def _save_queue(self):
        """Save queue to disk"""
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue_data, f, indent=2, default=str)

    def _generate_job_id(self, source: str, identifier: str) -> str:
        """Generate unique job ID"""
        content = f"{source}_{identifier}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def estimate_cost(self, source_type: str, item_count: int,
                      include_embeddings: bool = True,
                      include_vision: bool = False) -> Dict:
        """
        Estimate processing cost for a scraping job

        Returns dict with cost breakdown and warnings
        """
        costs = {}
        warnings = []

        # Base processing cost
        if source_type == 'twitter_archive':
            # Estimate months from tweet count (avg ~100 tweets/month for active user)
            estimated_months = max(1, item_count // 100)
            costs['archive_processing'] = estimated_months * self.COST_ESTIMATES['twitter_archive_month']

            if item_count > 5000:
                warnings.append(f"Large archive: {item_count:,} tweets will take ~{item_count // 500} batches")
            if item_count > 20000:
                warnings.append("Very large archive. Consider processing in stages.")

        elif source_type == 'twitter_api':
            # API calls needed
            pages_needed = (item_count // 100) + 1
            costs['api_calls'] = pages_needed * self.COST_ESTIMATES['twitter_api_page']
            warnings.append(f"API scraping requires ~{pages_needed} API calls")

        # Embedding costs
        if include_embeddings:
            # ~1 document per 100 tweets (grouped by month)
            doc_count = max(1, item_count // 100)
            costs['embeddings'] = doc_count * self.COST_ESTIMATES['embedding_generation']

        # Vision analysis costs
        if include_vision:
            # Estimate 20% of tweets have images
            image_count = int(item_count * 0.2)
            costs['vision_analysis'] = image_count * self.COST_ESTIMATES['image_analysis']
            warnings.append(f"Vision analysis on ~{image_count} images adds significant cost")

        total_cost = sum(costs.values())

        # Time estimates
        rate_config = self.RATE_LIMITS.get(source_type, self.RATE_LIMITS['default'])
        batches_needed = (item_count // rate_config['items_per_batch']) + 1
        estimated_minutes = (batches_needed * rate_config['cooldown_seconds']) / 60

        return {
            'costs': costs,
            'total_cost': total_cost,
            'cost_tier': self._get_cost_tier(total_cost),
            'warnings': warnings,
            'item_count': item_count,
            'batches_needed': batches_needed,
            'estimated_minutes': estimated_minutes,
            'can_pause': True,
            'pause_checkpoints': batches_needed // rate_config['pause_after_batches']
        }

    def _get_cost_tier(self, cost: float) -> str:
        """Categorize cost into tiers for user display"""
        if cost < 0.1:
            return 'minimal'
        elif cost < 0.5:
            return 'low'
        elif cost < 2.0:
            return 'moderate'
        elif cost < 10.0:
            return 'high'
        else:
            return 'very_high'

    def create_job(self, source_type: str, source_path: str,
                   username: str, options: Dict = None) -> Dict:
        """
        Create a new scraping job

        Args:
            source_type: 'twitter_archive', 'twitter_api', etc.
            source_path: Path to archive or API endpoint
            username: Username associated with data
            options: Additional options (include_embeddings, include_vision, etc.)

        Returns:
            Job info dict with ID and status
        """
        options = options or {}
        job_id = self._generate_job_id(source_type, username)

        # Analyze source to get item count
        item_count = self._count_items(source_type, source_path)

        # Get cost estimate
        estimate = self.estimate_cost(
            source_type,
            item_count,
            options.get('include_embeddings', True),
            options.get('include_vision', False)
        )

        job = {
            'id': job_id,
            'source_type': source_type,
            'source_path': str(source_path),
            'username': username,
            'options': options,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'progress': {
                'total_items': item_count,
                'processed_items': 0,
                'current_batch': 0,
                'total_batches': estimate['batches_needed'],
                'last_checkpoint': None,
                'checkpoint_data': None,  # Stores resume point
            },
            'estimate': estimate,
            'results': {
                'documents_created': 0,
                'errors': [],
                'processed_periods': []
            }
        }

        self.queue_data['jobs'][job_id] = job
        self._save_queue()

        logger.info(f"Created job {job_id}: {item_count} items from {source_type}")

        return job

    def _count_items(self, source_type: str, source_path: str) -> int:
        """Count items in source to estimate processing"""
        if source_type == 'twitter_archive':
            return self._count_twitter_archive_items(source_path)
        return 0

    def _count_twitter_archive_items(self, archive_path: str) -> int:
        """Count tweets in Twitter archive"""
        import re

        path = Path(archive_path)
        if not path.exists():
            return 0

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove JS wrapper
            content = re.sub(r'^window\.YTD\.(tweets?|tweet)\.part\d+\s*=\s*', '', content)
            content = content.strip()
            if content.endswith(';'):
                content = content[:-1]

            data = json.loads(content)
            return len(data)
        except Exception as e:
            logger.error(f"Error counting tweets: {e}")
            return 0

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        return self.queue_data['jobs'].get(job_id)

    def get_pending_jobs(self) -> List[Dict]:
        """Get all pending or paused jobs"""
        return [
            job for job in self.queue_data['jobs'].values()
            if job['status'] in ('pending', 'paused', 'in_progress')
        ]

    def get_resumable_jobs(self, username: str = None) -> List[Dict]:
        """Get jobs that can be resumed"""
        jobs = [
            job for job in self.queue_data['jobs'].values()
            if job['status'] == 'paused' and job['progress']['checkpoint_data']
        ]
        if username:
            jobs = [j for j in jobs if j['username'] == username]
        return jobs

    def pause_job(self, job_id: str, checkpoint_data: Dict = None) -> bool:
        """
        Pause a job with optional checkpoint data for resume

        Args:
            job_id: Job to pause
            checkpoint_data: Data needed to resume (e.g., last processed month)
        """
        job = self.queue_data['jobs'].get(job_id)
        if not job:
            return False

        job['status'] = 'paused'
        job['updated_at'] = datetime.now().isoformat()
        job['progress']['last_checkpoint'] = datetime.now().isoformat()

        if checkpoint_data:
            job['progress']['checkpoint_data'] = checkpoint_data

        self._save_queue()
        logger.info(f"Paused job {job_id} at batch {job['progress']['current_batch']}")
        return True

    def resume_job(self, job_id: str) -> Optional[Dict]:
        """
        Resume a paused job

        Returns:
            Checkpoint data needed to continue processing
        """
        job = self.queue_data['jobs'].get(job_id)
        if not job or job['status'] != 'paused':
            return None

        job['status'] = 'in_progress'
        job['updated_at'] = datetime.now().isoformat()
        self._save_queue()

        logger.info(f"Resumed job {job_id} from batch {job['progress']['current_batch']}")

        return {
            'job': job,
            'checkpoint': job['progress']['checkpoint_data'],
            'start_from_item': job['progress']['processed_items'],
            'start_from_batch': job['progress']['current_batch']
        }

    def update_progress(self, job_id: str, processed_items: int,
                       current_batch: int, checkpoint_data: Dict = None):
        """Update job progress"""
        job = self.queue_data['jobs'].get(job_id)
        if not job:
            return

        job['progress']['processed_items'] = processed_items
        job['progress']['current_batch'] = current_batch
        job['updated_at'] = datetime.now().isoformat()

        if checkpoint_data:
            job['progress']['checkpoint_data'] = checkpoint_data

        self._save_queue()

    def complete_job(self, job_id: str, results: Dict = None):
        """Mark job as complete"""
        job = self.queue_data['jobs'].get(job_id)
        if not job:
            return

        job['status'] = 'completed'
        job['completed_at'] = datetime.now().isoformat()
        job['updated_at'] = datetime.now().isoformat()

        if results:
            job['results'].update(results)

        # Move to history
        self.queue_data['history'].append({
            'job_id': job_id,
            'completed_at': job['completed_at'],
            'summary': {
                'source_type': job['source_type'],
                'items_processed': job['progress']['processed_items'],
                'documents_created': job['results']['documents_created']
            }
        })

        self._save_queue()
        logger.info(f"Completed job {job_id}")

    def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        job = self.queue_data['jobs'].get(job_id)
        if not job:
            return

        job['status'] = 'failed'
        job['updated_at'] = datetime.now().isoformat()
        job['results']['errors'].append({
            'time': datetime.now().isoformat(),
            'error': error
        })

        self._save_queue()
        logger.error(f"Job {job_id} failed: {error}")

    def get_queue_status(self) -> Dict:
        """Get overall queue status"""
        jobs = self.queue_data['jobs']

        return {
            'total_jobs': len(jobs),
            'pending': len([j for j in jobs.values() if j['status'] == 'pending']),
            'in_progress': len([j for j in jobs.values() if j['status'] == 'in_progress']),
            'paused': len([j for j in jobs.values() if j['status'] == 'paused']),
            'completed': len([j for j in jobs.values() if j['status'] == 'completed']),
            'failed': len([j for j in jobs.values() if j['status'] == 'failed']),
            'resumable': len(self.get_resumable_jobs()),
            'history_count': len(self.queue_data['history'])
        }


def process_twitter_archive_with_queue(archive_path: str, username: str,
                                       queue_manager: ScrapeQueueManager = None,
                                       job_id: str = None,
                                       resume_from: Dict = None) -> Dict:
    """
    Process Twitter archive with queue management and pause/resume support

    Scrolls through entire archive from newest to oldest posts.

    Args:
        archive_path: Path to tweets.js
        username: Twitter username
        queue_manager: Optional queue manager for progress tracking
        job_id: Existing job ID if resuming
        resume_from: Checkpoint data if resuming

    Returns:
        Processing results
    """
    import re
    from collectors.twitter_collector import (
        group_tweets_by_month,
        create_markdown_for_tweets,
        save_twitter_content
    )

    if queue_manager is None:
        queue_manager = ScrapeQueueManager()

    # Create or resume job
    if job_id and resume_from:
        # Resuming existing job
        job = queue_manager.get_job(job_id)
        start_from_period = resume_from.get('last_processed_period')
        processed_periods = set(resume_from.get('processed_periods', []))
    else:
        # New job
        job = queue_manager.create_job('twitter_archive', archive_path, username)
        job_id = job['id']
        start_from_period = None
        processed_periods = set()

    # Load and parse archive
    print(f"\n{'='*60}")
    print(f"Processing Twitter Archive: @{username}")
    print(f"Job ID: {job_id}")
    print(f"{'='*60}\n")

    path = Path(archive_path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'^window\.YTD\.(tweets?|tweet)\.part\d+\s*=\s*', '', content)
    content = content.strip()
    if content.endswith(';'):
        content = content[:-1]

    tweets = json.loads(content)
    tweets = [item.get('tweet', item) for item in tweets]

    # Group by month (sorted newest first to scroll back through history)
    grouped = group_tweets_by_month(tweets)
    periods = sorted(grouped.keys(), reverse=True)  # Newest first

    print(f"Found {len(tweets)} tweets across {len(periods)} periods")
    print(f"Date range: {periods[-1] if periods else 'N/A'} to {periods[0] if periods else 'N/A'}")

    # If resuming, skip already processed periods
    if start_from_period:
        try:
            start_idx = periods.index(start_from_period) + 1
            periods = periods[start_idx:]
            print(f"\nResuming from period: {start_from_period}")
            print(f"Remaining periods: {len(periods)}")
        except ValueError:
            pass

    rate_config = queue_manager.RATE_LIMITS['twitter_archive']
    batch_count = 0
    processed_items = job['progress']['processed_items'] if job else 0
    docs_created = job['results']['documents_created'] if job else 0

    results = {
        'processed_periods': list(processed_periods),
        'documents_created': docs_created,
        'errors': []
    }

    try:
        # Process each period (scrolling back through history)
        for period_idx, period in enumerate(periods):
            period_tweets = grouped[period]

            print(f"\n[{period_idx + 1}/{len(periods)}] Processing {period}: {len(period_tweets)} tweets")

            # Create markdown document
            markdown, doc_id, subject = create_markdown_for_tweets(
                period_tweets, period, username
            )

            # Save
            filepath = save_twitter_content(markdown, period_tweets, subject, doc_id)

            processed_items += len(period_tweets)
            docs_created += 1
            processed_periods.add(period)
            results['processed_periods'].append(period)
            results['documents_created'] = docs_created

            batch_count += 1

            # Update progress
            queue_manager.update_progress(
                job_id,
                processed_items,
                batch_count,
                checkpoint_data={
                    'last_processed_period': period,
                    'processed_periods': list(processed_periods)
                }
            )

            print(f"  Created: {filepath}")
            print(f"  Progress: {processed_items}/{len(tweets)} tweets")

            # Check for pause point
            if batch_count % rate_config['pause_after_batches'] == 0:
                # This is a checkpoint - job can be paused here
                print(f"\n  [Checkpoint] Batch {batch_count} complete. Safe to pause.")

        # Complete the job
        queue_manager.complete_job(job_id, results)

        print(f"\n{'='*60}")
        print(f"Archive Processing Complete!")
        print(f"{'='*60}")
        print(f"Total tweets: {processed_items}")
        print(f"Documents created: {docs_created}")
        print(f"Periods covered: {len(processed_periods)}")

    except KeyboardInterrupt:
        # User interrupted - pause job
        print(f"\n\nProcessing interrupted. Pausing job...")
        queue_manager.pause_job(job_id, {
            'last_processed_period': period if 'period' in dir() else None,
            'processed_periods': list(processed_periods)
        })
        print(f"Job {job_id} paused. Run again to resume.")
        results['status'] = 'paused'

    except Exception as e:
        queue_manager.fail_job(job_id, str(e))
        results['status'] = 'failed'
        results['error'] = str(e)
        raise

    return results


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage scraping queue")
    subparsers = parser.add_subparsers(dest='command')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show queue status')

    # List command
    list_parser = subparsers.add_parser('list', help='List jobs')
    list_parser.add_argument('--status', choices=['pending', 'paused', 'completed', 'all'], default='all')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process Twitter archive')
    process_parser.add_argument('archive_path', help='Path to tweets.js')
    process_parser.add_argument('--username', default='founder', help='Twitter username')

    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume paused job')
    resume_parser.add_argument('job_id', help='Job ID to resume')

    # Estimate command
    estimate_parser = subparsers.add_parser('estimate', help='Estimate processing cost')
    estimate_parser.add_argument('archive_path', help='Path to tweets.js')

    args = parser.parse_args()

    qm = ScrapeQueueManager()

    if args.command == 'status':
        status = qm.get_queue_status()
        print("\nQueue Status:")
        print(f"  Total jobs: {status['total_jobs']}")
        print(f"  Pending: {status['pending']}")
        print(f"  In Progress: {status['in_progress']}")
        print(f"  Paused: {status['paused']} ({status['resumable']} resumable)")
        print(f"  Completed: {status['completed']}")
        print(f"  Failed: {status['failed']}")

    elif args.command == 'list':
        jobs = list(qm.queue_data['jobs'].values())
        if args.status != 'all':
            jobs = [j for j in jobs if j['status'] == args.status]

        print(f"\nJobs ({len(jobs)}):")
        for job in jobs:
            progress = job['progress']
            print(f"\n  {job['id']} [{job['status']}]")
            print(f"    Source: {job['source_type']} - @{job['username']}")
            print(f"    Progress: {progress['processed_items']}/{progress['total_items']}")
            if job['status'] == 'paused':
                print(f"    Resume from: {progress['checkpoint_data'].get('last_processed_period', 'start')}")

    elif args.command == 'process':
        results = process_twitter_archive_with_queue(args.archive_path, args.username, qm)

    elif args.command == 'resume':
        resume_data = qm.resume_job(args.job_id)
        if resume_data:
            job = resume_data['job']
            results = process_twitter_archive_with_queue(
                job['source_path'],
                job['username'],
                qm,
                job_id=args.job_id,
                resume_from=resume_data['checkpoint']
            )
        else:
            print(f"Cannot resume job {args.job_id}")

    elif args.command == 'estimate':
        count = qm._count_twitter_archive_items(args.archive_path)
        estimate = qm.estimate_cost('twitter_archive', count)

        print(f"\nCost Estimate for {args.archive_path}:")
        print(f"  Items: {estimate['item_count']:,}")
        print(f"  Batches: {estimate['batches_needed']}")
        print(f"  Est. Time: {estimate['estimated_minutes']:.1f} minutes")
        print(f"  Cost Tier: {estimate['cost_tier']}")
        print(f"  Pause Checkpoints: {estimate['pause_checkpoints']}")

        if estimate['warnings']:
            print("\n  Warnings:")
            for w in estimate['warnings']:
                print(f"    - {w}")
    else:
        parser.print_help()
