"""
Comment Analysis Utilities.

This module provides utilities for analyzing scraped comments including
sentiment analysis, topic extraction, and content quality assessment.
"""

import re
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from collections import Counter
import logging

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available. Install with: pip install nltk")

from ..models.comment_models import CommentBase, CommentWithAnalysis, SentimentLabel

logger = logging.getLogger(__name__)


class CommentAnalyzer:
    """Analyzes comments for sentiment, topics, and quality metrics."""
    
    def __init__(self):
        """Initialize the comment analyzer."""
        self.sia = None
        self.lemmatizer = None
        self.stop_words = None
        
        if NLTK_AVAILABLE:
            self._initialize_nltk()
    
    def _initialize_nltk(self) -> None:
        """Initialize NLTK components."""
        try:
            # Download required NLTK data
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            # Initialize components
            self.sia = SentimentIntensityAnalyzer()
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
            
            logger.info("NLTK components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLTK: {e}")
            NLTK_AVAILABLE = False
    
    async def analyze_comment(self, comment: CommentBase) -> CommentWithAnalysis:
        """
        Analyze a single comment and return enhanced version.
        
        Args:
            comment: Base comment to analyze
            
        Returns:
            Enhanced comment with analysis results
        """
        try:
            # Perform sentiment analysis
            sentiment_result = await self.analyze_sentiment(comment.text)
            
            # Extract topics and keywords
            topics = await self.extract_topics(comment.text)
            
            # Detect intent
            intent = await self.detect_intent(comment.text)
            
            # Calculate quality score
            quality_score = await self.calculate_quality_score(comment)
            
            # Predict engagement potential
            engagement_potential = await self.predict_engagement_potential(comment, sentiment_result)
            
            # Create enhanced comment
            enhanced_comment = CommentWithAnalysis(
                **comment.dict(),
                sentiment_score=sentiment_result['score'],
                sentiment_label=sentiment_result['label'],
                sentiment_confidence=sentiment_result['confidence'],
                topics=topics,
                topic_scores=await self.calculate_topic_scores(comment.text, topics),
                intent=intent['intent'],
                intent_confidence=intent['confidence'],
                quality_score=quality_score,
                engagement_potential=engagement_potential,
                processed_at=datetime.utcnow()
            )
            
            return enhanced_comment
            
        except Exception as e:
            logger.error(f"Error analyzing comment {comment.comment_id}: {e}")
            # Return comment with minimal analysis on error
            return CommentWithAnalysis(
                **comment.dict(),
                sentiment_score=0.0,
                sentiment_label=SentimentLabel.NEUTRAL,
                sentiment_confidence=0.0,
                processed_at=datetime.utcnow()
            )
    
    async def analyze_batch(self, comments: List[CommentBase]) -> List[CommentWithAnalysis]:
        """
        Analyze a batch of comments concurrently.
        
        Args:
            comments: List of comments to analyze
            
        Returns:
            List of enhanced comments
        """
        tasks = [self.analyze_comment(comment) for comment in comments]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        analyzed_comments = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch analysis error: {result}")
            else:
                analyzed_comments.append(result)
        
        return analyzed_comments
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            if not text or not text.strip():
                return {
                    'score': 0.0,
                    'label': SentimentLabel.NEUTRAL,
                    'confidence': 0.0
                }
            
            if NLTK_AVAILABLE and self.sia:
                # Use VADER sentiment analyzer
                scores = self.sia.polarity_scores(text)
                compound_score = scores['compound']
                
                # Determine label
                if compound_score >= 0.05:
                    label = SentimentLabel.POSITIVE
                elif compound_score <= -0.05:
                    label = SentimentLabel.NEGATIVE
                else:
                    label = SentimentLabel.NEUTRAL
                
                # Calculate confidence based on absolute compound score
                confidence = min(abs(compound_score), 1.0)
                
                return {
                    'score': compound_score,
                    'label': label,
                    'confidence': confidence
                }
            else:
                # Fallback: simple keyword-based sentiment
                return await self._simple_sentiment_analysis(text)
                
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'score': 0.0,
                'label': SentimentLabel.NEUTRAL,
                'confidence': 0.0
            }
    
    async def _simple_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based sentiment analysis fallback."""
        positive_words = ['good', 'great', 'awesome', 'love', 'like', 'amazing', 'excellent', 'fantastic']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'horrible', 'disgusting', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            score = min(positive_count / 10, 1.0)
            label = SentimentLabel.POSITIVE
        elif negative_count > positive_count:
            score = -min(negative_count / 10, 1.0)
            label = SentimentLabel.NEGATIVE
        else:
            score = 0.0
            label = SentimentLabel.NEUTRAL
        
        confidence = abs(score)
        
        return {
            'score': score,
            'label': label,
            'confidence': confidence
        }
    
    async def extract_topics(self, text: str, max_topics: int = 5) -> List[str]:
        """
        Extract main topics/keywords from text.
        
        Args:
            text: Text to analyze
            max_topics: Maximum number of topics to return
            
        Returns:
            List of extracted topics
        """
        try:
            if not text or not text.strip():
                return []
            
            if NLTK_AVAILABLE:
                # Tokenize and clean text
                tokens = word_tokenize(text.lower())
                
                # Remove punctuation and stop words
                tokens = [
                    token for token in tokens 
                    if token.isalpha() and token not in self.stop_words and len(token) > 2
                ]
                
                # Lemmatize tokens
                lemmatized = [self.lemmatizer.lemmatize(token) for token in tokens]
                
                # Count frequency and get top topics
                counter = Counter(lemmatized)
                topics = [word for word, count in counter.most_common(max_topics)]
                
                return topics
            else:
                # Fallback: simple keyword extraction
                return await self._simple_keyword_extraction(text, max_topics)
                
        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return []
    
    async def _simple_keyword_extraction(self, text: str, max_topics: int) -> List[str]:
        """Simple keyword extraction fallback."""
        # Remove common words and punctuation
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Simple frequency analysis
        from collections import Counter
        counter = Counter(words)
        
        # Get most common words (simple topics)
        topics = [word for word, count in counter.most_common(max_topics)]
        return topics
    
    async def calculate_topic_scores(self, text: str, topics: List[str]) -> Dict[str, float]:
        """Calculate confidence scores for extracted topics."""
        if not topics:
            return {}
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic in topics:
            # Simple frequency-based scoring
            topic_count = text_lower.count(topic.lower())
            max_possible = len(text.split())
            score = min(topic_count / max_possible * 10, 1.0)
            topic_scores[topic] = score
        
        return topic_scores
    
    async def detect_intent(self, text: str) -> Dict[str, Any]:
        """
        Detect user intent from comment text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with intent detection results
        """
        try:
            text_lower = text.lower()
            
            # Define intent patterns
            intent_patterns = {
                'question': ['?', 'what', 'how', 'why', 'when', 'where', 'who', 'which'],
                'complaint': ['hate', 'terrible', 'awful', 'worst', 'horrible', 'disappointing'],
                'praise': ['love', 'great', 'awesome', 'amazing', 'excellent', 'fantastic'],
                'request': ['please', 'could', 'would', 'can you', 'please make'],
                'suggestion': ['should', 'could', 'maybe', 'suggest', 'recommend'],
                'feedback': ['suggest', 'recommend', 'think', 'feel', 'opinion']
            }
            
            # Score each intent
            intent_scores = {}
            for intent, patterns in intent_patterns.items():
                score = sum(1 for pattern in patterns if pattern in text_lower)
                intent_scores[intent] = score
            
            # Get highest scoring intent
            if intent_scores and max(intent_scores.values()) > 0:
                detected_intent = max(intent_scores, key=intent_scores.get)
                confidence = min(intent_scores[detected_intent] / len(text.split()) * 2, 1.0)
            else:
                detected_intent = 'comment'
                confidence = 0.1
            
            return {
                'intent': detected_intent,
                'confidence': confidence,
                'scores': intent_scores
            }
            
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'scores': {}
            }
    
    async def calculate_quality_score(self, comment: CommentBase) -> float:
        """
        Calculate comment quality score based on various factors.
        
        Args:
            comment: Comment to score
            
        Returns:
            Quality score between 0 and 1
        """
        try:
            score = 0.0
            
            # Length factor (too short or too long is lower quality)
            text_length = len(comment.text.split())
            if 5 <= text_length <= 50:
                score += 0.3
            elif text_length < 5:
                score += 0.1
            else:
                score += 0.2
            
            # Engagement factor
            if comment.like_count > 0:
                score += min(comment.like_count / 10, 0.3)  # Max 0.3 for likes
            
            # User verification factor
            if comment.user_verified:
                score += 0.1
            
            # Reply presence factor
            if comment.reply_count > 0:
                score += min(comment.reply_count / 5, 0.2)  # Max 0.2 for replies
            
            # Text quality factors
            text = comment.text.lower()
            
            # Exclamation marks (can indicate engagement)
            if '!' in comment.text:
                score += 0.05
            
            # Question marks (can indicate engagement)
            if '?' in comment.text:
                score += 0.05
            
            # Contains URL (often lower quality)
            if 'http' in text or 'www.' in text:
                score -= 0.1
            
            # Contains repeated characters (spam indicator)
            if re.search(r'(.)\1{3,}', text):
                score -= 0.2
            
            # Language quality (basic check)
            unique_words = len(set(text.split()))
            if unique_words > text_length * 0.7:  # Good vocabulary diversity
                score += 0.1
            
            # Ensure score is within bounds
            return max(0.0, min(score, 1.0))
            
        except Exception as e:
            logger.error(f"Quality score calculation error: {e}")
            return 0.0
    
    async def predict_engagement_potential(self, comment: CommentBase, sentiment_result: Dict[str, Any]) -> float:
        """
        Predict potential for this comment to generate engagement.
        
        Args:
            comment: Comment to analyze
            sentiment_result: Sentiment analysis results
            
        Returns:
            Engagement potential score between 0 and 1
        """
        try:
            score = 0.0
            
            # Sentiment factor
            sentiment_score = sentiment_result.get('score', 0)
            if abs(sentiment_score) > 0.5:  # Strong sentiment
                score += 0.3
            
            # Content characteristics
            text = comment.text.lower()
            
            # Questions tend to generate engagement
            if '?' in comment.text:
                score += 0.2
            
            # Emotional words
            emotional_words = ['love', 'hate', 'amazing', 'terrible', 'awesome', 'worst']
            emotional_count = sum(1 for word in emotional_words if word in text)
            score += min(emotional_count * 0.1, 0.2)
            
            # Length factor (medium length tends to get more engagement)
            word_count = len(comment.text.split())
            if 10 <= word_count <= 30:
                score += 0.2
            elif word_count > 50:
                score -= 0.1  # Very long comments often ignored
            
            # Call to action words
            cta_words = ['check', 'watch', 'subscribe', 'like', 'share', 'comment']
            cta_count = sum(1 for word in cta_words if word in text)
            score += min(cta_count * 0.1, 0.2)
            
            # User factors
            if comment.user_verified:
                score += 0.1
            
            # Initial engagement (comments with likes are more likely to get more)
            if comment.like_count > 5:
                score += 0.1
            
            return max(0.0, min(score, 1.0))
            
        except Exception as e:
            logger.error(f"Engagement prediction error: {e}")
            return 0.0
    
    async def analyze_comment_trends(self, comments: List[CommentWithAnalysis]) -> Dict[str, Any]:
        """
        Analyze trends across a collection of comments.
        
        Args:
            comments: List of analyzed comments
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            if not comments:
                return {}
            
            # Sentiment distribution
            sentiment_counts = Counter(comment.sentiment_label for comment in comments if comment.sentiment_label)
            
            # Topic frequency
            all_topics = []
            for comment in comments:
                all_topics.extend(comment.topics)
            topic_counts = Counter(all_topics)
            
            # Intent distribution
            intent_counts = Counter(comment.intent for comment in comments if comment.intent)
            
            # Quality metrics
            quality_scores = [comment.quality_score for comment in comments if comment.quality_score is not None]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Engagement potential
            engagement_scores = [comment.engagement_potential for comment in comments if comment.engagement_potential is not None]
            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
            
            return {
                'total_comments': len(comments),
                'sentiment_distribution': dict(sentiment_counts),
                'top_topics': dict(topic_counts.most_common(10)),
                'intent_distribution': dict(intent_counts),
                'average_quality_score': avg_quality,
                'average_engagement_potential': avg_engagement,
                'high_quality_comments': len([c for c in comments if (c.quality_score or 0) > 0.7]),
                'high_engagement_potential': len([c for c in comments if (c.engagement_potential or 0) > 0.7])
            }
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return {}


# Global analyzer instance
comment_analyzer = CommentAnalyzer()