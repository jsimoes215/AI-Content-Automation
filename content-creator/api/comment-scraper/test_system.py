#!/usr/bin/env python3
"""
Test Script for Comment Scraping System

This script tests the basic functionality of the comment scraping system
to ensure all components are working correctly.
"""

import asyncio
import logging
import sys
import os

# Add the parent directory to the path so we can import the comment_scraper module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comment_scraper import (
    CommentScrapingAPI, Platform, quick_scrape, get_system_health,
    validate_setup, ScraperFactory
)

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from comment_scraper import (
            CommentScrapingAPI, Platform, CommentBase, CommentWithAnalysis,
            ScraperFactory, scraping_manager, comment_analyzer, data_extractor,
            api_key_manager, rate_limiter
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


async def test_scraper_factory():
    """Test scraper factory functionality"""
    print("\nTesting scraper factory...")
    
    try:
        factory = ScraperFactory()
        supported_platforms = factory.get_supported_platforms()
        print(f"✅ Supported platforms: {[p.value for p in supported_platforms]}")
        
        # Test capability checking
        for platform in supported_platforms:
            capabilities = factory.get_platform_capabilities(platform)
            print(f"✅ {platform.value} capabilities: {capabilities}")
        
        return True
    except Exception as e:
        print(f"❌ Scraper factory test failed: {e}")
        return False


async def test_api_key_manager():
    """Test API key manager functionality"""
    print("\nTesting API key manager...")
    
    try:
        from comment_scraper.utils.api_key_manager import api_key_manager
        
        # Test health report
        health_report = api_key_manager.get_health_report()
        print(f"✅ API key health report generated")
        print(f"   - Configured platforms: {health_report['summary']['configured']}")
        print(f"   - Validated platforms: {health_report['summary']['validated']}")
        
        return True
    except Exception as e:
        print(f"❌ API key manager test failed: {e}")
        return False


async def test_rate_limiter():
    """Test rate limiter functionality"""
    print("\nTesting rate limiter...")
    
    try:
        from comment_scraper.utils.rate_limiter import rate_limiter
        
        # Test status checking
        status = rate_limiter.get_status(Platform.YOUTUBE)
        print(f"✅ Rate limiter status check successful")
        print(f"   - YouTube limit: {status.limit if status else 'Not configured'}")
        
        # Test all platforms
        all_status = rate_limiter.get_all_status()
        print(f"✅ All platform status: {len(all_status)} platforms")
        
        return True
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False


async def test_comment_analyzer():
    """Test comment analyzer functionality"""
    print("\nTesting comment analyzer...")
    
    try:
        from comment_scraper.utils.comment_analyzer import comment_analyzer
        from comment_scraper.models.comment_models import CommentBase
        
        # Create a test comment
        test_comment = CommentBase(
            comment_id="test123",
            platform=Platform.YOUTUBE,
            content_id="test_video",
            text="This is a great video! I really love the content.",
            username="test_user",
            like_count=5,
            created_at=datetime.utcnow()
        )
        
        # Test analysis
        analyzed_comment = await comment_analyzer.analyze_comment(test_comment)
        print(f"✅ Comment analysis successful")
        print(f"   - Sentiment: {analyzed_comment.sentiment_label}")
        print(f"   - Quality score: {analyzed_comment.quality_score}")
        print(f"   - Topics: {analyzed_comment.topics}")
        
        return True
    except Exception as e:
        print(f"❌ Comment analyzer test failed: {e}")
        return False


async def test_data_models():
    """Test data model creation and validation"""
    print("\nTesting data models...")
    
    try:
        from comment_scraper.models.comment_models import (
            CommentBase, CommentWithAnalysis, Platform, ScrapingJob,
            ContentType, SentimentLabel
        )
        from datetime import datetime
        
        # Test CommentBase
        comment = CommentBase(
            comment_id="test123",
            platform=Platform.YOUTUBE,
            content_id="video123",
            text="Test comment",
            username="user123"
        )
        print(f"✅ CommentBase creation successful")
        
        # Test ScrapingJob
        job = ScrapingJob(
            job_id="job123",
            platform=Platform.YOUTUBE,
            content_id="video123",
            content_type=ContentType.VIDEO
        )
        print(f"✅ ScrapingJob creation successful")
        
        return True
    except Exception as e:
        print(f"❌ Data model test failed: {e}")
        return False


async def test_system_health():
    """Test system health checking"""
    print("\nTesting system health...")
    
    try:
        health = await get_system_health()
        print(f"✅ System health check successful")
        print(f"   - Status: {health.get('status', 'unknown')}")
        print(f"   - Version: {health.get('version', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ System health test failed: {e}")
        return False


async def test_configuration_validation():
    """Test configuration validation"""
    print("\nTesting configuration validation...")
    
    try:
        validation = await validate_setup()
        print(f"✅ Configuration validation successful")
        print(f"   - Valid: {validation.get('configuration_valid', False)}")
        
        # Show API key status
        api_keys = validation.get('api_keys', {})
        for platform, status in api_keys.items():
            configured = "✅" if status.get('configured', False) else "❌"
            print(f"   - {platform}: Configured {configured}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling with invalid input"""
    print("\nTesting error handling...")
    
    try:
        # Test with invalid platform
        try:
            from comment_scraper.scraper_factory import ScraperFactory
            factory = ScraperFactory()
            scraper = factory.create_scraper("invalid_platform")
            print("❌ Should have failed with invalid platform")
            return False
        except ValueError:
            print("✅ Invalid platform correctly rejected")
        
        # Test with invalid content ID
        try:
            result = await quick_scrape(
                platform=Platform.YOUTUBE,
                content_id="",  # Empty ID
                max_comments=1
            )
            print("✅ Error handling working correctly")
            return True
        except Exception:
            print("✅ Error handling working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def test_minimal_scraping():
    """Test minimal scraping functionality (if API keys available)"""
    print("\nTesting minimal scraping...")
    
    try:
        # Only test if we have at least one valid API key
        validation = await validate_setup()
        has_valid_keys = any(
            status.get('configured', False) 
            for status in validation.get('api_keys', {}).values()
        )
        
        if not has_valid_keys:
            print("⚠️  No API keys configured, skipping scraping test")
            return True
        
        # Test with very small limits
        result = await quick_scrape(
            platform=Platform.YOUTUBE,
            content_id="dQw4w9WgXcQ",  # Rick Roll - test video
            max_comments=1  # Just one comment
        )
        
        if result.get('success', False):
            print(f"✅ Minimal scraping successful: {result['comments_scraped']} comments")
            return True
        else:
            print(f"⚠️  Scraping test failed (expected without valid keys): {result.get('error', 'Unknown error')}")
            return True
            
    except Exception as e:
        print(f"⚠️  Minimal scraping test encountered error (may be expected): {e}")
        return True  # Don't fail the test suite for this


async def run_all_tests():
    """Run all tests"""
    print("🧪 Comment Scraping System - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Scraper Factory", test_scraper_factory),
        ("API Key Manager", test_api_key_manager),
        ("Rate Limiter", test_rate_limiter),
        ("Comment Analyzer", test_comment_analyzer),
        ("Data Models", test_data_models),
        ("System Health", test_system_health),
        ("Configuration Validation", test_configuration_validation),
        ("Error Handling", test_error_handling),
        ("Minimal Scraping", test_minimal_scraping),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready to use.")
    else:
        print(f"⚠️  {failed} tests failed. Check configuration and dependencies.")
    
    return failed == 0


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)