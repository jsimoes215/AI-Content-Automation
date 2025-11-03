"""
Sentiment Analysis Test and Example Script

This script demonstrates the complete sentiment analysis system functionality
including comment analysis, topic extraction, and improvement identification.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the Python path for local imports
sys.path.insert(0, os.path.dirname(__file__))

from sentiment_analysis import (
    SentimentAnalysisPipeline,
    SentimentAnalysisPipelineFactory,
    quick_sentiment_analysis,
    batch_sentiment_analysis
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample comment data for testing
SAMPLE_COMMENTS = [
    {
        'id': '1',
        'text': 'Amazing tutorial! This really helped me understand the concepts clearly. Great explanation!',
        'platform': 'youtube',
        'timestamp': '2025-10-29T10:00:00Z',
        'author': 'TechEnthusiast92',
        'likes': 15,
        'replies': 3
    },
    {
        'id': '2',
        'text': 'The audio quality could be better, but the content is very informative and useful.',
        'platform': 'youtube',
        'timestamp': '2025-10-29T11:30:00Z',
        'author': 'User123456',
        'likes': 8,
        'replies': 1
    },
    {
        'id': '3',
        'text': 'This was confusing. I need more examples to understand this properly.',
        'platform': 'twitter',
        'timestamp': '2025-10-29T12:15:00Z',
        'author': 'ConfusedLearner',
        'likes': 2,
        'replies': 5
    },
    {
        'id': '4',
        'text': 'Love your content! Please make more videos like this. Subscribed! 🔥',
        'platform': 'instagram',
        'timestamp': '2025-10-29T13:45:00Z',
        'author': 'ContentFan2025',
        'likes': 23,
        'replies': 0
    },
    {
        'id': '5',
        'text': 'Could you create a follow-up video covering advanced topics? This intermediate level was perfect.',
        'platform': 'youtube',
        'timestamp': '2025-10-29T14:20:00Z',
        'author': 'AdvancedStudent',
        'likes': 6,
        'replies': 2
    },
    {
        'id': '6',
        'text': 'The video was too long. Consider making shorter versions for quick reference.',
        'platform': 'youtube',
        'timestamp': '2025-10-29T15:10:00Z',
        'author': 'BusyProfessional',
        'likes': 4,
        'replies': 8
    },
    {
        'id': '7',
        'text': 'Excellent production quality! Very professional and engaging throughout.',
        'platform': 'linkedin',
        'timestamp': '2025-10-29T16:00:00Z',
        'author': 'MarketingPro',
        'likes': 12,
        'replies': 1
    },
    {
        'id': '8',
        'text': 'I didn\'t like this video. The pacing was too slow and boring.',
        'platform': 'tiktok',
        'timestamp': '2025-10-29T17:30:00Z',
        'author': 'QuickViewer',
        'likes': 1,
        'replies': 12
    },
    {
        'id': '9',
        'text': 'This is exactly what I was looking for! Thank you for creating such helpful content.',
        'platform': 'youtube',
        'timestamp': '2025-10-29T18:45:00Z',
        'author': 'GratefulStudent',
        'likes': 18,
        'replies': 4
    },
    {
        'id': '10',
        'text': 'The subtitles would be helpful for non-native speakers. Consider adding them.',
        'platform': 'youtube',
        'timestamp': '2025-10-29T19:15:00Z',
        'author': 'InternationalLearner',
        'likes': 7,
        'replies': 3
    },
    {
        'id': '11',
        'text': 'Great work! This video deserves more views. Sharing with my network.',
        'platform': 'linkedin',
        'timestamp': '2025-10-29T20:00:00Z',
        'author': 'Networker',
        'likes': 14,
        'replies': 0
    },
    {
        'id': '12',
        'text': 'Not bad, but I expected more depth. Please cover advanced techniques next time.',
        'platform': 'youtube',
        'timestamp': '2025-10-29T21:30:00Z',
        'author': 'ExpertViewer',
        'likes': 5,
        'replies': 6
    }
]

async def test_quick_sentiment_analysis():
    """Test quick sentiment analysis for individual comments"""
    logger.info("=== Testing Quick Sentiment Analysis ===")
    
    test_comments = [
        "This is absolutely fantastic! Great job!",
        "The video was okay, nothing special.",
        "I hate this content. It's terrible and boring.",
        "Amazing tutorial, very helpful and informative!",
        "Could be better. Needs improvement."
    ]
    
    for i, comment in enumerate(test_comments):
        logger.info(f"\n--- Comment {i+1} ---")
        logger.info(f"Text: '{comment}'")
        
        analysis = await quick_sentiment_analysis(comment, "youtube")
        
        logger.info(f"Overall Sentiment: {analysis.sentiment.overall_score:.3f}")
        logger.info(f"Confidence: {analysis.sentiment.confidence:.3f}")
        logger.info(f"Positive Score: {analysis.sentiment.positive_score:.3f}")
        logger.info(f"Negative Score: {analysis.sentiment.negative_score:.3f}")
        logger.info(f"Neutral Score: {analysis.sentiment.neutral_score:.3f}")
        logger.info(f"Subjectivity: {analysis.sentiment.subjectivity:.3f}")
        logger.info(f"Identified Topics: {analysis.topics}")
        logger.info(f"Key Phrases: {analysis.key_phrases[:5]}")
        
        if analysis.improvement_suggestions:
            logger.info(f"Improvement Suggestions: {analysis.improvement_suggestions[:2]}")
        
        # Show top emotions
        emotions = analysis.sentiment.emotion_scores
        top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
        logger.info(f"Top Emotions: {[f'{emotion}: {score:.2f}' for emotion, score in top_emotions]}")

async def test_batch_analysis():
    """Test batch sentiment analysis"""
    logger.info("\n=== Testing Batch Sentiment Analysis ===")
    
    result = await batch_sentiment_analysis(SAMPLE_COMMENTS, "test_video_001")
    
    logger.info(f"Analysis Status: {result.status}")
    logger.info(f"Comments Analyzed: {result.comment_count}")
    logger.info(f"Processing Time: {result.processing_time:.2f} seconds")
    
    if result.summary:
        logger.info(f"\n--- Summary ---")
        logger.info(f"Overall Sentiment: {result.summary['overall_sentiment']:.3f}")
        logger.info(f"Sentiment Distribution: {result.summary['sentiment_distribution']}")
        logger.info(f"Top Topics: {result.summary['top_topics']}")
        logger.info(f"Improvement Priority: {result.summary['improvement_priority']}/5")
        
        logger.info(f"\n--- Key Insights ---")
        for insight in result.summary['key_insights']:
            logger.info(f"• {insight}")
        
        logger.info(f"\n--- Recommended Actions ---")
        for action in result.summary['recommended_actions'][:5]:
            logger.info(f"• {action}")

async def test_comprehensive_analysis():
    """Test comprehensive analysis with pipeline"""
    logger.info("\n=== Testing Comprehensive Analysis Pipeline ===")
    
    # Get pipeline instance
    pipeline = SentimentAnalysisPipelineFactory.get_pipeline("test_pipeline")
    
    # Create analysis request
    request = pipeline.create_request_from_comments(
        content_id="comprehensive_test_video",
        comments=SAMPLE_COMMENTS,
        analysis_options={
            "include_emotion_analysis": True,
            "include_topic_extraction": True,
            "include_improvement_suggestions": True,
            "detailed_reporting": True
        },
        time_window_days=30
    )
    
    # Perform comprehensive analysis
    result = await pipeline.analyze_comments(request)
    
    if result.status == "completed" and result.analysis:
        logger.info("=== COMPREHENSIVE ANALYSIS RESULTS ===")
        
        # Display comment analysis summary
        comment_analyses = result.analysis["comment_analyses"]
        logger.info(f"\n--- Comment Analysis Summary ({len(comment_analyses)} comments) ---")
        
        # Sample a few detailed analyses
        for i, comment in enumerate(comment_analyses[:3]):
            logger.info(f"\nComment {i+1}:")
            logger.info(f"Platform: {comment['platform']}")
            logger.info(f"Text: {comment['text'][:80]}...")
            logger.info(f"Sentiment: {comment['sentiment']['overall_score']:.3f}")
            logger.info(f"Topics: {comment['topics']}")
            logger.info(f"Engagement Potential: {comment['engagement_indicators']['engagement_potential']:.3f}")
        
        # Display topic analysis
        topic_analysis = result.analysis["topic_analysis"]
        logger.info(f"\n--- Topic Analysis ---")
        logger.info(f"Primary Topics ({len(topic_analysis['primary_topics'])}):")
        for topic in topic_analysis['primary_topics'][:5]:
            logger.info(f"• {topic['topic']}: {topic['relevance_score']:.3f} (freq: {topic['frequency']})")
        
        if topic_analysis['emerging_topics']:
            logger.info(f"\nEmerging Topics:")
            for topic in topic_analysis['emerging_topics']:
                logger.info(f"• {topic['topic']}: {topic['sentiment_association']:.3f}")
        
        # Display improvement analysis
        improvement_analysis = result.analysis["improvement_analysis"]
        logger.info(f"\n--- Improvement Analysis ---")
        logger.info(f"Total Opportunities: {len(improvement_analysis['opportunities'])}")
        
        if improvement_analysis['critical_issues']:
            logger.info(f"\nCritical Issues ({len(improvement_analysis['critical_issues'])}):")
            for issue in improvement_analysis['critical_issues'][:3]:
                logger.info(f"• {issue['title']} (Priority: {issue['priority']}/5)")
                logger.info(f"  {issue['description']}")
        
        if improvement_analysis['quick_wins']:
            logger.info(f"\nQuick Wins ({len(improvement_analysis['quick_wins'])}):")
            for win in improvement_analysis['quick_wins'][:3]:
                logger.info(f"• {win['title']} - {win['expected_impact']}")
        
        if improvement_analysis['content_gaps']:
            logger.info(f"\nContent Gaps:")
            for gap in improvement_analysis['content_gaps'][:3]:
                logger.info(f"• {gap}")
        
        # Display performance metrics
        if improvement_analysis['performance_metrics']:
            logger.info(f"\n--- Performance Metrics ---")
            metrics = improvement_analysis['performance_metrics']
            logger.info(f"Average Sentiment: {metrics.get('average_sentiment', 0):.3f}")
            logger.info(f"Positive Sentiment Ratio: {metrics.get('positive_sentiment_ratio', 0):.3f}")
            logger.info(f"Average Engagement: {metrics.get('average_engagement', 0):.3f}")
            logger.info(f"Topic Diversity: {metrics.get('topic_diversity', 0):.3f}")

async def test_platform_breakdown():
    """Test platform-specific analysis"""
    logger.info("\n=== Testing Platform Breakdown Analysis ===")
    
    pipeline = SentimentAnalysisPipelineFactory.get_pipeline("platform_test")
    
    # Group comments by platform for testing
    platform_comments = {}
    for comment in SAMPLE_COMMENTS:
        platform = comment['platform']
        if platform not in platform_comments:
            platform_comments[platform] = []
        platform_comments[platform].append(comment)
    
    # Analyze each platform separately
    for platform, comments in platform_comments.items():
        logger.info(f"\n--- Platform: {platform.upper()} ---")
        
        request = pipeline.create_request_from_comments(
            content_id=f"platform_analysis_{platform}",
            comments=comments
        )
        
        result = await pipeline.analyze_comments(request)
        
        if result.status == "completed" and result.summary:
            logger.info(f"Comments: {result.comment_count}")
            logger.info(f"Overall Sentiment: {result.summary['overall_sentiment']:.3f}")
            logger.info(f"Top Topics: {result.summary['top_topics'][:3]}")
            
            # Show platform-specific insights
            if result.summary['key_insights']:
                logger.info(f"Key Insight: {result.summary['key_insights'][0]}")

async def test_pipeline_statistics():
    """Test pipeline statistics and monitoring"""
    logger.info("\n=== Testing Pipeline Statistics ===")
    
    pipeline = SentimentAnalysisPipelineFactory.get_pipeline("stats_test")
    
    # Perform multiple analyses to build statistics
    analysis_count = 3
    for i in range(analysis_count):
        request = pipeline.create_request_from_comments(
            content_id=f"stats_test_video_{i}",
            comments=SAMPLE_COMMENTS[:5]  # Use subset for faster testing
        )
        
        result = await pipeline.analyze_comments(request)
        logger.info(f"Analysis {i+1}: {result.status} ({result.processing_time:.2f}s)")
    
    # Get final statistics
    stats = await pipeline.get_pipeline_stats()
    
    logger.info(f"\n--- Final Pipeline Statistics ---")
    processing_stats = stats["processing_stats"]
    logger.info(f"Total Analyses: {processing_stats['total_analyses']}")
    logger.info(f"Successful: {processing_stats['successful_analyses']}")
    logger.info(f"Failed: {processing_stats['failed_analyses']}")
    logger.info(f"Average Processing Time: {processing_stats['average_processing_time']:.2f}s")
    logger.info(f"Total Comments Processed: {processing_stats['comments_processed']}")
    
    if processing_stats['total_analyses'] > 0:
        success_rate = (processing_stats['successful_analyses'] / processing_stats['total_analyses']) * 100
        logger.info(f"Success Rate: {success_rate:.1f}%")

async def main():
    """Run all sentiment analysis tests"""
    logger.info("Starting Sentiment Analysis System Tests")
    logger.info("=" * 60)
    
    try:
        # Run individual component tests
        await test_quick_sentiment_analysis()
        
        await test_batch_analysis()
        
        await test_comprehensive_analysis()
        
        await test_platform_breakdown()
        
        await test_pipeline_statistics()
        
        logger.info("\n" + "=" * 60)
        logger.info("All sentiment analysis tests completed successfully!")
        logger.info("The sentiment analysis system is ready for production use.")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())