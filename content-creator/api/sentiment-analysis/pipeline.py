"""
Sentiment Analysis Pipeline - Main pipeline for comprehensive sentiment analysis
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from .sentiment_analyzer import SentimentAnalyzer, CommentAnalysis, SentimentScore
from .topic_extractor import TopicExtractor, TopicAnalysis
from .improvement_identifier import ImprovementIdentifier, ImprovementAnalysis

logger = logging.getLogger(__name__)

@dataclass
class SentimentAnalysisRequest:
    """Request for sentiment analysis"""
    id: str
    content_id: str
    comments: List[Dict[str, Any]]  # Raw comment data
    analysis_options: Dict[str, Any]
    time_window_days: int
    created_at: str

@dataclass
class SentimentAnalysisResult:
    """Complete sentiment analysis result"""
    id: str
    request_id: str
    content_id: str
    status: str
    comment_count: int
    analysis: Optional[Dict[str, Any]]
    summary: Optional[Dict[str, Any]]
    processing_time: float
    error_message: Optional[str]
    created_at: str

@dataclass
class AnalysisSummary:
    """Summary of sentiment analysis"""
    overall_sentiment: float
    sentiment_distribution: Dict[str, float]
    top_topics: List[str]
    improvement_priority: int
    key_insights: List[str]
    recommended_actions: List[str]

class SentimentAnalysisPipeline:
    """Main pipeline for comprehensive sentiment analysis"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.improvement_identifier = ImprovementIdentifier()
        
        # Processing statistics
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_processing_time": 0.0,
            "comments_processed": 0
        }
    
    async def analyze_comments(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResult:
        """
        Perform comprehensive sentiment analysis on comments
        
        Args:
            request: SentimentAnalysisRequest with comments and options
            
        Returns:
            SentimentAnalysisResult with complete analysis
        """
        start_time = datetime.now()
        logger.info(f"Starting sentiment analysis for content: {request.content_id}")
        
        try:
            # Update statistics
            self.stats["total_analyses"] += 1
            
            # Step 1: Analyze individual comments
            comment_analyses = await self._analyze_comments(request.comments, request.content_id)
            
            if not comment_analyses:
                raise ValueError("No valid comments found for analysis")
            
            # Step 2: Extract topics from analyzed comments
            topic_analysis = await self._extract_topics(comment_analyses)
            
            # Step 3: Identify improvement opportunities
            improvement_analysis = await self._identify_improvements(
                comment_analyses, topic_analysis, request.time_window_days
            )
            
            # Step 4: Generate summary insights
            summary = await self._generate_summary(
                comment_analyses, topic_analysis, improvement_analysis
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update success statistics
            self.stats["successful_analyses"] += 1
            self.stats["comments_processed"] += len(comment_analyses)
            self._update_processing_stats(processing_time)
            
            # Combine all analysis results
            analysis_result = {
                "comment_analyses": [asdict(ca) for ca in comment_analyses],
                "topic_analysis": asdict(topic_analysis),
                "improvement_analysis": asdict(improvement_analysis),
                "metadata": {
                    "analysis_options": request.analysis_options,
                    "time_window_days": request.time_window_days,
                    "platform_breakdown": self._get_platform_breakdown(comment_analyses)
                }
            }
            
            logger.info(f"Sentiment analysis completed in {processing_time:.2f} seconds")
            
            return SentimentAnalysisResult(
                id=str(uuid.uuid4()),
                request_id=request.id,
                content_id=request.content_id,
                status="completed",
                comment_count=len(comment_analyses),
                analysis=analysis_result,
                summary=asdict(summary),
                processing_time=processing_time,
                error_message=None,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            # Update failure statistics
            self.stats["failed_analyses"] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"Sentiment analysis failed: {e}")
            
            return SentimentAnalysisResult(
                id=str(uuid.uuid4()),
                request_id=request.id,
                content_id=request.content_id,
                status="failed",
                comment_count=0,
                analysis=None,
                summary=None,
                processing_time=processing_time,
                error_message=str(e),
                created_at=datetime.now().isoformat()
            )
    
    async def _analyze_comments(self, comments: List[Dict[str, Any]], 
                              content_id: str) -> List[CommentAnalysis]:
        """Analyze individual comments"""
        logger.info(f"Analyzing {len(comments)} comments...")
        
        # Prepare comment data for analysis
        prepared_comments = []
        for comment_data in comments:
            if isinstance(comment_data, dict) and 'text' in comment_data:
                # Ensure required fields
                prepared_comment = {
                    'id': comment_data.get('id', f"{content_id}_{hash(comment_data['text'])}"),
                    'text': comment_data['text'],
                    'platform': comment_data.get('platform', 'unknown'),
                    'timestamp': comment_data.get('timestamp', datetime.now().isoformat()),
                    'author': comment_data.get('author', 'anonymous'),
                    'likes': comment_data.get('likes', 0),
                    'replies': comment_data.get('replies', 0)
                }
                prepared_comments.append(prepared_comment)
        
        # Perform batch sentiment analysis
        comment_analyses = self.sentiment_analyzer.analyze_batch(prepared_comments)
        
        logger.info(f"Completed analysis of {len(comment_analyses)} comments")
        return comment_analyses
    
    async def _extract_topics(self, comment_analyses: List[CommentAnalysis]) -> TopicAnalysis:
        """Extract topics from analyzed comments"""
        logger.info("Extracting topics from comments...")
        
        topic_analysis = self.topic_extractor.extract_topics(comment_analyses)
        
        logger.info(f"Identified {len(topic_analysis.primary_topics)} primary topics")
        return topic_analysis
    
    async def _identify_improvements(self, 
                                   comment_analyses: List[CommentAnalysis],
                                   topic_analysis: TopicAnalysis,
                                   time_window_days: int) -> ImprovementAnalysis:
        """Identify improvement opportunities"""
        logger.info("Identifying improvement opportunities...")
        
        improvement_analysis = self.improvement_identifier.identify_opportunities(
            comment_analyses, topic_analysis, time_window_days
        )
        
        logger.info(f"Identified {len(improvement_analysis.opportunities)} improvement opportunities")
        return improvement_analysis
    
    async def _generate_summary(self,
                              comment_analyses: List[CommentAnalysis],
                              topic_analysis: TopicAnalysis,
                              improvement_analysis: ImprovementAnalysis) -> AnalysisSummary:
        """Generate summary insights"""
        
        # Calculate overall sentiment
        if comment_analyses:
            overall_sentiment = sum(ca.sentiment.overall_score for ca in comment_analyses) / len(comment_analyses)
        else:
            overall_sentiment = 0.0
        
        # Calculate sentiment distribution
        positive_count = sum(1 for ca in comment_analyses if ca.sentiment.overall_score > 0.1)
        negative_count = sum(1 for ca in comment_analyses if ca.sentiment.overall_score < -0.1)
        neutral_count = len(comment_analyses) - positive_count - negative_count
        
        sentiment_distribution = {
            "positive": positive_count / len(comment_analyses) if comment_analyses else 0,
            "negative": negative_count / len(comment_analyses) if comment_analyses else 0,
            "neutral": neutral_count / len(comment_analyses) if comment_analyses else 0
        }
        
        # Get top topics
        top_topics = [t.topic for t in topic_analysis.primary_topics[:5]]
        
        # Determine improvement priority
        if improvement_analysis.critical_issues:
            improvement_priority = 5
        elif len(improvement_analysis.quick_wins) > 0:
            improvement_priority = 4
        elif len(improvement_analysis.opportunities) > 3:
            improvement_priority = 3
        elif len(improvement_analysis.opportunities) > 0:
            improvement_priority = 2
        else:
            improvement_priority = 1
        
        # Generate key insights
        key_insights = self._generate_key_insights(
            overall_sentiment, sentiment_distribution, topic_analysis, improvement_analysis
        )
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(
            improvement_analysis, topic_analysis
        )
        
        return AnalysisSummary(
            overall_sentiment=overall_sentiment,
            sentiment_distribution=sentiment_distribution,
            top_topics=top_topics,
            improvement_priority=improvement_priority,
            key_insights=key_insights,
            recommended_actions=recommended_actions
        )
    
    def _generate_key_insights(self, 
                             overall_sentiment: float,
                             sentiment_distribution: Dict[str, float],
                             topic_analysis: TopicAnalysis,
                             improvement_analysis: ImprovementAnalysis) -> List[str]:
        """Generate key insights from analysis"""
        insights = []
        
        # Sentiment insights
        if overall_sentiment > 0.3:
            insights.append("Content receives predominantly positive feedback from audience")
        elif overall_sentiment < -0.3:
            insights.append("Content needs significant improvement based on negative feedback")
        else:
            insights.append("Content receives mixed feedback with room for improvement")
        
        # Topic insights
        if topic_analysis.primary_topics:
            top_topic = topic_analysis.primary_topics[0]
            insights.append(f"Most discussed topic: '{top_topic.topic}' ({top_topic.frequency} mentions)")
        
        # Improvement insights
        if improvement_analysis.critical_issues:
            insights.append(f"Critical issues identified: {len(improvement_analysis.critical_issues)} require immediate attention")
        
        if improvement_analysis.quick_wins:
            insights.append(f"Quick wins available: {len(improvement_analysis.quick_wins)} easy improvements identified")
        
        # Distribution insights
        if sentiment_distribution["negative"] > 0.4:
            insights.append("High proportion of negative sentiment suggests need for content strategy review")
        elif sentiment_distribution["positive"] > 0.6:
            insights.append("Strong positive sentiment indicates successful content approach")
        
        return insights
    
    def _generate_recommended_actions(self,
                                    improvement_analysis: ImprovementAnalysis,
                                    topic_analysis: TopicAnalysis) -> List[str]:
        """Generate prioritized recommended actions"""
        actions = []
        
        # Critical actions first
        for issue in improvement_analysis.critical_issues[:2]:
            actions.append(f"URGENT: {issue.title} - {issue.description}")
        
        # Quick wins
        for win in improvement_analysis.quick_wins[:3]:
            actions.append(f"Quick Win: {win.title} - {win.description}")
        
        # Content gap actions
        for gap in improvement_analysis.content_gaps[:2]:
            actions.append(f"Content Gap: {gap}")
        
        # Engagement strategies
        for strategy in improvement_analysis.engagement_strategies[:2]:
            actions.append(f"Engagement: {strategy}")
        
        return actions[:8]  # Limit to top 8 actions
    
    def _get_platform_breakdown(self, comment_analyses: List[CommentAnalysis]) -> Dict[str, int]:
        """Get breakdown of comments by platform"""
        platform_counts = {}
        for analysis in comment_analyses:
            platform = analysis.platform
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        return platform_counts
    
    def _update_processing_stats(self, processing_time: float):
        """Update processing time statistics"""
        current_avg = self.stats["average_processing_time"]
        total_successful = self.stats["successful_analyses"]
        
        if total_successful == 1:
            self.stats["average_processing_time"] = processing_time
        else:
            # Calculate new average
            total_time = current_avg * (total_successful - 1) + processing_time
            self.stats["average_processing_time"] = total_time / total_successful
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline processing statistics"""
        return {
            "processing_stats": self.stats,
            "pipeline_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "capabilities": {
                "sentiment_analysis": True,
                "topic_extraction": True,
                "improvement_identification": True,
                "batch_processing": True,
                "real_time_analysis": True
            }
        }
    
    def create_request_from_comments(self,
                                   content_id: str,
                                   comments: List[Dict[str, Any]],
                                   analysis_options: Optional[Dict[str, Any]] = None,
                                   time_window_days: int = 30) -> SentimentAnalysisRequest:
        """Create a SentimentAnalysisRequest from comment data"""
        
        if analysis_options is None:
            analysis_options = {
                "include_emotion_analysis": True,
                "include_topic_extraction": True,
                "include_improvement_suggestions": True,
                "detailed_reporting": True
            }
        
        return SentimentAnalysisRequest(
            id=str(uuid.uuid4()),
            content_id=content_id,
            comments=comments,
            analysis_options=analysis_options,
            time_window_days=time_window_days,
            created_at=datetime.now().isoformat()
        )

# Factory class for pipeline management
class SentimentAnalysisPipelineFactory:
    """Factory for creating and managing sentiment analysis pipeline instances"""
    
    _pipelines = {}
    
    @classmethod
    def get_pipeline(cls, pipeline_id: str = "default") -> SentimentAnalysisPipeline:
        """Get or create pipeline instance"""
        
        if pipeline_id not in cls._pipelines:
            cls._pipelines[pipeline_id] = SentimentAnalysisPipeline()
        
        return cls._pipelines[pipeline_id]
    
    @classmethod
    def create_batch_pipeline(cls, num_pipelines: int = 3) -> List[SentimentAnalysisPipeline]:
        """Create multiple pipeline instances for batch processing"""
        pipelines = []
        for i in range(num_pipelines):
            pipeline_id = f"batch_{i}"
            pipelines.append(cls.get_pipeline(pipeline_id))
        return pipelines

# Example usage
async def main():
    """Example usage of the sentiment analysis pipeline"""
    
    # Get pipeline instance
    pipeline = SentimentAnalysisPipelineFactory.get_pipeline()
    
    # Sample comment data
    sample_comments = [
        {
            'id': '1',
            'text': 'Great tutorial! Really helpful and easy to follow.',
            'platform': 'youtube',
            'timestamp': '2025-10-29T10:00:00Z',
            'author': 'user1',
            'likes': 5,
            'replies': 1
        },
        {
            'id': '2',
            'text': 'The audio quality could be better, but content is good.',
            'platform': 'youtube',
            'timestamp': '2025-10-29T11:00:00Z',
            'author': 'user2',
            'likes': 2,
            'replies': 0
        },
        {
            'id': '3',
            'text': 'Amazing video! Loved every minute of it.',
            'platform': 'instagram',
            'timestamp': '2025-10-29T12:00:00Z',
            'author': 'user3',
            'likes': 8,
            'replies': 2
        },
        {
            'id': '4',
            'text': 'Could you make a follow-up video on advanced topics?',
            'platform': 'youtube',
            'timestamp': '2025-10-29T13:00:00Z',
            'author': 'user4',
            'likes': 3,
            'replies': 0
        },
        {
            'id': '5',
            'text': 'This was confusing. Need more examples.',
            'platform': 'twitter',
            'timestamp': '2025-10-29T14:00:00Z',
            'author': 'user5',
            'likes': 1,
            'replies': 1
        }
    ]
    
    # Create request
    request = pipeline.create_request_from_comments(
        content_id="tutorial_video_001",
        comments=sample_comments,
        analysis_options={
            "include_emotion_analysis": True,
            "include_topic_extraction": True,
            "include_improvement_suggestions": True
        },
        time_window_days=7
    )
    
    # Perform analysis
    result = await pipeline.analyze_comments(request)
    
    print(f"Sentiment analysis result:")
    print(f"Status: {result.status}")
    print(f"Comments analyzed: {result.comment_count}")
    print(f"Processing time: {result.processing_time:.2f} seconds")
    
    if result.summary:
        print(f"Overall sentiment: {result.summary['overall_sentiment']:.3f}")
        print(f"Top topics: {result.summary['top_topics']}")
        print(f"Improvement priority: {result.summary['improvement_priority']}/5")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    # Get pipeline statistics
    stats = await pipeline.get_pipeline_stats()
    print(f"Pipeline statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())