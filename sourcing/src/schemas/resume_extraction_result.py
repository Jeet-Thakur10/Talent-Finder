from dataclasses import dataclass

from src.schemas.resume_candidate_output import (
    ResumeCandidateOutput,
)


@dataclass(slots=True)
class ResumeExtractionResult:
    payload: ResumeCandidateOutput
    provider: str