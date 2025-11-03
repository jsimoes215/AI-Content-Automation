"""
Data model for feedback data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class FeedbackData:
    """
    Comprehensive feedback data model containing all feedback information.
    """
    # Core identification
    content_id: str
    feedback_type: str  # 'comment', 'like', 'share', 'view', etc.
    text: str
    
    # Analysis results
    sentiment: 'SentimentMetrics'
    engagement_metrics: Dict[str, Any] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    content_type: Optional[str] = None  # 'script', 'thumbnail', 'title', etc.
    user_id: Optional[str] = None
    platform: Optional[str] = None
    
    # Additional analysis
    quality_indicators: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate required fields after initialization."""
        if not self.content_id:
            raise ValueError("content_id is required")
        if not self.feedback_type:
            raise ValueError("feedback_type is required")
        if not self.text and self.feedback_type == 'comment':
            raise ValueError("text is required for comment feedback_type")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'content_id': self.content_id,
            'feedback_type': self.feedback_type,
            'text': self.text,
            'sentiment': self.sentiment.__dict__ if hasattr(self.sentiment, '__dict__') else self.sentiment,
            'engagement_metrics': self.engagement_metrics,
            'patterns': self.patterns,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'content_type': self.content_type,
            'user_id': self.user_id,
            'platform': self.platform,
            'quality_indicators': self.quality_indicators,
            'improvement_areas': self.improvement_areas
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackData':
        """Create FeedbackData from dictionary."""
        # Convert timestamp back to datetime if needed
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate from metrics."""
        views = self.engagement_metrics.get('views', 0)
        if views == 0:
            return 0.0
        
        total_engagement = (
            self.engagement_metrics.get('likes', 0) +
            self.engagement_metrics.get('comments', 0) +
            self.engagement_metrics.get('shares', 0) +
            self.engagement_metrics.get('saves', 0)
        )
        
        return min(1.0, total_engagement / views)
    
    def get_sentiment_score(self) -> float:
        """Get overall sentiment score."""
        if hasattr(self.sentiment, 'overall_sentiment'):
            return self.sentiment.overall_sentiment.get('score', 0.0)
        elif isinstance(self.sentiment, dict):
            return self.sentiment.get('score', 0.0)
        return 0.0
    
    def get_sentiment_label(self) -> str:
        """Get overall sentiment label."""
        if hasattr(self.sentiment, 'overall_sentiment'):
            return self.sentiment.overall_sentiment.get('label', 'neutral')
        elif isinstance(self.sentiment, dict):
            return self.sentiment.get('label', 'neutral')
        return 'neutral'