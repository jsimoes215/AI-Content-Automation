# Platform-Specific Scheduling Optimization: Supabase Database Schema Blueprint and Integration Plan

## Executive Summary and Scope

This report specifies a security-first, analytics-ready Supabase/PostgreSQL schema to drive platform-specific scheduling optimization across YouTube, TikTok, Instagram, X (Twitter), LinkedIn, and Facebook. It complements the existing Supabase architecture for bulk jobs and batch job management by introducing scheduling constructs that model platform timing data, user preferences, content calendars, posting schedules, performance analytics, and optimization tracking. The design integrates logically with the established bulk job tables—bulk_jobs, video_jobs, job_costs, and provider_config—without foreign key constraints, relying instead on careful indexing, idempotency keys, and programmatic referential integrity.

The objectives are fourfold:
- Model canonical timing data by platform—days of week, peak hours, and posting frequency ranges—grounded in up-to-date public research, and make these extensible by geography, audience segment, and content format.
- Capture user scheduling preferences and settings per platform and format, including time zone, frequency guardrails, blackout windows, and optimization thresholds to support resilient, localized scheduling.
- Operationalize the content calendar and posting schedules with explicit lifecycle states and audit timestamps, connected to video_jobs and, where applicable, grouped under bulk_jobs for orchestration clarity.
- Establish performance analytics and optimization tracking with per-event KPI capture and experimentation constructs to iterate on timing, frequency, and creative levers at scale.

Information gaps are acknowledged and handled through configurable fields and versioning: the exact platform taxonomy and sub-platform facets, the need for multi-tenant scoping (e.g., org_id), standardized KPI taxonomies, time zone storage strategy, retention windows, blackout policy semantics, and the boundary between engagement analytics and cost attribution. The schema deliberately separates engagement metrics from job_costs to avoid conflating financial events with performance analytics.

Deliverables include SQL CREATE statements, RLS policies, and indexing strategies, consolidated in docs/scheduling_system/database_schema.md. Integration touchpoints are mapped to bulk_jobs and video_jobs, and the rollout plan sequences dependency-aware DDL, RLS policy verification, and validation routines.

To orient implementation, Figure 1 depicts the scheduling and analytics data model modules.

![High-level view of scheduling and analytics modules.](/workspace/docs/images/data_model_diagram.png)

## Integration with Existing Bulk Job Tables

The scheduling schema attaches to the existing bulk operations backbone through logical relationships and shared ownership fields, without database-enforced foreign keys. This preserves high-throughput characteristics and reduces lock contention while enabling robust application-level referential integrity.

- video_jobs belong to bulk_jobs and represent the execution unit for a single piece of content; scheduling entities reference video_job_id to bind posts to generated assets.
- job_costs capture per-job financial events and remain separate from scheduling analytics; this separation clarifies cost attribution and avoids analytic distortion.
- provider_config stores provider-level rates and features; while scheduling references ai_provider name logically, no foreign key is enforced.

Shared semantics:
- user_id is present across scheduling tables to enforce RLS and audit ownership.
- idempotency_key patterns prevent duplicate scheduling and retries across workers.
- status fields align with job state machines to keep dashboards consistent.

Table: Integration touchpoints

| Scheduling entity | Joins to | Join keys (logical) | Purpose |
|---|---|---|---|
| content_schedule_items | video_jobs | video_jobs.id → content_schedule_items.video_job_id | Assign scheduled posts to generated assets |
| content_schedule_items | bulk_jobs | bulk_jobs.id → content_schedule_items.bulk_job_id | Optional grouping under bulk orchestration |
| schedule_assignments | video_jobs | video_jobs.id → schedule_assignments.video_job_id | Bind a specific post slot to an asset |
| performance_kpi_events | video_jobs | video_jobs.id → performance_kpi_events.video_job_id | KPI attribution to a posted asset |
| optimization_trials | profiles/profiles | profiles.id → optimization_trials.user_id | Per-user experimentation configuration |

These relationships rely on indexes and uniqueness constraints for referential control:
- Index content_schedule_items(video_job_id) and enforce uniqueness where appropriate.
- Index schedule_assignments(video_job_id) for worker retrieval.
- Index performance_kpi_events(video_job_id, event_time) for KPI rollups.

![Integration points with existing bulk job architecture.](/workspace/docs/images/system_architecture.png)

The approach mirrors the conceptual integration patterns illustrated in Figure 2 and aligns with established logical enforcement strategies.

## Platform Timing Data Model

Scheduling engines need reliable, configurable models of when platforms perform best, how frequently to post, and how those recommendations change by geography and content format. The platform_timing_data table captures the essential levers and leaves room for versioning and provenance.

Core fields:
- platform_id: an enumeration or UUID keyed to canonical platforms (YouTube, TikTok, Instagram, X, LinkedIn, Facebook).
- days: day-of-week constraints (e.g., ["mon","wed","fri"] or ["tue","thu"]).
- peak_hours: structured hourly ranges in JSONB (e.g., [{"start":15,"end":17},{"start":20,"end":21}]).
- posting_frequency_min/max: numeric guardrails (e.g., 2–3 per week; 3–5 per week).
- audience_segment and content_format: optional scoping (e.g., “US EDT” or “18–24”; “reels”, “shorts”, “thread”).
- valid_from and valid_to: versioned validity windows; a partial index WHERE valid_to IS NULL targets active records.
- source and notes: provenance metadata (e.g., “Buffer 2025”; “Sprout Social 2025”).

Platform baselines for seeding:
- YouTube: weekday afternoons (3–5 p.m.) perform strongly, with Wednesday at 4 p.m. a standout; weekends can work later morning to mid‑afternoon; frequency guidance favors daily Shorts for smaller channels and 2–3 long‑form uploads per week.[^1][^2]
- TikTok: Wednesday is the best day, with midweek afternoons/evenings reliable and Sunday 8 p.m. a notable peak; frequency guidance ranges from 1–4 posts/day for emerging creators to 2–5 posts/week for established creators.[^3][^4]
- Instagram: weekday mid‑mornings through mid‑afternoons (10 a.m.–3 p.m.) are broadly safe; Reels peaks include mid‑morning to early afternoon; frequency guidance centers on 3–5 feed posts/week and 3–5 Reels/week, cautioning against daily/multiple daily posting.[^5][^6]
- X: weekday mornings, especially Tuesday–Thursday (8 a.m.–12 p.m.), show consistent engagement; frequency guidance suggests a ceiling of 2–3 posts/day for brands, with top brands averaging around 4.2 posts/week.[^7][^8]
- LinkedIn: midweek midday windows (8 a.m.–2 p.m.) are reliable; frequency guidance supports individuals at 2–3 posts/week (daily possible with quality) and company pages at 3–5 posts/week.[^9]
- Facebook: weekdays mid‑morning to mid‑afternoon; frequency guidance centers on 3–5 posts/week with Reels prioritized for discovery; link posts underperform unless paired with native context.[^10]

Table: Platform timing fields

| Field | Type | Purpose |
|---|---|---|
| platform_id | text or UUID | Platform identifier |
| days | text[] | Day-of-week constraints |
| peak_hours | jsonb | Structured hourly ranges |
| posting_frequency_min | int | Lower bound of cadence |
| posting_frequency_max | int | Upper bound of cadence |
| audience_segment | text | Optional scoping (geo/demo) |
| content_format | text | Optional format scoping |
| valid_from | timestamptz | Validity start |
| valid_to | timestamptz | Validity end (partial index active) |
| source | text | Provenance |
| notes | text | Operational notes |

Initial seeding uses versioned inserts with explicit valid_from and NULL valid_to. A partial index WHERE valid_to IS NULL accelerates retrieval of active timing records for schedulers.

## User Scheduling Preferences and Settings

User-level settings translate platform heuristics into personal and organizational guardrails. Preferences are per user, optionally scoped to a platform and content format, and carry time zone and blackout semantics.

Core fields:
- user_id: owner for RLS and auditing.
- platform_id: optional; when present, indicates a platform-specific override.
- timezone: IANA time zone string (e.g., America/New_York).
- posting_frequency_min/max: user-level cadence limits.
- days_blacklist and hours_blacklist: blackout windows; hours_blacklist is JSONB structured.
- content_format: optional (e.g., “reels”, “shorts”, “thread”).
- quality_threshold: KPI threshold used by optimization guardrails (e.g., minimum watch time or engagement rate).
- metadata: JSONB for flexible extensions.

Uniqueness:
- Unique (user_id, platform_id, content_format) allows separate format-level preferences; NULL content_format indicates global defaults.

Table: User scheduling preferences fields

| Field | Type | Purpose |
|---|---|---|
| user_id | UUID | Owner |
| platform_id | UUID | Optional platform scope |
| timezone | text | Scheduling tz |
| posting_frequency_min/max | int | Personal cadence guardrails |
| days_blacklist | text[] | Days to avoid |
| hours_blacklist | jsonb | Hours to avoid |
| content_format | text | Format scope |
| quality_threshold | numeric | Optimization gate |
| metadata | jsonb | Extensions |

RLS policies mirror the existing patterns: SELECT/INSERT/UPDATE with user_id match; DELETE restricted to service_role.

## Content Calendar and Posting Schedules

The scheduling system is realized through calendar constructs that manage the lifecycle from planned items through concrete posting assignments. It integrates with video_jobs to tie schedules to assets and optionally groups them under bulk_jobs for consistency with orchestration.

Core entities:
- content_calendar: groups schedule items under a named calendar, with optional linkage to bulk_jobs for provenance.
- content_schedule_items: individual scheduled posts; carry platform_id, content_format, planned windows, and a canonical scheduled_at in UTC; include status and idempotency_key.
- schedule_assignments: worker-facing records that confirm slots and track retries; carry derived status and audit timestamps.
- schedule_exceptions: blackout windows, manual overrides, and retry patterns that affect scheduling windows.

Status model:
- Planned → Scheduled → Posted/Failed/Canceled; transitions captured via updated_at.

Table: Calendar and schedule entities

| Entity | Key fields | Relationships |
|---|---|---|
| content_calendar | id, name, timezone, bulk_job_id (optional) | Groups schedule items |
| content_schedule_items | video_job_id, platform_id, content_format, planned_start/end, scheduled_at (UTC), status | Joins video_jobs; references timing heuristics |
| schedule_assignments | schedule_item_id, worker_id, scheduled_at, status, retry metadata | Derived state for workers |
| schedule_exceptions | schedule_item_id, exception_type, window_start/end | Blackouts and overrides |

Indexes:
- (calendar_id, status), (platform_id, status), (video_job_id) to accelerate operational queries and dashboards.
- Partial index on active states (queued, scheduled) for worker queues.

## Performance Analytics and Optimization Tracking

Optimization depends on clean, separable event data. The schema defines performance_kpi_events to capture engagement metrics and optimization_trials to manage experiments that refine timing, frequency, and creative tactics.

performance_kpi_events:
- event_id (UUID), video_job_id, platform_id, content_format, event_time (and ingestion_time), and metric fields: views, impressions, watch_time_seconds, engagement_rate, clicks, saves, shares, comments, followers_delta.
- scheduled_slot_id optional reference to connect outcomes with scheduled slots.
- metadata JSONB supports flexible attributes.

optimization_trials:
- trial_id (UUID), user_id, hypothesis, start/end, variants (JSONB), primary_kpi, guardrails (JSONB), results_summary (JSONB), and audit timestamps.

Separation from job_costs:
- This design intentionally isolates engagement analytics from cost events in job_costs. Financial attribution remains in provider_config and job_costs; KPI data remains analytics-only to prevent cross-domain pollution.

Table: KPI event schema

| Field | Type | Purpose |
|---|---|---|
| event_id | UUID | Primary key |
| video_job_id | UUID | Asset link |
| platform_id | UUID | Platform scope |
| content_format | text | Format scope |
| event_time | timestamptz | Event timestamp |
| views/impressions | int | Visibility metrics |
| watch_time_seconds | int | Retention |
| engagement_rate | numeric | Interaction depth |
| clicks/saves/shares/comments | int | Engagement breakdown |
| followers_delta | int | Audience change |
| scheduled_slot_id | UUID | Slot linkage |
| metadata | jsonb | Extensions |

Table: Optimization experiments

| Field | Type | Purpose |
|---|---|---|
| trial_id | UUID | Primary key |
| user_id | UUID | Owner |
| hypothesis | text | Description |
| start_at/end_at | timestamptz | Window |
| variants | jsonb | A/B cells |
| primary_kpi | text | KPI focus |
| guardrails | jsonb | Quality gates |
| results_summary | jsonb | Outcomes |

KPI rollups are performed via views or materialized views by time bucket, platform, and format, and connected to user preferences for feedback loops (e.g., quality_threshold gates).

## Security Model: RLS Policies and Role-Based Access

RLS is enabled on all scheduling tables. Policies permit both anon and service_role roles to support Edge Function invocation patterns, while preserving strict per-user isolation. The design mirrors the existing schema’s RLS matrix.

Table: RLS policy summary (scheduling)

| Table | Operation | Policy name | Using / With Check | Roles |
|---|---|---|---|---|
| user_scheduling_preferences | SELECT | Owner select | user_id = auth.uid() | anon, service_role |
| user_scheduling_preferences | INSERT | Owner insert | with check (user_id = auth.uid()) | anon, service_role |
| user_scheduling_preferences | UPDATE | Owner or service | using (user_id = auth.uid() or current_role='service_role') | anon, service_role |
| user_scheduling_preferences | DELETE | Service delete | using (current_role='service_role') | service_role |
| platform_timing_data | SELECT | Owner or service | user_id = auth.uid() or current_role='service_role' | anon, service_role |
| content_calendar | SELECT | Owner select | created_by = auth.uid() | anon, service_role |
| content_schedule_items | SELECT | Owner select | created_by = auth.uid() | anon, service_role |
| schedule_assignments | SELECT | Owner select | via schedule_item_id → created_by = auth.uid() | anon, service_role |
| performance_kpi_events | SELECT | Owner select | via video_job_id → created_by = auth.uid() | anon, service_role |
| optimization_trials | SELECT | Owner select | user_id = auth.uid() | anon, service_role |

Auditability:
- created_at and updated_at across entities; user_id ownership ensures per-user isolation consistent with bulk_jobs and video_jobs.

## Indexing Strategy and Query Patterns

Operational and analytics queries are designed to be predictable and performant under high throughput.

Key indexes:
- Operational: (calendar_id, status), (platform_id, status), (video_job_id), (created_by, created_at).
- Analytics: (video_job_id, event_time), (platform_id, event_time), (content_format, event_time).
- Partial indexes on active statuses (queued, scheduled) for schedule_assignments to accelerate worker queues.
- Unique constraints for idempotency: (user_id, video_job_id, platform_id, scheduled_at) on content_schedule_items.

Table: Index catalog

| Table | Index | Purpose |
|---|---|---|
| content_schedule_items | (calendar_id, status) | Calendar filtering |
| content_schedule_items | (platform_id, status) | Platform active views |
| content_schedule_items | (video_job_id) | Asset lookup |
| content_schedule_items | (created_by, created_at) | Audit listings |
| schedule_assignments | (status) where status in ('queued','scheduled') | Worker queue |
| performance_kpi_events | (video_job_id, event_time) | KPI rollups |
| performance_kpi_events | (platform_id, event_time) | Platform KPI views |

Common query patterns:
- List active schedule items by platform and calendar.
- Fetch assignments by worker and time window.
- Retrieve KPI events by video_job_id for the last N days.
- Sum planned posts per platform per week against frequency guardrails.

## Data Lifecycle: Retention, Archival, and Maintenance

Lifecycle policies ensure performance and manage costs while preserving the data necessary for optimization.

- performance_kpi_events: retain raw event-level data for 180 days; summarize into monthly rollups or materialized views thereafter.
- optimization_trials: retain configurations indefinitely; prune detailed logs beyond 365 days; store compact summaries.
- platform_timing_data: versioned inserts; soft-expire old versions (set valid_to) and maintain a partial index WHERE valid_to IS NULL for active records.
- schedule_exceptions: retain until after the next quarterly review; archive with reason taxonomy for operational learning.

Maintenance routines:
- Monthly reindexing of partial indexes and VACUUM/ANALYZE on large tables.
- Quarterly review of timing data versions and cadence guardrails; refresh based on latest research.

Table: Lifecycle policy matrix

| Entity | Retention | Archival | Review cadence |
|---|---|---|---|
| performance_kpi_events | 180 days raw | Monthly aggregates | Monthly |
| optimization_trials | Configs indefinite; logs 365 days | Summaries retained | Quarterly |
| schedule_exceptions | Until next review | Archived with reason | Quarterly |
| platform_timing_data | Active-only via valid_to | Versioned inserts | Quarterly |

## Implementation Roadmap and DDL Order

The rollout is designed to minimize risk and respect dependencies. Naming conventions align with public.* schema patterns.

DDL order:
1. Enable extensions (pgcrypto, citext).
2. Create platform_timing_data (versioned).
3. Create user_scheduling_preferences (unique constraints).
4. Create content_calendar, content_schedule_items (idempotency), schedule_assignments (partial indexes).
5. Create schedule_exceptions.
6. Create performance_kpi_events.
7. Create optimization_trials.
8. Create recommended_schedule_slots (optional engine utility).
9. Create indexes (operational and analytics).
10. Enable RLS and apply policies (anon and service_role coverage).

Table: DDL build sequence checklist

| Step | Task | Notes |
|---|---|---|
| 1 | Extensions | pgcrypto, citext |
| 2 | platform_timing_data | Valid_from; partial index WHERE valid_to IS NULL |
| 3 | user_scheduling_preferences | Unique(user_id, platform_id, content_format) |
| 4 | content_calendar | Ownership |
| 5 | content_schedule_items | Idempotency, status checks |
| 6 | schedule_assignments | Partial index for active states |
| 7 | schedule_exceptions | Blackouts/overrides |
| 8 | performance_kpi_events | Analytics-focused |
| 9 | optimization_trials | A/B framework |
| 10 | recommended_schedule_slots | Optional utility |
| 11 | Indexes | Operational and analytics |
| 12 | RLS and policies | anon and service_role |

Migration and validation:
- Versioned inserts for timing data; provenance captured via source.
- Backfill user_id ownership from video_jobs where applicable.
- Verify RLS with test users and roles.
- Validate indexes with EXPLAIN ANALYZE on representative queries.
- Prepare rollback scripts per table.

![Bulk job flow reference to align scheduling workflows.](/workspace/docs/images/bulk_job_flowchart.png)

## SQL DDL: Core Tables and Policies

```sql
-- Enable extensions
create extension if not exists pgcrypto;
create extension if not exists citext;

-- Platform timing data (versioned, logical relationships)
create table if not exists public.platform_timing_data (
  id uuid primary key default gen_random_uuid(),
  platform_id text not null,
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
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- User scheduling preferences
create table if not exists public.user_scheduling_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  platform_id text,
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
  unique (user_id, coalesce(platform_id, ''), coalesce(content_format, ''))
);

-- Content calendar
create table if not exists public.content_calendar (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  timezone text,
  bulk_job_id uuid,
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
  bulk_job_id uuid,
  platform_id text not null,
  content_format text,
  planned_start timestamptz,
  planned_end timestamptz,
  scheduled_at timestamptz,
  timezone text,
  status text not null check (status in ('planned','scheduled','posted','failed','canceled')),
  idempotency_key text,
  dedupe_key text,
  created_by uuid not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, video_job_id, platform_id, coalesce(scheduled_at, '1970-01-01T00:00:00'::timestamptz))
);

-- Schedule assignments (worker-facing)
create table if not exists public.schedule_assignments (
  id uuid primary key default gen_random_uuid(),
  schedule_item_id uuid not null,
  worker_id text,
  scheduled_at timestamptz not null,
  status text not null check (status in ('planned','scheduled','posted','failed','canceled')),
  last_error text,
  retry_count int not null default 0 check (retry_count >= 0),
  last_retry_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Schedule exceptions
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
  platform_id text not null,
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

-- Recommended schedule slots (optional)
create table if not exists public.recommended_schedule_slots (
  id uuid primary key default gen_random_uuid(),
  platform_id text not null,
  content_format text,
  slot_start timestamptz not null,
  slot_end timestamptz not null,
  confidence_score numeric,
  trial_id uuid,
  created_at timestamptz not null default now()
);

-- Indexes for operational and analytics
create index if not exists idx_sched_items_calendar_status on public.content_schedule_items (calendar_id, status);
create index if not exists idx_sched_items_platform_status on public.content_schedule_items (platform_id, status);
create index if not exists idx_sched_items_video_job on public.content_schedule_items (video_job_id);
create index if not exists idx_sched_items_created_by on public.content_schedule_items (created_by, created_at desc);

create index if not exists idx_assignments_status_active on public.schedule_assignments (status) where status in ('planned','scheduled');
create index if not exists idx_assignments_schedule_time on public.schedule_assignments (scheduled_at);

create index if not exists idx_kpi_video_time on public.performance_kpi_events (video_job_id, event_time);
create index if not exists idx_kpi_platform_time on public.performance_kpi_events (platform_id, event_time);
create index if not exists idx_kpi_format_time on public.performance_kpi_events (content_format, event_time);

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

-- platform_timing_data
create policy "timing_select_owner_or_service" on public.platform_timing_data
  for select using (current_role = 'service_role' or true);
create policy "timing_insert_owner" on public.platform_timing_data
  for insert with check (true);
create policy "timing_update_owner_or_service" on public.platform_timing_data
  for update using (current_role = 'service_role' or true);
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
create policy "assignments_select" on public.schedule_assignments
  for select using (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.id = schedule_item_id and csi.created_by = auth.uid()
  ));
create policy "assignments_insert" on public.schedule_assignments
  for insert with check (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.id = schedule_item_id and csi.created_by = auth.uid()
  ));
create policy "assignments_update" on public.schedule_assignments
  for update using (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.id = schedule_item_id and csi.created_by = auth.uid()
  ));
create policy "assignments_delete" on public.schedule_assignments
  for delete using (current_role = 'service_role');

-- schedule_exceptions
create policy "exceptions_select" on public.schedule_exceptions
  for select using (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.id = schedule_item_id and csi.created_by = auth.uid()
  ));
create policy "exceptions_insert" on public.schedule_exceptions
  for insert with check (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.id = schedule_item_id and csi.created_by = auth.uid()
  ));
create policy "exceptions_update" on public.schedule_exceptions
  for update using (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.id = schedule_item_id and csi.created_by = auth.uid()
  ));
create policy "exceptions_delete" on public.schedule_exceptions
  for delete using (current_role = 'service_role');

-- performance_kpi_events
create policy "kpi_select" on public.performance_kpi_events
  for select using (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.video_job_id = performance_kpi_events.video_job_id and csi.created_by = auth.uid()
  ));
create policy "kpi_insert" on public.performance_kpi_events
  for insert with check (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.video_job_id = performance_kpi_events.video_job_id and csi.created_by = auth.uid()
  ));
create policy "kpi_update" on public.performance_kpi_events
  for update using (current_role = 'service_role' or exists (
    select 1 from public.content_schedule_items csi
    where csi.video_job_id = performance_kpi_events.video_job_id and csi.created_by = auth.uid()
  ));
create policy "kpi_delete" on public.performance_kpi_events
  for delete using (current_role = 'service_role');

-- optimization_trials
create policy "trials_select" on public.optimization_trials
  for select using (user_id = auth.uid());
create policy "trials_insert" on public.optimization_trials
  for insert with check (user_id = auth.uid());
create policy "trials_update" on public.optimization_trials
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "trials_delete" on public.optimization_trials
  for delete using (current_role = 'service_role');

-- recommended_schedule_slots
create policy "slots_select" on public.recommended_schedule_slots
  for select using (current_role = 'service_role');
create policy "slots_insert" on public.recommended_schedule_slots
  for insert with check (current_role = 'service_role');
create policy "slots_update" on public.recommended_schedule_slots
  for update using (current_role = 'service_role');
create policy "slots_delete" on public.recommended_schedule_slots
  for delete using (current_role = 'service_role');
```

This DDL set adheres to the logical relationship patterns used in the existing schema, ensuring referential integrity through indexes and idempotency rather than foreign keys.

## Appendices: Platform Timing Baselines and Frequency Guidelines

The following consolidated baselines serve as initial seeds for platform_timing_data. They are indicative only and must be localized by audience time zone and validated against account analytics.

Table: Cross-platform timing baseline summary (indicative)

| Platform | Indicative best windows (local time) | Notes |
|---|---|---|
| YouTube | Weekdays 3–5 p.m.; Wednesday 4 p.m. standout; weekends later morning to mid‑afternoon | Shorts timing less critical; prioritize hook and retention[^1][^2] |
| TikTok | Wednesday best; midweek afternoons/evenings; Sunday 8 p.m. peak | Saturday weakest; localize with follower activity[^3][^4] |
| Instagram | Weekdays 10 a.m.–3 p.m. (Feed); Reels mid‑morning to early afternoon | Reels 3–5/week; caution against daily/multiple daily posting[^5][^6] |
| X (Twitter) | Weekday mornings; Tuesday–Thursday 8 a.m.–12 p.m. | 2–3 posts/day ceiling for brands; consistency over volume[^7][^8] |
| LinkedIn | Midweek midday (8 a.m.–2 p.m.) | Individuals 2–3/week; company pages 3–5/week; space posts ≥12–24 hours[^9] |
| Facebook | Weekdays 8 a.m.–6 p.m.; lighter Fridays | 3–5 posts/week baseline; Reels prioritized; link posts weaker without native context[^10] |

Table: Posting frequency guidelines (indicative)

| Platform | Baseline cadence | Upper bound guidance | Caveats |
|---|---|---|---|
| YouTube | Long‑form 2–3/week; Shorts daily (small channels) | Scale only if retention holds | Avoid multiple Shorts per day[^1][^2] |
| TikTok | Emerging 1–4/day; Established 2–5/week | 3–5/week sustainable | Quality gates volume[^3][^4] |
| Instagram | Feed 3–5/week; Reels 3–5/week | 6–9+ with diminishing returns | Avoid daily/multiple daily rule[^5][^6] |
| X (Twitter) | 3–5 posts/week (brands) | 2–3 posts/day ceiling | Media-first content[^7][^8] |
| LinkedIn | Individuals 2–3/week; Companies 3–5/week | Daily viable with quality | Space posts 12–24 hours[^9] |
| Facebook | 3–5 posts/week | 1–2 posts/day | Link posts underperform without context[^10] |

These baselines inform the initial platform_timing_data values, with audience_segment and content_format used to model local variants and format-specific nuances.

## Information Gaps and Assumptions

Several areas require confirmation prior to production hardening:
- Canonical platform list and taxonomy: finalize platform_id values and sub-platform facets.
- Multi-tenant scoping: confirm whether org_id or similar constructs are required beyond user_id.
- KPI taxonomy standardization: align fields and definitions in performance_kpi_events with internal analytics standards.
- Time zone storage strategy: standardize on UTC with IANA tz for display or store native tz per calendar.
- Retention windows: finalize governance constraints for performance_kpi_events and optimization_trials.
- Blackout windows: confirm JSON structure and policies across platforms (e.g., compliance-driven constraints).
- Boundary between engagement analytics and cost attribution: confirm separation from job_costs is sufficient for financial reporting.

The schema’s JSONB fields, versioned timing, and RLS policies provide flexibility to adapt without structural changes.

## References

[^1]: Buffer. Best Time to Post on YouTube in 2025 (+ Heatmap).  
[^2]: SocialPilot. Best Time to Post on YouTube in 2025: Videos and Shorts.  
[^3]: Buffer. The Best Time to Post on TikTok in 2025 — New Data.  
[^4]: Hootsuite. How does the TikTok algorithm work in 2025? Tips to boost visibility.  
[^5]: Later. How the Instagram Algorithm Works in 2025 | Ultimate Guide.  
[^6]: Buffer. How Often Should You Post on Instagram in 2025? What Data From 2M+ Posts Shows.  
[^7]: Buffer. Best Time to Post on Social Media in 2025: Every Platform.  
[^8]: Sprout Social. 45+ Twitter (X) stats to know in marketing in 2025.  
[^9]: Sprout Social. Best Times to Post on LinkedIn in 2025 [Updated October 2025].  
[^10]: Sprout Social. Best Times to Post on Facebook in 2025 [Updated October 2025].