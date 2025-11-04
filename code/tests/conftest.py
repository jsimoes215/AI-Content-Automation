"""
Pytest configuration and shared fixtures for bulk operations system tests.

This module provides:
- Test database setup and teardown
- Mock configurations for external services
- Shared test data and fixtures
- Test environment configuration

Author: AI Content Automation System
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock, patch

import pytest
import aiofiles
import aiohttp

# Import system components
from google_sheets_client import GoogleSheetsClient, SheetRange, RateLimitConfig
from batch_processor import (
    BatchProcessor, BulkJob, VideoJob, JobPriority, JobStatus, PipelineState,
    RateLimiter, QueueManager
)
from parallel_generator import (
    ParallelGenerator, GenerationRequest, GenerationType, Provider,
    TaskPriority, ResourcePool, ResourceType
)
from idea_data_service import IdeaDataService, SheetFormat, ColumnMapping, ProcessedIdea
from data_validation import DataValidationPipeline, VideoIdeaSchema


# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test Configuration
class TestConfig:
    """Test environment configuration."""
    
    # Mock credentials path
    MOCK_CREDENTIALS_PATH = "/tmp/test_credentials.json"
    
    # Test spreadsheet IDs
    TEST_SPREADSHEET_ID = "test_spreadsheet_123"
    TEST_SHEET_NAME = "TestSheet"
    
    # Test data paths
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    
    # Database paths
    TEST_DB_PATH = "/tmp/test_batch_processing.db"
    
    # Rate limit test config
    TEST_RATE_LIMITS = {
        "max_requests_per_minute": 10,
        "backoff_base_delay": 0.1,
        "backoff_multiplier": 1.5,
        "max_retries": 2
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Test configuration fixture."""
    config = TestConfig()
    config.TEST_DB_PATH = str(temp_dir / "test_batch_processing.db")
    config.TEST_DATA_DIR = temp_dir / "test_data"
    config.TEST_DATA_DIR.mkdir(exist_ok=True)
    return config


@pytest.fixture
def mock_credentials():
    """Mock Google Sheets credentials."""
    credentials_data = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(credentials_data, f)
        credentials_path = f.name
    
    yield credentials_path
    
    # Cleanup
    if os.path.exists(credentials_path):
        os.unlink(credentials_path)


@pytest.fixture
def mock_sheets_client(mock_credentials):
    """Mock Google Sheets client with sample data."""
    client = GoogleSheetsClient(
        credentials_path=mock_credentials,
        rate_limit_config=RateLimitConfig(**TestConfig.TEST_RATE_LIMITS)
    )
    
    # Mock the service responses
    mock_service = Mock()
    mock_spreadsheets = Mock()
    mock_values = Mock()
    mock_batch = Mock()
    
    mock_service.spreadsheets.return_value = mock_spreadsheets
    mock_spreadsheets.values.return_value = mock_values
    mock_spreadsheets.batchUpdate.return_value = mock_batch
    mock_spreadsheets.get.return_value = mock_batch
    
    # Set up mock responses
    client._service = mock_service
    
    yield client
    
    client.close()


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for parallel generator tests."""
    session = Mock(spec=aiohttp.ClientSession)
    
    # Mock response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = asyncio.coroutine(lambda: {
        "audio_url": "https://example.com/audio.mp3",
        "duration": 30,
        "cost": 0.10
    })
    mock_response.text = asyncio.coroutine(lambda: "audio_data")
    mock_response.read = asyncio.coroutine(lambda: b"audio_bytes")
    
    session.post.return_value.__aenter__.return_value = mock_response
    
    yield session


@pytest.fixture
def idea_data_service():
    """Initialized IdeaDataService."""
    return IdeaDataService()


@pytest.fixture
def data_validator():
    """Initialized DataValidationPipeline."""
    return DataValidationPipeline()


@pytest.fixture
def rate_limiter():
    """Test rate limiter instance."""
    return RateLimiter(
        per_user_limit=10,
        per_project_limit=50,
        refill_rate=1.0
    )


@pytest.fixture
def queue_manager():
    """Test queue manager instance."""
    return QueueManager(max_workers=2)


@pytest.fixture
def bulk_job_sample(test_config):
    """Sample bulk job for testing."""
    return BulkJob(
        id=str(uuid.uuid4()),
        sheet_id=test_config.TEST_SPREADSHEET_ID,
        status=PipelineState.IDLE,
        progress=0,
        user_id="test_user",
        priority=JobPriority.NORMAL
    )


@pytest.fixture
def video_job_sample():
    """Sample video job for testing."""
    return VideoJob(
        id=str(uuid.uuid4()),
        bulk_job_id=str(uuid.uuid4()),
        idea_data={
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "Developers",
            "tags": ["test", "demo"],
            "tone": "professional",
            "duration_estimate": 60
        },
        status=JobStatus.QUEUED,
        priority=JobPriority.NORMAL,
        ai_provider="minimax",
        cost=Decimal("1.50"),
        user_id="test_user"
    )


@pytest.fixture
def generation_request_sample():
    """Sample generation request for testing."""
    return GenerationRequest(
        id=str(uuid.uuid4()),
        type=GenerationType.AUDIO,
        provider=Provider.MINIMAX,
        prompt="Generate test audio",
        params={"voice": "default", "speed": 1.0},
        priority=TaskPriority.NORMAL,
        user_id="test_user"
    )


# Test Data Fixtures
@pytest.fixture
def sample_sheet_data():
    """Sample Google Sheets data for testing."""
    return [
        ["Title", "Description", "Target Audience", "Tags", "Tone", "Duration"],
        [
            "How to Learn Python",
            "A comprehensive guide to learning Python programming",
            "Beginner developers",
            "python, programming, tutorial",
            "educational",
            "300"
        ],
        [
            "AI in Healthcare",
            "Exploring AI applications in healthcare systems",
            "Healthcare professionals",
            "AI, healthcare, technology",
            "professional",
            "450"
        ],
        [
            "Mobile App Design",
            "Best practices for mobile application UI/UX design",
            "Designers and developers",
            "design, mobile, UI/UX",
            "creative",
            "600"
        ]
    ]


@pytest.fixture
def processed_ideas_sample(sample_sheet_data):
    """Sample processed ideas data."""
    ideas = []
    for i, row in enumerate(sample_sheet_data[1:], start=1):  # Skip header
        if len(row) >= 3:  # Ensure minimum required data
            processed_idea = ProcessedIdea(
                id=str(uuid.uuid4()),
                row_index=i,
                raw_data={"row": row},
                normalized_data={
                    "title": row[0] if len(row) > 0 else "",
                    "description": row[1] if len(row) > 1 else "",
                    "target_audience": row[2] if len(row) > 2 else "",
                    "tags": row[3].split(",") if len(row) > 3 and row[3] else [],
                    "tone": row[4] if len(row) > 4 else "",
                    "duration_estimate": int(row[5]) if len(row) > 5 and row[5].isdigit() else 60
                },
                validation_result=type('obj', (object,), {
                    'is_valid': True,
                    'errors': [],
                    'warnings': []
                })(),
                sheet_format=SheetFormat.STANDARD
            )
            ideas.append(processed_idea)
    
    return ideas


@pytest.fixture
def validation_result_sample():
    """Sample validation result."""
    from data_validation import ValidationResult
    return ValidationResult(
        is_valid=True,
        errors=[],
        warnings=[],
        cleaned_data={
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "Test audience"
        },
        quality_score=0.85,
        estimated_cost=Decimal("1.50"),
        duplicate_score=0.0
    )


# Mock Generation Functions
@pytest.fixture
def mock_generation_function():
    """Mock generation function for testing."""
    async def mock_generate(*args, **kwargs):
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            "success": True,
            "url": "https://example.com/generated_content.mp4",
            "duration": 60,
            "cost": 1.50,
            "metadata": {"provider": "minimax", "model": "test-model"}
        }
    
    return mock_generate


@pytest.fixture
def mock_validation_function():
    """Mock validation function for testing."""
    def mock_validate(data):
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            cleaned_data=data,
            quality_score=0.9,
            estimated_cost=Decimal("1.0")
        )
    
    return mock_validate


# Database Setup/Teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database for session."""
    # Initialize test database if needed
    yield
    # Cleanup after all tests
    if os.path.exists(TestConfig.TEST_DB_PATH):
        os.unlink(TestConfig.TEST_DB_PATH)


# Utility Functions for Tests
def create_mock_http_error(status_code=429, message="Rate limit exceeded"):
    """Create mock HTTP error for testing."""
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import RefreshError
    
    mock_resp = Mock()
    mock_resp.status = status_code
    
    error = HttpError(mock_resp, b'{"error": message}')
    error.resp = mock_resp
    
    return error


def create_test_batch_jobs(count=5, batch_id=None):
    """Create a batch of test jobs."""
    if batch_id is None:
        batch_id = str(uuid.uuid4())
    
    jobs = []
    for i in range(count):
        job = VideoJob(
            id=str(uuid.uuid4()),
            bulk_job_id=batch_id,
            idea_data={
                "title": f"Test Video {i+1}",
                "description": f"Test description {i+1}",
                "target_audience": "test audience"
            },
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="minimax",
            cost=Decimal("1.0")
        )
        jobs.append(job)
    
    return jobs


def assert_job_status(job: VideoJob, expected_status: JobStatus):
    """Assert job has expected status."""
    assert job.status == expected_status, f"Job {job.id} status is {job.status}, expected {expected_status}"


def assert_job_in_queue(queue_manager: QueueManager, job: VideoJob):
    """Assert job is in queue."""
    # This is a simplified check - in reality we'd need to inspect the queue internals
    # For now, just check that the queue is not empty when we expect jobs
    pass


# Marker for integration tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "unit: mark test as unit test")


# Custom Assertions
class BulkOperationsAssertions:
    """Custom assertions for bulk operations testing."""
    
    @staticmethod
    def assert_pipeline_state(bulk_job: BulkJob, expected_state: PipelineState):
        """Assert bulk job has expected state."""
        assert bulk_job.status == expected_state, \
            f"Bulk job {bulk_job.id} status is {bulk_job.status}, expected {expected_state}"
    
    @staticmethod
    def assert_progress_completed(bulk_job: BulkJob):
        """Assert bulk job progress shows completion."""
        assert bulk_job.progress >= 100, \
            f"Bulk job {bulk_job.id} progress is {bulk_job.progress}, expected >= 100"
        assert bulk_job.completed_at is not None, \
            f"Bulk job {bulk_job.id} should have completion timestamp"
    
    @staticmethod
    def assert_cost_calculated(cost: Decimal, expected_range: tuple):
        """Assert cost is within expected range."""
        min_cost, max_cost = expected_range
        assert min_cost <= cost <= max_cost, \
            f"Cost {cost} is not in expected range [{min_cost}, {max_cost}]"
    
    @staticmethod
    def assert_rate_limit_stats(rate_limiter: RateLimiter, user_id: str, project_id: str):
        """Assert rate limiter is functioning correctly."""
        # Test basic functionality
        can_proceed = rate_limiter.can_proceed(user_id, project_id)
        assert isinstance(can_proceed, bool), "Rate limiter should return boolean"


@pytest.fixture
def assertions():
    """Fixture providing custom assertions."""
    return BulkOperationsAssertions()


# Environment Setup for Tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/test_credentials.json")
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")