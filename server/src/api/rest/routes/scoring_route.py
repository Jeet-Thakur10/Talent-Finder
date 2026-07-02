from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.data.models.postgres.pipeline import HiringManagerDecision

from src.api.rest.dependencies import (
    get_authenticated_user_context,
    get_scoring_service,
    get_scoring_task_service,
)
from src.config.settings import settings
from src.core.services.scoring_service import ScoringService
from src.core.services.scoring_task_service import ScoringTaskService
from src.schemas.auth_schema import AuthenticatedUserContext
from src.schemas.scoring_schema import (
    CandidateDetailsResponse,
    CandidateEvaluationBoardResponse,
    CandidateImportRequest,
    CandidateScoreResponse,
    HiringManagerReviewRequest,
    HiringManagerReviewResponse,
    HMCampaignResponse,
    InterviewScheduleRequest,
    InterviewScheduleResponse,
    ParsedCandidateProfile,
    PipelineCandidateResult,
    PipelineEnqueueResponse,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineNotesUpdateRequest,
    PipelineSnapshotResponse,
    PipelineStageUpdateRequest,
    PipelineTaskStatusResponse,
    SharedCampaignCandidateResponse,
    ShortlistShareRequest,
    ShortlistShareResponse,
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


@router.get(
    "/tasks",
    response_model=list[PipelineTaskStatusResponse],
)
async def list_recruiter_tasks(
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    task_service: ScoringTaskService = Depends(
        get_scoring_task_service,
    ),
) -> list[PipelineTaskStatusResponse]:
    await task_service.recover_stale_tasks(settings.SCORING_TASK_TIMEOUT_MINUTES)
    tasks = await task_service.get_tasks_by_recruiter(current_user.user_id)
    return [
        PipelineTaskStatusResponse(
            id=task.id,
            job_description_id=task.job_description_id,
            status=task.status,
            current_stage=task.current_stage,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            matched_candidate_count=task.matched_candidate_count,
            eligible_candidate_count=task.eligible_candidate_count,
            selected_candidate_count=task.selected_candidate_count,
            job_description_title=(
                task.job_description.title
                if task.job_description
                else "Unknown Position"
            ),
        )
        for task in tasks
    ]


@router.post(
    "/{job_description_id}/pipeline",
    response_model=PipelineEnqueueResponse,
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
    task_service: ScoringTaskService = Depends(
        get_scoring_task_service,
    ),
) -> PipelineEnqueueResponse:
    await task_service.recover_stale_tasks(settings.SCORING_TASK_TIMEOUT_MINUTES)
    # 1. Authorize user has access to job description first
    await service._get_authorized_job_description(
        job_description_id,
        current_user,
    )

    # 2. Persist background task in PostgreSQL with initial QUEUED stage
    task = await task_service.create_task(
        recruiter_id=current_user.user_id,
        job_description_id=job_description_id,
    )

    # 3. Dispatch worker job
    from src.core.tasks import run_scoring_pipeline_task
    celery_res = run_scoring_pipeline_task.delay(
        str(task.id),
        str(current_user.user_id),
        str(job_description_id),
        data.model_dump(),
    )

    # 4. Save Celery execution ID
    await task_service.update_celery_task_id(task.id, celery_res.id)

    return PipelineEnqueueResponse(
        task_id=task.id,
        status="QUEUED",
    )


@router.get(
    "/tasks/{task_id}",
    response_model=PipelineTaskStatusResponse,
)
async def get_task_status(
    task_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
    task_service: ScoringTaskService = Depends(
        get_scoring_task_service,
    ),
) -> PipelineTaskStatusResponse:
    await task_service.recover_stale_tasks(settings.SCORING_TASK_TIMEOUT_MINUTES)
    task = await task_service.get_task_by_id(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")

    # Authorize user access to the job description associated with the task
    await service._get_authorized_job_description(
        task.job_description_id,
        current_user,
    )

    return PipelineTaskStatusResponse(
        id=task.id,
        job_description_id=task.job_description_id,
        status=task.status,
        current_stage=task.current_stage,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        matched_candidate_count=task.matched_candidate_count,
        eligible_candidate_count=task.eligible_candidate_count,
        selected_candidate_count=task.selected_candidate_count,
    )


@router.get(
    "/tasks/{task_id}/result",
    response_model=PipelineExecutionResponse,
)
async def get_task_result(
    task_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
    task_service: ScoringTaskService = Depends(
        get_scoring_task_service,
    ),
) -> PipelineExecutionResponse | JSONResponse:
    await task_service.recover_stale_tasks(settings.SCORING_TASK_TIMEOUT_MINUTES)
    task = await task_service.get_task_by_id(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")

    # Authorize user access
    await service._get_authorized_job_description(
        task.job_description_id,
        current_user,
    )

    if task.status in ("PENDING", "RUNNING"):
        return JSONResponse(
            status_code=202,
            content={"status": task.status, "stage": task.current_stage},
        )

    if task.status == "FAILED":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Task failed: {task.error_message}",
        )

    payload = task.final_response_payload if task.final_response_payload is not None else {}
    return PipelineExecutionResponse.model_validate(payload)


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


@router.post(
    "/recruiter/job-descriptions/{job_description_id}/share",
    response_model=ShortlistShareResponse,
)
async def share_shortlist(
    job_description_id: UUID,
    data: ShortlistShareRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> ShortlistShareResponse:
    count = await service.share_shortlist(
        job_description_id=job_description_id,
        current_user=current_user,
        candidate_ids=data.candidate_ids,
        notes_by_candidate=data.notes_by_candidate,
    )
    return ShortlistShareResponse(
        message="Shortlist shared successfully with hiring manager.",
        shared_candidate_count=count,
    )


@router.get(
    "/hm/campaigns",
    response_model=list[HMCampaignResponse],
)
async def get_hm_shared_campaigns(
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> list[HMCampaignResponse]:
    return await service.get_hm_shared_campaigns(current_user)


@router.get(
    "/hm/campaigns/{job_description_id}/candidates",
    response_model=list[SharedCampaignCandidateResponse],
)
async def get_hm_shared_candidates(
    job_description_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> list[SharedCampaignCandidateResponse]:
    return await service.get_hm_shared_candidates(
        job_description_id,
        current_user,
    )


@router.post(
    "/hm/campaigns/{job_description_id}/candidates/{candidate_id}/review",
    response_model=HiringManagerReviewResponse,
)
async def submit_hm_candidate_review(
    job_description_id: UUID,
    candidate_id: UUID,
    data: HiringManagerReviewRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> HiringManagerReviewResponse:
    pipeline_entry = await service.submit_hm_candidate_review(
        job_description_id=job_description_id,
        candidate_id=candidate_id,
        current_user=current_user,
        decision=data.decision,
        remarks=data.remarks,
    )
    hm_decision = pipeline_entry.hm_decision
    if hm_decision is None:
        hm_decision = data.decision
    return HiringManagerReviewResponse(
        message="Candidate review decision saved successfully.",
        candidate_id=pipeline_entry.candidate_id,
        hm_decision=hm_decision,
        hiring_manager_notes=pipeline_entry.hiring_manager_notes,
    )


@router.get(
    "/hm/campaigns/{job_description_id}/candidates/{candidate_id}/board",
    response_model=CandidateEvaluationBoardResponse,
)
async def get_hm_candidate_evaluation_board(
    job_description_id: UUID,
    candidate_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> CandidateEvaluationBoardResponse:
    return await service.get_hm_candidate_evaluation_board(
        job_description_id=job_description_id,
        candidate_id=candidate_id,
        current_user=current_user,
    )


@router.post(
    "/hm/campaigns/{job_description_id}/candidates/{candidate_id}/schedule-interview",
    response_model=InterviewScheduleResponse,
)
async def schedule_interview(
    job_description_id: UUID,
    candidate_id: UUID,
    data: InterviewScheduleRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: ScoringService = Depends(
        get_scoring_service,
    ),
) -> InterviewScheduleResponse:
    pipeline_entry = await service.schedule_interview(
        job_description_id=job_description_id,
        candidate_id=candidate_id,
        current_user=current_user,
        interview_link=data.interview_link,
        interview_datetime=data.interview_datetime,
        timezone=data.timezone,
        message=data.message,
    )
    hm_decision = pipeline_entry.hm_decision
    if hm_decision is None:
        hm_decision = HiringManagerDecision.INTERVIEW_SENT

    interview_link = pipeline_entry.interview_link
    if interview_link is None:
        interview_link = data.interview_link

    interview_datetime = pipeline_entry.interview_datetime
    if interview_datetime is None:
        interview_datetime = data.interview_datetime

    interview_timezone = pipeline_entry.interview_timezone
    if interview_timezone is None:
        interview_timezone = data.timezone

    return InterviewScheduleResponse(
        message=(
            "Interview scheduled successfully and invitation "
            "email sent to candidate."
        ),
        candidate_id=pipeline_entry.candidate_id,
        hm_decision=hm_decision,
        interview_link=interview_link,
        interview_datetime=interview_datetime,
        interview_timezone=interview_timezone,
        interview_message=pipeline_entry.interview_message,
    )
