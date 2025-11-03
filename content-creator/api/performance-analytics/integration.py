"""
Performance Analytics Integration Module

This module provides a simple interface for integrating the performance analytics
system into the main content creation pipeline.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

import asyncpg
import logging

from .engagement_tracker import EngagementTracker, EngagementSnapshot, Platform, MetricType
from .correlation_analyzer import CorrelationAnalyzer
from .trend_analyzer import TrendAnalyzer
from .analytics_dashboard import AnalyticsDashboard, DashboardTimeframe

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceAnalyticsManager:
    """Main manager class for the performance analytics system"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.engagement_tracker = EngagementTracker(db_pool)
        self.correlation_analyzer = CorrelationAnalyzer(db_pool)
        self.trend_analyzer = TrendAnalyzer(db_pool)
        self.dashboard = AnalyticsDashboard(db_pool)
        
        logger.info("Performance Analytics Manager initialized")
    
    async def initialize_system(self):
        """Initialize the analytics system and run setup tasks"""
        logger.info("Initializing performance analytics system...")
        
        # Run any initialization tasks
        await self._setup_benchmarks()
        await self._analyze_existing_content()
        
        logger.info("Performance analytics system initialized successfully")
    
    async def _setup_benchmarks(self):
        """Set up initial performance benchmarks"""
        try:
            # This would typically fetch industry benchmarks
            # For now, we'll create some placeholder data
            platforms = ['youtube', 'tiktok', 'instagram', 'linkedin', 'twitter']
            
            for platform in platforms:
                benchmark_data = {
                    'platform': platform,
                    'average_engagement_rate': 0.05,  # 5% average
                    'median_engagement_rate': 0.03,
                    'top_10_percent_threshold': 0.15,
                    'benchmark_date': datetime.now().date()
                }
                
                # Store benchmark (this would go to the performance_benchmarks table)
                logger.info(f"Benchmark setup for {platform}: {benchmark_data['average_engagement_rate']:.3f}")
                
        except Exception as e:
            logger.error(f"Error setting up benchmarks: {e}")
    
    async def _analyze_existing_content(self):
        """Analyze existing content for initial insights"""
        try:
            # Get all content from the last 90 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            query = """
            SELECT id, platform, content_type, created_at
            FROM generated_content
            WHERE created_at >= $1 AND created_at <= $2
            ORDER BY created_at DESC
            LIMIT 100
            """
            
            rows = await self.db_pool.fetch(query, start_date, end_date)
            
            # Analyze a sample for initial insights
            sample_size = min(20, len(rows))
            sample_content = rows[:sample_size]
            
            logger.info(f"Analyzing {sample_size} existing content pieces for initial insights")
            
            # This would trigger the correlation analysis
            # For now, just log what we're doing
            for row in sample_content:
                logger.debug(f"Analyzing content {row['id']} ({row['platform']})")
            
        except Exception as e:
            logger.error(f"Error analyzing existing content: {e}")
    
    async def track_content_performance(
        self,
        content_id: str,
        platform: str,
        metrics: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track performance metrics for a content piece"""
        
        try:
            # Convert metrics to MetricType format
            metrics_dict = {}
            for key, value in metrics.items():
                try:
                    metric_type = MetricType(key)
                    metrics_dict[metric_type] = float(value)
                except ValueError:
                    logger.warning(f"Unknown metric type: {key}")
            
            # Create engagement snapshot
            snapshot = EngagementSnapshot(
                content_id=content_id,
                platform=Platform(platform),
                timestamp=datetime.now(),
                metrics=metrics_dict,
                metadata=metadata or {}
            )
            
            # Track the snapshot
            snapshot_id = await self.engagement_tracker.track_engagement(snapshot)
            
            logger.info(f"Tracked performance for content {content_id}: {metrics}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error tracking content performance: {e}")
            raise
    
    async def analyze_content_performance(
        self,
        content_id: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze performance for a specific content piece"""
        
        try:
            results = {}
            
            if analysis_type in ["comprehensive", "trend"]:
                # Analyze trends
                trend_analysis = await self.trend_analyzer.analyze_trend(
                    content_id, 'engagement_rate', time_period_days=30
                )
                if trend_analysis:
                    results['trend_analysis'] = asdict(trend_analysis)
            
            if analysis_type in ["comprehensive", "correlations"]:
                # Analyze correlations (this would need to be implemented to focus on specific content)
                logger.info(f"Correlation analysis for content {content_id} would be implemented here")
            
            if analysis_type in ["comprehensive", "anomalies"]:
                # Detect anomalies
                anomalies = await self.engagement_tracker.detect_anomalies(
                    content_id, Platform('youtube'), [MetricType.ENGAGEMENT_RATE, MetricType.VIEWS]
                )
                results['anomalies'] = anomalies
            
            # Get dashboard summary
            content_summary = await self.dashboard.get_content_performance_summary(content_id)
            results['dashboard_summary'] = asdict(content_summary)
            
            logger.info(f"Completed {analysis_type} analysis for content {content_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {e}")
            raise
    
    async def get_platform_insights(
        self,
        platform: str,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive insights for a platform"""
        
        try:
            timeframe_map = {
                "7d": DashboardTimeframe.LAST_7_DAYS,
                "30d": DashboardTimeframe.LAST_30_DAYS,
                "90d": DashboardTimeframe.LAST_90_DAYS
            }
            
            dashboard_timeframe = timeframe_map.get(timeframe, DashboardTimeframe.LAST_30_DAYS)
            
            # Get platform analytics
            platform_analytics = await self.dashboard.get_platform_analytics(
                platform, dashboard_timeframe
            )
            
            # Get trending content
            trending_content = await self.trend_analyzer.get_trending_content(
                platform, time_period_days=int(timeframe[:-1])
            )
            
            # Get optimization insights for this platform
            optimization_insights = await self.dashboard.get_optimization_insights(
                dashboard_timeframe, [platform]
            )
            
            results = {
                'platform_analytics': asdict(platform_analytics),
                'trending_content': trending_content,
                'optimization_insights': [asdict(insight) for insight in optimization_insights],
                'timeframe': timeframe,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Generated insights for {platform} over {timeframe}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting platform insights: {e}")
            raise
    
    async def generate_optimization_recommendations(
        self,
        platforms: Optional[List[str]] = None,
        content_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate optimization recommendations based on data analysis"""
        
        try:
            # Get optimization insights
            insights = await self.dashboard.get_optimization_insights(
                DashboardTimeframe.LAST_30_DAYS, platforms
            )
            
            # If specific content IDs provided, analyze them
            content_analysis = {}
            if content_ids:
                for content_id in content_ids:
                    try:
                        analysis = await self.analyze_content_performance(content_id)
                        content_analysis[content_id] = analysis
                    except Exception as e:
                        logger.warning(f"Could not analyze content {content_id}: {e}")
            
            # Generate platform-specific recommendations
            platform_recommendations = {}
            if platforms:
                for platform in platforms:
                    platform_insights = await self.get_platform_insights(platform)
                    platform_recommendations[platform] = platform_insights
            
            results = {
                'general_optimization_insights': [asdict(insight) for insight in insights],
                'content_specific_analysis': content_analysis,
                'platform_recommendations': platform_recommendations,
                'generated_at': datetime.now().isoformat(),
                'analysis_scope': {
                    'platforms': platforms or ['all'],
                    'content_count': len(content_ids) if content_ids else 0
                }
            }
            
            logger.info(f"Generated optimization recommendations for {len(insights)} insights")
            return results
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            raise
    
    async def compare_content_performance(
        self,
        content_ids: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare performance between multiple content pieces"""
        
        try:
            if len(content_ids) < 2:
                raise ValueError("Need at least 2 content pieces for comparison")
            
            # Use dashboard comparative analysis
            comparative_analysis = await self.dashboard.get_comparative_analysis(
                content_ids, metrics
            )
            
            # Add additional insights
            comparative_analysis['comparison_metadata'] = {
                'content_count': len(content_ids),
                'metrics_analyzed': metrics or ['views', 'engagement_rate', 'performance_score'],
                'comparison_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Compared performance of {len(content_ids)} content pieces")
            return comparative_analysis
            
        except Exception as e:
            logger.error(f"Error comparing content performance: {e}")
            raise
    
    async def get_dashboard_overview(
        self,
        timeframe: str = "30d",
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get dashboard overview data"""
        
        try:
            timeframe_map = {
                "7d": DashboardTimeframe.LAST_7_DAYS,
                "30d": DashboardTimeframe.LAST_30_DAYS,
                "90d": DashboardTimeframe.LAST_90_DAYS,
                "1y": DashboardTimeframe.LAST_YEAR
            }
            
            dashboard_timeframe = timeframe_map.get(timeframe, DashboardTimeframe.LAST_30_DAYS)
            
            # Get overview from dashboard
            overview = await self.dashboard.get_dashboard_overview(
                dashboard_timeframe, platforms
            )
            
            logger.info(f"Generated dashboard overview for timeframe: {timeframe}")
            return asdict(overview)
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            raise
    
    async def export_analytics_data(
        self,
        format_type: str = "json",
        timeframe: str = "30d",
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Export analytics data in various formats"""
        
        try:
            timeframe_map = {
                "7d": DashboardTimeframe.LAST_7_DAYS,
                "30d": DashboardTimeframe.LAST_30_DAYS,
                "90d": DashboardTimeframe.LAST_90_DAYS
            }
            
            dashboard_timeframe = timeframe_map.get(timeframe, DashboardTimeframe.LAST_30_DAYS)
            
            # Export data using dashboard
            export_data = await self.dashboard.export_dashboard_data(
                format_type, dashboard_timeframe, platforms
            )
            
            logger.info(f"Exported analytics data in {format_type} format")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            raise
    
    async def cleanup_old_data(self, retention_days: int = 365):
        """Clean up old analytics data based on retention policy"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # This would implement data cleanup logic
            # For now, just log what would be done
            logger.info(f"Would clean up analytics data older than {cutoff_date}")
            
            # In a real implementation, you might:
            # 1. Archive old engagement snapshots
            # 2. Aggregate old trend analysis results
            # 3. Remove outdated optimization insights
            
            return {
                'cleanup_timestamp': datetime.now().isoformat(),
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'status': 'simulated'  # Would be 'completed' in real implementation
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise


# Usage examples and integration patterns

async def example_basic_usage():
    """Example of basic performance analytics usage"""
    
    # This assumes you have a database connection
    # db_pool = await asyncpg.create_pool(DATABASE_URL)
    
    # Initialize the manager
    # manager = PerformanceAnalyticsManager(db_pool)
    
    # Track some performance data
    # metrics = {
    #     'views': 1500,
    #     'likes': 120,
    #     'comments': 25,
    #     'shares': 8,
    #     'engagement_rate': 0.085,
    #     'watch_time': 1200
    # }
    # 
    # snapshot_id = await manager.track_content_performance(
    #     content_id="content-123",
    #     platform="youtube",
    #     metrics=metrics,
    #     metadata={'title': 'My Great Video'}
    # )
    
    print("Basic usage example completed")


async def example_platform_analysis():
    """Example of platform-specific analysis"""
    
    # manager = PerformanceAnalyticsManager(db_pool)
    
    # Get insights for a specific platform
    # insights = await manager.get_platform_insights(
    #     platform="youtube",
    #     timeframe="30d"
    # )
    
    print("Platform analysis example completed")


async def example_content_comparison():
    """Example of content performance comparison"""
    
    # manager = PerformanceAnalyticsManager(db_pool)
    
    # Compare multiple content pieces
    # comparison = await manager.compare_content_performance(
    #     content_ids=["content-1", "content-2", "content-3"],
    #     metrics=["views", "engagement_rate", "performance_score"]
    # )
    
    print("Content comparison example completed")


async def example_optimization_recommendations():
    """Example of generating optimization recommendations"""
    
    # manager = PerformanceAnalyticsManager(db_pool)
    
    # Get optimization recommendations
    # recommendations = await manager.generate_optimization_recommendations(
    #     platforms=["youtube", "tiktok"],
    #     content_ids=["content-1", "content-2"]
    # )
    
    print("Optimization recommendations example completed")


if __name__ == "__main__":
    # Run examples
    print("Performance Analytics Integration Examples")
    print("=" * 50)
    
    asyncio.run(example_basic_usage())
    asyncio.run(example_platform_analysis())
    asyncio.run(example_content_comparison())
    asyncio.run(example_optimization_recommendations())
    
    print("\nAll examples completed successfully!")