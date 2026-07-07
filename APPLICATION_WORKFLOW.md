# Talent Finder — Complete Application Workflow

> **What is this document?**
> This document explains, from beginning to end, how the Talent Finder application works. It covers everything: what the user sees on screen, what happens behind the scenes in the frontend code, what the backend server does, what the sourcing service does, how the databases are used, how AI models are involved, and how all the services talk to each other. It is written in plain, natural language so that anyone — even without prior knowledge of this project — can read it top to bottom and understand the full picture.

---

## Table of Contents

1. [The Big Picture](#1-the-big-picture)
2. [Infrastructure and Startup](#2-infrastructure-and-startup)
3. [Authentication](#3-authentication)
4. [The Recruiter Experience](#4-the-recruiter-experience)
    - 4.1 [Creating a Job Description](#41-creating-a-job-description)
    - 4.2 [Viewing and Editing Job Descriptions](#42-viewing-and-editing-job-descriptions)
    - 4.3 [Running the Scoring Pipeline](#43-running-the-scoring-pipeline)
    - 4.4 [Reviewing Scored Candidates](#44-reviewing-scored-candidates)
    - 4.5 [Sharing a Shortlist with the Hiring Manager](#45-sharing-a-shortlist-with-the-hiring-manager)
    - 4.6 [Importing a Candidate Resume Manually](#46-importing-a-candidate-resume-manually)
    - 4.7 [Monitoring Background Tasks](#47-monitoring-background-tasks)
5. [The Hiring Manager Experience](#5-the-hiring-manager-experience)
    - 5.1 [Viewing Shared Campaigns](#51-viewing-shared-campaigns)
    - 5.2 [Reviewing Candidates](#52-reviewing-candidates)
    - 5.3 [Scheduling an Interview](#53-scheduling-an-interview)
6. [The Scoring Pipeline — Deep Dive](#6-the-scoring-pipeline--deep-dive)
    - 6.1 [Stage 1: Acquiring Candidates](#61-stage-1-acquiring-candidates)
    - 6.2 [Stage 2: External Sourcing (PostJobFree)](#62-stage-2-external-sourcing-postjobfree)
    - 6.3 [Stage 3: Pre-Scoring](#63-stage-3-pre-scoring)
    - 6.4 [Stage 4: Selection and Filtering](#64-stage-4-selection-and-filtering)
    - 6.5 [Stage 5: Candidate Synchronization](#65-stage-5-candidate-synchronization)
    - 6.6 [Stage 6: Deep Scoring](#66-stage-6-deep-scoring)
    - 6.7 [Stage 7: Persistence and Completion](#67-stage-7-persistence-and-completion)
7. [The Sourcing Service — Deep Dive](#7-the-sourcing-service--deep-dive)
    - 7.1 [Architecture](#71-architecture)
    - 7.2 [The Search-or-Source Decision](#72-the-search-or-source-decision)
    - 7.3 [The Adaptive Scraping Loop](#73-the-adaptive-scraping-loop)
    - 7.4 [Resume Extraction](#74-resume-extraction)
    - 7.5 [The Candidate Database (Sourcing)](#75-the-candidate-database-sourcing)
8. [AI Agents and LLM Usage](#8-ai-agents-and-llm-usage)
9. [The Notification System](#9-the-notification-system)
10. [The Score Calculation Formula](#10-the-score-calculation-formula)
11. [Database Architecture](#11-database-architecture)
12. [Technology Stack Summary](#12-technology-stack-summary)

---

## 1. The Big Picture

Talent Finder is a recruitment intelligence platform. It helps recruiters and hiring managers find, evaluate, and hire candidates. The core idea is:

1. A **recruiter** creates a job description describing what kind of person they are looking for.
2. The system automatically **finds candidates** — first from its own database, and if that is not enough, it goes out to the internet (specifically PostJobFree.com) and scrapes real resumes.
3. An **AI pipeline** evaluates every candidate against the job description. It assigns scores, identifies skill matches and gaps, and ranks candidates from best to worst.
4. The recruiter reviews the ranked shortlist and **shares** their top picks with a **hiring manager**.
5. The hiring manager reviews the shared candidates, makes accept/reject decisions, and can **schedule interviews** directly from the platform. The candidate receives an interview invitation email.

The system is composed of three main services:

| Service | Purpose | Technology |
|---------|---------|-----------|
| **Client** | The user interface — what people see in their browser | React (TypeScript), Vite |
| **Server** | The central brain — handles authentication, job descriptions, scoring, notifications | FastAPI (Python), Celery, Redis |
| **Sourcing** | A specialized microservice for finding and storing candidate data | FastAPI (Python), PostJobFree scraper |

They are all orchestrated together using **Docker Compose** and share a PostgreSQL database cluster (two separate databases) and a Redis instance.

---

## 2. Infrastructure and Startup

When a developer runs `docker compose up`, five containers start:

### 2.1 PostgreSQL Database

A single PostgreSQL server hosts **two separate databases**:

- **`usecase`** — Used by the main server. Stores users, job descriptions, candidates (local copies), scores, pipeline entries, scoring tasks, and notifications.
- **`sourcing`** — Used by the sourcing service. Stores the master copy of all scraped and imported candidates, their skills, experiences, and education records.

An initialization script (`init-sourcing-db.sh`) automatically creates the `sourcing` database if it does not already exist.

### 2.2 Redis

Redis serves a dual purpose:

- **Message broker** for Celery — it is the queue where background tasks (like the scoring pipeline) are placed and picked up by workers.
- **Result backend** for Celery — workers report their task status back through Redis.

### 2.3 Sourcing Service

The sourcing service starts as a standalone FastAPI application on port `8001`. On startup, it runs Alembic database migrations against the `sourcing` database, then launches Uvicorn. This service has its own routes, models, and AI agents. The main server talks to it over HTTP using Docker's internal network (the hostname is just `sourcing`).

### 2.4 Server (API + Celery Worker)

The server container runs **two processes**:

1. **The FastAPI API server** on port `8000` — handles all HTTP requests from the frontend.
2. **A Celery worker** — picks up background tasks from the Redis queue and executes them. The scoring pipeline runs here because it can take several minutes (it involves multiple AI calls, web scraping, and database writes).

On startup, the server runs Alembic migrations against the `usecase` database. Then both processes start. The FastAPI lifespan hook also runs a **stale task recovery** check: any scoring tasks that were left in a "RUNNING" state from a previous crash are automatically marked as "FAILED" and the recruiter is notified.

### 2.5 Client

The React frontend is a Vite development server on port `5173`. It is a single-page application that communicates with the server via REST API calls.

---

## 3. Authentication

### What the user sees

When a user opens the application for the first time, they are redirected to the **login page**. They enter their email and password.

If they have forgotten their password, they can click "Forgot Password," which takes them through a flow: enter email → receive OTP via email → verify OTP → set new password.

### What happens internally

**Login Flow:**

1. The frontend sends a `POST /api/auth/login` request with `{ email, password }`.
2. The server's `AuthService` looks up the user in the `users` table by email.
3. It verifies the password hash using `bcrypt`.
4. If successful, it generates two JWT tokens:
   - An **access token** (short-lived, configured via `ACCESS_TOKEN_EXPIRE_MINUTES`) containing the user's ID and role (`recruiter` or `hiring_manager`).
   - A **refresh token** (long-lived, configured via `REFRESH_TOKEN_EXPIRE_DAYS`).
5. Both tokens are set as **HTTP-only cookies** in the response. This means JavaScript in the browser cannot directly read them — they are automatically sent with every request.
6. The response body contains the user's profile information (name, email, role).

**Token Refresh Flow:**

The frontend has an Axios HTTP interceptor configured in `lib/api.ts`. Whenever any API call returns a `401 Unauthorized` response with the error code `TOKEN_EXPIRED`:

1. The interceptor automatically sends a `POST /api/auth/refresh` request. The refresh token cookie is automatically included.
2. The server validates the refresh token, looks up the user, and issues a new access token cookie.
3. The original failed request is then automatically retried with the new access token.
4. If the refresh also fails, the user is logged out and redirected to the login page.

This happens completely transparently — the user never sees a login prompt unless their refresh token has also expired.

**Route Protection:**

The frontend uses a `ProtectedRoute` component that wraps all authenticated pages. It checks the authentication context (provided by `AuthProvider`). If the user is not authenticated, they are redirected to `/login`.

After login, the user is redirected based on their role:
- **Recruiters** → `/recruiter/job-descriptions`
- **Hiring Managers** → `/hm/shared-campaigns`

---

## 4. The Recruiter Experience

### 4.1 Creating a Job Description

**What the user sees:**

The recruiter navigates to the "Job Descriptions" page and clicks "Create New." They are taken to a form where they can either:

- **Paste a raw job description** (free text) and let the AI extract structured data from it.
- **Fill in the fields manually**: title, department, job purpose, responsibilities, experience range, location, education requirements, preferred qualifications, employment type, and skills (marking each as mandatory or optional).

They can also assign a **hiring manager** to the job description from a dropdown of registered hiring managers.

**What happens internally when AI extraction is used:**

1. The frontend sends a `POST /api/job-descriptions/extract` request with the raw text.
2. The server's `JobDescriptionService` calls the `JobDescriptionExtractionAgent`.
3. This agent uses a **HuggingFace LLM** (configured via `HF_MODEL` in settings) through LangChain. It sends the raw text along with a detailed system prompt (`JOB_DESCRIPTION_EXTRACTION_PROMPT`) that instructs the AI to extract: title, department, purpose, responsibilities, experience range, location, education, qualifications, and a list of skills with mandatory/optional flags.
4. The AI is configured for **structured output** — it returns a JSON object matching the `JobDescriptionExtraction` Pydantic schema. LangChain's `with_structured_output(method="json_mode")` ensures the response is valid JSON.
5. The extracted data is sent back to the frontend. The user can review and edit it before saving.

**What happens when the job description is saved:**

1. The frontend sends a `POST /api/job-descriptions` request with the structured data.
2. The server's `JobDescriptionService` creates a new `JobDescription` record in the database along with associated `JDSkill` records.
3. The job description is assigned an initial status (the `job_description_statuses` table contains status codes like `DRAFT`, `ACTIVE`, etc.).
4. If a hiring manager is assigned, the `hiring_manager_id` foreign key is set on the job description.

### 4.2 Viewing and Editing Job Descriptions

**What the user sees:**

The "Job Descriptions" page shows a list of all job descriptions created by the logged-in recruiter. Each card shows the title, department, status, and creation date.

Clicking a job description opens a **detail page** showing all the structured fields. From here, the recruiter can:

- **Edit** the job description (navigates to an edit form).
- **Run scoring** (navigates to the scoring configuration page).
- **View candidates** (navigates to the candidate board, available after scoring has run).

**What happens internally:**

- `GET /api/job-descriptions` — Fetches all job descriptions for the authenticated recruiter. The server filters by `recruiter_id` matching the JWT user ID.
- `GET /api/job-descriptions/{id}` — Fetches a single job description with all its skills eagerly loaded.
- `PUT /api/job-descriptions/{id}` — Updates the job description. The server verifies the recruiter owns this JD before allowing the update.
- `DELETE /api/job-descriptions/{id}` — Deletes the job description.

### 4.3 Running the Scoring Pipeline

**What the user sees:**

The recruiter navigates to the "Scoring Configuration" page for a job description. They configure:

- **`k`** — The number of top candidates they want to see (e.g., "show me the top 5").
- **`minimum_prescore_threshold`** — The minimum pre-screening score (0–100) a candidate needs to be considered.
- **`confirm`** — Whether to actually run the pipeline or just get a preview of how many candidates were found.

They click "Run Pipeline." The UI shows a progress indicator because the pipeline runs in the background.

**What happens internally:**

1. The frontend sends a `POST /api/scoring/{job_description_id}/pipeline` request with `{ k, minimum_prescore_threshold, confirm }`.

2. The server's `scoring_route.py` handler does the following:
   - **Recovers stale tasks** first — checks if any previously running tasks have been stuck too long and marks them failed.
   - **Authorizes** the recruiter — verifies they own this job description.
   - **Creates a ScoringTask** record in the database with status `PENDING` and stage `QUEUED`.
   - **Dispatches a Celery background task** — calls `run_scoring_pipeline_task.delay(...)`, which puts the work into the Redis queue.
   - **Saves the Celery task ID** on the ScoringTask record.
   - **Returns immediately** with `{ task_id, status: "QUEUED" }`.

3. The frontend starts **polling** `GET /api/scoring/tasks/{task_id}` every few seconds to check progress. The response includes the `current_stage` field which progresses through: `QUEUED` → `ACQUIRING` → `SOURCING` → `PRE_SCORING` → `SYNCHRONIZING` → `DEEP_SCORING` → `COMPLETED` (or `FAILED`).

4. Meanwhile, the **Celery worker** picks up the task from Redis and runs `async_run_scoring_pipeline()`. This is the full pipeline described in detail in [Section 6](#6-the-scoring-pipeline--deep-dive).

5. As the pipeline progresses, the `DatabaseProgressReporter` updates the `current_stage` column on the `ScoringTask` record. This is how the frontend polling sees real-time progress.

6. When the pipeline completes:
   - The task status is updated to `COMPLETED`.
   - The full response payload (candidate results) is stored as JSON in the `final_response_payload` column of the `ScoringTask`.
   - A **notification** is sent to the recruiter (both in-app and via email) saying "Scoring Completed."
   - If the pipeline fails, the task status becomes `FAILED`, the error message is stored, and a failure notification is sent.

7. The frontend can then fetch the results via `GET /api/scoring/tasks/{task_id}/result`.

### 4.4 Reviewing Scored Candidates

**What the user sees:**

After scoring completes, the recruiter navigates to the **Candidate Board** for the job description. This shows a ranked list of candidates with:

- Name, title, location
- Final score, confidence percentage
- Pre-score rank
- Matched mandatory skills (green), matched optional skills, missing mandatory skills (red)
- Pipeline stage (SHORTLISTED, INTERVIEW, etc.)

Clicking a candidate opens a **Candidate Evaluation Board** with:
- Full candidate profile (name, email, phone, location, summary)
- Complete work experience history with per-experience skills
- Education history
- Detailed score breakdown: skills score, experience score, recency score, role fit score, education score
- AI-generated explanation with strengths, weaknesses, and a summary

The recruiter can also:
- **Add notes** to any candidate (stored in the `pipeline` table as `recruiter_notes`).
- **Change the pipeline stage** (e.g., move from SHORTLISTED to INTERVIEW to OFFERED).
- **Re-score** a single candidate — triggers a fresh AI evaluation.

**What happens internally:**

- `GET /api/scoring/jobs/{jd_id}/candidates` — Returns all candidates with scores for this JD, sorted by final score descending. Loads data from the `candidate_job_scores` table joined with `candidates` and `pipeline` tables.
- `GET /api/scoring/jobs/{jd_id}/candidates/{candidate_id}/board` — Returns the full evaluation board: candidate details, pipeline snapshot, and score breakdown.
- `PATCH /api/scoring/jobs/{jd_id}/candidates/{candidate_id}/pipeline-notes` — Updates the recruiter's notes on the pipeline entry.
- `PATCH /api/scoring/jobs/{jd_id}/pipeline-stage` — Bulk-updates the pipeline stage for multiple candidates.
- `POST /api/scoring/jobs/{jd_id}/candidates/{candidate_id}/rescore` — Re-runs the deep scoring for a single candidate and returns the new score.

### 4.5 Sharing a Shortlist with the Hiring Manager

**What the user sees:**

The recruiter selects candidates from the candidate board and clicks "Share with Hiring Manager." They can optionally write personalized notes for each candidate explaining why they are recommending them.

**What happens internally:**

1. The frontend sends a `POST /api/scoring/recruiter/job-descriptions/{jd_id}/share` request with `{ candidate_ids, notes_by_candidate }`.

2. The `ScoringService.share_shortlist()` method:
   - Validates that the user is a recruiter.
   - Validates that all submitted candidate IDs actually exist in the pipeline for this job description.
   - Marks each pipeline entry with `shared_with_hiring_manager = True`, records the `shared_at` timestamp, sets the `hm_decision` to `PENDING`, and stores any recruiter notes.
   - Commits the transaction to the database.

3. **Notification dispatch** (best-effort — failures here never rollback the sharing):
   - Loads the hiring manager assigned to this job description.
   - Creates an **in-app notification** in the `notifications` table.
   - Sends an **email notification** via the Brevo transactional email API. The email includes a "Review Candidates" button linking directly to the hiring manager's campaign view.

### 4.6 Importing a Candidate Resume Manually

**What the user sees:**

The recruiter can paste the text of a resume into a form and click "Import." The system uses AI to parse the resume and create a candidate profile.

**What happens internally:**

1. The frontend sends a `POST /api/scoring/candidates/import` request with `{ job_description_id, resume_text }`.

2. The `ScoringService.import_candidate_resume()` method:
   - Authorizes the recruiter.
   - Validates the resume text is not empty.
   - Calls `ResumeParser.parse_resume()` which uses the `ResumeExtractionClient`.
   - The `ResumeExtractionClient` sends the resume text to a **Groq LLM** (via LangChain) with the `RESUME_EXTRACTION_PROMPT`. The AI extracts: full name, email, phone, current title, location, summary, total experience months, skills, work experiences (with per-experience skills), and education.
   - A SHA-256 hash of the resume text is computed for deduplication.
   - The parsed profile is stored in the database.

### 4.7 Monitoring Background Tasks

**What the user sees:**

The "Tasks" page shows all scoring tasks the recruiter has launched. Each task shows:
- The associated job description title
- Current status (PENDING, RUNNING, COMPLETED, FAILED)
- Current stage (QUEUED, ACQUIRING, SOURCING, etc.)
- Timestamps (created, started, completed)
- Candidate counts (matched, eligible, selected)
- Error message if failed

**What happens internally:**

- `GET /api/scoring/tasks` — Returns all tasks for the authenticated recruiter, ordered by creation date. Before returning, it runs `recover_stale_tasks()` which checks for any tasks stuck in PENDING/RUNNING state longer than the configured timeout. Stale tasks are marked FAILED and the recruiter is notified.

---

## 5. The Hiring Manager Experience

### 5.1 Viewing Shared Campaigns

**What the user sees:**

After logging in, the hiring manager lands on the "Shared Campaigns" page. This shows all job descriptions where a recruiter has shared candidates with them. Each campaign card shows:
- Job title and department
- Recruiter's name
- When the shortlist was shared
- Counts: total shared, accepted, rejected, pending

**What happens internally:**

- `GET /api/scoring/hm/campaigns` — Loads all job descriptions where `hiring_manager_id` matches the current user. For each JD, it counts pipeline entries that have `shared_with_hiring_manager = True`, grouped by their `hm_decision` status.

### 5.2 Reviewing Candidates

**What the user sees:**

Clicking a campaign shows the list of shared candidates with their scores, the recruiter's notes, and the current review status. The hiring manager can click each candidate to see their full evaluation board (same detailed view as the recruiter). They can:

- **Accept** a candidate (marks them for interview)
- **Reject** a candidate
- Add their own **hiring manager notes**

**What happens internally:**

- `GET /api/scoring/hm/campaigns/{jd_id}/candidates` — Returns all pipeline entries for this JD that have `shared_with_hiring_manager = True`. Joins with the `candidates` and `candidate_job_scores` tables to provide full details.

- `POST /api/scoring/hm/campaigns/{jd_id}/candidates/{candidate_id}/review` — Updates the `hm_decision` column on the pipeline entry (PENDING → INTERVIEW_SENT or REJECTED) and stores `hiring_manager_notes`.

- `GET /api/scoring/hm/campaigns/{jd_id}/candidates/{candidate_id}/board` — Returns the full evaluation board. Includes an authorization check that the hiring manager owns this campaign and the candidate is shared.

### 5.3 Scheduling an Interview

**What the user sees:**

For an accepted candidate, the hiring manager can schedule an interview by providing:
- Interview link (e.g., a Google Meet or Zoom URL)
- Date and time
- Timezone
- An optional personal message

They click "Send Interview Invitation."

**What happens internally:**

1. The frontend sends a `POST /api/scoring/hm/campaigns/{jd_id}/candidates/{candidate_id}/schedule-interview` request.

2. The `ScoringService.schedule_interview()` method:
   - Verifies the user is a hiring manager who owns this campaign.
   - Verifies the candidate is shared with the hiring manager.
   - Verifies the candidate has an email address on file.
   - **Sends an email to the candidate** via Brevo with the interview details (date, time, timezone, link, and optional message). This email is sent first — if it fails, the pipeline entry is not updated.
   - Only after successful email delivery, updates the pipeline entry: sets `hm_decision = INTERVIEW_SENT`, stores the interview link, datetime, timezone, message, and `interview_sent_at` timestamp.
   - **Sends a notification to the recruiter** (both in-app and email) informing them that the hiring manager has scheduled an interview. This notification is best-effort — failures do not affect the interview scheduling.

---

## 6. The Scoring Pipeline — Deep Dive

This is the core of the system. When a recruiter clicks "Run Pipeline," the following multi-stage process executes as a Celery background task. The entry point is `ScoringService.pipeline_prescore_and_score()`.

### 6.1 Stage 1: Acquiring Candidates

**Progress stage: `ACQUIRING`**

The `CandidateAcquisitionService` is responsible for building the initial pool of candidates to evaluate. It works in two phases:

**Phase 1: Local Database Search**

The system first searches its own database (the `usecase` database's `candidates` table) for candidates matching the job description. This is a heuristic filter — not an AI evaluation. The matching logic in `_source_candidates_for_job_description()` works like this:

1. It loads all candidates from the local database.
2. For each candidate, it checks:
   - **Experience threshold** — Does the candidate have at least `min_experience - 1` years of experience? If not, skip.
   - **Skill relevance** — Does the candidate have at least one matching mandatory or optional skill? Skills are compared by name (case-insensitive).
   - **Role hint** — Does the candidate's current title contain any significant words from the job title?
3. A candidate passes the filter if they meet the experience threshold AND (have relevant skills OR match the role hint).

**Phase 2: External Sourcing Decision**

The `CandidateAcquisitionService` calculates a target pool size: `10 × k` (where `k` is the number of top candidates the recruiter wants). If the local search found fewer candidates than this target:

- The system generates a **search query** using the `CandidateSearchQueryAgent` (an AI agent). This agent takes the job description and produces a generalized search request — broadening the title (e.g., "Senior Backend Engineer" → "Backend Engineer") and stripping proficiency modifiers from skills (e.g., "Advanced Python" → "Python").
- The search request is sent to the **Sourcing Service** via HTTP (`POST /candidates/search`). This triggers the external sourcing process described in [Section 7](#7-the-sourcing-service--deep-dive).
- The sourcing service returns candidate summaries (compressed profiles with just ID and profile text).

If the local pool already has enough candidates, external sourcing is skipped entirely.

**Merge and Deduplication**

Local candidates and sourced candidates are merged into a single pool. A deduplication step ensures no candidate ID appears twice.

Each candidate in the pool is represented as a `CandidateSummary` — just a `candidate_id` and a `profile_text` (a compressed text representation like "Title: Backend Engineer\nExperience: 5.2 years\nSkills: Python, FastAPI\nCareer: Software Engineer, Senior Developer").

### 6.2 Stage 2: External Sourcing (PostJobFree)

**Progress stage: `SOURCING`**

This stage only activates if the local database did not have enough candidates. It is handled entirely by the Sourcing Service — see [Section 7](#7-the-sourcing-service--deep-dive) for the full deep dive.

### 6.3 Stage 3: Pre-Scoring

**Progress stage: `PRE_SCORING`**

Now the system has a pool of candidates (potentially dozens or hundreds). It needs to quickly narrow this down. Pre-scoring is a fast, lightweight AI evaluation.

1. The `ScoringService` builds a `CompressedJobDescription` — a short text summary: "Title: Backend Engineer\nExperience: 3-5 years\nRequired Skills: Python, FastAPI\nOptional Skills: Docker, AWS".

2. All candidate summaries and the compressed JD are sent to the `CandidatePrescoringClient`, which calls a **Groq LLM** with the `CANDIDATE_PRESCORING_PROMPT`.

3. The AI assigns each candidate a **pre-score from 0 to 100** based on how promising they look for further evaluation. The scoring guide ranges from "0–19: Clear mismatch" to "90–100: Exceptional match."

4. The results are sorted by score (highest first).

### 6.4 Stage 4: Selection and Filtering

After pre-scoring, the system applies two filters:

1. **Threshold filter** — Any candidate scoring below `minimum_prescore_threshold` is eliminated.
2. **Top-K filter** — Only the top `k` candidates (by pre-score) are selected for the expensive deep scoring stage.

Each candidate is assigned a terminal lifecycle status:
- **Selected** (will proceed to deep scoring)
- **Skipped — below threshold** (pre-score too low)
- **Skipped — outside top K** (scored high enough but didn't make the cut)
- **Failed** (pre-scoring itself failed for this candidate)

### 6.5 Stage 5: Candidate Synchronization

**Progress stage: `SYNCHRONIZING`**

The selected top-K candidates need to have their **full profiles** available in the local database before deep scoring can work. The `CandidateSynchronizationService` handles this.

For each selected candidate, the system checks:

1. **Does the candidate exist in the local database?**
   - If not → it's "missing" and needs to be synchronized.
2. **Is the local copy fresh?**
   - If the candidate's `updated_at` timestamp is older than `CANDIDATE_REFRESH_AFTER_DAYS` → it's "stale" and needs to be refreshed.
   - If it's recent enough → it's "fresh" and can be used as-is.

For all missing and stale candidates:

1. The system calls the **Sourcing Service** via HTTP (`POST /candidates/by-ids`) with the list of candidate IDs.
2. The sourcing service looks up each candidate in its own database (the `sourcing` database) and returns full detailed profiles — name, email, phone, skills, experiences (with per-experience skills), education, etc.
3. Each returned profile is **upserted** into the local `usecase` database — if the candidate already exists, their record is updated; if not, a new record is created.

This synchronization ensures the main server has all the detailed information needed for deep scoring, even for candidates that were originally found by the sourcing service.

### 6.6 Stage 6: Deep Scoring

**Progress stage: `DEEP_SCORING`**

This is the most thorough and expensive stage. Each selected candidate is individually evaluated against the full job description by the AI.

1. The `ScoringService` builds a `JobDescriptionScoringInput` — the complete JD with all fields (title, department, purpose, responsibilities, experience range, education requirements, qualifications, and all skills with mandatory/optional flags).

2. For each candidate, it builds a `CandidateScoringInput` — the complete candidate profile with all skills, all work experiences (with per-experience skills), and all education records.

3. All scoring tasks are dispatched concurrently using `asyncio.gather()`. Each one calls the `CandidateScoringClient.score_candidate()` method.

4. For each candidate, the `CandidateScoringClient`:
   - Sends the JD and candidate data to a **Groq LLM** with the `CANDIDATE_DEEP_SCORING_PROMPT`.
   - The AI evaluates: mandatory skill matches (with proficiency-quality weights), optional skill matches, missing mandatory skills, role fit (0–12), education alignment (0–8), and a confidence score (0–100).
   - The AI also generates an **explanation** with strengths, weaknesses, and a summary.

5. The client-side scoring engine then **calculates the final score** using the formula described in [Section 10](#10-the-score-calculation-formula). The AI provides evaluations, but the numerical score is computed deterministically by the code.

6. If any individual scoring fails (AI error, timeout, etc.), that candidate is marked as failed but the pipeline continues for the others. This is a "recoverable error" approach.

### 6.7 Stage 7: Persistence and Completion

After all deep scores are calculated:

1. **Scores are persisted** — The `ScoringRepository` upserts records into the `candidate_job_scores` table. Each record links a candidate to a job description with their full score breakdown.

2. **Pipeline entries are created** — For each successfully scored candidate, a record is upserted into the `pipeline` table with stage `SHORTLISTED`. This is the record that tracks a candidate's progression through the hiring process.

3. **Job description status is updated** — If the JD was in DRAFT status, it is transitioned to ACTIVE.

4. **A pipeline execution report** is generated and logged. It includes invariant checks to verify data consistency (e.g., "number of selected candidates equals number of completed + failed").

5. The final response is constructed with the ranked candidate list, sorted by final score (highest first). This response is serialized as JSON and stored on the `ScoringTask` record.

6. A **success notification** is sent to the recruiter.

---

## 7. The Sourcing Service — Deep Dive

### 7.1 Architecture

The sourcing service is a separate FastAPI microservice with its own:
- **Database** — The `sourcing` PostgreSQL database with candidate, skill, experience, and education tables.
- **AI agents** — For resume extraction and search query optimization.
- **HTTP client** — For scraping PostJobFree.com.
- **API routes** — Three endpoints on the `/candidates` prefix.

The three API endpoints are:

| Endpoint | Purpose |
|----------|---------|
| `POST /candidates/search` | Search the sourcing database for candidates matching criteria; if not enough, scrape new ones from PostJobFree |
| `POST /candidates/by-ids` | Return full candidate details for a list of IDs |
| `GET /candidates/compressed` | Return all candidates as compressed profiles |

### 7.2 The Search-or-Source Decision

When the main server sends a search request to `POST /candidates/search`, the `CandidateSearchService` makes a decision:

1. **Search the local sourcing database** for candidates matching the request. The `CandidateRepository.search_candidates_by_skills()` does this using SQL:
   - Finds candidates whose skills match any of the requested skills (case-insensitive LIKE queries).
   - Finds candidates whose current title matches the requested title (case-insensitive ILIKE).
   - Unions these results and excludes any IDs in the `exclude_candidate_ids` list (these are candidates the main server already has locally).

2. **If local results are enough** (meeting `required_candidates`), return them immediately. No scraping happens. The response includes `sourced: false`.

3. **If local results are not enough**, trigger the `PostJobFreeSourcingService` to scrape new candidates from the internet. After scraping completes, re-query the local database and return results. The response includes `sourced: true`.

### 7.3 The Adaptive Scraping Loop

The `PostJobFreeSourcingService.source_candidates()` method runs an intelligent, multi-attempt scraping loop:

**Step 1: Generate an Optimization Plan**

Before any scraping begins, the `SearchQueryOptimizer` calls the `CandidateSearchStrategyAgent` — a Groq-powered AI agent. This agent analyzes the original search request and generates a `SearchOptimizationPlan`:
- **Inferred role** — The most likely hiring archetype (e.g., "Backend Engineer").
- **Representative title** — A generalized job title candidates are likely to use (e.g., "Software Engineer").
- **Representative skills** — The 2-3 most defining technologies for this role.
- **Reasoning** — Why these choices were made.

**Step 2: Iterative Search Attempts**

The scraper then runs a loop, making multiple search attempts with progressively broader queries. Each attempt uses a different strategy from a predefined sequence:

1. **Attempt 1: RepresentativeSkillsStrategy** — Uses the AI-recommended representative skills.
2. **Attempt 2: GeneralizedTitleStrategy** — Uses the generalized title plus representative skills.
3. **Attempt 3: SingleCoreSkillStrategy** — Uses the generalized title with only the single most important skill.
4. **Attempt 4+: TitleOnlyStrategy** — Uses only the generalized title, dropping all skill constraints.

Each strategy broadens the search to catch more candidates.

**Step 3: For Each Attempt**

1. The strategy generates a `PostJobFreeSearchRequest` with: title words, required words (skills joined by space), resume text words, and excluded words.
2. The `PostJobFreeClient` makes an HTTP GET request to `https://www.postjobfree.com/resumes` with query parameters.
3. The returned HTML is parsed by `PostJobFreeSearchParser` to extract resume URLs.
4. For each resume URL found:
   - The `PostJobFreeClient` downloads the full resume page HTML.
   - The `PostJobFreeResumeParser` extracts the raw resume text from the HTML.
   - The `ResumeExtractionAgent` sends the text to a **Groq LLM** which extracts structured candidate data (name, skills, experience, education, etc.).
   - The AI also filters non-English resumes — if the resume is not predominantly in English, it returns an empty result.
   - If extraction succeeds, the candidate is persisted to the `sourcing` database via `CandidateService.create_candidate()`. A SHA-256 hash of the resume text is used for deduplication — if a resume with the same hash already exists, the existing candidate record is returned.
   - A random delay of 10-15 seconds is added between requests to avoid rate limiting.

**Stopping Conditions:**

The loop terminates when any of these conditions are met:
- **Target satisfied** — Enough new candidates have been found.
- **Max attempts reached** — Configurable via `MAX_SOURCING_ATTEMPTS`.
- **No improvement** — Several consecutive attempts yielded no new candidates (configurable via `MAX_CONSECUTIVE_NO_IMPROVEMENT`).
- **Timeout** — The total elapsed time exceeds `SOURCING_LOOP_TIMEOUT_SECONDS`.
- **Duplicate query** — The generated query is identical to a previous attempt (normalized and deduplicated).

### 7.4 Resume Extraction

The `ResumeExtractionAgent` in the sourcing service is responsible for converting raw resume text into structured data. It uses:

- **Provider**: Groq (via `RotationalChatGroq` — a custom wrapper that rotates between multiple API keys to handle rate limits).
- **Model**: Configured via `GROQ_MODEL` setting.
- **Method**: LangChain's `with_structured_output(method="json_mode")` — forces the LLM to return JSON matching the `ResumeCandidateOutput` schema.
- **Prompt**: The system prompt instructs the AI to determine if the resume is in English, extract all information without inventing data, preserve proficiency levels on skills only when explicitly stated, and return dates in ISO format.

The agent has comprehensive error handling covering: validation errors, rate limits (429), timeouts, network errors, API errors, and unexpected exceptions. Each failure type is logged with a specific error code and stage identifier.

### 7.5 The Candidate Database (Sourcing)

The sourcing database mirrors the structure of candidate data in the main database but is the **authoritative source** for scraped candidates. Tables include:

- `candidates` — Full name, email, phone, title, location, summary, resume text, resume hash, source type ("postjobfree"), compressed profile text, total experience months.
- `candidate_skills` — Skills linked to candidates.
- `candidate_experiences` — Work history entries.
- `candidate_experience_skills` — Skills linked to specific work experiences.
- `candidate_educations` — Education records.

When the main server needs full candidate details for synchronization, it calls `POST /candidates/by-ids` which queries these tables with eager loading and returns complete profiles.

---

## 8. AI Agents and LLM Usage

The system uses AI at several critical points. Here is a summary of every AI agent:

| Agent | Service | Provider | Purpose |
|-------|---------|----------|---------|
| `JobDescriptionExtractionAgent` | Server | HuggingFace (via LangChain) | Extracts structured JD data from raw text |
| `CandidateSearchQueryAgent` | Server | HuggingFace (via LangChain) | Generates broadened search queries from a JD |
| `ResumeExtractionClient` | Server | Groq (via LangChain) | Extracts candidate data from pasted resumes |
| `CandidatePrescoringClient` | Server | Groq (via LangChain) | Quick 0–100 screening of candidate summaries |
| `CandidateScoringClient` | Server | Groq (via LangChain) | Detailed skill-by-skill evaluation with explanations |
| `ResumeExtractionAgent` | Sourcing | Groq (RotationalChatGroq) | Extracts candidate data from scraped resumes |
| `CandidateSearchStrategyAgent` | Sourcing | Groq (RotationalChatGroq) | Generates search optimization plans for scraping |

All agents use **structured output** — they are configured to return JSON matching specific Pydantic schemas. This ensures the AI output is always machine-parseable.

The **HuggingFace** provider is used for operations that are less latency-sensitive (JD extraction happens when the user submits a form and can wait a few seconds). The **Groq** provider is used for scoring operations where speed matters (multiple candidates are scored concurrently).

The sourcing service uses a **RotationalChatGroq** wrapper that cycles through multiple Groq API keys to avoid hitting rate limits during intensive scraping sessions.

---

## 9. The Notification System

The notification system serves both **recruiters** and **hiring managers**. It has two delivery channels:

### In-App Notifications

- Stored in the `notifications` table with fields: user ID, type, title, message, target URL, read status, metadata, and creation timestamp.
- Types include: `SCORING_COMPLETED`, `SHORTLIST_SHARED`, `CANDIDATE_ACCEPTED`, `INTERVIEW_INVITATION`, `JD_CLOSED`, `SYSTEM`.
- The frontend polls for unread notifications and displays them in a notification bell/page.
- Users can mark individual notifications as read or mark all as read.

### Email Notifications

- Sent via the **Brevo** transactional email API.
- The `BrevoClient` handles HTTP requests to `https://api.brevo.com/v3/smtp/email`.
- If the Brevo API key is not configured, emails are simulated (logged to console instead of sent).
- HTML email templates are generated by `get_generic_email_html()` which produces styled emails with a title, body text, and a call-to-action button.

### When Notifications Are Sent

| Event | Recipient | In-App | Email |
|-------|-----------|--------|-------|
| Scoring pipeline completed successfully | Recruiter | ✅ | ✅ |
| Scoring pipeline failed | Recruiter | ✅ | ✅ |
| Stale task recovered (auto-failed) | Recruiter | ✅ | ✅ |
| Shortlist shared with hiring manager | Hiring Manager | ✅ | ✅ |
| Interview scheduled by hiring manager | Recruiter | ✅ | ✅ |
| Interview invitation | Candidate (external) | ❌ | ✅ |

All notification dispatches are **best-effort** — if they fail, the primary operation (scoring, sharing, scheduling) still succeeds. Notification failures are logged but never cause a transaction rollback.

---

## 10. The Score Calculation Formula

The final candidate score is composed of five components, each with a maximum point value. The total possible score is **88 points**.

### Skills Score (max 40 points)

Split into mandatory skills (max 28) and optional skills (max 12).

For each matched skill, the AI assigns a **proficiency match quality** weight (0.0 to 1.0):
- `1.0` — Exact match or candidate exceeds the required level.
- `0.75` — Candidate is roughly one level below (slight gap).
- `0.4` — Candidate is two or more levels below (significant gap).

**Mandatory score** = (sum of matched weights / total mandatory skills) × 28

**Optional score** = (sum of matched weights / total optional skills) × 12

### Experience Score (max 25 points)

Based on the candidate's years of experience relative to the JD's min-max range:

- **Below minimum**: `(candidate_years / min_years) × 25` — proportional score, scales linearly.
- **Within range**: Full `25` points.
- **Above maximum**: `25 - decay` where `decay = min(excess_years × 0.5, 10)`, with a floor of `15` points. Overqualified candidates are slightly penalized but never below 15.

### Recency Score (max 15 points)

Based on how recently the candidate was employed:

- **Currently employed**: `15` points.
- **Left within 1 year**: `13.5` points.
- **Left within 2 years**: `11.25` points.
- **Left within 3 years**: `8.25` points.
- **Left within 4 years**: `5.25` points.
- **Left more than 4 years ago**: `3.5` points.
- **No experiences listed**: `0` points.
- **No end dates available**: `5` points.

### Role Fit Score (max 12 points)

Directly from the AI evaluation. The LLM assesses how well the candidate's career trajectory and overall profile align with the role. Scored 0–12.

### Education Score (max 8 points)

Directly from the AI evaluation. Scoring guide:
- `8` — Exact match.
- `7` — Higher qualification than required.
- `6` — Related field.
- `4` — Same level only.
- `0` — Poor match.

### Final Score

`final_score = skills_score + experience_score + recency_score + role_fit_score + education_score`

All component scores are rounded to 2 decimal places.

---

## 11. Database Architecture

### Main Database (`usecase`)

| Table | Purpose |
|-------|---------|
| `users` | Recruiter and hiring manager accounts (name, email, password hash, role) |
| `job_descriptions` | Job descriptions created by recruiters |
| `jd_skills` | Skills associated with JDs (name, is_mandatory flag) |
| `job_description_statuses` | Status codes (DRAFT, ACTIVE, etc.) |
| `employment_types` | Employment type codes |
| `candidates` | Local copies of candidate profiles |
| `candidate_skills` | Skills linked to candidates |
| `candidate_experiences` | Work history entries |
| `candidate_experience_skills` | Skills per work experience |
| `candidate_educations` | Education records |
| `candidate_job_scores` | AI-generated scores linking candidates to JDs |
| `pipeline` | Tracks candidate progression (stage, notes, sharing, interview info) |
| `scoring_tasks` | Background task tracking (status, stage, timestamps, errors, results) |
| `notifications` | In-app notifications for users |

Key relationships:
- A `JobDescription` belongs to a `User` (recruiter) and optionally to a `User` (hiring manager).
- A `Pipeline` entry links a `Candidate` to a `JobDescription` (unique constraint).
- A `CandidateJobScore` links a `Candidate` to a `JobDescription`.
- A `ScoringTask` links a recruiter to a job description.

### Sourcing Database (`sourcing`)

| Table | Purpose |
|-------|---------|
| `candidates` | Master candidate records (includes resume text and hash) |
| `candidate_skills` | Skills linked to candidates |
| `candidate_experiences` | Work history entries |
| `candidate_experience_skills` | Skills per work experience |
| `candidate_educations` | Education records |

The sourcing database is the **authoritative source** for candidate data. The main database's candidate records are copies that get synchronized from the sourcing database.

---

## 12. Technology Stack Summary

| Category | Technology |
|----------|-----------|
| **Frontend** | React 18, TypeScript, Vite, React Router, Axios |
| **Backend API** | Python 3, FastAPI, Uvicorn, Pydantic |
| **Background Tasks** | Celery, Redis (broker + backend) |
| **Database** | PostgreSQL (two databases), SQLAlchemy (async), Alembic |
| **AI / LLM** | LangChain, HuggingFace Inference API, Groq API |
| **Email** | Brevo (Sendinblue) Transactional Email API |
| **Web Scraping** | httpx (async HTTP), BeautifulSoup (HTML parsing) |
| **Authentication** | JWT (PyJWT), bcrypt, HTTP-only cookies |
| **Containerization** | Docker, Docker Compose |
| **External Data Source** | PostJobFree.com (resume database) |

---

> **End of document.** This workflow represents the complete behavior of the Talent Finder application as observed in the codebase. Every stage, decision point, and data flow described above is traced directly from the source code.
