# Integration Plan: Scheduling Optimization with Existing Batch Processing and Queue System

## 1. Executive Summary and Objectives

This plan integrates a scheduling optimization layer with the current batch processing pipeline to increase throughput, stabilize compliance with external quotas, and reduce operator overhead. The existing system already implements a robust baseline: a batch orchestrator that ingests Google Sheets, validates ideas, creates video jobs, prioritizes them, applies rate limiting, and tracks progress through a local SQLite database. The proposed integration builds on that foundation by adding schedule-aware dispatch, alignment with the enterprise queue system’s priority and rate-limit policies, and automated schedule generation for bulk video content.

The objectives are fourfold. First, augment bulk job creation with scheduling recommendations and constraints such as start windows, concurrency caps, and priority tiers. Second, integrate the local priority queue and rate limiter with the enterprise queue’s priority management and rate limiting policies, ensuring a unified dispatch order and consistent backoff behavior. Third, implement an automated schedule generator that produces job-level dispatch plans aligned to capacity, external quotas, and time windows. Fourth, establish performance tracking and optimization feedback loops that measure throughput, error rates (especially 429s), and progress to continuously refine scheduling policies. Throughout, the integration preserves backward compatibility: existing APIs remain unchanged, scheduling is opt-in, and legacy workflows continue to function without disruption.

In scope are: enhancements to bulk job creation to store scheduling hints; alignment with the priority, aging, and rate limiting models described in the enterprise queue system; schedule generation tailored for bulk video workloads; and feedback loops to improve scheduling parameters. Out of scope are re-architecting the video generation workflow, altering the core data model beyond additive fields, and changes to existing status enums or public interfaces.

Success criteria include: sustained throughput under quotas with reduced 429s; transparent schedule adherence; measurable improvements in job start latency and lower variance in completion times; and a smooth, backward-compatible rollout that does not disrupt current operations.

### 1.1 Scope & Deliverables

The deliverables for this integration are:

- A set of scheduling fields added to bulk and video jobs, with database migrations and write/read paths defined.
- A scheduling service integrated into the bulk job creation and processing flows, producing recommended schedules and enforced constraints.
- Priority and rate-limit policy alignment with the enterprise queue system, including aging rules and pre-dispatch checks.
- An automated schedule generation capability tailored to bulk video workloads, producing job-level dispatch plans and adhering to external API quotas.
- Performance tracking and optimization feedback loops, instrumented via the existing job_events table and progress callbacks, and aligned with the enterprise queue system’s observability guidance.
- A compatibility and rollout plan that introduces scheduling behind feature flags and preserves legacy behavior.

### 1.2 Key Outcomes

The integration yields three primary outcomes. Throughput improves by smoothing bursts, reducing retries due to rate-limit violations, and dispatching jobs in an order that respects both priority and freshness. Compliance with external quotas strengthens via a unified rate-limiter integration that applies per-user sliding windows and per-project token buckets with backoff and jitter. Finally, the user experience becomes more transparent: bulk jobs carry schedule metadata, jobs publish progress and ETA, and operators gain a consistent view of prioritization and fairness in the queue system, harmonized with existing status and event tracking[^24].

## 2. Baseline Architecture and Codebase Overview

The current system implements a BatchProcessor that ingests ideas from Google Sheets, validates them, and orchestrates video jobs through a priority-based queue. Key components include:

- Job data structures: BulkJob and VideoJob with fields for priority, idempotency, status, and timing.
- QueueManager: a priority-based queue with three tiers—URGENT, NORMAL, LOW—and workers that process jobs FIFO within each tier.
- RateLimiter: per-user sliding windows and per-project token buckets that enforce request pacing.
- Database: local SQLite tables for bulk_jobs, video_jobs, and job_events, with progress tracking and callbacks.
- Workflow hooks: generate_video and _execute_video_generation serve as integration points into the downstream video generation pipeline.

To ground the integration, the following table maps core classes and their responsibilities in the current codebase.

| Class/Module     | Responsibility                                   | Notes                                                                 |
|------------------|---------------------------------------------------|-----------------------------------------------------------------------|
| BatchProcessor   | Orchestrates bulk ingestion, validation, enqueue  | Manages state, callbacks, persistence, and monitoring loops          |
| BulkJob          | Represents a bulk ingestion instance              | Holds sheet_id, priority, idempotency_key, and progress              |
| VideoJob         | Represents a single video generation job          | Stores idea_data, priority, ai_provider, cost, status, and retries   |
| QueueManager     | Priority-based job queue and workers              | FIFO within priority; secondary sort by created_at                   |
| RateLimiter      | Enforces per-user and per-project rate limits     | Sliding window per user; token bucket per project                    |
| JobEvent         | Progress and lifecycle events                     | Persisted for observability; supports callbacks                      |
| generate_video   | Entry to downstream video generation              | Applies rate limit checks and retries before dispatch                |

The job lifecycle and state transitions are well-defined: jobs move through QUEUED, RATE_LIMITED, DISPATCHED, IN_PROGRESS, RETRIED, COMPLETED, FAILED, and CANCELLED. These states map directly to the progress tracking and monitoring hooks exposed by the processor. Priority is explicit—URGENT, NORMAL, LOW—and the QueueManager implements FIFO ordering within each priority level. The RateLimiter enforces both per-user and per-project constraints, calculating backoff when requests should wait to avoid 429 responses.

### 2.1 Inventory of Extant Hooks and Callbacks

The integration will leverage the existing callback surfaces:

- Progress callbacks: add_progress_callback registers handlers invoked during _monitor_job_progress for periodic updates.
- Completion callbacks: add_completion_callback registers handlers invoked when jobs finish, supporting downstream notifications or post-processing.
- Workflow hooks: generate_video and _execute_video_generation are called during job execution, already applying rate limit checks and retry behavior.

These hooks provide the natural seams where scheduling metadata can be read and acted upon without disrupting legacy behavior.

## 3. Integration Plan 1: Scheduling Recommendations in Bulk Job Creation

The first integration point augments the bulk job creation process to capture scheduling recommendations and constraints. The aim is to collect time windows, concurrency preferences, and priority hints when a bulk job is submitted, store them alongside the BulkJob and derived VideoJob records, and apply them during dispatch. This allows the queue to consider schedule-aware constraints without changing the public interface of existing methods.

To that end, we define a scheduling metadata structure that can be attached to bulk and video jobs. The structure includes optional fields for start_after and deadline, suggested concurrency, explicit priority overrides, max_parallelism, ai_provider preferences, and an ordered list of time windows during which jobs should be dispatched.

To illustrate the structure, Table 1 lists the fields to be added to bulk and video job records.

| Field                | Scope    | Type                    | Purpose                                               | Required/Optional |
|----------------------|----------|-------------------------|-------------------------------------------------------|-------------------|
| start_after          | Bulk/Job | ISO8601 timestamp       | Earliest time to start dispatch                       | Optional          |
| deadline             | Bulk/Job | ISO8601 timestamp       | Latest acceptable completion time                     | Optional          |
| suggested_concurrency| Bulk     | Integer                 | Hint for concurrency used in schedule generation      | Optional          |
| priority_hint        | Bulk/Job | Enum (URGENT/NORMAL/LOW)| Advisory; may influence effective priority            | Optional          |
| max_parallelism      | Bulk/Job | Integer                 | Cap on concurrent dispatches for related jobs         | Optional          |
| ai_provider_prefs    | Bulk     | List of strings         | Preferred providers to balance load and quotas        | Optional          |
| dispatch_windows     | Bulk/Job | List of window objects  | Time windows (start, end) for allowed dispatch        | Optional          |
| schedule_id          | Bulk/Job | String (UUID)           | Links job to a generated schedule                     | Optional          |
| effective_priority   | Bulk/Job | Integer/Score           | Scheduler-computed priority including aging boosts    | Optional          |

By adding these fields, we enable a schedule-aware QueueManager to select jobs whose windows are open and whose constraints are satisfied. The schedule_id ties a video job to a generated dispatch plan, making it easier to audit adherence and compute latencies relative to the plan.

### 3.1 Data Model Changes

To persist schedule metadata, we extend the existing SQLite schema with additive columns:

- bulk_jobs: add start_after, deadline, suggested_concurrency, ai_provider_prefs (JSON), schedule_id, effective_priority (nullable initially).
- video_jobs: add dispatch_windows (JSON), priority_hint, max_parallelism, ai_provider_prefs (if per-job), schedule_id, effective_priority.

Migration strategy:

- Add new columns with DEFAULT NULL so existing records remain valid.
- Create indexes on schedule_id and effective_priority to support queries during dispatch.
- Backfill effective_priority with the current priority.value for continuity, and allow the scheduler to overwrite for aging and fairness.

These changes are additive; existing code paths remain functional, and unpopulated schedule fields are safely ignored.

### 3.2 API and Workflow Hooks

The integration introduces a lightweight SchedulingService with the following methods:

- compute_schedule(bulk_job_id, constraints): constructs a job-level dispatch plan based on constraints and current rate limits, returning a schedule object with per-job timing and ordering.
- update_effective_priorities(bulk_job_id): recalculates effective_priority using aging rules.
- get_schedule(bulk_job_id): retrieves generated schedule metadata for observability.

The create_bulk_job method remains unchanged. An optional apply_scheduling_params step can be called after creation to attach scheduling constraints and generate a plan. During process_sheet_ideas, the processor reads scheduling fields, validates them, and passes them to newly created VideoJob records. If scheduling is disabled or no metadata is present, the system continues to dispatch jobs using legacy priority and FIFO ordering.

To make the extension explicit, Table 2 maps the existing method signatures to new scheduling hooks.

| Original Method                 | New Hook/Method                     | Behavioral Change                                                                 |
|---------------------------------|-------------------------------------|-----------------------------------------------------------------------------------|
| create_bulk_job(...)            | apply_scheduling_params(...)        | Optional: attaches constraints and generates schedule metadata                     |
| process_sheet_ideas(...)        | read_scheduling_metadata(...)       | Reads schedule fields; validates windows; passes to job creation                   |
| QueueManager.add_job(...)       | QueueManager.add_job(...)           | No change; can read schedule_id and effective_priority when available             |
| _monitor_job_progress(...)      | observe_schedule_adherence(...)     | Optional: adds schedule adherence metrics to job_events                            |

### 3.3 Backward Compatibility

Scheduling recommendations are opt-in. If no scheduling metadata is provided, the system behaves exactly as before: legacy priority and FIFO ordering apply, and existing progress and completion callbacks continue to function. Feature flags control the scheduling features; when disabled, no new schedule fields are read or written. Public APIs remain unchanged, ensuring no consumer-facing breakage.

## 4. Integration Plan 2: Queue System and Priority Management Alignment

The next integration aligns the local priority and rate limiting model with the enterprise queue system’s policies. The local queue uses three tiers—URGENT, NORMAL, LOW—and orders by creation time within each tier. The enterprise system describes aging and fairness rules that promote long-waiting jobs to prevent starvation, and it recommends a score-based effective priority computed from base weights and waiting-time boosts. We will adopt an effective_priority score, computed and periodically updated, to reflect these aging rules without preempting running jobs.

Table 3 outlines the alignment between the current tiers and the enterprise priority tiers, including suggested base weights and aging rules to be introduced.

| Local Tier | Enterprise Alignment | Base Weight | Aging Thresholds               | Boost Amount            | Notes                                              |
|------------|-----------------------|-------------|--------------------------------|-------------------------|----------------------------------------------------|
| URGENT     | Urgent                | 100         | None                           | Minimal                 | Time-critical; retains precedence                  |
| NORMAL     | Normal                | 10          | Boost to 20 after 15 minutes   | +10                     | Promotes fairness without over-throttling urgent   |
| LOW        | Low                   | 1           | Boost to 5 after 30 minutes; escalate to normal after 2 hours | +4; escalate to normal | Prevents starvation; encourages eventual execution |

We will also integrate rate limiting more explicitly with the scheduler:

- Pre-dispatch checks: before a worker dequeues a job, consult the RateLimiter to decide if the job should proceed, wait briefly, or be retried with backoff and jitter.
- Per-user sliding window: enforce fairness and smooth per-actor traffic.
- Per-project token bucket: ensure the aggregate does not exceed project caps; smooth bursts.
- Retry logic: apply truncated exponential backoff with jitter on 429s, respecting idempotency protections.

Table 4 summarizes the parameterization for rate limiting aligned with the enterprise design.

| Algorithm               | Core Parameters                            | Purpose                                              |
|-------------------------|--------------------------------------------|------------------------------------------------------|
| Sliding window (per user) | Window size ~60s; Max requests ~60; key=user_id | Fairness per actor; precise per-minute enforcement   |
| Token bucket (project)  | Capacity ~300; Refill rate ~5 tokens/sec; key=project_id | Smooth bursts; align with minute-gated quotas       |
| Enforcement point       | Pre-dispatch in worker loop                 | Decide proceed, defer, retry, or reject             |
| Backoff with jitter     | Initial delay ~1s; multiplier ~2–3; max delay ~60s; cap retries | Reduce synchronized retries; comply with quotas     |

By aligning the local model to the enterprise queue design, we ensure that the scheduler always selects the highest effective_priority job whose windows are open and whose rate-limit budget allows dispatch, producing consistent and fair behavior across both layers[^24][^1][^5].

### 4.1 Effective Priority and Aging

Effective priority becomes the primary ordering criterion at dequeue time. The scheduler computes effective_priority using base weights and waiting-time boosts. Aging rules promote long-waiting normal and low jobs over time:

- Normal tier boosts from 10 to 20 after 15 minutes in queue, then further escalates if needed.
- Low tier boosts from 1 to 5 after 30 minutes, then escalates to normal after two hours.

Workers never preempt running jobs; promotion applies at the claim boundary, ensuring stability.

### 4.2 Rate Limiter Enhancements

We introduce a scheduling-aware rate-limit gate: the QueueManager consults the RateLimiter before dispatch. If the limiter indicates insufficient budget, the job may be deferred with a short delay or marked RETRIED with backoff and jitter. The system avoids global sleep heuristics; backoff is attached to the specific job and call that received 429, reducing retry storms and aligning with minute-refill behavior[^1][^5].

## 5. Integration Plan 3: Automated Schedule Generation for Bulk Video Content

Automated schedule generation translates bulk scheduling constraints into job-level dispatch plans. The generator consumes time windows, capacity hints, and priority preferences, then produces a schedule that maps each VideoJob to a planned dispatch time and ordering. The plan respects ai_provider quotas and the configured rate limiter, ensuring external calls remain within budgets.

Inputs include:

- start_after and deadline windows for the bulk job and per-job windows when available.
- suggested concurrency and max_parallelism constraints.
- ai_provider preferences to spread load and respect provider-specific quotas.
- current rate limiter state and historical 429 observations to pace dispatch.

Outputs include:

- schedule_id linking the plan to jobs.
- per-job planned_start_at aligned to open windows and rate-limit budgets.
- ordering constraints that ensure effective priority and freshness are honored.
- throughput and error projections to guide operator review.

Table 5 outlines a canonical schedule plan.

| Job ID        | Planned Start         | Priority Tier | Effective Priority | Rate-limit Bucket | Provider      | Dependencies                      |
|---------------|-----------------------|---------------|--------------------|-------------------|---------------|-----------------------------------|
| video_job_001 | 2025-11-05T10:00:00Z  | Normal        | 20                 | user:normal       | provider_A    | window open; budget available     |
| video_job_002 | 2025-11-05T10:00:05Z  | Normal        | 10                 | user:normal       | provider_B    | after job_001; quota headroom     |
| video_job_003 | 2025-11-05T10:15:00Z  | Low           | 5                  | project:normal    | provider_A    | low-tier window open; smoothing   |

By generating job-level plans, the system ensures schedules adhere to windows and quotas while respecting effective priority.

### 5.1 Algorithms and Heuristics

The schedule generation logic applies several heuristics:

- Windowed dispatch: jobs are scheduled only when their start windows are open; if no windows are defined, default to the current time with smoothing to avoid bursts.
- Capacity-based batching: group jobs by provider to respect per-provider quotas and leverage batch operations where appropriate.
- Priority-first ordering: start with effective priority, then apply arrival order for fairness; aging boosts adjust the ordering over time.
- Idempotency and deduplication: any replays or retries consult idempotency keys to prevent duplicate side effects.

These heuristics prioritize simplicity and predictability, balancing throughput with compliance[^5].

### 5.2 Edge Cases and Fallbacks

The generator must handle common edge cases:

- Overlapping windows: if windows overlap across many jobs, apply smoothing and stagger starts to avoid bursts, respecting effective priority ordering.
- Provider quota exhaustion: if a provider’s quota is tight, shift jobs to alternative providers based on ai_provider_prefs, maintaining overall deadline adherence.
- Absent windows: if no windows are defined, fallback to immediate dispatch with pacing, monitoring 429 rates and adjusting concurrency dynamically.

These fallbacks ensure schedules remain resilient when constraints are ambiguous or tight.

## 6. Integration Plan 4: Performance Tracking and Optimization Feedback Loops

To optimize scheduling policies, we instrument performance metrics that reflect throughput, latency, error rates, and quota compliance. The existing job_events table and progress callbacks provide a natural observability surface. We will publish schedule adherence metrics—such as planned_start_at versus actual_start_at—into job_events and use callbacks to update dashboards. The system will apply feedback loops to adjust rate limiter caps, smoothing parameters, and aging thresholds based on observed 429 rates and backlog growth.

Table 6 maps metrics to insights and actions.

| Metric                     | Insight                                  | Action                                        |
|---------------------------|-------------------------------------------|-----------------------------------------------|
| Throughput (jobs/min)     | Overall capacity utilization               | Tune concurrency and smoothing windows        |
| 429 rate (%)              | Quota pressure and pacing errors           | Increase backoff; reduce concurrency; prefer batching[^5] |
| Job start latency (p50/p95)| Scheduling and rate-limit delays           | Adjust effective priority; stagger starts     |
| Progress adherence (%)    | Schedule execution vs plan                 | Rebalance windows; correct provider routing   |
| Retry counts              | Stability of external calls                | Investigate providers; refine idempotency     |
| Queue depth               | Backlog and starvation risk                | Adjust aging; apply degradation policies      |

### 6.1 Error Handling and Retry Instrumentation

Retry events are already persisted via job status changes (e.g., RETRIED) and error messages in job_events. The system will enhance instrumentation by:

- Tagging retries attributable to rate limiting with a specific event type (e.g., rate_limited_retry) and attaching backoff parameters to the message.
- Associating schedule_id with retry events to observe which parts of a schedule trigger quota violations.
- Using these observations to auto-tune backoff templates (initial delay, multiplier, max delay) and adapt rate-limiter caps in subsequent schedules.

### 6.2 Optimization Cycle

The optimization cycle comprises four steps:

1. Measure: collect throughput, latency, 429 rate, backlog, and schedule adherence.
2. Analyze: detect trends and threshold breaches (e.g., persistent 429s at high concurrency).
3. Adjust: update rate limiter parameters (token bucket refill, sliding window caps), effective priority aging thresholds, and schedule smoothing strategies.
4. Validate: run controlled tests and monitor for improvement; roll back if degradation is observed.

This loop ensures the scheduling layer evolves to match real workload patterns and quota constraints.

## 7. Integration Plan 5: Backward Compatibility and Rollout Strategy

Backward compatibility is preserved by default. Scheduling is introduced behind feature flags; if disabled, the system behaves identically to the current implementation. Existing APIs and workflows remain unchanged, and scheduling fields are optional. The rollout proceeds in phases to reduce risk and allow operator review.

Table 7 summarizes the phased rollout.

| Phase | Scope                                   | Success Criteria                                        | Rollback Path                           |
|-------|------------------------------------------|---------------------------------------------------------|------------------------------------------|
| 1     | Introduce scheduling metadata fields     | DB migration succeeds; legacy behavior preserved        | Disable feature flag; revert columns     |
| 2     | Enable scheduling in non-critical jobs   | Schedules generated; dispatch respects windows          | Turn off scheduling; fall back to FIFO   |
| 3     | Integrate effective priority and aging   | Priority ordering demonstrably improved; no starvation  | Disable aging; revert to base priority   |
| 4     | Rate-limit pre-dispatch checks           | Reduced 429 rate; stable throughput                     | Disable limiter integration; legacy checks |
| 5     | Observability and feedback loops         | Dashboards show adherence and 429s; auto-tuning effective | Freeze auto-tuning; manual parameter set |
| 6     | Controlled load tests and tuning         | Target throughput sustained; alerts configured          | Roll back to previous phase parameters   |

### 7.1 Safeguards and Kill Switches

Safeguards ensure rapid rollback if anomalies occur:

- Feature flags for scheduling and aging rules enable immediate disablement.
- Configuration-based caps on concurrency and backoff prevent runaway behavior.
- Clear rollback steps are documented per phase, from disabling scheduling to reverting DB changes if absolutely necessary.

## 8. Security, Reliability, and Disaster Recovery Alignment

Security and reliability are central to the integration. Idempotency keys already exist in BulkJob and VideoJob, ensuring safe retries and avoiding duplicate side effects. The rate limiter introduces fairness and protects external quotas, while the database persists state and events to support recovery and replay. Disaster recovery relies on backups of bulk_jobs, video_jobs, and job_events; replaying events restores in-memory state and progress tracking.

### 8.1 Operational Resilience

Operational resilience hinges on concurrency limits, backoff-and-jitter for 429s, and controlled retry caps. The QueueManager is already configured with a bounded number of workers; the integration caps concurrency further when schedules or quotas indicate pressure. Retry caps and truncated backoff minimize tail latencies and avoid repeated quota violations. DLQ pathways can be introduced for jobs that exhaust retries; the current status model already supports failure states and error messages to facilitate inspection.

## 9. Testing Strategy and Acceptance Criteria

Testing validates correctness, performance, and backward compatibility across all phases. The strategy includes unit tests for scheduling logic, integration tests for dispatch ordering and rate limiting, and load tests that simulate high-volume bulk jobs under constrained quotas. Acceptance criteria focus on the core goals: stable throughput, reduced 429s, accurate progress updates, and a smooth rollout with preserved legacy behavior.

Table 8 provides a test matrix for the phases.

| Feature Area           | Test Type        | Expected Outcome                                               | Acceptance Criteria                                           |
|------------------------|------------------|----------------------------------------------------------------|----------------------------------------------------------------|
| Scheduling metadata    | Unit             | Fields persisted and read correctly                            | Migrations pass; backward compatibility preserved             |
| Effective priority     | Integration      | Aging boosts applied; ordering correct                         | Urgent first; long-waiting low jobs eventually execute        |
| Rate-limit pre-dispatch| Integration      | 429s trigger backoff; concurrency adjusted                     | Drop in 429 rate; stable throughput under quotas              |
| Schedule generation    | Unit/Integration | Job plans created; windows respected                           | Plans adhere to windows; backlog growth controlled            |
| Progress callbacks     | Integration      | Events published; adherence metrics visible                    | Realtime updates accurate; snapshots reconcile missed events  |
| Rollout flags          | Integration      | Scheduling toggled without breaking legacy workflows           | No API breakage; feature flags effective                      |
| Load/stress            | Load/Performance | Throughput sustained; backoff effective                        | SLOs met; alerts configured; controlled retry storms          |

### 9.1 Metrics and SLOs

Target SLOs include:

- Throughput goals under quotas: sustained jobs/min within per-user and per-project caps, with headroom for retries.
- 429 rate targets: downward trend with pacing and batching; alerts at 60–80% of quotas.
- Latency targets: stable p50 and p95 job start times, with reduced variance as schedules smooth bursts.

These SLOs reflect the operational posture recommended for quota compliance and monitoring[^6][^7][^8][^9].

## 10. Appendices: Schema and API Extensions

The appendices document the schema changes and API surface introduced by the scheduling layer. These are additive and designed for backward compatibility.

Table 9 details the schema changes to bulk_jobs and video_jobs.

| Table       | New Column              | Type        | Purpose                                              | Default  | Index |
|-------------|-------------------------|-------------|------------------------------------------------------|----------|-------|
| bulk_jobs   | start_after             | TEXT (ISO)  | Earliest start time for bulk job                     | NULL     | No    |
| bulk_jobs   | deadline                | TEXT (ISO)  | Latest acceptable completion time                    | NULL     | No    |
| bulk_jobs   | suggested_concurrency   | INTEGER     | Concurrency hint for schedule generation             | NULL     | No    |
| bulk_jobs   | ai_provider_prefs       | TEXT (JSON) | Provider preferences                                 | NULL     | No    |
| bulk_jobs   | schedule_id             | TEXT        | Links to generated schedule                          | NULL     | Yes   |
| bulk_jobs   | effective_priority      | INTEGER     | Scheduler-computed priority                          | NULL     | Yes   |
| video_jobs  | dispatch_windows        | TEXT (JSON) | Per-job allowed dispatch windows                     | NULL     | No    |
| video_jobs  | priority_hint           | INTEGER     | Advisory hint                                        | NULL     | No    |
| video_jobs  | max_parallelism         | INTEGER     | Per-job concurrency cap                              | NULL     | No    |
| video_jobs  | ai_provider_prefs       | TEXT (JSON) | Per-job provider preferences                         | NULL     | No    |
| video_jobs  | schedule_id             | TEXT        | Links to generated schedule                          | NULL     | Yes   |
| video_jobs  | effective_priority      | INTEGER     | Scheduler-computed priority                          | NULL     | Yes   |

Table 10 summarizes the API surface introduced and extended.

| API/Method                   | Inputs                                            | Outputs                                 | Error Modes                                 |
|------------------------------|---------------------------------------------------|------------------------------------------|----------------------------------------------|
| SchedulingService.compute_schedule | bulk_job_id, constraints                      | schedule object with per-job plans       | ValidationError (invalid windows), RateLimitError (quota tight) |
| SchedulingService.update_effective_priorities | bulk_job_id                  | updated priorities per job               | ConflictError (concurrent updates)           |
| SchedulingService.get_schedule | bulk_job_id                                     | schedule metadata                        | NotFoundError (no schedule)                  |
| apply_scheduling_params       | bulk_job_id, scheduling_metadata                 | updated bulk job                         | ValidationError                              |
| read_scheduling_metadata      | bulk_job_id, row/idea                             | validated scheduling fields              | ValidationError                              |
| observe_schedule_adherence    | schedule_id, job_id, actual_start                 | job_event entries                        | PersistenceError                             |

These extensions provide a clear, optional pathway to introduce schedule-aware behavior without altering legacy interfaces.

## 11. Information Gaps and Assumptions

Several parameters require validation before production deployment. Exact per-minute quotas for the target project and per-user enforcement must be confirmed; representative numbers cited for planning are indicative only. The specific AI provider’s rate limit policy, burst tolerance, and cost model are not specified and must be measured. Workload characteristics—such as job volume distributions, concurrency targets, and peak bursts—should be characterized through controlled load tests. Batch composition constraints, including maximum subrequests per batch and payload distributions, will influence schedule generation. Operational SLOs for latency and throughput must be defined. Supabase Realtime channel scaling limits should be validated for publish/subscribe of job_events. Idempotency and de-dup strategies for third-party AI calls must be clarified. Multi-tenant isolation requirements and compliance needs, including PII handling, require policy decisions.

These gaps will be addressed during Phase 6 testing and tuning, with iterative adjustments to backoff parameters, rate caps, and batch sizes. Feature flags and rollback paths ensure safe exploration of the parameter space.

## 12. References

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
[^14]: A Developer's Guide to Modern Queue Patterns.  
[^15]: From Token Bucket to Sliding Window: Pick the Perfect Rate Limiting Algorithm.  
[^16]: Rate Limiting Fundamentals - ByteByteGo.  
[^17]: Retry — google-api-core (Python) documentation.  
[^18]: Class ExponentialBackOff | Google HTTP Client Java Library.  
[^19]: Exponential Backoff with Jitter: A Powerful Tool for Resilient Systems.  
[^20]: Timeouts, retries and backoff with jitter - Amazon AWS Builders Library.  
[^21]: Status Trackers and Progress Updates: 16 Design Guidelines - NN/G.  
[^22]: Virtual Queuing System - Qmatic.  
[^23]: 2025's Best Queue Management: Digital Solutions Guide - Skiplino.  
[^24]: Priority Queue pattern - Azure Architecture Center | Microsoft Learn.