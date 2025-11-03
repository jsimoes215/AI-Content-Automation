"""
Base Scraper Class for Comment Scraping System.

This module defines the base scraper interface and common functionality
that all platform-specific scrapers will inherit from.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Any, Tuple
from datetime import datetime
import aiohttp

from ..models.comment_models import (
    CommentBase, CommentWithAnalysis, Platform, ScrapingJob, 
    ContentType, SentimentLabel, ComplianceRecord
)
from ..utils.rate_limiter import rate_limiter, RateLimitExceeded, DailyLimitExceeded
from ..utils.api_key_manager import api_key_manager, require_api_key
from ..config.settings import settings

logger = logging.getLogger(__name__)


class BaseCommentScraper(ABC):
    """Base class for all comment scrapers."""
    
    def __init__(self, platform: Platform):
        """Initialize base scraper."""
        self.platform = platform
        self.config = settings.get_platform_config(platform.value)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics tracking
        self.stats = {
            "requests_made": 0,
            "comments_scraped": 0,
            "errors": 0,
            "rate_limit_hits": 0,
            "start_time": None,
            "end_time": None
        }
        
        logger.info(f"Initialized {platform.value} comment scraper")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """Initialize the scraper (create HTTP session, validate API key, etc.)."""
        # Create HTTP session with appropriate headers and timeouts
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_default_headers()
        )
        
        # Validate API key
        await self._validate_api_key()
        
        logger.info(f"{self.platform.value} scraper initialized successfully")
    
    async def cleanup(self) -> None:
        """Cleanup resources (close HTTP session, etc.)."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.stats["end_time"] = datetime.utcnow()
        logger.info(f"{self.platform.value} scraper cleanup completed")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers for API requests."""
        headers = {
            "User-Agent": "CommentScraper/1.0 (Academic Research)",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add platform-specific authentication
        if self.platform == Platform.YOUTUBE:
            headers["Authorization"] = f"Bearer {api_key_manager.get_api_key(Platform.YOUTUBE)}"
        elif self.platform == Platform.TWITTER:
            headers["Authorization"] = f"Bearer {api_key_manager.get_api_key(Platform.TWITTER)}"
        elif self.platform == Platform.INSTAGRAM:
            access_token = api_key_manager.get_api_key(Platform.INSTAGRAM)
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
        
        return headers
    
    async def _validate_api_key(self) -> None:
        """Validate API key for this platform."""
        if not api_key_manager.has_valid_key(self.platform):
            raise ValueError(f"Invalid or missing API key for {self.platform}")
        
        logger.info(f"API key validated for {self.platform}")
    
    async def scrape_comments(
        self,
        content_id: str,
        content_type: ContentType = ContentType.VIDEO,
        max_comments: int = 1000,
        include_replies: bool = True,
        language_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AsyncIterator[CommentBase]:
        """
        Scrape comments from content.
        
        Args:
            content_id: ID of the content to scrape comments from
            content_type: Type of content (video, post, etc.)
            max_comments: Maximum number of comments to scrape
            include_replies: Whether to include reply comments
            language_filter: Filter by language code (e.g., 'en')
            start_date: Only scrape comments after this date
            end_date: Only scrape comments before this date
            
        Yields:
            CommentBase objects for each scraped comment
            
        Raises:
            RateLimitExceeded: When rate limits are exceeded
            ValueError: For invalid parameters
            aiohttp.ClientError: For network/API errors
        """
        # Validate parameters
        if max_comments <= 0 or max_comments > 50000:
            raise ValueError("max_comments must be between 1 and 50000")
        
        if not content_id:
            raise ValueError("content_id is required")
        
        # Check daily limits for platforms that have them
        if self.platform == Platform.TIKTOK:
            can_proceed, message = rate_limiter.can_make_daily_request(self.platform)
            if not can_proceed:
                raise DailyLimitExceeded(self.platform, settings.TIKTOK_DAILY_LIMIT, 0)
        
        self.stats["start_time"] = datetime.utcnow()
        comments_scraped = 0
        
        logger.info(
            f"Starting comment scraping for {self.platform}:{content_id}. "
            f"Max: {max_comments}, Replies: {include_replies}"
        )
        
        try:
            # Use platform-specific implementation
            async for comment in self._scrape_comments_impl(
                content_id=content_id,
                content_type=content_type,
                max_comments=max_comments,
                include_replies=include_replies,
                language_filter=language_filter,
                start_date=start_date,
                end_date=end_date
            ):
                # Apply date filters
                if start_date and comment.created_at < start_date:
                    continue
                if end_date and comment.created_at > end_date:
                    continue
                
                # Apply language filter
                if language_filter and comment.language != language_filter:
                    continue
                
                comments_scraped += 1
                self.stats["comments_scraped"] = comments_scraped
                
                yield comment
                
                # Stop if we've reached the limit
                if comments_scraped >= max_comments:
                    logger.info(f"Reached max_comments limit: {max_comments}")
                    break
                
                # Progress logging
                if comments_scraped % 100 == 0:
                    logger.info(f"Scraped {comments_scraped} comments from {self.platform}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error during comment scraping: {e}")
            raise
        
        finally:
            logger.info(
                f"Completed scraping for {self.platform}:{content_id}. "
                f"Total: {comments_scraped}, Errors: {self.stats['errors']}"
            )
    
    @abstractmethod
    async def _scrape_comments_impl(
        self,
        content_id: str,
        content_type: ContentType,
        max_comments: int,
        include_replies: bool,
        language_filter: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> AsyncIterator[CommentBase]:
        """
        Platform-specific implementation of comment scraping.
        
        This method should be implemented by each platform scraper.
        
        Args:
            content_id: ID of the content to scrape comments from
            content_type: Type of content
            max_comments: Maximum comments to scrape
            include_replies: Whether to include replies
            language_filter: Language filter
            start_date: Start date filter
            end_date: End date filter
            
        Yields:
            CommentBase objects for each comment
        """
        pass
    
    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and error handling.
        
        Args:
            url: Request URL
            params: Query parameters
            method: HTTP method
            json_data: JSON data for POST requests
            retry_count: Current retry attempt
            
        Returns:
            JSON response data
            
        Raises:
            RateLimitExceeded: When rate limits are exceeded
            aiohttp.ClientError: For HTTP errors
        """
        max_retries = 3
        backoff_factor = 2 ** retry_count
        
        try:
            # Apply rate limiting
            endpoint = url.split("/")[-1] if url else "default"
            await rate_limiter.wait_for_capacity(self.platform, endpoint)
            
            # Make the request
            if not self.session:
                raise RuntimeError("HTTP session not initialized")
            
            self.stats["requests_made"] += 1
            
            kwargs = {"url": url}
            if params:
                kwargs["params"] = params
            if json_data:
                kwargs["json"] = json_data
            
            async with self.session.request(method, **kwargs) as response:
                # Handle rate limiting
                if response.status == 429:
                    self.stats["rate_limit_hits"] += 1
                    retry_after = response.headers.get("Retry-After", 60)
                    wait_time = float(retry_after)
                    
                    logger.warning(f"Rate limited by {self.platform}. Waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    
                    if retry_count < max_retries:
                        return await self._make_request(
                            url, params, method, json_data, retry_count + 1
                        )
                    else:
                        raise RateLimitExceeded(self.platform, wait_time, endpoint)
                
                # Handle other errors
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status}: {error_text}")
                    
                    if retry_count < max_retries and response.status >= 500:
                        wait_time = backoff_factor
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(
                            url, params, method, json_data, retry_count + 1
                        )
                    
                    response.raise_for_status()
                
                # Parse JSON response
                try:
                    response_data = await response.json()
                    return response_data
                except aiohttp.ContentTypeError:
                    logger.warning(f"Non-JSON response from {url}")
                    return {"error": "Non-JSON response"}
        
        except asyncio.TimeoutError:
            self.stats["errors"] += 1
            logger.error(f"Timeout while making request to {url}")
            if retry_count < max_retries:
                wait_time = backoff_factor
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    url, params, method, json_data, retry_count + 1
                )
            raise
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Request failed: {e}")
            if retry_count < max_retries:
                wait_time = backoff_factor
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    url, params, method, json_data, retry_count + 1
                )
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        stats = dict(self.stats)
        
        if stats["start_time"] and stats["end_time"]:
            duration = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["duration_seconds"] = duration
            stats["comments_per_second"] = stats["comments_scraped"] / duration if duration > 0 else 0
        
        return stats
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return rate_limiter.get_status(self.platform).dict()
    
    def validate_content_id(self, content_id: str) -> bool:
        """
        Validate content ID format for this platform.
        
        Args:
            content_id: Content ID to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Base implementation - platform scrapers should override
        return bool(content_id and len(content_id) > 0)
    
    async def test_connection(self) -> bool:
        """
        Test connection to platform API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Platform-specific test implementation
            test_url = self._get_test_url()
            response = await self._make_request(test_url)
            return "error" not in response
        except Exception as e:
            logger.error(f"Connection test failed for {self.platform}: {e}")
            return False
    
    @abstractmethod
    def _get_test_url(self) -> str:
        """Get test URL for connection testing."""
        pass