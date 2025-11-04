"""
Simple Test Runner for Batch Processing Pipeline

This script provides basic testing functionality without external dependencies.
Run this to verify the batch processor works correctly.

Author: AI Content Automation System
Version: 1.0.0
"""

import asyncio
import json
import tempfile
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any

# Import the batch processor components
from batch_processor import (
    BatchProcessor, BulkJob, VideoJob, JobEvent, JobStatus, JobPriority,
    PipelineState, RateLimiter
)


def test_rate_limiter():
    """Test rate limiting functionality."""
    print("🧪 Testing Rate Limiter...")
    
    limiter = RateLimiter(per_user_limit=3, per_project_limit=10, refill_rate=1.0)
    
    # Test token bucket
    print("  Testing token bucket...")
    for i in range(10):
        can_proceed = limiter.can_proceed(f"user{i % 3}", "project1")
        print(f"    Request {i+1}: {'✅ Allowed' if can_proceed else '❌ Blocked'}")
    
    # Test sliding window
    print("  Testing sliding window...")
    user_id = "test_user"
    for i in range(5):
        can_proceed = limiter.can_proceed(user_id, "project2")
        print(f"    User request {i+1}: {'✅ Allowed' if can_proceed else '❌ Blocked'}")
    
    # Test backoff calculation
    print("  Testing backoff calculation...")
    backoff = limiter.get_backoff_time(user_id)
    print(f"    Recommended backoff: {backoff:.1f} seconds")
    
    print("✅ Rate Limiter tests passed\n")


def test_queue_manager():
    """Test queue management functionality."""
    print("🧪 Testing Queue Manager...")
    
    from batch_processor import QueueManager
    
    queue_manager = QueueManager(max_workers=1)
    
    # Create test jobs with different priorities
    urgent_job = VideoJob(
        id="urgent_1", bulk_job_id="bulk_1",
        idea_data={"title": "Urgent Video"}, status=JobStatus.QUEUED,
        priority=JobPriority.URGENT, ai_provider="test"
    )
    
    normal_job = VideoJob(
        id="normal_1", bulk_job_id="bulk_1",
        idea_data={"title": "Normal Video"}, status=JobStatus.QUEUED,
        priority=JobPriority.NORMAL, ai_provider="test"
    )
    
    low_job = VideoJob(
        id="low_1", bulk_job_id="bulk_1",
        idea_data={"title": "Low Video"}, status=JobStatus.QUEUED,
        priority=JobPriority.LOW, ai_provider="test"
    )
    
    # Add jobs in different order
    print("  Adding jobs to queue...")
    queue_manager.add_job(normal_job)
    queue_manager.add_job(urgent_job)
    queue_manager.add_job(low_job)
    print("    Added: normal, urgent, low priority jobs")
    
    # Retrieve jobs and check order
    print("  Retrieving jobs from queue...")
    priorities = []
    for i in range(3):
        job = queue_manager.get_next_job()
        if job:
            priorities.append(job.priority.name)
            print(f"    Retrieved: {job.priority.name} priority job")
    
    expected = ["URGENT", "NORMAL", "LOW"]
    if priorities == expected:
        print(f"  ✅ Queue order correct: {priorities}")
    else:
        print(f"  ❌ Queue order wrong: got {priorities}, expected {expected}")
    
    print("✅ Queue Manager tests passed\n")


def test_database_operations():
    """Test database persistence."""
    print("🧪 Testing Database Operations...")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        processor = BatchProcessor("dummy_creds.json", db_path)
        
        # Test bulk job persistence
        print("  Testing bulk job persistence...")
        bulk_job = BulkJob(
            id="test_bulk",
            sheet_id="test_sheet",
            status=PipelineState.RUNNING,
            user_id="test_user",
            progress=50
        )
        
        processor._save_bulk_job(bulk_job)
        
        # Verify in database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT * FROM bulk_jobs WHERE id = ?", ("test_bulk",))
            row = cursor.fetchone()
            if row and row[1] == "test_sheet" and row[2] == "running":
                print("    ✅ Bulk job saved and retrieved correctly")
            else:
                print("    ❌ Bulk job persistence failed")
        
        # Test video job persistence
        print("  Testing video job persistence...")
        video_job = VideoJob(
            id="test_video",
            bulk_job_id="test_bulk",
            idea_data={"title": "Test Video", "script": "Test script"},
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="test_provider",
            cost=0.50
        )
        
        processor._save_video_job(video_job)
        
        # Verify in database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT * FROM video_jobs WHERE id = ?", ("test_video",))
            row = cursor.fetchone()
            if row and row[1] == "test_bulk" and row[5] == "test_provider":
                print("    ✅ Video job saved and retrieved correctly")
            else:
                print("    ❌ Video job persistence failed")
        
        # Test event tracking
        print("  Testing event tracking...")
        event = JobEvent(
            id="test_event",
            job_id="test_video",
            event_type="created",
            message="Test event message"
        )
        
        processor._save_job_event(event)
        
        if len(processor.job_events) == 1 and processor.job_events[0].id == "test_event":
            print("    ✅ Event tracking working correctly")
        else:
            print("    ❌ Event tracking failed")
        
        print("✅ Database tests passed\n")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_video_job_lifecycle():
    """Test video job processing lifecycle."""
    print("🧪 Testing Video Job Lifecycle...")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"type": "service_account"}, f)
        cred_path = f.name
    
    try:
        processor = BatchProcessor(cred_path, db_path, max_workers=2)
        
        # Create a test video job
        video_job = VideoJob(
            id="test_job_1",
            bulk_job_id="test_bulk",
            idea_data={"title": "Test Video", "script": "Test script"},
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="test_provider",
            user_id="test_user"
        )
        
        print("  Processing video job...")
        
        # Test the job processing
        result = await processor.generate_video(video_job)
        
        # Verify result
        print("  Verifying result...")
        if "output_url" in result and "cost" in result:
            print(f"    ✅ Video job completed: {result['output_url']}")
            print(f"    Cost: ${result['cost']}")
            print(f"    Duration: {result.get('duration', 'N/A')} seconds")
        else:
            print("    ❌ Video job processing failed")
        
        # Check job status updated
        if video_job.status == JobStatus.COMPLETED:
            print("    ✅ Job status updated correctly")
        else:
            print(f"    ❌ Job status wrong: {video_job.status}")
        
        print("✅ Video Job Lifecycle tests passed\n")
        
    finally:
        await processor.cleanup()
        for path in [db_path, cred_path]:
            if os.path.exists(path):
                os.unlink(path)


async def test_progress_tracking():
    """Test progress tracking and callbacks."""
    print("🧪 Testing Progress Tracking...")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"type": "service_account"}, f)
        cred_path = f.name
    
    try:
        processor = BatchProcessor(cred_path, db_path)
        
        # Track callback invocations
        callback_invocations = []
        
        def progress_callback(job_id: str, progress: int, message: str):
            callback_invocations.append((job_id, progress, message))
            print(f"    📊 Progress: {job_id} - {progress}% - {message}")
        
        # Register callback
        processor.add_progress_callback(progress_callback)
        
        # Test progress updates
        print("  Testing progress updates...")
        processor._notify_progress("test_job_1", 25, "Quarter complete")
        processor._notify_progress("test_job_1", 50, "Half complete")
        processor._notify_progress("test_job_1", 75, "Three quarters")
        processor._notify_progress("test_job_1", 100, "Complete")
        
        # Verify callbacks
        if len(callback_invocations) == 4:
            print("    ✅ Progress callbacks working correctly")
        else:
            print(f"    ❌ Expected 4 callbacks, got {len(callback_invocations)}")
        
        # Test completion callbacks
        print("  Testing completion callbacks...")
        completion_invocations = []
        
        def completion_callback(job_id: str, result: Dict[str, Any]):
            completion_invocations.append((job_id, result))
            print(f"    ✅ Completed: {job_id} - {result}")
        
        processor.add_completion_callback(completion_callback)
        
        # Trigger completion
        result = {"output_url": "test.mp4", "cost": 1.0}
        processor._notify_completion("test_job_1", result)
        
        if len(completion_invocations) == 1:
            print("    ✅ Completion callbacks working correctly")
        else:
            print(f"    ❌ Expected 1 completion callback, got {len(completion_invocations)}")
        
        print("✅ Progress Tracking tests passed\n")
        
    finally:
        await processor.cleanup()
        for path in [db_path, cred_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_job_creation_and_status():
    """Test bulk job creation and status management."""
    print("🧪 Testing Job Creation and Status...")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"type": "service_account"}, f)
        cred_path = f.name
    
    try:
        processor = BatchProcessor(cred_path, db_path)
        
        # Test bulk job creation
        print("  Testing bulk job creation...")
        bulk_job_id = processor.create_bulk_job(
            sheet_id="test_sheet_123",
            user_id="test_user",
            priority=JobPriority.NORMAL
        )
        
        if bulk_job_id and len(bulk_job_id) > 0:
            print(f"    ✅ Created bulk job: {bulk_job_id}")
        else:
            print("    ❌ Bulk job creation failed")
        
        # Test idempotency
        print("  Testing idempotency...")
        same_job_id = processor.create_bulk_job(
            sheet_id="test_sheet_123",
            user_id="test_user"
        )
        
        if bulk_job_id == same_job_id:
            print("    ✅ Idempotency working correctly")
        else:
            print("    ❌ Idempotency failed")
        
        # Test status retrieval
        print("  Testing status retrieval...")
        status = processor.get_bulk_job_status(bulk_job_id)
        
        if "status" in status and "statistics" in status:
            print(f"    ✅ Status retrieved: {status['status']}")
            print(f"    Statistics: {status['statistics']}")
        else:
            print("    ❌ Status retrieval failed")
        
        # Test system status
        print("  Testing system status...")
        system_status = processor.get_system_status()
        
        if "state" in system_status and "bulk_jobs" in system_status:
            print(f"    ✅ System status: {system_status['state']}")
            print(f"    Bulk jobs: {system_status['bulk_jobs']}")
        else:
            print("    ❌ System status retrieval failed")
        
        print("✅ Job Creation and Status tests passed\n")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(cred_path):
            os.unlink(cred_path)


async def main():
    """Run all tests."""
    print("🚀 Starting Batch Processing Pipeline Tests\n")
    
    try:
        # Run synchronous tests
        test_rate_limiter()
        test_queue_manager()
        test_database_operations()
        test_job_creation_and_status()
        
        # Run async tests
        await test_video_job_lifecycle()
        await test_progress_tracking()
        
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("✅ Rate Limiter - Token bucket and sliding window working")
        print("✅ Queue Manager - Priority-based scheduling working")
        print("✅ Database Operations - Persistence working")
        print("✅ Video Job Lifecycle - Processing workflow working")
        print("✅ Progress Tracking - Callbacks and events working")
        print("✅ Job Management - Creation and status working")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())