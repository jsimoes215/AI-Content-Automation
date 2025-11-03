"""
Feedback-Driven Content Improvement Optimizer

A comprehensive system for analyzing feedback patterns and generating
AI-powered improvement recommendations for content creation.
"""

from .analyzer import FeedbackAnalyzer
from .recommender import ContentImprovementRecommender
from .processor import SentimentProcessor
from .engine import LearningEngine

__version__ = "1.0.0"
__all__ = [
    "FeedbackAnalyzer",
    "ContentImprovementRecommender", 
    "SentimentProcessor",
    "LearningEngine"
]