# Scheduling Optimization API Reference

## Overview

The Scheduling Optimization API provides comprehensive endpoints for managing content posting schedules, generating intelligent recommendations for optimal posting times, and optimizing existing schedules based on engagement patterns and platform-specific analytics.

This API powers an intelligent scheduling system that analyzes historical engagement data, audience behavior patterns, and platform-specific constraints to provide data-driven recommendations for content timing optimization.

## Base Information

- **Base URL**: `https://api.content-automation.com/api/v1`
- **Protocol**: HTTPS only
- **API Version**: v1
- **Content Type**: `application/json`
- **Authentication**: Bearer Token (JWT)
- **Rate Limits**: 100 requests/minute per tenant
- **Documentation Version**: 1.0.0
- **Last Updated**: November 5, 2025

## Authentication

All API requests require authentication using Bearer tokens. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting Started

1. Obtain JWT token from authentication service
2. Include token in all API requests
3. Handle 401 responses by refreshing token
4. Store tokens securely (never expose client-side)

### Token Refresh

Tokens expire after 24 hours. Implement refresh logic:

```bash
curl -X POST "https://auth.content-automation.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=<refresh_token>"
```

## Data Models

### Core Models

#### Recommendation
Represents an optimal posting time window with scoring and metadata.

```typescript
interface Recommendation {
  id: string;                    // Unique recommendation ID
  window_start: string;          // ISO 8601 datetime
  window_end: string;            // ISO 8601 datetime
  score: number;                 // 0.0 to 1.0 confidence score
  reasons: string[];             // Optimization factors
  platforms: string[];           // Applicable platforms
  confidence: number;            // Prediction confidence
  content_types: string[];       // Suitable content types
}
```

#### Schedule
Container for scheduled content items with status tracking.

```typescript
interface Schedule {
  id: string;
  tenant_id: string;
  state: ScheduleState;
  title: string;
  timezone: string;
  percent_complete: number;
  items_total: number;
  items_completed: number;
  items_failed: number;
  items_skipped: number;
  items_canceled: number;
  items_pending: number;
  time_to_start_ms?: number;
  time_processing_ms: number;
  average_duration_ms_per_item?: number;
  eta_ms?: number;
  rate_limited: boolean;
  processing_deadline_ms: number;
  created_at: string;
  updated_at: string;
  idempotency_key?: string;
  items?: ScheduleItem[];
  page?: PageInfo;
}

type ScheduleState = 
  | "pending"
  | "running" 
  | "optimizing"
  | "completing"
  | "completed"
  | "canceling"
  | "canceled"
  | "failed";
```

#### ScheduleItem
Individual scheduled content with execution details.

```typescript
interface ScheduleItem {
  id: string;
  content_id: string;
  platform: string;
  state: ItemState;
  scheduled_time: string;
  published_time?: string;
  metadata?: Record<string, any>;
  callbacks?: Record<string, string>;
  errors: Array<{
    code: string;
    message: string;
    timestamp: string;
  }>;
  artifacts: Array<{
    type: string;
    url: string;
    metadata?: Record<string, any>;
  }>;
  created_at: string;
  updated_at: string;
}

type ItemState = 
  | "pending"
  | "scheduled"
  | "published"
  | "failed"
  | "skipped"
  | "canceled";
```

#### OptimizationResult
Results from schedule optimization operations.

```typescript
interface OptimizationResult {
  id: string;
  tenant_id: string;
  schedule_id: string;
  state: "pending" | "running" | "completed" | "failed";
  changes: OptimizationChange[];
  metrics: OptimizationMetrics;
  created_at: string;
  updated_at: string;
}

interface OptimizationChange {
  content_id: string;
  platform: string;
  previous_time: string;
  new_time: string;
  score_before: number;
  score_after: number;
  reason: string;
  confidence: number;
}

interface OptimizationMetrics {
  total_targeted: number;
  changed_count: number;
  unchanged_count: number;
  average_score_lift: number;
  rate_limited: boolean;
}
```

## Endpoints

### 1. Get Scheduling Recommendations

Retrieve intelligent recommendations for optimal posting times based on platform analytics and engagement patterns.

**Endpoint**: `GET /scheduling/recommendations`

#### Parameters

| Parameter | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `platforms` | `string[]` | No | - | Max 10 items | Filter by platform identifiers |
| `target_count` | `integer` | No | `10` | 10-200 | Number of time windows requested |
| `start_at` | `datetime` | No | - | RFC3339 format | Start of recommendation window |
| `end_at` | `datetime` | No | - | RFC3339 format | End of recommendation window |
| `timezone` | `string` | No | `"UTC"` | IANA timezone | Output timezone for recommendations |
| `content_type` | `string` | No | - | Available types | Content classification filter |
| `page_token` | `string` | No | - | - | Pagination cursor |
| `page_size` | `integer` | No | `50` | 10-200 | Results per page |
| `sort` | `string` | No | `"score"` | `created_at\|score` | Sort field |
| `order` | `string` | No | `"desc"` | `asc\|desc` | Sort order |

#### Request Examples

**Basic Request**:
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/recommendations?platforms=youtube&target_count=5" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Accept: application/json"
```

**With Date Range**:
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/recommendations?platforms=tiktok,instagram&start_at=2025-11-05T00:00:00Z&end_at=2025-11-12T23:59:59Z&timezone=America/New_York&content_type=video" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

#### Response

**Success (200)**:
```json
{
  "data": [
    {
      "id": "rec_01HQ4J8R9ABCDEF1234567890",
      "window_start": "2025-11-05T18:00:00Z",
      "window_end": "2025-11-05T19:30:00Z",
      "score": 0.847,
      "reasons": [
        "audience_active_peak",
        "historical_engagement_high",
        "optimal_algorithm_timing"
      ],
      "platforms": ["youtube"],
      "confidence": 0.82,
      "content_types": ["announcement", "tutorial"]
    },
    {
      "id": "rec_01HQ4J8S0BCDEFG2345678901",
      "window_start": "2025-11-05T20:00:00Z", 
      "window_end": "2025-11-05T21:15:00Z",
      "score": 0.793,
      "reasons": [
        "evening_engagement_peak",
        "weekday_pattern_match"
      ],
      "platforms": ["tiktok", "instagram"],
      "confidence": 0.78,
      "content_types": ["entertainment", "lifestyle"]
    }
  ],
  "page": {
    "next_page_token": null,
    "page_size": 50
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data` | `Recommendation[]` | Array of recommendation objects |
| `data[].id` | `string` | Unique recommendation identifier |
| `data[].window_start` | `datetime` | Start of optimal posting window |
| `data[].window_end` | `datetime` | End of optimal posting window |
| `data[].score` | `number` | Overall optimization score (0.0-1.0) |
| `data[].reasons` | `string[]` | Factors contributing to recommendation |
| `data[].platforms` | `string[]` | Platforms this recommendation applies to |
| `data[].confidence` | `number` | Model confidence in prediction (0.0-1.0) |
| `data[].content_types` | `string[]` | Content types that perform well in this window |
| `page.next_page_token` | `string?` | Token for next page, null if last page |
| `page.page_size` | `number` | Number of results returned |

#### Error Responses

**Bad Request (400)**:
```json
{
  "error_code": "invalid_parameter",
  "error_message": "Invalid timezone format: 'invalid/timezone'",
  "detail": {
    "parameter": "timezone",
    "value": "invalid/timezone",
    "expected": "IANA timezone format"
  }
}
```

**Unauthorized (401)**:
```json
{
  "error_code": "unauthorized",
  "error_message": "Invalid or expired token"
}
```

**Too Many Requests (429)**:
```json
{
  "error_code": "rate_limited",
  "error_message": "Rate limit exceeded",
  "detail": {
    "limit": 100,
    "window": "1 minute",
    "retry_after": 45
  }
}
```

### 2. Create Schedule

Create a new content posting schedule with specific items and timing.

**Endpoint**: `POST /scheduling/calendar`

#### Headers

| Header | Required | Type | Description |
|--------|----------|------|-------------|
| `Authorization` | Yes | `Bearer <token>` | JWT authentication |
| `Content-Type` | Yes | `application/json` | Request body format |
| `Idempotency-Key` | No | `UUID` | Ensures duplicate requests return same result |

#### Request Body

```json
{
  "title": "Product Launch Campaign Schedule",
  "timezone": "America/New_York",
  "items": [
    {
      "content_id": "content_01HQ5P2R3ABCDEF1234567890",
      "platform": "youtube",
      "scheduled_time": "2025-11-06T14:00:00-05:00",
      "metadata": {
        "campaign_id": "camp_01HQ5P2R3",
        "content_type": "announcement",
        "priority": "high"
      },
      "callbacks": {
        "on_published": "https://client.example.com/webhooks/published",
        "on_failed": "https://client.example.com/webhooks/failed"
      }
    },
    {
      "content_id": "content_01HQ5P2S4BCDEFG2345678901",
      "platform": "instagram", 
      "scheduled_time": "2025-11-06T14:30:00-05:00",
      "metadata": {
        "campaign_id": "camp_01HQ5P2R3",
        "content_type": "reel",
        "hashtags": ["#productlaunch", "#innovation"]
      }
    }
  ],
  "processing_deadline_ms": 10800000
}
```

#### Request Field Descriptions

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `title` | `string` | Yes | 1-200 chars | Human-readable schedule name |
| `timezone` | `string` | Yes | IANA format | Primary timezone for schedule |
| `items` | `ScheduleItemCreate[]` | Yes | 1-1000 items | Content items to schedule |
| `items[].content_id` | `string` | Yes | UUID format | Reference to content item |
| `items[].platform` | `string` | Yes | Supported platform | Target platform identifier |
| `items[].scheduled_time` | `datetime` | Yes | RFC3339 format | Exact posting time |
| `items[].metadata` | `object` | No | Max 10KB | Arbitrary metadata |
| `items[].callbacks` | `object` | No | Valid URLs | Webhook URLs for status updates |
| `processing_deadline_ms` | `integer` | No | 1-24 hours | Maximum processing time |

#### Request Examples

**Basic Schedule**:
```bash
curl -X POST "https://api.content-automation.com/api/v1/scheduling/calendar" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 3c5a9e2f-1d70-4a6f-9a3f-8e7a0b1c2d3e" \
  -d '{
    "title": "Weekly Content Schedule",
    "timezone": "America/New_York", 
    "items": [
      {
        "content_id": "content_01HQ5P2R3ABCDEF1234567890",
        "platform": "youtube",
        "scheduled_time": "2025-11-06T14:00:00-05:00"
      }
    ]
  }'
```

**Multi-Platform Campaign**:
```bash
curl -X POST "https://api.content-automation.com/api/v1/scheduling/calendar" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @multi_platform_schedule.json
```

#### Response

**Success (201)**:
```json
{
  "id": "sched_01HQ5P2T5CDEFGH3456789012",
  "tenant_id": "tenant_01HQ5P2R3",
  "state": "pending",
  "title": "Product Launch Campaign Schedule", 
  "timezone": "America/New_York",
  "percent_complete": 0.0,
  "items_total": 2,
  "items_completed": 0,
  "items_failed": 0,
  "items_skipped": 0,
  "items_canceled": 0,
  "items_pending": 2,
  "time_to_start_ms": 1500,
  "time_processing_ms": 0,
  "average_duration_ms_per_item": null,
  "eta_ms": 7200000,
  "rate_limited": false,
  "processing_deadline_ms": 10800000,
  "created_at": "2025-11-05T03:45:12Z",
  "updated_at": "2025-11-05T03:45:12Z",
  "idempotency_key": "3c5a9e2f-1d70-4a6f-9a3f-8e7a0b1c2d3e"
}
```

#### Idempotency

When using `Idempotency-Key` header, identical requests return the same schedule without creating duplicates. This is useful for handling network failures and retry logic.

### 3. Get Schedule Details

Retrieve comprehensive schedule information including items and status.

**Endpoint**: `GET /scheduling/calendar/{schedule_id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schedule_id` | `string` | Yes | Schedule identifier |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page_token` | `string` | No | - | Pagination cursor |
| `page_size` | `integer` | No | `50` | Items per page (10-200) |
| `state` | `string[]` | No | - | Filter items by state |
| `sort` | `string` | No | `created_at` | Sort field |
| `order` | `string` | No | `desc` | Sort order |
| `expand` | `string[]` | No | - | Expand options: `items`, `metrics`, `callbacks` |

#### Request Examples

**Basic Get**:
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/calendar/sched_01HQ5P2T5CDEFGH3456789012" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**With Items**:
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/calendar/sched_01HQ5P2T5CDEFGH3456789012?expand=items&page_size=100&sort=scheduled_time&order=asc" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Filter by State**:
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/calendar/sched_01HQ5P2T5CDEFGH3456789012?state=published,failed&expand=items" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

#### Response

**Success (200)**:
```json
{
  "id": "sched_01HQ5P2T5CDEFGH3456789012",
  "tenant_id": "tenant_01HQ5P2R3",
  "state": "running",
  "title": "Product Launch Campaign Schedule",
  "timezone": "America/New_York",
  "percent_complete": 25.0,
  "items_total": 2,
  "items_completed": 0,
  "items_failed": 0,
  "items_skipped": 0,
  "items_canceled": 0,
  "items_pending": 2,
  "time_to_start_ms": 0,
  "time_processing_ms": 45000,
  "average_duration_ms_per_item": 22500,
  "eta_ms": 900000,
  "rate_limited": false,
  "processing_deadline_ms": 10800000,
  "created_at": "2025-11-05T03:45:12Z",
  "updated_at": "2025-11-05T03:46:30Z",
  "items": [
    {
      "id": "item_01HQ5P2U6DEFGHI4567890123",
      "content_id": "content_01HQ5P2R3ABCDEF1234567890",
      "platform": "youtube",
      "state": "scheduled",
      "scheduled_time": "2025-11-06T14:00:00-05:00",
      "metadata": {
        "campaign_id": "camp_01HQ5P2R3",
        "content_type": "announcement",
        "priority": "high"
      },
      "callbacks": {
        "on_published": "https://client.example.com/webhooks/published",
        "on_failed": "https://client.example.com/webhooks/failed"
      },
      "errors": [],
      "artifacts": [
        {
          "type": "video_upload",
          "url": "https://storage.content-automation.com/artifacts/item_01HQ5P2U6DEFGHI4567890123/video.mp4",
          "metadata": {
            "duration": 180,
            "resolution": "1920x1080",
            "format": "mp4"
          }
        }
      ],
      "created_at": "2025-11-05T03:45:15Z",
      "updated_at": "2025-11-05T03:46:30Z"
    }
  ],
  "page": {
    "next_page_token": null,
    "page_size": 1
  }
}
```

#### Expand Options

- `items`: Include detailed schedule items
- `metrics`: Include performance metrics and analytics
- `callbacks`: Include webhook callback URLs and status

### 4. Optimize Schedule

Optimize existing schedule timing based on engagement patterns and audience behavior.

**Endpoint**: `POST /scheduling/optimize`

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | JWT authentication |
| `Content-Type` | Yes | `application/json` |
| `Idempotency-Key` | No | Ensures duplicate requests return same result |

#### Request Body

```json
{
  "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
  "targets": [
    {
      "content_id": "content_01HQ5P2R3ABCDEF1234567890",
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
        "min_interval_minutes": 120,
        "avoid_friday_evenings": true
      },
      "instagram": {
        "min_interval_minutes": 60,
        "preferred_time_zones": ["America/New_York", "America/Los_Angeles"]
      }
    }
  },
  "apply": true
}
```

#### Request Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schedule_id` | `string` | Yes | Schedule to optimize |
| `targets` | `OptimizationTarget[]` | Yes | Items to optimize |
| `targets[].content_id` | `string` | Yes | Content item identifier |
| `targets[].platform` | `string` | Yes | Target platform |
| `targets[].current_scheduled_time` | `datetime` | Yes | Current scheduled time |
| `constraints` | `OptimizationConstraint` | No | Optimization constraints |
| `constraints.do_not_move_before` | `datetime` | No | Earliest acceptable time |
| `constraints.do_not_move_after` | `datetime` | No | Latest acceptable time |
| `constraints.blackout_windows` | `TimeRange[]` | No | Times to avoid |
| `constraints.platform_specific_rules` | `object` | No | Platform-specific constraints |
| `apply` | `boolean` | No | `false` = dry run, `true` = apply changes |

#### Request Examples

**Dry Run Optimization**:
```bash
curl -X POST "https://api.content-automation.com/api/v1/scheduling/optimize" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
    "targets": [
      {
        "content_id": "content_01HQ5P2R3ABCDEF1234567890",
        "platform": "youtube",
        "current_scheduled_time": "2025-11-06T16:30:00-05:00"
      }
    ],
    "apply": false
  }'
```

**Apply Optimization**:
```bash
curl -X POST "https://api.content-automation.com/api/v1/scheduling/optimize" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: opt_01HQ5P2V7EFGHIJ5678901234" \
  -d @optimization_request.json
```

#### Response

**Success (200)**:
```json
{
  "id": "opt_01HQ5P2V7EFGHIJ5678901234",
  "tenant_id": "tenant_01HQ5P2R3",
  "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
  "state": "completed",
  "changes": [
    {
      "content_id": "content_01HQ5P2R3ABCDEF1234567890",
      "platform": "youtube",
      "previous_time": "2025-11-06T16:30:00-05:00",
      "new_time": "2025-11-06T18:15:00-05:00",
      "score_before": 0.68,
      "score_after": 0.84,
      "reason": "evening_engagement_peak",
      "confidence": 0.76
    }
  ],
  "metrics": {
    "total_targeted": 1,
    "changed_count": 1,
    "unchanged_count": 0,
    "average_score_lift": 0.16,
    "rate_limited": false
  },
  "created_at": "2025-11-05T03:50:00Z",
  "updated_at": "2025-11-05T03:50:45Z"
}
```

#### Optimization Factors

The optimization algorithm considers:

- **Historical Engagement**: Past performance during similar time windows
- **Audience Activity**: When target audience is most active
- **Platform Patterns**: Platform-specific posting behavior
- **Content Type**: Optimal timing for specific content categories  
- **Competition**: Avoid peak posting times to reduce competition
- **Geographic Considerations**: Time zone optimized for audience location
- **Day of Week**: Weekday vs weekend performance patterns
- **Seasonal Trends**: Time-based trends and seasonal variations

## WebSocket Real-Time Updates

Connect to WebSocket endpoint for real-time schedule and optimization updates.

**WebSocket URL**: `wss://api.content-automation.com/api/v1/scheduling/ws`

### Connection

**JavaScript**:
```javascript
const ws = new WebSocket('wss://api.content-automation.com/api/v1/scheduling/ws?schedule_id=sched_01HQ5P2T5CDEFGH3456789012');

ws.onopen = function(event) {
    console.log('Connected to scheduling updates');
    // Send authentication if required
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'your-jwt-token'
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    handleMessage(message);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log('Connection closed:', event.code, event.reason);
};
```

### Message Types

#### Client → Server

**Authentication**:
```json
{
  "type": "auth",
  "token": "your-jwt-token"
}
```

**Heartbeat**:
```json
{
  "type": "ping"
}
```

**Subscribe to Schedule**:
```json
{
  "type": "subscribe",
  "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012"
}
```

#### Server → Client

**Connection Established**:
```json
{
  "type": "connection_established",
  "data": {
    "message": "Connected to scheduling updates",
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012"
  }
}
```

**Schedule State Change**:
```json
{
  "type": "schedule.state_changed",
  "data": {
    "prior_state": "pending",
    "new_state": "running",
    "reason": "resources_available",
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012"
  },
  "correlation_id": "sched_01HQ5P2T5"
}
```

**Progress Update**:
```json
{
  "type": "schedule.progress",
  "data": {
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
    "percent_complete": 35.7,
    "items_total": 1000,
    "items_completed": 357,
    "items_failed": 2,
    "items_pending": 639,
    "eta_ms": 1845000,
    "rate_limited": false
  }
}
```

**Item Published**:
```json
{
  "type": "item.published",
  "data": {
    "id": "item_01HQ5P2U6DEFGHI4567890123",
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
    "platform": "youtube",
    "state": "published",
    "published_time": "2025-11-06T14:00:05-05:00",
    "metadata": {
      "url": "https://youtube.com/watch?v=example123",
      "post_id": "yt_post_789456123"
    }
  }
}
```

**Optimization Completed**:
```json
{
  "type": "optimization.completed",
  "data": {
    "opt_id": "opt_01HQ5P2V7EFGHIJ5678901234",
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
    "changes_count": 3,
    "summary": {
      "total_targeted": 5,
      "changed_count": 3,
      "unchanged_count": 2,
      "average_score_lift": 0.14
    }
  }
}
```

**Error Notification**:
```json
{
  "type": "item.failed",
  "data": {
    "id": "item_01HQ5P2W8FGHIJK6789012345",
    "schedule_id": "sched_01HQ5P2T5CDEFGH3456789012",
    "platform": "instagram",
    "state": "failed",
    "error": {
      "code": "platform_upload_failed",
      "message": "Failed to upload to Instagram: Rate limit exceeded",
      "timestamp": "2025-11-06T14:05:12Z"
    }
  }
}
```

## Utility Endpoints

### Health Check

Check the health and status of the scheduling service.

**Endpoint**: `GET /scheduling/health`

#### Request
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/health" \
  -H "Accept: application/json"
```

#### Response
```json
{
  "status": "healthy",
  "service": "scheduling_optimization",
  "version": "1.0.0",
  "timestamp": "2025-11-05T03:51:30Z",
  "uptime_seconds": 86400,
  "dependencies": {
    "database": "healthy",
    "cache": "healthy", 
    "queue_service": "healthy"
  }
}
```

### Supported Platforms

Get list of supported social media platforms and their capabilities.

**Endpoint**: `GET /scheduling/platforms`

#### Request
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/platforms" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

#### Response
```json
{
  "data": [
    {
      "id": "youtube",
      "name": "YouTube",
      "supports": ["long_form", "shorts"],
      "max_video_duration": 43200,
      "optimal_times": {
        "weekdays": ["14:00", "15:00", "20:00"],
        "weekends": ["09:00", "11:00", "16:00"]
      },
      "rate_limits": {
        "uploads_per_day": 6,
        "uploads_per_hour": 1
      }
    },
    {
      "id": "tiktok",
      "name": "TikTok",
      "supports": ["videos"],
      "max_video_duration": 600,
      "optimal_times": {
        "weekdays": ["18:00", "19:00", "21:00"],
        "weekends": ["10:00", "12:00", "20:00"]
      },
      "rate_limits": {
        "uploads_per_day": 3,
        "uploads_per_hour": 1
      }
    },
    {
      "id": "instagram",
      "name": "Instagram", 
      "supports": ["posts", "reels", "stories"],
      "max_video_duration": 90,
      "optimal_times": {
        "weekdays": ["11:00", "13:00", "19:00"],
        "weekends": ["10:00", "14:00", "16:00"]
      },
      "rate_limits": {
        "posts_per_day": 25,
        "stories_per_day": 100
      }
    },
    {
      "id": "linkedin",
      "name": "LinkedIn",
      "supports": ["posts", "articles"],
      "optimal_times": {
        "weekdays": ["08:00", "12:00", "17:00"],
        "weekends": ["10:00", "14:00"]
      },
      "rate_limits": {
        "posts_per_day": 10,
        "articles_per_week": 1
      }
    },
    {
      "id": "twitter",
      "name": "X (Twitter)",
      "supports": ["tweets", "threads"],
      "optimal_times": {
        "weekdays": ["09:00", "12:00", "15:00"],
        "weekends": ["12:00", "16:00", "19:00"]
      },
      "rate_limits": {
        "tweets_per_day": 50,
        "threads_per_day": 2
      }
    },
    {
      "id": "facebook",
      "name": "Facebook",
      "supports": ["posts", "videos"],
      "optimal_times": {
        "weekdays": ["13:00", "15:00", "19:00"],
        "weekends": ["12:00", "16:00", "18:00"]
      },
      "rate_limits": {
        "posts_per_day": 10,
        "videos_per_week": 25
      }
    }
  ]
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error_code": "specific_error_code",
  "error_message": "Human-readable error description",
  "error_class": "ExceptionClassName",
  "detail": {
    "field": "field_name",
    "value": "problematic_value",
    "expected": "expected_format_or_value"
  },
  "request_id": "req_01HQ5P2X9HIJKL7890123456",
  "timestamp": "2025-11-05T03:52:00Z"
}
```

### Common Error Codes

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `invalid_request` | 400 | Malformed request | Check request format and parameters |
| `validation_error` | 422 | Validation failed | Fix field validation errors |
| `unauthorized` | 401 | Invalid token | Refresh authentication token |
| `forbidden` | 403 | Insufficient permissions | Check API key scopes |
| `not_found` | 404 | Resource not found | Verify resource exists and ID is correct |
| `conflict` | 409 | Resource conflict | Handle idempotency or state conflicts |
| `rate_limited` | 429 | Rate limit exceeded | Implement exponential backoff |
| `service_unavailable` | 503 | Service temporarily unavailable | Retry with backoff |
| `internal_error` | 500 | Unexpected server error | Contact support with request_id |

### Error Handling Best Practices

1. **Always check HTTP status codes**
2. **Handle 401 by refreshing tokens**
3. **Implement exponential backoff for 429/503**
4. **Log request IDs for debugging**
5. **Validate request data before sending**
6. **Use idempotency keys for POST operations**

### Example Error Handling

```python
import requests
import time

def create_schedule_with_retry(schedule_data, max_retries=3):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Idempotency-Key': str(uuid.uuid4())
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'https://api.content-automation.com/api/v1/scheduling/calendar',
                json=schedule_data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Refresh token and retry
                token = refresh_auth_token()
                headers['Authorization'] = f'Bearer {token}'
            elif response.status_code == 429:
                # Rate limited, wait and retry
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
            elif response.status_code in [500, 503]:
                # Server error, retry with backoff
                time.sleep(2 ** attempt)
            else:
                # Other errors - log and handle
                error_data = response.json()
                raise Exception(f"API Error: {error_data['error_message']}")
                
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

## Rate Limiting

### Rate Limits

- **Default**: 100 requests per minute per tenant
- **Burst**: Up to 200 requests per minute
- **Optimization endpoints**: 10 requests per minute
- **WebSocket connections**: 10 connections per tenant

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701840000
X-RateLimit-Retry-After: 0
```

### Handling Rate Limits

**When Rate Limited (429)**:
```json
{
  "error_code": "rate_limited",
  "error_message": "Rate limit exceeded",
  "detail": {
    "limit": 100,
    "window": "1 minute",
    "retry_after": 45
  }
}
```

**Implementation Strategy**:
```javascript
const apiClient = {
    async request(endpoint, options = {}) {
        const response = await fetch(endpoint, {
            ...options,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get('Retry-After')) || 60;
            await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
            return this.request(endpoint, options); // Retry
        }
        
        return response;
    }
};
```

## Pagination

### Cursor-Based Pagination

All list endpoints use cursor-based pagination:

**Response Format**:
```json
{
  "data": [...],
  "page": {
    "next_page_token": "cursor_token_string",
    "previous_page_token": null,
    "page_size": 50
  }
}
```

**Request with Pagination**:
```bash
curl -X GET "https://api.content-automation.com/api/v1/scheduling/calendar/sched_01HQ5P2T5CDEFGH3456789012?page_token=eyJ0b2tlbiI6ICJwYWdlXzFfMjUwIn0"
```

### Pagination Best Practices

1. **Use provided tokens only** - don't construct your own
2. **Handle null tokens** - indicates end of results
3. **Implement maximum page limits** - avoid infinite loops
4. **Cache tokens appropriately** - respect TTL

## SDKs and Libraries

### Official SDKs

- **JavaScript/TypeScript**: `@content-automation/js-sdk`
- **Python**: `content-automation-python`  
- **PHP**: `content-automation/php-sdk`
- **Go**: `github.com/content-automation/go-sdk`

### Installation

**JavaScript**:
```bash
npm install @content-automation/js-sdk
```

**Python**:
```bash
pip install content-automation-python
```

### Basic Usage

**JavaScript**:
```typescript
import { ContentAutomation } from '@content-automation/js-sdk';

const client = new ContentAutomation({
    apiKey: 'your-api-key',
    baseUrl: 'https://api.content-automation.com'
});

// Get recommendations
const recommendations = await client.scheduling.getRecommendations({
    platforms: ['youtube', 'tiktok'],
    targetCount: 10,
    timezone: 'America/New_York'
});

// Create schedule
const schedule = await client.scheduling.createSchedule({
    title: 'Weekly Content',
    timezone: 'America/New_York',
    items: [
        {
            contentId: 'content_123',
            platform: 'youtube',
            scheduledTime: '2025-11-06T14:00:00-05:00'
        }
    ]
});
```

**Python**:
```python
from content_automation import ContentAutomation

client = ContentAutomation(
    api_key='your-api-key',
    base_url='https://api.content-automation.com'
)

# Get recommendations
recommendations = client.scheduling.get_recommendations(
    platforms=['youtube', 'tiktok'],
    target_count=10,
    timezone='America/New_York'
)

# Create schedule
schedule = client.scheduling.create_schedule(
    title='Weekly Content',
    timezone='America/New_York',
    items=[
        {
            'content_id': 'content_123',
            'platform': 'youtube', 
            'scheduled_time': '2025-11-06T14:00:00-05:00'
        }
    ]
)
```

## Testing

### Test Environment

**Base URL**: `https://api-staging.content-automation.com/api/v1`
**WebSocket URL**: `wss://api-staging.content-automation.com/api/v1/scheduling/ws`

### Testing Best Practices

1. **Use test data** - don't use production content for testing
2. **Isolate test environments** - use separate tenant IDs
3. **Mock WebSocket connections** - for automated testing
4. **Test error scenarios** - ensure proper error handling

### Sample Test Suite

```javascript
// scheduling_api.test.js
const { ContentAutomation } = require('@content-automation/js-sdk');

describe('Scheduling API', () => {
    let client;
    
    beforeAll(() => {
        client = new ContentAutomation({
            apiKey: process.env.TEST_API_KEY,
            baseUrl: process.env.TEST_API_URL
        });
    });
    
    test('should get recommendations', async () => {
        const recommendations = await client.scheduling.getRecommendations({
            platforms: ['youtube'],
            targetCount: 5
        });
        
        expect(recommendations.data).toHaveLength(5);
        expect(recommendations.data[0]).toHaveProperty('score');
        expect(recommendations.data[0].score).toBeGreaterThan(0);
        expect(recommendations.data[0].score).toBeLessThanOrEqual(1);
    });
    
    test('should create schedule', async () => {
        const scheduleData = {
            title: 'Test Schedule',
            timezone: 'UTC',
            items: [{
                contentId: 'test_content_123',
                platform: 'youtube',
                scheduledTime: '2025-11-06T14:00:00Z'
            }]
        };
        
        const schedule = await client.scheduling.createSchedule(scheduleData);
        
        expect(schedule.id).toBeDefined();
        expect(schedule.state).toBe('pending');
        expect(schedule.itemsTotal).toBe(1);
    });
    
    test('should handle validation errors', async () => {
        const invalidSchedule = {
            title: '', // Invalid - empty title
            items: []  // Invalid - empty items
        };
        
        await expect(
            client.scheduling.createSchedule(invalidSchedule)
        ).rejects.toThrow('validation_error');
    });
});
```

This completes the comprehensive Scheduling Optimization API Reference. For practical implementation examples and integration guides, see the accompanying documentation files.
