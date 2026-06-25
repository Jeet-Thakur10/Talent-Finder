from pydantic import BaseModel

from src.schemas.compressed_candidate import (
    CompressedCandidate,
)


class CandidateSearchResponse(BaseModel):
    candidates: list[CompressedCandidate]
    requested_candidates: int
    returned_candidates: int

    sourced: bool