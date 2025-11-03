"""
Pattern Analyzer Module

Analyzes successful content patterns to identify what makes content perform well.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics


class PatternAnalyzer:
    """Analyzes content performance patterns and identifies success factors."""
    
    def __init__(self, db_path: str = "data/content_creator.db"):
        self.db_path = db_path
        self.pattern_cache = {}
        self.analysis_timestamp = None
        
    def analyze_performance_patterns(self, 
                                   days_back: int = 30,
                                   content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze content performance patterns over a specified time period.
        
        Args:
            days_back: Number of days to look back for analysis
            content_type: Optional filter for specific content type
            
        Returns:
            Dictionary containing performance patterns and insights
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get content with performance metrics
                query = """
                SELECT content_id, content_type, title, tags, 
                       metrics_views, metrics_likes, metrics_comments,
                       metrics_shares, performance_score, created_at
                FROM content_items 
                WHERE created_at >= ? AND performance_score IS NOT NULL
                """
                params = [cutoff_date.isoformat()]
                
                if content_type:
                    query += " AND content_type = ?"
                    params.append(content_type)
                    
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                if not rows:
                    return {"error": "No performance data available"}
                    
                # Convert to list of dictionaries
                contents = []
                for row in rows:
                    contents.append({
                        'content_id': row[0],
                        'content_type': row[1],
                        'title': row[2],
                        'tags': json.loads(row[3]) if row[3] else [],
                        'metrics_views': row[4] or 0,
                        'metrics_likes': row[5] or 0,
                        'metrics_comments': row[6] or 0,
                        'metrics_shares': row[7] or 0,
                        'performance_score': row[8] or 0,
                        'created_at': row[9]
                    })
                
                patterns = self._extract_patterns(contents)
                insights = self._generate_insights(contents, patterns)
                
                return {
                    'analysis_date': datetime.now().isoformat(),
                    'period_days': days_back,
                    'content_count': len(contents),
                    'patterns': patterns,
                    'insights': insights,
                    'recommendations': self._generate_recommendations(patterns, insights)
                }
                
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _extract_patterns(self, contents: List[Dict]) -> Dict[str, Any]:
        """Extract patterns from content data."""
        patterns = {
            'successful_tags': self._analyze_successful_tags(contents),
            'optimal_timing': self._analyze_optimal_timing(contents),
            'title_patterns': self._analyze_title_patterns(contents),
            'content_length_patterns': self._analyze_content_length(contents),
            'engagement_ratios': self._analyze_engagement_ratios(contents),
            'platform_preferences': self._analyze_platform_preferences(contents)
        }
        
        return patterns
    
    def _analyze_successful_tags(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze which tags perform best."""
        tag_performance = defaultdict(list)
        
        for content in contents:
            for tag in content.get('tags', []):
                tag_performance[tag].append(content['performance_score'])
        
        # Calculate average performance for each tag
        tag_stats = {}
        for tag, scores in tag_performance.items():
            if len(scores) >= 3:  # Only analyze tags with sufficient data
                tag_stats[tag] = {
                    'avg_performance': statistics.mean(scores),
                    'median_performance': statistics.median(scores),
                    'usage_count': len(scores),
                    'success_rate': len([s for s in scores if s > 0.7]) / len(scores)
                }
        
        # Sort by average performance
        top_tags = sorted(tag_stats.items(), 
                         key=lambda x: x[1]['avg_performance'], 
                         reverse=True)[:10]
        
        return {
            'top_performing_tags': dict(top_tags),
            'total_tag_variety': len(tag_stats),
            'most_used_tags': dict(sorted(tag_stats.items(), 
                                        key=lambda x: x[1]['usage_count'], 
                                        reverse=True)[:10])
        }
    
    def _analyze_optimal_timing(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze optimal timing patterns."""
        weekday_performance = defaultdict(list)
        hour_performance = defaultdict(list)
        
        for content in contents:
            created = datetime.fromisoformat(content['created_at'])
            weekday = created.weekday()
            hour = created.hour
            
            weekday_performance[weekday].append(content['performance_score'])
            hour_performance[hour].append(content['performance_score'])
        
        # Calculate average performance by weekday (0=Monday, 6=Sunday)
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_stats = {}
        for i, day_name in enumerate(weekdays):
            if weekday_performance[i]:
                weekday_stats[day_name] = statistics.mean(weekday_performance[i])
        
        # Calculate average performance by hour
        hour_stats = {}
        for hour, scores in hour_performance.items():
            if scores:
                hour_stats[f"{hour:02d}:00"] = statistics.mean(scores)
        
        return {
            'best_weekdays': dict(sorted(weekday_stats.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True)[:3]),
            'best_hours': dict(sorted(hour_stats.items(), 
                                    key=lambda x: x[1], 
                                    reverse=True)[:5]),
            'worst_hours': dict(sorted(hour_stats.items(), 
                                     key=lambda x: x[1])[:3])
        }
    
    def _analyze_title_patterns(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze title patterns that perform well."""
        title_words = defaultdict(list)
        title_lengths = []
        
        for content in contents:
            title = content['title']
            title_lengths.append(len(title))
            
            # Extract words and their performance
            words = title.lower().split()
            for word in words:
                # Filter out common words
                if len(word) > 2 and word not in ['the', 'and', 'for', 'with', 'that', 'this']:
                    title_words[word].append(content['performance_score'])
        
        # Analyze successful words
        successful_words = {}
        for word, scores in title_words.items():
            if len(scores) >= 2:
                successful_words[word] = {
                    'avg_performance': statistics.mean(scores),
                    'usage_count': len(scores)
                }
        
        top_words = dict(sorted(successful_words.items(), 
                               key=lambda x: x[1]['avg_performance'], 
                               reverse=True)[:20])
        
        return {
            'top_performing_words': top_words,
            'optimal_title_length': {
                'average': statistics.mean(title_lengths),
                'min': min(title_lengths),
                'max': max(title_lengths),
                'median': statistics.median(title_lengths)
            },
            'length_vs_performance': self._analyze_correlation(title_lengths, [c['performance_score'] for c in contents])
        }
    
    def _analyze_content_length(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze content length patterns."""
        # This would need to be adapted based on your content length storage
        # For now, we'll analyze based on available metrics
        
        view_thresholds = [100, 500, 1000, 5000, 10000]
        length_ranges = {
            'very_short': {'min': 0, 'max': 100},
            'short': {'min': 100, 'max': 300},
            'medium': {'min': 300, 'max': 600},
            'long': {'min': 600, 'max': 1000},
            'very_long': {'min': 1000, 'max': float('inf')}
        }
        
        length_performance = {range_name: [] for range_name in length_ranges}
        
        # This is a simplified analysis - you'd want to use actual content length data
        for content in contents:
            # Mock content length based on views (simplified)
            estimated_length = min(max(content['metrics_views'] // 10, 50), 1000)
            
            for range_name, limits in length_ranges.items():
                if limits['min'] <= estimated_length < limits['max']:
                    length_performance[range_name].append(content['performance_score'])
                    break
        
        length_stats = {}
        for range_name, scores in length_performance.items():
            if scores:
                length_stats[range_name] = {
                    'avg_performance': statistics.mean(scores),
                    'sample_count': len(scores)
                }
        
        return length_stats
    
    def _analyze_engagement_ratios(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement ratio patterns."""
        like_ratios = []
        comment_ratios = []
        share_ratios = []
        
        for content in contents:
            views = content['metrics_views']
            if views > 0:
                like_ratios.append(content['metrics_likes'] / views)
                comment_ratios.append(content['metrics_comments'] / views)
                share_ratios.append(content['metrics_shares'] / views)
        
        return {
            'like_ratio': {
                'average': statistics.mean(like_ratios) if like_ratios else 0,
                'median': statistics.median(like_ratios) if like_ratios else 0,
                'high_performance_threshold': statistics.quantiles(like_ratios, n=4)[-1] if like_ratios else 0
            },
            'comment_ratio': {
                'average': statistics.mean(comment_ratios) if comment_ratios else 0,
                'median': statistics.median(comment_ratios) if comment_ratios else 0,
                'high_performance_threshold': statistics.quantiles(comment_ratios, n=4)[-1] if comment_ratios else 0
            },
            'share_ratio': {
                'average': statistics.mean(share_ratios) if share_ratios else 0,
                'median': statistics.median(share_ratios) if share_ratios else 0,
                'high_performance_threshold': statistics.quantiles(share_ratios, n=4)[-1] if share_ratios else 0
            }
        }
    
    def _analyze_platform_preferences(self, contents: List[Dict]) -> Dict[str, Any]:
        """Analyze platform-specific performance patterns."""
        platform_performance = defaultdict(list)
        platform_engagement = defaultdict(lambda: defaultdict(list))
        
        for content in contents:
            # This would need to be adapted based on your platform data structure
            # For now, we'll create mock platform analysis
            if 'youtube' in content.get('title', '').lower():
                platform = 'youtube'
            elif 'instagram' in content.get('title', '').lower():
                platform = 'instagram'
            elif 'tiktok' in content.get('title', '').lower():
                platform = 'tiktok'
            else:
                platform = 'general'
            
            platform_performance[platform].append(content['performance_score'])
            platform_engagement[platform]['likes'].append(content['metrics_likes'])
            platform_engagement[platform]['views'].append(content['metrics_views'])
        
        platform_stats = {}
        for platform, scores in platform_performance.items():
            platform_stats[platform] = {
                'avg_performance': statistics.mean(scores),
                'content_count': len(scores),
                'avg_engagement': statistics.mean([sum(platform_engagement[platform][metric]) 
                                                for metric in platform_engagement[platform]]) / len(scores) if scores else 0
            }
        
        return platform_stats
    
    def _analyze_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate correlation coefficient between two variables."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))**0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _generate_insights(self, contents: List[Dict], patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from patterns."""
        insights = []
        
        # Tag insights
        if patterns['successful_tags']['top_performing_tags']:
            top_tag = list(patterns['successful_tags']['top_performing_tags'].keys())[0]
            top_perf = patterns['successful_tags']['top_performing_tags'][top_tag]['avg_performance']
            insights.append(f"Tag '{top_tag}' shows highest average performance ({top_perf:.2f})")
        
        # Timing insights
        if patterns['optimal_timing']['best_weekdays']:
            best_day = max(patterns['optimal_timing']['best_weekdays'], 
                         key=patterns['optimal_timing']['best_weekdays'].get)
            insights.append(f"{best_day}s show best content performance")
        
        # Title insights
        if patterns['title_patterns']['top_performing_words']:
            top_word = list(patterns['title_patterns']['top_performing_words'].keys())[0]
            insights.append(f"Words like '{top_word}' in titles correlate with higher performance")
        
        # Engagement insights
        avg_like_ratio = patterns['engagement_ratios']['like_ratio']['average']
        if avg_like_ratio > 0.05:
            insights.append("High engagement rate suggests strong content-market fit")
        elif avg_like_ratio < 0.01:
            insights.append("Low engagement rate indicates need for content optimization")
        
        return insights
    
    def _generate_recommendations(self, patterns: Dict[str, Any], insights: List[str]) -> List[str]:
        """Generate specific optimization recommendations."""
        recommendations = []
        
        # Tag recommendations
        if patterns['successful_tags']['top_performing_tags']:
            top_tags = list(patterns['successful_tags']['top_performing_tags'].keys())[:3]
            recommendations.append(f"Prioritize tags: {', '.join(top_tags)}")
        
        # Timing recommendations
        if patterns['optimal_timing']['best_hours']:
            best_hours = list(patterns['optimal_timing']['best_hours'].keys())[:2]
            recommendations.append(f"Schedule posts during peak hours: {', '.join(best_hours)}")
        
        # Title recommendations
        optimal_length = patterns['title_patterns']['optimal_title_length']['average']
        recommendations.append(f"Target title length around {optimal_length:.0f} characters")
        
        # Platform recommendations
        if patterns['platform_preferences']:
            best_platform = max(patterns['platform_preferences'], 
                              key=lambda x: patterns['platform_preferences'][x]['avg_performance'])
            recommendations.append(f"Focus optimization efforts on {best_platform} platform")
        
        return recommendations
    
    def get_pattern_update(self) -> Optional[Dict[str, Any]]:
        """Get updated patterns if analysis is stale."""
        now = datetime.now()
        
        if (self.analysis_timestamp is None or 
            (now - self.analysis_timestamp).total_seconds() > 3600):  # 1 hour cache
            
            patterns = self.analyze_performance_patterns()
            if 'error' not in patterns:
                self.pattern_cache = patterns
                self.analysis_timestamp = now
                return patterns
        
        return self.pattern_cache if self.pattern_cache else None