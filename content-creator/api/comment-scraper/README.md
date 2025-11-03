# Comment Scraping System

A comprehensive, compliant comment scraping system for social media platforms with built-in analysis capabilities.

## Overview

This system provides production-ready comment scraping for YouTube, Twitter/X, Instagram, and TikTok with comprehensive features including:

- **Multi-platform Support**: YouTube Data API v3, Twitter API v2, Instagram Graph API, TikTok Research API
- **Rate Limiting & Compliance**: Platform-specific rate limiting, API key management, GDPR compliance
- **Advanced Analysis**: Sentiment analysis, topic extraction, intent detection, quality scoring
- **Batch Processing**: Concurrent scraping, data export in multiple formats
- **Error Handling**: Robust error handling, retry mechanisms, logging

## Architecture

```
api/comment-scraper/
├── config/               # Configuration settings and environment variables
├── models/               # Data models for comments, jobs, and analysis
├── platforms/            # Platform-specific scrapers
│   ├── base_scraper.py   # Base scraper interface
│   ├── youtube_scraper.py
│   ├── twitter_scraper.py
│   ├── instagram_scraper.py
│   └── tiktok_scraper.py
├── utils/                # Utility modules
│   ├── api_key_manager.py    # Secure API key management
│   ├── rate_limiter.py       # Platform-specific rate limiting
│   ├── comment_analyzer.py   # Sentiment and topic analysis
│   └── data_extractor.py     # Data export and filtering
├── scraper_factory.py    # Factory pattern for scraper creation
├── main_api.py          # Main API interface
└── __init__.py          # Package initialization
```

## Features

### 🔌 Multi-Platform Support

- **YouTube**: Full comment and reply scraping via Data API v3
- **Twitter/X**: Reply scraping (function as comments) via API v2
- **Instagram**: Comment scraping for Business/Creator accounts via Graph API
- **TikTok**: Limited functionality via Research API (experimental)

### 🛡️ Compliance & Security

- **Rate Limiting**: Platform-specific rate limits with automatic backoff
- **API Key Management**: Secure storage and validation of API credentials
- **GDPR Compliance**: Data minimization, retention policies, audit logging
- **Terms of Service**: Respectful scraping following platform guidelines

### 📊 Analysis Capabilities

- **Sentiment Analysis**: Using VADER (NLTK) with fallback methods
- **Topic Extraction**: Keyword and phrase extraction from comments
- **Intent Detection**: Question, complaint, praise, suggestion classification
- **Quality Scoring**: Engagement potential and comment quality assessment

### 🚀 Performance Features

- **Async Operations**: Full async/await support for concurrent processing
- **Batch Processing**: Multiple content scraping with concurrency control
- **Data Export**: JSON, CSV, Excel, and Parquet export formats
- **Caching**: Built-in caching for improved performance

## Installation

### Prerequisites

- Python 3.8+
- API keys for desired platforms (see Configuration)

### Install Dependencies

```bash
# Core dependencies
pip install aiohttp pydantic cryptography nltk pandas openpyxl pyarrow

# Optional for enhanced features
pip install redis  # For distributed caching
pip install sqlalchemy  # For database integration
```

### Install the Package

```bash
# If using as a development package
pip install -e /path/to/content-creator/api/comment-scraper/
```

## Configuration

### Environment Variables

Set the following environment variables for API access:

```bash
# YouTube
export YOUTUBE_API_KEY="your_youtube_api_key"

# Twitter/X
export TWITTER_BEARER_TOKEN="your_twitter_bearer_token"

# Instagram (Meta)
export INSTAGRAM_ACCESS_TOKEN="your_instagram_access_token"
export INSTAGRAM_APP_ID="your_instagram_app_id"
export INSTAGRAM_APP_SECRET="your_instagram_app_secret"

# TikTok
export TIKTOK_CLIENT_KEY="your_tiktok_client_key"
export TIKTOK_CLIENT_SECRET="your_tiktok_client_secret"

# Optional: Master encryption key
export COMMENT_SCRAPER_MASTER_KEY="your_master_key_for_encryption"
```

### API Key Setup

#### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Set quota limits and billing if needed

#### Twitter API v2
1. Apply for [Twitter Developer Account](https://developer.twitter.com/)
2. Create a new app
3. Generate Bearer Token (v2 API)
4. Ensure appropriate access level (Basic, Pro, or Enterprise)

#### Instagram Graph API
1. Create [Facebook App](https://developers.facebook.com/)
2. Add Instagram Basic Display or Instagram Graph API
3. Get access tokens through OAuth flow
4. Ensure Business/Creator account permissions

#### TikTok Research API
1. Apply for [TikTok Research Access](https://developers.tiktok.com/doc/research-api-faq)
2. Requires approval for research use cases
3. Limited to 1000 requests/day
4. Focus on research rather than commercial use

## Quick Start

### Basic Usage

```python
import asyncio
from comment_scraper import quick_scrape, Platform

async def main():
    # Scrape YouTube video comments
    result = await quick_scrape(
        platform=Platform.YOUTUBE,
        content_id="dQw4w9WgXcQ",  # Video ID or URL
        max_comments=100
    )
    
    if result['success']:
        print(f"Scraped {result['comments_scraped']} comments")
        for comment in result['comments']:
            print(f"- {comment.username}: {comment.text[:50]}...")
    else:
        print(f"Error: {result['error']}")

asyncio.run(main())
```

### Advanced Usage with Analysis

```python
import asyncio
from comment_scraper import CommentScrapingAPI, Platform

async def main():
    async with CommentScrapingAPI() as api:
        # Scrape and analyze comments
        result = await api.scrape_and_analyze_comments(
            platform=Platform.YOUTUBE,
            content_id="dQw4w9WgXcQ",
            max_comments=500,
            include_analysis=True,
            language_filter="en"
        )
        
        # Access analysis results
        if result['success']:
            analysis = result['analysis_stats']
            print(f"Sentiment Distribution: {analysis['sentiment_distribution']}")
            print(f"Top Topics: {analysis['top_topics']}")
            
            # High-quality comments
            high_quality = [
                c for c in result['comments'] 
                if c.quality_score > 0.7
            ]
            print(f"High Quality Comments: {len(high_quality)}")

asyncio.run(main())
```

### Batch Processing

```python
import asyncio
from comment_scraper import CommentScrapingAPI, Platform

async def main():
    async with CommentScrapingAPI() as api:
        # Batch scraping request
        requests = [
            {
                'platform': Platform.YOUTUBE,
                'content_id': 'dQw4w9WgXcQ',
                'max_comments': 100
            },
            {
                'platform': Platform.TWITTER,
                'content_id': '1234567890',
                'max_comments': 50
            }
        ]
        
        results = await api.batch_scrape(requests, max_concurrent=2)
        for i, result in enumerate(results):
            if result['success']:
                print(f"Request {i}: {result['comments_scraped']} comments")
            else:
                print(f"Request {i} failed: {result['error']}")

asyncio.run(main())
```

### Data Export

```python
import asyncio
from comment_scraper import CommentScrapingAPI, Platform

async def main():
    async with CommentScrapingAPI() as api:
        # Export to JSON
        result = await api.extract_and_export(
            platform=Platform.YOUTUBE,
            content_id="dQw4w9WgXcQ",
            output_format="json",
            output_file="youtube_comments.json",
            include_analysis=True
        )
        
        if result['success']:
            print(f"Exported to: {result['export']['file_path']}")

asyncio.run(main())
```

## Platform-Specific Usage

### YouTube

```python
# Support for video IDs or full URLs
video_id = "dQw4w9WgXcQ"  # Rick Roll
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

result = await api.scrape_youtube_video_comments(
    video_url_or_id=video_url,  # Automatically extracts ID
    max_comments=1000,
    include_replies=True
)
```

### Twitter/X

```python
# Replies are treated as comments
tweet_id = "1234567890"  # Numeric ID
tweet_url = "https://twitter.com/user/status/1234567890"

result = await api.scrape_twitter_replies(
    tweet_url_or_id=tweet_url,
    max_comments=500
)
```

### Instagram

```python
# Requires Business/Creator account permissions
media_id = "123456789012345_1234567890"  # Long numeric ID

result = await api.scrape_instagram_media_comments(
    media_url_or_id=media_id,
    max_comments=200,
    include_replies=True
)
```

### TikTok (Limited)

```python
# Limited functionality due to Research API constraints
result = await api.scrape_tiktok_video_comments(
    video_url_or_id="1234567890",
    max_comments=100
)
# Note: Results may be limited or unavailable
```

## Analysis Features

### Sentiment Analysis

The system provides sentiment analysis for each comment:

```python
comment = result['comments'][0]
print(f"Text: {comment.text}")
print(f"Sentiment: {comment.sentiment_label}")
print(f"Score: {comment.sentiment_score}")  # -1 to 1
print(f"Confidence: {comment.sentiment_confidence}")  # 0 to 1
```

### Topic Extraction

Extract main topics from comments:

```python
for comment in result['comments']:
    print(f"Topics: {comment.topics}")
    print(f"Topic Scores: {comment.topic_scores}")
```

### Quality Scoring

Each comment receives a quality score (0-1) based on:
- Text length and structure
- Engagement metrics
- User verification status
- Vocabulary diversity
- Spam detection

```python
for comment in result['comments']:
    print(f"Quality Score: {comment.quality_score}")
    print(f"Engagement Potential: {comment.engagement_potential}")
```

### Intent Detection

Classify user intent in comments:

```python
for comment in result['comments']:
    print(f"Intent: {comment.intent}")  # question, complaint, praise, etc.
    print(f"Intent Confidence: {comment.intent_confidence}")
```

## Filtering and Search

### Apply Filters During Scraping

```python
result = await api.scrape_and_analyze_comments(
    platform=Platform.YOUTUBE,
    content_id="dQw4w9WgXcQ",
    max_comments=1000,
    language_filter="en",  # English only
    start_date=datetime(2024, 1, 1),  # Only recent comments
    end_date=datetime(2024, 12, 31)
)
```

### Filter After Analysis

```python
# Filter by sentiment
positive_comments = [
    c for c in result['comments'] 
    if c.sentiment_label == SentimentLabel.POSITIVE
]

# Filter by quality
high_quality = [
    c for c in result['comments'] 
    if (c.quality_score or 0) > 0.7
]

# Filter by topics
topic_mentions = [
    c for c in result['comments'] 
    if 'tutorial' in c.topics
]
```

## System Administration

### Health Check

```python
async with CommentScrapingAPI() as api:
    health = await api.get_system_status()
    print(f"Status: {health['status']}")
    print(f"Available Platforms: {health['available_platforms']}")
```

### Configuration Validation

```python
async with CommentScrapingAPI() as api:
    validation = await api.validate_configuration()
    print(f"Configuration Valid: {validation['configuration_valid']}")
    for rec in validation['recommendations']:
        print(f"- {rec}")
```

### Rate Limit Monitoring

```python
from comment_scraper import rate_limiter

status = rate_limiter.get_status(Platform.YOUTUBE)
print(f"YouTube Rate Limit: {status.remaining}/{status.limit}")
print(f"Reset Time: {status.reset_time}")
```

## Advanced Features

### Trend Analysis

```python
# Analyze trending topics across multiple videos
trending = await api.get_trending_topics(
    platforms=[Platform.YOUTUBE, Platform.TWITTER],
    content_ids=['video1', 'video2', 'tweet1', 'tweet2'],
    time_range="7d",  # Last 7 days
    min_mentions=5
)
```

### Custom Analysis Pipeline

```python
# Extend analysis with custom logic
async def custom_analysis(comment):
    # Add your custom analysis here
    comment.custom_score = len(comment.text.split())  # Word count score
    return comment

# Process comments with custom analysis
async with CommentScrapingAPI() as api:
    result = await api.scrape_and_analyze_comments(
        platform=Platform.YOUTUBE,
        content_id="dQw4w9WgXcQ",
        max_comments=100,
        include_analysis=False  # We'll do custom analysis
    )
    
    # Apply custom analysis
    for comment in result['comments']:
        await custom_analysis(comment)
```

## Error Handling

### Graceful Error Handling

```python
try:
    result = await quick_scrape(
        platform=Platform.YOUTUBE,
        content_id="invalid_id"
    )
    
    if not result['success']:
        print(f"Failed to scrape: {result['error']}")
        # Handle specific error types
        if "rate limit" in result['error'].lower():
            print("Rate limit exceeded, retry later")
        elif "api key" in result['error'].lower():
            print("Invalid API key, check configuration")
            
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

The system includes automatic retry logic for:
- Rate limiting (with exponential backoff)
- Network timeouts
- Temporary server errors

## Performance Considerations

### Rate Limiting

Each platform has specific rate limits:
- YouTube: 100 requests/minute (default quota)
- Twitter: 75 requests/minute (Basic tier)
- Instagram: 200 requests/minute
- TikTok: 100 requests/minute, 1000 requests/day

### Concurrency

```python
# Configure concurrent operations
async with CommentScrapingAPI() as api:
    # Batch processing with concurrency control
    results = await api.batch_scrape(
        scraping_requests, 
        max_concurrent=3  # Max 3 concurrent requests
    )
```

### Caching

```python
# Results are cached for performance
# Cache TTL can be configured in settings
result = await api.scrape_and_analyze_comments(...)
# Subsequent calls within cache TTL will use cached data
```

## Compliance and Legal

### GDPR Compliance

The system includes GDPR compliance features:

- **Data Minimization**: Collect only necessary data
- **Purpose Limitation**: Define specific purposes for data collection
- **Retention Policies**: Automatic data deletion after retention period
- **Audit Logging**: Track all data processing activities
- **User Rights**: Support for access, deletion, and opt-out

### Platform Terms of Service

The system is designed to respect platform Terms of Service:

- **API-First Approach**: Prefer official APIs over scraping
- **Rate Limiting**: Respect platform rate limits
- **Data Usage**: Use data only for stated purposes
- **Commercial Use**: Some APIs restrict commercial usage

### Best Practices

1. **Respect Rate Limits**: Don't exceed platform quotas
2. **Handle Errors Gracefully**: Implement proper error handling
3. **Cache Results**: Reduce API calls through caching
4. **Monitor Usage**: Track API usage and costs
5. **Legal Review**: Consult legal counsel for production use

## Troubleshooting

### Common Issues

#### API Key Issues
```python
# Validate API keys
validation = await validate_setup()
if not validation['api_keys']['youtube']['configured']:
    print("YouTube API key not configured properly")
```

#### Rate Limit Errors
```python
# Check rate limit status
from comment_scraper import rate_limiter
status = rate_limiter.get_status(Platform.YOUTUBE)
if status.is_limited:
    print(f"Rate limited, retry after {status.retry_after} seconds")
```

#### Connection Issues
```python
# Test connections
health = await get_system_health()
for platform, status in health['api_keys'].items():
    if not status['connection_working']:
        print(f"Connection issue with {platform}")
```

### Debug Mode

```python
import logging
logging.getLogger('comment_scraper').setLevel(logging.DEBUG)

# Enable detailed logging
result = await quick_scrape(Platform.YOUTUBE, "video_id", max_comments=10)
```

## API Reference

See individual module documentation for detailed API reference:

- `comment_scraper.main_api` - Main API interface
- `comment_scraper.models` - Data models
- `comment_scraper.scraper_factory` - Scraper factory
- `comment_scraper.utils` - Utility modules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation
- Review the troubleshooting guide
- Open an issue on GitHub
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Multi-platform support (YouTube, Twitter, Instagram, TikTok)
- Sentiment analysis and topic extraction
- GDPR compliance features
- Batch processing capabilities
- Data export in multiple formats

---

**Note**: This system is designed for educational and research purposes. Always respect platform Terms of Service and applicable laws when using this software.