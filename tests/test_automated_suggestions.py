"""
Comprehensive Test Suite for Automated Suggestion Engine

This module tests the automated posting time suggestion system:
1. Real-time suggestion generation algorithms
2. Platform-aware scoring models
3. Cross-platform constraint resolution
4. Bayesian updating and learning
5. Performance validation and feedback
6. Google Sheets integration

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import pytest
import asyncio
import numpy as np
import sqlite3
import tempfile
import json
from datetime import datetime, timedelta, timezone, time
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, MagicMock, patch
import logging

# Import suggestion components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from automated_suggestions import (
    SuggestionEngine, Platform, ContentType, SeasonalityType,
    PostingSuggestion, UserPreferences, SuggestionContext,
    BayesianUpdater, ConstraintResolver
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAutomatedSuggestionEngine:
    """Test suite for automated suggestion engine."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def suggestion_engine(self, temp_db_path):
        """Initialize suggestion engine with test database."""
        engine = SuggestionEngine(db_path=temp_db_path)
        return engine
    
    @pytest.fixture
    def user_preferences(self):
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
    def suggestion_context(self, user_preferences):
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
    def historical_performance_data(self, suggestion_engine):
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
    
    # Basic Suggestion Generation Tests
    def test_generate_suggestions_basic(self, suggestion_engine, suggestion_context):
        """Test basic suggestion generation."""
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=suggestion_context,
            num_suggestions=5
        )
        
        assert isinstance(suggestions, list), "Should return list of suggestions"
        assert len(suggestions) == 5, "Should return requested number of suggestions"
        
        for suggestion in suggestions:
            assert isinstance(suggestion, PostingSuggestion), "Each item should be PostingSuggestion"
            assert suggestion.platform == Platform.INSTAGRAM, "Platform should match context"
            assert suggestion.content_type == ContentType.INSTAGRAM_REELS, "Content type should match"
            assert 0 <= suggestion.confidence_score <= 1, "Confidence should be in [0,1]"
            assert 0 <= suggestion.expected_performance <= 1, "Performance should be in [0,1]"
            assert suggestion.suggested_time is not None, "Should have suggested time"
            assert len(suggestion.reasoning) > 0, "Should have reasoning explanation"
    
    def test_suggestion_time_distribution(self, suggestion_engine, suggestion_context):
        """Test that suggestions are properly distributed across time."""
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=suggestion_context,
            num_suggestions=10
        )
        
        # Extract suggested hours
        suggested_hours = [s.suggested_time.hour for s in suggestions]
        
        # Should have variety in timing (not all clustered)
        assert len(set(suggested_hours)) >= 5, "Should suggest variety of times"
        
        # Should respect user preferences (not in blacklisted hours)
        for hour in suggested_hours:
            assert hour not in [0, 1, 2, 3, 4, 5], "Should not suggest blacklisted early morning hours"
        
        # Should prefer active hours
        active_hours_count = sum(1 for hour in suggested_hours if 8 <= hour <= 22)
        assert active_hours_count >= len(suggestions) * 0.8, "Should prefer active hours"
    
    def test_platform_specific_suggestions(self, suggestion_engine):
        """Test platform-specific suggestion patterns."""
        platforms_to_test = [Platform.TIKTOK, Platform.LINKEDIN, Platform.YOUTUBE]
        
        for platform in platforms_to_test:
            # Create context for each platform
            context = SuggestionContext(
                platform=platform,
                content_type=ContentType.TIKTOK_VIDEO if platform == Platform.TIKTOK
                           else ContentType.LINKEDIN_POST if platform == Platform.LINKEDIN
                           else ContentType.YOUTUBE_LONG_FORM,
                user_preferences=UserPreferences(
                    user_id=f"user_{platform.value}",
                    timezone="UTC-5",
                    active_hours_start=time(8, 0),
                    active_hours_end=time(22, 0),
                    posting_frequency_limits={},
                    blacklisted_hours=[],
                    preferred_content_types={platform: [ContentType.TIKTOK_VIDEO]},
                    automation_enabled=True
                ),
                target_audience={},
                content_metadata={}
            )
            
            suggestions = suggestion_engine.generate_posting_suggestions(
                context=context,
                num_suggestions=5
            )
            
            assert len(suggestions) == 5, f"Should generate suggestions for {platform.value}"
            
            # Each platform should have characteristic timing patterns
            suggested_hours = [s.suggested_time.hour for s in suggestions]
            
            if platform == Platform.LINKEDIN:
                # LinkedIn should prefer business hours
                business_hours = [h for h in suggested_hours if 8 <= h <= 17]
                assert len(business_hours) >= 3, "LinkedIn should suggest business hours"
            
            elif platform == Platform.TIKTOK:
                # TikTok should prefer evening hours
                evening_hours = [h for h in suggested_hours if 17 <= h <= 22]
                assert len(evening_hours) >= 2, "TikTok should suggest evening hours"
    
    # Bayesian Learning Tests
    def test_bayesian_updating(self, suggestion_engine, historical_performance_data):
        """Test Bayesian parameter updating."""
        # Get initial model parameters
        initial_params = suggestion_engine.get_model_parameters(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS
        )
        
        # Provide new performance feedback
        new_feedback = {
            'platform': Platform.INSTAGRAM,
            'content_type': ContentType.INSTAGRAM_REELS,
            'suggested_time': datetime.now(timezone.utc) - timedelta(hours=2),
            'actual_performance': 0.8,  # High performance
            'engagement_metrics': {
                'reach': 2000,
                'engagement_rate': 0.06,
                'click_through_rate': 0.03
            }
        }
        
        suggestion_engine.record_performance_feedback(**new_feedback)
        
        # Update model
        update_result = suggestion_engine.update_bayesian_model()
        
        assert update_result is True, "Bayesian update should succeed"
        
        # Get updated parameters
        updated_params = suggestion_engine.get_model_parameters(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS
        )
        
        # Parameters should be updated (though the exact change depends on learning rate)
        assert updated_params != initial_params, "Model parameters should be updated"
    
    def test_adaptive_learning_performance(self, suggestion_engine, historical_performance_data):
        """Test that adaptive learning improves suggestions over time."""
        # Create test context
        context = SuggestionContext(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            user_preferences=UserPreferences(
                user_id="adaptive_test_user",
                timezone="UTC-5",
                active_hours_start=time(6, 0),
                active_hours_end=time(23, 0),
                posting_frequency_limits={},
                blacklisted_hours=[],
                preferred_content_types={Platform.TIKTOK: [ContentType.TIKTOK_VIDEO]},
                automation_enabled=True
            ),
            target_audience={},
            content_metadata={}
        )
        
        # Generate initial suggestions
        initial_suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=3
        )
        
        initial_avg_confidence = np.mean([s.confidence_score for s in initial_suggestions])
        
        # Simulate posting and getting feedback for each suggestion
        for suggestion in initial_suggestions:
            # Provide feedback based on suggested time performance
            hour = suggestion.suggested_time.hour
            
            # Simulate that evening posts perform better
            if 17 <= hour <= 21:
                performance = np.random.normal(0.7, 0.1)  # Good performance
            else:
                performance = np.random.normal(0.4, 0.1)  # Poor performance
            
            suggestion_engine.record_performance_feedback(
                platform=context.platform,
                content_type=context.content_type,
                suggested_time=suggestion.suggested_time,
                actual_performance=np.clip(performance, 0, 1),
                engagement_metrics={'reach': 1000, 'engagement_rate': 0.04}
            )
        
        # Update model
        suggestion_engine.update_bayesian_model()
        
        # Generate new suggestions after learning
        updated_suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=3
        )
        
        updated_avg_confidence = np.mean([s.confidence_score for s in updated_suggestions])
        
        # Model should either maintain or improve confidence after learning
        assert updated_avg_confidence >= initial_avg_confidence * 0.95, \
            "Confidence should not decrease significantly after learning"
    
    # Cross-Platform Constraint Resolution Tests
    def test_cross_platform_conflict_resolution(self, suggestion_engine):
        """Test conflict resolution across multiple platforms."""
        # Create contexts for multiple platforms with potential conflicts
        contexts = [
            SuggestionContext(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_REELS,
                user_preferences=UserPreferences(
                    user_id="cross_platform_user",
                    timezone="UTC-5",
                    active_hours_start=time(6, 0),
                    active_hours_end=time(23, 0),
                    posting_frequency_limits={
                        Platform.INSTAGRAM: {"min_hours": 18, "max_per_day": 2}
                    },
                    blacklisted_hours=[],
                    preferred_content_types={Platform.INSTAGRAM: [ContentType.INSTAGRAM_REELS]},
                    automation_enabled=True
                ),
                target_audience={},
                content_metadata={}
            ),
            SuggestionContext(
                platform=Platform.TIKTOK,
                content_type=ContentType.TIKTOK_VIDEO,
                user_preferences=UserPreferences(
                    user_id="cross_platform_user",
                    timezone="UTC-5",
                    active_hours_start=time(6, 0),
                    active_hours_end=time(23, 0),
                    posting_frequency_limits={
                        Platform.TIKTOK: {"min_hours": 12, "max_per_day": 3}
                    },
                    blacklisted_hours=[],
                    preferred_content_types={Platform.TIKTOK: [ContentType.TIKTOK_VIDEO]},
                    automation_enabled=True
                ),
                target_audience={},
                content_metadata={}
            )
        ]
        
        # Generate suggestions for both platforms
        all_suggestions = {}
        for context in contexts:
            suggestions = suggestion_engine.generate_posting_suggestions(
                context=context,
                num_suggestions=3
            )
            all_suggestions[context.platform] = suggestions
        
        # Resolve conflicts
        resolved_schedule = suggestion_engine.resolve_cross_platform_conflicts(
            suggestions=all_suggestions,
            constraints={
                'min_gap_hours': 6.0,
                'max_concurrent_posts': 1,
                'time_window': (datetime.now(timezone.utc), 
                              datetime.now(timezone.utc) + timedelta(days=7))
            }
        )
        
        assert isinstance(resolved_schedule, dict), "Should return resolved schedule"
        assert len(resolved_schedule) >= 1, "Should schedule posts from at least one platform"
        
        # Check that scheduled times don't conflict
        scheduled_times = []
        for platform, suggestion in resolved_schedule.items():
            if suggestion:
                scheduled_times.append(suggestion.suggested_time)
        
        if len(scheduled_times) > 1:
            scheduled_times.sort()
            for i in range(1, len(scheduled_times)):
                time_diff = abs((scheduled_times[i] - scheduled_times[i-1]).total_seconds()) / 3600
                assert time_diff >= 6.0, f"Scheduled posts should be at least 6 hours apart"
    
    def test_time_window_optimization(self, suggestion_engine):
        """Test optimization within specific time windows."""
        context = SuggestionContext(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            user_preferences=UserPreferences(
                user_id="window_test_user",
                timezone="UTC-5",
                active_hours_start=time(8, 0),
                active_hours_end=time(18, 0),
                posting_frequency_limits={},
                blacklisted_hours=[],
                preferred_content_types={Platform.INSTAGRAM: [ContentType.INSTAGRAM_FEED]},
                automation_enabled=True
            ),
            target_audience={},
            content_metadata={},
            scheduling_constraints={
                'preferred_time_windows': [
                    {'start': time(10, 0), 'end': time(12, 0), 'weight': 0.9},
                    {'start': time(14, 0), 'end': time(16, 0), 'weight': 0.7}
                ]
            }
        )
        
        # Generate suggestions with window constraints
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=5,
            respect_time_windows=True
        )
        
        # All suggestions should be within preferred windows or active hours
        for suggestion in suggestions:
            hour = suggestion.suggested_time.hour
            
            # Check if within preferred windows
            in_preferred_window = False
            for window in context.scheduling_constraints['preferred_time_windows']:
                if window['start'].hour <= hour < window['end'].hour:
                    in_preferred_window = True
                    break
            
            # If not in preferred window, should be in general active hours
            if not in_preferred_window:
                assert 8 <= hour <= 18, f"Hour {hour} should be in active hours"
    
    # Real-time Performance Tests
    def test_real_time_suggestion_generation(self, suggestion_engine, suggestion_context):
        """Test real-time suggestion generation performance."""
        import time
        
        start_time = time.time()
        
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=suggestion_context,
            num_suggestions=5
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Should generate suggestions quickly
        assert generation_time < 2.0, f"Suggestion generation too slow: {generation_time:.3f}s"
        
        # Should still return valid suggestions
        assert len(suggestions) == 5, "Should return all requested suggestions"
    
    def test_batch_suggestion_generation(self, suggestion_engine):
        """Test batch generation of suggestions for multiple contexts."""
        contexts = []
        
        # Create multiple contexts for different platforms
        platforms_and_types = [
            (Platform.INSTAGRAM, ContentType.INSTAGRAM_REELS),
            (Platform.TIKTOK, ContentType.TIKTOK_VIDEO),
            (Platform.LINKEDIN, ContentType.LINKEDIN_POST),
            (Platform.YOUTUBE, ContentType.YOUTUBE_LONG_FORM)
        ]
        
        for platform, content_type in platforms_and_types:
            context = SuggestionContext(
                platform=platform,
                content_type=content_type,
                user_preferences=UserPreferences(
                    user_id=f"batch_user_{platform.value}",
                    timezone="UTC-5",
                    active_hours_start=time(8, 0),
                    active_hours_end=time(22, 0),
                    posting_frequency_limits={},
                    blacklisted_hours=[],
                    preferred_content_types={platform: [content_type]},
                    automation_enabled=True
                ),
                target_audience={},
                content_metadata={}
            )
            contexts.append(context)
        
        # Generate batch suggestions
        batch_results = suggestion_engine.generate_batch_suggestions(
            contexts=contexts,
            suggestions_per_context=3
        )
        
        assert len(batch_results) == len(contexts), "Should return results for all contexts"
        
        for i, (context, suggestions) in enumerate(zip(contexts, batch_results)):
            assert len(suggestions) == 3, f"Context {i} should have 3 suggestions"
            assert all(s.platform == context.platform for s in suggestions), \
                "All suggestions should match context platform"
    
    # Quality and Validation Tests
    def test_suggestion_quality_scoring(self, suggestion_engine, suggestion_context):
        """Test suggestion quality scoring system."""
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=suggestion_context,
            num_suggestions=10
        )
        
        # Check quality score distribution
        quality_scores = [s.quality_score for s in suggestions]
        
        # Should have reasonable distribution
        assert min(quality_scores) >= 0.0, "Quality scores should be non-negative"
        assert max(quality_scores) <= 1.0, "Quality scores should be <= 1.0"
        
        # Top suggestions should have higher scores than bottom ones
        sorted_suggestions = sorted(suggestions, key=lambda x: x.quality_score, reverse=True)
        top_quality = np.mean([s.quality_score for s in sorted_suggestions[:3]])
        bottom_quality = np.mean([s.quality_score for s in sorted_suggestions[-3:]])
        
        assert top_quality > bottom_quality, "Top suggestions should have better quality scores"
    
    def test_suggestion_reasoning_validation(self, suggestion_engine, suggestion_context):
        """Test that suggestion reasoning is comprehensive and valid."""
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=suggestion_context,
            num_suggestions=3
        )
        
        for suggestion in suggestions:
            # Each suggestion should have detailed reasoning
            assert len(suggestion.reasoning) > 10, "Reasoning should be detailed"
            
            # Reasoning should mention key factors
            reasoning_lower = suggestion.reasoning.lower()
            expected_factors = ['time', 'platform', 'audience', 'performance']
            
            # At least some factors should be mentioned
            mentioned_factors = [factor for factor in expected_factors 
                               if factor in reasoning_lower]
            assert len(mentioned_factors) >= 2, "Reasoning should mention key factors"
    
    def test_engagement_prediction_accuracy(self, suggestion_engine, historical_performance_data):
        """Test engagement prediction accuracy."""
        context = SuggestionContext(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            user_preferences=UserPreferences(
                user_id="prediction_test_user",
                timezone="UTC-5",
                active_hours_start=time(8, 0),
                active_hours_end=time(22, 0),
                posting_frequency_limits={},
                blacklisted_hours=[],
                preferred_content_types={Platform.INSTAGRAM: [ContentType.INSTAGRAM_REELS]},
                automation_enabled=True
            ),
            target_audience={},
            content_metadata={'has_video': True, 'duration': 30}
        )
        
        # Generate suggestions
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=5
        )
        
        # Check that predictions are reasonable
        for suggestion in suggestions:
            # Predicted metrics should be in reasonable ranges
            assert 0.0 <= suggestion.predicted_engagement_rate <= 0.2, \
                "Predicted engagement rate should be realistic"
            assert suggestion.predicted_reach >= 100, "Predicted reach should be positive"
            assert suggestion.predicted_click_through_rate >= 0.0, \
                "CTR should be non-negative"
    
    # User Preference Integration Tests
    def test_user_preference_integration(self, suggestion_engine):
        """Test integration of user preferences in suggestion generation."""
        # Create user with very specific preferences
        strict_preferences = UserPreferences(
            user_id="strict_preference_user",
            timezone="UTC-5",
            active_hours_start=time(10, 0),
            active_hours_end=time(16, 0),
            posting_frequency_limits={
                Platform.INSTAGRAM: {"min_hours": 24, "max_per_day": 1}
            },
            blacklisted_hours=list(range(0, 9)) + list(range(18, 24)),  # Only 9 AM - 6 PM
            preferred_content_types={
                Platform.INSTAGRAM: [ContentType.INSTAGRAM_FEED]
            },
            automation_enabled=True,
            quality_threshold=0.8  # High quality threshold
        )
        
        context = SuggestionContext(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_FEED,
            user_preferences=strict_preferences,
            target_audience={},
            content_metadata={}
        )
        
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=5
        )
        
        # All suggestions should respect strict preferences
        for suggestion in suggestions:
            hour = suggestion.suggested_time.hour
            
            # Should be within active hours (10 AM - 4 PM)
            assert 10 <= hour < 16, f"Hour {hour} should be within active hours"
            
            # Should not be in blacklisted hours
            assert hour not in strict_preferences.blacklisted_hours, \
                f"Hour {hour} should not be blacklisted"
    
    def test_preference_learning_adaptation(self, suggestion_engine, historical_performance_data):
        """Test that user preferences adapt based on performance feedback."""
        user_id = "adaptive_preference_user"
        
        # Create initial context
        context = SuggestionContext(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            user_preferences=UserPreferences(
                user_id=user_id,
                timezone="UTC-5",
                active_hours_start=time(8, 0),
                active_hours_end=time(23, 0),
                posting_frequency_limits={},
                blacklisted_hours=[],
                preferred_content_types={Platform.TIKTOK: [ContentType.TIKTOK_VIDEO]},
                automation_enabled=True,
                quality_threshold=0.5
            ),
            target_audience={},
            content_metadata={}
        )
        
        # Generate initial suggestions
        initial_suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=3
        )
        
        # Simulate good performance from specific time range
        for suggestion in initial_suggestions:
            if 18 <= suggestion.suggested_time.hour <= 21:  # Evening posts
                # Provide positive feedback for evening posts
                suggestion_engine.record_performance_feedback(
                    platform=context.platform,
                    content_type=context.content_type,
                    suggested_time=suggestion.suggested_time,
                    actual_performance=0.8,  # High performance
                    engagement_metrics={'reach': 2000, 'engagement_rate': 0.08}
                )
            else:
                # Provide negative feedback for other times
                suggestion_engine.record_performance_feedback(
                    platform=context.platform,
                    content_type=context.content_type,
                    suggested_time=suggestion.suggested_time,
                    actual_performance=0.3,  # Low performance
                    engagement_metrics={'reach': 500, 'engagement_rate': 0.02}
                )
        
        # Update model
        suggestion_engine.update_bayesian_model()
        
        # Generate new suggestions after feedback
        updated_suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=3
        )
        
        # More suggestions should be in evening hours after positive feedback
        evening_count_initial = sum(1 for s in initial_suggestions if 18 <= s.suggested_time.hour <= 21)
        evening_count_updated = sum(1 for s in updated_suggestions if 18 <= s.suggested_time.hour <= 21)
        
        assert evening_count_updated >= evening_count_initial, \
            "Should adapt to prefer times with better performance"
    
    # Error Handling and Edge Cases
    def test_insufficient_data_handling(self, suggestion_engine):
        """Test handling when insufficient historical data is available."""
        context = SuggestionContext(
            platform=Platform.LINKEDIN,  # Platform with likely minimal data
            content_type=ContentType.LINKEDIN_POST,
            user_preferences=UserPreferences(
                user_id="limited_data_user",
                timezone="UTC-5",
                active_hours_start=time(8, 0),
                active_hours_end=time(18, 0),
                posting_frequency_limits={},
                blacklisted_hours=[],
                preferred_content_types={Platform.LINKEDIN: [ContentType.LINKEDIN_POST]},
                automation_enabled=True
            ),
            target_audience={},
            content_metadata={}
        )
        
        # Generate suggestions with limited data
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=3
        )
        
        # Should still provide suggestions using rule-based fallback
        assert len(suggestions) == 3, "Should provide fallback suggestions"
        
        for suggestion in suggestions:
            # Should use conservative/rule-based scores
            assert suggestion.confidence_score >= 0.3, \
                "Fallback suggestions should have minimum confidence"
            assert suggestion.confidence_score <= 0.8, \
                "Fallback suggestions should not have overconfidence"
    
    def test_extreme_user_preferences(self, suggestion_engine):
        """Test handling of extreme user preferences."""
        extreme_preferences = UserPreferences(
            user_id="extreme_user",
            timezone="UTC-5",
            active_hours_start=time(2, 0),  # Very early
            active_hours_end=time(3, 0),   # Very narrow window
            posting_frequency_limits={
                Platform.INSTAGRAM: {"min_hours": 168, "max_per_day": 1}  # Once per week max
            },
            blacklisted_hours=list(range(24)),  # All hours blacklisted initially
            preferred_content_types={Platform.INSTAGRAM: [ContentType.INSTAGRAM_REELS]},
            automation_enabled=True,
            quality_threshold=0.95  # Very high threshold
        )
        
        context = SuggestionContext(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            user_preferences=extreme_preferences,
            target_audience={},
            content_metadata={}
        )
        
        # Should handle extreme preferences gracefully
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=context,
            num_suggestions=3
        )
        
        # Should either provide suggestions or indicate constraints cannot be met
        if len(suggestions) > 0:
            for suggestion in suggestions:
                # Any suggestions should respect extreme constraints
                hour = suggestion.suggested_time.hour
                # Allow for some flexibility in extreme cases
                assert 1 <= hour <= 4 or suggestion.confidence_score < 0.5, \
                    "Should respect or downweight extreme constraints"
    
    def test_concurrent_user_handling(self, suggestion_engine):
        """Test handling multiple concurrent users."""
        # Create multiple users with different preferences
        users_data = []
        for i in range(5):
            user_prefs = UserPreferences(
                user_id=f"concurrent_user_{i}",
                timezone="UTC-5",
                active_hours_start=time(8 + i, 0),  # Staggered active hours
                active_hours_end=time(20 + i, 0),
                posting_frequency_limits={},
                blacklisted_hours=[],
                preferred_content_types={
                    Platform.INSTAGRAM: [ContentType.INSTAGRAM_REELS]
                },
                automation_enabled=True
            )
            
            context = SuggestionContext(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_REELS,
                user_preferences=user_prefs,
                target_audience={},
                content_metadata={}
            )
            users_data.append(context)
        
        # Generate suggestions for all users concurrently
        import time
        start_time = time.time()
        
        all_suggestions = []
        for context in users_data:
            suggestions = suggestion_engine.generate_posting_suggestions(
                context=context,
                num_suggestions=2
            )
            all_suggestions.extend(suggestions)
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Should handle multiple users efficiently
        assert len(all_suggestions) == 10, "Should generate suggestions for all users"
        assert concurrent_time < 5.0, f"Concurrent handling too slow: {concurrent_time:.3f}s"
        
        # Each user should get personalized suggestions
        for i, context in enumerate(users_data):
            user_suggestions = all_suggestions[i*2:(i+1)*2]
            user_hours = [s.suggested_time.hour for s in user_suggestions]
            
            # Should generally be within user's active hours
            active_start = context.user_preferences.active_hours_start.hour
            active_end = context.user_preferences.active_hours_end.hour
            
            for hour in user_hours:
                if active_start <= active_end:  # Same day
                    assert active_start <= hour <= active_end or suggestion.confidence_score < 0.6, \
                        f"User {i} suggestions should respect active hours"
    
    # Integration and API Tests
    def test_google_sheets_integration(self, suggestion_engine):
        """Test integration with Google Sheets for bulk operations."""
        # Simulate bulk job data from sheets
        bulk_job_data = {
            "job_id": "sheets_job_123",
            "user_id": "sheets_user",
            "posts": [
                {
                    "platform": Platform.INSTAGRAM.value,
                    "content_type": ContentType.INSTAGRAM_REELS.value,
                    "title": "Sheets Post 1",
                    "scheduling_priority": "normal"
                },
                {
                    "platform": Platform.TIKTOK.value,
                    "content_type": ContentType.TIKTOK_VIDEO.value,
                    "title": "Sheets Post 2",
                    "scheduling_priority": "high"
                }
            ],
            "user_preferences": {
                "timezone": "UTC-5",
                "active_hours_start": "08:00",
                "active_hours_end": "22:00",
                "quality_threshold": 0.7
            }
        }
        
        # Generate suggestions for bulk job
        bulk_suggestions = suggestion_engine.generate_bulk_sheet_suggestions(
            bulk_job_data=bulk_job_data,
            max_suggestions_per_post=3
        )
        
        assert isinstance(bulk_suggestions, dict), "Should return bulk suggestions dict"
        assert len(bulk_suggestions) == len(bulk_job_data["posts"]), \
            "Should provide suggestions for all posts"
        
        for post_data, suggestions in bulk_suggestions.items():
            assert len(suggestions) == 3, "Should provide 3 suggestions per post"
            
            for suggestion in suggestions:
                assert suggestion.platform.value == post_data["platform"], \
                    "Platform should match"
                assert isinstance(suggestion.confidence_score, float), \
                    "Should have confidence score"
    
    def test_suggestion_export_functionality(self, suggestion_engine, suggestion_context):
        """Test export of suggestions to various formats."""
        # Generate suggestions
        suggestions = suggestion_engine.generate_posting_suggestions(
            context=suggestion_context,
            num_suggestions=5
        )
        
        # Test JSON export
        json_export = suggestion_engine.export_suggestions(
            suggestions=suggestions,
            format="json"
        )
        
        assert isinstance(json_export, str), "JSON export should return string"
        
        # Parse and validate JSON
        parsed_json = json.loads(json_export)
        assert "suggestions" in parsed_json, "Should have suggestions key"
        assert len(parsed_json["suggestions"]) == 5, "Should have all suggestions"
        
        # Test CSV export
        csv_export = suggestion_engine.export_suggestions(
            suggestions=suggestions,
            format="csv"
        )
        
        assert isinstance(csv_export, str), "CSV export should return string"
        assert "platform,content_type,suggested_time" in csv_export, \
            "Should have CSV headers"
        
        # Test calendar export (iCal format simulation)
        calendar_export = suggestion_engine.export_suggestions(
            suggestions=suggestions,
            format="calendar"
        )
        
        assert isinstance(calendar_export, str), "Calendar export should return string"
        assert "BEGIN:VCALENDAR" in calendar_export, "Should be valid calendar format"


class TestBayesianUpdaterComponent:
    """Test suite for Bayesian updating component."""
    
    @pytest.fixture
    def bayesian_updater(self, temp_db_path):
        """Initialize Bayesian updater for testing."""
        return BayesianUpdater(db_path=temp_db_path)
    
    def test_prior_parameter_initialization(self, bayesian_updater):
        """Test initialization of Bayesian priors."""
        priors = bayesian_updater.get_priors(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS
        )
        
        assert isinstance(priors, dict), "Should return priors dictionary"
        assert "mu_0" in priors, "Should have prior mean"
        assert "tau_0" in priors, "Should have prior precision"
        assert "alpha_0" in priors, "Should have prior alpha"
        assert "beta_0" in priors, "Should have prior beta"
        
        # Priors should be positive
        for key, value in priors.items():
            assert value > 0, f"Prior {key} should be positive"
    
    def test_posterior_update(self, bayesian_updater):
        """Test Bayesian posterior update with new data."""
        # Initial priors
        initial_priors = bayesian_updater.get_priors(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO
        )
        
        # New observations
        observations = [
            {'time_hour': 18, 'performance': 0.8},
            {'time_hour': 19, 'performance': 0.75},
            {'time_hour': 20, 'performance': 0.82},
            {'time_hour': 21, 'performance': 0.78}
        ]
        
        # Update posterior
        posterior = bayesian_updater.update_posterior(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            observations=observations
        )
        
        assert isinstance(posterior, dict), "Should return posterior dictionary"
        assert "mu_n" in posterior, "Should have posterior mean"
        assert "tau_n" in posterior, "Should have posterior precision"
        assert "alpha_n" in posterior, "Should have posterior alpha"
        assert "beta_n" in posterior, "Should have posterior beta"
        
        # Updated parameters should be different from priors
        updated_priors = bayesian_updater.get_priors(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO
        )
        
        assert updated_priors != initial_priors, "Priors should be updated"
    
    def test_predictive_distribution(self, bayesian_updater):
        """Test predictive distribution calculation."""
        # Setup with some data
        observations = [
            {'time_hour': hour, 'performance': np.random.beta(2, 3)}
            for hour in range(17, 22)
        ]
        
        bayesian_updater.update_posterior(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            observations=observations
        )
        
        # Get predictive distribution for a specific time
        pred_dist = bayesian_updater.get_predictive_distribution(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            time_hour=18
        )
        
        assert isinstance(pred_dist, dict), "Should return predictive distribution"
        assert "mean" in pred_dist, "Should have predictive mean"
        assert "variance" in pred_dist, "Should have predictive variance"
        assert "confidence_interval" in pred_dist, "Should have confidence interval"
        
        # Mean should be reasonable
        assert 0.0 <= pred_dist["mean"] <= 1.0, "Mean should be in [0,1]"
        
        # Confidence interval should be valid
        lower, upper = pred_dist["confidence_interval"]
        assert 0.0 <= lower <= upper <= 1.0, "CI should be valid [0,1] range"


class TestConstraintResolverComponent:
    """Test suite for constraint resolver component."""
    
    @pytest.fixture
    def constraint_resolver(self):
        """Initialize constraint resolver for testing."""
        return ConstraintResolver()
    
    def test_minimum_gap_constraint_resolution(self, constraint_resolver):
        """Test minimum gap constraint resolution."""
        suggestions = [
            PostingSuggestion(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_REELS,
                suggested_time=datetime.now(timezone.utc) + timedelta(hours=2),
                confidence_score=0.8,
                expected_performance=0.7
            ),
            PostingSuggestion(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_REELS,
                suggested_time=datetime.now(timezone.utc) + timedelta(hours=3),  # 1 hour gap
                confidence_score=0.7,
                expected_performance=0.6
            )
        ]
        
        constraints = {
            'min_gap_hours': 18.0,
            'platform': Platform.INSTAGRAM
        }
        
        resolved = constraint_resolver.resolve_minimum_gap_constraints(
            suggestions=suggestions,
            constraints=constraints
        )
        
        # Should reject one of the suggestions due to gap constraint
        assert len(resolved) <= len(suggestions), "Should not have more suggestions than input"
        
        if len(resolved) > 0:
            # If keeping suggestions, should maintain minimum gaps
            for i in range(1, len(resolved)):
                time_diff = abs((resolved[i].suggested_time - resolved[i-1].suggested_time).total_seconds()) / 3600
                assert time_diff >= constraints['min_gap_hours'], f"Gap {time_diff}h < {constraints['min_gap_hours']}h"
    
    def test_concurrency_limit_resolution(self, constraint_resolver):
        """Test concurrency limit constraint resolution."""
        # Create many suggestions at same time
        same_time = datetime.now(timezone.utc) + timedelta(hours=2)
        suggestions = []
        
        for i in range(5):
            suggestion = PostingSuggestion(
                platform=Platform.TIKTOK,
                content_type=ContentType.TIKTOK_VIDEO,
                suggested_time=same_time,
                confidence_score=0.9 - i * 0.1,
                expected_performance=0.8 - i * 0.1
            )
            suggestions.append(suggestion)
        
        constraints = {
            'max_concurrent_posts': 2,
            'time_window': (same_time - timedelta(hours=1), same_time + timedelta(hours=1))
        }
        
        resolved = constraint_resolver.resolve_concurrency_limits(
            suggestions=suggestions,
            constraints=constraints
        )
        
        # Should limit to max concurrent posts
        assert len(resolved) <= constraints['max_concurrent_posts'], \
            f"Should not exceed max concurrent posts: {len(resolved)} > {constraints['max_concurrent_posts']}"
        
        # Should keep highest confidence suggestions
        if len(resolved) > 0:
            resolved_confidences = [s.confidence_score for s in resolved]
            assert resolved_confidences == sorted(resolved_confidences, reverse=True), \
                "Should keep highest confidence suggestions"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])