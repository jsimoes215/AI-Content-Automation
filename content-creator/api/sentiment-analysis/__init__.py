"""
Sentiment Analysis Module - Comprehensive sentiment analysis for comment feedback

This module provides advanced sentiment analysis capabilities including:
- Individual comment sentiment analysis with emotion detection
- Topic extraction and categorization
- Improvement opportunity identification
- Comprehensive reporting and insights

Example usage:
    from api.sentiment_analysis import SentimentAnalysisPipeline, SentimentAnalysisPipelineFactory
    
    # Get pipeline instance
    pipeline = SentimentAnalysisPipelineFactory.get_pipeline()
    
    # Create analysis request
    request = pipeline.create_request_from_comments(
        content_id="content_001",
        comments=[{'text': 'Great content!', 'platform': 'youtube'}]
    )
    
    # Perform analysis
    result = await pipeline.analyze_comments(request)
    
    print(f"Overall sentiment: {result.summary['overall_sentiment']}")
"""

from .sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentScore,
    CommentAnalysis
)

from .topic_extractor import (
    TopicExtractor,
    TopicScore,
    TopicAnalysis
)

from .improvement_identifier import (
    ImprovementIdentifier,
    ImprovementOpportunity,
    ImprovementAnalysis
)

from .pipeline import (
    SentimentAnalysisPipeline,
    SentimentAnalysisPipelineFactory,
    SentimentAnalysisRequest,
    SentimentAnalysisResult,
    AnalysisSummary
)

__version__ = "1.0.0"
__all__ = [
    # Core sentiment analysis
    'SentimentAnalyzer',
    'SentimentScore', 
    'CommentAnalysis',
    
    # Topic extraction
    'TopicExtractor',
    'TopicScore',
    'TopicAnalysis',
    
    # Improvement identification
    'ImprovementIdentifier',
    'ImprovementOpportunity',
    'ImprovementAnalysis',
    
    # Main pipeline
    'SentimentAnalysisPipeline',
    'SentimentAnalysisPipelineFactory',
    'SentimentAnalysisRequest',
    'SentimentAnalysisResult',
    'AnalysisSummary'
]

# Convenience function for quick sentiment analysis
async def quick_sentiment_analysis(text: str, platform: str = "unknown") -> CommentAnalysis:
    """
    Quick sentiment analysis for a single comment
    
    Args:
        text: Comment text to analyze
        platform: Platform source (youtube, twitter, instagram, etc.)
        
    Returns:
        CommentAnalysis object with sentiment scores
    """
    analyzer = SentimentAnalyzer()
    return analyzer.analyze_comment(text, platform)

# Convenience function for batch analysis
async def batch_sentiment_analysis(comments: list, content_id: str = "batch_001") -> SentimentAnalysisResult:
    """
    Quick batch sentiment analysis for multiple comments
    
    Args:
        comments: List of comment dictionaries with 'text' and optional 'platform'
        content_id: Identifier for the content being analyzed
        
    Returns:
        SentimentAnalysisResult with complete analysis
    """
    pipeline = SentimentAnalysisPipelineFactory.get_pipeline()
    
    # Prepare comments
    prepared_comments = []
    for i, comment in enumerate(comments):
        if isinstance(comment, dict) and 'text' in comment:
            prepared_comments.append({
                'id': comment.get('id', f'{content_id}_{i}'),
                'text': comment['text'],
                'platform': comment.get('platform', 'unknown'),
                'timestamp': comment.get('timestamp'),
                'author': comment.get('author', 'anonymous'),
                'likes': comment.get('likes', 0),
                'replies': comment.get('replies', 0)
            })
    
    # Create request and analyze
    request = pipeline.create_request_from_comments(content_id, prepared_comments)
    return await pipeline.analyze_comments(request)

# Module metadata
__author__ = "AI Content Automation Team"
__description__ = "Advanced sentiment analysis and improvement identification for comment feedback"