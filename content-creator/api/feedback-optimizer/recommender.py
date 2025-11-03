"""
Content Improvement Recommender Module

Generates specific, actionable improvement recommendations for content based on feedback analysis.
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import re

from .models.feedback_data import FeedbackData
from .models.recommendation import Recommendation, RecommendationType, Priority
from .utils.content_analyzer import ContentAnalyzer
from .utils.template_engine import TemplateEngine


class ContentType(Enum):
    """Content types for targeted recommendations."""
    SCRIPT = "script"
    THUMBNAIL = "thumbnail"
    TITLE = "title"
    DESCRIPTION = "description"
    HASHTAGS = "hashtags"
    STRUCTURE = "structure"
    TONE = "tone"
    CALL_TO_ACTION = "call_to_action"


class ContentImprovementRecommender:
    """
    Generates AI-powered improvement recommendations for content elements.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the content improvement recommender."""
        self.config = config or self._default_config()
        self.content_analyzer = ContentAnalyzer()
        self.template_engine = TemplateEngine()
        self.recommendation_history: List[Recommendation] = []
        
    def _default_config(self) -> Dict:
        """Default configuration for the recommender."""
        return {
            'recommendation_weights': {
                'high_impact': 1.0,
                'medium_impact': 0.7,
                'low_impact': 0.4
            },
            'content_thresholds': {
                'quality_good': 0.8,
                'quality_average': 0.6,
                'quality_poor': 0.4
            },
            'recommendation_frequency': {
                'script': 5,
                'thumbnail': 3,
                'title': 2,
                'description': 4
            }
        }
    
    def generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[Recommendation]:
        """
        Generate comprehensive improvement recommendations based on analysis results.
        
        Args:
            analysis_results: Results from feedback analyzer
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Generate recommendations based on sentiment patterns
        sentiment_recs = self._generate_sentiment_recommendations(analysis_results.get('sentiment_patterns', {}))
        recommendations.extend(sentiment_recs)
        
        # Generate recommendations based on engagement patterns
        engagement_recs = self._generate_engagement_recommendations(analysis_results.get('engagement_patterns', {}))
        recommendations.extend(engagement_recs)
        
        # Generate content-specific recommendations
        content_quality = analysis_results.get('content_quality', {})
        content_recs = self._generate_content_recommendations(content_quality)
        recommendations.extend(content_recs)
        
        # Generate temporal recommendations
        temporal_recs = self._generate_temporal_recommendations(analysis_results.get('temporal_trends', {}))
        recommendations.extend(temporal_recs)
        
        # Generate priority-based recommendations
        priority_recs = self._generate_priority_recommendations(analysis_results)
        recommendations.extend(priority_recs)
        
        # Sort by priority and impact
        recommendations.sort(key=lambda x: (x.priority.value, x.impact_score), reverse=True)
        
        # Filter and deduplicate recommendations
        filtered_recs = self._filter_recommendations(recommendations)
        
        self.recommendation_history.extend(filtered_recs)
        return filtered_recs
    
    def _generate_sentiment_recommendations(self, sentiment_patterns: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations based on sentiment analysis."""
        recommendations = []
        
        distribution = sentiment_patterns.get('distribution', {})
        avg_sentiment = sentiment_patterns.get('average_score', 0.5)
        
        # Handle negative sentiment
        if distribution.get('negative', 0) > distribution.get('positive', 0):
            recommendations.append(Recommendation(
                id="sentiment_negative_imbalance",
                title="Address Negative Sentiment Patterns",
                description="Current content is receiving more negative than positive feedback. Review messaging tone and address common concerns.",
                recommendation_type=RecommendationType.CONTENT_TONE,
                priority=Priority.HIGH,
                impact_score=0.9,
                target_content_types=[ContentType.TONE, ContentType.SCRIPT],
                action_items=[
                    "Conduct sentiment analysis on recent comments",
                    "Identify common negative themes",
                    "Adjust content tone to be more positive",
                    "Address frequently mentioned concerns in future content"
                ],
                expected_outcome="Improved sentiment distribution and better audience reception",
                implementation_difficulty="Medium",
                estimated_time_hours=4
            ))
        
        # Handle low overall sentiment
        if avg_sentiment < 0.4:
            recommendations.append(Recommendation(
                id="overall_sentiment_low",
                title="Improve Overall Content Sentiment",
                description="Average sentiment score is below optimal levels. Focus on positive messaging and value delivery.",
                recommendation_type=RecommendationType.CONTENT_TONE,
                priority=Priority.HIGH,
                impact_score=0.85,
                target_content_types=[ContentType.TONE, ContentType.STRUCTURE],
                action_items=[
                    "Review successful high-sentiment content for patterns",
                    "Increase emphasis on value propositions",
                    "Reduce negative or controversial elements",
                    "Add more positive call-to-actions"
                ],
                expected_outcome="Higher overall sentiment scores and better audience satisfaction",
                implementation_difficulty="Medium",
                estimated_time_hours=6
            ))
        
        # Content-specific sentiment recommendations
        content_breakdown = sentiment_patterns.get('content_breakdown', {})
        for content_type, stats in content_breakdown.items():
            if stats.get('average_sentiment', 0.5) < 0.4:
                recommendations.append(Recommendation(
                    id=f"{content_type}_sentiment_low",
                    title=f"Improve {content_type.title()} Sentiment",
                    description=f"{content_type.title()} content is receiving lower sentiment scores than other content types.",
                    recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    impact_score=0.7,
                    target_content_types=[ContentType(content_type)],
                    action_items=[
                        f"Analyze successful {content_type} examples",
                        f"Identify common issues in {content_type} content",
                        f"Implement {content_type} improvement strategies",
                        f"Test A/B variations of {content_type} content"
                    ],
                    expected_outcome=f"Improved {content_type} sentiment and overall content quality",
                    implementation_difficulty="Medium",
                    estimated_time_hours=3
                ))
        
        return recommendations
    
    def _generate_engagement_recommendations(self, engagement_patterns: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations based on engagement analysis."""
        recommendations = []
        
        correlation_analysis = engagement_patterns.get('correlation_analysis', {})
        performance_dist = engagement_patterns.get('performance_distribution', {})
        avg_engagement = engagement_patterns.get('average_engagement_rate', 0.5)
        
        # Handle low overall engagement
        if avg_engagement < 0.3:
            recommendations.append(Recommendation(
                id="low_engagement_overall",
                title="Boost Overall Content Engagement",
                description="Content engagement rates are below optimal levels. Focus on creating more compelling content hooks and calls-to-action.",
                recommendation_type=RecommendationType.ENGAGEMENT_STRATEGY,
                priority=Priority.HIGH,
                impact_score=0.9,
                target_content_types=[ContentType.STRUCTURE, ContentType.CALL_TO_ACTION],
                action_items=[
                    "Review high-engagement content for common patterns",
                    "Strengthen opening hooks in scripts",
                    "Add more compelling calls-to-action",
                    "Improve content pacing and structure",
                    "Encourage more interaction through questions and prompts"
                ],
                expected_outcome="Higher engagement rates across all content types",
                implementation_difficulty="High",
                estimated_time_hours=8
            ))
        
        # Correlation-based recommendations
        sentiment_correlation = correlation_analysis.get('engagement_rate', 0)
        if sentiment_correlation > 0.5:
            recommendations.append(Recommendation(
                id="sentiment_engagement_correlation",
                title="Leverage Sentiment-Engagement Connection",
                description="Strong positive correlation detected between sentiment and engagement. Focus on improving sentiment to boost engagement.",
                recommendation_type=RecommendationType.STRATEGY_OPTIMIZATION,
                priority=Priority.MEDIUM,
                impact_score=0.8,
                target_content_types=[ContentType.TONE, ContentType.STRUCTURE],
                action_items=[
                    "Prioritize positive messaging in content creation",
                    "Use sentiment analysis as pre-publication quality check",
                    "Develop sentiment-optimized content templates",
                    "Train team on sentiment-engagement relationship"
                ],
                expected_outcome="Improved engagement through better sentiment optimization",
                implementation_difficulty="Medium",
                estimated_time_hours=5
            ))
        
        # High/low performer analysis
        top_characteristics = engagement_patterns.get('top_performing_characteristics', [])
        underperforming_characteristics = engagement_patterns.get('underperforming_characteristics', [])
        
        if top_characteristics:
            recommendations.append(Recommendation(
                id="replicate_success_patterns",
                title="Replicate High-Performing Content Patterns",
                description="Analysis shows clear patterns in high-performing content. Apply these learnings to improve underperforming content.",
                recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                priority=Priority.HIGH,
                impact_score=0.85,
                target_content_types=[ContentType.STRUCTURE, ContentType.TONE],
                action_items=[
                    "Document successful content patterns",
                    "Create templates based on top performers",
                    "Apply learnings to new content creation",
                    "Monitor performance of pattern-based content"
                ],
                expected_outcome="Consistent performance improvements across content portfolio",
                implementation_difficulty="Medium",
                estimated_time_hours=6
            ))
        
        return recommendations
    
    def _generate_content_recommendations(self, content_quality: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations for specific content types."""
        recommendations = []
        
        for content_type, quality_data in content_quality.items():
            avg_quality = quality_data.get('average_quality', 0.5)
            common_issues = quality_data.get('common_issues', [])
            strengths = quality_data.get('strengths', [])
            
            # Quality-based recommendations
            if avg_quality < 0.4:
                recommendations.append(Recommendation(
                    id=f"{content_type}_quality_improvement",
                    title=f"Improve {content_type.title()} Quality",
                    description=f"{content_type.title()} content quality is below acceptable levels. Requires immediate attention.",
                    recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                    priority=Priority.HIGH,
                    impact_score=0.9,
                    target_content_types=[ContentType(content_type)],
                    action_items=[
                        f"Review {content_type} best practices",
                        f"Analyze top-performing {content_type} examples",
                        f"Implement quality improvement checklist for {content_type}",
                        f"Consider outsourcing or restructuring {content_type} creation process"
                    ],
                    expected_outcome=f"Significant improvement in {content_type} quality scores",
                    implementation_difficulty="High",
                    estimated_time_hours=10
                ))
            
            elif avg_quality < 0.6:
                recommendations.append(Recommendation(
                    id=f"{content_type}_quality_optimization",
                    title=f"Optimize {content_type.title()} Quality",
                    description=f"{content_type.title()} content quality has room for improvement.",
                    recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    impact_score=0.7,
                    target_content_types=[ContentType(content_type)],
                    action_items=[
                        f"Identify specific quality issues in {content_type}",
                        f"Implement incremental improvements",
                        f"Test variations of {content_type} elements",
                        f"Monitor quality metrics post-implementation"
                    ],
                    expected_outcome=f"Measurable improvement in {content_type} quality",
                    implementation_difficulty="Medium",
                    estimated_time_hours=5
                ))
            
            # Issue-specific recommendations
            for issue in common_issues[:2]:  # Top 2 issues
                recommendations.append(Recommendation(
                    id=f"{content_type}_{issue}_fix",
                    title=f"Address {content_type.title()} {issue.replace('_', ' ').title()}",
                    description=f"Common issue detected in {content_type}: {issue}",
                    recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    impact_score=0.6,
                    target_content_types=[ContentType(content_type)],
                    action_items=[
                        f"Implement fix for {issue} in {content_type}",
                        f"Create checklist to prevent {issue} in future {content_type}",
                        f"Test improved {content_type} version",
                        f"Monitor for {issue} recurrence"
                    ],
                    expected_outcome=f"Reduction in {content_type} {issue} occurrences",
                    implementation_difficulty="Low",
                    estimated_time_hours=2
                ))
            
            # Strength amplification recommendations
            if strengths:
                recommendations.append(Recommendation(
                    id=f"{content_type}_amplify_strengths",
                    title=f"Leverage {content_type.title()} Strengths",
                    description=f"{content_type.title()} shows strengths in: {', '.join(strengths[:2])}. Amplify these positive aspects.",
                    recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                    priority=Priority.LOW,
                    impact_score=0.5,
                    target_content_types=[ContentType(content_type)],
                    action_items=[
                        f"Document and expand on {content_type} strengths",
                        f"Create style guide emphasizing {strengths[0] if strengths else 'positive aspects'}",
                        f"Use {content_type} strength patterns in future content",
                        f"Develop templates that reinforce {content_type} strengths"
                    ],
                    expected_outcome=f"Consistent {content_type} excellence",
                    implementation_difficulty="Low",
                    estimated_time_hours=3
                ))
        
        return recommendations
    
    def _generate_temporal_recommendations(self, temporal_trends: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations based on temporal patterns."""
        recommendations = []
        
        trend_analysis = temporal_trends.get('trend_analysis', {})
        peak_days = temporal_trends.get('peak_performance_days', [])
        
        # Overall trend recommendations
        overall_trend = trend_analysis.get('overall', 'stable')
        if overall_trend == 'declining':
            recommendations.append(Recommendation(
                id="declining_performance_trend",
                title="Address Declining Performance Trend",
                description="Overall content performance shows declining trend. Immediate action needed to reverse negative trajectory.",
                recommendation_type=RecommendationType.STRATEGY_OPTIMIZATION,
                priority=Priority.HIGH,
                impact_score=0.95,
                target_content_types=[ContentType.STRUCTURE, ContentType.TONE],
                action_items=[
                    "Conduct comprehensive performance audit",
                    "Identify specific declining performance areas",
                    "Implement immediate corrective measures",
                    "Monitor daily performance metrics",
                    "Develop turnaround strategy with milestones"
                ],
                expected_outcome="Reversal of declining trend and return to positive performance",
                implementation_difficulty="High",
                estimated_time_hours=12
            ))
        
        # Peak performance day analysis
        if peak_days:
            recommendations.append(Recommendation(
                id="replicate_peak_performance",
                title="Replicate Peak Performance Patterns",
                description=f"Identified {len(peak_days)} days with peak performance. Analyze and replicate success patterns.",
                recommendation_type=RecommendationType.STRATEGY_OPTIMIZATION,
                priority=Priority.MEDIUM,
                impact_score=0.75,
                target_content_types=[ContentType.STRUCTURE, ContentType.CALL_TO_ACTION],
                action_items=[
                    f"Analyze content published on peak days: {', '.join(peak_days[-3:])}",
                    "Identify common patterns in peak performance content",
                    "Develop peak performance content template",
                    "Apply peak patterns to future content creation",
                    "Monitor for replication of peak performance"
                ],
                expected_outcome="Increased frequency of peak performance days",
                implementation_difficulty="Medium",
                estimated_time_hours=6
            ))
        
        # Sentiment trend recommendations
        sentiment_trend = trend_analysis.get('sentiment', 'stable')
        if sentiment_trend == 'declining':
            recommendations.append(Recommendation(
                id="declining_sentiment_trend",
                title="Address Declining Sentiment Trend",
                description="Audience sentiment shows declining trend over time. Focus on rebuilding positive perception.",
                recommendation_type=RecommendationType.CONTENT_TONE,
                priority=Priority.HIGH,
                impact_score=0.8,
                target_content_types=[ContentType.TONE, ContentType.STRUCTURE],
                action_items=[
                    "Survey audience to understand sentiment decline reasons",
                    "Adjust content strategy to address concerns",
                    "Increase positive messaging frequency",
                    "Engage more with audience feedback",
                    "Implement sentiment monitoring dashboard"
                ],
                expected_outcome="Stabilization and improvement of audience sentiment",
                implementation_difficulty="High",
                estimated_time_hours=8
            ))
        
        return recommendations
    
    def _generate_priority_recommendations(self, analysis_results: Dict[str, Any]) -> List[Recommendation]:
        """Generate high-priority recommendations based on overall analysis."""
        recommendations = []
        
        improvement_areas = analysis_results.get('improvement_areas', [])
        overall_score = analysis_results.get('overall_score', 0.5)
        
        # Overall score-based recommendations
        if overall_score < 0.3:
            recommendations.append(Recommendation(
                id="urgent_comprehensive_review",
                title="Urgent Comprehensive Content Review",
                description="Overall content performance is critically low. Comprehensive review and overhaul required.",
                recommendation_type=RecommendationType.STRATEGY_OPTIMIZATION,
                priority=Priority.HIGH,
                impact_score=1.0,
                target_content_types=list(ContentType),
                action_items=[
                    "Conduct full content strategy audit",
                    "Review all content types and creation processes",
                    "Implement comprehensive improvement plan",
                    "Set up enhanced monitoring and analytics",
                    "Consider external content strategy consultation"
                ],
                expected_outcome="Comprehensive turnaround of content performance",
                implementation_difficulty="Very High",
                estimated_time_hours=20
            ))
        
        # Critical improvement area recommendations
        for area in improvement_areas:
            if area.get('priority') == 'high':
                recommendations.append(Recommendation(
                    id=f"critical_{area['area']}",
                    title=f"Address Critical Issue: {area['area'].replace('_', ' ').title()}",
                    description=area.get('description', 'Critical issue identified in content analysis.'),
                    recommendation_type=RecommendationType.CONTENT_OPTIMIZATION,
                    priority=Priority.HIGH,
                    impact_score=0.9,
                    target_content_types=self._map_area_to_content_types(area['area']),
                    action_items=[area.get('recommendation', 'Implement immediate corrective action')],
                    expected_outcome="Resolution of critical content issue",
                    implementation_difficulty="Medium",
                    estimated_time_hours=8
                ))
        
        return recommendations
    
    def _filter_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Filter and deduplicate recommendations."""
        seen_recommendations = set()
        filtered = []
        
        for rec in recommendations:
            # Create signature for deduplication
            signature = (rec.title, rec.recommendation_type.value)
            
            if signature not in seen_recommendations:
                seen_recommendations.add(signature)
                filtered.append(rec)
        
        # Limit recommendations per session based on priority
        high_priority = [r for r in filtered if r.priority == Priority.HIGH][:3]
        medium_priority = [r for r in filtered if r.priority == Priority.MEDIUM][:4]
        low_priority = [r for r in filtered if r.priority == Priority.LOW][:3]
        
        return high_priority + medium_priority + low_priority
    
    def _map_area_to_content_types(self, area: str) -> List[ContentType]:
        """Map improvement area to relevant content types."""
        area_mapping = {
            'sentiment_optimization': [ContentType.TONE, ContentType.SCRIPT],
            'engagement_optimization': [ContentType.STRUCTURE, ContentType.CALL_TO_ACTION],
            'script_optimization': [ContentType.SCRIPT],
            'thumbnail_optimization': [ContentType.THUMBNAIL],
            'title_optimization': [ContentType.TITLE],
            'description_optimization': [ContentType.DESCRIPTION],
            'hashtag_optimization': [ContentType.HASHTAGS]
        }
        
        return area_mapping.get(area, [ContentType.STRUCTURE])
    
    def get_recommendation_summary(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Generate summary of recommendations."""
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        type_counts = defaultdict(int)
        total_impact = 0
        total_time = 0
        
        for rec in recommendations:
            priority_counts[rec.priority.value] += 1
            type_counts[rec.recommendation_type.value] += 1
            total_impact += rec.impact_score
            total_time += rec.estimated_time_hours
        
        return {
            'total_recommendations': len(recommendations),
            'priority_distribution': priority_counts,
            'type_distribution': dict(type_counts),
            'average_impact_score': total_impact / len(recommendations) if recommendations else 0,
            'total_estimated_hours': total_time,
            'key_focus_areas': list(type_counts.keys())[:3],
            'immediate_actions_needed': [r for r in recommendations if r.priority == Priority.HIGH]
        }