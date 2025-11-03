"""
Twitter (X) Comment Scraper.

This module implements comment scraping for Twitter using API v2,
focusing on tweet replies which function as comments.
"""

import re
from typing import AsyncIterator, Optional, Dict, Any, Set
from datetime import datetime
import asyncio

from .base_scraper import BaseCommentScraper
from ..models.comment_models import CommentBase, Platform, ContentType
from ..utils.api_key_manager import require_api_key

import logging

logger = logging.getLogger(__name__)


class TwitterCommentScraper(BaseCommentScraper):
    """Twitter (X) comment scraper using API v2."""
    
    def __init__(self):
        """Initialize Twitter scraper."""
        super().__init__(Platform.TWITTER)
        self.bearer_token = None
        
    async def initialize(self) -> None:
        """Initialize Twitter scraper with bearer token."""
        await super().initialize()
        self.bearer_token = await require_api_key(Platform.TWITTER)
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get Twitter-specific headers."""
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "CommentScraper/1.0"
        }
        return headers
    
    def _get_test_url(self) -> str:
        """Get test URL for Twitter API connection."""
        return f"{self.config['base_url']}/users/me"
    
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
        Implement Twitter-specific comment scraping.
        
        Twitter doesn't have traditional comments, but we can scrape
        replies to tweets which serve a similar function.
        """
        logger.info(f"Starting Twitter comment scraping for tweet: {content_id}")
        
        # Validate tweet ID format
        if not self._is_valid_twitter_id(content_id):
            logger.error(f"Invalid Twitter tweet ID: {content_id}")
            raise ValueError(f"Invalid Twitter tweet ID: {content_id}")
        
        # Verify the tweet exists
        if not await self._verify_tweet_exists(content_id):
            raise ValueError(f"Tweet not found or inaccessible: {content_id}")
        
        comments_scraped = 0
        processed_tweets: Set[str] = set()
        
        # Twitter API v2 search for replies
        search_query = f"conversation_id:{content_id} -is:retweet"
        
        # Add date filters if provided
        if start_date:
            search_query += f" since:{start_date.strftime('%Y-%m-%d')}"
        if end_date:
            search_query += f" until:{end_date.strftime('%Y-%m-%d')}"
        
        if language_filter:
            search_query += f" lang:{language_filter}"
        
        next_token = None
        
        while comments_scraped < max_comments:
            try:
                params = {
                    "query": search_query,
                    "max_results": min(100, max_comments - comments_scraped),
                    "tweet.fields": "author_id,created_at,public_metrics,referenced_tweets,context_annotations,lang",
                    "user.fields": "username,name,verified,public_metrics",
                    "expansions": "author_id,referenced_tweets.id",
                    "sort_order": "recency"
                }
                
                if next_token:
                    params["next_token"] = next_token
                
                url = f"{self.config['base_url']}/tweets/search/recent"
                response = await self._make_request(url, params=params)
                
                if "error" in response:
                    logger.error(f"Twitter API error: {response['error']}")
                    break
                
                tweets = response.get("data", [])
                users = {user["id"]: user for user in response.get("includes", {}).get("users", [])}
                
                if not tweets:
                    logger.info("No more replies available")
                    break
                
                # Process each tweet reply
                for tweet in tweets:
                    tweet_id = tweet.get("id")
                    
                    # Skip if already processed (can happen with retweets/quotes)
                    if tweet_id in processed_tweets:
                        continue
                    
                    if comments_scraped >= max_comments:
                        break
                    
                    # Verify this is actually a reply to our target tweet
                    referenced_tweets = tweet.get("referenced_tweets", [])
                    is_reply = any(
                        ref.get("type") == "replied_to" and ref.get("id") == content_id
                        for ref in referenced_tweets
                    )
                    
                    if not is_reply:
                        continue
                    
                    # Parse reply as comment
                    comment = await self._parse_tweet_reply(tweet, users.get(tweet.get("author_id")), content_id)
                    if comment:
                        processed_tweets.add(tweet_id)
                        yield comment
                        comments_scraped += 1
                
                # Check for next page
                next_token = response.get("meta", {}).get("next_token")
                if not next_token:
                    logger.info("No more pages available")
                    break
                
                logger.info(f"Scraped {comments_scraped} replies so far...")
                
                # Rate limiting: Twitter has strict rate limits
                await asyncio.sleep(1)  # Respect rate limits
                
            except Exception as e:
                logger.error(f"Error scraping Twitter replies: {e}")
                break
    
    async def _parse_tweet_reply(
        self, 
        tweet: Dict[str, Any], 
        author: Optional[Dict[str, Any]], 
        parent_tweet_id: str
    ) -> Optional[CommentBase]:
        """Parse Twitter reply as comment."""
        try:
            # Extract tweet details
            tweet_id = tweet.get("id")
            text = tweet.get("text", "")
            author_id = tweet.get("author_id")
            created_at_str = tweet.get("created_at")
            lang = tweet.get("lang", "en")
            
            # Parse timestamp
            created_at = self._parse_twitter_timestamp(created_at_str)
            
            # Extract engagement metrics
            metrics = tweet.get("public_metrics", {})
            like_count = metrics.get("like_count", 0)
            reply_count = metrics.get("reply_count", 0)
            retweet_count = metrics.get("retweet_count", 0)
            
            # Extract user information
            username = author.get("username", "") if author else ""
            display_name = author.get("name", "") if author else ""
            user_verified = author.get("verified", False) if author else False
            
            # Extract user metrics
            user_metrics = author.get("public_metrics", {}) if author else {}
            followers_count = user_metrics.get("followers_count", 0)
            
            # Create comment object
            comment = CommentBase(
                comment_id=tweet_id,
                platform=Platform.TWITTER,
                content_id=parent_tweet_id,
                parent_comment_id=None,  # Twitter doesn't have threaded replies in API v2
                text=text,
                language=lang,
                user_id=author_id,
                username=f"@{username}" if username else "",
                user_verified=user_verified,
                like_count=int(like_count) if like_count else 0,
                reply_count=int(reply_count) if reply_count else 0,
                created_at=created_at,
                raw_data={
                    "tweet": tweet,
                    "author": author,
                    "followers_count": followers_count
                }
            )
            
            return comment
            
        except Exception as e:
            logger.error(f"Error parsing Twitter reply: {e}")
            return None
    
    def _parse_twitter_timestamp(self, timestamp: str) -> datetime:
        """Parse Twitter timestamp to datetime."""
        if not timestamp:
            return datetime.utcnow()
        
        # Twitter uses ISO 8601 format: 2023-12-25T10:30:00.000Z
        try:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception:
            return datetime.utcnow()
    
    def _is_valid_twitter_id(self, tweet_id: str) -> bool:
        """Validate Twitter tweet ID format."""
        # Twitter IDs are numeric (as strings)
        return tweet_id.isdigit() and len(tweet_id) >= 10
    
    async def _verify_tweet_exists(self, tweet_id: str) -> bool:
        """Verify that a tweet exists and is accessible."""
        try:
            params = {
                "tweet.fields": "author_id,created_at,public_metrics,context_annotations",
                "expansions": "author_id"
            }
            
            url = f"{self.config['base_url']}/tweets/{tweet_id}"
            response = await self._make_request(url, params=params)
            
            if "error" in response:
                logger.error(f"Twitter API error verifying tweet: {response['error']}")
                return False
            
            if not response.get("data"):
                logger.warning(f"Tweet not found: {tweet_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying Twitter tweet {tweet_id}: {e}")
            return False
    
    async def get_tweet_info(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get tweet information for debugging."""
        try:
            params = {
                "tweet.fields": "author_id,created_at,public_metrics,context_annotations,lang,referenced_tweets",
                "user.fields": "username,name,verified,public_metrics",
                "expansions": "author_id,referenced_tweets.id"
            }
            
            url = f"{self.config['base_url']}/tweets/{tweet_id}"
            response = await self._make_request(url, params=params)
            
            if "error" in response or not response.get("data"):
                return None
            
            return {
                "tweet": response["data"],
                "includes": response.get("includes", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting Twitter tweet info: {e}")
            return None
    
    async def scrape_replies_by_url(self, tweet_url: str, **kwargs) -> AsyncIterator[CommentBase]:
        """
        Scrape replies from Twitter tweet URL.
        
        Args:
            tweet_url: Full Twitter URL or tweet ID
            **kwargs: Additional arguments for scrape_comments
            
        Yields:
            CommentBase objects
        """
        # Extract tweet ID from URL if needed
        tweet_id = self._extract_tweet_id(tweet_url)
        if not tweet_id:
            raise ValueError(f"Invalid Twitter URL: {tweet_url}")
        
        async for comment in self.scrape_comments(tweet_id, **kwargs):
            yield comment
    
    def _extract_tweet_id(self, url_or_id: str) -> Optional[str]:
        """Extract Twitter tweet ID from URL or return if already ID."""
        # If it's already a valid tweet ID, return it
        if self._is_valid_twitter_id(url_or_id):
            return url_or_id
        
        # Extract from Twitter URL patterns
        patterns = [
            r'twitter\.com/[^/]+/status/(\d+)',
            r'x\.com/[^/]+/status/(\d+)',
            r'(?:twitter\.com|x\.com)/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    async def search_tweets(self, query: str, max_results: int = 10) -> list:
        """
        Search for tweets matching a query.
        
        Args:
            query: Search query
            max_results: Maximum number of tweets to return
            
        Returns:
            List of tweet data
        """
        try:
            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "author_id,created_at,public_metrics,lang",
                "user.fields": "username,name,verified",
                "expansions": "author_id",
                "sort_order": "recency"
            }
            
            url = f"{self.config['base_url']}/tweets/search/recent"
            response = await self._make_request(url, params=params)
            
            return response.get("data", [])
            
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []
    
    def get_account_tweet_count_estimate(self, user_id: str, engagement_data: Dict[str, Any]) -> Optional[int]:
        """Estimate tweet count from user engagement data."""
        try:
            metrics = engagement_data.get("public_metrics", {})
            tweet_count = metrics.get("tweet_count")
            
            if tweet_count:
                return int(tweet_count)
                
        except Exception as e:
            logger.error(f"Error extracting tweet count: {e}")
        
        return None