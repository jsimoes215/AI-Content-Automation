# Scheduling Optimization API

A FastAPI-based backend service for content scheduling optimization, providing recommendations, calendar management, and real-time optimization capabilities.

## Features

- **Smart Recommendations**: Get AI-generated optimal posting times based on platform data and historical engagement
- **Schedule Management**: Create and manage content posting calendars with full lifecycle tracking
- **Real-time Optimization**: Optimize timing for better engagement using machine learning algorithms
- **WebSocket Support**: Real-time updates for schedule progress and changes
- **Multi-platform Support**: YouTube, TikTok, Instagram, LinkedIn, Twitter/X, Facebook
- **Supabase Integration**: Full database schema with Row Level Security (RLS)
- **RESTful API**: Complete REST API following OpenAPI specifications

## Architecture

```
├── backend/
│   ├── api/
│   │   └── scheduling_api.py      # Main API implementation
│   ├── database/
│   │   ├── db.py                  # Database connection
│   │   └── scheduling_schema.sql  # Database schema
│   ├── docs/
│   │   └── SCHEDULING_API.md      # API documentation
│   ├── main.py                    # FastAPI application
│   └── test_scheduling_api.py     # Test suite
```

## Quick Start

### 1. Setup Dependencies

```bash
cd /workspace/content-creator/backend
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Apply the scheduling schema to your Supabase database
# Copy the contents of database/scheduling_schema.sql and run in your Supabase SQL editor
```

### 3. Start the Server

```bash
cd /workspace/content-creator/backend
python main.py
```

The API will be available at `http://localhost:8000`

### 4. Run Tests

```bash
cd /workspace/content-creator/backend
python test_scheduling_api.py
```

## API Endpoints

### Core Endpoints

- `GET /api/v1/scheduling/recommendations` - Get posting time recommendations
- `POST /api/v1/scheduling/calendar` - Create a new schedule
- `GET /api/v1/scheduling/calendar/{id}` - Get schedule details
- `POST /api/v1/scheduling/optimize` - Optimize schedule timing
- `WS /api/v1/scheduling/ws` - WebSocket for real-time updates

### Utility Endpoints

- `GET /api/v1/scheduling/health` - Health check
- `GET /api/v1/scheduling/platforms` - List supported platforms

## Supported Platforms

| Platform | Content Types | Best Times (Indicative) | Frequency |
|----------|---------------|-------------------------|-----------|
| YouTube | Long-form, Shorts | Weekdays 3-5pm | 2-3/week long-form, daily shorts |
| TikTok | Videos | Wed 3-4pm, Sun 8pm | 2-5/week |
| Instagram | Posts, Reels | Weekdays 10am-3pm | 3-5/week |
| LinkedIn | Posts, Articles | Midweek 8am-2pm | 2-5/week |
| Twitter/X | Tweets, Threads | Tue-Thu 8am-12pm | 3-14/week |
| Facebook | Posts, Videos | Weekdays 8am-6pm | 3-5/week |

## Database Schema

The scheduling system uses the following main tables:

- **`content_calendar`** - Schedule metadata and grouping
- **`content_schedule_items`** - Individual scheduled posts
- **`platform_timing_data`** - Platform-specific timing heuristics
- **`recommended_schedule_slots`** - AI-generated recommendations
- **`performance_kpi_events`** - Engagement metrics
- **`optimization_trials`** - A/B testing configurations

All tables include Row Level Security (RLS) for multi-tenant isolation.

## Usage Examples

### Get Recommendations

```bash
curl -X GET "http://localhost:8000/api/v1/scheduling/recommendations?platforms=youtube&target_count=5"
```

### Create Schedule

```bash
curl -X POST "http://localhost:8000/api/v1/scheduling/calendar" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Launch Week Cadence",
    "timezone": "America/New_York",
    "items": [
      {
        "content_id": "content_123",
        "platform": "youtube",
        "scheduled_time": "2025-11-06T14:00:00-05:00",
        "metadata": {"campaign_id": "camp_456"}
      }
    ]
  }'
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/scheduling/ws?schedule_id=sched_123');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Update:', update);
};
```

## State Management

### Schedule States

- `pending` → `running` → `optimizing` → `completing` → `completed`
- `pending` → `canceling` → `canceled`
- Any state → `failed` (error condition)

### Item States

- `pending` → `scheduled` → `published`
- `pending` → `skipped` (intentionally skipped)
- `pending` → `failed` (error condition)

## Rate Limiting

- **Per-tenant RPS**: 10 requests per second
- **Burst capacity**: 2x per-minute
- **Page limits**: 10-200 items per request
- **Retry-After**: Returned on 429 responses

## Error Handling

The API uses standard HTTP status codes:

- `200/201` - Success
- `400` - Invalid request
- `401/403` - Authentication/authorization
- `404` - Not found
- `409` - Conflict (state/idempotency)
- `422` - Validation error
- `429` - Rate limited
- `500` - Internal error

Error response format:
```json
{
  "error_code": "validation_error",
  "error_message": "Invalid scheduled_time format",
  "error_class": "ValueError"
}
```

## Integration with Content Creator System

The scheduling API integrates seamlessly with the existing content-creator backend:

1. **Generated Content**: Schedules reference `video_job_id` from generated content
2. **Bulk Jobs**: Optional linking to `bulk_job_id` for orchestration
3. **WebSocket Updates**: Real-time progress broadcasting
4. **Shared Database**: Uses existing Supabase infrastructure

## Development

### Adding New Platforms

1. Add platform data to `platform_timing_data` table
2. Update platform configuration in `get_supported_platforms()`
3. Test with sample recommendations

### Custom Optimization Algorithms

1. Modify the `optimize_schedule` method in `SchedulingService`
2. Add platform-specific rules to `platform_specific_rules`
3. Update the optimization constraints validation

### WebSocket Events

Add new event types by updating the `broadcast` method and documenting in the API docs.

## Testing

The test suite (`test_scheduling_api.py`) includes:

- **Unit Tests**: Individual endpoint testing
- **Integration Tests**: Full workflow testing
- **WebSocket Tests**: Real-time communication testing
- **Error Handling**: Invalid input and error scenario testing

Run the full test suite:
```bash
python test_scheduling_api.py
```

## Deployment

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Database**: Ensure Supabase connection pooling is configured
2. **Caching**: Consider Redis for recommendation caching
3. **Monitoring**: Add application metrics and logging
4. **Scaling**: Use multiple workers for high-load scenarios
5. **Security**: Implement proper JWT authentication
6. **Backup**: Regular database backups and recovery procedures

## API Documentation

Complete API documentation is available at:

- **OpenAPI Spec**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Local Docs**: `backend/docs/SCHEDULING_API.md`

## Contributing

1. Follow the existing code patterns in `main.py` and `api/scheduling_api.py`
2. Update API documentation when adding endpoints
3. Include tests for new functionality
4. Ensure database schema updates include RLS policies
5. Test with the provided test suite

## License

This scheduling API implementation is part of the AI Content Automation System.