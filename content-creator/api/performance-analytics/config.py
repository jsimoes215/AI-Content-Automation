"""
Performance Analytics Configuration

Configuration settings and defaults for the performance analytics system.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class AnalyticsConfig:
    """Configuration class for performance analytics system"""
    
    # Database settings
    DB_POOL_SIZE = 20
    DB_POOL_TIMEOUT = 30
    DB_POOL_MAX_OVERFLOW = 10
    
    # Cache settings
    CACHE_TTL_SECONDS = 300  # 5 minutes
    CACHE_MAX_SIZE = 1000
    
    # Analytics settings
    DEFAULT_ANALYSIS_PERIOD_DAYS = 90
    MIN_DATA_POINTS_FOR_ANALYSIS = 10
    ANOMALY_DETECTION_THRESHOLD = 2.0
    
    # Correlation analysis settings
    CORRELATION_SIGNIFICANCE_THRESHOLD = 0.05
    MIN_CORRELATION_STRENGTH = 0.3
    
    # Trend analysis settings
    TREND_ANALYSIS_MIN_PERIOD_DAYS = 7
    TREND_FORECAST_DAYS = 30
    TREND_CONFIDENCE_THRESHOLD = 0.1
    
    # Platform settings
    SUPPORTED_PLATFORMS = [
        'youtube', 'tiktok', 'instagram', 'linkedin', 'twitter'
    ]
    
    # Performance thresholds
    LOW_PERFORMANCE_THRESHOLD = 3.0
    HIGH_PERFORMANCE_THRESHOLD = 8.0
    LOW_ENGAGEMENT_THRESHOLD = 0.02  # 2%
    HIGH_ENGAGEMENT_THRESHOLD = 0.10  # 10%
    
    # Optimization settings
    MAX_OPTIMIZATION_INSIGHTS = 20
    INSIGHT_CONFIDENCE_THRESHOLD = 0.6
    IMPLEMENTATION_DIFFICULTY_WEIGHTS = {
        'easy': 1.0,
        'medium': 0.7,
        'hard': 0.4
    }
    
    # Data retention settings
    ENGAGEMENT_DATA_RETENTION_DAYS = 365
    TREND_DATA_RETENTION_DAYS = 180
    OPTIMIZATION_INSIGHTS_RETENTION_DAYS = 90
    
    # Export settings
    EXPORT_BATCH_SIZE = 1000
    MAX_EXPORT_RECORDS = 10000
    
    @classmethod
    def get_platform_config(cls, platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        
        configs = {
            'youtube': {
                'metrics_to_track': ['views', 'likes', 'comments', 'shares', 'watch_time', 'engagement_rate'],
                'update_frequency_minutes': 60,
                'benchmark_engagement_rate': 0.04,
                'peak_posting_hours': [10, 14, 20],
                'content_types': ['video', 'short', 'live'],
                'trending_threshold_multiplier': 1.2
            },
            'tiktok': {
                'metrics_to_track': ['views', 'likes', 'comments', 'shares', 'saves', 'engagement_rate'],
                'update_frequency_minutes': 30,
                'benchmark_engagement_rate': 0.08,
                'peak_posting_hours': [9, 12, 19],
                'content_types': ['video', 'live'],
                'trending_threshold_multiplier': 1.5
            },
            'instagram': {
                'metrics_to_track': ['views', 'likes', 'comments', 'shares', 'saves', 'engagement_rate'],
                'update_frequency_minutes': 45,
                'benchmark_engagement_rate': 0.06,
                'peak_posting_hours': [11, 14, 20],
                'content_types': ['image', 'video', 'story', 'reel'],
                'trending_threshold_multiplier': 1.3
            },
            'linkedin': {
                'metrics_to_track': ['views', 'likes', 'comments', 'shares', 'engagement_rate', 'click_through_rate'],
                'update_frequency_minutes': 120,
                'benchmark_engagement_rate': 0.03,
                'peak_posting_hours': [8, 12, 17],
                'content_types': ['article', 'video', 'image'],
                'trending_threshold_multiplier': 1.1
            },
            'twitter': {
                'metrics_to_track': ['views', 'likes', 'comments', 'shares', 'engagement_rate'],
                'update_frequency_minutes': 30,
                'benchmark_engagement_rate': 0.02,
                'peak_posting_hours': [9, 12, 17, 21],
                'content_types': ['text', 'image', 'video', 'thread'],
                'trending_threshold_multiplier': 1.4
            }
        }
        
        return configs.get(platform, configs['youtube'])  # Default to YouTube config
    
    @classmethod
    def get_metric_config(cls, metric_name: str) -> Dict[str, Any]:
        """Get configuration for specific metrics"""
        
        configs = {
            'views': {
                'weight': 1.0,
                'display_format': 'integer',
                'range': (0, 10000000),
                'update_frequency': 'real-time'
            },
            'engagement_rate': {
                'weight': 2.0,
                'display_format': 'percentage',
                'range': (0, 1),
                'update_frequency': 'hourly'
            },
            'performance_score': {
                'weight': 3.0,
                'display_format': 'float',
                'range': (0, 10),
                'update_frequency': 'daily'
            },
            'watch_time': {
                'weight': 1.5,
                'display_format': 'duration',
                'range': (0, 86400),  # seconds
                'update_frequency': 'hourly'
            },
            'click_through_rate': {
                'weight': 2.5,
                'display_format': 'percentage',
                'range': (0, 1),
                'update_frequency': 'hourly'
            }
        }
        
        return configs.get(metric_name, configs['engagement_rate'])
    
    @classmethod
    def get_correlation_feature_config(cls) -> Dict[str, Any]:
        """Get configuration for correlation analysis features"""
        
        return {
            'duration': {
                'type': 'continuous',
                'weight': 1.0,
                'description': 'Content duration in seconds',
                'optimization_tip': 'Optimize length based on platform and audience preferences'
            },
            'video_quality': {
                'type': 'continuous',
                'weight': 1.2,
                'description': 'Video quality score (1-10)',
                'optimization_tip': 'Higher quality generally improves engagement'
            },
            'tone': {
                'type': 'categorical',
                'weight': 0.8,
                'description': 'Content tone (professional, casual, etc.)',
                'optimization_tip': 'Match tone to target audience and platform culture'
            },
            'scene_count': {
                'type': 'continuous',
                'weight': 0.9,
                'description': 'Number of scenes in content',
                'optimization_tip': 'Balance visual variety with narrative flow'
            },
            'target_audience': {
                'type': 'categorical',
                'weight': 1.1,
                'description': 'Intended audience demographic',
                'optimization_tip': 'Customize content style for specific audience segments'
            }
        }
    
    @classmethod
    def get_insight_config(cls) -> Dict[str, Any]:
        """Get configuration for optimization insights"""
        
        return {
            'feature_optimization': {
                'priority_weights': {
                    'high': 3.0,
                    'medium': 2.0,
                    'low': 1.0
                },
                'min_correlation_strength': 0.3,
                'max_insights': 10
            },
            'timing_optimization': {
                'priority_weights': {
                    'high': 2.5,
                    'medium': 1.5,
                    'low': 1.0
                },
                'min_seasonal_reliability': 0.6,
                'max_insights': 5
            },
            'content_strategy': {
                'priority_weights': {
                    'high': 2.8,
                    'medium': 1.8,
                    'low': 1.0
                },
                'min_performance_gap': 0.2,
                'max_insights': 8
            }
        }
    
    @classmethod
    def get_dashboard_config(cls) -> Dict[str, Any]:
        """Get configuration for dashboard display"""
        
        return {
            'default_timeframe': '30d',
            'available_timeframes': ['7d', '30d', '90d', '1y'],
            'default_platforms': ['youtube', 'tiktok', 'instagram'],
            'metrics_per_page': 20,
            'chart_update_interval': 60,  # seconds
            'real_time_metrics': ['views', 'likes', 'engagement_rate'],
            'cached_metrics': ['performance_score', 'watch_time', 'sentiment_score']
        }


# Environment-specific configurations
class DevelopmentConfig(AnalyticsConfig):
    """Development environment configuration"""
    
    CACHE_TTL_SECONDS = 60  # Shorter cache for development
    MIN_DATA_POINTS_FOR_ANALYSIS = 5  # Less strict for testing
    CORRELATION_SIGNIFICANCE_THRESHOLD = 0.1  # More relaxed for development


class ProductionConfig(AnalyticsConfig):
    """Production environment configuration"""
    
    CACHE_TTL_SECONDS = 300  # 5 minutes
    MIN_DATA_POINTS_FOR_ANALYSIS = 10
    CORRELATION_SIGNIFICANCE_THRESHOLD = 0.05
    DB_POOL_SIZE = 50
    DB_POOL_MAX_OVERFLOW = 20


class TestingConfig(AnalyticsConfig):
    """Testing environment configuration"""
    
    CACHE_TTL_SECONDS = 10  # Very short cache for tests
    MIN_DATA_POINTS_FOR_ANALYSIS = 3
    CORRELATION_SIGNIFICANCE_THRESHOLD = 0.2
    ANOMALY_DETECTION_THRESHOLD = 3.0  # More strict for tests


def get_config_for_environment(env: str = 'development') -> AnalyticsConfig:
    """Get appropriate configuration for environment"""
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'staging': ProductionConfig,  # Staging uses production config
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()


# Configuration validation
def validate_config(config: AnalyticsConfig) -> List[str]:
    """Validate configuration settings and return any issues"""
    
    issues = []
    
    # Validate thresholds
    if config.LOW_PERFORMANCE_THRESHOLD >= config.HIGH_PERFORMANCE_THRESHOLD:
        issues.append("LOW_PERFORMANCE_THRESHOLD must be less than HIGH_PERFORMANCE_THRESHOLD")
    
    if config.LOW_ENGAGEMENT_THRESHOLD >= config.HIGH_ENGAGEMENT_THRESHOLD:
        issues.append("LOW_ENGAGEMENT_THRESHOLD must be less than HIGH_ENGAGEMENT_THRESHOLD")
    
    # Validate correlation threshold
    if not 0 < config.CORRELATION_SIGNIFICANCE_THRESHOLD < 1:
        issues.append("CORRELATION_SIGNIFICANCE_THRESHOLD must be between 0 and 1")
    
    # Validate time periods
    if config.TREND_ANALYSIS_MIN_PERIOD_DAYS < 1:
        issues.append("TREND_ANALYSIS_MIN_PERIOD_DAYS must be at least 1")
    
    if config.TREND_FORECAST_DAYS < 1:
        issues.append("TREND_FORECAST_DAYS must be at least 1")
    
    # Validate retention periods
    if config.ENGAGEMENT_DATA_RETENTION_DAYS < 30:
        issues.append("ENGAGEMENT_DATA_RETENTION_DAYS should be at least 30 days")
    
    return issues


# Default configuration instance
default_config = get_config_for_environment()

if __name__ == "__main__":
    # Configuration validation example
    print("Performance Analytics Configuration")
    print("=" * 50)
    
    config = get_config_for_environment('development')
    issues = validate_config(config)
    
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid!")
    
    print(f"\nDefault configuration:")
    print(f"  Cache TTL: {config.CACHE_TTL_SECONDS} seconds")
    print(f"  Analysis period: {config.DEFAULT_ANALYSIS_PERIOD_DAYS} days")
    print(f"  Correlation threshold: {config.CORRELATION_SIGNIFICANCE_THRESHOLD}")
    print(f"  Supported platforms: {len(config.SUPPORTED_PLATFORMS)}")
    
    # Show platform configurations
    print(f"\nPlatform configurations:")
    for platform in config.SUPPORTED_PLATFORMS[:3]:  # Show first 3
        platform_config = config.get_platform_config(platform)
        print(f"  {platform}: engagement benchmark = {platform_config['benchmark_engagement_rate']:.3f}")