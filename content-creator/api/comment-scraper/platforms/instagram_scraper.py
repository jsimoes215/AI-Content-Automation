"""
Instagram Comment Scraper.

This module implements comment scraping for Instagram using the Graph API,
focusing on Business and Creator accounts with proper permissions.
"""

from typing import AsyncIterator, Optional, Dict, Any
from datetime import datetime
import asyncio

from .base_scraper import BaseCommentScraper
from ..models.comment_models import CommentBase, Platform, ContentType
from ..utils.api_key_manager import require_api_key

import logging

logger = logging.getLogger(__name__)


class InstagramCommentScraper(BaseCommentScraper):
    """Instagram comment scraper using Graph API."""
    
    def __init__(self):
        """Initialize Instagram scraper."""
        super().__init__(Platform.INSTAGRAM)
        self.access_token = None
        
    async def initialize(self) -> None:
        """Initialize Instagram scraper with access token."""
        await super().initialize()
        self.access_token = await require_api_key(Platform.INSTAGRAM)
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get Instagram-specific headers."""
        headers = {
            "Content-Type": "application/json"
        }
        return headers
    
    def _get_test_url(self) -> str:
        """Get test URL for Instagram API connection."""
        return f"{self.config['base_url']}/me?access_token={self.access_token}"
    
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
        Implement Instagram-specific comment scraping.
        
        Instagram Graph API allows comment retrieval for Business/Creator accounts
        that the authenticated user owns or has been granted permissions for.
        """
        logger.info(f"Starting Instagram comment scraping for media: {content_id}")
        
        # Validate media ID format
        if not self._is_valid_instagram_id(content_id):
            logger.error(f"Invalid Instagram media ID: {content_id}")
            raise ValueError(f"Invalid Instagram media ID: {content_id}")
        
        # Verify the media exists and is accessible
        if not await self._verify_media_exists(content_id):
            raise ValueError(f"Media not found or inaccessible: {content_id}")
        
        comments_scraped = 0
        next_after = None
        
        while comments_scraped < max_comments:
            try:
                params = {
                    "fields": self._get_comment_fields(),
                    "limit": min(50, max_comments - comments_scraped),
                    "access_token": self.access_token
                }
                
                if next_after:
                    params["after"] = next_after
                
                # Order by time (newest first)
                params["order"] = "chronological"
                
                url = f"{self.config['base_url']}/{content_id}/comments"
                response = await self._make_request(url, params=params)
                
                if "error" in response:
                    logger.error(f"Instagram API error: {response['error']}")
                    break
                
                data = response.get("data", [])
                if not data:
                    logger.info("No more comments available")
                    break
                
                # Process each comment
                for comment in data:
                    if comments_scraped >= max_comments:
                        break
                    
                    # Parse comment
                    parsed_comment = await self._parse_instagram_comment(comment, content_id)
                    if parsed_comment:
                        # Apply date filters
                        if start_date and parsed_comment.created_at < start_date:
                            continue
                        if end_date and parsed_comment.created_at > end_date:
                            continue
                        
                        yield parsed_comment
                        comments_scraped += 1
                    
                    # Get replies if requested
                    if include_replies and comment.get("replies", {}).get("data"):
                        async for reply in self._scrape_replies(comment["id"], content_id, max_comments - comments_scraped):
                            if comments_scraped >= max_comments:
                                break
                            
                            # Apply date filters to replies
                            if start_date and reply.created_at < start_date:
                                continue
                            if end_date and reply.created_at > end_date:
                                continue
                            
                            yield reply
                            comments_scraped += 1
                
                # Check for pagination
                paging = response.get("paging", {})
                cursors = paging.get("cursors", {})
                next_after = cursors.get("after")
                
                if not next_after:
                    logger.info("No more pages available")
                    break
                
                logger.info(f"Scraped {comments_scraped} comments so far...")
                
                # Rate limiting for Instagram Graph API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error scraping Instagram comments: {e}")
                break
    
    async def _scrape_replies(self, comment_id: str, parent_media_id: str, max_replies: int) -> AsyncIterator[CommentBase]:
        """Scrape replies to a specific comment."""
        replies_scraped = 0
        next_after = None
        
        while replies_scraped < max_replies:
            try:
                params = {
                    "fields": self._get_comment_fields(),
                    "limit": min(25, max_replies - replies_scraped),
                    "access_token": self.access_token
                }
                
                if next_after:
                    params["after"] = next_after
                
                url = f"{self.config['base_url']}/{comment_id}/replies"
                response = await self._make_request(url, params=params)
                
                if "error" in response:
                    logger.error(f"Instagram API error fetching replies: {response['error']}")
                    break
                
                data = response.get("data", [])
                if not data:
                    break
                
                for reply in data:
                    parsed_reply = await self._parse_instagram_comment(reply, parent_media_id, comment_id)
                    if parsed_reply:
                        yield parsed_reply
                        replies_scraped += 1
                
                # Check for pagination
                paging = response.get("paging", {})
                cursors = paging.get("cursors", {})
                next_after = cursors.get("after")
                
                if not next_after:
                    break
                
                await asyncio.sleep(0.2)  # Rate limiting for replies
                
            except Exception as e:
                logger.error(f"Error scraping Instagram replies: {e}")
                break
    
    def _get_comment_fields(self) -> str:
        """Get fields to request for comments."""
        return ",".join([
            "id",
            "text",
            "timestamp",
            "username",
            "like_count",
            "replies",
            "replies_count"
        ])
    
    async def _parse_instagram_comment(
        self, 
        comment_data: Dict[str, Any], 
        media_id: str, 
        parent_id: Optional[str] = None
    ) -> Optional[CommentBase]:
        """Parse Instagram comment data."""
        try:
            # Extract comment details
            comment_id = comment_data.get("id")
            text = comment_data.get("text", "")
            username = comment_data.get("username", "")
            timestamp = comment_data.get("timestamp")
            like_count = comment_data.get("like_count", 0)
            
            # Parse timestamp
            created_at = self._parse_instagram_timestamp(timestamp)
            
            # Create comment object
            comment = CommentBase(
                comment_id=comment_id,
                platform=Platform.INSTAGRAM,
                content_id=media_id,
                parent_comment_id=parent_id,
                text=text,
                language="en",  # Instagram API doesn't provide language directly
                username=username,
                user_verified=False,  # Instagram API doesn't provide verification status in comments
                like_count=int(like_count) if like_count else 0,
                created_at=created_at,
                raw_data=comment_data
            )
            
            return comment
            
        except Exception as e:
            logger.error(f"Error parsing Instagram comment: {e}")
            return None
    
    def _parse_instagram_timestamp(self, timestamp: str) -> datetime:
        """Parse Instagram timestamp to datetime."""
        if not timestamp:
            return datetime.utcnow()
        
        # Instagram timestamps are in Unix timestamp format (seconds)
        try:
            return datetime.fromtimestamp(int(timestamp))
        except Exception:
            return datetime.utcnow()
    
    def _is_valid_instagram_id(self, media_id: str) -> bool:
        """Validate Instagram media ID format."""
        # Instagram media IDs are numeric
        return media_id.isdigit() and len(media_id) >= 10
    
    async def _verify_media_exists(self, media_id: str) -> bool:
        """Verify that media exists and is accessible."""
        try:
            params = {
                "fields": "id,media_type,media_url,permalink,timestamp,username",
                "access_token": self.access_token
            }
            
            url = f"{self.config['base_url']}/{media_id}"
            response = await self._make_request(url, params=params)
            
            if "error" in response:
                logger.error(f"Instagram API error verifying media: {response['error']}")
                return False
            
            if not response.get("id"):
                logger.warning(f"Media not found: {media_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying Instagram media {media_id}: {e}")
            return False
    
    async def get_media_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media information for debugging."""
        try:
            params = {
                "fields": "id,media_type,media_url,permalink,timestamp,username,like_count,comments_count",
                "access_token": self.access_token
            }
            
            url = f"{self.config['base_url']}/{media_id}"
            response = await self._make_request(url, params=params)
            
            if "error" in response or not response.get("id"):
                return None
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting Instagram media info: {e}")
            return None
    
    async def get_user_media(self, user_id: str, media_type: Optional[str] = None, limit: int = 25) -> list:
        """
        Get media for a user (requires user permissions).
        
        Args:
            user_id: Instagram user ID
            media_type: Filter by media type (IMAGE, VIDEO, CAROUSEL_ALBUM)
            limit: Maximum number of media to return
            
        Returns:
            List of media data
        """
        try:
            params = {
                "fields": "id,media_type,media_url,permalink,timestamp,username,like_count,comments_count",
                "limit": min(limit, 50),
                "access_token": self.access_token
            }
            
            if media_type:
                params["media_type"] = media_type
            
            url = f"{self.config['base_url']}/{user_id}/media"
            response = await self._make_request(url, params=params)
            
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Error getting user media: {e}")
            return []
    
    async def scrape_comments_by_url(self, media_url: str, **kwargs) -> AsyncIterator[CommentBase]:
        """
        Scrape comments from Instagram media URL.
        
        Args:
            media_url: Instagram media URL
            **kwargs: Additional arguments for scrape_comments
            
        Yields:
            CommentBase objects
        """
        # Extract media ID from URL if needed
        media_id = self._extract_media_id(media_url)
        if not media_id:
            raise ValueError(f"Invalid Instagram URL: {media_url}")
        
        async for comment in self.scrape_comments(media_id, **kwargs):
            yield comment
    
    def _extract_media_id(self, url_or_id: str) -> Optional[str]:
        """Extract Instagram media ID from URL or return if already ID."""
        # If it's already a valid media ID, return it
        if self._is_valid_instagram_id(url_or_id):
            return url_or_id
        
        # Extract from Instagram URL patterns
        import re
        patterns = [
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/tv/([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                # Instagram shortcodes need to be resolved to media IDs
                # This would require additional API calls
                return None  # Placeholder - would need shortcode resolution
        
        return None
    
    def get_comment_count_estimate(self, media_id: str, media_data: Dict[str, Any]) -> Optional[int]:
        """Estimate comment count from media engagement data."""
        try:
            comments_count = media_data.get("comments_count")
            
            if comments_count:
                return int(comments_count)
                
        except Exception as e:
            logger.error(f"Error extracting comment count: {e}")
        
        return None
    
    async def moderate_comment(self, comment_id: str, action: str) -> bool:
        """
        Moderate a comment (requires proper permissions).
        
        Args:
            comment_id: Comment ID to moderate
            action: Action to take ("DELETE", "HIDE", "UNHIDE")
            
        Returns:
            True if action was successful
        """
        try:
            # Note: This requires additional permissions for comment moderation
            logger.warning("Comment moderation requires special Instagram permissions")
            return False
            
        except Exception as e:
            logger.error(f"Error moderating Instagram comment: {e}")
            return False