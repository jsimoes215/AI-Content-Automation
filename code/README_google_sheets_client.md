# Google Sheets API v4 Client for AI Content Automation System

A comprehensive, production-ready Google Sheets API v4 client designed specifically for the AI Content Automation system. This client provides robust service account authentication, efficient batch operations, rate limiting compliance, and comprehensive error handling.

## 🚀 Features

### Core Functionality
- **Service Account Authentication**: Secure authentication using Google service accounts
- **Flexible Data Reading**: Read data with customizable rendering options (FORMULA, UNFORMATTED_VALUE, FORMATTED_VALUE)
- **Batch Operations**: Efficient batch read and write operations to minimize API calls
- **Range Operations**: Support for A1 notation ranges, named ranges, and complex cell selections
- **Atomic Updates**: Ensure data consistency with atomic batch updates

### Rate Limiting & Performance
- **Rate Limiting Compliance**: Respects Google Sheets API quotas (300 requests/minute per project, 60 per user)
- **Exponential Backoff**: Intelligent retry mechanism with jitter for handling 429 errors
- **Request Optimization**: Compressed responses and partial field selection
- **Monitoring**: Built-in rate limit monitoring and health checks

### Error Handling & Reliability
- **Comprehensive Error Handling**: Graceful handling of HTTP errors, network issues, and API failures
- **Idempotent Operations**: Safe retry mechanisms for read and update operations
- **Detailed Logging**: Structured logging for debugging and monitoring
- **Connection Management**: Proper resource cleanup and connection handling

## 📋 Table of Contents

1. [Installation](#installation)
2. [Setup & Configuration](#setup--configuration)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Integration Examples](#integration-examples)
6. [Rate Limiting](#rate-limiting)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## 📦 Installation

### Requirements
- Python 3.8+
- Google Cloud Platform account
- Service account credentials

### Install Dependencies

```bash
pip install -r requirements-google-sheets.txt
```

Required packages:
- `google-api-python-client>=2.108.0`
- `google-auth>=2.22.0`
- `google-auth-oauthlib>=1.1.0`
- `google-auth-httplib2>=0.1.1`

## ⚙️ Setup & Configuration

### 1. Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create service account credentials
5. Download the JSON key file

### 2. Configure Environment

Set environment variables:

```bash
# Required: Path to service account JSON file
export GOOGLE_SHEETS_CREDENTIALS_PATH="/path/to/service-account.json"

# Optional: Rate limiting configuration
export GOOGLE_SHEETS_MAX_PER_MINUTE=300
export GOOGLE_SHEETS_MAX_PER_USER=60
export GOOGLE_SHEETS_TIMEOUT=180
export GOOGLE_SHEETS_MAX_PAYLOAD_MB=2
export GOOGLE_SHEETS_BACKOFF_BASE=1.0
export GOOGLE_SHEETS_BACKOFF_MULTIPLIER=2.0
export GOOGLE_SHEETS_BACKOFF_MAX=60.0
export GOOGLE_SHEETS_MAX_RETRIES=5
```

### 3. Share Spreadsheets

Share your target Google Sheets with the service account email address (found in the JSON credentials file).

## 🚀 Quick Start

### Basic Usage

```python
from google_sheets_client import GoogleSheetsClient, SheetRange, ValueRenderOption
from google_sheets_config import get_client_config, create_client_from_config

# Create client
config = get_client_config()
client = create_client_from_config(config)

# Read data from a sheet
spreadsheet_id = "your-spreadsheet-id"
data = client.get_sheet_data(
    spreadsheet_id=spreadsheet_id,
    sheet_name="Sheet1",
    value_render_option=ValueRenderOption.FORMATTED_VALUE
)
print(f"Read {len(data)} rows")

# Write data to a range
range_spec = SheetRange(sheet_name="Sheet1", start_row=1, end_row=2, start_col="A", end_col="C")
client.write_values(
    spreadsheet_id=spreadsheet_id,
    sheet_range=range_spec,
    values=[["Name", "Value", "Status"], ["Test", "123", "Active"]]
)

client.close()
```

### Configuration-Based Setup

```python
from google_sheets_client import create_client_from_config
from google_sheets_config import get_client_config

# Get configuration
config = get_client_config()

# Create client from config
client = create_client_from_config(config)

# Use the client...
client.close()
```

## 📖 API Reference

### Classes

#### `GoogleSheetsClient`
Main client class for Google Sheets API operations.

**Methods:**
- `get_sheet_data()` - Read all data from a sheet
- `get_rows_in_range()` - Read data from specific range
- `get_multiple_ranges()` - Read multiple ranges efficiently
- `write_values()` - Write data to specific range
- `append_values()` - Append data to end of sheet
- `batch_update()` - Perform atomic batch operations
- `create_sheet()` - Create new sheet
- `get_spreadsheet_metadata()` - Get spreadsheet metadata
- `health_check()` - Verify client functionality
- `get_rate_limit_status()` - Check current rate limits

#### `SheetRange`
Represents a range in a Google Sheet.

**Properties:**
- `sheet_name` - Name of the sheet
- `start_row`, `end_row` - Row boundaries (1-indexed)
- `start_col`, `end_col` - Column boundaries (A, B, C, etc.)

**Methods:**
- `to_a1_notation()` - Convert to A1 notation

#### `RateLimitConfig`
Configuration for rate limiting behavior.

**Properties:**
- `max_requests_per_minute` - Project-level quota
- `max_requests_per_minute_per_user` - User-level quota
- `request_timeout_seconds` - Request timeout
- `max_payload_size_mb` - Maximum payload size
- `backoff_*` - Exponential backoff parameters

### Enums

#### `ValueRenderOption`
- `FORMULA` - Returns formulas as entered
- `UNFORMATTED_VALUE` - Returns computed values without formatting
- `FORMATTED_VALUE` - Returns displayed strings

#### `DateTimeRenderOption`
- `SERIAL_NUMBER` - Returns dates/times as serial numbers
- `FORMATTED_STRING` - Returns dates/times as formatted strings

#### `ValueInputOption`
- `RAW` - Values stored as entered
- `USER_ENTERED` - Values parsed and evaluated

## 🔧 Integration Examples

### Content Tracking Integration

```python
from google_sheets_examples import ContentTrackingIntegration

# Initialize with your client and spreadsheet
tracking = ContentTrackingIntegration(client, spreadsheet_id)

# Create tracking sheet
tracking.create_project_tracking_sheet()

# Update project status
project_data = {
    "project_id": "proj-123",
    "project_name": "AI Tutorial Series",
    "status": "processing",
    "progress": 75,
    "content_type": "educational",
    "platform": "youtube",
    "quality_score": 8.5
}
tracking.update_project_status(project_data)

# Get project data
project_info = tracking.get_project_data("proj-123")
```

### Batch Job Monitoring

```python
from google_sheets_examples import BatchJobMonitoring

# Initialize monitoring
monitoring = BatchJobMonitoring(client, spreadsheet_id)

# Create monitoring sheet
monitoring.create_job_monitoring_sheet()

# Log job progress
job_data = {
    "job_id": "job-456",
    "project_id": "proj-123", 
    "job_type": "video_generation",
    "status": "processing",
    "progress": 60,
    "current_stage": "audio_synthesis",
    "started_at": "2025-11-05T10:00:00"
}
monitoring.log_job_progress(job_data)

# Get active jobs
active_jobs = monitoring.get_active_jobs()
```

### Performance Analytics

```python
from google_sheets_examples import PerformanceAnalytics

# Initialize analytics
analytics = PerformanceAnalytics(client, spreadsheet_id)

# Create analytics sheet
analytics.create_analytics_sheet()

# Log performance metrics
metrics = [
    {
        "project_id": "proj-123",
        "platform": "youtube",
        "views": 15000,
        "likes": 850,
        "comments": 45,
        "shares": 120,
        "engagement_rate": 0.068,
        "watch_time": 2850,
        "ctr": 0.042,
        "performance_score": 7.8
    }
]
analytics.log_performance_metrics(metrics)

# Get platform performance
youtube_data = analytics.get_platform_performance("youtube", days=30)
```

## 🏃 Rate Limiting

The client automatically handles Google Sheets API rate limits:

### Default Limits
- **300 requests per minute** per project
- **60 requests per minute** per user
- **180 second** request timeout
- **2 MB** recommended maximum payload

### Exponential Backoff
On 429 errors (quota exceeded), the client automatically:
1. Waits using exponential backoff with jitter
2. Retries up to the configured maximum attempts
3. Logs retry attempts and delays
4. Eventually raises the error if all retries fail

### Backoff Parameters
```python
# Custom rate limit configuration
config = {
    'rate_limits': {
        'max_requests_per_minute': 300,
        'backoff_base_delay': 1.0,      # Initial delay
        'backoff_multiplier': 2.0,      # Delay multiplier
        'backoff_max_delay': 60.0,      # Maximum delay
        'max_retries': 5               # Maximum retry attempts
    }
}
```

### Monitoring Rate Limits
```python
# Check current rate limit status
status = client.get_rate_limit_status()
print(f"Requests in current window: {status['requests_in_current_window']}")
print(f"Requests remaining: {status['requests_remaining']}")
print(f"Window resets in: {status['window_resets_in_seconds']} seconds")
```

## ⚠️ Error Handling

### HTTP Error Handling
The client handles various HTTP errors gracefully:

| Error Code | Description | Handling |
|------------|-------------|----------|
| 429 | Quota exceeded | Exponential backoff retry |
| 500-504 | Server errors | Exponential backoff retry |
| 403 | Permission denied | Logs error, re-raises |
| 404 | Resource not found | Logs error, re-raises |
| 400 | Bad request | Logs error, re-raises |

### Error Recovery
```python
try:
    data = client.get_sheet_data(spreadsheet_id, sheet_name)
except HttpError as e:
    if e.resp.status == 429:
        print("Rate limit exceeded, will retry automatically")
    elif e.resp.status == 403:
        print("Permission denied, check service account access")
    else:
        print(f"HTTP error: {e}")
```

### Health Checks
```python
# Verify client is working
if client.health_check():
    print("Client is healthy and ready")
else:
    print("Client has issues")
```

## 🏆 Best Practices

### 1. Batch Operations
Use batch operations to minimize API calls:
```python
# Good: Batch read multiple ranges
ranges = [
    SheetRange(sheet_name="Sheet1", start_row=1, end_row=10, start_col="A", end_col="C"),
    SheetRange(sheet_name="Sheet2", start_row=1, end_row=5, start_col="A", end_col="B")
]
results = client.get_multiple_ranges(spreadsheet_id, ranges)

# Avoid: Multiple individual calls
# data1 = client.get_sheet_data(spreadsheet_id, "Sheet1")
# data2 = client.get_sheet_data(spreadsheet_id, "Sheet2")
```

### 2. Efficient Data Reading
Choose appropriate rendering options:
```python
# For calculations: Use UNFORMATTED_VALUE
data = client.get_sheet_data(
    spreadsheet_id, sheet_name,
    value_render_option=ValueRenderOption.UNFORMATTED_VALUE
)

# For display: Use FORMATTED_VALUE
data = client.get_sheet_data(
    spreadsheet_id, sheet_name, 
    value_render_option=ValueRenderOption.FORMATTED_VALUE
)
```

### 3. Range Selection
Use specific ranges instead of reading entire sheets:
```python
# Good: Read specific range
range_spec = SheetRange(
    sheet_name="Data", 
    start_row=1, end_row=100, 
    start_col="A", end_col="E"
)
data = client.get_rows_in_range(spreadsheet_id, range_spec)

# Avoid: Reading entire sheet when only partial data needed
# data = client.get_sheet_data(spreadsheet_id, "Data")
```

### 4. Error Handling
Always wrap client calls in try-except blocks:
```python
try:
    data = client.get_sheet_data(spreadsheet_id, sheet_name)
    # Process data...
except HttpError as e:
    logger.error(f"API error: {e}")
    # Handle error appropriately
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle unexpected errors
```

### 5. Resource Management
Always close the client when done:
```python
client = GoogleSheetsClient(credentials_path)
try:
    # Use client...
    pass
finally:
    client.close()
```

## 🔍 Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Request had insufficient authentication scopes
```
**Solution**: Ensure service account has access to the spreadsheet and correct scopes are requested.

#### Permission Denied
```
Error: The caller does not have permission
```
**Solution**: Share the spreadsheet with the service account email address.

#### Rate Limit Exceeded
```
Error: 429 Too Many Requests
```
**Solution**: The client automatically handles this with exponential backoff. If issues persist, check your quota limits.

#### Invalid Range
```
Error: Unable to parse range
```
**Solution**: Verify sheet names and range specifications are correct.

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check
Verify client setup:
```python
if not client.health_check():
    print("Client setup issue detected")
    # Check credentials, permissions, etc.
```

## 📁 File Structure

```
code/
├── google_sheets_client.py          # Main client implementation
├── google_sheets_config.py          # Configuration and setup
├── google_sheets_examples.py        # Usage examples and integrations
├── requirements-google-sheets.txt   # Dependencies
└── README_google_sheets_client.md   # This documentation
```

## 🤝 Contributing

1. Follow the existing code patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure all rate limiting requirements are met
5. Add proper error handling and logging

## 📄 License

This Google Sheets client implementation is part of the AI Content Automation system.

---

**Note**: This client is designed specifically for the AI Content Automation system and includes optimizations for batch content generation workflows, job monitoring, and performance analytics. For general Google Sheets API usage, refer to the [official documentation](https://developers.google.com/sheets/api).