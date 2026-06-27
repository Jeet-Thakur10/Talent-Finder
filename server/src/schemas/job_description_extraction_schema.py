from pydantic import BaseModel, Field


class JobDescriptionSkill(BaseModel):
    skill_name: str
    is_mandatory: bool


class JobDescriptionExtraction(BaseModel):
    title: str | None = None
    department: str | None = None
    job_purpose: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    location: str | None = None
    min_experience: int | None = None
    max_experience: int | None = None
    education_requirement: str | None = None
    preferred_qualifications: list[str] = Field(default_factory=list)
    employment_type: str | None = None
    hiring_manager: str | None = None
    skills: list[JobDescriptionSkill] = Field(default_factory=list)
