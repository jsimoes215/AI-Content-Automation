# Platform Timing Service

A comprehensive platform timing optimization service that provides data-driven scheduling recommendations for social media platforms based on research-backed timing data and user preferences.

## Overview

The Platform Timing Service is designed to help content creators and social media managers optimize their posting schedules across multiple platforms by leveraging research data and implementing platform-specific optimization logic.

## Features

### Core Functionality
- **Platform Timing Data Loading**: Loads and stores platform timing data from research findings
- **Database Operations**: Provides CRUD operations for timing recommendations using Supabase
- **Platform-Specific Optimization**: Implements optimization logic for YouTube, TikTok, Instagram, Twitter/X, LinkedIn, and Facebook
- **Supabase Integration**: Full integration with Supabase for data persistence
- **API Client**: HTTP API client for scheduling recommendations

### Supported Platforms
- **YouTube**: Long-form videos, Shorts, audience segments (US East, India, Philippines)
- **TikTok**: Emerging creators, established creators, brands, general/segmented audiences
- **Instagram**: Feed posts, Reels, Stories, working professionals, Gen Z audiences
- **Twitter/X**: Brands, threads, business and general audiences
- **LinkedIn**: Individual users, company pages, business hours, global audiences
- **Facebook**: Feed posts, Reels, general and segmented audiences

### Key Components

#### 1. Platform Timing Data Model
- Platform-specific optimal posting days and hours
- Content format variations (long-form, short-form, reels, etc.)
- Audience segment targeting
- Posting frequency guidelines
- Research data source attribution

#### 2. User Scheduling Preferences
- Personal timezone settings
- Frequency constraints (minimum/maximum posts)
- Day and hour blacklists
- Quality thresholds
- Content format preferences
- Automation settings

#### 3. Optimization Algorithms
- Confidence scoring for recommended slots
- Platform-specific timing adjustments
- User preference integration
- Cross-platform schedule coordination
- Performance-based recommendations

#### 4. Performance Tracking
- KPI event logging
- Performance analytics
- A/B testing framework
- Optimization trial management

## Installation

### Requirements
- Python 3.8+
- PostgreSQL/Supabase
- Required packages (see requirements.txt)

### Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export API_KEY="your_api_key"
```

3. Initialize the database schema:
```sql
-- Run the schema from docs/scheduling_system/database_schema.md
```

## Usage

### Basic Usage

```python
from platform_timing_service import PlatformTimingService, UserSchedulingPreferences

# Initialize service
service = PlatformTimingService(
    supabase_url="your_supabase_url",
    supabase_key="your_supabase_key"
)

# Create user preferences
prefs = UserSchedulingPreferences(
    user_id="user_123",
    platform_id="youtube",
    timezone="America/New_York",
    posting_frequency_min=2,
    posting_frequency_max=4,
    days_blacklist=["sat", "sun"],
    content_format="long_form"
)

# Calculate optimal posting slots
recommendation = service.calculate_optimal_posting_slots(
    platform_id="youtube",
    user_preferences=prefs,
    content_format="long_form",
    audience_segment="us_east",
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=14),
    timezone_str="America/New_York"
)

print(f"Confidence Score: {recommendation.confidence_score:.2%}")
print(f"Recommended Slots: {len(recommendation.recommended_slots)}")
```

### Batch Optimization

```python
# Create batch requests for multiple platforms
requests = [
    {
        "platform_id": "youtube",
        "user_preferences": {...},
        "content_format": "long_form",
        "audience_segment": "us_east",
        "start_date": "2025-01-01",
        "end_date": "2025-01-14"
    },
    {
        "platform_id": "instagram",
        "user_preferences": {...},
        "content_format": "reels",
        "audience_segment": "general",
        "start_date": "2025-01-01",
        "end_date": "2025-01-14"
    }
]

# Get batch recommendations
recommendations = await service.batch_get_timing_recommendations(requests)
```

### Performance Tracking

```python
# Log performance KPI
await service.log_performance_kpi(
    video_job_id="video_123",
    platform_id="youtube",
    views=2500,
    impressions=8000,
    engagement_rate=0.075,
    watch_time_seconds=1800
)

# Get performance analytics
kpis = await service.get_performance_kpis("video_123")
```

### Optimization Trials

```python
# Create optimization trial
trial_id = await service.create_optimization_trial(
    user_id="user_123",
    hypothesis="Wednesday 4 PM posts perform better than Monday 4 PM posts",
    variants={
        "A": {"day": "wednesday", "time": "16:00"},
        "B": {"day": "monday", "time": "16:00"}
    },
    primary_kpi="engagement_rate",
    start_at=datetime.now(),
    end_at=datetime.now() + timedelta(days=28)
)
```

## Platform-Specific Guidelines

### YouTube
- **Best Days**: Monday, Tuesday, Wednesday, Thursday, Friday
- **Peak Hours**: 3-5 PM, 8-9 PM (weekday afternoons)
- **Frequency**: 2-3 posts per week (long-form), daily Shorts
- **Key Insight**: Wednesday 4 PM is the highest-performing slot

### TikTok
- **Best Days**: Tuesday, Wednesday, Thursday, Friday
- **Peak Hours**: 4-6 PM, 8-9 PM
- **Frequency**: 2-5 posts per week
- **Key Insight**: Wednesday is best day, Sunday 8 PM notable peak

### Instagram
- **Best Days**: Monday, Tuesday, Wednesday, Thursday, Friday
- **Peak Hours**: 10 AM-3 PM (feed), 9 AM-12 PM, 6-9 PM (reels)
- **Frequency**: 3-5 posts per week (feed), 3-5 reels per week
- **Key Insight**: Weekdays 10 AM-3 PM safest window

### Twitter/X
- **Best Days**: Tuesday, Wednesday, Thursday
- **Peak Hours**: 8 AM-12 PM
- **Frequency**: 3-5 posts per week
- **Key Insight**: Weekday mornings show consistent engagement

### LinkedIn
- **Best Days**: Tuesday, Wednesday, Thursday
- **Peak Hours**: 8 AM-2 PM
- **Frequency**: 2-3 posts per week (individuals), 3-5 (companies)
- **Key Insight**: Midweek midday windows are reliable

### Facebook
- **Best Days**: Monday, Tuesday, Wednesday, Thursday, Friday
- **Peak Hours**: 8 AM-6 PM
- **Frequency**: 3-5 posts per week
- **Key Insight**: Weekdays 8 AM-6 PM, lighter on Fridays

## API Client

### HTTP API Usage

```python
from platform_timing_service import SchedulingAPIClient

async with SchedulingAPIClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"
) as client:
    
    # Get recommendation via API
    response = await client.get_timing_recommendation(
        platform_id="youtube",
        user_preferences={
            "user_id": "user_123",
            "timezone": "America/New_York",
            "posting_frequency_min": 2,
            "posting_frequency_max": 4
        }
    )
```

## Database Schema Integration

The service integrates with the Supabase database schema defined in `docs/scheduling_system/database_schema.md`. Key tables include:

- `platform_timing_data`: Platform timing recommendations
- `user_scheduling_preferences`: User-specific settings
- `content_calendar`: Content planning calendars
- `content_schedule_items`: Individual scheduled posts
- `performance_kpi_events`: Performance analytics
- `optimization_trials`: A/B testing framework

## Configuration

### Environment Variables
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase service role key
- `API_KEY`: API authentication key
- `API_BASE_URL`: API base URL (default: http://localhost:8000)
- `LOGGING_LEVEL`: Logging level (default: INFO)
- `TIMEZONE_DEFAULT`: Default timezone (default: UTC)

### Configuration File
```python
from config import load_config_from_env

config = load_config_from_env()
validate_config(config)
```

## Testing

Run the validation tests:

```bash
python validate_platform_timing.py
```

Run comprehensive tests:

```bash
python test_platform_timing.py
```

## Examples

See `platform_timing_examples.py` for detailed usage examples including:
- Single platform optimization
- Multi-platform optimization
- Performance tracking
- User preferences management
- API client usage

## Architecture

### Service Classes
- `PlatformTimingService`: Main service class
- `UserSchedulingPreferences`: User preference management
- `ScheduleRecommendation`: Recommendation output format
- `SchedulingAPIClient`: HTTP API client

### Data Models
- `PlatformTimingData`: Platform timing data structure
- Performance tracking models
- User preference models

### Integration Points
- Supabase database integration
- Research data loading
- Performance analytics
- Optimization algorithms

## Performance Considerations

- **Caching**: Platform timing data can be cached for performance
- **Batch Operations**: Use batch endpoints for multiple platform optimization
- **Database Indexing**: Proper indexing on timing data tables
- **Rate Limiting**: Built-in rate limiting for API usage

## Research Data Sources

The service integrates research data from:
- Buffer 2025 studies
- SocialPilot 2025 analysis
- Sprout Social 2025 reports
- Platform-specific insights
- Large-scale posting analysis (1M+ posts)

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Ensure database schema compatibility
5. Validate with research data

## License

This project is part of the scheduling optimization system.

## Support

For issues and questions:
1. Check the validation tests
2. Review the example usage
3. Verify database schema compatibility
4. Ensure proper environment configuration