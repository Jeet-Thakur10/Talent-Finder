from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# (done, parsed candidate)
class ParsedSkill(BaseModel):
    skill_name: str


class ParsedExperience(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    skills: list[ParsedSkill] = Field(default_factory=list)


class ParsedEducation(BaseModel):
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ParsedCandidateProfile(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[ParsedSkill] = Field(default_factory=list)
    experiences: list[ParsedExperience] = Field(default_factory=list)
    educations: list[ParsedEducation] = Field(default_factory=list)
    total_experience_months: int = 0

class CandidateImportRequest(BaseModel):
    job_description_id: UUID
    resume_text: str = Field(min_length=20)


class ResumeSkillOutput(BaseModel):
    skill_name: str

class ResumeExperienceOutput(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    skills: list[ResumeSkillOutput] = Field(default_factory=list)


class ResumeEducationOutput(BaseModel):
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ResumeCandidateOutput(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[ResumeSkillOutput] = Field(default_factory=list)
    experiences: list[ResumeExperienceOutput] = Field(default_factory=list)
    educations: list[ResumeEducationOutput] = Field(default_factory=list)
    total_experience_months: int = 0


# LLM based resume scoring

class CandidateSkillInput(BaseModel):
    skill_name: str


class CandidateExperienceInput(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False

    skills: list[CandidateSkillInput] = []


class CandidateEducationInput(BaseModel):
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CandidateScoringInput(BaseModel):
    candidate_id: UUID

    full_name: str

    current_title: str | None = None
    location: str | None = None
    summary: str | None = None

    total_experience_months: int

    skills: list[CandidateSkillInput]
    experiences: list[CandidateExperienceInput]
    educations: list[CandidateEducationInput]


class JobSkillInput(BaseModel):
    skill_name: str
    is_mandatory: bool


class JobDescriptionScoringInput(BaseModel):
    job_description_id: UUID

    title: str
    department: str | None = None

    job_purpose: str

    responsibilities: str

    min_experience: int
    max_experience: int

    location: str

    education_requirement: str

    preferred_qualifications: str | None = None

    skills: list[JobSkillInput]

class CandidateScoreExplanation(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]

# adding an experimental evaluation schema

class CandidateEvaluationOutput(BaseModel):
    candidate_id: UUID

    confidence: float
    role_fit_score: float
    education_score: float

    matched_mandatory_skills: list[str]
    matched_optional_skills: list[str]
    missing_mandatory_skills: list[str]

    explanation: CandidateScoreExplanation


class CandidateScoreOutput(BaseModel):
    candidate_id: UUID

    final_score: float

    confidence: float

    skills_score: float
    experience_score: float
    recency_score: float
    role_fit_score: float
    education_score: float

    matched_mandatory_skills: list[str]
    matched_optional_skills: list[str]
    missing_mandatory_skills: list[str]

    explanation: CandidateScoreExplanation


class CandidateBatchScoreOutput(BaseModel):
    scores: list[CandidateScoreOutput]


class CandidateSkillResponse(BaseModel):
    id: UUID
    skill_name: str
    is_primary: bool


class CandidateExperienceSkillResponse(BaseModel):
    id: UUID
    skill_name: str


class CandidateExperienceResponse(BaseModel):
    id: UUID
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    skills: list[CandidateExperienceSkillResponse] = Field(
        default_factory=list,
    )


class CandidateEducationResponse(BaseModel):
    id: UUID
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    end_date: date | None = None


class ParsedCandidateProfile(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[ParsedSkill] = Field(default_factory=list)
    experiences: list[ParsedExperience] = Field(default_factory=list)
    educations: list[ParsedEducation] = Field(default_factory=list)
    total_experience_months: int = 0

class CandidateImportRequest(BaseModel):
    job_description_id: UUID
    resume_text: str = Field(min_length=20)


class ResumeSkillOutput(BaseModel):
    skill_name: str

class ResumeExperienceOutput(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    skills: list[ResumeSkillOutput] = Field(default_factory=list)


class ResumeEducationOutput(BaseModel):
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ResumeCandidateOutput(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[ResumeSkillOutput] = Field(default_factory=list)
    experiences: list[ResumeExperienceOutput] = Field(default_factory=list)
    educations: list[ResumeEducationOutput] = Field(default_factory=list)
    total_experience_months: int = 0


# LLM based resume scoring

class CandidateSkillInput(BaseModel):
    skill_name: str


class CandidateExperienceInput(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False

    skills: list[CandidateSkillInput] = []


class CandidateEducationInput(BaseModel):
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CandidateScoringInput(BaseModel):
    candidate_id: UUID

    full_name: str

    current_title: str | None = None
    location: str | None = None
    summary: str | None = None

    total_experience_months: int

    skills: list[CandidateSkillInput]
    experiences: list[CandidateExperienceInput]
    educations: list[CandidateEducationInput]


class JobSkillInput(BaseModel):
    skill_name: str
    is_mandatory: bool


class JobDescriptionScoringInput(BaseModel):
    job_description_id: UUID

    title: str
    department: str | None = None

    job_purpose: str

    responsibilities: str

    min_experience: int
    max_experience: int

    location: str

    education_requirement: str

    preferred_qualifications: str | None = None

    skills: list[JobSkillInput]

class CandidateScoreExplanation(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]

# adding an experimental evaluation schema

class CandidateEvaluationOutput(BaseModel):
    candidate_id: UUID

    confidence: float
    role_fit_score: float
    education_score: float

    matched_mandatory_skills: list[str]
    matched_optional_skills: list[str]
    missing_mandatory_skills: list[str]

    explanation: CandidateScoreExplanation


class CandidateScoreOutput(BaseModel):
    candidate_id: UUID

    final_score: float

    confidence: float

    skills_score: float
    experience_score: float
    recency_score: float
    role_fit_score: float
    education_score: float

    matched_mandatory_skills: list[str]
    matched_optional_skills: list[str]
    missing_mandatory_skills: list[str]

    explanation: CandidateScoreExplanation


class CandidateBatchScoreOutput(BaseModel):
    scores: list[CandidateScoreOutput]


class CandidateSkillResponse(BaseModel):
    id: UUID
    skill_name: str
    is_primary: bool


class CandidateExperienceSkillResponse(BaseModel):
    id: UUID
    skill_name: str


class CandidateExperienceResponse(BaseModel):
    id: UUID
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    skills: list[CandidateExperienceSkillResponse] = Field(
        default_factory=list,
    )


class CandidateEducationResponse(BaseModel):
    id: UUID
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CandidateDetailsResponse(BaseModel):
    id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None
    source_type: str
    total_experience_months: int
    resume_text: str | None = None
    created_at: datetime
    updated_at: datetime
    skills: list[CandidateSkillResponse] = Field(
        default_factory=list,
    )
    experiences: list[CandidateExperienceResponse] = Field(
        default_factory=list,
    )
    educations: list[CandidateEducationResponse] = Field(
        default_factory=list,
    )


class PipelineStageUpdateRequest(BaseModel):
    stage: str = Field(min_length=1)
    candidate_ids: list[UUID] = Field(
        min_length=1,
    )


class PipelineNotesUpdateRequest(BaseModel):
    recruiter_notes: str | None = None


class PipelineSnapshotResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    jd_id: UUID
    stage: str
    recruiter_notes: str | None = None
    hiring_manager_notes: str | None = None
    created_at: datetime
    hm_decision: Literal["PENDING", "INTERVIEW_SENT", "REJECTED"] | None = None
    interview_link: str | None = None
    interview_datetime: datetime | None = None
    interview_timezone: str | None = None
    interview_message: str | None = None
    interview_sent_at: datetime | None = None


class CandidateScoreBreakdownResponse(BaseModel):
    final_score: float
    skill_score: float
    experience_score: float
    recency_score: float
    role_fit_score: float
    education_score: float
    confidence: float
    explanation: CandidateScoreExplanation | dict[str, object]


class CandidateEvaluationBoardResponse(BaseModel):
    candidate: CandidateDetailsResponse
    pipeline: PipelineSnapshotResponse | None = None
    score: CandidateScoreBreakdownResponse | None = None


class CandidateScoreDetailBreakdown(BaseModel):
    skills: float
    experience: float
    recency: float
    role_fit: float
    education: float


class CandidateScoreResponse(BaseModel):
    candidate_id: UUID
    job_description_id: UUID
    final_score: float
    confidence: float
    breakdown: CandidateScoreDetailBreakdown
    matched_mandatory_skills: list[str]
    matched_optional_skills: list[str]
    missing_mandatory_skills: list[str]
    explanation: CandidateScoreExplanation | dict[str, object]
    updated_at: datetime


# prescoring schema
class CompressedCandidate(BaseModel):
    candidate_id: UUID
    profile_text: str


class CompressedJobDescription(BaseModel):
    job_description_id: UUID
    profile_text: str


class CandidatePrescoreOutput(BaseModel):
    candidate_id: UUID
    score: int



class CandidatePrescoreBatchOutput(BaseModel):
    scores: list[CandidatePrescoreOutput]


class PipelineExecutionRequest(BaseModel):
    confirm: bool = False
    k: int = Field(default=10, ge=1, le=25)
    minimum_prescore_threshold: int = Field(default=0, ge=0, le=100)


class PipelineCandidateResult(BaseModel):
    candidate_id: UUID
    full_name: str
    current_title: str | None = None
    location: str | None = None
    total_experience_months: int
    prescore_score: int | None = None
    prescore_rank: int | None = None
    final_score: float | None = None
    confidence: float | None = None
    matched_mandatory_skills: list[str] = Field(default_factory=list)
    matched_optional_skills: list[str] = Field(default_factory=list)
    missing_mandatory_skills: list[str] = Field(default_factory=list)
    stage: str = "PRE_SCORED"
    recruiter_notes: str | None = None
    hiring_manager_notes: str | None = None
    shared_with_hiring_manager: bool = False
    updated_at: datetime | None = None
    hm_decision: Literal["PENDING", "INTERVIEW_SENT", "REJECTED"] | None = None
    interview_link: str | None = None
    interview_datetime: datetime | None = None
    interview_timezone: str | None = None
    interview_message: str | None = None
    interview_sent_at: datetime | None = None


class PipelineExecutionResponse(BaseModel):
    stage: Literal["preview", "completed"]
    matched_candidate_count: int
    eligible_candidate_count: int | None = None
    selected_candidate_count: int | None = None
    top_k: int
    candidates: list[PipelineCandidateResult] = Field(
        default_factory=list,
    )


class PipelineEnqueueResponse(BaseModel):
    task_id: UUID
    status: str


class PipelineTaskStatusResponse(BaseModel):
    id: UUID
    job_description_id: UUID
    status: str
    current_stage: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    matched_candidate_count: int | None = None
    eligible_candidate_count: int | None = None
    selected_candidate_count: int | None = None
    job_description_title: str | None = None


# --- Hiring Manager Shortlist Sharing Schemas ---
from src.data.models.postgres.pipeline import HiringManagerDecision

class ShortlistShareRequest(BaseModel):
    candidate_ids: list[UUID]
    notes_by_candidate: dict[UUID, str] = Field(default_factory=dict)


class ShortlistShareResponse(BaseModel):
    message: str
    shared_candidate_count: int


class HiringManagerReviewRequest(BaseModel):
    decision: HiringManagerDecision
    remarks: str | None = None


class HiringManagerReviewResponse(BaseModel):
    message: str
    candidate_id: UUID
    hm_decision: HiringManagerDecision
    hiring_manager_notes: str | None = None


class SharedCampaignCandidateResponse(BaseModel):
    candidate_id: UUID
    full_name: str
    current_title: str | None = None
    total_experience_months: int
    location: str | None = None
    final_score: float | None = None
    recruiter_notes: str | None = None
    shared_at: datetime | None = None
    hm_decision: HiringManagerDecision
    hiring_manager_notes: str | None = None
    interview_link: str | None = None
    interview_datetime: datetime | None = None
    interview_timezone: str | None = None
    interview_message: str | None = None
    interview_sent_at: datetime | None = None


class HMCampaignResponse(BaseModel):
    id: UUID
    title: str
    department: str | None
    recruiter_name: str
    shared_at: datetime | None
    shared_candidate_count: int
    accepted_candidate_count: int
    rejected_candidate_count: int
    pending_candidate_count: int

class InterviewScheduleRequest(BaseModel):
    interview_link: str
    interview_datetime: datetime
    timezone: str
    message: str | None = None


class InterviewScheduleResponse(BaseModel):
    message: str
    candidate_id: UUID
    hm_decision: HiringManagerDecision
    interview_link: str
    interview_datetime: datetime
    interview_timezone: str
    interview_message: str | None = None
