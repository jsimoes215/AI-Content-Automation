# Scheduling Optimization API Blueprint

## Executive Summary and Objectives

This blueprint defines a secure, evolvable, and tenant-aware RESTful API and companion WebSocket protocol for a scheduling optimization system. The API enables clients to discover optimal posting times, create and manage posting schedules, and continuously optimize timing for existing content. It borrows proven conventions from the existing architecture—predictable resource naming, uniform error envelopes, explicit state machines, robust pagination, and real-time updates—so product teams can integrate scheduling features with confidence.

The core use cases are threefold. First, clients can request recommended posting windows derived from historical engagement patterns, content metadata, and operational constraints. Second, clients can create and manage calendars of scheduled posts, including concrete times, platforms, and optional callbacks for downstream automation. Third, clients can request optimization for content already assigned to schedules, shifting times to improve reach or compliance with policies. The design emphasizes idempotent creation of schedules, precise error semantics, and real-time updates via WebSocket.

Out of scope are billing and quota enforcement (layered later), platform-specific publishing integrations, and client SDKs. The API contract is versioned (/api/v1), uses Bearer authentication with tenant isolation, and standardizes HTTP statuses and error envelopes. The outcome is a stable contract that product engineers and integrators can rely on, while leaving room for future enhancements such as richer recommendation algorithms and expanded schedule semantics.

## API Conventions Alignment

The scheduling API aligns with the existing architecture in naming, versioning, authentication, and operational semantics. Paths are hyphenated and pluralized under /api/v1. Bearer tokens authenticate requests and scopes enforce least-privilege access. Tenants are isolated by default, and clients must not supply tenant_id in request bodies; if present, it must match the caller’s tenant or the request fails.

Creation endpoints support idempotency via Idempotency-Key headers and deduplicate within a configured window. List endpoints use cursor-based pagination with page_token and next_page_token and allow server-side throttling to protect performance. Errors follow a canonical envelope with error_code, error_message, and error_class. Correlation and trace IDs are returned in response headers to aid diagnostics and observability.

Rate limiting applies per tenant. Clients must implement backoff on 429 and honor Retry-After when present. Processing deadlines can be specified at schedule creation to bound system processing or publishing preparation time.

To anchor these conventions in implementation, Table 1 enumerates error types and HTTP status mapping; Table 2 defines rate limit and backoff parameters. These tables set explicit expectations for clients to handle transient and terminal errors consistently, while allowing the service to protect itself under load.

### Table 1: Error Types and HTTP Status Mapping

| Error Type                | HTTP Status | Description                                                                 |
|--------------------------|-------------|-----------------------------------------------------------------------------|
| invalid_request          | 400         | Malformed request body or query parameters                                  |
| validation_error         | 422         | Semantics failed validation (e.g., missing required fields)                 |
| unauthorized             | 401         | Missing or invalid authentication                                           |
| forbidden                | 403         | Authenticated but lacking required scope or permissions                     |
| not_found                | 404         | Resource not found or not visible to the caller                             |
| conflict                 | 409         | State conflict (e.g., transition not allowed)                               |
| rate_limited             | 429         | Request rejected due to rate limits                                         |
| idempotency_conflict     | 409         | Provided idempotency_key conflicts with a different resource                |
| quota_exceeded           | 429         | Per-tenant quota exceeded                                                   |
| internal_error           | 500         | Unexpected server error                                                     |
| service_unavailable      | 503         | Service unable to handle the request due to temporary outage                |
| gateway_timeout          | 504         | Upstream processing exceeded configured timeouts                            |

### Table 2: Rate Limit and Backoff Parameters

| Parameter                  | Value / Guidance                          | Description                                                                |
|---------------------------|-------------------------------------------|----------------------------------------------------------------------------|
| Per-tenant RPS            | Configurable (e.g., 10 RPS)               | Requests per second allowed per tenant                                     |
| Burst Capacity            | 2x per-minute                             | Short-term capacity to accommodate spikes                                 |
| Retry-After               | Returned on 429                           | Duration to wait before retrying                                           |
| WebSocket Reconnect Backoff | Exponential (e.g., 1s, 2s, 4s, max 30s) | Progressive backoff to prevent thundering herds                            |
| Idempotency Window        | 24 hours                                  | Duration within which idempotency keys are honored                         |
| Page Size Limits          | Min 10, Max 200                           | Enforced fairness and response size management                             |

## Domain Model and State Machine

The domain model centers on schedules and schedule items. A schedule represents a planned set of posts over time—often tied to a campaign or content collection—where the lifecycle and constraints are explicit and observable. Schedule items are atomic entries in a schedule representing a single post at a specific time, with optional platform targeting and configuration. This separation allows clients to reason at both the plan level (schedule) and the execution level (item).

Schedule lifecycle mirrors the existing job machine in spirit: pending, running, optimizing, completing, canceling, canceled, and failed. Pending indicates acceptance but no active processing; running indicates work is underway; optimizing indicates that content timing adjustments are in progress; completing indicates that finalization steps are occurring; canceling and canceled handle stop flows; failed indicates a terminal unrecoverable error. Item-level states typically include pending, scheduled, published, skipped, failed, and canceled, with transitions that reflect concrete publishing outcomes or preemptive policy decisions.

Progress semantics include aggregate fields (percent_complete, items_total, items_completed, items_failed, items_skipped, items_canceled, items_pending) and estimated time remaining (eta_ms). When schedules include processing deadlines, these bind the allowed processing time, after which the system may cancel remaining items if necessary. These semantics align with the architecture’s progress definitions to facilitate consistent monitoring.

### Table 3: Schedule States

| State        | Description                                                | Permitted Transitions                                 | State-Specific Semantics                                        |
|--------------|------------------------------------------------------------|--------------------------------------------------------|------------------------------------------------------------------|
| pending      | Accepted but not yet running; queued                       | running, canceling, failed                             | Times uninitialized; may be canceled preemptively                |
| running      | Actively being processed                                   | optimizing, completing, canceling, failed              | Items being scheduled or prepared                                |
| optimizing   | Timing optimization in progress                            | running, completing, canceling, failed                 | May emit progress events with optimization metrics               |
| completing   | Finalizing prepared items and artifacts                    | completed, failed                                      | No new items; final outputs prepared                             |
| completed    | Terminal state indicating successful finish                | None                                                   | Final metrics set; items should be scheduled or published        |
| canceling    | Stop requests in progress                                  | canceled, failed                                       | In-flight items may be canceled or retained per policy           |
| canceled     | Terminal state after stop                                  | None                                                   | Partial schedules may persist per retention policy               |
| failed       | Terminal state indicating unrecoverable error              | None                                                   | error_code and error_message summarize root cause                |

### Table 4: Schedule Item States

| State       | Description                                 | Permitted Transitions                                   | State-Specific Semantics                                         |
|-------------|---------------------------------------------|---------------------------------------------------------|-------------------------------------------------------------------|
| pending     | Accepted but not yet assigned a time        | scheduled, skipped, failed, canceled                    | Awaiting assignment or validation                                 |
| scheduled   | Assigned a concrete time                    | published, skipped, failed, canceled                    | Ready for publication preparation                                 |
| published   | Successfully published                      | None                                                     | Final state; artifact references may be attached                   |
| failed      | Unrecoverable error                         | None                                                     | error_code, error_message, error_class capture diagnostics         |
| skipped     | Skipped intentionally per policy            | None                                                     | reason clarifies policy or conflicts                              |
| canceled    | Stopped due to schedule cancelation         | None                                                     | Partial results may be unavailable                                |

### Table 5: Progress Semantics (Schedule-Level)

| Field                           | Unit    | Description                                                                                 | Example Values    |
|---------------------------------|---------|---------------------------------------------------------------------------------------------|-------------------|
| percent_complete                | 0–100   | Ratio of published + skipped items to total items                                           | 42.3              |
| items_total                     | count   | Total number of items in the schedule                                                       | 10,000            |
| items_completed                 | count   | Items scheduled or published                                                                | 4,200             |
| items_failed                    | count   | Failed items count                                                                          | 45                |
| items_skipped                   | count   | Skipped items count                                                                         | 80                |
| items_canceled                  | count   | Canceled items count                                                                        | 10                |
| items_pending                   | count   | Items not yet completed (including pending and scheduled)                                   | 5,665             |
| time_to_start_ms                | ms      | Elapsed time until first item was scheduled                                                 | 2,500             |
| time_processing_ms              | ms      | Cumulative preparation time across completed items                                          | 1,250,000         |
| average_duration_ms_per_item    | ms      | Mean preparation time per completed item                                                    | 300               |
| eta_ms                          | ms      | Estimated time remaining based on throughput                                                | 4,200,000         |
| rate_limited                    | boolean | True if rate limits are constraining throughput                                             | false             |
| processing_deadline_ms          | ms      | Maximum time allowed for processing before cancellation                                     | 1,800,000         |

Aggregate percent is computed as (items_completed + items_skipped) / items_total. ETA derives from average duration per item and remaining counts.

## Endpoint Specifications

The following endpoint designs conform to established conventions, include precise request/response schemas, and enumerate status codes and error handling. All endpoints are prefixed with /api/v1 and enforce tenant isolation and scope checks.

### GET /api/v1/scheduling/recommendations

Fetch recommended posting times derived from historical engagement, content metadata, and constraints such as business hours or blackout windows. The endpoint accepts query parameters for tenant scoping, platform filters, and target counts, and returns ranked windows with explanations.

#### Request

Headers:
- Authorization: Bearer {token}

Query parameters:
- tenant_id (server-derived, do not accept client-provided values)
- platforms (repeated string, optional): filter by platform identifiers
- target_count (integer, optional, default 10, max 200): number of windows requested
- start_at (RFC3339 timestamp, optional): window start for recommendations
- end_at (RFC3339 timestamp, optional): window end for recommendations
- timezone (string, optional): IANA timezone for recommendation outputs
- content_type (string, optional): classification to bias engagement models
- page_token (string, optional): cursor for pagination
- page_size (integer, optional, default 50, max 200): number of windows per page
- sort (string, optional): created_at or score (default score)
- order (string, optional): asc or desc (default desc)

#### Response

Status: 200 OK

Body:
```json
{
  "data": [
    {
      "id": "rec_01HABC1234567890",
      "window_start": "2025-11-05T18:00:00Z",
      "window_end": "2025-11-05T19:30:00Z",
      "score": 0.823,
      "reasons": ["audience_active_peak", "historical_engagement_high"],
      "platforms": ["platform_a", "platform_b"],
      "confidence": 0.77,
      "content_types": ["announcement", "howto"]
    },
    {
      "id": "rec_01HABC1234567891",
      "window_start": "2025-11-06T12:00:00Z",
      "window_end": "2025-11-06T13:00:00Z",
      "score": 0.791,
      "reasons": ["regional_peak_eu"],
      "platforms": ["platform_c"],
      "confidence": 0.72,
      "content_types": ["event"]
    }
  ],
  "page": {
    "next_page_token": "eyJvZmZzZXQiOjUwLCJzdGFydF9hZnRlciI6InJlY18wMUhBQkMxMjM0NTY3ODkwIn0=",
    "page_size": 50
  }
}
```

Error handling:
- 400 invalid_request for malformed query parameters.
- 401 unauthorized, 403 forbidden for missing or insufficient scopes.
- 422 validation_error for out-of-range pagination or conflicting date windows.
- 429 rate_limited when rate limits are exceeded.
- 500 internal_error for unexpected failures.

#### Notes on Scoring

Scores quantify predicted posting effectiveness for the requested tenant and platforms. Explanations (“audience_active_peak”, “historical_engagement_high”, “regional_peak_eu”) communicate the rationale. Confidence indicates model certainty in the recommendation, ranging from 0 to 1. Content types allow clients to bias recommendations toward engagement behaviors typical for that class (e.g., announcements vs. tutorials).

---

### POST /api/v1/scheduling/calendar

Create a new schedule (calendar) that reserves specific posting times for content items. Supports idempotency via Idempotency-Key and returns the schedule’s initial state and progress metadata.

#### Request

Headers:
- Authorization: Bearer {token}
- Content-Type: application/json
- Idempotency-Key: {uuid} (optional)

Body:
```json
{
  "title": "Launch Week Cadence",
  "timezone": "America/New_York",
  "items": [
    {
      "content_id": "content_01HXYZ1234",
      "platform": "platform_a",
      "scheduled_time": "2025-11-06T14:00:00-05:00",
      "metadata": {
        "campaign_id": "camp_01H1234",
        "format": "video"
      },
      "callbacks": {
        "on_published": "https://client.example.com/webhooks/published"
      }
    },
    {
      "content_id": "content_01HXYZ5678",
      "platform": "platform_b",
      "scheduled_time": "2025-11-06T16:30:00-05:00",
      "metadata": {
        "campaign_id": "camp_01H1234",
        "format": "image"
      }
    }
  ],
  "processing_deadline_ms": 7200000
}
```

Validation rules:
- scheduled_time must be RFC3339 with timezone; conflicts within a platform window are resolved per conflict policy.
- metadata is optional and passed through to callbacks when available.
- processing_deadline_ms bounds preparation time.
- Items exceeding processing_deadline_ms may be canceled or moved per policy.

#### Response

Status: 201 Created

Body:
```json
{
  "id": "sched_01HDEF9876543210",
  "tenant_id": "tenant_7x9y",
  "state": "pending",
  "title": "Launch Week Cadence",
  "timezone": "America/New_York",
  "percent_complete": 0.0,
  "items_total": 2,
  "items_completed": 0,
  "items_failed": 0,
  "items_skipped": 0,
  "items_canceled": 0,
  "items_pending": 2,
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

Error handling:
- 400 invalid_request for malformed bodies.
- 401 unauthorized, 403 forbidden for missing or insufficient scopes.
- 409 conflict for idempotency conflicts or disallowed state transitions.
- 422 validation_error for invalid scheduled_time or unsupported metadata.
- 429 rate_limited or quota_exceeded when limits are exceeded.
- 503 service_unavailable when temporarily unavailable.

#### Idempotency Semantics

When Idempotency-Key is supplied, duplicate creation requests within the window return the original schedule with its current state. Keys are scoped per tenant to prevent cross-tenant collisions.

#### Scopes and Tenancy

Creation requires scope schedules:write. Tenants are strictly isolated; the service ignores client-supplied tenant_id and derives it from claims.

---

### GET /api/v1/scheduling/calendar/{id}

Fetch schedule details, including metadata, aggregates, and item-level listings with pagination, filtering, sorting, and optional expansions. The response returns a consistent snapshot across items and aggregates to facilitate UI rendering and dashboards.

#### Request

Headers:
- Authorization: Bearer {token}

Path parameter:
- id: schedule identifier

Query parameters:
- page_token (string, optional): cursor for pagination
- page_size (integer, optional, default 50, max 200)
- state (string, repeated): filter items by item state (e.g., scheduled, published, failed)
- sort (string, optional): created_at or updated_at
- order (string, optional): asc or desc (default asc)
- expand (string, repeated): optional expansions (items, conflicts, callbacks)

#### Response

Status: 200 OK

Body:
```json
{
  "id": "sched_01HDEF9876543210",
  "tenant_id": "tenant_7x9y",
  "state": "running",
  "title": "Launch Week Cadence",
  "timezone": "America/New_York",
  "percent_complete": 30.0,
  "items_total": 2,
  "items_completed": 1,
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
      "platform": "platform_a",
      "state": "published",
      "scheduled_time": "2025-11-06T14:00:00-05:00",
      "published_time": "2025-11-06T14:00:05-05:00",
      "metadata": {
        "campaign_id": "camp_01H1234",
        "format": "video"
      },
      "callbacks": {
        "on_published": "https://client.example.com/webhooks/published"
      },
      "errors": [],
      "artifacts": [
        {
          "type": "post_metadata",
          "content_type": "application/json",
          "size": 1024,
          "url": "https://storage.example.com/tenant_7x9y/schedules/sched_01HDEF9876543210/items/item_01HABCDEFAAA1111/metadata.json"
        }
      ],
      "created_at": "2025-11-05T02:05:20Z",
      "updated_at": "2025-11-06T14:00:10Z"
    },
    {
      "id": "item_01HABCDEFAAA2222",
      "content_id": "content_01HXYZ5678",
      "platform": "platform_b",
      "state": "scheduled",
      "scheduled_time": "2025-11-06T16:30:00-05:00",
      "metadata": {
        "campaign_id": "camp_01H1234",
        "format": "image"
      },
      "errors": [],
      "created_at": "2025-11-05T02:05:25Z",
      "updated_at": "2025-11-05T02:06:30Z"
    }
  ],
  "page": {
    "next_page_token": null,
    "page_size": 50
  }
}
```

Error handling:
- 401 unauthorized, 403 forbidden for access violations.
- 404 not_found if the schedule ID is not found or belongs to a different tenant.
- 409 conflict if a state transition is requested via query (not allowed here).
- 500 internal_error for unexpected failures.

#### Expansion Options

Items, conflicts, and callbacks expansions provide additional metadata for operational review. Conflicts return collision details (e.g., overlapping windows within the same platform) to inform resolution workflows. Callbacks expose registered URLs and delivery status where available.

---

### POST /api/v1/scheduling/optimize

Optimize timing for existing content assigned to a schedule or catalog. The endpoint accepts targets and constraints, computes new times using the recommendation engine, and returns a result set describing applied changes and rationale.

#### Request

Headers:
- Authorization: Bearer {token}
- Content-Type: application/json
- Idempotency-Key: {uuid} (optional)

Body:
```json
{
  "schedule_id": "sched_01HDEF9876543210",
  "targets": [
    {
      "content_id": "content_01HXYZ5678",
      "platform": "platform_b",
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
      "platform_b": {
        "min_interval_minutes": 90
      }
    }
  },
  "apply": true
}
```

Validation rules:
- Targets must reference existing content and platforms.
- Constraints must form valid intervals; blackout windows must not overlap scheduled publication policies.
- Idempotency applies when apply is true; repeated requests within the idempotency window return the original optimization result.

#### Response

Status: 200 OK

Body:
```json
{
  "id": "opt_01HJKL5555555555",
  "tenant_id": "tenant_7x9y",
  "schedule_id": "sched_01HDEF9876543210",
  "state": "completed",
  "changes": [
    {
      "content_id": "content_01HXYZ5678",
      "platform": "platform_b",
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

Error handling:
- 400 invalid_request for malformed bodies.
- 401 unauthorized, 403 forbidden for missing or insufficient scopes.
- 404 not_found if schedule_id or targets are not found or not visible.
- 409 conflict for idempotency conflicts or disallowed transitions.
- 422 validation_error for invalid constraints or targets.
- 429 rate_limited when rate limits are exceeded.
- 500 internal_error for unexpected failures.

#### Notes on Constraints

Constraints protect operational boundaries and ensure compliance with platform-specific rules. “Do not move before/after” define allowable windows; blackout windows prevent publishing during maintenance or policy-sensitive periods. Platform rules (e.g., minimum interval minutes between posts) enforce cadence. If constraints make optimization impossible for a target, the system returns unchanged with reason “constraints_forbid_move”.

---

## WebSocket Protocol for Real-Time Schedule Updates

The WebSocket channel streams real-time updates for schedules and items, enabling dashboards and automation to react promptly to state changes and progress. Clients connect to the WebSocket endpoint, passing an authentication token and identifiers (schedule_id or campaign scope). The service validates tenant access and emits only events within the authenticated tenant’s scope.

Authentication is via Bearer token; connections are single-tenant and isolated. Messages adopt the envelope { type, ts, correlation_id, data }. Event types cover schedule lifecycle transitions, item-level updates, and progress metrics. Clients reconnect with backoff and supply last_event_timestamp to request missed events for catch-up.

### Table 6: WebSocket Event Types

| Type                 | Trigger Condition                                  | Data Fields Included                                                    | Client Handling Guidance                                              |
|----------------------|-----------------------------------------------------|-------------------------------------------------------------------------|------------------------------------------------------------------------|
| schedule.state_changed | Schedule enters a new state                        | prior_state, new_state, reason                                          | Update UI state; gate actions based on new_state                      |
| schedule.progress    | Periodic or on threshold change                     | percent_complete, items_*, time_processing_ms, eta_ms                   | Update progress bars and throughput metrics                           |
| item.created         | New schedule item recognized                        | id, schedule_id, content_id, platform, state                            | Add to list; enable item-level tracking                               |
| item.updated         | Item progress or metadata changes                   | id, schedule_id, state, scheduled_time, updated_at                      | Refresh details; handle transient states                              |
| item.published       | Item published successfully                         | id, artifacts (type, content_type, size, url), published_time           | Enable retrieval or downstream processing                             |
| item.failed          | Item failed                                         | id, errors (error_code, error_message, error_class)                     | Show error; prompt retry if policy permits                            |
| optimization.completed | Optimization run completed                          | opt_id, schedule_id, changes (target, new_time, score_before/after)     | Update scheduling views; show deltas and rationale                    |
| schedule.canceled    | Schedule reached canceled state                     | summary fields, partial artifacts info                                  | Clean up; mark canceled items as unavailable                          |
| schedule.failed      | Schedule reached failed state                       | error_code, error_message, error_class                                  | Show failure; log correlation_id; consider alerting                   |

### Table 7: State Transition Event Matrix (Schedule-Level)

| From State | To State   | WebSocket Events Emitted                             | Notes                                                                              |
|------------|------------|-------------------------------------------------------|------------------------------------------------------------------------------------|
| pending    | running    | schedule.state_changed, schedule.progress            | Start heartbeats; time_to_start_ms set                                            |
| running    | optimizing | schedule.state_changed                               | Optimization in progress                                                           |
| optimizing | running    | schedule.state_changed                               | Resumed standard processing                                                        |
| running    | completing | schedule.state_changed                               | No new items; finalize outputs                                                     |
| completing | completed  | schedule.state_changed, schedule.completed           | Terminal state; emit artifacts                                                     |
| running    | canceling  | schedule.state_changed                               | Terminate in-flight items; partial retention policy applies                        |
| canceling  | canceled   | schedule.state_changed, schedule.canceled            | Terminal state; no further events                                                  |
| any        | failed     | schedule.state_changed, schedule.failed              | Terminal; error payload includes diagnostics                                       |

#### Sample WebSocket Frames

State change event:
```json
{
  "type": "schedule.state_changed",
  "ts": "2025-11-05T02:06:05Z",
  "correlation_id": "c8d3-2f11",
  "data": {
    "prior_state": "pending",
    "new_state": "running",
    "reason": "resources_available"
  }
}
```

Progress update:
```json
{
  "type": "schedule.progress",
  "ts": "2025-11-05T02:06:10Z",
  "correlation_id": "c8d3-2f11",
  "data": {
    "percent_complete": 15.3,
    "items_total": 1000,
    "items_completed": 153,
    "items_failed": 1,
    "items_skipped": 2,
    "items_canceled": 0,
    "items_pending": 844,
    "time_to_start_ms": 1500,
    "time_processing_ms": 42000,
    "average_duration_ms_per_item": 275,
    "eta_ms": 2327500,
    "rate_limited": false
  }
}
```

Item published event:
```json
{
  "type": "item.published",
  "ts": "2025-11-06T14:00:10Z",
  "correlation_id": "c8d3-2f11",
  "data": {
    "id": "item_01HABCDEFAAA1111",
    "schedule_id": "sched_01HDEF9876543210",
    "state": "published",
    "published_time": "2025-11-06T14:00:05-05:00",
    "artifacts": [
      {
        "type": "post_metadata",
        "content_type": "application/json",
        "size": 1024,
        "url": "https://storage.example.com/tenant_7x9y/schedules/sched_01HDEF9876543210/items/item_01HABCDEFAAA1111/metadata.json"
      }
    ]
  }
}
```

Optimization completed event:
```json
{
  "type": "optimization.completed",
  "ts": "2025-11-05T02:10:15Z",
  "correlation_id": "c8d3-2f11",
  "data": {
    "opt_id": "opt_01HJKL5555555555",
    "schedule_id": "sched_01HDEF9876543210",
    "summary": {
      "total_targeted": 1,
      "changed_count": 1,
      "unchanged_count": 0,
      "average_score_lift": 0.17,
      "rate_limited": false
    },
    "changes": [
      {
        "content_id": "content_01HXYZ5678",
        "platform": "platform_b",
        "previous_time": "2025-11-06T16:30:00-05:00",
        "new_time": "2025-11-06T17:15:00-05:00",
        "score_before": 0.65,
        "score_after": 0.82,
        "reason": "audience_active_peak",
        "confidence": 0.74
      }
    ]
  }
}
```

#### Resilience and Reconnect

Clients must implement exponential backoff on reconnect to avoid thundering herd effects. Supply last_event_timestamp in the connection query parameters to request missed events; the server responds with a catch-up payload containing events since the timestamp, allowing clients to maintain consistency in UI and downstream systems.

## Operational Concerns

The scheduling API adopts operational safeguards consistent with the architecture. Concurrency controls ensure consistent state transitions and protect against race conditions. Idempotency covers creation and optimization to guard against duplicate requests. Timeouts and processing_deadline_ms ensure the system bounds work and cancels when limits are exceeded. Logging correlation and trace IDs enables cross-component tracing, while rate_limited flags signal when the client should back off.

Under sustained load, the service may adjust page sizes and return 429 or 503 to preserve reliability. Clients should treat 429 as a signal to throttle and respect Retry-After headers. WebSocket resilience depends on reconnection and event replay semantics as described.

## Security and Compliance

Transport security uses TLS for all endpoints and the WebSocket channel. Tokens should be short-lived with least-privilege scopes. Tenants are strictly isolated and must not supply tenant_id in requests; the service rejects mismatches. Scopes govern access: schedules:read for queries, schedules:write for creation and control, optimization:write for timing optimization.

Callbacks and webhook endpoints must be protected and avoid unnecessary exposure of personal data. If personal data appears in content metadata or schedule items, clients and services should handle it according to applicable policies.

## Extensibility, Versioning, and Migration

Versioning is accomplished through /api/v1. Future enhancements are introduced via /api/v2 without breaking the v1 contract. Additive fields, new event types, and optional expansions are the preferred evolution path. Deprecations are communicated via response headers indicating status and sunset dates, with documentation updates and migration guidance.

#### Table 8: Version Compatibility Matrix

| Feature/Field                        | v1 Support | v2 Plan | Migration Notes                                                               |
|-------------------------------------|------------|---------|-------------------------------------------------------------------------------|
| Schedule core fields                | Yes        | Yes     | Core fields preserved; additive changes only                                  |
| Item states and transitions         | Yes        | Yes     | New states added while preserving existing semantics                          |
| WebSocket events                    | Yes        | Yes     | New event types added; existing semantics unchanged                           |
| recommendation scoring fields       | Yes        | Yes     | Additional metrics may be added as optional fields                            |
| processing_deadline_ms              | Yes        | Yes     | Retained; behavior may be refined                                             |
| ETags for list responses            | Yes        | Yes     | ETag semantics stable; conditional requests supported                         |

## Example Scenarios

### End-to-End Flow: Recommendations → Create Schedule → Track Progress → Optimize

1. Fetch recommendations:
   - GET /api/v1/scheduling/recommendations with target_count and platform filters.
   - Receive ranked windows with scores and explanations.

2. Create schedule:
   - POST /api/v1/scheduling/calendar with items referencing content_id, platform, scheduled_time, and optional callbacks.
   - Accept 201 Created with schedule id and state pending.

3. Monitor progress:
   - Open a WebSocket connection with schedule_id and token.
   - Receive schedule.state_changed and schedule.progress events; update the UI.

4. Optimize timing:
   - POST /api/v1/scheduling/optimize with targets and constraints; set apply to true to commit changes.
   - Receive optimization.completed via WebSocket; update item times and rationale.

5. Completion:
   - When the schedule reaches completed, retrieve final artifacts and persist schedule outputs.

### Reconnect and Catch-Up Flow

- On disconnect, reconnect with last_event_timestamp in query parameters.
- The server sends missed events since the timestamp; clients merge updates to maintain consistent state.

### Table 9: Scenario Timeline

| Step | Action                      | Request/Event                                   | Response/Event                                         | Outcome                                           |
|------|------------------------------|-------------------------------------------------|--------------------------------------------------------|---------------------------------------------------|
| 1    | Fetch recommendations        | GET /api/v1/scheduling/recommendations          | 200 OK with ranked windows                             | Client selects preferred windows                  |
| 2    | Create schedule              | POST /api/v1/scheduling/calendar                | 201 Created with schedule id and state pending         | Schedule queued                                   |
| 3    | Start processing             | (system)                                        | schedule.state_changed: pending → running              | Processing begins                                 |
| 4    | Track progress               | WebSocket                                       | schedule.progress (periodic), item.* events            | Live dashboard updates                            |
| 5    | Optimize timing              | POST /api/v1/scheduling/optimize                | 200 OK with changes; optimization.completed via WebSocket | New times committed; metrics updated             |
| 6    | Complete schedule            | (system)                                        | schedule.state_changed: running → completing → completed | Terminal state with summary and artifacts       |

## Appendix: Schemas, Status Codes, and Glossary

### JSON Schemas

Recommendation:
```json
{
  "type": "object",
  "required": ["id", "window_start", "window_end", "score", "reasons"],
  "properties": {
    "id": { "type": "string" },
    "window_start": { "type": "string", "format": "date-time" },
    "window_end": { "type": "string", "format": "date-time" },
    "score": { "type": "number", "minimum": 0, "maximum": 1 },
    "reasons": {
      "type": "array",
      "items": { "type": "string" }
    },
    "platforms": {
      "type": "array",
      "items": { "type": "string" }
    },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "content_types": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

ScheduleCreateRequest:
```json
{
  "type": "object",
  "required": ["title", "items"],
  "properties": {
    "title": { "type": "string", "maxLength": 200 },
    "timezone": { "type": "string" },
    "items": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["content_id", "platform", "scheduled_time"],
        "properties": {
          "content_id": { "type": "string" },
          "platform": { "type": "string" },
          "scheduled_time": { "type": "string", "format": "date-time" },
          "metadata": { "type": "object", "additionalProperties": true },
          "callbacks": {
            "type": "object",
            "properties": {
              "on_published": { "type": "string", "format": "uri" }
            }
          }
        }
      }
    },
    "processing_deadline_ms": { "type": "integer", "minimum": 0 },
    "idempotency_key": { "type": "string", "format": "uuid" }
  }
}
```

Schedule:
```json
{
  "type": "object",
  "required": ["id", "tenant_id", "state", "title", "timezone", "items_total"],
  "properties": {
    "id": { "type": "string" },
    "tenant_id": { "type": "string" },
    "state": { "type": "string", "enum": ["pending", "running", "optimizing", "completing", "completed", "canceling", "canceled", "failed"] },
    "title": { "type": "string" },
    "timezone": { "type": "string" },
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
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "idempotency_key": { "type": ["string", "null"] },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "content_id", "platform", "state", "scheduled_time"],
        "properties": {
          "id": { "type": "string" },
          "content_id": { "type": "string" },
          "platform": { "type": "string" },
          "state": { "type": "string", "enum": ["pending", "scheduled", "published", "failed", "skipped", "canceled"] },
          "scheduled_time": { "type": "string", "format": "date-time" },
          "published_time": { "type": ["string", "null"], "format": "date-time" },
          "metadata": { "type": "object", "additionalProperties": true },
          "callbacks": {
            "type": "object",
            "properties": {
              "on_published": { "type": "string", "format": "uri" }
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
          "artifacts": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["type", "content_type", "size", "url"],
              "properties": {
                "type": { "type": "string", "enum": ["post_metadata", "report", "thumbnail"] },
                "content_type": { "type": "string" },
                "size": { "type": "integer", "minimum": 0 },
                "url": { "type": "string", "format": "uri" }
              }
            }
          },
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "page": {
      "type": "object",
      "properties": {
        "next_page_token": { "type": ["string", "null"] },
        "page_size": { "type": "integer", "minimum": 10, "maximum": 200 }
      }
    }
  }
}
```

OptimizationRequest:
```json
{
  "type": "object",
  "required": ["schedule_id", "targets"],
  "properties": {
    "schedule_id": { "type": "string" },
    "targets": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["content_id", "platform", "current_scheduled_time"],
        "properties": {
          "content_id": { "type": "string" },
          "platform": { "type": "string" },
          "current_scheduled_time": { "type": "string", "format": "date-time" }
        }
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "do_not_move_before": { "type": "string", "format": "date-time" },
        "do_not_move_after": { "type": "string", "format": "date-time" },
        "blackout_windows": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["start", "end"],
            "properties": {
              "start": { "type": "string", "format": "date-time" },
              "end": { "type": "string", "format": "date-time" }
            }
          }
        },
        "platform_specific_rules": {
          "type": "object",
          "additionalProperties": true
        }
      }
    },
    "apply": { "type": "boolean", "default": false },
    "idempotency_key": { "type": "string", "format": "uuid" }
  }
}
```

OptimizationResult:
```json
{
  "type": "object",
  "required": ["id", "tenant_id", "schedule_id", "state", "changes", "metrics"],
  "properties": {
    "id": { "type": "string" },
    "tenant_id": { "type": "string" },
    "schedule_id": { "type": "string" },
    "state": { "type": "string", "enum": ["pending", "running", "completed", "failed"] },
    "changes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["content_id", "platform", "previous_time", "new_time", "reason"],
        "properties": {
          "content_id": { "type": "string" },
          "platform": { "type": "string" },
          "previous_time": { "type": "string", "format": "date-time" },
          "new_time": { "type": "string", "format": "date-time" },
          "score_before": { "type": "number", "minimum": 0, "maximum": 1 },
          "score_after": { "type": "number", "minimum": 0, "maximum": 1 },
          "reason": { "type": "string" },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
        }
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "total_targeted": { "type": "integer", "minimum": 0 },
        "changed_count": { "type": "integer", "minimum": 0 },
        "unchanged_count": { "type": "integer", "minimum": 0 },
        "average_score_lift": { "type": "number" },
        "rate_limited": { "type": "boolean" }
      }
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" }
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

### Table 10: HTTP Status Codes Usage

| Status Code       | Scenario                                                 | Retry Guidance                                                   |
|-------------------|-----------------------------------------------------------|------------------------------------------------------------------|
| 200 OK            | Successful GET/POST with response body                    | None                                                             |
| 201 Created       | Successful schedule creation                              | None                                                             |
| 400 Bad Request   | Malformed request                                         | Fix request                                                      |
| 401 Unauthorized  | Missing/invalid token                                     | Obtain valid token                                               |
| 403 Forbidden     | Insufficient scope                                        | Request appropriate scopes                                       |
| 404 Not Found     | Resource missing or not visible                           | Confirm identifier and tenant                                    |
| 409 Conflict      | State conflict or idempotency conflict                    | Do not retry blindly; review state and idempotency               |
| 422 Unprocessable Entity | Validation failure                                 | Correct input                                                    |
| 429 Too Many Requests | Rate limit or quota exceeded                         | Backoff and retry after Retry-After                              |
| 500 Internal Server Error | Unexpected server error                         | Retry with backoff                                               |
| 503 Service Unavailable | Temporary outage                                  | Retry with exponential backoff                                   |
| 504 Gateway Timeout | Upstream timeout                                         | Retry with backoff; consider adjusting deadlines                 |

### Table 11: Glossary of Terms

| Term                       | Definition                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| Schedule                   | Planned set of posts over time, including metadata and constraints          |
| Schedule Item              | Atomic entry in a schedule representing a single post at a specific time    |
| Recommendation             | Ranked posting windows with score, confidence, and explanations             |
| Optimization               | Process of shifting item times to maximize predicted engagement             |
| State Machine              | Explicit set of states and transitions governing lifecycle                  |
| Progress                   | Aggregated metrics indicating completion and throughput                      |
| Artifact                   | Output metadata or file produced by schedule or item                         |
| Tenant                     | Isolated organizational context for multi-tenant security                    |
| Idempotency                | Property ensuring duplicate requests produce the same effect within a window |
| Cursor-Based Pagination    | List navigation using tokens rather than offsets                             |
| ETag                       | Entity tag for cache validation of list responses                            |
| Correlation ID             | Identifier for tracing requests and events across components                 |
| Rate Limiting              | Enforcing per-tenant request rate and quota constraints                      |
| Processing Deadline        | Maximum time allowed for processing before cancellation                       |
| Callback URL               | Client-provided endpoint for receiving lifecycle notifications               |
| WebSocket                  | Full-duplex protocol for real-time updates                                   |

## Information Gaps and Assumptions

The API contract is stable, but several operational parameters require configuration or future specification:

- Authentication scheme specifics (token lifetimes, claims) are not defined and will be finalized during implementation.
- Per-tenant rate limits, quota policies, and burst thresholds require configuration.
- Detailed fields for recommendation scoring inputs and algorithms will be layered in without breaking the contract.
- Artifact storage locations and access URL format (signed vs. public) are intentionally unspecified.
- Idempotency window and conflict handling specifics need to be established.
- Processing deadline units and enforcement policy require confirmation (advisory vs. strict).
- WebSocket authentication and reconnection semantics (handshake details and missed event payload format) need finalization.
- Pagination defaults and maximums need confirmation; current values are examples.
- Error code taxonomy beyond the common set will be extended as needed.
- ETags and cache semantics for list endpoints are mentioned but require implementation specifics.
- Callbacks/webhooks payload format and signature verification will be detailed later.
- Concurrency controls for schedule pausing/resuming and item-level cancelation are assumed.
- Retention policies for canceled/failed schedules and partial outputs need definition.

These gaps do not alter the core API contract; they represent operational refinements that can evolve independently without breaking client integrations.

## Conclusion

This blueprint defines a coherent, robust API and WebSocket protocol for scheduling optimization. It uses the architecture’s proven conventions to minimize integration complexity and maximize reliability. With clear state machines, consistent error semantics, and real-time observability, product teams can build resilient workflows that recommend optimal posting times, create and manage schedules, and continuously refine timing for existing content. The design is intentionally extensible, allowing richer algorithms and operational policies to be layered in without compromising the v1 contract.