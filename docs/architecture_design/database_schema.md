# Supabase Database Schema for Bulk Operations and Batch Job Management

## Executive Summary and Objectives

This report specifies a security-first, scalable database schema for a Supabase/Postgres application that orchestrates bulk operations and batch job processing, with an emphasis on video idea generation and media production. The design centers on two primary entities—Bulk Jobs and Individual Video Jobs—supplemented by cost tracking and optimization, as well as integration with Supabase Auth. The schema balances operational clarity (state machines, progress reporting, and error semantics) with analytics needs (cost rollups and provider-level insights), while ensuring row-level security (RLS) is consistent with Edge Function invocations and service-role operations.

The scope of this document covers the conceptual model, entity definitions, relationships, SQL DDL with indexes and constraints, security policies, and integration patterns for authentication and cost observability. The success criteria are straightforward: enforce secure and correct access via RLS; optimize for high-volume bulk operations and batched job management; provide clear state transitions and progress tracking; and ensure compatibility with Edge Function invocations (outer authentication via anon) and database writes (inner operations potentially using service_role), with policies that allow both roles to perform necessary actions without violating security. The design also acknowledges the minute-gated throughput model of the Google Sheets API, offering strategies for sharding and backoff to sustain steady-state performance.[^1][^2]

Information gaps and assumptions are explicitly called out where they materially affect the design, including the lack of formal foreign key enforcement in the provided guidance, variable Sheets API quotas across projects, and incomplete business rules for cost attribution and optimization. These are handled through pragmatic patterns, observability hooks, and policy controls rather than hard constraints, enabling the system to adapt as business rules and quota realities become clearer.

## Requirements and Constraints

The requirements combine functional and non-functional concerns. Functionally, the system must track bulk jobs sourced from a Google Sheet, manage individual video jobs spawned from the bulk job, and provide cost tracking per job and per provider. Non-functional requirements focus on supporting high-volume operations with predictable performance, clear state transitions, robust error reporting, and strong security and privacy controls.

Operational constraints derive from two sources. First, database design guidance emphasizes avoiding foreign key constraints and instead managing relationships programmatically with indexes and filters. Second, Google Sheets API quotas enforce per-minute budgets that refill every minute, with a recommended request payload size near 2 MB and a 180-second processing timeout per request. BatchUpdate compresses multiple subrequests into one request but remains atomic and ordered; designing for these realities requires sharding workloads and applying backoff when throttled.[^1][^2]

To map requirements to design elements, Table 1 provides a concise overview. It highlights how each requirement translates into specific tables, fields, constraints, and policies. The aim is to ensure traceability from functional needs to concrete schema decisions.

Table 1. Requirement-to-Design Element Mapping

| Requirement | Design Element | Rationale |
|-------------|----------------|-----------|
| Track bulk jobs from a Google Sheet | bulk_jobs table (sheet_id, status, progress, timestamps) | Encapsulates state and provenance from Sheets with progress and timing for throughput analysis |
| Manage individual video jobs | video_jobs table (bulk_job_id, idea_data, status, provider, cost, output_url) | Provides per-idea execution record and cost/output linkage |
| Enforce security | RLS policies on all tables; allow anon and service_role; auth.user_id references | Ensures correct access control, supports Edge Function flows, and preserves auditability |
| Optimize for high-volume operations | Indexes on (bulk_job_id, status), (user_id, created_at), partial indexes for active jobs | Accelerates state queries and reduces scan costs for active workloads |
| Cost tracking and optimization | job_costs table with rollup metrics; provider_config table for rate storage | Enables per-job and provider-level cost analysis and rate plan observability |
| Sheets quota-driven throughput | sheet_work_units and operational playbooks; backoff and payload shaping | Aligns job creation and writes with per-minute quotas and ~2 MB payload guidance[^1][^2] |

## Conceptual Data Model

The conceptual model includes four main entities: Bulk Jobs, Individual Video Jobs, Cost Events, and User Profiles. A fifth entity, Provider Config, captures provider-level rate and feature information for cost attribution and optimization. Relationships are logical, enforced through indexes and programmatic controls rather than foreign key constraints.

Bulk jobs originate from a Google Sheet and carry the spreadsheet ID (sheet_id), status, progress, and timestamps. Individual video jobs belong to a bulk job (bulk_job_id), store the original idea payload (idea_data) in JSONB, track status, ai_provider, cost in numeric form, and an output_url. Cost events record per-jobline-item costs with currency, unit metrics, and timestamps; they can be aggregated for rollups. Provider configurations store ai_provider attributes, including rate metrics and quotas where available. User profiles map directly to Supabase Auth users (auth.user_id), enabling user-based access policies and auditing.

Table 2. Entity Overview

| Entity | Key Attributes | Purpose |
|--------|----------------|---------|
| bulk_jobs | id, sheet_id, status, progress, created_at, completed_at, user_id | Parent object representing a batch sourced from a Google Sheet; tracks state and provenance |
| video_jobs | id, bulk_job_id, idea_data (JSONB), status, ai_provider, cost, output_url, user_id, created_at, updated_at | Child object representing a single video idea execution within a bulk job |
| job_costs | id, video_job_id, cost_type, amount, currency, unit_count, started_at, ended_at, user_id, created_at | Per-job and per-provider cost events for detailed cost tracking and rollups |
| provider_config | id, ai_provider, rate_model, rate_unit, rate_amount, quota_hint, features, user_id, created_at, updated_at | Provider-level configuration and rate plan references for cost attribution |
| profiles | id (UUID, auth user), email, display_name, created_at, updated_at | Application-level profile for user metadata and display; maps to auth.user_id |

The logical relationships reflect one-to-many from bulk jobs to video jobs, and one-to-many from video jobs to cost events. Provider config relates to video jobs via ai_provider for attribution. Profiles join to all job tables via user_id, aligning RLS and auditing. Table 3 summarizes these relationships and join paths.

Table 3. Relationship Summary

| Parent | Child | Join Keys | Notes |
|--------|-------|-----------|-------|
| bulk_jobs | video_jobs | bulk_jobs.id → video_jobs.bulk_job_id | Enforced with indexes; no FK constraint per guidance |
| video_jobs | job_costs | video_jobs.id → job_costs.video_job_id | Cost line items link to jobs for rollups |
| provider_config | video_jobs | provider_config.ai_provider → video_jobs.ai_provider | Attribution based on provider name; no FK constraint |
| profiles | bulk_jobs/video_jobs/job_costs | profiles.id → user_id | RLS and auditing align to auth user |

### Bulk Jobs

Bulk jobs encapsulate the lifecycle of a batch sourced from a Google Sheet. The sheet_id stores the spreadsheet identifier; status captures the current state; progress is a numeric indicator (0–100) to support dashboards; created_at and completed_at provide timing; and user_id ties the job to the initiating user. Additional fields include error messages, a priority level, and idempotency keys to guard against duplicate submissions.

Table 4. Bulk Jobs Fields and Semantics

| Field | Type | Purpose |
|-------|------|---------|
| id | UUID | Primary key |
| sheet_id | Text | Source spreadsheet identifier from Sheets API |
| status | Text | State machine value (e.g., queued, running, paused, completed, failed) |
| progress | Integer (0–100) | Dashboard progress indicator |
| created_at | Timestamp | Creation time |
| completed_at | Timestamp | Completion time (nullable) |
| user_id | UUID | Initiating user (maps to auth.user_id) |
| error_message | Text | Last error for failed/paused states |
| priority | Integer | Scheduling priority (lower number = higher priority) |
| idempotency_key | Text | Ensures only one bulk job per key per user |

### Individual Video Jobs

Individual video jobs represent execution units derived from each idea row in the source sheet. The bulk_job_id links to the parent; idea_data stores the original input payload (for example, the row’s cell values) in JSONB; status tracks the job’s lifecycle; ai_provider identifies the service used; cost is a numeric field for attribution; and output_url holds the produced artifact reference. Timestamps and user_id support auditing and RLS. Retry metadata records attempts and backoff parameters.

Table 5. Video Jobs Fields and Semantics

| Field | Type | Purpose |
|-------|------|---------|
| id | UUID | Primary key |
| bulk_job_id | UUID | Parent bulk job identifier |
| idea_data | JSONB | Original idea payload (e.g., cell range values) |
| status | Text | State machine value (e.g., queued, running, succeeded, failed, canceled) |
| ai_provider | Text | Provider name for cost attribution and policy checks |
| cost | Numeric | Cost incurred for this job (e.g., USD) |
| output_url | Text | Reference to produced media or artifact |
| created_at | Timestamp | Creation time |
| updated_at | Timestamp | Last update time |
| user_id | UUID | Owner for RLS and auditing |
| retry_count | Integer | Number of retries attempted |
| last_retry_at | Timestamp | Timestamp of last retry |
| idempotency_key | Text | Ensures only one job per idea per bulk job per user |

### Cost Tracking and Optimization

Cost tracking is implemented as a line-item event model (job_costs), enabling detailed attribution per provider, per job, and per time window. The schema records cost_type (for example, model inference, render, storage), amount, currency, unit_count (for example, seconds of video, tokens), and timestamps. Aggregation views or materialized views can compute rollups by provider, by bulk job, or by time period. The provider_config table stores provider-level rates and optional quota hints; it supports rate plan comparisons and optimization without enforcing foreign keys.

Table 6. Cost Events Fields and Semantics

| Field | Type | Purpose |
|-------|------|---------|
| id | UUID | Primary key |
| video_job_id | UUID | Link to child job |
| cost_type | Text | Categorization of cost (e.g., inference, render, storage) |
| amount | Numeric | Monetary amount |
| currency | Text (3-char) | Currency code (e.g., USD) |
| unit_count | Numeric | Unit quantity (e.g., seconds, tokens) |
| started_at | Timestamp | Start time for usage window |
| ended_at | Timestamp | End time for usage window |
| user_id | UUID | Owner for RLS and rollups |

Table 7. Provider Configuration Fields and Semantics

| Field | Type | Purpose |
|-------|------|---------|
| id | UUID | Primary key |
| ai_provider | Text | Provider identifier |
| rate_model | Text | Pricing model (e.g., per-second, per-token) |
| rate_unit | Text | Unit of measure (e.g., sec, token) |
| rate_amount | Numeric | Rate per unit |
| quota_hint | Text | Optional quota note (e.g., per-minute limits) |
| features | JSONB | Provider features or constraints |
| user_id | UUID | Owner (if user-specific) |
| created_at | Timestamp | Creation time |
| updated_at | Timestamp | Last update time |

### User Authentication Integration

User integration uses Supabase Auth to anchor user identity, with a profiles table for application-level metadata. RLS policies reference auth.user_id to ensure users can access only their own records. Policies allow both anon and service_role roles to support Edge Function flows while maintaining security. Audit trails are created via created_at and user_id across job and cost tables, and status transitions are recorded via updated_at.

Table 8. User-to-Entity Access Matrix

| Role | Entity | Access | Policy Note |
|------|--------|--------|-------------|
| anon | bulk_jobs, video_jobs, job_costs | SELECT/INSERT where user_id matches auth.user_id | Supports Edge Function invocation; outer auth is anon |
| service_role | bulk_jobs, video_jobs, job_costs | SELECT/INSERT/UPDATE/DELETE | Inner operations may use service_role; policy allows both roles |
| auth user | profiles | SELECT/UPDATE where id matches auth.user_id | User updates only their profile |

## Logical Schema and Relationships (No Foreign Key Constraints)

The schema follows best practices that avoid foreign key constraints, using indexes and programmatic enforcement instead. This approach provides flexibility in high-throughput systems and reduces lock contention. Logical relationships are established by naming conventions and unique indexes, and application logic is responsible for referential integrity.

Table 9. Logical Relationship Map

| Relationship | Enforcement Method | Notes |
|--------------|--------------------|-------|
| video_jobs.bulk_job_id → bulk_jobs.id | Index on (bulk_job_id); application ensures validity | No FK constraint; cascade deletes avoided |
| job_costs.video_job_id → video_jobs.id | Index on (video_job_id); application ensures validity | Enables rollups; soft deletes preferred |
| video_jobs.ai_provider ↔ provider_config.ai_provider | Index on (ai_provider); application ensures mapping | Attribution by name; no FK constraint |
| user_id across tables → profiles.id (auth.user_id) | RLS policies; indexes on (user_id, created_at) | Ensures isolation per user |

Indexes focus on common query predicates, including composite indexes for bulk_job_id plus status, and user_id plus created_at for auditing. Partial indexes target active statuses to accelerate live dashboards.

Table 10. Proposed Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| bulk_jobs | (user_id, created_at DESC) | Fast list for user dashboards |
| bulk_jobs | (status) partial WHERE status IN ('queued','running','paused') | Accelerate active job queries |
| video_jobs | (bulk_job_id, status) | Fast child filtering by parent and state |
| video_jobs | (user_id, created_at DESC) | Fast per-user audit view |
| job_costs | (video_job_id) | Cost rollups per job |
| job_costs | (user_id, created_at DESC) | Cost analytics per user |
| provider_config | (ai_provider) | Provider lookups for attribution |
| provider_config | unique (user_id, ai_provider) | Prevent duplicate rate plans per user |

## SQL DDL: Tables, Indexes, Constraints

The following DDL defines the schema. Types are chosen for clarity and performance: UUID for primary keys, JSONB for idea_data and provider features, numeric for cost fields, and timestamps with timezone for auditability. Uniqueness and check constraints enforce basic integrity without foreign keys.

```sql
-- Enable required extensions
create extension if not exists pgcrypto;
create extension if not exists citext;

-- Profiles: application-level user metadata aligned with auth.user_id
create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  email citext unique,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Bulk jobs sourced from a Google Sheet
create table if not exists public.bulk_jobs (
  id uuid primary key default gen_random_uuid(),
  sheet_id text not null,
  status text not null check (status in ('queued','running','paused','completed','failed')),
  progress int not null default 0 check (progress >= 0 and progress <= 100),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  user_id uuid not null,
  error_message text,
  priority int not null default 5 check (priority >= 0 and priority <= 10),
  idempotency_key text,
  unique (user_id, idempotency_key)
);

-- Individual video jobs within a bulk job
create table if not exists public.video_jobs (
  id uuid primary key default gen_random_uuid(),
  bulk_job_id uuid not null,
  idea_data jsonb not null,
  status text not null check (status in ('queued','running','succeeded','failed','canceled')),
  ai_provider text not null,
  cost numeric(12,2) not null default 0,
  output_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  user_id uuid not null,
  retry_count int not null default 0 check (retry_count >= 0),
  last_retry_at timestamptz,
  idempotency_key text,
  unique (user_id, bulk_job_id, idempotency_key)
);

-- Job cost events (line items) for detailed cost tracking
create table if not exists public.job_costs (
  id uuid primary key default gen_random_uuid(),
  video_job_id uuid not null,
  cost_type text not null,
  amount numeric(12,2) not null,
  currency text not null check (char_length(currency) = 3),
  unit_count numeric(18,4),
  started_at timestamptz,
  ended_at timestamptz,
  user_id uuid not null,
  created_at timestamptz not null default now()
);

-- Provider configuration and rate plans
create table if not exists public.provider_config (
  id uuid primary key default gen_random_uuid(),
  ai_provider text not null,
  rate_model text,
  rate_unit text,
  rate_amount numeric(18,6),
  quota_hint text,
  features jsonb,
  user_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, ai_provider)
);

-- Indexes for common queries and active-state filtering
create index if not exists idx_bulk_jobs_user_created on public.bulk_jobs (user_id, created_at desc);
create index if not exists idx_bulk_jobs_active on public.bulk_jobs (status) where status in ('queued','running','paused');

create index if not exists idx_video_jobs_bulk_status on public.video_jobs (bulk_job_id, status);
create index if not exists idx_video_jobs_user_created on public.video_jobs (user_id, created_at desc);

create index if not exists idx_job_costs_video_job on public.job_costs (video_job_id);
create index if not exists idx_job_costs_user_created on public.job_costs (user_id, created_at desc);

create index if not exists idx_provider_config_provider on public.provider_config (ai_provider);
```

## Security and Row-Level Security (RLS) Policies

RLS is enabled on all tables to enforce access control aligned with Supabase Auth. Policies allow both anon and service_role roles to support Edge Function invocation flows while ensuring data isolation per user. Select policies restrict rows to the authenticated user; insert policies ensure the user_id matches auth.user_id; and update/delete policies either restrict to service_role or require user ownership.

Table 11. RLS Policy Summary

| Table | Operation | Policy Name | Using / With Check | Allowed Roles |
|-------|-----------|-------------|--------------------|---------------|
| profiles | SELECT | Profiles are viewable by owner | id = auth.uid() | anon, service_role |
| profiles | UPDATE | Profiles updatable by owner | id = auth.uid() | anon, service_role |
| bulk_jobs | SELECT | Bulk jobs viewable by owner | user_id = auth.uid() | anon, service_role |
| bulk_jobs | INSERT | Bulk jobs creatable by owner | user_id = auth.uid() | anon, service_role |
| bulk_jobs | UPDATE | Bulk jobs updatable by owner or service_role | user_id = auth.uid() or current_role = 'service_role' | anon, service_role |
| bulk_jobs | DELETE | Bulk jobs deletable by service_role | current_role = 'service_role' | service_role |
| video_jobs | SELECT | Video jobs viewable by owner | user_id = auth.uid() | anon, service_role |
| video_jobs | INSERT | Video jobs creatable by owner | user_id = auth.uid() | anon, service_role |
| video_jobs | UPDATE | Video jobs updatable by owner or service_role | user_id = auth.uid() or current_role = 'service_role' | anon, service_role |
| video_jobs | DELETE | Video jobs deletable by service_role | current_role = 'service_role' | service_role |
| job_costs | SELECT | Costs viewable by owner | user_id = auth.uid() | anon, service_role |
| job_costs | INSERT | Costs creatable by owner | user_id = auth.uid() | anon, service_role |
| job_costs | UPDATE | Costs updatable by service_role | current_role = 'service_role' | service_role |
| job_costs | DELETE | Costs deletable by service_role | current_role = 'service_role' | service_role |
| provider_config | SELECT | Provider config viewable by owner or service_role | user_id = auth.uid() or current_role = 'service_role' | anon, service_role |
| provider_config | INSERT | Provider config creatable by owner | user_id = auth.uid() | anon, service_role |
| provider_config | UPDATE | Provider config updatable by owner or service_role | user_id = auth.uid() or current_role = 'service_role' | anon, service_role |
| provider_config | DELETE | Provider config deletable by service_role | current_role = 'service_role' | service_role |

Example policy SQL (summarized patterns):

```sql
-- Enable RLS
alter table public.profiles enable row level security;
alter table public.bulk_jobs enable row level security;
alter table public.video_jobs enable row level security;
alter table public.job_costs enable row level security;
alter table public.provider_config enable row level security;

-- Profiles
create policy "profiles_select_owner" on public.profiles
  for select using (id = auth.uid());
create policy "profiles_update_owner" on public.profiles
  for update using (id = auth.uid());

-- Bulk jobs
create policy "bulk_jobs_select_owner" on public.bulk_jobs
  for select using (user_id = auth.uid());
create policy "bulk_jobs_insert_owner" on public.bulk_jobs
  for insert with check (user_id = auth.uid());
create policy "bulk_jobs_update_owner_or_service" on public.bulk_jobs
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "bulk_jobs_delete_service" on public.bulk_jobs
  for delete using (current_role = 'service_role');

-- Video jobs
create policy "video_jobs_select_owner" on public.video_jobs
  for select using (user_id = auth.uid());
create policy "video_jobs_insert_owner" on public.video_jobs
  for insert with check (user_id = auth.uid());
create policy "video_jobs_update_owner_or_service" on public.video_jobs
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "video_jobs_delete_service" on public.video_jobs
  for delete using (current_role = 'service_role');

-- Job costs
create policy "job_costs_select_owner" on public.job_costs
  for select using (user_id = auth.uid());
create policy "job_costs_insert_owner" on public.job_costs
  for insert with check (user_id = auth.uid());
create policy "job_costs_update_service" on public.job_costs
  for update using (current_role = 'service_role');
create policy "job_costs_delete_service" on public.job_costs
  for delete using (current_role = 'service_role');

-- Provider config
create policy "provider_config_select_owner_or_service" on public.provider_config
  for select using (user_id = auth.uid() or current_role = 'service_role');
create policy "provider_config_insert_owner" on public.provider_config
  for insert with check (user_id = auth.uid());
create policy "provider_config_update_owner_or_service" on public.provider_config
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "provider_config_delete_service" on public.provider_config
  for delete using (current_role = 'service_role');
```

Operational guidance for avoiding “new row violates row-level security policy” errors: policies should allow both anon and service_role because Edge Functions typically invoke with anon at the outer layer while performing database writes with service_role inside. Allowing both roles prevents authorization mismatches without compromising security.[^3]

## State Machines and Progress Semantics

Bulk jobs and video jobs follow explicit state machines to ensure predictable orchestration. Bulk jobs: queued → running → paused/completed/failed. Video jobs: queued → running → succeeded/failed/canceled. Progress is a numeric value from 0 to 100 for bulk jobs, typically computed as the ratio of succeeded video jobs to total video jobs. Status transitions are recorded via updated_at, and retry behavior is captured in video_jobs.retry_count and last_retry_at.

Table 12. State Transition Tables

| Entity | From | To | Trigger | Side Effects |
|--------|------|----|---------|--------------|
| bulk_job | queued | running | Scheduler picks job | Progress starts at 0 |
| bulk_job | running | paused | User/system pause | Error message set; no new child jobs started |
| bulk_job | running | completed | All child jobs succeeded | completed_at set; progress = 100 |
| bulk_job | running | failed | Irrecoverable error | error_message set; completed_at optional |
| video_job | queued | running | Worker begins | last_retry_at set if initial attempt |
| video_job | running | succeeded | Provider returns success | cost recorded; output_url set |
| video_job | running | failed | Provider error or timeout | retry_count incremented; backoff applied |
| video_job | running | canceled | User/system cancellation | Status finalized; no further retries |

Table 13. Retry and Backoff Metadata

| Field | Purpose |
|-------|---------|
| retry_count | Number of attempts; used to compute next backoff interval |
| last_retry_at | Timestamp of last attempt; helps pace retries |
| idempotency_key | Prevents duplicate jobs across retries |

## Performance, Indexing, and Throughput Planning

Throughput planning aligns to per-minute quotas and operational limits in upstream systems, particularly the Google Sheets API. The database schema is optimized for common query patterns: filtering by status for active jobs, joining children to parents, and listing jobs per user. Indexes described earlier accelerate these paths. Operational strategies such as sharding workloads by user or provider, and pacing job creation to respect minute-gated quotas, are essential to maintain steady performance. When throttling occurs, truncated exponential backoff with jitter should be applied to calls, and batch requests should be kept compact—near the 2 MB payload guidance—to avoid timeouts.[^1][^2]

Table 14. Query Patterns and Index Coverage

| Query Pattern | Covered By | Notes |
|---------------|------------|-------|
| List active bulk jobs for a user | idx_bulk_jobs_user_created; partial idx_bulk_jobs_active | Fast dashboard and scheduler queries |
| Retrieve video jobs by bulk_job_id and status | idx_video_jobs_bulk_status | Efficient child filtering and state counts |
| Aggregate cost by provider over time | idx_job_costs_user_created; rollup views | Supports cost analytics |
| Fetch provider config for attribution | idx_provider_config_provider | Fast provider lookups |

Table 15. Operational Playbook: Quotas to Actions

| Constraint | Signal | Action |
|------------|--------|--------|
| Per-minute request budget | 429 Too Many Requests | Apply truncated exponential backoff with jitter; reduce batch size; pace submissions[^1] |
| ~2 MB payload guidance | Increasing latency or timeouts | Split large batches; compress where possible; scope ranges narrowly[^1] |
| Atomic batch updates | Subrequest failure causes full rollback | Validate subrequests; segment independent changes into separate batches[^2] |
| Scheduler pacing | Frequent “running” → “paused” transitions | Introduce priority queues; stagger job creation; shard by user/provider |

## Cost Tracking and Optimization Model

Cost tracking follows a structured model: job_costs captures line items, provider_config stores rates and features, and aggregation can be implemented via views or materialized views. Optimization levers include comparing provider rates, adjusting unit counts (for example, seconds of video), and shifting workloads to more cost-effective providers when feasible. Policies should ensure only authorized roles can modify cost data (service_role), while users can read their own costs.

Table 16. Cost Aggregation Plan

| Source | Metric | Grouping | Output |
|--------|--------|----------|--------|
| job_costs | amount, unit_count | by ai_provider, by time period | Provider spend dashboard |
| job_costs | amount | by bulk_job_id | Bulk job cost rollup |
| provider_config | rate_amount, rate_unit | by ai_provider | Rate comparison matrix |
| video_jobs | cost | by ai_provider, by status | Efficacy and outcome analysis |

Table 17. Provider Configuration Attributes

| Attribute | Description |
|-----------|-------------|
| rate_model | Pricing schema (e.g., per-second) |
| rate_unit | Unit of measure (e.g., sec) |
| rate_amount | Numeric rate per unit |
| features | Capabilities and constraints (JSONB) |
| quota_hint | Optional guidance (e.g., per-minute limits) |

## Operations: Backoff, Sharding, and Quota-Aware Scheduling

Operationally, the system should shard workloads by user or provider to avoid hot spots and respect per-user quotas. Idempotency keys on bulk_jobs and video_jobs eliminate duplicate work across retries. Monitoring queues and backlog size, and pacing job creation to fit within per-minute budgets, are core practices. When a 429 occurs, apply truncated exponential backoff with jitter to the specific call, cap retries, and reassess batch composition. Atomic batch semantics require careful validation to avoid all-or-nothing failures that waste quota budgets.[^1][^2][^4][^5][^8][^9]

Table 18. Operational Policies and Triggers

| Policy | Trigger | Action |
|--------|---------|--------|
| Retry with backoff | 429 or transient errors | Use exponential backoff with jitter; cap retries and total timeout[^4][^5] |
| Shard workloads | High per-user quota utilization | Split queues by user/provider; reduce contention |
| Validate batches | Frequent atomic rollbacks | Review subrequests; segment independent changes[^2] |
| Monitor quotas | Approaching limits | Alert; reduce batch sizes; request increases if justified[^8][^9] |

## Deliverables and File Output

The SQL DDL and relationships described above are intended to be consolidated as the canonical schema in a single, version-controlled document. The schema file will include table definitions, indexes, constraints, and RLS policy stubs. It will be accompanied by a change log that records migrations, index additions, and policy updates, ensuring repeatability and auditability across deployments.

## Appendices: DDL and Policy Stubs

### Full SQL DDL

```sql
-- Profiles: aligned with auth.user_id
create table if not exists public.profiles (
  id uuid primary key,
  email citext unique,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Bulk jobs
create table if not exists public.bulk_jobs (
  id uuid primary key default gen_random_uuid(),
  sheet_id text not null,
  status text not null check (status in ('queued','running','paused','completed','failed')),
  progress int not null default 0 check (progress >= 0 and progress <= 100),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  user_id uuid not null,
  error_message text,
  priority int not null default 5 check (priority >= 0 and priority <= 10),
  idempotency_key text,
  unique (user_id, idempotency_key)
);

-- Video jobs
create table if not exists public.video_jobs (
  id uuid primary key default gen_random_uuid(),
  bulk_job_id uuid not null,
  idea_data jsonb not null,
  status text not null check (status in ('queued','running','succeeded','failed','canceled')),
  ai_provider text not null,
  cost numeric(12,2) not null default 0,
  output_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  user_id uuid not null,
  retry_count int not null default 0 check (retry_count >= 0),
  last_retry_at timestamptz,
  idempotency_key text,
  unique (user_id, bulk_job_id, idempotency_key)
);

-- Job costs
create table if not exists public.job_costs (
  id uuid primary key default gen_random_uuid(),
  video_job_id uuid not null,
  cost_type text not null,
  amount numeric(12,2) not null,
  currency text not null check (char_length(currency) = 3),
  unit_count numeric(18,4),
  started_at timestamptz,
  ended_at timestamptz,
  user_id uuid not null,
  created_at timestamptz not null default now()
);

-- Provider config
create table if not exists public.provider_config (
  id uuid primary key default gen_random_uuid(),
  ai_provider text not null,
  rate_model text,
  rate_unit text,
  rate_amount numeric(18,6),
  quota_hint text,
  features jsonb,
  user_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, ai_provider)
);

-- Indexes
create index if not exists idx_bulk_jobs_user_created on public.bulk_jobs (user_id, created_at desc);
create index if not exists idx_bulk_jobs_active on public.bulk_jobs (status) where status in ('queued','running','paused');

create index if not exists idx_video_jobs_bulk_status on public.video_jobs (bulk_job_id, status);
create index if not exists idx_video_jobs_user_created on public.video_jobs (user_id, created_at desc);

create index if not exists idx_job_costs_video_job on public.job_costs (video_job_id);
create index if not exists idx_job_costs_user_created on public.job_costs (user_id, created_at desc);

create index if not exists idx_provider_config_provider on public.provider_config (ai_provider);
```

### RLS Policy Stubs (Summary)

```sql
-- Enable RLS
alter table public.profiles enable row level security;
alter table public.bulk_jobs enable row level security;
alter table public.video_jobs enable row level security;
alter table public.job_costs enable row level security;
alter table public.provider_config enable row level security;

-- Profiles
create policy "profiles_select_owner" on public.profiles
  for select using (id = auth.uid());
create policy "profiles_update_owner" on public.profiles
  for update using (id = auth.uid());

-- Bulk jobs
create policy "bulk_jobs_select_owner" on public.bulk_jobs
  for select using (user_id = auth.uid());
create policy "bulk_jobs_insert_owner" on public.bulk_jobs
  for insert with check (user_id = auth.uid());
create policy "bulk_jobs_update_owner_or_service" on public.bulk_jobs
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "bulk_jobs_delete_service" on public.bulk_jobs
  for delete using (current_role = 'service_role');

-- Video jobs
create policy "video_jobs_select_owner" on public.video_jobs
  for select using (user_id = auth.uid());
create policy "video_jobs_insert_owner" on public.video_jobs
  for insert with check (user_id = auth.uid());
create policy "video_jobs_update_owner_or_service" on public.video_jobs
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "video_jobs_delete_service" on public.video_jobs
  for delete using (current_role = 'service_role');

-- Job costs
create policy "job_costs_select_owner" on public.job_costs
  for select using (user_id = auth.uid());
create policy "job_costs_insert_owner" on public.job_costs
  for insert with check (user_id = auth.uid());
create policy "job_costs_update_service" on public.job_costs
  for update using (current_role = 'service_role');
create policy "job_costs_delete_service" on public.job_costs
  for delete using (current_role = 'service_role');

-- Provider config
create policy "provider_config_select_owner_or_service" on public.provider_config
  for select using (user_id = auth.uid() or current_role = 'service_role');
create policy "provider_config_insert_owner" on public.provider_config
  for insert with check (user_id = auth.uid());
create policy "provider_config_update_owner_or_service" on public.provider_config
  for update using (user_id = auth.uid() or current_role = 'service_role');
create policy "provider_config_delete_service" on public.provider_config
  for delete using (current_role = 'service_role');
```

## Information Gaps and Assumptions

Several areas require confirmation or future refinement:

- No explicit foreign key constraints: The current guidance recommends avoiding FKs. If business rules demand strict referential integrity, add FKs with cascade behaviors and assess lock impacts on high-throughput workloads.
- Supabase Auth user profile mapping: The schema assumes a profiles table keyed by auth.user_id; confirm whether additional fields (for example, org_id) are needed for multi-tenant scenarios.
- AI provider catalog and rate models: provider_config includes generic fields; finalize the provider list and rate structures before production rollout.
- Currency handling and cost attribution: Clarify multi-currency scenarios, rounding rules, and conversion strategies; consider separate tables for exchange rates if needed.
- Google Sheets API quota values: Representative per-minute numbers are indicative; confirm official quotas in the Cloud Console for the target project and use them to calibrate throughput and backoff parameters.[^1][^6]
- Media storage strategy: The output_url is a text reference; finalize the storage backend and access policies, and align with Edge Function capabilities for uploads if necessary.
- Job prioritization and SLAs: The priority field is included; define scheduling policies and service-level objectives (for example, maximum latency per status transition).
- Error code taxonomy: error_message is free text; consider adding an error_code field for structured diagnostics and routing to appropriate recovery playbooks.
- Retry limits and backoff parameters: Establish policy defaults (initial delay, multiplier, max delay, max retries) and instrument backoff telemetry.[^4][^5]

## References

[^1]: Usage limits | Google Sheets. https://developers.google.com/workspace/sheets/api/limits  
[^2]: Batch requests | Google Sheets. https://developers.google.com/workspace/sheets/api/guides/batch  
[^3]: Retry — google-api-core (Python) documentation. https://googleapis.dev/python/google-api-core/latest/retry.html  
[^4]: Class ExponentialBackOff | Google HTTP Client Java Library. https://cloud.google.com/java/docs/reference/google-http-client/latest/com.google.api.client.util.ExponentialBackOff  
[^5]: Google Sheets API Essential Guide | Rollout. https://rollout.com/integration-guides/google-sheets/api-essentials  
[^6]: View and manage quotas | Google Cloud Documentation. https://docs.cloud.google.com/docs/quotas/view-manage  
[^7]: Google Sheets API Limits: What It Is and How to Avoid It | Stateful. https://stateful.com/blog/google-sheets-api-limits  
[^8]: Is it possible to increase the Google Sheets API quota limit beyond 2500 per account? | Stack Overflow. https://stackoverflow.com/questions/52266726/is-it-possible-to-increase-the-google-sheets-api-quota-limit-beyond-2500-per-acc  
[^9]: How to handle Quota exceeded error 429 in Google Sheets when inserting data through Apps Script? | Stack Overflow. https://stackoverflow.com/questions/67278848/how-to-handle-quota-exceeded-error-429-in-google-sheets-when-inserting-data-thro