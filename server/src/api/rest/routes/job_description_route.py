from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import (
    get_authenticated_user_context,
    get_job_description_service,
)
from src.core.services.job_description_service import (
    JobDescriptionService,
)
from src.schemas.auth_schema import AuthenticatedUserContext
from src.schemas.job_description_schema import (
    JobDescriptionCreateRequest,
    JobDescriptionExtractRequest,
    JobDescriptionResponse,
    JobDescriptionUpdateRequest,
)

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


@router.post("/extract", response_model=JobDescriptionResponse)
async def extract_job_description(
    data: JobDescriptionExtractRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
) -> JobDescriptionResponse:
    return await service.extract_job_description(
        data,
        current_user,
    )


@router.post("", response_model=JobDescriptionResponse)
async def create_job_description(
    data: JobDescriptionCreateRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
) -> JobDescriptionResponse:
    return await service.create_job_description(
        data,
        current_user,
    )

@router.get("", response_model=list[JobDescriptionResponse])
async def get_job_descriptions(
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
) -> list[JobDescriptionResponse]:
    return await service.get_job_descriptions(
        current_user,
    )

@router.get(
    "/{job_description_id}",
    response_model=JobDescriptionResponse,
)
async def get_job_description(
    job_description_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
) -> JobDescriptionResponse:
    return await service.get_job_description(
        job_description_id,
        current_user,
    )


@router.put(
    "/{job_description_id}",
    response_model=JobDescriptionResponse,
)
async def update_job_description(
    job_description_id: UUID,
    data: JobDescriptionUpdateRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
) -> JobDescriptionResponse:
    return await service.update_job_description(
        job_description_id,
        data,
        current_user,
    )
