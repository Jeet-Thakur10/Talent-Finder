from fastapi import APIRouter, Depends

from src.api.rest.dependencies import (
    get_candidate_search_service,
    get_candidate_service,
)
from src.core.services.candidate_search_service import (
    CandidateSearchService,
)
from src.core.services.candidate_service import (
    CandidateService,
)
from src.schemas.candidate_details_response import (
    CandidateDetailsResponse,
)
from src.schemas.candidate_search_request import (
    CandidateSearchRequest,
)
from src.schemas.candidate_search_response import (
    CandidateSearchResponse,
)
from src.schemas.compressed_candidate import (
    CandidateIdsRequest,
    CompressedCandidate,
)

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


@router.get(
    "/compressed",
    response_model=list[CompressedCandidate],
)
async def get_compressed_candidates(
    service: CandidateService = Depends(
        get_candidate_service,
    ),
) -> list[CompressedCandidate]:
    return await service.get_compressed_candidates()


@router.post(
    "/by-ids",
    response_model=list[CandidateDetailsResponse],
)
async def get_candidates_by_ids(
    request: CandidateIdsRequest,
    service: CandidateService = Depends(
        get_candidate_service,
    ),
) -> list[CandidateDetailsResponse]:
    return await service.get_candidates_by_ids(
        request.candidate_ids,
    )

@router.post(
    "/search",
    response_model=CandidateSearchResponse,
)
async def search_candidates(
    request: CandidateSearchRequest,
    service: CandidateSearchService = Depends(
        get_candidate_search_service,
    ),
) -> CandidateSearchResponse:

    return await service.search_or_source_candidates(
        request,
    )
