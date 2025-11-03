"""
Rate Limiting System for Comment Scraping.

This module implements comprehensive rate limiting across all platforms
to ensure compliance with API terms of service and prevent service abuse.
"""

import asyncio
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging

from ..models.comment_models import Platform, RateLimitInfo
from ..config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitWindow:
    """Rate limit tracking window."""
    requests: deque = field(default_factory=deque)
    limit: int = 100  # requests per window
    window_seconds: int = 60  # window size in seconds
    
    def can_make_request(self) -> bool:
        """Check if a request can be made within rate limits."""
        now = time.time()
        
        # Remove old requests outside the window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        # Check if under limit
        return len(self.requests) < self.limit
    
    def record_request(self) -> None:
        """Record a new request."""
        self.requests.append(time.time())
    
    def time_until_reset(self) -> float:
        """Get seconds until rate limit resets."""
        if not self.requests:
            return 0
        
        oldest_request = self.requests[0]
        reset_time = oldest_request + self.window_seconds
        return max(0, reset_time - time.time())
    
    def remaining_requests(self) -> int:
        """Get number of requests remaining in current window."""
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        return max(0, self.limit - len(self.requests))


class RateLimiter:
    """Comprehensive rate limiter for multiple platforms."""
    
    def __init__(self):
        """Initialize the rate limiter with platform configurations."""
        self._platform_limits: Dict[Platform, RateLimitWindow] = {}
        self._endpoint_limits: Dict[str, RateLimitWindow] = defaultdict(lambda: RateLimitWindow())
        self._last_reset: Dict[Platform, datetime] = {}
        self._lock = asyncio.Lock()
        
        # Initialize platform-specific limits
        self._initialize_limits()
        
        logger.info("Rate limiter initialized with platform configurations")
    
    def _initialize_limits(self) -> None:
        """Initialize rate limit windows for all platforms."""
        platform_configs = {
            Platform.YOUTUBE: {
                "limit": settings.YOUTUBE_RATE_LIMIT,
                "window_seconds": 60
            },
            Platform.TWITTER: {
                "limit": settings.TWITTER_RATE_LIMIT,
                "window_seconds": 60
            },
            Platform.INSTAGRAM: {
                "limit": settings.INSTAGRAM_RATE_LIMIT,
                "window_seconds": 60
            },
            Platform.TIKTOK: {
                "limit": settings.TIKTOK_RATE_LIMIT,
                "window_seconds": 60
            }
        }
        
        for platform, config in platform_configs.items():
            self._platform_limits[platform] = RateLimitWindow(
                limit=config["limit"],
                window_seconds=config["window_seconds"]
            )
            self._last_reset[platform] = datetime.utcnow()
    
    async def acquire(self, platform: Platform, endpoint: str = "default") -> Tuple[bool, float]:
        """
        Acquire permission to make a request.
        
        Args:
            platform: Platform to make request for
            endpoint: API endpoint being accessed
            
        Returns:
            Tuple of (can_proceed, wait_time_seconds)
        """
        async with self._lock:
            platform_window = self._platform_limits.get(platform)
            endpoint_window = self._endpoint_limits.get(endpoint)
            
            if not platform_window:
                logger.warning(f"No rate limit configured for platform {platform}")
                return True, 0
            
            # Check platform-level limit
            if not platform_window.can_make_request():
                wait_time = platform_window.time_until_reset()
                logger.info(
                    f"Rate limit hit for {platform}. Waiting {wait_time:.2f} seconds"
                )
                return False, wait_time
            
            # Check endpoint-specific limit if configured
            if endpoint_window and not endpoint_window.can_make_request():
                wait_time = endpoint_window.time_until_reset()
                logger.info(
                    f"Rate limit hit for endpoint {endpoint}. Waiting {wait_time:.2f} seconds"
                )
                return False, wait_time
            
            # Record the request
            platform_window.record_request()
            if endpoint_window:
                endpoint_window.record_request()
            
            logger.debug(f"Request allowed for {platform}:{endpoint}")
            return True, 0
    
    async def wait_for_capacity(self, platform: Platform, endpoint: str = "default") -> None:
        """Wait until capacity is available for a request."""
        can_proceed, wait_time = await self.acquire(platform, endpoint)
        
        if not can_proceed:
            logger.info(f"Waiting {wait_time:.2f} seconds for rate limit reset")
            await asyncio.sleep(wait_time)
    
    def get_status(self, platform: Platform) -> Optional[RateLimitInfo]:
        """Get current rate limit status for a platform."""
        platform_window = self._platform_limits.get(platform)
        
        if not platform_window:
            return None
        
        return RateLimitInfo(
            platform=platform,
            endpoint="all",
            limit=platform_window.limit,
            remaining=platform_window.remaining_requests(),
            reset_time=datetime.utcnow() + timedelta(seconds=platform_window.time_until_reset()),
            is_limited=platform_window.remaining_requests() <= 0,
            retry_after=int(platform_window.time_until_reset()) if platform_window.remaining_requests() <= 0 else None
        )
    
    def get_all_status(self) -> Dict[Platform, RateLimitInfo]:
        """Get rate limit status for all platforms."""
        return {platform: self.get_status(platform) for platform in Platform}
    
    def reset_limits(self, platform: Platform) -> None:
        """Manually reset rate limits for a platform (used for testing)."""
        if platform in self._platform_limits:
            self._platform_limits[platform].requests.clear()
            self._last_reset[platform] = datetime.utcnow()
            logger.info(f"Rate limits reset for {platform}")
    
    def get_daily_usage(self, platform: Platform) -> int:
        """Get estimated daily usage for platforms with daily limits (e.g., TikTok)."""
        if platform == Platform.TIKTOK:
            # TikTok Research API has a fixed daily limit of 1000 requests
            # This is a simplified calculation - in practice you'd track this properly
            platform_window = self._platform_limits.get(platform)
            if platform_window:
                return len(platform_window.requests)
        return 0
    
    def can_make_daily_request(self, platform: Platform) -> Tuple[bool, str]:
        """Check if daily request limits allow for a new request."""
        if platform == Platform.TIKTOK:
            daily_usage = self.get_daily_usage(platform)
            if daily_usage >= settings.TIKTOK_DAILY_LIMIT:
                return False, f"Daily limit reached ({daily_usage}/{settings.TIKTOK_DAILY_LIMIT})"
        
        return True, ""


class RateLimitMiddleware:
    """Middleware for handling rate limiting in API requests."""
    
    def __init__(self, rate_limiter: RateLimiter):
        """Initialize with rate limiter instance."""
        self.rate_limiter = rate_limiter
    
    async def handle_request(self, platform: Platform, endpoint: str = "default") -> None:
        """
        Handle a request with rate limiting.
        
        Args:
            platform: Platform for the request
            endpoint: API endpoint being accessed
            
        Raises:
            RateLimitExceeded: When rate limit is exceeded
        """
        can_proceed, wait_time = await self.rate_limiter.acquire(platform, endpoint)
        
        if not can_proceed:
            # This could be raised as a custom exception
            logger.warning(f"Rate limit exceeded for {platform}:{endpoint}, wait time: {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            # Retry after waiting
            await self.rate_limiter.wait_for_capacity(platform, endpoint)
    
    async def handle_batch(self, platform: Platform, requests: list, endpoint: str = "default") -> None:
        """
        Handle a batch of requests with rate limiting.
        
        Args:
            platform: Platform for all requests
            requests: List of request data
            endpoint: API endpoint being accessed
        """
        logger.info(f"Processing batch of {len(requests)} requests for {platform}")
        
        for i, request_data in enumerate(requests):
            await self.handle_request(platform, endpoint)
            
            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(requests)} requests for {platform}")
        
        logger.info(f"Completed batch processing for {platform}")


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitExceeded(Exception):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, platform: Platform, wait_time: float, endpoint: str = "default"):
        self.platform = platform
        self.wait_time = wait_time
        self.endpoint = endpoint
        super().__init__(
            f"Rate limit exceeded for {platform}:{endpoint}. "
            f"Wait {wait_time:.2f} seconds before retrying."
        )


class DailyLimitExceeded(Exception):
    """Exception raised when daily request limits are exceeded."""
    
    def __init__(self, platform: Platform, limit: int, used: int):
        self.platform = platform
        self.limit = limit
        self.used = used
        super().__init__(
            f"Daily request limit exceeded for {platform}. "
            f"Used {used}/{limit} requests today."
        )