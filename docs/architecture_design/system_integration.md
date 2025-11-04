# AI Content Automation: Integration Architecture with Batch Video Generation and Supabase

## Executive Summary

This report outlines a technical integration plan to extend the existing AI Content Automation system with batch video generation capabilities, migrate the data layer from a local SQLite database to a managed PostgreSQL database using Supabase, integrate Supabase Auth for secure multi-user access, and evolve the frontend with React components for batch control and monitoring. The objective is to preserve full backward compatibility with the current single-video workflow while introducing reliable multi-job orchestration, observability, and multi-tenant security.

The existing system comprises a React single-page application, a FastAPI backend, a content library, analytics and feedback modules, and an end-to-end pipeline that converts topics into multi-platform videos. A local SQLite database and file system currently persist projects, scripts, scenes, generated content, jobs, performance metrics, and analytics. Building on this foundation, the proposed integration introduces:

- A batch-aware job orchestration layer that schedules, prioritizes, and tracks many generation jobs in parallel.
- A database evolution from SQLite to Supabase (PostgreSQL) with a JSONB-first schema, partitioning strategies for high-volume tables, and RLS (Row-Level Security) for tenant isolation.
- Supabase Auth integrated into the React and FastAPI stacks, with secure session handling, middleware guards, and signed URL support for assets.
- A refined frontend featuring batch creation, a live queue, progress tracking, and retry/pause controls, designed for accessibility and responsiveness.
- Backward-compatible endpoints and UI flows that ensure current single-video users and automations experience no regressions.

Key outcomes include resilient batch processing, deeper operational visibility, improved multi-tenant security, and a maintainable path to scale. Success will be measured by end-to-end job reliability, progress fidelity, reduced manual effort, higher content throughput, and robust isolation guarantees across tenants. The plan references the existing repository for system context and the documented production interface for deployment anchor points.[^1][^2]

## Current System Overview and Context

The current system’s end-to-end workflow starts with projects and topics, generates scripts, synthesizes audio, composes video scenes, and performs platform-specific adaptations for channels such as YouTube, TikTok, Instagram, and others. A content library stores reusable scenes with tagging, and analytics capture performance metrics and insights. The React UI includes Dashboard, Projects, ProjectDetail, ContentLibrary, and Analytics pages. The existing pipeline factory orchestrates stages, and WebSocket or polling mechanisms provide progress updates to the frontend. SQLite is used for local persistence, and a file-based asset store organizes generated media.

This baseline is production-ready and accessible via a documented web interface. It already supports multi-platform content and features a content library with meta-tagging for reuse. These capabilities form the foundation for more advanced batch workflows and managed database operations.[^1][^2]

To illustrate the mapping of current frontend views to backend responsibilities and data models, Table 1 summarizes the principal components and their interactions.

### Table 1. Current Frontend Pages vs Backend Responsibilities vs Data Models

| Frontend View         | Primary User Actions                                | Backend Modules Involved                            | Key Data Models                               |
|-----------------------|-----------------------------------------------------|-----------------------------------------------------|-----------------------------------------------|
| Dashboard             | Overview of recent activity, quick start            | Analytics API, main pipeline                        | projects, analytics                           |
| Projects              | Create, list, filter projects                       | Projects API, job creation                          | projects, generation_jobs                     |
| ProjectDetail         | Inspect project details, track progress             | Pipeline factory, job status APIs                   | scripts, scenes, generated_content, generation_jobs |
| ContentLibrary        | Browse and search reusable scenes                   | Content library manager                             | content_library, scenes                       |
| Analytics             | View performance metrics and trends                 | Performance analytics                               | performance_metrics, analytics                |

The data flow aligns with the current schema: projects feed scripts, scripts produce scenes, and generated content references scenes. Performance metrics link to generated content, and analytics aggregate project-level insights. The proposed batch architecture leverages and extends these relationships.[^1]

### Data Model Highlights

The current schema includes projects, generation_jobs, scripts, scenes, generated_content, content_library, performance_metrics, and analytics. These entities and their indices support fast lookups by project, job status, and content platform. JSONTEXT fields are used to store flexible metadata, content, and platform-specific variants. Foreign key constraints and cascading deletes preserve referential integrity.

The following summary in Table 2 captures the principal tables, keys, and relationships that the batch integration will build upon.

### Table 2. Core Tables, Primary Keys, Foreign Keys, and Relationship Summary

| Table                  | Primary Key | Key Foreign References             | Relationship Summary                                                                 |
|------------------------|-------------|------------------------------------|--------------------------------------------------------------------------------------|
| projects               | id          | —                                  | Owns scripts, scenes, analytics, and jobs                                            |
| scripts                | id          | project_id → projects              | Generated from projects; parent to scenes                                            |
| scenes                 | id          | script_id → scripts                | Compose videos; parent to generated_content                                          |
| generated_content      | id          | scene_id → scenes                  | Stores video/audio/thumbnail/subtitle assets with platform and quality metadata     |
| content_library        | id          | scene_id → scenes                  | Reusable scene catalog with tags, usage stats, performance                          |
| performance_metrics    | id          | content_id → generated_content     | Engagement metrics per platform                                                      |
| generation_jobs        | id          | project_id → projects              | Tracks async job status, progress, and results                                      |
| analytics              | id          | project_id → projects              | Aggregated project-level performance                                                 |

### Pipeline Factory and Stages

The pipeline factory provides a modular sequence from script to audio to video to platform adaptation. The current orchestration supports real-time status updates, either through WebSockets or polling, and maintains progress across stages. The batch integration requires richer orchestration primitives—queues, priorities, retries, and cross-job dependencies—while keeping the stage semantics intact.[^1]

### Gaps and Constraints for Multi-Job Workloads

Operating multiple jobs concurrently exposes several constraints:

- Job scheduling and prioritization are not explicitly defined; parallel execution may compete for resources without clear limits.
- Progress tracking must scale across many jobs and provide per-stage granularity to support informative UI displays.
- File organization and concurrent write safety require more structure to prevent path collisions and partial reads.
- Database write contention and index scan efficiency need attention when many jobs update status and write artifacts in bursts.
- Observability is limited beyond basic job status; system operators need per-stage timing, error aggregation, and throughput metrics.
- Storage scaling, particularly for large video assets, needs a strategy for durable, access-controlled distribution.

These gaps inform the extension proposals in the next section.

## Integration Objectives and Requirements

The integration has four primary objectives:

1. Enable batch video generation with a robust job queue, resource-aware scheduling, and resilient progress tracking.
2. Evolve the database from SQLite to Supabase (PostgreSQL) with a JSONB-first schema, RLS-based multi-tenant security, and partitioning for high-volume tables.
3. Integrate Supabase Auth for secure user sessions, token validation, and per-tenant access control across UI, API, and storage.
4. Maintain full backward compatibility with the existing single-video generation flow, ensuring no breaking changes to endpoints or user experience.

The non-functional requirements include horizontal scalability for batch throughput, secure multi-tenant access, and high observability for job lifecycle events. Success criteria include >99% job completion reliability for batches of 50+, a maximum UI progress staleness window of a few seconds, and secure, audited access to tenant-scoped resources. These objectives align with the existing repository and deployment context.[^1][^2]

## Pipeline Architecture: Extending to Batch Video Generation

The batch pipeline extends the current orchestration by introducing a dedicated orchestrator service and per-stage workers. The orchestrator manages job intake, validates project ownership and parameters, creates job records, schedules stage tasks, and tracks progress. Stage-specific workers consume tasks, execute them, and report updates. This structure allows independent scaling per stage and isolates failures.

A message queue mediates between the orchestrator and workers, supporting prioritization, retries with exponential backoff, and rate-limited concurrency per project or tenant. The system avoids re-running duplicate work by memoizing intermediate artifacts per scene and using content-addressed storage identifiers. The content library feeds reusable scenes into the batch pipeline to accelerate generation and maintain quality.

Table 3 proposes a stage-task mapping that aligns batch job types with the existing workflow.

### Table 3. Stage-to-Task Mapping and Required Inputs/Outputs

| Stage                  | Task Type                    | Inputs                                           | Outputs                                           |
|------------------------|------------------------------|--------------------------------------------------|---------------------------------------------------|
| Script generation      | script_generation            | Project metadata, topic                          | scripts.content (JSON), metrics, timings          |
| Audio synthesis        | audio_generation             | Scene voiceover text                             | Audio files, duration, quality_score              |
| Video composition      | video_generation             | Audio, visual descriptions, scene timing         | Video files, resolution, format                   |
| Platform adaptation    | platform_adaptation          | Base video, platform constraints                  | Platform-specific variants and metadata           |
| Post-processing        | subtitle/thumbnail generation| Video, style rules                                | Subtitles, thumbnails, packaging                  |

### Job Orchestration and Queueing Model

The orchestrator implements a FIFO queue with priority lanes for premium tenants or urgent projects. Each project can define concurrency caps to prevent resource starvation. The system supports cross-job dependencies—for example, platform adaptation waits until base video generation completes for a scene—while allowing independent scenes to run in parallel. Idempotency keys on scene content prevent redundant work when retries occur.

### Progress Tracking and Event Streaming

Per-job and per-stage progress events are published to a real-time channel. The frontend subscribes to project-specific streams and updates the batch queue and job cards with minimal latency. Event payloads include job_id, project_id, stage, status, current_step, progress percentage, error codes, and timestamps. This design supports both detailed per-scene tracking and a high-level batch summary.

### Failure Handling and Retries

Failures are classified as retriable (transient AI service errors, temporary storage failures) or terminal (invalid inputs, permission errors). Retriable errors trigger exponential backoff with jitter. After max retries, jobs move to a failed state with actionable error messages and suggested next steps. Dead-letter queues capture failed tasks for operator review and replay once root causes are addressed.

### Storage and Asset Management

Assets are organized by tenant, project, and job, with a deterministic path scheme to prevent collisions. Large video files are durably stored and accessed via signed URLs to enforce access control. Shared caches (e.g., audio synthesis for repeated scenes) reduce compute by referencing immutable artifacts. The library retains reusable scenes with versioned metadata and performance scores to guide reuse.

## Database Migration and Schema Evolution (SQLite → Supabase Postgres)

The migration adopts a JSONB-first schema in PostgreSQL, preserving the current entity relationships while enabling flexible metadata queries, full-text search, and efficient indexing. RLS policies enforce tenant isolation at the row level, ensuring users only see and manipulate their own data. High-volume tables such as generated_content, performance_metrics, and generation_jobs are partitioned by time or project to maintain write throughput and query performance. The migration process includes schema generation, data export/transform/load (ETL), index creation, and a rolling cutover with rollbacks if needed.

RLS is a core control plane, mapping session claims (tenant and user identifiers) to row access predicates across projects, jobs, and assets. This strategy is designed for scale and aligns with Supabase’s multi-tenant recommendations.[^3]

### Table 4. SQLite-to-Postgres Field Mapping and Type Conversions

| SQLite Field                         | Postgres Column             | Type                  | Notes                                                                 |
|-------------------------------------|-----------------------------|-----------------------|-----------------------------------------------------------------------|
| projects.id                         | projects.id                 | UUID                  | Use UUID primary keys                                                 |
| projects.metadata (JSONTEXT)        | projects.metadata           | JSONB                 | Default {}; index GIN for common keys                                 |
| scripts.content (JSONTEXT)          | scripts.content             | JSONB                 | Retain structure; add tsvector for search                             |
| scenes.platform_specific (JSONTEXT) | scenes.platform_specific    | JSONB                 | Per-platform variant storage                                          |
| generated_content.generation_metadata (JSONTEXT) | generated_content.generation_metadata | JSONB | Capture AI tool versions, prompts, quality scores                    |
| generation_jobs.result_data (JSONTEXT) | generation_jobs.result_data | JSONB               | Store stage outputs and metrics                                       |
| performance_metrics.*               | performance_metrics.*       | Numeric/INTEGER       | Retain constraints; add partitioning by month                         |
| analytics.metrics_data (JSONTEXT)   | analytics.metrics_data      | JSONB                 | Store extra KPIs                                                      |

### Table 5. Proposed RLS Policies by Table

| Table                | Policy Name                  | USING Clause (Conceptual)                            | Notes                                                        |
|----------------------|------------------------------|------------------------------------------------------|--------------------------------------------------------------|
| projects             | tenant_isolation             | auth.jwt() -> tenant_id = projects.tenant_id         | All CRUD restricted to tenant                                |
| scripts              | project_access               | EXISTS projects p WHERE p.id = scripts.project_id AND p.tenant_id = auth.jwt().tenant_id | Access via project ownership                                 |
| scenes               | script_access                | EXISTS scripts s WHERE s.id = scenes.script_id AND s.project_id IN (SELECT id FROM projects WHERE tenant_id = auth.jwt().tenant_id) | Cascaded access through scripts and projects                 |
| generated_content    | scene_access                 | EXISTS scenes s WHERE s.id = generated_content.scene_id AND s.script_id IN (SELECT id FROM scripts WHERE project_id IN (SELECT id FROM projects WHERE tenant_id = auth.jwt().tenant_id)) | Tenant isolation via scenes and projects                     |
| performance_metrics  | content_access               | EXISTS generated_content gc WHERE gc.id = performance_metrics.content_id AND gc.scene_id IN (SELECT id FROM scenes WHERE script_id IN (SELECT id FROM scripts WHERE project_id IN (SELECT id FROM projects WHERE tenant_id = auth.jwt().tenant_id))) | Read-only for analytics users; write via service role        |
| generation_jobs      | project_access               | EXISTS projects p WHERE p.id = generation_jobs.project_id AND p.tenant_id = auth.jwt().tenant_id | Job visibility scoped to tenant projects                     |
| content_library      | tenant_or_public             | scene_id IN (SELECT id FROM scenes WHERE script_id IN (SELECT id FROM scripts WHERE project_id IN (SELECT id FROM projects WHERE tenant_id = auth.jwt().tenant_id))) OR library_category = 'public' | Optional public catalog; controlled by tenant                |
| analytics            | project_access               | EXISTS projects p WHERE p.id = analytics.project_id AND p.tenant_id = auth.jwt().tenant_id | Aggregation readable to tenant                               |

### Schema Design and Data Types

The migration adopts UUIDs for all primary keys, consistent with managed database best practices. JSONB stores flexible metadata, with GIN indices on common keys for fast filtering (e.g., tags, platforms, status). Foreign key constraints cascade deletes appropriately. Where full-text search is required—such as searching scripts and scene descriptions—tsvector columns accompany JSONB fields. Check constraints preserve domain integrity for fields like script_type, scene_type, and platform.

### Table 6. JSONB Keys and Suggested GIN Indices

| Table                | JSONB Field                   | Keys to Index                            | Purpose                                      |
|----------------------|-------------------------------|-------------------------------------------|----------------------------------------------|
| projects             | metadata                      | status, tone, created_at                  | Quick filters and dashboards                 |
| scripts              | content                       | title, topics, summary                    | Search and reuse                             |
| scenes               | platform_specific             | platform, aspect_ratio, constraints       | Variant selection                            |
| generated_content    | generation_metadata           | voice_id, model_version, quality_score    | Traceability and quality filters             |
| generation_jobs      | result_data                   | stage_outputs, performance summary        | Observability and debugging                  |
| content_library      | specific_tags, generic_tags   | tags[]                                    | Tag-based retrieval                          |
| performance_metrics  | derived_metrics (JSONB)       | engagement_breakdown                      | Advanced analytics                           |
| analytics            | metrics_data                  | extra_kpis                                | Custom KPI tracking                          |

### Migration Strategy

The migration proceeds through incremental steps to minimize risk and ensure reversibility. A parallel-read strategy allows both databases to serve reads during validation, while a rolling cutover moves write traffic once checks pass. Backups and snapshots are created at each stage.

### Table 7. Migration Steps, Preconditions, and Validation Checks

| Step                          | Description                                   | Preconditions                         | Validation Check                                      |
|-------------------------------|-----------------------------------------------|---------------------------------------|-------------------------------------------------------|
| 1. Schema generation          | Create Postgres schema with RLS               | Supabase project provisioned          | DDL diff verified; no FK violations                   |
| 2. Baseline ETL               | Export SQLite, transform, load to Postgres    | Stable SQLite snapshot                 | Row counts match; sample reads return correct records |
| 3. Index and constraints      | Create indices, checks, triggers              | ETL complete                           | Query plans show index usage; constraints enforced    |
| 4. Parallel reads             | Read from both DBs; reconcile results         | App configured for dual reads          | No drift in critical queries                          |
| 5. Cutover to Postgres        | Switch writes; retain SQLite as fallback      | Stakeholder approval                   | Write success rate; error rate below threshold        |
| 6. Rollback window            | Monitor; revert if critical issues arise      | Cutover completed                      | Defined rollback decision point; data integrity       |

## Frontend Integration Plan (React)

The frontend evolves to support batch creation, monitoring, and control while preserving the current single-video flow. New components include BatchCreateForm, BatchQueue, BatchJobCard, StageProgressBar, RetryDialog, and PauseControl. State management uses React Query for data fetching and caching, and WebSocket subscriptions for live updates. Accessibility and internationalization align with existing component conventions and pages (Dashboard, Projects, ProjectDetail, ContentLibrary, Analytics).[^1]

### Table 8. Component Responsibilities, Props, and Event Handlers

| Component         | Responsibilities                                  | Key Props                               | Event Handlers                                  |
|-------------------|---------------------------------------------------|-----------------------------------------|-------------------------------------------------|
| BatchCreateForm   | Collect batch parameters, validate, submit        | defaultProjectId, onSubmit              | handleSubmit                                    |
| BatchQueue        | Show ordered jobs, filters, pagination            | jobs[], filters, page, pageSize         | onFilterChange, onPageChange                    |
| BatchJobCard      | Display job summary, actions (pause/resume/retry) | job, liveStatus                         | onPause, onResume, onRetry                      |
| StageProgressBar  | Render per-stage progress with accessibility      | stages[], progressMap                   | onExpandDetails                                 |
| RetryDialog       | Confirm retry with options                        | jobId, lastError                        | onConfirmRetry, onCancel                        |
| PauseControl      | Toggle job pausing                                | jobId, isPaused                         | onTogglePause                                   |
| ErrorBoundary     | Catch and display errors                          | fallback UI                             | —                                               |

### Table 9. UI Pages vs New Components and Data Flow

| Page            | New Components                   | Data Flow Summary                                      |
|-----------------|----------------------------------|--------------------------------------------------------|
| Dashboard       | BatchQueue, ErrorBoundary        | Live job stream; summary KPIs                          |
| Projects        | BatchCreateForm                  | Create batches tied to projects                        |
| ProjectDetail   | BatchJobCard, StageProgressBar   | Job and stage-level progress; control actions          |
| ContentLibrary  | ReusePanel in Batch context      | Tag-based scene selection for batch reuse              |
| Analytics       | BatchAnalyticsView               | Filter batch jobs; per-stage timings and outcomes      |

### Batch UI and Interaction Design

The batch creation form gathers topics, platform selections, concurrency settings, and reuse preferences from the content library. The batch queue supports filtering by status, project, and date range, with pagination for large sets. Job cards present progress by stage, actionable buttons, and error summaries. RetryDialogs offer targeted retries at the job or stage level. The design provides clear keyboard navigation, ARIA attributes for progress bars, and consistent iconography.

### State Management and Real-Time Updates

React Query handles fetching and caching of jobs, projects, and analytics. A WebSocket client connects to project-specific channels and updates local state for live progress. When connectivity drops, the app falls back to polling at conservative intervals, preserving UX continuity.

## Authentication Flow with Supabase Auth

Supabase Auth provides sign-in, sign-up, and session management, with email/password and OAuth as options. The frontend retrieves session tokens and supplies them with API requests. The backend validates tokens and enforces RLS at the database level, ensuring users only access tenant-scoped data. Edge cases such as token refresh, logout, and multi-device sessions are handled gracefully. Storage access for large assets uses signed URLs, and project ownership governs which users can create or control jobs in a project.[^3][^4]

### Table 10. Auth Flows, Endpoints, Token Types, and Frontend Callbacks

| Flow              | Frontend Actions                         | Backend Endpoints                    | Token Type           | Callbacks and Effects                                  |
|-------------------|------------------------------------------|--------------------------------------|----------------------|--------------------------------------------------------|
| Sign-up           | Create user, tenant                      | POST /auth/signup                    | JWT (access, refresh)| Store session; redirect to Dashboard                   |
| Sign-in           | Email/password or OAuth                  | POST /auth/signin                    | JWT (access, refresh)| Persist session; subscribe to project streams          |
| Token refresh     | On expiry or before critical calls       | POST /auth/refresh                   | JWT (refresh)        | Update access token; retry pending requests            |
| Sign-out          | Invalidate session                       | POST /auth/signout                   | —                    | Clear session; close streams                           |
| File access       | Request signed URL for asset             | GET /assets/signed-url               | JWT (access)         | Download asset; revoke URL after use                   |

### Table 11. Protected Endpoints and Required Scopes/Claims

| Endpoint Group         | Examples                                        | Required Claims (Conceptual)                |
|------------------------|--------------------------------------------------|---------------------------------------------|
| Projects CRUD          | POST /projects, GET /projects/:id               | tenant_id, user_id                          |
| Batch operations       | POST /batches, GET /batches, POST /batches/:id/actions | tenant_id, project_role                     |
| Jobs lifecycle         | GET /jobs, POST /jobs/:retry, POST /jobs/:pause | tenant_id, project_role                     |
| Content library        | GET /library, POST /library/items               | tenant_id or public catalog access          |
| Analytics              | GET /analytics, GET /projects/:id/analytics     | tenant_id, analytics_scope                  |
| Assets                 | GET /assets/signed-url                          | tenant_id, project access                   |

### Session Handling and API Security

Tokens are stored securely, with HttpOnly cookies or secure storage mechanisms. Axios interceptors attach tokens to outbound requests and handle 401 responses by refreshing tokens and retrying once. Backend middleware validates JWTs and enforces RLS policies. Cross-origin requests respect configured allowed origins and use secure cookie attributes. Caching is disabled for sensitive endpoints to prevent data leakage.

## Backward Compatibility and Migration Strategy

Existing single-video generation flows remain unchanged, with the same endpoints and UI paths. A legacy mode preserves local SQLite behavior for users who have not opted into the batch or cloud features. Compatibility shims map old request/response formats to new job types when users select batch parameters. The rollout plan includes feature flags, canary cohorts, telemetry-based monitoring, and documentation updates. A rollback path exists at the feature flag and database levels.

### Table 12. Endpoint Compatibility Matrix

| Endpoint                    | Old Behavior                          | New Behavior (Batch-Aware)                 | Migration Notes                                |
|-----------------------------|---------------------------------------|--------------------------------------------|------------------------------------------------|
| POST /projects              | Create project                        | Same; metadata optionally includes batch opts | No change required; new fields ignored        |
| POST /jobs                  | Create single video job               | Create job (single or batch)                | Add job_type; default single                   |
| GET /jobs/:id               | Job status for single video           | Status for any job type                     | Same schema; more granular stage progress      |
| POST /jobs/:id/retry        | Retry last failed job                 | Retry job or specific stage                 | Add optional stage parameter                   |
| GET /projects/:id           | Project details                       | Include batch summary and queue metrics     | Backward compatible fields added               |
| GET /analytics              | Aggregated analytics                  | Batch-filtered analytics                    | Add filter params; default to existing scope   |

## Operational Concerns: Observability, Scaling, and Quality

Observability spans structured logs, metrics, and traces across the pipeline, with per-stage latency reporting and job throughput dashboards. Scaling uses horizontal stage workers and partitioning to maintain performance as batch sizes grow. Storage scales with durable media storage and CDN-backed distribution via signed URLs. Data quality relies on checks for content integrity, audit trails, and a library curation process that tags high-performance scenes. Disaster recovery is supported by backups, snapshots, and a tested recovery runbook.

### Table 13. Key Metrics, SLO Targets, and Alert Thresholds

| Metric                                   | Description                                 | SLO Target                     | Alert Threshold                          |
|------------------------------------------|---------------------------------------------|--------------------------------|------------------------------------------|
| Job completion rate                       | % of jobs reaching completed                | ≥ 99% for batches ≤ 100        | < 98% over rolling hour                  |
| Stage latency (p95)                       | 95th percentile time per stage              | ≤ defined per stage budget     | > 20% above budget for 3 consecutive periods |
| Progress staleness                        | Max UI lag behind worker status             | ≤ 3 seconds                    | ≥ 10 seconds                             |
| Error rate (retriable)                    | % of retriable failures before success      | ≤ 5%                           | ≥ 10%                                    |
| Storage write success                     | % of successful asset writes                | ≥ 99.9%                        | < 99.5%                                  |
| RLS policy enforcement                    | Unauthorized access attempts                | 0                              | ≥ 1 attempt per hour                     |

## Implementation Roadmap and Work Breakdown

The roadmap is phased to deliver value early while managing risk. Dependencies include Supabase provisioning, storage configuration, and environment readiness. Milestones feature end-to-end tests and dry runs before public rollout.

### Table 14. Phases, Tasks, Owners, Dependencies, and Acceptance Criteria

| Phase | Task                                      | Owner         | Dependencies                         | Acceptance Criteria                                    |
|-------|-------------------------------------------|---------------|--------------------------------------|--------------------------------------------------------|
| 1     | Design batch orchestrator                 | Backend Lead  | Queue service                        | Orchestrator MVP handles job intake and scheduling     |
| 1     | Define job types and stage tasks          | Product + Eng | Current pipeline factory             | Documented mapping; approved by stakeholders           |
| 2     | Implement DB migration                    | Data Eng      | Supabase project                     | ETL complete; row counts match; indices created        |
| 2     | Add RLS policies                          | Data Eng      | Migration complete                    | RLS tests pass; no unauthorized access                 |
| 3     | Integrate Supabase Auth in frontend       | Frontend Lead | Auth provider configured              | Sign-up/sign-in flows verified                         |
| 3     | Backend auth middleware and guards        | Backend Lead  | JWT validation setup                  | Protected endpoints enforce claims                     |
| 4     | Build batch UI components                 | Frontend Eng  | Real-time channel                     | BatchCreateForm, BatchQueue, JobCard functional        |
| 4     | Implement real-time progress streaming    | Full-stack    | WebSocket or polling                  | UI updates within staleness SLO                        |
| 5     | Add retry/pause flows and error handling  | Frontend + Backend | Orchestrator backoff policies      | RetryDialog and PauseControl operational               |
| 5     | Observability dashboards                  | SRE           | Metrics and logs                      | SLO dashboards live; alerts configured                 |
| 6     | Documentation and training                | PM + Eng      | All features stable                   | Guides published; support processes established        |
| 6     | Production rollout                        | PM + SRE      | Feature flags, canary cohorts         | No critical incidents in canary; decision gate passed  |

## Appendices

### A. Proposed Postgres Schema Excerpts

The following DDL excerpts illustrate core tables, JSONB fields, and indexing strategies. Names and constraints are representative and should be refined during implementation.

```sql
-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  original_idea TEXT NOT NULL,
  target_audience TEXT,
  tone TEXT CHECK (tone IN ('professional','casual','educational','entertaining','motivational')),
  status TEXT CHECK (status IN ('draft','processing','completed','published','archived')) DEFAULT 'draft',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_tenant ON projects(tenant_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_metadata ON projects USING GIN (metadata);

-- Scripts
CREATE TABLE scripts (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  content JSONB NOT NULL,
  total_duration INTEGER DEFAULT 0,
  word_count INTEGER DEFAULT 0,
  script_type TEXT CHECK (script_type IN ('explainer','tutorial','story','demo','testimonial')) DEFAULT 'explainer',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scripts_project ON scripts(project_id);
CREATE INDEX idx_scripts_content_fts ON scripts USING GIN (to_tsvector('english', content::text));

-- Scenes
CREATE TABLE scenes (
  id UUID PRIMARY KEY,
  script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
  scene_number INTEGER NOT NULL,
  duration INTEGER NOT NULL,
  voiceover_text TEXT NOT NULL,
  visual_description TEXT NOT NULL,
  scene_type TEXT CHECK (scene_type IN ('intro','main_content','demo','testimonial','conclusion','call_to_action')) DEFAULT 'main_content',
  platform_specific JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(script_id, scene_number)
);

CREATE INDEX idx_scenes_script ON scenes(script_id);
CREATE INDEX idx_scenes_platform_specific ON scenes USING GIN (platform_specific);

-- Generated Content
CREATE TABLE generated_content (
  id UUID PRIMARY KEY,
  scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  content_type TEXT CHECK (content_type IN ('video','audio','thumbnail','subtitle')) NOT NULL,
  file_path TEXT NOT NULL,
  file_size INTEGER DEFAULT 0,
  duration INTEGER,
  quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 10) DEFAULT 0,
  platform TEXT CHECK (platform IN ('youtube','tiktok','instagram','linkedin','twitter','universal')) DEFAULT 'universal',
  resolution TEXT,
  format TEXT,
  generation_metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_content_scene ON generated_content(scene_id);
CREATE INDEX idx_generated_content_platform ON generated_content(platform);
CREATE INDEX idx_generated_content_metadata ON generated_content USING GIN (generation_metadata);

-- Content Library
CREATE TABLE content_library (
  id UUID PRIMARY KEY,
  scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  specific_tags JSONB DEFAULT '[]',
  generic_tags JSONB DEFAULT '[]',
  usage_count INTEGER DEFAULT 0,
  performance_score REAL CHECK (performance_score >= 0 AND performance_score <= 10) DEFAULT 0,
  last_used TIMESTAMP,
  library_category TEXT CHECK (library_category IN ('high_performance','experimental','archived','favorite')) DEFAULT 'experimental',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_content_library_performance ON content_library(performance_score DESC);
CREATE INDEX idx_content_library_usage ON content_library(usage_count DESC);
CREATE INDEX idx_content_library_tags ON content_library USING GIN (specific_tags, generic_tags);

-- Generation Jobs
CREATE TABLE generation_jobs (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  job_type TEXT CHECK (job_type IN ('script_generation','video_generation','audio_generation','platform_adaptation')) NOT NULL,
  status TEXT CHECK (status IN ('pending','processing','completed','failed')) DEFAULT 'pending',
  progress INTEGER DEFAULT 0,
  total_steps INTEGER DEFAULT 0,
  current_step INTEGER DEFAULT 0,
  error_message TEXT,
  result_data JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX idx_generation_jobs_project ON generation_jobs(project_id);

-- Performance Metrics
CREATE TABLE performance_metrics (
  id UUID PRIMARY KEY,
  content_id UUID NOT NULL REFERENCES generated_content(id) ON DELETE CASCADE,
  platform TEXT CHECK (platform IN ('youtube','tiktok','instagram','linkedin','twitter')) NOT NULL,
  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  dislikes INTEGER DEFAULT 0,
  comments_count INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  engagement_rate REAL CHECK (engagement_rate >= 0 AND engagement_rate <= 1) DEFAULT 0,
  watch_time INTEGER DEFAULT 0,
  click_through_rate REAL CHECK (click_through_rate >= 0 AND click_through_rate <= 1) DEFAULT 0,
  performance_score REAL CHECK (performance_score >= 0 AND performance_score <= 10) DEFAULT 0,
  collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics
CREATE TABLE analytics (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  total_views INTEGER DEFAULT 0,
  total_engagement INTEGER DEFAULT 0,
  avg_watch_time REAL DEFAULT 0,
  top_platform TEXT,
  metrics_data JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, date)
);

CREATE INDEX idx_analytics_project ON analytics(project_id);
```

### B. Sample RLS Policies

Enable RLS and apply tenant isolation policies.

```sql
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
  USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

ALTER TABLE scripts ENABLE ROW LEVEL SECURITY;

CREATE POLICY project_access ON scripts
  USING (EXISTS (
    SELECT 1 FROM projects p
    WHERE p.id = scripts.project_id
      AND p.tenant_id = (auth.jwt() ->> 'tenant_id')::UUID
  ));

-- Similar policies should be created for scenes, generated_content,
-- performance_metrics (read-only for non-service-role), generation_jobs,
-- content_library (with optional public catalog), and analytics.
```

### C. API Endpoint Inventory (Batch-Aware)

- POST /projects
- GET /projects/:id
- POST /batches
- GET /batches
- POST /batches/:id/actions { action: "pause" | "resume" }
- POST /jobs
- GET /jobs/:id
- POST /jobs/:id/retry { stage?: string }
- POST /jobs/:id/pause
- GET /jobs
- GET /analytics
- GET /library
- POST /library/items
- GET /assets/signed-url?content_id=UUID

### D. Event Payloads for Progress and Error Streams

Progress event:
```json
{
  "job_id": "uuid",
  "project_id": "uuid",
  "stage": "audio_generation",
  "status": "processing",
  "current_step": 2,
  "total_steps": 4,
  "progress": 50,
  "timestamp": "2025-11-05T00:52:13Z"
}
```

Error event:
```json
{
  "job_id": "uuid",
  "stage": "video_generation",
  "status": "failed",
  "error_code": "TRANSIENT_STORAGE_FAILURE",
  "error_message": "Unable to write asset to storage",
  "retries": 2,
  "timestamp": "2025-11-05T00:53:10Z"
}
```

## Information Gaps

The integration plan acknowledges the following gaps that require confirmation before finalizing designs and schedules:

- Supabase project configuration, including environment variables, keys, and tenant model (single vs multi-tenant).
- Final choice of queue/broker for the orchestrator and deployment details for the batch service.
- Scalability targets and resource constraints for batch sizes, concurrency limits, and performance service-level objectives.
- Precise storage locations and path conventions for large assets, including CDN or signed URL requirements.
- Frontend state management conventions beyond existing pages and components (e.g., WebSocket client details, Axios interceptors).
- Security posture for API protection, CORS origins, and token refresh flows tailored to this application.
- Data retention policies and PII classification for analytics and performance metrics.
- End-to-end test coverage plan, including fixture data and canary rollout strategy.
- Exact UI requirements for batch job management and any localization or accessibility mandates.

Addressing these gaps early will reduce integration risk and accelerate rollout.

## References

[^1]: AI Content Automation GitHub Repository. https://github.com/jsimoes215/AI-Content-Automation.git

[^2]: AI Content Automation Production Interface. https://7v9b5bhnkpx9.space.minimax.io

[^3]: Supabase Documentation: Row Level Security (RLS). https://supabase.com/docs/guides/auth/row-level-security

[^4]: Supabase Authentication Guide. https://supabase.com/docs/guides/auth