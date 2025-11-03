"""
Comment Scraping System Main API.

This module provides the main API interface for the comment scraping system,
exposing high-level functions for scraping and analyzing comments across platforms.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from datetime import datetime

from .models.comment_models import (
    CommentBase, CommentWithAnalysis, Platform, ContentType, ScrapingJob
)
from .scraper_factory import scraping_manager, ScraperFactory
from .utils.comment_analyzer import comment_analyzer
from .utils.data_extractor import data_extractor
from .utils.api_key_manager import api_key_manager
from .utils.rate_limiter import rate_limiter
from .config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class CommentScrapingAPI:
    """
    Main API for the Comment Scraping System.
    
    This class provides a high-level interface for all comment scraping
    and analysis operations.
    """
    
    def __init__(self):
        """Initialize the API."""
        self.version = "1.0.0"
        logger.info(f"Comment Scraping API v{self.version} initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await scraping_manager.cleanup()
        logger.info("Comment Scraping API cleanup completed")
    
    # ====================
    # High-level API Methods
    # ====================
    
    async def scrape_and_analyze_comments(
        self,
        platform: Platform,
        content_id: str,
        content_type: str = "video",
        max_comments: int = 1000,
        include_analysis: bool = True,
        language_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Scrape and analyze comments from specified content.
        
        Args:
            platform: Platform to scrape from
            content_id: Content ID to scrape comments from
            content_type: Type of content (video, post, reel, etc.)
            max_comments: Maximum comments to scrape
            include_analysis: Whether to include sentiment analysis
            language_filter: Filter by language code
            start_date: Only scrape comments after this date
            end_date: Only scrape comments before this date
            
        Returns:
            Dictionary with scraped comments and analysis results
        """
        logger.info(f"Starting scrape and analysis for {platform}:{content_id}")
        
        try:
            # Scrape comments
            comments = []
            async for comment in scraping_manager.scrape_comments(
                platform=platform,
                content_id=content_id,
                content_type=ContentType(content_type),
                max_comments=max_comments,
                language_filter=language_filter,
                start_date=start_date,
                end_date=end_date
            ):
                comments.append(comment)
            
            logger.info(f"Scraped {len(comments)} comments from {platform}")
            
            # Analyze comments if requested
            analyzed_comments = comments
            analysis_stats = {}
            
            if include_analysis and comments:
                logger.info("Starting sentiment analysis...")
                analyzed_comments = await comment_analyzer.analyze_batch(comments)
                
                # Generate analysis statistics
                trends = await comment_analyzer.analyze_comment_trends(analyzed_comments)
                analysis_stats = trends
            
            return {
                'success': True,
                'platform': platform.value,
                'content_id': content_id,
                'content_type': content_type,
                'comments_scraped': len(comments),
                'comments_analyzed': len(analyzed_comments),
                'comments': analyzed_comments,
                'analysis_stats': analysis_stats,
                'timestamp': datetime.utcnow().isoformat(),
                'filters_applied': {
                    'language': language_filter,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'max_comments': max_comments
                }
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_and_analyze: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': platform.value,
                'content_id': content_id,
                'comments_scraped': 0,
                'comments': []
            }
    
    async def extract_and_export(
        self,
        platform: Platform,
        content_id: str,
        output_format: str = "json",
        output_file: Optional[str] = None,
        include_analysis: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract comments and export to file.
        
        Args:
            platform: Platform to extract from
            content_id: Content ID to extract from
            output_format: Output format (json, csv, xlsx, parquet)
            output_file: Optional output file path
            include_analysis: Whether to include analysis
            **kwargs: Additional extraction parameters
            
        Returns:
            Dictionary with extraction and export results
        """
        logger.info(f"Starting extraction and export for {platform}:{content_id}")
        
        try:
            extraction_result = await data_extractor.extract_comments(
                platform=platform,
                content_id=content_id,
                include_analysis=include_analysis,
                output_format=output_format,
                output_file=output_file,
                **kwargs
            )
            
            return {
                'success': True,
                'extraction': extraction_result,
                'export': extraction_result.get('export'),
                'message': f"Successfully extracted and exported {extraction_result['total_extracted']} comments"
            }
            
        except Exception as e:
            logger.error(f"Error in extract_and_export: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Export failed"
            }
    
    async def batch_scrape(
        self,
        scraping_requests: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Scrape comments from multiple sources concurrently.
        
        Args:
            scraping_requests: List of scraping request dictionaries
            max_concurrent: Maximum concurrent scraping operations
            
        Returns:
            List of scraping results
        """
        logger.info(f"Starting batch scraping with {len(scraping_requests)} requests")
        
        try:
            results = await data_extractor.batch_extract(
                extraction_requests=scraping_requests,
                max_concurrent=max_concurrent
            )
            
            successful_results = [r for r in results if r.get('success', False)]
            failed_results = [r for r in results if not r.get('success', False)]
            
            logger.info(
                f"Batch scraping completed: {len(successful_results)} successful, "
                f"{len(failed_results)} failed"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch_scrape: {e}")
            return [{'success': False, 'error': str(e)} for _ in scraping_requests]
    
    async def get_trending_topics(
        self,
        platforms: List[Platform],
        content_ids: List[str],
        time_range: str = "7d",
        min_mentions: int = 3
    ) -> Dict[str, Any]:
        """
        Get trending topics across multiple content pieces.
        
        Args:
            platforms: Platforms to analyze
            content_ids: Content IDs to analyze
            time_range: Time range for analysis (e.g., "7d", "30d", "2024-01-01:2024-12-31")
            min_mentions: Minimum mentions for a topic to be considered
            
        Returns:
            Dictionary with trending topics analysis
        """
        logger.info(f"Analyzing trending topics across {len(platforms)} platforms")
        
        try:
            trending_analysis = await data_extractor.extract_trending_topics(
                platforms=platforms,
                content_ids=content_ids,
                time_range=time_range,
                min_mentions=min_mentions
            )
            
            return {
                'success': True,
                'trending_topics': trending_analysis,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_trending_topics: {e}")
            return {
                'success': False,
                'error': str(e),
                'trending_topics': []
            }
    
    # ====================
    # System Information Methods
    # ====================
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            available_platforms = await scraping_manager.get_available_platforms()
            health_report = await scraping_manager.get_system_health()
            api_key_status = api_key_manager.get_all_key_status()
            
            return {
                'status': 'operational',
                'version': self.version,
                'available_platforms': [p.value for p in available_platforms],
                'supported_platforms': [p.value for p in Platform],
                'health': health_report,
                'api_keys': api_key_status,
                'rate_limits': {p.value: status.dict() for p, status in rate_limiter.get_all_status().items()},
                'settings': {
                    'gdpr_compliant': settings.ENABLE_GDPR_COMPLIANCE,
                    'data_retention_days': settings.DEFAULT_RETENTION_DAYS,
                    'cache_ttl': settings.CACHE_TTL
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'version': self.version
            }
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate system configuration and API keys."""
        logger.info("Validating system configuration...")
        
        try:
            # Check API keys
            api_validation = await api_key_manager.validate_all_keys()
            
            # Test connections
            connection_results = {}
            async with scraping_manager:
                for platform in Platform:
                    if api_validation.get(platform.value, False):
                        try:
                            scraper = await scraping_manager.get_scraper(platform)
                            connection_results[platform.value] = await scraper.test_connection()
                        except Exception as e:
                            connection_results[platform.value] = False
                            logger.warning(f"Connection test failed for {platform}: {e}")
            
            # Validate settings
            config_validations = {
                'gdpr_enabled': settings.ENABLE_GDPR_COMPLIANCE,
                'retention_configured': settings.ENABLE_DATA_RETENTION,
                'rate_limits_configured': all([
                    settings.YOUTUBE_RATE_LIMIT,
                    settings.TWITTER_RATE_LIMIT,
                    settings.INSTAGRAM_RATE_LIMIT,
                    settings.TIKTOK_RATE_LIMIT
                ])
            }
            
            all_api_keys_valid = all(api_validation.values())
            all_connections_working = all(connection_results.values())
            
            return {
                'configuration_valid': all_api_keys_valid and all_connections_working,
                'api_keys': {
                    platform.value: {
                        'configured': api_validation.get(platform.value, False),
                        'connection_working': connection_results.get(platform.value, False)
                    }
                    for platform in Platform
                },
                'configuration': config_validations,
                'recommendations': self._get_configuration_recommendations(api_validation, connection_results)
            }
            
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return {
                'configuration_valid': False,
                'error': str(e)
            }
    
    def _get_configuration_recommendations(
        self, 
        api_validation: Dict[str, bool], 
        connection_results: Dict[str, bool]
    ) -> List[str]:
        """Generate configuration recommendations."""
        recommendations = []
        
        for platform in Platform:
            platform_key = platform.value
            
            if not api_validation.get(platform_key, False):
                recommendations.append(f"Configure API key for {platform_key}")
            
            elif not connection_results.get(platform_key, False):
                recommendations.append(f"Fix connection issues for {platform_key}")
        
        if not recommendations:
            recommendations.append("All platforms configured and working correctly")
        
        return recommendations
    
    # ====================
    # Platform-specific Methods
    # ====================
    
    async def scrape_youtube_video_comments(
        self,
        video_url_or_id: str,
        max_comments: int = 1000,
        include_replies: bool = True,
        language_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for scraping YouTube video comments.
        
        Args:
            video_url_or_id: YouTube video URL or ID
            max_comments: Maximum comments to scrape
            include_replies: Whether to include replies
            language_filter: Filter by language code
            
        Returns:
            Dictionary with scraping results
        """
        return await self.scrape_and_analyze_comments(
            platform=Platform.YOUTUBE,
            content_id=video_url_or_id,  # YouTube scraper handles URL parsing
            content_type="video",
            max_comments=max_comments,
            include_replies=include_replies,
            language_filter=language_filter
        )
    
    async def scrape_twitter_replies(
        self,
        tweet_url_or_id: str,
        max_comments: int = 1000,
        language_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for scraping Twitter/X replies.
        
        Args:
            tweet_url_or_id: Twitter/X tweet URL or ID
            max_comments: Maximum replies to scrape
            language_filter: Filter by language code
            
        Returns:
            Dictionary with scraping results
        """
        return await self.scrape_and_analyze_comments(
            platform=Platform.TWITTER,
            content_id=tweet_url_or_id,  # Twitter scraper handles URL parsing
            content_type="post",
            max_comments=max_comments,
            include_replies=False,  # Twitter API handles replies in the same query
            language_filter=language_filter
        )
    
    async def scrape_instagram_media_comments(
        self,
        media_url_or_id: str,
        max_comments: int = 1000,
        include_replies: bool = True,
        language_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for scraping Instagram media comments.
        
        Args:
            media_url_or_id: Instagram media URL or ID
            max_comments: Maximum comments to scrape
            include_replies: Whether to include replies
            language_filter: Filter by language code
            
        Returns:
            Dictionary with scraping results
        """
        return await self.scrape_and_analyze_comments(
            platform=Platform.INSTAGRAM,
            content_id=media_url_or_id,
            content_type="post",
            max_comments=max_comments,
            include_replies=include_replies,
            language_filter=language_filter
        )
    
    async def scrape_tiktok_video_comments(
        self,
        video_url_or_id: str,
        max_comments: int = 1000,
        language_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for scraping TikTok video comments.
        
        Note: TikTok Research API has limited comment access capabilities.
        This method may return limited results.
        
        Args:
            video_url_or_id: TikTok video URL or ID
            max_comments: Maximum comments to scrape
            language_filter: Filter by language code
            
        Returns:
            Dictionary with scraping results
        """
        logger.warning(
            "TikTok Research API has limited comment access. "
            "Results may be limited or unavailable."
        )
        
        return await self.scrape_and_analyze_comments(
            platform=Platform.TIKTOK,
            content_id=video_url_or_id,
            content_type="video",
            max_comments=max_comments,
            include_replies=False,  # Limited in Research API
            language_filter=language_filter
        )


# Global API instance
comment_api = CommentScrapingAPI()


# ====================
# Convenience Functions
# ====================

async def quick_scrape(
    platform: Union[Platform, str],
    content_id: str,
    max_comments: int = 100,
    include_analysis: bool = True
) -> Dict[str, Any]:
    """
    Quick scrape function for simple use cases.
    
    Args:
        platform: Platform to scrape from
        content_id: Content ID
        max_comments: Maximum comments to scrape
        include_analysis: Whether to include analysis
        
    Returns:
        Dictionary with scraping results
    """
    if isinstance(platform, str):
        platform = Platform(platform)
    
    async with comment_api:
        return await comment_api.scrape_and_analyze_comments(
            platform=platform,
            content_id=content_id,
            max_comments=max_comments,
            include_analysis=include_analysis
        )


async def get_system_health() -> Dict[str, Any]:
    """Get system health status."""
    async with comment_api:
        return await comment_api.get_system_status()


async def validate_setup() -> Dict[str, Any]:
    """Validate system setup and configuration."""
    async with comment_api:
        return await comment_api.validate_configuration()


# ====================
# Export public API
# ====================

__all__ = [
    'CommentScrapingAPI',
    'comment_api',
    'quick_scrape',
    'get_system_health',
    'validate_setup',
    'ScraperFactory',
    'scraping_manager',
    'comment_analyzer',
    'data_extractor',
    'api_key_manager',
    'rate_limiter'
]