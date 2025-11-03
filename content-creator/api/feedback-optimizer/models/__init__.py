"""
Data models for the feedback optimizer system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

@dataclass
class SentimentMetrics:
    """Metrics for sentiment analysis results."""
    overall_sentiment: Dict[str, Any]  # {'label': 'positive/negative/neutral', 'score': float}
    emotion_breakdown: Dict[str, float]  # {'joy': 0.3, 'anger': 0.1, ...}
    confidence_score: float
    sentiment_keywords: List[str]
    subjectivity: float
    polarity_distribution: Dict[str, float]
    
@dataclass
class FeedbackData:
    """Individual feedback data point."""
    content_id: str
    feedback_type: str  # 'comment', 'like', 'share', etc.
    text: str
    sentiment: SentimentMetrics
    engagement_metrics: Dict[str, Any]  # {'views': 100, 'likes': 10, ...}
    metadata: Dict[str, Any]
    patterns: List[Dict[str, Any]]
    timestamp: datetime
    content_type: Optional[str] = None  # 'script', 'thumbnail', 'title', etc.
    user_id: Optional[str] = None
    platform: Optional[str] = None