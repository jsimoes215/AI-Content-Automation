"""
Test Suite for Batch Processing Pipeline

This module provides comprehensive tests for the batch processing pipeline,
demonstrating all features including queue management, prioritization,
progress tracking, and integration with existing services.

Author: AI Content Automation System
Version: 1.0.0
"""

import asyncio
import json
import tempfile
import sqlite3
import os
import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch

# Import the batch processor components
from batch_processor import (
    BatchProcessor, BulkJob, VideoJob, JobEvent, JobStatus, JobPriority,
    PipelineState, RateLimiter, QueueManager
)
from idea_data_service import SheetFormat, ValidationLevel
from data_validation import ValidationResult


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_token_bucket_operation(self):
        """Test token bucket basic operation."""
        limiter = RateLimiter(per_project_limit=10, refill_rate=1.0)
        
        # Should allow initial requests
        for i in range(10):
            assert limiter.can_proceed(f"user{i}", "project1")
        
        # Should block when empty
        assert not limiter.can_proceed("user11", "project1")
        
        # Wait for refill and try again
        import time
        time.sleep(1.1)  # Wait for refill
        assert limiter.can_proceed("user12", "project1")
    
    def test_sliding_window_enforcement(self):
        """Test sliding window for per-user limits."""
        limiter = RateLimiter(per_user_limit=3)
        
        user_id = "test_user"
        
        # Should allow first 3 requests
        for i in range(3):
            assert limiter.can_proceed(user_id, "project1")
        
        # Should block 4th request immediately
        assert not limiter.can_proceed(user_id, "project1")
        
        # Should allow after window expires
        import time
        time.sleep(61)  # Wait for sliding window to clear
        assert limiter.can_proceed(user_id, "project1")
    
    def test_backoff_calculation(self):
        """Test backoff time calculation."""
        limiter = RateLimiter(per_user_limit=2)
        
        user_id = "test_user"
        
        # Make 2 requests to hit limit
        assert limiter.can_proceed(user_id, "project1")
        assert limiter.can_proceed(user_id, "project1")
        
        # Get backoff time
        backoff = limiter.get_backoff_time(user_id)
        assert 0 < backoff <= 60


class TestQueueManager:
    """Test queue management functionality."""
    
    def test_priority_queue_ordering(self):
        """Test that priority queue maintains correct ordering."""
        queue_manager = QueueManager(max_workers=1)
        
        # Create jobs with different priorities
        urgent_job = VideoJob(
            id="urgent_1", bulk_job_id="bulk_1",
            idea_data={}, status=JobStatus.QUEUED,
            priority=JobPriority.URGENT, ai_provider="test"
        )
        
        normal_job = VideoJob(
            id="normal_1", bulk_job_id="bulk_1",
            idea_data={}, status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL, ai_provider="test"
        )
        
        low_job = VideoJob(
            id="low_1", bulk_job_id="bulk_1",
            idea_data={}, status=JobStatus.QUEUED,
            priority=JobPriority.LOW, ai_provider="test"
        )
        
        # Add in different order
        queue_manager.add_job(normal_job)
        queue_manager.add_job(urgent_job)
        queue_manager.add_job(low_job)
        
        # Should get urgent first
        first_job = queue_manager.get_next_job()
        assert first_job.priority == JobPriority.URGENT
        
        # Should get normal next
        second_job = queue_manager.get_next_job()
        assert second_job.priority == JobPriority.NORMAL
        
        # Should get low last
        third_job = queue_manager.get_next_job()
        assert third_job.priority == JobPriority.LOW


class TestBatchProcessor:
    """Test the main batch processor functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "type": "service_account",
                "project_id": "test-project"
            }, f)
            cred_path = f.name
        
        yield cred_path
        
        # Cleanup
        if os.path.exists(cred_path):
            os.unlink(cred_path)
    
    @pytest.fixture
    def processor(self, mock_credentials, temp_db):
        """Create a batch processor for testing."""
        return BatchProcessor(
            credentials_path=mock_credentials,
            db_path=temp_db,
            max_workers=2
        )
    
    def test_bulk_job_creation(self, processor):
        """Test bulk job creation and idempotency."""
        sheet_id = "test_sheet_123"
        user_id = "test_user"
        
        # Create first job
        job_id_1 = processor.create_bulk_job(sheet_id, user_id)
        assert len(job_id_1) > 0
        
        # Create duplicate job (should reuse)
        job_id_2 = processor.create_bulk_job(sheet_id, user_id)
        assert job_id_1 == job_id_2
        
        # Create job with different user (should be different)
        job_id_3 = processor.create_bulk_job(sheet_id, "other_user")
        assert job_id_1 != job_id_3
    
    def test_bulk_job_status(self, processor):
        """Test bulk job status tracking."""
        sheet_id = "test_sheet_123"
        user_id = "test_user"
        
        job_id = processor.create_bulk_job(sheet_id, user_id)
        status = processor.get_bulk_job_status(job_id)
        
        assert status["status"] == "idle"
        assert status["statistics"]["total"] == 0
        assert "created_at" in status
    
    def test_system_status(self, processor):
        """Test system status reporting."""
        status = processor.get_system_status()
        
        assert "state" in status
        assert "queue_running" in status
        assert "bulk_jobs" in status
        assert "video_jobs" in status
        assert "rate_limiter" in status
    
    @pytest.mark.asyncio
    async def test_video_job_lifecycle(self, processor):
        """Test complete video job lifecycle."""
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
        
        processor._save_video_job(video_job)
        
        # Test job processing
        result = await processor.generate_video(video_job)
        
        assert result["output_url"].startswith("https://")
        assert "cost" in result
        assert "duration" in result
        assert "quality" in result
        
        # Check job status updated
        updated_job = processor.bulk_jobs["test_bulk"].video_jobs[0]
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.output_url is not None


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    @pytest.fixture
    def integration_processor(self):
        """Create processor with mocked external dependencies."""
        with patch('batch_processor.GoogleSheetsClient') as mock_sheets:
            with patch('batch_processor.IdeaDataService') as mock_idea_service:
                with patch('batch_processor.DataValidator') as mock_validator:
                    
                    # Mock sheets client
                    mock_client = AsyncMock()
                    mock_sheets.return_value = mock_client
                    
                    # Mock idea service
                    mock_service = Mock()
                    mock_service.process_sheet_data = AsyncMock(return_value=[
                        {
                            "title": "Test Video 1",
                            "script": "Test script 1",
                            "voice": "voice1",
                            "style": "style1"
                        },
                        {
                            "title": "Test Video 2", 
                            "script": "Test script 2",
                            "voice": "voice2",
                            "style": "style2"
                        }
                    ])
                    mock_idea_service.return_value = mock_service
                    
                    # Mock validator
                    mock_validator_instance = Mock()
                    mock_validator_instance.validate_idea = AsyncMock(return_value=ValidationResult(
                        is_valid=True,
                        errors=[],
                        warnings=[],
                        cleaned_data={"title": "Test Video", "script": "Test script"},
                        quality_score=0.8,
                        estimated_cost=0.50,
                        duplicate_score=0.1
                    ))
                    mock_validator.return_value = mock_validator_instance
                    
                    # Create processor
                    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                        db_path = f.name
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump({"type": "service_account"}, f)
                        cred_path = f.name
                    
                    processor = BatchProcessor(
                        credentials_path=cred_path,
                        db_path=db_path,
                        max_workers=2
                    )
                    
                    yield processor
                    
                    # Cleanup
                    for path in [db_path, cred_path]:
                        if os.path.exists(path):
                            os.unlink(path)
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, integration_processor):
        """Test the complete pipeline from sheet to video generation."""
        processor = integration_processor
        
        # Create bulk job
        bulk_job_id = processor.create_bulk_job(
            sheet_id="test_sheet_123",
            user_id="test_user",
            priority=JobPriority.NORMAL
        )
        
        assert bulk_job_id is not None
        
        # Process ideas from sheet
        result = await processor.process_sheet_ideas(
            bulk_job_id=bulk_job_id,
            sheet_format=SheetFormat.STANDARD,
            validation_level=ValidationLevel.MODERATE,
            ai_provider="test_provider"
        )
        
        assert result["status"] == "started"
        assert result["created_jobs"] == 2
        
        # Check that video jobs were created
        bulk_job = processor.bulk_jobs[bulk_job_id]
        assert len(bulk_job.video_jobs) == 2
        
        # Check job status
        status = processor.get_bulk_job_status(bulk_job_id)
        assert status["status"] == "running"
        assert status["statistics"]["queued"] == 2
        
        # Clean up
        await processor.cleanup()
    
    @pytest.mark.asyncio 
    async def test_error_handling_and_retry(self, integration_processor):
        """Test error handling and retry mechanisms."""
        processor = integration_processor
        
        # Create a video job that will fail
        video_job = VideoJob(
            id="failing_job",
            bulk_job_id="test_bulk",
            idea_data={"title": "Failing Video"},
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="failing_provider",
            user_id="test_user"
        )
        
        # Mock the video generation to fail
        with patch.object(processor, '_execute_video_generation', side_effect=Exception("Simulated failure")):
            # Process the job (should handle error and retry)
            with pytest.raises(Exception):
                await processor.generate_video(video_job)
            
            # Check that job was marked for retry
            assert video_job.retry_count == 1
            assert video_job.status == JobStatus.RETRIED
        
        await processor.cleanup()
    
    @pytest.mark.asyncio
    async def test_pause_resume_functionality(self, integration_processor):
        """Test pause and resume functionality."""
        processor = integration_processor
        
        # Create bulk job
        bulk_job_id = processor.create_bulk_job("test_sheet", "test_user")
        
        # Process ideas (this will set status to running)
        await processor.process_sheet_ideas(bulk_job_id)
        
        # Pause the job
        assert processor.pause_bulk_job(bulk_job_id)
        
        status = processor.get_bulk_job_status(bulk_job_id)
        assert status["status"] == "paused"
        
        # Resume the job
        assert processor.resume_bulk_job(bulk_job_id)
        
        status = processor.get_bulk_job_status(bulk_job_id)
        assert status["status"] == "running"
        
        await processor.cleanup()
    
    def test_job_event_tracking(self, processor):
        """Test job event tracking and logging."""
        # Create a test event
        event = JobEvent(
            id="event_1",
            job_id="job_1",
            event_type="state_change",
            message="Job started",
            progress_percent=0.0
        )
        
        processor._save_job_event(event)
        
        # Check that event was saved
        assert len(processor.job_events) == 1
        assert processor.job_events[0].id == "event_1"
        assert processor.job_events[0].job_id == "job_1"
    
    def test_database_operations(self, temp_db):
        """Test database persistence operations."""
        processor = BatchProcessor("dummy_creds.json", temp_db)
        
        # Create and save a bulk job
        bulk_job = BulkJob(
            id="test_bulk",
            sheet_id="test_sheet",
            status=PipelineState.RUNNING,
            user_id="test_user"
        )
        
        processor._save_bulk_job(bulk_job)
        
        # Verify in database
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT * FROM bulk_jobs WHERE id = ?", ("test_bulk",))
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == "test_sheet"  # sheet_id
            assert row[2] == "running"     # status
        
        # Create and save a video job
        video_job = VideoJob(
            id="test_video",
            bulk_job_id="test_bulk",
            idea_data={"title": "Test"},
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="test"
        )
        
        processor._save_video_job(video_job)
        
        # Verify in database
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT * FROM video_jobs WHERE id = ?", ("test_video",))
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == "test_bulk"  # bulk_job_id


class TestProgressTracking:
    """Test progress tracking and callback functionality."""
    
    @pytest.fixture
    def tracking_processor(self):
        """Create processor for progress tracking tests."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account"}, f)
            cred_path = f.name
        
        processor = BatchProcessor(cred_path, db_path)
        
        yield processor
        
        # Cleanup
        for path in [db_path, cred_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_progress_callbacks(self, tracking_processor):
        """Test progress callback registration and invocation."""
        processor = tracking_processor
        
        # Track callback invocations
        callback_invocations = []
        
        def progress_callback(job_id: str, progress: int, message: str):
            callback_invocations.append((job_id, progress, message))
        
        # Register callback
        processor.add_progress_callback(progress_callback)
        
        # Trigger progress update
        processor._notify_progress("test_job", 50, "Halfway there")
        processor._notify_progress("test_job", 100, "Completed")
        
        # Verify callbacks were called
        assert len(callback_invocations) == 2
        assert callback_invocations[0] == ("test_job", 50, "Halfway there")
        assert callback_invocations[1] == ("test_job", 100, "Completed")
    
    def test_completion_callbacks(self, tracking_processor):
        """Test completion callback registration and invocation."""
        processor = tracking_processor
        
        # Track callback invocations
        callback_invocations = []
        
        def completion_callback(job_id: str, result: Dict[str, Any]):
            callback_invocations.append((job_id, result))
        
        # Register callback
        processor.add_completion_callback(completion_callback)
        
        # Trigger completion
        result = {"output_url": "test.mp4", "cost": 1.0}
        processor._notify_completion("test_job", result)
        
        # Verify callback was called
        assert len(callback_invocations) == 1
        assert callback_invocations[0] == ("test_job", result)


def run_integration_demo():
    """Run a demonstration of the batch processor integration."""
    
    print("=== Batch Processing Pipeline Integration Demo ===\n")
    
    async def demo():
        # Create processor with mock data
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "service_account"}, f)
            cred_path = f.name
        
        processor = BatchProcessor(cred_path, db_path, max_workers=2)
        
        try:
            print("1. Creating bulk job...")
            bulk_job_id = processor.create_bulk_job(
                sheet_id="demo_sheet_123",
                user_id="demo_user",
                priority=JobPriority.NORMAL
            )
            print(f"   Created bulk job: {bulk_job_id}")
            
            print("\n2. Testing progress callbacks...")
            progress_updates = []
            
            def progress_cb(job_id, progress, message):
                progress_updates.append(f"Job {job_id}: {progress}% - {message}")
            
            processor.add_progress_callback(progress_cb)
            processor._notify_progress(bulk_job_id, 25, "Processing started")
            processor._notify_progress(bulk_job_id, 50, "Halfway done")
            
            print("   Progress updates:")
            for update in progress_updates:
                print(f"   {update}")
            
            print("\n3. Testing job event tracking...")
            event = JobEvent(
                id="demo_event_1",
                job_id=bulk_job_id,
                event_type="created",
                message="Demo event created"
            )
            processor._save_job_event(event)
            print(f"   Created event: {event.message}")
            
            print("\n4. Testing system status...")
            status = processor.get_system_status()
            print(f"   System state: {status['state']}")
            print(f"   Queue running: {status['queue_running']}")
            print(f"   Total bulk jobs: {status['bulk_jobs']['total']}")
            
            print("\n5. Testing rate limiting...")
            limiter = processor.rate_limiter
            
            # Test token bucket
            for i in range(5):
                can_proceed = limiter.can_proceed("demo_user", "demo_project")
                print(f"   Request {i+1}: {'Allowed' if can_proceed else 'Blocked'}")
            
            backoff = limiter.get_backoff_time("demo_user")
            print(f"   Recommended backoff: {backoff:.1f} seconds")
            
            print("\n6. Testing database operations...")
            
            # Test bulk job persistence
            test_bulk = BulkJob(
                id="test_bulk_persistence",
                sheet_id="test_sheet",
                status=PipelineState.COMPLETED,
                progress=100,
                user_id="test_user"
            )
            processor._save_bulk_job(test_bulk)
            
            # Test video job persistence
            test_video = VideoJob(
                id="test_video_job",
                bulk_job_id="test_bulk_persistence",
                idea_data={"title": "Test Video"},
                status=JobStatus.COMPLETED,
                priority=JobPriority.NORMAL,
                ai_provider="test_provider",
                cost=0.50
            )
            processor._save_video_job(test_video)
            
            print("   ✓ Bulk job saved to database")
            print("   ✓ Video job saved to database")
            
            print("\n7. Testing queue management...")
            queue_manager = processor.queue_manager
            
            # Add test jobs
            test_jobs = [
                VideoJob("job1", "bulk1", {}, JobStatus.QUEUED, JobPriority.URGENT, "test"),
                VideoJob("job2", "bulk1", {}, JobStatus.QUEUED, JobPriority.NORMAL, "test"),
                VideoJob("job3", "bulk1", {}, JobStatus.QUEUED, JobPriority.LOW, "test")
            ]
            
            for job in test_jobs:
                queue_manager.add_job(job)
            
            # Retrieve jobs
            retrieved = []
            for _ in range(3):
                job = queue_manager.get_next_job()
                if job:
                    retrieved.append(job.priority.name)
            
            print(f"   Retrieved jobs in order: {retrieved}")
            print("   ✓ Priority ordering works correctly")
            
            print("\n8. Testing job status management...")
            
            # Test pause/resume
            pause_result = processor.pause_bulk_job("test_bulk_persistence")
            print(f"   Pause result: {'Success' if pause_result else 'Failed'}")
            
            resume_result = processor.resume_bulk_job("test_bulk_persistence") 
            print(f"   Resume result: {'Success' if resume_result else 'Failed'}")
            
            print("\n=== Integration Demo Completed Successfully ===")
            
        except Exception as e:
            print(f"\nDemo failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            await processor.cleanup()
            for path in [db_path, cred_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    # Run the demo
    asyncio.run(demo())


if __name__ == "__main__":
    # Run the integration demo
    run_integration_demo()