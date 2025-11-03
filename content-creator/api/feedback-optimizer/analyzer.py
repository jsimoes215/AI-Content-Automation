"""
Core Feedback Analyzer Module

Analyzes sentiment patterns and feedback data to identify content improvement opportunities.
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from .utils.sentiment_analyzer import SentimentAnalyzer
from .utils.pattern_detector import PatternDetector
from .models.feedback_data import FeedbackData
from .models.sentiment_metrics import SentimentMetrics


class FeedbackAnalyzer:
    """
    Analyzes feedback patterns and sentiment to identify improvement areas.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the feedback analyzer with configuration."""
        self.config = config or self._default_config()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.pattern_detector = PatternDetector()
        self.feedback_history: List[FeedbackData] = []
        
    def _default_config(self) -> Dict:
        """Default configuration for the analyzer."""
        return {
            'sentiment_weights': {
                'positive': 1.0,
                'neutral': 0.5,
                'negative': -1.0
            },
            'threshold_values': {
                'high_engagement': 0.8,
                'medium_engagement': 0.5,
                'low_engagement': 0.3
            },
            'pattern_sensitivity': 0.7
        }
    
    def analyze_feedback(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """
        Comprehensive analysis of feedback data.
        
        Args:
            feedback_data: List of feedback items with metadata
            
        Returns:
            Dict containing analysis results and insights
        """
        processed_feedback = []
        
        for item in feedback_data:
            # Convert to FeedbackData model
            fb_data = self._process_feedback_item(item)
            if fb_data:
                processed_feedback.append(fb_data)
        
        # Perform various analyses
        sentiment_analysis = self._analyze_sentiment_patterns(processed_feedback)
        engagement_analysis = self._analyze_engagement_patterns(processed_feedback)
        content_analysis = self._analyze_content_quality(processed_feedback)
        trend_analysis = self._analyze_temporal_trends(processed_feedback)
        
        return {
            'sentiment_patterns': sentiment_analysis,
            'engagement_patterns': engagement_analysis,
            'content_quality': content_analysis,
            'temporal_trends': trend_analysis,
            'overall_score': self._calculate_overall_score(sentiment_analysis, engagement_analysis),
            'improvement_areas': self._identify_improvement_areas(sentiment_analysis, engagement_analysis),
            'timestamp': datetime.now().isoformat()
        }
    
    def _process_feedback_item(self, item: Dict) -> Optional[FeedbackData]:
        """Process individual feedback item into FeedbackData model."""
        try:
            # Extract sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(
                text=item.get('text', ''),
                metadata=item
            )
            
            # Detect patterns
            patterns = self.pattern_detector.detect_patterns(
                text=item.get('text', ''),
                context=item
            )
            
            return FeedbackData(
                content_id=item.get('content_id'),
                feedback_type=item.get('feedback_type', 'comment'),
                text=item.get('text', ''),
                sentiment=sentiment,
                engagement_metrics=item.get('engagement_metrics', {}),
                metadata=item.get('metadata', {}),
                patterns=patterns,
                timestamp=datetime.fromisoformat(item.get('timestamp', datetime.now().isoformat()))
            )
        except Exception as e:
            print(f"Error processing feedback item: {e}")
            return None
    
    def _analyze_sentiment_patterns(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """Analyze sentiment patterns across feedback data."""
        if not feedback_data:
            return {}
        
        sentiments = [fb.sentiment.overall_sentiment for fb in feedback_data]
        sentiment_counts = Counter([s['label'] for s in sentiments])
        
        # Calculate sentiment trends
        recent_sentiments = self._get_recent_sentiments(feedback_data, days=7)
        historical_sentiments = self._get_historical_sentiments(feedback_data, days=30)
        
        # Sentiment evolution
        sentiment_evolution = self._calculate_sentiment_evolution(recent_sentiments, historical_sentiments)
        
        # Content-specific sentiment analysis
        script_sentiments = [fb for fb in feedback_data if fb.content_type == 'script']
        thumbnail_sentiments = [fb for fb in feedback_data if fb.content_type == 'thumbnail']
        title_sentiments = [fb for fb in feedback_data if fb.content_type == 'title']
        
        return {
            'distribution': dict(sentiment_counts),
            'average_score': statistics.mean([s['score'] for s in sentiments]),
            'sentiment_evolution': sentiment_evolution,
            'content_breakdown': {
                'script': self._calculate_content_sentiment_stats(script_sentiments),
                'thumbnail': self._calculate_content_sentiment_stats(thumbnail_sentiments),
                'title': self._calculate_content_sentiment_stats(title_sentiments)
            },
            'trending_direction': self._determine_sentiment_trend(sentiment_evolution)
        }
    
    def _analyze_engagement_patterns(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """Analyze engagement patterns and correlations with sentiment."""
        if not feedback_data:
            return {}
        
        # Extract engagement metrics
        engagement_data = []
        for fb in feedback_data:
            metrics = fb.engagement_metrics
            engagement_data.append({
                'sentiment_score': fb.sentiment.overall_sentiment['score'],
                'views': metrics.get('views', 0),
                'likes': metrics.get('likes', 0),
                'comments': metrics.get('comments', 0),
                'shares': metrics.get('shares', 0),
                'engagement_rate': self._calculate_engagement_rate(metrics)
            })
        
        # Calculate correlations
        engagement_correlations = self._calculate_engagement_correlations(engagement_data)
        
        # Identify high vs low performing content
        high_performers = [e for e in engagement_data if e['engagement_rate'] > self.config['threshold_values']['high_engagement']]
        low_performers = [e for e in engagement_data if e['engagement_rate'] < self.config['threshold_values']['low_engagement']]
        
        return {
            'correlation_analysis': engagement_correlations,
            'performance_distribution': {
                'high': len(high_performers),
                'medium': len(engagement_data) - len(high_performers) - len(low_performers),
                'low': len(low_performers)
            },
            'average_engagement_rate': statistics.mean([e['engagement_rate'] for e in engagement_data]),
            'top_performing_characteristics': self._identify_top_performing_characteristics(high_performers),
            'underperforming_characteristics': self._identify_underperforming_characteristics(low_performers)
        }
    
    def _analyze_content_quality(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """Analyze content quality indicators based on feedback patterns."""
        content_quality_scores = defaultdict(list)
        quality_indicators = defaultdict(list)
        
        for fb in feedback_data:
            content_type = fb.content_type
            
            # Calculate quality score based on sentiment and engagement
            quality_score = self._calculate_quality_score(fb)
            content_quality_scores[content_type].append(quality_score)
            
            # Extract quality indicators
            indicators = self._extract_quality_indicators(fb)
            for indicator in indicators:
                quality_indicators[content_type].append(indicator)
        
        # Aggregate quality metrics
        quality_summary = {}
        for content_type, scores in content_quality_scores.items():
            quality_summary[content_type] = {
                'average_quality': statistics.mean(scores),
                'quality_trend': self._calculate_quality_trend(scores),
                'common_issues': self._find_common_quality_issues(quality_indicators[content_type]),
                'strengths': self._identify_content_strengths(quality_indicators[content_type])
            }
        
        return quality_summary
    
    def _analyze_temporal_trends(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """Analyze temporal trends in feedback patterns."""
        # Group feedback by time periods
        daily_sentiments = defaultdict(list)
        daily_engagement = defaultdict(list)
        
        for fb in feedback_data:
            date_key = fb.timestamp.date().isoformat()
            
            daily_sentiments[date_key].append(fb.sentiment.overall_sentiment['score'])
            daily_engagement[date_key].append(self._calculate_engagement_rate(fb.engagement_metrics))
        
        # Calculate trends
        sentiment_trends = {}
        for date, scores in daily_sentiments.items():
            sentiment_trends[date] = statistics.mean(scores)
        
        engagement_trends = {}
        for date, rates in daily_engagement.items():
            engagement_trends[date] = statistics.mean(rates)
        
        return {
            'sentiment_trends': sentiment_trends,
            'engagement_trends': engagement_trends,
            'trend_analysis': self._analyze_trend_direction(sentiment_trends, engagement_trends),
            'peak_performance_days': self._identify_peak_performance_days(sentiment_trends, engagement_trends)
        }
    
    def _calculate_overall_score(self, sentiment_analysis: Dict, engagement_analysis: Dict) -> float:
        """Calculate overall content improvement score."""
        sentiment_score = sentiment_analysis.get('average_score', 0.5)
        engagement_score = engagement_analysis.get('average_engagement_rate', 0.5)
        
        # Weighted combination
        overall_score = (sentiment_score * 0.6) + (engagement_score * 0.4)
        return max(0.0, min(1.0, overall_score))
    
    def _identify_improvement_areas(self, sentiment_analysis: Dict, engagement_analysis: Dict) -> List[Dict[str, Any]]:
        """Identify specific areas that need improvement."""
        improvements = []
        
        # Check sentiment distribution
        sentiment_dist = sentiment_analysis.get('distribution', {})
        if sentiment_dist.get('negative', 0) > sentiment_dist.get('positive', 0):
            improvements.append({
                'area': 'sentiment_optimization',
                'priority': 'high',
                'description': 'High negative sentiment detected - review content tone and messaging',
                'recommendation': 'Focus on positive messaging and addressing common concerns'
            })
        
        # Check content breakdown
        content_breakdown = sentiment_analysis.get('content_breakdown', {})
        lowest_performing = min(content_breakdown.items(), 
                               key=lambda x: x[1].get('average_sentiment', 0.5))
        
        if lowest_performing[1].get('average_sentiment', 0.5) < 0.4:
            improvements.append({
                'area': f'{lowest_performing[0]}_optimization',
                'priority': 'medium',
                'description': f'{lowest_performing[0]} content showing lower sentiment scores',
                'recommendation': f'Review and improve {lowest_performing[0]} creation process'
            })
        
        # Check engagement patterns
        performance_dist = engagement_analysis.get('performance_distribution', {})
        if performance_dist.get('low', 0) > performance_dist.get('high', 0):
            improvements.append({
                'area': 'engagement_optimization',
                'priority': 'high',
                'description': 'Majority of content underperforming in engagement',
                'recommendation': 'Analyze successful content patterns and apply learnings'
            })
        
        return improvements
    
    # Helper methods for specific analyses
    def _get_recent_sentiments(self, feedback_data: List[FeedbackData], days: int) -> List[float]:
        """Get sentiments from recent time period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [fb.sentiment.overall_sentiment['score'] for fb in feedback_data 
                if fb.timestamp >= cutoff_date]
    
    def _get_historical_sentiments(self, feedback_data: List[FeedbackData], days: int) -> List[float]:
        """Get sentiments from historical time period."""
        cutoff_date = datetime.now() - timedelta(days=days*2)
        recent_cutoff = datetime.now() - timedelta(days=days)
        return [fb.sentiment.overall_sentiment['score'] for fb in feedback_data 
                if cutoff_date <= fb.timestamp < recent_cutoff]
    
    def _calculate_sentiment_evolution(self, recent: List[float], historical: List[float]) -> float:
        """Calculate sentiment evolution between periods."""
        if not recent or not historical:
            return 0.0
        
        recent_avg = statistics.mean(recent)
        historical_avg = statistics.mean(historical)
        
        return recent_avg - historical_avg
    
    def _calculate_content_sentiment_stats(self, feedback_list: List[FeedbackData]) -> Dict[str, Any]:
        """Calculate sentiment statistics for specific content type."""
        if not feedback_list:
            return {}
        
        scores = [fb.sentiment.overall_sentiment['score'] for fb in feedback_list]
        return {
            'count': len(feedback_list),
            'average_sentiment': statistics.mean(scores),
            'sentiment_distribution': Counter([fb.sentiment.overall_sentiment['label'] for fb in feedback_list])
        }
    
    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """Calculate engagement rate from metrics."""
        views = metrics.get('views', 0)
        if views == 0:
            return 0.0
        
        likes = metrics.get('likes', 0)
        comments = metrics.get('comments', 0)
        shares = metrics.get('shares', 0)
        
        total_engagement = likes + comments + shares
        return min(1.0, total_engagement / views)
    
    def _calculate_engagement_correlations(self, engagement_data: List[Dict]) -> Dict[str, float]:
        """Calculate correlations between sentiment and engagement metrics."""
        # Simplified correlation calculation
        sentiments = [e['sentiment_score'] for e in engagement_data]
        
        correlations = {}
        for metric in ['views', 'likes', 'comments', 'shares', 'engagement_rate']:
            values = [e[metric] for e in engagement_data]
            
            if len(values) > 1:
                # Simple correlation coefficient calculation
                correlation = self._pearson_correlation(sentiments, values)
                correlations[metric] = correlation
        
        return correlations
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _determine_sentiment_trend(self, evolution: float) -> str:
        """Determine overall sentiment trend direction."""
        if evolution > 0.1:
            return 'improving'
        elif evolution < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_quality_score(self, fb: FeedbackData) -> float:
        """Calculate quality score for feedback data."""
        sentiment_score = fb.sentiment.overall_sentiment['score']
        engagement_score = self._calculate_engagement_rate(fb.engagement_metrics)
        
        # Combine sentiment and engagement
        return (sentiment_score * 0.7) + (engagement_score * 0.3)
    
    def _extract_quality_indicators(self, fb: FeedbackData) -> List[str]:
        """Extract quality indicators from feedback."""
        indicators = []
        
        # Based on sentiment analysis
        if fb.sentiment.overall_sentiment['label'] == 'positive':
            indicators.append('positive_reception')
        
        # Based on patterns
        for pattern in fb.patterns:
            indicators.append(pattern['type'])
        
        # Based on engagement
        engagement_rate = self._calculate_engagement_rate(fb.engagement_metrics)
        if engagement_rate > 0.5:
            indicators.append('high_engagement')
        elif engagement_rate < 0.2:
            indicators.append('low_engagement')
        
        return indicators
    
    def _calculate_quality_trend(self, scores: List[float]) -> str:
        """Calculate trend direction for quality scores."""
        if len(scores) < 2:
            return 'insufficient_data'
        
        # Simple trend calculation
        recent_scores = scores[-7:]  # Last 7 scores
        older_scores = scores[:-7] if len(scores) > 7 else scores
        
        if not older_scores:
            return 'insufficient_data'
        
        recent_avg = statistics.mean(recent_scores)
        older_avg = statistics.mean(older_scores)
        
        if recent_avg > older_avg + 0.1:
            return 'improving'
        elif recent_avg < older_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _find_common_quality_issues(self, indicators: List[str]) -> List[str]:
        """Find common quality issues from indicators."""
        if not indicators:
            return []
        
        indicator_counts = Counter(indicators)
        # Filter for negative indicators
        negative_indicators = [ind for ind in indicator_counts if 'negative' in ind.lower() or 'low' in ind.lower()]
        
        return [ind for ind, count in indicator_counts.most_common(3) 
                if ind in negative_indicators]
    
    def _identify_content_strengths(self, indicators: List[str]) -> List[str]:
        """Identify content strengths from positive indicators."""
        if not indicators:
            return []
        
        positive_indicators = [ind for ind in indicators if any(pos in ind.lower() for pos in ['high', 'positive', 'good'])]
        indicator_counts = Counter(positive_indicators)
        
        return [ind for ind, count in indicator_counts.most_common(3)]
    
    def _identify_top_performing_characteristics(self, high_performers: List[Dict]) -> List[str]:
        """Identify characteristics of top-performing content."""
        if not high_performers:
            return []
        
        # Analyze common traits
        high_sentiment = [p for p in high_performers if p['sentiment_score'] > 0.7]
        return [f"Average sentiment: {statistics.mean([p['sentiment_score'] for p in high_performers]):.2f}"]
    
    def _identify_underperforming_characteristics(self, low_performers: List[Dict]) -> List[str]:
        """Identify characteristics of underperforming content."""
        if not low_performers:
            return []
        
        low_sentiment = [p for p in low_performers if p['sentiment_score'] < 0.3]
        return [f"Average sentiment: {statistics.mean([p['sentiment_score'] for p in low_performers]):.2f}"]
    
    def _analyze_trend_direction(self, sentiment_trends: Dict, engagement_trends: Dict) -> Dict[str, str]:
        """Analyze overall trend direction."""
        if not sentiment_trends or not engagement_trends:
            return {'overall': 'insufficient_data'}
        
        # Calculate overall trends
        sentiment_values = list(sentiment_trends.values())
        engagement_values = list(engagement_trends.values())
        
        sentiment_trend = self._determine_sentiment_trend(
            statistics.mean(sentiment_values[-7:]) - statistics.mean(sentiment_values[:7]) if len(sentiment_values) > 7 else 0
        )
        
        engagement_trend = self._determine_sentiment_trend(
            statistics.mean(engagement_values[-7:]) - statistics.mean(engagement_values[:7]) if len(engagement_values) > 7 else 0
        )
        
        return {
            'sentiment': sentiment_trend,
            'engagement': engagement_trend,
            'overall': 'improving' if sentiment_trend == 'improving' and engagement_trend == 'improving' else 'needs_attention'
        }
    
    def _identify_peak_performance_days(self, sentiment_trends: Dict, engagement_trends: Dict) -> List[str]:
        """Identify days with peak performance."""
        if not sentiment_trends or not engagement_trends:
            return []
        
        # Find days where both sentiment and engagement are above average
        avg_sentiment = statistics.mean(sentiment_trends.values())
        avg_engagement = statistics.mean(engagement_trends.values())
        
        peak_days = []
        for date in sentiment_trends:
            if date in engagement_trends:
                if sentiment_trends[date] > avg_sentiment and engagement_trends[date] > avg_engagement:
                    peak_days.append(date)
        
        return sorted(peak_days)[-5:]  # Return last 5 peak days