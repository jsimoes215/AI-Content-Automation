"""
TikTok Comment Scraper.

This module implements comment scraping for TikTok using the Research API,
which has strict daily limits and requires approval for research use cases.
"""

from typing import AsyncIterator, Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from .base_scraper import BaseCommentScraper
from ..models.comment_models import CommentBase, Platform, ContentType
from ..utils.rate_limiter import DailyLimitExceeded
from ..utils.api_key_manager import require_api_key
from ..config.settings import settings

import logging

logger = logging.getLogger(__name__)


class TikTokCommentScraper(BaseCommentScraper):
    """TikTok comment scraper using Research API."""
    
    def __init__(self):
        """Initialize TikTok scraper."""
        super().__init__(Platform.TIKTOK)
        self.client_key = None
        self.client_secret = None
        self.access_token = None
        self.daily_request_count = 0
        
    async def initialize(self) -> None:
        """Initialize TikTok scraper with client credentials."""
        await super().initialize()
        self.client_key = await require_api_key(Platform.TIKTOK)
        
        # Get client secret from environment
        from ..config.settings import settings
        self.client_secret = settings.TIKTOK_CLIENT_SECRET
        
        if not self.client_secret:
            raise ValueError("TikTok client secret not configured")
        
        # Get access token
        await self._get_access_token()
        
        logger.info("TikTok scraper initialized with Research API access")
    
    async def _get_access_token(self) -> None:
        """Get access token using client credentials."""
        try:
            url = f"{self.config['base_url']}/oauth/token/"
            
            data = {
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
            
            if not self.session:
                raise RuntimeError("HTTP session not initialized")
            
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get("access_token")
                    
                    if not self.access_token:
                        raise ValueError("No access token received from TikTok")
                    
                    logger.info("Successfully obtained TikTok access token")
                else:
                    error_text = await response.text()
                    raise ValueError(f"Failed to get TikTok token: {error_text}")
        
        except Exception as e:
            logger.error(f"Error getting TikTok access token: {e}")
            raise
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get TikTok-specific headers."""
        headers = {
            "Content-Type": "application/json",
            "X-Tt-Log-Accept": "client"
        }
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    def _get_test_url(self) -> str:
        """Get test URL for TikTok API connection."""
        return f"{self.config['base_url']}/research/user/info/"
    
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
        Implement TikTok-specific comment scraping.
        
        TikTok Research API has very limited comment access and strict daily limits.
        This implementation focuses on what is available through the Research API.
        """
        logger.info(f"Starting TikTok comment scraping for video: {content_id}")
        
        # Check daily limits before proceeding
        if self.daily_request_count >= settings.TIKTOK_DAILY_LIMIT:
            raise DailyLimitExceeded(Platform.TIKTOK, settings.TIKTOK_DAILY_LIMIT, self.daily_request_count)
        
        # Validate video ID format
        if not self._is_valid_tiktok_id(content_id):
            logger.error(f"Invalid TikTok video ID: {content_id}")
            raise ValueError(f"Invalid TikTok video ID: {content_id}")
        
        # Note: TikTok Research API has very limited comment capabilities
        # This implementation demonstrates the structure but may have limited functionality
        comments_scraped = 0
        
        try:
            # Get video information first
            video_info = await self._get_video_info(content_id)
            if not video_info:
                logger.warning(f"Video not found: {content_id}")
                return
            
            # TikTok Research API doesn't provide direct comment endpoints
            # This is a placeholder implementation showing the structure
            # In practice, you'd need to use alternative methods or wait for API updates
            
            logger.warning(
                "TikTok Research API has limited comment access. "
                "Consider using alternative data sources."
            )
            
            # For demonstration, we'll create a placeholder implementation
            # that would need to be updated when TikTok provides better comment access
            
            # Placeholder: This would be implemented when TikTok enables comment scraping
            async for comment in self._placeholder_comment_generation(content_id, max_comments):
                if comments_scraped >= max_comments:
                    break
                
                # Apply filters
                if language_filter and comment.language != language_filter:
                    continue
                
                if start_date and comment.created_at < start_date:
                    continue
                if end_date and comment.created_at > end_date:
                    continue
                
                yield comment
                comments_scraped += 1
                
                self.daily_request_count += 1
                
                if self.daily_request_count >= settings.TIKTOK_DAILY_LIMIT:
                    logger.warning("Daily request limit reached for TikTok Research API")
                    break
        
        except Exception as e:
            logger.error(f"Error scraping TikTok comments: {e}")
            raise
    
    async def _placeholder_comment_generation(self, video_id: str, max_comments: int) -> AsyncIterator[CommentBase]:
        """
        Placeholder implementation for comment generation.
        
        Note: This is a placeholder showing the structure. TikTok Research API
        currently doesn't provide comment endpoints. This would need to be updated
        when TikTok enables comment scraping capabilities.
        """
        # This would be replaced with actual API calls when available
        # For now, we simulate the structure
        
        placeholder_comments = [
            {
                "id": f"tiktok_comment_{i}",
                "text": f"Sample TikTok comment {i}",
                "user": {"nickname": f"user_{i}"},
                "create_time": int(datetime.utcnow().timestamp()) - i * 3600
            }
            for i in range(min(max_comments, 10))  # Generate placeholder data
        ]
        
        for comment_data in placeholder_comments:
            yield CommentBase(
                comment_id=comment_data["id"],
                platform=Platform.TIKTOK,
                content_id=video_id,
                text=comment_data["text"],
                username=comment_data["user"]["nickname"],
                created_at=datetime.fromtimestamp(comment_data["create_time"]),
                raw_data=comment_data
            )
    
    def _is_valid_tiktok_id(self, video_id: str) -> bool:
        """Validate TikTok video ID format."""
        # TikTok video IDs are numeric
        return video_id.isdigit() and len(video_id) >= 10
    
    async def _get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get TikTok video information."""
        try:
            url = f"{self.config['base_url']}/research/video/info/"
            
            params = {
                "video_id": video_id,
                "fields": "id,create_time,description,creator,video,statistics"
            }
            
            response = await self._make_request(url, params=params)
            
            if "error" in response:
                logger.error(f"TikTok API error: {response['error']}")
                return None
            
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"Error getting TikTok video info: {e}")
            return None
    
    async def search_videos(
        self, 
        query: str, 
        max_count: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for videos using TikTok Research API.
        
        Args:
            query: Search query
            max_count: Maximum number of videos to return
            start_date: Filter videos after this date
            end_date: Filter videos before this date
            
        Returns:
            List of video data
        """
        try:
            url = f"{self.config['base_url']}/research/video/query/"
            
            search_params = {
                "query": {
                    "operation_name": "videos_search",
                    "variables": {
                        "keyword": query,
                        "count": min(max_count, 100)
                    }
                }
            }
            
            if start_date:
                search_params["query"]["variables"]["start_date"] = start_date.strftime("%Y%m%d")
            if end_date:
                search_params["query"]["variables"]["end_date"] = end_date.strftime("%Y%m%d")
            
            response = await self._make_request(url, json_data=search_params)
            
            if "error" in response:
                logger.error(f"TikTok search API error: {response['error']}")
                return []
            
            return response.get("data", {}).get("videos", [])
            
        except Exception as e:
            logger.error(f"Error searching TikTok videos: {e}")
            return []
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from TikTok Research API."""
        try:
            url = f"{self.config['base_url']}/research/user/info/"
            
            params = {
                "user_id": user_id,
                "fields": "open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count"
            }
            
            response = await self._make_request(url, params=params)
            
            if "error" in response:
                logger.error(f"TikTok user API error: {response['error']}")
                return None
            
            return response.get("data", {})
            
        except Exception as e:
            logger.error(f"Error getting TikTok user info: {e}")
            return None
    
    async def get_comments_statistics(self, video_ids: List[str]) -> Dict[str, int]:
        """
        Get comment statistics for videos (if available).
        
        Note: TikTok Research API may not provide direct comment access.
        This method demonstrates the intended structure.
        """
        comment_stats = {}
        
        for video_id in video_ids:
            try:
                # This would need to be implemented when TikTok provides comment endpoints
                # For now, return placeholder data
                comment_stats[video_id] = 0
                
            except Exception as e:
                logger.error(f"Error getting comment stats for {video_id}: {e}")
                comment_stats[video_id] = 0
        
        return comment_stats
    
    async def get_daily_usage_report(self) -> Dict[str, Any]:
        """Get current daily usage report for TikTok Research API."""
        return {
            "platform": Platform.TIKTOK.value,
            "daily_limit": settings.TIKTOK_DAILY_LIMIT,
            "requests_used": self.daily_request_count,
            "requests_remaining": max(0, settings.TIKTOK_DAILY_LIMIT - self.daily_request_count),
            "reset_time": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        }
    
    async def test_connection(self) -> bool:
        """Test TikTok API connection."""
        try:
            # Test with a simple user info request
            url = f"{self.config['base_url']}/research/user/info/"
            response = await self._make_request(url, params={"user_id": "12345"})  # Test user ID
            
            # Even if the user doesn't exist, if we get a proper API response, connection works
            return "error" not in response or "User not found" in str(response)
            
        except Exception as e:
            logger.error(f"TikTok connection test failed: {e}")
            return False
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Get information about which features are supported by TikTok Research API."""
        return {
            "video_search": True,
            "user_info": True,
            "video_info": True,
            "comment_scraping": False,  # Currently not available
            "hashtag_search": True,
            "trend_analysis": True,
            "daily_limits": True
        }