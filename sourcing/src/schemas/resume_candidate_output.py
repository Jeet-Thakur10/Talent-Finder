from pydantic import BaseModel, Field
from datetime import date


class ResumeSkillOutput(BaseModel):
    skill_name: str


class ResumeExperienceOutput(BaseModel):
    company_name: str | None = None
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    skills: list[ResumeSkillOutput] = Field(
        default_factory=list,
    )


class ResumeEducationOutput(BaseModel):
    institution_name: str | None = None
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ResumeCandidateOutput(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None

    skills: list[ResumeSkillOutput] = Field(
        default_factory=list,
    )

    experiences: list[ResumeExperienceOutput] = Field(
        default_factory=list,
    )

    educations: list[ResumeEducationOutput] = Field(
        default_factory=list,
    )

    total_experience_months: int = 0