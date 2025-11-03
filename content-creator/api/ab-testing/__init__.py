"""
A/B Testing System for Content Variations

This module provides comprehensive A/B testing capabilities for content variations
including titles, thumbnails, scripts, and posting times.

Features:
- Content variation management
- Performance tracking and analytics
- Statistical significance testing
- Automatic winner selection
- Multi-platform support
"""

from .content_variations import ContentVariationManager
from .performance_tracker import PerformanceTracker
from .statistical_tests import StatisticalAnalyzer
from .winner_selector import WinnerSelector
from .ab_test_manager import ABTestManager

__version__ = "1.0.0"
__all__ = [
    "ContentVariationManager",
    "PerformanceTracker", 
    "StatisticalAnalyzer",
    "WinnerSelector",
    "ABTestManager"
]