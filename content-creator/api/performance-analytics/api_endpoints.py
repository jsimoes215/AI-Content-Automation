"""
FastAPI Endpoints for Performance Analytics

This module provides REST API endpoints for the performance analytics system.
Integrates with FastAPI to provide HTTP endpoints for all analytics features.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncpg
import logging

# Import performance analytics modules
from .engagement_tracker import EngagementTracker, EngagementSnapshot, Platform, MetricType
from .correlation_analyzer import CorrelationAnalyzer
from .trend_analyzer import TrendAnalyzer
from .analytics_dashboard import AnalyticsDashboard, DashboardTimeframe
from .integration import PerformanceAnalyticsManager
from .config import get_config_for_environment

# Set up logging
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses

class EngagementMetric(BaseModel):
    """Model for engagement metrics"""
    views: int = Field(0, ge=0)
    likes: int = Field(0, ge=0)
    comments: int = Field(0, ge=0)
    shares: int = Field(0, ge=0)
    saves: int = Field(0, ge=0)
    watch_time: int = Field(0, ge=0)
    engagement_rate: float = Field(0, ge=0, le=1)
    click_through_rate: float = Field(0, ge=0, le=1)
    reach: int = Field(0, ge=0)
    impressions: int = Field(0, ge=0)


class TrackEngagementRequest(BaseModel):
    """Request model for tracking engagement"""
    content_id: str = Field(..., description="Unique identifier for the content")
    platform: str = Field(..., description="Platform name (youtube, tiktok, etc.)")
    metrics: EngagementMetric
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ContentAnalysisRequest(BaseModel):
    """Request model for content analysis"""
    content_id: str = Field(..., description="Content to analyze")
    analysis_types: List[str] = Field(default_factory=lambda: ["comprehensive"], 
                                     description="Types of analysis to perform")
    time_period_days: int = Field(30, ge=7, le=365, description="Analysis time period in days")


class PlatformInsightsRequest(BaseModel):
    """Request model for platform insights"""
    platform: str = Field(..., description="Platform to analyze")
    timeframe: str = Field("30d", description="Time period (7d, 30d, 90d)")
    include_trending: bool = Field(True, description="Include trending content analysis")


class OptimizationRequest(BaseModel):
    """Request model for optimization recommendations"""
    platforms: Optional[List[str]] = Field(None, description="Platforms to analyze")
    content_ids: Optional[List[str]] = Field(None, description="Specific content to analyze")
    priority_filter: Optional[str] = Field(None, description="Filter by priority (high, medium, low)")


class ComparisonRequest(BaseModel):
    """Request model for content comparison"""
    content_ids: List[str] = Field(..., min_items=2, max_items=10, description="Content IDs to compare")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to compare")


class ExportRequest(BaseModel):
    """Request model for data export"""
    format: str = Field("json", description="Export format (json, csv, excel)")
    timeframe: str = Field("30d", description="Export time period")
    platforms: Optional[List[str]] = Field(None, description="Platforms to include")
    include_metadata: bool = Field(True, description="Include metadata in export")


# API Response Models

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DashboardOverviewResponse(BaseModel):
    """Dashboard overview response"""
    total_content_pieces: int
    total_views: int
    average_engagement_rate: float
    best_performing_platform: str
    trending_content_count: int
    performance_trend: str
    top_performing_content: Dict[str, Any]
    recent_highlights: List[str]
    alerts: List[str]


# Dependencies

async def get_db_pool() -> asyncpg.Pool:
    """Dependency to get database pool"""
    # This would be configured based on your database setup
    # For example, using environment variables
    return getattr(get_db_pool, '_pool', None)

async def get_analytics_manager(db_pool: asyncpg.Pool = Depends(get_db_pool)) -> PerformanceAnalyticsManager:
    """Dependency to get analytics manager"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    manager = PerformanceAnalyticsManager(db_pool)
    return manager


# Create router
router = APIRouter(prefix="/analytics", tags=["Performance Analytics"])

# Health and System Endpoints

@router.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint for the analytics service"""
    return APIResponse(
        success=True,
        message="Performance Analytics service is healthy",
        data={
            "service": "Performance Analytics",
            "version": "1.0.0",
            "status": "operational",
            "features": [
                "engagement_tracking",
                "correlation_analysis", 
                "trend_analysis",
                "dashboard_analytics",
                "optimization_insights"
            ]
        }
    )


@router.get("/system/status", response_model=APIResponse)
async def system_status(manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)):
    """Get system status including cache stats and configuration"""
    try:
        # Get cache statistics
        cache_stats = await manager.engagement_tracker.get_cache_stats()
        
        # Get configuration
        config = get_config_for_environment()
        
        status = {
            "database": "connected",
            "cache": {
                "size": cache_stats['cache_size'],
                "entries": cache_stats['cached_entries'][:5]  # Show first 5 entries
            },
            "configuration": {
                "environment": "development",  # Would be determined from environment
                "supported_platforms": len(config.SUPPORTED_PLATFORMS),
                "default_timeframe": config.DEFAULT_ANALYSIS_PERIOD_DAYS,
                "cache_ttl": config.CACHE_TTL_SECONDS
            },
            "features": {
                "engagement_tracking": True,
                "correlation_analysis": True,
                "trend_analysis": True,
                "optimization_insights": True
            }
        }
        
        return APIResponse(
            success=True,
            message="System status retrieved successfully",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


# Engagement Tracking Endpoints

@router.post("/engagement/track", response_model=APIResponse)
async def track_engagement(
    request: TrackEngagementRequest,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Track engagement metrics for content"""
    try:
        # Convert metrics to dict
        metrics_dict = request.metrics.dict()
        
        # Track the engagement
        snapshot_id = await manager.track_content_performance(
            content_id=request.content_id,
            platform=request.platform,
            metrics=metrics_dict,
            metadata=request.metadata
        )
        
        return APIResponse(
            success=True,
            message="Engagement tracked successfully",
            data={
                "snapshot_id": snapshot_id,
                "content_id": request.content_id,
                "platform": request.platform,
                "metrics_tracked": len(metrics_dict)
            }
        )
        
    except Exception as e:
        logger.error(f"Error tracking engagement: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track engagement: {str(e)}")


@router.post("/engagement/batch-track", response_model=APIResponse)
async def batch_track_engagement(
    requests: List[TrackEngagementRequest],
    background_tasks: BackgroundTasks,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Track engagement metrics for multiple content pieces"""
    try:
        # Process in background for large batches
        background_tasks.add_task(process_batch_tracking, requests, manager)
        
        return APIResponse(
            success=True,
            message=f"Batch tracking initiated for {len(requests)} items",
            data={
                "items_to_process": len(requests),
                "status": "processing"
            }
        )
        
    except Exception as e:
        logger.error(f"Error initiating batch tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate batch tracking: {str(e)}")


async def process_batch_tracking(requests: List[TrackEngagementRequest], manager: PerformanceAnalyticsManager):
    """Background task to process batch tracking"""
    try:
        snapshots = []
        for request in requests:
            metrics_dict = request.metrics.dict()
            snapshot = EngagementSnapshot(
                content_id=request.content_id,
                platform=Platform(request.platform),
                timestamp=datetime.now(),
                metrics={MetricType(k): float(v) for k, v in metrics_dict.items()},
                metadata=request.metadata
            )
            snapshots.append(snapshot)
        
        results = await manager.engagement_tracker.batch_track_engagement(snapshots)
        logger.info(f"Batch tracking completed: {len(results)} successful out of {len(requests)}")
        
    except Exception as e:
        logger.error(f"Error in batch tracking: {e}")


# Analytics Endpoints

@router.post("/content/analyze", response_model=APIResponse)
async def analyze_content(
    request: ContentAnalysisRequest,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Analyze performance for specific content"""
    try:
        analysis_results = await manager.analyze_content_performance(
            content_id=request.content_id,
            analysis_type="comprehensive" if "comprehensive" in request.analysis_types else "trend"
        )
        
        return APIResponse(
            success=True,
            message=f"Content analysis completed for {request.content_id}",
            data=analysis_results
        )
        
    except Exception as e:
        logger.error(f"Error analyzing content {request.content_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Content not found or analysis failed: {str(e)}")


@router.post("/platform/insights", response_model=APIResponse)
async def get_platform_insights(
    request: PlatformInsightsRequest,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Get comprehensive insights for a platform"""
    try:
        insights = await manager.get_platform_insights(
            platform=request.platform,
            timeframe=request.timeframe
        )
        
        return APIResponse(
            success=True,
            message=f"Platform insights generated for {request.platform}",
            data=insights
        )
        
    except Exception as e:
        logger.error(f"Error getting platform insights for {request.platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.post("/optimization/recommendations", response_model=APIResponse)
async def get_optimization_recommendations(
    request: OptimizationRequest,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Generate optimization recommendations"""
    try:
        recommendations = await manager.generate_optimization_recommendations(
            platforms=request.platforms,
            content_ids=request.content_ids
        )
        
        # Filter by priority if requested
        if request.priority_filter:
            filtered_insights = [
                insight for insight in recommendations['general_optimization_insights']
                if insight.get('priority') == request.priority_filter
            ]
            recommendations['general_optimization_insights'] = filtered_insights
        
        return APIResponse(
            success=True,
            message="Optimization recommendations generated",
            data=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error generating optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.post("/content/compare", response_model=APIResponse)
async def compare_content_performance(
    request: ComparisonRequest,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Compare performance between multiple content pieces"""
    try:
        comparison = await manager.compare_content_performance(
            content_ids=request.content_ids,
            metrics=request.metrics
        )
        
        return APIResponse(
            success=True,
            message=f"Performance comparison completed for {len(request.content_ids)} content pieces",
            data=comparison
        )
        
    except Exception as e:
        logger.error(f"Error comparing content performance: {e}")
        raise HTTPException(status_code=400, detail=f"Comparison failed: {str(e)}")


# Dashboard Endpoints

@router.get("/dashboard/overview", response_model=APIResponse)
async def get_dashboard_overview(
    timeframe: str = Query("30d", description="Time period (7d, 30d, 90d, 1y)"),
    platforms: Optional[List[str]] = Query(None, description="Platforms to include"),
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Get dashboard overview data"""
    try:
        overview = await manager.get_dashboard_overview(
            timeframe=timeframe,
            platforms=platforms
        )
        
        return APIResponse(
            success=True,
            message="Dashboard overview retrieved successfully",
            data=overview
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")


@router.get("/dashboard/trending", response_model=APIResponse)
async def get_trending_content(
    platform: str = Query(..., description="Platform to analyze"),
    timeframe: str = Query("7d", description="Time period (7d, 30d, 90d)"),
    limit: int = Query(10, ge=1, le=50, description="Number of trending items to return"),
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Get trending content for a platform"""
    try:
        trending_content = await manager.trend_analyzer.get_trending_content(
            platform=platform,
            time_period_days=int(timeframe[:-1]),  # Remove 'd' and convert to int
            top_n=limit
        )
        
        return APIResponse(
            success=True,
            message=f"Trending content retrieved for {platform}",
            data={
                "platform": platform,
                "timeframe": timeframe,
                "trending_content": trending_content,
                "total_found": len(trending_content)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting trending content for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trending content: {str(e)}")


# Export and Reporting Endpoints

@router.post("/export/data", response_model=APIResponse)
async def export_analytics_data(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Export analytics data in various formats"""
    try:
        # For large exports, process in background
        if request.format.lower() in ['csv', 'excel'] or request.include_metadata:
            background_tasks.add_task(process_export, request, manager)
            
            return APIResponse(
                success=True,
                message="Data export initiated",
                data={
                    "status": "processing",
                    "format": request.format,
                    "estimated_time": "30-60 seconds"
                }
            )
        else:
            # Process immediately for simple JSON exports
            export_data = await manager.export_analytics_data(
                format_type=request.format,
                timeframe=request.timeframe,
                platforms=request.platforms
            )
            
            return APIResponse(
                success=True,
                message="Data exported successfully",
                data=export_data
            )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


async def process_export(request: ExportRequest, manager: PerformanceAnalyticsManager):
    """Background task to process data export"""
    try:
        export_data = await manager.export_analytics_data(
            format_type=request.format,
            timeframe=request.timeframe,
            platforms=request.platforms
        )
        
        # In a real implementation, you might:
        # 1. Save to file storage
        # 2. Send email with download link
        # 3. Store export request for later retrieval
        
        logger.info(f"Export completed: {request.format} format")
        
    except Exception as e:
        logger.error(f"Error in export processing: {e}")


# Real-time Metrics Endpoints

@router.get("/realtime/metrics/{content_id}", response_model=APIResponse)
async def get_realtime_metrics(
    content_id: str,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Get real-time metrics for specific content"""
    try:
        # Get latest metrics
        content_summary = await manager.dashboard.get_content_performance_summary(content_id)
        
        return APIResponse(
            success=True,
            message="Real-time metrics retrieved",
            data={
                "content_id": content_id,
                "current_metrics": content_summary.current_metrics,
                "last_updated": content_summary.last_updated,
                "trend": {
                    "direction": content_summary.performance_trend,
                    "strength": content_summary.trend_strength
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting realtime metrics for {content_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Content not found: {str(e)}")


@router.get("/realtime/platform-metrics/{platform}", response_model=APIResponse)
async def get_realtime_platform_metrics(
    platform: str,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Get real-time metrics for a platform"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)  # Last 24 hours
        
        platform_metrics = await manager.engagement_tracker.get_platform_metrics(
            platform=Platform(platform),
            start_date=start_date,
            end_date=end_date
        )
        
        return APIResponse(
            success=True,
            message=f"Real-time platform metrics retrieved for {platform}",
            data=platform_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting realtime platform metrics for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get platform metrics: {str(e)}")


# Admin and Maintenance Endpoints

@router.delete("/admin/cleanup", response_model=APIResponse)
async def cleanup_old_data(
    retention_days: int = Query(365, ge=30, le=1095, description="Data retention period in days"),
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Clean up old analytics data"""
    try:
        cleanup_result = await manager.cleanup_old_data(retention_days=retention_days)
        
        return APIResponse(
            success=True,
            message="Data cleanup completed",
            data=cleanup_result
        )
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/admin/recalculate", response_model=APIResponse)
async def recalculate_analytics(
    background_tasks: BackgroundTasks,
    manager: PerformanceAnalyticsManager = Depends(get_analytics_manager)
):
    """Recalculate all analytics data"""
    try:
        background_tasks.add_task(process_recalculation, manager)
        
        return APIResponse(
            success=True,
            message="Analytics recalculation initiated",
            data={
                "status": "processing",
                "estimated_time": "5-15 minutes",
                "action": "Background recalculation of all analytics"
            }
        )
        
    except Exception as e:
        logger.error(f"Error initiating recalculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate recalculation: {str(e)}")


async def process_recalculation(manager: PerformanceAnalyticsManager):
    """Background task to recalculate analytics"""
    try:
        # This would trigger recalculation of:
        # 1. Correlations
        # 2. Trends
        # 3. Benchmarks
        # 4. Optimization insights
        
        logger.info("Starting analytics recalculation...")
        
        # Clear caches
        await manager.engagement_tracker.clear_cache()
        await manager.correlation_analyzer.clear_cache()
        await manager.trend_analyzer.clear_cache()
        
        # Re-analyze existing content
        await manager._analyze_existing_content()
        
        logger.info("Analytics recalculation completed")
        
    except Exception as e:
        logger.error(f"Error in recalculation: {e}")


# Error handling
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )