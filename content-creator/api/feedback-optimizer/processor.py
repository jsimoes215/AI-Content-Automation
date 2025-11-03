"""
Sentiment Processing Module

Processes and normalizes sentiment data for consistent analysis across different sources.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from .models.sentiment_metrics import SentimentMetrics
from .utils.sentiment_analyzer import SentimentAnalyzer


class SentimentProcessor:
    """
    Processes and normalizes sentiment data from various sources.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the sentiment processor."""
        self.config = config or self._default_config()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.normalization_factors = self._initialize_normalization_factors()
        
    def _default_config(self) -> Dict:
        """Default configuration for sentiment processing."""
        return {
            'sentiment_scale': {
                'min': -1.0,
                'max': 1.0,
                'neutral_range': 0.1
            },
            'platform_adjustments': {
                'youtube': 0.05,
                'twitter': -0.02,
                'facebook': 0.02,
                'instagram': 0.03
            },
            'normalization_enabled': True,
            'cross_platform_calibration': True
        }
    
    def _initialize_normalization_factors(self) -> Dict[str, float]:
        """Initialize platform-specific normalization factors."""
        return {
            'youtube_comments': 1.0,
            'twitter_tweets': 0.8,
            'facebook_posts': 0.9,
            'instagram_captions': 0.85,
            'linkedin_posts': 0.95,
            'reddit_comments': 1.1
        }
    
    def process_sentiment_batch(self, feedback_items: List[Dict[str, Any]]) -> List[SentimentMetrics]:
        """
        Process a batch of feedback items for sentiment analysis.
        
        Args:
            feedback_items: List of feedback items with text and metadata
            
        Returns:
            List of processed SentimentMetrics objects
        """
        processed_sentiments = []
        
        for item in feedback_items:
            # Extract text and metadata
            text = item.get('text', '')
            metadata = item.get('metadata', {})
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(text, metadata)
            
            # Normalize sentiment if needed
            if self.config['normalization_enabled']:
                sentiment = self._normalize_sentiment(sentiment, metadata)
            
            # Apply platform adjustments
            if self.config['cross_platform_calibration']:
                sentiment = self._apply_platform_adjustments(sentiment, metadata)
            
            processed_sentiments.append(sentiment)
        
        return processed_sentiments
    
    def normalize_sentiment_score(self, raw_score: float, source_type: str) -> float:
        """
        Normalize sentiment score based on source characteristics.
        
        Args:
            raw_score: Raw sentiment score
            source_type: Type of sentiment source
            
        Returns:
            Normalized sentiment score
        """
        # Get normalization factor
        normalization_factor = self.normalization_factors.get(source_type, 1.0)
        
        # Apply normalization
        normalized_score = raw_score * normalization_factor
        
        # Ensure score is within bounds
        min_score = self.config['sentiment_scale']['min']
        max_score = self.config['sentiment_scale']['max']
        
        return max(min_score, min(max_score, normalized_score))
    
    def aggregate_sentiment_metrics(self, sentiments: List[SentimentMetrics]) -> Dict[str, Any]:
        """
        Aggregate sentiment metrics from multiple items.
        
        Args:
            sentiments: List of SentimentMetrics objects
            
        Returns:
            Aggregated sentiment analysis
        """
        if not sentiments:
            return {'status': 'no_data'}
        
        # Calculate overall metrics
        overall_scores = [s.get_sentiment_score() for s in sentiments]
        avg_sentiment = sum(overall_scores) / len(overall_scores)
        
        # Determine overall sentiment
        if avg_sentiment > self.config['sentiment_scale']['neutral_range']:
            overall_label = 'positive'
        elif avg_sentiment < -self.config['sentiment_scale']['neutral_range']:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
        
        # Aggregate emotion breakdown
        emotion_sums = defaultdict(float)
        emotion_counts = defaultdict(int)
        
        for sentiment in sentiments:
            for emotion, score in sentiment.emotion_breakdown.items():
                emotion_sums[emotion] += score
                emotion_counts[emotion] += 1
        
        avg_emotions = {emotion: emotion_sums[emotion] / emotion_counts[emotion] 
                       for emotion in emotion_sums}
        
        # Calculate confidence metrics
        confidence_scores = [s.confidence_score for s in sentiments]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            'overall_sentiment': {
                'label': overall_label,
                'score': round(avg_sentiment, 3),
                'confidence': round(avg_confidence, 3)
            },
            'emotion_breakdown': avg_emotions,
            'data_quality': {
                'item_count': len(sentiments),
                'average_confidence': round(avg_confidence, 3),
                'sentiment_distribution': self._calculate_sentiment_distribution(overall_scores)
            },
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def _normalize_sentiment(self, sentiment: SentimentMetrics, metadata: Dict[str, Any]) -> SentimentMetrics:
        """Normalize sentiment based on metadata."""
        # Apply normalization to overall sentiment
        source_type = metadata.get('source_type', 'general')
        
        normalized_sentiment = sentiment.overall_sentiment.copy()
        normalized_sentiment['score'] = self.normalize_sentiment_score(
            normalized_sentiment['score'], source_type
        )
        
        # Update sentiment metrics
        sentiment.overall_sentiment = normalized_sentiment
        
        return sentiment
    
    def _apply_platform_adjustments(self, sentiment: SentimentMetrics, metadata: Dict[str, Any]) -> SentimentMetrics:
        """Apply platform-specific adjustments to sentiment."""
        platform = metadata.get('platform', '').lower()
        
        if platform in self.config['platform_adjustments']:
            adjustment = self.config['platform_adjustments'][platform]
            
            # Adjust overall sentiment score
            adjusted_score = sentiment.overall_sentiment['score'] + adjustment
            
            # Ensure score stays within bounds
            min_score = self.config['sentiment_scale']['min']
            max_score = self.config['sentiment_scale']['max']
            adjusted_score = max(min_score, min(max_score, adjusted_score))
            
            # Update sentiment
            sentiment.overall_sentiment['score'] = adjusted_score
            
            # Update label if necessary
            if adjusted_score > self.config['sentiment_scale']['neutral_range']:
                sentiment.overall_sentiment['label'] = 'positive'
            elif adjusted_score < -self.config['sentiment_scale']['neutral_range']:
                sentiment.overall_sentiment['label'] = 'negative'
            else:
                sentiment.overall_sentiment['label'] = 'neutral'
        
        return sentiment
    
    def _calculate_sentiment_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of sentiment labels."""
        positive_count = sum(1 for score in scores if score > self.config['sentiment_scale']['neutral_range'])
        negative_count = sum(1 for score in scores if score < -self.config['sentiment_scale']['neutral_range'])
        neutral_count = len(scores) - positive_count - negative_count
        
        return {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count
        }