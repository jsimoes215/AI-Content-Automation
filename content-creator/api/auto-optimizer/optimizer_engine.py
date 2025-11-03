"""
Optimizer Engine Module

Applies optimizations to content generation based on patterns and feedback analysis.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import re


class OptimizationType(Enum):
    """Types of optimizations that can be applied."""
    TITLE_OPTIMIZATION = "title_optimization"
    TAG_OPTIMIZATION = "tag_optimization"
    TIMING_OPTIMIZATION = "timing_optimization"
    CONTENT_LENGTH = "content_length"
    ENGAGEMENT_HOOK = "engagement_hook"
    CALL_TO_ACTION = "call_to_action"
    THUMBNAIL_OPTIMIZATION = "thumbnail_optimization"
    PLATFORM_SPECIFIC = "platform_specific"


@dataclass
class OptimizationRule:
    """Represents an optimization rule."""
    name: str
    optimization_type: OptimizationType
    condition: str  # When to apply this rule
    action: str  # What to do when condition is met
    weight: float  # Priority weight (0-1)
    success_rate: float  # How often this optimization succeeds
    applied_count: int = 0
    successful_count: int = 0


@dataclass
class OptimizationResult:
    """Result of applying an optimization."""
    original_content: Dict[str, Any]
    optimized_content: Dict[str, Any]
    applied_optimizations: List[str]
    confidence_score: float
    expected_improvement: float
    applied_at: datetime


class OptimizerEngine:
    """Core engine that applies optimizations to content generation."""
    
    def __init__(self, db_path: str = "data/content_creator.db"):
        self.db_path = db_path
        self.optimization_rules = self._load_optimization_rules()
        self.optimization_history = []
        
    def optimize_content(self, 
                        content_request: Dict[str, Any],
                        target_platform: Optional[str] = None,
                        optimization_level: str = "medium") -> OptimizationResult:
        """
        Optimize content based on learned patterns and rules.
        
        Args:
            content_request: Content to optimize
            target_platform: Target platform (youtube, instagram, tiktok, etc.)
            optimization_level: "light", "medium", "aggressive"
            
        Returns:
            OptimizationResult with optimized content and metadata
        """
        original_content = content_request.copy()
        applied_optimizations = []
        confidence_scores = []
        expected_improvements = []
        
        # Apply different optimization strategies
        if optimization_level in ["medium", "aggressive"]:
            # Title optimization
            title_opt = self._optimize_title(content_request, target_platform)
            if title_opt:
                content_request['title'] = title_opt['optimized_title']
                applied_optimizations.append(f"Title: {title_opt['improvement']}")
                confidence_scores.append(title_opt['confidence'])
                expected_improvements.append(title_opt['expected_improvement'])
        
        if optimization_level == "aggressive":
            # Tag optimization
            tag_opt = self._optimize_tags(content_request, target_platform)
            if tag_opt:
                content_request['tags'] = tag_opt['optimized_tags']
                applied_optimizations.append(f"Tags: Added {tag_opt['added_tags']}, Removed {tag_opt['removed_tags']}")
                confidence_scores.append(tag_opt['confidence'])
                expected_improvements.append(tag_opt['expected_improvement'])
            
            # Timing optimization
            timing_opt = self._optimize_timing(content_request, target_platform)
            if timing_opt:
                content_request['suggested_publish_time'] = timing_opt['optimal_time']
                applied_optimizations.append(f"Timing: {timing_opt['recommendation']}")
                confidence_scores.append(timing_opt['confidence'])
                expected_improvements.append(timing_opt['expected_improvement'])
            
            # Content length optimization
            length_opt = self._optimize_content_length(content_request, target_platform)
            if length_opt:
                content_request['suggested_length'] = length_opt['recommended_length']
                content_request['content_adjustments'] = length_opt['adjustments']
                applied_optimizations.append(f"Length: {length_opt['recommendation']}")
                confidence_scores.append(length_opt['confidence'])
                expected_improvements.append(length_opt['expected_improvement'])
        
        # Calculate overall confidence and improvement
        overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
        overall_improvement = statistics.mean(expected_improvements) if expected_improvements else 0.0
        
        result = OptimizationResult(
            original_content=original_content,
            optimized_content=content_request,
            applied_optimizations=applied_optimizations,
            confidence_score=overall_confidence,
            expected_improvement=overall_improvement,
            applied_at=datetime.now()
        )
        
        # Log optimization
        self._log_optimization(result, optimization_level, target_platform)
        
        return result
    
    def _optimize_title(self, content: Dict[str, Any], platform: Optional[str]) -> Optional[Dict[str, Any]]:
        """Optimize content title based on successful patterns."""
        title = content.get('title', '')
        
        # Get title patterns from pattern analyzer
        patterns = self._get_title_patterns()
        if not patterns:
            return None
        
        optimized_title = title
        improvements = []
        
        # Apply successful words
        top_words = patterns.get('top_performing_words', {})
        if top_words:
            title_words = title.lower().split()
            for word, stats in top_words.items():
                if stats.get('avg_performance', 0) > 0.7:
                    # Add high-performing words that aren't already in title
                    if word not in title.lower() and len(title_words) < 10:
                        title_words.insert(-1, word)  # Insert before last word
                        improvements.append(f"Added high-performing word: {word}")
        
        # Optimize length
        optimal_length = patterns.get('optimal_title_length', {}).get('average', 60)
        if len(title) < optimal_length * 0.8:
            # Title is too short, add compelling elements
            if '?' not in title:
                optimized_title += "?"
                improvements.append("Added question for engagement")
            
            # Add power words
            power_words = ['amazing', 'incredible', 'secret', 'ultimate', 'proven']
            existing_words = [w.lower() for w in title_words]
            for word in power_words:
                if word not in existing_words:
                    optimized_title = f"{word} {optimized_title}"
                    improvements.append(f"Added power word: {word}")
                    break
        
        elif len(title) > optimal_length * 1.2:
            # Title is too long, optimize for brevity
            optimized_title = title[:int(optimal_length)].rsplit(' ', 1)[0] + "..."
            improvements.append("Truncated for optimal length")
        
        # Platform-specific optimizations
        if platform:
            platform_opt = self._optimize_for_platform(optimized_title, platform)
            if platform_opt:
                optimized_title = platform_opt
                improvements.append(f"Optimized for {platform}")
        
        if improvements:
            confidence = min(0.8, len(improvements) * 0.2)
            expected_improvement = confidence * 0.15  # Up to 15% improvement
            
            return {
                'optimized_title': optimized_title,
                'improvement': '; '.join(improvements),
                'confidence': confidence,
                'expected_improvement': expected_improvement
            }
        
        return None
    
    def _optimize_tags(self, content: Dict[str, Any], platform: Optional[str]) -> Optional[Dict[str, Any]]:
        """Optimize content tags based on successful patterns."""
        current_tags = content.get('tags', [])
        
        # Get tag patterns
        patterns = self._get_tag_patterns()
        if not patterns:
            return None
        
        new_tags = current_tags.copy()
        added_tags = []
        removed_tags = []
        
        # Add high-performing tags
        top_tags = patterns.get('top_performing_tags', {})
        for tag, stats in top_tags.items():
            if (stats.get('avg_performance', 0) > 0.6 and 
                stats.get('usage_count', 0) >= 3 and
                tag not in new_tags and
                len(new_tags) < 10):
                new_tags.append(tag)
                added_tags.append(tag)
        
        # Remove low-performing tags
        for tag in current_tags[:]:
            if tag in top_tags:
                if top_tags[tag].get('avg_performance', 0) < 0.3:
                    new_tags.remove(tag)
                    removed_tags.append(tag)
        
        # Add trending tags based on analysis
        trending_tags = self._get_trending_tags()
        for tag in trending_tags[:5]:
            if tag not in new_tags and len(new_tags) < 10:
                new_tags.append(tag)
                added_tags.append(f"trending:{tag}")
        
        if added_tags or removed_tags:
            confidence = min(0.9, (len(added_tags) + len(removed_tags)) * 0.1)
            expected_improvement = confidence * 0.12
            
            return {
                'optimized_tags': new_tags,
                'added_tags': added_tags,
                'removed_tags': removed_tags,
                'confidence': confidence,
                'expected_improvement': expected_improvement
            }
        
        return None
    
    def _optimize_timing(self, content: Dict[str, Any], platform: Optional[str]) -> Optional[Dict[str, Any]]:
        """Optimize publishing timing based on engagement patterns."""
        patterns = self._get_timing_patterns()
        if not patterns:
            return None
        
        best_hours = patterns.get('best_hours', {})
        best_weekdays = patterns.get('best_weekdays', {})
        
        if not best_hours and not best_weekdays:
            return None
        
        # Calculate optimal time
        now = datetime.now()
        
        # Find next best hour
        optimal_hours = sorted(best_hours.items(), key=lambda x: x[1], reverse=True)
        if optimal_hours:
            best_hour = int(optimal_hours[0][0].split(':')[0])
            optimal_time = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
            
            # If time has passed today, schedule for tomorrow
            if optimal_time < now:
                optimal_time += timedelta(days=1)
            
            # Find best weekday
            if best_weekdays:
                best_weekday_name = max(best_weekdays, key=best_weekdays.get)
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                best_weekday = weekday_names.index(best_weekday_name)
                
                # Adjust to best weekday
                days_ahead = best_weekday - optimal_time.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                
                optimal_time += timedelta(days=days_ahead)
            
            recommendation = f"Schedule for {optimal_time.strftime('%A at %I:%M %p')}"
            confidence = min(0.85, len(best_hours) * 0.1 + len(best_weekdays) * 0.05)
            expected_improvement = confidence * 0.18
            
            return {
                'optimal_time': optimal_time.isoformat(),
                'recommendation': recommendation,
                'confidence': confidence,
                'expected_improvement': expected_improvement
            }
        
        return None
    
    def _optimize_content_length(self, content: Dict[str, Any], platform: Optional[str]) -> Optional[Dict[str, Any]]:
        """Optimize content length based on performance patterns."""
        patterns = self._get_length_patterns()
        if not patterns:
            return None
        
        # Determine optimal length based on content type and platform
        content_type = content.get('content_type', 'general')
        content_length = content.get('estimated_length', 300)  # Default estimate
        
        optimal_ranges = {
            'video': {'short': 60, 'medium': 180, 'long': 600},
            'text': {'short': 150, 'medium': 400, 'long': 800},
            'audio': {'short': 120, 'medium': 300, 'long': 900},
            'general': {'short': 200, 'medium': 500, 'long': 1000}
        }
        
        target_range = optimal_ranges.get(content_type, optimal_ranges['general'])
        
        # Find best performing length range
        best_range = 'medium'
        best_performance = 0
        
        for range_name, performance in patterns.items():
            if isinstance(performance, dict) and 'avg_performance' in performance:
                if performance['avg_performance'] > best_performance:
                    best_performance = performance['avg_performance']
                    best_range = range_name
        
        recommended_length = target_range[best_range]
        adjustments = []
        
        if content_length < recommended_length * 0.8:
            adjustments.append(f"Increase length from ~{content_length} to ~{recommended_length} characters")
            adjustments.append("Add more detailed explanations and examples")
            adjustments.append("Include additional supporting information")
        elif content_length > recommended_length * 1.2:
            adjustments.append(f"Reduce length from ~{content_length} to ~{recommended_length} characters")
            adjustments.append("Condense information while maintaining key points")
            adjustments.append("Remove redundant or less important details")
        else:
            adjustments.append("Current length is optimal for content type")
        
        confidence = min(0.8, best_performance if best_performance else 0.5)
        expected_improvement = confidence * 0.1
        
        return {
            'recommended_length': recommended_length,
            'adjustments': adjustments,
            'recommendation': f"Target {best_range} length ({recommended_length} characters)",
            'confidence': confidence,
            'expected_improvement': expected_improvement
        }
    
    def _optimize_for_platform(self, content: str, platform: str) -> Optional[str]:
        """Apply platform-specific optimizations."""
        optimizations = {
            'youtube': {
                'max_length': 100,
                'add_hooks': True,
                'trending_words': ['tutorial', 'how to', 'review', 'vs', 'best']
            },
            'instagram': {
                'max_length': 125,
                'add_hashtags': True,
                'engagement_words': ['love', 'amazing', 'incredible', 'life changing']
            },
            'tiktok': {
                'max_length': 100,
                'trendy_format': True,
                'trending_words': ['POV', 'Wait for it', 'Plot twist', 'No one talks about']
            }
        }
        
        platform_rules = optimizations.get(platform.lower())
        if not platform_rules:
            return content
        
        optimized = content
        
        # Truncate if too long
        if len(optimized) > platform_rules['max_length']:
            optimized = optimized[:platform_rules['max_length']-3] + "..."
        
        # Add platform-specific enhancements
        if 'add_hooks' in platform_rules and platform_rules['add_hooks']:
            hooks = ['How to', 'The secret of', 'Why everyone is talking about']
            if not any(hook.lower() in optimized.lower() for hook in hooks):
                optimized = f"{random.choice(hooks)} {optimized}"
        
        if 'trendy_format' in platform_rules and platform_rules['trendy_format']:
            formats = ['POV:', 'Wait for it...', 'No one talks about this:']
            if not any(fmt.lower() in optimized.lower() for fmt in formats):
                optimized = f"{random.choice(formats)} {optimized}"
        
        return optimized
    
    def _load_optimization_rules(self) -> List[OptimizationRule]:
        """Load optimization rules from database or defaults."""
        rules = []
        
        # Default optimization rules
        default_rules = [
            OptimizationRule(
                name="High-performing tags",
                optimization_type=OptimizationType.TAG_OPTIMIZATION,
                condition="performance_score > 0.7",
                action="add_high_performing_tags",
                weight=0.8,
                success_rate=0.75
            ),
            OptimizationRule(
                name="Optimal timing",
                optimization_type=OptimizationType.TIMING_OPTIMIZATION,
                condition="any",
                action="suggest_optimal_time",
                weight=0.7,
                success_rate=0.65
            ),
            OptimizationRule(
                name="Title enhancement",
                optimization_type=OptimizationType.TITLE_OPTIMIZATION,
                condition="low_engagement",
                action="enhance_title_with_power_words",
                weight=0.6,
                success_rate=0.55
            ),
            OptimizationRule(
                name="Content length optimization",
                optimization_type=OptimizationType.CONTENT_LENGTH,
                condition="performance_score < 0.5",
                action="adjust_content_length",
                weight=0.5,
                success_rate=0.60
            ),
            OptimizationRule(
                name="Platform-specific optimization",
                optimization_type=OptimizationType.PLATFORM_SPECIFIC,
                condition="platform_identified",
                action="apply_platform_rules",
                weight=0.9,
                success_rate=0.80
            )
        ]
        
        return default_rules
    
    def _get_title_patterns(self) -> Optional[Dict[str, Any]]:
        """Get title optimization patterns."""
        # This would integrate with the PatternAnalyzer
        # For now, return mock data
        return {
            'top_performing_words': {
                'how': {'avg_performance': 0.8, 'usage_count': 15},
                'best': {'avg_performance': 0.75, 'usage_count': 12},
                'secret': {'avg_performance': 0.72, 'usage_count': 8},
                'amazing': {'avg_performance': 0.7, 'usage_count': 20}
            },
            'optimal_title_length': {'average': 65}
        }
    
    def _get_tag_patterns(self) -> Optional[Dict[str, Any]]:
        """Get tag optimization patterns."""
        return {
            'top_performing_tags': {
                'tutorial': {'avg_performance': 0.85, 'usage_count': 25},
                'productivity': {'avg_performance': 0.78, 'usage_count': 18},
                'tips': {'avg_performance': 0.75, 'usage_count': 22},
                'how-to': {'avg_performance': 0.82, 'usage_count': 30},
                'lifehack': {'avg_performance': 0.70, 'usage_count': 15}
            }
        }
    
    def _get_timing_patterns(self) -> Optional[Dict[str, Any]]:
        """Get timing optimization patterns."""
        return {
            'best_hours': {
                '09:00': 0.8,
                '14:00': 0.75,
                '19:00': 0.7,
                '12:00': 0.65
            },
            'best_weekdays': {
                'Tuesday': 0.75,
                'Wednesday': 0.73,
                'Thursday': 0.72
            }
        }
    
    def _get_length_patterns(self) -> Optional[Dict[str, Any]]:
        """Get content length patterns."""
        return {
            'short': {'avg_performance': 0.6, 'sample_count': 15},
            'medium': {'avg_performance': 0.8, 'sample_count': 25},
            'long': {'avg_performance': 0.65, 'sample_count': 10}
        }
    
    def _get_trending_tags(self) -> List[str]:
        """Get currently trending tags."""
        # This would be updated from external sources or trend analysis
        trending = ['ai', 'automation', 'productivity', 'workflow', 'smart']
        return trending
    
    def _log_optimization(self, result: OptimizationResult, level: str, platform: Optional[str]):
        """Log optimization for future learning."""
        log_entry = {
            'timestamp': result.applied_at.isoformat(),
            'optimization_level': level,
            'platform': platform,
            'applied_optimizations': result.applied_optimizations,
            'confidence_score': result.confidence_score,
            'expected_improvement': result.expected_improvement,
            'original_content_preview': result.original_content.get('title', '')[:50]
        }
        
        # In a real implementation, this would save to database
        self.optimization_history.append(log_entry)
    
    def get_optimization_suggestions(self, content_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get specific optimization suggestions for content."""
        suggestions = []
        
        # Analyze current content
        title = content_request.get('title', '')
        tags = content_request.get('tags', [])
        content_type = content_request.get('content_type', '')
        
        # Title suggestions
        if len(title) < 30:
            suggestions.append({
                'type': 'title',
                'priority': 'high',
                'suggestion': 'Title could be longer for better SEO and engagement',
                'example': f'{title} - The Complete Guide'
            })
        
        # Tag suggestions
        if len(tags) < 5:
            suggestions.append({
                'type': 'tags',
                'priority': 'medium',
                'suggestion': 'Add more relevant tags to improve discoverability',
                'suggested_tags': ['trending', 'popular', 'how-to', 'tutorial']
            })
        
        # Content type specific suggestions
        if content_type == 'video' and 'thumbnail' not in content_request:
            suggestions.append({
                'type': 'thumbnail',
                'priority': 'high',
                'suggestion': 'Consider adding thumbnail optimization for better click-through rates',
                'recommendations': ['Use bright colors', 'Include faces', 'Add text overlay']
            })
        
        return suggestions