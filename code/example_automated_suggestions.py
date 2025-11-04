#!/usr/bin/env python3
"""
Example Usage of Automated Posting Time Suggestion System

This script demonstrates various features of the automated suggestions system
including basic usage, bulk processing, and performance validation.

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from automated_suggestions import (
    Platform, ContentType, SuggestionEngine, BulkSuggestionProcessor,
    ContentProfile, AudienceProfile, PerformanceMetrics, SuggestionPriority,
    create_suggestion_from_user_input
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demonstrate_basic_suggestions():
    """Demonstrate basic suggestion generation."""
    print("\n=== Basic Suggestion Generation ===")
    
    # Create suggestion engine
    engine = SuggestionEngine(
        db_path="demo_suggestions.db",
        learning_rate=0.15,
        min_confidence=0.6
    )
    
    # Example 1: YouTube educational content
    print("\n--- YouTube Educational Video ---")
    content_profile = ContentProfile(
        content_type=ContentType.VIDEO_LONG,
        duration=600,  # 10 minutes
        industry="education",
        hashtags=["#tutorial", "#learning", "#ai"],
        keywords=["machine learning", "python tutorial"],
        urgency_level=SuggestionPriority.MEDIUM
    )
    
    audience_profile = AudienceProfile(
        age_cohorts={"18-24": 0.25, "25-34": 0.40, "35-44": 0.25, "45-54": 0.10},
        device_split={"mobile": 0.60, "desktop": 0.40},
        time_zones={"EST": 0.5, "PST": 0.3, "UTC": 0.2}
    )
    
    suggestion = engine.generate_suggestion(
        platform=Platform.YOUTUBE,
        content_profile=content_profile,
        audience_profile=audience_profile,
        num_alternatives=3
    )
    
    print(f"Suggested time: {suggestion.suggested_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"Confidence: {suggestion.confidence:.2f}")
    print(f"Score: {suggestion.score.score:.3f}")
    print(f"Priority: {suggestion.priority.name}")
    print(f"Factors: {', '.join(suggestion.score.explanation)}")
    
    if suggestion.alternatives:
        print("\nAlternative times:")
        for i, alt in enumerate(suggestion.alternatives[:3], 1):
            print(f"  {i}. Day {alt.day_of_week}, Hour {alt.hour} (Score: {alt.score:.3f})")
    
    # Example 2: TikTok short-form entertainment
    print("\n--- TikTok Entertainment Video ---")
    tiktok_content = ContentProfile(
        content_type=ContentType.VIDEO_SHORT,
        duration=15,  # 15 seconds
        industry="entertainment",
        hashtags=["#fyp", "#funny", "#comedy"],
        keywords=["skit", "humor", "trending"],
        urgency_level=SuggestionPriority.HIGH
    )
    
    young_audience = AudienceProfile(
        age_cohorts={"18-24": 0.50, "25-34": 0.30, "35-44": 0.15, "45-54": 0.05},
        device_split={"mobile": 0.95, "desktop": 0.05},
        time_zones={"EST": 0.4, "PST": 0.4, "CST": 0.2}
    )
    
    tiktok_suggestion = engine.generate_suggestion(
        platform=Platform.TIKTOK,
        content_profile=tiktok_content,
        audience_profile=young_audience,
        num_alternatives=3
    )
    
    print(f"Suggested time: {tiktok_suggestion.suggested_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"Confidence: {tiktok_suggestion.confidence:.2f}")
    print(f"Score: {tiktok_suggestion.score.score:.3f}")
    print(f"Best for {tiktok_suggestion.platform.value} audience patterns")
    
    return engine


def demonstrate_platform_comparison():
    """Demonstrate cross-platform timing analysis."""
    print("\n=== Cross-Platform Timing Analysis ===")
    
    engine = SuggestionEngine()
    
    # Same content, different platforms
    content_profile = ContentProfile(
        content_type=ContentType.VIDEO_SHORT,
        duration=60,
        industry="tech",
        hashtags=["#technology", "#innovation"],
        keywords=["startup", "business"],
        urgency_level=SuggestionPriority.MEDIUM
    )
    
    audience_profile = AudienceProfile(
        age_cohorts={"25-34": 0.40, "35-44": 0.35, "45-54": 0.20, "55+": 0.05},
        device_split={"mobile": 0.70, "desktop": 0.30},
        time_zones={"EST": 0.6, "PST": 0.4}
    )
    
    platforms = [Platform.YOUTUBE, Platform.INSTAGRAM, Platform.TIKTOK, Platform.LINKEDIN, Platform.X]
    
    print("\nOptimal posting times by platform:")
    for platform in platforms:
        suggestion = engine.generate_suggestion(
            platform=platform,
            content_profile=content_profile,
            audience_profile=audience_profile,
            num_alternatives=1
        )
        
        print(f"{platform.value.upper():>12}: {suggestion.suggested_datetime.strftime('%A %I:%M %p')} "
              f"(confidence: {suggestion.confidence:.2f})")


def demonstrate_content_type_variations():
    """Demonstrate how content type affects timing."""
    print("\n=== Content Type Impact Analysis ===")
    
    engine = SuggestionEngine()
    
    platform = Platform.INSTAGRAM
    
    # Same audience, different content types
    audience_profile = AudienceProfile(
        age_cohorts={"18-24": 0.35, "25-34": 0.35, "35-44": 0.20, "45-54": 0.10},
        device_split={"mobile": 0.85, "desktop": 0.15},
        time_zones={"EST": 1.0}
    )
    
    content_types = [
        (ContentType.IMAGE, "static image post"),
        (ContentType.CAROUSEL, "image carousel"),
        (ContentType.REEL, "short video"),
        (ContentType.STORY, "instagram story")
    ]
    
    print(f"\nTiming recommendations for {platform.value} by content type:")
    for content_type, description in content_types:
        content_profile = ContentProfile(
            content_type=content_type,
            duration=30 if content_type in [ContentType.REEL, ContentType.STORY] else None,
            industry="lifestyle",
            urgency_level=SuggestionPriority.MEDIUM
        )
        
        suggestion = engine.generate_suggestion(
            platform=platform,
            content_profile=content_profile,
            audience_profile=audience_profile,
            num_alternatives=1
        )
        
        print(f"{description:>20}: {suggestion.suggested_datetime.strftime('%A %I:%M %p')} "
              f"(score: {suggestion.score.score:.3f})")


def demonstrate_preference_learning():
    """Demonstrate how the system learns from performance data."""
    print("\n=== Learning from Performance Data ===")
    
    engine = SuggestionEngine(
        db_path="learning_demo.db",
        learning_rate=0.20,  # Faster learning for demo
        min_confidence=0.5
    )
    
    # Generate initial suggestion
    content_profile = ContentProfile(
        content_type=ContentType.VIDEO_LONG,
        duration=300,
        industry="business",
        urgency_level=SuggestionPriority.MEDIUM
    )
    
    audience_profile = AudienceProfile(
        age_cohorts={"25-34": 0.45, "35-44": 0.35, "45-54": 0.20},
        device_split={"mobile": 0.65, "desktop": 0.35},
        time_zones={"EST": 1.0}
    )
    
    print("Generating initial suggestion...")
    initial_suggestion = engine.generate_suggestion(
        platform=Platform.LINKEDIN,
        content_profile=content_profile,
        audience_profile=audience_profile
    )
    
    print(f"Initial suggestion: {initial_suggestion.suggested_datetime.strftime('%A %I:%M %p')} "
          f"(confidence: {initial_suggestion.confidence:.2f})")
    
    # Simulate performance validation - let's say this was successful
    successful_metrics = PerformanceMetrics(
        post_id="linkedin_post_001",
        platform=Platform.LINKEDIN,
        content_type=ContentType.VIDEO_LONG,
        post_time=initial_suggestion.suggested_datetime,
        metrics={
            "impressions": 2500,
            "engagement_rate": 0.045,
            "clicks": 120,
            "comments": 15,
            "shares": 8,
            "dwell_time": 45.5
        },
        validation_score=0.82  # High performing post
    )
    
    print("\nValidating successful performance...")
    engine.validate_suggestion_performance(
        suggestion_id=initial_suggestion.id,
        performance_metrics=successful_metrics
    )
    
    # Generate new suggestion after learning
    print("Generating new suggestion after learning...")
    learned_suggestion = engine.generate_suggestion(
        platform=Platform.LINKEDIN,
        content_profile=content_profile,
        audience_profile=audience_profile
    )
    
    print(f"Learned suggestion: {learned_suggestion.suggested_datetime.strftime('%A %I:%M %p')} "
          f"(confidence: {learned_suggestion.confidence:.2f})")
    
    # Show insights
    insights = engine.get_optimization_insights()
    print(f"\nLearning progress:")
    print(f"- Total suggestions: {insights['overall_performance']['total_suggestions']}")
    print(f"- Success rate: {insights['overall_performance']['success_rate']:.1%}")
    print(f"- Bayesian parameters learned: {insights['learning_status']['bayesian_params_count']}")


def demonstrate_simple_input():
    """Demonstrate simple user input interface."""
    print("\n=== Simple User Input Interface ===")
    
    # Simple interface for quick suggestions
    print("Creating suggestion from simple input...")
    
    suggestion = create_suggestion_from_user_input(
        platform_str="youtube",
        content_type_str="video_short",
        duration=60,
        industry="gaming"
    )
    
    print(f"Platform: {suggestion.platform.value}")
    print(f"Content type: {suggestion.content_profile.content_type.value}")
    print(f"Suggested time: {suggestion.suggested_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"Confidence: {suggestion.confidence:.2f}")
    print(f"Factors: {', '.join(suggestion.score.explanation)}")


async def demonstrate_bulk_processing():
    """Demonstrate bulk processing with Google Sheets (simulated)."""
    print("\n=== Bulk Processing Simulation ===")
    
    # Note: This is a simulation since we don't have actual Google Sheets credentials
    print("Simulating bulk processing from Google Sheets...")
    
    # Simulate sheet data
    sheet_data = [
        ["Platform", "Content_Type", "Duration", "Industry", "Hashtags", "Keywords", "Urgency"],
        ["youtube", "video_long", "600", "education", "#tutorial", "python programming", "2"],
        ["tiktok", "video_short", "30", "entertainment", "#funny", "comedy skit", "3"],
        ["instagram", "reel", "45", "lifestyle", "#motivation", "daily routine", "1"],
        ["linkedin", "document", "", "business", "#strategy", "market analysis", "2"],
        ["x", "text", "", "news", "#breaking", "tech news", "4"]
    ]
    
    engine = SuggestionEngine(db_path="bulk_demo.db")
    results = []
    
    print(f"\nProcessing {len(sheet_data)-1} rows...")
    
    for i, row in enumerate(sheet_data[1:], 1):  # Skip header
        try:
            platform_str, content_type_str, duration_str, industry, hashtags, keywords, urgency_str = row
            
            # Parse duration
            duration = int(duration_str) if duration_str else None
            
            # Create profiles
            content_profile = ContentProfile(
                content_type=ContentType(content_type_str),
                duration=duration,
                industry=industry,
                hashtags=hashtags.split(",") if hashtags else [],
                keywords=keywords.split(",") if keywords else [],
                urgency_level=SuggestionPriority(int(urgency_str))
            )
            
            audience_profile = AudienceProfile(
                age_cohorts={"18-24": 0.3, "25-34": 0.4, "35-44": 0.3},
                device_split={"mobile": 0.8, "desktop": 0.2},
                time_zones={"UTC": 1.0}
            )
            
            # Generate suggestion
            suggestion = engine.generate_suggestion(
                platform=Platform(platform_str),
                content_profile=content_profile,
                audience_profile=audience_profile
            )
            
            # Format result
            result = {
                "Row": i,
                "Platform": platform_str,
                "Content_Type": content_type_str,
                "Suggested_DateTime": suggestion.suggested_datetime.strftime("%Y-%m-%d %H:%M"),
                "Confidence": round(suggestion.confidence, 3),
                "Score": round(suggestion.score.score, 3),
                "Priority": suggestion.priority.name
            }
            
            results.append(result)
            
            print(f"Row {i}: {platform_str} {content_type_str} → "
                  f"{suggestion.suggested_datetime.strftime('%a %H:%M')} "
                  f"(confidence: {suggestion.confidence:.2f})")
            
        except Exception as e:
            print(f"Row {i}: Error - {e}")
    
    print(f"\nBulk processing completed: {len(results)} suggestions generated")
    
    # Show summary
    if results:
        platforms = {}
        for result in results:
            platform = result["Platform"]
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(result)
        
        print("\nSummary by platform:")
        for platform, platform_results in platforms.items():
            avg_confidence = sum(r["Confidence"] for r in platform_results) / len(platform_results)
            print(f"  {platform}: {len(platform_results)} suggestions, "
                  f"avg confidence: {avg_confidence:.3f}")


def demonstrate_advanced_features():
    """Demonstrate advanced features and customizations."""
    print("\n=== Advanced Features Demo ===")
    
    # High-frequency content scenario
    print("\n--- High-Frequency Content Scenario ---")
    
    engine = SuggestionEngine(db_path="advanced_demo.db", min_confidence=0.8)  # High confidence requirement
    
    # TikTok influencer posting multiple times per day
    tiktok_profiles = [
        ContentProfile(
            content_type=ContentType.VIDEO_SHORT,
            duration=15 + i * 5,  # Varying durations
            industry="lifestyle",
            hashtags=["#daily", "#vlog", f"#{day}"]
        )
        for i, day in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday"])
    ]
    
    print("Generating suggestions for high-frequency TikTok posting:")
    suggestions = []
    for i, profile in enumerate(tiktok_profiles):
        suggestion = engine.generate_suggestion(
            platform=Platform.TIKTOK,
            content_profile=profile,
            num_alternatives=2
        )
        suggestions.append(suggestion)
        print(f"  Day {i+1}: {suggestion.suggested_datetime.strftime('%A %I:%M %p')} "
              f"(score: {suggestion.score.score:.3f})")
    
    # Check for spacing conflicts
    print("\nChecking spacing conflicts:")
    for i, suggestion in enumerate(suggestions):
        if i > 0:
            prev_time = suggestions[i-1].suggested_datetime
            time_diff = (suggestion.suggested_datetime - prev_time).total_seconds() / 3600
            if time_diff < 3:  # Less than 3 hours apart
                print(f"  Warning: Posts {i} and {i+1} are {time_diff:.1f} hours apart")
            else:
                print(f"  Good: Post {i+1} has {time_diff:.1f} hours spacing")
    
    # Industry-specific optimization
    print("\n--- Industry-Specific Optimization ---")
    
    industries = ["education", "entertainment", "business", "technology", "health"]
    platform = Platform.LINKEDIN
    
    print(f"Optimal timing for {platform.value} by industry:")
    
    for industry in industries:
        content_profile = ContentProfile(
            content_type=ContentType.DOCUMENT,
            industry=industry,
            urgency_level=SuggestionPriority.MEDIUM
        )
        
        suggestion = engine.generate_suggestion(
            platform=platform,
            content_profile=content_profile
        )
        
        print(f"  {industry:>12}: {suggestion.suggested_datetime.strftime('%A %I:%M %p')} "
              f"(confidence: {suggestion.confidence:.2f})")


def main():
    """Run all demonstration examples."""
    print("=" * 60)
    print("AUTOMATED POSTING TIME SUGGESTION SYSTEM")
    print("Demonstration Examples")
    print("=" * 60)
    
    # Basic demonstrations
    engine = demonstrate_basic_suggestions()
    demonstrate_platform_comparison()
    demonstrate_content_type_variations()
    demonstrate_preference_learning()
    demonstrate_simple_input()
    
    # Async demonstrations
    print("\n" + "=" * 60)
    print("ASYNC OPERATIONS")
    print("=" * 60)
    
    # Run async bulk processing demo
    asyncio.run(demonstrate_bulk_processing())
    
    # Advanced features
    demonstrate_advanced_features()
    
    # Final insights
    print("\n" + "=" * 60)
    print("SYSTEM INSIGHTS")
    print("=" * 60)
    
    insights = engine.get_optimization_insights()
    print(f"Total suggestions generated: {insights['overall_performance']['total_suggestions']}")
    print(f"Success rate: {insights['overall_performance']['success_rate']:.1%}")
    print(f"Bayesian learning parameters: {insights['learning_status']['bayesian_params_count']}")
    
    if insights['platform_breakdown']:
        print("\nPlatform performance breakdown:")
        for platform, stats in insights['platform_breakdown'].items():
            if stats['suggestions'] > 0:
                print(f"  {platform}: {stats['success_rate']:.1%} success rate "
                      f"({stats['suggestions']} suggestions)")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETED")
    print("=" * 60)
    print("\nKey takeaways:")
    print("• Platform-specific timing optimization based on 2025 data")
    print("• Adaptive learning from performance feedback")
    print("• Cross-platform conflict resolution and spacing constraints")
    print("• Google Sheets integration for bulk processing")
    print("• Confidence-based filtering and explainable recommendations")
    print("\nNext steps:")
    print("• Integrate with your content generation pipeline")
    print("• Connect to Google Sheets for bulk operations")
    print("• Set up performance validation feedback loops")
    print("• Configure platform-specific constraints and preferences")


if __name__ == "__main__":
    main()