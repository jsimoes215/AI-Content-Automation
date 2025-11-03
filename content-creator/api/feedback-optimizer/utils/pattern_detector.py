"""
Pattern Detection Utility Module

Identifies common patterns and themes in feedback data for targeted improvements.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics

from ..models.feedback_data import FeedbackData


class PatternDetector:
    """
    Advanced pattern detection for feedback analysis and improvement targeting.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the pattern detector."""
        self.config = config or self._default_config()
        self.pattern_library = self._load_pattern_library()
        self.content_patterns = self._load_content_patterns()
        
    def _default_config(self) -> Dict:
        """Default configuration for pattern detection."""
        return {
            'pattern_threshold': 0.3,
            'min_frequency': 2,
            'context_window': 3,
            'similarity_threshold': 0.8,
            'pattern_weights': {
                'content_quality': 1.0,
                'engagement': 0.9,
                'technical': 0.8,
                'aesthetic': 0.7,
                'performance': 1.0
            }
        }
    
    def detect_patterns(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect patterns in feedback text and context.
        
        Args:
            text: Feedback text to analyze
            context: Additional context information
            
        Returns:
            List of detected patterns with confidence scores
        """
        patterns = []
        
        # Text-based pattern detection
        text_patterns = self._detect_text_patterns(text)
        patterns.extend(text_patterns)
        
        # Context-based pattern detection
        context_patterns = self._detect_context_patterns(context)
        patterns.extend(context_patterns)
        
        # Content-specific pattern detection
        content_patterns = self._detect_content_patterns(text, context)
        patterns.extend(content_patterns)
        
        # Performance pattern detection
        performance_patterns = self._detect_performance_patterns(text, context)
        patterns.extend(performance_patterns)
        
        return self._filter_and_rank_patterns(patterns)
    
    def _detect_text_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Detect patterns based on text content."""
        patterns = []
        text_lower = text.lower()
        
        # Quality-related patterns
        quality_patterns = [
            {
                'type': 'content_quality',
                'pattern': 'quality.*(good|bad|poor|excellent|amazing|terrible)',
                'keywords': ['quality', 'standard', 'level'],
                'sentiment_impact': 0.8
            },
            {
                'type': 'content_quality',
                'pattern': '(well|poorly)(-|\\s)?made',
                'keywords': ['well-made', 'poorly-made'],
                'sentiment_impact': 0.7
            },
            {
                'type': 'content_quality',
                'pattern': 'professional.*(look|appearance|quality)',
                'keywords': ['professional', 'amateur'],
                'sentiment_impact': 0.6
            }
        ]
        
        # Engagement patterns
        engagement_patterns = [
            {
                'type': 'engagement',
                'pattern': '(boring|interesting|engaging|exciting|captivating)',
                'keywords': ['boring', 'interesting', 'engaging', 'exciting', 'captivating'],
                'sentiment_impact': 0.9
            },
            {
                'type': 'engagement',
                'pattern': '(watch|view|listen).*(all|entire|complete)',
                'keywords': ['complete viewing', 'full attention'],
                'sentiment_impact': 0.8
            },
            {
                'type': 'engagement',
                'pattern': '(skip|fast.?forward|pause)',
                'keywords': ['skip', 'fast-forward', 'pause'],
                'sentiment_impact': -0.7
            }
        ]
        
        # Technical patterns
        technical_patterns = [
            {
                'type': 'technical',
                'pattern': '(audio|sound).*(clear|muddy|loud|quiet|good|bad)',
                'keywords': ['audio quality', 'sound quality'],
                'sentiment_impact': 0.6
            },
            {
                'type': 'technical',
                'pattern': '(video|picture|image).*(clear|blurry|pixelated|sharp)',
                'keywords': ['video quality', 'image quality'],
                'sentiment_impact': 0.6
            },
            {
                'type': 'technical',
                'pattern': '(loading|slow|buffer|lag)',
                'keywords': ['loading', 'slow', 'buffer', 'lag'],
                'sentiment_impact': -0.5
            }
        ]
        
        # Aesthetic patterns
        aesthetic_patterns = [
            {
                'type': 'aesthetic',
                'pattern': '(beautiful|ugly|attractive|visually.*(appealing|appealing|great))',
                'keywords': ['beautiful', 'ugly', 'attractive', 'visually appealing'],
                'sentiment_impact': 0.7
            },
            {
                'type': 'aesthetic',
                'pattern': '(design|layout|color|font|style).*(good|bad|poor|excellent)',
                'keywords': ['design', 'layout', 'color', 'font', 'style'],
                'sentiment_impact': 0.5
            }
        ]
        
        all_patterns = quality_patterns + engagement_patterns + technical_patterns + aesthetic_patterns
        
        for pattern_def in all_patterns:
            if re.search(pattern_def['pattern'], text_lower, re.IGNORECASE):
                patterns.append({
                    'type': pattern_def['type'],
                    'pattern': pattern_def['pattern'],
                    'matched_text': self._extract_matched_text(text, pattern_def['pattern']),
                    'keywords': pattern_def['keywords'],
                    'confidence': self._calculate_pattern_confidence(text, pattern_def),
                    'sentiment_impact': pattern_def['sentiment_impact'],
                    'category': 'text_based'
                })
        
        return patterns
    
    def _detect_context_patterns(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect patterns based on context information."""
        patterns = []
        
        # Platform-specific patterns
        platform = context.get('platform', '').lower()
        if platform:
            patterns.append({
                'type': 'platform_specific',
                'pattern': f'platform_{platform}',
                'matched_text': platform,
                'confidence': 0.9,
                'sentiment_impact': 0.3,
                'category': 'context_based',
                'metadata': {'platform': platform}
            })
        
        # Device-specific patterns
        device = context.get('device', '').lower()
        if device:
            patterns.append({
                'type': 'device_specific',
                'pattern': f'device_{device}',
                'matched_text': device,
                'confidence': 0.8,
                'sentiment_impact': 0.2,
                'category': 'context_based',
                'metadata': {'device': device}
            })
        
        # Time-based patterns
        time_of_day = context.get('time_of_day', '')
        if time_of_day:
            patterns.append({
                'type': 'temporal',
                'pattern': f'time_{time_of_day}',
                'matched_text': time_of_day,
                'confidence': 0.6,
                'sentiment_impact': 0.1,
                'category': 'context_based',
                'metadata': {'time_of_day': time_of_day}
            })
        
        return patterns
    
    def _detect_content_patterns(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect content-specific patterns."""
        patterns = []
        content_type = context.get('content_type', '')
        
        if not content_type:
            return patterns
        
        # Script-specific patterns
        if content_type == 'script':
            script_patterns = [
                {
                    'type': 'script_structure',
                    'pattern': '(confusing|clear|well.?structured|hard.?follow)',
                    'sentiment_impact': 0.7
                },
                {
                    'type': 'script_content',
                    'pattern': '(informative|educational|useful|worthless|irrelevant)',
                    'sentiment_impact': 0.8
                },
                {
                    'type': 'script_tone',
                    'pattern': '(friendly|professional|casual|boring|enthusiastic)',
                    'sentiment_impact': 0.6
                }
            ]
            
            for pattern_def in script_patterns:
                if re.search(pattern_def['pattern'], text.lower(), re.IGNORECASE):
                    patterns.append({
                        'type': pattern_def['type'],
                        'pattern': pattern_def['pattern'],
                        'matched_text': self._extract_matched_text(text, pattern_def['pattern']),
                        'confidence': 0.8,
                        'sentiment_impact': pattern_def['sentiment_impact'],
                        'category': 'content_specific',
                        'metadata': {'content_type': 'script'}
                    })
        
        # Thumbnail-specific patterns
        elif content_type == 'thumbnail':
            thumbnail_patterns = [
                {
                    'type': 'thumbnail_design',
                    'pattern': '(eye.?catching|attention.?grabbing|boring|ugly|attractive)',
                    'sentiment_impact': 0.8
                },
                {
                    'type': 'thumbnail_clarity',
                    'pattern': '(clear|unclear|blurry|pixelated|readable)',
                    'sentiment_impact': 0.7
                },
                {
                    'type': 'thumbnail_colors',
                    'pattern': '(vibrant|muted|bright|dark|colorful)',
                    'sentiment_impact': 0.5
                }
            ]
            
            for pattern_def in thumbnail_patterns:
                if re.search(pattern_def['pattern'], text.lower(), re.IGNORECASE):
                    patterns.append({
                        'type': pattern_def['type'],
                        'pattern': pattern_def['pattern'],
                        'matched_text': self._extract_matched_text(text, pattern_def['pattern']),
                        'confidence': 0.8,
                        'sentiment_impact': pattern_def['sentiment_impact'],
                        'category': 'content_specific',
                        'metadata': {'content_type': 'thumbnail'}
                    })
        
        # Title-specific patterns
        elif content_type == 'title':
            title_patterns = [
                {
                    'type': 'title_clarity',
                    'pattern': '(clear|confusing|descriptive|misleading)',
                    'sentiment_impact': 0.7
                },
                {
                    'type': 'title_appeal',
                    'pattern': '(interesting|boring|click.?bait|compelling)',
                    'sentiment_impact': 0.8
                },
                {
                    'type': 'title_length',
                    'pattern': '(too.?long|too.?short|perfect.?length)',
                    'sentiment_impact': 0.5
                }
            ]
            
            for pattern_def in title_patterns:
                if re.search(pattern_def['pattern'], text.lower(), re.IGNORECASE):
                    patterns.append({
                        'type': pattern_def['type'],
                        'pattern': pattern_def['pattern'],
                        'matched_text': self._extract_matched_text(text, pattern_def['pattern']),
                        'confidence': 0.7,
                        'sentiment_impact': pattern_def['sentiment_impact'],
                        'category': 'content_specific',
                        'metadata': {'content_type': 'title'}
                    })
        
        return patterns
    
    def _detect_performance_patterns(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect performance-related patterns."""
        patterns = []
        
        # Engagement metrics-based patterns
        engagement_metrics = context.get('engagement_metrics', {})
        
        if engagement_metrics:
            views = engagement_metrics.get('views', 0)
            likes = engagement_metrics.get('likes', 0)
            comments = engagement_metrics.get('comments', 0)
            
            # Low engagement patterns
            if views > 0:
                engagement_rate = (likes + comments) / views
                if engagement_rate < 0.01:  # Less than 1% engagement
                    patterns.append({
                        'type': 'low_engagement',
                        'pattern': 'engagement_rate_low',
                        'matched_text': f'engagement_rate_{engagement_rate:.3f}',
                        'confidence': 0.9,
                        'sentiment_impact': -0.5,
                        'category': 'performance_based',
                        'metadata': {
                            'engagement_rate': engagement_rate,
                            'views': views,
                            'likes': likes,
                            'comments': comments
                        }
                    })
            
            # High engagement patterns
            if views > 100 and engagement_rate > 0.05:  # Over 5% engagement with sufficient views
                patterns.append({
                    'type': 'high_engagement',
                    'pattern': 'engagement_rate_high',
                    'matched_text': f'engagement_rate_{engagement_rate:.3f}',
                    'confidence': 0.9,
                    'sentiment_impact': 0.5,
                    'category': 'performance_based',
                    'metadata': {
                        'engagement_rate': engagement_rate,
                        'views': views,
                        'likes': likes,
                        'comments': comments
                    }
                })
        
        # Comment sentiment patterns
        if 'sentiment_score' in context:
            sentiment_score = context['sentiment_score']
            if sentiment_score < -0.3:
                patterns.append({
                    'type': 'negative_sentiment_pattern',
                    'pattern': 'negative_feedback_cluster',
                    'matched_text': f'sentiment_{sentiment_score:.2f}',
                    'confidence': 0.8,
                    'sentiment_impact': -0.7,
                    'category': 'performance_based',
                    'metadata': {'sentiment_score': sentiment_score}
                })
            elif sentiment_score > 0.3:
                patterns.append({
                    'type': 'positive_sentiment_pattern',
                    'pattern': 'positive_feedback_cluster',
                    'matched_text': f'sentiment_{sentiment_score:.2f}',
                    'confidence': 0.8,
                    'sentiment_impact': 0.7,
                    'category': 'performance_based',
                    'metadata': {'sentiment_score': sentiment_score}
                })
        
        return patterns
    
    def analyze_pattern_frequency(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """
        Analyze pattern frequency across multiple feedback items.
        
        Args:
            feedback_data: List of feedback data items
            
        Returns:
            Dictionary with pattern frequency analysis
        """
        pattern_frequency = defaultdict(int)
        pattern_details = defaultdict(list)
        pattern_trends = defaultdict(list)
        
        for fb in feedback_data:
            # Extract patterns from feedback
            patterns = self.detect_patterns(fb.text, fb.metadata)
            
            for pattern in patterns:
                pattern_type = pattern['type']
                pattern_frequency[pattern_type] += 1
                
                pattern_details[pattern_type].append({
                    'sentiment_impact': pattern['sentiment_impact'],
                    'confidence': pattern['confidence'],
                    'timestamp': fb.timestamp,
                    'content_id': fb.content_id
                })
                
                pattern_trends[pattern_type].append({
                    'date': fb.timestamp.date(),
                    'frequency': 1
                })
        
        # Calculate pattern statistics
        pattern_stats = {}
        for pattern_type, frequency in pattern_frequency.items():
            details = pattern_details[pattern_type]
            
            if details:
                pattern_stats[pattern_type] = {
                    'frequency': frequency,
                    'average_sentiment_impact': statistics.mean([d['sentiment_impact'] for d in details]),
                    'average_confidence': statistics.mean([d['confidence'] for d in details]),
                    'latest_occurrence': max(d['timestamp'] for d in details),
                    'trend': self._calculate_pattern_trend(pattern_trends[pattern_type])
                }
        
        return {
            'pattern_frequency': dict(pattern_frequency),
            'pattern_statistics': pattern_stats,
            'total_patterns': sum(pattern_frequency.values()),
            'unique_patterns': len(pattern_frequency),
            'most_frequent_pattern': max(pattern_frequency.items(), key=lambda x: x[1])[0] if pattern_frequency else None
        }
    
    def identify_improvement_opportunities(self, pattern_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify specific improvement opportunities based on pattern analysis.
        
        Args:
            pattern_analysis: Results from pattern frequency analysis
            
        Returns:
            List of improvement opportunities
        """
        opportunities = []
        pattern_stats = pattern_analysis.get('pattern_statistics', {})
        
        for pattern_type, stats in pattern_stats.items():
            frequency = stats['frequency']
            avg_sentiment_impact = stats['average_sentiment_impact']
            avg_confidence = stats['average_confidence']
            
            # High-frequency negative patterns
            if frequency >= self.config['min_frequency'] and avg_sentiment_impact < -0.3:
                opportunities.append({
                    'type': 'frequent_negative_pattern',
                    'pattern': pattern_type,
                    'priority': 'high',
                    'frequency': frequency,
                    'impact': abs(avg_sentiment_impact),
                    'confidence': avg_confidence,
                    'action': f'Address recurring {pattern_type} issues',
                    'description': f'Pattern "{pattern_type}" appears {frequency} times with negative sentiment impact'
                })
            
            # Low-confidence high-impact patterns
            elif avg_confidence < 0.6 and abs(avg_sentiment_impact) > 0.5:
                opportunities.append({
                    'type': 'uncertain_high_impact',
                    'pattern': pattern_type,
                    'priority': 'medium',
                    'frequency': frequency,
                    'impact': abs(avg_sentiment_impact),
                    'confidence': avg_confidence,
                    'action': f'Investigate {pattern_type} patterns more deeply',
                    'description': f'Uncertain but potentially impactful pattern: {pattern_type}'
                })
            
            # Emerging patterns
            elif frequency >= 2 and self._is_emerging_pattern(pattern_type, pattern_stats):
                opportunities.append({
                    'type': 'emerging_pattern',
                    'pattern': pattern_type,
                    'priority': 'medium',
                    'frequency': frequency,
                    'impact': abs(avg_sentiment_impact),
                    'confidence': avg_confidence,
                    'action': f'Monitor {pattern_type} patterns for growth',
                    'description': f'Emerging pattern detected: {pattern_type}'
                })
        
        # Sort by priority and impact
        opportunities.sort(key=lambda x: (x['priority'] == 'high', x['impact']), reverse=True)
        
        return opportunities
    
    def _extract_matched_text(self, text: str, pattern: str) -> str:
        """Extract the specific text that matched the pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group() if match else ''
    
    def _calculate_pattern_confidence(self, text: str, pattern_def: Dict[str, Any]) -> float:
        """Calculate confidence score for a detected pattern."""
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on keyword matches
        if 'keywords' in pattern_def:
            keyword_matches = sum(1 for keyword in pattern_def['keywords'] if keyword.lower() in text.lower())
            confidence += min(0.4, keyword_matches * 0.2)
        
        # Increase confidence based on pattern specificity
        if len(pattern_def['pattern']) > 10:  # More specific patterns
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _filter_and_rank_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter patterns by confidence and rank by importance."""
        filtered_patterns = [p for p in patterns if p['confidence'] >= self.config['pattern_threshold']]
        
        # Sort by confidence and sentiment impact
        filtered_patterns.sort(
            key=lambda x: (x['confidence'], abs(x['sentiment_impact'])),
            reverse=True
        )
        
        return filtered_patterns
    
    def _calculate_pattern_trend(self, trend_data: List[Dict[str, Any]]) -> str:
        """Calculate trend direction for a pattern."""
        if len(trend_data) < 2:
            return 'insufficient_data'
        
        # Group by date and sum frequencies
        daily_frequencies = defaultdict(int)
        for item in trend_data:
            daily_frequencies[item['date']] += item['frequency']
        
        sorted_dates = sorted(daily_frequencies.keys())
        
        if len(sorted_dates) < 2:
            return 'stable'
        
        # Compare first half vs second half
        midpoint = len(sorted_dates) // 2
        first_half_avg = statistics.mean([daily_frequencies[date] for date in sorted_dates[:midpoint]])
        second_half_avg = statistics.mean([daily_frequencies[date] for date in sorted_dates[midpoint:]])
        
        difference = second_half_avg - first_half_avg
        
        if difference > 0.5:
            return 'increasing'
        elif difference < -0.5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _is_emerging_pattern(self, pattern_type: str, all_patterns: Dict[str, Any]) -> bool:
        """Check if a pattern is emerging (recently increased frequency)."""
        # This is a simplified check - in reality, you'd want more sophisticated trend analysis
        return all_patterns[pattern_type]['frequency'] >= 2
    
    def _load_pattern_library(self) -> Dict[str, Any]:
        """Load the pattern detection library."""
        return {
            'quality_indicators': [
                r'quality', r'standard', r'level', r'professional', r'amateur',
                r'well.?made', r'poorly.?made', r'good', r'bad', r'poor', r'excellent'
            ],
            'engagement_indicators': [
                r'boring', r'interesting', r'engagement', r'exciting', r'captivating',
                r'skip', r'fast.?forward', r'pause', r'watch', r'view', r'listen'
            ],
            'technical_indicators': [
                r'audio', r'sound', r'video', r'picture', r'image', r'clear', r'blurry',
                r'loading', r'slow', r'buffer', r'lag', r'pixelated', r'sharp'
            ],
            'aesthetic_indicators': [
                r'beautiful', r'ugly', r'attractive', r'design', r'layout', r'color',
                r'font', r'style', r'visually', r'appealing'
            ]
        }
    
    def _load_content_patterns(self) -> Dict[str, Any]:
        """Load content-specific pattern definitions."""
        return {
            'script': {
                'structure': [r'confusing', r'clear', r'well.?structured', r'hard.?follow'],
                'content': [r'informative', r'educational', r'useful', r'worthless', r'irrelevant'],
                'tone': [r'friendly', r'professional', r'casual', r'boring', r'enthusiastic']
            },
            'thumbnail': {
                'design': [r'eye.?catching', r'attention.?grabbing', r'boring', r'ugly', r'attractive'],
                'clarity': [r'clear', r'unclear', r'blurry', r'pixelated', r'readable'],
                'colors': [r'vibrant', r'muted', r'bright', r'dark', r'colorful']
            },
            'title': {
                'clarity': [r'clear', r'confusing', r'descriptive', r'misleading'],
                'appeal': [r'interesting', r'boring', r'click.?bait', r'compelling'],
                'length': [r'too.?long', r'too.?short', r'perfect.?length']
            }
        }