"""
Improvement Opportunities Module - Identify specific areas for content improvement
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import math

from .sentiment_analyzer import CommentAnalysis, SentimentScore
from .topic_extractor import TopicAnalysis, TopicScore

logger = logging.getLogger(__name__)

@dataclass
class ImprovementOpportunity:
    """Specific improvement opportunity with details"""
    category: str
    priority: int  # 1-5, where 5 is highest priority
    title: str
    description: str
    evidence: List[str]
    suggested_actions: List[str]
    expected_impact: str
    implementation_difficulty: str
    timeframe: str

@dataclass
class ImprovementAnalysis:
    """Complete improvement analysis result"""
    opportunities: List[ImprovementOpportunity]
    critical_issues: List[ImprovementOpportunity]
    quick_wins: List[ImprovementOpportunity]
    long_term_improvements: List[ImprovementOpportunity]
    content_gaps: List[str]
    engagement_strategies: List[str]
    performance_metrics: Dict[str, float]

class ImprovementIdentifier:
    """Identify specific improvement opportunities from feedback"""
    
    def __init__(self):
        self.improvement_categories = self._load_improvement_categories()
        self.action_templates = self._load_action_templates()
        self.impact_mapping = self._load_impact_mapping()
        
    def identify_opportunities(self, 
                             comments: List[CommentAnalysis],
                             topic_analysis: TopicAnalysis,
                             time_period_days: int = 30) -> ImprovementAnalysis:
        """
        Identify improvement opportunities from comments and topic analysis
        
        Args:
            comments: List of analyzed comments
            topic_analysis: Topic analysis results
            time_period_days: Time period to analyze (for trend calculation)
            
        Returns:
            ImprovementAnalysis with opportunities and recommendations
        """
        # Filter comments by time period (simplified)
        recent_comments = self._filter_recent_comments(comments, time_period_days)
        
        # Identify improvement opportunities by category
        opportunities = self._categorize_opportunities(recent_comments, topic_analysis)
        
        # Identify critical issues (high priority, negative sentiment)
        critical_issues = self._identify_critical_issues(opportunities, recent_comments)
        
        # Identify quick wins (easy to implement, high impact)
        quick_wins = self._identify_quick_wins(opportunities)
        
        # Identify long-term improvements (complex but high value)
        long_term_improvements = self._identify_long_term_improvements(opportunities)
        
        # Identify content gaps
        content_gaps = self._identify_content_gaps(topic_analysis, recent_comments)
        
        # Generate engagement strategies
        engagement_strategies = self._generate_engagement_strategies(recent_comments, topic_analysis)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(recent_comments, topic_analysis)
        
        return ImprovementAnalysis(
            opportunities=opportunities,
            critical_issues=critical_issues,
            quick_wins=quick_wins,
            long_term_improvements=long_term_improvements,
            content_gaps=content_gaps,
            engagement_strategies=engagement_strategies,
            performance_metrics=performance_metrics
        )
    
    def _filter_recent_comments(self, comments: List[CommentAnalysis], 
                               days: int) -> List[CommentAnalysis]:
        """Filter comments by recent time period"""
        # Simplified implementation - in production, use actual timestamps
        # For now, return all comments as they're all considered "recent"
        return comments
    
    def _categorize_opportunities(self, 
                                comments: List[CommentAnalysis],
                                topic_analysis: TopicAnalysis) -> List[ImprovementOpportunity]:
        """Categorize opportunities by improvement area"""
        opportunities = []
        
        # Analyze each category
        for category, keywords in self.improvement_categories.items():
            category_comments = []
            category_keywords_found = []
            
            for comment in comments:
                # Check if comment relates to this category
                comment_text_lower = comment.text.lower()
                keywords_found = [kw for kw in keywords if kw in comment_text_lower]
                
                if keywords_found:
                    category_comments.append(comment)
                    category_keywords_found.extend(keywords_found)
            
            if category_comments:
                opportunity = self._create_category_opportunity(
                    category, category_comments, category_keywords_found, topic_analysis
                )
                if opportunity:
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _create_category_opportunity(self, 
                                   category: str,
                                   comments: List[CommentAnalysis],
                                   keywords_found: List[str],
                                   topic_analysis: TopicAnalysis) -> Optional[ImprovementOpportunity]:
        """Create improvement opportunity for a specific category"""
        if not comments:
            return None
        
        # Calculate average sentiment for this category
        avg_sentiment = sum(c.sentiment.overall_score for c in comments) / len(comments)
        
        # Calculate priority based on sentiment and frequency
        frequency_score = len(comments) / len(topic_analysis.primary_topics) if topic_analysis.primary_topics else 0
        priority = self._calculate_priority(avg_sentiment, frequency_score, len(comments))
        
        # Generate evidence
        evidence = self._generate_evidence(comments, keywords_found)
        
        # Generate actions
        suggested_actions = self._generate_suggested_actions(category, avg_sentiment, comments)
        
        # Determine impact and difficulty
        expected_impact = self._determine_expected_impact(category, avg_sentiment)
        implementation_difficulty = self._determine_difficulty(category, len(comments))
        timeframe = self._determine_timeframe(category, priority)
        
        # Create opportunity
        return ImprovementOpportunity(
            category=category,
            priority=priority,
            title=f"Improve {category.replace('_', ' ').title()}",
            description=self._generate_description(category, avg_sentiment, len(comments)),
            evidence=evidence,
            suggested_actions=suggested_actions,
            expected_impact=expected_impact,
            implementation_difficulty=implementation_difficulty,
            timeframe=timeframe
        )
    
    def _calculate_priority(self, sentiment: float, frequency: float, count: int) -> int:
        """Calculate priority score (1-5)"""
        # Priority is higher for more negative sentiment and higher frequency
        negativity = max(0, -sentiment)  # Only negative sentiment matters for priority
        frequency_factor = min(1.0, frequency)
        
        priority_score = (negativity * 0.6 + frequency_factor * 0.4) * 5
        
        return max(1, min(5, int(priority_score)))
    
    def _generate_evidence(self, comments: List[CommentAnalysis], keywords: List[str]) -> List[str]:
        """Generate evidence from comments"""
        evidence = []
        
        # Find representative comments
        sorted_comments = sorted(comments, key=lambda c: abs(c.sentiment.overall_score), reverse=True)
        
        for comment in sorted_comments[:3]:  # Top 3 most sentiment-laden comments
            # Truncate long comments
            text = comment.text[:100] + "..." if len(comment.text) > 100 else comment.text
            evidence.append(f"'{text}' (Sentiment: {comment.sentiment.overall_score:.2f})")
        
        # Add keyword evidence
        if keywords:
            keyword_counts = Counter(keywords)
            top_keywords = [f"{word} ({count} mentions)" for word, count in keyword_counts.most_common(3)]
            evidence.extend(top_keywords)
        
        return evidence
    
    def _generate_suggested_actions(self, category: str, sentiment: float, 
                                  comments: List[CommentAnalysis]) -> List[str]:
        """Generate specific suggested actions"""
        actions = []
        
        # Get base actions for category
        if category in self.action_templates:
            base_actions = self.action_templates[category]
            actions.extend(base_actions)
        
        # Add sentiment-specific actions
        if sentiment < -0.3:
            actions.append("Address negative feedback proactively in future content")
            actions.append("Create follow-up content to clarify confusing topics")
        elif sentiment > 0.3:
            actions.append("Leverage positive feedback for testimonials")
            actions.append("Create more content in this successful area")
        
        # Add comment-specific insights
        engagement_issues = any(c.engagement_indicators.get('engagement_potential', 0) < 0.3 for c in comments)
        if engagement_issues:
            actions.append("Improve content engagement through more interactive elements")
        
        return actions[:5]  # Limit to top 5 actions
    
    def _generate_description(self, category: str, sentiment: float, count: int) -> str:
        """Generate descriptive text for the opportunity"""
        sentiment_desc = "negative" if sentiment < -0.1 else "positive" if sentiment > 0.1 else "neutral"
        
        return f"Analysis shows {count} comments related to {category.replace('_', ' ')} with {sentiment_desc} sentiment. This area shows potential for improvement to enhance overall content quality and audience satisfaction."
    
    def _determine_expected_impact(self, category: str, sentiment: float) -> str:
        """Determine expected impact of improvement"""
        if abs(sentiment) > 0.5:
            return "High - Significant improvement in audience satisfaction"
        elif abs(sentiment) > 0.3:
            return "Medium - Noticeable improvement in content quality"
        else:
            return "Low - Minor enhancement to user experience"
    
    def _determine_difficulty(self, category: str, frequency: int) -> str:
        """Determine implementation difficulty"""
        high_difficulty_categories = {'technical_infrastructure', 'major_redesign', 'content_strategy_overhaul'}
        medium_difficulty_categories = {'content_quality', 'engagement', 'user_experience'}
        
        if category in high_difficulty_categories:
            return "High - Requires significant resources and time"
        elif category in medium_difficulty_categories:
            return "Medium - Moderate effort with clear implementation path"
        else:
            return "Low - Quick implementation with minimal resources"
    
    def _determine_timeframe(self, category: str, priority: int) -> str:
        """Determine suggested implementation timeframe"""
        if priority >= 4:
            return "Immediate (1-2 weeks)"
        elif priority >= 3:
            return "Short-term (1 month)"
        elif priority >= 2:
            return "Medium-term (2-3 months)"
        else:
            return "Long-term (3+ months)"
    
    def _identify_critical_issues(self, opportunities: List[ImprovementOpportunity],
                                comments: List[CommentAnalysis]) -> List[ImprovementOpportunity]:
        """Identify critical issues that need immediate attention"""
        critical = []
        
        for opportunity in opportunities:
            if (opportunity.priority >= 4 and 
                any(issue in opportunity.category for issue in ['technical', 'usability', 'content_errors'])):
                critical.append(opportunity)
        
        # Also check for overwhelming negative sentiment
        if comments:
            negative_comments = [c for c in comments if c.sentiment.overall_score < -0.5]
            if len(negative_comments) > len(comments) * 0.2:  # More than 20% very negative
                critical.append(ImprovementOpportunity(
                    category="urgent_overall_improvement",
                    priority=5,
                    title="Address Overwhelming Negative Feedback",
                    description="More than 20% of recent comments show very negative sentiment. Immediate action required.",
                    evidence=[f"{len(negative_comments)} highly negative comments identified"],
                    suggested_actions=["Conduct comprehensive content review", "Survey audience for specific concerns", "Implement immediate improvements"],
                    expected_impact="Critical - Prevent further audience loss",
                    implementation_difficulty="High",
                    timeframe="Immediate (1-2 weeks)"
                ))
        
        return sorted(critical, key=lambda x: x.priority, reverse=True)
    
    def _identify_quick_wins(self, opportunities: List[ImprovementOpportunity]) -> List[ImprovementOpportunity]:
        """Identify opportunities that are easy to implement but impactful"""
        quick_wins = []
        
        for opportunity in opportunities:
            if (opportunity.implementation_difficulty == "Low" and 
                opportunity.expected_impact in ["Medium - Noticeable improvement in content quality", "High - Significant improvement in audience satisfaction"]):
                quick_wins.append(opportunity)
        
        return sorted(quick_wins, key=lambda x: x.priority, reverse=True)[:5]
    
    def _identify_long_term_improvements(self, opportunities: List[ImprovementOpportunity]) -> List[ImprovementOpportunity]:
        """Identify complex but high-value improvements"""
        long_term = []
        
        for opportunity in opportunities:
            if (opportunity.implementation_difficulty == "High" and 
                opportunity.expected_impact == "High - Significant improvement in audience satisfaction"):
                long_term.append(opportunity)
        
        return sorted(long_term, key=lambda x: x.priority, reverse=True)
    
    def _identify_content_gaps(self, topic_analysis: TopicAnalysis, 
                              comments: List[CommentAnalysis]) -> List[str]:
        """Identify gaps in content coverage"""
        gaps = []
        
        # Check for topics with positive sentiment but low coverage
        underserved_positive = [
            topic for topic in topic_analysis.primary_topics 
            if topic.sentiment_association > 0.3 and topic.frequency < 5
        ]
        
        for topic in underserved_positive:
            gaps.append(f"Create more content about '{topic.topic}' - high positive sentiment but low coverage")
        
        # Check for topics with questions but few answers
        question_topics = []
        for comment in comments:
            if '?' in comment.text:
                question_topics.extend(comment.topics)
        
        question_counter = Counter(question_topics)
        answered_topics = set(topic.topic for topic in topic_analysis.primary_topics)
        
        for topic, question_count in question_counter.most_common(5):
            if topic not in answered_topics and question_count >= 2:
                gaps.append(f"Address frequently asked questions about '{topic}'")
        
        return gaps[:7]
    
    def _generate_engagement_strategies(self, comments: List[CommentAnalysis],
                                      topic_analysis: TopicAnalysis) -> List[str]:
        """Generate engagement improvement strategies"""
        strategies = []
        
        # Analyze engagement levels
        avg_engagement = sum(
            c.engagement_indicators.get('engagement_potential', 0) 
            for c in comments
        ) / len(comments) if comments else 0
        
        if avg_engagement < 0.5:
            strategies.append("Implement more interactive content formats (polls, quizzes, challenges)")
            strategies.append("Ask direct questions to encourage audience participation")
            strategies.append("Create content that sparks discussion and debate")
        
        # Topic-based strategies
        for topic in topic_analysis.primary_topics[:3]:
            if topic.sentiment_association > 0.2:
                strategies.append(f"Host Q&A sessions about '{topic.topic}' to capitalize on positive sentiment")
        
        # Comment-based strategies
        questions_count = sum(1 for c in comments if '?' in c.text)
        if questions_count > len(comments) * 0.3:
            strategies.append("Respond to questions more promptly to build community engagement")
            strategies.append("Create FAQ content addressing common questions")
        
        return strategies[:6]
    
    def _calculate_performance_metrics(self, comments: List[CommentAnalysis],
                                     topic_analysis: TopicAnalysis) -> Dict[str, float]:
        """Calculate key performance metrics"""
        if not comments:
            return {}
        
        metrics = {}
        
        # Sentiment metrics
        sentiments = [c.sentiment.overall_score for c in comments]
        metrics['average_sentiment'] = sum(sentiments) / len(sentiments)
        metrics['sentiment_variance'] = self._calculate_variance(sentiments)
        metrics['positive_sentiment_ratio'] = sum(1 for s in sentiments if s > 0.1) / len(sentiments)
        metrics['negative_sentiment_ratio'] = sum(1 for s in sentiments if s < -0.1) / len(sentiments)
        
        # Engagement metrics
        engagements = [c.engagement_indicators.get('engagement_potential', 0) for c in comments]
        metrics['average_engagement'] = sum(engagements) / len(engagements)
        metrics['high_engagement_ratio'] = sum(1 for e in engagements if e > 0.7) / len(engagements)
        
        # Topic diversity
        all_topics = []
        for comment in comments:
            all_topics.extend(comment.topics)
        unique_topics = len(set(all_topics))
        metrics['topic_diversity'] = unique_topics / len(all_topics) if all_topics else 0
        
        return metrics
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def _load_improvement_categories(self) -> Dict[str, List[str]]:
        """Load improvement category keywords"""
        return {
            'content_quality': [
                'quality', 'resolution', 'audio', 'video', 'editing', 'production',
                'clear', 'crisp', 'professional', 'polished', 'refined'
            ],
            'technical_issues': [
                'error', 'bug', 'broken', 'not working', 'crash', 'lag', 'slow',
                'loading', 'freeze', 'problem', 'issue', 'trouble'
            ],
            'user_experience': [
                'difficult', 'confusing', 'hard to use', 'complicated', 'interface',
                'navigation', 'user-friendly', 'intuitive', 'easy', 'simple'
            ],
            'engagement': [
                'boring', 'uninteresting', 'engaging', 'captivating', 'entertaining',
                'fun', 'interactive', 'boring', 'dry', 'monotonous'
            ],
            'educational_value': [
                'educational', 'informative', 'helpful', 'useful', 'learning',
                'teaching', 'tutorial', 'guide', 'explained', 'clarified'
            ],
            'content_length': [
                'too long', 'too short', 'length', 'duration', 'quick', 'brief',
                'detailed', 'comprehensive', 'thorough', 'shallow'
            ],
            'pace_timing': [
                'pace', 'speed', 'fast', 'slow', 'timing', 'rushed', 'drawn out',
                'rhythm', 'flow', 'transition'
            ],
            'accessibility': [
                'subtitle', 'caption', 'accessibility', 'hard of hearing', 'visual impairment',
                'language', 'translation', 'comprehension', 'understandable'
            ]
        }
    
    def _load_action_templates(self) -> Dict[str, List[str]]:
        """Load action templates for each improvement category"""
        return {
            'content_quality': [
                "Improve video/audio quality standards",
                "Enhance post-production editing process",
                "Invest in better equipment or software",
                "Implement quality control checkpoints"
            ],
            'technical_issues': [
                "Fix reported bugs and technical problems",
                "Implement better error handling",
                "Optimize performance and loading times",
                "Conduct thorough testing before release"
            ],
            'user_experience': [
                "Simplify user interface and navigation",
                "Improve content organization and structure",
                "Add helpful tutorials or guides",
                "Conduct user experience testing"
            ],
            'engagement': [
                "Add interactive elements to content",
                "Vary content format and style",
                "Include more dynamic visual elements",
                "Encourage audience participation"
            ],
            'educational_value': [
                "Provide more detailed explanations",
                "Include practical examples and case studies",
                "Add supplementary learning materials",
                "Structure content for better learning outcomes"
            ],
            'content_length': [
                "Adjust content length to optimal duration",
                "Create both brief and comprehensive versions",
                "Improve content density and pacing",
                "Segment long content into digestible parts"
            ],
            'pace_timing': [
                "Adjust content pacing for better flow",
                "Improve transitions between sections",
                "Optimize timing for key points",
                "Test different pacing approaches"
            ],
            'accessibility': [
                "Add closed captions and subtitles",
                "Improve visual accessibility features",
                "Provide content in multiple formats",
                "Ensure compliance with accessibility standards"
            ]
        }
    
    def _load_impact_mapping(self) -> Dict[str, str]:
        """Load impact assessment mappings"""
        return {
            'content_quality': 'High - Directly affects viewer satisfaction',
            'technical_issues': 'Critical - Can completely block content consumption',
            'user_experience': 'High - Determines ease of content engagement',
            'engagement': 'Medium - Affects content virality and sharing',
            'educational_value': 'High - Core value proposition for educational content',
            'content_length': 'Medium - Affects completion rates and accessibility',
            'pace_timing': 'Medium - Influences viewer retention and enjoyment',
            'accessibility': 'Medium - Expands potential audience reach'
        }