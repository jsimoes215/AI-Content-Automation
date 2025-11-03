"""
Engagement Tracker Module

Handles real-time tracking and collection of engagement metrics from various platforms.
Supports batch processing, caching, and real-time updates.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import asyncpg
import numpy as np
from scipy import stats


class MetricType(Enum):
    """Types of engagement metrics to track"""
    VIEWS = "views"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    WATCH_TIME = "watch_time"
    CLICK_THROUGH = "click_through"
    ENGAGEMENT_RATE = "engagement_rate"
    REACH = "reach"
    IMPRESSIONS = "impressions"


class Platform(Enum):
    """Supported platforms for metrics collection"""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


@dataclass
class EngagementSnapshot:
    """Snapshot of engagement metrics at a specific point in time"""
    content_id: str
    platform: Platform
    timestamp: datetime
    metrics: Dict[MetricType, float]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        data['platform'] = self.platform.value
        data['metrics'] = {k.value: v for k, v in self.metrics.items()}
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class EngagementSummary:
    """Summary of engagement metrics over a time period"""
    content_id: str
    platform: Platform
    period_start: datetime
    period_end: datetime
    total_metrics: Dict[MetricType, float]
    average_metrics: Dict[MetricType, float]
    growth_rates: Dict[MetricType, float]
    trend_direction: Dict[MetricType, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['platform'] = self.platform.value
        data['total_metrics'] = {k.value: v for k, v in self.total_metrics.items()}
        data['average_metrics'] = {k.value: v for k, v in self.average_metrics.items()}
        data['growth_rates'] = {k.value: v for k, v in self.growth_rates.items()}
        return data


class EngagementTracker:
    """Tracks and analyzes engagement metrics across platforms"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
        self._metric_cache = {}
        self._cache_duration = timedelta(minutes=5)
        
    async def track_engagement(self, snapshot: EngagementSnapshot) -> str:
        """Record a new engagement snapshot"""
        try:
            # Store in database
            query = """
            INSERT INTO engagement_snapshots 
            (content_id, platform, timestamp, metrics, metadata)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (content_id, platform, timestamp::date) 
            DO UPDATE SET 
                metrics = EXCLUDED.metrics,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING id
            """
            
            result = await self.db_pool.fetchval(
                query,
                snapshot.content_id,
                snapshot.platform.value,
                snapshot.timestamp,
                json.dumps(snapshot.metrics),
                json.dumps(snapshot.metadata)
            )
            
            # Update cache
            cache_key = f"{snapshot.content_id}:{snapshot.platform.value}"
            self._metric_cache[cache_key] = {
                'data': snapshot,
                'timestamp': datetime.now()
            }
            
            return str(result)
            
        except Exception as e:
            self.logger.error(f"Error tracking engagement: {e}")
            raise
    
    async def get_engagement_summary(
        self, 
        content_id: str,
        platform: Platform,
        period_days: int = 30
    ) -> Optional[EngagementSummary]:
        """Get engagement summary for a specific content piece over a time period"""
        
        cache_key = f"{content_id}:{platform.value}:{period_days}"
        
        # Check cache first
        if cache_key in self._metric_cache:
            cache_entry = self._metric_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < self._cache_duration:
                return cache_entry['data']
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            query = """
            SELECT timestamp, metrics 
            FROM engagement_snapshots 
            WHERE content_id = $1 
            AND platform = $2 
            AND timestamp >= $3 
            AND timestamp <= $4
            ORDER BY timestamp
            """
            
            rows = await self.db_pool.fetch(
                query, content_id, platform.value, start_date, end_date
            )
            
            if not rows:
                return None
            
            # Process metrics data
            all_metrics = {}
            timestamps = []
            
            for row in rows:
                timestamps.append(row['timestamp'])
                metrics_data = json.loads(row['metrics'])
                
                for metric_key, value in metrics_data.items():
                    if metric_key not in all_metrics:
                        all_metrics[metric_key] = []
                    all_metrics[metric_key].append(float(value))
            
            # Calculate summaries
            total_metrics = {}
            average_metrics = {}
            growth_rates = {}
            trend_directions = {}
            
            for metric_key, values in all_metrics.items():
                metric_type = MetricType(metric_key)
                total_metrics[metric_type] = sum(values)
                average_metrics[metric_type] = np.mean(values)
                
                # Calculate growth rate (linear regression slope)
                if len(values) > 1:
                    x = np.arange(len(values))
                    slope, _, r_value, p_value, _ = stats.linregress(x, values)
                    
                    growth_rates[metric_type] = slope
                    
                    # Determine trend direction
                    if p_value < 0.05:  # Statistically significant
                        if slope > 0:
                            trend_directions[metric_type] = "increasing"
                        elif slope < 0:
                            trend_directions[metric_type] = "decreasing"
                        else:
                            trend_directions[metric_type] = "stable"
                    else:
                        trend_directions[metric_type] = "stable"
                else:
                    growth_rates[metric_type] = 0
                    trend_directions[metric_type] = "stable"
            
            summary = EngagementSummary(
                content_id=content_id,
                platform=platform,
                period_start=start_date,
                period_end=end_date,
                total_metrics=total_metrics,
                average_metrics=average_metrics,
                growth_rates=growth_rates,
                trend_direction=trend_directions
            )
            
            # Cache the result
            self._metric_cache[cache_key] = {
                'data': summary,
                'timestamp': datetime.now()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting engagement summary: {e}")
            raise
    
    async def batch_track_engagement(self, snapshots: List[EngagementSnapshot]) -> List[str]:
        """Track multiple engagement snapshots in batch"""
        tasks = []
        for snapshot in snapshots:
            task = self.track_engagement(snapshot)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid IDs
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to track snapshot {i}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def get_platform_metrics(
        self, 
        platform: Platform,
        start_date: datetime,
        end_date: datetime,
        content_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get aggregated metrics for a platform over a time period"""
        
        try:
            query = """
            SELECT 
                content_id,
                DATE_TRUNC('day', timestamp) as date,
                AVG((metrics->>'views')::float) as avg_views,
                AVG((metrics->>'likes')::float) as avg_likes,
                AVG((metrics->>'comments')::float) as avg_comments,
                AVG((metrics->>'engagement_rate')::float) as avg_engagement_rate,
                SUM((metrics->>'views')::float) as total_views,
                SUM((metrics->>'likes')::float) as total_likes,
                SUM((metrics->>'comments')::float) as total_comments
            FROM engagement_snapshots 
            WHERE platform = $1 
            AND timestamp >= $2 
            AND timestamp <= $3
            """
            
            params = [platform.value, start_date, end_date]
            
            if content_ids:
                query += " AND content_id = ANY($4)"
                params.append(content_ids)
            
            query += " GROUP BY content_id, DATE_TRUNC('day', timestamp) ORDER BY date"
            
            rows = await self.db_pool.fetch(query, *params)
            
            # Process results
            daily_metrics = {}
            content_performance = {}
            
            for row in rows:
                date_str = row['date'].strftime('%Y-%m-%d')
                content_id = row['content_id']
                
                if date_str not in daily_metrics:
                    daily_metrics[date_str] = {
                        'total_views': 0,
                        'total_likes': 0,
                        'total_comments': 0,
                        'avg_engagement_rate': 0,
                        'content_count': 0
                    }
                
                daily_metrics[date_str]['total_views'] += row['total_views'] or 0
                daily_metrics[date_str]['total_likes'] += row['total_likes'] or 0
                daily_metrics[date_str]['total_comments'] += row['total_comments'] or 0
                daily_metrics[date_str]['avg_engagement_rate'] += row['avg_engagement_rate'] or 0
                daily_metrics[date_str]['content_count'] += 1
                
                # Track individual content performance
                if content_id not in content_performance:
                    content_performance[content_id] = {
                        'total_views': 0,
                        'total_likes': 0,
                        'total_comments': 0,
                        'avg_engagement_rate': 0,
                        'active_days': 0
                    }
                
                content_performance[content_id]['total_views'] += row['total_views'] or 0
                content_performance[content_id]['total_likes'] += row['total_likes'] or 0
                content_performance[content_id]['total_comments'] += row['total_comments'] or 0
                content_performance[content_id]['avg_engagement_rate'] += row['avg_engagement_rate'] or 0
                content_performance[content_id]['active_days'] += 1
            
            # Calculate averages
            for date_data in daily_metrics.values():
                if date_data['content_count'] > 0:
                    date_data['avg_engagement_rate'] /= date_data['content_count']
            
            for content_data in content_performance.values():
                if content_data['active_days'] > 0:
                    content_data['avg_engagement_rate'] /= content_data['active_days']
            
            return {
                'platform': platform.value,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'daily_metrics': daily_metrics,
                'content_performance': content_performance,
                'summary': {
                    'total_content_pieces': len(content_performance),
                    'average_daily_views': np.mean([d['total_views'] for d in daily_metrics.values()]),
                    'average_engagement_rate': np.mean([d['avg_engagement_rate'] for d in daily_metrics.values()]),
                    'best_performing_content': max(content_performance.items(), 
                                                 key=lambda x: x[1]['total_views'])[0] if content_performance else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting platform metrics: {e}")
            raise
    
    async def detect_anomalies(
        self, 
        content_id: str, 
        platform: Platform,
        metric_types: List[MetricType],
        threshold_std: float = 2.0
    ) -> Dict[str, Any]:
        """Detect anomalies in engagement metrics using statistical methods"""
        
        try:
            # Get historical data for the past 90 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            query = """
            SELECT timestamp, metrics 
            FROM engagement_snapshots 
            WHERE content_id = $1 
            AND platform = $2 
            AND timestamp >= $3 
            ORDER BY timestamp
            """
            
            rows = await self.db_pool.fetch(
                query, content_id, platform.value, start_date, end_date
            )
            
            if len(rows) < 10:  # Need minimum data points for anomaly detection
                return {'anomalies': [], 'status': 'insufficient_data'}
            
            anomalies = []
            metric_data = {mt.value: [] for mt in metric_types}
            
            # Collect historical data
            for row in rows:
                metrics_data = json.loads(row['metrics'])
                for metric_type in metric_types:
                    if metric_type.value in metrics_data:
                        metric_data[metric_type.value].append({
                            'timestamp': row['timestamp'],
                            'value': float(metrics_data[metric_type.value])
                        })
            
            # Detect anomalies for each metric
            for metric_type in metric_types:
                metric_key = metric_type.value
                if len(metric_data[metric_key]) < 10:
                    continue
                
                values = [d['value'] for d in metric_data[metric_key]]
                timestamps = [d['timestamp'] for d in metric_data[metric_key]]
                
                # Calculate z-scores
                mean_val = np.mean(values)
                std_val = np.std(values)
                
                for i, (timestamp, value) in enumerate(zip(timestamps, values)):
                    if std_val > 0:
                        z_score = abs((value - mean_val) / std_val)
                        
                        if z_score > threshold_std:
                            anomaly_type = "spike" if value > mean_val else "drop"
                            
                            anomalies.append({
                                'metric_type': metric_key,
                                'timestamp': timestamp.isoformat(),
                                'value': value,
                                'expected_value': mean_val,
                                'z_score': z_score,
                                'anomaly_type': anomaly_type,
                                'severity': 'high' if z_score > 3.0 else 'medium'
                            })
            
            return {
                'anomalies': sorted(anomalies, key=lambda x: x['z_score'], reverse=True),
                'analysis_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'total_data_points': len(rows)
                },
                'status': 'completed'
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            raise
    
    async def clear_cache(self):
        """Clear the metric cache"""
        self._metric_cache.clear()
        
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self._metric_cache),
            'cached_entries': list(self._metric_cache.keys())
        }