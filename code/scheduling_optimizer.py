#!/usr/bin/env python3
"""
Scheduling Optimizer with AI Recommendations

This module implements a comprehensive scheduling optimization system that:
1. Calculates optimal posting times using evidence-based algorithms
2. Coordinates multi-platform scheduling with constraint handling
3. Provides machine learning-based timing recommendations
4. Integrates with batch processing systems
5. Tracks performance and adapts scheduling policies dynamically

Based on the optimization algorithms and batch integration specifications.
"""

import asyncio
import json
import logging
import math
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import uuid4

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class ContentType(Enum):
    """Content types for different platforms."""
    # YouTube
    YOUTUBE_LONG_FORM = "youtube_long_form"
    YOUTUBE_SHORTS = "youtube_shorts"
    
    # TikTok
    TIKTOK_VIDEO = "tiktok_video"
    
    # Instagram
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_REELS = "instagram_reels"
    INSTAGRAM_STORIES = "instagram_stories"
    INSTAGRAM_CAROUSEL = "instagram_carousel"
    
    # Twitter/X
    TWITTER_POST = "twitter_post"
    TWITTER_THREAD = "twitter_thread"
    
    # LinkedIn
    LINKEDIN_POST = "linkedin_post"
    LINKEDIN_CAROUSEL = "linkedin_carousel"
    
    # Facebook
    FACEBOOK_POST = "facebook_post"
    FACEBOOK_REELS = "facebook_reels"


class PriorityTier(Enum):
    """Priority tiers for job scheduling."""
    URGENT = 3
    NORMAL = 2
    LOW = 1


@dataclass
class AudienceProfile:
    """Audience demographics and device information."""
    age_cohorts: Dict[str, float]  # {'18-24': 0.3, '25-34': 0.4, ...}
    device_split: Dict[str, float]  # {'mobile': 0.7, 'desktop': 0.3}
    time_zone_weights: Dict[str, float]  # {'UTC-5': 0.3, 'UTC-8': 0.2, ...}
    geography: Optional[Dict[str, float]] = None


@dataclass
class PostingWindow:
    """A time window for posting content."""
    start_hour: int
    end_hour: int
    weight: float
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday


@dataclass
class PerformanceMetrics:
    """Performance metrics for a posted piece of content."""
    platform: Platform
    content_type: ContentType
    posted_at: datetime
    
    # Platform-specific KPIs
    reach: Optional[int] = None
    impressions: Optional[int] = None
    engagement_rate: Optional[float] = None
    watch_time: Optional[float] = None  # seconds
    completion_rate: Optional[float] = None
    ctr: Optional[float] = None  # click-through rate
    saves: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None
    
    # Success classification
    is_successful: bool = False


@dataclass
class SchedulingConstraint:
    """Scheduling constraint for multi-platform coordination."""
    platform: Platform
    min_gap_hours: float = 12.0
    max_concurrent_posts: int = 3
    prohibited_windows: Optional[List[PostingWindow]] = None
    preferred_windows: Optional[List[PostingWindow]] = None


@dataclass
class SchedulePlan:
    """A generated schedule plan for bulk content."""
    schedule_id: str
    created_at: datetime
    bulk_job_id: Optional[str] = None
    
    # Job assignments
    job_assignments: List[Dict] = None
    
    # Performance metrics
    projected_throughput: Optional[float] = None
    quota_compliance_score: Optional[float] = None
    schedule_adherence_score: Optional[float] = None


class SchedulingOptimizer:
    """
    Main scheduling optimizer class that implements the algorithm suite from the specification.
    """
    
    def __init__(self, db_path: str = "scheduling_optimizer.db"):
        """Initialize the scheduling optimizer."""
        self.db_path = db_path
        self._init_database()
        
        # Initialize platform baseline windows from evidence synthesis
        self._platform_windows = self._init_platform_windows()
        
        # Initialize machine learning models
        self._ml_models = {}
        self._scalers = {}
        
        # Initialize adaptive parameters
        self._daypart_weights = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        self._posterior_params = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: (1, 1))))
        self._seasonality_factors = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        
        # ML training data
        self._training_data = []
        
        # Current constraints
        self._constraints = {}
        
        logger.info("SchedulingOptimizer initialized successfully")
    
    def _init_database(self):
        """Initialize SQLite database for storing optimization data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Performance history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    posted_at TIMESTAMP NOT NULL,
                    hour_of_day INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    reach INTEGER,
                    impressions INTEGER,
                    engagement_rate REAL,
                    watch_time REAL,
                    completion_rate REAL,
                    ctr REAL,
                    saves INTEGER,
                    shares INTEGER,
                    comments INTEGER,
                    success BOOLEAN NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Schedule plans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_plans (
                    schedule_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    bulk_job_id TEXT,
                    plan_data TEXT NOT NULL,
                    projected_throughput REAL,
                    quota_compliance_score REAL,
                    schedule_adherence_score REAL
                )
            ''')
            
            # Adaptive parameters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adaptive_params (
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    hour_of_day INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    posterior_alpha REAL NOT NULL,
                    posterior_beta REAL NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (platform, content_type, day_of_week, hour_of_day)
                )
            ''')
            
            # Training data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    features TEXT NOT NULL,
                    label REAL NOT NULL,
                    posted_at TIMESTAMP NOT NULL
                )
            ''')
            
            conn.commit()
    
    def _init_platform_windows(self) -> Dict[Platform, Dict[int, List[PostingWindow]]]:
        """
        Initialize platform baseline windows from 2025 evidence synthesis.
        Returns: Dict[Platform][day_of_week] -> List[PostingWindow]
        """
        windows = {}
        
        # YouTube baseline windows
        windows[Platform.YOUTUBE] = {
            # Monday-Friday: Weekday afternoons
            0: [PostingWindow(15, 17, 0.8), PostingWindow(18, 20, 0.9)],  # Mon
            1: [PostingWindow(15, 17, 0.85), PostingWindow(18, 20, 0.9)],  # Tue
            2: [PostingWindow(16, 17, 1.0), PostingWindow(15, 17, 0.95)],  # Wed (strongest: 4pm)
            3: [PostingWindow(15, 17, 0.85), PostingWindow(18, 20, 0.9)],  # Thu
            4: [PostingWindow(15, 17, 0.8), PostingWindow(18, 20, 0.85)],  # Fri
            5: [PostingWindow(11, 15, 0.75)],  # Sat: Later morning-mid-afternoon
            6: [PostingWindow(11, 15, 0.7)]   # Sun
        }
        
        # TikTok baseline windows
        windows[Platform.TIKTOK] = {
            0: [PostingWindow(17, 19, 0.85)],  # Mon: 5-7pm
            1: [PostingWindow(14, 15, 0.9), PostingWindow(16, 17, 0.9), PostingWindow(20, 21, 0.85)],  # Tue: 2pm, 4pm, 8pm
            2: [PostingWindow(16, 18, 1.0)],  # Wed: 4-6pm (strongest day)
            3: [PostingWindow(13, 14, 0.9), PostingWindow(15, 17, 0.85)],  # Thu: 1pm, 3-5pm
            4: [PostingWindow(14, 18, 0.85)],  # Fri: 2-6pm
            5: [PostingWindow(16, 19, 0.6)],  # Sat: 4-7pm (quietest overall)
            6: [PostingWindow(16, 20, 0.9)]   # Sun: 4-8pm (evening spike)
        }
        
        # Instagram baseline windows
        windows[Platform.INSTAGRAM] = {
            # Feed/Carousels: Mon-Thu 10am-3pm
            0: [PostingWindow(10, 15, 0.9), PostingWindow(15, 16, 0.85)],  # Mon
            1: [PostingWindow(10, 15, 0.9), PostingWindow(15, 16, 0.85)],  # Tue
            2: [PostingWindow(10, 15, 0.9), PostingWindow(15, 16, 0.85), PostingWindow(18, 19, 0.8)],  # Wed
            3: [PostingWindow(10, 15, 0.9), PostingWindow(15, 16, 0.85)],  # Thu
            4: [PostingWindow(10, 14, 0.7), PostingWindow(16, 18, 0.75)],  # Fri (lighter)
            5: [PostingWindow(10, 13, 0.6), PostingWindow(17, 19, 0.7)],  # Sat
            6: [PostingWindow(10, 13, 0.6), PostingWindow(17, 19, 0.7)]   # Sun
        }
        
        # X (Twitter) baseline windows
        windows[Platform.TWITTER] = {
            0: [PostingWindow(8, 10, 0.8)],  # Mon: 8-10am (weaker)
            1: [PostingWindow(10, 13, 0.9), PostingWindow(14, 16, 0.85)],  # Tue
            2: [PostingWindow(9, 12, 1.0), PostingWindow(14, 16, 0.85)],  # Wed: ~9am peak
            3: [PostingWindow(10, 13, 0.9), PostingWindow(14, 16, 0.85)],  # Thu
            4: [PostingWindow(10, 12, 0.7)],  # Fri: 10-12am (lighter)
            5: [PostingWindow(10, 13, 0.4)],  # Sat: weekend underperforms
            6: [PostingWindow(9, 12, 0.3)]   # Sun: quietest day
        }
        
        # LinkedIn baseline windows
        windows[Platform.LINKEDIN] = {
            0: [PostingWindow(11, 12, 0.8)],  # Mon: 11am-noon
            1: [PostingWindow(8, 14, 0.9)],  # Tue: 8am-2pm
            2: [PostingWindow(8, 9, 0.9), PostingWindow(12, 13, 0.95)],  # Wed: 8am, 12pm
            3: [PostingWindow(8, 9, 0.9), PostingWindow(12, 13, 0.95)],  # Thu: 8am, 12pm
            4: [PostingWindow(7, 14, 0.7)],  # Fri: 7am-2pm (lighter)
            5: [PostingWindow(9, 11, 0.3)],  # Sat: weekend underperforms
            6: [PostingWindow(10, 12, 0.3)]  # Sun
        }
        
        # Facebook baseline windows
        windows[Platform.FACEBOOK] = {
            0: [PostingWindow(9, 18, 0.85)],  # Mon: 9am-6pm
            1: [PostingWindow(9, 18, 0.85)],  # Tue
            2: [PostingWindow(8, 18, 0.9)],  # Wed
            3: [PostingWindow(8, 18, 0.9)],  # Thu
            4: [PostingWindow(9, 11, 0.8), PostingWindow(14, 16, 0.8)],  # Fri: 9-11am, 2-4pm
            5: [PostingWindow(10, 12, 0.6), PostingWindow(15, 17, 0.6)],  # Sat
            6: [PostingWindow(8, 10, 0.7)]   # Sun: especially for travel/hospitality
        }
        
        return windows
    
    def calculate_timing_scores(self, 
                               platform: Platform,
                               content_type: ContentType,
                               audience_profile: AudienceProfile,
                               day_of_week: int,
                               calendar_signals: Optional[Dict] = None) -> Dict[int, float]:
        """
        Calculate timing scores for a given platform, content type, and audience.
        
        Implements the scoring model from the optimization algorithms specification:
        Score(p, d, h) = w_base(p, d, h) × (1 + w_demo × DemoAdjust) × (1 + w_fmt × FormatAdjust) × 
                         (1 + w_seas × Seasonality) × RecencyPenalty × ComplianceGuardrails
        
        Args:
            platform: Target platform
            content_type: Content format
            audience_profile: Audience demographics and device info
            day_of_week: Day of week (0=Monday, 6=Sunday)
            calendar_signals: Optional holiday/seasonality indicators
            
        Returns:
            Dict mapping hour -> score (0-1)
        """
        scores = {}
        
        # Hyperparameters (tunable)
        w_demo = 0.3
        w_fmt = 0.2
        w_seas = 0.1
        
        # 1. Initialize with platform baseline
        for hour in range(24):
            scores[hour] = self._get_baseline_weight(platform, day_of_week, hour)
        
        # 2. Apply demographic adjustments
        demo_adjust = self._calculate_demo_adjustment(audience_profile, day_of_week)
        for hour in range(24):
            scores[hour] *= (1 + w_demo * demo_adjust.get(hour, 0))
        
        # 3. Apply content format adjustments
        format_adjust = self._calculate_format_adjustment(platform, content_type)
        for hour in range(24):
            scores[hour] *= (1 + w_fmt * format_adjust.get(hour, 0))
        
        # 4. Apply seasonality signals
        seasonality = self._calculate_seasonality(day_of_week, calendar_signals or {})
        for hour in range(24):
            scores[hour] *= (1 + w_seas * seasonality.get(hour, 0))
        
        # 5. Apply recency penalty (check if recent posts exist)
        recency_penalty = self._calculate_recency_penalty(platform, content_type)
        for hour in range(24):
            scores[hour] *= recency_penalty.get(hour, 1.0)
        
        # 6. Apply compliance guardrails
        compliance_mask = self._apply_compliance_guardrails(platform, content_type)
        for hour in range(24):
            if not compliance_mask.get(hour, True):
                scores[hour] = 0.0
        
        # 7. Normalize scores
        max_score = max(scores.values()) if scores.values() else 1.0
        if max_score > 0:
            scores = {hour: score / max_score for hour, score in scores.items()}
        
        return scores
    
    def _get_baseline_weight(self, platform: Platform, day_of_week: int, hour: int) -> float:
        """Get baseline weight for platform/day/hour combination."""
        platform_windows = self._platform_windows.get(platform, {})
        day_windows = platform_windows.get(day_of_week, [])
        
        for window in day_windows:
            if window.start_hour <= hour < window.end_hour:
                return window.weight
        
        return 0.1  # Default low weight for non-preferred hours
    
    def _calculate_demo_adjustment(self, audience: AudienceProfile, day_of_week: int) -> Dict[int, float]:
        """Calculate demographic-based adjustments."""
        adjustments = {}
        
        # Mobile-first audiences favor evening/weekend hours
        mobile_share = audience.device_split.get('mobile', 0.5)
        young_audience_share = sum([
            audience.age_cohorts.get('18-24', 0),
            audience.age_cohorts.get('25-34', 0)
        ])
        
        if mobile_share > 0.7 and young_audience_share > 0.5:
            # Boost evening hours (6pm-11pm) and weekend mornings
            for hour in range(18, 24):
                adjustments[hour] = adjustments.get(hour, 0) + 0.1
            
            if day_of_week in [5, 6]:  # Weekend
                for hour in range(8, 12):
                    adjustments[hour] = adjustments.get(hour, 0) + 0.05
        
        # Work-age audiences favor post-workday windows
        work_age_share = sum([
            audience.age_cohorts.get('25-34', 0),
            audience.age_cohorts.get('35-44', 0)
        ])
        
        if work_age_share > 0.4 and day_of_week < 5:  # Weekdays
            # Boost 3-6pm window
            for hour in range(15, 18):
                adjustments[hour] = adjustments.get(hour, 0) + 0.08
        
        return adjustments
    
    def _calculate_format_adjustment(self, platform: Platform, content_type: ContentType) -> Dict[int, float]:
        """Calculate content format-specific adjustments."""
        adjustments = {}
        
        # YouTube Shorts: reduce timing sensitivity
        if content_type == ContentType.YOUTUBE_SHORTS:
            # Flatten timing sensitivity, boost some evening hours
            for hour in range(24):
                adjustments[hour] = -0.1 if 0 <= hour <= 8 else 0.05
        
        # Instagram Reels: boost bookend windows and midday
        elif content_type == ContentType.INSTAGRAM_REELS:
            # Morning bookends (6-9am) and evening (6-9pm), plus midday
            for hour in [6, 7, 8, 18, 19, 20]:
                adjustments[hour] = adjustments.get(hour, 0) + 0.1
            for hour in range(11, 14):
                adjustments[hour] = adjustments.get(hour, 0) + 0.05
        
        # LinkedIn: boost business hours
        elif platform == Platform.LINKEDIN:
            for hour in range(8, 11):
                adjustments[hour] = adjustments.get(hour, 0) + 0.15
            for hour in [12, 13]:
                adjustments[hour] = adjustments.get(hour, 0) + 0.12
        
        # X (Twitter): morning-first strategy
        elif platform == Platform.TWITTER:
            for hour in range(8, 13):
                adjustments[hour] = adjustments.get(hour, 0) + 0.1
        
        return adjustments
    
    def _calculate_seasonality(self, day_of_week: int, calendar_signals: Dict) -> Dict[int, float]:
        """Calculate seasonality-based adjustments."""
        adjustments = {}
        
        # Weekend adjustments
        if day_of_week in [5, 6]:  # Saturday/Sunday
            for hour in range(24):
                adjustments[hour] = -0.05  # Slight weekend penalty for most content
        
        # Holiday indicators
        if calendar_signals.get('is_holiday', False):
            # Adjust for holiday posting patterns
            for hour in range(24):
                adjustments[hour] = adjustments.get(hour, 0) - 0.1
        
        # Back-to-school season, etc. could be added here
        season = calendar_signals.get('season', 'normal')
        if season == 'back_to_school':
            for hour in range(8, 10):
                adjustments[hour] = adjustments.get(hour, 0) + 0.05
        
        return adjustments
    
    def _calculate_recency_penalty(self, platform: Platform, content_type: ContentType) -> Dict[int, float]:
        """Calculate recency penalty to avoid posting collisions."""
        penalties = {}
        
        # Get recent posts for this platform
        recent_posts = self._get_recent_posts(platform, hours_back=24)
        
        # Apply minimum spacing rules
        min_gap = self._get_min_gap_hours(platform, content_type)
        
        for post in recent_posts:
            post_hour = post['posted_at'].hour
            # Penalize hours within the min gap window
            for hour in range(max(0, post_hour - int(min_gap)), 
                            min(24, post_hour + int(min_gap))):
                penalties[hour] = penalties.get(hour, 1.0) * 0.5  # 50% penalty
        
        return penalties
    
    def _apply_compliance_guardrails(self, platform: Platform, content_type: ContentType) -> Dict[int, bool]:
        """Apply platform compliance and policy guardrails."""
        guardrails = {}
        
        # LinkedIn: avoid link-heavy posts outside business hours
        if platform == Platform.LINKEDIN:
            for hour in range(24):
                if content_type == ContentType.LINKEDIN_POST:
                    if not (8 <= hour <= 14):  # Outside business hours
                        guardrails[hour] = False
        
        # General late-night restrictions (11pm-6am)
        for hour in range(23, 24) or range(0, 6):
            if platform != Platform.TIKTOK:  # TikTok is more flexible
                guardrails[hour] = False
        
        return guardrails
    
    def _get_recent_posts(self, platform: Platform, hours_back: int = 24) -> List[Dict]:
        """Get recent posts for a platform within the specified time window."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT platform, content_type, posted_at, hour_of_day
                FROM performance_history
                WHERE platform = ? AND posted_at >= ?
                ORDER BY posted_at DESC
            ''', (platform.value, cutoff_time))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_min_gap_hours(self, platform: Platform, content_type: ContentType) -> float:
        """Get minimum gap requirements between posts for platform/content type."""
        # Default spacing requirements from evidence synthesis
        spacing_map = {
            (Platform.LINKEDIN, ContentType.LINKEDIN_POST): 24.0,
            (Platform.LINKEDIN, ContentType.LINKEDIN_CAROUSEL): 24.0,
            (Platform.INSTAGRAM, ContentType.INSTAGRAM_REELS): 18.0,
            (Platform.INSTAGRAM, ContentType.INSTAGRAM_FEED): 12.0,
            (Platform.YOUTUBE, ContentType.YOUTUBE_SHORTS): 24.0,  # For small channels
            (Platform.YOUTUBE, ContentType.YOUTUBE_LONG_FORM): 48.0,
        }
        
        return spacing_map.get((platform, content_type), 12.0)
    
    def generate_optimal_schedule(self, 
                                 posts: List[Dict],
                                 constraints: List[SchedulingConstraint],
                                 audience_profiles: Dict[Platform, AudienceProfile],
                                 start_date: datetime,
                                 end_date: datetime,
                                 max_concurrent: int = 3) -> SchedulePlan:
        """
        Generate an optimal multi-platform schedule using greedy heuristic with dynamic penalties.
        
        Args:
            posts: List of posts to schedule, each with platform, content_type, priority, etc.
            constraints: Platform-specific scheduling constraints
            audience_profiles: Audience profiles for each platform
            start_date: Schedule start date
            end_date: Schedule end date
            max_concurrent: Maximum concurrent posts across platforms
            
        Returns:
            SchedulePlan with optimal assignments
        """
        schedule_id = str(uuid4())
        created_at = datetime.now()
        
        # Convert constraint dict for quick lookup
        constraint_map = {c.platform: c for c in constraints}
        
        # Calculate candidate posts with global priority scores
        candidate_posts = []
        for post in posts:
            platform = Platform(post['platform'])
            content_type = ContentType(post['content_type'])
            audience = audience_profiles.get(platform)
            
            if not audience:
                logger.warning(f"No audience profile for {platform}, skipping")
                continue
            
            # Calculate base timing scores for each day
            day_scores = {}
            current_date = start_date
            while current_date <= end_date:
                day_scores[current_date.date()] = self.calculate_timing_scores(
                    platform, content_type, audience, 
                    current_date.weekday()
                )
                current_date += timedelta(days=1)
            
            # Calculate global priority score
            base_priority = post.get('priority', PriorityTier.NORMAL.value)
            timing_score = max([max(scores.values()) for scores in day_scores.values()])
            global_score = base_priority * (1 + timing_score)
            
            candidate_posts.append({
                'post': post,
                'platform': platform,
                'content_type': content_type,
                'audience': audience,
                'day_scores': day_scores,
                'global_score': global_score,
                'constraint': constraint_map.get(platform)
            })
        
        # Sort by global priority score
        candidate_posts.sort(key=lambda x: x['global_score'], reverse=True)
        
        # Initialize schedule
        schedule = []
        scheduled_times = defaultdict(list)  # platform -> list of scheduled times
        active_concurrent = 0
        
        # Greedy assignment with dynamic penalties
        for candidate in candidate_posts:
            best_assignment = self._find_best_slot(
                candidate, schedule, scheduled_times, start_date, end_date, max_concurrent
            )
            
            if best_assignment:
                schedule.append(best_assignment)
                scheduled_times[candidate['platform']].append(best_assignment['scheduled_time'])
                active_concurrent = min(active_concurrent + 1, max_concurrent)
            
        # Create job assignments for batch integration
        job_assignments = []
        for assignment in schedule:
            job_assignments.append({
                'post_id': assignment['post'].get('id', str(uuid4())),
                'platform': assignment['platform'].value,
                'content_type': assignment['content_type'].value,
                'scheduled_time': assignment['scheduled_time'].isoformat(),
                'timing_score': assignment['timing_score'],
                'constraint_violations': assignment.get('constraint_violations', []),
                'penalty_score': assignment.get('penalty_score', 0)
            })
        
        # Calculate performance projections
        projected_throughput = self._calculate_project_throughput(job_assignments)
        quota_compliance_score = self._calculate_quota_compliance(job_assignments, constraints)
        schedule_adherence_score = self._calculate_adherence_score(job_assignments, constraint_map)
        
        return SchedulePlan(
            schedule_id=schedule_id,
            created_at=created_at,
            bulk_job_id=None,  # To be filled by caller
            job_assignments=job_assignments,
            projected_throughput=projected_throughput,
            quota_compliance_score=quota_compliance_score,
            schedule_adherence_score=schedule_adherence_score
        )
    
    def _find_best_slot(self, candidate, existing_schedule, scheduled_times, start_date, end_date, max_concurrent):
        """Find the best scheduling slot for a candidate post."""
        platform = candidate['platform']
        content_type = candidate['content_type']
        constraint = candidate['constraint']
        
        best_slot = None
        best_penalty = float('inf')
        
        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            day_scores = candidate['day_scores'].get(current_date.date())
            
            if not day_scores:
                current_date += timedelta(days=1)
                continue
            
            # Check each hour of the day
            for hour in range(24):
                scheduled_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Skip if outside business hours
                if scheduled_time < start_date or scheduled_time > end_date:
                    continue
                
                # Calculate total penalty for this slot
                penalty = self._calculate_assignment_penalty(
                    candidate, scheduled_time, existing_schedule, scheduled_times, max_concurrent
                )
                
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_slot = {
                        'post': candidate['post'],
                        'platform': platform,
                        'content_type': content_type,
                        'scheduled_time': scheduled_time,
                        'timing_score': day_scores.get(hour, 0),
                        'penalty_score': penalty,
                        'constraint_violations': self._check_constraint_violations(
                            candidate, scheduled_time, existing_schedule, scheduled_times
                        )
                    }
            
            current_date += timedelta(days=1)
        
        return best_slot
    
    def _calculate_assignment_penalty(self, candidate, scheduled_time, existing_schedule, scheduled_times, max_concurrent):
        """Calculate total penalty for assigning a post to a specific time slot."""
        platform = candidate['platform']
        constraint = candidate.get('constraint')
        penalty = 0.0
        
        # Collision penalty: check for posts at similar times
        collision_penalty = self._calculate_collision_penalty(scheduled_time, existing_schedule)
        penalty += collision_penalty
        
        # Spacing penalty: check minimum gaps
        spacing_penalty = self._calculate_spacing_penalty(platform, scheduled_time, scheduled_times, constraint)
        penalty += spacing_penalty
        
        # Concurrency penalty: check max concurrent posts
        concurrency_penalty = self._calculate_concurrency_penalty(scheduled_time, existing_schedule, max_concurrent)
        penalty += concurrency_penalty
        
        # Negative timing score (we want high scores)
        timing_score = candidate['day_scores'].get(scheduled_time.date(), {}).get(scheduled_time.hour, 0)
        penalty -= timing_score  # Subtract because lower penalty is better
        
        return penalty
    
    def _calculate_collision_penalty(self, scheduled_time, existing_schedule):
        """Calculate penalty for posting near other scheduled posts."""
        penalty = 0.0
        for assignment in existing_schedule:
            time_diff = abs((scheduled_time - assignment['scheduled_time']).total_seconds() / 3600)
            if time_diff < 1:  # Within 1 hour
                penalty += 10.0
            elif time_diff < 2:  # Within 2 hours
                penalty += 5.0
        
        return penalty
    
    def _calculate_spacing_penalty(self, platform, scheduled_time, scheduled_times, constraint):
        """Calculate penalty for violating minimum spacing requirements."""
        if not constraint:
            return 0.0
        
        min_gap = constraint.min_gap_hours
        recent_times = scheduled_times.get(platform, [])
        
        for recent_time in recent_times:
            time_diff = (scheduled_time - recent_time).total_seconds() / 3600
            if time_diff < min_gap:
                # Penalty increases as we get closer to recent posts
                gap_ratio = time_diff / min_gap
                penalty = (1 - gap_ratio) * 5.0
                return penalty
        
        return 0.0
    
    def _calculate_concurrency_penalty(self, scheduled_time, existing_schedule, max_concurrent):
        """Calculate penalty for exceeding concurrent post limits."""
        concurrent_count = 0
        for assignment in existing_schedule:
            time_diff = abs((scheduled_time - assignment['scheduled_time']).total_seconds() / 900)  # 15 min window
            if time_diff <= 0.25:  # Within 15 minutes
                concurrent_count += 1
        
        if concurrent_count >= max_concurrent:
            return (concurrent_count - max_concurrent + 1) * 20.0  # Heavy penalty for excess
        
        return 0.0
    
    def _check_constraint_violations(self, candidate, scheduled_time, existing_schedule, scheduled_times):
        """Check for constraint violations and return list of violations."""
        violations = []
        
        platform = candidate['platform']
        constraint = candidate.get('constraint')
        
        if constraint:
            # Check spacing
            min_gap = constraint.min_gap_hours
            recent_times = scheduled_times.get(platform, [])
            for recent_time in recent_times:
                time_diff = (scheduled_time - recent_time).total_seconds() / 3600
                if time_diff < min_gap:
                    violations.append(f"Violates minimum spacing: {time_diff:.1f}h < {min_gap}h")
            
            # Check concurrent limit
            concurrent_count = sum(1 for assignment in existing_schedule 
                                 if abs((scheduled_time - assignment['scheduled_time']).total_seconds() / 900) <= 0.25)
            if concurrent_count >= constraint.max_concurrent_posts:
                violations.append(f"Exceeds concurrent limit: {concurrent_count} >= {constraint.max_concurrent_posts}")
        
        return violations
    
    def _calculate_project_throughput(self, job_assignments) -> float:
        """Calculate projected throughput for the schedule."""
        if not job_assignments:
            return 0.0
        
        # Simple throughput calculation based on schedule density
        scheduled_times = [datetime.fromisoformat(assignment['scheduled_time']) for assignment in job_assignments]
        if len(scheduled_times) < 2:
            return float(len(job_assignments))
        
        # Calculate average time between posts
        sorted_times = sorted(scheduled_times)
        intervals = [(sorted_times[i+1] - sorted_times[i]).total_seconds() / 3600 
                    for i in range(len(sorted_times)-1)]
        avg_interval = sum(intervals) / len(intervals) if intervals else 24
        
        # Posts per hour
        throughput = 1.0 / avg_interval if avg_interval > 0 else 1.0
        
        return min(throughput, 10.0)  # Cap at reasonable maximum
    
    def _calculate_quota_compliance(self, job_assignments, constraints) -> float:
        """Calculate quota compliance score for the schedule."""
        if not job_assignments:
            return 1.0
        
        platform_counts = defaultdict(int)
        time_buckets = defaultdict(int)  # Hour-level buckets
        
        for assignment in job_assignments:
            platform = Platform(assignment['platform'])
            scheduled_time = datetime.fromisoformat(assignment['scheduled_time'])
            
            # Count posts per platform
            platform_counts[platform] += 1
            
            # Count posts per hour (for rate limiting assessment)
            hour_key = scheduled_time.strftime('%Y-%m-%d-%H')
            time_buckets[hour_key] += 1
        
        compliance_score = 1.0
        
        # Check for rate limiting violations (too many posts in same hour)
        max_per_hour = 5  # Conservative limit
        for bucket_count in time_buckets.values():
            if bucket_count > max_per_hour:
                compliance_score -= (bucket_count - max_per_hour) * 0.1
        
        # Platform-specific checks
        for platform, count in platform_counts.items():
            constraint = next((c for c in constraints if c.platform == platform), None)
            if constraint and count > constraint.max_concurrent_posts * 10:  # Daily limit heuristic
                compliance_score -= 0.1
        
        return max(0.0, compliance_score)
    
    def _calculate_adherence_score(self, job_assignments, constraint_map) -> float:
        """Calculate how well the schedule adheres to constraints."""
        if not job_assignments:
            return 1.0
        
        violations = 0
        total_assignments = len(job_assignments)
        
        for assignment in job_assignments:
            platform = Platform(assignment['platform'])
            constraint = constraint_map.get(platform)
            
            if constraint and assignment.get('constraint_violations'):
                violations += len(assignment['constraint_violations'])
        
        # Score decreases with violations
        adherence_score = 1.0 - (violations / (total_assignments * 2))  # Normalize violations
        return max(0.0, adherence_score)
    
    async def train_ml_models(self) -> Dict[str, float]:
        """
        Train machine learning models for timing predictions using historical performance data.
        
        Returns:
            Dict mapping model name to training accuracy
        """
        logger.info("Training ML models for timing predictions...")
        
        # Collect training data from database
        training_data = self._collect_training_data()
        
        if len(training_data) < 100:
            logger.warning(f"Insufficient training data: {len(training_data)} samples")
            return {}
        
        # Group by platform
        platforms_data = defaultdict(list)
        for sample in training_data:
            platforms_data[sample['platform']].append(sample)
        
        model_scores = {}
        
        for platform, samples in platforms_data.items():
            if len(samples) < 50:  # Minimum samples per platform
                continue
            
            # Prepare features and labels
            features = []
            labels = []
            
            for sample in samples:
                feature_vector = self._extract_features(sample)
                features.append(feature_vector)
                labels.append(sample['success_rate'])  # Target: success rate
            
            if len(features) < 20:
                continue
            
            # Convert to numpy arrays
            X = np.array(features)
            y = np.array(labels)
            
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train Random Forest model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            scaler = StandardScaler()
            
            # Scale features
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            
            # Store model and scaler
            self._ml_models[platform] = model
            self._scalers[platform] = scaler
            
            model_scores[platform] = {
                'train_r2': train_score,
                'test_r2': test_score
            }
            
            logger.info(f"Trained {platform} model: R² = {test_score:.3f}")
        
        return model_scores
    
    def _collect_training_data(self) -> List[Dict]:
        """Collect training data from the performance history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT platform, content_type, posted_at, hour_of_day, day_of_week,
                       reach, impressions, engagement_rate, watch_time, 
                       completion_rate, ctr, saves, shares, comments, success
                FROM performance_history
                ORDER BY posted_at DESC
                LIMIT 1000
            ''')
            
            samples = []
            for row in cursor.fetchall():
                (platform, content_type, posted_at, hour_of_week, day_of_week,
                 reach, impressions, engagement_rate, watch_time, completion_rate,
                 ctr, saves, shares, comments, success) = row
                
                # Calculate success rate (composite score)
                success_rate = self._calculate_success_rate({
                    'reach': reach,
                    'engagement_rate': engagement_rate,
                    'watch_time': watch_time,
                    'completion_rate': completion_rate,
                    'ctr': ctr
                })
                
                samples.append({
                    'platform': platform,
                    'content_type': content_type,
                    'posted_at': posted_at,
                    'hour_of_week': hour_of_week,
                    'day_of_week': day_of_week,
                    'success_rate': success_rate,
                    'raw_metrics': {
                        'reach': reach,
                        'engagement_rate': engagement_rate,
                        'watch_time': watch_time,
                        'completion_rate': completion_rate,
                        'ctr': ctr
                    }
                })
            
            return samples
    
    def _calculate_success_rate(self, metrics: Dict) -> float:
        """Calculate a composite success rate from metrics."""
        score = 0.0
        weights = 0.0
        
        # Normalize and weight different metrics based on platform
        if metrics.get('engagement_rate'):
            score += metrics['engagement_rate'] * 0.3
            weights += 0.3
        
        if metrics.get('watch_time'):
            # Normalize watch time (assume max 300 seconds for normalization)
            norm_watch_time = min(metrics['watch_time'] / 300, 1.0)
            score += norm_watch_time * 0.25
            weights += 0.25
        
        if metrics.get('completion_rate'):
            score += metrics['completion_rate'] * 0.25
            weights += 0.25
        
        if metrics.get('ctr'):
            score += metrics['ctr'] * 0.2
            weights += 0.2
        
        return score / weights if weights > 0 else 0.5
    
    def _extract_features(self, sample: Dict) -> List[float]:
        """Extract feature vector from a training sample."""
        # Time-based features
        hour = sample['hour_of_week'] % 24
        day_of_week = sample['day_of_week']
        
        # Cyclical encoding for time features
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        day_sin = math.sin(2 * math.pi * day_of_week / 7)
        day_cos = math.cos(2 * math.pi * day_of_week / 7)
        
        # Platform encoding (simple one-hot)
        platform_encodings = self._encode_platform(sample['platform'])
        
        # Content type encoding
        content_type_encodings = self._encode_content_type(sample['content_type'])
        
        # Combine all features
        features = [
            hour_sin, hour_cos, day_sin, day_cos,
            hour / 24.0, day_of_week / 7.0,
            sample['hour_of_week'] / 168.0  # Hour of week normalized
        ] + platform_encodings + content_type_encodings
        
        return features
    
    def _encode_platform(self, platform: str) -> List[float]:
        """One-hot encode platform."""
        platforms = ['youtube', 'tiktok', 'instagram', 'twitter', 'linkedin', 'facebook']
        encoding = [0.0] * len(platforms)
        if platform in platforms:
            encoding[platforms.index(platform)] = 1.0
        return encoding
    
    def _encode_content_type(self, content_type: str) -> List[float]:
        """One-hot encode content type."""
        content_types = ['youtube_long_form', 'youtube_shorts', 'tiktok_video',
                        'instagram_feed', 'instagram_reels', 'instagram_stories',
                        'twitter_post', 'twitter_thread', 'linkedin_post',
                        'linkedin_carousel', 'facebook_post', 'facebook_reels']
        encoding = [0.0] * len(content_types)
        if content_type in content_types:
            encoding[content_types.index(content_type)] = 1.0
        return encoding
    
    def predict_optimal_times(self, 
                             platform: Platform,
                             content_type: ContentType,
                             audience_profile: AudienceProfile,
                             num_predictions: int = 5) -> List[Dict]:
        """
        Use trained ML models to predict optimal posting times.
        
        Args:
            platform: Target platform
            content_type: Content format
            audience_profile: Audience demographics
            num_predictions: Number of top predictions to return
            
        Returns:
            List of optimal time predictions with confidence scores
        """
        if platform not in self._ml_models:
            logger.warning(f"No trained model for {platform}, falling back to rule-based scores")
            return self._rule_based_predictions(platform, content_type, audience_profile, num_predictions)
        
        model = self._ml_models[platform]
        scaler = self._scalers[platform]
        
        predictions = []
        
        # Generate predictions for next 7 days
        start_date = datetime.now()
        for day_offset in range(7):
            target_date = start_date + timedelta(days=day_offset)
            day_of_week = target_date.weekday()
            
            # Generate hourly predictions for this day
            for hour in range(24):
                # Create feature vector
                sample = {
                    'platform': platform.value,
                    'content_type': content_type.value,
                    'hour_of_week': day_offset * 24 + hour,
                    'day_of_week': day_of_week
                }
                
                features = self._extract_features(sample)
                features_array = np.array(features).reshape(1, -1)
                
                # Scale features
                features_scaled = scaler.transform(features_array)
                
                # Predict success rate
                predicted_score = model.predict(features_scaled)[0]
                
                predictions.append({
                    'datetime': target_date.replace(hour=hour, minute=0, second=0, microsecond=0),
                    'predicted_score': max(0.0, min(1.0, predicted_score)),
                    'day_of_week': day_of_week,
                    'hour': hour,
                    'method': 'ml_prediction'
                })
        
        # Sort by predicted score and return top predictions
        predictions.sort(key=lambda x: x['predicted_score'], reverse=True)
        return predictions[:num_predictions]
    
    def _rule_based_predictions(self, platform: Platform, content_type: ContentType, 
                               audience_profile: AudienceProfile, num_predictions: int) -> List[Dict]:
        """Fallback rule-based predictions when ML models are not available."""
        predictions = []
        start_date = datetime.now()
        
        for day_offset in range(7):
            target_date = start_date + timedelta(days=day_offset)
            day_of_week = target_date.weekday()
            
            # Get timing scores for this day
            scores = self.calculate_timing_scores(platform, content_type, audience_profile, day_of_week)
            
            # Convert to predictions
            for hour, score in scores.items():
                predictions.append({
                    'datetime': target_date.replace(hour=hour, minute=0, second=0, microsecond=0),
                    'predicted_score': score,
                    'day_of_week': day_of_week,
                    'hour': hour,
                    'method': 'rule_based'
                })
        
        # Sort and return top predictions
        predictions.sort(key=lambda x: x['predicted_score'], reverse=True)
        return predictions[:num_predictions]
    
    async def adaptive_optimization_cycle(self) -> Dict[str, Any]:
        """
        Perform the adaptive optimization cycle:
        1. Measure performance metrics
        2. Analyze trends and thresholds
        3. Adjust parameters
        4. Validate improvements
        
        Returns:
            Dict with cycle results and recommendations
        """
        logger.info("Starting adaptive optimization cycle...")
        
        cycle_results = {
            'started_at': datetime.now().isoformat(),
            'measurements': {},
            'analysis': {},
            'adjustments': {},
            'validation': {}
        }
        
        # Step 1: Measure current performance
        measurements = self._measure_performance_metrics()
        cycle_results['measurements'] = measurements
        
        # Step 2: Analyze trends and detect issues
        analysis = self._analyze_performance_trends(measurements)
        cycle_results['analysis'] = analysis
        
        # Step 3: Adjust parameters based on analysis
        if analysis.get('needs_adjustment', False):
            adjustments = self._adjust_parameters(analysis)
            cycle_results['adjustments'] = adjustments
        else:
            cycle_results['adjustments'] = {'status': 'no_adjustment_needed'}
        
        # Step 4: Validate improvements (placeholder for next cycle)
        validation = {'status': 'pending_next_cycle'}
        cycle_results['validation'] = validation
        
        cycle_results['completed_at'] = datetime.now().isoformat()
        
        # Store cycle results
        await self._store_optimization_cycle_results(cycle_results)
        
        return cycle_results
    
    def _measure_performance_metrics(self) -> Dict[str, Any]:
        """Measure current performance metrics."""
        metrics = {}
        
        # Calculate throughput metrics
        metrics['throughput'] = self._calculate_current_throughput()
        
        # Calculate 429 rate (rate limit errors)
        metrics['rate_limit_errors'] = self._calculate_rate_limit_errors()
        
        # Calculate job start latency
        metrics['job_start_latency'] = self._calculate_job_start_latency()
        
        # Calculate schedule adherence
        metrics['schedule_adherence'] = self._calculate_current_schedule_adherence()
        
        # Calculate queue depth and starvation risk
        metrics['queue_depth'] = self._calculate_queue_depth()
        
        return metrics
    
    def _calculate_current_throughput(self) -> Dict[str, float]:
        """Calculate current throughput metrics."""
        # Get recent job completion data
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as completed_jobs,
                       MIN(posted_at) as first_job,
                       MAX(posted_at) as last_job
                FROM performance_history
                WHERE posted_at >= ?
            ''', (cutoff_time,))
            
            result = cursor.fetchone()
            if result and result[1] and result[2]:
                completed_jobs = result[0]
                time_span = (result[2] - result[1]).total_seconds() / 3600  # hours
                throughput = completed_jobs / max(time_span, 1)
                
                return {
                    'jobs_per_hour': throughput,
                    'completed_jobs_24h': completed_jobs,
                    'time_span_hours': time_span
                }
        
        return {'jobs_per_hour': 0.0, 'completed_jobs_24h': 0, 'time_span_hours': 0}
    
    def _calculate_rate_limit_errors(self) -> Dict[str, float]:
        """Calculate rate limit error rates."""
        # This would integrate with actual error tracking
        # For now, return placeholder metrics
        return {
            '429_rate_percent': 0.0,
            'rate_limit_events_24h': 0
        }
    
    def _calculate_job_start_latency(self) -> Dict[str, float]:
        """Calculate job start latency statistics."""
        # Placeholder for job start latency calculation
        return {
            'p50_latency_minutes': 5.0,
            'p95_latency_minutes': 15.0,
            'average_latency_minutes': 7.5
        }
    
    def _calculate_current_schedule_adherence(self) -> float:
        """Calculate current schedule adherence percentage."""
        # Placeholder for schedule adherence calculation
        return 0.95  # 95% adherence
    
    def _calculate_queue_depth(self) -> Dict[str, int]:
        """Calculate queue depth and starvation risk."""
        # Placeholder for queue depth calculation
        return {
            'total_queued': 0,
            'urgent_jobs': 0,
            'normal_jobs': 0,
            'low_jobs': 0,
            'starvation_risk': 0.0
        }
    
    def _analyze_performance_trends(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends and detect if adjustments are needed."""
        analysis = {
            'throughput_status': 'normal',
            'rate_limit_status': 'normal',
            'latency_status': 'normal',
            'adherence_status': 'good',
            'needs_adjustment': False,
            'recommendations': []
        }
        
        # Analyze throughput
        throughput = measurements.get('throughput', {})
        jobs_per_hour = throughput.get('jobs_per_hour', 0)
        
        if jobs_per_hour < 0.5:  # Very low throughput
            analysis['throughput_status'] = 'low'
            analysis['needs_adjustment'] = True
            analysis['recommendations'].append('Increase concurrency or optimize scheduling')
        
        # Analyze rate limiting
        rate_limit = measurements.get('rate_limit_errors', {})
        error_rate = rate_limit.get('429_rate_percent', 0)
        
        if error_rate > 5.0:  # High error rate
            analysis['rate_limit_status'] = 'high'
            analysis['needs_adjustment'] = True
            analysis['recommendations'].append('Reduce concurrency and improve backoff strategy')
        elif error_rate > 2.0:  # Moderate error rate
            analysis['rate_limit_status'] = 'moderate'
            analysis['recommendations'].append('Monitor rate limiting closely')
        
        # Analyze latency
        latency = measurements.get('job_start_latency', {})
        p95_latency = latency.get('p95_latency_minutes', 0)
        
        if p95_latency > 30.0:  # High latency
            analysis['latency_status'] = 'high'
            analysis['needs_adjustment'] = True
            analysis['recommendations'].append('Optimize scheduling algorithms and queue management')
        
        # Analyze schedule adherence
        adherence = measurements.get('schedule_adherence', 0)
        if adherence < 0.9:  # Poor adherence
            analysis['adherence_status'] = 'poor'
            analysis['needs_adjustment'] = True
            analysis['recommendations'].append('Review constraint definitions and schedule generation')
        
        return analysis
    
    def _adjust_parameters(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust system parameters based on analysis results."""
        adjustments = {
            'effective_priority_weights': {},
            'rate_limit_params': {},
            'concurrency_settings': {},
            'smoothing_params': {}
        }
        
        # Adjust effective priority weights if throughput is low
        if analysis['throughput_status'] == 'low':
            adjustments['effective_priority_weights'] = {
                'urgent_boost': 1.1,
                'normal_aging_threshold_minutes': 10,  # Faster aging
                'low_escalation_hours': 1.5  # Faster escalation
            }
        
        # Adjust rate limiting if 429 rate is high
        if analysis['rate_limit_status'] in ['high', 'moderate']:
            adjustments['rate_limit_params'] = {
                'initial_backoff_seconds': 2.0,  # Longer initial backoff
                'backoff_multiplier': 2.5,  # Faster backoff growth
                'max_backoff_seconds': 120.0,  # Longer max backoff
                'token_bucket_capacity': 0.8  # Reduce capacity by 20%
            }
        
        # Adjust concurrency settings
        if analysis['latency_status'] == 'high':
            adjustments['concurrency_settings'] = {
                'max_concurrent_posts': 2,  # Reduce max concurrency
                'worker_count': 0.8  # Reduce worker count
            }
        
        # Apply adjustments (in a real implementation, these would update actual parameters)
        logger.info(f"Applying adjustments: {adjustments}")
        
        return adjustments
    
    async def _store_optimization_cycle_results(self, results: Dict[str, Any]):
        """Store optimization cycle results for tracking and analysis."""
        # In a real implementation, this would store results in a database
        logger.info(f"Optimization cycle completed: {results['started_at']}")
    
    def integrate_with_batch_system(self, 
                                   bulk_job_id: str,
                                   posts: List[Dict],
                                   scheduling_metadata: Optional[Dict] = None) -> SchedulePlan:
        """
        Integrate with the batch processing system for schedule generation and execution.
        
        This method generates schedules that respect batch system constraints and integrate
        with the existing queue and rate limiting infrastructure.
        
        Args:
            bulk_job_id: ID of the bulk job
            posts: List of posts to schedule
            scheduling_metadata: Optional scheduling constraints and preferences
            
        Returns:
            SchedulePlan integrated with batch system
        """
        logger.info(f"Integrating schedule for bulk job {bulk_job_id}")
        
        # Extract scheduling metadata or use defaults
        metadata = scheduling_metadata or {}
        start_after = datetime.fromisoformat(metadata.get('start_after', datetime.now().isoformat()))
        deadline = datetime.fromisoformat(metadata.get('deadline', (datetime.now() + timedelta(days=7)).isoformat()))
        suggested_concurrency = metadata.get('suggested_concurrency', 3)
        ai_provider_prefs = metadata.get('ai_provider_prefs', [])
        
        # Create scheduling constraints
        constraints = []
        for post in posts:
            platform = Platform(post['platform'])
            constraint = SchedulingConstraint(
                platform=platform,
                min_gap_hours=self._get_min_gap_hours(platform, ContentType(post['content_type'])),
                max_concurrent_posts=metadata.get('max_parallelism', 3)
            )
            constraints.append(constraint)
        
        # Create audience profiles (placeholder - would come from actual data)
        audience_profiles = {}
        for post in posts:
            platform = Platform(post['platform'])
            if platform not in audience_profiles:
                audience_profiles[platform] = AudienceProfile(
                    age_cohorts={'25-34': 0.4, '35-44': 0.3, '18-24': 0.3},
                    device_split={'mobile': 0.7, 'desktop': 0.3},
                    time_zone_weights={'UTC-5': 0.4, 'UTC-8': 0.3, 'UTC+0': 0.3}
                )
        
        # Generate optimal schedule
        schedule_plan = self.generate_optimal_schedule(
            posts=posts,
            constraints=constraints,
            audience_profiles=audience_profiles,
            start_date=start_after,
            end_date=deadline,
            max_concurrent=suggested_concurrency
        )
        
        # Attach bulk job ID
        schedule_plan.bulk_job_id = bulk_job_id
        
        # Store schedule plan in database
        self._store_schedule_plan(schedule_plan)
        
        logger.info(f"Generated schedule {schedule_plan.schedule_id} for bulk job {bulk_job_id}")
        
        return schedule_plan
    
    def _store_schedule_plan(self, plan: SchedulePlan):
        """Store schedule plan in database for tracking and integration."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO schedule_plans
                (schedule_id, created_at, bulk_job_id, plan_data, 
                 projected_throughput, quota_compliance_score, schedule_adherence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan.schedule_id,
                plan.created_at,
                plan.bulk_job_id,
                json.dumps([asdict(assignment) for assignment in plan.job_assignments]),
                plan.projected_throughput,
                plan.quota_compliance_score,
                plan.schedule_adherence_score
            ))
            conn.commit()
    
    def record_performance_metrics(self, metrics: PerformanceMetrics):
        """
        Record performance metrics for a posted piece of content.
        This data is used for adaptive optimization and ML training.
        
        Args:
            metrics: Performance metrics for the posted content
        """
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO performance_history
                (platform, content_type, posted_at, hour_of_day, day_of_week,
                 reach, impressions, engagement_rate, watch_time, 
                 completion_rate, ctr, saves, shares, comments, success, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.platform.value,
                metrics.content_type.value,
                metrics.posted_at,
                metrics.posted_at.hour,
                metrics.posted_at.weekday(),
                metrics.reach,
                metrics.impressions,
                metrics.engagement_rate,
                metrics.watch_time,
                metrics.completion_rate,
                metrics.ctr,
                metrics.saves,
                metrics.shares,
                metrics.comments,
                metrics.is_successful,
                json.dumps({k: v for k, v in asdict(metrics).items() 
                           if k not in ['platform', 'content_type', 'posted_at', 'is_successful']})
            ))
            conn.commit()
        
        # Update adaptive parameters
        self._update_adaptive_parameters(metrics)
        
        logger.info(f"Recorded performance metrics for {metrics.platform.value} post at {metrics.posted_at}")
    
    def _update_adaptive_parameters(self, metrics: PerformanceMetrics):
        """Update adaptive parameters based on performance results."""
        platform = metrics.platform
        content_type = metrics.content_type
        day_of_week = metrics.posted_at.weekday()
        hour_of_day = metrics.posted_at.hour
        
        # Get current posterior parameters
        key = (platform.value, content_type.value, day_of_week, hour_of_day)
        alpha, beta = self._posterior_params[key]
        
        # Update based on success/failure
        if metrics.is_successful:
            alpha += 1
        else:
            beta += 1
        
        self._posterior_params[key] = (alpha, beta)
        
        # Calculate posterior mean
        posterior_mean = alpha / (alpha + beta)
        
        # Update daypart weights with exponential smoothing
        current_weight = self._daypart_weights[platform][day_of_week][hour_of_day]
        smoothed_weight = 0.8 * current_weight + 0.2 * posterior_mean
        self._daypart_weights[platform][day_of_week][hour_of_day] = smoothed_weight
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO adaptive_params
                (platform, content_type, day_of_week, hour_of_day, weight, 
                 posterior_alpha, posterior_beta, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                platform.value, content_type.value, day_of_week, hour_of_day,
                smoothed_weight, alpha, beta, datetime.now()
            ))
            conn.commit()
    
    def get_schedule_recommendations(self, platform: Platform) -> Dict[str, Any]:
        """
        Get scheduling recommendations for a specific platform based on current data.
        
        Args:
            platform: Target platform
            
        Returns:
            Dict with recommendations including best times, constraints, and insights
        """
        # Get performance history for platform
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT day_of_week, hour_of_day, AVG(success) as success_rate,
                       COUNT(*) as sample_count
                FROM performance_history
                WHERE platform = ? AND sample_count >= 5
                GROUP BY day_of_week, hour_of_day
                ORDER BY success_rate DESC, sample_count DESC
                LIMIT 20
            ''', (platform.value,))
            
            top_slots = []
            for row in cursor.fetchall():
                day_of_week, hour_of_day, success_rate, sample_count = row
                top_slots.append({
                    'day_of_week': day_of_week,
                    'hour_of_day': hour_of_day,
                    'success_rate': success_rate,
                    'sample_count': sample_count,
                    'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week],
                    'time_str': f"{hour_of_day:02d}:00"
                })
        
        # Get constraint recommendations
        constraint_recs = self._get_constraint_recommendations(platform)
        
        # Get ML insights if available
        ml_insights = self._get_ml_insights(platform)
        
        return {
            'platform': platform.value,
            'top_posting_slots': top_slots,
            'constraint_recommendations': constraint_recs,
            'ml_insights': ml_insights,
            'recommendations': self._generate_platform_recommendations(platform, top_slots)
        }
    
    def _get_constraint_recommendations(self, platform: Platform) -> Dict[str, Any]:
        """Get constraint recommendations for a platform."""
        # Platform-specific constraints based on evidence synthesis
        constraints = {
            Platform.YOUTUBE: {
                'min_gap_hours': 24.0 if platform == Platform.YOUTUBE else 12.0,
                'max_concurrent_posts': 3,
                'preferred_content_types': ['youtube_long_form', 'youtube_shorts'],
                'frequency_recommendations': {
                    'small_channels': '1/day Shorts, 2-3/week long-form',
                    'medium_channels': '3-5/week Shorts, 2-3/week long-form',
                    'large_channels': '3-5/week Shorts, 1-3/week long-form'
                }
            },
            Platform.TIKTOK: {
                'min_gap_hours': 12.0,
                'max_concurrent_posts': 3,
                'preferred_content_types': ['tiktok_video'],
                'frequency_recommendations': {
                    'emerging': '1-4/day',
                    'established': '2-5/week',
                    'brands': '4/week'
                }
            },
            Platform.INSTAGRAM: {
                'min_gap_hours': 18.0,
                'max_concurrent_posts': 3,
                'preferred_content_types': ['instagram_feed', 'instagram_reels'],
                'frequency_recommendations': {
                    'nano': '5-7 feed posts/week, 1-2 Reels/week',
                    'micro': '4-5 feed posts/week, 1-2 Reels/week',
                    'large': '2-3 feed posts/week, 2 Reels/week'
                }
            },
            Platform.LINKEDIN: {
                'min_gap_hours': 24.0,
                'max_concurrent_posts': 2,
                'preferred_content_types': ['linkedin_post', 'linkedin_carousel'],
                'frequency_recommendations': {
                    'individuals': '2-3 posts/week',
                    'companies': '3-5 posts/week'
                }
            }
        }
        
        return constraints.get(platform, {
            'min_gap_hours': 12.0,
            'max_concurrent_posts': 3,
            'frequency_recommendations': 'Follow platform-specific best practices'
        })
    
    def _get_ml_insights(self, platform: Platform) -> Dict[str, Any]:
        """Get ML model insights for a platform."""
        if platform not in self._ml_models:
            return {'status': 'no_model_trained', 'message': 'Train ML models first for insights'}
        
        model = self._ml_models[platform]
        
        # Get feature importance
        feature_names = [
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'hour_norm', 'day_norm', 'hour_week_norm',
            'youtube', 'tiktok', 'instagram', 'twitter', 'linkedin', 'facebook',
            'yt_long', 'yt_shorts', 'tt_video', 'ig_feed', 'ig_reels', 'ig_stories',
            'tw_post', 'tw_thread', 'li_post', 'li_carousel', 'fb_post', 'fb_reels'
        ]
        
        importances = model.feature_importances_
        
        # Top features
        feature_importance = list(zip(feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'model_trained': True,
            'feature_importance': feature_importance[:10],  # Top 10 features
            'model_score': getattr(model, 'score', None),
            'training_samples': len(getattr(model, 'estimators_', [])) * 100  # Approximate
        }
    
    def _generate_platform_recommendations(self, platform: Platform, top_slots: List[Dict]) -> List[str]:
        """Generate specific recommendations for a platform."""
        recommendations = []
        
        if not top_slots:
            recommendations.append("Collect more performance data to generate recommendations")
            return recommendations
        
        # Analyze top slots
        best_days = [slot['day_name'] for slot in top_slots[:3]]
        best_hours = [slot['time_str'] for slot in top_slots[:3]]
        
        recommendations.append(f"Post during peak times: {', '.join(best_hours)} on {', '.join(best_days)}")
        
        # Platform-specific recommendations
        if platform == Platform.YOUTUBE:
            recommendations.append("Focus on weekday afternoons, especially Wednesday 4 PM")
            recommendations.append("Use Shorts for more frequent posting, long-form for quality content")
        
        elif platform == Platform.TIKTOK:
            recommendations.append("Wednesday evenings are strongest, avoid Saturday posting")
            recommendations.append("Maintain consistent daily posting for emerging accounts")
        
        elif platform == Platform.INSTAGRAM:
            recommendations.append("Weekday mid-mornings to afternoons work best for Feed posts")
            recommendations.append("Reels perform well in bookend hours (6-9 AM, 6-9 PM)")
        
        elif platform == Platform.LINKEDIN:
            recommendations.append("Business hours (8-11 AM, 12-2 PM) on Tuesday-Thursday")
            recommendations.append("Maintain 12-24 hour spacing between posts")
        
        elif platform == Platform.TWITTER:
            recommendations.append("Morning posting (8 AM-12 PM) Tuesday-Thursday")
            recommendations.append("Weekend posting underperforms significantly")
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Initialize optimizer
        optimizer = SchedulingOptimizer()
        
        # Example audience profile
        audience = AudienceProfile(
            age_cohorts={'18-24': 0.3, '25-34': 0.4, '35-44': 0.3},
            device_split={'mobile': 0.7, 'desktop': 0.3},
            time_zone_weights={'UTC-5': 0.5, 'UTC-8': 0.3, 'UTC+0': 0.2}
        )
        
        # Calculate timing scores for Instagram Reels
        print("=== Instagram Reels Timing Scores ===")
        scores = optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=audience,
            day_of_week=2  # Wednesday
        )
        
        # Show top 5 hours
        top_hours = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for hour, score in top_hours:
            print(f"Hour {hour:02d}: {score:.3f}")
        
        # Generate optimal schedule
        print("\n=== Generating Optimal Schedule ===")
        posts = [
            {
                'id': 'post_1',
                'platform': 'instagram',
                'content_type': 'instagram_reels',
                'priority': PriorityTier.NORMAL.value,
                'title': 'Product Demo Reel'
            },
            {
                'id': 'post_2',
                'platform': 'tiktok',
                'content_type': 'tiktok_video',
                'priority': PriorityTier.URGENT.value,
                'title': 'Behind the Scenes'
            },
            {
                'id': 'post_3',
                'platform': 'youtube',
                'content_type': 'youtube_long_form',
                'priority': PriorityTier.NORMAL.value,
                'title': 'Tutorial Video'
            }
        ]
        
        constraints = [
            SchedulingConstraint(Platform.INSTAGRAM, min_gap_hours=18.0, max_concurrent_posts=3),
            SchedulingConstraint(Platform.TIKTOK, min_gap_hours=12.0, max_concurrent_posts=3),
            SchedulingConstraint(Platform.YOUTUBE, min_gap_hours=48.0, max_concurrent_posts=2)
        ]
        
        audience_profiles = {
            Platform.INSTAGRAM: audience,
            Platform.TIKTOK: audience,
            Platform.YOUTUBE: audience
        }
        
        schedule = optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=constraints,
            audience_profiles=audience_profiles,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            max_concurrent=3
        )
        
        print(f"Generated schedule: {schedule.schedule_id}")
        for assignment in schedule.job_assignments:
            print(f"  {assignment['platform']} - {assignment['content_type']} at {assignment['scheduled_time']}")
        
        # Get recommendations
        print("\n=== Platform Recommendations ===")
        recs = optimizer.get_schedule_recommendations(Platform.INSTAGRAM)
        print(json.dumps(recs, indent=2, default=str))
        
        # Train ML models (would need actual training data)
        print("\n=== ML Training (Simulated) ===")
        # Note: In real usage, you'd have performance history data
        model_scores = await optimizer.train_ml_models()
        print(f"ML model scores: {model_scores}")
    
    # Run the example
    import asyncio
    asyncio.run(main())