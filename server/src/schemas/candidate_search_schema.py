from datetime import date, datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class CandidateSearchRequest(BaseModel):
    title: str
    skills: list[str]
    min_experience: int
    required_candidates: int = Field(
        validation_alias=AliasChoices("required_candidates", "min_candidates")
    )
    max_source_resumes: int
    exclude_candidate_ids: list[UUID] = Field(default_factory=list)


class CandidateSearchQueryOutput(BaseModel):
    title: str
    skills: list[str]
    min_experience: int


class CandidateSummary(BaseModel):
    candidate_id: UUID
    profile_text: str


class CandidateSearchResponse(BaseModel):
    candidates: list[CandidateSummary]


class CandidateSkillResponse(BaseModel):
    skill_name: str


class CandidateExperienceSkillResponse(BaseModel):
    skill_name: str


class CandidateExperienceResponse(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool
    skills: list[CandidateExperienceSkillResponse] = Field(default_factory=list)


class CandidateEducationResponse(BaseModel):
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
    total_experience_months: int
    source_type: str
    created_at: datetime
    updated_at: datetime
    skills: list[CandidateSkillResponse] = Field(default_factory=list)
    experiences: list[CandidateExperienceResponse] = Field(default_factory=list)
    educations: list[CandidateEducationResponse] = Field(default_factory=list)
