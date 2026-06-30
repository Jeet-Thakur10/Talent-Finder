from uuid import UUID
from pydantic import BaseModel, Field


class CandidateSearchRequest(BaseModel):
    title: str

    skills: list[str] = Field(
        default_factory=list,
    )

    min_experience: int = 0

    required_candidates: int = 10

    max_source_resumes: int = 5

    exclude_candidate_ids: list[UUID] = Field(
        default_factory=list,
    )