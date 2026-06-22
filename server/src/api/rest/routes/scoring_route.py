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
    CandidateEvaluationBoardResponse,
    CandidateDetailsResponse,
    CandidateImportRequest,
    CandidatePrescoreBatchOutput,
    ParsedCandidateProfile,
    PipelineCandidateResult,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineNotesUpdateRequest,
    PipelineSnapshotResponse,
    PipelineStageUpdateRequest,
    CandidateScoreResponse,
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


@router.post(
    "/{job_description_id}/pipeline",
    response_model=PipelineExecutionResponse,
)
async def pipeline_prescore_and_score(
    job_description_id: UUID,
    data: PipelineExecutionRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> PipelineExecutionResponse:
    return await service.pipeline_prescore_and_score(
        job_description_id,
        current_user,
        data,
    )


@router.get(
    "/jobs/{job_description_id}/candidates",
    response_model=list[PipelineCandidateResult],
)
async def list_ranked_candidates_for_job_description(
    job_description_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> list[PipelineCandidateResult]:
    return await service.list_ranked_candidates_for_job_description(
        job_description_id,
        current_user,
    )


@router.get(
    "/jobs/{job_description_id}/candidates/{candidate_id}",
    response_model=CandidateDetailsResponse,
)
async def get_candidate_details(
    job_description_id: UUID,
    candidate_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidateDetailsResponse:
    return await service.get_candidate_details(
        job_description_id,
        candidate_id,
        current_user,
    )


@router.get(
    "/jobs/{job_description_id}/candidates/{candidate_id}/board",
    response_model=CandidateEvaluationBoardResponse,
)
async def get_candidate_evaluation_board(
    job_description_id: UUID,
    candidate_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidateEvaluationBoardResponse:
    return await service.get_candidate_evaluation_board(
        job_description_id,
        candidate_id,
        current_user,
    )


@router.get(
    "/jobs/{job_description_id}/candidates/{candidate_id}/score",
    response_model=CandidateScoreResponse,
)
async def get_candidate_score(
    job_description_id: UUID,
    candidate_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidateScoreResponse:
    return await service.get_candidate_score(
        job_description_id,
        candidate_id,
        current_user,
    )


@router.post(
    "/jobs/{job_description_id}/candidates/{candidate_id}/rescore",
    response_model=CandidateScoreResponse,
)
async def rescore_candidate(
    job_description_id: UUID,
    candidate_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidateScoreResponse:
    return await service.rescore_candidate(
        job_description_id,
        candidate_id,
        current_user,
    )


@router.patch(
    "/jobs/{job_description_id}/candidates/{candidate_id}/pipeline-notes",
    response_model=PipelineSnapshotResponse,
)
async def update_pipeline_notes(
    job_description_id: UUID,
    candidate_id: UUID,
    data: PipelineNotesUpdateRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> PipelineSnapshotResponse:
    return await service.update_pipeline_notes(
        job_description_id,
        candidate_id,
        data,
        current_user,
    )


@router.patch(
    "/jobs/{job_description_id}/pipeline-stage",
    response_model=list[PipelineSnapshotResponse],
)
async def bulk_update_pipeline_stage(
    job_description_id: UUID,
    data: PipelineStageUpdateRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> list[PipelineSnapshotResponse]:
    return await service.bulk_update_pipeline_stage(
        job_description_id,
        data,
        current_user,
    )
