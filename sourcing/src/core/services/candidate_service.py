import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.candidate import Candidate
from src.data.repositories.candidate_repository import (
    CandidateRepository,
)
from src.schemas.resume_candidate_output import (
    ResumeCandidateOutput,
)
from src.schemas.candidate_details_response import (
    CandidateDetailsResponse,
)
from src.schemas.compressed_candidate import CompressedCandidate
from src.schemas.candidate_search_request import (
    CandidateSearchRequest,
)

class CandidateService:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self._db = db

        self._repository = CandidateRepository(
            db,
        )

    async def create_candidate(
        self,
        candidate: ResumeCandidateOutput,
        resume_text: str,
        source_type: str,
    ) -> Candidate:

        resume_hash = hashlib.sha256(
            resume_text.encode(
                "utf-8",
            ),
        ).hexdigest()

        existing_candidate = (
            await self._repository.get_candidate_by_resume_hash(
                resume_hash,
            )
        )

        if existing_candidate:
            return existing_candidate

        return await self._repository.store_candidate(
            candidate=candidate,
            resume_text=resume_text,
            resume_hash=resume_hash,
            source_type=source_type,
        )

    async def commit(self) -> None:
        await self._db.commit()
    
    async def get_compressed_candidates(
        self,
    ) -> list[CompressedCandidate]:
        return await self._repository.get_compressed_candidates()
    
    async def get_candidates_by_ids(
        self,
        candidate_ids: list,
    ) -> list[CandidateDetailsResponse]:
        return await self._repository.get_candidates_by_ids(
            candidate_ids,
        )
    
    async def search_candidates(
        self,
        request: CandidateSearchRequest,
    ) -> list[CompressedCandidate]:
        return await self._repository.search_candidates_by_skills(
            request,
        )