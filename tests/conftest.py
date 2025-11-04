"""
Pytest configuration and shared fixtures for scheduling optimization system tests.

This module provides:
- Test database setup and teardown for scheduling components
- Mock configurations for external services
- Shared test data and fixtures for scheduling algorithms
- Test environment configuration
- Platform timing data and research validation fixtures

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import asyncio
import json
import logging
import os
import sqlite3
import tempfile
import uuid
import numpy as np
from datetime import datetime, timezone, timedelta, time, date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, MagicMock, patch

import pytest
import aiofiles
import aiohttp

# Import scheduling system components
try:
    from google_sheets_client import GoogleSheetsClient, SheetRange, RateLimitConfig
    from batch_processor import (
        BatchProcessor, BulkJob, VideoJob, JobPriority, JobStatus, PipelineState,
        RateLimiter, QueueManager
    )
    from scheduling_optimizer import (
        SchedulingOptimizer, Platform, ContentType, AudienceProfile, 
        PostingWindow, PerformanceMetrics, SchedulingConstraint, 
        SchedulePlan, PriorityTier
    )
    from content_calendar import (
        ContentCalendar, ScheduleItem, ScheduleStatus, CalendarAnalytics,
        CalendarView, TimeRange, BulkScheduleRequest
    )
    from automated_suggestions import (
        SuggestionEngine, PostingSuggestion, UserPreferences, SuggestionContext,
        BayesianUpdater, ConstraintResolver, SeasonalityType
    )
    from data_validation import DataValidationPipeline, VideoIdeaSchema
except ImportError as e:
    logging.warning(f"Could not import all scheduling components: {e}")

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test Configuration
class TestConfig:
    """Test environment configuration for scheduling system."""
    
    # Mock credentials path
    MOCK_CREDENTIALS_PATH = "/tmp/test_credentials.json"
    
    # Test database paths
    SCHEDULING_DB_PATH = "/tmp/test_scheduling_optimization.db"
    CALENDAR_DB_PATH = "/tmp/test_content_calendar.db"
    SUGGESTIONS_DB_PATH = "/tmp/test_automated_suggestions.db"
    
    # Test data paths
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    RESEARCH_DATA_DIR = TEST_DATA_DIR / "research_data"
    
    # Rate limit test config
    TEST_RATE_LIMITS = {
        "max_requests_per_minute": 10,
        "backoff_base_delay": 0.1,
        "backoff_multiplier": 1.5,
        "max_retries": 2
    }
    
    # Platform timing research data
    PLATFORM_RESEARCH_DATA = {
        'youtube': {
            'peak_windows': [
                {'day': 2, 'start_hour': 15, 'end_hour': 17, 'weight': 0.9},  # Wed 3-5PM
                {'day': 1, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},  # Tue 3-5PM
            ],
            'content_factors': {
                'youtube_long_form': 1.0,
                'youtube_shorts': 1.2
            }
        },
        'instagram': {
            'peak_windows': [
                {'day': 1, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},  # Mon-Thu
                {'day': 1, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},    # Reels morning
                {'day': 1, 'start_hour': 18, 'end_hour': 21, 'weight': 0.8},  # Reels evening
            ],
            'content_factors': {
                'instagram_reels': 1.1,
                'instagram_feed': 0.9,
                'instagram_stories': 0.8
            }
        },
        'tiktok': {
            'peak_windows': [
                {'day': 2, 'start_hour': 17, 'end_hour': 18, 'weight': 0.9},  # Wed 5-6PM
                {'day': 6, 'start_hour': 20, 'end_hour': 22, 'weight': 0.85}, # Sun 8-10PM
            ],
            'avoid_windows': [
                {'day': 5, 'start_hour': 0, 'end_hour': 23, 'weight': 0.1}    # Saturday
            ]
        },
        'linkedin': {
            'peak_windows': [
                {'day': 1, 'start_hour': 8, 'end_hour': 11, 'weight': 0.9},   # Business hours
                {'day': 1, 'start_hour': 12, 'end_hour': 14, 'weight': 0.8},
            ]
        },
        'facebook': {
            'peak_windows': [
                {'day': 1, 'start_hour': 11, 'end_hour': 14, 'weight': 0.8},  # Mid-day
            ],
            'content_factors': {
                'facebook_reels': 1.2,
                'facebook_post': 0.9
            }
        }
    }


# Session-wide Event Loop
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Temporary Directories
@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Test configuration fixture."""
    config = TestConfig()
    config.TEST_DATA_DIR = temp_dir / "test_data"
    config.TEST_DATA_DIR.mkdir(exist_ok=True)
    config.RESEARCH_DATA_DIR = config.TEST_DATA_DIR / "research_data"
    config.RESEARCH_DATA_DIR.mkdir(exist_ok=True)
    
    # Set up database paths
    config.SCHEDULING_DB_PATH = str(temp_dir / "test_scheduling.db")
    config.CALENDAR_DB_PATH = str(temp_dir / "test_calendar.db")
    config.SUGGESTIONS_DB_PATH = str(temp_dir / "test_suggestions.db")
    
    return config


# Database Setup and Teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_databases():
    """Setup test databases for session."""
    # Setup would happen here if needed
    yield
    # Cleanup after all tests
    for db_path in [TestConfig.SCHEDULING_DB_PATH, TestConfig.CALENDAR_DB_PATH, 
                   TestConfig.SUGGESTIONS_DB_PATH]:
        if os.path.exists(db_path):
            os.unlink(db_path)


# Scheduling Optimizer Fixtures
@pytest.fixture
def scheduling_optimizer(temp_db_path):
    """Initialize scheduling optimizer with test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        optimizer = SchedulingOptimizer(db_path=db_path)
        yield optimizer
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def sample_audience_profiles():
    """Sample audience profiles for testing."""
    return {
        'gen_z_mobile': AudienceProfile(
            age_cohorts={'18-24': 0.8, '25-34': 0.2},
            device_split={'mobile': 0.9, 'desktop': 0.1},
            time_zone_weights={'UTC-5': 0.4, 'UTC-8': 0.3, 'UTC+5.5': 0.3},
            geography={'US': 0.7, 'India': 0.3}
        ),
        'working_professionals': AudienceProfile(
            age_cohorts={'25-34': 0.4, '35-44': 0.4, '45-54': 0.2},
            device_split={'desktop': 0.6, 'mobile': 0.3, 'tablet': 0.1},
            time_zone_weights={'UTC': 0.5, 'UTC-5': 0.5},
            geography={'US': 0.8, 'UK': 0.2}
        ),
        'mixed_global': AudienceProfile(
            age_cohorts={'18-24': 0.3, '25-34': 0.3, '35-44': 0.25, '45-54': 0.15},
            device_split={'mobile': 0.65, 'desktop': 0.3, 'tablet': 0.05},
            time_zone_weights={'UTC-8': 0.25, 'UTC-5': 0.25, 'UTC': 0.25, 'UTC+8': 0.25},
            geography={'US': 0.5, 'UK': 0.2, 'China': 0.2, 'Other': 0.1}
        )
    }


@pytest.fixture
def sample_constraints():
    """Sample scheduling constraints for testing."""
    return [
        SchedulingConstraint(
            platform=Platform.INSTAGRAM,
            min_gap_hours=18.0,
            max_concurrent_posts=2,
            preferred_windows=[PostingWindow(10, 15, 0.8, 1)]
        ),
        SchedulingConstraint(
            platform=Platform.TIKTOK,
            min_gap_hours=12.0,
            max_concurrent_posts=3
        ),
        SchedulingConstraint(
            platform=Platform.YOUTUBE,
            min_gap_hours=48.0,
            max_concurrent_posts=1
        )
    ]


@pytest.fixture
def sample_performance_data(scheduling_optimizer):
    """Generate sample performance data for ML training."""
    np.random.seed(42)  # For reproducible tests
    
    platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE, Platform.LINKEDIN]
    content_types = [ContentType.INSTAGRAM_REELS, ContentType.TIKTOK_VIDEO, 
                    ContentType.YOUTUBE_LONG_FORM, ContentType.LINKEDIN_POST]
    
    for _ in range(100):  # Generate 100 samples per platform
        platform = np.random.choice(platforms)
        content_type = np.random.choice(content_types)
        
        # Generate synthetic performance metrics
        base_reach = np.random.normal(1000, 200)
        engagement_rate = np.random.beta(2, 5)
        
        metrics = PerformanceMetrics(
            platform=platform,
            content_type=content_type,
            posted_at=datetime.now(timezone.utc),
            reach=max(100, int(base_reach)),
            engagement_rate=engagement_rate,
            click_through_rate=np.random.beta(1, 10),
            conversion_rate=np.random.beta(1, 20),
            is_successful=engagement_rate > 0.03
        )
        
        scheduling_optimizer.record_performance_metrics(metrics)


# Content Calendar Fixtures
@pytest.fixture
def content_calendar(temp_db_path):
    """Initialize content calendar with test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        calendar = ContentCalendar(db_path=db_path)
        yield calendar
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def sample_schedule_items(content_calendar):
    """Create sample schedule items for testing."""
    items = []
    
    # Instagram post
    instagram_item = ScheduleItem(
        id="cal_item_1",
        title="Product Launch Announcement",
        platform=Platform.INSTAGRAM.value,
        content_type=ContentType.INSTAGRAM_FEED.value,
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        status=ScheduleStatus.PLANNED,
        priority=JobPriority.NORMAL,
        metadata={
            "hashtags": "#product #launch #innovation",
            "target_audience": "tech enthusiasts",
            "cost_estimate": 0.50
        }
    )
    content_calendar.create_schedule_item(instagram_item)
    items.append(instagram_item)
    
    # TikTok video
    tiktok_item = ScheduleItem(
        id="cal_item_2",
        title="Behind the Scenes",
        platform=Platform.TIKTOK.value,
        content_type=ContentType.TIKTOK_VIDEO.value,
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=6),
        status=ScheduleStatus.SCHEDULED,
        priority=JobPriority.NORMAL,
        metadata={
            "duration": 30,
            "music_trend": "upbeat",
            "cost_estimate": 1.20
        }
    )
    content_calendar.create_schedule_item(tiktok_item)
    items.append(tiktok_item)
    
    # LinkedIn post
    linkedin_item = ScheduleItem(
        id="cal_item_3",
        title="Industry Insights",
        platform=Platform.LINKEDIN.value,
        content_type=ContentType.LINKEDIN_POST.value,
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=12),
        status=ScheduleStatus.SCHEDULED,
        priority=JobPriority.URGENT,
        metadata={
            "industry": "technology",
            "engagement_goal": "thought leadership",
            "cost_estimate": 0.30
        }
    )
    content_calendar.create_schedule_item(linkedin_item)
    items.append(linkedin_item)
    
    return items


# Automated Suggestions Fixtures
@pytest.fixture
def suggestion_engine(temp_db_path):
    """Initialize suggestion engine with test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        engine = SuggestionEngine(db_path=db_path)
        yield engine
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def user_preferences():
    """Sample user preferences for testing."""
    return UserPreferences(
        user_id="test_user_123",
        timezone="UTC-5",
        active_hours_start=time(8, 0),  # 8 AM
        active_hours_end=time(22, 0),   # 10 PM
        posting_frequency_limits={
            Platform.INSTAGRAM: {"min_hours": 18, "max_per_day": 2},
            Platform.TIKTOK: {"min_hours": 12, "max_per_day": 3},
            Platform.YOUTUBE: {"min_hours": 48, "max_per_day": 1}
        },
        blacklisted_hours=list(range(0, 6)),  # 12 AM - 6 AM
        preferred_content_types={
            Platform.INSTAGRAM: [ContentType.INSTAGRAM_REELS, ContentType.INSTAGRAM_FEED],
            Platform.TIKTOK: [ContentType.TIKTOK_VIDEO],
            Platform.YOUTUBE: [ContentType.YOUTUBE_LONG_FORM]
        },
        automation_enabled=True,
        quality_threshold=0.7,
        cost_sensitivity="medium"
    )


@pytest.fixture
def suggestion_context(user_preferences):
    """Sample suggestion context for testing."""
    return SuggestionContext(
        platform=Platform.INSTAGRAM,
        content_type=ContentType.INSTAGRAM_REELS,
        user_preferences=user_preferences,
        target_audience={
            'age_groups': {'18-24': 0.4, '25-34': 0.35, '35-44': 0.25},
            'device_split': {'mobile': 0.75, 'desktop': 0.25},
            'geography': {'US': 0.6, 'Canada': 0.2, 'UK': 0.2}
        },
        content_metadata={
            'duration': 30,
            'has_video': True,
            'has_audio': True,
            'estimated_cost': 1.50
        },
        scheduling_constraints={
            'max_posts_per_day': 3,
            'preferred_time_windows': [
                {'start': time(10, 0), 'end': time(12, 0), 'weight': 0.8},
                {'start': time(18, 0), 'end': time(21, 0), 'weight': 0.9}
            ]
        }
    )


@pytest.fixture
def historical_performance_data(suggestion_engine):
    """Generate historical performance data for learning."""
    np.random.seed(42)  # For reproducible tests
    
    platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE, Platform.LINKEDIN]
    content_types = [ContentType.INSTAGRAM_REELS, ContentType.TIKTOK_VIDEO, 
                    ContentType.YOUTUBE_LONG_FORM, ContentType.LINKEDIN_POST]
    
    # Generate 200 performance records
    for _ in range(200):
        platform = np.random.choice(platforms)
        content_type = np.random.choice(content_types)
        
        # Simulate platform-specific performance patterns
        base_performance = np.random.normal(0.5, 0.2)
        
        # Time-based adjustments
        hour = np.random.randint(0, 24)
        day_of_week = np.random.randint(0, 7)
        
        # Platform-specific timing bonuses
        if platform == Platform.LINKEDIN and 8 <= hour <= 14 and day_of_week < 5:
            base_performance += 0.3  # Business hours boost
        elif platform == Platform.TIKTOK and 17 <= hour <= 21:
            base_performance += 0.2  # Evening boost
        elif platform == Platform.INSTAGRAM and 10 <= hour <= 15 and day_of_week < 5:
            base_performance += 0.25  # Business hours
        
        # Ensure performance is in valid range
        base_performance = np.clip(base_performance, 0.0, 1.0)
        
        # Record performance data
        suggestion_engine.record_performance_feedback(
            platform=platform,
            content_type=content_type,
            suggested_time=datetime.now(timezone.utc) - timedelta(days=np.random.randint(1, 30)),
            actual_performance=base_performance,
            engagement_metrics={
                'reach': int(np.random.normal(1000, 300)),
                'engagement_rate': np.random.beta(2, 5),
                'click_through_rate': np.random.beta(1, 10)
            }
        )


# Research Data Fixtures
@pytest.fixture
def research_timing_data():
    """Research-based timing data for validation."""
    return {
        'instagram_reels_evening_boost': {
            'hours': [18, 19, 20, 21],
            'expected_min_score': 0.65,
            'research_source': '2025 Instagram Engagement Study'
        },
        'linkedin_business_hours': {
            'hours': list(range(8, 12)) + list(range(12, 14)),
            'expected_min_score': 0.70,
            'research_source': 'LinkedIn Marketing Solutions 2025'
        },
        'tiktok_wednesday_peak': {
            'hours': [17, 18],
            'expected_min_score': 0.80,
            'research_source': 'TikTok Creator Fund Research 2025'
        },
        'youtube_afternoon_preference': {
            'hours': list(range(15, 18)),
            'expected_min_score': 0.75,
            'research_source': 'YouTube Creator Academy 2025'
        }
    }


@pytest.fixture
def platform_timing_profiles():
    """Platform-specific timing profiles from research."""
    return {
        'youtube': {
            'baseline_windows': [
                {'day': 2, 'start_hour': 15, 'end_hour': 17, 'weight': 0.9},
                {'day': 1, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},
                {'day': 3, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},
                {'day': 4, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},
            ],
            'content_adjustments': {
                'youtube_long_form': {'weight_multiplier': 1.0},
                'youtube_shorts': {'weight_multiplier': 1.2, 'peak_expansion': True}
            }
        },
        'instagram': {
            'baseline_windows': [
                {'day': 1, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                {'day': 2, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                {'day': 3, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                {'day': 4, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                {'day': 1, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},
                {'day': 2, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},
                {'day': 3, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},
                {'day': 1, 'start_hour': 18, 'end_hour': 21, 'weight': 0.8},
                {'day': 2, 'start_hour': 18, 'end_hour': 21, 'weight': 0.8},
                {'day': 3, 'start_hour': 18, 'end_hour': 21, 'weight': 0.8},
            ],
            'content_adjustments': {
                'instagram_reels': {'weight_multiplier': 1.1, 'evening_boost': True},
                'instagram_feed': {'weight_multiplier': 0.9, 'business_hours_boost': True},
                'instagram_stories': {'weight_multiplier': 0.8, 'flexible_timing': True}
            }
        },
        'tiktok': {
            'baseline_windows': [
                {'day': 2, 'start_hour': 17, 'end_hour': 18, 'weight': 0.9},
                {'day': 6, 'start_hour': 20, 'end_hour': 22, 'weight': 0.85},
                {'day': 1, 'start_hour': 17, 'end_hour': 19, 'weight': 0.8},
                {'day': 3, 'start_hour': 17, 'end_hour': 19, 'weight': 0.8},
                {'day': 4, 'start_hour': 17, 'end_hour': 19, 'weight': 0.8},
            ],
            'avoid_windows': [
                {'day': 5, 'start_hour': 0, 'end_hour': 23, 'weight': 0.1}
            ],
            'content_adjustments': {
                'tiktok_video': {'weight_multiplier': 1.0, 'peak_concentration': True}
            }
        }
    }


# Mock Services
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
    try:
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
    except Exception as e:
        logger.warning(f"Could not create mock sheets client: {e}")
        yield Mock()


# Utility Functions for Tests
def create_mock_http_error(status_code=429, message="Rate limit exceeded"):
    """Create mock HTTP error for testing."""
    try:
        from googleapiclient.errors import HttpError
        from google.auth.exceptions import RefreshError
        
        mock_resp = Mock()
        mock_resp.status = status_code
        
        error = HttpError(mock_resp, b'{"error": message}')
        error.resp = mock_resp
        
        return error
    except ImportError:
        return Exception(f"HTTP {status_code}: {message}")


def create_test_schedule_posts(count=5, platforms=None):
    """Create a batch of test posts for scheduling."""
    if platforms is None:
        platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]
    
    posts = []
    for i in range(count):
        platform = np.random.choice(platforms)
        content_type_map = {
            Platform.INSTAGRAM: ContentType.INSTAGRAM_REELS,
            Platform.TIKTOK: ContentType.TIKTOK_VIDEO,
            Platform.YOUTUBE: ContentType.YOUTUBE_LONG_FORM,
            Platform.LINKEDIN: ContentType.LINKEDIN_POST
        }
        
        post = {
            'id': f'schedule_post_{i}',
            'platform': platform.value,
            'content_type': content_type_map.get(platform, ContentType.INSTAGRAM_REELS).value,
            'priority': np.random.choice([PriorityTier.NORMAL.value, PriorityTier.URGENT.value]),
            'title': f'Test Post {i}',
            'metadata': {
                'estimated_cost': np.random.uniform(0.5, 2.0),
                'target_audience': 'general',
                'content_length': np.random.randint(30, 300)
            }
        }
        posts.append(post)
    
    return posts


def create_test_performance_metrics(platform, content_type, count=10):
    """Create test performance metrics."""
    metrics = []
    for i in range(count):
        metric = PerformanceMetrics(
            platform=platform,
            content_type=content_type,
            posted_at=datetime.now(timezone.utc) - timedelta(days=i),
            reach=int(np.random.normal(1500, 300)),
            engagement_rate=np.random.beta(2, 5),
            click_through_rate=np.random.beta(1, 10),
            conversion_rate=np.random.beta(1, 20),
            is_successful=np.random.choice([True, False], p=[0.7, 0.3])
        )
        metrics.append(metric)
    return metrics


# Custom Assertions
class SchedulingAssertions:
    """Custom assertions for scheduling system testing."""
    
    @staticmethod
    def assert_timing_scores_valid(scores):
        """Assert timing scores are valid."""
        assert isinstance(scores, dict), "Scores should be dictionary"
        assert len(scores) == 24, "Should have scores for 24 hours"
        assert all(0 <= score <= 1 for score in scores.values()), \
            "All scores should be between 0 and 1"
    
    @staticmethod
    def assert_schedule_constraints_satisfied(schedule, constraints):
        """Assert schedule satisfies all constraints."""
        if not schedule.scheduled_posts:
            return  # No posts to check
        
        # Check platform-specific constraints
        platform_posts = {}
        for post in schedule.scheduled_posts:
            platform = post.platform
            if platform not in platform_posts:
                platform_posts[platform] = []
            platform_posts[platform].append(post)
        
        for constraint in constraints:
            platform = constraint.platform
            if platform in platform_posts:
                posts = platform_posts[platform]
                
                # Check minimum gap
                if len(posts) > 1 and constraint.min_gap_hours:
                    times = [post.scheduled_time for post in posts]
                    times.sort()
                    for i in range(1, len(times)):
                        time_diff = abs((times[i] - times[i-1]).total_seconds()) / 3600
                        assert time_diff >= constraint.min_gap_hours, \
                            f"Minimum gap violated: {time_diff}h < {constraint.min_gap_hours}h"
                
                # Check concurrency limit
                if constraint.max_concurrent_posts and len(posts) > constraint.max_concurrent_posts:
                    assert len(posts) <= constraint.max_concurrent_posts, \
                        f"Concurrency limit violated: {len(posts)} > {constraint.max_concurrent_posts}"
    
    @staticmethod
    def assert_suggestion_quality(suggestions):
        """Assert suggestions meet quality standards."""
        assert len(suggestions) > 0, "Should have suggestions"
        
        for suggestion in suggestions:
            assert 0 <= suggestion.confidence_score <= 1, "Confidence should be in [0,1]"
            assert 0 <= suggestion.expected_performance <= 1, "Performance should be in [0,1]"
            assert len(suggestion.reasoning) > 10, "Should have detailed reasoning"
            assert suggestion.suggested_time is not None, "Should have suggested time"
            assert suggestion.platform is not None, "Should have platform"
            assert suggestion.content_type is not None, "Should have content type"
    
    @staticmethod
    def assert_calendar_consistency(calendar_items):
        """Assert calendar items are consistent."""
        seen_ids = set()
        for item in calendar_items:
            assert item.id not in seen_ids, f"Duplicate ID found: {item.id}"
            seen_ids.add(item.id)
            
            assert item.platform in [p.value for p in Platform], f"Invalid platform: {item.platform}"
            assert item.status in [s.value for s in ScheduleStatus], f"Invalid status: {item.status}"
            assert isinstance(item.scheduled_time, datetime), "Invalid scheduled time"


@pytest.fixture
def assertions():
    """Fixture providing custom assertions."""
    return SchedulingAssertions()


# Environment Setup for Tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/test_credentials.json")
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SCHEDULING_DB_PATH", "/tmp/test_scheduling.db")
    monkeypatch.setenv("CALENDAR_DB_PATH", "/tmp/test_calendar.db")
    monkeypatch.setenv("SUGGESTIONS_DB_PATH", "/tmp/test_suggestions.db")


# Pytest Markers Configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "scheduling: mark test as scheduling optimization test")
    config.addinivalue_line("markers", "calendar: mark test as content calendar test")
    config.addinivalue_line("markers", "suggestions: mark test as suggestion engine test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


# Async Test Helpers
@pytest.fixture
def async_timeout():
    """Helper for async test timeouts."""
    class AsyncTimeout:
        def __init__(self, timeout_seconds=30):
            self.timeout_seconds = timeout_seconds
            self.start_time = None
        
        def __enter__(self):
            import time
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start_time:
                import time
                elapsed = time.time() - self.start_time
                if elapsed > self.timeout_seconds:
                    logger.warning(f"Test took {elapsed:.2f}s, exceeding {self.timeout_seconds}s timeout")
    
    return AsyncTimeout


# Data Generation Helpers
@pytest.fixture
def data_generator():
    """Helper for generating test data."""
    class DataGenerator:
        @staticmethod
        def random_audience_profile():
            """Generate random audience profile."""
            age_cohorts = {
                f'{i}-{i+4}': np.random.uniform(0.1, 0.3) 
                for i in range(18, 60, 5)
            }
            # Normalize to sum to 1
            total = sum(age_cohorts.values())
            age_cohorts = {k: v/total for k, v in age_cohorts.items()}
            
            return AudienceProfile(
                age_cohorts=age_cohorts,
                device_split={
                    'mobile': np.random.uniform(0.6, 0.9),
                    'desktop': np.random.uniform(0.1, 0.4),
                    'tablet': 1.0 - np.random.uniform(0.6, 0.9) - np.random.uniform(0.1, 0.4)
                },
                time_zone_weights={
                    'UTC-8': np.random.uniform(0.2, 0.4),
                    'UTC-5': np.random.uniform(0.3, 0.5),
                    'UTC': np.random.uniform(0.1, 0.3),
                    'UTC+5.5': np.random.uniform(0.1, 0.3)
                }
            )
        
        @staticmethod
        def random_performance_metrics(platform, content_type):
            """Generate random performance metrics."""
            return PerformanceMetrics(
                platform=platform,
                content_type=content_type,
                posted_at=datetime.now(timezone.utc) - timedelta(days=np.random.randint(1, 30)),
                reach=int(np.random.normal(1200, 400)),
                engagement_rate=np.random.beta(2, 5),
                click_through_rate=np.random.beta(1, 10),
                conversion_rate=np.random.beta(1, 20),
                is_successful=np.random.choice([True, False], p=[0.65, 0.35])
            )
    
    return DataGenerator()


# Test Database Cleanup
@pytest.fixture(autouse=True)
def clean_test_files():
    """Clean up test files after each test."""
    yield
    # Cleanup happens after test
    test_files = [
        "/tmp/test_scheduling*.db",
        "/tmp/test_calendar*.db", 
        "/tmp/test_suggestions*.db",
        "/tmp/test_credentials.json"
    ]
    
    import glob
    for pattern in test_files:
        for file_path in glob.glob(pattern):
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass


# Performance Monitoring
@pytest.fixture
def performance_monitor():
    """Monitor test performance."""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.checkpoints = {}
        
        def start(self):
            self.start_time = time.time()
        
        def checkpoint(self, name):
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.checkpoints[name] = elapsed
                return elapsed
            return None
        
        def get_report(self):
            if not self.checkpoints:
                return "No checkpoints recorded"
            
            report = "Performance Report:\\n"
            for name, elapsed in self.checkpoints.items():
                report += f"  {name}: {elapsed:.3f}s\\n"
            
            total = max(self.checkpoints.values()) if self.checkpoints else 0
            report += f"  Total: {total:.3f}s\\n"
            return report
    
    return PerformanceMonitor()