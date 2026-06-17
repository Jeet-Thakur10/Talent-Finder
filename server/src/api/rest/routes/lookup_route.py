from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_job_description_service
from src.core.services.job_description_service import JobDescriptionService
from src.schemas.job_description_schema import (
    EmploymentTypeResponse,
    JobDescriptionStatusResponse,
)

router = APIRouter(
    prefix="/lookups",
    tags=["Lookups"],
)


@router.get(
    "/employment-types",
    response_model=list[EmploymentTypeResponse],
)
async def get_employment_types(
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
):
    return await service.get_employment_types()


@router.get(
    "/job-description-statuses",
    response_model=list[JobDescriptionStatusResponse],
)
async def get_job_description_statuses(
    service: JobDescriptionService = Depends(
        get_job_description_service,
    ),
):
    return await service.get_job_description_statuses()
