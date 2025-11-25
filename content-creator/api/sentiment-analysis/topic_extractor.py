"""
Topic Extraction Module - Extract and categorize topics from comments
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime
import math

from .sentiment_analyzer import CommentAnalysis

logger = logging.getLogger(__name__)

@dataclass
class TopicScore:
    """Topic with relevance score"""
    topic: str
    relevance_score: float
    frequency: int
    sentiment_association: float
    keywords: List[str]

@dataclass
class TopicAnalysis:
    """Complete topic analysis result"""
    primary_topics: List[TopicScore]
    emerging_topics: List[TopicScore]
    declining_topics: List[TopicScore]
    topic_trends: Dict[str, List[float]]
    topic_relationships: Dict[str, List[str]]
    content_recommendations: List[str]

class TopicExtractor:
    """Advanced topic extraction and analysis"""
    
    def __init__(self):
        self.topic_taxonomy = self._load_topic_taxonomy()
        self.topic_keywords = self._build_topic_keywords()
        self.nlp_processors = {}
        
    def extract_topics(self, comments: List[CommentAnalysis], 
                      time_window: Optional[Dict[str, str]] = None) -> TopicAnalysis:
        """
        Extract topics from a collection of comments
        
        Args:
            comments: List of analyzed comments
            time_window: Optional time window for trend analysis
            
        Returns:
            TopicAnalysis with topic insights
        """
        # Extract all text content
        all_texts = [comment.text for comment in comments]
        
        # Perform topic scoring
        topic_scores = self._score_topics(comments)
        
        # Identify primary topics (highest scores)
        primary_topics = sorted(topic_scores, key=lambda x: x.relevance_score, reverse=True)[:10]
        
        # Identify emerging topics (recent high activity)
        emerging_topics = self._identify_emerging_topics(comments, topic_scores)
        
        # Identify declining topics (recent low activity)
        declining_topics = self._identify_declining_topics(comments, topic_scores)
        
        # Calculate topic trends
        topic_trends = self._calculate_topic_trends(comments)
        
        # Identify topic relationships
        topic_relationships = self._identify_topic_relationships(comments)
        
        # Generate content recommendations
        content_recommendations = self._generate_content_recommendations(
            primary_topics, emerging_topics, topic_trends
        )
        
        return TopicAnalysis(
            primary_topics=primary_topics,
            emerging_topics=emerging_topics,
            declining_topics=declining_topics,
            topic_trends=topic_trends,
            topic_relationships=topic_relationships,
            content_recommendations=content_recommendations
        )
    
    def _score_topics(self, comments: List[CommentAnalysis]) -> List[TopicScore]:
        """Score topics based on frequency, sentiment, and engagement"""
        topic_data = defaultdict(lambda: {
            'frequency': 0,
            'sentiment_sum': 0,
            'sentiment_count': 0,
            'keywords': Counter(),
            'engagement_sum': 0
        })
        
        for comment in comments:
            for topic in comment.topics:
                topic_data[topic]['frequency'] += 1
                topic_data[topic]['sentiment_sum'] += comment.sentiment.overall_score
                topic_data[topic]['sentiment_count'] += 1
                topic_data[topic]['engagement_sum'] += comment.engagement_indicators.get('engagement_potential', 0)
                
                # Add keywords from this comment
                for phrase in comment.key_phrases:
                    topic_data[topic]['keywords'][phrase] += 1
        
        # Calculate scores
        scored_topics = []
        total_comments = len(comments)
        
        for topic, data in topic_data.items():
            # Frequency score (normalized)
            frequency_score = data['frequency'] / total_comments if total_comments > 0 else 0
            
            # Sentiment association (average sentiment for this topic)
            sentiment_association = (
                data['sentiment_sum'] / data['sentiment_count'] 
                if data['sentiment_count'] > 0 else 0
            )
            
            # Engagement score
            engagement_score = data['engagement_sum'] / data['frequency'] if data['frequency'] > 0 else 0
            
            # Combined relevance score
            relevance_score = (
                frequency_score * 0.4 +
                abs(sentiment_association) * 0.3 +
                engagement_score * 0.3
            )
            
            # Get top keywords for this topic
            top_keywords = [word for word, count in data['keywords'].most_common(5)]
            
            scored_topics.append(TopicScore(
                topic=topic,
                relevance_score=relevance_score,
                frequency=data['frequency'],
                sentiment_association=sentiment_association,
                keywords=top_keywords
            ))
        
        return scored_topics
    
    def _identify_emerging_topics(self, comments: List[CommentAnalysis], 
                                 topic_scores: List[TopicScore]) -> List[TopicScore]:
        """Identify topics that are gaining traction"""
        # Simple implementation - in production, this would use time-based analysis
        # For now, we'll use topics with high sentiment but lower frequency as "emerging"
        
        emerging_threshold = 0.6  # High sentiment threshold
        frequency_threshold = 3   # Low frequency threshold
        
        emerging = []
        for topic_score in topic_scores:
            if (topic_score.sentiment_association > emerging_threshold and 
                topic_score.frequency >= frequency_threshold and
                topic_score.relevance_score > 0.3):
                emerging.append(topic_score)
        
        return sorted(emerging, key=lambda x: x.sentiment_association, reverse=True)[:5]
    
    def _identify_declining_topics(self, comments: List[CommentAnalysis], 
                                  topic_scores: List[TopicScore]) -> List[TopicScore]:
        """Identify topics that are losing relevance"""
        # Simple implementation - topics with negative sentiment and high frequency
        
        declining_threshold = -0.4  # Low sentiment threshold
        frequency_threshold = 5     # Minimum frequency to be considered
        
        declining = []
        for topic_score in topic_scores:
            if (topic_score.sentiment_association < declining_threshold and 
                topic_score.frequency >= frequency_threshold):
                declining.append(topic_score)
        
        return sorted(declining, key=lambda x: x.sentiment_association)[:5]
    
    def _calculate_topic_trends(self, comments: List[CommentAnalysis]) -> Dict[str, List[float]]:
        """Calculate trend data for topics over time"""
        # Group comments by time periods (simplified - using comment index as proxy for time)
        time_periods = 5  # Divide comments into 5 time periods
        period_size = max(1, len(comments) // time_periods)
        
        topic_trends = defaultdict(lambda: [0.0] * time_periods)
        
        for i, comment in enumerate(comments):
            period = min(i // period_size, time_periods - 1)
            sentiment_score = comment.sentiment.overall_score
            
            for topic in comment.topics:
                # Add sentiment score to topic trend
                topic_trends[topic][period] += sentiment_score
                
                # Normalize by frequency in this period
                period_comments = comments[period * period_size:min((period + 1) * period_size, len(comments))]
                topic_frequency = sum(1 for c in period_comments if topic in c.topics)
                if topic_frequency > 0:
                    topic_trends[topic][period] /= topic_frequency
        
        return dict(topic_trends)
    
    def _identify_topic_relationships(self, comments: List[CommentAnalysis]) -> Dict[str, List[str]]:
        """Identify relationships between topics (topics that appear together)"""
        topic_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for comment in comments:
            comment_topics = comment.topics
            # Count co-occurrences
            for i, topic1 in enumerate(comment_topics):
                for topic2 in comment_topics[i+1:]:
                    topic_cooccurrence[topic1][topic2] += 1
                    topic_cooccurrence[topic2][topic1] += 1
        
        # Find strong relationships (high co-occurrence)
        relationships = {}
        min_cooccurrence = 2
        
        for topic1, related_topics in topic_cooccurrence.items():
            strong_relationships = [
                topic2 for topic2, count in related_topics.items() 
                if count >= min_cooccurrence
            ]
            if strong_relationships:
                relationships[topic1] = strong_relationships
        
        return dict(relationships)
    
    def _generate_content_recommendations(self, 
                                        primary_topics: List[TopicScore],
                                        emerging_topics: List[TopicScore],
                                        topic_trends: Dict[str, List[float]]) -> List[str]:
        """Generate content recommendations based on topic analysis"""
        recommendations = []
        
        # Primary topic recommendations
        if primary_topics:
            top_topic = primary_topics[0]
            recommendations.append(f"Focus more content on '{top_topic.topic}' - it's your most discussed topic")
            
            if top_topic.sentiment_association > 0.3:
                recommendations.append(f"Leverage the positive sentiment around '{top_topic.topic}' in your marketing")
            elif top_topic.sentiment_association < -0.3:
                recommendations.append(f"Address concerns about '{top_topic.topic}' in upcoming content")
        
        # Emerging topic recommendations
        if emerging_topics:
            for emerging in emerging_topics[:2]:
                recommendations.append(f"Create more content around '{emerging.topic}' - it's gaining positive traction")
        
        # Trend-based recommendations
        for topic, trend_data in topic_trends.items():
            if len(trend_data) >= 2:
                # Check for upward trend
                recent_avg = sum(trend_data[-2:]) / 2
                early_avg = sum(trend_data[:2]) / 2
                
                if recent_avg > early_avg + 0.2:
                    recommendations.append(f"Capitalize on the growing interest in '{topic}' with targeted content")
                elif recent_avg < early_avg - 0.2:
                    recommendations.append(f"Revitalize content about '{topic}' - interest may be declining")
        
        # Sentiment-based recommendations
        positive_topics = [t for t in primary_topics if t.sentiment_association > 0.3]
        if positive_topics:
            recommendations.append(f"Use positive topics like '{positive_topics[0].topic}' for viral content strategies")
        
        return recommendations[:8]  # Limit recommendations
    
    def extract_key_topics_from_text(self, text: str) -> List[str]:
        """Extract topics from a single text string"""
        # This is a simpler method for quick topic extraction
        text_lower = text.lower()
        identified_topics = []
        
        for topic, keywords in self.topic_keywords.items():
            keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
            if keyword_matches >= 1:  # At least one keyword match
                identified_topics.append(topic)
        
        return identified_topics
    
    def get_topic_suggestions(self, current_topics: List[str], 
                            content_goals: List[str]) -> List[str]:
        """Suggest new topics based on current topics and content goals"""
        suggestions = []
        
        # Topic expansion based on current topics
        topic_expansions = {
            'technical': ['advanced tutorials', 'troubleshooting', 'best practices'],
            'educational': ['case studies', 'examples', 'comparisons'],
            'engagement': ['interactive content', 'polls', 'challenges'],
            'productivity': ['workflow optimization', 'time management', 'automation'],
            'ui_ux': ['user feedback', 'design principles', 'accessibility']
        }
        
        for topic in current_topics:
            if topic in topic_expansions:
                suggestions.extend(topic_expansions[topic])
        
        # Goal-based suggestions
        goal_topic_mapping = {
            'increase engagement': ['interactive content', 'community discussions', 'Q&A sessions'],
            'educational content': ['step-by-step guides', 'beginner tutorials', 'advanced techniques'],
            'brand awareness': ['behind-the-scenes', 'company culture', 'success stories'],
            'productivity': ['efficiency tips', 'time-saving hacks', 'workflow optimization']
        }
        
        for goal in content_goals:
            if goal in goal_topic_mapping:
                suggestions.extend(goal_topic_mapping[goal])
        
        return list(set(suggestions))  # Remove duplicates
    
    def _load_topic_taxonomy(self) -> Dict[str, List[str]]:
        """Load comprehensive topic taxonomy"""
        return {
            'content_quality': {
                'video_quality', 'audio_quality', 'editing', 'production_value',
                'resolution', 'lighting', 'visuals', 'graphics'
            },
            'educational_value': {
                'learning', 'tutorial', 'guide', 'instruction', 'explanation',
                'teaching', 'knowledge', 'skills', 'tips', 'advice'
            },
            'engagement': {
                'entertaining', 'fun', 'interesting', 'captivating', 'boring',
                'engaging', 'interactive', 'exciting', 'amazing', 'wow'
            },
            'technical_aspects': {
                'tutorial', 'setup', 'installation', 'configuration', 'troubleshooting',
                'debug', 'error', 'problem', 'solution', 'fix'
            },
            'user_experience': {
                'easy', 'simple', 'difficult', 'confusing', 'clear', 'user-friendly',
                'intuitive', 'navigation', 'interface', 'design'
            },
            'performance': {
                'fast', 'slow', 'speed', 'performance', 'optimization', 'efficiency',
                'loading', 'lag', 'responsive', 'smooth'
            },
            'accessibility': {
                'accessible', 'inclusive', 'diverse', 'multilingual', 'subtitles',
                'closed_captions', ' disabilities', 'barrier-free'
            },
            'monetization': {
                'price', 'cost', 'free', 'premium', 'subscription', 'value',
                'worth', 'affordable', 'expensive', 'roi'
            },
            'community': {
                'community', 'discussion', 'feedback', 'comments', 'interaction',
                'collaboration', 'sharing', 'support', 'help'
            },
            'trends': {
                'trending', 'viral', 'popular', 'latest', 'new', 'innovative',
                'cutting-edge', 'modern', 'contemporary'
            }
        }
    
    def _build_topic_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mapping for topic identification"""
        topic_keywords = {}
        
        for category, keywords in self.topic_taxonomy.items():
            # Add each keyword to the category
            topic_keywords[category] = list(keywords)
            
            # Add common variations and synonyms
            variations = {
                'video_quality': ['hd', '4k', '1080p', 'clear', 'sharp', 'pixelated'],
                'audio_quality': ['sound', 'volume', 'clear audio', 'background noise'],
                'educational_value': ['learn', 'education', 'teach', 'informative'],
                'engagement': ['fun', 'enjoy', 'love', 'like', 'entertaining'],
                'technical_aspects': ['how to', 'step by step', 'tutorial', 'guide'],
                'user_experience': ['easy', 'simple', 'user friendly', 'intuitive'],
                'performance': ['fast', 'quick', 'speed', 'performance', 'efficient'],
                'trends': ['trending', 'viral', 'popular', 'latest', 'new']
            }
            
            if category in variations:
                topic_keywords[category].extend(variations[category])
        
        return topic_keywords