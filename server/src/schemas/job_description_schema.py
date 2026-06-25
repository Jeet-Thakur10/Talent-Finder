from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JDSkillCreateRequest(BaseModel):
    skill_name: str
    is_mandatory: bool = True


class JobDescriptionCreateRequest(BaseModel):
    title: str
    department: str | None = None
    job_purpose: str
    responsibilities: str
    min_experience: int = Field(ge=0)
    max_experience: int = Field(ge=0)
    location: str
    employment_type_id: UUID
    education_requirement: str
    preferred_qualifications: str | None = None
    skills: list[JDSkillCreateRequest]

class JDSkillResponse(BaseModel):
    id: UUID
    skill_name: str
    is_mandatory: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobDescriptionResponse(BaseModel):
    id: UUID
    title: str
    department: str | None
    job_purpose: str
    responsibilities: str
    min_experience: int
    max_experience: int
    location: str
    education_requirement: str
    preferred_qualifications: str | None
    employment_type_id: UUID
    status_id: UUID
    created_at: datetime
    updated_at: datetime
    skills: list[JDSkillResponse]

    model_config = ConfigDict(
        from_attributes=True,
    )

class EmploymentTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str


class JobDescriptionStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
