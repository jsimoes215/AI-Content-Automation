#!/usr/bin/env python3
"""
Example usage of the Progress Monitoring System

This script demonstrates how to integrate and use the progress monitoring
system in a real-world bulk content generation application.

Features demonstrated:
- Job lifecycle management
- Real-time progress updates
- WebSocket broadcasting
- Supabase integration
- Error handling and recovery
"""

import asyncio
import json
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the progress monitoring system
from progress_monitor import (
    ProgressMonitor, JobState, VideoState, EventType, 
    JobProgress, VideoProgress
)


class ContentGenerationWorker:
    """
    Simulated content generation worker that processes bulk video jobs.
    This demonstrates how to integrate the progress monitor with actual work.
    """
    
    def __init__(self, monitor: ProgressMonitor):
        self.monitor = monitor
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        
        # Add handlers for demonstration
        self.monitor.add_state_change_handler(self._on_state_change)
        self.monitor.add_progress_handler(self._on_progress_update)
    
    def _on_state_change(self, job_id: str, prior_state, new_state, reason: str):
        """Handle job state changes."""
        print(f"🔄 Job {job_id} state changed: {prior_state.value} → {new_state.value}")
        print(f"   Reason: {reason}")
        
        if new_state in [JobState.COMPLETED, JobState.CANCELED, JobState.FAILED]:
            # Clean up completed job
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def _on_progress_update(self, job_id: str, progress: JobProgress):
        """Handle progress updates."""
        eta_minutes = progress.eta_ms / 1000 / 60 if progress.eta_ms else 0
        print(f"📊 Job {job_id} progress: {progress.percent_complete:.1f}% "
              f"({progress.items_completed}/{progress.items_total} items)")
        if eta_minutes > 0:
            print(f"   ETA: {eta_minutes:.1f} minutes")
        
        if progress.rate_limited:
            print(f"   ⚠️  Rate limited - processing may be delayed")
    
    def create_job(self, title: str, item_count: int, template_id: str = "tpl_001") -> str:
        """
        Create a new bulk content generation job.
        
        Args:
            title: Human-readable job title
            item_count: Number of video items to generate
            template_id: Template to use for generation
            
        Returns:
            Job ID
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # Job creation data
        job_data = {
            'id': job_id,
            'title': title,
            'state': JobState.PENDING.value,
            'items_total': item_count,
            'items_completed': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'items_canceled': 0,
            'items_pending': item_count,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'template_id': template_id,
            'rate_limited': False,
            'processing_deadline_ms': int(item_count * 60000),  # 1 minute per item
            'callback_url': f'https://example.com/webhook/{job_id}'
        }
        
        # Register job with monitor
        self.monitor.register_job(job_id, job_data)
        self.active_jobs[job_id] = job_data
        
        print(f"✅ Created job: {title} ({job_id}) with {item_count} items")
        return job_id
    
    def start_job(self, job_id: str, delay_seconds: int = 2):
        """
        Start processing a job.
        
        Args:
            job_id: Job to start
            delay_seconds: Delay before starting (simulates queue processing)
        """
        if job_id not in self.active_jobs:
            print(f"❌ Job {job_id} not found")
            return
        
        def _start_job():
            time.sleep(delay_seconds)
            
            # Update state to running
            self.monitor.update_job_state(job_id, JobState.RUNNING, "worker_assigned")
            
            # Start processing items
            self._process_job_items(job_id)
        
        # Start in background
        import threading
        thread = threading.Thread(target=_start_job, daemon=True)
        thread.start()
    
    def _process_job_items(self, job_id: str):
        """Process all items in a job."""
        if job_id not in self.active_jobs:
            return
        
        job_data = self.active_jobs[job_id]
        total_items = job_data['items_total']
        
        print(f"🚀 Starting processing of {total_items} items for job {job_id}")
        
        # Create tasks for each item
        items = []
        for i in range(total_items):
            item = {
                'id': f"vid_{job_id}_{i:04d}",
                'row_index': i + 1,
                'title': f"Video {i + 1}: {job_data['title']}",
                'script': f"Content for video {i + 1}",
                'duration': random.randint(30, 120),  # seconds
                'style': random.choice(['modern', 'classic', 'minimal'])
            }
            items.append(item)
        
        # Process items with some delay and failure simulation
        for i, item in enumerate(items):
            # Simulate processing time
            processing_time = random.uniform(1, 5)
            time.sleep(processing_time)
            
            # Simulate occasional failures (5% chance)
            if random.random() < 0.05:
                self._simulate_item_failure(job_id, item)
            else:
                self._simulate_item_completion(job_id, item)
            
            # Update job progress
            job_data['items_completed'] = i + 1
            job_data['state'] = JobState.RUNNING.value
            self.monitor.update_job_progress(job_id, job_data)
            
            # Simulate rate limiting occasionally
            if random.random() < 0.1:
                self._simulate_rate_limiting(job_id)
        
        # Complete the job
        self.monitor.update_job_state(job_id, JobState.COMPLETED, "all_items_processed")
        print(f"🎉 Job {job_id} completed successfully!")
    
    def _simulate_item_completion(self, job_id: str, item: Dict[str, Any]):
        """Simulate successful item completion."""
        video_data = {
            'id': item['id'],
            'state': VideoState.COMPLETED.value,
            'percent_complete': 100.0,
            'row_index': item['row_index'],
            'title': item['title'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'artifacts': [
                {
                    'type': 'video',
                    'content_type': 'video/mp4',
                    'size': random.randint(1000000, 50000000),  # 1-50 MB
                    'url': f'https://storage.example.com/{job_id}/{item["id"]}.mp4'
                },
                {
                    'type': 'thumbnail',
                    'content_type': 'image/jpeg',
                    'size': random.randint(50000, 200000),  # 50-200 KB
                    'url': f'https://storage.example.com/{job_id}/{item["id"]}_thumb.jpg'
                }
            ],
            'errors': []
        }
        
        self.monitor.update_video_progress(job_id, video_data)
        print(f"   ✅ Completed: {item['title']}")
    
    def _simulate_item_failure(self, job_id: str, item: Dict[str, Any]):
        """Simulate item processing failure."""
        video_data = {
            'id': item['id'],
            'state': VideoState.FAILED.value,
            'percent_complete': 0.0,
            'row_index': item['row_index'],
            'title': item['title'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'artifacts': [],
            'errors': [
                {
                    'error_code': 'asset_unavailable',
                    'error_message': 'Required asset file not found',
                    'error_class': 'InputError',
                    'occurred_at': datetime.utcnow().isoformat()
                }
            ]
        }
        
        self.monitor.update_video_progress(job_id, video_data)
        print(f"   ❌ Failed: {item['title']} - Asset unavailable")
    
    def _simulate_rate_limiting(self, job_id: str):
        """Simulate temporary rate limiting."""
        print(f"   🐌 Rate limiting detected for job {job_id}")
        
        # Update job state temporarily
        self.monitor.update_job_state(job_id, JobState.RATE_LIMITED, "quota_exceeded")
        
        # Wait and resume
        def _resume_after_delay():
            time.sleep(random.uniform(2, 8))
            self.monitor.update_job_state(job_id, JobState.RUNNING, "quota_refreshed")
        
        import threading
        thread = threading.Thread(target=_resume_after_delay, daemon=True)
        thread.start()
    
    def cancel_job(self, job_id: str):
        """Cancel a running job."""
        if job_id not in self.active_jobs:
            print(f"❌ Job {job_id} not found")
            return
        
        self.monitor.update_job_state(job_id, JobState.CANCELED, "user_requested")
        print(f"🛑 Canceled job {job_id}")
        
        # Unregister from monitor
        self.monitor.unregister_job(job_id)
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current job status."""
        return self.monitor.get_job_status(job_id) or {}


async def demo_websocket_client(job_id: str, duration: int = 30):
    """
    Simulate a WebSocket client listening to job updates.
    
    Args:
        job_id: Job to monitor
        duration: How long to listen (seconds)
    """
    import websockets
    
    print(f"📱 Starting WebSocket client for job {job_id}")
    
    try:
        # Note: This is a simplified client for demonstration
        # In a real application, you would use the proper WebSocket URL
        uri = f"ws://localhost:8765?job_id={job_id}&token=demo_token"
        
        # In a real scenario, you would connect like this:
        # async with websockets.connect(uri) as websocket:
        #     start_time = time.time()
        #     while time.time() - start_time < duration:
        #         try:
        #             message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
        #             data = json.loads(message)
        #             print(f"📨 WebSocket: {data['type']} - {data.get('data', {})}")
        #         except asyncio.TimeoutError:
        #             continue
        
        # For demo, just show that we would be listening
        print("   (WebSocket client listening for updates...)")
        await asyncio.sleep(duration)
        print("   WebSocket client session completed")
        
    except Exception as e:
        print(f"   WebSocket client error: {e}")


async def run_demo_scenarios():
    """Run various demonstration scenarios."""
    print("🎬 Progress Monitoring System Demo")
    print("=" * 50)
    
    # Initialize the monitoring system
    monitor = ProgressMonitor(
        supabase_url=os.getenv('SUPABASE_URL', 'http://localhost:54321'),
        supabase_key= os.getenv('SUPABASE_ANON_KEY', 'demo_key'),
        ws_host='0.0.0.0',
        ws_port=8765
    )
    
    # Start monitoring
    monitor.start_monitoring()
    print("✅ Progress monitoring system started")
    
    # Create worker
    worker = ContentGenerationWorker(monitor)
    
    try:
        # Demo 1: Small job (fast completion)
        print("\n🚀 Demo 1: Small job with 5 items")
        job1_id = worker.create_job("Product Demo Video", 5, "tpl_demo_001")
        
        # Start WebSocket client for this job
        websocket_task = asyncio.create_task(
            demo_websocket_client(job1_id, duration=20)
        )
        
        # Start the job
        worker.start_job(job1_id, delay_seconds=1)
        
        # Wait for job to complete
        while worker.get_job_status(job1_id) and \
              worker.get_job_status(job1_id)['state'] != 'completed':
            await asyncio.sleep(1)
        
        await websocket_task
        
        # Demo 2: Medium job with some failures
        print("\n🚀 Demo 2: Medium job with 10 items (simulated failures)")
        job2_id = worker.create_job("Marketing Campaign Videos", 10, "tpl_marketing_001")
        
        # Monitor via WebSocket
        websocket_task = asyncio.create_task(
            demo_websocket_client(job2_id, duration=30)
        )
        
        # Start the job
        worker.start_job(job2_id, delay_seconds=2)
        
        # Wait for job to complete
        while worker.get_job_status(job2_id) and \
              worker.get_job_status(job2_id)['state'] not in ['completed', 'failed']:
            await asyncio.sleep(1)
        
        await websocket_task
        
        # Demo 3: Large job with rate limiting
        print("\n🚀 Demo 3: Large job with 20 items (rate limiting simulation)")
        job3_id = worker.create_job("Training Video Series", 20, "tpl_training_001")
        
        # Monitor via WebSocket
        websocket_task = asyncio.create_task(
            demo_websocket_client(job3_id, duration=40)
        )
        
        # Start the job
        worker.start_job(job3_id, delay_seconds=1)
        
        # Demo: Cancel partway through
        await asyncio.sleep(10)
        if worker.get_job_status(job3_id):
            print("\n🛑 Canceling job 3 halfway through...")
            worker.cancel_job(job3_id)
        
        await websocket_task
        
        # Demo 4: Show system statistics
        print("\n📊 System Statistics")
        all_jobs = monitor.get_all_jobs_status()
        print(f"   Total jobs monitored: {len(all_jobs)}")
        print(f"   WebSocket connections: {sum(len(clients) for clients in monitor.websocket_broadcaster.clients.values())}")
        
        # Show job details
        for job_id, job_info in all_jobs.items():
            state = job_info.get('state', 'unknown')
            start_time = job_info.get('start_time', 'unknown')
            print(f"   Job {job_id}: {state} (started: {start_time})")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        # Cleanup
        monitor.stop_monitoring()
        print("\n🛑 Progress monitoring system stopped")


def run_basic_test():
    """Run a basic test without async complications."""
    print("🧪 Running Basic Progress Monitor Test")
    print("=" * 40)
    
    # Initialize monitor
    monitor = ProgressMonitor(
        supabase_url='http://localhost:54321',
        supabase_key='demo_key'
    )
    
    # Add simple handlers
    def on_state_change(job_id, prior_state, new_state, reason):
        print(f"State: {job_id} {prior_state} → {new_state} ({reason})")
    
    def on_progress(job_id, progress):
        print(f"Progress: {job_id} {progress.percent_complete:.1f}% "
              f"({progress.items_completed}/{progress.items_total})")
    
    monitor.add_state_change_handler(on_state_change)
    monitor.add_progress_handler(on_progress)
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Create test job
        job_data = {
            'id': 'test_job_001',
            'state': JobState.PENDING.value,
            'items_total': 10,
            'items_completed': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'items_canceled': 0,
            'created_at': datetime.utcnow().isoformat(),
            'rate_limited': False
        }
        
        monitor.register_job('test_job_001', job_data)
        
        # Simulate job progression
        for i in range(0, 11, 2):
            job_data['items_completed'] = i
            job_data['state'] = JobState.RUNNING.value
            monitor.update_job_progress('test_job_001', job_data)
            
            # Simulate video updates
            if i > 0:
                video_data = {
                    'id': f'vid_{i:03d}',
                    'state': VideoState.COMPLETED.value,
                    'percent_complete': 100.0,
                    'row_index': i,
                    'title': f'Video {i}',
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                monitor.update_video_progress('test_job_001', video_data)
            
            time.sleep(1)
        
        # Complete job
        monitor.update_job_state('test_job_001', JobState.COMPLETED, "test_completed")
        
        print("✅ Basic test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "basic":
        run_basic_test()
    else:
        # Run the full async demo
        asyncio.run(run_demo_scenarios())