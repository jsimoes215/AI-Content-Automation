# Database Schema for Platform-Specific Scheduling Optimization: Supabase Design and Integration with Bulk Job Tables

## Executive Overview: Objectives, Scope, and Deliverables

This technical architecture and database design report specifies a security-first, performance-conscious Supabase/PostgreSQL schema that enables platform-specific scheduling optimization across YouTube, TikTok, Instagram, X (Twitter), LinkedIn, and Facebook. The solution models platform timing heuristics, user scheduling preferences, content calendars and posting schedules, performance analytics, and optimization tracking, and it integrates seamlessly with the existing bulk job tables: bulk_jobs, video_jobs, job_costs, and provider_config.

The design adheres to three guiding principles:

- Security by default: Row-Level Security (RLS) is enabled on all tables; policies permit both anon (Edge Function outer authentication) and service_role (inner database operations) roles without compromising isolation.
- High-throughput operational safety: Relationships are enforced logically (no foreign key constraints), backed by targeted indexes, idempotency keys, and partial indexes for active states.
- Analytics readiness: KPI and optimization event models are structured for rollups and experimentation, with consistent user_id ownership for RLS and auditing.

Deliverables in this report include:
- SQL CREATE statements for all new scheduling tables and indexes.
- RLS policy stubs and a policy matrix aligned to existing patterns.
- A data lifecycle playbook (retention, archival, reindexing, compaction).
- Query patterns and index coverage maps for dashboards and schedulers.
- Integration mappings between scheduling entities and bulk_jobs/video_jobs.

![Conceptual data model for scheduling and analytics modules.](/workspace/docs/images/data_model_diagram.png)

## Integration with Existing Bulk Job Tables: Mapping and ID Strategy

The scheduling system attaches to the established bulk operations model without introducing foreign key constraints, instead relying on indexes, uniqueness, and application-side validation. The logical connections are as follows:
- video_jobs are child units within bulk_jobs; scheduling assignments reference video_jobs and, when bulk作业 style is used, also reference bulk_jobs directly.
- job_costs provide cost line items for video_jobs; KPI metrics are captured separately in scheduling-specific analytics tables rather than overloading job_costs.
- provider_config is used to attribute provider-level rates and features but does not enforce referential integrity with scheduling tables.

Ownership and auditability are anchored by user_id, matching the established pattern across bulk_jobs, video_jobs, and job_costs. Where applicable, status is reconciled between scheduling and job tables to maintain dashboard consistency.

To prevent duplicate work and enable safe retries, idempotency keys are carried through scheduling entities. For example, content_schedule_items can be unique on (user_id, video_job_id, platform_id, scheduled_at), preventing double-scheduling for the same asset.

Table: Integration touchpoints and mapping

| Scheduling entity | Joins to | Join keys (logical) | Purpose |
|---|---|---|---|
| content_schedule_items | video_jobs | video_jobs.id → content_schedule_items.video_job_id | Assign scheduled posts to generated assets |
| content_schedule_items | bulk_jobs | bulk_jobs.id → content_schedule_items.bulk_job_id | Group schedule items under a bulk job context |
| schedule_assignments | video_jobs | video_jobs.id → schedule_assignments.video_job_id | Bind a specific post slot to an asset |
| performance_kpi_events | video_jobs | video_jobs.id → performance_kpi_events.video_job_id | KPI attribution to a posted asset |
| optimization_trials | user_id | profiles/profiles.id alignment via RLS | Per-user experiment configuration |

Table: Cross-module field mapping

| Field | Source table | Target table | Notes |
|---|---|---|---|
| user_id | video_jobs.user_id | All scheduling tables | Ownership for RLS |
| bulk_job_id | video_jobs.bulk_job_id | content_schedule_items | Optional grouping |
| video_job_id | video_jobs.id | content_schedule_items, schedule_assignments, performance_kpi_events | Asset-level scheduling |
| platform_id | platform_timing_data.id | content_schedule_items, schedule_assignments | Platform-scoped timing |
| status | video_jobs.status | schedule_assignments (derived) | Derived scheduling state |

The data model supports both item-level scheduling (per video_job) and bulk-level groupings (per bulk_job). Scheduling inherits the same idempotency guarantees as video_jobs, ensuring replays and retries remain safe.

![High-level architecture reference for integration points.](/workspace/docs/images/system_architecture.png)

## Platform Timing Data: Model and Canonical Fields

Platform timing data captures three operational levers that scheduling engines use to generate posting windows and guardrails: days of week, peak hours, and posting frequency ranges. Because timing heuristics evolve and vary by geography, audience segment, and format (e.g., Reels vs Feed), the model allows per-platform overrides and audience_segment scoping. Each record carries validity windows and versioning to avoid stale recommendations, and source provenance supports traceability and periodic refresh.

Core fields:
- platform_id: maps to a canonical platform enumeration (youtube, tiktok, instagram, x, linkedin, facebook).
- days: day-of-week constraints or preferences (e.g., Tue–Thu).
- peak_hours: JSONB array of preferred hour windows in 24-hour format (e.g., [{"start": 15, "end": 17}, {"start": 20, "end": 21}]).
- posting_frequency_min/max: numeric guardrails for cadence (e.g., min=3, max=5 posts/week), parameterized by audience_segment and content_format.

Versioning and validity:
- valid_from, valid_to: define effective date range.
- source: provenance tag for auditability.
- notes: free-form operational notes (e.g., “localized to EDT audience”).

Table: Platform timing fields and semantics

| Field | Type | Purpose |
|---|---|---|
| platform_id | UUID (FK-less) | Platform identifier aligned to canonical list |
| days | text[] | Day-of-week constraints/preferences |
| peak_hours | jsonb | Structured hourly ranges used by scheduler |
| posting_frequency_min/max | int | Frequency guardrails per segment/format |
| audience_segment | text | Optional segment label (e.g., “US EDT”, “18–24”) |
| content_format | text | Optional format scoping (e.g., “reels”, “shorts”) |
| valid_from/valid_to | timestamptz | Validity window for timing data |
| source | text | Provenance/reference tag |
| notes | text | Operational notes |

Platform baselines (2025) to seed initial values:
- YouTube: weekday afternoons (3–5 p.m.) with Wednesday 4 p.m. a standout; weekends acceptable later morning to mid‑afternoon; frequency: Shorts daily for small channels, long‑form 2–3/week.[^1][^2]
- TikTok: Wednesday best day; midweek afternoons/evenings; Sunday 8 p.m. notable; frequency: emerging creators 1–4/day, established creators 2–5/week.[^3][^4]
- Instagram: weekday mid‑mornings to mid‑afternoons; Reels: mid‑morning to early afternoon; frequency: 3–5 posts/week baseline on feed; Reels 3–5/week; caution against daily/multiple daily posting.[^5][^6]
- X (Twitter): weekday mornings; Tuesday–Thursday, 8 a.m.–12 p.m. strong; frequency: 2–3 posts/day ceiling for brands; top brands ~4.2 posts/week.[^7][^8]
- LinkedIn: midweek midday windows; frequency: individuals 2–3/week baseline (daily viable with quality); company pages 3–5/week.[^9]
- Facebook: weekdays mid‑morning to mid‑afternoon; frequency: 3–5 posts/week baseline; Reels for discovery; link posts underperform without native context.[^10]

Initial seeding is accomplished through a versioned insert strategy (valid_from only), with active records marked by a partial index WHERE valid_to IS NULL for fast retrieval by schedulers and dashboards.

References for platform timing baselines: YouTube[^1][^2], TikTok[^3][^4], Instagram[^5][^6], X[^7][^8], LinkedIn[^9], Facebook[^10].

## User Scheduling Preferences and Settings: Model and RLS

User preferences allow individuals or organizations to refine platform defaults by timezone, frequency, and blackout windows. The model supports per-platform overrides and audience_segment-specific settings, enabling teams to schedule against geography or demographic cohorts.

Core fields:
- user_id: owner for RLS.
- platform_id: optional; when present, indicates a platform-specific override; when absent, applies as global defaults.
- timezone: IANA timezone string (e.g., “America/New_York”).
- posting_frequency_min/max: user-level guardrails that complement platform timing guardrails.
- days_blacklist: array of days to avoid (e.g., ["sat","sun"]).
- hours_blacklist: JSONB structured blackout windows (e.g., [{"start": 0, "end": 5}]).
- content_format: optional scoping (e.g., “reels”, “shorts”, “thread”).
- quality_threshold: numeric KPI threshold used by optimization loops to gate scale decisions (e.g., minimum watch time or engagement rate).
- metadata: JSONB for flexible settings (e.g., preferred slot density, cadence variance).

Uniqueness prevents duplicate preferences:
- Unique on (user_id, platform_id, content_format) enables separate settings per format, with NULL content_format representing global preferences.

Table: User scheduling preferences fields

| Field | Type | Purpose |
|---|---|---|
| user_id | UUID | Owner for RLS and auditing |
| platform_id | UUID | Optional platform scoping |
| timezone | text | Scheduling timezone |
| posting_frequency_min/max | int | User-level cadence guardrails |
| days_blacklist | text[] | Avoid days |
| hours_blacklist | jsonb | Avoid hours windows |
| content_format | text | Optional format scoping |
| quality_threshold | numeric | KPI gate for optimization |
| metadata | jsonb | Flexible extension space |

RLS policies:
- SELECT/INSERT/UPDATE/DELETE permitted when user_id matches auth.uid().
- service_role bypass for administrative operations.

Table: RLS policy matrix (preferences)

| Operation | Policy |
|---|---|
| SELECT | user_id = auth.uid() |
| INSERT | with check (user_id = auth.uid()) |
| UPDATE | using (user_id = auth.uid() or current_role = 'service_role') |
| DELETE | using (current_role = 'service_role') |

These policies align with existing RLS patterns for bulk_jobs and video_jobs, allowing anon and service_role roles to operate safely in Edge Function contexts.

## Content Calendar and Posting Schedules: Entities and Operations

The content calendar holds scheduled items and their lifecycle. It supports both draft planning and confirmed schedule assignments, with clear linkage to video_jobs (for assets) and platform_timing_data (for timing heuristics). Workflow states mirror bulk/video job semantics and facilitate dashboard rollups and operational monitoring.

Core entities:
- content_calendar: groups scheduled content, optionally linked to a bulk_job.
- content_schedule_items: individual scheduled posts, tied to video_job, platform_id, content_format, and planned time windows.
- schedule_assignments: worker-facing records indicating concrete slots; include derived status and attribution back to video_jobs.
- schedule_exceptions: blackout windows, retries, and manual overrides.

Key fields:
- calendar_id: group container.
- video_job_id: the asset being scheduled.
- platform_id: the target platform.
- content_format: format descriptor (e.g., “reel”, “short”, “thread”, “carousel”).
- planned_start/planned_end: intended posting window.
- timezone: calendar timezone; scheduled_at is stored in UTC.
- status: queued, scheduled, posted, failed, canceled.
- idempotency_key: uniqueness for safe retries.
- created_by/owned_by: user_id ownership.
- dedupe_key: optional business-level deduplication (e.g., content hash).

Status semantics align with established job state machines:
- queued → scheduled (worker commitment) → posted (successful publish) or failed/canceled.
- schedule_assignments.status reflects derived state from publishing attempts.

Table: Content calendar entities and relationships

| Entity | Key fields | Relationships |
|---|---|---|
| content_calendar | id, name, created_by, timezone | Groups schedule items; optional bulk_job_id |
| content_schedule_items | id, calendar_id, video_job_id, platform_id, content_format, planned_start/end, timezone, status | Joins video_jobs (asset), platform_timing_data (timing) |
| schedule_assignments | id, schedule_item_id, worker_id, scheduled_at, status | Derived state; audit timestamps |
| schedule_exceptions | id, schedule_item_id, exception_type, window_start/end, reason | Blackouts, retries, overrides |

Indexes cover common predicates:
- (calendar_id, status)
- (platform_id, status)
- (video_job_id)
- (user_id, created_at) for auditing

Table: Schedule operations and status transitions

| From | To | Trigger |
|---|---|---|
| queued | scheduled | Worker confirms slot |
| scheduled | posted | Publisher success |
| scheduled | failed | Publisher error; record retry metadata |
| scheduled | canceled | Manual or policy cancel |

These tables integrate with bulk_jobs via optional bulk_job_id and inherit user ownership via user_id. Idempotency prevents duplicate scheduling across retries or replays.

## Performance Analytics and Optimization Tracking

Optimization requires two models: per-event KPI captures and experiment trial configurations. The design avoids conflating cost events (job_costs) with engagement metrics, instead providing a clean analytics layer for scheduling decisions and A/B testing.

Core entities:
- performance_kpi_events: per-post event metrics with timestamps and attribution to video_job_id, platform_id, and content_format.
- optimization_trials: configuration and results for A/B tests (e.g., time slots vs formats).
- schedule_recommendations: engine-generated recommendations with confidence scores and references to platform timing data and trial outcomes.

KPI metrics:
- views, impressions, watch_time_seconds, engagement_rate, clicks, saves, shares, comments, followers_delta.
- Timestamps: event_time, ingestion_time.
- Attribution: video_job_id, platform_id, content_format, scheduled_slot_id (optional).

Experiment design:
- trial_id, hypothesis, start/end, variants, primary KPI, guardrails, results summary.
- Integration with platform timing data allows trials to adjust or override defaults during test windows.

Table: Performance KPI schema

| Field | Type | Purpose |
|---|---|---|
| event_id | UUID | Primary key |
| video_job_id | UUID | Asset attribution |
| platform_id | UUID | Platform scope |
| content_format | text | Format attribution |
| event_time | timestamptz | Event timestamp |
| views | int | View count |
| impressions | int | Impression count |
| watch_time_seconds | int | Watch time |
| engagement_rate | numeric | Engagement rate |
| clicks | int | Click count |
| saves | int | Saves |
| shares | int | Shares |
| comments | int | Comments |
| followers_delta | int | Follower change |
| scheduled_slot_id | UUID | Optional slot reference |
| metadata | jsonb | Flexible fields |

Table: Optimization experiments

| Field | Type | Purpose |
|---|---|---|
| trial_id | UUID | Primary key |
| hypothesis | text | Description |
| start_at/end_at | timestamptz | Test window |
| variants | jsonb | A/B cells |
| primary_kpi | text | KPI focus |
| guardrails | jsonb | Quality gates |
| results_summary | jsonb | Outcome summary |

These tables roll up into dashboards and optimization routines without interfering with job_costs. KPI-based feedback loops connect directly to user scheduling preferences (quality_threshold), enabling automated guardrails when performance dips.

## Security Model: RLS Policies and Role-Based Access

RLS is enabled on all scheduling tables. Policies are designed to allow anon and service_role roles to operate in Edge Function flows while preserving isolation by user_id. Owner-only access is enforced for SELECT/INSERT/UPDATE/DELETE on scheduling records, with service_role permitted for administrative operations.

Table: RLS policy summary (scheduling)

| Table | Operation | Policy name | Using / With Check | Roles |
|---|---|---|---|---|
| user_scheduling_preferences | SELECT | Owner select | user_id = auth.uid() | anon, service_role |
| user_scheduling_preferences | INSERT | Owner insert | with check (user_id = auth.uid()) | anon, service_role |
| user_scheduling_preferences | UPDATE | Owner or service | using (user_id = auth.uid() or current_role='service_role') | anon, service_role |
| user_scheduling_preferences | DELETE | Service delete | using (current_role='service_role') | service_role |
| platform_timing_data | SELECT | Owner or service | user_id = auth.uid() or current_role='service_role' | anon, service_role |
| content_calendar | SELECT | Owner select | user_id = auth.uid() | anon, service_role |
| content_schedule_items | SELECT | Owner select | user_id = auth.uid() | anon, service_role |
| schedule_assignments | SELECT | Owner select | user_id = auth.uid() | anon, service_role |
| performance_kpi_events | SELECT | Owner select | user_id = auth.uid() | anon, service_role |
| optimization_trials | SELECT | Owner select | user_id = auth.uid() | anon, service_role |

Auditability:
- created_at, updated_at across entities.
- user_id ownership ensures per-user isolation.

The design matches the established security patterns, enabling Edge Functions to invoke with anon while database writes inside the function use service_role without policy conflicts.

## Indexing Strategy, Query Patterns, and Throughput

Scheduling systems require predictable performance across operational queries (e.g., fetching active schedules) and analytics queries (e.g., KPI rollups). Indexes are tailored to frequent predicates, and partial indexes target active statuses for dashboards and schedulers.

Operational query patterns:
- List active schedule items by platform and calendar.
- Fetch assignments by worker and time window.
- Retrieve KPI events by video_job_id and platform_id for the last N days.
- Sum planned posts per platform per week against frequency guardrails.

Table: Query patterns and index coverage

| Query pattern | Index | Notes |
|---|---|---|
| Active schedule items by platform | idx_sched_items_platform_status (platform_id, status) WHERE status in ('queued','scheduled') | Partial index accelerates active views |
| Schedules by calendar | idx_sched_items_calendar_status (calendar_id, status) | Group and filter calendars |
| Assignments by worker/time | idx_assignments_worker_scheduled (worker_id, scheduled_at) | Worker queueing |
| KPI events by asset | idx_kpi_video_time (video_job_id, event_time) | Analytics and rollups |
| KPI by platform/day | idx_kpi_platform_day (platform_id, date_trunc('day', event_time)) | Time-bucketed reporting |
| Frequency guardrail checks | idx_timing_platform_active (platform_id) WHERE valid_to IS NULL | Active timing retrieval |
| Preference lookups | idx_prefs_user_platform (user_id, coalesce(platform_id,'00000000-0000-0000-0000-000000000000'::uuid)) | Unique constraint supports fast lookup |

Partial indexes for active states:
- schedule_assignments(status) WHERE status IN ('queued','scheduled') to accelerate worker queues.
- platform_timing_data(platform_id) WHERE valid_to IS NULL for current timing.

Idempotency and uniqueness:
- content_schedule_items unique on (user_id, video_job_id, platform_id, scheduled_at).
- schedule_assignments unique on (schedule_item_id, scheduled_at).
- user_scheduling_preferences unique on (user_id, platform_id, content_format).

These strategies align with high-throughput practices in the existing schema and minimize lock contention while preserving referential logic.

## Data Lifecycle: Retention, Archival, and Maintenance

Optimization depends on clean historical data and predictable maintenance windows. The lifecycle defines retention for raw events, archival for cold storage, and routine maintenance for indexes and stats.

Retention and archival:
- performance_kpi_events: retain raw events for 180 days; archive aggregates monthly into summary tables or materialized views.
- optimization_trials: retain configurations and summaries indefinitely; prune variants and detailed logs beyond 365 days.
- schedule_exceptions: retain until after next quarterly review to inform playbooks.

Maintenance:
- Monthly reindexing of active partial indexes.
- Quarterly VACUUM/ANALYZE sweeps on large tables.
- Quarterly review of timing data versions; expire stale records and insert new versions.

Table: Lifecycle policy matrix

| Entity | Retention window | Archival approach | Review cadence |
|---|---|---|---|
| performance_kpi_events | 180 days | Summarize monthly via materialized views | Monthly |
| optimization_trials | Configs: indefinite; logs: 365 days | Compress variants; store summaries | Quarterly |
| schedule_exceptions | Until next quarterly review | Archive with reason taxonomy | Quarterly |
| platform_timing_data | Active-only (valid_to IS NULL) | Versioned inserts; soft-expire old versions | Quarterly |

These policies reflect operational realities in the existing schema and reduce scan costs on hot tables.

## Implementation Roadmap and DDL Specification Order

Implementation proceeds in dependency order to minimize risk and ensure RLS coverage from the start. Naming conventions follow public.* patterns, using UUID primary keys and JSONB for flexible fields.

DDL order:
1. Enable extensions.
2. Create platform_timing_data.
3. Create user_scheduling_preferences.
4. Create content_calendar.
5. Create content_schedule_items.
6. Create schedule_assignments.
7. Create schedule_exceptions.
8. Create performance_kpi_events.
9. Create optimization_trials.
10. Create recommended_schedule_slots (optional utility).
11. Create indexes.
12. Enable RLS and add policies.

![Implementation workflow for schema creation and integration.](/workspace/docs/images/bulk_job_flowchart.png)

Table: DDL build sequence checklist

| Step | Task | Notes |
|---|---|---|
| 1 | Create extensions | pgcrypto, citext |
| 2 | Create platform_timing_data | Versioned timing |
| 3 | Create user_scheduling_preferences | Unique (user_id, platform_id, content_format) |
| 4 | Create content_calendar | Ownership via created_by |
| 5 | Create content_schedule_items | Idempotency, status |
| 6 | Create schedule_assignments | Partial index for active states |
| 7 | Create schedule_exceptions | Blackouts/overrides |
| 8 | Create performance_kpi_events | KPI rollups |
| 9 | Create optimization_trials | A/B testing |
| 10 | Create recommended_schedule_slots | Optional engine output |
| 11 | Create indexes | Operational and analytics |
| 12 | Enable RLS and policies | anon and service_role coverage |

Migration strategy:
- Versioned inserts for timing data with valid_from and source provenance.
- Backfill user_id and ownership fields from associated video_jobs.
- Validate idempotency constraints before enabling write paths.

Validation and rollback:
- Verify RLS using auth.uid() on test users.
- Confirm index usage with EXPLAIN ANALYZE on representative queries.
- Snapshot rollback scripts per table.

## SQL DDL: Core Tables and Policies

```sql
-- Enable required extensions
create extension if not exists pgcrypto;
create extension if not exists citext;

-- Platform timing data (versioned)
create table if not exists public.platform_timing_data (
  id uuid primary key default gen_random_uuid(),
  platform_id uuid not null,
  days text[] not null,
  peak_hours jsonb not null,
  posting_frequency_min int,
  posting_frequency_max int,
  audience_segment text,
  content_format text,
  valid_from timestamptz not null default now(),
  valid_to timestamptz,
  source text,
  notes text,
  user_id uuid, -- optional ownership for scoping; null indicates global defaults
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- User scheduling preferences
create table if not exists public.user_scheduling_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  platform_id uuid,
  timezone text not null,
  posting_frequency_min int,
  posting_frequency_max int,
  days_blacklist text[],
  hours_blacklist jsonb,
  content_format text,
  quality_threshold numeric,
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, coalesce(platform_id, '00000000-0000-0000-0000-000000000000'::uuid), coalesce(content_format, ''))
);

-- Content calendar
create table if not exists public.content_calendar (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  timezone text,
  bulk_job_id uuid, -- optional linkage
  created_by uuid not null,
  owned_by uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Content schedule items
create table if not exists public.content_schedule_items (
  id uuid primary key default gen_random_uuid(),
  calendar_id uuid not null,
  video_job_id uuid not null,
  bulk_job_id uuid, -- optional grouping
  platform_id uuid not null,
  content_format text,
  planned_start timestamptz,
  planned_end timestamptz,
  scheduled_at timestamptz, -- canonical slot (UTC)
  timezone text,
  status text not null check (status in ('queued','scheduled','posted','failed','canceled')),
  idempotency_key text,
  dedupe_key text,
  created_by uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, video_job_id, platform_id, scheduled_at)
);

-- Schedule assignments (worker-facing)
create table if not exists public.schedule_assignments (
  id uuid primary key default gen_random_uuid(),
  schedule_item_id uuid not null,
  worker_id text,
  scheduled_at timestamptz not null,
  status text not null check (status in ('queued','scheduled','posted','failed','canceled')),
  last_error text,
  retry_count int not null default 0 check (retry_count >= 0),
  last_retry_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (schedule_item_id, scheduled_at)
);

-- Schedule exceptions (blackouts, overrides, retries)
create table if not exists public.schedule_exceptions (
  id uuid primary key default gen_random_uuid(),
  schedule_item_id uuid,
  exception_type text not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  reason text,
  created_at timestamptz not null default now()
);

-- Performance KPI events
create table if not exists public.performance_kpi_events (
  id uuid primary key default gen_random_uuid(),
  video_job_id uuid not null,
  platform_id uuid not null,
  content_format text,
  event_time timestamptz not null,
  ingestion_time timestamptz default now(),
  views int,
  impressions int,
  watch_time_seconds int,
  engagement_rate numeric,
  clicks int,
  saves int,
  shares int,
  comments int,
  followers_delta int,
  scheduled_slot_id uuid,
  metadata jsonb,
  created_at timestamptz not null default now()
);

-- Optimization trials
create table if not exists public.optimization_trials (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  trial_id text unique not null,
  hypothesis text not null,
  start_at timestamptz not null,
  end_at timestamptz,
  variants jsonb not null,
  primary_kpi text not null,
  guardrails jsonb,
  results_summary jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Optional utility: recommended schedule slots
create table if not exists public.recommended_schedule_slots (
  id uuid primary key default gen_random_uuid(),
  platform_id uuid not null,
  content_format text,
  slot_start timestamptz not null,
  slot_end timestamptz not null,
  confidence_score numeric,
  trial_id uuid,
  source_timing_id uuid,
  created_at timestamptz not null default now()
);

-- Indexes for operational and analytics queries
create index if not exists idx_sched_items_calendar_status on public.content_schedule_items (calendar_id, status);
create index if not exists idx_sched_items_platform_status on public.content_schedule_items (platform_id, status) where status in ('queued','scheduled');
create index if not exists idx_sched_items_video_job on public.content_schedule_items (video_job_id);
create index if not exists idx_sched_items_user_created on public.content_schedule_items (created_by, created_at desc);

create index if not exists idx_assignments_worker_scheduled on public.schedule_assignments (worker_id, scheduled_at);
create index if not exists idx_assignments_status_active on public.schedule_assignments (status) where status in ('queued','scheduled');

create index if not exists idx_kpi_video_time on public.performance_kpi_events (video_job_id, event_time);
create index if not exists idx_kpi_platform_time on public.performance_kpi_events (platform_id, event_time);
create index if not exists idx_kpi_format_time on public.performance_kpi_events (content_format, event_time);

create index if not exists idx_prefs_user_platform on public.user_scheduling_preferences (user_id, coalesce(platform_id, '00000000-0000-0000-0000-000000000000'::uuid));

create index if not exists idx_timing_platform_active on public.platform_timing_data (platform_id) where valid_to is null;

-- RLS enablement and policies
alter table public.user_scheduling_preferences enable row level security;
alter table public.platform_timing_data enable row level security;
alter table public.content_calendar enable row level security;
alter table public.content_schedule_items enable row level security;
alter table public.schedule_assignments enable row level security;
alter table public.schedule_exceptions enable row level security;
alter table public.performance_kpi_events enable row level security;
alter table public.optimization_trials enable row level security;
alter table public.recommended_schedule_slots enable row level security;

-- user_scheduling_preferences
create policy "prefs_owner_select" on public.user_scheduling_preferences
  for select using (user_id = auth.uid());
create policy "prefs_owner_insert" on public.user_scheduling_preferences
  for insert with check (user_id = auth.uid());
create policy "prefs_owner_or_service_update" on public.user_scheduling_preferences
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "prefs_service_delete" on public.user_scheduling_preferences
  for delete using (current_role = 'service_role');

-- platform_timing_data (owner or service)
create policy "timing_select_owner_or_service" on public.platform_timing_data
  for select using (user_id = auth.uid() or current_role = 'service_role');
create policy "timing_insert_owner" on public.platform_timing_data
  for insert with check (user_id = auth.uid());
create policy "timing_update_owner_or_service" on public.platform_timing_data
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "timing_delete_service" on public.platform_timing_data
  for delete using (current_role = 'service_role');

-- content_calendar
create policy "calendar_owner_select" on public.content_calendar
  for select using (created_by = auth.uid());
create policy "calendar_owner_insert" on public.content_calendar
  for insert with check (created_by = auth.uid());
create policy "calendar_owner_or_service_update" on public.content_calendar
  for update using (created_by = auth.uid() or current_role = 'service_role');
create policy "calendar_service_delete" on public.content_calendar
  for delete using (current_role = 'service_role');

-- content_schedule_items
create policy "sched_items_owner_select" on public.content_schedule_items
  for select using (created_by = auth.uid());
create policy "sched_items_owner_insert" on public.content_schedule_items
  for insert with check (created_by = auth.uid());
create policy "sched_items_owner_or_service_update" on public.content_schedule_items
  for update using (created_by = auth.uid() or current_role = 'service_role');
create policy "sched_items_service_delete" on public.content_schedule_items
  for delete using (current_role = 'service_role');

-- schedule_assignments
create policy "assignments_owner_select" on public.schedule_assignments
  for select using (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.id = schedule_item_id and csi.created_by = auth.uid()
    )
  );
create policy "assignments_owner_or_service_insert" on public.schedule_assignments
  for insert with check (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.id = schedule_item_id and csi.created_by = auth.uid()
    )
  );
create policy "assignments_owner_or_service_update" on public.schedule_assignments
  for update using (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.id = schedule_item_id and csi.created_by = auth.uid()
    )
    or current_role = 'service_role'
  );
create policy "assignments_service_delete" on public.schedule_assignments
  for delete using (current_role = 'service_role');

-- schedule_exceptions
create policy "exceptions_owner_select" on public.schedule_exceptions
  for select using (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.id = schedule_item_id and csi.created_by = auth.uid()
    )
  );
create policy "exceptions_owner_insert" on public.schedule_exceptions
  for insert with check (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.id = schedule_item_id and csi.created_by = auth.uid()
    )
  );
create policy "exceptions_owner_or_service_update" on public.schedule_exceptions
  for update using (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.id = schedule_item_id and csi.created_by = auth.uid()
    )
    or current_role = 'service_role'
  );
create policy "exceptions_service_delete" on public.schedule_exceptions
  for delete using (current_role = 'service_role');

-- performance_kpi_events
create policy "kpi_owner_select" on public.performance_kpi_events
  for select using (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.video_job_id = performance_kpi_events.video_job_id and csi.created_by = auth.uid()
    )
  );
create policy "kpi_owner_insert" on public.performance_kpi_events
  for insert with check (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.video_job_id = performance_kpi_events.video_job_id and csi.created_by = auth.uid()
    )
  );
create policy "kpi_owner_or_service_update" on public.performance_kpi_events
  for update using (
    exists (
      select 1 from public.content_schedule_items csi
      where csi.video_job_id = performance_kpi_events.video_job_id and csi.created_by = auth.uid()
    )
    or current_role = 'service_role'
  );
create policy "kpi_service_delete" on public.performance_kpi_events
  for delete using (current_role = 'service_role');

-- optimization_trials
create policy "trials_owner_select" on public.optimization_trials
  for select using (user_id = auth.uid());
create policy "trials_owner_insert" on public.optimization_trials
  for insert with check (user_id = auth.uid());
create policy "trials_owner_or_service_update" on public.optimization_trials
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "trials_service_delete" on public.optimization_trials
  for delete using (current_role = 'service_role');

-- recommended_schedule_slots
create policy "slots_select_owner_or_service" on public.recommended_schedule_slots
  for select using (current_role = 'service_role' or exists (
    select 1 from public.platform_timing_data ptd
    where ptd.id = source_timing_id and (ptd.user_id = auth.uid() or ptd.user_id is null)
  ));
create policy "slots_insert_owner_or_service" on public.recommended_schedule_slots
  for insert with check (current_role = 'service_role');
create policy "slots_update_owner_or_service" on public.recommended_schedule_slots
  for update using (current_role = 'service_role');
create policy "slots_delete_service" on public.recommended_schedule_slots
  for delete using (current_role = 'service_role');
```

These policies mirror established RLS patterns, allow both anon and service_role, and maintain per-user isolation.

## Appendices: Cross-Platform Timing Baselines and Frequency Guidelines

Cross-platform timing baselines and frequency guidelines for 2025 help seed platform_timing_data and user preferences. All timing is to be localized by audience timezone and validated with account analytics before hard commitments.

Table: Cross-platform timing baseline summary (indicative)

| Platform | Indicative best windows (local time) | Notes |
|---|---|---|
| YouTube | Weekdays 3–5 p.m.; Wednesday 4 p.m. standout; weekends later morning to mid‑afternoon | Shorts timing less critical; prioritize hooks[^1][^2] |
| TikTok | Wednesday best; midweek afternoons/evenings; Sunday 8 p.m. peak | Saturday weakest; localize with follower activity[^3] |
| Instagram | Weekdays 10 a.m.–3 p.m. (Feed); Reels mid‑morning to early afternoon | Reels 3–5/week; caution on daily posting[^5][^6] |
| X (Twitter) | Weekday mornings; Tuesday–Thursday 8 a.m.–12 p.m. | 2–3 posts/day ceiling for brands[^7][^8] |
| LinkedIn | Midweek midday (8 a.m.–2 p.m.) | Individuals 2–3/week baseline; companies 3–5/week[^9] |
| Facebook | Weekdays 8 a.m.–6 p.m.; lighter Fridays | 3–5 posts/week baseline; Reels prioritized[^10] |

Table: Posting frequency guidelines (indicative)

| Platform | Baseline cadence | Upper bound guidance | Caveats |
|---|---|---|---|
| YouTube | Long‑form 2–3/week; Shorts daily (small channels) | Scale only if retention holds | Shorts multiple per day not recommended[^1][^2] |
| TikTok | Emerging 1–4/day; Established 2–5/week | 3–5/week sustainable | Quality gate on volume[^3][^4] |
| Instagram | Feed 3–5/week; Reels 3–5/week | 6–9+ with diminishing returns | Avoid daily/multiple daily as rule[^5][^6] |
| X (Twitter) | 3–5 posts/week for brands | 2–3 posts/day ceiling | Consistency over volume[^7][^8] |
| LinkedIn | Individuals 2–3/week; Companies 3–5/week | Daily posting viable for individuals | Spacing ≥12–24 hours[^9] |
| Facebook | 3–5 posts/week | 1–2 posts/day | Link posts underperform without context[^10] |

Localized validation is essential. Use account analytics to refine windows and guardrails, then version timing records with source provenance and validity windows.

## Information Gaps and Assumptions

Several decisions require further confirmation:
- Platform enumeration and taxonomy: finalize canonical platform_id values and any sub-platform facets.
- Supabase Auth profile mapping: confirm whether organizational scoping (e.g., org_id) is required beyond auth.user_id.
- KPI event schemas: standardize field names and definitions aligned to internal analytics taxonomy.
- Time zone model: decide whether to standardize on UTC storage with IANA tz for display or to store native tz per calendar.
- Retention windows: confirm data governance constraints for performance_kpi_events and optimization_trials.
- Blackout windows: finalize expected formats and policies per platform (e.g., service maintenance or compliance constraints).
- Cost attribution boundary: confirm separation from job_costs to avoid mixing cost line items with engagement metrics.

These gaps are handled through flexible fields (JSONB), versioned timing, and policy stubs, enabling adaptation without schema churn.

## References

[^1]: Buffer. Best Time to Post on YouTube in 2025 (+ Heatmap).  
https://buffer.com/resources/best-time-to-post-on-youtube/

[^2]: SocialPilot. Best Time to Post on YouTube in 2025: Videos and Shorts.  
https://www.socialpilot.co/blog/best-time-to-post-on-youtube

[^3]: Buffer. The Best Time to Post on TikTok in 2025 — New Data.  
https://buffer.com/resources/best-time-to-post-on-tiktok/

[^4]: Hootsuite. How does the TikTok algorithm work in 2025? Tips to boost visibility.  
https://blog.hootsuite.com/tiktok-algorithm/

[^5]: Later. How the Instagram Algorithm Works in 2025 | Ultimate Guide.  
https://later.com/blog/how-instagram-algorithm-works/

[^6]: Buffer. How Often Should You Post on Instagram in 2025? What Data From 2M+ Posts Shows.  
https://buffer.com/resources/how-often-to-post-on-instagram/

[^7]: Buffer. Best Time to Post on Social Media in 2025: Every Platform.  
https://buffer.com/resources/best-time-to-post-social-media/

[^8]: Sprout Social. 45+ Twitter (X) stats to know in marketing in 2025.  
https://sproutsocial.com/insights/twitter-statistics/

[^9]: Sprout Social. Best Times to Post on LinkedIn in 2025 [Updated October 2025].  
https://sproutsocial.com/insights/best-times-to-post-on-linkedin/

[^10]: Sprout Social. Best Times to Post on Facebook in 2025 [Updated October 2025].  
https://sproutsocial.com/insights/best-times-to-post-on-facebook/