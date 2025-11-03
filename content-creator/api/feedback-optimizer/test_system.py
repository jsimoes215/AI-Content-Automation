#!/usr/bin/env python3
"""
Test script for the Feedback-Driven Content Improvement Optimizer

This script demonstrates the key functionality of the system by processing
sample feedback data and generating improvement recommendations.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feedback_optimizer import LearningEngine
from feedback_optimizer.models.feedback_data import FeedbackData
from feedback_optimizer.models.sentiment_metrics import SentimentMetrics


def create_sample_feedback_data() -> List[Dict[str, Any]]:
    """Create sample feedback data for testing."""
    return [
        {
            'content_id': 'video_001',
            'feedback_type': 'comment',
            'text': 'This video was absolutely amazing! The script was really well-structured and the thumbnail caught my attention immediately.',
            'engagement_metrics': {'views': 1500, 'likes': 85, 'comments': 12, 'shares': 5},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'script',
                'device': 'mobile',
                'time_of_day': 'evening'
            },
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            'content_id': 'video_001',
            'feedback_type': 'comment',
            'text': 'Great content but the title could be more compelling. Also, maybe add a stronger call to action at the end?',
            'engagement_metrics': {'views': 1500, 'likes': 85, 'comments': 12, 'shares': 5},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'title',
                'device': 'desktop',
                'time_of_day': 'afternoon'
            },
            'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            'content_id': 'video_002',
            'feedback_type': 'comment',
            'text': 'The video was too long and I got bored halfway through. The pacing was really slow.',
            'engagement_metrics': {'views': 800, 'likes': 15, 'comments': 8, 'shares': 1},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'script',
                'device': 'mobile',
                'time_of_day': 'morning'
            },
            'timestamp': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'content_id': 'video_002',
            'feedback_type': 'comment',
            'text': 'Good information but the thumbnail was not very eye-catching. I almost skipped it.',
            'engagement_metrics': {'views': 800, 'likes': 15, 'comments': 8, 'shares': 1},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'thumbnail',
                'device': 'mobile',
                'time_of_day': 'evening'
            },
            'timestamp': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'content_id': 'video_003',
            'feedback_type': 'like',
            'text': '',
            'engagement_metrics': {'views': 2000, 'likes': 120, 'comments': 25, 'shares': 15},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'script',
                'device': 'desktop',
                'time_of_day': 'evening'
            },
            'timestamp': (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            'content_id': 'video_003',
            'feedback_type': 'comment',
            'text': 'Love your content! This video in particular was very informative and well-presented.',
            'engagement_metrics': {'views': 2000, 'likes': 120, 'comments': 25, 'shares': 15},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'script',
                'device': 'desktop',
                'time_of_day': 'evening'
            },
            'timestamp': (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            'content_id': 'video_004',
            'feedback_type': 'comment',
            'text': 'Not bad but the audio quality could be better. Also, the script felt a bit repetitive.',
            'engagement_metrics': {'views': 600, 'likes': 8, 'comments': 3, 'shares': 0},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'script',
                'device': 'mobile',
                'time_of_day': 'afternoon'
            },
            'timestamp': (datetime.now() - timedelta(days=4)).isoformat()
        },
        {
            'content_id': 'video_005',
            'feedback_type': 'comment',
            'text': 'Excellent video! The intro was compelling and I watched the whole thing. Great thumbnail design too!',
            'engagement_metrics': {'views': 1800, 'likes': 95, 'comments': 18, 'shares': 8},
            'metadata': {
                'platform': 'youtube',
                'content_type': 'script',
                'device': 'mobile',
                'time_of_day': 'evening'
            },
            'timestamp': (datetime.now() - timedelta(days=5)).isoformat()
        }
    ]


def run_basic_analysis_test():
    """Run basic analysis test."""
    print("🔍 Running Basic Analysis Test...")
    print("=" * 50)
    
    try:
        # Initialize the learning engine
        engine = LearningEngine()
        print("✅ Learning engine initialized successfully")
        
        # Create sample feedback data
        feedback_data = create_sample_feedback_data()
        print(f"📊 Created {len(feedback_data)} sample feedback items")
        
        # Run complete learning cycle
        results = engine.process_feedback_learning_cycle(feedback_data)
        print("✅ Analysis completed successfully")
        
        # Display results
        analysis_results = results['analysis_results']
        recommendations = results['recommendations']
        learning_insights = results['learning_insights']
        
        # Print overall score
        overall_score = analysis_results.get('overall_score', 0)
        print(f"\n📈 Overall Content Quality Score: {overall_score:.2f}")
        
        # Print sentiment patterns
        sentiment_patterns = analysis_results.get('sentiment_patterns', {})
        sentiment_dist = sentiment_patterns.get('distribution', {})
        print(f"\n😊 Sentiment Distribution:")
        for sentiment, count in sentiment_dist.items():
            print(f"   {sentiment.title()}: {count}")
        
        # Print engagement patterns
        engagement_patterns = analysis_results.get('engagement_patterns', {})
        avg_engagement = engagement_patterns.get('average_engagement_rate', 0)
        print(f"\n📊 Average Engagement Rate: {avg_engagement:.1%}")
        
        # Print recommendations
        print(f"\n💡 Generated {len(recommendations)} Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
            print(f"   {i}. {rec.title}")
            print(f"      Priority: {rec.priority.value.title()}")
            print(f"      Impact: {rec.impact_score:.1%}")
            print(f"      Time: {rec.estimated_time_hours}h")
            print()
        
        # Print key learnings
        print("🧠 Key Learning Insights:")
        key_learnings = learning_insights.get('pattern_recognition', {})
        print(f"   Patterns identified: {len(key_learnings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def run_predictive_insights_test():
    """Test predictive insights generation."""
    print("\n🔮 Running Predictive Insights Test...")
    print("=" * 50)
    
    try:
        engine = LearningEngine()
        feedback_data = create_sample_feedback_data()
        
        # Generate predictive insights
        insights = engine.generate_predictive_insights(feedback_data)
        print("✅ Predictive insights generated successfully")
        
        # Display predictions
        predictions = insights.get('performance_predictions', {})
        print(f"\n🔮 Performance Predictions:")
        print(f"   Sentiment Trend: {predictions.get('sentiment_prediction', 'unknown')}")
        print(f"   Engagement Prediction: {predictions.get('engagement_prediction', 'unknown')}")
        print(f"   Overall Performance: {predictions.get('overall_performance_prediction', 'unknown')}")
        
        # Display emerging trends
        emerging_trends = insights.get('emerging_trends', [])
        print(f"\n📈 Emerging Trends: {len(emerging_trends)} identified")
        for trend in emerging_trends:
            print(f"   - {trend['pattern']} (confidence: {trend['confidence']:.1%})")
        
        # Display proactive recommendations
        proactive_recs = insights.get('proactive_recommendations', [])
        print(f"\n⚡ Proactive Recommendations: {len(proactive_recs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Predictive insights test failed: {str(e)}")
        return False


def run_implementation_tracking_test():
    """Test implementation result tracking."""
    print("\n📝 Running Implementation Tracking Test...")
    print("=" * 50)
    
    try:
        engine = LearningEngine()
        
        # Simulate implementation results
        implementation_results = {
            'recommendation_id': 'rec_001',
            'implementation_date': datetime.now().isoformat(),
            'before_metrics': {
                'sentiment_score': 0.45,
                'engagement_rate': 0.025,
                'content_quality': 0.60
            },
            'after_metrics': {
                'sentiment_score': 0.62,
                'engagement_rate': 0.038,
                'content_quality': 0.75
            },
            'notes': 'Improved script opening hook and added stronger CTA',
            'actual_time_hours': 2.5,
            'estimated_time_hours': 3.0
        }
        
        # Track implementation
        learning_feedback = engine.learn_from_implementation_results(
            'rec_001',
            implementation_results
        )
        print("✅ Implementation results tracked successfully")
        
        # Display results
        success_analysis = learning_feedback.get('success_analysis', {})
        print(f"\n🎯 Implementation Success Analysis:")
        print(f"   Success Score: {success_analysis.get('success_score', 0):.2f}")
        print(f"   Overall Impact: {success_analysis.get('overall_impact', 'unknown')}")
        print(f"   Metrics Improved: {len(success_analysis.get('metrics_improved', []))}")
        print(f"   Metrics Degraded: {len(success_analysis.get('metrics_degraded', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Implementation tracking test failed: {str(e)}")
        return False


def run_learning_summary_test():
    """Test learning summary generation."""
    print("\n📊 Running Learning Summary Test...")
    print("=" * 50)
    
    try:
        engine = LearningEngine()
        
        # Run a few cycles to build learning history
        feedback_data = create_sample_feedback_data()
        for _ in range(3):
            engine.process_feedback_learning_cycle(feedback_data)
        
        # Generate learning summary
        summary = engine.get_learning_summary(days_back=30)
        print("✅ Learning summary generated successfully")
        
        # Display summary
        print(f"\n📈 Learning Summary:")
        print(f"   Learning Cycles: {summary.get('learning_cycles_count', 0)}")
        print(f"   Progress Status: {summary.get('progress_analysis', {}).get('quality_trend', 'unknown')}")
        
        performance_summary = summary.get('performance_summary', {})
        if 'percentage_improvement' in performance_summary:
            improvement = performance_summary['percentage_improvement']
            print(f"   Performance Improvement: {improvement:.1f}%")
        
        key_learnings = summary.get('key_learnings', [])
        print(f"   Key Learnings: {len(key_learnings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Learning summary test failed: {str(e)}")
        return False


def run_api_test():
    """Test the API endpoints."""
    print("\n🌐 Running API Test...")
    print("=" * 50)
    
    try:
        # Test importing the API module
        from feedback_optimizer.api import app
        print("✅ API module imported successfully")
        
        # Test FastAPI app creation
        print(f"✅ FastAPI app created: {app.title}")
        
        # Test Pydantic models
        from feedback_optimizer.api import FeedbackItem
        sample_feedback = FeedbackItem(
            content_id='test_001',
            text='Test feedback for API validation'
        )
        print("✅ Pydantic models working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False


def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🚀 Feedback-Driven Content Improvement Optimizer - Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ("Basic Analysis", run_basic_analysis_test),
        ("Predictive Insights", run_predictive_insights_test),
        ("Implementation Tracking", run_implementation_tracking_test),
        ("Learning Summary", run_learning_summary_test),
        ("API Integration", run_api_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test encountered an error: {str(e)}")
            results.append((test_name, False))
        
        print()  # Add spacing between tests
    
    # Print summary
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The Feedback Optimizer is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the system configuration.")
        return False


if __name__ == "__main__":
    """Run the comprehensive test suite."""
    success = run_comprehensive_test()
    
    if success:
        print("\n" + "=" * 70)
        print("🎯 Next Steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Start the API server: python -m uvicorn feedback_optimizer.api:app --reload")
        print("   3. Access API docs at: http://localhost:8000/docs")
        print("   4. Integrate with your content creation workflow")
        print("=" * 70)
    
    sys.exit(0 if success else 1)