# Queue System Architecture for Bulk Request Management, Prioritization, Rate Limiting, Retries with Backoff, Progress Tracking, and Supabase Edge Functions Integration

## Executive Summary and Objectives

This blueprint defines a production-grade queue system designed to process bulk requests at scale while honoring strict external rate limits and providing end-to-end observability. The system is optimized for downstream APIs with per-minute quotas—most notably the Google Sheets API—and integrates natively with Supabase Postgres for durable state, Supabase Edge Functions for secure processing and orchestration, and Supabase Realtime for push-based progress updates.

The core objectives are fourfold. First, deliver robust job prioritization—urgent, normal, low—so that time-sensitive work is reliably expedited without starving lower-tier workloads. Second, implement multi-dimensional rate limiting across project and user scopes to prevent quota breaches, minimize 429 errors, and shape traffic within minute-gated constraints. Third, ensure resilience through a retry mechanism with truncated exponential backoff and jitter, bounded by idempotency protections and a dead-letter pathway for terminal failures. Fourth, provide clear progress tracking and status transparency via a well-defined job state model, evented updates, and Realtime publication.

The design leverages Postgres as the durable queue backend using transactional polling with SKIP LOCKED to safely distribute work among concurrent workers. Edge Functions are introduced for secure operations, controlled API invocations, and key management, with Row Level Security (RLS) policies tuned to allow both the anonymous caller and the service role where appropriate. The system’s operating model is grounded in minute-refill quotas, backoff-and-jitter on 429 responses, batch operations (e.g., batchUpdate) for efficiency, and monitoring practices that surface near-breach conditions before they become incidents[^1][^3][^5][^6].

We explicitly acknowledge information gaps that must be closed during implementation: exact per-minute quotas for the target project; the specific AI provider’s rate limit policy and burst tolerance; payload composition and maximum subrequests per batch; operational SLOs for latency and throughput; Supabase Realtime cardinality limits; idempotency and de-duplication strategies for third-party AI calls; multi-tenant isolation requirements; and any compliance needs for PII or audit obligations. These gaps do not block design progress, but they require validation and parameter tuning prior to go-live.

## Context and Constraints from Source Materials

External APIs such as Google Sheets enforce per-minute quotas that refill every minute, which means throughput planning must be shaped to a minute-gated model rather than daily budgets. In practice, exceeding these budgets results in HTTP 429 (Too Many Requests), and safe recovery requires truncated exponential backoff with jitter on the failing call. The recommended posture is to design for steady throughput within quotas, keep payloads small—around the 2 MB guidance—and prefer batch operations like values.batchGet and batchUpdate to compress multiple subrequests into a single call, counting as one request against per-minute limits[^1][^2][^5][^3].

At a design level, we must account for three implications. First, per-project and per-user quotas both apply concurrently; the system should enforce the tighter constraint dynamically and respect user-level fairness to prevent a single actor from saturating shared budgets[^1][^3]. Second, batchUpdate is atomic—if any subrequest is invalid, no changes are applied—so we must validate subrequests and segment batches to minimize collateral failures. Third, minute-refill behavior favors backoff on 429 at the individual request level rather than global “sleep” heuristics, which often underperform against rolling windows[^1][^5].

The following table summarizes representative planning numbers and operating guidance derived from integration references. These are indicative and must be validated in the project’s own quotas dashboard.

To illustrate this point, the following table consolidates representative per-minute limits that are widely used for planning. They are not authoritative and should be confirmed against the current project configuration.

| Scope       | Read requests (per minute) | Write requests (per minute) | Notes |
|-------------|-----------------------------|------------------------------|-------|
| Per project | 300                         | 300                          | Representative numbers; verify in the Cloud Console quotas dashboard[^3]. |
| Per user    | 60                          | 60                           | Representative caps to protect fairness; verify per-user enforcement[^3]. |

The key takeaway is that workloads must be paced to remain comfortably under per-minute caps with headroom for retries and transient spikes. When these conditions hold, systems can achieve stable throughput without repeated quota breaches[^1][^3][^5].

## High-Level Architecture and Data Flow

The architecture is organized around five actors: Producers, the Queue, Workers, a Rate Limiter service, and Observability. Producers submit jobs via Edge Functions, which write job records to the queue. Workers poll the queue using transactional queries that adopt SKIP LOCKED, ensuring each job is assigned to exactly one worker without coordinator bottlenecks. The Rate Limiter service consults both per-project and per-user counters before dispatching jobs, dynamically shaping work to avoid 429s. Observability captures job lifecycle events, progress updates, and system metrics, publishing job status via Realtime.

The end-to-end flow is straightforward. Producers submit job requests to an Edge Function endpoint, which validates inputs, applies RLS, and writes a job record to the jobs table. Workers run continuously, polling for the next available job by priority and freshness using SKIP LOCKED to avoid double assignment. Before invoking external APIs, Workers query the Rate Limiter, which evaluates available budget and either dispatches the call, delays it, or instructs a retry with backoff. On completion, Workers emit job events to a job_events stream, which Observability consumes to update dashboards, trigger alerts, and publish Realtime updates to clients. This design cleanly separates concerns and scales horizontally by adding workers, with minimal coupling to the database backend[^10][^11][^12][^13].

### Data Store Selection and Transactional Polling

Postgres is well-suited as the queue backend due to its ACID guarantees, SQL flexibility, and native support for SKIP LOCKED. Transactional polling enables multiple workers to contend for work safely: a worker issues a SELECT…FOR UPDATE SKIP LOCKED to claim the next available job, thereby locking the row and skipping rows locked by other workers. This pattern ensures exactly-once assignment under concurrency, with the database serving as the arbiter of ownership. With careful indexing on status, priority, and id, workers can select jobs in priority order while maintaining fairness through aging and degradation policies[^10][^11][^12][^13].

The advantages are clear: minimal infrastructure, strong consistency, and operational simplicity. The trade-off is that Postgres is not a specialized message broker and can become the bottleneck at extreme throughput. However, for moderate-to-high workloads backed by appropriate indexing and batching, this pattern has been shown to perform reliably and integrate well with application data and backup/restore processes[^10][^11][^12][^13].

## Job Prioritization and Scheduling

The system defines three priority tiers—urgent, normal, low—to reflect business impact and user expectations. Priority alone, however, is not sufficient; we must also account for freshness and fairness. Aging promotes lower-priority jobs over time to prevent starvation, and degradation temporarily boosts priority for long-waiting jobs. Scheduling is preemptive at the job claim boundary: workers always select the highest-priority, oldest job first, but never preempt a job that is already running.

To anchor these concepts, the system can adopt a score-based priority model that combines the original priority with waiting-time boosts. For example, urgent jobs could be given a base weight that outpaces normal and low tiers, while a linear or step boost increases the effective score for jobs that have waited beyond a threshold. The scheduler orders jobs by this score at poll time, and aging rules escalate low-priority jobs after prolonged waiting periods.

To illustrate this scheme, the following table shows example priority scoring rules and aging boosts.

| Priority level | Base score | Aging rule | Waiting-time boost | Notes |
|----------------|------------|------------|--------------------|-------|
| Urgent         | 100        | None       | Optional small boost after long wait | Intended for time-critical operations. |
| Normal         | 10         | Boost to 20 after 15 minutes in queue | Linear boost per hour | Prevents starvation while honoring original tier. |
| Low            | 1          | Boost to 5 after 30 minutes; escalate to normal after 2 hours | Step boosts at fixed intervals | Ensures low-priority work eventually executes. |

The scheduler is summarized below to highlight how base weights and aging interact.

| Tier   | Base weight | Aging thresholds | Boost amount | Escalation path |
|--------|-------------|------------------|--------------|-----------------|
| Urgent | 100         | None             | Minimal      | None            |
| Normal | 10          | 15 minutes       | +10          | Escalate to urgent only under exceptional conditions |
| Low    | 1           | 30 minutes; 2 hours | +4; escalate to normal | Escalate to normal after maximum wait window |

In a Postgres-backed queue, scheduling logic can be implemented through a composite ORDER BY on priority and created_at fields, with periodic updates to priority fields to reflect aging. Alternatively, a separate priority_scores table can be updated by a background process that applies aging rules at defined intervals. The priority queue pattern ensures high-priority work is processed quickly while preserving system fairness and preventing starvation[^24][^10].

### Database Design for Prioritization

The jobs table should include a priority column (e.g., enum: urgent, normal, low), a created_at timestamp, and fields for effective_priority or scoring attributes. Indexes on (status, priority, created_at) enable efficient polling ordered by priority and freshness. For fairness, age-based adjustments should update effective_priority as jobs wait longer; workers then select the highest effective_priority job that is pending. Transactional updates to effective_priority must be performed carefully to avoid contention and ensure consistent ordering.

Aged jobs can be surfaced to workers through a materialized view or through periodic updates within the transaction that claims the next job. Both approaches are viable; the choice depends on workload characteristics and the acceptable overhead of background maintenance versus runtime complexity[^24][^10].

## Rate Limiting Logic for AI API Calls

Rate limiting operates at two scopes simultaneously: per project and per user. In practice, both quotas apply, and the system must respect the tighter limit. The design favors a sliding window rate limiter for per-user counters, combined with a token bucket or leaky bucket for project-level smoothing. This combination enables precise fairness control per actor while preventing bursty traffic at the project level from triggering 429s. Enforcement is applied in the scheduler path: before a worker invokes the external API, it checks the limiter; if insufficient budget remains, the job is deferred with a retry instruction that includes backoff and jitter. Edge Functions are responsible for authoritative invocations and secure key management, acting as the trusted execution context[^1][^15][^16][^5][^6].

To ground parameter choices, we summarize common sliding window and token bucket configurations below. These are templates that require tuning to match observed traffic patterns and official quotas.

To make these trade-offs explicit, Table 1 compares sliding window and token bucket options for rate limiting.

| Algorithm     | Core parameters                  | Strengths                                       | Trade-offs                                     | Typical use |
|---------------|----------------------------------|--------------------------------------------------|------------------------------------------------|------------|
| Sliding window (per user) | Window size (e.g., 60s), Max requests (e.g., 60), Bucket key (user_id) | Fairness per actor; precise per-minute enforcement | Requires per-actor state; clock drift sensitivity | Per-user quotas |
| Token bucket (project)   | Capacity (e.g., 300 tokens), Refill rate (e.g., 5 tokens/sec), Bucket key (project_id) | Smooths bursts; supports controlled oversubscription | Requires token accounting; bucket management | Project-level shaping |
| Leaky bucket (project)   | Leak rate (fixed), Queue size             | Smooths output rate; simple implementation       | Less flexible for bursts; queue overflow handling | Fixed-rate smoothing |

A recommended baseline is to set per-user sliding window caps at 60 requests per minute, and per-project token bucket capacity at 300 requests per minute with a refill rate aligned to minute-level quotas. This configuration allows short bursts while maintaining steady consumption across the minute, thereby reducing synchronized retry storms[^1][^15][^16].

We also map common error responses to remediation tactics to guide consistent handling.

| HTTP status | Typical cause                          | Recommended remediation |
|-------------|----------------------------------------|-------------------------|
| 429         | Per-minute quota exceeded              | Truncated exponential backoff with jitter; reduce concurrency; prefer batching[^5]. |
| 403         | Permission or scope issues             | Validate credentials; check scopes and entitlements. |
| 404         | Resource not found                     | Verify identifiers; ensure target resource exists. |
| 400         | Malformed request                      | Validate request grammar and field masks. |

### Integration with Scheduler and Workers

The Rate Limiter service exposes a pre-dispatch check that Workers must call before invoking the external API. The call includes actor identity (user_id and project_id), planned call type (read/write), and estimated cost. The limiter returns one of four decisions: proceed, defer for a calculated short delay, retry with backoff parameters, or reject with a terminal error (e.g., for malformed requests). Enforcement must be consistent and centralized to avoid policy drift across workers.

To align with minute-refill behavior, we avoid global sleep heuristics and instead attach backoff to the individual call that received 429. Jitter randomization prevents herding effects where many workers retry at once. Retry instructions reference job-specific state so the worker can persist the backoff attempt and update the job status transparently to downstream systems[^5].

## Retry Mechanism with Exponential Backoff and Jitter

Retries must be bounded and safe. The system adopts a truncated exponential backoff strategy with jitter for retriable errors, notably 429 and transient network failures. Two example parameter sets are recommended as baselines. Template A emphasizes moderate pacing: initial delay 1 second, multiplier 3×, maximum delay ~60 seconds, maximum retries 5, and a total timeout window near 500 seconds. Template B is more aggressive: initial delay 1 second, multiplier 2×, maximum delay ~64 seconds, and up to 10 retries. The choice depends on workload sensitivity to latency and the cost of extending retry windows. In all cases, only idempotent operations should be retried; non-idempotent operations require idempotency keys or similar protection[^5][^7][^8][^17][^18][^19][^20].

The comparison below helps teams pick a starting point and tune based on observed error patterns.

| Parameter                    | Template A (moderate pacing) | Template B (aggressive) |
|-----------------------------|-------------------------------|-------------------------|
| Initial delay               | 1 second                      | 1 second                |
| Delay multiplier            | 3×                            | 2×                      |
| Maximum retry delay         | ~60 seconds                   | ~64 seconds             |
| Maximum retries             | 5                             | 10                      |
| Jitter                      | Full jitter (recommended)     | None/limited (example)  |
| Total timeout window        | ~500 seconds (example)        | Not specified           |
| Idempotency                 | Required                      | Required                |

For batch operations, atomicity must be considered explicitly. With batchUpdate, if any subrequest fails validation, the entire batch fails, and no changes are applied. This property can be used to isolate errors and avoid partial state changes. Workers should classify failures into retriable (e.g., 429) and non-retriable (e.g., 400, 403, 404), and then either re-queue with backoff or route to a dead-letter queue for investigation[^2][^7][^8][^5][^19][^20].

### Dead-Letter Queue (DLQ) and Observability

Jobs that exhaust retries or fail with terminal errors are routed to a DLQ. The DLQ stores the full payload, last error code and message, and retry metadata. Operators and automated tools inspect DLQ records to determine remediation—correcting malformed requests, updating scopes, adjusting quotas, or filing incidents for upstream outages. DLQ entries should trigger alerts and surface in dashboards to maintain visibility and drive rapid resolution[^14].

## Progress Tracking and Status Updates

Users and operators need transparent, timely updates on job progress. The system defines a job state model that captures the lifecycle from submission to completion or failure, including intermediate progress steps for long-running jobs. A job_events table records each state transition and progress percentage with timestamps; a Realtime publication on the jobs table or a dedicated job_events view broadcasts changes to subscribed clients. Clients display status trackers and progress bars while operators use dashboards to monitor throughput, error rates, and queue depth[^21][^22][^23].

A typical state model includes: queued, rate_limited, dispatched, in_progress, retried, completed, and failed. A progress percentage and optional eta support richer feedback. The following table describes the states and permitted transitions.

| State          | Description                              | Allowed transitions                   |
|----------------|------------------------------------------|---------------------------------------|
| queued         | Accepted; awaiting dispatch              | rate_limited, dispatched, retried     |
| rate_limited   | Deferred due to quota constraints        | queued, dispatched, retried           |
| dispatched     | Sent to external API; awaiting response  | in_progress, retried, failed          |
| in_progress    | External API executing                   | retried, completed, failed            |
| retried        | Backoff scheduled and re-queued          | queued, rate_limited, dispatched      |
| completed      | Successful finish                        | terminal                              |
| failed         | Terminal failure or DLQ                  | terminal                              |

For user-facing status trackers versus system progress updates, design patterns differ: trackers emphasize clarity and predictability, while progress updates favor evented, push-based delivery for responsiveness. The system should implement both: pull-based trackers for on-demand views and push-based Realtime events for live progress and state changes[^21][^22][^23].

### Supabase Realtime Considerations

Realtime channels must be scoped carefully to avoid excessive fan-out and cardinality. A sensible approach is to publish per-user channels for client dashboards and global admin channels for operations. Filtering by job_id and user_id keeps subscriptions focused. Backpressure and reconnection strategies are essential: clients should handle missed events through snapshot queries on reconnect, and the system should tolerate temporary disconnects without sacrificing correctness. The precise Realtime limits and scaling characteristics should be validated in the target environment; this is an acknowledged information gap to be closed prior to go-live.

## Supabase Edge Functions Integration

Edge Functions are the interface for producers and the orchestration point for secure operations. They enforce CORS, validate inputs, check authentication, and write job records to the queue via Postgres. Because Edge Functions can use the service role key internally while preserving the original caller’s identity for RLS purposes, policies must allow both the anonymous role and the service role to perform required operations. This dual-layer authentication posture prevents “new row violates row-level security policy” errors and allows secure insertion and updates from server-side functions[^3].

Key integration practices include:
- Allowing both anon and service_role in RLS policies for queue and job events tables.
- Using Deno’s built-in Web APIs; avoiding external imports and Node.js-specific modules.
- Ensuring file paths and storage operations use ASCII-only characters; mapping localized inputs to safe paths.
- Treating Edge Functions as trusted contexts for API key management and rate-limited invocations.

### API Endpoints and Request Lifecycle

The Edge Function endpoint for job submission accepts a JSON payload, validates inputs, and writes a job record with a durable status of queued. Authentication is verified, and RLS policies are applied. The job is then available for polling workers. For status queries, the endpoint can return job state, progress, and last event details. Realtime subscriptions broadcast job_events, and clients use these channels to render live progress.

Rate limiting decisions and retry instructions are propagated to producers and workers through structured responses and job metadata. For example, when a job is rate_limited, the system includes a recommended backoff interval; workers use this to reschedule the job without operator intervention[^3].

## Database Schema and Indexing Strategy

The schema centers on a jobs table, a job_events table, and optional rate_limit_counters and priority_scores tables. The jobs table holds the durable record of work to be performed and its current state; job_events records lifecycle events and progress. Rate limit counters capture per-user sliding window state and project-level token bucket usage; priority_scores supports aging and fairness by storing computed priority boosts. Indexing emphasizes efficient polling by status, priority, and id, plus event queries by job_id and created_at.

Below is a field dictionary for the core jobs and job_events tables. Types are illustrative; adapt them to your environment and ORM preferences.

| Table        | Field               | Type                 | Description                                        |
|--------------|---------------------|----------------------|----------------------------------------------------|
| jobs         | id                  | UUID (primary key)   | Unique job identifier                              |
|              | status              | enum                 | One of queued, rate_limited, dispatched, in_progress, retried, completed, failed |
|              | priority            | enum                 | urgent, normal, low                                |
|              | effective_priority  | numeric              | Computed priority score including aging boosts     |
|              | payload             | JSONB                | Job parameters and request context                 |
|              | user_id             | UUID                 | Actor identity for per-user rate limits            |
|              | project_id          | text                 | Project identity for per-project rate limits       |
|              | idempotency_key     | text                 | Uniquely identifies the job for safe retries       |
|              | retry_count         | integer              | Number of retry attempts                           |
|              | next_attempt_after  | timestamp            | When to attempt the next retry                     |
|              | created_at          | timestamp            | Creation time                                      |
|              | updated_at          | timestamp            | Last update time                                   |
| job_events   | id                  | bigserial            | Event identifier                                   |
|              | job_id              | UUID                 | Foreign key to job                                 |
|              | event_type          | enum                 | state_change, progress, error                      |
|              | message             | text                 | Human-readable details                             |
|              | progress_percent    | numeric              | 0–100                                              |
|              | created_at          | timestamp            | Event time                                         |

Indexing recommendations:
- jobs: (status, effective_priority DESC, created_at ASC), (user_id), (project_id), (idempotency_key UNIQUE).
- job_events: (job_id, created_at), (event_type, created_at).
- rate_limit_counters: per-user and per-project keys with (window_start) to support sliding window cleanup.
- priority_scores: (effective_priority DESC, next_eval_at) for aging sweeps.

### Concurrency-Safe Polling with SKIP LOCKED

Workers claim the next job using a transactional query: SELECT…FOR UPDATE SKIP LOCKED WHERE status = 'queued' ORDER BY effective_priority DESC, created_at ASC LIMIT 1. This atomically locks the row and removes it from contention for other workers. If no row is available, the query returns quickly, and the worker sleeps briefly before retrying. The pattern is highly efficient and avoids central coordination. Careful index design on status, effective_priority, and created_at is required to ensure the query plan is optimal and scalable under load[^10][^11][^13].

## Operations, Monitoring, and Alerting

Operational visibility is the difference between graceful compliance with quotas and repeated incidents. The system should track request counts, error rates (especially 429s), latencies, response sizes, and queue depth. Quota metrics—rate quota usage, quota exceeded indicators, and allocation usage—must be monitored with alerts at 60–80% of caps, leaving headroom for retries and transient spikes. When usage approaches limits, incident runbooks should guide mitigation: reduce concurrency, increase backoff, adjust batch composition, and, if justified, request higher quotas through standard processes[^6][^7][^8][^9][^4][^15].

To make these practices concrete, the following table maps metrics to operational insights and actions.

| Metric type                     | Insight                                    | Action |
|---------------------------------|--------------------------------------------|--------|
| Request count                   | Traffic volume and trends                  | Tune batch sizes; stagger starts; adjust caching. |
| Error rate (429, 4xx classes)   | Quota breaches; configuration issues       | Increase backoff; reduce concurrency; validate scopes. |
| Latency (request/backend)       | Inefficiencies; long-running operations    | Use partial responses; compress; split heavy batches. |
| Response sizes                  | Over-fetching; payload bloat               | Add field masks; compress; limit ranges. |
| Quota rate/net usage            | Proximity to per-minute limits             | Set alerts at 60–80%; enforce per-user throttles. |
| Quota exceeded (BOOL)           | Limit breaches                             | Activate backoff; lower concurrency; request increases if justified. |
| Allocation quota usage          | Consumed allocation vs limits              | Review quotas; file increase requests as needed. |

Operational runbooks should include steps for diagnosing 429s (backoff parameters, batching effectiveness), tuning token bucket settings, and performing controlled load tests to verify throughput under realistic quotas. Staggering job start times and smoothing burst traffic are effective techniques to keep systems within per-minute caps[^6][^7][^8][^9][^4][^15].

## Security, Reliability, and Disaster Recovery

Security is enforced through RLS policies that allow both anon and service_role for Edge Function operations, preventing authorization errors while keeping writes and updates safe. Sensitive credentials—API keys and service role tokens—are confined to the Edge Function runtime. Idempotency keys at the job level ensure retried operations do not duplicate side effects, and de-duplication is implemented using unique indexes on idempotency_key.

Reliability is strengthened through DLQ management, runbooks, and a robust retry posture. Backups include both the queue data and job events, enabling consistent restore and replay. High availability is achieved through stateless workers and a horizontally scalable queue; leader election and worker fencing can be added to prevent pathological contention. Disaster recovery emphasizes restore validation, replay of job_events to rebuild in-memory state, and controlled resumption of operations to avoid re-triggering quota breaches[^3].

## Cost Optimization and Batching Strategies

Although many APIs are not billed per request, operational costs arise from over-fetching, over-writing, and handling quota violations. The most effective lever is to minimize API calls through batching and request shaping. For Google Sheets, batchUpdate allows multiple subrequests—adding sheets, setting data validation, applying formatting—to be combined in one atomic call, counting as a single request against per-minute limits. Keeping payloads small and using field masks for partial updates reduces latency and the likelihood of throttling. Enabling gzip compression further reduces bandwidth. Cache static metadata and stage writes to minimize redundant reads. Shard workloads by project and user to respect per-user quotas and prevent hot spots[^2][^3][^6][^7][^8][^9].

To guide batching decisions, the following table maps common scenarios to optimization techniques and expected effects.

| Scenario                      | Technique                                | Expected effect |
|-------------------------------|------------------------------------------|-----------------|
| Reading large ranges          | fields + pagination                       | Smaller responses; faster reads; lower CPU/memory[^3]. |
| Writing many small cells      | batchUpdate (grouped)                     | Fewer requests; higher throughput; reduced throttling risk[^2]. |
| Structural changes            | batchUpdate + field masks                 | Precise updates; avoid collateral changes; fewer calls[^2]. |
| High-latency or bandwidth     | gzip compression                          | Reduced payload size; lower network usage; minor CPU overhead[^3]. |

The principle is steady, compact operations that do the maximum useful work per call while staying well under per-minute quotas. Monitoring ties these choices together by exposing where requests are inefficient and where quotas are tight[^6][^7][^8][^9][^4][^15].

## Implementation Roadmap and Acceptance Criteria

A staged rollout reduces risk and ensures operability from the outset.

Phase 1: Baseline queue with SKIP LOCKED
- Implement jobs and job_events tables with indexes.
- Deploy workers that poll and claim jobs transactionally.
- Acceptance: multiple workers claim distinct jobs without double assignment; jobs complete successfully; event log captures state transitions.

Phase 2: Prioritization and aging
- Add priority tiers, effective_priority scoring, and aging rules.
- Acceptance: urgent jobs are consistently selected first; long-waiting normal and low jobs receive boosts and eventually execute; fairness is demonstrably improved.

Phase 3: Rate limiting
- Implement per-user sliding window and project-level token bucket.
- Acceptance: dispatch decisions honor both scopes; 429 rate drops; operators can tune caps; alerts fire near 60–80% of quotas.

Phase 4: Retries with backoff and jitter
- Adopt truncated exponential backoff and jitter; define retry caps and total timeout windows; implement DLQ.
- Acceptance: 429s trigger backoff; retries eventually succeed or route to DLQ; idempotency protections prevent duplicate side effects.

Phase 5: Progress tracking
- Publish job_events via Realtime; design status trackers and push updates.
- Acceptance: clients receive timely state and progress updates; missed events are reconciled via snapshot queries; operators view queue depth and event timelines.

Phase 6: Monitoring and runbooks
- Instrument request counts, error rates, latencies, response sizes, quota metrics; configure alerts; write incident playbooks.
- Acceptance: dashboards reflect ground truth; alerts are actionable; operators follow playbooks to mitigate incidents.

Acceptance criteria across phases include: a demonstrated drop in 429 incidents; stable throughput under quotas; transparent progress updates; and a DR plan that has been tested through restore and replay exercises[^6][^7][^8][^9][^4][^15].

## Information Gaps and Assumptions

The following items require validation and may influence parameter choices and operational thresholds:
- Exact, current numeric quotas per minute for the target project and per-user enforcement; representative numbers cited are indicative only.
- The specific AI provider’s rate limit policy, burst tolerance, and cost model.
- Workload characteristics such as job volume distributions, concurrency targets, and peak bursts.
- Batch composition constraints (maximum subrequests per batch; payload size distribution).
- Operational SLOs for latency and throughput.
- Supabase Realtime channel scaling limits and recommended cardinality management.
- Idempotency and de-duplication strategies for third-party AI calls.
- Multi-tenant isolation requirements and keying strategy.
- Compliance and audit requirements, including PII handling.

These gaps should be addressed in a pre-launch tuning phase, with controlled load tests and iterative adjustments to backoff parameters, rate caps, and batch sizes.

## References

[^1]: Usage limits | Google Sheets.  
[^2]: Batch requests | Google Sheets.  
[^3]: Improve performance | Google Sheets.  
[^4]: Google Sheets API Essential Guide | Rollout.  
[^5]: How to handle Quota exceeded error 429 in Google Sheets when inserting data through Apps Script? | Stack Overflow.  
[^6]: View and manage quotas | Google Cloud Documentation.  
[^7]: Chart and monitor quota metrics - Google Cloud Documentation.  
[^8]: Set up quota alerts and monitoring - Google Cloud Documentation.  
[^9]: Cloud Monitoring quotas and limits - Google Cloud Documentation.  
[^10]: Building a Simple yet Robust Job Queue System Using PostgreSQL.  
[^11]: Devious SQL: Message Queuing Using Native PostgreSQL.  
[^12]: Lessons from scaling PostgreSQL queues to 100k events per second.  
[^13]: The best way to use a DB table as a job queue (a.k.a batch queue or message queue) | Stack Overflow.  
[^14]: A Developer’s Guide to Modern Queue Patterns.  
[^15]: From Token Bucket to Sliding Window: Pick the Perfect Rate Limiting Algorithm.  
[^16]: Rate Limiting Fundamentals - ByteByteGo.  
[^17]: Retry — google-api-core (Python) documentation.  
[^18]: Class ExponentialBackOff | Google HTTP Client Java Library.  
[^19]: Exponential Backoff with Jitter: A Powerful Tool for Resilient Systems.  
[^20]: Timeouts, retries and backoff with jitter - Amazon AWS Builders Library.  
[^21]: Status Trackers and Progress Updates: 16 Design Guidelines - NN/G.  
[^22]: Virtual Queuing System - Qmatic.  
[^23]: 2025’s Best Queue Management: Digital Solutions Guide - Skiplino.  
[^24]: Priority Queue pattern - Azure Architecture Center | Microsoft Learn.