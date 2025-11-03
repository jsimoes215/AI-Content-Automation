"""
Comment Scraping System for Social Media Platforms.

This package provides comprehensive comment scraping capabilities for
YouTube, Twitter/X, Instagram, and TikTok, with built-in analysis
and compliance features.

Features:
- Multi-platform comment scraping
- Rate limiting and API key management
- Sentiment analysis and topic extraction
- GDPR compliance and data retention
- Batch processing and data export
- Platform-specific optimizations

Supported Platforms:
- YouTube (Data API v3)
- Twitter/X (API v2)
- Instagram (Graph API)
- TikTok (Research API)

Usage:
    import asyncio
    from comment_scraper import quick_scrape, Platform
    
    async def main():
        # Quick scrape YouTube video
        result = await quick_scrape(
            Platform.YOUTUBE,
            "dQw4w9WgXcQ",
            max_comments=100
        )
        print(f"Scraped {result['comments_scraped']} comments")
    
    asyncio.run(main())

For advanced usage, use the CommentScrapingAPI class directly.
"""

from .main_api import (
    CommentScrapingAPI,
    comment_api,
    quick_scrape,
    get_system_health,
    validate_setup
)

from .models.comment_models import (
    Platform,
    CommentBase,
    CommentWithAnalysis,
    SentimentLabel,
    ContentType,
    ScrapingJob,
    ComplianceRecord
)

from .scraper_factory import (
    ScraperFactory,
    scraping_manager
)

from .utils.comment_analyzer import comment_analyzer
from .utils.data_extractor import data_extractor
from .utils.api_key_manager import api_key_manager
from .utils.rate_limiter import rate_limiter

__version__ = "1.0.0"
__author__ = "Comment Scraping System"
__email__ = "support@commentscraper.com"

__all__ = [
    # Main API
    'CommentScrapingAPI',
    'comment_api',
    'quick_scrape',
    'get_system_health',
    'validate_setup',
    
    # Models
    'Platform',
    'CommentBase',
    'CommentWithAnalysis',
    'SentimentLabel',
    'ContentType',
    'ScrapingJob',
    'ComplianceRecord',
    
    # Core Components
    'ScraperFactory',
    'scraping_manager',
    'comment_analyzer',
    'data_extractor',
    'api_key_manager',
    'rate_limiter'
]