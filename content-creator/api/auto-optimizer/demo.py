#!/usr/bin/env python3
"""
Auto-Optimizer Demo Script

Demonstrates the automated content optimization system capabilities.
"""

import json
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.auto_optimizer import (
    AutoOptimizerAPI, 
    create_auto_optimizer, 
    quick_optimize,
    AutoOptimizer
)


def demo_basic_optimization():
    """Demo basic content optimization."""
    print("=== Basic Content Optimization Demo ===")
    
    # Sample content to optimize
    sample_content = {
        "content_id": "demo_001",
        "title": "A tutorial about coding",
        "content_type": "video",
        "tags": ["coding", "tutorial", "video"],
        "platform": "youtube",
        "estimated_length": 200,
        "performance_score": 0.4
    }
    
    print(f"Original Content:")
    print(f"  Title: {sample_content['title']}")
    print(f"  Tags: {sample_content['tags']}")
    print(f"  Performance Score: {sample_content['performance_score']}")
    
    # Quick optimization
    result = quick_optimize(sample_content, optimization_level="medium")
    
    if result['success']:
        optimized = result['data']
        print(f"\nOptimization Applied: {optimized['optimization_applied']}")
        print(f"Confidence Score: {optimized['confidence_score']:.2f}")
        print(f"Expected Improvement: {optimized['expected_improvement']:.2%}")
        
        if optimized['optimization_applied']:
            print(f"\nOptimized Title: {optimized['content']['title']}")
            print(f"Optimized Tags: {optimized['content'].get('tags', [])}")
            print(f"Applied Optimizations: {optimized['applied_optimizations']}")
    else:
        print(f"Optimization failed: {result['error']}")


def demo_api_wrapper():
    """Demo the AutoOptimizerAPI wrapper."""
    print("\n=== AutoOptimizerAPI Demo ===")
    
    # Create API instance
    api = AutoOptimizerAPI()
    
    # Sample content context
    content_context = {
        "content_type": "video",
        "platform": "youtube",
        "target_audience": "developers",
        "current_performance": 0.3
    }
    
    # Get optimization recommendations
    recommendations = api.get_optimization_recommendations(content_context)
    
    print(f"Optimization Recommendations:")
    if recommendations['success']:
        data = recommendations['data']
        print(f"  Analysis Timestamp: {data['analysis_timestamp']}")
        print(f"  Content Context: {data['content_context']}")
        
        if 'recommendations' in data:
            print(f"  Number of Recommendations: {len(data['recommendations'])}")
            for i, rec in enumerate(data['recommendations'][:3]):
                print(f"    {i+1}. {rec['optimization_type']} (confidence: {rec['confidence']:.2f})")
    else:
        print(f"  Error: {recommendations['error']}")


def demo_pattern_analysis():
    """Demo pattern analysis functionality."""
    print("\n=== Pattern Analysis Demo ===")
    
    api = AutoOptimizerAPI()
    
    # Analyze patterns for the last 30 days
    patterns = api.analyze_content_patterns(days_back=30)
    
    print(f"Content Performance Patterns:")
    if patterns['success']:
        data = patterns['data']
        print(f"  Analysis Period: {data.get('period_days', 'N/A')} days")
        print(f"  Content Count: {data.get('content_count', 0)}")
        
        if 'patterns' in data:
            patterns_data = data['patterns']
            
            # Show successful tags
            if 'successful_tags' in patterns_data:
                tags = patterns_data['successful_tags']
                print(f"  Top Performing Tags:")
                for tag, stats in list(tags.get('top_performing_tags', {}).items())[:3]:
                    print(f"    {tag}: {stats['avg_performance']:.2f} performance")
            
            # Show optimal timing
            if 'optimal_timing' in patterns_data:
                timing = patterns_data['optimal_timing']
                print(f"  Best Posting Times:")
                for day, score in list(timing.get('best_weekdays', {}).items())[:2]:
                    print(f"    {day}: {score:.2f} average performance")
    else:
        print(f"  Error: {patterns['error']}")


def demo_learning_system():
    """Demo the learning system."""
    print("\n=== Learning System Demo ===")
    
    api = AutoOptimizerAPI()
    
    # Get learning insights
    insights = api.get_learning_insights(days_back=30)
    
    print(f"Learning System Insights:")
    if insights['success']:
        data = insights['data']
        print(f"  Analysis Period: {data.get('analysis_period_days', 'N/A')} days")
        print(f"  Total Learning Events: {data.get('total_events', 0)}")
        print(f"  Overall Success Rate: {data.get('overall_success_rate', 0):.1%}")
        print(f"  Average Improvement: {data.get('average_improvement', 0):.2%}")
        
        if 'optimization_insights' in data:
            insights_data = data['optimization_insights']
            if 'best_performing' in insights_data:
                print(f"  Best Performing Optimizations:")
                for opt_type, stats in list(insights_data['best_performing'].items())[:2]:
                    print(f"    {opt_type}: {stats['success_rate']:.1%} success rate")
    else:
        print(f"  Error: {insights['error']}")


def demo_system_status():
    """Demo system status check."""
    print("\n=== System Status Demo ===")
    
    api = AutoOptimizerAPI()
    
    # Get system status
    status = api.get_system_status()
    
    print(f"Auto-Optimizer System Status:")
    if status['success']:
        data = status['data']
        
        # System health
        if 'system_status' in data:
            sys_status = data['system_status']
            print(f"  System Running: {sys_status.get('is_running', False)}")
            print(f"  Total Optimizations: {sys_status.get('total_optimizations', 0)}")
            print(f"  Average Confidence: {sys_status.get('average_confidence', 0):.2f}")
        
        # Configuration summary
        if 'configuration' in data:
            config = data['configuration']
            print(f"  Active Optimizations: {config.get('auto_apply_enabled', 0)}")
            print(f"  Configured Platforms: {config.get('total_platforms', 0)}")
        
        # System health
        if 'system_health' in data:
            health = data['system_health']
            print(f"  Overall Health: {health.get('status', 'unknown')}")
    else:
        print(f"  Error: {status['error']}")


def demo_configuration():
    """Demo system configuration."""
    print("\n=== Configuration Demo ===")
    
    api = AutoOptimizerAPI()
    
    # Configure optimization settings
    config_result = api.configure_optimization(
        enabled=True,
        optimization_level="medium",
        global_settings={
            "min_improvement_threshold": 0.05,
            "max_concurrent_optimizations": 3,
            "confidence_threshold": 0.7
        }
    )
    
    print(f"Configuration Update:")
    if config_result['success']:
        data = config_result['data']
        print(f"  Auto-optimizer Configured: {data.get('auto_optimizer_configured', False)}")
        print(f"  Settings Updated: {data.get('global_settings_updated', [])}")
    else:
        print(f"  Error: {config_result['error']}")


def demo_optimization_tips():
    """Demo optimization tips."""
    print("\n=== Optimization Tips Demo ===")
    
    api = AutoOptimizerAPI()
    
    # Get tips for different content types
    content_types = ["video", "text", "social"]
    
    for content_type in content_types:
        tips = api.get_optimization_tips(content_type)
        if tips['success']:
            print(f"\n  {content_type.title()} Content Tips:")
            for i, tip in enumerate(tips['data']['tips'][:3], 1):
                print(f"    {i}. {tip}")


def main():
    """Run all demo functions."""
    print("Automated Content Optimization System Demo")
    print("=" * 50)
    print(f"Demo started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Run demos
        demo_basic_optimization()
        demo_api_wrapper()
        demo_pattern_analysis()
        demo_learning_system()
        demo_system_status()
        demo_configuration()
        demo_optimization_tips()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nNext steps:")
        print("1. Integrate with your content pipeline")
        print("2. Configure optimization parameters")
        print("3. Start continuous optimization")
        print("4. Monitor performance improvements")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        print("This might be due to missing database or configuration files.")
        print("The auto-optimizer will create default configurations automatically.")


if __name__ == "__main__":
    main()