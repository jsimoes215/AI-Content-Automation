"""
Automated Content Optimization System

This module provides automatic content optimization based on feedback patterns
and successful content analysis. It continuously learns and improves content quality.
"""

from .pattern_analyzer import PatternAnalyzer
from .feedback_processor import FeedbackProcessor
from .optimizer_engine import OptimizerEngine
from .learning_system import LearningSystem
from .config_manager import ConfigManager
from .auto_optimizer import AutoOptimizer
from .integration import AutoOptimizerIntegration
from .api_wrapper import AutoOptimizerAPI, create_auto_optimizer, quick_optimize

__all__ = [
    'PatternAnalyzer',
    'FeedbackProcessor', 
    'OptimizerEngine',
    'LearningSystem',
    'ConfigManager',
    'AutoOptimizer',
    'AutoOptimizerIntegration',
    'AutoOptimizerAPI',
    'create_auto_optimizer',
    'quick_optimize'
]