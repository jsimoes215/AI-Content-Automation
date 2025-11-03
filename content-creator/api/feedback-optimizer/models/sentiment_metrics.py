"""
Data model for sentiment analysis metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SentimentMetrics:
    """
    Comprehensive sentiment analysis results and metrics.
    """
    # Overall sentiment
    overall_sentiment: Dict[str, Any] = field(default_factory=dict)  # {'label': 'positive/negative/neutral', 'score': float}
    
    # Detailed emotion breakdown
    emotion_breakdown: Dict[str, float] = field(default_factory=dict)  # {'joy': 0.3, 'anger': 0.1, 'fear': 0.2, 'sadness': 0.4}
    
    # Analysis confidence and quality
    confidence_score: float = 0.0
    subjectivity: float = 0.0
    polarity_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Text analysis
    sentiment_keywords: List[str] = field(default_factory=list)
    opinion_words: List[str] = field(default_factory=list)
    intensity_modifiers: List[str] = field(default_factory=list)
    
    # Contextual analysis
    context_sentiment: Dict[str, Any] = field(default_factory=dict)
    topic_sentiment: Dict[str, float] = field(default_factory=dict)
    
    # Temporal sentiment (if applicable)
    sentiment_timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    # Supporting data
    word_count: int = 0
    sentence_count: int = 0
    language: str = 'en'
    analysis_method: str = 'hybrid'  # 'rule-based', 'ml-based', 'hybrid'
    
    def __post_init__(self):
        """Validate and set defaults after initialization."""
        if not self.overall_sentiment:
            self.overall_sentiment = {'label': 'neutral', 'score': 0.0}
        
        # Ensure required fields have defaults
        if not self.emotion_breakdown:
            self.emotion_breakdown = {
                'joy': 0.0,
                'anger': 0.0,
                'fear': 0.0,
                'sadness': 0.0,
                'surprise': 0.0,
                'disgust': 0.0
            }
        
        if not self.polarity_distribution:
            self.polarity_distribution = {
                'positive': 0.33,
                'neutral': 0.34,
                'negative': 0.33
            }
    
    def get_sentiment_score(self) -> float:
        """Get the overall sentiment score."""
        return self.overall_sentiment.get('score', 0.0)
    
    def get_sentiment_label(self) -> str:
        """Get the overall sentiment label."""
        return self.overall_sentiment.get('label', 'neutral')
    
    def is_positive(self) -> bool:
        """Check if sentiment is positive."""
        return self.get_sentiment_label() == 'positive' and self.get_sentiment_score() > 0.1
    
    def is_negative(self) -> bool:
        """Check if sentiment is negative."""
        return self.get_sentiment_label() == 'negative' and self.get_sentiment_score() < -0.1
    
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return self.get_sentiment_label() == 'neutral' or abs(self.get_sentiment_score()) <= 0.1
    
    def get_dominant_emotion(self) -> str:
        """Get the dominant emotion from breakdown."""
        if not self.emotion_breakdown:
            return 'neutral'
        
        return max(self.emotion_breakdown.items(), key=lambda x: x[1])[0]
    
    def get_emotion_intensity(self) -> float:
        """Get overall emotion intensity (how emotionally charged)."""
        if not self.emotion_breakdown:
            return 0.0
        
        return max(self.emotion_breakdown.values())
    
    def get_confidence_level(self) -> str:
        """Get confidence level as string."""
        score = self.confidence_score
        
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'very_low'
    
    def get_subjectivity_level(self) -> str:
        """Get subjectivity level as string."""
        score = self.subjectivity
        
        if score >= 0.7:
            return 'highly_subjective'
        elif score >= 0.5:
            return 'subjective'
        elif score >= 0.3:
            return 'balanced'
        else:
            return 'objective'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'overall_sentiment': self.overall_sentiment,
            'emotion_breakdown': self.emotion_breakdown,
            'confidence_score': self.confidence_score,
            'subjectivity': self.subjectivity,
            'polarity_distribution': self.polarity_distribution,
            'sentiment_keywords': self.sentiment_keywords,
            'opinion_words': self.opinion_words,
            'intensity_modifiers': self.intensity_modifiers,
            'context_sentiment': self.context_sentiment,
            'topic_sentiment': self.topic_sentiment,
            'sentiment_timeline': self.sentiment_timeline,
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'language': self.language,
            'analysis_method': self.analysis_method
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentMetrics':
        """Create SentimentMetrics from dictionary."""
        return cls(**data)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the sentiment analysis."""
        return {
            'sentiment': {
                'label': self.get_sentiment_label(),
                'score': self.get_sentiment_score(),
                'confidence': self.get_confidence_level()
            },
            'emotions': {
                'dominant': self.get_dominant_emotion(),
                'intensity': self.get_emotion_intensity(),
                'breakdown': self.emotion_breakdown
            },
            'subjectivity': {
                'score': self.subjectivity,
                'level': self.get_subjectivity_level()
            },
            'content_metrics': {
                'word_count': self.word_count,
                'sentence_count': self.sentence_count,
                'keywords_count': len(self.sentiment_keywords)
            }
        }