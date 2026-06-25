from pydantic import BaseModel, Field


class CandidateSearchRequest(BaseModel):
    title: str

    skills: list[str] = Field(
        default_factory=list,
    )

    min_experience: int = 0

    min_candidates: int = 10

    max_source_resumes: int = 5