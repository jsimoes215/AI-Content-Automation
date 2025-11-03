"""
YouTube Comment Scraper.

This module implements comment scraping specifically for YouTube using
the YouTube Data API v3, ensuring compliance with platform terms of service.
"""

import re
from typing import AsyncIterator, Optional, Dict, Any
from datetime import datetime
import asyncio

from .base_scraper import BaseCommentScraper
from ..models.comment_models import CommentBase, Platform, ContentType
from ..utils.api_key_manager import require_api_key
from ..config.settings import settings

import logging

logger = logging.getLogger(__name__)


class YouTubeCommentScraper(BaseCommentScraper):
    """YouTube comment scraper using Data API v3."""
    
    def __init__(self):
        """Initialize YouTube scraper."""
        super().__init__(Platform.YOUTUBE)
        self.api_key = None
        
    async def initialize(self) -> None:
        """Initialize YouTube scraper with API key."""
        await super().initialize()
        self.api_key = await require_api_key(Platform.YOUTUBE)
    
    def _get_test_url(self) -> str:
        """Get test URL for YouTube API connection."""
        return f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key={self.api_key}"
    
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
        Implement YouTube-specific comment scraping.
        
        YouTube supports two comment endpoints:
        1. commentThreads.list - for top-level comments
        2. comments.list - for replies
        """
        logger.info(f"Starting YouTube comment scraping for video: {content_id}")
        
        # Validate video ID format
        if not self._is_valid_youtube_id(content_id):
            logger.error(f"Invalid YouTube video ID: {content_id}")
            raise ValueError(f"Invalid YouTube video ID: {content_id}")
        
        # First, verify the video exists
        if not await self._verify_video_exists(content_id):
            raise ValueError(f"Video not found or private: {content_id}")
        
        comments_scraped = 0
        next_page_token = None
        
        # Scrape top-level comments
        while comments_scraped < max_comments:
            try:
                params = {
                    "part": "snippet,replies",
                    "videoId": content_id,
                    "maxResults": min(100, max_comments - comments_scraped),
                    "order": "time",
                    "textFormat": "plainText"
                }
                
                if next_page_token:
                    params["pageToken"] = next_page_token
                
                if language_filter:
                    params["regionCode"] = language_filter.upper()
                
                url = f"{self.config['base_url']}/commentThreads"
                response = await self._make_request(url, params=params)
                
                if "error" in response:
                    logger.error(f"YouTube API error: {response['error']}")
                    break
                
                items = response.get("items", [])
                if not items:
                    logger.info("No more comments available")
                    break
                
                # Process each comment thread
                for item in items:
                    if comments_scraped >= max_comments:
                        break
                    
                    # Parse top-level comment
                    top_comment = await self._parse_comment_thread(item, content_id)
                    if top_comment:
                        yield top_comment
                        comments_scraped += 1
                    
                    # Parse replies if requested
                    if include_replies and "replies" in item:
                        replies = item["replies"]["comments"]
                        for reply in replies:
                            if comments_scraped >= max_comments:
                                break
                            
                            reply_comment = await self._parse_youtube_comment(reply, content_id, top_comment.comment_id)
                            if reply_comment:
                                yield reply_comment
                                comments_scraped += 1
                
                # Check for next page
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    logger.info("No more pages available")
                    break
                
                logger.info(f"Scraped {comments_scraped} comments so far...")
                
                # Rate limiting: YouTube API has quota costs
                await asyncio.sleep(0.1)  # Small delay to avoid hitting quota too fast
                
            except Exception as e:
                logger.error(f"Error scraping YouTube comments: {e}")
                break
    
    async def _parse_comment_thread(self, item: Dict[str, Any], content_id: str) -> Optional[CommentBase]:
        """Parse a YouTube comment thread item."""
        snippet = item.get("snippet", {})
        top_level_comment = snippet.get("topLevelComment", {})
        
        return await self._parse_youtube_comment(top_level_comment, content_id)
    
    async def _parse_youtube_comment(
        self, 
        comment_data: Dict[str, Any], 
        content_id: str, 
        parent_id: Optional[str] = None
    ) -> Optional[CommentBase]:
        """Parse individual YouTube comment."""
        try:
            snippet = comment_data.get("snippet", {})
            
            # Extract comment details
            comment_id = comment_data.get("id")
            text = snippet.get("textDisplay", "")
            author_name = snippet.get("authorDisplayName", "")
            author_channel_id = snippet.get("authorChannelId", {}).get("value")
            
            # Parse timestamp
            published_at = snippet.get("publishedAt")
            created_at = self._parse_youtube_timestamp(published_at)
            
            # Extract engagement metrics
            like_count = snippet.get("likeCount", 0)
            viewer_rating = snippet.get("viewerRating")
            
            # Determine if comment is positive/negative based on viewer rating
            is_positive = viewer_rating in ["like", "none"]
            
            # Clean text (YouTube HTML entities)
            clean_text = self._clean_youtube_text(text)
            
            # Create comment object
            comment = CommentBase(
                comment_id=comment_id,
                platform=Platform.YOUTUBE,
                content_id=content_id,
                parent_comment_id=parent_id,
                text=clean_text,
                language="en",  # YouTube API doesn't provide language directly
                user_id=author_channel_id,
                username=author_name,
                user_verified=snippet.get("authorIsChannelOwner", False),
                like_count=int(like_count) if like_count else 0,
                created_at=created_at,
                raw_data=comment_data
            )
            
            return comment
            
        except Exception as e:
            logger.error(f"Error parsing YouTube comment: {e}")
            return None
    
    def _clean_youtube_text(self, text: str) -> str:
        """Clean YouTube comment text."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace HTML entities
        html_entities = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&nbsp;": " "
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text.strip()
    
    def _parse_youtube_timestamp(self, timestamp: str) -> datetime:
        """Parse YouTube timestamp to datetime."""
        if not timestamp:
            return datetime.utcnow()
        
        # YouTube uses ISO 8601 format: 2023-12-25T10:30:00Z
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception:
            return datetime.utcnow()
    
    def _is_valid_youtube_id(self, video_id: str) -> bool:
        """Validate YouTube video ID format."""
        # YouTube video IDs are 11 characters, alphanumeric, dash, underscore
        pattern = r'^[a-zA-Z0-9_-]{11}$'
        return bool(re.match(pattern, video_id))
    
    async def _verify_video_exists(self, video_id: str) -> bool:
        """Verify that a YouTube video exists and is accessible."""
        try:
            params = {
                "part": "snippet,status",
                "id": video_id,
                "key": self.api_key
            }
            
            url = f"{self.config['base_url']}/videos"
            response = await self._make_request(url, params=params)
            
            if "error" in response:
                logger.error(f"YouTube API error verifying video: {response['error']}")
                return False
            
            items = response.get("items", [])
            if not items:
                logger.warning(f"Video not found: {video_id}")
                return False
            
            # Check if video is private or removed
            video = items[0]
            status = video.get("status", {})
            privacy_status = status.get("privacyStatus", "public")
            
            if privacy_status in ["private", "hidden"]:
                logger.warning(f"Video is {privacy_status}: {video_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying YouTube video {video_id}: {e}")
            return False
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video information for debugging."""
        try:
            params = {
                "part": "snippet,statistics,status",
                "id": video_id,
                "key": self.api_key
            }
            
            url = f"{self.config['base_url']}/videos"
            response = await self._make_request(url, params=params)
            
            if "error" in response or not response.get("items"):
                return None
            
            return response["items"][0]
            
        except Exception as e:
            logger.error(f"Error getting YouTube video info: {e}")
            return None
    
    def get_comment_count_estimate(self, video_id: str, engagement_data: Dict[str, Any]) -> Optional[int]:
        """Estimate comment count from video engagement data."""
        try:
            statistics = engagement_data.get("statistics", {})
            comment_count = statistics.get("commentCount")
            
            if comment_count:
                return int(comment_count)
            
        except Exception as e:
            logger.error(f"Error extracting comment count: {e}")
        
        return None
    
    async def scrape_comments_by_url(self, video_url: str, **kwargs) -> AsyncIterator[CommentBase]:
        """
        Scrape comments from YouTube video URL.
        
        Args:
            video_url: Full YouTube URL or video ID
            **kwargs: Additional arguments for scrape_comments
            
        Yields:
            CommentBase objects
        """
        # Extract video ID from URL if needed
        video_id = self._extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {video_url}")
        
        async for comment in self.scrape_comments(video_id, **kwargs):
            yield comment
    
    def _extract_video_id(self, url_or_id: str) -> Optional[str]:
        """Extract YouTube video ID from URL or return if already ID."""
        # If it's already a valid video ID, return it
        if self._is_valid_youtube_id(url_or_id):
            return url_or_id
        
        # Extract from YouTube URL patterns
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None