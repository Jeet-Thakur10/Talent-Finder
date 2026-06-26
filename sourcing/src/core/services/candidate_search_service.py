from src.core.services.candidate_service import (
    CandidateService,
)
from src.core.services.postjobfree_sourcing_service import (
    PostJobFreeSourcingService,
)
from src.schemas.candidate_search_request import (
    CandidateSearchRequest,
)
from src.schemas.candidate_search_response import (
    CandidateSearchResponse,
)


class CandidateSearchService:
    def __init__(
        self,
        candidate_service: CandidateService,
        sourcing_service: PostJobFreeSourcingService,
    ) -> None:
        self._candidate_service = candidate_service
        self._sourcing_service = sourcing_service

    async def search_or_source_candidates(
        self,
        request: CandidateSearchRequest,
    ) -> CandidateSearchResponse:

        candidates = (
            await self._candidate_service.search_candidates(
                request,
            )
        )

        if len(candidates) >= request.required_candidates:
            selected_candidates = candidates[:request.required_candidates]
            return CandidateSearchResponse(
                candidates=selected_candidates,
                requested_candidates=request.required_candidates,
                returned_candidates=len(
                    selected_candidates,
                ),
                sourced=False,
            )

        #
        # fallback sourcing
        #

        await self._sourcing_service.source_candidates(
            request,
        )

        candidates = (
            await self._candidate_service.search_candidates(
                request,
            )
        )

        selected_candidates = candidates[:request.required_candidates]
        return CandidateSearchResponse(
            candidates=selected_candidates,
            requested_candidates=request.required_candidates,
            returned_candidates=len(
                selected_candidates,
            ),
            sourced=True,
        )