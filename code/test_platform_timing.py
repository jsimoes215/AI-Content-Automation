"""
Simple test script for Platform Timing Service

This script provides basic validation tests to ensure the platform
timing service components are working correctly.
"""

import sys
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Import the platform timing service
try:
    from platform_timing_service import (
        PlatformTimingService,
        UserSchedulingPreferences,
        ScheduleRecommendation,
        PlatformTimingData
    )
    print("✓ Successfully imported PlatformTimingService")
except ImportError as e:
    print(f"✗ Failed to import PlatformTimingService: {e}")
    sys.exit(1)


def test_data_structures():
    """Test that data structures are working correctly"""
    print("\n=== Testing Data Structures ===")
    
    try:
        # Test PlatformTimingData creation
        timing_data = PlatformTimingData(
            platform_id="youtube",
            days=["mon", "tue", "wed"],
            peak_hours=[{"start": 15, "end": 17}],
            posting_frequency_min=2,
            posting_frequency_max=3,
            source="Test source",
            notes="Test notes"
        )
        assert timing_data.platform_id == "youtube"
        assert "wed" in timing_data.days
        print("✓ PlatformTimingData creation works")
        
        # Test UserSchedulingPreferences creation
        user_prefs = UserSchedulingPreferences(
            user_id="test_user",
            timezone="UTC",
            posting_frequency_min=2,
            posting_frequency_max=4
        )
        assert user_prefs.user_id == "test_user"
        assert user_prefs.timezone == "UTC"
        print("✓ UserSchedulingPreferences creation works")
        
        # Test ScheduleRecommendation creation
        recommendation = ScheduleRecommendation(
            recommended_slots=[],
            confidence_score=0.8,
            reasoning=["test reason"]
        )
        assert recommendation.confidence_score == 0.8
        print("✓ ScheduleRecommendation creation works")
        
        return True
        
    except Exception as e:
        print(f"✗ Data structure tests failed: {e}")
        return False


def test_timing_calculations():
    """Test timing calculation logic without database dependency"""
    print("\n=== Testing Timing Calculations ===")
    
    try:
        # Create a mock service to test timing logic
        service = PlatformTimingService.__new__(PlatformTimingService)
        
        # Mock the platform timing bases
        service.platform_timing_bases = {
            "youtube": {
                "days": ["mon", "tue", "wed", "thu", "fri"],
                "peak_hours": [{"start": 15, "end": 17}],
                "posting_frequency_min": 2,
                "posting_frequency_max": 3,
                "source": "Test source"
            }
        }
        
        # Test confidence score calculation
        timing_data = service.platform_timing_bases["youtube"]
        user_prefs = UserSchedulingPreferences(
            user_id="test_user",
            timezone="UTC"
        )
        slots = [{"confidence": 0.8}]
        
        confidence = service._calculate_confidence_score(
            timing_data, user_prefs, slots
        )
        assert 0.0 <= confidence <= 1.0
        print(f"✓ Confidence score calculation works: {confidence:.2f}")
        
        # Test slot confidence calculation
        slot_confidence = service._calculate_slot_confidence(
            "youtube", "wed", {"start": 16, "end": 17}, timing_data
        )
        assert 0.0 <= slot_confidence <= 1.0
        print(f"✓ Slot confidence calculation works: {slot_confidence:.2f}")
        
        # Test reasoning generation
        reasoning = service._generate_reasoning(
            "youtube", timing_data, user_prefs, "long_form"
        )
        assert isinstance(reasoning, list)
        assert len(reasoning) > 0
        print(f"✓ Reasoning generation works: {len(reasoning)} reasons")
        
        return True
        
    except Exception as e:
        print(f"✗ Timing calculation tests failed: {e}")
        return False


def test_platform_data_loading():
    """Test platform data structure integrity"""
    print("\n=== Testing Platform Data Loading ===")
    
    try:
        service = PlatformTimingService.__new__(PlatformTimingService)
        service._load_platform_timing_bases()
        
        # Verify all expected platforms are loaded
        expected_platforms = ["youtube", "tiktok", "instagram", "twitter", "linkedin", "facebook"]
        for platform in expected_platforms:
            assert platform in service.platform_timing_bases
            platform_data = service.platform_timing_bases[platform]
            
            # Verify required fields exist
            required_fields = ["days", "peak_hours", "posting_frequency_min", "posting_frequency_max", "source"]
            for field in required_fields:
                assert field in platform_data
            
            print(f"✓ {platform.title()} platform data loaded correctly")
        
        # Test specific platform insights
        youtube_data = service.platform_timing_bases["youtube"]
        assert "wednesday 4 p.m." in youtube_data["notes"].lower()
        print("✓ YouTube platform insight found")
        
        tiktok_data = service.platform_timing_bases["tiktok"]
        assert tiktok_data["days"] == ["tue", "wed", "thu", "fri"]
        print("✓ TikTok platform data verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Platform data loading tests failed: {e}")
        return False


async def test_mock_database_operations():
    """Test database operations with mocked responses"""
    print("\n=== Testing Database Operations ===")
    
    try:
        # Create service with mock supabase client
        with patch('supabase.create_client') as mock_create_client:
            mock_supabase = MagicMock()
            mock_create_client.return_value = mock_supabase
            
            # Mock execute responses
            mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
                {
                    "platform_id": "youtube",
                    "days": ["mon", "tue", "wed"],
                    "peak_hours": [{"start": 15, "end": 17}],
                    "posting_frequency_min": 2,
                    "posting_frequency_max": 3,
                    "source": "Test source"
                }
            ]
            
            service = PlatformTimingService("mock_url", "mock_key")
            
            # Test getting timing data
            timing_data = await service.get_platform_timing_data("youtube")
            assert timing_data is not None
            assert timing_data.platform_id == "youtube"
            print("✓ Get platform timing data works")
            
            # Test getting user preferences
            mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
                {
                    "user_id": "test_user",
                    "timezone": "UTC",
                    "posting_frequency_min": 2,
                    "posting_frequency_max": 4
                }
            ]
            
            prefs = await service.get_user_scheduling_preferences("test_user")
            assert prefs is not None
            assert prefs.user_id == "test_user"
            print("✓ Get user preferences works")
            
            # Test logging KPI
            kpi_success = await service.log_performance_kpi(
                video_job_id="test_video",
                platform_id="youtube",
                views=1000,
                impressions=3000,
                engagement_rate=0.05
            )
            assert kpi_success is True
            print("✓ Log KPI event works")
            
            return True
            
    except Exception as e:
        print(f"✗ Database operation tests failed: {e}")
        return False


def test_configuration():
    """Test configuration management"""
    print("\n=== Testing Configuration ===")
    
    try:
        from config import load_config_from_env, validate_config
        
        # Test loading configuration from environment variables
        import os
        os.environ["SUPABASE_URL"] = "test_url"
        os.environ["SUPABASE_KEY"] = "test_key"
        os.environ["API_KEY"] = "test_api_key"
        
        config = load_config_from_env()
        assert config.database.supabase_url == "test_url"
        assert config.database.supabase_key == "test_key"
        assert config.api.api_key == "test_api_key"
        print("✓ Configuration loading works")
        
        # Test validation
        from config import DatabaseConfig, APIConfig, ServiceConfig
        
        valid_config = ServiceConfig(
            database=DatabaseConfig("test_url", "test_key"),
            api=APIConfig("test_base_url", "test_api_key")
        )
        
        is_valid = validate_config(valid_config)
        assert is_valid is True
        print("✓ Configuration validation works")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration tests failed: {e}")
        return False


def test_integration_scenarios():
    """Test complete integration scenarios"""
    print("\n=== Testing Integration Scenarios ===")
    
    try:
        service = PlatformTimingService.__new__(PlatformTimingService)
        service.platform_timing_bases = service._load_platform_timing_bases()
        
        # Test multi-platform scenario
        platforms_to_test = ["youtube", "instagram", "tiktok"]
        
        for platform in platforms_to_test:
            assert platform in service.platform_timing_bases
            platform_data = service.platform_timing_bases[platform]
            
            # Verify platform has valid data structure
            assert isinstance(platform_data["days"], list)
            assert isinstance(platform_data["peak_hours"], list)
            assert isinstance(platform_data["posting_frequency_min"], int)
            assert isinstance(platform_data["posting_frequency_max"], int)
            
            print(f"✓ {platform.title()} integration test passed")
        
        # Test content format data
        youtube_formats = service.platform_timing_bases["youtube"].get("content_formats", {})
        assert "long_form" in youtube_formats
        assert "shorts" in youtube_formats
        print("✓ Content format data integration test passed")
        
        # Test audience segment data
        tiktok_segments = service.platform_timing_bases["tiktok"].get("audience_segments", {})
        assert "general" in tiktok_segments
        assert "weekend" in tiktok_segments
        print("✓ Audience segment data integration test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration scenario tests failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Platform Timing Service - Basic Validation Tests")
    print("=" * 60)
    
    tests = [
        ("Data Structures", test_data_structures),
        ("Timing Calculations", test_timing_calculations),
        ("Platform Data Loading", test_platform_data_loading),
        ("Configuration", test_configuration),
        ("Integration Scenarios", test_integration_scenarios),
    ]
    
    results = []
    
    # Run synchronous tests
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Run async tests
    print("\n=== Running Async Tests ===")
    try:
        async_result = asyncio.run(test_mock_database_operations())
        results.append(("Database Operations", async_result))
    except Exception as e:
        print(f"✗ Database Operations failed with exception: {e}")
        results.append(("Database Operations", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 All tests passed! The Platform Timing Service is ready to use.")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())