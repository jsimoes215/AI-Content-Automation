"""
Feedback Processor Module

Processes user feedback and engagement metrics to identify optimization opportunities.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics
import re


class FeedbackProcessor:
    """Processes various types of feedback to identify optimization signals."""
    
    def __init__(self, db_path: str = "data/content_creator.db"):
        self.db_path = db_path
        self.feedback_cache = {}
        self.sentiment_cache = {}
        
    def process_feedback_data(self, 
                            content_id: Optional[str] = None,
                            days_back: int = 30) -> Dict[str, Any]:
        """
        Process feedback data for content optimization.
        
        Args:
            content_id: Specific content to analyze (optional)
            days_back: Number of days to look back
            
        Returns:
            Dictionary containing processed feedback insights
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            feedback_data = self._collect_feedback_data(cutoff_date, content_id)
            
            if not feedback_data:
                return {"error": "No feedback data available"}
            
            processed_feedback = {
                'sentiment_analysis': self._analyze_sentiment(feedback_data),
                'engagement_patterns': self._analyze_engagement_patterns(feedback_data),
                'comment_analysis': self._analyze_comments(feedback_data),
                'performance_trends': self._analyze_performance_trends(feedback_data),
                'optimization_signals': self._extract_optimization_signals(feedback_data)
            }
            
            return {
                'analysis_date': datetime.now().isoformat(),
                'feedback_count': len(feedback_data),
                'processed_data': processed_feedback,
                'actionable_insights': self._generate_actionable_insights(processed_feedback)
            }
            
        except Exception as e:
            return {"error": f"Feedback processing failed: {str(e)}"}
    
    def _collect_feedback_data(self, cutoff_date: datetime, content_id: Optional[str]) -> List[Dict]:
        """Collect feedback data from multiple sources."""
        feedback_data = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get content items
                query = """
                SELECT content_id, content_type, title, metrics_views, metrics_likes,
                       metrics_comments, metrics_shares, performance_score, created_at
                FROM content_items 
                WHERE created_at >= ?
                """
                params = [cutoff_date.isoformat()]
                
                if content_id:
                    query += " AND content_id = ?"
                    params.append(content_id)
                
                cursor.execute(query, params)
                content_rows = cursor.fetchall()
                
                # Get engagement data (comments, reactions, etc.)
                engagement_query = """
                SELECT content_id, reaction_type, comment_text, sentiment_score,
                       engagement_timestamp, user_feedback
                FROM engagement_data 
                WHERE engagement_timestamp >= ?
                """
                engagement_params = [cutoff_date.isoformat()]
                
                cursor.execute(engagement_query, engagement_params)
                engagement_rows = cursor.fetchall()
                
                # Combine data
                content_map = {}
                for row in content_rows:
                    content_id = row[0]
                    content_map[content_id] = {
                        'content_id': content_id,
                        'content_type': row[1],
                        'title': row[2],
                        'metrics_views': row[3] or 0,
                        'metrics_likes': row[4] or 0,
                        'metrics_comments': row[5] or 0,
                        'metrics_shares': row[6] or 0,
                        'performance_score': row[7] or 0,
                        'created_at': row[8],
                        'engagement_data': []
                    }
                
                # Add engagement data
                for row in engagement_rows:
                    content_id = row[0]
                    if content_id in content_map:
                        content_map[content_id]['engagement_data'].append({
                            'reaction_type': row[1],
                            'comment_text': row[2],
                            'sentiment_score': row[3] or 0,
                            'engagement_timestamp': row[4],
                            'user_feedback': row[5]
                        })
                
                feedback_data = list(content_map.values())
                
        except sqlite3.OperationalError:
            # If engagement_data table doesn't exist, create mock data
            feedback_data = self._generate_mock_feedback_data(cutoff_date, content_id)
        
        return feedback_data
    
    def _generate_mock_feedback_data(self, cutoff_date: datetime, content_id: Optional[str]) -> List[Dict]:
        """Generate mock feedback data for testing."""
        # This is for demonstration - replace with actual data collection
        base_date = cutoff_date
        
        mock_data = []
        for i in range(10):
            content_date = base_date + timedelta(days=i)
            mock_content = {
                'content_id': f"content_{i}",
                'content_type': 'video' if i % 2 == 0 else 'text',
                'title': f"Sample Content {i}",
                'metrics_views': 100 + i * 50,
                'metrics_likes': 10 + i * 5,
                'metrics_comments': 2 + i,
                'metrics_shares': 1 + i // 2,
                'performance_score': 0.3 + i * 0.05,
                'created_at': content_date.isoformat(),
                'engagement_data': [
                    {
                        'reaction_type': 'like',
                        'comment_text': 'Great content!' if i % 3 == 0 else 'Could be better',
                        'sentiment_score': 0.8 if i % 3 == 0 else -0.2,
                        'engagement_timestamp': (content_date + timedelta(hours=1)).isoformat(),
                        'user_feedback': 'positive' if i % 3 == 0 else 'neutral'
                    }
                ]
            }
            mock_data.append(mock_content)
        
        return mock_data
    
    def _analyze_sentiment(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment patterns in feedback."""
        positive_scores = []
        negative_scores = []
        neutral_scores = []
        sentiment_keywords = defaultdict(list)
        
        for content in feedback_data:
            for engagement in content['engagement_data']:
                sentiment = engagement.get('sentiment_score', 0)
                
                if sentiment > 0.3:
                    positive_scores.append(sentiment)
                elif sentiment < -0.3:
                    negative_scores.append(sentiment)
                else:
                    neutral_scores.append(sentiment)
                
                # Extract keywords from positive/negative comments
                comment = engagement.get('comment_text', '').lower()
                words = re.findall(r'\b\w+\b', comment)
                
                if sentiment > 0.3:
                    sentiment_keywords['positive'].extend(words)
                elif sentiment < -0.3:
                    sentiment_keywords['negative'].extend(words)
        
        # Count most common words
        positive_words = dict(Counter(sentiment_keywords['positive']).most_common(10))
        negative_words = dict(Counter(sentiment_keywords['negative']).most_common(10))
        
        return {
            'overall_sentiment': {
                'positive_percentage': len(positive_scores) / len(feedback_data) * 100 if feedback_data else 0,
                'negative_percentage': len(negative_scores) / len(feedback_data) * 100 if feedback_data else 0,
                'neutral_percentage': len(neutral_scores) / len(feedback_data) * 100 if feedback_data else 0,
                'average_score': statistics.mean([s for sublist in [positive_scores, negative_scores, neutral_scores] for s in sublist]) if feedback_data else 0
            },
            'positive_keywords': positive_words,
            'negative_keywords': negative_words,
            'sentiment_trend': self._calculate_sentiment_trend(feedback_data),
            'high_impact_content': self._identify_high_impact_content(feedback_data, 'positive'),
            'problematic_content': self._identify_high_impact_content(feedback_data, 'negative')
        }
    
    def _analyze_engagement_patterns(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement patterns across content."""
        engagement_by_time = defaultdict(list)
        engagement_by_type = defaultdict(list)
        peak_engagement_periods = []
        
        for content in feedback_data:
            created_time = datetime.fromisoformat(content['created_at'])
            hour = created_time.hour
            weekday = created_time.weekday()
            
            # Calculate engagement rate
            views = content['metrics_views']
            if views > 0:
                engagement_rate = (content['metrics_likes'] + content['metrics_comments']) / views
                engagement_by_time[f"{hour:02d}:00"].append(engagement_rate)
                weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                engagement_by_time[weekday_names[weekday]].append(engagement_rate)
                engagement_by_type[content['content_type']].append(engagement_rate)
        
        # Find peak engagement periods
        for period, rates in engagement_by_time.items():
            if rates:
                avg_rate = statistics.mean(rates)
                peak_engagement_periods.append((period, avg_rate))
        
        peak_engagement_periods.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'best_engagement_times': dict(peak_engagement_periods[:5]),
            'engagement_by_content_type': {k: statistics.mean(v) for k, v in engagement_by_type.items() if v},
            'engagement_volatility': statistics.stdev([rate for sublist in engagement_by_time.values() for rate in sublist]) if len(engagement_by_time) > 1 else 0,
            'high_engagement_threshold': statistics.quantiles([rate for sublist in engagement_by_time.values() for rate in sublist], n=4)[-1] if engagement_by_time else 0
        }
    
    def _analyze_comments(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze comment patterns and content."""
        comment_themes = defaultdict(int)
        question_patterns = []
        suggestion_patterns = []
        complaint_patterns = []
        
        for content in feedback_data:
            for engagement in content['engagement_data']:
                comment = engagement.get('comment_text', '').lower()
                
                # Identify question patterns
                if '?' in comment:
                    question_patterns.append(comment)
                
                # Identify suggestion patterns
                if any(word in comment for word in ['should', 'could', 'would', 'suggest', 'recommend']):
                    suggestion_patterns.append(comment)
                
                # Identify complaint patterns
                if any(word in comment for word in ['bad', 'terrible', 'awful', 'hate', 'boring', 'disappointing']):
                    complaint_patterns.append(comment)
                
                # Extract themes (simplified keyword extraction)
                words = re.findall(r'\b\w+\b', comment)
                for word in words:
                    if len(word) > 3 and word not in ['this', 'that', 'with', 'have', 'will', 'they', 'them', 'from']:
                        comment_themes[word] += 1
        
        top_themes = dict(Counter(comment_themes).most_common(15))
        
        return {
            'comment_themes': top_themes,
            'question_frequency': len(question_patterns),
            'suggestion_frequency': len(suggestion_patterns),
            'complaint_frequency': len(complaint_patterns),
            'avg_comment_length': statistics.mean([len(comment) for content in feedback_data for engagement in content['engagement_data'] for comment in [engagement.get('comment_text', '')]]) if feedback_data else 0,
            'engagement_ratio': len([content for content in feedback_data if content['metrics_comments'] > 0]) / len(feedback_data) if feedback_data else 0
        }
    
    def _analyze_performance_trends(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not feedback_data:
            return {}
        
        # Sort by creation date
        sorted_data = sorted(feedback_data, key=lambda x: x['created_at'])
        
        scores = [content['performance_score'] for content in sorted_data]
        views = [content['metrics_views'] for content in sorted_data]
        likes = [content['metrics_likes'] for content in sorted_data]
        
        # Calculate trends
        performance_trend = self._calculate_trend(scores)
        view_trend = self._calculate_trend(views)
        engagement_trend = self._calculate_trend([like/view if view > 0 else 0 for like, view in zip(likes, views)])
        
        return {
            'performance_trend': performance_trend,
            'view_trend': view_trend,
            'engagement_trend': engagement_trend,
            'volatility': {
                'performance': statistics.stdev(scores) if len(scores) > 1 else 0,
                'views': statistics.stdev(views) if len(views) > 1 else 0
            },
            'improvement_rate': (scores[-1] - scores[0]) / len(scores) if len(scores) > 1 else 0,
            'best_performing_period': self._identify_best_period(sorted_data)
        }
    
    def _extract_optimization_signals(self, feedback_data: List[Dict]) -> List[Dict]:
        """Extract specific optimization signals from feedback."""
        signals = []
        
        for content in feedback_data:
            content_signals = []
            
            # Low engagement signal
            if content['metrics_views'] > 0:
                engagement_rate = (content['metrics_likes'] + content['metrics_comments']) / content['metrics_views']
                if engagement_rate < 0.01:  # Less than 1% engagement
                    content_signals.append({
                        'type': 'low_engagement',
                        'severity': 'high' if engagement_rate < 0.005 else 'medium',
                        'content_id': content['content_id'],
                        'recommendation': 'Improve content hook and engagement elements'
                    })
            
            # High negative sentiment signal
            negative_count = len([eng for eng in content['engagement_data'] 
                                if eng.get('sentiment_score', 0) < -0.3])
            if negative_count > len(content['engagement_data']) * 0.3:  # More than 30% negative
                content_signals.append({
                    'type': 'negative_feedback',
                    'severity': 'high' if negative_count > len(content['engagement_data']) * 0.5 else 'medium',
                    'content_id': content['content_id'],
                    'recommendation': 'Review content approach and messaging'
                })
            
            # High performance signal
            if content['performance_score'] > 0.8:
                content_signals.append({
                    'type': 'high_performance',
                    'severity': 'positive',
                    'content_id': content['content_id'],
                    'recommendation': 'Analyze successful elements for replication'
                })
            
            signals.extend(content_signals)
        
        return signals
    
    def _generate_actionable_insights(self, processed_feedback: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from processed feedback."""
        insights = []
        
        sentiment_data = processed_feedback.get('sentiment_analysis', {})
        if sentiment_data:
            pos_pct = sentiment_data.get('overall_sentiment', {}).get('positive_percentage', 0)
            if pos_pct < 30:
                insights.append("High negative sentiment detected - review content quality and messaging")
            elif pos_pct > 70:
                insights.append("Strong positive sentiment - maintain current content approach")
        
        engagement_data = processed_feedback.get('engagement_patterns', {})
        if engagement_data:
            best_times = list(engagement_data.get('best_engagement_times', {}).keys())[:2]
            if best_times:
                insights.append(f"Peak engagement occurs during: {', '.join(best_times)}")
        
        optimization_signals = processed_feedback.get('optimization_signals', [])
        high_priority_signals = [s for s in optimization_signals if s.get('severity') == 'high']
        if high_priority_signals:
            insights.append(f"{len(high_priority_signals)} high-priority optimization signals detected")
        
        return insights
    
    def _calculate_sentiment_trend(self, feedback_data: List[Dict]) -> str:
        """Calculate overall sentiment trend."""
        sentiment_scores = []
        for content in feedback_data:
            for engagement in content['engagement_data']:
                sentiment_scores.append(engagement.get('sentiment_score', 0))
        
        if not sentiment_scores:
            return "no_data"
        
        recent_avg = statistics.mean(sentiment_scores[-5:]) if len(sentiment_scores) >= 5 else statistics.mean(sentiment_scores)
        early_avg = statistics.mean(sentiment_scores[:5]) if len(sentiment_scores) >= 10 else recent_avg
        
        if recent_avg > early_avg + 0.1:
            return "improving"
        elif recent_avg < early_avg - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _identify_high_impact_content(self, feedback_data: List[Dict], sentiment_type: str) -> List[Dict]:
        """Identify content with high impact (positive or negative)."""
        threshold = 0.7 if sentiment_type == 'positive' else -0.7
        
        high_impact = []
        for content in feedback_data:
            for engagement in content['engagement_data']:
                sentiment = engagement.get('sentiment_score', 0)
                if (sentiment_type == 'positive' and sentiment > threshold) or \
                   (sentiment_type == 'negative' and sentiment < threshold):
                    high_impact.append({
                        'content_id': content['content_id'],
                        'title': content['title'],
                        'sentiment_score': sentiment,
                        'comment': engagement.get('comment_text', '')
                    })
        
        return sorted(high_impact, key=lambda x: x['sentiment_score'], reverse=(sentiment_type == 'positive'))
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and strength."""
        if len(values) < 2:
            return {"direction": "no_data", "strength": 0}
        
        # Simple linear regression slope
        n = len(values)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        
        direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        
        return {
            "direction": direction,
            "strength": abs(slope),
            "slope": slope
        }
    
    def _identify_best_period(self, feedback_data: List[Dict]) -> str:
        """Identify the best performing time period."""
        if not feedback_data:
            return "no_data"
        
        # Group by week and find best week
        weekly_performance = defaultdict(list)
        
        for content in feedback_data:
            created_date = datetime.fromisoformat(content['created_at'])
            week_key = f"{created_date.year}-W{created_date.isocalendar()[1]}"
            weekly_performance[week_key].append(content['performance_score'])
        
        if not weekly_performance:
            return "no_data"
        
        avg_performance = {week: statistics.mean(scores) for week, scores in weekly_performance.items()}
        best_week = max(avg_performance, key=avg_performance.get)
        
        return best_week