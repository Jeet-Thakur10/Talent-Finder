from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import (
    get_authenticated_user_context,
    get_scoring_service,
)
from src.core.services.scoring_service import ScoringService
from src.schemas.auth_schema import AuthenticatedUserContext
from src.schemas.scoring_schema import (
    CandidateBatchScoreOutput,
    CandidateImportRequest,
    ParsedCandidateProfile,
    CandidatePrescoreBatchOutput,
)

router = APIRouter(prefix="/scoring", tags=["Scoring"])


@router.post("/candidates/import", response_model=ParsedCandidateProfile)
async def import_candidate_resume(
    data: CandidateImportRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> ParsedCandidateProfile:
    return await service.import_candidate_resume(
        data,
        current_user,
    )

@router.post(
    "/{job_description_id}/score",
    response_model=CandidateBatchScoreOutput,
)
async def score_candidates_for_job_description(
    job_description_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidateBatchScoreOutput:
    return await service.score_candidates_for_job_description(
        job_description_id,
        current_user,
    )

@router.post(
    "/{job_description_id}/prescore",
    response_model=CandidatePrescoreBatchOutput,
)
async def prescore_candidates_for_job_description(
    job_description_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidatePrescoreBatchOutput:
    return await service.prescore_candidates_for_job_description(
        job_description_id,
    )

