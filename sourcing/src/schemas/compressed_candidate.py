from uuid import UUID

from pydantic import BaseModel


class CompressedCandidate(BaseModel):
    candidate_id: UUID
    profile_text: str

class CompressedCandidateRequest(BaseModel):
    limit: int | None = None

class CandidateIdsRequest(BaseModel):
    candidate_ids: list[UUID]
