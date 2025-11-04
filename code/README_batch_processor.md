# Batch Processing Pipeline for Video Ideas from Google Sheets

## Overview

The Batch Processing Pipeline is a comprehensive system for orchestrating multiple video ideas sourced from Google Sheets. It provides queue management, prioritization, progress tracking, and integration with existing video generation workflows.

## Architecture

### Core Components

1. **BatchProcessor** - Main orchestrator class that manages the entire pipeline
2. **QueueManager** - Handles job queue operations with priority-based scheduling
3. **RateLimiter** - Implements token bucket and sliding window rate limiting
4. **BulkJob** - Represents a batch of video ideas from a single Google Sheet
5. **VideoJob** - Individual video generation job
6. **JobEvent** - Progress tracking and logging events

### Integration Points

- **Google Sheets Client** - Reads idea data from spreadsheets
- **Idea Data Service** - Processes and validates sheet data
- **Data Validator** - Validates and cleans idea data
- **Error Handler** - Provides retry logic and error handling

## Key Features

### 1. Pipeline Orchestration
- Process multiple video ideas from a single Google Sheet
- Coordinate with existing video generation workflows
- Handle batch operations efficiently

### 2. Job Queue Management
- Priority-based scheduling (urgent, normal, low)
- FIFO ordering within same priority levels
- Concurrent worker processing

### 3. Rate Limiting
- Per-user sliding window rate limiting
- Per-project token bucket implementation
- Automatic backoff on quota exceeded

### 4. Progress Tracking
- Real-time progress updates
- Event-based logging system
- Completion callbacks

### 5. State Management
- Job lifecycle tracking
- Pause/resume functionality
- Error handling and retry logic

## Quick Start

### Basic Usage

```python
import asyncio
from batch_processor import BatchProcessor, JobPriority, SheetFormat, ValidationLevel

async def main():
    # Create processor
    processor = BatchProcessor(
        credentials_path="path/to/credentials.json",
        max_workers=4
    )
    
    try:
        # Add progress callback
        def progress_callback(job_id: str, progress: int, message: str):
            print(f"Progress [{job_id}]: {progress}% - {message}")
        
        processor.add_progress_callback(progress_callback)
        
        # Create bulk job
        bulk_job_id = processor.create_bulk_job(
            sheet_id="your_spreadsheet_id",
            user_id="user123",
            priority=JobPriority.NORMAL
        )
        
        # Process ideas from sheet
        result = await processor.process_sheet_ideas(
            bulk_job_id=bulk_job_id,
            sheet_format=SheetFormat.STANDARD,
            validation_level=ValidationLevel.MODERATE,
            ai_provider="openai"
        )
        
        print(f"Processing started: {result}")
        
        # Monitor progress
        while True:
            status = processor.get_bulk_job_status(bulk_job_id)
            print(f"Status: {status}")
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                break
            
            await asyncio.sleep(5)
        
    finally:
        await processor.cleanup()

# Run
asyncio.run(main())
```

### Advanced Usage with Callbacks

```python
from batch_processor import BatchProcessor

processor = BatchProcessor("credentials.json")

# Progress tracking
def on_progress(job_id: str, progress: int, message: str):
    print(f"📊 {job_id}: {progress}% - {message}")

# Completion tracking  
def on_completion(job_id: str, result: dict):
    print(f"✅ {job_id} completed: {result['output_url']}")

# Error handling
def on_error(job_id: str, error: str):
    print(f"❌ {job_id} failed: {error}")

# Register callbacks
processor.add_progress_callback(on_progress)
processor.add_completion_callback(on_completion)
processor.add_error_callback(on_error)

# Create and process bulk job
bulk_job_id = processor.create_bulk_job("sheet_id", "user_id")
await processor.process_sheet_ideas(bulk_job_id)
```

## Configuration

### Rate Limiting

```python
from batch_processor import RateLimiter

# Custom rate limiter
rate_limiter = RateLimiter(
    per_user_limit=60,        # 60 requests per minute per user
    per_project_limit=300,    # 300 requests per minute per project
    refill_rate=5.0          # 5 tokens per second refill
)

processor = BatchProcessor(
    credentials_path="creds.json",
    rate_limiter=rate_limiter
)
```

### Queue Configuration

```python
from batch_processor import QueueManager

# Custom queue manager
queue_manager = QueueManager(max_workers=8)
processor.queue_manager = queue_manager
```

## Job Management

### Priority Levels

```python
from batch_processor import JobPriority

# Create jobs with different priorities
urgent_job = VideoJob(..., priority=JobPriority.URGENT)   # Highest priority
normal_job = VideoJob(..., priority=JobPriority.NORMAL)   # Default priority  
low_job = VideoJob(..., priority=JobPriority.LOW)         # Lowest priority
```

### Status Management

```python
# Get job status
status = processor.get_bulk_job_status(bulk_job_id)
print(f"Progress: {status['progress']}%")
print(f"Jobs: {status['statistics']}")

# Pause a job
processor.pause_bulk_job(bulk_job_id)

# Resume a job
processor.resume_bulk_job(bulk_job_id)

# Cancel a job
processor.cancel_bulk_job(bulk_job_id)
```

### Event Tracking

```python
# Get recent job events
events = processor.get_job_events(bulk_job_id, limit=50)
for event in events:
    print(f"{event['created_at']}: {event['message']}")
```

## Integration with Video Generation

The batch processor integrates with existing video generation workflows through the `_execute_video_generation` method. This method should be customized to call your specific video generation service:

```python
class CustomBatchProcessor(BatchProcessor):
    async def _execute_video_generation(self, video_job: VideoJob) -> Dict[str, Any]:
        """Custom video generation integration."""
        
        # Import your video generation service
        from your_video_service import VideoGenerationService
        
        service = VideoGenerationService()
        
        # Generate video
        result = await service.generate_video(
            prompt=video_job.idea_data['script'],
            voice=video_job.idea_data.get('voice'),
            style=video_job.idea_data.get('style'),
            provider=video_job.ai_provider
        )
        
        return {
            "output_url": result.video_url,
            "cost": result.cost,
            "duration": result.duration,
            "quality": result.quality
        }
```

## Error Handling

### Retry Logic

The system implements exponential backoff for failed operations:

```python
# Retry configuration in error handler
processor.error_handler = SheetsErrorHandler(
    name="batch_processor",
    retry_template=RetryTemplate(
        initial_delay=1.0,    # Start with 1 second
        max_delay=60.0,       # Maximum 60 seconds
        max_retries=5,        # Maximum 5 retries
        multiplier=3.0        # 3x increase each retry
    )
)
```

### Error Types Handled

- **QuotaExceededError** - Rate limit exceeded
- **NetworkError** - Connection issues
- **AuthenticationError** - Auth failures
- **PermissionError** - Access denied
- **ServerError** - 5xx errors

### Custom Error Handling

```python
def custom_error_handler(job_id: str, error: Exception):
    if isinstance(error, QuotaExceededError):
        print(f"Rate limited job {job_id}, will retry automatically")
    elif "timeout" in str(error).lower():
        print(f"Timeout on job {job_id}, will retry with backoff")
    else:
        print(f"Unknown error on job {job_id}: {error}")

processor.add_error_callback(custom_error_handler)
```

## Monitoring and Observability

### System Status

```python
# Get overall system status
status = processor.get_system_status()
print(f"State: {status['state']}")
print(f"Running jobs: {status['bulk_jobs']['running']}")
print(f"Queue workers: {status['queue_running']}")
```

### Database Schema

The processor uses SQLite for local job tracking:

- `bulk_jobs` - Bulk job records
- `video_jobs` - Individual video jobs
- `job_events` - Progress events and logs

### Progress Tracking

Real-time progress updates via callbacks:

```python
def detailed_progress(job_id: str, progress: int, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Job {job_id}: {progress:3d}% - {message}")

processor.add_progress_callback(detailed_progress)
```

## Best Practices

### 1. Resource Management

```python
# Always cleanup resources
try:
    processor = BatchProcessor("creds.json")
    # ... your processing code
finally:
    await processor.cleanup()
```

### 2. Progress Monitoring

```python
# Use progress callbacks for real-time updates
processor.add_progress_callback(lambda job_id, progress, msg: 
    logger.info(f"Progress {job_id}: {progress}% - {msg}"))
```

### 3. Error Handling

```python
# Implement comprehensive error handling
try:
    result = await processor.process_sheet_ideas(bulk_job_id)
except QuotaExceededError:
    logger.error("Rate limit exceeded, implement backoff strategy")
except Exception as e:
    logger.error(f"Processing failed: {e}")
```

### 4. Rate Limiting

```python
# Configure appropriate rate limits based on API quotas
rate_limiter = RateLimiter(
    per_user_limit=60,      # Conservative per-user limit
    per_project_limit=300,  # Project-level capacity
    refill_rate=5.0         # Smooth refill rate
)
```

### 5. Database Cleanup

```python
# Clean up old jobs periodically
def cleanup_old_jobs(processor, days_old=30):
    cutoff = datetime.now() - timedelta(days=days_old)
    # Remove completed jobs older than cutoff
    # Implementation depends on your retention policy
```

## API Reference

### BatchProcessor Class

#### Constructor
```python
BatchProcessor(
    credentials_path: str,
    db_path: str = "batch_processing.db",
    max_workers: int = 4,
    rate_limiter: Optional[RateLimiter] = None
)
```

#### Key Methods

##### `create_bulk_job(sheet_id, user_id, priority, column_range, sheet_format) -> str`
Creates a new bulk job from a Google Sheet.

##### `process_sheet_ideas(bulk_job_id, sheet_format, validation_level, ai_provider, column_range) -> Dict[str, Any]`
Processes ideas from the sheet and creates video jobs.

##### `get_bulk_job_status(bulk_job_id) -> Dict[str, Any]`
Gets current status of a bulk job.

##### `pause_bulk_job(bulk_job_id) -> bool`
Pauses a running bulk job.

##### `resume_bulk_job(bulk_job_id) -> bool`
Resumes a paused bulk job.

##### `cancel_bulk_job(bulk_job_id) -> bool`
Cancels a bulk job.

##### `get_system_status() -> Dict[str, Any]`
Gets overall system status.

### RateLimiter Class

#### Constructor
```python
RateLimiter(
    per_user_limit: int = 60,
    per_project_limit: int = 300,
    refill_rate: float = 5.0
)
```

#### Methods

##### `can_proceed(user_id, project_id) -> bool`
Checks if a request can proceed under rate limits.

##### `get_backoff_time(user_id) -> float`
Gets recommended backoff time for rate limiting.

### Job Priority Levels

```python
JobPriority.URGENT  # Highest priority
JobPriority.NORMAL  # Default priority
JobPriority.LOW     # Lowest priority
```

### Job Status Values

```python
JobStatus.QUEUED         # Waiting in queue
JobStatus.RATE_LIMITED   # Delayed due to rate limits
JobStatus.DISPATCHED     # Sent to generation service
JobStatus.IN_PROGRESS    # Currently processing
JobStatus.RETRIED        # Scheduled for retry
JobStatus.COMPLETED      # Successfully finished
JobStatus.FAILED         # Failed with error
JobStatus.CANCELLED      # Cancelled by user
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest test_batch_processor.py -v

# Run specific test classes
python -m pytest test_batch_processor.py::TestBatchProcessor -v

# Run integration demo
python test_batch_processor.py
```

## Deployment

### Production Considerations

1. **Database**: Use PostgreSQL instead of SQLite for production
2. **Authentication**: Implement proper user authentication
3. **Monitoring**: Add comprehensive logging and metrics
4. **Scaling**: Use multiple processor instances behind a load balancer
5. **Storage**: Configure proper video output storage
6. **Security**: Implement proper access controls and rate limiting

### Environment Variables

```bash
# Example environment configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json
BATCH_PROCESSOR_DB_URL=postgresql://user:pass@localhost/batch_db
BATCH_PROCESSOR_MAX_WORKERS=8
BATCH_PROCESSOR_RATE_LIMIT_USER=60
BATCH_PROCESSOR_RATE_LIMIT_PROJECT=300
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "batch_processor_server.py"]
```

## Troubleshooting

### Common Issues

#### 1. Rate Limit Errors
```python
# Check rate limiter configuration
status = processor.get_system_status()
print(f"Rate limiter buckets: {status['rate_limiter']}")

# Adjust backoff
backoff = processor.rate_limiter.get_backoff_time("user_id")
print(f"Recommended backoff: {backoff} seconds")
```

#### 2. Job Queue Backlog
```python
# Check queue status
print(f"Queue running: {processor.queue_manager.running}")
print(f"System status: {processor.get_system_status()}")

# Increase workers if needed
processor.queue_manager.max_workers = 8
```

#### 3. Database Issues
```python
# Check database connectivity
try:
    with sqlite3.connect(processor.db_path) as conn:
        conn.execute("SELECT 1").fetchone()
    print("Database connection OK")
except Exception as e:
    print(f"Database error: {e}")
```

### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
logger = logging.getLogger('batch_processor')
logger.setLevel(logging.DEBUG)
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure compatibility with existing integrations
5. Test with real Google Sheets data

## License

This batch processing pipeline is part of the AI Content Automation System.