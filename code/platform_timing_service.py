"""
Platform Timing Service for Scheduling Optimization

This service provides comprehensive platform timing optimization capabilities including:
- Loading and storing platform timing data from research
- Database operations for timing recommendations
- Platform-specific optimization logic (YouTube, TikTok, Instagram, Twitter/X, LinkedIn, Facebook)
- Integration with Supabase for data persistence
- API client for scheduling recommendations

Author: Scheduling Optimization System
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import pytz

import asyncpg
import aiohttp
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PlatformTimingData:
    """Platform timing data structure based on research findings"""
    platform_id: str
    days: List[str]
    peak_hours: List[Dict[str, int]]
    posting_frequency_min: int
    posting_frequency_max: int
    audience_segment: Optional[str] = None
    content_format: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    timezone: Optional[str] = None


@dataclass
class UserSchedulingPreferences:
    """User scheduling preferences and settings"""
    user_id: str
    platform_id: Optional[str] = None
    timezone: str = "UTC"
    posting_frequency_min: Optional[int] = None
    posting_frequency_max: Optional[int] = None
    days_blacklist: Optional[List[str]] = None
    hours_blacklist: Optional[List[Dict[str, int]]] = None
    content_format: Optional[str] = None
    quality_threshold: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ScheduleRecommendation:
    """Scheduling recommendation output"""
    recommended_slots: List[Dict[str, Any]]
    confidence_score: float
    reasoning: List[str]
    alternatives: Optional[List[Dict[str, Any]]] = None


class PlatformTimingService:
    """
    Main service class for platform timing optimization
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize the platform timing service
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.platform_research_path = Path("/workspace/docs/platform_research")
        
        # Platform-specific timing data from research
        self.platform_timing_bases = self._load_platform_timing_bases()
    
    def _load_platform_timing_bases(self) -> Dict[str, Dict]:
        """Load base timing data from research files"""
        return {
            "youtube": {
                "days": ["mon", "tue", "wed", "thu", "fri"],
                "peak_hours": [{"start": 15, "end": 17}, {"start": 20, "end": 21}],
                "posting_frequency_min": 2,
                "posting_frequency_max": 3,
                "content_formats": {
                    "long_form": {"frequency_min": 2, "frequency_max": 3, "peak_hours": [{"start": 15, "end": 17}]},
                    "shorts": {"frequency_min": 1, "frequency_max": 1, "peak_hours": [{"start": 15, "end": 17}]}
                },
                "audience_segments": {
                    "us_east": {"peak_hours": [{"start": 14, "end": 21}]},
                    "india": {"peak_hours": [{"start": 18, "end": 22}]},
                    "philippines": {"peak_hours": [{"start": 8, "end": 18}]}
                },
                "source": "Buffer 2025; SocialPilot 2025",
                "notes": "Wednesday 4 p.m. is the highest-performing slot; weekends work later morning to mid-afternoon"
            },
            "tiktok": {
                "days": ["tue", "wed", "thu", "fri"],
                "peak_hours": [{"start": 16, "end": 18}, {"start": 20, "end": 21}],
                "posting_frequency_min": 2,
                "posting_frequency_max": 5,
                "content_formats": {
                    "emerging": {"frequency_min": 1, "frequency_max": 4},
                    "established": {"frequency_min": 2, "frequency_max": 5},
                    "brands": {"frequency_min": 3, "frequency_max": 5}
                },
                "audience_segments": {
                    "general": {"best_day": "wednesday", "peak_hours": [{"start": 17, "end": 18}]},
                    "weekend": {"best_day": "sunday", "peak_hours": [{"start": 20, "end": 21}]}
                },
                "source": "Buffer 2025; 1M+ posts analysis",
                "notes": "Wednesday is best day; Sunday 8 p.m. is notable peak; Saturday is weakest day"
            },
            "instagram": {
                "days": ["mon", "tue", "wed", "thu", "fri"],
                "peak_hours": [{"start": 10, "end": 15}, {"start": 18, "end": 21}],
                "posting_frequency_min": 3,
                "posting_frequency_max": 5,
                "content_formats": {
                    "feed": {"frequency_min": 3, "frequency_max": 5, "peak_hours": [{"start": 10, "end": 15}]},
                    "reels": {"frequency_min": 3, "frequency_max": 5, "peak_hours": [{"start": 9, "end": 12}, {"start": 18, "end": 21}]},
                    "stories": {"frequency_min": 1, "frequency_max": 3, "peak_hours": [{"start": 9, "end": 11}, {"start": 18, "end": 20}]}
                },
                "audience_segments": {
                    "working_professionals": {"peak_hours": [{"start": 7, "end": 9}, {"start": 12, "end": 13}, {"start": 18, "end": 20}]},
                    "gen_z": {"peak_hours": [{"start": 19, "end": 22}]}
                },
                "source": "Sprout Social 2025; Buffer 2025; 2.1M posts analysis",
                "notes": "Weekdays 10 a.m.-3 p.m. safest window; Reels peak mid-morning to early afternoon"
            },
            "twitter": {
                "days": ["tue", "wed", "thu"],
                "peak_hours": [{"start": 8, "end": 12}],
                "posting_frequency_min": 3,
                "posting_frequency_max": 5,
                "content_formats": {
                    "brands": {"frequency_min": 3, "frequency_max": 5},
                    "threads": {"frequency_min": 1, "frequency_max": 3}
                },
                "audience_segments": {
                    "business": {"peak_hours": [{"start": 8, "end": 12}]},
                    "general": {"peak_hours": [{"start": 9, "end": 11}, {"start": 13, "end": 15}]}
                },
                "source": "Buffer 2025; Sprout Social 2025",
                "notes": "Weekday mornings (8-12 p.m.) show consistent engagement; Tuesday-Thursday strongest"
            },
            "linkedin": {
                "days": ["tue", "wed", "thu"],
                "peak_hours": [{"start": 8, "end": 14}],
                "posting_frequency_min": 2,
                "posting_frequency_max": 3,
                "content_formats": {
                    "individuals": {"frequency_min": 2, "frequency_max": 3},
                    "company_pages": {"frequency_min": 3, "frequency_max": 5}
                },
                "audience_segments": {
                    "business_hours": {"peak_hours": [{"start": 8, "end": 14}]},
                    "global": {"peak_hours": [{"start": 9, "end": 13}]}
                },
                "source": "Sprout Social 2025",
                "notes": "Midweek midday windows (8 a.m.-2 p.m.) are reliable; space posts 12-24 hours"
            },
            "facebook": {
                "days": ["mon", "tue", "wed", "thu", "fri"],
                "peak_hours": [{"start": 8, "end": 18}],
                "posting_frequency_min": 3,
                "posting_frequency_max": 5,
                "content_formats": {
                    "feed": {"frequency_min": 3, "frequency_max": 5},
                    "reels": {"frequency_min": 3, "frequency_max": 5}
                },
                "audience_segments": {
                    "general": {"peak_hours": [{"start": 8, "end": 18}]},
                    "lighter_fridays": {"peak_hours": [{"start": 8, "end": 16}]}
                },
                "source": "Sprout Social 2025",
                "notes": "Weekdays 8 a.m.-6 p.m.; lighter on Fridays; link posts underperform without native context"
            }
        }

    async def load_research_data_to_database(self) -> bool:
        """
        Load platform timing data from research into Supabase database
        
        Returns:
            bool: Success status
        """
        try:
            for platform_id, timing_data in self.platform_timing_bases.items():
                # Load base timing data
                platform_timing = PlatformTimingData(
                    platform_id=platform_id,
                    days=timing_data["days"],
                    peak_hours=timing_data["peak_hours"],
                    posting_frequency_min=timing_data["posting_frequency_min"],
                    posting_frequency_max=timing_data["posting_frequency_max"],
                    source=timing_data["source"],
                    notes=timing_data["notes"]
                )
                
                # Insert into database
                await self._insert_platform_timing_data(platform_timing)
                
                # Load content format specific data
                if "content_formats" in timing_data:
                    for format_type, format_data in timing_data["content_formats"].items():
                        format_timing = PlatformTimingData(
                            platform_id=platform_id,
                            days=timing_data["days"],
                            peak_hours=format_data.get("peak_hours", timing_data["peak_hours"]),
                            posting_frequency_min=format_data["frequency_min"],
                            posting_frequency_max=format_data["frequency_max"],
                            content_format=format_type,
                            source=timing_data["source"],
                            notes=f"Format-specific data for {format_type}"
                        )
                        await self._insert_platform_timing_data(format_timing)
                
                # Load audience segment specific data
                if "audience_segments" in timing_data:
                    for segment, segment_data in timing_data["audience_segments"].items():
                        segment_timing = PlatformTimingData(
                            platform_id=platform_id,
                            days=timing_data["days"],
                            peak_hours=segment_data.get("peak_hours", timing_data["peak_hours"]),
                            posting_frequency_min=timing_data["posting_frequency_min"],
                            posting_frequency_max=timing_data["posting_frequency_max"],
                            audience_segment=segment,
                            source=timing_data["source"],
                            notes=f"Segment-specific data for {segment}"
                        )
                        await self._insert_platform_timing_data(segment_timing)
            
            logger.info("Successfully loaded all platform timing data to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load research data to database: {e}")
            return False

    async def _insert_platform_timing_data(self, timing_data: PlatformTimingData) -> None:
        """Insert platform timing data into Supabase"""
        try:
            data = asdict(timing_data)
            
            # Handle datetime serialization
            if data.get("valid_from"):
                data["valid_from"] = data["valid_from"].isoformat()
            if data.get("valid_to"):
                data["valid_to"] = data["valid_to"].isoformat()
                
            # Insert data
            response = self.supabase.table("platform_timing_data").insert(data).execute()
            logger.debug(f"Inserted timing data for {timing_data.platform_id}")
            
        except Exception as e:
            logger.error(f"Failed to insert timing data for {timing_data.platform_id}: {e}")
            raise

    async def get_platform_timing_data(
        self, 
        platform_id: str, 
        content_format: Optional[str] = None,
        audience_segment: Optional[str] = None,
        valid_only: bool = True
    ) -> Optional[PlatformTimingData]:
        """
        Get platform timing data from database
        
        Args:
            platform_id: Platform identifier
            content_format: Content format filter
            audience_segment: Audience segment filter
            valid_only: Only return currently valid data
            
        Returns:
            PlatformTimingData or None
        """
        try:
            query = self.supabase.table("platform_timing_data").select("*").eq("platform_id", platform_id)
            
            if content_format:
                query = query.eq("content_format", content_format)
            
            if audience_segment:
                query = query.eq("audience_segment", audience_segment)
            
            if valid_only:
                query = query.is_("valid_to", "null")
            
            response = query.execute()
            
            if response.data:
                data = response.data[0]
                return self._dict_to_timing_data(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get timing data for {platform_id}: {e}")
            return None

    def _dict_to_timing_data(self, data: Dict) -> PlatformTimingData:
        """Convert database row to PlatformTimingData object"""
        return PlatformTimingData(
            platform_id=data["platform_id"],
            days=data["days"],
            peak_hours=data["peak_hours"],
            posting_frequency_min=data["posting_frequency_min"],
            posting_frequency_max=data["posting_frequency_max"],
            audience_segment=data.get("audience_segment"),
            content_format=data.get("content_format"),
            valid_from=datetime.fromisoformat(data["valid_from"].replace("Z", "+00:00")) if data.get("valid_from") else None,
            valid_to=datetime.fromisoformat(data["valid_to"].replace("Z", "+00:00")) if data.get("valid_to") else None,
            source=data.get("source"),
            notes=data.get("notes")
        )

    async def get_user_scheduling_preferences(
        self, 
        user_id: str, 
        platform_id: Optional[str] = None
    ) -> Optional[UserSchedulingPreferences]:
        """
        Get user scheduling preferences
        
        Args:
            user_id: User identifier
            platform_id: Platform identifier (optional for global preferences)
            
        Returns:
            UserSchedulingPreferences or None
        """
        try:
            query = self.supabase.table("user_scheduling_preferences").select("*").eq("user_id", user_id)
            
            if platform_id:
                query = query.eq("platform_id", platform_id)
            else:
                query = query.is_("platform_id", "null")
            
            response = query.execute()
            
            if response.data:
                data = response.data[0]
                return UserSchedulingPreferences(
                    user_id=data["user_id"],
                    platform_id=data.get("platform_id"),
                    timezone=data["timezone"],
                    posting_frequency_min=data.get("posting_frequency_min"),
                    posting_frequency_max=data.get("posting_frequency_max"),
                    days_blacklist=data.get("days_blacklist"),
                    hours_blacklist=data.get("hours_blacklist"),
                    content_format=data.get("content_format"),
                    quality_threshold=data.get("quality_threshold"),
                    metadata=data.get("metadata")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return None

    async def save_user_scheduling_preferences(
        self, 
        preferences: UserSchedulingPreferences
    ) -> bool:
        """
        Save user scheduling preferences
        
        Args:
            preferences: UserSchedulingPreferences object
            
        Returns:
            bool: Success status
        """
        try:
            data = asdict(preferences)
            
            # Upsert preferences
            response = self.supabase.table("user_scheduling_preferences").upsert(
                data,
                on="user_id,coalesce(platform_id,''),coalesce(content_format,'')"
            ).execute()
            
            logger.info(f"Saved scheduling preferences for user {preferences.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user preferences for {preferences.user_id}: {e}")
            return False

    def calculate_optimal_posting_slots(
        self,
        platform_id: str,
        user_preferences: UserSchedulingPreferences,
        content_format: str,
        audience_segment: str,
        start_date: datetime,
        end_date: datetime,
        timezone_str: str
    ) -> ScheduleRecommendation:
        """
        Calculate optimal posting slots based on platform data and user preferences
        
        Args:
            platform_id: Platform identifier
            user_preferences: User scheduling preferences
            content_format: Content format
            audience_segment: Target audience segment
            start_date: Start date for scheduling
            end_date: End date for scheduling
            timezone_str: Timezone for scheduling
            
        Returns:
            ScheduleRecommendation with recommended slots
        """
        try:
            # Get platform timing data
            timing_data = self.platform_timing_bases.get(platform_id, {})
            
            if not timing_data:
                raise ValueError(f"No timing data found for platform {platform_id}")
            
            # Get content format specific data
            format_data = timing_data.get("content_formats", {})
            content_timing = format_data.get(content_format, timing_data)
            
            # Get audience segment specific data
            segment_data = timing_data.get("audience_segments", {})
            audience_timing = segment_data.get(audience_segment, content_timing)
            
            # Apply user preferences
            preferred_timezone = pytz.timezone(user_preferences.timezone or timezone_str)
            schedule_timezone = pytz.timezone(timezone_str)
            
            # Calculate recommended slots
            recommended_slots = self._generate_schedule_slots(
                platform_id=platform_id,
                timing_data=audience_timing,
                user_preferences=user_preferences,
                start_date=start_date,
                end_date=end_date,
                preferred_timezone=preferred_timezone,
                schedule_timezone=schedule_timezone,
                content_format=content_format
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                timing_data, user_preferences, recommended_slots
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                platform_id, timing_data, user_preferences, content_format
            )
            
            return ScheduleRecommendation(
                recommended_slots=recommended_slots,
                confidence_score=confidence_score,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate optimal posting slots: {e}")
            return ScheduleRecommendation(
                recommended_slots=[],
                confidence_score=0.0,
                reasoning=[f"Error calculating slots: {e}"]
            )

    def _generate_schedule_slots(
        self,
        platform_id: str,
        timing_data: Dict,
        user_preferences: UserSchedulingPreferences,
        start_date: datetime,
        end_date: datetime,
        preferred_timezone: timezone,
        schedule_timezone: timezone,
        content_format: str
    ) -> List[Dict[str, Any]]:
        """Generate schedule slots based on timing data and preferences"""
        slots = []
        current_date = start_date
        
        # Get posting frequency from timing data
        freq_min = timing_data.get("posting_frequency_min", 2)
        freq_max = timing_data.get("posting_frequency_max", 5)
        
        # Apply user preferences if set
        if user_preferences.posting_frequency_min:
            freq_min = max(freq_min, user_preferences.posting_frequency_min)
        if user_preferences.posting_frequency_max:
            freq_max = min(freq_max, user_preferences.posting_frequency_max)
        
        # Generate slots for each week in range
        while current_date <= end_date:
            weekday = current_date.strftime("%a").lower()
            
            # Check if this day is in the platform's best days
            best_days = timing_data.get("days", ["mon", "tue", "wed", "thu", "fri"])
            
            if weekday in [day.lower() for day in best_days]:
                # Check if day is blacklisted
                if user_preferences.days_blacklist and weekday in user_preferences.days_blacklist:
                    current_date += timedelta(days=1)
                    continue
                
                # Get peak hours for this platform
                peak_hours = timing_data.get("peak_hours", [{"start": 12, "end": 14}])
                
                for hour_range in peak_hours:
                    # Check if hour is blacklisted
                    if user_preferences.hours_blacklist:
                        if self._is_hour_blacklisted(hour_range["start"], user_preferences.hours_blacklist):
                            continue
                    
                    # Create slot
                    slot_time = current_date.replace(
                        hour=hour_range["start"],
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                    
                    # Convert to user's preferred timezone
                    slot_time_utc = slot_time.astimezone(pytz.UTC)
                    
                    slot = {
                        "scheduled_at": slot_time_utc.isoformat(),
                        "platform_id": platform_id,
                        "content_format": content_format,
                        "timezone": user_preferences.timezone,
                        "confidence": self._calculate_slot_confidence(
                            platform_id, weekday, hour_range, timing_data
                        ),
                        "reasoning": f"Based on {platform_id} optimal timing: {weekday} at {hour_range['start']}:00-{hour_range['end']}:00"
                    }
                    
                    slots.append(slot)
            
            current_date += timedelta(days=1)
        
        # Sort by confidence and limit to frequency range
        slots.sort(key=lambda x: x["confidence"], reverse=True)
        slots = slots[:freq_max]
        
        return slots

    def _is_hour_blacklisted(self, hour: int, blacklisted_hours: List[Dict[str, int]]) -> bool:
        """Check if hour is in blacklisted ranges"""
        for blacklisted_range in blacklisted_hours:
            if blacklisted_range["start"] <= hour < blacklisted_range["end"]:
                return True
        return False

    def _calculate_slot_confidence(
        self, 
        platform_id: str, 
        weekday: str, 
        hour_range: Dict[str, int], 
        timing_data: Dict
    ) -> float:
        """Calculate confidence score for a specific slot"""
        confidence = 0.5  # Base confidence
        
        # Platform-specific confidence adjustments
        if platform_id == "youtube":
            if weekday == "wed" and hour_range["start"] == 16:
                confidence += 0.3  # Wednesday 4 p.m. is standout slot
            elif weekday in ["mon", "thu"] and hour_range["start"] == 16:
                confidence += 0.2  # Monday/Thursday 4 p.m. also strong
        elif platform_id == "tiktok":
            if weekday == "wed":
                confidence += 0.3  # Wednesday is best day
            elif weekday == "sun" and hour_range["start"] == 20:
                confidence += 0.2  # Sunday 8 p.m. peak
        elif platform_id == "instagram":
            if 10 <= hour_range["start"] <= 15:
                confidence += 0.2  # Weekday 10 a.m.-3 p.m. window
            if 18 <= hour_range["start"] <= 21:
                confidence += 0.1  # Evening slot
        
        return min(confidence, 1.0)

    def _calculate_confidence_score(
        self, 
        timing_data: Dict, 
        user_preferences: UserSchedulingPreferences, 
        slots: List[Dict]
    ) -> float:
        """Calculate overall confidence score for the recommendations"""
        base_confidence = 0.7  # Base confidence for platform data
        
        # Adjust based on user preference alignment
        if user_preferences.timezone:
            base_confidence += 0.1
        
        if not user_preferences.days_blacklist:
            base_confidence += 0.05
        
        # Adjust based on slot count alignment
        expected_slots = len(slots)
        optimal_slots = timing_data.get("posting_frequency_max", 5)
        
        if abs(expected_slots - optimal_slots) <= 1:
            base_confidence += 0.1
        elif expected_slots > optimal_slots * 1.5:
            base_confidence -= 0.1
        
        return min(max(base_confidence, 0.0), 1.0)

    def _generate_reasoning(
        self, 
        platform_id: str, 
        timing_data: Dict, 
        user_preferences: UserSchedulingPreferences, 
        content_format: str
    ) -> List[str]:
        """Generate reasoning for the schedule recommendations"""
        reasoning = [
            f"Based on {platform_id} timing research from {timing_data.get('source', '2025 data')}",
            f"Recommended days: {', '.join(timing_data.get('days', []))}",
            f"Peak hours: {timing_data.get('peak_hours', [])}"
        ]
        
        if content_format != "general":
            reasoning.append(f"Optimized for {content_format} content format")
        
        if user_preferences.timezone:
            reasoning.append(f"Adjusted for user's timezone: {user_preferences.timezone}")
        
        if user_preferences.days_blacklist:
            reasoning.append(f"Excluded blacklisted days: {', '.join(user_preferences.days_blacklist)}")
        
        if user_preferences.hours_blacklist:
            reasoning.append(f"Excluded blacklisted hours: {user_preferences.hours_blacklist}")
        
        # Add platform-specific notes
        if timing_data.get("notes"):
            reasoning.append(f"Platform insight: {timing_data['notes']}")
        
        return reasoning

    async def get_performance_kpis(
        self, 
        video_job_id: str,
        days_back: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Get performance KPIs for a video job
        
        Args:
            video_job_id: Video job identifier
            days_back: Number of days to look back
            
        Returns:
            KPI data or None
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            response = self.supabase.table("performance_kpi_events").select("*").eq(
                "video_job_id", video_job_id
            ).gte("event_time", cutoff_date.isoformat()).execute()
            
            if response.data:
                # Aggregate KPIs
                total_views = sum(event.get("views", 0) for event in response.data)
                total_impressions = sum(event.get("impressions", 0) for event in response.data)
                avg_engagement_rate = sum(
                    event.get("engagement_rate", 0) for event in response.data
                ) / len(response.data) if response.data else 0
                
                return {
                    "video_job_id": video_job_id,
                    "total_views": total_views,
                    "total_impressions": total_impressions,
                    "avg_engagement_rate": avg_engagement_rate,
                    "events_count": len(response.data),
                    "latest_event": max(
                        response.data, 
                        key=lambda x: x.get("event_time", "")
                    ) if response.data else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get performance KPIs for {video_job_id}: {e}")
            return None

    async def log_performance_kpi(
        self,
        video_job_id: str,
        platform_id: str,
        views: int,
        impressions: int,
        engagement_rate: float,
        event_time: Optional[datetime] = None,
        **kwargs
    ) -> bool:
        """
        Log performance KPI event
        
        Args:
            video_job_id: Video job identifier
            platform_id: Platform identifier
            views: View count
            impressions: Impression count
            engagement_rate: Engagement rate (0.0-1.0)
            event_time: Event timestamp (defaults to now)
            **kwargs: Additional KPI fields
            
        Returns:
            bool: Success status
        """
        try:
            if not event_time:
                event_time = datetime.now(timezone.utc)
            
            data = {
                "video_job_id": video_job_id,
                "platform_id": platform_id,
                "event_time": event_time.isoformat(),
                "views": views,
                "impressions": impressions,
                "engagement_rate": engagement_rate,
                **kwargs
            }
            
            response = self.supabase.table("performance_kpi_events").insert(data).execute()
            
            logger.info(f"Logged KPI event for {video_job_id} on {platform_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log KPI event for {video_job_id}: {e}")
            return False

    async def create_optimization_trial(
        self,
        user_id: str,
        hypothesis: str,
        variants: Dict[str, Any],
        primary_kpi: str,
        start_at: datetime,
        end_at: Optional[datetime] = None,
        guardrails: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create an optimization trial
        
        Args:
            user_id: User identifier
            hypothesis: Trial hypothesis
            variants: Trial variants configuration
            primary_kpi: Primary KPI to measure
            start_at: Trial start timestamp
            end_at: Trial end timestamp (optional)
            guardrails: Quality guardrails
            
        Returns:
            Trial ID or None
        """
        try:
            trial_id = f"trial_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            data = {
                "user_id": user_id,
                "trial_id": trial_id,
                "hypothesis": hypothesis,
                "variants": variants,
                "primary_kpi": primary_kpi,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat() if end_at else None,
                "guardrails": guardrails or {}
            }
            
            response = self.supabase.table("optimization_trials").insert(data).execute()
            
            logger.info(f"Created optimization trial {trial_id} for user {user_id}")
            return trial_id
            
        except Exception as e:
            logger.error(f"Failed to create optimization trial: {e}")
            return None

    async def batch_get_timing_recommendations(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get timing recommendations for multiple platforms/content in batch
        
        Args:
            requests: List of recommendation requests
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for request in requests:
            try:
                # Extract parameters
                platform_id = request["platform_id"]
                user_preferences = UserSchedulingPreferences(**request["user_preferences"])
                content_format = request.get("content_format", "general")
                audience_segment = request.get("audience_segment", "general")
                start_date = datetime.fromisoformat(request["start_date"])
                end_date = datetime.fromisoformat(request["end_date"])
                timezone_str = request.get("timezone", "UTC")
                
                # Get recommendation
                recommendation = self.calculate_optimal_posting_slots(
                    platform_id=platform_id,
                    user_preferences=user_preferences,
                    content_format=content_format,
                    audience_segment=audience_segment,
                    start_date=start_date,
                    end_date=end_date,
                    timezone_str=timezone_str
                )
                
                recommendations.append({
                    "platform_id": platform_id,
                    "content_format": content_format,
                    "recommendation": asdict(recommendation),
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Failed to get recommendation for request: {e}")
                recommendations.append({
                    "platform_id": request.get("platform_id", "unknown"),
                    "status": "error",
                    "error": str(e)
                })
        
        return recommendations


# API Client for scheduling recommendations
class SchedulingAPIClient:
    """
    HTTP API client for scheduling recommendations
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize API client
        
        Args:
            base_url: API base URL
            api_key: API authentication key
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_timing_recommendation(
        self,
        platform_id: str,
        user_preferences: Dict[str, Any],
        content_format: str = "general",
        audience_segment: str = "general",
        start_date: str = None,
        end_date: str = None,
        timezone_str: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Get timing recommendation via API
        
        Args:
            platform_id: Platform identifier
            user_preferences: User preferences dictionary
            content_format: Content format
            audience_segment: Audience segment
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            timezone_str: Timezone string
            
        Returns:
            API response
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        payload = {
            "platform_id": platform_id,
            "user_preferences": user_preferences,
            "content_format": content_format,
            "audience_segment": audience_segment,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone_str
        }
        
        async with self.session.post(
            f"{self.base_url}/timing/recommendations",
            json=payload
        ) as response:
            return await response.json()
    
    async def batch_get_recommendations(
        self,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get multiple timing recommendations via API
        
        Args:
            requests: List of recommendation requests
            
        Returns:
            API response
        """
        async with self.session.post(
            f"{self.base_url}/timing/recommendations/batch",
            json={"requests": requests}
        ) as response:
            return await response.json()
    
    async def log_performance_event(
        self,
        video_job_id: str,
        platform_id: str,
        views: int,
        impressions: int,
        engagement_rate: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log performance event via API
        
        Args:
            video_job_id: Video job identifier
            platform_id: Platform identifier
            views: View count
            impressions: Impression count
            engagement_rate: Engagement rate
            **kwargs: Additional event data
            
        Returns:
            API response
        """
        payload = {
            "video_job_id": video_job_id,
            "platform_id": platform_id,
            "views": views,
            "impressions": impressions,
            "engagement_rate": engagement_rate,
            "event_time": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/performance/events",
            json=payload
        ) as response:
            return await response.json()


# Example usage and testing functions
async def example_usage():
    """Example usage of the platform timing service"""
    
    # Initialize service
    service = PlatformTimingService(
        supabase_url="your_supabase_url",
        supabase_key="your_supabase_key"
    )
    
    # Load research data to database
    success = await service.load_research_data_to_database()
    print(f"Research data loaded: {success}")
    
    # Create user preferences
    user_prefs = UserSchedulingPreferences(
        user_id="user_123",
        platform_id="youtube",
        timezone="America/New_York",
        posting_frequency_min=2,
        posting_frequency_max=4,
        days_blacklist=["sat", "sun"],
        hours_blacklist=[{"start": 0, "end": 6}],
        content_format="long_form",
        quality_threshold=0.05
    )
    
    # Save user preferences
    await service.save_user_scheduling_preferences(user_prefs)
    
    # Get timing recommendation
    start_date = datetime.now()
    end_date = start_date + timedelta(days=14)
    
    recommendation = service.calculate_optimal_posting_slots(
        platform_id="youtube",
        user_preferences=user_prefs,
        content_format="long_form",
        audience_segment="us_east",
        start_date=start_date,
        end_date=end_date,
        timezone_str="America/New_York"
    )
    
    print(f"Recommendation confidence: {recommendation.confidence_score}")
    print(f"Recommended slots: {recommendation.recommended_slots}")
    print(f"Reasoning: {recommendation.reasoning}")
    
    # Log performance KPI
    await service.log_performance_kpi(
        video_job_id="video_123",
        platform_id="youtube",
        views=1500,
        impressions=5000,
        engagement_rate=0.08,
        watch_time_seconds=1200,
        comments=25,
        likes=150
    )
    
    # Create optimization trial
    trial_id = await service.create_optimization_trial(
        user_id="user_123",
        hypothesis="Wednesday 4 PM posts perform better than Monday 4 PM posts",
        variants={
            "A": {"day": "wednesday", "time": "16:00"},
            "B": {"day": "monday", "time": "16:00"}
        },
        primary_kpi="engagement_rate",
        start_at=datetime.now(),
        end_at=datetime.now() + timedelta(days=14),
        guardrails={"min_engagement_rate": 0.03}
    )
    
    print(f"Created optimization trial: {trial_id}")


if __name__ == "__main__":
    import asyncio
    
    # Run example
    asyncio.run(example_usage())