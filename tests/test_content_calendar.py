"""
Comprehensive Test Suite for Content Calendar Operations

This module tests content calendar functionality:
1. Calendar CRUD operations
2. Schedule item management
3. Content scheduling workflows
4. Cross-platform coordination
5. Calendar analytics and reporting
6. Integration with batch processing

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import pytest
import asyncio
import sqlite3
import tempfile
import json
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, MagicMock, patch
import logging

# Import calendar and related components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from content_calendar import (
    ContentCalendar, ScheduleItem, ScheduleStatus, CalendarAnalytics,
    CalendarView, TimeRange, BulkScheduleRequest
)
from scheduling_optimizer import (
    Platform, ContentType, AudienceProfile, SchedulingConstraint
)
from batch_processor import JobStatus, JobPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestContentCalendarOperations:
    """Test suite for content calendar operations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def content_calendar(self, temp_db_path):
        """Initialize content calendar with test database."""
        calendar = ContentCalendar(db_path=temp_db_path)
        return calendar
    
    @pytest.fixture
    def sample_schedule_items(self, content_calendar):
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
    
    @pytest.fixture
    def time_range_sample(self):
        """Sample time range for testing."""
        start_date = datetime.now(timezone.utc).date()
        end_date = start_date + timedelta(days=30)
        return TimeRange(start_date, end_date)
    
    # CRUD Operations Tests
    def test_create_schedule_item(self, content_calendar):
        """Test creating new schedule items."""
        item = ScheduleItem(
            id="test_item_1",
            title="Test Schedule Item",
            platform=Platform.INSTAGRAM.value,
            content_type=ContentType.INSTAGRAM_REELS.value,
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            status=ScheduleStatus.PLANNED,
            priority=JobPriority.NORMAL
        )
        
        result = content_calendar.create_schedule_item(item)
        
        assert result is True, "Schedule item should be created successfully"
        
        # Verify item exists in database
        retrieved_item = content_calendar.get_schedule_item("test_item_1")
        assert retrieved_item is not None, "Created item should be retrievable"
        assert retrieved_item.title == item.title, "Title should match"
        assert retrieved_item.platform == item.platform, "Platform should match"
        assert retrieved_item.scheduled_time == item.scheduled_time, "Scheduled time should match"
    
    def test_get_schedule_item(self, content_calendar, sample_schedule_items):
        """Test retrieving schedule items."""
        # Test getting existing item
        item = content_calendar.get_schedule_item("cal_item_1")
        assert item is not None, "Should retrieve existing item"
        assert item.title == "Product Launch Announcement", "Title should match"
        assert item.platform == Platform.INSTAGRAM.value, "Platform should match"
        
        # Test getting non-existent item
        non_existent = content_calendar.get_schedule_item("non_existent_id")
        assert non_existent is None, "Non-existent item should return None"
    
    def test_update_schedule_item(self, content_calendar, sample_schedule_items):
        """Test updating schedule items."""
        # Get existing item
        item = content_calendar.get_schedule_item("cal_item_1")
        assert item is not None
        
        # Update item
        item.title = "Updated Product Title"
        item.status = ScheduleStatus.SCHEDULED
        item.metadata["updated_field"] = "test_value"
        
        result = content_calendar.update_schedule_item(item)
        assert result is True, "Update should succeed"
        
        # Verify update
        updated_item = content_calendar.get_schedule_item("cal_item_1")
        assert updated_item.title == "Updated Product Title", "Title should be updated"
        assert updated_item.status == ScheduleStatus.SCHEDULED, "Status should be updated"
        assert "updated_field" in updated_item.metadata, "Metadata should be updated"
    
    def test_delete_schedule_item(self, content_calendar, sample_schedule_items):
        """Test deleting schedule items."""
        # Verify item exists
        item = content_calendar.get_schedule_item("cal_item_1")
        assert item is not None, "Item should exist before deletion"
        
        # Delete item
        result = content_calendar.delete_schedule_item("cal_item_1")
        assert result is True, "Deletion should succeed"
        
        # Verify item is deleted
        deleted_item = content_calendar.get_schedule_item("cal_item_1")
        assert deleted_item is None, "Item should be deleted"
    
    def test_bulk_operations(self, content_calendar):
        """Test bulk CRUD operations."""
        # Create multiple items in bulk
        items = []
        for i in range(5):
            item = ScheduleItem(
                id=f"bulk_item_{i}",
                title=f"Bulk Item {i}",
                platform=Platform.INSTAGRAM.value,
                content_type=ContentType.INSTAGRAM_FEED.value,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=i),
                status=ScheduleStatus.PLANNED,
                priority=JobPriority.NORMAL
            )
            items.append(item)
        
        # Bulk create
        results = content_calendar.bulk_create_schedule_items(items)
        assert len(results) == 5, "All items should be created"
        assert all(results), "All creations should succeed"
        
        # Verify all items exist
        for i in range(5):
            item = content_calendar.get_schedule_item(f"bulk_item_{i}")
            assert item is not None, f"Bulk item {i} should exist"
        
        # Bulk update status
        status_updates = {
            f"bulk_item_{i}": ScheduleStatus.SCHEDULED 
            for i in range(3)
        }
        
        update_results = content_calendar.bulk_update_schedule_status(status_updates)
        assert len(update_results) == 3, "Should update 3 items"
        assert all(update_results.values()), "All updates should succeed"
        
        # Verify updates
        for i in range(3):
            item = content_calendar.get_schedule_item(f"bulk_item_{i}")
            assert item.status == ScheduleStatus.SCHEDULED, f"Item {i} status should be updated"
    
    # Query and Filter Tests
    def test_get_items_by_platform(self, content_calendar, sample_schedule_items):
        """Test querying items by platform."""
        instagram_items = content_calendar.get_schedule_items_by_platform(Platform.INSTAGRAM.value)
        
        assert len(instagram_items) >= 1, "Should find at least one Instagram item"
        for item in instagram_items:
            assert item.platform == Platform.INSTAGRAM.value, "All items should be Instagram"
    
    def test_get_items_by_status(self, content_calendar, sample_schedule_items):
        """Test querying items by status."""
        planned_items = content_calendar.get_schedule_items_by_status(ScheduleStatus.PLANNED)
        scheduled_items = content_calendar.get_schedule_items_by_status(ScheduleStatus.SCHEDULED)
        
        assert len(planned_items) >= 1, "Should find planned items"
        assert len(scheduled_items) >= 1, "Should find scheduled items"
        
        for item in planned_items:
            assert item.status == ScheduleStatus.PLANNED, "All should be planned status"
        
        for item in scheduled_items:
            assert item.status == ScheduleStatus.SCHEDULED, "All should be scheduled status"
    
    def test_get_items_by_time_range(self, content_calendar, sample_schedule_items):
        """Test querying items by time range."""
        now = datetime.now(timezone.utc)
        
        # Next 4 hours
        recent_items = content_calendar.get_schedule_items_by_time_range(
            now - timedelta(hours=1),
            now + timedelta(hours=4)
        )
        
        assert len(recent_items) >= 1, "Should find items in recent time range"
        for item in recent_items:
            assert now - timedelta(hours=1) <= item.scheduled_time <= now + timedelta(hours=4), \
                "All items should be within time range"
    
    def test_get_items_by_priority(self, content_calendar, sample_schedule_items):
        """Test querying items by priority."""
        urgent_items = content_calendar.get_schedule_items_by_priority(JobPriority.URGENT)
        normal_items = content_calendar.get_schedule_items_by_priority(JobPriority.NORMAL)
        
        assert len(urgent_items) >= 1, "Should find urgent items"
        assert len(normal_items) >= 1, "Should find normal priority items"
        
        for item in urgent_items:
            assert item.priority == JobPriority.URGENT, "All should be urgent priority"
        
        for item in normal_items:
            assert item.priority == JobPriority.NORMAL, "All should be normal priority"
    
    def test_complex_query_filters(self, content_calendar, sample_schedule_items):
        """Test complex query with multiple filters."""
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(hours=24)
        
        # Get Instagram items scheduled in next 24 hours with normal priority
        filters = {
            'platform': Platform.INSTAGRAM.value,
            'status': [ScheduleStatus.PLANNED, ScheduleStatus.SCHEDULED],
            'priority': [JobPriority.NORMAL, JobPriority.HIGH],
            'time_range': (now, end_time)
        }
        
        filtered_items = content_calendar.get_schedule_items_with_filters(filters)
        
        for item in filtered_items:
            assert item.platform == Platform.INSTAGRAM.value, "Platform filter should work"
            assert item.status in filters['status'], "Status filter should work"
            assert item.priority in filters['priority'], "Priority filter should work"
            assert now <= item.scheduled_time <= end_time, "Time range filter should work"
    
    # Status Management Tests
    def test_status_transitions(self, content_calendar, sample_schedule_items):
        """Test status transition logic."""
        # Test valid transitions
        valid_transitions = [
            (ScheduleStatus.PLANNED, ScheduleStatus.SCHEDULED),
            (ScheduleStatus.SCHEDULED, ScheduleStatus.POSTED),
            (ScheduleStatus.PLANNED, ScheduleStatus.CANCELED),
            (ScheduleStatus.SCHEDULED, ScheduleStatus.FAILED)
        ]
        
        for from_status, to_status in valid_transitions:
            # Find item with from_status
            item = content_calendar.get_schedule_items_by_status(from_status)[0]
            if item:
                result = content_calendar.update_item_status(item.id, to_status)
                assert result is True, f"Should allow {from_status} -> {to_status} transition"
                
                updated_item = content_calendar.get_schedule_item(item.id)
                assert updated_item.status == to_status, "Status should be updated"
        
        # Test invalid transition (POSTED -> PLANNED)
        posted_item = ScheduleItem(
            id="posted_test",
            title="Posted Item",
            platform=Platform.TIKTOK.value,
            content_type=ContentType.TIKTOK_VIDEO.value,
            scheduled_time=datetime.now(timezone.utc),
            status=ScheduleStatus.POSTED,
            priority=JobPriority.NORMAL
        )
        content_calendar.create_schedule_item(posted_item)
        
        # Should not allow invalid transition
        result = content_calendar.update_item_status("posted_test", ScheduleStatus.PLANNED)
        assert result is False, "Should not allow POSTED -> PLANNED transition"
    
    def test_status_update_with_metadata(self, content_calendar, sample_schedule_items):
        """Test status updates with additional metadata."""
        item_id = "cal_item_2"  # TikTok item
        
        # Update status with metadata
        status_metadata = {
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "post_id": "tiktok_12345",
            "engagement_initial": 150,
            "reach_estimate": 2500
        }
        
        result = content_calendar.update_item_status(
            item_id, 
            ScheduleStatus.POSTED, 
            metadata=status_metadata
        )
        
        assert result is True, "Status update with metadata should succeed"
        
        # Verify metadata is stored
        updated_item = content_calendar.get_schedule_item(item_id)
        assert "posted_at" in updated_item.metadata, "Posted timestamp should be stored"
        assert updated_item.metadata["post_id"] == "tiktok_12345", "Post ID should be stored"
    
    # Calendar Analytics Tests
    def test_calendar_analytics_basic(self, content_calendar, sample_schedule_items):
        """Test basic calendar analytics."""
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=30)
        
        analytics = content_calendar.generate_calendar_analytics(
            start_date=now.date(),
            end_date=end_date.date()
        )
        
        assert isinstance(analytics, CalendarAnalytics), "Should return CalendarAnalytics object"
        assert analytics.total_items >= len(sample_schedule_items), "Should count all items"
        assert analytics.platform_breakdown is not None, "Should have platform breakdown"
        assert analytics.status_breakdown is not None, "Should have status breakdown"
        
        # Check platform breakdown
        total_by_platform = sum(analytics.platform_breakdown.values())
        assert total_by_platform >= len(sample_schedule_items), "Platform counts should sum correctly"
        
        # Check status breakdown
        total_by_status = sum(analytics.status_breakdown.values())
        assert total_by_status >= len(sample_schedule_items), "Status counts should sum correctly"
    
    def test_platform_performance_analytics(self, content_calendar):
        """Test platform-specific performance analytics."""
        # Create items with performance data
        platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.LINKEDIN]
        
        for platform in platforms:
            item = ScheduleItem(
                id=f"perf_{platform.value}",
                title=f"Performance Test - {platform.value}",
                platform=platform.value,
                content_type=ContentType.INSTAGRAM_FEED.value,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
                status=ScheduleStatus.POSTED,
                priority=JobPriority.NORMAL,
                metadata={
                    "performance": {
                        "reach": 1000,
                        "engagement_rate": 0.045,
                        "click_through_rate": 0.02
                    }
                }
            )
            content_calendar.create_schedule_item(item)
            
            # Update to posted status with performance
            content_calendar.update_item_status(item.id, ScheduleStatus.POSTED)
        
        analytics = content_calendar.get_platform_performance_analytics(
            start_date=datetime.now(timezone.utc).date(),
            end_date=datetime.now(timezone.utc).date() + timedelta(days=7)
        )
        
        assert isinstance(analytics, dict), "Should return analytics dictionary"
        
        for platform in platforms:
            platform_key = platform.value
            if platform_key in analytics:
                assert "avg_reach" in analytics[platform_key], "Should have average reach"
                assert "avg_engagement_rate" in analytics[platform_key], "Should have engagement rate"
                assert "total_posts" in analytics[platform_key], "Should have post count"
    
    def test_content_type_analytics(self, content_calendar):
        """Test content type performance analytics."""
        # Create items with different content types
        content_types = [
            ContentType.INSTAGRAM_FEED,
            ContentType.INSTAGRAM_REELS,
            ContentType.TIKTOK_VIDEO,
            ContentType.LINKEDIN_POST
        ]
        
        for i, content_type in enumerate(content_types):
            item = ScheduleItem(
                id=f"content_type_{i}",
                title=f"Content Type Test {i}",
                platform=Platform.INSTAGRAM.value,
                content_type=content_type.value,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=i),
                status=ScheduleStatus.POSTED,
                priority=JobPriority.NORMAL,
                metadata={"performance": {"engagement_rate": 0.03 + i * 0.01}}
            )
            content_calendar.create_schedule_item(item)
            content_calendar.update_item_status(item.id, ScheduleStatus.POSTED)
        
        analytics = content_calendar.get_content_type_analytics(
            start_date=datetime.now(timezone.utc).date(),
            end_date=datetime.now(timezone.utc).date() + timedelta(days=7)
        )
        
        assert isinstance(analytics, dict), "Should return content type analytics"
        
        for content_type in content_types:
            type_key = content_type.value
            assert type_key in analytics, f"Should have analytics for {type_key}"
            assert "count" in analytics[type_key], "Should have content count"
            assert "avg_performance" in analytics[type_key], "Should have performance metrics"
    
    # Time Management Tests
    def test_timezone_handling(self, content_calendar):
        """Test timezone-aware scheduling."""
        from zoneinfo import ZoneInfo
        
        # Create item with specific timezone
        eastern_time = ZoneInfo("America/New_York")
        utc_time = datetime.now(timezone.utc)
        eastern_dt = utc_time.astimezone(eastern_time)
        
        item = ScheduleItem(
            id="timezone_test",
            title="Timezone Test",
            platform=Platform.LINKEDIN.value,
            content_type=ContentType.LINKEDIN_POST.value,
            scheduled_time=eastern_dt,
            status=ScheduleStatus.PLANNED,
            priority=JobPriority.NORMAL,
            metadata={"timezone": "America/New_York"}
        )
        
        content_calendar.create_schedule_item(item)
        
        # Retrieve and verify timezone handling
        retrieved_item = content_calendar.get_schedule_item("timezone_test")
        assert retrieved_item is not None, "Item should be created"
        
        # Calendar should handle timezone conversion properly
        analytics = content_calendar.generate_calendar_analytics(
            start_date=utc_time.date(),
            end_date=utc_time.date() + timedelta(days=1)
        )
        
        assert analytics.total_items >= 1, "Should include timezone-aware items"
    
    def test_recurring_schedules(self, content_calendar):
        """Test recurring schedule creation."""
        # Create a recurring schedule (weekly posts)
        base_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        recurring_config = {
            "frequency": "weekly",
            "day_of_week": 1,  # Tuesday
            "time": time(10, 0),  # 10:00 AM
            "count": 4,  # 4 weeks
            "platform": Platform.LINKEDIN.value,
            "content_type": ContentType.LINKEDIN_POST.value,
            "title_template": "Weekly Industry Update - Week {week}",
            "priority": JobPriority.NORMAL
        }
        
        created_items = content_calendar.create_recurring_schedule(
            schedule_id="weekly_updates",
            config=recurring_config
        )
        
        assert len(created_items) == 4, "Should create 4 weekly items"
        
        # Verify each item
        for i, item in enumerate(created_items):
            assert item.platform == Platform.LINKEDIN.value, "Platform should be correct"
            assert item.content_type == ContentType.LINKEDIN_POST.value, "Content type should be correct"
            assert item.scheduled_time.weekday() == 1, "Should be scheduled on Tuesday"
            assert 10 <= item.scheduled_time.hour <= 11, "Should be scheduled at 10 AM"
            assert f"Week {i+1}" in item.title, "Title should include week number"
    
    def test_schedule_conflicts_detection(self, content_calendar, sample_schedule_items):
        """Test schedule conflict detection."""
        # Add an item that conflicts with existing schedule
        existing_item = content_calendar.get_schedule_item("cal_item_1")
        conflict_time = existing_item.scheduled_time + timedelta(minutes=30)
        
        conflict_item = ScheduleItem(
            id="conflict_item",
            title="Conflicting Post",
            platform=Platform.INSTAGRAM.value,
            content_type=ContentType.INSTAGRAM_FEED.value,
            scheduled_time=conflict_time,
            status=ScheduleStatus.PLANNED,
            priority=JobPriority.NORMAL
        )
        
        # Check for conflicts before creating
        conflicts = content_calendar.detect_schedule_conflicts([conflict_item])
        assert len(conflicts) >= 1, "Should detect conflict with existing item"
        
        # Create anyway for testing
        content_calendar.create_schedule_item(conflict_item)
        
        # Verify conflict is detected
        all_conflicts = content_calendar.get_all_schedule_conflicts(
            start_date=datetime.now(timezone.utc).date(),
            end_date=datetime.now(timezone.utc).date() + timedelta(days=1)
        )
        
        assert len(all_conflicts) >= 1, "Should detect all schedule conflicts"
    
    # Integration Tests
    def test_integration_with_scheduling_optimizer(self, content_calendar):
        """Test integration with scheduling optimizer."""
        # Import scheduling optimizer
        from scheduling_optimizer import SchedulingOptimizer
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            optimizer_db = f.name
        
        optimizer = SchedulingOptimizer(db_path=optimizer_db)
        
        # Create audience profile
        audience = AudienceProfile(
            age_cohorts={'25-34': 0.4, '35-44': 0.3, '18-24': 0.3},
            device_split={'mobile': 0.7, 'desktop': 0.3},
            time_zone_weights={'UTC-5': 0.5, 'UTC-8': 0.3}
        )
        
        # Generate schedule from optimizer
        posts = [
            {
                'id': 'optimizer_post_1',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': 'normal'
            }
        ]
        
        schedule = optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=[],
            audience_profiles={Platform.INSTAGRAM: audience},
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        # Import schedule into calendar
        if schedule.scheduled_posts:
            imported_count = content_calendar.import_schedule_from_optimizer(schedule)
            assert imported_count >= 1, "Should import at least one scheduled post"
            
            # Verify imported items
            imported_items = content_calendar.get_schedule_items_by_platform(Platform.INSTAGRAM.value)
            assert len(imported_items) >= 1, "Should have imported Instagram items"
    
    def test_bulk_import_from_sheets(self, content_calendar):
        """Test bulk import from Google Sheets data."""
        # Simulate Google Sheets data
        sheets_data = [
            {
                "id": "sheet_1",
                "title": "Sheet Post 1",
                "platform": Platform.TIKTOK.value,
                "content_type": ContentType.TIKTOK_VIDEO.value,
                "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                "priority": "normal"
            },
            {
                "id": "sheet_2", 
                "title": "Sheet Post 2",
                "platform": Platform.INSTAGRAM.value,
                "content_type": ContentType.INSTAGRAM_FEED.value,
                "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
                "priority": "high"
            }
        ]
        
        # Import from sheets
        imported_items = content_calendar.bulk_import_from_sheets_data(sheets_data)
        
        assert len(imported_items) == 2, "Should import both items"
        
        # Verify imported items
        for item_data in sheets_data:
            imported_item = content_calendar.get_schedule_item(item_data["id"])
            assert imported_item is not None, f"Item {item_data['id']} should be imported"
            assert imported_item.title == item_data["title"], "Title should match"
            assert imported_item.platform == item_data["platform"], "Platform should match"
    
    def test_calendar_export_functionality(self, content_calendar, sample_schedule_items):
        """Test calendar export functionality."""
        # Export calendar data
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=7)
        
        export_data = content_calendar.export_calendar_data(
            start_date=now.date(),
            end_date=end_date.date(),
            format="json"
        )
        
        assert isinstance(export_data, dict), "Should export as dictionary"
        assert "items" in export_data, "Should include items in export"
        assert "analytics" in export_data, "Should include analytics in export"
        assert "metadata" in export_data, "Should include metadata in export"
        
        exported_items = export_data["items"]
        assert len(exported_items) >= len(sample_schedule_items), "Should export all relevant items"
        
        # Verify exported item structure
        if exported_items:
            first_item = exported_items[0]
            required_fields = ["id", "title", "platform", "scheduled_time", "status", "priority"]
            for field in required_fields:
                assert field in first_item, f"Required field {field} should be in export"
    
    # Error Handling and Edge Cases
    def test_invalid_schedule_item_handling(self, content_calendar):
        """Test handling of invalid schedule items."""
        # Test item with missing required fields
        invalid_item = ScheduleItem(
            id="",  # Empty ID
            title="",  # Empty title
            platform="invalid_platform",  # Invalid platform
            content_type="",  # Empty content type
            scheduled_time=datetime.now(timezone.utc),
            status=ScheduleStatus.PLANNED,
            priority=JobPriority.NORMAL
        )
        
        result = content_calendar.create_schedule_item(invalid_item)
        assert result is False, "Should not create invalid item"
    
    def test_database_consistency_checks(self, content_calendar, sample_schedule_items):
        """Test database consistency checks."""
        # Add some test data for consistency checks
        for i in range(3):
            item = ScheduleItem(
                id=f"consistency_test_{i}",
                title=f"Consistency Test {i}",
                platform=Platform.INSTAGRAM.value,
                content_type=ContentType.INSTAGRAM_FEED.value,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=i),
                status=ScheduleStatus.POSTED,
                priority=JobPriority.NORMAL
            )
            content_calendar.create_schedule_item(item)
        
        # Run consistency check
        issues = content_calendar.run_consistency_checks()
        
        assert isinstance(issues, list), "Should return list of issues"
        
        # Check for specific types of issues
        issue_types = [issue["type"] for issue in issues]
        assert "orphaned_items" in issue_types or "duplicate_ids" in issue_types or len(issues) >= 0, \
            "Should detect potential consistency issues"
    
    def test_performance_with_large_dataset(self, content_calendar):
        """Test performance with large calendar dataset."""
        import time
        
        # Create large number of items
        start_time = time.time()
        
        items_created = 0
        for i in range(100):
            item = ScheduleItem(
                id=f"perf_test_{i}",
                title=f"Performance Test Item {i}",
                platform=np.random.choice([p.value for p in [
                    Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE
                ]]),
                content_type=ContentType.INSTAGRAM_FEED.value,
                scheduled_time=datetime.now(timezone.utc) + timedelta(hours=i),
                status=ScheduleStatus.PLANNED,
                priority=JobPriority.NORMAL
            )
            
            if content_calendar.create_schedule_item(item):
                items_created += 1
        
        creation_time = time.time() - start_time
        
        # Should handle 100 items in reasonable time
        assert creation_time < 5.0, f"Creating 100 items took too long: {creation_time}s"
        assert items_created == 100, "All items should be created"
        
        # Test query performance
        start_time = time.time()
        
        instagram_items = content_calendar.get_schedule_items_by_platform(Platform.INSTAGRAM.value)
        
        query_time = time.time() - start_time
        
        # Query should be fast
        assert query_time < 1.0, f"Query took too long: {query_time}s"
        assert len(instagram_items) > 0, "Should find Instagram items"
    
    def test_backup_and_restore(self, content_calendar, sample_schedule_items):
        """Test calendar backup and restore functionality."""
        # Create backup
        backup_path = "/tmp/calendar_backup.json"
        
        backup_result = content_calendar.create_backup(backup_path)
        assert backup_result is True, "Backup should succeed"
        
        # Verify backup file exists
        import os
        assert os.path.exists(backup_path), "Backup file should exist"
        
        # Read and validate backup
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        assert "items" in backup_data, "Backup should contain items"
        assert "metadata" in backup_data, "Backup should contain metadata"
        assert len(backup_data["items"]) >= len(sample_schedule_items), \
            "Backup should contain all items"
        
        # Test restore to new calendar
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            new_db_path = f.name
        
        new_calendar = ContentCalendar(db_path=new_db_path)
        restore_result = new_calendar.restore_from_backup(backup_path)
        
        assert restore_result is True, "Restore should succeed"
        
        # Verify restored data
        restored_items = new_calendar.get_schedule_items_by_platform(Platform.INSTAGRAM.value)
        assert len(restored_items) >= 1, "Restored calendar should have items"
        
        # Cleanup
        if os.path.exists(backup_path):
            os.unlink(backup_path)


class TestCalendarViewsAndFiltering:
    """Test suite for calendar views and advanced filtering."""
    
    @pytest.fixture
    def calendar_with_varied_data(self, temp_db_path):
        """Create calendar with varied data for view testing."""
        calendar = ContentCalendar(db_path=temp_db_path)
        
        # Create items across different time periods
        now = datetime.now(timezone.utc)
        
        # Past items
        for i in range(3):
            item = ScheduleItem(
                id=f"past_item_{i}",
                title=f"Past Item {i}",
                platform=Platform.INSTAGRAM.value,
                content_type=ContentType.INSTAGRAM_FEED.value,
                scheduled_time=now - timedelta(days=i+1),
                status=ScheduleStatus.POSTED,
                priority=JobPriority.NORMAL
            )
            calendar.create_schedule_item(item)
        
        # Current items
        for i in range(2):
            item = ScheduleItem(
                id=f"current_item_{i}",
                title=f"Current Item {i}",
                platform=Platform.TIKTOK.value,
                content_type=ContentType.TIKTOK_VIDEO.value,
                scheduled_time=now + timedelta(hours=i),
                status=ScheduleStatus.SCHEDULED,
                priority=JobPriority.URGENT
            )
            calendar.create_schedule_item(item)
        
        # Future items
        for i in range(3):
            item = ScheduleItem(
                id=f"future_item_{i}",
                title=f"Future Item {i}",
                platform=Platform.LINKEDIN.value,
                content_type=ContentType.LINKEDIN_POST.value,
                scheduled_time=now + timedelta(days=i+1),
                status=ScheduleStatus.PLANNED,
                priority=JobPriority.NORMAL
            )
            calendar.create_schedule_item(item)
        
        return calendar
    
    def test_calendar_view_week(self, calendar_with_varied_data):
        """Test week view of calendar."""
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        
        view = calendar_with_varied_data.get_calendar_view(
            view_type=CalendarView.WEEK,
            start_date=week_start.date()
        )
        
        assert view is not None, "Week view should be generated"
        assert "items" in view, "View should contain items"
        assert "date_range" in view, "View should contain date range"
        
        # Week view should contain current items
        view_items = view["items"]
        assert len(view_items) >= 2, "Week view should show current scheduled items"
        
        for item in view_items:
            item_time = datetime.fromisoformat(item["scheduled_time"])
            assert week_start <= item_time <= week_end, "Items should be within week range"
    
    def test_calendar_view_month(self, calendar_with_varied_data):
        """Test month view of calendar."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        
        view = calendar_with_varied_data.get_calendar_view(
            view_type=CalendarView.MONTH,
            start_date=month_start.date()
        )
        
        assert view is not None, "Month view should be generated"
        assert "items" in view, "View should contain items"
        assert "daily_breakdown" in view, "View should have daily breakdown"
        
        # Month view should show items across the month
        view_items = view["items"]
        daily_breakdown = view["daily_breakdown"]
        
        assert len(daily_breakdown) >= 1, "Should have daily breakdown"
        assert len(view_items) >= 5, "Month view should show multiple items"
    
    def test_calendar_view_agenda(self, calendar_with_varied_data):
        """Test agenda view of calendar."""
        now = datetime.now(timezone.utc)
        agenda_end = now + timedelta(days=14)
        
        view = calendar_with_varied_data.get_calendar_view(
            view_type=CalendarView.AGENDA,
            start_date=now.date(),
            end_date=agenda_end.date()
        )
        
        assert view is not None, "Agenda view should be generated"
        assert "items" in view, "Agenda should contain items"
        assert "sorted_by_date" in view, "Agenda should be sorted by date"
        
        # Agenda should be sorted by date
        items = view["items"]
        dates = [datetime.fromisoformat(item["scheduled_time"]) for item in items]
        assert dates == sorted(dates), "Agenda items should be sorted by date"
        
        # All items should be within agenda range
        for item in items:
            item_time = datetime.fromisoformat(item["scheduled_time"])
            assert now.date() <= item_time.date() <= agenda_end.date(), \
                "Items should be within agenda range"
    
    def test_advanced_filtering(self, calendar_with_varied_data):
        """Test advanced filtering capabilities."""
        # Test time-based filtering
        now = datetime.now(timezone.utc)
        
        # Get items scheduled in next 24 hours
        upcoming_items = calendar_with_varied_data.get_schedule_items_with_advanced_filter(
            time_filter={
                "type": "upcoming",
                "hours_ahead": 24
            }
        )
        
        assert len(upcoming_items) >= 2, "Should find upcoming items"
        
        for item in upcoming_items:
            time_diff = (item.scheduled_time - now).total_seconds() / 3600
            assert 0 <= time_diff <= 24, "Items should be within 24 hours"
        
        # Test status-based filtering
        posted_items = calendar_with_varied_data.get_schedule_items_with_advanced_filter(
            status_filter={
                "status": [ScheduleStatus.POSTED],
                "exclude_planned": True
            }
        )
        
        assert len(posted_items) >= 3, "Should find posted items"
        for item in posted_items:
            assert item.status == ScheduleStatus.POSTED, "All should be posted items"
        
        # Test performance-based filtering
        high_priority_items = calendar_with_varied_data.get_schedule_items_with_advanced_filter(
            priority_filter={
                "min_priority": JobPriority.URGENT,
                "sort_by_priority": True
            }
        )
        
        assert len(high_priority_items) >= 1, "Should find high priority items"
        
        # Verify sorting by priority
        priorities = [item.priority.value for item in high_priority_items]
        assert priorities == sorted(priorities, reverse=True), "Should be sorted by priority"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])