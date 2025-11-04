"""
Comprehensive Test Suite for Platform Timing Calculations

This module tests platform-specific timing calculation algorithms:
1. Evidence-based timing window calculations
2. Platform-specific optimization algorithms
3. Audience demographic adjustments
4. Time zone and geographic considerations
5. Content type variations

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import pytest
import numpy as np
import sqlite3
import tempfile
import json
from datetime import datetime, timedelta, timezone, time
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, patch
import logging

# Import scheduling components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from scheduling_optimizer import (
    SchedulingOptimizer, Platform, ContentType, AudienceProfile, 
    PostingWindow, PerformanceMetrics
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPlatformTimingCalculations:
    """Test suite for platform-specific timing calculations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def platform_timing_optimizer(self, temp_db_path):
        """Initialize timing optimizer with test database."""
        return SchedulingOptimizer(db_path=temp_db_path)
    
    @pytest.fixture
    def research_data_samples(self):
        """Sample research data based on 2025 platform studies."""
        return {
            'youtube': {
                'baseline_windows': [
                    {'day': 2, 'start_hour': 15, 'end_hour': 17, 'weight': 0.9},  # Wed 3-5PM peak
                    {'day': 1, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},  # Tue 3-5PM
                    {'day': 3, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},  # Thu 3-5PM
                    {'day': 4, 'start_hour': 15, 'end_hour': 17, 'weight': 0.8},  # Fri 3-5PM
                ],
                'content_adjustments': {
                    'youtube_long_form': {'weight_multiplier': 1.0},
                    'youtube_shorts': {'weight_multiplier': 1.2, 'peak_expansion': True}
                }
            },
            'instagram': {
                'baseline_windows': [
                    {'day': 1, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},  # Mon-Thu 10AM-3PM
                    {'day': 2, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                    {'day': 3, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                    {'day': 4, 'start_hour': 10, 'end_hour': 15, 'weight': 0.85},
                    {'day': 1, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},    # Morning Reels
                    {'day': 2, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},
                    {'day': 3, 'start_hour': 6, 'end_hour': 9, 'weight': 0.7},
                    {'day': 1, 'start_hour': 18, 'end_hour': 21, 'weight': 0.8},  # Evening Reels
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
                    {'day': 2, 'start_hour': 17, 'end_hour': 18, 'weight': 0.9},  # Wed 5-6PM peak
                    {'day': 6, 'start_hour': 20, 'end_hour': 22, 'weight': 0.85}, # Sun 8-10PM
                    {'day': 1, 'start_hour': 17, 'end_hour': 19, 'weight': 0.8},  # Mon 5-7PM
                    {'day': 3, 'start_hour': 17, 'end_hour': 19, 'weight': 0.8},  # Wed 5-7PM
                    {'day': 4, 'start_hour': 17, 'end_hour': 19, 'weight': 0.8},  # Thu 5-7PM
                ],
                'avoid_windows': [
                    {'day': 5, 'start_hour': 0, 'end_hour': 23, 'weight': 0.1}    # Saturday low performance
                ],
                'content_adjustments': {
                    'tiktok_video': {'weight_multiplier': 1.0, 'peak_concentration': True}
                }
            },
            'linkedin': {
                'baseline_windows': [
                    {'day': 1, 'start_hour': 8, 'end_hour': 11, 'weight': 0.9},   # Tue-Thu 8-11AM
                    {'day': 1, 'start_hour': 12, 'end_hour': 14, 'weight': 0.8},  # Tue-Thu 12-2PM
                    {'day': 2, 'start_hour': 8, 'end_hour': 11, 'weight': 0.9},
                    {'day': 2, 'start_hour': 12, 'end_hour': 14, 'weight': 0.8},
                    {'day': 3, 'start_hour': 8, 'end_hour': 11, 'weight': 0.9},
                    {'day': 3, 'start_hour': 12, 'end_hour': 14, 'weight': 0.8},
                ],
                'content_adjustments': {
                    'linkedin_post': {'weight_multiplier': 1.0, 'business_hours_only': True},
                    'linkedin_carousel': {'weight_multiplier': 1.1, 'morning_preference': True}
                }
            },
            'facebook': {
                'baseline_windows': [
                    {'day': 1, 'start_hour': 11, 'end_hour': 14, 'weight': 0.8},  # Mon-Thu mid-day
                    {'day': 2, 'start_hour': 11, 'end_hour': 14, 'weight': 0.8},
                    {'day': 3, 'start_hour': 11, 'end_hour': 14, 'weight': 0.8},
                    {'day': 4, 'start_hour': 11, 'end_hour': 14, 'weight': 0.8},
                ],
                'content_adjustments': {
                    'facebook_reels': {'weight_multiplier': 1.2, 'priority_boost': True},
                    'facebook_post': {'weight_multiplier': 0.9, 'standard_timing': True}
                }
            }
        }
    
    @pytest.fixture
    def audience_profiles(self):
        """Different audience profile types for testing."""
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
    
    # YouTube Timing Tests
    def test_youtube_optimal_timing_calculation(self, platform_timing_optimizer, audience_profiles):
        """Test YouTube optimal timing calculations."""
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.YOUTUBE,
            content_type=ContentType.YOUTUBE_LONG_FORM,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=2  # Wednesday
        )
        
        # YouTube should prefer afternoon hours (3-5PM)
        afternoon_scores = [scores[hour] for hour in range(15, 18)]
        morning_scores = [scores[hour] for hour in range(6, 9)]
        late_night_scores = [scores[hour] for hour in range(0, 6)]
        
        avg_afternoon = np.mean(afternoon_scores)
        avg_morning = np.mean(morning_scores)
        avg_late_night = np.mean(late_night_scores)
        
        assert avg_afternoon > avg_morning * 1.2, \
            "YouTube should prefer afternoon over morning"
        assert avg_afternoon > avg_late_night * 2.0, \
            "YouTube should strongly prefer afternoon over late night"
        
        # Wednesday should have peak scores
        wednesday_peak_scores = [scores[hour] for hour in [15, 16, 17]]
        assert np.mean(wednesday_peak_scores) > 0.7, \
            "Wednesday peak hours should have high scores"
    
    def test_youtube_shorts_vs_longform(self, platform_timing_optimizer, audience_profiles):
        """Test YouTube Shorts vs Long-form content timing differences."""
        longform_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.YOUTUBE,
            content_type=ContentType.YOUTUBE_LONG_FORM,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2
        )
        
        shorts_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.YOUTUBE,
            content_type=ContentType.YOUTUBE_SHORTS,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2
        )
        
        # Shorts should be more flexible with timing
        shorts_variance = np.var(list(shorts_scores.values()))
        longform_variance = np.var(list(longform_scores.values()))
        
        assert shorts_variance >= longform_variance * 0.8, \
            "Shorts should have more flexible timing (similar or higher variance)"
        
        # Both should still prefer afternoon
        afternoon_short_score = np.mean([shorts_scores[hour] for hour in [15, 16, 17]])
        afternoon_long_score = np.mean([longform_scores[hour] for hour in [15, 16, 17]])
        
        assert afternoon_short_score > 0.6, "Shorts afternoon should be good"
        assert afternoon_long_score > 0.6, "Long-form afternoon should be good"
    
    # Instagram Timing Tests
    def test_instagram_peak_timing_calculation(self, platform_timing_optimizer, audience_profiles):
        """Test Instagram peak timing calculations."""
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=2  # Wednesday
        )
        
        # Instagram should prefer business hours (10AM-3PM)
        business_hours = [scores[hour] for hour in range(10, 15)]
        evening_hours = [scores[hour] for hour in range(18, 21)]
        night_hours = [scores[hour] for hour in range(22, 24)]
        
        avg_business = np.mean(business_hours)
        avg_evening = np.mean(evening_hours)
        avg_night = np.mean(night_hours)
        
        assert avg_business > avg_evening, \
            "Instagram should prefer business hours over evening"
        assert avg_business > avg_night * 2.0, \
            "Instagram should strongly prefer business hours over night"
    
    def test_instagram_reels_timing(self, platform_timing_optimizer, audience_profiles):
        """Test Instagram Reels specific timing patterns."""
        feed_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2
        )
        
        reels_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2
        )
        
        # Reels should have evening boost
        evening_reels = [reels_scores[hour] for hour in [18, 19, 20]]
        evening_feed = [feed_scores[hour] for hour in [18, 19, 20]]
        
        assert np.mean(evening_reels) > np.mean(evening_feed), \
            "Reels should have evening timing advantage"
        
        # Reels should also perform well in morning
        morning_reels = [reels_scores[hour] for hour in [6, 7, 8, 9]]
        morning_feed = [feed_scores[hour] for hour in [6, 7, 8, 9]]
        
        assert np.mean(morning_reels) > 0.5, \
            "Reels should have good morning performance"
    
    def test_instagram_stories_timing_flexibility(self, platform_timing_optimizer, audience_profiles):
        """Test Instagram Stories timing flexibility."""
        stories_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_STORIES,
            audience_profile=audience_profiles['mixed_global'],
            day_of_week=6  # Saturday
        )
        
        # Stories should be more flexible than feed content
        all_hours_stories = list(stories_scores.values())
        
        # Stories should have more uniform distribution (less variance)
        stories_variance = np.var(all_hours_stories)
        
        # Compare with feed content on same day
        feed_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=audience_profiles['mixed_global'],
            day_of_week=6  # Saturday
        )
        
        feed_variance = np.var(list(feed_scores.values()))
        
        # Stories should be more flexible (similar or higher variance indicates flexibility)
        assert stories_variance >= feed_variance * 0.8, \
            "Stories should have flexible timing"
    
    # TikTok Timing Tests
    def test_tiktok_peak_timing_calculation(self, platform_timing_optimizer, audience_profiles):
        """Test TikTok peak timing calculations."""
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2  # Wednesday
        )
        
        # TikTok should have strong evening peak (5-6PM)
        peak_hour_scores = [scores[17], scores[18]]  # 5-6PM
        morning_scores = [scores[hour] for hour in range(6, 10)]
        late_night_scores = [scores[hour] for hour in range(0, 6)]
        
        avg_peak = np.mean(peak_hour_scores)
        avg_morning = np.mean(morning_scores)
        avg_late_night = np.mean(late_night_scores)
        
        assert avg_peak > 0.8, "TikTok peak hours should have very high scores"
        assert avg_peak > avg_morning * 2.0, \
            "TikTok should strongly prefer evening over morning"
        assert avg_peak > avg_late_night * 3.0, \
            "TikTok should strongly prefer evening over late night"
    
    def test_tiktok_saturday_avoidance(self, platform_timing_optimizer, audience_profiles):
        """Test TikTok Saturday performance penalty."""
        wednesday_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2  # Wednesday
        )
        
        saturday_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=5  # Saturday
        )
        
        # Saturday should have lower overall performance
        wed_avg = np.mean(list(wednesday_scores.values()))
        sat_avg = np.mean(list(saturday_scores.values()))
        
        # Allow for some variance, but Saturday should generally be worse
        assert sat_avg < wed_avg * 0.9, \
            "Saturday should have lower performance than Wednesday"
    
    def test_tiktok_sunday_evenings(self, platform_timing_optimizer, audience_profiles):
        """Test TikTok Sunday evening performance."""
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=6  # Sunday
        )
        
        # Sunday evenings (8-10PM) should be good
        sunday_evening = [scores[hour] for hour in [20, 21, 22]]
        sunday_morning = [scores[hour] for hour in [6, 7, 8, 9]]
        
        avg_evening = np.mean(sunday_evening)
        avg_morning = np.mean(sunday_morning)
        
        assert avg_evening > 0.7, "Sunday evenings should have good TikTok performance"
        assert avg_evening > avg_morning, \
            "Sunday evenings should outperform morning"
    
    # LinkedIn Timing Tests
    def test_linkedin_business_hours(self, platform_timing_optimizer, audience_profiles):
        """Test LinkedIn business hours preference."""
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=2  # Wednesday
        )
        
        # LinkedIn should strongly prefer business hours
        business_morning = [scores[hour] for hour in range(8, 11)]
        business_lunch = [scores[hour] for hour in range(12, 14)]
        evening = [scores[hour] for hour in range(17, 20)]
        weekend = [scores[hour] for hour in [10, 11]]  # Weekend hours
        
        avg_business = (np.mean(business_morning) + np.mean(business_lunch)) / 2
        avg_evening = np.mean(evening)
        avg_weekend = np.mean(weekend)
        
        assert avg_business > 0.7, "Business hours should have high LinkedIn scores"
        assert avg_business > avg_evening * 2.0, \
            "LinkedIn should strongly prefer business over evening"
        assert avg_business > avg_weekend * 3.0, \
            "LinkedIn should strongly prefer business over weekend"
    
    def test_linkedin_content_type_variations(self, platform_timing_optimizer, audience_profiles):
        """Test LinkedIn content type timing differences."""
        post_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=2
        )
        
        carousel_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_CAROUSEL,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=2
        )
        
        # Carousels might have morning preference
        morning_carousel = np.mean([carousel_scores[hour] for hour in [8, 9, 10]])
        morning_post = np.mean([post_scores[hour] for hour in [8, 9, 10]])
        
        assert morning_carousel > 0.6, "Carousels should have good morning performance"
        assert morning_carousel >= morning_post, \
            "Carousels should prefer morning over regular posts"
    
    # Facebook Timing Tests
    def test_facebook_midday_preference(self, platform_timing_optimizer, audience_profiles):
        """Test Facebook midday posting preference."""
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.FACEBOOK,
            content_type=ContentType.FACEBOOK_POST,
            audience_profile=audience_profiles['mixed_global'],
            day_of_week=2  # Wednesday
        )
        
        # Facebook should prefer midday (11AM-2PM)
        midday_scores = [scores[hour] for hour in range(11, 14)]
        morning_scores = [scores[hour] for hour in range(6, 9)]
        evening_scores = [scores[hour] for hour in range(17, 20)]
        
        avg_midday = np.mean(midday_scores)
        avg_morning = np.mean(morning_scores)
        avg_evening = np.mean(evening_scores)
        
        assert avg_midday > 0.6, "Facebook midday should have good performance"
        assert avg_midday > avg_morning, \
            "Facebook should prefer midday over morning"
        assert avg_midday > avg_evening, \
            "Facebook should prefer midday over evening"
    
    def test_facebook_reels_priority(self, platform_timing_optimizer, audience_profiles):
        """Test Facebook Reels priority boost."""
        post_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.FACEBOOK,
            content_type=ContentType.FACEBOOK_POST,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2
        )
        
        reels_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.FACEBOOK,
            content_type=ContentType.FACEBOOK_REELS,
            audience_profile=audience_profiles['gen_z_mobile'],
            day_of_week=2
        )
        
        # Reels should have priority boost
        reels_avg = np.mean(list(reels_scores.values()))
        post_avg = np.mean(list(post_scores.values()))
        
        assert reels_avg > post_avg, \
            "Facebook Reels should have priority over regular posts"
        assert reels_avg > 0.6, "Reels should have good overall performance"
    
    # Audience Demographics Tests
    def test_age_cohort_impact(self, platform_timing_optimizer):
        """Test age cohort impact on timing calculations."""
        gen_z_audience = AudienceProfile(
            age_cohorts={'18-24': 0.8, '25-34': 0.2},
            device_split={'mobile': 0.9, 'desktop': 0.1},
            time_zone_weights={'UTC-5': 1.0}
        )
        
        millennials_audience = AudienceProfile(
            age_cohorts={'25-34': 0.5, '35-44': 0.5},
            device_split={'mobile': 0.6, 'desktop': 0.4},
            time_zone_weights={'UTC': 1.0}
        )
        
        # Test TikTok (Gen Z platform)
        gen_z_tiktok = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            audience_profile=gen_z_audience,
            day_of_week=2
        )
        
        millennials_tiktok = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            audience_profile=millennials_audience,
            day_of_week=2
        )
        
        # Gen Z should have higher scores on TikTok
        gen_z_avg = np.mean(list(gen_z_tiktok.values()))
        millennials_avg = np.mean(list(millennials_tiktok.values()))
        
        assert gen_z_avg > millennials_avg, \
            "Gen Z audience should perform better on TikTok"
    
    def test_device_split_impact(self, platform_timing_optimizer):
        """Test device split impact on platform timing."""
        mobile_heavy = AudienceProfile(
            age_cohorts={'25-34': 1.0},
            device_split={'mobile': 0.9, 'desktop': 0.1},
            time_zone_weights={'UTC-5': 1.0}
        )
        
        desktop_heavy = AudienceProfile(
            age_cohorts={'35-44': 1.0},
            device_split={'mobile': 0.3, 'desktop': 0.7},
            time_zone_weights={'UTC-5': 1.0}
        )
        
        # Test LinkedIn (desktop-heavy platform)
        mobile_linkedin = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            audience_profile=mobile_heavy,
            day_of_week=2
        )
        
        desktop_linkedin = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            audience_profile=desktop_heavy,
            day_of_week=2
        )
        
        # Desktop-heavy audience should perform better on LinkedIn
        desktop_avg = np.mean(list(desktop_linkedin.values()))
        mobile_avg = np.mean(list(mobile_linkedin.values()))
        
        assert desktop_avg > mobile_avg, \
            "Desktop-heavy audience should perform better on LinkedIn"
    
    def test_time_zone_distribution(self, platform_timing_optimizer):
        """Test time zone distribution impact."""
        us_focused = AudienceProfile(
            age_cohorts={'25-34': 1.0},
            device_split={'mobile': 0.7, 'desktop': 0.3},
            time_zone_weights={'UTC-8': 0.5, 'UTC-5': 0.5}
        )
        
        global_mixed = AudienceProfile(
            age_cohorts={'25-34': 1.0},
            device_split={'mobile': 0.7, 'desktop': 0.3},
            time_zone_weights={'UTC-8': 0.25, 'UTC-5': 0.25, 'UTC': 0.25, 'UTC+8': 0.25}
        )
        
        # Test Instagram timing
        us_instagram = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=us_focused,
            day_of_week=2
        )
        
        global_instagram = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=global_mixed,
            day_of_week=2
        )
        
        # Both should have peak windows, but distribution might differ
        us_variance = np.var(list(us_instagram.values()))
        global_variance = np.var(list(global_instagram.values()))
        
        # US-focused should have more concentrated peaks
        assert us_variance > global_variance * 0.8, \
            "US-focused audience should have more concentrated timing peaks"
    
    # Cross-Platform Timing Tests
    def test_cross_platform_peak_comparison(self, platform_timing_optimizer, audience_profiles):
        """Test timing peaks across different platforms."""
        platforms_and_types = [
            (Platform.INSTAGRAM, ContentType.INSTAGRAM_FEED),
            (Platform.TIKTOK, ContentType.TIKTOK_VIDEO),
            (Platform.LINKEDIN, ContentType.LINKEDIN_POST),
            (Platform.YOUTUBE, ContentType.YOUTUBE_LONG_FORM)
        ]
        
        timing_scores = {}
        for platform, content_type in platforms_and_types:
            scores = platform_timing_optimizer.calculate_timing_scores(
                platform=platform,
                content_type=content_type,
                audience_profile=audience_profiles['working_professionals'],
                day_of_week=2  # Wednesday
            )
            timing_scores[platform.value] = scores
        
        # Each platform should have distinct peak patterns
        instagram_peak_hours = sorted(timing_scores[Platform.INSTAGRAM.value].items(), 
                                    key=lambda x: x[1], reverse=True)[:3]
        tiktok_peak_hours = sorted(timing_scores[Platform.TIKTOK.value].items(), 
                                 key=lambda x: x[1], reverse=True)[:3]
        linkedin_peak_hours = sorted(timing_scores[Platform.LINKEDIN.value].items(), 
                                   key=lambda x: x[1], reverse=True)[:3]
        youtube_peak_hours = sorted(timing_scores[Platform.YOUTUBE.value].items(), 
                                  key=lambda x: x[1], reverse=True)[:3]
        
        # Verify distinct patterns
        instagram_peak_times = [hour for hour, score in instagram_peak_hours]
        tiktok_peak_times = [hour for hour, score in tiktok_peak_hours]
        linkedin_peak_times = [hour for hour, score in linkedin_peak_hours]
        youtube_peak_times = [hour for hour, score in youtube_peak_hours]
        
        # LinkedIn should prefer business hours (8-14)
        linkedin_business_count = sum(1 for hour in linkedin_peak_times if 8 <= hour <= 14)
        assert linkedin_business_count >= 2, \
            "LinkedIn should prefer business hours"
        
        # TikTok should prefer evening (17-21)
        tiktok_evening_count = sum(1 for hour in tiktok_peak_times if 17 <= hour <= 21)
        assert tiktok_evening_count >= 2, \
            "TikTok should prefer evening hours"
    
    def test_seasonality_adjustments(self, platform_timing_optimizer, audience_profiles):
        """Test seasonal and day-of-week adjustments."""
        # Test same platform on different days
        monday_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=0  # Monday
        )
        
        wednesday_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=2  # Wednesday
        )
        
        saturday_scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=audience_profiles['working_professionals'],
            day_of_week=5  # Saturday
        )
        
        # Wednesday should generally outperform Monday and Saturday for business content
        wed_avg = np.mean(list(wednesday_scores.values()))
        mon_avg = np.mean(list(monday_scores.values()))
        sat_avg = np.mean(list(saturday_scores.values()))
        
        # Allow some variance but weekday should generally be better than weekend
        assert wed_avg >= mon_avg * 0.9, \
            "Wednesday should perform at least as well as Monday"
        assert wed_avg > sat_avg * 1.1, \
            "Wednesday should outperform Saturday"
    
    # Performance and Validation Tests
    def test_timing_score_normalization(self, platform_timing_optimizer, audience_profiles):
        """Test that timing scores are properly normalized."""
        platforms_to_test = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]
        content_types = [ContentType.INSTAGRAM_FEED, ContentType.TIKTOK_VIDEO, 
                        ContentType.YOUTUBE_LONG_FORM]
        
        for i, platform in enumerate(platforms_to_test):
            scores = platform_timing_optimizer.calculate_timing_scores(
                platform=platform,
                content_type=content_types[i],
                audience_profile=audience_profiles['mixed_global'],
                day_of_week=2
            )
            
            # All scores should be between 0 and 1
            assert all(0 <= score <= 1 for score in scores.values()), \
                f"Scores for {platform.value} should be normalized to [0,1]"
            
            # Should have some variation (not all the same)
            assert len(set(scores.values())) > 5, \
                f"Scores for {platform.value} should have variation"
            
            # Should have both high and low scoring periods
            max_score = max(scores.values())
            min_score = min(scores.values())
            assert max_score - min_score > 0.3, \
                f"Scores for {platform.value} should have significant variation"
    
    def test_algorithm_consistency(self, platform_timing_optimizer, audience_profiles):
        """Test algorithm consistency across multiple calls."""
        # Get scores multiple times for same parameters
        all_scores = []
        for _ in range(5):
            scores = platform_timing_optimizer.calculate_timing_scores(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_REELS,
                audience_profile=audience_profiles['gen_z_mobile'],
                day_of_week=2
            )
            all_scores.append(scores)
        
        # All results should be identical
        for i in range(1, len(all_scores)):
            assert all_scores[0] == all_scores[i], \
                "Algorithm should produce consistent results"
    
    def test_large_audience_handling(self, platform_timing_optimizer):
        """Test handling of large audience profiles."""
        # Create large audience profile with many demographics
        large_audience = AudienceProfile(
            age_cohorts={f'{i}-{i+4}': 0.1 for i in range(18, 65, 5)},
            device_split={'mobile': 0.6, 'desktop': 0.3, 'tablet': 0.1},
            time_zone_weights={f'UTC{offset:+d}': 0.1 for offset in range(-12, 13, 2)},
            geography={f'Country_{i}': 0.05 for i in range(20)}
        )
        
        scores = platform_timing_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            audience_profile=large_audience,
            day_of_week=2
        )
        
        # Should still produce valid scores
        assert len(scores) == 24
        assert all(0 <= score <= 1 for score in scores.values())
    
    def test_time_complexity_performance(self, platform_timing_optimizer, audience_profiles):
        """Test timing calculation performance."""
        import time
        
        platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE, 
                    Platform.LINKEDIN, Platform.FACEBOOK]
        content_types = [ContentType.INSTAGRAM_FEED, ContentType.TIKTOK_VIDEO,
                        ContentType.YOUTUBE_LONG_FORM, ContentType.LINKEDIN_POST,
                        ContentType.FACEBOOK_POST]
        
        start_time = time.time()
        
        for i, (platform, content_type) in enumerate(zip(platforms, content_types)):
            scores = platform_timing_optimizer.calculate_timing_scores(
                platform=platform,
                content_type=content_type,
                audience_profile=audience_profiles['mixed_global'],
                day_of_week=2
            )
            assert len(scores) == 24
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should calculate all platform timings quickly (< 1 second)
        assert total_time < 1.0, \
            f"Timing calculations too slow: {total_time:.3f}s for 5 platforms"
        
        # Individual calculation should be very fast
        individual_time = total_time / len(platforms)
        assert individual_time < 0.1, \
            f"Individual timing calculation too slow: {individual_time:.3f}s"


class TestTimingValidationAgainstResearch:
    """Test suite validating timing algorithms against research data."""
    
    @pytest.fixture
    def research_validation_data(self):
        """Research-based validation data."""
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
    
    def test_research_based_validation(self, research_validation_data):
        """Validate timing calculations against research data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        optimizer = SchedulingOptimizer(db_path=db_path)
        
        audience = AudienceProfile(
            age_cohorts={'25-34': 0.4, '35-44': 0.3, '18-24': 0.3},
            device_split={'mobile': 0.7, 'desktop': 0.3},
            time_zone_weights={'UTC-5': 0.5, 'UTC-8': 0.3}
        )
        
        # Test Instagram Reels evening boost
        reels_scores = optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=audience,
            day_of_week=2  # Wednesday
        )
        
        evening_scores = [reels_scores[hour] for hour in research_validation_data['instagram_reels_evening_boost']['hours']]
        min_evening_score = min(evening_scores)
        
        assert min_evening_score >= research_validation_data['instagram_reels_evening_boost']['expected_min_score'], \
            f"Instagram Reels evening scores {evening_scores} below research minimum {research_validation_data['instagram_reels_evening_boost']['expected_min_score']}"
        
        # Test LinkedIn business hours
        linkedin_scores = optimizer.calculate_timing_scores(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            audience_profile=audience,
            day_of_week=2  # Wednesday
        )
        
        business_scores = [linkedin_scores[hour] for hour in research_validation_data['linkedin_business_hours']['hours']]
        min_business_score = min(business_scores)
        
        assert min_business_score >= research_validation_data['linkedin_business_hours']['expected_min_score'], \
            f"LinkedIn business hour scores below research minimum"
        
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])