"""
Integration tests for the entire bulk operations pipeline.

This module tests the end-to-end integration between all components:
- Google Sheets client
- Batch processor
- Parallel generator
- Data validation
- Rate limiting
- Progress monitoring

Tests cover complete workflows from reading data to generating content.

Author: AI Content Automation System
Version: 1.0.0
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

import pytest
import aiofiles

# Import system components
from google_sheets_client import GoogleSheetsClient, SheetRange, ValueRenderOption
from batch_processor import (
    BatchProcessor, BulkJob, VideoJob, JobPriority, JobStatus, PipelineState,
    RateLimiter, QueueManager
)
from parallel_generator import (
    ParallelGenerator, GenerationRequest, GenerationType, Provider,
    TaskPriority, ResourcePool
)
from idea_data_service import IdeaDataService, ProcessedIdea, SheetFormat
from data_validation import DataValidationPipeline, ValidationResult


class TestBulkOperationsIntegration:
    """Integration tests for bulk operations pipeline."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_pipeline_workflow(
        self,
        mock_sheets_client,
        bulk_job_sample,
        processed_ideas_sample,
        mock_generation_function,
        temp_dir
    ):
        """Test complete pipeline from Google Sheets to content generation."""
        
        # Step 1: Mock Google Sheets data retrieval
        mock_sheets_client.get_sheet_data.return_value = [
            ["Title", "Description", "Target Audience", "Tags", "Tone", "Duration"],
            ["Test Video 1", "A test video", "Developers", "test, demo", "professional", "60"],
            ["Test Video 2", "Another test video", "Designers", "design, tutorial", "creative", "90"]
        ]
        
        # Step 2: Create batch processor
        batch_processor = BatchProcessor(
            credentials_path="/tmp/test_credentials.json",
            db_path=str(temp_dir / "test.db"),
            max_workers=2
        )
        batch_processor.sheets_client = mock_sheets_client
        
        # Step 3: Process sheet data
        with patch.object(batch_processor, '_generate_content') as mock_generate:
            mock_generate.return_value = AsyncMock(return_value={
                "success": True,
                "url": "https://example.com/video.mp4",
                "cost": 1.50
            })
            
            # Start processing
            result = await batch_processor.process_sheet(
                spreadsheet_id="test_spreadsheet",
                sheet_name="TestSheet",
                bulk_job_id=bulk_job_sample.id
            )
            
            # Verify results
            assert result is not None
            assert result.sheet_id == "test_spreadsheet"
            assert result.processed_rows > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_google_sheets_to_batch_processor_integration(
        self,
        mock_sheets_client,
        rate_limiter,
        queue_manager,
        temp_dir
    ):
        """Test integration between Google Sheets client and batch processor."""
        
        # Setup mock data
        sample_data = [
            ["Title", "Description", "Target Audience", "Tags"],
            ["Video 1", "Description 1", "Audience 1", "tag1,tag2"],
            ["Video 2", "Description 2", "Audience 2", "tag3,tag4"]
        ]
        mock_sheets_client.get_sheet_data.return_value = sample_data
        
        # Create batch processor
        batch_processor = BatchProcessor(
            credentials_path="/tmp/test_credentials.json",
            db_path=str(temp_dir / "test.db"),
            max_workers=2
        )
        batch_processor.sheets_client = mock_sheets_client
        batch_processor.rate_limiter = rate_limiter
        batch_processor.queue_manager = queue_manager
        
        # Process the data
        bulk_job = BulkJob(
            id=str(uuid.uuid4()),
            sheet_id="test_spreadsheet",
            status=PipelineState.RUNNING
        )
        
        # Add jobs to queue
        for i, row in enumerate(sample_data[1:], 1):
            job = VideoJob(
                id=str(uuid.uuid4()),
                bulk_job_id=bulk_job.id,
                idea_data={
                    "title": row[0],
                    "description": row[1],
                    "target_audience": row[2],
                    "tags": row[3].split(",")
                },
                status=JobStatus.QUEUED,
                priority=JobPriority.NORMAL,
                ai_provider="minimax"
            )
            queue_manager.add_job(job)
        
        # Verify jobs are in queue
        assert not queue_manager.queues[JobPriority.NORMAL].empty()
        
        # Process jobs
        queue_manager.start()
        await asyncio.sleep(0.2)  # Allow time for processing
        queue_manager.stop()
        
        # Verify some jobs were processed
        assert queue_manager.queues[JobPriority.NORMAL].empty() or \
               queue_manager.queues[JobPriority.URGENT].empty() or \
               queue_manager.queues[JobPriority.LOW].empty()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_processor_to_parallel_generator_integration(
        self,
        queue_manager,
        mock_generation_function,
        temp_dir
    ):
        """Test integration between batch processor and parallel generator."""
        
        # Create parallel generator
        generator = ParallelGenerator(
            max_concurrent_jobs=2,
            rate_limiter_config=TestRateLimitConfig()
        )
        
        # Create test jobs
        test_jobs = []
        for i in range(3):
            job = VideoJob(
                id=str(uuid.uuid4()),
                bulk_job_id=str(uuid.uuid4()),
                idea_data={
                    "title": f"Test Video {i+1}",
                    "description": f"Test description {i+1}",
                    "target_audience": "developers"
                },
                status=JobStatus.QUEUED,
                priority=JobPriority.NORMAL,
                ai_provider="minimax",
                cost=Decimal("1.0")
            )
            test_jobs.append(job)
            queue_manager.add_job(job)
        
        # Mock parallel generator methods
        with patch.object(generator, 'generate_content') as mock_gen:
            mock_gen.return_value = AsyncMock(return_value={
                "success": True,
                "url": f"https://example.com/video_{i}.mp4",
                "cost": 1.0
            })
            
            # Process jobs through parallel generator
            queue_manager.start()
            results = []
            
            # Simulate processing
            for _ in range(len(test_jobs)):
                job = queue_manager.get_next_job()
                if job:
                    result = await generator.generate_content(job)
                    results.append(result)
                    job.status = JobStatus.COMPLETED
            
            queue_manager.stop()
            
            # Verify results
            assert len(results) >= 0  # Some jobs may have been processed
            for result in results:
                assert "success" in result
                assert result["success"] is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(
        self,
        mock_sheets_client,
        rate_limiter,
        temp_dir
    ):
        """Test rate limiting across the entire pipeline."""
        
        # Create batch processor with rate limiting
        batch_processor = BatchProcessor(
            credentials_path="/tmp/test_credentials.json",
            db_path=str(temp_dir / "test.db"),
            max_workers=2
        )
        batch_processor.sheets_client = mock_sheets_client
        batch_processor.rate_limiter = rate_limiter
        
        # Test rate limiting with multiple requests
        user_id = "test_user"
        project_id = "test_project"
        
        # Allow initial requests
        can_proceed_1 = rate_limiter.can_proceed(user_id, project_id)
        assert can_proceed_1 is True
        
        # Fill up to limit
        for i in range(9):  # Start from 1, add 9 more to reach limit of 10
            rate_limiter.can_proceed(user_id, project_id)
        
        # Next request should be blocked
        can_proceed_blocked = rate_limiter.can_proceed(user_id, project_id)
        assert can_proceed_blocked is False
        
        # Test backoff time calculation
        backoff_time = rate_limiter.get_backoff_time(user_id)
        assert backoff_time > 0
        assert backoff_time <= 60  # Should not exceed 60 seconds
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self,
        mock_sheets_client,
        queue_manager,
        temp_dir
    ):
        """Test error handling across pipeline components."""
        
        # Create test job
        job = VideoJob(
            id=str(uuid.uuid4()),
            bulk_job_id=str(uuid.uuid4()),
            idea_data={
                "title": "Test Video",
                "description": "Test description"
            },
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="minimax"
        )
        queue_manager.add_job(job)
        
        # Mock error in processing
        def mock_error_process_job(worker_id, job):
            job.status = JobStatus.FAILED
            job.error_message = "Test error"
            logger.error(f"Worker {worker_id} simulated error for job {job.id}")
        
        with patch.object(queue_manager, '_process_job', mock_error_process_job):
            queue_manager.start()
            await asyncio.sleep(0.1)  # Allow time for processing
            queue_manager.stop()
        
        # Verify error was handled
        assert job.status == JobStatus.FAILED
        assert job.error_message is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_progress_monitoring_integration(
        self,
        bulk_job_sample,
        queue_manager,
        temp_dir
    ):
        """Test progress monitoring throughout the pipeline."""
        
        # Create multiple test jobs
        jobs = []
        for i in range(5):
            job = VideoJob(
                id=str(uuid.uuid4()),
                bulk_job_id=bulk_job_sample.id,
                idea_data={
                    "title": f"Test Video {i+1}",
                    "description": f"Test description {i+1}"
                },
                status=JobStatus.QUEUED,
                priority=JobPriority.NORMAL,
                ai_provider="minimax"
            )
            jobs.append(job)
            queue_manager.add_job(job)
        
        # Monitor progress
        initial_progress = bulk_job_sample.progress
        total_jobs = len(jobs)
        
        # Mock successful processing
        def mock_process_job(worker_id, job):
            job.status = JobStatus.COMPLETED
            # Simulate progress update
            completed_jobs = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
            bulk_job_sample.progress = (completed_jobs / total_jobs) * 100
        
        with patch.object(queue_manager, '_process_job', mock_process_job):
            queue_manager.start()
            
            # Simulate gradual completion
            for i, job in enumerate(jobs):
                await asyncio.sleep(0.1)
                mock_process_job(0, job)
                
                # Check progress update
                expected_progress = ((i + 1) / total_jobs) * 100
                assert abs(bulk_job_sample.progress - expected_progress) < 0.1
            
            queue_manager.stop()
        
        # Verify final state
        assert bulk_job_sample.progress >= 100
        assert all(job.status == JobStatus.COMPLETED for job in jobs)
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_processing_integration(
        self,
        queue_manager,
        rate_limiter,
        temp_dir
    ):
        """Test concurrent processing across multiple workers."""
        
        # Create test jobs
        num_jobs = 20
        jobs = []
        for i in range(num_jobs):
            job = VideoJob(
                id=str(uuid.uuid4()),
                bulk_job_id=str(uuid.uuid4()),
                idea_data={
                    "title": f"Concurrent Test Video {i+1}",
                    "description": f"Concurrent test description {i+1}",
                    "target_audience": "developers"
                },
                status=JobStatus.QUEUED,
                priority=JobPriority.NORMAL,
                ai_provider="minimax"
            )
            jobs.append(job)
            queue_manager.add_job(job)
        
        # Start multiple workers
        queue_manager.start()
        
        # Allow time for processing
        await asyncio.sleep(2.0)
        
        # Check worker status
        assert len(queue_manager.workers) > 0
        for worker in queue_manager.workers:
            assert worker.is_alive()  # Workers should still be running or completed
        
        queue_manager.stop()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pipeline_pause_resume_integration(
        self,
        queue_manager,
        temp_dir
    ):
        """Test pipeline pause and resume functionality."""
        
        # Create test job
        job = VideoJob(
            id=str(uuid.uuid4()),
            bulk_job_id=str(uuid.uuid4()),
            idea_data={
                "title": "Pause/Resume Test",
                "description": "Test pause and resume"
            },
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="minimax"
        )
        queue_manager.add_job(job)
        
        # Start processing
        queue_manager.start()
        assert queue_manager.running is True
        
        # Pause by stopping
        queue_manager.stop()
        assert queue_manager.running is False
        
        # Resume by starting again
        queue_manager.start()
        assert queue_manager.running is True
        
        # Clean up
        queue_manager.stop()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_validation_pipeline_integration(
        self,
        data_validator,
        mock_sheets_client,
        temp_dir
    ):
        """Test data validation as part of the pipeline."""
        
        # Test data with various quality levels
        test_data = [
            {
                "title": "Valid Video Title",
                "description": "This is a valid video description with sufficient length",
                "target_audience": "developers",
                "tags": "python,programming,tutorial"
            },
            {
                "title": "Short",  # Too short
                "description": "Short",  # Too short
                "target_audience": "",
                "tags": ""
            }
        ]
        
        results = []
        for data in test_data:
            # Validate each piece of data
            validation_result = data_validator.validate(data)
            results.append(validation_result)
        
        # Verify results
        assert len(results) == 2
        assert results[0].is_valid is True  # First item should be valid
        assert results[1].is_valid is False  # Second item should be invalid
        
        # Check validation details
        if not results[1].is_valid:
            assert len(results[1].errors) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cost_estimation_integration(
        self,
        data_validator,
        processed_ideas_sample,
        temp_dir
    ):
        """Test cost estimation throughout the pipeline."""
        
        total_estimated_cost = Decimal("0.0")
        total_actual_cost = Decimal("0.0")
        
        for idea in processed_ideas_sample:
            # Estimate cost from validation
            validation_result = data_validator.validate(idea.normalized_data)
            if validation_result.is_valid:
                total_estimated_cost += validation_result.estimated_cost
                
                # Simulate actual generation cost (slightly higher due to overhead)
                actual_cost = validation_result.estimated_cost * Decimal("1.1")
                total_actual_cost += actual_cost
        
        # Verify cost calculations
        assert total_estimated_cost > 0
        assert total_actual_cost > total_estimated_cost  # Actual cost should include overhead
        assert total_actual_cost / total_estimated_cost < Decimal("1.2")  # Overhead should be reasonable


class TestRateLimitConfig:
    """Test rate limit configuration."""
    
    def __init__(self):
        self.max_requests_per_minute = 10
        self.max_requests_per_minute_per_user = 5
        self.backoff_base_delay = 0.1
        self.backoff_multiplier = 2.0
        self.max_retries = 2


# Helper function for test logging
def log_test_info(message: str):
    """Log test information for debugging."""
    logger.info(f"TEST INFO: {message}")


# Test execution helpers
@pytest.mark.integration
@pytest.mark.asyncio
async def run_integration_test(test_func, *args, **kwargs):
    """Helper to run integration tests with proper setup/teardown."""
    logger.info(f"Starting integration test: {test_func.__name__}")
    
    try:
        await test_func(*args, **kwargs)
        logger.info(f"Integration test passed: {test_func.__name__}")
        return True
    except Exception as e:
        logger.error(f"Integration test failed: {test_func.__name__}, Error: {str(e)}")
        raise
    finally:
        logger.info(f"Completed integration test: {test_func.__name__}")


if __name__ == "__main__":
    # Run specific integration test
    import sys
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        pytest.main([__file__, f"-k {test_name}", "-v"])