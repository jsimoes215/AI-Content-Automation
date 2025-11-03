"""
Comment Scraper Factory and Manager.

This module provides a factory pattern for creating platform-specific scrapers
and a manager class for coordinating scraping operations across platforms.
"""

import asyncio
from typing import Dict, List, Optional, AsyncIterator, Type
from datetime import datetime
import logging

from .models.comment_models import (
    CommentBase, CommentWithAnalysis, Platform, ScrapingJob, 
    ContentType, ComplianceRecord, ScrapingStats
)
from .platforms.base_scraper import BaseCommentScraper
from .platforms.youtube_scraper import YouTubeCommentScraper
from .platforms.twitter_scraper import TwitterCommentScraper
from .platforms.instagram_scraper import InstagramCommentScraper
from .platforms.tiktok_scraper import TikTokCommentScraper
from .utils.rate_limiter import rate_limiter
from .utils.api_key_manager import api_key_manager
from .config.settings import settings

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory for creating platform-specific comment scrapers."""
    
    _scrapers: Dict[Platform, Type[BaseCommentScraper]] = {
        Platform.YOUTUBE: YouTubeCommentScraper,
        Platform.TWITTER: TwitterCommentScraper,
        Platform.INSTAGRAM: InstagramCommentScraper,
        Platform.TIKTOK: TikTokCommentScraper
    }
    
    @classmethod
    def create_scraper(cls, platform: Platform) -> BaseCommentScraper:
        """
        Create a scraper instance for the specified platform.
        
        Args:
            platform: Platform to create scraper for
            
        Returns:
            Configured scraper instance
            
        Raises:
            ValueError: If platform is not supported
        """
        scraper_class = cls._scrapers.get(platform)
        if not scraper_class:
            raise ValueError(f"Unsupported platform: {platform}")
        
        logger.info(f"Creating scraper for {platform}")
        return scraper_class()
    
    @classmethod
    def get_supported_platforms(cls) -> List[Platform]:
        """Get list of supported platforms."""
        return list(cls._scrapers.keys())
    
    @classmethod
    def get_platform_capabilities(cls, platform: Platform) -> Dict[str, bool]:
        """Get capabilities for a specific platform."""
        scraper_class = cls._scrapers.get(platform)
        if not scraper_class:
            return {}
        
        # Create a temporary instance to check capabilities
        # Note: This won't work for async __init__ methods
        capabilities = {
            "comment_scraping": True,
            "rate_limiting": True,
            "pagination": True,
            "date_filtering": True,
            "language_filtering": True,
            "reply_scraping": True
        }
        
        # Platform-specific capabilities
        if platform == Platform.TIKTOK:
            capabilities.update({
                "comment_scraping": False,  # Research API limitations
                "daily_limits": True
            })
        
        return capabilities


class CommentScrapingManager:
    """Manager for coordinating comment scraping operations."""
    
    def __init__(self):
        """Initialize the scraping manager."""
        self.active_scrapers: Dict[Platform, BaseCommentScraper] = {}
        self.scraping_jobs: Dict[str, ScrapingJob] = {}
        
        logger.info("Comment scraping manager initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def cleanup(self) -> None:
        """Cleanup all active scrapers."""
        for scraper in self.active_scrapers.values():
            await scraper.cleanup()
        
        self.active_scrapers.clear()
        logger.info("Scraping manager cleanup completed")
    
    async def get_scraper(self, platform: Platform) -> BaseCommentScraper:
        """
        Get or create a scraper for the specified platform.
        
        Args:
            platform: Platform to get scraper for
            
        Returns:
            Configured and initialized scraper
        """
        if platform in self.active_scrapers:
            return self.active_scrapers[platform]
        
        # Check if API key is available
        if not api_key_manager.has_valid_key(platform):
            raise ValueError(f"No valid API key available for {platform}")
        
        # Create and initialize scraper
        scraper = ScraperFactory.create_scraper(platform)
        await scraper.initialize()
        
        self.active_scrapers[platform] = scraper
        return scraper
    
    async def scrape_comments(
        self,
        platform: Platform,
        content_id: str,
        content_type: ContentType = ContentType.VIDEO,
        max_comments: int = 1000,
        include_replies: bool = True,
        language_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        job_id: Optional[str] = None
    ) -> AsyncIterator[CommentBase]:
        """
        Scrape comments from specified content.
        
        Args:
            platform: Platform to scrape from
            content_id: Content ID to scrape comments from
            content_type: Type of content
            max_comments: Maximum comments to scrape
            include_replies: Whether to include replies
            language_filter: Filter by language code
            start_date: Only scrape comments after this date
            end_date: Only scrape comments before this date
            job_id: Optional job ID for tracking
            
        Yields:
            CommentBase objects for each scraped comment
        """
        job_id = job_id or f"{platform.value}_{content_id}_{int(datetime.utcnow().timestamp())}"
        
        # Create scraping job
        job = ScrapingJob(
            job_id=job_id,
            platform=platform,
            content_id=content_id,
            content_type=content_type,
            max_comments=max_comments,
            include_replies=include_replies,
            language_filter=language_filter,
            status="running",
            started_at=datetime.utcnow()
        )
        
        self.scraping_jobs[job_id] = job
        
        try:
            # Get scraper and start scraping
            scraper = await self.get_scraper(platform)
            
            logger.info(
                f"Starting scraping job {job_id} for {platform}:{content_id}. "
                f"Max: {max_comments}, Replies: {include_replies}"
            )
            
            async for comment in scraper.scrape_comments(
                content_id=content_id,
                content_type=content_type,
                max_comments=max_comments,
                include_replies=include_replies,
                language_filter=language_filter,
                start_date=start_date,
                end_date=end_date
            ):
                # Update job progress
                job.comments_scraped += 1
                job.progress = job.comments_scraped / max_comments
                job.comments.append(comment)
                
                # Update status
                if job.comments_scraped >= max_comments:
                    job.status = "completed"
                    job.completed_at = datetime.utcnow()
                    break
                
                yield comment
            
            # Final status update
            if job.status == "running":
                job.status = "completed"
                job.completed_at = datetime.utcnow()
            
            logger.info(f"Completed scraping job {job_id}: {job.comments_scraped} comments")
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            logger.error(f"Scraping job {job_id} failed: {e}")
            raise
        
        finally:
            self.scraping_jobs[job_id] = job
    
    async def scrape_multiple_platforms(
        self,
        content_mappings: Dict[Platform, str],
        content_type: ContentType = ContentType.VIDEO,
        max_comments: int = 1000,
        include_replies: bool = True,
        language_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[Platform, AsyncIterator[CommentBase]]:
        """
        Scrape comments from multiple platforms simultaneously.
        
        Args:
            content_mappings: Mapping of platform to content ID
            content_type: Type of content
            max_comments: Maximum comments per platform
            include_replies: Whether to include replies
            language_filter: Filter by language code
            start_date: Only scrape comments after this date
            end_date: Only scrape comments before this date
            
        Returns:
            Dictionary mapping platforms to async iterators of comments
        """
        tasks = {}
        
        for platform, content_id in content_mappings.items():
            task = self.scrape_comments(
                platform=platform,
                content_id=content_id,
                content_type=content_type,
                max_comments=max_comments,
                include_replies=include_replies,
                language_filter=language_filter,
                start_date=start_date,
                end_date=end_date
            )
            tasks[platform] = task
        
        return tasks
    
    async def get_job_status(self, job_id: str) -> Optional[ScrapingJob]:
        """Get status of a scraping job."""
        return self.scraping_jobs.get(job_id)
    
    async def get_all_jobs(self) -> List[ScrapingJob]:
        """Get all scraping jobs."""
        return list(self.scraping_jobs.values())
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running scraping job.
        
        Note: This is a placeholder implementation. In a full system,
        you'd need to implement actual job cancellation.
        """
        job = self.scraping_jobs.get(job_id)
        if job and job.status == "running":
            job.status = "cancelled"
            job.completed_at = datetime.utcnow()
            logger.info(f"Cancelled scraping job {job_id}")
            return True
        
        return False
    
    async def get_available_platforms(self) -> List[Platform]:
        """Get list of platforms with valid API keys and scrapers."""
        available_platforms = []
        
        for platform in Platform:
            try:
                # Check if API key is valid
                if api_key_manager.has_valid_key(platform):
                    # Try to get scraper (this validates the API key)
                    scraper = await self.get_scraper(platform)
                    
                    # Test connection
                    if await scraper.test_connection():
                        available_platforms.append(platform)
                    else:
                        logger.warning(f"Connection test failed for {platform}")
                
            except Exception as e:
                logger.warning(f"Platform {platform} not available: {e}")
        
        return available_platforms
    
    async def get_platform_stats(self, platform: Platform) -> Dict[str, any]:
        """Get statistics for a platform's scraper."""
        scraper = self.active_scrapers.get(platform)
        if not scraper:
            return {}
        
        return scraper.get_stats()
    
    async def get_system_health(self) -> Dict[str, any]:
        """Get overall system health report."""
        available_platforms = await self.get_available_platforms()
        active_jobs = [job for job in self.scraping_jobs.values() if job.status == "running"]
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": "healthy",
            "available_platforms": [p.value for p in available_platforms],
            "active_jobs": len(active_jobs),
            "total_jobs": len(self.scraping_jobs),
            "rate_limits": rate_limiter.get_all_status(),
            "api_key_status": api_key_manager.get_all_key_status()
        }
        
        # Check for any critical issues
        if not available_platforms:
            health_report["system_status"] = "degraded"
            health_report["issues"] = ["No platforms available"]
        
        if any(job.status == "failed" for job in self.scraping_jobs.values()):
            health_report["system_status"] = "degraded"
            health_report["issues"] = health_report.get("issues", []) + ["Failed jobs detected"]
        
        return health_report
    
    async def batch_scrape(
        self,
        scraping_requests: List[Dict[str, any]],
        max_concurrent: int = 3
    ) -> List[AsyncIterator[CommentBase]]:
        """
        Batch scrape from multiple sources with concurrency control.
        
        Args:
            scraping_requests: List of scraping request dictionaries
            max_concurrent: Maximum number of concurrent scraping operations
            
        Returns:
            List of async iterators for each request
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(request):
            async with semaphore:
                return self.scrape_comments(**request)
        
        tasks = [scrape_with_semaphore(req) for req in scraping_requests]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid iterators
        valid_iterators = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch scraping task failed: {result}")
            else:
                valid_iterators.append(result)
        
        return valid_iterators


# Global manager instance
scraping_manager = CommentScrapingManager()