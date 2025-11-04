# Scheduling Optimization API Documentation

## Overview

The Scheduling Optimization API provides endpoints for managing content posting schedules, getting recommendations for optimal posting times, and optimizing timing based on engagement data. The API is built with FastAPI and follows RESTful conventions.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses Bearer token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## Endpoints

### 1. Get Scheduling Recommendations

**GET** `/scheduling/recommendations`

Get recommended posting times based on historical engagement, content metadata, and platform constraints.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platforms` | array[string] | No | - | Filter by platform identifiers |
| `target_count` | integer | No | 10 | Number of windows requested (10-200) |
| `start_at` | datetime | No | - | Window start for recommendations (RFC3339) |
| `end_at` | datetime | No | - | Window end for recommendations (RFC3339) |
| `timezone` | string | No | "UTC" | IANA timezone for outputs |
| `content_type` | string | No | - | Content classification |
| `page_token` | string | No | - | Cursor for pagination |
| `page_size` | integer | No | 50 | Number of windows per page (10-200) |
| `sort` | string | No | "score" | Sort by `created_at` or `score` |
| `order` | string | No | "desc" | Sort order `asc` or `desc` |

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/scheduling/recommendations?platforms=youtube&target_count=5&timezone=America/New_York" \
  -H "Authorization: Bearer your-token"
```

#### Response

```json
{
  "data": [
    {
      "id": "rec_01HABC1234567890",
      "window_start": "2025-11-05T18:00:00Z",
      "window_end": "2025-11-05T19:30:00Z",
      "score": 0.823,
      "reasons": ["audience_active_peak", "historical_engagement_high"],
      "platforms": ["youtube"],
      "confidence": 0.77,
      "content_types": ["announcement"]
    }
  ],
  "page": {
    "next_page_token": null,
    "page_size": 50
  }
}
```

### 2. Create Schedule

**POST** `/scheduling/calendar`

Create a new schedule (calendar) that reserves specific posting times for content items.

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token |
| `Content-Type` | Yes | `application/json` |
| `Idempotency-Key` | No | UUID for idempotency |

#### Request Body

```json
{
  "title": "Launch Week Cadence",
  "timezone": "America/New_York",
  "items": [
    {
      "content_id": "content_01HXYZ1234",
      "platform": "youtube",
      "scheduled_time": "2025-11-06T14:00:00-05:00",
      "metadata": {
        "campaign_id": "camp_01H1234",
        "format": "video"
      },
      "callbacks": {
        "on_published": "https://client.example.com/webhooks/published"
      }
    }
  ],
  "processing_deadline_ms": 7200000
}
```

#### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/scheduling/calendar" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 3c5a9e2f-1d70-4a6f-9a3f-8e7a0b1c2d3e" \
  -d '{
    "title": "Launch Week Cadence",
    "timezone": "America/New_York",
    "items": [
      {
        "content_id": "content_01HXYZ1234",
        "platform": "youtube",
        "scheduled_time": "2025-11-06T14:00:00-05:00",
        "metadata": {
          "campaign_id": "camp_01H1234",
          "format": "video"
        },
        "callbacks": {
          "on_published": "https://client.example.com/webhooks/published"
        }
      }
    ],
    "processing_deadline_ms": 7200000
  }'
```

#### Response

```json
{
  "id": "sched_01HDEF9876543210",
  "tenant_id": "tenant_7x9y",
  "state": "pending",
  "title": "Launch Week Cadence",
  "timezone": "America/New_York",
  "percent_complete": 0.0,
  "items_total": 1,
  "items_completed": 0,
  "items_failed": 0,
  "items_skipped": 0,
  "items_canceled": 0,
  "items_pending": 1,
  "time_to_start_ms": null,
  "time_processing_ms": 0,
  "average_duration_ms_per_item": null,
  "eta_ms": null,
  "rate_limited": false,
  "processing_deadline_ms": 7200000,
  "created_at": "2025-11-05T02:05:12Z",
  "updated_at": "2025-11-05T02:05:12Z",
  "idempotency_key": "3c5a9e2f-1d70-4a6f-9a3f-8e7a0b1c2d3e"
}
```

### 3. Get Schedule Details

**GET** `/scheduling/calendar/{schedule_id}`

Fetch schedule details, including metadata, aggregates, and item-level listings.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schedule_id` | string | Yes | Schedule identifier |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_token` | string | No | Cursor for pagination |
| `page_size` | integer | No | Items per page (10-200) |
| `state` | array[string] | No | Filter items by state |
| `sort` | string | No | Sort by `created_at` or `updated_at` |
| `order` | string | No | Sort order `asc` or `desc` |
| `expand` | array[string] | No | Expand options: `items`, `conflicts`, `callbacks` |

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/scheduling/calendar/sched_01HDEF9876543210?expand=items&page_size=20" \
  -H "Authorization: Bearer your-token"
```

#### Response

```json
{
  "id": "sched_01HDEF9876543210",
  "tenant_id": "tenant_7x9y",
  "state": "running",
  "title": "Launch Week Cadence",
  "timezone": "America/New_York",
  "percent_complete": 30.0,
  "items_total": 1,
  "items_completed": 0,
  "items_failed": 0,
  "items_skipped": 0,
  "items_canceled": 0,
  "items_pending": 1,
  "time_to_start_ms": 1500,
  "time_processing_ms": 45000,
  "average_duration_ms_per_item": 220,
  "eta_ms": 350000,
  "rate_limited": false,
  "processing_deadline_ms": 7200000,
  "created_at": "2025-11-05T02:05:12Z",
  "updated_at": "2025-11-05T02:06:30Z",
  "items": [
    {
      "id": "item_01HABCDEFAAA1111",
      "content_id": "content_01HXYZ1234",
      "platform": "youtube",
      "state": "scheduled",
      "scheduled_time": "2025-11-06T14:00:00-05:00",
      "metadata": {
        "campaign_id": "camp_01H1234",
        "format": "video"
      },
      "callbacks": {
        "on_published": "https://client.example.com/webhooks/published"
      },
      "errors": [],
      "artifacts": [],
      "created_at": "2025-11-05T02:05:20Z",
      "updated_at": "2025-11-05T02:06:30Z"
    }
  ],
  "page": {
    "next_page_token": null,
    "page_size": 1
  }
}
```

### 4. Optimize Schedule

**POST** `/scheduling/optimize`

Optimize timing for existing content assigned to a schedule.

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token |
| `Content-Type` | Yes | `application/json` |
| `Idempotency-Key` | No | UUID for idempotency |

#### Request Body

```json
{
  "schedule_id": "sched_01HDEF9876543210",
  "targets": [
    {
      "content_id": "content_01HXYZ5678",
      "platform": "youtube",
      "current_scheduled_time": "2025-11-06T16:30:00-05:00"
    }
  ],
  "constraints": {
    "do_not_move_before": "2025-11-06T12:00:00-05:00",
    "do_not_move_after": "2025-11-06T20:00:00-05:00",
    "blackout_windows": [
      {
        "start": "2025-11-06T18:00:00-05:00",
        "end": "2025-11-06T18:30:00-05:00"
      }
    ],
    "platform_specific_rules": {
      "youtube": {
        "min_interval_minutes": 120
      }
    }
  },
  "apply": true
}
```

#### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/scheduling/optimize" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_01HDEF9876543210",
    "targets": [
      {
        "content_id": "content_01HXYZ5678",
        "platform": "youtube",
        "current_scheduled_time": "2025-11-06T16:30:00-05:00"
      }
    ],
    "constraints": {
      "do_not_move_before": "2025-11-06T12:00:00-05:00",
      "do_not_move_after": "2025-11-06T20:00:00-05:00"
    },
    "apply": true
  }'
```

#### Response

```json
{
  "id": "opt_01HJKL5555555555",
  "tenant_id": "tenant_7x9y",
  "schedule_id": "sched_01HDEF9876543210",
  "state": "completed",
  "changes": [
    {
      "content_id": "content_01HXYZ5678",
      "platform": "youtube",
      "previous_time": "2025-11-06T16:30:00-05:00",
      "new_time": "2025-11-06T17:15:00-05:00",
      "score_before": 0.65,
      "score_after": 0.82,
      "reason": "audience_active_peak",
      "confidence": 0.74
    }
  ],
  "metrics": {
    "total_targeted": 1,
    "changed_count": 1,
    "unchanged_count": 0,
    "average_score_lift": 0.17,
    "rate_limited": false
  },
  "created_at": "2025-11-05T02:10:00Z",
  "updated_at": "2025-11-05T02:10:15Z"
}
```

## WebSocket for Real-Time Updates

### WebSocket Endpoint

**WS** `/scheduling/ws`

Connect to receive real-time updates for schedules and items.

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/scheduling/ws?schedule_id=sched_01HDEF9876543210');

ws.onopen = function(event) {
    console.log('Connected to scheduling updates');
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

#### Supported Messages

**Client → Server:**

- `{"type": "ping"}` - Heartbeat
- `{"type": "subscribe", "schedule_id": "sched_123"}` - Subscribe to specific schedule

**Server → Client:**

**Schedule State Change:**
```json
{
  "type": "schedule.state_changed",
  "data": {
    "prior_state": "pending",
    "new_state": "running",
    "reason": "resources_available"
  },
  "correlation_id": "c8d3-2f11"
}
```

**Progress Update:**
```json
{
  "type": "schedule.progress",
  "data": {
    "percent_complete": 15.3,
    "items_total": 1000,
    "items_completed": 153,
    "items_failed": 1,
    "items_pending": 844,
    "eta_ms": 2327500
  }
}
```

**Item Published:**
```json
{
  "type": "item.published",
  "data": {
    "id": "item_01HABCDEFAAA1111",
    "schedule_id": "sched_01HDEF9876543210",
    "state": "published",
    "published_time": "2025-11-06T14:00:05-05:00"
  }
}
```

**Optimization Completed:**
```json
{
  "type": "optimization.completed",
  "data": {
    "opt_id": "opt_01HJKL5555555555",
    "schedule_id": "sched_01HDEF9876543210",
    "summary": {
      "total_targeted": 1,
      "changed_count": 1,
      "average_score_lift": 0.17
    }
  }
}
```

## Utility Endpoints

### Health Check

**GET** `/scheduling/health`

Check the health of the scheduling service.

```bash
curl -X GET "http://localhost:8000/api/v1/scheduling/health"
```

Response:
```json
{
  "status": "healthy",
  "service": "scheduling_optimization",
  "timestamp": "2025-11-05T02:05:12Z"
}
```

### Supported Platforms

**GET** `/scheduling/platforms`

Get list of supported platforms.

```bash
curl -X GET "http://localhost:8000/api/v1/scheduling/platforms"
```

Response:
```json
{
  "data": [
    {
      "id": "youtube",
      "name": "YouTube",
      "supports": ["long_form", "shorts"]
    },
    {
      "id": "tiktok",
      "name": "TikTok",
      "supports": ["videos"]
    }
  ]
}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in the following format:

```json
{
  "error_code": "validation_error",
  "error_message": "Invalid scheduled_time format",
  "error_class": "ValueError"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `invalid_request` | 400 | Malformed request body or query parameters |
| `validation_error` | 422 | Semantics failed validation |
| `unauthorized` | 401 | Missing or invalid authentication |
| `forbidden` | 403 | Authenticated but lacking required scope |
| `not_found` | 404 | Resource not found |
| `conflict` | 409 | State conflict or idempotency conflict |
| `rate_limited` | 429 | Request rejected due to rate limits |
| `internal_error` | 500 | Unexpected server error |

## Rate Limiting

- Per-tenant RPS: 10 requests per second
- Burst capacity: 2x per-minute
- Page size limits: Min 10, Max 200
- Retry-After header returned on 429 responses

## State Machine

### Schedule States

| State | Description | Transitions |
|-------|-------------|-------------|
| `pending` | Accepted but not yet running | → `running`, → `canceling`, → `failed` |
| `running` | Actively being processed | → `optimizing`, → `completing`, → `canceling`, → `failed` |
| `optimizing` | Timing optimization in progress | → `running`, → `completing`, → `canceling`, → `failed` |
| `completing` | Finalizing prepared items | → `completed`, → `failed` |
| `completed` | Terminal state - successful finish | Terminal |
| `canceling` | Stop requests in progress | → `canceled`, → `failed` |
| `canceled` | Terminal state after stop | Terminal |
| `failed` | Terminal state - unrecoverable error | Terminal |

### Item States

| State | Description | Transitions |
|-------|-------------|-------------|
| `pending` | Accepted but not yet assigned a time | → `scheduled`, → `skipped`, → `failed`, → `canceled` |
| `scheduled` | Assigned a concrete time | → `published`, → `skipped`, → `failed`, → `canceled` |
| `published` | Successfully published | Terminal |
| `failed` | Unrecoverable error | Terminal |
| `skipped` | Skipped intentionally | Terminal |
| `canceled` | Stopped due to schedule cancelation | Terminal |

## Integration with Supabase

The scheduling API is designed to work with Supabase PostgreSQL database. The database schema includes:

- `content_calendar` - Schedule metadata
- `content_schedule_items` - Individual scheduled posts
- `schedule_assignments` - Worker-facing assignment records
- `platform_timing_data` - Platform-specific timing heuristics
- `recommended_schedule_slots` - Generated recommendation windows
- `performance_kpi_events` - Engagement metrics
- `optimization_trials` - A/B testing configurations

All tables have Row Level Security (RLS) enabled for multi-tenant isolation.

## Testing

### Example End-to-End Flow

1. **Get Recommendations:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/scheduling/recommendations?platforms=youtube&target_count=5"
   ```

2. **Create Schedule:**
   ```bash
   # Use recommended times from step 1
   curl -X POST "http://localhost:8000/api/v1/scheduling/calendar" \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d @schedule_request.json
   ```

3. **Monitor Progress:**
   - Connect to WebSocket for real-time updates
   - Periodically GET schedule details

4. **Optimize Timing:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/scheduling/optimize" \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d @optimization_request.json
   ```

This completes the scheduling API implementation. The endpoints follow the design specifications in `docs/scheduling_system/api_endpoints.md` and integrate with the existing content-creator backend structure.