"""
Sentiment Analysis Module - Core sentiment analysis functionality
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import Counter, defaultdict
import math

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Sentiment score with detailed breakdown"""
    overall_score: float  # -1.0 to 1.0 (negative to positive)
    confidence: float  # 0.0 to 1.0
    positive_score: float
    negative_score: float
    neutral_score: float
    emotion_scores: Dict[str, float]  # joy, anger, fear, sadness, surprise, disgust
    subjectivity: float  # 0.0 (objective) to 1.0 (subjective)

@dataclass
class CommentAnalysis:
    """Complete analysis of a single comment"""
    comment_id: str
    text: str
    platform: str
    timestamp: str
    sentiment: SentimentScore
    key_phrases: List[str]
    topics: List[str]
    improvement_suggestions: List[str]
    engagement_indicators: Dict[str, float]
    language_features: Dict[str, Any]

class SentimentAnalyzer:
    """Advanced sentiment analysis with NLP techniques"""
    
    def __init__(self):
        self.positive_words = self._load_positive_lexicon()
        self.negative_words = self._load_negative_lexicon()
        self.emotion_lexicon = self._load_emotion_lexicon()
        self.intensifiers = self._load_intensifiers()
        self.negation_words = self._load_negation_words()
        self.topic_keywords = self._load_topic_keywords()
        
    def analyze_comment(self, comment_text: str, platform: str, 
                       comment_id: Optional[str] = None) -> CommentAnalysis:
        """
        Perform comprehensive sentiment analysis on a comment
        
        Args:
            comment_text: The comment text to analyze
            platform: Social media platform (youtube, twitter, instagram, etc.)
            comment_id: Optional comment identifier
            
        Returns:
            CommentAnalysis with all sentiment metrics
        """
        if not comment_id:
            comment_id = f"comment_{hash(comment_text)}"
        
        # Preprocess text
        processed_text = self._preprocess_text(comment_text)
        
        # Calculate sentiment scores
        sentiment = self._calculate_sentiment_scores(processed_text)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(processed_text)
        
        # Identify topics
        topics = self._identify_topics(processed_text)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            sentiment, topics, key_phrases
        )
        
        # Calculate engagement indicators
        engagement_indicators = self._calculate_engagement_indicators(
            comment_text, sentiment
        )
        
        # Extract language features
        language_features = self._extract_language_features(comment_text)
        
        return CommentAnalysis(
            comment_id=comment_id,
            text=comment_text,
            platform=platform,
            timestamp=datetime.now().isoformat(),
            sentiment=sentiment,
            key_phrases=key_phrases,
            topics=topics,
            improvement_suggestions=improvement_suggestions,
            engagement_indicators=engagement_indicators,
            language_features=language_features
        )
    
    def analyze_batch(self, comments: List[Dict[str, Any]]) -> List[CommentAnalysis]:
        """Analyze multiple comments efficiently"""
        results = []
        
        for comment_data in comments:
            try:
                analysis = self.analyze_comment(
                    comment_text=comment_data.get('text', ''),
                    platform=comment_data.get('platform', 'unknown'),
                    comment_id=comment_data.get('id')
                )
                results.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing comment {comment_data.get('id', 'unknown')}: {e}")
                continue
                
        return results
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Handle emojis (basic emoji handling)
        emoji_pattern = re.compile("["
                                  u"\U0001F600-\U0001F64F"  # emoticons
                                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                  "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        return text
    
    def _calculate_sentiment_scores(self, text: str) -> SentimentScore:
        """Calculate detailed sentiment scores"""
        words = text.split()
        
        # Count sentiment words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Apply negation handling
        negation_context = self._apply_negation(words)
        
        # Calculate emotion scores
        emotion_scores = self._calculate_emotion_scores(words)
        
        # Calculate subjectivity
        subjectivity = self._calculate_subjectivity(words)
        
        # Calculate overall sentiment
        total_words = len(words) if words else 1
        raw_positive = positive_count / total_words
        raw_negative = negative_count / total_words
        
        # Adjust for negation
        if negation_context['negated_words'] > 0:
            raw_positive, raw_negative = raw_negative, raw_positive
        
        # Apply intensifiers
        intensity_multiplier = 1.0 + (negation_context['intensifiers'] * 0.3)
        raw_positive *= intensity_multiplier
        raw_negative *= intensity_multiplier
        
        # Normalize scores
        total_sentiment = raw_positive + raw_negative
        if total_sentiment > 0:
            positive_score = raw_positive / total_sentiment
            negative_score = raw_negative / total_sentiment
        else:
            positive_score = 0.0
            negative_score = 0.0
            
        neutral_score = max(0.0, 1.0 - positive_score - negative_score)
        
        # Calculate overall score (-1 to 1)
        overall_score = positive_score - negative_score
        
        # Calculate confidence based on strength of sentiment
        confidence = min(1.0, total_sentiment * 2)
        
        return SentimentScore(
            overall_score=overall_score,
            confidence=confidence,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            emotion_scores=emotion_scores,
            subjectivity=subjectivity
        )
    
    def _apply_negation(self, words: List[str]) -> Dict[str, int]:
        """Apply negation and intensifier handling"""
        negation_count = 0
        intensifier_count = 0
        
        for word in words:
            if word in self.negation_words:
                negation_count += 1
            elif word in self.intensifiers:
                intensifier_count += 1
        
        return {
            'negated_words': negation_count,
            'intensifiers': intensifier_count
        }
    
    def _calculate_emotion_scores(self, words: List[str]) -> Dict[str, float]:
        """Calculate emotion scores for different emotions"""
        emotions = ['joy', 'anger', 'fear', 'sadness', 'surprise', 'disgust']
        emotion_counts = {emotion: 0 for emotion in emotions}
        
        for word in words:
            for emotion in emotions:
                if word in self.emotion_lexicon.get(emotion, []):
                    emotion_counts[emotion] += 1
        
        # Normalize scores
        total_emotion_words = sum(emotion_counts.values())
        if total_emotion_words > 0:
            normalized_scores = {emotion: count / total_emotion_words 
                               for emotion, count in emotion_counts.items()}
        else:
            normalized_scores = {emotion: 0.0 for emotion in emotions}
            
        return normalized_scores
    
    def _calculate_subjectivity(self, words: List[str]) -> float:
        """Calculate subjectivity score (0.0 to 1.0)"""
        subjective_words = sum(1 for word in words if word in self.positive_words or word in self.negative_words)
        total_words = len(words) if words else 1
        
        return min(1.0, subjective_words / total_words)
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple key phrase extraction based on word frequency and sentiment
        words = text.split()
        if not words:
            return []
        
        # Count word frequency
        word_freq = Counter(words)
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        filtered_words = [(word, freq) for word, freq in word_freq.items() 
                         if word not in stop_words and len(word) > 2]
        
        # Sort by frequency and sentiment relevance
        filtered_words.sort(key=lambda x: x[1], reverse=True)
        
        # Return top phrases
        return [word for word, freq in filtered_words[:10]]
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identify topics in the text"""
        identified_topics = []
        
        for topic, keywords in self.topic_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in text)
            if match_count > 0:
                identified_topics.append(topic)
        
        return identified_topics
    
    def _generate_improvement_suggestions(self, sentiment: SentimentScore, 
                                        topics: List[str], 
                                        key_phrases: List[str]) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        # Sentiment-based suggestions
        if sentiment.overall_score < -0.3:
            suggestions.append("Consider addressing negative feedback directly")
            suggestions.append("Improve content quality to reduce negative sentiment")
        elif sentiment.overall_score > 0.3:
            suggestions.append("Leverage positive feedback for marketing")
            suggestions.append("Maintain current content approach")
        else:
            suggestions.append("Focus on creating more engaging content")
        
        # Topic-based suggestions
        if 'technical' in topics:
            suggestions.append("Consider adding more technical tutorials")
        if 'engagement' in topics:
            suggestions.append("Increase interactive elements in content")
        
        # Emotion-based suggestions
        if sentiment.emotion_scores.get('anger', 0) > 0.3:
            suggestions.append("Address user frustrations more proactively")
        if sentiment.emotion_scores.get('surprise', 0) > 0.3:
            suggestions.append("Continue creating unexpected and valuable content")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _calculate_engagement_indicators(self, text: str, sentiment: SentimentScore) -> Dict[str, float]:
        """Calculate engagement indicators"""
        indicators = {}
        
        # Length indicator (engagement often correlates with comment length)
        length_score = min(1.0, len(text.split()) / 20)  # Normalize to 0-1
        indicators['length_score'] = length_score
        
        # Question indicator
        question_score = 1.0 if '?' in text else 0.0
        indicators['question_score'] = question_score
        
        # Exclamation indicator
        exclamation_score = min(1.0, text.count('!') / 3)
        indicators['exclamation_score'] = exclamation_score
        
        # Emotional intensity
        emotional_intensity = max(sentiment.emotion_scores.values())
        indicators['emotional_intensity'] = emotional_intensity
        
        # Overall engagement potential
        engagement_potential = (length_score + question_score + exclamation_score + emotional_intensity) / 4
        indicators['engagement_potential'] = engagement_potential
        
        return indicators
    
    def _extract_language_features(self, text: str) -> Dict[str, Any]:
        """Extract language features for analysis"""
        words = text.split()
        
        return {
            'word_count': len(words),
            'character_count': len(text),
            'sentence_count': len(re.findall(r'[.!?]+', text)),
            'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
            'caps_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'has_url': bool(re.search(r'http\S+|www', text)),
            'has_hashtag': bool(re.search(r'#\w+', text)),
            'has_mention': bool(re.search(r'@\w+', text))
        }
    
    def _load_positive_lexicon(self) -> set:
        """Load positive sentiment words"""
        return {
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful',
            'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'delighted',
            'perfect', 'brilliant', 'outstanding', 'superb', 'magnificent', 'marvelous',
            'helpful', 'useful', 'valuable', 'informative', 'insightful', 'educational',
            'inspiring', 'motivating', 'encouraging', 'positive', 'optimistic', 'uplifting',
            'best', 'better', 'improved', 'enhanced', 'optimized', 'efficient',
            'clear', 'easy', 'simple', 'understandable', 'accessible', 'user-friendly',
            'innovative', 'creative', 'original', 'unique', 'fresh', 'new',
            'powerful', 'effective', 'efficient', 'fast', 'quick', 'smooth',
            'beautiful', 'attractive', 'appealing', 'stunning', 'gorgeous',
            'nice', 'cool', 'neat', 'impressive', 'remarkable', 'exceptional'
        }
    
    def _load_negative_lexicon(self) -> set:
        """Load negative sentiment words"""
        return {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike',
            'ugly', 'ugliest', 'worst', 'worse', 'poor', 'disappointing', 'frustrating',
            'annoying', 'irritating', 'confusing', 'complicated', 'difficult', 'hard',
            'slow', 'laggy', 'crash', 'broken', 'damaged', 'faulty', 'defective',
            'stupid', 'dumb', 'idiotic', 'silly', 'ridiculous', 'absurd',
            'boring', 'useless', 'worthless', 'pointless', 'meaningless',
            'annoyed', 'angry', 'mad', 'furious', 'upset', 'disappointed',
            'problem', 'issue', 'bug', 'error', 'mistake', 'flaw', 'defect',
            'fail', 'failure', 'failed', 'doesnt', 'don\'t', 'cannot', 'can\'t',
            'unnecessary', 'redundant', 'pointless', 'useless', 'worthless'
        }
    
    def _load_emotion_lexicon(self) -> Dict[str, set]:
        """Load emotion-specific words"""
        return {
            'joy': {'happy', 'joy', 'excited', 'cheerful', 'delighted', 'thrilled', 'glad'},
            'anger': {'angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed', 'frustrated'},
            'fear': {'scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified', 'panic'},
            'sadness': {'sad', 'depressed', 'unhappy', 'disappointed', 'heartbroken', 'melancholy'},
            'surprise': {'surprised', 'shocked', 'amazed', 'astonished', 'unexpected', 'wow'},
            'disgust': {'disgusted', 'revolted', 'sickened', 'repulsed', 'nauseated'}
        }
    
    def _load_intensifiers(self) -> set:
        """Load intensifying words"""
        return {
            'very', 'extremely', 'incredibly', 'absolutely', 'totally', 'completely',
            'really', 'truly', 'definitely', 'certainly', 'undoubtedly', 'obviously',
            'clearly', 'definitely', 'highly', 'remarkably', 'exceptionally', 'tremendously',
            'awfully', 'terribly', 'horribly', 'fantastically', 'wonderfully', 'perfectly'
        }
    
    def _load_negation_words(self) -> set:
        """Load negation words"""
        return {
            'not', 'no', 'never', 'nothing', 'nobody', 'nowhere', 'neither',
            'nor', 'none', 'hardly', 'scarcely', 'barely', 'rarely',
            'don\'t', 'doesn\'t', 'didn\'t', 'won\'t', 'wouldn\'t', 'couldn\'t',
            'shouldn\'t', 'haven\'t', 'hasn\'t', 'hadn\'t', 'isn\'t', 'aren\'t',
            'wasn\'t', 'weren\'t', 'cannot', 'can\'t', 'mustn\'t'
        }
    
    def _load_topic_keywords(self) -> Dict[str, List[str]]:
        """Load topic identification keywords"""
        return {
            'technical': ['tutorial', 'how', 'guide', 'setup', 'install', 'configuration', 'debug', 'error', 'problem'],
            'engagement': ['interactive', 'engaging', 'boring', 'entertaining', 'fun', 'interesting', 'captivating'],
            'content_quality': ['quality', 'resolution', 'clear', 'audio', 'video', 'production', 'editing'],
            'educational': ['learn', 'teach', 'understand', 'explanation', 'concept', 'knowledge', 'information'],
            'entertainment': ['fun', 'entertaining', 'funny', 'comedy', 'humor', 'enjoy', 'amazing'],
            'productivity': ['efficient', 'productivity', 'time', 'save', 'optimize', 'workflow', 'automation'],
            'ui_ux': ['interface', 'design', 'user', 'experience', 'easy', 'intuitive', 'navigation'],
            'performance': ['speed', 'fast', 'slow', 'performance', 'lag', 'optimization', 'loading']
        }