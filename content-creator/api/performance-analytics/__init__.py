"""
Performance Analytics API Module

This module provides comprehensive analytics capabilities for tracking,
analyzing, and reporting on content performance across multiple platforms.

Features:
- Real-time engagement metrics tracking
- Correlation analysis between content features and performance
- Trend identification and prediction
- A/B testing analysis
- Content optimization recommendations
"""

from .engagement_tracker import EngagementTracker
from .correlation_analyzer import CorrelationAnalyzer
from .trend_analyzer import TrendAnalyzer
from .analytics_dashboard import AnalyticsDashboard

__all__ = [
    'EngagementTracker',
    'CorrelationAnalyzer', 
    'TrendAnalyzer',
    'AnalyticsDashboard'
]

__version__ = "1.0.0"