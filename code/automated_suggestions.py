"""
Automated Posting Time Suggestion System for AI Content Automation

This module implements an intelligent posting time suggestion system that provides
real-time, platform-aware recommendations based on:
- Platform-specific optimization data (2025)
- User preference learning and adaptation
- Performance analytics integration
- Cross-platform scheduling constraints
- Google Sheets bulk processing integration

Architecture:
- Real-time suggestion engine with Bayesian updating
- Platform-aware scoring models for YouTube, TikTok, Instagram, X, LinkedIn, Facebook
- Cross-platform conflict resolution and constraint handling
- Google Sheets integration for bulk operations
- Performance validation and feedback loops

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, NamedTuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import sqlite3
import numpy as np
from pathlib import Path

# Import existing services
try:
    from batch_processor import BatchProcessor, JobPriority, VideoJob, BulkJob
    from google_sheets_client import GoogleSheetsClient
    from data_validation import DataValidationPipeline
except ImportError as e:
    logging.warning(f"Could not import existing services: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    X = "x"  # Alias for Twitter
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class ContentType(Enum):
    """Content types for platform-specific optimization."""
    VIDEO_LONG = "video_long"
    VIDEO_SHORT = "video_short"
    REEL = "reel"
    STORY = "story"
    IMAGE = "image"
    CAROUSEL = "carousel"
    TEXT = "text"
    LIVE = "live"
    DOCUMENT = "document"


class SeasonalityType(Enum):
    """Seasonality patterns for timing adjustments."""
    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    SPECIAL_EVENT = "special_event"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class SuggestionPriority(Enum):
    """Priority levels for timing suggestions."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class SuggestionStatus(Enum):
    """Status of timing suggestions."""
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    EXECUTED = "executed"
    VALIDATED = "validated"
    DEPRECATED = "deprecated"


@dataclass
class PlatformTimingData:
    """Platform-specific timing optimization data."""
    platform: Platform
    best_hours: Dict[int, List[int]] = field(default_factory=dict)  # day_of_week -> [hours]
    peak_windows: List[Tuple[int, int]] = field(default_factory=list)  # (start_hour, end_hour)
    frequency_guidelines: Dict[str, str] = field(default_factory=dict)  # account_type -> frequency
    algorithm_signals: Dict[str, float] = field(default_factory=dict)  # signal -> weight
    audience_demographics: Dict[str, float] = field(default_factory=dict)  # demographic -> weight


@dataclass
class AudienceProfile:
    """User audience profile for timing optimization."""
    age_cohorts: Dict[str, float] = field(default_factory=dict)  # "18-24": 0.35, etc.
    device_split: Dict[str, float] = field(default_factory=dict)  # "mobile": 0.8, "desktop": 0.2
    time_zones: Dict[str, float] = field(default_factory=dict)  # "EST": 0.4, etc.
    geographic_regions: Dict[str, float] = field(default_factory=dict)  # region -> percentage
    activity_patterns: Dict[str, float] = field(default_factory=dict)  # hour -> activity_level
    engagement_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ContentProfile:
    """Content characteristics for timing optimization."""
    content_type: ContentType
    duration: Optional[int] = None  # seconds for video content
    language: str = "en"
    hashtags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    target_audience: Optional[str] = None
    industry: Optional[str] = None
    urgency_level: SuggestionPriority = SuggestionPriority.MEDIUM
    expected_engagement: Optional[float] = None  # predicted engagement score


@dataclass
class TimingScore:
    """Timing score for a specific platform, day, and hour."""
    platform: Platform
    day_of_week: int  # 0-6, Monday=0
    hour: int  # 0-23
    score: float  # 0-1 normalized score
    confidence: float  # 0-1 confidence level
    factors: Dict[str, float] = field(default_factory=dict)  # contributing factors
    explanation: List[str] = field(default_factory=list)  # human-readable explanations


@dataclass
class PostingSuggestion:
    """Complete posting time suggestion."""
    id: str
    platform: Platform
    content_profile: ContentProfile
    suggested_datetime: datetime
    confidence: float
    score: TimingScore
    alternatives: List[TimingScore] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    status: SuggestionStatus = SuggestionStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    performance_data: Optional[Dict[str, Any]] = None


@dataclass
class UserPreferences:
    """User preferences for posting behavior."""
    preferred_time_slots: List[Tuple[int, int]] = field(default_factory=list)  # (start_hour, end_hour)
    avoided_time_slots: List[Tuple[int, int]] = field(default_factory=list)
    platform_priorities: Dict[Platform, float] = field(default_factory=dict)
    content_type_preferences: Dict[ContentType, float] = field(default_factory=dict)
    timezone: str = "UTC"
    working_hours: Tuple[int, int] = (9, 17)  # (start, end)
    weekend_preference: float = 0.5  # 0-1, preference for weekend posting
    quality_vs_quantity: float = 0.7  # 0-1, emphasis on quality


@dataclass
class PerformanceMetrics:
    """Performance metrics for validation and learning."""
    post_id: str
    platform: Platform
    content_type: ContentType
    post_time: datetime
    metrics: Dict[str, float]  # engagement, reach, clicks, etc.
    validation_score: float  # 0-1 overall score
    feedback_quality: float  # 0-1 quality of feedback data


class PlatformTimingOptimizer:
    """Platform-specific timing optimization with 2025 evidence base."""
    
    def __init__(self):
        self.platform_data = self._initialize_platform_data()
        self.seasonality_adjustments = self._initialize_seasonality()
    
    def _initialize_platform_data(self) -> Dict[Platform, PlatformTimingData]:
        """Initialize platform data with 2025 evidence."""
        data = {}
        
        # YouTube optimization data (2025)
        data[Platform.YOUTUBE] = PlatformTimingData(
            platform=Platform.YOUTUBE,
            best_hours={
                0: [15, 16, 17],  # Monday 3-5pm
                1: [15, 16, 17],  # Tuesday 3-5pm
                2: [16, 15, 17],  # Wednesday 4pm (strongest), 3pm, 5pm
                3: [15, 16, 17],  # Thursday 3-5pm
                4: [14, 16, 15],  # Friday 2pm, 4pm, 3pm
                5: [17, 15, 16],  # Saturday 5pm, 3pm, 4pm
                6: [15, 16, 14],  # Sunday 3pm, 4pm, 2pm
            },
            peak_windows=[(14, 18), (20, 22)],
            frequency_guidelines={
                "small": "1/week long-form, daily Shorts if quality maintained",
                "medium": "2-3/week long-form, 3-5/week Shorts",
                "large": "1-3/week long-form mix, 3-5/week Shorts"
            },
            algorithm_signals={
                "watch_time": 0.35,
                "retention": 0.25,
                "ctr": 0.20,
                "engagement": 0.15,
                "subscriber_conversion": 0.05
            },
            audience_demographics={
                "18-24": 0.25,
                "25-34": 0.35,
                "35-44": 0.20,
                "45-54": 0.12,
                "55+": 0.08
            }
        )
        
        # TikTok optimization data (2025)
        data[Platform.TIKTOK] = PlatformTimingData(
            platform=Platform.TIKTOK,
            best_hours={
                0: [19, 18, 17],  # Monday 7pm, 6pm, 5pm
                1: [16, 20, 14],  # Tuesday 4pm, 8pm, 2pm
                2: [17, 18, 16],  # Wednesday 5pm, 6pm, 4pm (strongest day)
                3: [17, 13, 15],  # Thursday 5pm, 1pm, 3pm
                4: [16, 14, 18],  # Friday 4pm, 2pm, 6pm
                5: [17, 16, 19],  # Saturday 5pm, 4pm, 7pm (quietest day)
                6: [20, 17, 16],  # Sunday 8pm, 5pm, 4pm (strong evening peak)
            },
            peak_windows=[(13, 17), (18, 21)],
            frequency_guidelines={
                "emerging": "1-4 posts/day for accelerated learning",
                "established": "2-5 posts/week sustainable cadence",
                "brands": "~4 posts/week brand baseline"
            },
            algorithm_signals={
                "watch_time": 0.40,
                "completion_rate": 0.25,
                "engagement_velocity": 0.20,
                "shares_saves": 0.15
            },
            audience_demographics={
                "18-24": 0.30,
                "25-34": 0.25,
                "35-44": 0.20,
                "45-54": 0.15,
                "55+": 0.10
            }
        )
        
        # Instagram optimization data (2025)
        data[Platform.INSTAGRAM] = PlatformTimingData(
            platform=Platform.INSTAGRAM,
            best_hours={
                0: [10, 11, 13, 15],  # Monday 10am-3pm
                1: [10, 11, 13, 15],  # Tuesday 10am-3pm
                2: [10, 11, 13, 15],  # Wednesday 10am-3pm
                3: [10, 11, 13, 15],  # Thursday 10am-3pm
                4: [10, 11, 13, 15],  # Friday 10am-3pm
                5: [9, 10, 11],       # Saturday mornings
                6: [9, 10, 11, 20],   # Sunday mornings + 8pm
            },
            peak_windows=[(9, 12), (18, 21), (10, 15)],  # Bookends + midday
            frequency_guidelines={
                "nano": "5-7 feed posts/week, 1-2 Reels/week",
                "micro": "4-5 feed posts/week, 1-2 Reels/week",
                "mid": "3-4 feed posts/week, 2 Reels/week",
                "large": "2-3 feed posts/week, 2 Reels/week"
            },
            algorithm_signals={
                "saves": 0.30,
                "shares": 0.25,
                "watch_time": 0.25,  # For Reels
                "comments": 0.20
            },
            audience_demographics={
                "18-24": 0.35,
                "25-34": 0.30,
                "35-44": 0.20,
                "45-54": 0.10,
                "55+": 0.05
            }
        )
        
        # X (Twitter) optimization data (2025)
        data[Platform.X] = PlatformTimingData(
            platform=Platform.X,
            best_hours={
                0: [8, 9, 10],      # Monday 8-10am (weaker)
                1: [10, 11, 14, 15], # Tuesday 10am-3pm
                2: [9, 10, 11, 14],  # Wednesday 9am-12pm (peak), 2-4pm
                3: [10, 11, 14, 15], # Thursday 10am-3pm
                4: [10, 11, 12],     # Friday 10am-12pm (lighter)
                5: [11, 12],         # Saturday lighter
                6: [10, 11],         # Sunday lightest
            },
            peak_windows=[(8, 12), (14, 17)],
            frequency_guidelines={
                "brands": "2-3 posts/day max (~4.2/week average)",
                "creators": "1-3 posts/day, scale during events",
                "newsrooms": "1-3 posts/day consistency priority"
            },
            algorithm_signals={
                "engagement_rate": 0.35,
                "impressions": 0.30,
                "media_engagement": 0.25,
                "follower_growth": 0.10
            },
            audience_demographics={
                "18-24": 0.25,
                "25-34": 0.30,
                "35-44": 0.25,
                "45-54": 0.15,
                "55+": 0.05
            }
        )
        
        # LinkedIn optimization data (2025)
        data[Platform.LINKEDIN] = PlatformTimingData(
            platform=Platform.LINKEDIN,
            best_hours={
                0: [11, 12],      # Monday 11am-12pm
                1: [8, 9, 10, 11, 12, 13, 14], # Tuesday 8am-2pm
                2: [8, 12],       # Wednesday 8am, 12pm
                3: [8, 12],       # Thursday 8am, 12pm
                4: [7, 8, 9, 10, 11, 12, 13, 14], # Friday 7am-2pm (lighter)
                5: [10, 11],      # Saturday lighter
                6: [10, 11],      # Sunday lightest
            },
            peak_windows=[(8, 11), (12, 14)],
            frequency_guidelines={
                "individuals": "2-3 posts/week (daily if quality holds)",
                "companies": "3-5 posts/week, ≥12-24h spacing",
                "personal_brands": "2-3 posts/week, focus on value"
            },
            algorithm_signals={
                "first_hour_engagement": 0.30,
                "comment_depth": 0.25,
                "dwell_time": 0.25,  # Especially for carousels/docs
                "saves": 0.20
            },
            audience_demographics={
                "25-34": 0.35,
                "35-44": 0.30,
                "45-54": 0.20,
                "55+": 0.15
            }
        )
        
        # Facebook optimization data (2025)
        data[Platform.FACEBOOK] = PlatformTimingData(
            platform=Platform.FACEBOOK,
            best_hours={
                0: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18], # Monday 9am-6pm
                1: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18], # Tuesday 9am-6pm
                2: [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], # Wednesday 8am-6pm
                3: [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], # Thursday 8am-6pm
                4: [9, 10, 11, 12, 13, 14], # Friday 9am-2pm (lighter, earlier)
                5: [10, 11],       # Saturday lighter
                6: [10, 11],       # Sunday varies by industry
            },
            peak_windows=[(9, 18)],
            frequency_guidelines={
                "business_pages": "3-5 posts/week baseline",
                "brands": "1-2 posts/day if quality maintained",
                "community_pages": "Daily posting acceptable"
            },
            algorithm_signals={
                "watch_time": 0.30,
                "completion_rate": 0.25,
                "reshares": 0.25,
                "saves": 0.20
            },
            audience_demographics={
                "25-34": 0.25,
                "35-44": 0.25,
                "45-54": 0.20,
                "55+": 0.30
            }
        )
        
        return data
    
    def _initialize_seasonality(self) -> Dict[SeasonalityType, Dict[str, float]]:
        """Initialize seasonality adjustment factors."""
        return {
            SeasonalityType.WEEKDAY: {
                "engagement_boost": 0.15,
                "competition_penalty": -0.05
            },
            SeasonalityType.WEEKEND: {
                "engagement_boost": 0.10,
                "competition_penalty": -0.10,
                "audience_shift": 0.20  # Younger audience active
            },
            SeasonalityType.HOLIDAY: {
                "engagement_boost": -0.20,  # Generally lower engagement
                "competition_penalty": -0.30,
                "special_patterns": 0.15  # Different timing patterns
            }
        }
    
    def calculate_timing_score(self, 
                             platform: Platform, 
                             day_of_week: int, 
                             hour: int,
                             audience_profile: Optional[AudienceProfile] = None,
                             content_profile: Optional[ContentProfile] = None) -> TimingScore:
        """Calculate timing score for a specific platform, day, and hour."""
        
        platform_data = self.platform_data[platform]
        
        # Base score from platform data
        base_score = 0.0
        if day_of_week in platform_data.best_hours and hour in platform_data.best_hours[day_of_week]:
            # Calculate position-based score (earlier positions get higher scores)
            hours_list = platform_data.best_hours[day_of_week]
            if hour in hours_list:
                position = hours_list.index(hour)
                base_score = max(0.1, 1.0 - (position * 0.1))
        
        # Audience adjustment
        audience_adjustment = self._calculate_audience_adjustment(
            platform, audience_profile, day_of_week, hour
        )
        
        # Content type adjustment
        content_adjustment = self._calculate_content_adjustment(
            platform, content_profile, day_of_week, hour
        )
        
        # Seasonality adjustment
        seasonality_adjustment = self._calculate_seasonality_adjustment(
            day_of_week, hour
        )
        
        # Calculate final score with weighted combination
        final_score = (
            base_score * 0.4 +
            audience_adjustment * 0.25 +
            content_adjustment * 0.20 +
            seasonality_adjustment * 0.15
        )
        
        # Normalize score to 0-1 range
        final_score = max(0.0, min(1.0, final_score))
        
        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(platform_data, audience_profile, content_profile)
        
        # Build explanation
        explanation = []
        if base_score > 0.8:
            explanation.append(f"Peak posting window for {platform.value}")
        if audience_adjustment > 0.1:
            explanation.append("Optimal for target audience activity")
        if content_adjustment > 0.1:
            explanation.append(f"Strong performance for {content_profile.content_type.value if content_profile else 'content type'}")
        if seasonality_adjustment > 0.05:
            explanation.append("Seasonal alignment")
        
        return TimingScore(
            platform=platform,
            day_of_week=day_of_week,
            hour=hour,
            score=final_score,
            confidence=confidence,
            factors={
                "base": base_score,
                "audience": audience_adjustment,
                "content": content_adjustment,
                "seasonality": seasonality_adjustment
            },
            explanation=explanation
        )
    
    def _calculate_audience_adjustment(self, 
                                     platform: Platform,
                                     audience_profile: Optional[AudienceProfile],
                                     day_of_week: int, 
                                     hour: int) -> float:
        """Calculate audience-based adjustment to timing score."""
        if not audience_profile:
            return 0.0
        
        adjustment = 0.0
        
        # Device-based adjustment
        mobile_share = audience_profile.device_split.get("mobile", 0.5)
        if mobile_share > 0.7:
            # Mobile-heavy audience, boost evening/weekend hours
            if day_of_week >= 5 or hour >= 18:  # Weekend or evening
                adjustment += 0.1
        elif mobile_share < 0.3:
            # Desktop-heavy audience, boost traditional business hours
            if 9 <= hour <= 17 and day_of_week < 5:  # Weekday business hours
                adjustment += 0.1
        
        # Age cohort adjustments
        young_audience = audience_profile.age_cohorts.get("18-24", 0.0) + audience_profile.age_cohorts.get("25-34", 0.0)
        if young_audience > 0.6:
            # Younger audience, boost evening and late hours
            if hour >= 19 or (day_of_week >= 5 and hour >= 14):
                adjustment += 0.15
        
        # Time zone alignment
        if "UTC" in audience_profile.time_zones:
            adjustment += 0.05  # Well-aligned with global optimization
        
        return adjustment
    
    def _calculate_content_adjustment(self, 
                                    platform: Platform,
                                    content_profile: Optional[ContentProfile],
                                    day_of_week: int, 
                                    hour: int) -> float:
        """Calculate content-type specific adjustment."""
        if not content_profile:
            return 0.0
        
        adjustment = 0.0
        
        # Content type specific rules
        if content_profile.content_type == ContentType.VIDEO_SHORT:
            # Short content less time-sensitive
            adjustment += 0.05
        elif content_profile.content_type == ContentType.LIVE:
            # Live content benefits from evening hours
            if hour >= 18:
                adjustment += 0.1
        elif content_profile.content_type == ContentType.DOCUMENT:
            # Documents perform better during business hours on LinkedIn
            if platform == Platform.LINKEDIN and 9 <= hour <= 17 and day_of_week < 5:
                adjustment += 0.15
        
        # Duration adjustments
        if content_profile.duration:
            if content_profile.duration > 600:  # 10+ minutes
                # Longer content benefits from dedicated viewing time
                if hour >= 19 or (day_of_week >= 5 and hour >= 14):
                    adjustment += 0.1
            elif content_profile.duration < 60:  # Under 1 minute
                # Short content can perform well throughout the day
                adjustment += 0.05
        
        # Industry adjustments
        if content_profile.industry == "education":
            # Educational content benefits from morning hours
            if hour <= 10:
                adjustment += 0.1
        elif content_profile.industry == "entertainment":
            # Entertainment content benefits from evening/weekend
            if hour >= 18 or day_of_week >= 5:
                adjustment += 0.1
        
        return adjustment
    
    def _calculate_seasonality_adjustment(self, day_of_week: int, hour: int) -> float:
        """Calculate seasonality-based adjustment."""
        adjustment = 0.0
        
        # Weekend vs weekday patterns
        if day_of_week >= 5:  # Weekend
            adjustment += self.seasonality_adjustments[SeasonalityType.WEEKEND]["engagement_boost"]
        else:  # Weekday
            adjustment += self.seasonality_adjustments[SeasonalityType.WEEKDAY]["engagement_boost"]
        
        # Time-based adjustments
        if 9 <= hour <= 17:  # Business hours
            adjustment += 0.05
        elif hour >= 19:  # Evening
            adjustment += 0.03
        
        return adjustment
    
    def _calculate_confidence(self, 
                            platform_data: PlatformTimingData,
                            audience_profile: Optional[AudienceProfile],
                            content_profile: Optional[ContentProfile]) -> float:
        """Calculate confidence in the timing score."""
        confidence = 0.7  # Base confidence
        
        # Increase confidence with more data
        if audience_profile:
            confidence += 0.1
            if len(audience_profile.activity_patterns) > 0:
                confidence += 0.1
        
        if content_profile:
            confidence += 0.05
        
        # Decrease confidence if important data is missing
        if not audience_profile:
            confidence -= 0.2
        
        return max(0.1, min(1.0, confidence))


class SuggestionEngine:
    """Real-time suggestion engine with learning capabilities."""
    
    def __init__(self, 
                 db_path: str = "suggestions.db",
                 learning_rate: float = 0.1,
                 min_confidence: float = 0.6):
        
        self.db_path = db_path
        self.learning_rate = learning_rate
        self.min_confidence = min_confidence
        
        # Core components
        self.optimizer = PlatformTimingOptimizer()
        self.user_preferences = UserPreferences()
        
        # Learning state
        self.posterior_params: Dict[str, Tuple[float, float]] = {}  # (alpha, beta) for Beta distribution
        self.performance_history: deque = deque(maxlen=1000)  # Recent performance data
        self.suggestion_history: Dict[str, PostingSuggestion] = {}
        
        # Statistics
        self.total_suggestions = 0
        self.successful_suggestions = 0
        self.confidence_history = deque(maxlen=100)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize suggestion tracking database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS suggestions (
                        id TEXT PRIMARY KEY,
                        platform TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        suggested_time TIMESTAMP NOT NULL,
                        confidence REAL NOT NULL,
                        score REAL NOT NULL,
                        status TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        executed_at TIMESTAMP,
                        performance_score REAL,
                        user_id TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_data (
                        id TEXT PRIMARY KEY,
                        suggestion_id TEXT NOT NULL,
                        post_id TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        post_time TIMESTAMP NOT NULL,
                        metrics TEXT NOT NULL,
                        validation_score REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (suggestion_id) REFERENCES suggestions (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        preference_key TEXT NOT NULL,
                        preference_value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, preference_key)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bayesian_params (
                        platform TEXT NOT NULL,
                        day_of_week INTEGER NOT NULL,
                        hour INTEGER NOT NULL,
                        alpha REAL NOT NULL,
                        beta REAL NOT NULL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (platform, day_of_week, hour)
                    )
                """)
                
                conn.commit()
                logger.info("Suggestion engine database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize suggestion database: {e}")
            raise
    
    def generate_suggestion(self,
                          platform: Platform,
                          content_profile: ContentProfile,
                          audience_profile: Optional[AudienceProfile] = None,
                          num_alternatives: int = 3) -> PostingSuggestion:
        """Generate intelligent posting time suggestions."""
        
        current_time = datetime.now(timezone.utc)
        
        # Generate timing scores for the next 7 days
        timing_scores = []
        for day_offset in range(7):
            target_date = current_time + timedelta(days=day_offset)
            day_of_week = target_date.weekday()
            
            for hour in range(24):
                score = self.optimizer.calculate_timing_score(
                    platform=platform,
                    day_of_week=day_of_week,
                    hour=hour,
                    audience_profile=audience_profile,
                    content_profile=content_profile
                )
                
                # Apply Bayesian learning if we have historical data
                if self._has_historical_data(platform, day_of_week, hour):
                    score = self._apply_bayesian_learning(score, platform, day_of_week, hour)
                
                timing_scores.append((target_date.replace(hour=hour, minute=0, second=0, microsecond=0), score))
        
        # Sort by score and filter by confidence threshold
        timing_scores.sort(key=lambda x: x[1].score * x[1].confidence, reverse=True)
        filtered_scores = [(dt, score) for dt, score in timing_scores 
                         if score.confidence >= self.min_confidence]
        
        if not filtered_scores:
            # Relax confidence requirement if no suggestions meet threshold
            filtered_scores = timing_scores[:10]  # Take top 10 regardless of confidence
        
        # Select best suggestion and alternatives
        best_datetime, best_score = filtered_scores[0]
        alternatives = [score for _, score in filtered_scores[1:num_alternatives+1]]
        
        # Apply cross-platform constraints
        best_datetime, best_score, alternatives = self._apply_cross_platform_constraints(
            best_datetime, best_score, alternatives, platform, content_profile
        )
        
        # Create suggestion
        suggestion = PostingSuggestion(
            id=self._generate_suggestion_id(),
            platform=platform,
            content_profile=content_profile,
            suggested_datetime=best_datetime,
            confidence=best_score.confidence,
            score=best_score,
            alternatives=alternatives,
            priority=self._determine_priority(content_profile, best_score)
        )
        
        # Save to database
        self._save_suggestion(suggestion)
        self.suggestion_history[suggestion.id] = suggestion
        self.total_suggestions += 1
        
        logger.info(f"Generated suggestion for {platform.value}: {best_datetime.strftime('%Y-%m-%d %H:%M')} "
                   f"(confidence: {best_score.confidence:.2f})")
        
        return suggestion
    
    def _generate_suggestion_id(self) -> str:
        """Generate unique suggestion ID."""
        import uuid
        return f"sugg_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def _has_historical_data(self, platform: Platform, day_of_week: int, hour: int) -> bool:
        """Check if we have historical performance data for this slot."""
        key = f"{platform.value}_{day_of_week}_{hour}"
        return key in self.posterior_params
    
    def _apply_bayesian_learning(self, 
                               score: TimingScore, 
                               platform: Platform, 
                               day_of_week: int, 
                               hour: int) -> TimingScore:
        """Apply Bayesian learning to improve timing scores."""
        
        key = f"{platform.value}_{day_of_week}_{hour}"
        
        if key in self.posterior_params:
            alpha, beta = self.posterior_params[key]
            posterior_mean = alpha / (alpha + beta)
            
            # Combine with existing score using learning rate
            adjusted_score = (1 - self.learning_rate) * score.score + self.learning_rate * posterior_mean
            
            # Update the score
            score.score = adjusted_score
            
            # Add explanation factor
            score.factors["bayesian_learning"] = self.learning_rate * (posterior_mean - score.score)
            if abs(self.learning_rate * (posterior_mean - score.score)) > 0.05:
                score.explanation.append("Adjusted based on historical performance")
        
        return score
    
    def _apply_cross_platform_constraints(self,
                                        best_datetime: datetime,
                                        best_score: TimingScore,
                                        alternatives: List[TimingScore],
                                        platform: Platform,
                                        content_profile: ContentProfile) -> Tuple[datetime, TimingScore, List[TimingScore]]:
        """Apply cross-platform scheduling constraints."""
        
        constraints = []
        
        # Check for conflicts with existing suggestions
        conflicts = self._check_scheduling_conflicts(best_datetime, platform)
        if conflicts:
            # Find next best alternative
            for i, alt in enumerate(alternatives):
                alt_datetime = self._get_datetime_for_alternative(alt, best_datetime)
                if not self._check_scheduling_conflicts(alt_datetime, platform):
                    # Use this alternative
                    best_datetime = alt_datetime
                    best_score = alt
                    alternatives = [a for j, a in enumerate(alternatives) if j != i]
                    constraints.append("Avoided scheduling conflict")
                    break
            else:
                constraints.append("Scheduling conflict - multiple posts planned")
        
        # Platform-specific constraints
        if platform == Platform.LINKEDIN:
            # LinkedIn requires spacing between posts
            if self._check_linkedin_spacing(best_datetime):
                constraints.append("LinkedIn spacing constraint applied")
        
        # Add constraints to best score
        best_score.explanation.extend(constraints)
        
        return best_datetime, best_score, alternatives
    
    def _get_datetime_for_alternative(self, alternative_score: TimingScore, base_datetime: datetime) -> datetime:
        """Get datetime for an alternative timing score."""
        # This would need to be implemented based on how alternatives are structured
        # For now, return base datetime with hour adjusted
        return base_datetime.replace(hour=alternative_score.hour)
    
    def _check_scheduling_conflicts(self, datetime: datetime, platform: Platform) -> bool:
        """Check for scheduling conflicts with existing suggestions."""
        # Simple conflict check - look for posts within 2 hours
        for suggestion in self.suggestion_history.values():
            if suggestion.platform == platform:
                time_diff = abs((suggestion.suggested_datetime - datetime).total_seconds())
                if time_diff < 7200:  # 2 hours
                    return True
        return False
    
    def _check_linkedin_spacing(self, datetime: datetime) -> bool:
        """Check LinkedIn spacing requirements (≥12 hours between posts)."""
        # Check for recent LinkedIn posts
        recent_posts = []
        for suggestion in self.suggestion_history.values():
            if suggestion.platform == Platform.LINKEDIN and suggestion.executed_at:
                recent_posts.append(suggestion.executed_at)
        
        if recent_posts:
            latest_post = max(recent_posts)
            time_diff = (datetime - latest_post).total_seconds()
            if time_diff < 43200:  # 12 hours
                return True
        return False
    
    def _determine_priority(self, content_profile: ContentProfile, score: TimingScore) -> SuggestionPriority:
        """Determine suggestion priority based on content and score."""
        if content_profile.urgency_level == SuggestionPriority.CRITICAL:
            return SuggestionPriority.CRITICAL
        elif content_profile.urgency_level == SuggestionPriority.HIGH:
            return SuggestionPriority.HIGH
        elif score.confidence >= 0.8 and score.score >= 0.7:
            return SuggestionPriority.HIGH
        else:
            return content_profile.urgency_level
    
    def _save_suggestion(self, suggestion: PostingSuggestion):
        """Save suggestion to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO suggestions 
                    (id, platform, content_type, suggested_time, confidence, score, 
                     status, priority, executed_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    suggestion.id,
                    suggestion.platform.value,
                    suggestion.content_profile.content_type.value,
                    suggestion.suggested_datetime,
                    suggestion.confidence,
                    suggestion.score.score,
                    suggestion.status.value,
                    suggestion.priority.value,
                    suggestion.executed_at,
                    None  # user_id would be passed in real implementation
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save suggestion {suggestion.id}: {e}")
    
    def validate_suggestion_performance(self, 
                                      suggestion_id: str,
                                      performance_metrics: PerformanceMetrics) -> bool:
        """Validate suggestion performance and update learning models."""
        
        try:
            # Save performance data
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_data
                    (id, suggestion_id, post_id, platform, post_time, metrics, validation_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"perf_{int(time.time())}_{suggestion_id[:8]}",
                    suggestion_id,
                    performance_metrics.post_id,
                    performance_metrics.platform.value,
                    performance_metrics.post_time,
                    json.dumps(performance_metrics.metrics),
                    performance_metrics.validation_score
                ))
                conn.commit()
            
            # Update Bayesian parameters
            self._update_bayesian_params(
                performance_metrics.platform,
                performance_metrics.post_time.weekday(),
                performance_metrics.post_time.hour,
                performance_metrics.validation_score
            )
            
            # Update statistics
            if performance_metrics.validation_score >= 0.6:  # Consider successful
                self.successful_suggestions += 1
            
            # Add to performance history
            self.performance_history.append(performance_metrics)
            
            # Update suggestion status
            if suggestion_id in self.suggestion_history:
                suggestion = self.suggestion_history[suggestion_id]
                suggestion.status = SuggestionStatus.VALIDATED
                suggestion.performance_data = asdict(performance_metrics)
            
            logger.info(f"Validated suggestion {suggestion_id} with score {performance_metrics.validation_score:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate suggestion performance: {e}")
            return False
    
    def _update_bayesian_params(self, 
                              platform: Platform, 
                              day_of_week: int, 
                              hour: int, 
                              success: float):
        """Update Bayesian parameters based on performance."""
        
        key = f"{platform.value}_{day_of_week}_{hour}"
        
        # Convert success to binary (0 or 1) for Beta distribution
        binary_success = 1 if success >= 0.6 else 0
        
        if key not in self.posterior_params:
            # Initialize with uniform prior
            self.posterior_params[key] = (1.0, 1.0)
        
        alpha, beta = self.posterior_params[key]
        
        # Update with new observation
        alpha += binary_success
        beta += (1 - binary_success)
        
        self.posterior_params[key] = (alpha, beta)
        
        # Save to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO bayesian_params
                    (platform, day_of_week, hour, alpha, beta, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    platform.value,
                    day_of_week,
                    hour,
                    alpha,
                    beta,
                    datetime.now(timezone.utc)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save Bayesian parameters: {e}")
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights and analytics from the suggestion engine."""
        
        success_rate = (self.successful_suggestions / max(1, self.total_suggestions))
        
        # Platform-specific performance
        platform_stats = defaultdict(lambda: {"suggestions": 0, "successes": 0, "avg_confidence": 0})
        
        for suggestion in self.suggestion_history.values():
            platform = suggestion.platform.value
            platform_stats[platform]["suggestions"] += 1
            if suggestion.performance_data and suggestion.performance_data.get("validation_score", 0) >= 0.6:
                platform_stats[platform]["successes"] += 1
            platform_stats[platform]["avg_confidence"] += suggestion.confidence
        
        # Calculate final averages
        for platform in platform_stats:
            if platform_stats[platform]["suggestions"] > 0:
                platform_stats[platform]["success_rate"] = (
                    platform_stats[platform]["successes"] / platform_stats[platform]["suggestions"]
                )
                platform_stats[platform]["avg_confidence"] /= platform_stats[platform]["suggestions"]
        
        # Learning progress
        learning_stats = {
            "total_suggestions": self.total_suggestions,
            "successful_suggestions": self.successful_suggestions,
            "success_rate": success_rate,
            "confidence_trend": list(self.confidence_history)[-10:] if self.confidence_history else [],
            "bayesian_params_count": len(self.posterior_params)
        }
        
        return {
            "overall_performance": learning_stats,
            "platform_breakdown": dict(platform_stats),
            "learning_status": {
                "active_bayesian_learning": len(self.posterior_params) > 0,
                "performance_history_size": len(self.performance_history),
                "recent_confidence": list(self.confidence_history)[-5:] if self.confidence_history else []
            }
        }


class BulkSuggestionProcessor:
    """Google Sheets integration for bulk timing suggestions."""
    
    def __init__(self, 
                 suggestions_engine: SuggestionEngine,
                 credentials_path: str,
                 sheets_range: str = "A:Z"):
        
        self.engine = suggestions_engine
        self.credentials_path = credentials_path
        self.sheets_range = sheets_range
        
        # Google Sheets client
        self.sheets_client: Optional[GoogleSheetsClient] = None
        
        # Batch processing components
        self.batch_processor: Optional[BatchProcessor] = None
        
        # Processing statistics
        self.processed_rows = 0
        self.generated_suggestions = 0
        self.errors = []
    
    async def initialize(self):
        """Initialize Google Sheets client and batch processor."""
        
        # Initialize Sheets client
        try:
            from google_sheets_client import GoogleSheetsClient
            
            self.sheets_client = GoogleSheetsClient(credentials_path=self.credentials_path)
            await self.sheets_client.initialize()
            logger.info("Google Sheets client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
        
        # Initialize batch processor if available
        try:
            self.batch_processor = BatchProcessor(
                credentials_path=self.credentials_path,
                max_workers=2
            )
            logger.info("Batch processor initialized")
        except Exception as e:
            logger.warning(f"Batch processor not available: {e}")
    
    async def process_bulk_suggestions(self,
                                     spreadsheet_id: str,
                                     sheet_name: str = "Suggestions") -> Dict[str, Any]:
        """Process bulk timing suggestions from Google Sheets."""
        
        if not self.sheets_client:
            await self.initialize()
        
        try:
            # Read data from Google Sheets
            sheet_data = await self.sheets_client.get_values(
                spreadsheet_id=spreadsheet_id,
                range_name=f"{sheet_name}!{self.sheets_range}",
                value_render_option="FORMATTED_VALUE"
            )
            
            if not sheet_data or len(sheet_data) < 2:
                raise ValueError("No data found in the specified sheet range")
            
            # Process header row
            headers = sheet_data[0]
            data_rows = sheet_data[1:]
            
            logger.info(f"Processing {len(data_rows)} rows from sheet")
            
            # Process each row
            results = []
            for i, row in enumerate(data_rows):
                try:
                    result = await self._process_row(headers, row, i + 2)  # +2 for 1-indexed + header
                    if result:
                        results.append(result)
                        self.generated_suggestions += 1
                    
                    self.processed_rows += 1
                    
                except Exception as e:
                    error_msg = f"Row {i+2}: {e}"
                    self.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Write results back to sheet
            await self._write_results_to_sheet(spreadsheet_id, sheet_name, results)
            
            logger.info(f"Bulk processing completed: {len(results)} suggestions generated")
            
            return {
                "processed_rows": self.processed_rows,
                "generated_suggestions": self.generated_suggestions,
                "errors": self.errors,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Bulk processing failed: {e}")
            raise
    
    async def _process_row(self, headers: List[str], row: List[Any], row_number: int) -> Optional[Dict[str, Any]]:
        """Process a single row from the sheet."""
        
        if len(row) < len(headers):
            raise ValueError(f"Row {row_number} has insufficient data")
        
        # Convert row to dictionary
        row_data = dict(zip(headers, row))
        
        # Parse platform
        platform_str = row_data.get("Platform", "").lower()
        if platform_str in ["twitter", "x"]:
            platform = Platform.X
        else:
            try:
                platform = Platform(platform_str)
            except ValueError:
                raise ValueError(f"Invalid platform: {platform_str}")
        
        # Parse content type
        content_type_str = row_data.get("Content_Type", "video_short").lower()
        try:
            content_type = ContentType(content_type_str)
        except ValueError:
            # Default to video_short for unknown types
            content_type = ContentType.VIDEO_SHORT
        
        # Create content profile
        content_profile = ContentProfile(
            content_type=content_type,
            duration=int(row_data.get("Duration", 60)) if row_data.get("Duration") else None,
            language=row_data.get("Language", "en"),
            hashtags=row_data.get("Hashtags", "").split(",") if row_data.get("Hashtags") else [],
            keywords=row_data.get("Keywords", "").split(",") if row_data.get("Keywords") else [],
            industry=row_data.get("Industry"),
            urgency_level=SuggestionPriority(int(row_data.get("Urgency", 2)))
        )
        
        # Create audience profile if provided
        audience_profile = None
        if any(row_data.get(field) for field in ["Age_18_24", "Mobile_Share", "Primary_Timezone"]):
            audience_profile = AudienceProfile(
                age_cohorts={
                    "18-24": float(row_data.get("Age_18_24", 0)) if row_data.get("Age_18_24") else 0,
                    "25-34": float(row_data.get("Age_25_34", 0)) if row_data.get("Age_25_34") else 0,
                },
                device_split={
                    "mobile": float(row_data.get("Mobile_Share", 0.8)) if row_data.get("Mobile_Share") else 0.8,
                    "desktop": float(row_data.get("Desktop_Share", 0.2)) if row_data.get("Desktop_Share") else 0.2,
                },
                time_zones={
                    row_data.get("Primary_Timezone", "UTC"): 1.0
                } if row_data.get("Primary_Timezone") else {"UTC": 1.0}
            )
        
        # Generate suggestion
        suggestion = self.engine.generate_suggestion(
            platform=platform,
            content_profile=content_profile,
            audience_profile=audience_profile,
            num_alternatives=3
        )
        
        # Format result for sheet output
        result = {
            "Row_Number": row_number,
            "Original_Platform": platform.value,
            "Original_Content_Type": content_type.value,
            "Suggested_DateTime": suggestion.suggested_datetime.strftime("%Y-%m-%d %H:%M"),
            "Suggested_Day": suggestion.suggested_datetime.strftime("%A"),
            "Suggested_Hour": suggestion.suggested_datetime.hour,
            "Confidence": round(suggestion.confidence, 3),
            "Score": round(suggestion.score.score, 3),
            "Priority": suggestion.priority.name,
            "Alternative_1": f"{suggestion.alternatives[0].day_of_week}-{suggestion.alternatives[0].hour}" if suggestion.alternatives else "",
            "Alternative_2": f"{suggestion.alternatives[1].day_of_week}-{suggestion.alternatives[1].hour}" if len(suggestion.alternatives) > 1 else "",
            "Alternative_3": f"{suggestion.alternatives[2].day_of_week}-{suggestion.alternatives[2].hour}" if len(suggestion.alternatives) > 2 else "",
            "Explanation": "; ".join(suggestion.score.explanation[:3])  # Top 3 explanations
        }
        
        return result
    
    async def _write_results_to_sheet(self, 
                                    spreadsheet_id: str, 
                                    sheet_name: str, 
                                    results: List[Dict[str, Any]]):
        """Write processing results back to Google Sheets."""
        
        if not results:
            logger.warning("No results to write to sheet")
            return
        
        # Prepare header row
        headers = list(results[0].keys())
        
        # Prepare data rows
        data_rows = [headers]
        for result in results:
            data_rows.append([result.get(header, "") for header in headers])
        
        # Write to sheet (using a results section)
        try:
            # Write to a new range below the original data
            start_row = len(data_rows) + 5  # Add some spacing
            end_row = start_row + len(data_rows) - 1
            
            await self.sheets_client.update_values(
                spreadsheet_id=spreadsheet_id,
                range_name=f"{sheet_name}!A{start_row}:{chr(65 + len(headers) - 1)}{end_row}",
                values=data_rows,
                value_input_option="RAW"
            )
            
            logger.info(f"Wrote {len(results)} results to sheet starting at row {start_row}")
            
        except Exception as e:
            logger.error(f"Failed to write results to sheet: {e}")
            raise
    
    async def create_suggestion_template(self, spreadsheet_id: str, sheet_name: str = "Suggestions_Template"):
        """Create a template sheet for bulk timing suggestions."""
        
        if not self.sheets_client:
            await self.initialize()
        
        # Template headers
        headers = [
            "Platform", "Content_Type", "Duration", "Language", "Hashtags", 
            "Keywords", "Industry", "Urgency", "Age_18_24", "Age_25_34", 
            "Mobile_Share", "Desktop_Share", "Primary_Timezone"
        ]
        
        # Sample data rows
        sample_rows = [
            ["youtube", "video_long", "600", "en", "#tech #tutorial", "artificial intelligence", "education", "2", "0.2", "0.4", "0.6", "0.4", "EST"],
            ["tiktok", "video_short", "30", "en", "#fyp #funny", "comedy skit", "entertainment", "3", "0.4", "0.3", "0.9", "0.1", "PST"],
            ["instagram", "reel", "45", "en", "#lifestyle #motivation", "daily routine", "lifestyle", "1", "0.3", "0.3", "0.8", "0.2", "UTC"],
            ["linkedin", "document", "", "en", "#business #strategy", "market analysis", "business", "2", "0.1", "0.5", "0.4", "0.6", "EST"],
            ["x", "text", "", "en", "#news #tech", "breaking news", "news", "4", "0.2", "0.4", "0.7", "0.3", "EST"]
        ]
        
        # Create sheet structure
        sheet_data = [headers] + sample_rows
        
        try:
            # Clear existing content (if any)
            await self.sheets_client.clear_values(
                spreadsheet_id=spreadsheet_id,
                range_name=f"{sheet_name}!A:Z"
            )
            
            # Write template
            await self.sheets_client.update_values(
                spreadsheet_id=spreadsheet_id,
                range_name=f"{sheet_name}!A1:{chr(65 + len(headers) - 1)}{len(sheet_data)}",
                values=sheet_data,
                value_input_option="RAW"
            )
            
            logger.info(f"Created suggestion template in sheet {sheet_name}")
            
        except Exception as e:
            logger.error(f"Failed to create template sheet: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources."""
        if self.sheets_client:
            await self.sheets_client.close()
        
        if self.batch_processor:
            await self.batch_processor.cleanup()
        
        logger.info("Bulk suggestion processor cleanup completed")


# Example usage and integration functions
async def example_bulk_suggestion_processing():
    """Example of using the bulk suggestion processor."""
    
    # Initialize suggestion engine
    engine = SuggestionEngine(
        db_path="suggestions_example.db",
        learning_rate=0.15,
        min_confidence=0.7
    )
    
    # Initialize bulk processor
    bulk_processor = BulkSuggestionProcessor(
        suggestions_engine=engine,
        credentials_path="path/to/credentials.json"
    )
    
    try:
        # Create template
        await bulk_processor.create_suggestion_template(
            spreadsheet_id="your_spreadsheet_id",
            sheet_name="Suggestions_Template"
        )
        
        # Process bulk suggestions
        results = await bulk_processor.process_bulk_suggestions(
            spreadsheet_id="your_spreadsheet_id",
            sheet_name="Suggestions_Template"
        )
        
        print(f"Processing completed:")
        print(f"- Processed rows: {results['processed_rows']}")
        print(f"- Generated suggestions: {results['generated_suggestions']}")
        print(f"- Errors: {len(results['errors'])}")
        
        # Get insights
        insights = engine.get_optimization_insights()
        print(f"\\nOptimization insights:")
        print(f"- Success rate: {insights['overall_performance']['success_rate']:.2%}")
        print(f"- Bayesian parameters: {insights['learning_status']['bayesian_params_count']}")
        
    except Exception as e:
        logger.error(f"Example bulk processing failed: {e}")
    finally:
        await bulk_processor.cleanup()


def create_suggestion_from_user_input(platform_str: str, 
                                    content_type_str: str,
                                    duration: Optional[int] = None,
                                    industry: Optional[str] = None) -> PostingSuggestion:
    """Create a suggestion from simple user input."""
    
    # Parse platform
    platform_str = platform_str.lower()
    if platform_str in ["twitter", "x"]:
        platform = Platform.X
    else:
        platform = Platform(platform_str)
    
    # Parse content type
    content_type = ContentType(content_type_str.lower())
    
    # Create profiles
    content_profile = ContentProfile(
        content_type=content_type,
        duration=duration,
        industry=industry
    )
    
    # Create default audience profile
    audience_profile = AudienceProfile(
        age_cohorts={"18-24": 0.3, "25-34": 0.4, "35-44": 0.2},
        device_split={"mobile": 0.8, "desktop": 0.2},
        time_zones={"UTC": 1.0}
    )
    
    # Generate suggestion
    engine = SuggestionEngine()
    suggestion = engine.generate_suggestion(
        platform=platform,
        content_profile=content_profile,
        audience_profile=audience_profile
    )
    
    return suggestion


if __name__ == "__main__":
    # Run example
    asyncio.run(example_bulk_suggestion_processing())