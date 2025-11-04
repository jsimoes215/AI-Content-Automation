"""
Content Calendar Integration System

This module implements a comprehensive content calendar system that integrates with the
bulk job creation workflow to provide:

1. Content calendar management and scheduling
2. Integration with bulk job creation workflow  
3. Automated schedule generation for video content
4. Cross-platform content coordination
5. Calendar analytics and optimization

The system follows the database schema design from docs/scheduling_system/database_schema.md
and integrates with existing bulk job patterns (VideoJob, BulkJob, JobStatus).

Author: AI Content Automation System
Version: 1.0.0
"""

import json
import logging
import uuid
import hashlib
import asyncio
from datetime import datetime, timezone, timedelta, time
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from decimal import Decimal
from collections import defaultdict, Counter
import statistics
import sqlite3
from pathlib import Path

# Import existing system components
from batch_processor import VideoJob, BulkJob, JobStatus, JobPriority
from data_validation import ValidationResult, DataValidationPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduleStatus(Enum):
    """Content schedule item status states."""
    PLANNED = "planned"
    SCHEDULED = "scheduled" 
    POSTED = "posted"
    FAILED = "failed"
    CANCELED = "canceled"


class ContentFormat(Enum):
    """Supported content formats for different platforms."""
    # YouTube formats
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_SHORTS = "youtube_shorts"
    
    # TikTok formats  
    TIKTOK_VIDEO = "tiktok_video"
    
    # Instagram formats
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_STORIES = "instagram_stories"
    
    # X (Twitter) formats
    X_TWEET = "x_tweet"
    X_THREAD = "x_thread"
    
    # LinkedIn formats
    LINKEDIN_POST = "linkedin_post"
    LINKEDIN_ARTICLE = "linkedin_article"
    
    # Facebook formats
    FACEBOOK_POST = "facebook_post"
    FACEBOOK_REELS = "facebook_reels"


class PlatformId(Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    X = "x"  # Twitter
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class ExceptionType(Enum):
    """Types of schedule exceptions."""
    BLACKOUT_WINDOW = "blackout_window"
    MANUAL_OVERRIDE = "manual_override"
    TECHNICAL_MAINTENANCE = "technical_maintenance"
    COMPLIANCE_LOCKDOWN = "compliance_lockdown"
    HOLIDAY_OBSERVANCE = "holiday_observance"
    PLATFORM_OUTAGE = "platform_outage"


@dataclass
class PlatformTimingData:
    """Platform timing data for scheduling optimization."""
    platform_id: PlatformId
    days: List[str]
    peak_hours: List[Dict[str, int]]  # [{"start": 15, "end": 17}]
    posting_frequency_min: int
    posting_frequency_max: int
    audience_segment: Optional[str] = None
    content_format: Optional[str] = None
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_to: Optional[datetime] = None
    source: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class UserSchedulingPreferences:
    """User-level scheduling preferences and settings."""
    user_id: str
    platform_id: Optional[PlatformId] = None
    timezone: str = "UTC"
    posting_frequency_min: Optional[int] = None
    posting_frequency_max: Optional[int] = None
    days_blacklist: List[str] = field(default_factory=list)
    hours_blacklist: List[Dict[str, int]] = field(default_factory=list)
    content_format: Optional[str] = None
    quality_threshold: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentScheduleItem:
    """Individual content schedule item."""
    id: str
    calendar_id: str
    video_job_id: str
    bulk_job_id: Optional[str]
    platform_id: PlatformId
    content_format: str
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    timezone: str = "UTC"
    status: ScheduleStatus = ScheduleStatus.PLANNED
    idempotency_key: Optional[str] = None
    dedupe_key: Optional[str] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ScheduleAssignment:
    """Worker-facing schedule assignment."""
    id: str
    schedule_item_id: str
    worker_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: ScheduleStatus = ScheduleStatus.PLANNED
    last_error: Optional[str] = None
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ScheduleException:
    """Schedule exception or blackout window."""
    id: str
    schedule_item_id: Optional[str] = None
    exception_type: ExceptionType = ExceptionType.BLACKOUT_WINDOW
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    window_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PerformanceKPIEvent:
    """Performance KPI event data."""
    id: str
    video_job_id: str
    platform_id: PlatformId
    content_format: Optional[str] = None
    event_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ingestion_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    views: Optional[int] = None
    impressions: Optional[int] = None
    watch_time_seconds: Optional[int] = None
    engagement_rate: Optional[float] = None
    clicks: Optional[int] = None
    saves: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None
    followers_delta: Optional[int] = None
    scheduled_slot_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OptimizationTrial:
    """A/B testing trial for scheduling optimization."""
    id: str
    user_id: str
    trial_id: str
    hypothesis: str
    start_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_at: Optional[datetime] = None
    variants: Dict[str, Any] = field(default_factory=dict)
    primary_kpi: str = ""
    guardrails: Dict[str, Any] = field(default_factory=dict)
    results_summary: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ContentCalendar:
    """Content calendar grouping schedule items."""
    id: str
    name: str
    description: Optional[str] = None
    timezone: str = "UTC"
    bulk_job_id: Optional[str] = None
    created_by: str = ""
    owned_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CalendarAnalytics:
    """Calendar analytics and optimization insights."""
    total_scheduled: int = 0
    total_posted: int = 0
    total_failed: int = 0
    average_engagement_rate: float = 0.0
    best_performing_times: List[Dict[str, Any]] = field(default_factory=list)
    platform_distribution: Dict[PlatformId, int] = field(default_factory=dict)
    content_format_performance: Dict[str, float] = field(default_factory=dict)
    optimization_recommendations: List[str] = field(default_factory=list)


class ContentCalendarManager:
    """
    Main content calendar management system.
    
    Provides comprehensive content calendar functionality including:
    - Calendar creation and management
    - Schedule generation and optimization  
    - Bulk job integration
    - Cross-platform coordination
    - Analytics and reporting
    """
    
    def __init__(self, storage_path: str = "data/content_calendar.db"):
        """Initialize content calendar manager."""
        self.storage_path = storage_path
        self.storage_dir = Path(storage_path).parent
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_storage()
        self._platform_timing_cache: Dict[PlatformId, List[PlatformTimingData]] = {}
        self._user_preferences_cache: Dict[str, List[UserSchedulingPreferences]] = {}
        
        # Initialize default platform timing data
        self._seed_platform_timing_data()
        
    def _init_storage(self) -> None:
        """Initialize SQLite storage for content calendar data."""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        # Content calendars table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_calendars (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                timezone TEXT DEFAULT 'UTC',
                bulk_job_id TEXT,
                created_by TEXT NOT NULL,
                owned_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Content schedule items table  
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_schedule_items (
                id TEXT PRIMARY KEY,
                calendar_id TEXT NOT NULL,
                video_job_id TEXT NOT NULL,
                bulk_job_id TEXT,
                platform_id TEXT NOT NULL,
                content_format TEXT,
                planned_start TIMESTAMP,
                planned_end TIMESTAMP,
                scheduled_at TIMESTAMP,
                timezone TEXT DEFAULT 'UTC',
                status TEXT NOT NULL CHECK (status IN ('planned', 'scheduled', 'posted', 'failed', 'canceled')),
                idempotency_key TEXT,
                dedupe_key TEXT,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (created_by, video_job_id, platform_id, COALESCE(scheduled_at, '1970-01-01T00:00:00'))
            )
        """)
        
        # Schedule assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_assignments (
                id TEXT PRIMARY KEY,
                schedule_item_id TEXT NOT NULL,
                worker_id TEXT,
                scheduled_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('planned', 'scheduled', 'posted', 'failed', 'canceled')),
                last_error TEXT,
                retry_count INTEGER DEFAULT 0,
                last_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Schedule exceptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_exceptions (
                id TEXT PRIMARY KEY,
                schedule_item_id TEXT,
                exception_type TEXT NOT NULL,
                window_start TIMESTAMP NOT NULL,
                window_end TIMESTAMP NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance KPI events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_kpi_events (
                id TEXT PRIMARY KEY,
                video_job_id TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                content_format TEXT,
                event_time TIMESTAMP NOT NULL,
                ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER,
                impressions INTEGER,
                watch_time_seconds INTEGER,
                engagement_rate REAL,
                clicks INTEGER,
                saves INTEGER,
                shares INTEGER,
                comments INTEGER,
                followers_delta INTEGER,
                scheduled_slot_id TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Optimization trials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_trials (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                trial_id TEXT UNIQUE NOT NULL,
                hypothesis TEXT NOT NULL,
                start_at TIMESTAMP NOT NULL,
                end_at TIMESTAMP,
                variants TEXT NOT NULL,
                primary_kpi TEXT NOT NULL,
                guardrails TEXT,
                results_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Platform timing data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_timing_data (
                id TEXT PRIMARY KEY,
                platform_id TEXT NOT NULL,
                days TEXT NOT NULL,
                peak_hours TEXT NOT NULL,
                posting_frequency_min INTEGER,
                posting_frequency_max INTEGER,
                audience_segment TEXT,
                content_format TEXT,
                valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                valid_to TIMESTAMP,
                source TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User scheduling preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_scheduling_preferences (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                platform_id TEXT,
                timezone TEXT NOT NULL,
                posting_frequency_min INTEGER,
                posting_frequency_max INTEGER,
                days_blacklist TEXT,
                hours_blacklist TEXT,
                content_format TEXT,
                quality_threshold REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, COALESCE(platform_id, ''), COALESCE(content_format, ''))
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sched_items_calendar_status ON content_schedule_items (calendar_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_sched_items_platform_status ON content_schedule_items (platform_id, status)", 
            "CREATE INDEX IF NOT EXISTS idx_sched_items_video_job ON content_schedule_items (video_job_id)",
            "CREATE INDEX IF NOT EXISTS idx_sched_items_created_by ON content_schedule_items (created_by, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_assignments_status_active ON schedule_assignments (status) WHERE status IN ('planned', 'scheduled')",
            "CREATE INDEX IF NOT EXISTS idx_assignments_schedule_time ON schedule_assignments (scheduled_at)",
            "CREATE INDEX IF NOT EXISTS idx_kpi_video_time ON performance_kpi_events (video_job_id, event_time)",
            "CREATE INDEX IF NOT EXISTS idx_kpi_platform_time ON performance_kpi_events (platform_id, event_time)",
            "CREATE INDEX IF NOT EXISTS idx_kpi_format_time ON performance_kpi_events (content_format, event_time)",
            "CREATE INDEX IF NOT EXISTS idx_timing_platform_active ON platform_timing_data (platform_id) WHERE valid_to IS NULL"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            
        conn.commit()
        conn.close()
        
    def _seed_platform_timing_data(self) -> None:
        """Seed platform timing data based on research baselines."""
        default_timing_data = [
            # YouTube timing data
            PlatformTimingData(
                platform_id=PlatformId.YOUTUBE,
                days=["mon", "tue", "wed", "thu", "fri"],
                peak_hours=[{"start": 15, "end": 17}],
                posting_frequency_min=2,
                posting_frequency_max=3,
                source="Buffer 2025",
                notes="Weekdays 3-5 p.m. perform strongly, Wednesday 4 p.m. standout"
            ),
            PlatformTimingData(
                platform_id=PlatformId.YOUTUBE,
                days=["wed"],
                peak_hours=[{"start": 16, "end": 16}],
                posting_frequency_min=1,
                posting_frequency_max=1,
                content_format="youtube_shorts",
                source="Buffer 2025",
                notes="Daily Shorts for smaller channels"
            ),
            
            # TikTok timing data  
            PlatformTimingData(
                platform_id=PlatformId.TIKTOK,
                days=["wed"],
                peak_hours=[{"start": 14, "end": 18}],
                posting_frequency_min=2,
                posting_frequency_max=5,
                source="Buffer 2025",
                notes="Wednesday is best day, midweek afternoons/evenings reliable"
            ),
            PlatformTimingData(
                platform_id=PlatformId.TIKTOK,
                days=["sun"],
                peak_hours=[{"start": 20, "end": 20}],
                posting_frequency_min=1,
                posting_frequency_max=1,
                source="Buffer 2025", 
                notes="Sunday 8 p.m. peak"
            ),
            
            # Instagram timing data
            PlatformTimingData(
                platform_id=PlatformId.INSTAGRAM,
                days=["mon", "tue", "wed", "thu", "fri"],
                peak_hours=[{"start": 10, "end": 15}],
                posting_frequency_min=3,
                posting_frequency_max=5,
                content_format="instagram_feed",
                source="Later 2025",
                notes="Weekday mid-mornings through mid-afternoons"
            ),
            PlatformTimingData(
                platform_id=PlatformId.INSTAGRAM,
                days=["mon", "tue", "wed", "thu", "fri"],
                peak_hours=[{"start": 10, "end": 14}],
                posting_frequency_min=3,
                posting_frequency_max=5,
                content_format="instagram_reels",
                source="Later 2025",
                notes="Reels peaks include mid-morning to early afternoon"
            ),
            
            # X (Twitter) timing data
            PlatformTimingData(
                platform_id=PlatformId.X,
                days=["tue", "wed", "thu"],
                peak_hours=[{"start": 8, "end": 12}],
                posting_frequency_min=3,
                posting_frequency_max=5,
                source="Buffer 2025",
                notes="Weekday mornings, Tuesday-Thursday 8 a.m.-12 p.m."
            ),
            
            # LinkedIn timing data
            PlatformTimingData(
                platform_id=PlatformId.LINKEDIN,
                days=["tue", "wed", "thu"],
                peak_hours=[{"start": 8, "end": 14}],
                posting_frequency_min=2,
                posting_frequency_max=3,
                source="Sprout Social 2025",
                notes="Midweek midday windows (8 a.m.-2 p.m.) reliable"
            ),
            
            # Facebook timing data
            PlatformTimingData(
                platform_id=PlatformId.FACEBOOK,
                days=["mon", "tue", "wed", "thu", "fri"],
                peak_hours=[{"start": 8, "end": 18}],
                posting_frequency_min=3,
                posting_frequency_max=5,
                source="Sprout Social 2025",
                notes="Weekdays 8 a.m.-6 p.m., lighter Fridays"
            )
        ]
        
        for timing_data in default_timing_data:
            self.save_platform_timing_data(timing_data)
            
    def create_calendar(self, name: str, created_by: str, description: str = "", 
                       timezone: str = "UTC", bulk_job_id: Optional[str] = None) -> ContentCalendar:
        """Create a new content calendar."""
        calendar_id = str(uuid.uuid4())
        
        calendar = ContentCalendar(
            id=calendar_id,
            name=name,
            description=description,
            timezone=timezone,
            bulk_job_id=bulk_job_id,
            created_by=created_by,
            owned_by=created_by
        )
        
        # Store in database
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO content_calendars 
            (id, name, description, timezone, bulk_job_id, created_by, owned_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            calendar.id, calendar.name, calendar.description, calendar.timezone,
            calendar.bulk_job_id, calendar.created_by, calendar.owned_by
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created content calendar {calendar_id} for user {created_by}")
        return calendar
        
    def get_calendar(self, calendar_id: str) -> Optional[ContentCalendar]:
        """Retrieve content calendar by ID."""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM content_calendars WHERE id = ?", (calendar_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return ContentCalendar(
            id=row[0], name=row[1], description=row[2], timezone=row[3],
            bulk_job_id=row[4], created_by=row[5], owned_by=row[6],
            created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(timezone.utc)
        )
        
    def list_calendars(self, created_by: str, limit: int = 50) -> List[ContentCalendar]:
        """List content calendars for a user."""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM content_calendars 
            WHERE created_by = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (created_by, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        calendars = []
        for row in rows:
            calendars.append(ContentCalendar(
                id=row[0], name=row[1], description=row[2], timezone=row[3],
                bulk_job_id=row[4], created_by=row[5], owned_by=row[6],
                created_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(timezone.utc)
            ))
            
        return calendars
        
    def save_platform_timing_data(self, timing_data: PlatformTimingData) -> None:
        """Save platform timing data to database."""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO platform_timing_data 
            (id, platform_id, days, peak_hours, posting_frequency_min, posting_frequency_max,
             audience_segment, content_format, valid_from, valid_to, source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), timing_data.platform_id.value,
            json.dumps(timing_data.days), json.dumps(timing_data.peak_hours),
            timing_data.posting_frequency_min, timing_data.posting_frequency_max,
            timing_data.audience_segment, timing_data.content_format,
            timing_data.valid_from, timing_data.valid_to, 
            timing_data.source, timing_data.notes
        ))
        
        conn.commit()
        conn.close()
        
    def get_platform_timing_data(self, platform_id: PlatformId, 
                                content_format: Optional[str] = None) -> List[PlatformTimingData]:
        """Get active platform timing data."""
        # Check cache first
        cache_key = f"{platform_id.value}_{content_format or 'all'}"
        if cache_key in self._platform_timing_cache:
            return self._platform_timing_cache[cache_key]
            
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        if content_format:
            cursor.execute("""
                SELECT * FROM platform_timing_data 
                WHERE platform_id = ? AND content_format = ? AND valid_to IS NULL
                ORDER BY created_at DESC
            """, (platform_id.value, content_format))
        else:
            cursor.execute("""
                SELECT * FROM platform_timing_data 
                WHERE platform_id = ? AND valid_to IS NULL
                ORDER BY created_at DESC
            """, (platform_id.value,))
            
        rows = cursor.fetchall()
        conn.close()
        
        timing_data_list = []
        for row in rows:
            timing_data = PlatformTimingData(
                platform_id=PlatformId(row[1]),
                days=json.loads(row[2]),
                peak_hours=json.loads(row[3]),
                posting_frequency_min=row[4],
                posting_frequency_max=row[5],
                audience_segment=row[6],
                content_format=row[7],
                valid_from=datetime.fromisoformat(row[8]) if row[8] else datetime.now(timezone.utc),
                valid_to=datetime.fromisoformat(row[9]) if row[9] else None,
                source=row[10],
                notes=row[11]
            )
            timing_data_list.append(timing_data)
            
        # Cache the results
        self._platform_timing_cache[cache_key] = timing_data_list
        return timing_data_list
        
    def set_user_scheduling_preferences(self, preferences: UserSchedulingPreferences) -> None:
        """Save user scheduling preferences."""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_scheduling_preferences 
            (id, user_id, platform_id, timezone, posting_frequency_min, posting_frequency_max,
             days_blacklist, hours_blacklist, content_format, quality_threshold, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), preferences.user_id,
            preferences.platform_id.value if preferences.platform_id else None,
            preferences.timezone, preferences.posting_frequency_min, preferences.posting_frequency_max,
            json.dumps(preferences.days_blacklist), json.dumps(preferences.hours_blacklist),
            preferences.content_format, preferences.quality_threshold,
            json.dumps(preferences.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        # Clear cache for this user
        user_cache_keys = [key for key in self._user_preferences_cache.keys() 
                          if key.startswith(preferences.user_id)]
        for key in user_cache_keys:
            del self._user_preferences_cache[key]
            
    def get_user_scheduling_preferences(self, user_id: str, 
                                       platform_id: Optional[PlatformId] = None) -> List[UserSchedulingPreferences]:
        """Get user scheduling preferences."""
        cache_key = f"{user_id}_{platform_id.value if platform_id else 'all'}"
        if cache_key in self._user_preferences_cache:
            return self._user_preferences_cache[cache_key]
            
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        if platform_id:
            cursor.execute("""
                SELECT * FROM user_scheduling_preferences 
                WHERE user_id = ? AND platform_id = ?
                ORDER BY created_at DESC
            """, (user_id, platform_id.value))
        else:
            cursor.execute("""
                SELECT * FROM user_scheduling_preferences 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
        rows = cursor.fetchall()
        conn.close()
        
        preferences_list = []
        for row in rows:
            preferences = UserSchedulingPreferences(
                user_id=row[1],
                platform_id=PlatformId(row[2]) if row[2] else None,
                timezone=row[3],
                posting_frequency_min=row[4],
                posting_frequency_max=row[5],
                days_blacklist=json.loads(row[6]) if row[6] else [],
                hours_blacklist=json.loads(row[7]) if row[7] else [],
                content_format=row[8],
                quality_threshold=row[9] if row[9] else 0.0,
                metadata=json.loads(row[10]) if row[10] else {}
            )
            preferences_list.append(preferences)
            
        # Cache the results
        self._user_preferences_cache[cache_key] = preferences_list
        return preferences_list


class ScheduleGenerator:
    """
    Automated schedule generation engine.
    
    Generates optimized posting schedules for video content across multiple platforms
    based on platform timing data, user preferences, and content performance analytics.
    """
    
    def __init__(self, calendar_manager: ContentCalendarManager):
        """Initialize schedule generator."""
        self.calendar_manager = calendar_manager
        
    def generate_schedule_for_bulk_job(self, bulk_job: BulkJob, 
                                      video_jobs: List[VideoJob],
                                      created_by: str,
                                      target_platforms: List[PlatformId],
                                      timezone: str = "UTC") -> List[ContentScheduleItem]:
        """
        Generate a complete schedule for a bulk job across multiple platforms.
        
        This method integrates with the existing bulk job workflow to create
        optimized schedules for all generated video content.
        """
        schedule_items = []
        
        # Get platform timing data for each platform
        platform_timing = {}
        for platform in target_platforms:
            platform_timing[platform] = self.calendar_manager.get_platform_timing_data(platform)
            
        # Get user scheduling preferences
        user_prefs = self.calendar_manager.get_user_scheduling_preferences(created_by)
        
        # Create calendar for this bulk job if needed
        calendar = self._get_or_create_calendar_for_bulk_job(bulk_job, created_by, timezone)
        
        for video_job in video_jobs:
            # Parse content format from video job idea data
            content_format = self._extract_content_format(video_job)
            
            for platform in target_platforms:
                # Generate optimal posting times
                scheduled_times = self._generate_optimal_times(
                    platform, content_format, video_job.created_at, user_prefs, timezone
                )
                
                for scheduled_time in scheduled_times:
                    # Create schedule item
                    schedule_item = ContentScheduleItem(
                        id=str(uuid.uuid4()),
                        calendar_id=calendar.id,
                        video_job_id=video_job.id,
                        bulk_job_id=bulk_job.id,
                        platform_id=platform,
                        content_format=content_format,
                        scheduled_at=scheduled_time,
                        timezone=timezone,
                        status=ScheduleStatus.PLANNED,
                        created_by=created_by,
                        idempotency_key=self._generate_idempotency_key(
                            video_job.id, platform.value, scheduled_time
                        )
                    )
                    
                    schedule_items.append(schedule_item)
                    
        # Save schedule items to database
        self._save_schedule_items(schedule_items)
        
        logger.info(f"Generated {len(schedule_items)} schedule items for bulk job {bulk_job.id}")
        return schedule_items
        
    def _get_or_create_calendar_for_bulk_job(self, bulk_job: BulkJob, 
                                           created_by: str, timezone: str) -> ContentCalendar:
        """Get or create calendar for bulk job."""
        # Try to find existing calendar for this bulk job
        calendars = self.calendar_manager.list_calendars(created_by)
        for calendar in calendars:
            if calendar.bulk_job_id == bulk_job.id:
                return calendar
                
        # Create new calendar for this bulk job
        return self.calendar_manager.create_calendar(
            name=f"Bulk Job {bulk_job.id[:8]} Schedule",
            description=f"Auto-generated schedule for bulk job {bulk_job.id}",
            created_by=created_by,
            timezone=timezone,
            bulk_job_id=bulk_job.id
        )
        
    def _extract_content_format(self, video_job: VideoJob) -> str:
        """Extract content format from video job idea data."""
        # Default to youtube_video if not specified
        content_format = video_job.idea_data.get('content_format', 'youtube_video')
        
        # Map common formats
        format_mapping = {
            'video': 'youtube_video',
            'short': 'youtube_shorts', 
            'tiktok': 'tiktok_video',
            'reel': 'instagram_reels',
            'post': 'instagram_feed'
        }
        
        return format_mapping.get(content_format.lower(), content_format)
        
    def _generate_optimal_times(self, platform: PlatformId, content_format: str,
                              created_at: datetime, user_prefs: List[UserSchedulingPreferences],
                              timezone: str) -> List[datetime]:
        """Generate optimal posting times for platform and content format."""
        # Get platform timing data
        timing_data = self.calendar_manager.get_platform_timing_data(platform, content_format)
        
        if not timing_data:
            # Fallback to platform-specific defaults
            return self._generate_fallback_times(platform, created_at)
            
        # Get user preferences for this platform
        platform_prefs = [pref for pref in user_prefs if pref.platform_id == platform]
        
        # Generate times based on platform timing and user preferences
        optimal_times = []
        
        for timing in timing_data:
            # Generate times within the next 30 days
            start_date = created_at.date()
            end_date = (created_at + timedelta(days=30)).date()
            
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%a').lower()
                
                # Skip if day is blacklisted
                if platform_prefs:
                    blacklisted_days = set()
                    for pref in platform_prefs:
                        blacklisted_days.update(pref.days_blacklist)
                    if day_name in blacklisted_days:
                        current_date += timedelta(days=1)
                        continue
                
                # Check if this day is in optimal days
                if day_name in timing.days:
                    for hour_range in timing.peak_hours:
                        # Generate time in the middle of peak hour
                        hour = (hour_range['start'] + hour_range['end']) // 2
                        optimal_time = datetime.combine(current_date, time(hour, 0))
                        
                        # Apply timezone conversion
                        optimal_time = self._convert_to_timezone(optimal_time, timezone)
                        
                        optimal_times.append(optimal_time)
                        
                current_date += timedelta(days=1)
                
        # Sort and return top 3 optimal times
        optimal_times.sort()
        return optimal_times[:3]
        
    def _generate_fallback_times(self, platform: PlatformId, created_at: datetime) -> List[datetime]:
        """Generate fallback times when no timing data available."""
        # Simple fallback: 3 times spread across next week
        fallback_times = []
        base_time = created_at + timedelta(hours=24)  # Start tomorrow
        
        for i in range(3):
            fallback_times.append(base_time + timedelta(days=i*2))
            
        return fallback_times
        
    def _convert_to_timezone(self, dt: datetime, timezone_str: str) -> datetime:
        """Convert datetime to specified timezone."""
        # Simplified timezone conversion - in production would use pytz
        return dt
        
    def _generate_idempotency_key(self, video_job_id: str, platform: str, scheduled_at: datetime) -> str:
        """Generate idempotency key for schedule item."""
        key_string = f"{video_job_id}_{platform}_{scheduled_at.isoformat()}"
        return hashlib.sha256(key_string.encode()).hexdigest()
        
    def _save_schedule_items(self, schedule_items: List[ContentScheduleItem]) -> None:
        """Save schedule items to database."""
        conn = sqlite3.connect(self.calendar_manager.storage_path)
        cursor = conn.cursor()
        
        for item in schedule_items:
            cursor.execute("""
                INSERT OR IGNORE INTO content_schedule_items 
                (id, calendar_id, video_job_id, bulk_job_id, platform_id, content_format,
                 planned_start, planned_end, scheduled_at, timezone, status, 
                 idempotency_key, dedupe_key, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.calendar_id, item.video_job_id, item.bulk_job_id,
                item.platform_id.value, item.content_format, item.planned_start,
                item.planned_end, item.scheduled_at, item.timezone, item.status.value,
                item.idempotency_key, item.dedupe_key, item.created_by
            ))
            
        conn.commit()
        conn.close()


class CrossPlatformCoordinator:
    """
    Cross-platform content coordination system.
    
    Manages content distribution across multiple platforms with:
    - Platform-specific formatting and optimization
    - Cross-platform performance tracking
    - Content reuse and adaptation management
    - Platform-specific scheduling coordination
    """
    
    def __init__(self, calendar_manager: ContentCalendarManager):
        """Initialize cross-platform coordinator."""
        self.calendar_manager = calendar_manager
        
    def coordinate_content_distribution(self, video_job_id: str, 
                                      target_platforms: List[PlatformId],
                                      created_by: str) -> Dict[PlatformId, str]:
        """
        Coordinate content distribution across multiple platforms.
        
        Returns mapping of platform to schedule item ID.
        """
        # Get existing schedule items for this video job
        schedule_items = self._get_schedule_items_for_video_job(video_job_id, created_by)
        
        platform_schedule_mapping = {}
        
        for platform in target_platforms:
            # Find existing schedule item for this platform
            platform_item = next(
                (item for item in schedule_items if item.platform_id == platform),
                None
            )
            
            if not platform_item:
                # Create new schedule item if none exists
                platform_item = self._create_schedule_item_for_platform(
                    video_job_id, platform, created_by
                )
                
            platform_schedule_mapping[platform] = platform_item.id
            
        return platform_schedule_mapping
        
    def optimize_for_platform(self, platform: PlatformId, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content data for specific platform requirements."""
        optimized_data = content_data.copy()
        
        # Platform-specific optimizations
        if platform == PlatformId.YOUTUBE:
            # YouTube: focus on SEO keywords and engagement hooks
            optimized_data['title'] = self._optimize_youtube_title(optimized_data.get('title', ''))
            optimized_data['description'] = self._optimize_youtube_description(optimized_data.get('description', ''))
            optimized_data['tags'] = self._extract_youtube_tags(optimized_data.get('description', ''))
            
        elif platform == PlatformId.TIKTOK:
            # TikTok: focus on trending hashtags and hooks
            optimized_data['hashtags'] = self._extract_tiktok_hashtags(optimized_data.get('description', ''))
            optimized_data['sound'] = self._select_tiktok_sound(optimized_data.get('mood', 'trending'))
            
        elif platform == PlatformId.INSTAGRAM:
            # Instagram: focus on visual appeal and hashtags
            optimized_data['hashtags'] = self._extract_instagram_hashtags(optimized_data.get('description', ''))
            optimized_data['story_elements'] = self._generate_instagram_story_elements(optimized_data)
            
        elif platform == PlatformId.X:
            # X: focus on concise, engaging text
            optimized_data['text'] = self._optimize_x_text(optimized_data.get('description', ''))
            
        elif platform == PlatformId.LINKEDIN:
            # LinkedIn: focus on professional tone and networking
            optimized_data['tone'] = 'professional'
            optimized_data['linkedin_specific'] = self._add_linkedin_elements(optimized_data)
            
        return optimized_data
        
    def _get_schedule_items_for_video_job(self, video_job_id: str, 
                                        created_by: str) -> List[ContentScheduleItem]:
        """Get schedule items for a video job."""
        conn = sqlite3.connect(self.calendar_manager.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM content_schedule_items 
            WHERE video_job_id = ? AND created_by = ?
        """, (video_job_id, created_by))
        
        rows = cursor.fetchall()
        conn.close()
        
        schedule_items = []
        for row in rows:
            schedule_items.append(ContentScheduleItem(
                id=row[0], calendar_id=row[1], video_job_id=row[2], bulk_job_id=row[3],
                platform_id=PlatformId(row[4]), content_format=row[5],
                planned_start=datetime.fromisoformat(row[6]) if row[6] else None,
                planned_end=datetime.fromisoformat(row[7]) if row[7] else None,
                scheduled_at=datetime.fromisoformat(row[8]) if row[8] else None,
                timezone=row[9], status=ScheduleStatus(row[10]),
                idempotency_key=row[11], dedupe_key=row[12], created_by=row[13],
                created_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(row[15]) if row[15] else datetime.now(timezone.utc)
            ))
            
        return schedule_items
        
    def _create_schedule_item_for_platform(self, video_job_id: str, platform: PlatformId,
                                         created_by: str) -> ContentScheduleItem:
        """Create new schedule item for platform."""
        schedule_item = ContentScheduleItem(
            id=str(uuid.uuid4()),
            calendar_id="",  # Will be set when assigned to calendar
            video_job_id=video_job_id,
            bulk_job_id=None,
            platform_id=platform,
            content_format="",
            timezone="UTC",
            status=ScheduleStatus.PLANNED,
            created_by=created_by
        )
        
        # Save to database
        conn = sqlite3.connect(self.calendar_manager.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO content_schedule_items 
            (id, video_job_id, platform_id, content_format, timezone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule_item.id, schedule_item.video_job_id, schedule_item.platform_id.value,
            schedule_item.content_format, schedule_item.timezone, 
            schedule_item.status.value, schedule_item.created_by
        ))
        
        conn.commit()
        conn.close()
        
        return schedule_item
        
    def _optimize_youtube_title(self, title: str) -> str:
        """Optimize title for YouTube."""
        # Add SEO keywords, keep under 60 characters
        if len(title) > 60:
            title = title[:57] + "..."
        return title
        
    def _optimize_youtube_description(self, description: str) -> str:
        """Optimize description for YouTube."""
        # Add timestamps, keywords, and call-to-action
        if len(description) < 100:
            description += "\n\n👍 Like this video if it helped!\n🔔 Subscribe for more content!\n💬 Comment below with your thoughts!"
        return description
        
    def _extract_youtube_tags(self, description: str) -> List[str]:
        """Extract relevant tags for YouTube."""
        # Simple keyword extraction - in production would use NLP
        words = description.lower().split()
        return words[:10]  # Top 10 words as tags
        
    def _extract_tiktok_hashtags(self, description: str) -> List[str]:
        """Extract hashtags for TikTok."""
        # Extract hashtags and trending topics
        hashtags = []
        words = description.lower().split()
        for word in words:
            if len(word) > 3:
                hashtags.append(f"#{word}")
        return hashtags[:5]  # Top 5 hashtags
        
    def _select_tiktok_sound(self, mood: str) -> str:
        """Select appropriate TikTok sound based on mood."""
        sound_mapping = {
            'trending': 'trending_sound_2025',
            'happy': 'upbeat_pop_beat',
            'sad': 'melancholy_ambient',
            'energetic': 'electronic_dance',
            'calm': 'peaceful_acoustic'
        }
        return sound_mapping.get(mood, 'trending_sound_2025')
        
    def _extract_instagram_hashtags(self, description: str) -> List[str]:
        """Extract hashtags for Instagram."""
        hashtags = []
        words = description.lower().split()
        for word in words:
            if len(word) > 3:
                hashtags.append(f"#{word}")
        return hashtags[:30]  # Instagram allows more hashtags
        
    def _generate_instagram_story_elements(self, content_data: Dict[str, Any]) -> List[str]:
        """Generate story elements for Instagram."""
        return [
            "question_sticker",
            "poll_sticker", 
            "link_sticker"
        ]
        
    def _optimize_x_text(self, description: str) -> str:
        """Optimize text for X (Twitter)."""
        # Keep under 280 characters, add engagement elements
        if len(description) > 250:
            description = description[:247] + "..."
        return description
        
    def _add_linkedin_elements(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add LinkedIn-specific elements."""
        return {
            'include_industry_tags': True,
            'professional_tone': True,
            'networking_elements': True
        }


class CalendarAnalyticsEngine:
    """
    Calendar analytics and optimization engine.
    
    Provides insights and optimization recommendations based on:
    - Historical performance data
    - Platform-specific analytics
    - Content format effectiveness
    - Timing optimization opportunities
    """
    
    def __init__(self, calendar_manager: ContentCalendarManager):
        """Initialize analytics engine."""
        self.calendar_manager = calendar_manager
        
    def generate_calendar_analytics(self, calendar_id: str) -> CalendarAnalytics:
        """Generate comprehensive analytics for a content calendar."""
        # Get all schedule items for calendar
        schedule_items = self._get_schedule_items_for_calendar(calendar_id)
        
        # Get performance data for all video jobs
        performance_data = self._get_performance_data_for_calendar(calendar_id)
        
        # Calculate analytics
        analytics = CalendarAnalytics()
        
        # Basic counts
        analytics.total_scheduled = len(schedule_items)
        analytics.total_posted = len([item for item in schedule_items if item.status == ScheduleStatus.POSTED])
        analytics.total_failed = len([item for item in schedule_items if item.status == ScheduleStatus.FAILED])
        
        # Platform distribution
        for item in schedule_items:
            analytics.platform_distribution[item.platform_id] = \
                analytics.platform_distribution.get(item.platform_id, 0) + 1
                
        # Performance metrics
        if performance_data:
            analytics.average_engagement_rate = statistics.mean([
                event.engagement_rate for event in performance_data 
                if event.engagement_rate is not None
            ])
            
            # Best performing times
            analytics.best_performing_times = self._calculate_best_performing_times(performance_data)
            
            # Content format performance
            analytics.content_format_performance = self._calculate_content_format_performance(performance_data)
            
        # Generate optimization recommendations
        analytics.optimization_recommendations = self._generate_optimization_recommendations(
            schedule_items, performance_data
        )
        
        return analytics
        
    def optimize_schedule_timing(self, calendar_id: str) -> List[Dict[str, Any]]:
        """Generate timing optimization recommendations."""
        schedule_items = self._get_schedule_items_for_calendar(calendar_id)
        performance_data = self._get_performance_data_for_calendar(calendar_id)
        
        optimizations = []
        
        # Analyze platform performance
        platform_performance = defaultdict(list)
        for event in performance_data:
            if event.engagement_rate is not None:
                platform_performance[event.platform_id].append(event.engagement_rate)
                
        for platform, engagement_rates in platform_performance.items():
            if len(engagement_rates) >= 5:  # Need sufficient data
                avg_engagement = statistics.mean(engagement_rates)
                
                optimizations.append({
                    'type': 'platform_timing',
                    'platform': platform.value,
                    'recommendation': f'Increase posting frequency for {platform.value} - average engagement: {avg_engagement:.2%}',
                    'confidence': 'high' if len(engagement_rates) >= 20 else 'medium'
                })
                
        # Analyze day-of-week performance
        day_performance = defaultdict(list)
        for event in performance_data:
            if event.engagement_rate is not None and event.event_time:
                day_of_week = event.event_time.strftime('%a').lower()
                day_performance[day_of_week].append(event.engagement_rate)
                
        for day, engagement_rates in day_performance.items():
            if len(engagement_rates) >= 5:
                avg_engagement = statistics.mean(engagement_rates)
                if avg_engagement > 0.05:  # 5% engagement threshold
                    optimizations.append({
                        'type': 'day_optimization',
                        'day': day,
                        'recommendation': f'{day.capitalize()} shows strong performance ({avg_engagement:.2%}) - consider posting more content',
                        'confidence': 'high' if len(engagement_rates) >= 15 else 'medium'
                    })
                    
        return optimizations
        
    def _get_schedule_items_for_calendar(self, calendar_id: str) -> List[ContentScheduleItem]:
        """Get all schedule items for a calendar."""
        conn = sqlite3.connect(self.calendar_manager.storage_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM content_schedule_items WHERE calendar_id = ?
        """, (calendar_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        schedule_items = []
        for row in rows:
            schedule_items.append(ContentScheduleItem(
                id=row[0], calendar_id=row[1], video_job_id=row[2], bulk_job_id=row[3],
                platform_id=PlatformId(row[4]), content_format=row[5],
                planned_start=datetime.fromisoformat(row[6]) if row[6] else None,
                planned_end=datetime.fromisoformat(row[7]) if row[7] else None,
                scheduled_at=datetime.fromisoformat(row[8]) if row[8] else None,
                timezone=row[9], status=ScheduleStatus(row[10]),
                idempotency_key=row[11], dedupe_key=row[12], created_by=row[13],
                created_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(row[15]) if row[15] else datetime.now(timezone.utc)
            ))
            
        return schedule_items
        
    def _get_performance_data_for_calendar(self, calendar_id: str) -> List[PerformanceKPIEvent]:
        """Get performance data for a calendar."""
        # Get video jobs for calendar first
        schedule_items = self._get_schedule_items_for_calendar(calendar_id)
        video_job_ids = [item.video_job_id for item in schedule_items]
        
        if not video_job_ids:
            return []
            
        conn = sqlite3.connect(self.calendar_manager.storage_path)
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in video_job_ids])
        cursor.execute(f"""
            SELECT * FROM performance_kpi_events 
            WHERE video_job_id IN ({placeholders})
        """, video_job_ids)
        
        rows = cursor.fetchall()
        conn.close()
        
        performance_events = []
        for row in rows:
            performance_events.append(PerformanceKPIEvent(
                id=row[0], video_job_id=row[1], platform_id=PlatformId(row[2]),
                content_format=row[3], event_time=datetime.fromisoformat(row[4]),
                ingestion_time=datetime.fromisoformat(row[5]) if row[5] else datetime.now(timezone.utc),
                views=row[6], impressions=row[7], watch_time_seconds=row[8],
                engagement_rate=row[9], clicks=row[10], saves=row[11],
                shares=row[12], comments=row[13], followers_delta=row[14],
                scheduled_slot_id=row[15],
                metadata=json.loads(row[16]) if row[16] else {},
                created_at=datetime.fromisoformat(row[17]) if row[17] else datetime.now(timezone.utc)
            ))
            
        return performance_events
        
    def _calculate_best_performing_times(self, performance_data: List[PerformanceKPIEvent]) -> List[Dict[str, Any]]:
        """Calculate best performing times from performance data."""
        hourly_performance = defaultdict(list)
        
        for event in performance_data:
            if event.engagement_rate is not None and event.event_time:
                hour = event.event_time.hour
                hourly_performance[hour].append(event.engagement_rate)
                
        best_times = []
        for hour, engagement_rates in hourly_performance.items():
            if len(engagement_rates) >= 3:  # Minimum data points
                avg_engagement = statistics.mean(engagement_rates)
                best_times.append({
                    'hour': hour,
                    'average_engagement': avg_engagement,
                    'sample_size': len(engagement_rates)
                })
                
        # Sort by engagement rate
        best_times.sort(key=lambda x: x['average_engagement'], reverse=True)
        return best_times[:5]  # Top 5 performing hours
        
    def _calculate_content_format_performance(self, performance_data: List[PerformanceKPIEvent]) -> Dict[str, float]:
        """Calculate performance by content format."""
        format_performance = defaultdict(list)
        
        for event in performance_data:
            if event.engagement_rate is not None and event.content_format:
                format_performance[event.content_format].append(event.engagement_rate)
                
        avg_performance = {}
        for format_type, engagement_rates in format_performance.items():
            if engagement_rates:
                avg_performance[format_type] = statistics.mean(engagement_rates)
                
        return avg_performance
        
    def _generate_optimization_recommendations(self, schedule_items: List[ContentScheduleItem],
                                             performance_data: List[PerformanceKPIEvent]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Analyze posting frequency vs performance
        if len(performance_data) > 10:
            recommendations.append("Consider A/B testing different posting times based on your top-performing content")
            
        # Platform-specific recommendations
        platform_counts = Counter(item.platform_id for item in schedule_items)
        if len(platform_counts) > 1:
            recommendations.append("Diversify across multiple platforms to maximize reach and engagement")
            
        # Format recommendations
        format_counts = Counter(item.content_format for item in schedule_items)
        if len(format_counts) > 1:
            recommendations.append("Experiment with different content formats to find what resonates with your audience")
            
        # Timing recommendations
        if performance_data:
            recent_events = [e for e in performance_data if e.event_time > datetime.now(timezone.utc) - timedelta(days=30)]
            if len(recent_events) < 5:
                recommendations.append("Increase posting frequency to gather more performance data for optimization")
                
        return recommendations


# Integration functions for bulk job workflow
def integrate_with_bulk_job_workflow(calendar_manager: ContentCalendarManager,
                                   bulk_job: BulkJob,
                                   video_jobs: List[VideoJob],
                                   created_by: str,
                                   target_platforms: List[PlatformId] = None) -> List[ContentScheduleItem]:
    """
    Integration function for bulk job workflow.
    
    This function seamlessly integrates content calendar scheduling with the 
    existing bulk job creation process.
    """
    if target_platforms is None:
        target_platforms = [PlatformId.YOUTUBE, PlatformId.TIKTOK, PlatformId.INSTAGRAM]
        
    # Initialize schedule generator
    schedule_generator = ScheduleGenerator(calendar_manager)
    
    # Generate schedule for bulk job
    schedule_items = schedule_generator.generate_schedule_for_bulk_job(
        bulk_job, video_jobs, created_by, target_platforms
    )
    
    logger.info(f"Integrated {len(schedule_items)} schedule items with bulk job {bulk_job.id}")
    return schedule_items


def create_optimization_trial(user_id: str, hypothesis: str, 
                            calendar_manager: ContentCalendarManager) -> OptimizationTrial:
    """Create an optimization trial for A/B testing scheduling strategies."""
    trial = OptimizationTrial(
        id=str(uuid.uuid4()),
        user_id=user_id,
        trial_id=str(uuid.uuid4()),
        hypothesis=hypothesis,
        primary_kpi="engagement_rate",
        variants={
            "control": {"posting_times": "standard"},
            "variant_a": {"posting_times": "optimized"},
            "variant_b": {"posting_times": "experimental"}
        },
        guardrails={"min_engagement_rate": 0.02}
    )
    
    # Save to database
    conn = sqlite3.connect(calendar_manager.storage_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO optimization_trials 
        (id, user_id, trial_id, hypothesis, start_at, variants, primary_kpi, guardrails)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trial.id, trial.user_id, trial.trial_id, trial.hypothesis,
        trial.start_at, json.dumps(trial.variants), trial.primary_kpi,
        json.dumps(trial.guardrails)
    ))
    
    conn.commit()
    conn.close()
    
    return trial


# Example usage and testing
if __name__ == "__main__":
    # Example integration with existing bulk job workflow
    from batch_processor import JobStatus, JobPriority
    
    # Initialize content calendar manager
    calendar_manager = ContentCalendarManager()
    
    # Create user scheduling preferences
    user_prefs = UserSchedulingPreferences(
        user_id="user_123",
        platform_id=PlatformId.YOUTUBE,
        timezone="America/New_York",
        posting_frequency_min=2,
        posting_frequency_max=5,
        days_blacklist=["sat", "sun"],
        quality_threshold=0.03
    )
    calendar_manager.set_user_scheduling_preferences(user_prefs)
    
    # Example bulk job integration
    bulk_job = BulkJob(
        id="bulk_123",
        sheet_id="sheet_456",
        total_jobs=10,
        completed_jobs=0,
        failed_jobs=0,
        total_cost=Decimal('0.00'),
        status=JobStatus.QUEUED
    )
    
    video_jobs = [
        VideoJob(
            id=f"video_{i}",
            bulk_job_id=bulk_job.id,
            idea_data={"title": f"Video {i}", "description": f"Description for video {i}"},
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="minimax"
        ) for i in range(3)
    ]
    
    # Generate schedule
    schedule_items = integrate_with_bulk_job_workflow(
        calendar_manager, bulk_job, video_jobs, "user_123"
    )
    
    # Create optimization trial
    trial = create_optimization_trial(
        "user_123", 
        "Testing optimized posting times vs standard times",
        calendar_manager
    )
    
    # Generate analytics
    if schedule_items:
        analytics_engine = CalendarAnalyticsEngine(calendar_manager)
        analytics = analytics_engine.generate_calendar_analytics(schedule_items[0].calendar_id)
        
        print(f"Calendar Analytics:")
        print(f"- Total Scheduled: {analytics.total_scheduled}")
        print(f"- Total Posted: {analytics.total_posted}")
        print(f"- Average Engagement: {analytics.average_engagement_rate:.2%}")
        print(f"- Optimization Recommendations: {len(analytics.optimization_recommendations)}")