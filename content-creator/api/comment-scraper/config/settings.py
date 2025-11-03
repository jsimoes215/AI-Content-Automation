"""
Configuration settings for the Comment Scraping System.

This module contains all configuration settings including API keys,
rate limits, and platform-specific parameters. All settings are
loaded from environment variables for security.
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings, Field


class CommentScraperSettings(BaseSettings):
    """Configuration settings for comment scraping system."""
    
    # API Keys - Store in environment variables for security
    YOUTUBE_API_KEY: str = Field(default="", env="YOUTUBE_API_KEY")
    TWITTER_BEARER_TOKEN: str = Field(default="", env="TWITTER_BEARER_TOKEN") 
    INSTAGRAM_ACCESS_TOKEN: str = Field(default="", env="INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_APP_ID: str = Field(default="", env="INSTAGRAM_APP_ID")
    INSTAGRAM_APP_SECRET: str = Field(default="", env="INSTAGRAM_APP_SECRET")
    TIKTOK_CLIENT_KEY: str = Field(default="", env="TIKTOK_CLIENT_KEY")
    TIKTOK_CLIENT_SECRET: str = Field(default="", env="TIKTOK_CLIENT_SECRET")
    
    # Rate Limits (requests per minute unless specified)
    YOUTUBE_RATE_LIMIT: int = 100  # YouTube Data API default quota
    TWITTER_RATE_LIMIT: int = 75   # Twitter API v2 Basic tier
    INSTAGRAM_RATE_LIMIT: int = 200  # Instagram Graph API limit
    TIKTOK_RATE_LIMIT: int = 100   # TikTok Research API
    
    # Daily Request Limits
    TIKTOK_DAILY_LIMIT: int = 1000  # Fixed daily limit for Research API
    
    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///./comment_scraper.db")
    
    # Cache Settings
    REDIS_URL: str = Field(default="redis://localhost:6379")
    CACHE_TTL: int = 3600  # 1 hour default cache TTL
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    # Compliance Settings
    ENABLE_GDPR_COMPLIANCE: bool = True
    ENABLE_DATA_RETENTION: bool = True
    DEFAULT_RETENTION_DAYS: int = 90
    
    # Content Filtering
    MIN_COMMENT_LENGTH: int = 3
    MAX_COMMENT_LENGTH: int = 2000
    ENABLE_SPAM_FILTER: bool = True
    SPAM_THRESHOLD: float = 0.8
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        configs = {
            "youtube": {
                "api_key": self.YOUTUBE_API_KEY,
                "rate_limit": self.YOUTUBE_RATE_LIMIT,
                "base_url": "https://www.googleapis.com/youtube/v3",
                "endpoints": {
                    "comments": "/comments",
                    "comment_threads": "/commentThreads"
                }
            },
            "twitter": {
                "bearer_token": self.TWITTER_BEARER_TOKEN,
                "rate_limit": self.TWITTER_RATE_LIMIT,
                "base_url": "https://api.twitter.com/2",
                "endpoints": {
                    "tweets": "/tweets",
                    "comments": "/tweets/{id}/ replies"
                }
            },
            "instagram": {
                "access_token": self.INSTAGRAM_ACCESS_TOKEN,
                "app_id": self.INSTAGRAM_APP_ID,
                "app_secret": self.INSTAGRAM_APP_SECRET,
                "rate_limit": self.INSTAGRAM_RATE_LIMIT,
                "base_url": "https://graph.facebook.com/v18.0",
                "endpoints": {
                    "comments": "/{media-id}/comments"
                }
            },
            "tiktok": {
                "client_key": self.TIKTOK_CLIENT_KEY,
                "client_secret": self.TIKTOK_CLIENT_SECRET,
                "rate_limit": self.TIKTOK_RATE_LIMIT,
                "daily_limit": self.TIKTOK_DAILY_LIMIT,
                "base_url": "https://open.tiktokapis.com/v2",
                "endpoints": {
                    "research": "/research"
                }
            }
        }
        return configs.get(platform.lower(), {})
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are configured."""
        required_keys = {
            "youtube": self.YOUTUBE_API_KEY,
            "twitter": self.TWITTER_BEARER_TOKEN,
            "instagram": self.INSTAGRAM_ACCESS_TOKEN,
            "tiktok": self.TIKTOK_CLIENT_KEY
        }
        
        return {platform: bool(key) for platform, key in required_keys.items()}


# Global settings instance
settings = CommentScraperSettings()