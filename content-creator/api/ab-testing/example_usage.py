"""
Example Usage of A/B Testing System

This script demonstrates how to use the A/B testing system for content variations.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path to import the ab-testing module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ab_testing import (
    ContentType, 
    ABTestManager,
    ABTestConfig,
    SignificanceLevel,
    SelectionStrategy
)

def example_title_ab_test():
    """Example of A/B testing for video titles."""
    
    print("=== Title A/B Test Example ===")
    
    # Create A/B test manager
    config = ABTestConfig(
        min_sample_size=200,
        significance_level=SignificanceLevel.P05,
        test_duration_days=7,
        auto_stop_enabled=True
    )
    
    manager = ABTestManager(config=config)
    
    # Create title test
    base_title = "10 Tips for Better Video Editing"
    test_id = manager.create_test(
        name="Video Title Test",
        description="Testing different title formats for video engagement",
        content_type=ContentType.TITLE,
        base_content=base_title,
        variation_count=3
    )
    
    print(f"Created test: {test_id}")
    
    # Start the test
    success = manager.start_test(test_id)
    print(f"Test started: {success}")
    
    # Simulate some performance data
    from ab_testing.performance_tracker import MetricType
    
    # Get variation IDs
    test = manager.tests[test_id]
    variation_ids = test.variation_ids
    
    # Simulate metrics for each variation
    # Variation 1: 1200 impressions, 60 clicks, 5% engagement
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[0],
        metric_type=MetricType.IMPRESSIONS,
        value=1200,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[0],
        metric_type=MetricType.CLICKS,
        value=60,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[0],
        metric_type=MetricType.LIKES,
        value=30,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[0],
        metric_type=MetricType.COMMENTS,
        value=5,
        platform="youtube"
    )
    
    # Variation 2: 1100 impressions, 45 clicks, 4% engagement
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[1],
        metric_type=MetricType.IMPRESSIONS,
        value=1100,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[1],
        metric_type=MetricType.CLICKS,
        value=45,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[1],
        metric_type=MetricType.LIKES,
        value=25,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[1],
        metric_type=MetricType.COMMENTS,
        value=3,
        platform="youtube"
    )
    
    # Variation 3: 1050 impressions, 40 clicks, 3.5% engagement
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[2],
        metric_type=MetricType.IMPRESSIONS,
        value=1050,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[2],
        metric_type=MetricType.CLICKS,
        value=40,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[2],
        metric_type=MetricType.LIKES,
        value=20,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[2],
        metric_type=MetricType.COMMENTS,
        value=2,
        platform="youtube"
    )
    
    # Analyze the test
    analysis = manager.analyze_test(test_id)
    print(f"Analysis result: {analysis}")
    
    # Check test status
    status = manager.get_test_status(test_id)
    print(f"Test status: {status['test']['status']}")
    
    return manager, test_id

def example_thumbnail_ab_test():
    """Example of A/B testing for video thumbnails."""
    
    print("\n=== Thumbnail A/B Test Example ===")
    
    manager = ABTestManager()
    
    # Base thumbnail configuration
    base_thumbnail = {
        "style": "text_overlay",
        "colors": ["#FF0000", "#FFFFFF"],
        "text_position": "center",
        "background": "solid"
    }
    
    test_id = manager.create_test(
        name="Thumbnail Style Test",
        description="Testing different thumbnail styles for click-through rate",
        content_type=ContentType.THUMBNAIL,
        base_content=base_thumbnail,
        variation_count=4
    )
    
    print(f"Created thumbnail test: {test_id}")
    manager.start_test(test_id)
    
    # Simulate performance data for thumbnails
    test = manager.tests[test_id]
    variation_ids = test.variation_ids
    
    for i, variation_id in enumerate(variation_ids):
        # Different performance for each thumbnail style
        impressions = 800 + (i * 50)
        clicks = impressions * (0.08 - i * 0.01)  # Varying CTR
        
        manager.performance_tracker.track_metric(
            variation_id=variation_id,
            metric_type=MetricType.IMPRESSIONS,
            value=impressions,
            platform="youtube"
        )
        manager.performance_tracker.track_metric(
            variation_id=variation_id,
            metric_type=MetricType.CLICKS,
            value=clicks,
            platform="youtube"
        )
    
    return manager, test_id

def example_posting_time_ab_test():
    """Example of A/B testing for posting times."""
    
    print("\n=== Posting Time A/B Test Example ===")
    
    manager = ABTestManager()
    
    # Base posting time
    base_time = datetime(2025, 11, 1, 12, 0, 0)  # 12 PM on Nov 1, 2025
    
    test_id = manager.create_test(
        name="Optimal Posting Time Test",
        description="Finding the best time to post for maximum engagement",
        content_type=ContentType.POSTING_TIME,
        base_content=base_time,
        variation_count=3
    )
    
    print(f"Created posting time test: {test_id}")
    manager.start_test(test_id)
    
    # Simulate performance data for different posting times
    test = manager.tests[test_id]
    variation_ids = test.variation_ids
    
    # Morning post (9 AM)
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[0],
        metric_type=MetricType.IMPRESSIONS,
        value=900,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[0],
        metric_type=MetricType.ENGAGEMENT_RATE,
        value=3.5,
        platform="youtube"
    )
    
    # Afternoon post (3 PM)
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[1],
        metric_type=MetricType.IMPRESSIONS,
        value=1200,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[1],
        metric_type=MetricType.ENGAGEMENT_RATE,
        value=4.2,
        platform="youtube"
    )
    
    # Evening post (6 PM)
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[2],
        metric_type=MetricType.IMPRESSIONS,
        value=1100,
        platform="youtube"
    )
    manager.performance_tracker.track_metric(
        variation_id=variation_ids[2],
        metric_type=MetricType.ENGAGEMENT_RATE,
        value=3.8,
        platform="youtube"
    )
    
    return manager, test_id

def demonstrate_statistical_analysis():
    """Demonstrate statistical analysis capabilities."""
    
    print("\n=== Statistical Analysis Demonstration ===")
    
    from ab_testing.statistical_tests import StatisticalAnalyzer
    
    analyzer = StatisticalAnalyzer()
    
    # Generate sample data
    group_a = [3.2, 2.8, 3.5, 3.1, 2.9, 3.0, 3.3, 2.7, 3.4, 3.1]
    group_b = [2.8, 2.5, 3.1, 2.9, 2.6, 2.7, 3.0, 2.4, 2.9, 2.8]
    
    # Perform different statistical tests
    tests = [
        StatisticalAnalyzer().analyze_ab_test(group_a, group_b, StatisticalTest.T_TEST),
        StatisticalAnalyzer().analyze_ab_test(group_a, group_b, StatisticalTest.Z_TEST),
        StatisticalAnalyzer().analyze_ab_test(group_a, group_b, StatisticalTest.MANN_WHITNEY_U)
    ]
    
    for test in tests:
        print(f"\nTest: {test.test_type}")
        print(f"P-value: {test.p_value:.4f}")
        print(f"Significant: {test.is_significant}")
        print(f"Effect size: {test.effect_size:.4f}")
        print(f"Confidence interval: {test.confidence_interval}")
    
    # Export comprehensive report
    report = analyzer.export_analysis_report(tests)
    print(f"\nFull analysis report: {report}")

def demonstrate_winner_selection():
    """Demonstrate automatic winner selection."""
    
    print("\n=== Winner Selection Demonstration ===")
    
    from ab_testing.winner_selector import WinnerSelector
    
    selector = WinnerSelector()
    
    # Sample variation metrics
    variation_metrics = {
        "var_1": {
            "click_through_rate_average": 5.2,
            "engagement_rate_average": 3.8,
            "conversion_rate_average": 1.5,
            "impressions_total": 1200
        },
        "var_2": {
            "click_through_rate_average": 4.8,
            "engagement_rate_average": 3.5,
            "conversion_rate_average": 1.3,
            "impressions_total": 1100
        },
        "var_3": {
            "click_through_rate_average": 5.5,
            "engagement_rate_average": 4.1,
            "conversion_rate_average": 1.7,
            "impressions_total": 1150
        }
    }
    
    # Test different selection strategies
    strategies = [
        SelectionStrategy.BEST_PERFORMANCE,
        SelectionStrategy.HYBRID,
        SelectionStrategy.REVENUE_OPTIMIZED
    ]
    
    test_start_time = datetime.now() - timedelta(days=2)
    
    for strategy in strategies:
        print(f"\nUsing strategy: {strategy.value}")
        result = selector.select_winner(
            variation_metrics,
            test_start_time,
            strategy
        )
        
        print(f"Winner: {result.winner_variation_id}")
        print(f"Confidence: {result.confidence_score:.3f}")
        print(f"Selected: {result.is_winner_selected}")
        print(f"Reason: {result.selection_reason}")
    
    # Get recommendations
    recommendations = selector.get_selection_recommendations(variation_metrics)
    print(f"\nRecommendations: {recommendations}")

def main():
    """Run all examples."""
    
    print("A/B Testing System Example Usage")
    print("=" * 50)
    
    # Run examples
    try:
        # Title test
        manager1, test_id1 = example_title_ab_test()
        
        # Thumbnail test
        manager2, test_id2 = example_thumbnail_ab_test()
        
        # Posting time test
        manager3, test_id3 = example_posting_time_ab_test()
        
        # Statistical analysis demonstration
        demonstrate_statistical_analysis()
        
        # Winner selection demonstration
        demonstrate_winner_selection()
        
        # Show test results
        print("\n=== Final Test Results ===")
        
        tests = [test_id1, test_id2, test_id3]
        managers = [manager1, manager2, manager3]
        
        for i, (manager, test_id) in enumerate(zip(managers, tests)):
            print(f"\nTest {i+1}:")
            status = manager.get_test_status(test_id)
            if status:
                print(f"  Status: {status['test']['status']}")
                print(f"  Variations: {len(status['variation_statuses'])}")
                
                # Export test data
                export_data = manager.export_test_data(test_id)
                print(f"  Export successful: {len(export_data.get('variations', {}))} variations exported")
        
        print("\n=== Example Complete ===")
        print("All A/B testing features demonstrated successfully!")
        
    except Exception as e:
        print(f"Error during example execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
