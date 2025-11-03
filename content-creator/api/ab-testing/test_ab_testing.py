"""
Test suite for A/B testing system

Simple tests to verify core functionality works correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the API directory to the path
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(api_dir)

from ab_testing import (
    ContentType, 
    ABTestManager,
    ABTestConfig,
    SignificanceLevel,
    SelectionStrategy
)
from ab_testing.content_variations import ContentVariationManager
from ab_testing.performance_tracker import PerformanceTracker, MetricType
from ab_testing.statistical_tests import StatisticalAnalyzer, StatisticalTest
from ab_testing.winner_selector import WinnerSelector

def test_variation_manager():
    """Test content variation management."""
    print("Testing Content Variation Manager...")
    
    manager = ContentVariationManager()
    
    # Test title variations
    variations = manager.generate_title_variations(
        base_title="Test Video Title",
        experiment_id="test_exp_1",
        count=3,
        style="emotional"
    )
    
    assert len(variations) == 3, f"Expected 3 variations, got {len(variations)}"
    assert all(v.content_type == ContentType.TITLE for v in variations), "Wrong content type"
    
    print("✓ Title variations created successfully")
    
    # Test thumbnail variations
    base_config = {"style": "text_overlay", "colors": ["#000", "#fff"]}
    thumb_variations = manager.generate_thumbnail_variations(
        base_thumbnail_config=base_config,
        experiment_id="test_exp_2",
        count=2
    )
    
    assert len(thumb_variations) == 2, f"Expected 2 thumbnail variations, got {len(thumb_variations)}"
    assert all(v.content_type == ContentType.THUMBNAIL for v in thumb_variations), "Wrong thumbnail content type"
    
    print("✓ Thumbnail variations created successfully")
    
    # Test posting time variations
    base_time = datetime(2025, 11, 1, 12, 0, 0)
    time_variations = manager.generate_posting_time_variations(
        base_time=base_time,
        experiment_id="test_exp_3",
        count=3
    )
    
    assert len(time_variations) == 3, f"Expected 3 time variations, got {len(time_variations)}"
    assert all(v.content_type == ContentType.POSTING_TIME for v in time_variations), "Wrong time content type"
    
    print("✓ Posting time variations created successfully")
    
    return True

def test_performance_tracker():
    """Test performance tracking."""
    print("\nTesting Performance Tracker...")
    
    tracker = PerformanceTracker()
    
    # Test single metric tracking
    metric_id = tracker.track_metric(
        variation_id="test_var_1",
        metric_type=MetricType.CLICKS,
        value=150,
        platform="youtube"
    )
    
    assert metric_id is not None, "Metric ID should be generated"
    
    print("✓ Single metric tracking works")
    
    # Test batch tracking
    metrics_data = [
        {
            "variation_id": "test_var_2",
            "metric_type": "impressions",
            "value": 1000,
            "platform": "youtube"
        },
        {
            "variation_id": "test_var_2", 
            "metric_type": "clicks",
            "value": 50,
            "platform": "youtube"
        }
    ]
    
    metric_ids = tracker.batch_track_metrics(metrics_data)
    assert len(metric_ids) == 2, f"Expected 2 metric IDs, got {len(metric_ids)}"
    
    print("✓ Batch metric tracking works")
    
    # Test aggregated metrics
    aggregated = tracker.get_aggregated_metrics("test_var_2")
    assert "impressions_total" in aggregated, "Missing impressions_total in aggregated metrics"
    assert aggregated["impressions_total"] == 1000, f"Expected 1000 impressions, got {aggregated['impressions_total']}"
    
    print("✓ Aggregated metrics calculation works")
    
    return True

def test_statistical_analyzer():
    """Test statistical analysis."""
    print("\nTesting Statistical Analyzer...")
    
    analyzer = StatisticalAnalyzer()
    
    # Create sample data
    group_a = [3.2, 2.8, 3.5, 3.1, 2.9, 3.0, 3.3, 2.7, 3.4, 3.1]
    group_b = [2.8, 2.5, 3.1, 2.9, 2.6, 2.7, 3.0, 2.4, 2.9, 2.8]
    
    # Test t-test
    result = analyzer.analyze_ab_test(
        group_a, group_b, 
        test_type=StatisticalTest.T_TEST,
        significance_level=SignificanceLevel.P05
    )
    
    assert result.test_type == "t_test", f"Expected t_test, got {result.test_type}"
    assert 0 <= result.p_value <= 1, f"P-value should be between 0 and 1, got {result.p_value}"
    assert isinstance(result.is_significant, bool), "is_significant should be boolean"
    
    print(f"✓ T-test works: p-value={result.p_value:.4f}, significant={result.is_significant}")
    
    # Test sample size calculation
    required_n = analyzer.sample_size_calculation(
        baseline_rate=0.03,
        minimum_detectable_effect=0.01
    )
    
    assert required_n > 0, f"Sample size should be positive, got {required_n}"
    assert isinstance(required_n, int), f"Sample size should be integer, got {type(required_n)}"
    
    print(f"✓ Sample size calculation works: {required_n}")
    
    return True

def test_winner_selector():
    """Test winner selection."""
    print("\nTesting Winner Selector...")
    
    selector = WinnerSelector()
    
    # Create sample variation metrics
    variation_metrics = {
        "var_1": {
            "click_through_rate_average": 5.2,
            "engagement_rate_average": 3.8,
            "impressions_total": 1200,
            "conversion_rate_average": 1.5
        },
        "var_2": {
            "click_through_rate_average": 4.8,
            "engagement_rate_average": 3.5,
            "impressions_total": 1100,
            "conversion_rate_average": 1.3
        }
    }
    
    test_start_time = datetime.now() - timedelta(days=2)
    
    # Test different selection strategies
    strategies = [SelectionStrategy.BEST_PERFORMANCE, SelectionStrategy.HYBRID]
    
    for strategy in strategies:
        result = selector.select_winner(
            variation_metrics,
            test_start_time,
            strategy
        )
        
        assert result.winner_variation_id in ["var_1", "var_2"], "Winner should be one of the variations"
        assert 0 <= result.confidence_score <= 1, "Confidence should be between 0 and 1"
        assert isinstance(result.is_winner_selected, bool), "is_winner_selected should be boolean"
        
        print(f"✓ {strategy.value} strategy works: winner={result.winner_variation_id}, confidence={result.confidence_score:.3f}")
    
    return True

def test_ab_test_manager():
    """Test main A/B test manager."""
    print("\nTesting AB Test Manager...")
    
    config = ABTestConfig(
        min_sample_size=50,
        test_duration_days=1
    )
    
    manager = ABTestManager(config=config)
    
    # Test title test creation
    test_id = manager.create_test(
        name="Test Title Optimization",
        description="Testing different titles",
        content_type=ContentType.TITLE,
        base_content="Sample Video Title",
        variation_count=2
    )
    
    assert test_id is not None, "Test ID should be generated"
    assert test_id in manager.tests, "Test should be saved in manager"
    
    print("✓ Test creation works")
    
    # Test starting test
    success = manager.start_test(test_id)
    assert success, "Test should start successfully"
    
    test = manager.tests[test_id]
    assert test.status.value == "running", f"Test status should be running, got {test.status.value}"
    
    print("✓ Test starting works")
    
    # Test getting test status
    status = manager.get_test_status(test_id)
    assert status is not None, "Status should be returned"
    assert "test" in status, "Status should contain test info"
    assert "current_metrics" in status, "Status should contain metrics"
    
    print("✓ Test status retrieval works")
    
    # Test getting all tests
    all_tests = manager.get_all_tests()
    assert len(all_tests) >= 1, "Should have at least one test"
    
    print("✓ Getting all tests works")
    
    return True

def test_integration():
    """Test full integration."""
    print("\nTesting Full Integration...")
    
    # Create integrated test
    manager = ABTestManager()
    
    # Create test
    test_id = manager.create_test(
        name="Integration Test",
        description="Full integration test",
        content_type=ContentType.TITLE,
        base_content="Integration Test Video",
        variation_count=2
    )
    
    # Start test
    manager.start_test(test_id)
    
    # Get test and variations
    test = manager.tests[test_id]
    variation_ids = test.variation_ids
    
    # Add some performance data
    for i, var_id in enumerate(variation_ids):
        impressions = 100 + (i * 50)
        clicks = impressions * 0.05
        
        manager.performance_tracker.track_metric(
            variation_id=var_id,
            metric_type=MetricType.IMPRESSIONS,
            value=impressions,
            platform="youtube"
        )
        manager.performance_tracker.track_metric(
            variation_id=var_id,
            metric_type=MetricType.CLICKS,
            value=clicks,
            platform="youtube"
        )
    
    # Analyze test
    analysis = manager.analyze_test(test_id)
    assert analysis is not None, "Analysis should complete"
    
    print("✓ Full integration test works")
    
    # Export data
    export_data = manager.export_test_data(test_id)
    assert "test_info" in export_data, "Export should contain test info"
    assert "variations" in export_data, "Export should contain variations"
    
    print("✓ Data export works")
    
    return True

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("A/B Testing System - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Content Variation Manager", test_variation_manager),
        ("Performance Tracker", test_performance_tracker),
        ("Statistical Analyzer", test_statistical_analyzer),
        ("Winner Selector", test_winner_selector),
        ("AB Test Manager", test_ab_test_manager),
        ("Integration Test", test_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            result = test_func()
            if result:
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! A/B testing system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
