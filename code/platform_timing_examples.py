"""
Example usage of the Platform Timing Service

This script demonstrates how to use the platform timing service
for scheduling optimization across multiple social media platforms.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the platform timing service
from platform_timing_service import (
    PlatformTimingService,
    UserSchedulingPreferences,
    SchedulingAPIClient,
    load_config_from_env
)


async def example_single_platform_optimization():
    """Example: Optimize timing for a single platform"""
    
    print("=== Single Platform Optimization Example ===\n")
    
    # Load configuration
    config = load_config_from_env()
    
    # Initialize service
    service = PlatformTimingService(
        supabase_url=config.database.supabase_url,
        supabase_key=config.database.supabase_key
    )
    
    # Create user preferences for YouTube content creator
    user_prefs = UserSchedulingPreferences(
        user_id="creator_123",
        platform_id="youtube",
        timezone="America/New_York",
        posting_frequency_min=2,
        posting_frequency_max=4,
        days_blacklist=["sat", "sun"],  # Avoid weekends
        hours_blacklist=[{"start": 0, "end": 6}],  # Avoid late night/early morning
        content_format="long_form",
        quality_threshold=0.05  # Minimum 5% engagement rate
    )
    
    # Calculate optimal posting slots for next 2 weeks
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
    
    print(f"Platform: YouTube")
    print(f"Content Format: Long Form")
    print(f"Audience Segment: US East Coast")
    print(f"Confidence Score: {recommendation.confidence_score:.2%}")
    print(f"Number of Recommended Slots: {len(recommendation.recommended_slots)}")
    print("\nReasoning:")
    for reason in recommendation.reasoning:
        print(f"  • {reason}")
    
    print(f"\nRecommended Posting Schedule:")
    for i, slot in enumerate(recommendation.recommended_slots, 1):
        local_time = datetime.fromisoformat(slot["scheduled_at"]).astimezone(
            pytz.timezone(user_prefs.timezone)
        )
        print(f"  {i}. {local_time.strftime('%A, %B %d at %I:%M %p')} "
              f"({slot['confidence']:.1%} confidence)")
    
    return recommendation


async def example_multi_platform_optimization():
    """Example: Optimize timing for multiple platforms simultaneously"""
    
    print("\n=== Multi-Platform Optimization Example ===\n")
    
    # Load configuration
    config = load_config_from_env()
    
    # Initialize service
    service = PlatformTimingService(
        supabase_url=config.database.supabase_url,
        supabase_key=config.database.supabase_key
    )
    
    # Create batch optimization requests
    requests = []
    
    platforms = [
        {
            "platform_id": "youtube",
            "content_format": "long_form",
            "timezone": "America/New_York",
            "user_prefs": {
                "user_id": "creator_123",
                "timezone": "America/New_York",
                "posting_frequency_min": 2,
                "posting_frequency_max": 3,
                "days_blacklist": ["sat", "sun"],
                "content_format": "long_form"
            }
        },
        {
            "platform_id": "instagram",
            "content_format": "feed",
            "timezone": "America/New_York",
            "user_prefs": {
                "user_id": "creator_123",
                "timezone": "America/New_York",
                "posting_frequency_min": 3,
                "posting_frequency_max": 5,
                "content_format": "feed"
            }
        },
        {
            "platform_id": "tiktok",
            "content_format": "general",
            "timezone": "America/New_York",
            "user_prefs": {
                "user_id": "creator_123",
                "timezone": "America/New_York",
                "posting_frequency_min": 2,
                "posting_frequency_max": 5,
                "content_format": "general"
            }
        }
    ]
    
    # Prepare batch requests
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    for platform_config in platforms:
        request = {
            "platform_id": platform_config["platform_id"],
            "user_preferences": platform_config["user_prefs"],
            "content_format": platform_config["content_format"],
            "audience_segment": "general",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timezone": platform_config["timezone"]
        }
        requests.append(request)
    
    # Get batch recommendations
    recommendations = await service.batch_get_timing_recommendations(requests)
    
    print(f"Generated recommendations for {len(recommendations)} platforms:")
    
    for rec in recommendations:
        if rec["status"] == "success":
            platform = rec["platform_id"]
            content_format = rec["content_format"]
            recommendation = rec["recommendation"]
            
            print(f"\n--- {platform.upper()} ({content_format}) ---")
            print(f"Confidence: {recommendation['confidence_score']:.2%}")
            print(f"Recommended Slots: {len(recommendation['recommended_slots'])}")
            
            # Show top 3 slots
            for i, slot in enumerate(recommendation['recommended_slots'][:3], 1):
                local_time = datetime.fromisoformat(slot["scheduled_at"]).astimezone(
                    pytz.timezone("America/New_York")
                )
                print(f"  {i}. {local_time.strftime('%a %b %d, %I:%M %p')}")
        else:
            print(f"\n--- {rec['platform_id'].upper()} ---")
            print(f"Error: {rec.get('error', 'Unknown error')}")
    
    return recommendations


async def example_performance_tracking():
    """Example: Track performance and create optimization trials"""
    
    print("\n=== Performance Tracking & Optimization Example ===\n")
    
    # Load configuration
    config = load_config_from_env()
    
    # Initialize service
    service = PlatformTimingService(
        supabase_url=config.database.supabase_url,
        supabase_key=config.database.supabase_key
    )
    
    # Simulate logging performance KPI events
    print("Logging performance KPI events...")
    
    # Log performance for a YouTube video
    await service.log_performance_kpi(
        video_job_id="youtube_video_123",
        platform_id="youtube",
        views=2500,
        impressions=8000,
        engagement_rate=0.075,  # 7.5%
        watch_time_seconds=1800,  # 30 minutes average
        comments=42,
        likes=180,
        shares=25,
        subscribers_gained=15
    )
    
    # Log performance for an Instagram post
    await service.log_performance_kpi(
        video_job_id="instagram_post_456",
        platform_id="instagram",
        views=3200,
        impressions=12000,
        engagement_rate=0.085,  # 8.5%
        saves=120,
        shares=45,
        comments=35
    )
    
    # Get performance KPIs for a video
    kpis = await service.get_performance_kpis("youtube_video_123")
    if kpis:
        print(f"\nYouTube Video KPIs (last 30 days):")
        print(f"  Total Views: {kpis['total_views']:,}")
        print(f"  Total Impressions: {kpis['total_impressions']:,}")
        print(f"  Average Engagement Rate: {kpis['avg_engagement_rate']:.2%}")
        print(f"  KPI Events Logged: {kpis['events_count']}")
    
    # Create optimization trial
    print("\nCreating optimization trial...")
    trial_id = await service.create_optimization_trial(
        user_id="creator_123",
        hypothesis="Wednesday 4 PM YouTube posts achieve 20% higher engagement than Monday 4 PM posts",
        variants={
            "A": {
                "name": "Wednesday Schedule",
                "schedule": {"day": "wednesday", "time": "16:00"},
                "description": "Post YouTube videos on Wednesdays at 4 PM"
            },
            "B": {
                "name": "Monday Schedule", 
                "schedule": {"day": "monday", "time": "16:00"},
                "description": "Post YouTube videos on Mondays at 4 PM"
            }
        },
        primary_kpi="engagement_rate",
        start_at=datetime.now(),
        end_at=datetime.now() + timedelta(days=28),  # 4 weeks
        guardrails={
            "min_engagement_rate": 0.03,
            "min_views": 1000,
            "max_posting_frequency": 3
        }
    )
    
    if trial_id:
        print(f"Created optimization trial: {trial_id}")
        print("Trial will run for 4 weeks to compare Wednesday vs Monday posting times")
    
    return trial_id


async def example_preferences_management():
    """Example: Managing user scheduling preferences"""
    
    print("\n=== User Preferences Management Example ===\n")
    
    # Load configuration
    config = load_config_from_env()
    
    # Initialize service
    service = PlatformTimingService(
        supabase_url=config.database.supabase_url,
        supabase_key=config.database.supabase_key
    )
    
    # Create comprehensive user preferences
    preferences = UserSchedulingPreferences(
        user_id="creator_123",
        platform_id=None,  # Global preferences
        timezone="America/Los_Angeles",  # West Coast creator
        posting_frequency_min=3,
        posting_frequency_max=7,
        days_blacklist=["sat"],  # Avoid Saturdays
        hours_blacklist=[
            {"start": 0, "end": 6},   # Avoid late night
            {"start": 22, "end": 24}  # Avoid very late
        ],
        content_format=None,  # Global settings
        quality_threshold=0.04,  # 4% minimum engagement
        metadata={
            "automation_enabled": True,
            "preferred_content_types": ["educational", "tutorial"],
            "target_audience": "professionals",
            "posting_constraints": {
                "max_daily_posts": 2,
                "weekend_preference": "limited"
            }
        }
    )
    
    # Save preferences
    success = await service.save_user_scheduling_preferences(preferences)
    print(f"User preferences saved: {success}")
    
    # Retrieve preferences
    retrieved_prefs = await service.get_user_scheduling_preferences("creator_123")
    if retrieved_prefs:
        print(f"\nRetrieved preferences for user {retrieved_prefs.user_id}:")
        print(f"  Timezone: {retrieved_prefs.timezone}")
        print(f"  Frequency Range: {retrieved_prefs.posting_frequency_min}-{retrieved_prefs.posting_frequency_max}")
        print(f"  Blacklisted Days: {retrieved_prefs.days_blacklist}")
        print(f"  Quality Threshold: {retrieved_prefs.quality_threshold:.1%}")
    
    return success


async def example_api_client_usage():
    """Example: Using the HTTP API client"""
    
    print("\n=== API Client Usage Example ===\n")
    
    config = load_config_from_env()
    
    # Initialize API client
    async with SchedulingAPIClient(
        base_url=config.api.base_url,
        api_key=config.api.api_key
    ) as client:
        
        # Get single recommendation via API
        print("Requesting timing recommendation via API...")
        
        response = await client.get_timing_recommendation(
            platform_id="youtube",
            user_preferences={
                "user_id": "creator_123",
                "timezone": "America/New_York",
                "posting_frequency_min": 2,
                "posting_frequency_max": 4
            },
            content_format="long_form",
            audience_segment="us_east"
        )
        
        print(f"API Response Status: Success")
        if "recommendation" in response:
            rec = response["recommendation"]
            print(f"Confidence Score: {rec['confidence_score']:.2%}")
            print(f"Recommended Slots: {len(rec['recommended_slots'])}")
        
        # Log performance event via API
        print("\nLogging performance event via API...")
        
        event_response = await client.log_performance_event(
            video_job_id="api_test_video",
            platform_id="youtube",
            views=1800,
            impressions=6000,
            engagement_rate=0.06,
            watch_time_seconds=900,
            comments=28
        )
        
        print(f"Event logged successfully: {event_response.get('success', False)}")


async def main():
    """Run all examples"""
    
    print("Platform Timing Service - Usage Examples")
    print("=" * 50)
    
    try:
        # Run individual examples
        await example_single_platform_optimization()
        await example_multi_platform_optimization()
        await example_performance_tracking()
        await example_preferences_management()
        # await example_api_client_usage()  # Commented out for demo
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import pytz
    
    # Run the examples
    asyncio.run(main())