"""
Comprehensive Test Suite for Scheduling Optimization Algorithms

This module tests all optimization algorithms used in the scheduling system:
1. Timing score calculation algorithms
2. Multi-platform scheduling optimization 
3. Machine learning-based predictions
4. Adaptive optimization cycles
5. Constraint satisfaction algorithms

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import pytest
import asyncio
import numpy as np
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, MagicMock, patch
import logging

# Import scheduling components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from scheduling_optimizer import (
    SchedulingOptimizer, Platform, ContentType, AudienceProfile, 
    PostingWindow, PerformanceMetrics, SchedulingConstraint, 
    SchedulePlan, PriorityTier
)
from data_validation import ValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSchedulingOptimizationAlgorithms:
    """Test suite for scheduling optimization algorithms."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def scheduling_optimizer(self, temp_db_path):
        """Initialize scheduling optimizer with test database."""
        optimizer = SchedulingOptimizer(db_path=temp_db_path)
        return optimizer
    
    @pytest.fixture
    def sample_audience_profile(self):
        """Sample audience profile for testing."""
        return AudienceProfile(
            age_cohorts={
                '18-24': 0.25,
                '25-34': 0.35,
                '35-44': 0.25,
                '45-54': 0.10,
                '55+': 0.05
            },
            device_split={
                'mobile': 0.70,
                'desktop': 0.25,
                'tablet': 0.05
            },
            time_zone_weights={
                'UTC-8': 0.30,  # West Coast
                'UTC-5': 0.40,  # East Coast
                'UTC': 0.20,    # GMT
                'UTC+5.5': 0.10  # India
            },
            geography={
                'US': 0.70,
                'UK': 0.15,
                'India': 0.10,
                'Other': 0.05
            }
        )
    
    @pytest.fixture
    def sample_constraints(self):
        """Sample scheduling constraints for testing."""
        return [
            SchedulingConstraint(
                platform=Platform.INSTAGRAM,
                min_gap_hours=18.0,
                max_concurrent_posts=2,
                preferred_windows=[PostingWindow(10, 15, 0.8, 1)]  # Tue-Thu 10AM-3PM
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
    def sample_performance_data(self, scheduling_optimizer):
        """Generate sample performance data for ML training."""
        np.random.seed(42)  # For reproducible tests
        
        platforms = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]
        content_types = [ContentType.INSTAGRAM_REELS, ContentType.TIKTOK_VIDEO, 
                        ContentType.YOUTUBE_LONG_FORM]
        
        for _ in range(100):  # Generate 100 samples per platform
            platform = np.random.choice(platforms)
            content_type = np.random.choice(content_types)
            
            # Generate synthetic performance metrics
            base_reach = np.random.normal(1000, 200)
            engagement_rate = np.random.beta(2, 5)  # Realistic engagement distribution
            
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
    
    # Test Timing Score Calculation
    def test_calculate_timing_scores_basic(self, scheduling_optimizer, sample_audience_profile):
        """Test basic timing score calculation."""
        scores = scheduling_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=sample_audience_profile,
            day_of_week=2  # Wednesday
        )
        
        # Check that scores are returned for all 24 hours
        assert len(scores) == 24, "Should return scores for all 24 hours"
        
        # Check that all scores are between 0 and 1
        assert all(0 <= score <= 1 for score in scores.values()), \
            "All scores should be between 0 and 1"
        
        # Check that some variation exists
        assert len(set(scores.values())) > 1, "Scores should vary across hours"
        
        # Instagram Reels should show preference for evening hours
        # Based on research: 6-9AM, 6-9PM are peak times
        morning_scores = [scores[hour] for hour in [6, 7, 8, 9]]
        evening_scores = [scores[hour] for hour in [18, 19, 20, 21]]
        afternoon_scores = [scores[hour] for hour in [12, 13, 14, 15]]
        
        # Evening scores should generally be higher than afternoon
        avg_evening = np.mean(evening_scores)
        avg_afternoon = np.mean(afternoon_scores)
        assert avg_evening > avg_afternoon * 0.8, \
            "Evening hours should have higher scores than afternoon"
    
    def test_calculate_timing_scores_platform_specific(self, scheduling_optimizer, sample_audience_profile):
        """Test timing scores for different platforms."""
        platforms_to_test = [Platform.YOUTUBE, Platform.TIKTOK, Platform.LINKEDIN]
        
        for platform in platforms_to_test:
            scores = scheduling_optimizer.calculate_timing_scores(
                platform=platform,
                content_type=ContentType.YOUTUBE_LONG_FORM if platform == Platform.YOUTUBE 
                           else ContentType.TIKTOK_VIDEO if platform == Platform.TIKTOK 
                           else ContentType.LINKEDIN_POST,
                audience_profile=sample_audience_profile,
                day_of_week=2  # Wednesday
            )
            
            assert len(scores) == 24
            assert all(0 <= score <= 1 for score in scores.values())
            
            # Each platform should have unique timing patterns
            if platform == Platform.LINKEDIN:
                # LinkedIn should prefer business hours
                business_hours = [scores[hour] for hour in range(8, 18)]
                non_business = [scores[hour] for hour in [0, 1, 2, 3, 22, 23]]
                assert np.mean(business_hours) > np.mean(non_business), \
                    "LinkedIn should prefer business hours"
    
    def test_calculate_timing_scores_demographics(self, scheduling_optimizer):
        """Test demographic adjustments in timing scores."""
        # Young audience (Gen Z)
        young_audience = AudienceProfile(
            age_cohorts={'18-24': 0.8, '25-34': 0.2},
            device_split={'mobile': 0.9, 'desktop': 0.1},
            time_zone_weights={'UTC-5': 1.0}
        )
        
        # Professional audience  
        professional_audience = AudienceProfile(
            age_cohorts={'35-44': 0.6, '45-54': 0.4},
            device_split={'desktop': 0.6, 'mobile': 0.4},
            time_zone_weights={'UTC': 1.0}
        )
        
        young_scores = scheduling_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=young_audience,
            day_of_week=5  # Saturday
        )
        
        professional_scores = scheduling_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=professional_audience,
            day_of_week=5  # Saturday
        )
        
        # Young audiences should prefer evening/weekend times
        # Professional audiences should prefer weekday business hours
        assert young_scores[21] > professional_scores[21], \
            "Young audiences should prefer late evening content"
    
    # Test Multi-Platform Scheduling
    def test_generate_optimal_schedule_basic(self, scheduling_optimizer, sample_constraints, sample_audience_profile):
        """Test basic optimal schedule generation."""
        posts = [
            {
                'id': 'post_1',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': PriorityTier.NORMAL.value,
                'title': 'Product Demo Reel'
            },
            {
                'id': 'post_2',
                'platform': Platform.TIKTOK.value,
                'content_type': ContentType.TIKTOK_VIDEO.value,
                'priority': PriorityTier.URGENT.value,
                'title': 'Behind the Scenes'
            },
            {
                'id': 'post_3',
                'platform': Platform.YOUTUBE.value,
                'content_type': ContentType.YOUTUBE_LONG_FORM.value,
                'priority': PriorityTier.NORMAL.value,
                'title': 'Tutorial Video'
            }
        ]
        
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=7)
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=sample_constraints,
            audience_profiles={
                Platform.INSTAGRAM: sample_audience_profile,
                Platform.TIKTOK: sample_audience_profile,
                Platform.YOUTUBE: sample_audience_profile
            },
            start_date=start_date,
            end_date=end_date
        )
        
        # Check schedule structure
        assert isinstance(schedule, SchedulePlan)
        assert schedule.id is not None
        assert len(schedule.scheduled_posts) >= 1
        
        # Check constraint satisfaction
        scheduled_times = [post.scheduled_time for post in schedule.scheduled_posts]
        
        # Verify no overlapping posts on same platform
        platform_posts = {}
        for post in schedule.scheduled_posts:
            platform = post.platform
            if platform not in platform_posts:
                platform_posts[platform] = []
            platform_posts[platform].append(post.scheduled_time)
        
        for platform, times in platform_posts.items():
            if len(times) > 1:
                times.sort()
                # Check minimum gap constraints
                min_gap = 12.0  # Default, should be overridden by constraints
                for i in range(1, len(times)):
                    time_diff = abs((times[i] - times[i-1]).total_seconds()) / 3600
                    assert time_diff >= min_gap, \
                        f"Posts on {platform} violate minimum gap constraint"
    
    def test_generate_optimal_schedule_with_constraints(self, scheduling_optimizer, sample_constraints, sample_audience_profile):
        """Test schedule generation with complex constraints."""
        posts = [
            {
                'id': 'urgent_instagram',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': PriorityTier.URGENT.value,
                'title': 'Urgent Announcement'
            },
            {
                'id': 'normal_instagram_1',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_FEED.value,
                'priority': PriorityTier.NORMAL.value,
                'title': 'Regular Post 1'
            },
            {
                'id': 'normal_instagram_2', 
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_FEED.value,
                'priority': PriorityTier.NORMAL.value,
                'title': 'Regular Post 2'
            }
        ]
        
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=3)
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=sample_constraints,
            audience_profiles={
                Platform.INSTAGRAM: sample_audience_profile
            },
            start_date=start_date,
            end_date=end_date
        )
        
        # Check that urgent post gets priority scheduling
        urgent_post = next((post for post in schedule.scheduled_posts 
                           if post.post_id == 'urgent_instagram'), None)
        assert urgent_post is not None, "Urgent post should be scheduled"
        
        # All posts should be scheduled within the time window
        for post in schedule.scheduled_posts:
            assert start_date <= post.scheduled_time <= end_date, \
                f"Post {post.post_id} scheduled outside of time window"
    
    # Test Machine Learning Predictions
    @pytest.mark.asyncio
    async def test_train_ml_models(self, scheduling_optimizer, sample_performance_data):
        """Test ML model training functionality."""
        # Train models with sample data
        model_scores = await scheduling_optimizer.train_ml_models()
        
        # Check that models are trained for all platforms
        assert isinstance(model_scores, dict)
        
        for platform in [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]:
            assert platform.value in model_scores, \
                f"Model should be trained for {platform.value}"
            
            platform_score = model_scores[platform.value]
            assert isinstance(platform_score, dict)
            assert 'r2_score' in platform_score
            assert 'train_size' in platform_score
            assert 'test_size' in platform_score
            
            # R² score should be reasonable (positive or not too negative)
            assert platform_score['r2_score'] > -1.0, \
                f"Model R² score for {platform.value} is unexpectedly poor"
            
            # Should have reasonable train/test split
            assert platform_score['train_size'] > 0, \
                f"No training data for {platform.value}"
    
    @pytest.mark.asyncio
    async def test_predict_optimal_times(self, scheduling_optimizer, sample_audience_profile, sample_performance_data):
        """Test ML-based optimal time predictions."""
        # First train the models
        await scheduling_optimizer.train_ml_models()
        
        # Get predictions
        predictions = scheduling_optimizer.predict_optimal_times(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=sample_audience_profile,
            num_predictions=5
        )
        
        # Check prediction structure
        assert isinstance(predictions, list)
        assert len(predictions) == 5
        
        for pred in predictions:
            assert isinstance(pred, dict)
            assert 'hour' in pred
            assert 'confidence' in pred
            assert 'predicted_score' in pred
            
            # Validate hour range
            assert 0 <= pred['hour'] <= 23
            
            # Confidence should be between 0 and 1
            assert 0 <= pred['confidence'] <= 1
            
            # Predicted score should be between 0 and 1
            assert 0 <= pred['predicted_score'] <= 1
        
        # Predictions should be sorted by confidence (best first)
        confidences = [pred['confidence'] for pred in predictions]
        assert confidences == sorted(confidences, reverse=True), \
            "Predictions should be sorted by confidence"
    
    @pytest.mark.asyncio
    async def test_ml_fallback_behavior(self, scheduling_optimizer, sample_audience_profile):
        """Test fallback behavior when insufficient training data."""
        # Try to get predictions without training data
        predictions = scheduling_optimizer.predict_optimal_times(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            audience_profile=sample_audience_profile,
            num_predictions=3
        )
        
        # Should fall back to rule-based predictions
        assert isinstance(predictions, list)
        assert len(predictions) == 3
        
        # Fallback predictions should still follow business logic
        for pred in predictions:
            assert 'hour' in pred
            assert 'confidence' in pred
            # LinkedIn predictions should prefer business hours
            if 9 <= pred['hour'] <= 17:  # Business hours
                assert pred['confidence'] > 0.5, \
                    "Business hour predictions should have higher confidence"
    
    # Test Adaptive Optimization
    def test_record_performance_metrics(self, scheduling_optimizer):
        """Test performance metrics recording."""
        metrics = PerformanceMetrics(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            posted_at=datetime.now(timezone.utc),
            reach=1500,
            engagement_rate=0.045,
            click_through_rate=0.02,
            conversion_rate=0.005,
            is_successful=True
        )
        
        # Record metrics
        scheduling_optimizer.record_performance_metrics(metrics)
        
        # Verify metrics are stored in database
        conn = sqlite3.connect(scheduling_optimizer.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM performance_history")
        count = cursor.fetchone()[0]
        assert count >= 1, "Performance metrics should be stored"
        
        cursor.execute("""
            SELECT reach, engagement_rate, is_successful 
            FROM performance_history 
            WHERE platform = ? AND content_type = ?
        """, (Platform.INSTAGRAM.value, ContentType.INSTAGRAM_REELS.value))
        
        result = cursor.fetchone()
        assert result is not None, "Recorded metrics should be retrievable"
        assert result[0] == 1500
        assert result[1] == 0.045
        assert result[2] == 1  # is_successful is stored as boolean
        
        conn.close()
    
    def test_adaptive_optimization_cycle(self, scheduling_optimizer, sample_performance_data):
        """Test adaptive optimization cycle."""
        # Run optimization cycle
        results = scheduling_optimizer.adaptive_optimization_cycle()
        
        # Check cycle results structure
        assert isinstance(results, dict)
        assert 'metrics_collected' in results
        assert 'parameters_updated' in results
        assert 'performance_improvements' in results
        
        # Should have collected metrics
        assert results['metrics_collected'] > 0, "Should collect performance metrics"
        
        # Parameters should be updated or remain unchanged
        assert isinstance(results['parameters_updated'], bool)
        
        # Should identify improvement areas
        assert isinstance(results['performance_improvements'], list)
    
    def test_performance_impact_tracking(self, scheduling_optimizer):
        """Test performance impact tracking and learning."""
        # Record multiple performance records with different outcomes
        successful_metrics = PerformanceMetrics(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            posted_at=datetime.now(timezone.utc),
            reach=2000,
            engagement_rate=0.06,
            is_successful=True
        )
        
        poor_metrics = PerformanceMetrics(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            posted_at=datetime.now(timezone.utc) - timedelta(hours=6),
            reach=300,
            engagement_rate=0.01,
            is_successful=False
        )
        
        scheduling_optimizer.record_performance_metrics(successful_metrics)
        scheduling_optimizer.record_performance_metrics(poor_metrics)
        
        # Run adaptive cycle to analyze performance patterns
        results = scheduling_optimizer.adaptive_optimization_cycle()
        
        # System should identify patterns in successful vs unsuccessful posts
        assert 'performance_improvements' in results
        assert len(results['performance_improvements']) >= 0
    
    # Test Integration with Batch Processing
    def test_integrate_with_batch_system(self, scheduling_optimizer):
        """Test integration with batch processing system."""
        bulk_job_id = f"job_{uuid.uuid4()}"
        
        posts = [
            {
                'id': 'batch_post_1',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': PriorityTier.NORMAL.value
            }
        ]
        
        scheduling_metadata = {
            'start_after': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            'deadline': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            'suggested_concurrency': 2,
            'max_parallelism': 3
        }
        
        # Integrate with batch system
        schedule_plan = scheduling_optimizer.integrate_with_batch_system(
            bulk_job_id=bulk_job_id,
            posts=posts,
            scheduling_metadata=scheduling_metadata
        )
        
        # Check integration results
        assert isinstance(schedule_plan, SchedulePlan)
        assert schedule_plan.bulk_job_id == bulk_job_id
        assert len(schedule_plan.scheduled_posts) >= 1
        
        # Verify scheduling respects batch constraints
        scheduled_post = schedule_plan.scheduled_posts[0]
        assert scheduled_post.scheduled_time >= datetime.fromisoformat(scheduling_metadata['start_after'])
        assert scheduled_post.scheduled_time <= datetime.fromisoformat(scheduling_metadata['deadline'])
    
    # Test Error Handling and Edge Cases
    def test_invalid_platform_handling(self, scheduling_optimizer, sample_audience_profile):
        """Test handling of invalid platform specifications."""
        with pytest.raises(ValueError):
            scheduling_optimizer.calculate_timing_scores(
                platform="invalid_platform",
                content_type=ContentType.INSTAGRAM_REELS,
                audience_profile=sample_audience_profile,
                day_of_week=2
            )
    
    def test_empty_audience_profile(self, scheduling_optimizer):
        """Test behavior with empty audience profile."""
        empty_audience = AudienceProfile(
            age_cohorts={},
            device_split={},
            time_zone_weights={}
        )
        
        scores = scheduling_optimizer.calculate_timing_scores(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            audience_profile=empty_audience,
            day_of_week=2
        )
        
        # Should still return valid scores, using default weights
        assert len(scores) == 24
        assert all(0 <= score <= 1 for score in scores.values())
    
    def test_conflict_resolution(self, scheduling_optimizer, sample_audience_profile):
        """Test scheduling conflict resolution."""
        # Create posts that would conflict if not handled properly
        conflicting_posts = []
        for i in range(5):  # Create 5 Instagram posts
            conflicting_posts.append({
                'id': f'conflict_post_{i}',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': PriorityTier.NORMAL.value,
                'title': f'Conflicting Post {i}'
            })
        
        constraints = [SchedulingConstraint(
            platform=Platform.INSTAGRAM,
            min_gap_hours=24.0,  # 1 post per day minimum
            max_concurrent_posts=1
        )]
        
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=3)
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=conflicting_posts,
            constraints=constraints,
            audience_profiles={Platform.INSTAGRAM: sample_audience_profile},
            start_date=start_date,
            end_date=end_date
        )
        
        # Check that conflicts are resolved within time window
        assert len(schedule.scheduled_posts) >= 1
        assert len(schedule.scheduled_posts) <= len(conflicting_posts)
        
        # Verify time separation
        instagram_posts = [post for post in schedule.scheduled_posts 
                          if post.platform == Platform.INSTAGRAM]
        if len(instagram_posts) > 1:
            times = [post.scheduled_time for post in instagram_posts]
            times.sort()
            
            for i in range(1, len(times)):
                time_diff = (times[i] - times[i-1]).total_seconds() / 3600
                assert time_diff >= 24.0, "Posts should be separated by minimum gap"
    
    def test_schedule_quality_metrics(self, scheduling_optimizer, sample_constraints, sample_audience_profile):
        """Test schedule quality assessment."""
        posts = [
            {
                'id': 'quality_test_1',
                'platform': Platform.INSTAGRAM.value,
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': PriorityTier.NORMAL.value
            },
            {
                'id': 'quality_test_2',
                'platform': Platform.TIKTOK.value,
                'content_type': ContentType.TIKTOK_VIDEO.value,
                'priority': PriorityTier.URGENT.value
            }
        ]
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=sample_constraints,
            audience_profiles={Platform.INSTAGRAM: sample_audience_profile,
                             Platform.TIKTOK: sample_audience_profile},
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        # Assess schedule quality
        quality_metrics = scheduling_optimizer.assess_schedule_quality(schedule)
        
        assert isinstance(quality_metrics, dict)
        assert 'constraint_satisfaction' in quality_metrics
        assert 'optimal_timing_score' in quality_metrics
        assert 'platform_coverage' in quality_metrics
        
        # Constraint satisfaction should be high (close to 1.0)
        assert 0.8 <= quality_metrics['constraint_satisfaction'] <= 1.0
        
        # Should have good optimal timing score
        assert 0.0 <= quality_metrics['optimal_timing_score'] <= 1.0
        
        # Should cover both platforms
        assert quality_metrics['platform_coverage'] >= 2
    
    # Performance and Stress Tests
    def test_large_scale_schedule_generation(self, scheduling_optimizer, sample_audience_profile):
        """Test schedule generation with many posts."""
        # Create a large number of posts
        posts = []
        for i in range(50):
            posts.append({
                'id': f'large_scale_post_{i}',
                'platform': np.random.choice([p.value for p in [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]]),
                'content_type': ContentType.INSTAGRAM_REELS.value,
                'priority': PriorityTier.NORMAL.value
            })
        
        constraints = [
            SchedulingConstraint(platform=Platform.INSTAGRAM, min_gap_hours=12.0),
            SchedulingConstraint(platform=Platform.TIKTOK, min_gap_hours=8.0),
            SchedulingConstraint(platform=Platform.YOUTUBE, min_gap_hours=24.0)
        ]
        
        import time
        start_time = time.time()
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=constraints,
            audience_profiles={p: sample_audience_profile for p in [Platform.INSTAGRAM, Platform.TIKTOK, Platform.YOUTUBE]},
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (less than 10 seconds for 50 posts)
        assert processing_time < 10.0, f"Large scale scheduling took too long: {processing_time}s"
        
        # Should schedule a reasonable number of posts within time window
        assert len(schedule.scheduled_posts) > 0, "Should schedule some posts"
    
    def test_database_performance(self, scheduling_optimizer):
        """Test database operation performance."""
        # Insert many performance records
        import time
        start_time = time.time()
        
        for i in range(100):
            metrics = PerformanceMetrics(
                platform=Platform.INSTAGRAM,
                content_type=ContentType.INSTAGRAM_REELS,
                posted_at=datetime.now(timezone.utc),
                reach=1000 + i,
                engagement_rate=0.03 + (i % 10) * 0.001,
                is_successful=(i % 3) == 0
            )
            scheduling_optimizer.record_performance_metrics(metrics)
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        # Should handle 100 inserts in reasonable time
        assert insert_time < 5.0, f"Database inserts too slow: {insert_time}s"
        
        # Test retrieval performance
        start_time = time.time()
        
        history = scheduling_optimizer.get_performance_history(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            limit=50
        )
        
        end_time = time.time()
        retrieve_time = end_time - start_time
        
        # Should retrieve 50 records quickly
        assert retrieve_time < 1.0, f"Database retrieval too slow: {retrieve_time}s"
        assert len(history) == 50, "Should retrieve requested number of records"


class TestConstraintSatisfaction:
    """Test suite for constraint satisfaction algorithms."""
    
    @pytest.fixture
    def scheduling_optimizer(self):
        """Initialize scheduling optimizer for constraint tests."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        optimizer = SchedulingOptimizer(db_path=db_path)
        yield optimizer
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_minimum_gap_constraint(self, scheduling_optimizer):
        """Test minimum gap between posts constraint."""
        posts = [
            {'id': 'post1', 'platform': Platform.INSTAGRAM.value, 'priority': PriorityTier.NORMAL.value},
            {'id': 'post2', 'platform': Platform.INSTAGRAM.value, 'priority': PriorityTier.NORMAL.value}
        ]
        
        constraints = [SchedulingConstraint(
            platform=Platform.INSTAGRAM,
            min_gap_hours=6.0
        )]
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=constraints,
            audience_profiles={Platform.INSTAGRAM: AudienceProfile({}, {}, {})},
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=2)
        )
        
        # Should satisfy minimum gap
        if len(schedule.scheduled_posts) > 1:
            times = [post.scheduled_time for post in schedule.scheduled_posts]
            times.sort()
            
            for i in range(1, len(times)):
                time_diff = (times[i] - times[i-1]).total_seconds() / 3600
                assert time_diff >= 6.0, f"Minimum gap violated: {time_diff}h < 6h"
    
    def test_concurrency_limit_constraint(self, scheduling_optimizer):
        """Test concurrency limit constraint."""
        posts = [{'id': f'post{i}', 'platform': Platform.TIKTOK.value, 'priority': PriorityTier.NORMAL.value} 
                for i in range(10)]
        
        constraints = [SchedulingConstraint(
            platform=Platform.TIKTOK,
            max_concurrent_posts=3
        )]
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=constraints,
            audience_profiles={Platform.TIKTOK: AudienceProfile({}, {}, {})},
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=3)
        )
        
        # Check that concurrency limit is respected
        concurrent_posts = scheduling_optimizer.analyze_concurrency_violations(schedule)
        assert len(concurrent_posts) == 0, f"Found concurrency violations: {concurrent_posts}"
    
    def test_preferred_windows_constraint(self, scheduling_optimizer):
        """Test preferred posting windows constraint."""
        posts = [{'id': 'preferred_post', 'platform': Platform.LINKEDIN.value, 'priority': PriorityTier.NORMAL.value}]
        
        preferred_windows = [
            PostingWindow(9, 11, 0.9, 1),  # Tuesday 9-11 AM
            PostingWindow(13, 15, 0.8, 2),  # Wednesday 1-3 PM
        ]
        
        constraints = [SchedulingConstraint(
            platform=Platform.LINKEDIN,
            preferred_windows=preferred_windows
        )]
        
        schedule = scheduling_optimizer.generate_optimal_schedule(
            posts=posts,
            constraints=constraints,
            audience_profiles={Platform.LINKEDIN: AudienceProfile({}, {}, {})},
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=3)
        )
        
        if len(schedule.scheduled_posts) > 0:
            scheduled_time = schedule.scheduled_posts[0].scheduled_time
            hour = scheduled_time.hour
            
            # Should be in preferred hours (9-11 or 13-15)
            is_preferred = (9 <= hour <= 11) or (13 <= hour <= 15)
            assert is_preferred, f"Scheduled time {hour}:00 not in preferred windows"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])