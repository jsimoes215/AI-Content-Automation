#!/usr/bin/env python3
"""
Example Usage Script for Comment Scraping System

This script demonstrates various ways to use the comment scraping system
for different platforms and use cases.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from comment_scraper import (
    CommentScrapingAPI, Platform, quick_scrape, get_system_health,
    validate_setup, SentimentLabel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_scraping():
    """Example 1: Basic comment scraping"""
    print("\n=== Example 1: Basic Comment Scraping ===")
    
    try:
        # Quick scrape example
        result = await quick_srapse(
            platform=Platform.YOUTUBE,
            content_id="dQw4w9WgXcQ",  # Rick Roll video
            max_comments=10  # Small number for demo
        )
        
        if result['success']:
            print(f"✅ Successfully scraped {result['comments_scraped']} comments")
            for i, comment in enumerate(result['comments'][:3], 1):
                print(f"{i}. {comment.username}: {comment.text[:50]}...")
        else:
            print(f"❌ Failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_advanced_scraping_with_analysis():
    """Example 2: Advanced scraping with sentiment analysis"""
    print("\n=== Example 2: Advanced Scraping with Analysis ===")
    
    async with CommentScrapingAPI() as api:
        try:
            result = await api.scrape_and_analyze_comments(
                platform=Platform.YOUTUBE,
                content_id="dQw4w9WgXcQ",
                max_comments=20,
                include_analysis=True,
                language_filter="en"
            )
            
            if result['success']:
                print(f"✅ Scraped and analyzed {result['comments_scraped']} comments")
                
                # Analyze sentiment distribution
                analysis = result['analysis_stats']
                print(f"📊 Sentiment Distribution: {analysis['sentiment_distribution']}")
                print(f"📊 Average Quality Score: {analysis['average_quality_score']:.2f}")
                
                # Show high-quality positive comments
                high_quality_positive = [
                    c for c in result['comments']
                    if (c.quality_score or 0) > 0.7 and 
                       c.sentiment_label == SentimentLabel.POSITIVE
                ]
                
                print(f"✨ High-quality positive comments: {len(high_quality_positive)}")
                for comment in high_quality_positive[:2]:
                    print(f"  - Score: {comment.quality_score:.2f}, Sentiment: {comment.sentiment_label.value}")
                    print(f"    Text: {comment.text[:80]}...")
                    
        except Exception as e:
            print(f"❌ Error: {e}")


async def example_batch_scraping():
    """Example 3: Batch scraping multiple sources"""
    print("\n=== Example 3: Batch Scraping ===")
    
    async with CommentScrapingAPI() as api:
        try:
            # Batch request for multiple platforms
            requests = [
                {
                    'platform': Platform.YOUTUBE,
                    'content_id': "dQw4w9WgXcQ",
                    'max_comments': 5,
                    'include_analysis': False
                },
                {
                    'platform': Platform.TWITTER,
                    'content_id': "1234567890",  # Replace with real tweet ID
                    'max_comments': 5,
                    'include_analysis': False
                }
            ]
            
            results = await api.batch_scrape(requests, max_concurrent=2)
            
            successful = 0
            for i, result in enumerate(results):
                if result.get('success', False):
                    successful += 1
                    print(f"✅ Request {i+1}: {result['comments_scraped']} comments")
                else:
                    print(f"❌ Request {i+1}: {result.get('error', 'Unknown error')}")
            
            print(f"📊 Batch Results: {successful}/{len(requests)} successful")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def example_data_export():
    """Example 4: Data export and filtering"""
    print("\n=== Example 4: Data Export ===")
    
    async with CommentScrapingAPI() as api:
        try:
            # Export with analysis to JSON
            result = await api.extract_and_export(
                platform=Platform.YOUTUBE,
                content_id="dQw4w9WgXcQ",
                output_format="json",
                output_file="example_youtube_comments.json",
                include_analysis=True,
                max_comments=10
            )
            
            if result['success']:
                export_info = result['export']
                print(f"✅ Exported {export_info['records_exported']} comments")
                print(f"📁 File: {export_info['file_path']}")
                print(f"📏 Size: {export_info['file_size_bytes']} bytes")
            else:
                print(f"❌ Export failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def example_trend_analysis():
    """Example 5: Trending topics analysis"""
    print("\n=== Example 5: Trend Analysis ===")
    
    async with CommentScrapingAPI() as api:
        try:
            # Analyze trending topics across multiple content pieces
            trending = await api.get_trending_topics(
                platforms=[Platform.YOUTUBE],
                content_ids=["dQw4w9WgXcQ"],  # Replace with multiple videos
                time_range="7d",
                min_mentions=1
            )
            
            if trending['success']:
                analysis = trending['trending_topics']
                print(f"📈 Analysis Summary:")
                summary = analysis['analysis_summary']
                print(f"  - Total comments: {summary['total_comments_analyzed']}")
                print(f"  - Platforms: {summary['platforms_analyzed']}")
                print(f"  - Time range: {summary['time_range']}")
                
                print(f"🔥 Top Trending Topics:")
                for topic in analysis['trending_topics']['trending_topics'][:5]:
                    print(f"  - {topic['topic']}: {topic['mentions']} mentions ({topic['percentage']:.1f}%)")
            else:
                print(f"❌ Trend analysis failed: {trending['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def example_system_monitoring():
    """Example 6: System health and monitoring"""
    print("\n=== Example 6: System Monitoring ===")
    
    try:
        # Check system health
        health = await get_system_health()
        print(f"🏥 System Health: {health['status']}")
        print(f"🌐 Available Platforms: {health['available_platforms']}")
        print(f"🔧 Active Jobs: {health['active_jobs']}")
        
        # Validate configuration
        validation = await validate_setup()
        print(f"\n⚙️ Configuration Validation:")
        print(f"  - Valid: {validation['configuration_valid']}")
        
        for platform, status in validation['api_keys'].items():
            connection_status = "✅" if status['connection_working'] else "❌"
            config_status = "✅" if status['configured'] else "❌"
            print(f"  - {platform}: Configured {config_status}, Connection {connection_status}")
        
        print(f"\n💡 Recommendations:")
        for rec in validation['recommendations']:
            print(f"  - {rec}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_filtered_scraping():
    """Example 7: Filtered scraping"""
    print("\n=== Example 7: Filtered Scraping ===")
    
    async with CommentScrapingAPI() as api:
        try:
            # Scraping with date filters
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()
            
            result = await api.scrape_and_analyze_comments(
                platform=Platform.YOUTUBE,
                content_id="dQw4w9WgXcQ",
                max_comments=20,
                include_analysis=True,
                start_date=start_date,
                end_date=end_date,
                language_filter="en"
            )
            
            if result['success']:
                print(f"✅ Scraped {result['comments_scraped']} comments (last 7 days)")
                
                # Filter and analyze results
                positive_comments = [
                    c for c in result['comments']
                    if c.sentiment_label == SentimentLabel.POSITIVE
                ]
                
                print(f"😊 Positive sentiment: {len(positive_comments)} comments")
                
                # Show engagement potential
                high_engagement = [
                    c for c in result['comments']
                    if (c.engagement_potential or 0) > 0.7
                ]
                
                print(f"🚀 High engagement potential: {len(high_engagement)} comments")
                
            else:
                print(f"❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def example_custom_analysis():
    """Example 8: Custom analysis pipeline"""
    print("\n=== Example 8: Custom Analysis ===")
    
    async with CommentScrapingAPI() as api:
        try:
            # Scrape without built-in analysis
            result = await api.scrape_and_analyze_comments(
                platform=Platform.YOUTUBE,
                content_id="dQw4w9WgXcQ",
                max_comments=15,
                include_analysis=False  # We'll do custom analysis
            )
            
            if result['success']:
                print(f"✅ Scraped {result['comments_scraped']} comments for custom analysis")
                
                # Custom analysis: Comment length analysis
                short_comments = []
                medium_comments = []
                long_comments = []
                
                for comment in result['comments']:
                    word_count = len(comment.text.split())
                    if word_count <= 5:
                        short_comments.append(comment)
                    elif word_count <= 20:
                        medium_comments.append(comment)
                    else:
                        long_comments.append(comment)
                
                print(f"\n📏 Comment Length Analysis:")
                print(f"  - Short (≤5 words): {len(short_comments)} comments")
                print(f"  - Medium (6-20 words): {len(medium_comments)} comments")
                print(f"  - Long (>20 words): {len(long_comments)} comments")
                
                # Find most engaged comment
                most_liked = max(result['comments'], key=lambda c: c.like_count)
                print(f"\n👍 Most Liked Comment:")
                print(f"  - Likes: {most_liked.like_count}")
                print(f"  - Author: {most_liked.username}")
                print(f"  - Text: {most_liked.text[:80]}...")
                
            else:
                print(f"❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all examples"""
    print("🚀 Comment Scraping System - Example Usage")
    print("=" * 50)
    
    # Check if API keys are configured
    try:
        validation = await validate_setup()
        if not validation['configuration_valid']:
            print("⚠️  Warning: Not all API keys are configured properly.")
            print("   Some examples may fail. See recommendations below.")
            for rec in validation['recommendations']:
                print(f"   - {rec}")
            print()
    except Exception as e:
        print(f"⚠️  Warning: Could not validate configuration: {e}")
    
    # Run examples
    await example_system_monitoring()
    await example_basic_scraping()
    await example_advanced_scraping_with_analysis()
    await example_filtered_scraping()
    await example_batch_scraping()
    await example_data_export()
    await example_trend_analysis()
    await example_custom_analysis()
    
    print("\n🎉 All examples completed!")
    print("\n💡 Tips:")
    print("  - Configure your API keys in environment variables for full functionality")
    print("  - Check the README.md for detailed documentation")
    print("  - Adjust the 'content_id' values to test with your own content")


if __name__ == "__main__":
    # Fix typo in function name
    asyncio.run(main())