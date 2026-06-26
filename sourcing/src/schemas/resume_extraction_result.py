from dataclasses import dataclass

from src.schemas.resume_candidate_output import (
    ResumeCandidateOutput,
)


@dataclass(slots=True)
class ResumeExtractionResult:
    success: bool
    provider: str
    payload: ResumeCandidateOutput | None = None
    error: str | None = None