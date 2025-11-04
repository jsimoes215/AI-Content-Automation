#!/usr/bin/env python3
"""
Example usage of the Scheduling Optimizer with AI Recommendations

This script demonstrates how to use the scheduling optimizer for:
1. Calculating optimal posting times
2. Generating multi-platform schedules
3. Training ML models for predictions
4. Integrating with batch processing systems
"""

import asyncio
import json
from datetime import datetime, timedelta
from scheduling_optimizer import (
    SchedulingOptimizer, Platform, ContentType, PriorityTier,
    AudienceProfile, SchedulingConstraint, PerformanceMetrics
)


async def demonstrate_basic_timing_scores():
    """Demonstrate basic timing score calculation."""
    print("=" * 60)
    print("BASIC TIMING SCORE CALCULATION")
    print("=" * 60)
    
    optimizer = SchedulingOptimizer()
    
    # Create audience profile
    audience = AudienceProfile(
        age_cohorts={'18-24': 0.3, '25-34': 0.4, '35-44': 0.3},
        device_split={'mobile': 0.7, 'desktop': 0.3},
        time_zone_weights={'UTC-5': 0.5, 'UTC-8': 0.3, 'UTC+0': 0.2}
    )
    
    # Calculate scores for different platforms
    platforms_to_test = [
        (Platform.INSTAGRAM, ContentType.INSTAGRAM_REELS),
        (Platform.TIKTOK, ContentType.TIKTOK_VIDEO),
        (Platform.LINKEDIN, ContentType.LINKEDIN_POST),
        (Platform.YOUTUBE, ContentType.YOUTUBE_SHORTS)
    ]
    
    for platform, content_type in platforms_to_test:
        print(f"\n{platform.value.upper()} - {content_type.value}")
        print("-" * 40)
        
        scores = optimizer.calculate_timing_scores(
            platform=platform,
            content_type=content_type,
            audience_profile=audience,
            day_of_week=2  # Wednesday
        )
        
        # Show top 5 hours
        top_hours = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for hour, score in top_hours:
            time_str = f"{hour:02d}:00"
            bar = "█" * int(score * 20)  # Visual bar
            print(f"  {time_str} │{bar:<20}│ {score:.3f}")


async def demonstrate_schedule_generation():
    """Demonstrate multi-platform schedule generation."""
    print("\n" + "=" * 60)
    print("MULTI-PLATFORM SCHEDULE GENERATION")
    print("=" * 60)
    
    optimizer = SchedulingOptimizer()
    
    # Define posts to schedule
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
        },
        {
            'id': 'post_4',
            'platform': 'linkedin',
            'content_type': 'linkedin_post',
            'priority': PriorityTier.LOW.value,
            'title': 'Industry Insights'
        }
    ]
    
    # Define scheduling constraints
    constraints = [
        SchedulingConstraint(
            Platform.INSTAGRAM, 
            min_gap_hours=18.0, 
            max_concurrent_posts=3
        ),
        SchedulingConstraint(
            Platform.TIKTOK, 
            min_gap_hours=12.0, 
            max_concurrent_posts=3
        ),
        SchedulingConstraint(
            Platform.YOUTUBE, 
            min_gap_hours=48.0, 
            max_concurrent_posts=2
        ),
        SchedulingConstraint(
            Platform.LINKEDIN, 
            min_gap_hours=24.0, 
            max_concurrent_posts=2
        )
    ]
    
    # Create audience profiles
    audience = AudienceProfile(
        age_cohorts={'25-34': 0.4, '35-44': 0.3, '18-24': 0.3},
        device_split={'mobile': 0.7, 'desktop': 0.3},
        time_zone_weights={'UTC-5': 0.5, 'UTC-8': 0.3, 'UTC+0': 0.2}
    )
    
    audience_profiles = {
        Platform.INSTAGRAM: audience,
        Platform.TIKTOK: audience,
        Platform.YOUTUBE: audience,
        Platform.LINKEDIN: audience
    }
    
    # Generate schedule
    schedule = optimizer.generate_optimal_schedule(
        posts=posts,
        constraints=constraints,
        audience_profiles=audience_profiles,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=7),
        max_concurrent=3
    )
    
    print(f"\nGenerated Schedule: {schedule.schedule_id}")
    print(f"Created: {schedule.created_at}")
    print(f"Projected Throughput: {schedule.projected_throughput:.2f} jobs/hour")
    print(f"Quota Compliance: {schedule.quota_compliance_score:.2f}")
    print(f"Schedule Adherence: {schedule.schedule_adherence_score:.2f}")
    
    print("\nJob Assignments:")
    print("-" * 80)
    for i, assignment in enumerate(schedule.job_assignments, 1):
        print(f"{i}. {assignment['platform'].title()} - {assignment['content_type'].replace('_', ' ').title()}")
        print(f"   Scheduled: {assignment['scheduled_time']}")
        print(f"   Timing Score: {assignment['timing_score']:.3f}")
        if assignment.get('constraint_violations'):
            print(f"   ⚠️  Violations: {', '.join(assignment['constraint_violations'])}")
        print()


async def demonstrate_ml_predictions():
    """Demonstrate ML-based timing predictions."""
    print("\n" + "=" * 60)
    print("ML-BASED TIMING PREDICTIONS")
    print("=" * 60)
    
    optimizer = SchedulingOptimizer()
    
    # Create audience profile
    audience = AudienceProfile(
        age_cohorts={'25-34': 0.5, '35-44': 0.3, '18-24': 0.2},
        device_split={'mobile': 0.8, 'desktop': 0.2},
        time_zone_weights={'UTC-5': 0.6, 'UTC-8': 0.4}
    )
    
    # Train ML models (simulated - would need real data)
    print("Training ML models...")
    model_scores = await optimizer.train_ml_models()
    
    if model_scores:
        print("Model Training Results:")
        for platform, scores in model_scores.items():
            print(f"  {platform}: Train R² = {scores['train_r2']:.3f}, Test R² = {scores['test_r2']:.3f}")
    else:
        print("⚠️  Insufficient training data - using rule-based predictions")
    
    # Get predictions for TikTok
    print(f"\nTikTok Optimal Times (Next 7 Days):")
    print("-" * 40)
    predictions = optimizer.predict_optimal_times(
        platform=Platform.TIKTOK,
        content_type=ContentType.TIKTOK_VIDEO,
        audience_profile=audience,
        num_predictions=5
    )
    
    for i, pred in enumerate(predictions, 1):
        dt = pred['datetime']
        score = pred['predicted_score']
        day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dt.weekday()]
        method = "🤖 ML" if pred['method'] == 'ml_prediction' else "📋 Rule-based"
        
        print(f"{i}. {day_name} {dt.strftime('%m/%d %H:%M')} │ Score: {score:.3f} │ {method}")


async def demonstrate_batch_integration():
    """Demonstrate integration with batch processing system."""
    print("\n" + "=" * 60)
    print("BATCH PROCESSING INTEGRATION")
    print("=" * 60)
    
    optimizer = SchedulingOptimizer()
    
    # Define bulk job posts
    posts = [
        {
            'id': 'bulk_post_1',
            'platform': 'instagram',
            'content_type': 'instagram_feed',
            'priority': PriorityTier.NORMAL.value
        },
        {
            'id': 'bulk_post_2',
            'platform': 'instagram',
            'content_type': 'instagram_reels',
            'priority': PriorityTier.NORMAL.value
        },
        {
            'id': 'bulk_post_3',
            'platform': 'twitter',
            'content_type': 'twitter_post',
            'priority': PriorityTier.LOW.value
        }
    ]
    
    # Define scheduling metadata
    scheduling_metadata = {
        'start_after': (datetime.now() + timedelta(hours=2)).isoformat(),
        'deadline': (datetime.now() + timedelta(days=3)).isoformat(),
        'suggested_concurrency': 3,
        'max_parallelism': 3,
        'ai_provider_prefs': ['provider_a', 'provider_b']
    }
    
    # Generate schedule for bulk job
    schedule_plan = optimizer.integrate_with_batch_system(
        bulk_job_id="bulk_job_12345",
        posts=posts,
        scheduling_metadata=scheduling_metadata
    )
    
    print(f"Bulk Job ID: {schedule_plan.bulk_job_id}")
    print(f"Schedule ID: {schedule_plan.schedule_id}")
    print(f"Created: {schedule_plan.created_at}")
    
    print("\nDispatch Plan:")
    print("-" * 60)
    for assignment in schedule_plan.job_assignments:
        print(f"📅 {assignment['scheduled_time']}")
        print(f"   Platform: {assignment['platform'].title()}")
        print(f"   Content: {assignment['content_type'].replace('_', ' ').title()}")
        print(f"   Score: {assignment['timing_score']:.3f}")
        print()


async def demonstrate_performance_tracking():
    """Demonstrate performance tracking and optimization."""
    print("\n" + "=" * 60)
    print("PERFORMANCE TRACKING & ADAPTIVE OPTIMIZATION")
    print("=" * 60)
    
    optimizer = SchedulingOptimizer()
    
    # Record some example performance metrics
    print("Recording example performance metrics...")
    
    metrics_examples = [
        PerformanceMetrics(
            platform=Platform.INSTAGRAM,
            content_type=ContentType.INSTAGRAM_REELS,
            posted_at=datetime.now() - timedelta(hours=2),
            reach=1500,
            engagement_rate=0.045,
            watch_time=45.2,
            completion_rate=0.78,
            saves=23,
            shares=15,
            comments=8,
            is_successful=True
        ),
        PerformanceMetrics(
            platform=Platform.TIKTOK,
            content_type=ContentType.TIKTOK_VIDEO,
            posted_at=datetime.now() - timedelta(hours=5),
            reach=3200,
            engagement_rate=0.067,
            watch_time=78.5,
            completion_rate=0.85,
            saves=45,
            shares=32,
            comments=12,
            is_successful=True
        ),
        PerformanceMetrics(
            platform=Platform.LINKEDIN,
            content_type=ContentType.LINKEDIN_POST,
            posted_at=datetime.now() - timedelta(hours=8),
            reach=800,
            engagement_rate=0.032,
            ctr=0.025,
            saves=12,
            shares=8,
            comments=5,
            is_successful=False  # Below threshold
        )
    ]
    
    for metrics in metrics_examples:
        optimizer.record_performance_metrics(metrics)
        print(f"✓ Recorded {metrics.platform.value} performance")
    
    # Run adaptive optimization cycle
    print("\nRunning adaptive optimization cycle...")
    cycle_results = await optimizer.adaptive_optimization_cycle()
    
    print(f"Cycle started: {cycle_results['started_at']}")
    
    if cycle_results['measurements']:
        print("\nPerformance Measurements:")
        measurements = cycle_results['measurements']
        if 'throughput' in measurements:
            throughput = measurements['throughput']
            print(f"  Throughput: {throughput.get('jobs_per_hour', 0):.2f} jobs/hour")
    
    if cycle_results['analysis'].get('recommendations'):
        print("\nRecommendations:")
        for rec in cycle_results['analysis']['recommendations']:
            print(f"  • {rec}")


async def demonstrate_platform_recommendations():
    """Demonstrate platform-specific recommendations."""
    print("\n" + "=" * 60)
    print("PLATFORM-SPECIFIC RECOMMENDATIONS")
    print("=" * 60)
    
    optimizer = SchedulingOptimizer()
    
    platforms_to_analyze = [Platform.INSTAGRAM, Platform.TIKTOK, Platform.LINKEDIN]
    
    for platform in platforms_to_analyze:
        print(f"\n{platform.value.upper()} RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = optimizer.get_schedule_recommendations(platform)
        
        print(f"Platform: {recommendations['platform'].title()}")
        
        if recommendations['top_posting_slots']:
            print("\nTop Performing Times:")
            for slot in recommendations['top_posting_slots'][:5]:
                success_rate = slot['success_rate']
                sample_count = slot['sample_count']
                print(f"  • {slot['day_name']} at {slot['time_str']}: "
                      f"{success_rate:.1%} success ({sample_count} samples)")
        
        if recommendations['recommendations']:
            print("\nAI Recommendations:")
            for rec in recommendations['recommendations']:
                print(f"  📌 {rec}")
        
        if recommendations['ml_insights'].get('feature_importance'):
            print("\nTop Predictive Features:")
            for feature, importance in recommendations['ml_insights']['feature_importance'][:3]:
                print(f"  🔍 {feature}: {importance:.3f}")


async def main():
    """Run all demonstration examples."""
    print("🚀 SCHEDULING OPTIMIZER WITH AI RECOMMENDATIONS")
    print("=" * 60)
    print("This example demonstrates the complete functionality of the")
    print("scheduling optimizer including timing calculations, ML predictions,")
    print("multi-platform coordination, and batch integration.")
    print()
    
    try:
        # Run all demonstrations
        await demonstrate_basic_timing_scores()
        await demonstrate_schedule_generation()
        await demonstrate_ml_predictions()
        await demonstrate_batch_integration()
        await demonstrate_performance_tracking()
        await demonstrate_platform_recommendations()
        
        print("\n" + "=" * 60)
        print("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Configure your audience profiles with real demographic data")
        print("2. Train ML models with your historical performance data")
        print("3. Set up batch integration with your content management system")
        print("4. Monitor performance and let the adaptive optimization cycle improve scheduling")
        print("5. Use platform recommendations to inform content strategy")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())