"""
Performance Tracker

Tracks and analyzes performance metrics for A/B test variations.
Supports multiple platforms and metrics collection.
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics tracked in A/B tests."""
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    LIKES = "likes"
    SHARES = "shares"
    COMMENTS = "comments"
    ENGAGEMENT_RATE = "engagement_rate"
    CONVERSION_RATE = "conversion_rate"
    REVENUE = "revenue"
    WATCH_TIME = "watch_time"
    SUBSCRIBERS = "subscribers"
    CTR = "click_through_rate"

@dataclass
class PerformanceMetric:
    """Represents a single performance metric."""
    metric_id: str
    variation_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    platform: str
    additional_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

class PerformanceTracker:
    """Tracks performance metrics for A/B test variations."""
    
    def __init__(self, storage_backend: Optional[Any] = None):
        """Initialize the performance tracker."""
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.variation_metrics: Dict[str, List[str]] = {}  # variation_id -> metric_ids
        self.aggregated_metrics: Dict[str, Dict[str, float]] = {}  # variation_id -> aggregated_metrics
        self.storage_backend = storage_backend
        self.platform_adapters = {}  # platform -> adapter instance
        
        # Load existing metrics
        self._load_existing_metrics()
    
    def register_platform_adapter(self, platform: str, adapter):
        """Register a platform adapter for metric collection."""
        self.platform_adapters[platform] = adapter
        logger.info(f"Registered platform adapter for {platform}")
    
    def track_metric(
        self,
        variation_id: str,
        metric_type: MetricType,
        value: float,
        platform: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track a single performance metric."""
        metric_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        metric = PerformanceMetric(
            metric_id=metric_id,
            variation_id=variation_id,
            metric_type=metric_type,
            value=value,
            timestamp=timestamp,
            platform=platform,
            additional_data=additional_data
        )
        
        self.metrics[metric_id] = metric
        
        if variation_id not in self.variation_metrics:
            self.variation_metrics[variation_id] = []
        self.variation_metrics[variation_id].append(metric_id)
        
        # Update aggregated metrics
        self._update_aggregated_metrics(variation_id)
        
        # Save metric
        self._save_metric(metric)
        
        logger.debug(f"Tracked metric {metric_type.value} = {value} for variation {variation_id}")
        return metric_id
    
    def batch_track_metrics(self, metrics_data: List[Dict[str, Any]]) -> List[str]:
        """Track multiple metrics at once."""
        metric_ids = []
        
        for data in metrics_data:
            metric_id = self.track_metric(
                variation_id=data["variation_id"],
                metric_type=MetricType(data["metric_type"]),
                value=data["value"],
                platform=data["platform"],
                additional_data=data.get("additional_data")
            )
            metric_ids.append(metric_id)
        
        return metric_ids
    
    def get_variation_metrics(
        self,
        variation_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceMetric]:
        """Get all metrics for a variation within time range."""
        metric_ids = self.variation_metrics.get(variation_id, [])
        variation_metrics = []
        
        for metric_id in metric_ids:
            metric = self.metrics[metric_id]
            
            # Filter by time range if specified
            if start_time and metric.timestamp < start_time:
                continue
            if end_time and metric.timestamp > end_time:
                continue
                
            variation_metrics.append(metric)
        
        return variation_metrics
    
    def get_aggregated_metrics(
        self,
        variation_id: str,
        metric_types: Optional[List[MetricType]] = None
    ) -> Dict[str, float]:
        """Get aggregated metrics for a variation."""
        metrics = self.get_variation_metrics(variation_id)
        
        if not metrics:
            return {}
        
        # Filter by metric types if specified
        if metric_types:
            metrics = [m for m in metrics if m.metric_type in metric_types]
        
        # Aggregate metrics
        aggregated = {}
        for metric in metrics:
            metric_key = metric.metric_type.value
            
            if metric_key not in aggregated:
                aggregated[metric_key] = []
            aggregated[metric_key].append(metric.value)
        
        # Calculate statistics
        result = {}
        for metric_key, values in aggregated.items():
            if len(values) > 0:
                result[f"{metric_key}_total"] = sum(values)
                result[f"{metric_key}_average"] = sum(values) / len(values)
                result[f"{metric_key}_count"] = len(values)
        
        # Add calculated metrics
        if MetricType.IMPRESSIONS.value in aggregated and MetricType.CLICKS.value in aggregated:
            impressions = sum(aggregated[MetricType.IMPRESSIONS.value])
            clicks = sum(aggregated[MetricType.CLICKS.value])
            if impressions > 0:
                result["click_through_rate"] = (clicks / impressions) * 100
        
        if (MetricType.LIKES.value in aggregated and 
            MetricType.COMMENTS.value in aggregated and 
            MetricType.SHARES.value in aggregated and
            MetricType.IMPRESSIONS.value in aggregated):
            
            likes = sum(aggregated[MetricType.LIKES.value])
            comments = sum(aggregated[MetricType.COMMENTS.value])
            shares = sum(aggregated[MetricType.SHARES.value])
            impressions = sum(aggregated[MetricType.IMPRESSIONS.value])
            
            if impressions > 0:
                engagement_rate = ((likes + comments + shares) / impressions) * 100
                result["engagement_rate"] = engagement_rate
        
        return result
    
    def get_comparison_metrics(
        self,
        variation_ids: List[str],
        metric_types: Optional[List[MetricType]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Get aggregated metrics for multiple variations for comparison."""
        comparison = {}
        
        for variation_id in variation_ids:
            metrics = self.get_aggregated_metrics(variation_id, metric_types)
            comparison[variation_id] = metrics
        
        return comparison
    
    def collect_metrics_from_platform(self, platform: str, variation_ids: List[str]):
        """Collect metrics from a specific platform."""
        if platform not in self.platform_adapters:
            logger.warning(f"No adapter registered for platform {platform}")
            return
        
        adapter = self.platform_adapters[platform]
        
        for variation_id in variation_ids:
            try:
                # Get platform-specific metrics
                platform_metrics = adapter.get_metrics(variation_id)
                
                # Track each metric
                for metric_data in platform_metrics:
                    self.track_metric(
                        variation_id=variation_id,
                        metric_type=MetricType(metric_data["metric_type"]),
                        value=metric_data["value"],
                        platform=platform,
                        additional_data=metric_data.get("additional_data")
                    )
                    
            except Exception as e:
                logger.error(f"Error collecting metrics from {platform}: {e}")
    
    def schedule_metric_collection(self, platform: str, variation_ids: List[str], interval_minutes: int = 60):
        """Schedule automatic metric collection from platform."""
        # In a real implementation, this would set up a background task
        logger.info(f"Scheduled metric collection for {platform} every {interval_minutes} minutes")
        
        # For now, we'll collect immediately
        self.collect_metrics_from_platform(platform, variation_ids)
    
    def get_experiment_performance_summary(self, experiment_id: str) -> Dict[str, Any]:
        """Get performance summary for an entire experiment."""
        # This would typically get all variations for the experiment
        # For now, assume experiment_id is the variation_id
        variation_id = experiment_id
        
        metrics = self.get_aggregated_metrics(variation_id)
        
        summary = {
            "variation_id": variation_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        
        # Add calculated performance indicators
        if "engagement_rate" in metrics:
            if metrics["engagement_rate"] >= 5.0:
                summary["performance_level"] = "excellent"
            elif metrics["engagement_rate"] >= 3.0:
                summary["performance_level"] = "good"
            elif metrics["engagement_rate"] >= 1.0:
                summary["performance_level"] = "average"
            else:
                summary["performance_level"] = "poor"
        
        if "click_through_rate" in metrics:
            if metrics["click_through_rate"] >= 3.0:
                summary["click_performance"] = "high"
            elif metrics["click_through_rate"] >= 1.5:
                summary["click_performance"] = "medium"
            else:
                summary["click_performance"] = "low"
        
        return summary
    
    def export_metrics(
        self,
        variation_ids: List[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export metrics for analysis."""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "variations": {},
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            }
        }
        
        for variation_id in variation_ids:
            metrics = self.get_variation_metrics(variation_id, start_time, end_time)
            
            export_data["variations"][variation_id] = {
                "raw_metrics": [metric.to_dict() for metric in metrics],
                "aggregated_metrics": self.get_aggregated_metrics(variation_id)
            }
        
        return export_data
    
    def _update_aggregated_metrics(self, variation_id: str):
        """Update aggregated metrics for a variation."""
        aggregated = self.get_aggregated_metrics(variation_id)
        self.aggregated_metrics[variation_id] = aggregated
    
    def _save_metric(self, metric: PerformanceMetric):
        """Save metric to storage backend."""
        if self.storage_backend:
            # Implementation depends on storage backend
            pass
        # For now, just log
        logger.debug(f"Saved metric {metric.metric_id}")
    
    def _load_existing_metrics(self):
        """Load existing metrics from storage."""
        # Implementation for loading from storage backend
        logger.debug("Loading existing metrics")

class PlatformAdapter:
    """Base class for platform-specific metric collection adapters."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    def get_metrics(self, variation_id: str) -> List[Dict[str, Any]]:
        """Get metrics from the platform for a variation."""
        raise NotImplementedError
    
    def authenticate(self, credentials: Dict[str, Any]):
        """Authenticate with the platform."""
        raise NotImplementedError

# Example platform adapters
class YouTubeAdapter(PlatformAdapter):
    """YouTube-specific metric collection adapter."""
    
    def __init__(self):
        super().__init__("youtube")
    
    def get_metrics(self, variation_id: str) -> List[Dict[str, Any]]:
        """Get YouTube metrics for a variation."""
        # This would integrate with YouTube Analytics API
        # For now, return mock data
        return [
            {
                "metric_type": "impressions",
                "value": 1000,
                "additional_data": {"video_id": variation_id}
            },
            {
                "metric_type": "clicks",
                "value": 50,
                "additional_data": {"video_id": variation_id}
            }
        ]

class TikTokAdapter(PlatformAdapter):
    """TikTok-specific metric collection adapter."""
    
    def __init__(self):
        super().__init__("tiktok")
    
    def get_metrics(self, variation_id: str) -> List[Dict[str, Any]]:
        """Get TikTok metrics for a variation."""
        # This would integrate with TikTok Analytics API
        # For now, return mock data
        return [
            {
                "metric_type": "impressions",
                "value": 2000,
                "additional_data": {"video_id": variation_id}
            },
            {
                "metric_type": "engagement_rate",
                "value": 4.5,
                "additional_data": {"video_id": variation_id}
            }
        ]

class InstagramAdapter(PlatformAdapter):
    """Instagram-specific metric collection adapter."""
    
    def __init__(self):
        super().__init__("instagram")
    
    def get_metrics(self, variation_id: str) -> List[Dict[str, Any]]:
        """Get Instagram metrics for a variation."""
        # This would integrate with Instagram Insights API
        # For now, return mock data
        return [
            {
                "metric_type": "impressions",
                "value": 1500,
                "additional_data": {"post_id": variation_id}
            },
            {
                "metric_type": "likes",
                "value": 75,
                "additional_data": {"post_id": variation_id}
            }
        ]
