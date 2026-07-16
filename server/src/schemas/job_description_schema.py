from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JDSkillCreateRequest(BaseModel):
    skill_name: str = Field(min_length=1)
    is_mandatory: bool = True


class JobDescriptionWriteRequest(BaseModel):
    title: str
    department: str | None = None
    job_purpose: str
    responsibilities: str
    min_experience: int = Field(ge=0)
    max_experience: int | None = Field(default=None, ge=0)
    location: str
    employment_type_id: UUID
    education_requirement: str
    preferred_qualifications: str | None = None
    skills: list[JDSkillCreateRequest]
    hiring_manager_id: UUID | None = None
    raw_job_description: str | None = None

    @model_validator(mode="after")
    def validate_experience_range(self) -> "JobDescriptionWriteRequest":
        if (
            self.max_experience is not None
            and self.max_experience < self.min_experience
        ):
            raise ValueError(
                "max_experience must be greater than or equal to min_experience",
            )

        if not self.skills:
            raise ValueError(
                "At least one skill is required",
            )

        return self


class JobDescriptionCreateRequest(JobDescriptionWriteRequest):
    pass


class JobDescriptionUpdateRequest(JobDescriptionWriteRequest):
    pass


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
    max_experience: int | None
    location: str
    education_requirement: str
    preferred_qualifications: str | None
    employment_type_id: UUID
    status_id: UUID
    hiring_manager_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    skills: list[JDSkillResponse]
    raw_job_description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobDescriptionExtractResponse(BaseModel):
    id: UUID
    title: str
    department: str | None
    job_purpose: str
    responsibilities: str
    min_experience: int | None
    max_experience: int | None
    location: str
    education_requirement: str
    preferred_qualifications: str | None
    employment_type_id: UUID
    status_id: UUID
    hiring_manager_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    skills: list[JDSkillResponse]
    raw_job_description: str | None = None

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


class HiringManagerResponse(BaseModel):
    id: UUID
    name: str
    email: str


class JobDescriptionExtractRequest(BaseModel):
    raw_job_description: str

