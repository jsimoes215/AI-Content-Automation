# RESTful API Design for Bulk Content Generation Operations

## Executive Summary

This document specifies a secure, scalable, and evolvable RESTful API and a companion WebSocket protocol for bulk content generation. The design centers on three primary resources—Bulk Jobs, Videos, and Sheets—and emphasizes a uniform interface, robust job orchestration, multi-tenant isolation, and real-time observability. The API employs predictable naming, consistent status codes, and explicit state machines to support reliable client integration and system maintainability.

### Design Goals and Non-Goals

The design aims to be a reliable foundation for clients to submit large batches of content generation workloads, track progress, fetch results, and receive real-time updates. It supports idempotency on job creation, pagination for high-volume outputs, and clear error semantics to simplify error handling and recovery.

Out of scope are billing and quota details, per-tenant storage specifics, client SDKs, and implementation-side worker architecture. These can be layered into the system without breaking compatibility, preserving a stable contract for clients.

### API Surface Overview

The API surface exposes:

- POST /api/bulk-jobs to create jobs, returning a job ID and initial state.
- GET /api/bulk-jobs/{id} for job status, aggregate progress, and state.
- GET /api/bulk-jobs/{id}/videos to list outputs per job, supporting pagination and filtering.
- POST /api/sheets/connect to register a Google Sheet source for batch inputs and validate access.
- A WebSocket channel for real-time progress and state updates.

Resource identifiers are immutable, and stable ETags are provided for list responses. Errors are returned using a canonical envelope to promote uniform client handling.

## Domain Model and State Machine

At the core of the system are Bulk Jobs, which orchestrate batches of work items (Videos) sourced from inputs. A job’s lifecycle is explicit and observable through both REST and WebSocket channels. Videos are the atomic outputs produced by a job, with states, progress, and error details.

To ground the model, Table 1 summarizes the Bulk Job state machine, followed by Table 2 for the Video state machine. Table 3 describes progress semantics, and Table 4 clarifies the relationships among bulk jobs, inputs, and outputs.

### Table 1: Bulk Job States

The following table outlines the canonical states, permitted transitions, and an overview of state-specific semantics.

| State            | Description                                                                 | Permitted Transitions                         | State-Specific Semantics                                                                 |
|------------------|-----------------------------------------------------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------------|
| pending          | Accepted but not yet running; queued for execution                          | running, canceling, failed                    | May be preemptively canceled; all times uninitialized until leaving pending              |
| running          | Actively being processed; workers dequeuing items                           | pausing, completing, canceling, failed        | Aggregated progress advances; time_to_start and processing_deadline may be set           |
| pausing          | Transitional state while orchestrator suspends execution                    | paused, running, canceling, failed            | Short-lived; transitions to paused when safe; otherwise resumes or aborts                |
| paused           | Execution suspended; can be resumed                                         | running, canceling                            | No new work items start; existing items may continue to completion depending on policy   |
| completing       | Finalization of completed items; preparing results                           | completed, failed                             | No new work starts; the orchestrator finalizes outputs and produces artifacts            |
| completed        | Terminal state indicating successful finish                                  | None                                          | Final metrics set; all items should be in completed or skipped states                    |
| canceling        | Stop requests in progress; terminating or rolling back as required          | canceled, failed                              | In-flight items may be canceled; partial outputs can be retained or invalidated          |
| canceled         | Terminal state after stop request                                            | None                                          | May retain completed items depending on retention policy                                 |
| failed           | Terminal state indicating a unrecoverable error                              | None                                          | An error_code and error_message summarize the root cause                                 |

State transitions are driven by the server, based on user actions, system health, or policy. This explicit model enables clients to reason about the system’s behavior and to automate responses.

### Table 2: Video States

Videos represent individual content items. Their states, transitions, and semantics are designed for granular observability and control.

| State       | Description                                  | Permitted Transitions                                  | State-Specific Semantics                                                     |
|-------------|----------------------------------------------|--------------------------------------------------------|------------------------------------------------------------------------------|
| pending     | Accepted but not yet processed               | processing, failed, skipped                            | Not assigned to a worker                                                      |
| processing  | Actively being worked on                     | completed, failed, canceled                            | Progress increments; heartbeats expected                                     |
| completed   | Finished successfully                        | None                                                    | artifacts and content references are available                               |
| failed      | Encountered an unrecoverable error           | None                                                    | error_code, error_message, and error_class capture diagnostics               |
| skipped     | Skipped intentionally per policy             | None                                                    | reason clarifies why the item was skipped                                   |
| canceled    | Stopped due to job-level cancelation         | None                                                    | partial results may be unavailable                                           |

This per-item state machine complements the job-level lifecycle, enabling clients to distinguish between transient interruptions and terminal failures.

### Table 3: Progress Semantics

Progress communicates execution throughput at both job and item levels. The following table clarifies fields, units, and computations.

| Field                                 | Level    | Unit    | Description                                                                                 | Example Values                       |
|---------------------------------------|----------|---------|---------------------------------------------------------------------------------------------|--------------------------------------|
| percent_complete                      | Job      | 0–100   | Aggregated ratio of completed and skipped items to total items                              | 42.3                                 |
| items_total                           | Job      | count   | Total number of items for the job                                                           | 10,000                               |
| items_completed                       | Job      | count   | Completed items count                                                                       | 4,200                                |
| items_failed                          | Job      | count   | Failed items count                                                                          | 45                                   |
| items_skipped                         | Job      | count   | Skipped items count                                                                         | 80                                   |
| items_canceled                        | Job      | count   | Canceled items count                                                                        | 10                                   |
| items_pending                         | Job      | count   | Items not yet completed (including processing, pending)                                     | 5,665                                |
| time_to_start_ms                      | Job      | ms      | Elapsed time since job creation until first item started processing                         | 2,500                                |
| time_processing_ms                    | Job      | ms      | Cumulative processing time across completed items                                           | 1,250,000                            |
| average_duration_ms_per_item          | Job      | ms      | Mean processing time per completed item                                                     | 300                                  |
| eta_ms                                | Job      | ms      | Estimated time remaining based on throughput                                                | 4,200,000                            |
| percent_complete                      | Video    | 0–100   | Item-level progress where applicable                                                         | 77.5                                 |
| processing_deadline_ms                | Job      | ms      | Maximum time allowed for processing before cancellation                                     | 1,800,000                            |
| rate_limited                          | Job      | boolean | True if rate limits are currently constraining throughput                                    | false                                |

Aggregate percent for a job is computed as (items_completed + items_skipped) / items_total. ETA derives from average duration per item and remaining count. All time fields are measured in milliseconds since epoch or elapsed intervals, depending on endpoint design.

### Table 4: Resource Relationships

This table explains how Bulk Jobs relate to their inputs and outputs, informing pagination, filtering, and expansion options in API responses.

| Relationship                          | Description                                                                                   | Pagination/Expansion Implications                                       |
|--------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| job -> videos (1:N)                  | A bulk job generates many videos over its lifecycle                                           | List endpoint supports pagination and optional expansion of metadata     |
| job -> sheet_source (1:1 optional)   | A job may reference a connected Google Sheet as the source of inputs                          | If present, the sheet metadata is returned in job details               |
| job -> artifacts (1:N)               | Outputs like manifests, archives, or reports may be attached to a job                         | Artifact references are included in job response when available         |
| video -> artifacts (1:N)             | Each video may have associated files (e.g., media, thumbnails)                                | List and detail views expose artifact metadata and retrieval links      |

These relationships define the shape of responses and influence client workflows for tracking job progress and retrieving results.

## Common API Conventions

The API follows consistent conventions to reduce client complexity and enhance evolvability.

### Resource Naming and Versioning

All endpoints are prefixed with /api/v1 to isolate breaking changes. Paths use hyphenated lowercase plural nouns. Resource identifiers are immutable.

### Authentication, Authorization, and Multi-Tenancy

Authentication is required via a Bearer token. Claims include subject, scopes, and tenant identifiers. Authorization checks enforce tenant isolation and scope requirements. Request filtering is required to restrict responses to the tenant of the caller.

### Idempotency and Safe Retries

Creation of a bulk job supports idempotency by accepting an optional idempotency_key in headers and body. The server treats duplicate keys from the same tenant as references to the prior job. Idempotency is respected for a configurable window; responses are stable and reproducible.

### Pagination, Sorting, Filtering

List endpoints employ cursor-based pagination using page_token and next_page_token, returning page_size when specified. Sorting is available by created_at, updated_at, and percent_complete. Filtering is supported by state using a repeated state parameter. Server-driven throttle may adjust page_size for fairness under load.

### Error Envelope and Tracing

All error responses use a standard envelope containing error_code, error_message, and error_class fields, with a detail object for additional context. Correlation IDs and trace IDs are returned in response headers to aid diagnostics. Clients are encouraged to log these IDs for support and observability.

To illustrate standard error handling, Table 5 enumerates common error types and the corresponding HTTP statuses.

### Table 5: Error Types and HTTP Status Mapping

| Error Type                   | HTTP Status | Description                                                                                 |
|-----------------------------|-------------|---------------------------------------------------------------------------------------------|
| invalid_request             | 400         | Malformed request body or query parameters                                                  |
| validation_error            | 422         | Semantics failed validation (e.g., missing required fields)                                 |
| unauthorized                | 401         | Missing or invalid authentication                                                           |
| forbidden                   | 403         | Authenticated but lacking required scope or permissions                                     |
| not_found                   | 404         | Resource not found or not visible to the caller                                             |
| conflict                    | 409         | State conflict (e.g., state transition not allowed)                                         |
| rate_limited                | 429         | Request rejected due to rate limits                                                         |
| idempotency_conflict        | 409         | Provided idempotency_key conflicts with a different resource                                |
| quota_exceeded              | 429         | Per-tenant quota exceeded                                                                   |
| internal_error              | 500         | Unexpected server error                                                                     |
| service_unavailable         | 503         | Service unable to handle the request due to temporary outage                                |
| gateway_timeout             | 504         | Upstream processing exceeded configured timeouts                                            |

## Endpoint Specifications

This section defines the endpoints, their request and response schemas, and examples.

### POST /api/v1/bulk-jobs

Create a new bulk job. This endpoint accepts job configuration, validates it, initializes state, and returns a job ID.

#### Request

Headers:
- Authorization: Bearer {token}
- Content-Type: application/json
- Idempotency-Key: {uuid} (optional)

Body:
```json
{
  "title": "Campaign Spring Launch",
  "priority": "normal",
  "callback_url": "https://client.example.com/webhooks/job",
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
    "template_id": "tpl_abc123",
    "overrides": {
      "style": "modern",
      "voice": "female"
    }
  }
}
```

#### Response

Status: 201 Created

Body:
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
  "callback_url": "https://client.example.com/webhooks/job",
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

Validation and error handling:
- 400 invalid_request for malformed bodies.
- 422 validation_error for invalid ranges or unsupported options.
- 401 unauthorized / 403 forbidden for missing or insufficient scopes.
- 409 conflict if the idempotency_key refers to a different resource or state conflict occurs.
- 429 rate_limited or quota_exceeded when requests exceed limits.
- 503 service_unavailable when service is temporarily unavailable.

#### Idempotency Semantics

When Idempotency-Key is provided, subsequent identical requests from the same tenant within the idempotency window return the original job with its current state, using the same response schema. Keys are scoped per tenant to prevent cross-tenant conflicts.

#### Notes on Scopes and Tenancy

Creation of a job typically requires scope: jobs:write. The tenant_id is derived from the caller’s claims, and the service filters and enforces access accordingly. Clients must not supply tenant_id in the body; if present, it must match the authenticated tenant or the request is rejected.

### GET /api/v1/bulk-jobs/{id}

Get job status, progress, and related metadata for a single job.

#### Request

Headers:
- Authorization: Bearer {token}

Path parameter:
- id: job_ string identifier

#### Response

Status: 200 OK

Body:
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
  "callback_url": "https://client.example.com/webhooks/job",
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

Error handling:
- 401 unauthorized, 403 forbidden for scope or access violations.
- 404 not_found if the job ID is not found or belongs to a different tenant.
- 409 conflict if a requested state transition is invalid.
- 500 internal_error for unexpected failures.

### GET /api/v1/bulk-jobs/{id}/videos

List individual videos produced by the job. Supports pagination, filtering, and optional metadata expansion.

#### Request

Headers:
- Authorization: Bearer {token}

Query parameters:
- page_token (string, optional): cursor for pagination
- page_size (integer, optional, default 50, max 200)
- state (string, repeated): filter by video state (e.g., completed, failed)
- sort (string, optional): field to sort by (created_at, updated_at, percent_complete)
- order (string, optional): asc or desc (default asc)
- expand (string, repeated): optional expansions (artifacts, errors, input_row)

#### Response

Status: 200 OK

Body:
```json
{
  "data": [
    {
      "id": "vid_01HXYZ1234567890",
      "job_id": "job_01HABCDEF0123456789",
      "state": "completed",
      "percent_complete": 100.0,
      "row_index": 1,
      "title": "Video 1",
      "created_at": "2025-11-05T00:53:45Z",
      "updated_at": "2025-11-05T00:54:12Z",
      "artifacts": [
        {
          "type": "video",
          "content_type": "video/mp4",
          "size": 5242880,
          "url": "https://storage.example.com/tenant_7x9y/jobs/job_01HABCDEF0123456789/videos/vid_01HXYZ1234567890.mp4"
        }
      ],
      "errors": [],
      "input_row": {
        "A": "Intro",
        "B": "Voiceover Script Line 1",
        "C": "https://asset.example.com/image.png"
      }
    },
    {
      "id": "vid_01HXYZ1234567891",
      "job_id": "job_01HABCDEF0123456789",
      "state": "failed",
      "percent_complete": 0.0,
      "row_index": 2,
      "title": "Video 2",
      "created_at": "2025-11-05T00:53:45Z",
      "updated_at": "2025-11-05T00:54:03Z",
      "artifacts": [],
      "errors": [
        {
          "error_code": "render_failed",
          "error_message": "Asset unavailable",
          "error_class": "UpstreamError",
          "occurred_at": "2025-11-05T00:54:02Z"
        }
      ],
      "input_row": {
        "A": "Body",
        "B": "Voiceover Script Line 2",
        "C": "https://asset-missing.example.com/image.png"
      }
    }
  ],
  "page": {
    "next_page_token": "eyJvZmZzZXQiOjUwLCJzdGFydF9hZnRlciI6InZpZF8wMUhYWFgxMjM0NTY3ODkwIn0=",
    "page_size": 50
  }
}
```

Error handling:
- 400 invalid_request for unsupported sort or order values.
- 401 unauthorized, 403 forbidden for access violations.
- 404 not_found if the job does not exist or is not accessible.
- 409 conflict if a conflicting request state is detected (e.g., job canceled while listing).
- 500 internal_error for unexpected failures.

### POST /api/v1/sheets/connect

Connect or validate access to a Google Sheet for use as a job input source. This endpoint registers the sheet with the tenant, validates read access, and optionally warms the cache by fetching a small sample.

#### Request

Headers:
- Authorization: Bearer {token}
- Content-Type: application/json

Body:
```json
{
  "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
  "range": "A1:Z1000",
  "share_permissions": "read"
}
```

#### Response

Status: 200 OK

Body:
```json
{
  "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
  "range": "A1:Z1000",
  "tenant_id": "tenant_7x9y",
  "status": "connected",
  "last_validated_at": "2025-11-05T00:52:00Z",
  "sample": {
    "row_count": 5,
    "columns": ["A", "B", "C", "D", "E"]
  }
}
```

#### Security Considerations

The service should not store raw tokens in plaintext. Short-lived tokens or restricted-scoped tokens are preferred. Access is validated using read-only scopes. Clients must ensure callback endpoints protect personal data and comply with applicable policies.

#### Error Handling

- 400 invalid_request for malformed sheet_id or range.
- 401 unauthorized for missing or invalid credentials.
- 403 forbidden when the token lacks read permission to the sheet.
- 409 conflict if a connection with different parameters already exists for the tenant.
- 422 validation_error when the sheet exists but the specified range is invalid or empty.
- 429 rate_limited if requests exceed limits.
- 500 internal_error for unexpected failures.

## WebSocket Protocol for Real-Time Progress

A WebSocket channel provides real-time updates of job and item states, enabling clients to render live progress dashboards and trigger event-driven integrations.

### Connection and Authentication

Clients connect to a secure WebSocket endpoint and supply an authentication token and job_id as a query parameter. The service validates tenant access and emits updates only for jobs within the authenticated tenant’s scope. Connections are single-tenant and isolated.

### Message Schema and Event Types

Messages use a standard envelope and event types to ensure predictable parsing. The envelope is composed of type, ts (timestamp), correlation_id, and data.

Event types and their data payloads:
- job.state_changed: prior_state, new_state, reason
- job.progress: current metrics, as in the job detail response
- video.created: video object (subset of fields)
- video.updated: video object or delta
- video.completed: video object plus artifact references
- video.failed: video object with error details
- job.completed: final job summary and artifacts
- job.canceled: final job summary and partial results info
- job.failed: final error details at job level

The following table standardizes these event types, followed by a state-transition event matrix to guide client responses.

### Table 6: WebSocket Event Types

| Type             | Trigger Condition                                      | Data Fields Included                                              | Client Handling Guidance                                                                 |
|------------------|--------------------------------------------------------|-------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| job.state_changed| Job enters a new state                                 | prior_state, new_state, reason                                    | Update UI state; gate actions based on new_state                                         |
| job.progress     | Periodic or on threshold change                        | percent_complete, items_*, time_to_start_ms, time_processing_ms   | Update progress bars and throughput metrics                                              |
| video.created    | New video item is recognized                           | id, job_id, state, row_index, title                               | Add item to lists; enable item-level tracking                                            |
| video.updated    | Item progress or metadata changes                      | id, job_id, state, percent_complete, updated_at                   | Refresh item details; handle transient states                                            |
| video.completed  | Item completed successfully                            | id, artifacts (type, content_type, size, url)                     | Enable download or playback                                                              |
| video.failed     | Item failed                                            | id, errors (error_code, error_message, error_class)               | Show error; optionally prompt retry if policy permits                                    |
| job.completed    | Job reached completed state                            | summary fields, artifacts                                         | Finalize; persist manifest; trigger client-side post-processing                          |
| job.canceled     | Job reached canceled state                             | summary fields, partial artifacts info                            | Clean up; mark canceled items as unavailable                                             |
| job.failed       | Job reached failed state                               | error_code, error_message, error_class                            | Show failure; log correlation_id; consider alerting                                      |

### Table 7: State Transition Event Matrix

| From State | To State   | WebSocket Events Emitted                      | Notes                                                                                 |
|------------|------------|-----------------------------------------------|---------------------------------------------------------------------------------------|
| pending    | running    | job.state_changed, job.progress               | Start heartbeats; time_to_start_ms set                                               |
| running    | pausing    | job.state_changed                              | Short-lived; no new items start                                                      |
| pausing    | paused     | job.state_changed                              | Execution suspended; can be resumed                                                  |
| paused     | running    | job.state_changed, job.progress                | Resumed; restart progress updates                                                     |
| running    | completing | job.state_changed                              | No new items; finalize outputs                                                        |
| completing | completed  | job.state_changed, job.completed               | Terminal state; emit artifacts                                                        |
| running    | canceling  | job.state_changed                              | Terminate in-flight items; partial retention policy applies                           |
| canceling  | canceled   | job.state_changed, job.canceled                | Terminal state; no further events                                                     |
| any        | failed     | job.state_changed, job.failed                  | Terminal; error payload includes diagnostics                                          |

### Sample WebSocket Frames

A text frame announcing state change:
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

A progress update:
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

A video completion event:
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
        "url": "https://storage.example.com/tenant_7x9y/jobs/job_01HABCDEF0123456789/videos/vid_01HXYZ1234567890.mp4"
      }
    ]
  }
}
```

## Operational Concerns

Operational reliability requires careful management of concurrency, rate limits, timeouts, and resilience features such as circuit breakers. The API exposes indicators like rate_limited and uses HTTP 429 to signal when the client should back off.

### Concurrency and Rate Limiting

Per-tenant rate limiting applies to all endpoints. Clients should implement exponential backoff and respect Retry-After headers where provided. Under high load, the server may return 429 rate_limited or 503 service_unavailable.

### Idempotency and Safe Retries

Creation endpoints accept Idempotency-Key. When a client retries, the server returns the original job and its current state within the idempotency window. Clients must not reuse idempotency keys across tenants or across materially different requests.

### WebSocket Resilience

WebSocket connections should anticipate temporary disconnects. Clients reconnect and resume using a last_event_timestamp. The service may include missed events in a catch-up payload upon reconnect to maintain consistency.

### Timeouts and Deadlines

A processing_deadline_ms can be specified to bound total processing time for a job. The system aims to complete work within the deadline; items or jobs exceeding the deadline may be canceled with appropriate events and artifacts.

#### Table 8: Rate Limit and Backoff Parameters

| Parameter                 | Value / Guidance                      | Description                                                                 |
|--------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| Per-tenant RPS           | Configurable (e.g., 10 RPS)            | Requests per second allowed per tenant                                      |
| Burst Capacity           | 2x per-minute                          | Short-term capacity to accommodate spikes                                  |
| Retry-After              | Returned on 429                        | Duration to wait before retrying                                            |
| WebSocket Reconnect Backoff | Exponential (e.g., 1s, 2s, 4s, max 30s) | Progressive backoff to prevent thundering herds                             |
| Idempotency Window       | 24 hours                               | Duration within which idempotency keys are honored                          |
| Page Size Limits         | Min 10, Max 200                        | Enforced fairness and response size management                              |

## Example Scenarios

This section illustrates end-to-end flows to demonstrate how clients should interact with the API under common conditions.

### End-to-End Flow: Create Job from Sheet, Track Progress, Retrieve Outputs

1. Connect the sheet:
   - POST /api/v1/sheets/connect with sheet_id and range.
   - Expect 200 OK with status connected and sample metadata.

2. Create the job:
   - POST /api/v1/bulk-jobs with input_source type sheet, referencing the connected sheet_id and range.
   - Accept the 201 Created response with job id and initial state pending.

3. Monitor progress:
   - Open a WebSocket connection with job_id and token.
   - Receive job.state_changed and periodic job.progress events; update the UI accordingly.

4. Fetch outputs:
   - Use GET /api/v1/bulk-jobs/{id}/videos with pagination and filter state=completed to retrieve links to artifacts.
   - Download or process artifacts as needed.

5. Completion:
   - Receive job.completed via WebSocket; fetch the final manifest artifact and archive results for downstream workflows.

### Cancel and Resume Flow

- Client requests cancel through a dedicated action endpoint (assumed), setting the job into canceling.
- WebSocket emits job.state_changed events; completed items may remain available per retention policy.
- To resume, create a new job referencing the same sheet source or use server-side resume capability (if provided), avoiding duplication via idempotency.

### WebSocket Reconnect and Catch-Up

- On disconnect, clients reconnect with last_event_timestamp in the query parameters.
- The server sends a catch-up payload containing events since the last timestamp.
- Clients merge events to maintain consistent state.

#### Table 9: Scenario Timeline

| Step | Action                                   | Request/Event                               | Response/Event                                        | Outcome                                           |
|------|-------------------------------------------|---------------------------------------------|-------------------------------------------------------|---------------------------------------------------|
| 1    | Connect Google Sheet                      | POST /api/v1/sheets/connect                  | 200 OK with status connected                          | Sheet is registered and validated                 |
| 2    | Create bulk job                           | POST /api/v1/bulk-jobs                       | 201 Created with job id and state pending             | Job is queued                                     |
| 3    | Start job                                 | (system)                                     | job.state_changed: pending -> running                 | Processing begins                                 |
| 4    | Track progress                            | WebSocket                                    | job.progress (periodic), video.created/updated events | Live dashboard updates                            |
| 5    | Fetch outputs                             | GET /api/v1/bulk-jobs/{id}/videos            | 200 OK with paginated list                            | Artifacts are available for download              |
| 6    | Complete job                              | (system)                                     | job.state_changed: running -> completing -> completed | Terminal state with final summary and artifacts   |

## Security and Compliance

The API must protect data in transit and at rest, enforce least-privilege access, and handle personal data with care.

### Transport Security

All endpoints, including WebSocket, use TLS. Clients should validate certificates and avoid transmitting tokens over insecure channels.

### Authorization and Scope Model

Scopes govern access:
- jobs:read to query job status and lists.
- jobs:write to create and control jobs.
- sheets:connect to connect or validate Google Sheets.
- videos:read to list and fetch artifacts.

Tenants are strictly isolated. Requests are filtered to ensure only resources within the authenticated tenant are returned.

### Data Protection

Tokens and credentials are handled according to least-privilege principles. Short-lived tokens reduce exposure. Callback URLs must be protected and should not expose personal data unnecessarily. Personal data present in sheet inputs or video metadata should be processed in accordance with applicable policies.

## Extensibility, Versioning, and Migration

Versioning is achieved through the /api/v1 prefix. Future enhancements can introduce /api/v2 without breaking clients. Additive fields, new event types, and optional expansions are the preferred evolution path.

Deprecations are communicated via:
- Response headers indicating deprecation status and sunset dates.
- Documentation updates with migration guidance.
- Optional warnings on non-critical fields.

#### Table 10: Version Compatibility Matrix

| Feature/Field                     | v1 Support | v2 Plan | Migration Notes                                                                     |
|----------------------------------|------------|---------|-------------------------------------------------------------------------------------|
| Bulk Jobs core fields            | Yes        | Yes     | Core fields preserved; additive changes only                                        |
| Video.artifacts.type             | Yes        | Yes     | New artifact types may be added                                                     |
| WebSocket events                 | Yes        | Yes     | New event types added; existing semantics unchanged                                 |
| sheet_source.range syntax        | Yes        | Yes     | Existing syntax supported; new syntax introduced alongside                          |
| processing_deadline_ms           | Yes        | Yes     | Retained; behavior may be refined                                                   |
| ETags for list responses         | Yes        | Yes     | ETag semantics stable; conditional requests                                         |

## Appendix: Schemas, Status Codes, and Glossary

### JSON Schemas

BulkJobCreateRequest:
```json
{
  "type": "object",
  "required": ["input_source", "output", "template"],
  "properties": {
    "title": { "type": "string", "maxLength": 200 },
    "priority": { "type": "string", "enum": ["low", "normal", "high"] },
    "callback_url": { "type": "string", "format": "uri" },
    "processing_deadline_ms": { "type": "integer", "minimum": 0 },
    "input_source": {
      "type": "object",
      "required": ["type", "sheet_id", "range"],
      "properties": {
        "type": { "type": "string", "enum": ["sheet"] },
        "sheet_id": { "type": "string", "minLength": 10, "maxLength": 200 },
        "range": { "type": "string", "minLength": 1 }
      }
    },
    "output": {
      "type": "object",
      "required": ["format", "video_codec", "audio_codec", "resolution", "output_bucket"],
      "properties": {
        "format": { "type": "string", "enum": ["mp4", "mov", "webm"] },
        "video_codec": { "type": "string", "enum": ["h264", "h265", "vp9"] },
        "audio_codec": { "type": "string", "enum": ["aac", "opus"] },
        "resolution": { "type": "string", "enum": ["720p", "1080p", "4k"] },
        "output_bucket": { "type": "string", "minLength": 1 }
      }
    },
    "template": {
      "type": "object",
      "required": ["template_id"],
      "properties": {
        "template_id": { "type": "string", "minLength": 1 },
        "overrides": { "type": "object", "additionalProperties": true }
      }
    },
    "idempotency_key": { "type": "string", "format": "uuid" }
  }
}
```

BulkJob:
```json
{
  "type": "object",
  "required": ["id", "tenant_id", "state"],
  "properties": {
    "id": { "type": "string" },
    "tenant_id": { "type": "string" },
    "state": { "type": "string", "enum": ["pending", "running", "pausing", "paused", "completing", "completed", "canceling", "canceled", "failed"] },
    "percent_complete": { "type": "number", "minimum": 0, "maximum": 100 },
    "items_total": { "type": "integer", "minimum": 0 },
    "items_completed": { "type": "integer", "minimum": 0 },
    "items_failed": { "type": "integer", "minimum": 0 },
    "items_skipped": { "type": "integer", "minimum": 0 },
    "items_canceled": { "type": "integer", "minimum": 0 },
    "items_pending": { "type": "integer", "minimum": 0 },
    "time_to_start_ms": { "type": ["integer", "null"], "minimum": 0 },
    "time_processing_ms": { "type": "integer", "minimum": 0 },
    "average_duration_ms_per_item": { "type": ["number", "null"] },
    "eta_ms": { "type": ["integer", "null"], "minimum": 0 },
    "rate_limited": { "type": "boolean" },
    "processing_deadline_ms": { "type": "integer", "minimum": 0 },
    "callback_url": { "type": ["string", "null"], "format": "uri" },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "idempotency_key": { "type": ["string", "null"] },
    "sheet_source": {
      "type": ["object", "null"],
      "properties": {
        "sheet_id": { "type": "string" },
        "range": { "type": "string" },
        "connected_at": { "type": "string", "format": "date-time" }
      }
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "content_type", "size", "url"],
        "properties": {
          "type": { "type": "string", "enum": ["manifest", "video", "thumbnail", "report"] },
          "content_type": { "type": "string" },
          "size": { "type": "integer", "minimum": 0 },
          "url": { "type": "string", "format": "uri" }
        }
      }
    }
  }
}
```

Video:
```json
{
  "type": "object",
  "required": ["id", "job_id", "state"],
  "properties": {
    "id": { "type": "string" },
    "job_id": { "type": "string" },
    "state": { "type": "string", "enum": ["pending", "processing", "completed", "failed", "skipped", "canceled"] },
    "percent_complete": { "type": "number", "minimum": 0, "maximum": 100 },
    "row_index": { "type": "integer", "minimum": 0 },
    "title": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "content_type", "size", "url"],
        "properties": {
          "type": { "type": "string", "enum": ["video", "thumbnail", "caption", "metadata"] },
          "content_type": { "type": "string" },
          "size": { "type": "integer", "minimum": 0 },
          "url": { "type": "string", "format": "uri" }
        }
      }
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["error_code", "error_message", "error_class", "occurred_at"],
        "properties": {
          "error_code": { "type": "string" },
          "error_message": { "type": "string" },
          "error_class": { "type": "string" },
          "occurred_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "input_row": { "type": "object", "additionalProperties": true }
  }
}
```

ErrorEnvelope:
```json
{
  "type": "object",
  "required": ["error_code", "error_message"],
  "properties": {
    "error_code": { "type": "string" },
    "error_message": { "type": "string" },
    "error_class": { "type": "string" },
    "detail": { "type": "object", "additionalProperties": true }
  }
}
```

#### Table 11: HTTP Status Codes Usage

| Status Code       | Scenario                                                        | Retry Guidance                                                    |
|-------------------|------------------------------------------------------------------|-------------------------------------------------------------------|
| 200 OK            | Successful GET/POST with response body                           | None                                                              |
| 201 Created       | Successful job creation                                          | None                                                              |
| 400 Bad Request   | Malformed request                                                | Fix request                                                       |
| 401 Unauthorized  | Missing/invalid token                                            | Obtain valid token                                                |
| 403 Forbidden     | Insufficient scope                                               | Request appropriate scopes                                        |
| 404 Not Found     | Resource missing or not visible                                  | Confirm identifier and tenant                                     |
| 409 Conflict      | State conflict or idempotency conflict                           | Do not retry blindly; review state and idempotency                |
| 422 Unprocessable Entity | Validation failure                                        | Correct input                                                     |
| 429 Too Many Requests | Rate limit or quota exceeded                              | Backoff and retry after Retry-After                               |
| 500 Internal Server Error | Unexpected server error                                | Retry with backoff                                                |
| 503 Service Unavailable | Temporary outage                                         | Retry with exponential backoff                                    |
| 504 Gateway Timeout | Upstream timeout                                              | Retry with backoff; consider adjusting deadlines                  |

#### Table 12: Glossary of Terms

| Term                         | Definition                                                                                   |
|------------------------------|----------------------------------------------------------------------------------------------|
| Bulk Job                     | Orchestrated batch of content generation items                                               |
| Video                        | Individual content item produced by a job                                                    |
| Sheet Source                 | Registered Google Sheet used as input for a job                                              |
| State Machine                | Explicit set of states and transitions governing lifecycle                                   |
| Progress                     | Aggregated and per-item metrics indicating completion and throughput                         |
| Artifact                     | Output file or metadata produced by a job or video                                           |
| Tenant                       | Isolated organizational context for multi-tenant security                                    |
| Idempotency                  | Property ensuring duplicate requests produce the same effect within a window                 |
| Cursor-Based Pagination      | List navigation using tokens rather than offsets                                             |
| ETag                         | Entity tag for cache validation of list responses                                            |
| Correlation ID               | Identifier for tracing requests and events across components                                 |
| Rate Limiting                | Enforcing per-tenant request rate and quota constraints                                      |
| Processing Deadline          | Maximum time allowed for processing before cancellation                                      |
| Callback URL                 | Client-provided endpoint for receiving job lifecycle notifications                           |
| WebSocket                    | Full-duplex protocol for real-time updates                                                   |

## Information Gaps and Assumptions

Several operational parameters are intentionally left configurable and will be finalized during implementation:

- Authentication scheme and token format (e.g., JWT claims, token lifetimes) are not specified.
- Per-tenant rate limits, quota policies, and burst thresholds require configuration.
- Detailed fields for the Google Sheet payload and validation logic are partially defined.
- Artifact storage locations and access URL format (signed URL vs. public) are not fixed.
- Idempotency window and conflict handling specifics need to be established.
- Processing deadline units and policy (enforcement vs. advisory) require confirmation.
- WebSocket authentication and reconnection semantics (handshake details and missed event handling) need specification.
- Pagination parameters (default page size and max) and ordering options are defined in principle but values are examples.
- Error code taxonomy beyond common error types is not exhaustive.
- ETags and cache semantics for list endpoints are mentioned, but specifics need configuration.
- Callbacks/webhooks payload format and signature verification are referenced but not detailed.
- Concurrency controls for pausing/resuming and item-level cancellation are assumed but not specified.
- Retention policies for canceled/failed jobs and partial outputs need definition.

These gaps do not affect the stability of the core API contract but will be elaborated in operational playbooks and configuration.

## Conclusion

This API design provides a robust and evolvable foundation for bulk content generation workloads. By combining a clear resource model, explicit state machines, uniform error handling, and real-time event delivery, it enables clients to build reliable, responsive workflows. The endpoints and protocol are structured to support multi-tenant security, operational resilience, and future extensions without breaking compatibility.