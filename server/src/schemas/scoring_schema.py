from datetime import date
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
