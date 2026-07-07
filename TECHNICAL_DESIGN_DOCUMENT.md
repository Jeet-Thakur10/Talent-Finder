# Talent Finder System: Technical Design Document

This document outlines the architectural design, component responsibilities, data models, algorithm specifications, and workflows of the **Talent Finder** system. It reflects the current implementation of the application.

---

## 1. Project Overview

### Purpose
The Talent Finder system is an AI-powered recruitment automation and talent-matching platform. It automates candidate acquisition, profile parsing, semantic pre-screening, and deep multi-dimensional suitability scoring. By bridging the gap between raw job postings and massive candidate databases, the platform assists recruiters in building high-quality, ranked candidate shortlists and simplifies the hiring manager review process.

### Problem Statement
Traditional recruitment processes are bottle-necked by manual resume review, which is:
1. **Inefficient & Slow:** Sifting through hundreds of raw resumes takes days, delaying time-to-hire.
2. **Subjective:** Manual screening often introduces cognitive bias or inconsistent grading criteria.
3. **Siloed Sourcing:** Recruiters must manually execute search queries across separate internal and external resume databases, making it difficult to maintain a consolidated candidate pool.
4. **Poor Collaboration:** Transitioning candidates from recruiter screening to hiring manager review involves offline emails, spreadsheets, and fragmented feedback loops.

### Goals
- **Job Description Structuring:** Parse raw, unstructured job description text into structured parameters, including experience ranges, department classification, and explicit lists of mandatory versus preferred skills.
- **Unified Candidate Acquisition:** Search and deduplicate candidates from a local profile database and automatically trigger external scraping from external resume platforms (e.g., PostJobFree) when local pools are insufficient.
- **Adaptive Search Optimization:** Employ an LLM-driven query optimizer to broaden or shift search parameters progressively across search strategies, maximizing recall from external resume sources.
- **Scale-Ready Pre-Screening:** Perform lightweight semantic pre-scoring on larger candidate pools to rapidly filter out unqualified applicants before running detailed, resource-intensive evaluations.
- **Strict Deep Scoring:** Calculate multi-dimensional match scores based on skill proficiency, years of experience, employment recency, role fit, and educational credentials.
- **Collaborative Shortlisting:** Provide dedicated interfaces for recruiters to write candidate notes, share candidate dashboards with hiring managers, and allow hiring managers to approve, reject, or schedule interviews.

### Current Capabilities
- **Raw JD Parsing:** Automatic extraction using Hugging Face's `Llama-3.3-70B-Instruct` model, mapped against database schemas for employment types and hiring managers.
- **Multi-Strategy Scraping Loop:** An adaptive search scraper targeting PostJobFree. It utilizes four distinct query strategies in sequence to satisfy a requested target candidate count ($k$).
- **Structured Resume Extraction:** AI-based resume parsing using ChatGroq with validation rules that filter out empty or non-English profiles.
- **Asynchronous Task Processing:** Backend pipelines executed as Celery tasks with a Redis broker, featuring structured stage progression reports and auto-recovery of stale tasks.
- **Fine-Grained Scoring Engine:** A deterministic matching algorithm combining LLM match-quality outputs (e.g., skill proficiency weightings, role fit, education level) with numeric calculations (experience decay, current employment recency).
- **Security & Session Management:** Access control based on HttpOnly secure cookies, JWT tokens, and an OTP password-reset flow backed by Redis.

---

## 2. Business Impact

- **Reduced Time-to-Fill:** Automating the initial sourcing and screening phases reduces recruiter manual effort from days to minutes.
- **Increased Quality of Hire:** Standardizing scoring rules ensures candidates are graded against objective criteria.
- **Optimized Sourcing Costs:** By prioritizing local database lookups and using external scrapers only as a fallback, the system limits API costs and respects external rate limits.
- **Frictionless Collaboration:** The sharing mechanism, interactive candidate boards, and built-in interview scheduler keep the entire hiring team aligned.

---

## 3. Functional Requirements

### Recruiter Capabilities
- **Authentication:** Login using credentials; access protected routes via secure JWT session cookies. Recover password via email-based OTP verification.
- **Job Description (JD) Management:**
  - Create and store job descriptions.
  - Submit raw, unstructured text to extract structured details (title, department, purpose, responsibilities, skills, experience).
  - Preview, modify, and confirm the extracted details before saving.
  - Tag skills as mandatory or optional.
  - Assign a target Hiring Manager to the campaign.
- **Pipeline Execution:** Configure pipeline execution parameters (number of target candidates $k$, minimum pre-score threshold) and trigger background evaluation.
- **Task Center:** Monitor the real-time execution of background tasks, tracking stages (`ACQUIRING`, `SOURCING`, `PRE_SCORING`, `SYNCHRONIZING`, `DEEP_SCORING`).
- **Shortlist Management:**
  - View a list of candidates matched to a JD, ranked by final suitability score.
  - View detailed profile breakdowns, including skill matches, proficiency gaps, work history, and education.
  - Add and update internal recruiter notes for each candidate.
  - Select and share shortlists with the assigned Hiring Manager.
- **Notifications:** Receive in-app notifications and email alerts when background evaluations complete or fail.

### Hiring Manager Capabilities
- **Campaign Dashboard:** List job campaigns shared by recruiters.
- **Candidate Evaluation Board:** Access the profiles, score breakdowns, and recruiter notes of shared candidates.
- **Review Decisioning:** Submit a review decision (`APPROVE` or `REJECT`) along with detailed remarks.
- **Interview Scheduling:** For approved candidates, schedule interviews directly by specifying the date, time, timezone, meeting link, and message.

### System Capabilities
- **Rate-Limit Resilience:** Perform API key rotation across multiple Groq credentials when hitting rate limits.
- **Self-Healing Background Work:** Automatically identify and transition stale or hung tasks to a failed status if the background worker becomes unavailable.
- **Notification Engine:** Dispatch transactional emails (SMTP or Brevo API) and create persistent in-app notifications.

---

## 4. User Roles

### Recruiter
The recruiter is the campaign owner. They create JDs, configure and trigger candidate sourcing pipelines, review the initial pool, record notes, and share candidates with hiring managers.

### Hiring Manager
The hiring manager is the decision-maker. They review shared shortlists, provide feedback on selected profiles, approve/reject candidates, and schedule interviews.

---

## 5. User Journeys

### Recruiter Journey
1. **Login:** Recruiter logs in via the UI. Upon validation, the server sets secure HttpOnly cookies (`access_token` and `refresh_token`). The UI redirects to `/recruiter/job-descriptions`.
2. **Create JD:** Clicks "Create Job Description". Pastes raw JD text and clicks "Extract". The frontend calls `/api/job-descriptions/extract`.
3. **JD Extraction & Review:** The system uses Hugging Face to parse the JD. The recruiter reviews the extracted fields, edits the title, department, or location, marks specific skills as mandatory/optional, selects an assigned Hiring Manager, and saves the record.
4. **Pipeline Execution:** Navigates to `/recruiter/job-descriptions/{id}/score-config`. The recruiter specifies the target shortlist size $k$ (e.g., $k=5$) and a minimum pre-score threshold. Clicking "Run Pipeline" invokes POST `/scoring/{id}/pipeline`.
5. **Background Monitoring:** The recruiter is redirected to `/recruiter/tasks`. They monitor progress through stages (`ACQUIRING`, `SOURCING`, `PRE_SCORING`, `SYNCHRONIZING`, `DEEP_SCORING`).
6. **Shortlist Review:** When the task completes, the recruiter navigates to `/recruiter/job-descriptions/{id}/candidates`. They review candidates sorted by final score.
7. **Candidate Evaluation:** Recruiter clicks on a candidate to view their evaluation board. They examine matched skills, missing mandatory skills, experience level, employment recency, and AI-generated strengths and weaknesses. The recruiter records internal notes.
8. **Shortlist Sharing:** Recruiter selects a subset of candidates and clicks "Share Shortlist". In the dialog box, they write notes for each candidate and click share. This transitions the candidates' pipeline stage to `SHARED` and alerts the Hiring Manager.

### Hiring Manager Journey
1. **Login:** Hiring Manager logs in and is redirected to `/hm/shared-campaigns`.
2. **Campaign Selection:** HM reviews the list of campaigns with shared candidates and selects a campaign to open `/hm/shared-campaigns/{job_description_id}`.
3. **Shared Board Review:** The HM views candidates shared for this campaign, alongside recruiter notes and overall suitability scores.
4. **Candidate Review:** HM clicks on a candidate. They review the candidate's parsed work history, education alignment, and detailed skill match quality.
5. **Decision Submission:** HM selects a decision:
   - **Reject:** Enters remarks and submits. The candidate's decision is set to `REJECTED`.
   - **Approve:** Enters remarks and submits. The decision is set to `APPROVED`.
6. **Interview Scheduling:** If approved, the HM schedules an interview, inputting the link, date/time, timezone, and invitation message. The system sets the decision to `INTERVIEW_SENT`, updates the pipeline stage to `INTERVIEW_SCHEDULED`, and emails the candidate.

---

## 6. Scope

### In Scope
- **Extraction and Structuring:** Parsing unstructured job descriptions into schema-conforming profiles via Hugging Face API.
- **Adaptive Web Scraping:** Sourcing resume listings from PostJobFree via dynamic query optimization and BeautifulSoup parsing.
- **Resume Information Extraction:** Converting raw resume text into structured candidate records using ChatGroq.
- **Semantic Filtering:** Performing quick pre-screening on candidates to filter out low-matching profiles using a semantic pre-scoring model.
- **Deep Match Assessment:** Execution of deep scoring algorithms that calculate a final suitability score (out of 100).
- **Asynchronous Workflows:** Queueing pipeline tasks in Redis and executing them via Celery workers with transactional database updates.
- **Collaborative Sharing and Decisioning:** Recruiter-to-HM sharing mechanisms, review forms, and meeting scheduling tools.
- **Fail-safe Security:** OTP password-reset services stored in Redis and sent via SMTP.

### Out of Scope
- **Version Management of Job Descriptions:** The system does not support versioning of JDs. Modifying an existing JD overwrites the database record, and historical revisions are not preserved.
- **Comparing Multiple JD Versions:** There is no mechanism to compare changes between historical job descriptions.
- **Candidate Evaluation History Across JD Revisions:** Candidate scores are computed based on the current state of a JD. Historical candidate scores are not archived when a JD is updated.
- **Direct Candidate Messaging/Chat:** No internal chat interface exists. Communication is restricted to email-based notifications.
- **Direct Interview Execution:** The system does not host video interviews; it only stores meeting links and sends invitations.

---

## 7. Assumptions & Constraints

- **API Access & Key Integrity:** The system relies on Groq and Hugging Face APIs. Valid, unexpired keys must be supplied. Groq requests are constrained by token/request rate limits.
- **Third-Party HTML Stability:** Sourcing relies on scraping PostJobFree HTML structures. Changes to PostJobFree's CSS selectors or DOM structure will break the BeautifulSoup parsers.
- **Host System Configuration:** Local SMTP credentials or Brevo API keys must be configured for email notifications to function.
- **Data Locality:** Local databases must be running and initialized with master data (employment types and job description statuses) for JDs to save correctly.
- **Background Worker Availability:** If Celery worker processes are not running, background tasks will remain queued in Redis indefinitely.

---

## 8. System Architecture

The Talent Finder system is built as a microservices architecture composed of a React single-page application, a main server API, a candidate sourcing service, PostgreSQL databases, and Redis for background queuing.

> Architecture Diagram: (To be added)

### Components and Communication Channels
- **Frontend Client:** React SPA built with Vite. Communicates with the Main Server API via HTTP REST.
- **Main Server:** FastAPI backend that handles authentication, job description management, and pipeline orchestration. Communicates with:
  - **PostgreSQL Database:** Main persistent storage for users, JDs, candidates, scores, pipelines, and notifications.
  - **Redis:** Used as the message broker and result backend for Celery, and for caching active OTP tokens.
  - **Sourcing Service:** FastAPI microservice queried via HTTP REST for candidate search and details retrieval.
- **Sourcing Service:** FastAPI microservice managing external candidate search and resume scraping. Communicates with:
  - **PostgreSQL Database:** Sourcing database storing scraped candidate profiles.
  - **PostJobFree:** Scraped over HTTPS.
  - **Groq API:** Interacted with via ChatGroq (with rotational key management) to parse unstructured resume texts.
- **Celery Worker:** Asynchronous task executor sharing the Server codebase. Pulls tasks from Redis, writes results to the PostgreSQL database, and triggers notification emails.

---

## 9. Detailed Component Responsibilities

### Server (FastAPI API)
- **Directory:** `/server`
- **Responsibilities:**
  - Exposes REST endpoints for authentication, JD CRUD operations, candidate list queries, notes updates, shortlist sharing, and interview scheduling.
  - Initiates background task executions by queueing tasks in Celery.
  - Provides dependencies for database session creation, cookie-based JWT authentication, and user role validation.
  - Manages database transactions across the `usecase` logical database.

### Sourcing Service (FastAPI Microservice)
- **Directory:** `/sourcing`
- **Responsibilities:**
  - Exposes endpoints `/candidates/search` and `/candidates/by-ids` for the Main Server.
  - Checks the local sourcing database before triggering external scraper loops.
  - Orchestrates adaptive scraping strategies using a query optimizer.
  - Parses PostJobFree search results and resume pages using BeautifulSoup.
  - Performs LLM resume parsing to extract structured candidates.
  - Manages database transactions across the `sourcing` logical database.

### Database Layer (PostgreSQL)
- **Directory:** `/infra/postgres`
- **Responsibilities:**
  - Main relational storage. Runs two separate logical databases: `usecase` (for client/server application state) and `sourcing` (for scraped candidate storage).
  - Configured with SQLAlchemy models for database mapping.

### Redis (Broker, Result Backend, & Cache)
- **Responsibilities:**
  - Acts as the Celery message broker, queueing pipeline execution tasks.
  - Stores Celery task results.
  - Caches OTP verification codes mapped to user emails with a strict 10-minute time-to-live (TTL).

### Celery Worker
- **Directory:** `/server/src/core/tasks.py`
- **Responsibilities:**
  - Executes the asynchronous, multi-stage pipeline: `ACQUIRING` -> `SOURCING` -> `PRE_SCORING` -> `SYNCHRONIZING` -> `DEEP_SCORING`.
  - Coordinates database status updates using a database-backed progress reporter.
  - Sends success or failure notifications and emails upon pipeline completion.

### Authentication & OTP Flow
- **Directory:** `/server/src/core/security`
- **Responsibilities:**
  - Generates and validates access, refresh, and password reset JWT tokens.
  - Validates secure, HttpOnly, secure, and SameSite cookies on incoming requests.
  - Generates 6-digit numeric OTP codes, stores them in Redis, and dispatches them via SMTP.

### Frontend (React SPA)
- **Directory:** `/client`
- **Responsibilities:**
  - Renders dashboards, task logs, JD details, candidate boards, and evaluation views.
  - Implements role-based routing (`/recruiter/*` and `/hm/*`).
  - Fetches data from the main server API, attaching credential cookies to requests.
  - Features real-time state feedback (e.g., polling task status).

---

## 10. End-to-End Pipeline

The evaluation pipeline is executed asynchronously. Below is the step-by-step runtime sequence:

> Sequence Diagram: (To be added)

### Pipeline Stages
1. **Recruiter Configuration:** The recruiter inputs parameters for a JD evaluation ($k$, $threshold$).
2. **Queueing (FastAPI → Redis):** Server receives the request, writes a `ScoringTask` record with status `PENDING` and stage `QUEUED` to PostgreSQL, and calls `run_scoring_pipeline_task.delay()`.
3. **Execution Start:** A Celery worker picks up the task, sets the task status to `RUNNING`, and initializes the progress reporter.
4. **Acquisition Stage (`ACQUIRING`):**
   - The worker queries the local PostgreSQL database for candidates already matching the JD.
   - If the local matching count is $\ge 10 \times k$, the system skips external sourcing.
   - If the local count is insufficient, the system sets the stage to `SOURCING` and requests candidates from the Sourcing Service.
5. **External Sourcing Stage (`SOURCING` - Optional):**
   - The Sourcing Service optimizes the search query (title, skills).
   - It scrapes resume URLs from PostJobFree, downloads the resume pages, extracts structured profiles via LLM, and saves them to the sourcing database.
   - Returns a consolidated list of candidates to the Celery worker.
6. **Deduplication:** The acquisition service merges local and sourced candidate summaries, removing duplicate candidate IDs.
7. **Pre-Scoring Stage (`PRE_SCORING`):**
   - The worker sends candidate summaries to the pre-scoring agent (`CandidatePrescoringClient`).
   - The agent returns a semantic score (0 to 100) for each profile.
8. **Threshold Filtering:** The worker filters out candidates with a pre-score below the user-defined `minimum_prescore_threshold`.
9. **Selection:** The remaining candidates are sorted by pre-score, and the top $k$ candidates are selected for deep evaluation.
10. **Synchronization Stage (`SYNCHRONIZING`):**
    - The worker passes the selected candidate IDs to the `CandidateSynchronizationService`.
    - The service checks the main DB. If a candidate profile is missing or stale ($> \text{refresh threshold}$), it calls the Sourcing Service to fetch full details.
    - Full details are persisted to the main server database.
11. **Deep Scoring Stage (`DEEP_SCORING`):**
    - The worker queries the main database for the full profile details of the top $k$ candidates.
    - Each profile is evaluated by `CandidateScoringClient` (ChatGroq) using a multi-dimensional rubric.
12. **Persistence:**
    - Suitability scores and AI explanations are written to the `candidate_job_scores` table.
    - Pipeline records are created or updated with the stage set to `SHORTLISTED`.
    - The JD status is transitioned to active.
13. **Completion & Notifications:**
    - Task status is updated to `SUCCESS` in the database.
    - An in-app notification is written to the database.
    - An email containing a link to the candidate board is sent to the recruiter.

---

## 11. Sourcing Pipeline

When candidate acquisition triggers external sourcing, the Sourcing Service executes an adaptive scraping loop:

> Sourcing Workflow Diagram: (To be added)

### Sourcing Flow Details
1. **Plan Initialization:** The service calls `CandidateSearchStrategyAgent` to generate a `SearchOptimizationPlan` (inferred role, representative title, and key representative skills).
2. **Strategy Execution Loop:** Sourcing continues until the required candidate count is met, a timeout is reached, or the search strategies are exhausted. The optimizer applies these strategies in sequence:
   - **Attempt 1: Representative Skills Strategy:** Search using the original job title and the optimized representative skills.
   - **Attempt 2: Generalized Title Strategy:** Search using the generalized job title and representative skills.
   - **Attempt 3: Single Core Skill Strategy:** Search using the generalized job title and only the first/most important representative skill.
   - **Attempt 4+: Title Only Strategy:** Search using the generalized job title, dropping all skill constraints to maximize recall.
3. **Scraping PostJobFree:**
   - Construct search URL: `https://www.postjobfree.com/resumes?q={skills}&t={title}&d={title}&r=10`
   - Download search results page and extract resume URLs.
4. **Resume Scraping & Extraction:**
   - For each resume URL:
     - Check if already processed to avoid duplicate page downloads.
     - Download the HTML page.
     - Parse the HTML layout using BeautifulSoup to isolate text.
     - Invoke `ResumeExtractionAgent` (ChatGroq) to structure the resume.
5. **Deduplication and Filters:**
     - Reject the resume if the LLM determines it is not in English.
     - Save the candidate profile to the database.
     - Skip if the candidate ID is in `exclude_candidate_ids` or already exists in the current session.
6. **Delay:** Wait 10 to 15 seconds between downloads to comply with rate limits.
7. **Return Results:** Once the target count is satisfied or the loop terminates, the sourced candidate profiles are returned.

---

## 12. Scoring Algorithm

The Candidate Scoring Engine uses a multi-dimensional formula. The maximum possible score is **100 points**.

$$\text{Final Score} = \text{Skills Score} + \text{Experience Score} + \text{Recency Score} + \text{Role Fit Score} + \text{Education Score}$$

### Scoring Rubric Breakdown

| Dimensions | Maximum Points | Calculation Method |
| :--- | :--- | :--- |
| **Skills Matching** | **40 points** | Split into Mandatory (28 pts) and Optional (12 pts) skills. Uses LLM-derived match quality weightings. |
| **Experience Fit** | **25 points** | Compares candidate years of experience against JD bounds, penalizing over-qualification. |
| **Employment Recency** | **15 points** | Evaluates current employment status or calculates decay based on years since last active role. |
| **Role Fit** | **12 points** | Semantic role alignment evaluated directly by ChatGroq. |
| **Education Alignment** | **8 points** | Degree and field match evaluation graded by ChatGroq. |

---

### Detailed Calculation Rules

#### 1. Skills Matching (40 Points Max)
The job description defines a list of mandatory skills and optional skills. The scoring agent compares the candidate's profile against this list and returns matches with a quality rating:
- `SkillName|1.0`: Exact match or candidate exceeds required level.
- `SkillName|0.75`: Candidate is one level below required proficiency.
- `SkillName|0.4`: Candidate is two or more levels below required proficiency.

- **Mandatory Skills Score (28 Points Max):**
  $$\text{Mandatory Score} = \left( \frac{\sum \text{Matched Mandatory Skill Quality}}{\text{Total JD Mandatory Skills Count}} \right) \times 28$$
- **Optional Skills Score (12 Points Max):**
  $$\text{Optional Score} = \left( \frac{\sum \text{Matched Optional Skill Quality}}{\text{Total JD Optional Skills Count}} \right) \times 12$$

#### 2. Experience Fit (25 Points Max)
Calculated deterministically using the candidate's total experience in years ($\text{candidate\_years} = \text{total\_experience\_months} / 12$):
- **Under-qualified:** If $\text{candidate\_years} < \text{min\_years}$ (from JD):
  $$\text{Experience Score} = \max\left(0, \frac{\text{candidate\_years}}{\max(\text{min\_years}, 1)} \times 25\right)$$
- **Fully Qualified:** If $\text{min\_years} \le \text{candidate\_years} \le \text{max\_years}$:
  $$\text{Experience Score} = 25$$
- **Over-qualified:** If $\text{candidate\_years} > \text{max\_years}$ (applying decay):
  $$\text{Decay} = \min\left((\text{candidate\_years} - \text{max\_years}) \times 0.5, 10\right)$$
  $$\text{Experience Score} = \max(15, 25 - \text{Decay})$$

#### 3. Employment Recency (15 Points Max)
Evaluates how recently the candidate was active in the workforce:
- No experience history: **0 points**
- Currently employed (`is_current == True`): **15 points**
- Unemployed: Calculate years since last job end date ($\text{years\_since}$):
  - $\text{years\_since} \le 1.0$: **13.5 points**
  - $\text{years\_since} \le 2.0$: **11.25 points**
  - $\text{years\_since} \le 3.0$: **8.25 points**
  - $\text{years\_since} \le 4.0$: **5.25 points**
  - $\text{years\_since} > 4.0$: **3.5 points**

#### 4. Role Fit (12 Points Max)
Evaluated directly by ChatGroq based on resume context:
- `12` = Excellent alignment
- `6` = Moderate alignment
- `0` = No alignment

#### 5. Education Alignment (8 Points Max)
Evaluated directly by ChatGroq based on credentials:
- `8` = Exact degree and field match
- `7` = Higher qualification than required
- `6` = Related field match
- `4` = Same level, unrelated field
- `0` = Mismatch/poor match

---

## 13. AI Components

The system coordinates several specialized AI agents, prompts, and models:

### 1. Job Description Extraction Agent
- **Model:** `meta-llama/Llama-3.3-70B-Instruct` (hosted on Hugging Face).
- **Purpose:** Extracts structured fields from raw text job descriptions.
- **Inputs:** Raw job description text.
- **Outputs:** JSON object mapping to `JobDescriptionExtraction` (title, department, purpose, responsibilities, experience range, skills, qualifications).
- **Prompting Rule:** Uses `JOB_DESCRIPTION_EXTRACTION_PROMPT`. Isolates experience bounds, and extracts skill names while preserving proficiency context (e.g. "Basic Python", "Expert Kubernetes").

### 2. Candidate Search Query Agent
- **Model:** ChatGroq (`llama-3.3-70b-versatile`).
- **Purpose:** Broadens and optimizes structured JD requirements to maximize database recall.
- **Inputs:** Structured JD title, skills list, and minimum experience.
- **Outputs:** Optimized search query containing generalized job title and canonical skill terms (e.g., removing "Advanced" or "Basic" qualifiers).
- **Prompting Rule:** Uses `CANDIDATE_SEARCH_QUERY_PROMPT`. Generalizes job titles (e.g., "Software Development Engineer II" -> "Software Engineer").

### 3. Candidate Search Strategy Agent
- **Model:** ChatGroq (`llama-3.3-70b-versatile`).
- **Purpose:** Analyzes a search query to generate an optimization plan for external scraper queries.
- **Inputs:** Sourcing search query requests.
- **Outputs:** `SearchOptimizationPlan` (inferred hiring archetype, representative title, prioritized representative skills, and rationale).
- **Prompting Rule:** Groups queries into a single hiring archetype. Focuses on the 2-3 defining technologies.

### 4. Resume Extraction Agent
- **Model:** ChatGroq (`llama-3.3-70b-versatile`).
- **Purpose:** Extracts candidate profile data from raw scraped resume texts.
- **Inputs:** Raw resume text, source URL.
- **Outputs:** JSON object conforming to `ResumeCandidateOutput` (full name, phone, email, skills, experiences, educations).
- **Prompting Rule:** Uses `RESUME_EXTRACTION_PROMPT` combined with validation rules. Inspects if the resume is in English, preserves mentioned skill proficiencies, and formats dates.

### 5. Candidate Pre-Scoring Agent
- **Model:** ChatGroq (`llama-3.3-70b-versatile`).
- **Purpose:** Conducts lightweight semantic screening on candidate profiles.
- **Inputs:** Compressed candidate profiles and compressed JD details.
- **Outputs:** `CandidatePrescoreBatchOutput` (list of candidate IDs and preliminary match scores from 0 to 100).
- **Prompting Rule:** Uses `CANDIDATE_PRESCORING_PROMPT`. Instructs the model to use the full scoring scale.

### 6. Candidate Scoring Agent (Deep Scoring)
- **Model:** ChatGroq (`llama-3.3-70b-versatile`).
- **Purpose:** Performs multi-dimensional evaluation of a candidate profile against a JD.
- **Inputs:** Full candidate profile and job description specifications.
- **Outputs:** `CandidateEvaluationOutput` (matched mandatory skills with pipe-delimited quality ratings, matched optional skills with pipe-delimited quality ratings, missing mandatory skills, role fit score, education score, confidence rating, and explanation texts).
- **Prompting Rule:** Uses `CANDIDATE_DEEP_SCORING_PROMPT`. Enforces strict matching rules for mandatory skills.

---

## 14. Database Design

The databases run on PostgreSQL. Below is the relational structure of the main `usecase` database:

### Core Tables & Entities

#### 1. `users`
- Tracks recruiters and hiring managers.
- **Fields:** `id` (UUID, PK), `name` (String), `email` (String, Unique), `password_hash` (String), `role` (String: "recruiter" or "hiring_manager"), `created_at` (DateTime), `last_login` (DateTime, Nullable).

#### 2. `job_descriptions`
- Stores campaign requirements.
- **Fields:** `id` (UUID, PK), `recruiter_id` (FK -> `users.id`), `hiring_manager_id` (FK -> `users.id`, Nullable), `title` (String), `department` (String, Nullable), `job_purpose` (Text), `responsibilities` (Text), `min_experience` (Int), `max_experience` (Int), `location` (String), `employment_type_id` (FK -> `employment_types.id`), `education_requirement` (String), `preferred_qualifications` (Text, Nullable), `status_id` (FK -> `job_description_statuses.id`), `raw_job_description` (Text, Nullable), `created_at` (DateTime), `updated_at` (DateTime).

#### 3. `jd_skills`
- Skills associated with a JD.
- **Fields:** `id` (UUID, PK), `jd_id` (FK -> `job_descriptions.id`, Cascade Delete), `skill_name` (String), `is_mandatory` (Boolean).

#### 4. `candidates`
- Parsed candidate profiles.
- **Fields:** `id` (UUID, PK), `full_name` (String), `email` (String, Nullable), `phone` (String, Nullable), `current_title` (String, Nullable), `location` (String, Nullable), `summary` (Text, Nullable), `resume_text` (Text, Nullable), `resume_hash` (String, Unique, Nullable), `source_type` (String), `total_experience_months` (Int), `created_at` (DateTime), `updated_at` (DateTime).

#### 5. `candidate_skills`
- Skills associated with a candidate.
- **Fields:** `id` (UUID, PK), `candidate_id` (FK -> `candidates.id`, Cascade Delete), `skill_name` (String), `is_primary` (Boolean).

#### 6. `candidate_experiences`
- Candidate employment history records.
- **Fields:** `id` (UUID, PK), `candidate_id` (FK -> `candidates.id`, Cascade Delete), `company_name` (String), `title` (String), `description` (Text, Nullable), `start_date` (Date), `end_date` (Date, Nullable), `is_current` (Boolean).

#### 7. `candidate_experience_skills`
- Join table linking skills to candidate experience blocks.
- **Fields:** `id` (UUID, PK), `experience_id` (FK -> `candidate_experiences.id`, Cascade Delete), `skill_name` (String).

#### 8. `candidate_educations`
- Candidate educational background records.
- **Fields:** `id` (UUID, PK), `candidate_id` (FK -> `candidates.id`, Cascade Delete), `institution_name` (String), `degree` (String), `field_of_study` (String), `start_date` (Date), `end_date` (Date, Nullable).

#### 9. `candidate_job_scores`
- Match results for candidate-JD evaluations.
- **Fields:** `id` (UUID, PK), `candidate_id` (FK -> `candidates.id`, Cascade Delete), `job_description_id` (FK -> `job_descriptions.id`, Cascade Delete), `final_score` (Float), `confidence` (Float), `skills_score` (Float), `experience_score` (Float), `recency_score` (Float), `role_fit_score` (Float), `education_score` (Float), `matched_mandatory_skills` (JSON), `matched_optional_skills` (JSON), `missing_mandatory_skills` (JSON), `explanation` (JSON), `created_at` (DateTime), `updated_at` (DateTime).
- **Constraints:** Unique Index on `(candidate_id, job_description_id)`.

#### 10. `pipeline`
- Candidate hiring pipeline tracking.
- **Fields:** `id` (UUID, PK), `candidate_id` (FK -> `candidates.id`, Cascade Delete), `jd_id` (FK -> `job_descriptions.id`, Cascade Delete), `stage` (String: e.g., "SHORTLISTED", "SHARED", "INTERVIEW_SCHEDULED"), `recruiter_notes` (Text, Nullable), `hiring_manager_notes` (Text, Nullable), `shared_with_hiring_manager` (Boolean), `shared_at` (DateTime, Nullable), `hm_decision` (String/Enum: "PENDING", "INTERVIEW_SENT", "REJECTED"), `interview_link` (String, Nullable), `interview_datetime` (DateTime, Nullable), `interview_timezone` (String, Nullable), `interview_message` (Text, Nullable), `interview_sent_at` (DateTime, Nullable), `created_at` (DateTime).
- **Constraints:** Unique Index on `(candidate_id, jd_id)`.

#### 11. `scoring_tasks`
- Background execution tracking.
- **Fields:** `id` (UUID, PK), `celery_task_id` (String, Nullable), `recruiter_id` (FK -> `users.id`), `job_description_id` (FK -> `job_descriptions.id`), `status` (String: "PENDING", "RUNNING", "SUCCESS", "FAILED"), `current_stage` (String: e.g. "QUEUED", "ACQUIRING", "SOURCING", "PRE_SCORING", "SYNCHRONIZING", "DEEP_SCORING", "COMPLETED", "FAILED"), `cancel_requested` (Boolean), `matched_candidate_count` (Int, Nullable), `eligible_candidate_count` (Int, Nullable), `selected_candidate_count` (Int, Nullable), `created_at` (DateTime), `started_at` (DateTime, Nullable), `completed_at` (DateTime, Nullable), `error_message` (String, Nullable), `error_code` (String, Nullable), `final_response_payload` (JSON, Nullable).

#### 12. `notifications`
- In-app notification dispatcher.
- **Fields:** `id` (UUID, PK), `user_id` (FK -> `users.id`, Cascade Delete), `notification_type` (Enum: "SCORING_COMPLETED", "SYSTEM"), `title` (String), `message` (String), `target_url` (String, Nullable), `is_read` (Boolean), `metadata_` (JSON, Nullable), `created_at` (DateTime).

---

## 15. API Overview

The backend exposes a REST API built with FastAPI. Below are the key endpoints:

### Authentication & OTP
- `POST /auth/login`: Validates user credentials. Sets secure, HttpOnly, secure cookies `access_token` and `refresh_token`. Returns the authenticated user context.
- `POST /auth/refresh`: Validates the `refresh_token` cookie and issues a new access token cookie.
- `POST /auth/logout`: Deletes `access_token` and `refresh_token` cookies.
- `POST /otp/forgot-password`: Generates an OTP, stores it in Redis, and dispatches it via SMTP.
- `POST /otp/verify-otp`: Validates the OTP against the Redis store. Returns a JWT password reset token on success.
- `POST /auth/reset-password`: Resets the password using the reset token.

### Job Description Management
- `POST /job-descriptions`: Creates a new structured JD.
- `GET /job-descriptions`: Lists JDs for the logged-in user.
- `GET /job-descriptions/{id}`: Retrieves details of a specific JD.
- `PUT /job-descriptions/{id}`: Overwrites JD fields.
- `POST /job-descriptions/extract`: Extracts structured details from raw JD text.

### Candidate Sourcing & Evaluation
- `POST /scoring/candidates/import`: Manually imports candidate resume text for a JD. Parses and stores it in the database.
- `POST /scoring/{job_description_id}/pipeline`: Enqueues an evaluation pipeline run. Creates a `ScoringTask` and triggers a Celery task.
- `GET /scoring/tasks`: Lists background tasks for the logged-in recruiter (recovers stale tasks first).
- `GET /scoring/tasks/{task_id}`: Gets the status and current stage of a background task.
- `GET /scoring/tasks/{task_id}/result`: Retrieves the final candidate pool from a successful task. Returns `202 Accepted` if still running.

### Shortlists & Collaboration
- `GET /scoring/jobs/{job_description_id}/candidates`: Retrieves scored, ranked candidates.
- `GET /scoring/jobs/{job_description_id}/candidates/{candidate_id}/board`: Retrieves the detailed candidate evaluation board.
- `PATCH /scoring/jobs/{job_description_id}/candidates/{candidate_id}/pipeline-notes`: Updates recruiter notes on a candidate.
- `PATCH /scoring/jobs/{job_description_id}/pipeline-stage`: Bulk updates the stage of candidates in the pipeline (e.g., shortlisting).
- `POST /scoring/recruiter/job-descriptions/{job_description_id}/share`: Shares selected candidates with the Hiring Manager.
- `GET /scoring/hm/campaigns`: Lists campaigns shared with the logged-in Hiring Manager.
- `GET /scoring/hm/campaigns/{job_description_id}/candidates`: Lists shared candidates for a campaign.
- `POST /scoring/hm/campaigns/{job_description_id}/candidates/{candidate_id}/review`: Submits a review decision (approve/reject) and remarks.
- `POST /scoring/hm/campaigns/{job_description_id}/candidates/{candidate_id}/schedule-interview`: Schedules an interview and emails the candidate.

---

## 16. Authentication

### JWT Design & Token Structure
The system uses JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).
- **Access Tokens:** Contains the user's ID (`sub`), role, and type (`access`). Expires after 60 minutes.
- **Refresh Tokens:** Contains the user's ID (`sub`) and type (`refresh`). Expires after 30 days.
- **Reset Password Tokens:** Contains the user's ID (`sub`) and type (`password_reset`). Issued upon OTP verification and expires after 10 minutes.

### Cookie Handling
Tokens are stored in cookies rather than localStorage to mitigate XSS risks:
- `HttpOnly`: Checked to block JavaScript access.
- `Secure`: Transmitted only over HTTPS.
- `SameSite=lax`: Mitigates CSRF vulnerabilities.

### OTP (One-Time Password) Lifecycle
1. **Request:** The user requests password recovery. The server generates a random 6-digit number.
2. **Cache Storage:** The server writes a JSON record `{ "otp": "123456", "expires_at": "ISO_TIMESTAMP" }` to Redis under the key `otp:{email}` with a 10-minute expiry (TTL = 600s).
3. **Delivery:** The code is sent to the user via SMTP.
4. **Verification:** The user submits the code. The server verifies it against Redis. If valid, the code is deleted, and a JWT password reset token is issued.

### Role-Based Access Control (RBAC)
- **Recruiter Role (`recruiter`):** Authorized to manage JDs, trigger background scoring, write recruiter notes, and share candidates.
- **Hiring Manager Role (`hiring_manager`):** Authorized to view shared campaigns, submit approvals/rejections, and schedule interviews.
- **Enforcement:** Enforced in the FastAPI API using route dependencies (`get_authenticated_user_context`) and in the React frontend using `<ProtectedRoute>`.

---

## 17. Background Processing

### Celery & Redis Integration
Asynchronous execution is managed using Celery and Redis. The Celery worker runs in its own Docker container, using the same codebase and database models as the main API.

### Task Lifecycle & DB Synchronization
1. **Enqueued:** A task is written to the database with state `PENDING` and enqueued in Redis.
2. **Running:** The worker starts the task, setting the status to `RUNNING` and recording the start timestamp.
3. **Stage Tracking:** As the task progresses, the database is updated with the current stage (e.g., `SOURCING`, `DEEP_SCORING`).
4. **Success:** Upon completion, the worker writes the candidate counts and payload, updates the status to `SUCCESS`, and records the completion timestamp.
5. **Failure:** If an exception occurs, the worker writes the traceback to the `error_message` field, sets the status to `FAILED`, and releases resources.

### Real-Time Progress Reporting
- The API does not use WebSockets for progress tracking.
- The `DatabaseProgressReporter` class writes stage updates directly to the database.
- The frontend client polls `/scoring/tasks/{task_id}` to track progress and update the UI.

### Stale Task Auto-Recovery
If a Celery worker crashes, tasks in the `PENDING` or `RUNNING` states can hang. To prevent this:
- Every time a task list or task status endpoint is queried, `task_service.recover_stale_tasks(timeout_minutes)` is executed.
- It finds tasks that have been running for longer than the timeout threshold (defined by `SCORING_TASK_TIMEOUT_MINUTES`, defaulting to 15 minutes).
- These tasks are transitioned to `FAILED` with the error code `WORKER_UNAVAILABLE` and error message `"Background worker became unavailable..."`, and the recruiter is notified.

---

## 18. Docker Architecture

The application is deployed using Docker Compose, which configures networking, volumes, and startup dependencies.

### Container Definitions

#### 1. `postgres` (postgres:17-alpine)
- **Role:** Persistent database storage.
- **Initialization:** Executes `./infra/postgres/init.sql` on first launch to create the `usecase` and `sourcing` databases.
- **Volume:** Mounts `postgres_data` to persist data.

#### 2. `redis` (redis:7-alpine)
- **Role:** Message broker for Celery and cache for OTP records.

#### 3. `sourcing`
- **Role:** FastAPI microservice for scraping and resume parsing.
- **Dependencies:** Starts only after `postgres` is healthy.
- **Environment:** Connected to PostgreSQL (`sourcing` database).

#### 4. `server`
- **Role:** Main API backend.
- **Dependencies:** Starts only after `postgres`, `redis`, and `sourcing` are healthy.
- **Ports:** Exposes port `8000`.
- **Environment:** Connected to PostgreSQL (`usecase` database) and Redis.

#### 5. `celery-worker`
- **Role:** Asynchronous task processor.
- **Image:** Shares the `server` container image.
- **Command:** `celery -A src.core.celery_app worker --loglevel=info --concurrency=2`
- **Dependencies:** Starts only after `postgres` and `redis` are healthy.

#### 6. `client`
- **Role:** Frontend web client.
- **Ports:** Exposes port `5173`.
- **Dependencies:** Starts only after `server` is healthy.

### Container Communication & Networking
- All services reside on a custom bridge network named `talent-finder`.
- Services communicate using Docker's internal DNS (e.g., the server connects to the database via `postgres:5432` and the sourcing microservice via `http://sourcing:8001`).
- The browser connects to the host on port `5173` for the frontend and sends API requests directly to `http://localhost:8000`.

---

## 19. Error Handling

### 1. LLM API Resilience
- **Rotational Keys:** Sourcing uses the `RotationalChatGroq` client, which cycles through configured API keys when a `RateLimitError` (429) occurs.
- **Graceful Failbacks:** If all API keys are exhausted, a fallback response is returned (e.g., returning an empty candidate profile instead of crashing).

### 2. Sourcing & Scraping Resilience
- **Network Failures:** If PostJobFree is down or times out, the scraper logs the error and continues to the next candidate URL.
- **Timeout Limits:** The scraping loop is wrapped in a timeout handler (`SOURCING_LOOP_TIMEOUT_SECONDS = 260.0`). If the timeout is reached, the loop exits early, and any candidates scraped up to that point are processed.

### 3. Database Resilience
- **Scoring Pipeline Transactions:** Scoring runs are executed in a transaction block. If persisting scores to the database fails, the transaction is rolled back.
- **Task Failure Persistence:** If a task fails, a new transaction block and database session are opened to record the failure state in the database, ensuring the error is saved even if the main pipeline transaction rolled back.

### 4. Notification Resilience
- Email dispatches are treated as best-effort operations. If SMTP or Brevo API requests fail, the error is logged, but the pipeline execution completes successfully.

---

## 20. Performance Considerations

- **Database Performance:** Core queries lookup records by candidate ID, JD ID, and task ID. Unique constraints and foreign keys are indexed.
- **Connection Reuse:** The backend uses `httpx.AsyncClient` inside `CandidateSearchClient` to reuse TCP connections, minimizing connection overhead.
- **Deduplication:** Candidate profiles are deduplicated before pre-scoring and deep scoring using candidate ID and resume hash lookups.
- **Concurrency Control:** The Celery worker runs with `--concurrency=2` to prevent CPU and API key rate limit exhaustion.
- **Scraper Delays:** The sourcing service adds a random delay (10 to 15 seconds) between HTTP requests to respect target site rate limits.

---

## 21. Non-Functional Requirements

- **Reliability:** Background tasks are isolated from the main web server. Stale tasks are recovered automatically, and database transactions are protected by rollbacks.
- **Security:** Access control is enforced via JWT HttpOnly cookies, secure CORS origins, parameter validation, and encrypted password storage.
- **Scalability:** Sourcing and scoring tasks are processed asynchronously by Celery workers, allowing the API to remain responsive under load.
- **Maintainability:** Relies on clear folder structures (models, services, routes), standard formatting rules, type hints, and dependencies.
- **Observability:** Structural logs are recorded across all major services, tracing tasks from creation to termination.

---

## 22. Testing Strategy

The test suite consists of integration scripts placed directly in the service roots:

### Test Suite Structure
- **Pipeline Integration Tests (`test_pipeline_integration.py`):** Mocks the Groq API and sourcing client to test pipeline execution under various scenarios (e.g., sufficient local candidates, missing candidates).
- **Resilience Tests (`test_pipeline_resilience.py` / `test_stale_task_recovery.py`):** Simulates database errors and worker crashes to verify transactional rollbacks and stale task recovery.
- **Scoring Logic Tests (`test_proficiency_scoring.py` / `test_prescore_threshold.py`):** Asserts the accuracy of the experience decay, recency calculations, and pre-scoring thresholds.
- **Authentication Tests (`test_auth_flow.py`):** Validates password hashing, JWT creation, cookie verification, and OTP workflows.

### Execution
Integration tests are executed using python or pytest in local development environments:
```bash
python test_pipeline_integration.py
```

---

## 23. Future Enhancements

The following features are planned for future development and are not supported in the current implementation:
1. **JD Version History:** A history log to track changes to job descriptions, allowing recruiters to revert to previous versions.
2. **JD Version Comparison:** A visual diffing tool to compare requirements across different versions of a JD.
3. **Candidate Score History:** The ability to preserve and compare a candidate's suitability scores across different versions of a JD.
4. **Third-Party Integrations:** Integrating with other resume databases (e.g., Indeed, LinkedIn) to broaden candidate sourcing options.
5. **Campaign Analytics:** A dashboard for recruiters to analyze candidate conversion rates and pipeline velocity.
