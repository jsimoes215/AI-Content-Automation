"""
Analytics Dashboard Module

Provides a unified interface for accessing all performance analytics features.
Generates comprehensive reports and actionable insights.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import asyncpg
import numpy as np
import pandas as pd

from .engagement_tracker import EngagementTracker, EngagementSummary, Platform, MetricType
from .correlation_analyzer import CorrelationAnalyzer, CorrelationResult, FeatureImportance
from .trend_analyzer import TrendAnalyzer, TrendAnalysis, TrendDirection


class DashboardTimeframe(Enum):
    """Timeframe options for dashboard data"""
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_YEAR = "1y"
    CUSTOM = "custom"


class DashboardMetric(Enum):
    """Metrics available in dashboard"""
    VIEWS = "views"
    ENGAGEMENT_RATE = "engagement_rate"
    PERFORMANCE_SCORE = "performance_score"
    REACH = "reach"
    WATCH_TIME = "watch_time"
    CLICK_THROUGH_RATE = "click_through_rate"


@dataclass
class DashboardOverview:
    """High-level dashboard overview"""
    total_content_pieces: int
    total_views: int
    average_engagement_rate: float
    best_performing_platform: str
    trending_content_count: int
    performance_trend: str
    top_performing_content: Dict[str, Any]
    recent_highlights: List[str]
    alerts: List[str]


@dataclass
class ContentPerformanceSummary:
    """Summary of content performance for dashboard"""
    content_id: str
    title: str
    platform: str
    current_metrics: Dict[str, float]
    performance_trend: str
    trend_strength: str
    rank_in_category: int
    optimization_suggestions: List[str]
    last_updated: str


@dataclass
class PlatformAnalytics:
    """Platform-specific analytics"""
    platform: str
    total_content: int
    total_views: int
    average_engagement: float
    top_performing_content: Dict[str, Any]
    performance_trend: str
    content_types: Dict[str, int]
    audience_insights: Dict[str, Any]


@dataclass
class OptimizationInsight:
    """Actionable optimization insight"""
    insight_type: str
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    impact_prediction: str
    implementation_difficulty: str
    affected_content: List[str]
    data_supporting: Dict[str, Any]


class AnalyticsDashboard:
    """Main analytics dashboard providing unified access to all features"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.engagement_tracker = EngagementTracker(db_pool)
        self.correlation_analyzer = CorrelationAnalyzer(db_pool)
        self.trend_analyzer = TrendAnalyzer(db_pool)
        self.logger = logging.getLogger(__name__)
        
    async def get_dashboard_overview(
        self,
        timeframe: DashboardTimeframe = DashboardTimeframe.LAST_30_DAYS,
        platforms: Optional[List[str]] = None,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None
    ) -> DashboardOverview:
        """Get comprehensive dashboard overview"""
        
        try:
            # Calculate time period
            if timeframe == DashboardTimeframe.CUSTOM:
                start_date = custom_start or (datetime.now() - timedelta(days=30))
                end_date = custom_end or datetime.now()
            else:
                days_map = {
                    DashboardTimeframe.LAST_7_DAYS: 7,
                    DashboardTimeframe.LAST_30_DAYS: 30,
                    DashboardTimeframe.LAST_90_DAYS: 90,
                    DashboardTimeframe.LAST_YEAR: 365
                }
                days = days_map.get(timeframe, 30)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
            
            # Get basic metrics
            overview_stats = await self._get_overview_stats(start_date, end_date, platforms)
            
            # Get trending content
            trending_content = []
            for platform in platforms or ['youtube', 'tiktok', 'instagram']:
                try:
                    platform_trending = await self.trend_analyzer.get_trending_content(
                        platform, time_period_days=min(7, (end_date - start_date).days)
                    )
                    trending_content.extend(platform_trending[:2])  # Top 2 per platform
                except Exception as e:
                    self.logger.warning(f"Could not get trending content for {platform}: {e}")
            
            # Determine overall performance trend
            performance_trend = await self._determine_overall_trend(start_date, end_date, platforms)
            
            # Get top performing content
            top_content = await self._get_top_performing_content(start_date, end_date, platforms)
            
            # Generate recent highlights
            highlights = await self._generate_recent_highlights(start_date, end_date, platforms)
            
            # Generate alerts
            alerts = await self._generate_alerts(start_date, end_date, platforms)
            
            return DashboardOverview(
                total_content_pieces=overview_stats['total_content'],
                total_views=overview_stats['total_views'],
                average_engagement_rate=overview_stats['avg_engagement'],
                best_performing_platform=overview_stats['best_platform'],
                trending_content_count=len(trending_content),
                performance_trend=performance_trend,
                top_performing_content=top_content,
                recent_highlights=highlights,
                alerts=alerts
            )
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard overview: {e}")
            raise
    
    async def get_content_performance_summary(
        self,
        content_id: str,
        include_trends: bool = True,
        include_correlations: bool = True,
        include_recommendations: bool = True
    ) -> ContentPerformanceSummary:
        """Get detailed performance summary for specific content"""
        
        try:
            # Get basic content info
            content_info = await self._get_content_info(content_id)
            if not content_info:
                raise ValueError(f"Content {content_id} not found")
            
            # Get latest metrics
            latest_metrics = await self._get_latest_metrics(content_id)
            
            # Get performance trend
            trend_analysis = None
            trend_strength = "unknown"
            performance_trend = "stable"
            
            if include_trends:
                try:
                    trend_analysis = await self.trend_analyzer.analyze_trend(
                        content_id, 'engagement_rate', time_period_days=30
                    )
                    if trend_analysis:
                        performance_trend = trend_analysis.overall_direction.value
                        trend_strength = trend_analysis.strength.value
                except Exception as e:
                    self.logger.warning(f"Could not analyze trend for {content_id}: {e}")
            
            # Get rank in category
            rank = await self._get_content_rank(content_id)
            
            # Generate optimization suggestions
            suggestions = []
            if include_recommendations:
                suggestions = await self._generate_optimization_suggestions(
                    content_id, trend_analysis
                )
            
            return ContentPerformanceSummary(
                content_id=content_id,
                title=content_info.get('title', 'Untitled'),
                platform=content_info.get('platform', 'unknown'),
                current_metrics=latest_metrics,
                performance_trend=performance_trend,
                trend_strength=trend_strength,
                rank_in_category=rank,
                optimization_suggestions=suggestions,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting content performance summary: {e}")
            raise
    
    async def get_platform_analytics(
        self,
        platform: str,
        timeframe: DashboardTimeframe = DashboardTimeframe.LAST_30_DAYS
    ) -> PlatformAnalytics:
        """Get comprehensive platform analytics"""
        
        try:
            # Calculate time period
            days_map = {
                DashboardTimeframe.LAST_7_DAYS: 7,
                DashboardTimeframe.LAST_30_DAYS: 30,
                DashboardTimeframe.LAST_90_DAYS: 90,
                DashboardTimeframe.LAST_YEAR: 365
            }
            days = days_map.get(timeframe, 30)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get platform metrics
            platform_metrics = await self.engagement_tracker.get_platform_metrics(
                Platform(platform), start_date, end_date
            )
            
            # Get trending content for platform
            trending_content = await self.trend_analyzer.get_trending_content(
                platform, time_period_days=min(7, days), top_n=1
            )
            
            # Analyze performance trend
            trend_analysis = await self._analyze_platform_trend(platform, start_date, end_date)
            
            # Get content type breakdown
            content_types = await self._get_content_type_breakdown(platform, start_date, end_date)
            
            # Get audience insights
            audience_insights = await self._get_audience_insights(platform, start_date, end_date)
            
            return PlatformAnalytics(
                platform=platform,
                total_content=platform_metrics['summary']['total_content_pieces'],
                total_views=int(platform_metrics['summary']['average_daily_views'] * days),
                average_engagement=platform_metrics['summary']['average_engagement_rate'],
                top_performing_content=trending_content[0] if trending_content else {},
                performance_trend=trend_analysis['direction'],
                content_types=content_types,
                audience_insights=audience_insights
            )
            
        except Exception as e:
            self.logger.error(f"Error getting platform analytics: {e}")
            raise
    
    async def get_optimization_insights(
        self,
        timeframe: DashboardTimeframe = DashboardTimeframe.LAST_30_DAYS,
        platforms: Optional[List[str]] = None,
        top_n: int = 5
    ) -> List[OptimizationInsight]:
        """Get actionable optimization insights based on data analysis"""
        
        try:
            insights = []
            
            # Analyze correlations for optimization opportunities
            correlations = await self.correlation_analyzer.analyze_feature_correlations(
                time_period_days=90, significance_threshold=0.05
            )
            
            for correlation in correlations[:top_n]:
                if correlation.p_value < 0.05 and abs(correlation.correlation_coefficient) > 0.3:
                    insight = OptimizationInsight(
                        insight_type="feature_optimization",
                        priority="high" if abs(correlation.correlation_coefficient) > 0.7 else "medium",
                        title=f"Optimize {correlation.feature.value} for better {correlation.metric.value}",
                        description=correlation.interpretation,
                        impact_prediction=f"Potential {correlation.metric.value} improvement of {abs(correlation.correlation_coefficient) * 20:.1f}%",
                        implementation_difficulty="medium",
                        affected_content=await self._get_affected_content(correlation.feature),
                        data_supporting={
                            'correlation_coefficient': correlation.correlation_coefficient,
                            'p_value': correlation.p_value,
                            'sample_size': correlation.sample_size
                        }
                    )
                    insights.append(insight)
            
            # Analyze trends for timing optimization
            platform_trends = await self._analyze_platform_trends_for_optimization(
                platforms or ['youtube', 'tiktok', 'instagram']
            )
            
            for platform, trend_data in platform_trends.items():
                if trend_data['seasonal_patterns']:
                    for pattern in trend_data['seasonal_patterns']:
                        insight = OptimizationInsight(
                            insight_type="timing_optimization",
                            priority="medium",
                            title=f"Optimize {platform} posting schedule",
                            description=f"Peak performance detected on {pattern.get('peak_times', ['unknown'])}",
                            impact_prediction="15-25% engagement improvement",
                            implementation_difficulty="low",
                            affected_content=await _get_platform_content(platform),
                            data_supporting={'seasonal_pattern': pattern}
                        )
                        insights.append(insight)
            
            # Content performance insights
            performance_insights = await self._generate_performance_insights(timeframe, platforms)
            insights.extend(performance_insights)
            
            # Sort by priority
            priority_order = {"high": 3, "medium": 2, "low": 1}
            insights.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)
            
            return insights[:top_n * 2]  # Return top insights
            
        except Exception as e:
            self.logger.error(f"Error generating optimization insights: {e}")
            raise
    
    async def get_comparative_analysis(
        self,
        content_ids: List[str],
        metrics: List[DashboardMetric] = None
    ) -> Dict[str, Any]:
        """Get comparative analysis between multiple content pieces"""
        
        try:
            if not metrics:
                metrics = [DashboardMetric.VIEWS, DashboardMetric.ENGAGEMENT_RATE, DashboardMetric.PERFORMANCE_SCORE]
            
            # Get individual summaries
            summaries = []
            for content_id in content_ids:
                summary = await self.get_content_performance_summary(content_id)
                summaries.append(summary)
            
            # Compare trends
            trend_comparison = await self.trend_analyzer.compare_content_trends(
                content_ids, 'engagement_rate'
            )
            
            # Analyze correlations
            correlation_insights = await self.correlation_analyzer.analyze_feature_correlations(
                content_ids=content_ids
            )
            
            # Generate comparative insights
            comparative_insights = await self._generate_comparative_insights(summaries)
            
            return {
                'content_summaries': [asdict(summary) for summary in summaries],
                'trend_comparison': trend_comparison,
                'correlation_insights': [asdict(correlation) for correlation in correlation_insights],
                'comparative_insights': comparative_insights,
                'recommendations': await self._generate_comparative_recommendations(summaries)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comparative analysis: {e}")
            raise
    
    async def export_dashboard_data(
        self,
        output_format: str = 'json',
        timeframe: DashboardTimeframe = DashboardTimeframe.LAST_30_DAYS,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Export dashboard data in specified format"""
        
        try:
            # Get all dashboard data
            overview = await self.get_dashboard_overview(timeframe, platforms)
            platform_analytics = {}
            
            for platform in platforms or ['youtube', 'tiktok', 'instagram']:
                try:
                    platform_analytics[platform] = await self.get_platform_analytics(platform, timeframe)
                except Exception as e:
                    self.logger.warning(f"Could not get analytics for {platform}: {e}")
            
            optimization_insights = await self.get_optimization_insights(timeframe, platforms)
            
            # Compile export data
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'timeframe': timeframe.value,
                'platforms': platforms,
                'overview': asdict(overview),
                'platform_analytics': {k: asdict(v) for k, v in platform_analytics.items()},
                'optimization_insights': [asdict(insight) for insight in optimization_insights],
                'metadata': {
                    'total_content_analyzed': overview.total_content_pieces,
                    'analysis_period_days': 30,
                    'platforms_included': list(platform_analytics.keys())
                }
            }
            
            # Format for different output types
            if output_format.lower() == 'csv':
                # Convert key metrics to CSV-compatible format
                return self._format_for_csv_export(export_data)
            elif output_format.lower() == 'excel':
                return self._format_for_excel_export(export_data)
            else:
                return export_data
                
        except Exception as e:
            self.logger.error(f"Error exporting dashboard data: {e}")
            raise
    
    # Helper methods
    
    async def _get_overview_stats(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        platforms: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Get basic overview statistics"""
        
        query = """
        SELECT 
            COUNT(DISTINCT gc.id) as total_content,
            SUM(pm.views) as total_views,
            AVG(pm.engagement_rate) as avg_engagement,
            gc.platform,
            COUNT(*) as platform_count
        FROM generated_content gc
        JOIN performance_metrics pm ON gc.id = pm.content_id
        WHERE gc.created_at >= $1 AND gc.created_at <= $2
        """
        
        params = [start_date, end_date]
        
        if platforms:
            query += " AND gc.platform = ANY($3)"
            params.append(platforms)
        
        query += " GROUP BY gc.platform"
        
        rows = await self.db_pool.fetch(query, *params)
        
        if not rows:
            return {
                'total_content': 0,
                'total_views': 0,
                'avg_engagement': 0,
                'best_platform': 'none'
            }
        
        total_content = sum(row['total_content'] for row in rows)
        total_views = sum(row['total_views'] or 0 for row in rows)
        avg_engagement = np.mean([row['avg_engagement'] or 0 for row in rows])
        
        # Find best performing platform
        best_platform = max(rows, key=lambda x: x['avg_engagement'] or 0)['platform']
        
        return {
            'total_content': total_content,
            'total_views': int(total_views),
            'avg_engagement': avg_engagement,
            'best_platform': best_platform
        }
    
    async def _determine_overall_trend(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: Optional[List[str]]
    ) -> str:
        """Determine overall performance trend"""
        
        try:
            # Get platform trends
            trend_directions = []
            
            for platform in platforms or ['youtube', 'tiktok', 'instagram']:
                try:
                    trends = await self.trend_analyzer.get_trending_content(
                        platform, time_period_days=(end_date - start_date).days
                    )
                    if trends:
                        # If there are trending items, it's generally positive
                        trend_directions.append("positive")
                    else:
                        trend_directions.append("stable")
                except Exception:
                    trend_directions.append("stable")
            
            # Determine overall trend
            positive_count = trend_directions.count("positive")
            total_count = len(trend_directions)
            
            if positive_count / total_count > 0.6:
                return "improving"
            elif positive_count / total_count < 0.4:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Error determining overall trend: {e}")
            return "unknown"
    
    async def _get_top_performing_content(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Get top performing content"""
        
        query = """
        SELECT 
            gc.id,
            gc.content_type,
            gc.platform,
            pm.performance_score,
            pm.views,
            pm.engagement_rate,
            sc.content->>'title' as title
        FROM generated_content gc
        JOIN performance_metrics pm ON gc.id = pm.content_id
        LEFT JOIN scenes s ON gc.scene_id = s.id
        LEFT JOIN scripts sc ON s.script_id = sc.id
        WHERE gc.created_at >= $1 AND gc.created_at <= $2
        """
        
        params = [start_date, end_date]
        
        if platforms:
            query += " AND gc.platform = ANY($3)"
            params.append(platforms)
        
        query += " ORDER BY pm.performance_score DESC LIMIT 1"
        
        row = await self.db_pool.fetchrow(query, *params)
        
        if row:
            return {
                'content_id': str(row['id']),
                'title': row['title'] or 'Untitled',
                'platform': row['platform'],
                'performance_score': float(row['performance_score'] or 0),
                'views': int(row['views'] or 0),
                'engagement_rate': float(row['engagement_rate'] or 0)
            }
        
        return {}
    
    async def _generate_recent_highlights(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: Optional[List[str]]
    ) -> List[str]:
        """Generate recent highlights"""
        
        highlights = []
        
        try:
            # Check for significant performance improvements
            query = """
            SELECT 
                gc.id,
                pm.performance_score,
                sc.content->>'title' as title
            FROM generated_content gc
            JOIN performance_metrics pm ON gc.id = pm.content_id
            LEFT JOIN scenes s ON gc.scene_id = s.id
            LEFT JOIN scripts sc ON s.script_id = sc.id
            WHERE gc.created_at >= $1 AND gc.created_at <= $2
            AND pm.performance_score > 8.0
            ORDER BY pm.performance_score DESC LIMIT 3
            """
            
            params = [start_date, end_date]
            
            if platforms:
                query += " AND gc.platform = ANY($3)"
                params.append(platforms)
            
            rows = await self.db_pool.fetch(query, *params)
            
            for row in rows:
                highlights.append(f"High-performing content: '{row['title'] or 'Untitled'}' (Score: {row['performance_score']:.1f})")
            
            return highlights
            
        except Exception as e:
            self.logger.error(f"Error generating highlights: {e}")
            return ["Unable to generate highlights at this time"]
    
    async def _generate_alerts(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: Optional[List[str]]
    ) -> List[str]:
        """Generate alerts for attention areas"""
        
        alerts = []
        
        try:
            # Check for underperforming content
            query = """
            SELECT COUNT(*) as underperforming_count
            FROM generated_content gc
            JOIN performance_metrics pm ON gc.id = pm.content_id
            WHERE gc.created_at >= $1 AND gc.created_at <= $2
            AND pm.performance_score < 3.0
            """
            
            params = [start_date, end_date]
            
            if platforms:
                query += " AND gc.platform = ANY($3)"
                params.append(platforms)
            
            count = await self.db_pool.fetchval(query, *params)
            
            if count and count > 0:
                alerts.append(f"{count} content pieces performing below threshold (score < 3.0)")
            
            # Check for engagement rate drops
            query = """
            SELECT COUNT(*) as low_engagement_count
            FROM generated_content gc
            JOIN performance_metrics pm ON gc.id = pm.content_id
            WHERE gc.created_at >= $1 AND gc.created_at <= $2
            AND pm.engagement_rate < 0.02
            """
            
            params = [start_date, end_date]
            
            if platforms:
                query += " AND gc.platform = ANY($3)"
                params.append(platforms)
            
            count = await self.db_pool.fetchval(query, *params)
            
            if count and count > 0:
                alerts.append(f"{count} content pieces with low engagement rate (< 2%)")
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            return []
    
    async def _get_content_info(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get basic content information"""
        
        query = """
        SELECT 
            gc.id,
            gc.content_type,
            gc.platform,
            sc.content->>'title' as title,
            sc.content->>'description' as description
        FROM generated_content gc
        LEFT JOIN scenes s ON gc.scene_id = s.id
        LEFT JOIN scripts sc ON s.script_id = sc.id
        WHERE gc.id = $1
        """
        
        row = await self.db_pool.fetchrow(query, content_id)
        
        if row:
            return {
                'id': str(row['id']),
                'content_type': row['content_type'],
                'platform': row['platform'],
                'title': row['title'] or 'Untitled',
                'description': row['description'] or ''
            }
        
        return None
    
    async def _get_latest_metrics(self, content_id: str) -> Dict[str, float]:
        """Get latest performance metrics for content"""
        
        query = """
        SELECT 
            views,
            likes,
            comments_count,
            engagement_rate,
            watch_time,
            performance_score
        FROM performance_metrics
        WHERE content_id = $1
        ORDER BY collected_at DESC
        LIMIT 1
        """
        
        row = await self.db_pool.fetchrow(query, content_id)
        
        if row:
            return {
                'views': float(row['views'] or 0),
                'likes': float(row['likes'] or 0),
                'comments': float(row['comments_count'] or 0),
                'engagement_rate': float(row['engagement_rate'] or 0),
                'watch_time': float(row['watch_time'] or 0),
                'performance_score': float(row['performance_score'] or 0)
            }
        
        return {}
    
    async def _get_content_rank(self, content_id: str) -> int:
        """Get content rank within its platform category"""
        
        query = """
        SELECT COUNT(*) + 1 as rank
        FROM performance_metrics pm1
        JOIN performance_metrics pm2 ON pm1.content_id = $1
        WHERE pm2.platform = pm1.platform
        AND pm2.performance_score > pm1.performance_score
        """
        
        rank = await self.db_pool.fetchval(query, content_id)
        return int(rank) if rank else 999
    
    async def _generate_optimization_suggestions(
        self,
        content_id: str,
        trend_analysis: Optional[TrendAnalysis]
    ) -> List[str]:
        """Generate optimization suggestions for content"""
        
        suggestions = []
        
        if not trend_analysis:
            return ["Insufficient data for optimization suggestions"]
        
        # Trend-based suggestions
        if trend_analysis.overall_direction == TrendDirection.FALLING:
            suggestions.append("Consider reviewing content strategy - declining trend detected")
        elif trend_analysis.overall_direction == TrendDirection.RISING:
            suggestions.append("Strong upward trend - consider creating similar content")
        
        # Volatility suggestions
        if trend_analysis.statistical_metrics['volatility'] > 0.5:
            suggestions.append("High performance variability - consider more consistent posting schedule")
        
        # Seasonal pattern suggestions
        if trend_analysis.seasonality_patterns:
            for pattern in trend_analysis.seasonality_patterns:
                if pattern.get('peak_times'):
                    suggestions.append(f"Post during peak times: {pattern['peak_times']}")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    async def _get_affected_content(self, feature) -> List[str]:
        """Get content affected by a specific feature"""
        
        # This would depend on the feature type
        # For now, return a generic response
        return ["all_relevant_content"]
    
    async def _analyze_platform_trend(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze trend for a platform"""
        
        # Simplified implementation
        return {
            'direction': 'stable',
            'strength': 'moderate',
            'seasonal_patterns': []
        }
    
    async def _get_content_type_breakdown(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Get content type breakdown for platform"""
        
        query = """
        SELECT content_type, COUNT(*) as count
        FROM generated_content
        WHERE platform = $1
        AND created_at >= $2 AND created_at <= $3
        GROUP BY content_type
        """
        
        rows = await self.db_pool.fetch(query, platform, start_date, end_date)
        
        return {row['content_type']: int(row['count']) for row in rows}
    
    async def _get_audience_insights(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get audience insights for platform"""
        
        # Placeholder implementation
        return {
            'peak_activity_hours': ['10:00', '14:00', '20:00'],
            'primary_demographics': ['25-34', '35-44'],
            'engagement_patterns': {
                'weekdays': 'higher',
                'weekends': 'lower'
            }
        }
    
    async def _generate_performance_insights(
        self,
        timeframe: DashboardTimeframe,
        platforms: Optional[List[str]]
    ) -> List[OptimizationInsight]:
        """Generate insights based on overall performance"""
        
        # Placeholder - would analyze performance patterns
        return []
    
    async def _analyze_platform_trends_for_optimization(
        self,
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Analyze platform trends for optimization opportunities"""
        
        trends = {}
        for platform in platforms:
            trends[platform] = {
                'seasonal_patterns': [],
                'optimization_opportunities': []
            }
        
        return trends
    
    async def _generate_comparative_insights(
        self,
        summaries: List[ContentPerformanceSummary]
    ) -> List[str]:
        """Generate insights from content comparison"""
        
        insights = []
        
        if len(summaries) >= 2:
            # Compare performance
            avg_engagement = np.mean([
                summary.current_metrics.get('engagement_rate', 0) 
                for summary in summaries
            ])
            
            best_performer = max(summaries, key=lambda x: x.current_metrics.get('performance_score', 0))
            
            insights.append(f"Best performer: '{best_performer.title}' with {best_performer.current_metrics.get('performance_score', 0):.1f} score")
            insights.append(f"Average engagement rate across compared content: {avg_engagement:.3f}")
        
        return insights
    
    async def _generate_comparative_recommendations(
        self,
        summaries: List[ContentPerformanceSummary]
    ) -> List[str]:
        """Generate recommendations based on comparison"""
        
        recommendations = []
        
        # Find common patterns
        platforms = [summary.platform for summary in summaries]
        if len(set(platforms)) > 1:
            recommendations.append("Consider focusing on the best-performing platform for future content")
        
        # Trend-based recommendations
        declining_trends = [s for s in summaries if s.performance_trend == 'falling']
        if declining_trends:
            recommendations.append(f"{len(declining_trends)} pieces showing declining trends need attention")
        
        return recommendations
    
    def _format_for_csv_export(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for CSV export"""
        return {
            'format': 'csv',
            'data': export_data,
            'note': 'CSV export would require additional processing'
        }
    
    def _format_for_excel_export(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for Excel export"""
        return {
            'format': 'excel',
            'data': export_data,
            'note': 'Excel export would require additional processing'
        }


# Helper functions
async def _get_platform_content(platform: str) -> List[str]:
    """Get content IDs for a specific platform"""
    # Placeholder - would query database
    return [f"content_{platform}_1", f"content_{platform}_2"]