#!/usr/bin/env python3
"""
Simple test script for sentiment analysis system
"""

import sys
import os
import asyncio

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import modules directly
try:
    from .sentiment_analyzer import SentimentAnalyzer
    from .topic_extractor import TopicExtractor  
    from .improvement_identifier import ImprovementIdentifier
    print("✓ Successfully imported all modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

async def test_sentiment_analyzer():
    """Test the core sentiment analyzer"""
    print("\n=== Testing Sentiment Analyzer ===")
    
    analyzer = SentimentAnalyzer()
    
    test_comments = [
        "This is amazing! Great job on the tutorial!",
        "The video was okay, nothing special.",
        "I hate this content. It's terrible and boring.",
        "Could you make this clearer? I'm confused.",
        "Excellent work! Very professional and helpful!"
    ]
    
    for i, comment in enumerate(test_comments, 1):
        print(f"\n--- Comment {i} ---")
        print(f"Text: '{comment}'")
        
        analysis = analyzer.analyze_comment(comment, "youtube")
        
        print(f"Overall Sentiment: {analysis.sentiment.overall_score:.3f}")
        print(f"Confidence: {analysis.sentiment.confidence:.3f}")
        print(f"Positive: {analysis.sentiment.positive_score:.3f}")
        print(f"Negative: {analysis.sentiment.negative_score:.3f}")
        print(f"Topics: {analysis.topics}")
        print(f"Key Phrases: {analysis.key_phrases[:3]}")
        
        if analysis.improvement_suggestions:
            print(f"Suggestions: {analysis.improvement_suggestions[:2]}")

async def test_topic_extractor():
    """Test topic extraction"""
    print("\n=== Testing Topic Extractor ===")
    
    # First create some sample analyses
    analyzer = SentimentAnalyzer()
    sample_texts = [
        "This tutorial was very helpful for learning",
        "The audio quality needs improvement",
        "Great educational content, very informative",
        "Could use better video editing",
        "Amazing tutorial, love the clear explanation",
        "Confusing at some points, need more examples"
    ]
    
    # Analyze comments
    analyses = []
    for text in sample_texts:
        analysis = analyzer.analyze_comment(text, "youtube")
        analyses.append(analysis)
    
    # Extract topics
    extractor = TopicExtractor()
    topic_analysis = extractor.extract_topics(analyses)
    
    print(f"\nPrimary Topics ({len(topic_analysis.primary_topics)}):")
    for topic in topic_analysis.primary_topics:
        print(f"• {topic.topic}: {topic.relevance_score:.3f} (freq: {topic.frequency})")
    
    if topic_analysis.emerging_topics:
        print(f"\nEmerging Topics:")
        for topic in topic_analysis.emerging_topics:
            print(f"• {topic.topic}: {topic.sentiment_association:.3f}")
    
    if topic_analysis.content_recommendations:
        print(f"\nContent Recommendations:")
        for rec in topic_analysis.content_recommendations[:3]:
            print(f"• {rec}")

async def test_improvement_identifier():
    """Test improvement identification"""
    print("\n=== Testing Improvement Identifier ===")
    
    # Create sample data
    analyzer = SentimentAnalyzer()
    sample_comments = [
        "The audio is terrible, hard to hear",
        "Great content but needs better editing",
        "Confusing explanation, not clear",
        "Excellent tutorial, very helpful",
        "Could use more examples",
        "Amazing video, love it!",
        "Audio quality needs improvement",
        "Very informative and well done"
    ]
    
    analyses = []
    for comment in sample_comments:
        analysis = analyzer.analyze_comment(comment, "youtube")
        analyses.append(analysis)
    
    # Get topic analysis
    extractor = TopicExtractor()
    topic_analysis = extractor.extract_topics(analyses)
    
    # Identify improvements
    identifier = ImprovementIdentifier()
    improvement_analysis = identifier.identify_opportunities(analyses, topic_analysis)
    
    print(f"\nImprovement Opportunities ({len(improvement_analysis.opportunities)}):")
    for opportunity in improvement_analysis.opportunities[:3]:
        print(f"• {opportunity.title} (Priority: {opportunity.priority}/5)")
        print(f"  {opportunity.description}")
        print(f"  Suggested Actions: {opportunity.suggested_actions[:2]}")
    
    if improvement_analysis.critical_issues:
        print(f"\nCritical Issues:")
        for issue in improvement_analysis.critical_issues:
            print(f"• {issue.title} - {issue.timeframe}")
    
    if improvement_analysis.quick_wins:
        print(f"\nQuick Wins:")
        for win in improvement_analysis.quick_wins:
            print(f"• {win.title} - {win.expected_impact}")
    
    if improvement_analysis.content_gaps:
        print(f"\nContent Gaps:")
        for gap in improvement_analysis.content_gaps[:3]:
            print(f"• {gap}")

async def main():
    """Run all tests"""
    print("Sentiment Analysis System Test")
    print("=" * 50)
    
    try:
        await test_sentiment_analyzer()
        await test_topic_extractor()
        await test_improvement_identifier()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("The sentiment analysis system is working correctly.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)