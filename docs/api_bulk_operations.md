# Bulk Operations API Reference

## Overview

The Bulk Operations API provides a scalable, secure, and evolvable RESTful interface for managing large-scale content generation workflows. It supports batch processing, real-time progress tracking, and multi-tenant isolation for enterprise-grade operations.

## Base URL

```
Development: https://api.dev.contentcreator.com/api/v1
Production: https://api.contentcreator.com/api/v1
```

## Authentication

All endpoints require JWT authentication via Bearer token:

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Required Scopes

- `jobs:read` - Query job status and lists
- `jobs:write` - Create and control jobs
- `sheets:connect` - Connect Google Sheets
- `videos:read` - List and fetch video artifacts

## Core Concepts

### Bulk Jobs
Bulk Jobs orchestrate batches of content generation work items. Each job:
- Processes multiple content items from an input source
- Tracks progress with real-time updates
- Produces artifacts (videos, manifests, reports)
- Supports lifecycle management (pause, resume, cancel)

### State Machine
Jobs progress through well-defined states:
- `pending` → `running` → `completed`
- `running` → `pausing` → `paused` → `running`
- `running` → `canceling` → `canceled`
- Any state → `failed`

### Progress Tracking
Each job provides:
- Percentage completion
- Item counts (total, completed, failed, skipped, canceled)
- Time metrics (time to start, processing time, ETA)
- Rate limiting indicators

## Endpoints

### 1. Create Bulk Job

Create a new bulk job for processing content generation tasks.

```http
POST /api/v1/bulk-jobs
```

#### Headers
```
Authorization: Bearer {token}
Content-Type: application/json
Idempotency-Key: {uuid}  # Optional for safe retries
```

#### Request Body
```json
{
  "title": "Spring Campaign Video Generation",
  "priority": "normal",
  "callback_url": "https://client.example.com/webhooks/job-complete",
  "processing_deadline_ms": 7200000,
  "input_source": {
    "type": "sheet",
    "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
    "range": "A1:Z1000"
  },
  "output": {
    "format": "mp4",
    "video_codec": "h264",
    "audio_codec": "aac",
    "resolution": "1080p",
    "output_bucket": "campaign-videos"
  },
  "template": {
    "template_id": "tpl_modern_promotional",
    "overrides": {
      "style": "modern",
      "voice": "professional_female",
      "background_music": "upbeat_corporate"
    }
  }
}
```

#### Response

**Status: 201 Created**
```json
{
  "id": "job_01HABCDEF0123456789",
  "tenant_id": "tenant_7x9y",
  "state": "pending",
  "percent_complete": 0.0,
  "items_total": 1000,
  "items_completed": 0,
  "items_failed": 0,
  "items_skipped": 0,
  "items_canceled": 0,
  "items_pending": 1000,
  "time_to_start_ms": null,
  "time_processing_ms": 0,
  "average_duration_ms_per_item": null,
  "eta_ms": null,
  "rate_limited": false,
  "processing_deadline_ms": 7200000,
  "callback_url": "https://client.example.com/webhooks/job-complete",
  "created_at": "2025-11-05T00:52:13Z",
  "updated_at": "2025-11-05T00:52:13Z",
  "idempotency_key": "2f1b3e9b-5c2d-4a5a-9b1e-0e5a8f3a2b1c",
  "sheet_source": {
    "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
    "range": "A1:Z1000",
    "connected_at": "2025-11-05T00:51:10Z"
  }
}
```

#### Validation Rules
- `items_total` must be between 1 and 10,000
- `sheet_id` must be a valid Google Sheets ID
- `range` must follow A1 notation (e.g., "A1:Z1000")
- `callback_url` must be a valid HTTPS URL
- `processing_deadline_ms` maximum is 24 hours (86400000 ms)

#### Error Responses

**400 Bad Request**
```json
{
  "error_code": "invalid_request",
  "error_message": "Invalid range format: A1:Z0",
  "error_class": "ValidationError",
  "detail": {
    "field": "input_source.range",
    "issue": "End row must be greater than start row"
  }
}
```

**422 Unprocessable Entity**
```json
{
  "error_code": "validation_error",
  "error_message": "Template not found",
  "error_class": "ResourceNotFound",
  "detail": {
    "field": "template.template_id",
    "issue": "Template tpl_nonexistent does not exist"
  }
}
```

### 2. Get Job Status

Retrieve detailed information about a specific bulk job.

```http
GET /api/v1/bulk-jobs/{id}
```

#### Path Parameters
- `id` (string, required) - Job identifier (format: `job_*`)

#### Headers
```
Authorization: Bearer {token}
```

#### Response

**Status: 200 OK**
```json
{
  "id": "job_01HABCDEF0123456789",
  "tenant_id": "tenant_7x9y",
  "state": "running",
  "percent_complete": 21.4,
  "items_total": 1000,
  "items_completed": 214,
  "items_failed": 2,
  "items_skipped": 3,
  "items_canceled": 1,
  "items_pending": 780,
  "time_to_start_ms": 2100,
  "time_processing_ms": 60000,
  "average_duration_ms_per_item": 280,
  "eta_ms": 2198000,
  "rate_limited": false,
  "processing_deadline_ms": 7200000,
  "callback_url": "https://client.example.com/webhooks/job-complete",
  "created_at": "2025-11-05T00:52:13Z",
  "updated_at": "2025-11-05T00:55:40Z",
  "sheet_source": {
    "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
    "range": "A1:Z1000",
    "connected_at": "2025-11-05T00:51:10Z"
  },
  "artifacts": [
    {
      "type": "manifest",
      "content_type": "application/json",
      "size": 4096,
      "url": "https://storage.example.com/tenant_7x9y/jobs/job_01HABCDEF0123456789/manifest.json"
    }
  ]
}
```

#### Error Responses

**404 Not Found**
```json
{
  "error_code": "not_found",
  "error_message": "Job job_01HNOTEXIST not found",
  "error_class": "ResourceNotFound"
}
```

### 3. List Job Videos

Retrieve paginated list of videos produced by a job.

```http
GET /api/v1/bulk-jobs/{id}/videos
```

#### Path Parameters
- `id` (string, required) - Job identifier

#### Query Parameters
- `page_token` (string, optional) - Cursor for pagination
- `page_size` (integer, optional, default: 50, max: 200) - Number of results per page
- `state` (string, repeated) - Filter by video state
- `sort` (string, optional) - Sort field: `created_at`, `updated_at`, `percent_complete`
- `order` (string, optional) - Sort order: `asc`, `desc` (default: `asc`)
- `expand` (string, repeated) - Expand additional data: `artifacts`, `errors`, `input_row`

#### Response

**Status: 200 OK**
```json
{
  "data": [
    {
      "id": "vid_01HXYZ1234567890",
      "job_id": "job_01HABCDEF0123456789",
      "state": "completed",
      "percent_complete": 100.0,
      "row_index": 1,
      "title": "Productivity Tips Video 1",
      "created_at": "2025-11-05T00:53:45Z",
      "updated_at": "2025-11-05T00:54:12Z",
      "artifacts": [
        {
          "type": "video",
          "content_type": "video/mp4",
          "size": 5242880,
          "url": "https://storage.example.com/tenant_7x9y/jobs/job_01HABCDEF0123456789/videos/vid_01HXYZ1234567890.mp4"
        },
        {
          "type": "thumbnail",
          "content_type": "image/jpeg",
          "size": 45600,
          "url": "https://storage.example.com/tenant_7x9y/jobs/job_01HABCDEF0123456789/thumbnails/vid_01HXYZ1234567890.jpg"
        }
      ],
      "errors": [],
      "input_row": {
        "A": "Intro",
        "B": "Voiceover Script Line 1",
        "C": "https://asset.example.com/image.png",
        "D": "5 minutes",
        "E": "professional"
      }
    },
    {
      "id": "vid_01HXYZ1234567891",
      "job_id": "job_01HABCDEF0123456789",
      "state": "failed",
      "percent_complete": 0.0,
      "row_index": 2,
      "title": "Productivity Tips Video 2",
      "created_at": "2025-11-05T00:53:45Z",
      "updated_at": "2025-11-05T00:54:03Z",
      "artifacts": [],
      "errors": [
        {
          "error_code": "asset_download_failed",
          "error_message": "Unable to download asset: https://broken-asset.example.com/image.png",
          "error_class": "UpstreamError",
          "occurred_at": "2025-11-05T00:54:02Z"
        }
      ],
      "input_row": {
        "A": "Main Content",
        "B": "Voiceover Script Line 2",
        "C": "https://broken-asset.example.com/image.png",
        "D": "8 minutes",
        "E": "professional"
      }
    }
  ],
  "page": {
    "next_page_token": "eyJvZmZzZXQiOjUwLCJzdGFydF9hZnRlciI6InZpZF8wMUhYWFgxMjM0NTY3ODkwIn0=",
    "page_size": 50
  }
}
```

#### Error Responses

**400 Bad Request**
```json
{
  "error_code": "invalid_request",
  "error_message": "Invalid sort field: invalid_field",
  "error_class": "ValidationError",
  "detail": {
    "field": "sort",
    "issue": "Sort field must be one of: created_at, updated_at, percent_complete"
  }
}
```

### 4. Connect Google Sheet

Register and validate access to a Google Sheet for use as job input source.

```http
POST /api/v1/sheets/connect
```

#### Headers
```
Authorization: Bearer {token}
Content-Type: application/json
```

#### Request Body
```json
{
  "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
  "range": "A1:Z1000",
  "share_permissions": "read"
}
```

#### Response

**Status: 200 OK**
```json
{
  "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
  "range": "A1:Z1000",
  "tenant_id": "tenant_7x9y",
  "status": "connected",
  "last_validated_at": "2025-11-05T00:52:00Z",
  "sample": {
    "row_count": 5,
    "columns": ["A", "B", "C", "D", "E"],
    "preview": [
      ["Intro", "Voiceover Script Line 1", "https://asset.example.com/image.png", "5 minutes", "professional"],
      ["Main Content", "Voiceover Script Line 2", "https://asset.example.com/image2.png", "8 minutes", "professional"],
      ["Case Study", "Voiceover Script Line 3", "https://asset.example.com/image3.png", "6 minutes", "casual"],
      ["Conclusion", "Voiceover Script Line 4", "https://asset.example.com/image4.png", "4 minutes", "professional"],
      ["CTA", "Voiceover Script Line 5", "https://asset.example.com/image5.png", "3 minutes", "energetic"]
    ]
  }
}
```

#### Error Responses

**403 Forbidden**
```json
{
  "error_code": "forbidden",
  "error_message": "Insufficient permissions to access sheet",
  "error_class": "AuthorizationError",
  "detail": {
    "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
    "issue": "Service account lacks read access to the specified sheet"
  }
}
```

### 5. List Bulk Jobs (Optional)

Retrieve paginated list of bulk jobs for the authenticated tenant.

```http
GET /api/v1/bulk-jobs
```

#### Query Parameters
- `page_token` (string, optional) - Cursor for pagination
- `page_size` (integer, optional, default: 50, max: 200) - Number of results per page
- `state` (string, repeated) - Filter by job state
- `sort` (string, optional) - Sort field: `created_at`, `updated_at`, `percent_complete`
- `order` (string, optional) - Sort order: `asc`, `desc` (default: `desc`)
- `created_after` (string, optional) - ISO 8601 timestamp filter
- `created_before` (string, optional) - ISO 8601 timestamp filter

#### Response

**Status: 200 OK**
```json
{
  "data": [
    {
      "id": "job_01HABCDEF0123456789",
      "state": "running",
      "title": "Spring Campaign Video Generation",
      "percent_complete": 21.4,
      "items_total": 1000,
      "items_completed": 214,
      "created_at": "2025-11-05T00:52:13Z",
      "updated_at": "2025-11-05T00:55:40Z"
    },
    {
      "id": "job_01HDEF0123456789012",
      "state": "completed",
      "title": "Product Tutorial Series",
      "percent_complete": 100.0,
      "items_total": 25,
      "items_completed": 25,
      "created_at": "2025-11-04T14:30:00Z",
      "updated_at": "2025-11-04T16:45:00Z"
    }
  ],
  "page": {
    "next_page_token": null,
    "page_size": 50
  }
}
```

## WebSocket Protocol

For real-time progress updates, connect to the WebSocket endpoint:

```
wss://api.contentcreator.com/api/v1/ws/bulk-jobs
```

### Connection Parameters
- `job_id` (query parameter) - Job to monitor
- `token` (query parameter) - JWT authentication token

### Authentication Header
```
Sec-WebSocket-Protocol: Bearer <jwt_token>
```

### Message Format

All WebSocket messages use this standard envelope:

```json
{
  "type": "event_type",
  "ts": "2025-11-05T00:55:30Z",
  "correlation_id": "8b2f-4a1c",
  "data": { /* event-specific payload */ }
}
```

### Event Types

#### Job State Change
```json
{
  "type": "job.state_changed",
  "ts": "2025-11-05T00:55:30Z",
  "correlation_id": "8b2f-4a1c",
  "data": {
    "prior_state": "pending",
    "new_state": "running",
    "reason": "resource_available"
  }
}
```

#### Progress Update
```json
{
  "type": "job.progress",
  "ts": "2025-11-05T00:55:32Z",
  "correlation_id": "8b2f-4a1c",
  "data": {
    "percent_complete": 15.3,
    "items_total": 1000,
    "items_completed": 153,
    "items_failed": 1,
    "items_skipped": 2,
    "items_canceled": 0,
    "items_pending": 844,
    "time_to_start_ms": 2100,
    "time_processing_ms": 42000,
    "average_duration_ms_per_item": 275,
    "eta_ms": 2327500,
    "rate_limited": false
  }
}
```

#### Video Completion
```json
{
  "type": "video.completed",
  "ts": "2025-11-05T00:55:40Z",
  "correlation_id": "8b2f-4a1c",
  "data": {
    "id": "vid_01HXYZ1234567890",
    "job_id": "job_01HABCDEF0123456789",
    "state": "completed",
    "percent_complete": 100.0,
    "artifacts": [
      {
        "type": "video",
        "content_type": "video/mp4",
        "size": 5242880,
        "url": "https://storage.example.com/vid_01HXYZ1234567890.mp4"
      }
    ]
  }
}
```

#### Job Completion
```json
{
  "type": "job.completed",
  "ts": "2025-11-05T01:30:00Z",
  "correlation_id": "8b2f-4a1c",
  "data": {
    "summary": {
      "items_total": 1000,
      "items_completed": 995,
      "items_failed": 3,
      "items_skipped": 2
    },
    "artifacts": [
      {
        "type": "manifest",
        "content_type": "application/json",
        "size": 10240,
        "url": "https://storage.example.com/job_01HABCDEF0123456789/manifest.json"
      }
    ]
  }
}
```

## Error Handling

### Standard Error Envelope

All errors follow this format:

```json
{
  "error_code": "error_type",
  "error_message": "Human-readable error description",
  "error_class": "ErrorClassification",
  "detail": {
    "field": "specific_field",
    "issue": "Detailed issue description"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Malformed request or invalid parameters |
| `validation_error` | 422 | Request failed semantic validation |
| `unauthorized` | 401 | Missing or invalid authentication |
| `forbidden` | 403 | Insufficient permissions or scope |
| `not_found` | 404 | Resource not found or not accessible |
| `conflict` | 409 | State conflict or idempotency violation |
| `rate_limited` | 429 | Rate limit or quota exceeded |
| `idempotency_conflict` | 409 | Idempotency key conflict |
| `internal_error` | 500 | Unexpected server error |
| `service_unavailable` | 503 | Temporary service outage |
| `gateway_timeout` | 504 | Upstream processing timeout |

## Rate Limiting

### Limits
- **Per-tenant RPS**: 10 requests per second
- **Burst capacity**: 2x per-minute allowance
- **Daily job creation limit**: 100 jobs
- **Total items per job**: 1-10,000 items

### Rate Limit Headers
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1641234567
X-RateLimit-Window: 60
```

### Retry Guidance
- Use `Retry-After` header for 429 responses
- Implement exponential backoff (1s, 2s, 4s, max 30s)
- Monitor `rate_limited` flag in job responses

## Idempotency

### Creating Jobs
Use the `Idempotency-Key` header to ensure safe retries:

```http
Idempotency-Key: 2f1b3e9b-5c2d-4a5a-9b1e-0e5a8f3a2b1c
```

- Keys are valid for 24 hours
- Keys are scoped per tenant
- Duplicate requests return the original job with current state
- Different requests must use different keys

## Pagination

### Cursor-Based Pagination
List endpoints use cursor-based pagination:

```
GET /api/v1/bulk-jobs/{id}/videos?page_size=50
```

Response includes `page.next_page_token`:

```json
{
  "data": [ /* results */ ],
  "page": {
    "next_page_token": "eyJvZmZzZXQiOjUwLCJzdGFydF9hZnRlciI6InZpZF8wMUhYWFgxMjM0NTY3ODkwIn0=",
    "page_size": 50
  }
}
```

Use the token for subsequent requests:

```
GET /api/v1/bulk-jobs/{id}/videos?page_token=eyJvZmZzZXQiOjUwLCJzdGFydF9hZnRlciI6InZpZF8wMUhYWFgxMjM0NTY3ODkwIn0=&page_size=50
```

### Page Size Limits
- Minimum: 10 items
- Maximum: 200 items
- Default: 50 items

## Processing Deadlines

### Setting Deadlines
Jobs support processing deadlines to bound total execution time:

```json
{
  "processing_deadline_ms": 7200000  // 2 hours
}
```

### Deadline Behavior
- System attempts to complete work within deadline
- Items exceeding deadline may be canceled
- Partial results retained based on retention policy
- Deadline violations emit appropriate WebSocket events

## Webhooks

### Job Completion Webhook
Jobs support callback URLs for completion notifications:

```json
{
  "callback_url": "https://client.example.com/webhooks/job-complete"
}
```

### Webhook Payload
```json
{
  "event": "job.completed",
  "job": {
    "id": "job_01HABCDEF0123456789",
    "state": "completed",
    "summary": {
      "items_total": 1000,
      "items_completed": 995,
      "items_failed": 3,
      "items_skipped": 2
    }
  },
  "timestamp": "2025-11-05T01:30:00Z",
  "signature": "sha256=..."
}
```

### Webhook Security
- Webhooks include HMAC signature for verification
- Clients should validate signatures before processing
- Signatures computed using webhook secret and payload

## Security Considerations

### Multi-Tenant Isolation
- All requests automatically filtered by tenant
- Resource IDs scoped to tenant
- No cross-tenant data leakage

### Data Protection
- All API endpoints use TLS 1.2+
- WebSocket connections use WSS
- Tokens should be short-lived (≤ 24 hours)
- PII handling follows applicable regulations

### Permission Model
- `jobs:read` - View job status and lists
- `jobs:write` - Create and manage jobs
- `sheets:connect` - Connect external sheet sources
- `videos:read` - Access video artifacts and metadata

## Best Practices

### Job Creation
1. Always use `Idempotency-Key` for retry-safe job creation
2. Validate sheet connectivity before creating large jobs
3. Set appropriate `processing_deadline_ms` based on workload
4. Use descriptive job titles for organization

### Progress Monitoring
1. Use WebSocket for real-time updates
2. Implement reconnection logic with exponential backoff
3. Store correlation IDs for support escalation
4. Monitor `rate_limited` flag to adjust UI

### Error Handling
1. Parse error envelope consistently
2. Implement retry logic with exponential backoff
3. Log correlation IDs for debugging
4. Provide user-friendly error messages

### Performance
1. Use pagination for large result sets
2. Filter list endpoints by state when possible
3. Cache job status to reduce API calls
4. Batch artifact downloads when possible

## SDK Support

### JavaScript/TypeScript

```javascript
import { BulkOperationsClient } from '@contentcreator/api-client';

const client = new BulkOperationsClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.contentcreator.com/api/v1'
});

// Create a bulk job
const job = await client.jobs.create({
  title: 'Spring Campaign',
  inputSource: {
    type: 'sheet',
    sheetId: '1A2B3C4D5E6F7G8H9I0J',
    range: 'A1:Z1000'
  },
  output: {
    format: 'mp4',
    resolution: '1080p'
  },
  template: {
    templateId: 'tpl_modern_promotional'
  }
});

// Monitor progress with WebSocket
client.jobs.watch(job.id, (event) => {
  if (event.type === 'job.progress') {
    console.log(`Progress: ${event.data.percent_complete}%`);
  }
});
```

### Python

```python
from contentcreator import BulkOperationsClient

client = BulkOperationsClient(
    api_key='your-api-key',
    base_url='https://api.contentcreator.com/api/v1'
)

# Create a bulk job
job = client.jobs.create({
    'title': 'Spring Campaign',
    'input_source': {
        'type': 'sheet',
        'sheet_id': '1A2B3C4D5E6F7G8H9I0J',
        'range': 'A1:Z1000'
    },
    'output': {
        'format': 'mp4',
        'resolution': '1080p'
    }
})

# Monitor progress
for event in client.jobs.watch(job['id']):
    if event['type'] == 'job.progress':
        print(f"Progress: {event['data']['percent_complete']}%")
```

## Changelog

### Version 1.0.0 (2025-11-05)
- Initial release of Bulk Operations API
- Support for job creation, monitoring, and artifact retrieval
- WebSocket real-time progress updates
- Google Sheets integration
- Multi-tenant security model

## Support

For API support and questions:
- Documentation: https://docs.contentcreator.com/api/bulk-operations
- Support Email: api-support@contentcreator.com
- Status Page: https://status.contentcreator.com
- Community Forum: https://community.contentcreator.com
