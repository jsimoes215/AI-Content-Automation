"""
Content Calendar Integration System Demo

This script demonstrates the content calendar integration system in action,
showing how to integrate with the bulk job workflow and use analytics features.

Author: AI Content Automation System
Version: 1.0.0
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json

# Add the code directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Handle import dependencies gracefully
try:
    from content_calendar import (
        ContentCalendarManager, ScheduleGenerator, CrossPlatformCoordinator,
        CalendarAnalyticsEngine, PlatformId, ContentFormat, ScheduleStatus,
        UserSchedulingPreferences, integrate_with_bulk_job_workflow,
        create_optimization_trial
    )
    
    # Define minimal Job classes for demo if batch_processor not available
    class JobStatus:
        QUEUED = "queued"
    
    class JobPriority:
        NORMAL = 5
    
    class VideoJob:
        def __init__(self, id, bulk_job_id, idea_data, status, priority, ai_provider, cost=Decimal('0.00'), 
                     created_at=None, updated_at=None):
            self.id = id
            self.bulk_job_id = bulk_job_id
            self.idea_data = idea_data
            self.status = status
            self.priority = priority
            self.ai_provider = ai_provider
            self.cost = cost
            self.created_at = created_at or datetime.now(timezone.utc)
            self.updated_at = updated_at or datetime.now(timezone.utc)
    
    class BulkJob:
        def __init__(self, id, sheet_id, total_jobs, completed_jobs, failed_jobs, total_cost, status,
                     created_at=None, updated_at=None):
            self.id = id
            self.sheet_id = sheet_id
            self.total_jobs = total_jobs
            self.completed_jobs = completed_jobs
            self.failed_jobs = failed_jobs
            self.total_cost = total_cost
            self.status = status
            self.created_at = created_at or datetime.now(timezone.utc)
            self.updated_at = updated_at or datetime.now(timezone.utc)
            
except ImportError as e:
    print(f"Import error: {e}")
    print("Running minimal demo without full dependencies...")


def demo_content_calendar_integration():
    """Demonstrate the complete content calendar integration workflow."""
    print("🎬 Content Calendar Integration System Demo")
    print("=" * 50)
    
    # Initialize the content calendar manager
    print("\n1. Initializing Content Calendar Manager...")
    calendar_manager = ContentCalendarManager("demo_content_calendar.db")
    
    # Create user scheduling preferences
    print("\n2. Setting up user scheduling preferences...")
    user_prefs = UserSchedulingPreferences(
        user_id="demo_user_123",
        platform_id=PlatformId.YOUTUBE,
        timezone="America/New_York",
        posting_frequency_min=2,
        posting_frequency_max=4,
        days_blacklist=["sat", "sun"],  # No weekend posting
        quality_threshold=0.03  # Minimum 3% engagement rate
    )
    calendar_manager.set_user_scheduling_preferences(user_prefs)
    print(f"✅ Set preferences: {user_prefs.posting_frequency_min}-{user_prefs.posting_frequency_max} posts/week")
    
    # Simulate bulk job creation (like from Google Sheets)
    print("\n3. Creating bulk job from Google Sheets data...")
    bulk_job = BulkJob(
        id="demo_bulk_789",
        sheet_id="sheets_abc123",
        total_jobs=5,
        completed_jobs=0,
        failed_jobs=0,
        total_cost=Decimal('50.00'),
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Create video jobs from bulk job
    print("\n4. Generating video jobs from bulk job...")
    video_ideas = [
        {"title": "AI Tools for Content Creation", "description": "Best AI tools for creating engaging content", "target_audience": "Content creators"},
        {"title": "Video Marketing Strategies", "description": "Effective video marketing tactics for 2025", "target_audience": "Marketers"},
        {"title": "Social Media Optimization", "description": "Optimize your social media presence", "target_audience": "Businesses"},
        {"title": "YouTube Channel Growth", "description": "Tips to grow your YouTube channel", "target_audience": "YouTubers"},
        {"title": "TikTok Algorithm Secrets", "description": "Understanding TikTok's algorithm", "target_audience": "TikTok creators"}
    ]
    
    video_jobs = []
    for i, idea in enumerate(video_ideas):
        video_job = VideoJob(
            id=f"demo_video_{i+1}",
            bulk_job_id=bulk_job.id,
            idea_data=idea,
            status=JobStatus.QUEUED,
            priority=JobPriority.NORMAL,
            ai_provider="minimax",
            cost=Decimal('10.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        video_jobs.append(video_job)
        
    print(f"✅ Created {len(video_jobs)} video jobs from bulk job")
    
    # Generate schedules across multiple platforms
    print("\n5. Generating optimized schedules across platforms...")
    target_platforms = [PlatformId.YOUTUBE, PlatformId.TIKTOK, PlatformId.INSTAGRAM]
    
    schedule_items = integrate_with_bulk_job_workflow(
        calendar_manager, bulk_job, video_jobs, "demo_user_123", target_platforms
    )
    
    print(f"✅ Generated {len(schedule_items)} schedule items")
    
    # Show schedule details
    print("\n📅 Generated Schedule Details:")
    for i, item in enumerate(schedule_items[:3], 1):  # Show first 3
        print(f"  {i}. {item.platform_id.value.title()} - {item.content_format}")
        if item.scheduled_at:
            print(f"     Scheduled: {item.scheduled_at.strftime('%Y-%m-%d %H:%M')} {item.timezone}")
        print(f"     Status: {item.status.value}")
        print()
    
    # Demonstrate cross-platform coordination
    print("\n6. Demonstrating cross-platform coordination...")
    coordinator = CrossPlatformCoordinator(calendar_manager)
    
    # Optimize content for each platform
    sample_content = {
        "title": "AI Tools for Content Creation",
        "description": "Discover the best AI tools to enhance your content creation process in 2025",
        "target_audience": "Content creators",
        "keywords": ["AI", "content creation", "tools", "2025"]
    }
    
    for platform in target_platforms:
        optimized_content = coordinator.optimize_for_platform(platform, sample_content)
        print(f"✅ Optimized for {platform.value.title()}:")
        
        if platform == PlatformId.YOUTUBE:
            print(f"   - Title: {optimized_content.get('title', 'N/A')}")
            print(f"   - Tags: {optimized_content.get('tags', [])}")
        elif platform == PlatformId.TIKTOK:
            print(f"   - Hashtags: {optimized_content.get('hashtags', [])}")
            print(f"   - Sound: {optimized_content.get('sound', 'N/A')}")
        elif platform == PlatformId.INSTAGRAM:
            print(f"   - Hashtags: {optimized_content.get('hashtags', [])}")
            print(f"   - Story elements: {optimized_content.get('story_elements', [])}")
        print()
    
    # Create optimization trial
    print("\n7. Creating optimization trial for A/B testing...")
    trial = create_optimization_trial(
        "demo_user_123",
        "Testing optimized posting times vs standard times for AI content",
        calendar_manager
    )
    print(f"✅ Created trial: {trial.trial_id}")
    print(f"   Hypothesis: {trial.hypothesis}")
    print(f"   Variants: {list(trial.variants.keys())}")
    
    # Simulate performance data for analytics
    print("\n8. Simulating performance data for analytics...")
    simulate_performance_data(calendar_manager, schedule_items[:3])
    
    # Generate calendar analytics
    print("\n9. Generating calendar analytics and insights...")
    analytics_engine = CalendarAnalyticsEngine(calendar_manager)
    
    if schedule_items:
        analytics = analytics_engine.generate_calendar_analytics(schedule_items[0].calendar_id)
        
        print(f"📊 Calendar Analytics Summary:")
        print(f"   Total Scheduled: {analytics.total_scheduled}")
        print(f"   Total Posted: {analytics.total_posted}")
        print(f"   Total Failed: {analytics.total_failed}")
        print(f"   Average Engagement Rate: {analytics.average_engagement_rate:.2%}")
        
        if analytics.platform_distribution:
            print(f"   Platform Distribution:")
            for platform, count in analytics.platform_distribution.items():
                print(f"     - {platform.value.title()}: {count} posts")
        
        if analytics.optimization_recommendations:
            print(f"   Optimization Recommendations:")
            for i, rec in enumerate(analytics.optimization_recommendations, 1):
                print(f"     {i}. {rec}")
    
    # Generate timing optimization recommendations
    print("\n10. Generating timing optimization recommendations...")
    if schedule_items:
        optimizations = analytics_engine.optimize_schedule_timing(schedule_items[0].calendar_id)
        
        if optimizations:
            print("🎯 Timing Optimization Recommendations:")
            for opt in optimizations:
                print(f"   • {opt['type'].replace('_', ' ').title()}")
                print(f"     Platform: {opt.get('platform', 'All')}")
                print(f"     Recommendation: {opt['recommendation']}")
                print(f"     Confidence: {opt['confidence']}")
                print()
        else:
            print("   Not enough data for optimization recommendations")
            print("   (Need more performance data for meaningful insights)")
    
    # Show platform timing data
    print("\n11. Displaying platform timing research data...")
    for platform in target_platforms[:2]:  # Show first 2 platforms
        timing_data = calendar_manager.get_platform_timing_data(platform)
        if timing_data:
            print(f"📈 {platform.value.title()} Timing Data:")
            for timing in timing_data[:2]:  # Show first 2 timing entries
                print(f"   - Best days: {', '.join(timing.days)}")
                print(f"   - Peak hours: {timing.peak_hours}")
                print(f"   - Frequency: {timing.posting_frequency_min}-{timing.posting_frequency_max}/week")
                print(f"   - Source: {timing.source}")
                print()
    
    print("\n🎉 Demo completed successfully!")
    print("=" * 50)
    print("\nKey Integration Points:")
    print("• Seamless integration with existing VideoJob/BulkJob workflow")
    print("• Research-based platform timing optimization")
    print("• Cross-platform content coordination and optimization")
    print("• Comprehensive analytics and A/B testing framework")
    print("• User preference-based scheduling customization")
    print("• Performance tracking and optimization recommendations")


def simulate_performance_data(calendar_manager: ContentCalendarManager, schedule_items: list):
    """Simulate performance data for demo purposes."""
    import random
    
    conn = calendar_manager.storage_path
    if isinstance(conn, str):
        import sqlite3
        conn = sqlite3.connect(calendar_manager.storage_path)
        cursor = conn.cursor()
        
        for item in schedule_items:
            # Simulate performance events
            for days_after_post in [1, 7, 30]:  # Performance at 1 day, 1 week, 1 month
                event_data = {
                    'id': f"demo_kpi_{item.id}_{days_after_post}",
                    'video_job_id': item.video_job_id,
                    'platform_id': item.platform_id.value,
                    'content_format': item.content_format,
                    'event_time': (datetime.now(timezone.utc) - timedelta(days=days_after_post)).isoformat(),
                    'views': random.randint(100, 10000),
                    'impressions': random.randint(500, 50000),
                    'watch_time_seconds': random.randint(30, 300),
                    'engagement_rate': round(random.uniform(0.01, 0.08), 4),
                    'clicks': random.randint(10, 500),
                    'saves': random.randint(5, 100),
                    'shares': random.randint(2, 50),
                    'comments': random.randint(1, 30),
                    'followers_delta': random.randint(-5, 20),
                    'metadata': json.dumps({'demo': True})
                }
                
                cursor.execute("""
                    INSERT INTO performance_kpi_events 
                    (id, video_job_id, platform_id, content_format, event_time, views, 
                     impressions, watch_time_seconds, engagement_rate, clicks, saves, 
                     shares, comments, followers_delta, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data['id'], event_data['video_job_id'], event_data['platform_id'],
                    event_data['content_format'], event_data['event_time'], event_data['views'],
                    event_data['impressions'], event_data['watch_time_seconds'], 
                    event_data['engagement_rate'], event_data['clicks'], event_data['saves'],
                    event_data['shares'], event_data['comments'], event_data['followers_delta'],
                    event_data['metadata']
                ))
        
        conn.commit()
        conn.close()


def demo_platform_timing_data():
    """Demonstrate platform timing data features."""
    print("\n🔍 Platform Timing Data Deep Dive")
    print("=" * 40)
    
    calendar_manager = ContentCalendarManager("demo_timing_data.db")
    
    # Show timing data for different platforms
    platforms = [PlatformId.YOUTUBE, PlatformId.TIKTOK, PlatformId.INSTAGRAM]
    
    for platform in platforms:
        timing_data = calendar_manager.get_platform_timing_data(platform)
        print(f"\n📊 {platform.value.title()} Research Data:")
        print(f"   Available timing profiles: {len(timing_data)}")
        
        for timing in timing_data:
            print(f"   • Content format: {timing.content_format or 'default'}")
            print(f"     - Optimal days: {', '.join(timing.days)}")
            print(f"     - Peak hours: {timing.peak_hours}")
            print(f"     - Frequency range: {timing.posting_frequency_min}-{timing.posting_frequency_max}/week")
            print(f"     - Research source: {timing.source}")
            print()


if __name__ == "__main__":
    try:
        # Run the main demo
        demo_content_calendar_integration()
        
        # Optional: Show platform timing data deep dive
        demo_platform_timing_data()
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()