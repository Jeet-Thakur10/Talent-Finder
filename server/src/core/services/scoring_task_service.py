from __future__ import annotations

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.scoring_task import ScoringTask
from src.data.repositories.scoring_task_repository import ScoringTaskRepository


class ScoringTaskService:
    def __init__(self, db: AsyncSession):
        self.repository = ScoringTaskRepository(db)

    async def create_task(
        self,
        recruiter_id: UUID,
        job_description_id: UUID,
    ) -> ScoringTask:
        return await self.repository.create_task(
            recruiter_id=recruiter_id,
            job_description_id=job_description_id,
        )

    async def get_task_by_id(self, task_id: UUID) -> ScoringTask | None:
        return await self.repository.get_task_by_id(task_id)

    async def update_celery_task_id(self, task_id: UUID, celery_task_id: str) -> None:
        await self.repository.update_celery_task_id(task_id, celery_task_id)

    async def update_task_stage(self, task_id: UUID, stage: str) -> None:
        await self.repository.update_task_stage(task_id, stage)

    async def update_task_started(self, task_id: UUID) -> None:
        await self.repository.update_task_started(task_id)

    async def update_task_success(
        self,
        task_id: UUID,
        payload: dict,
        matched: int,
        eligible: int | None,
        selected: int | None,
    ) -> None:
        await self.repository.update_task_success(
            task_id=task_id,
            payload=payload,
            matched=matched,
            eligible=eligible,
            selected=selected,
        )

    async def update_task_failure(self, task_id: UUID, error_message: str) -> None:
        await self.repository.update_task_failure(task_id, error_message)

    async def get_tasks_by_recruiter(self, recruiter_id: UUID) -> list[ScoringTask]:
        return await self.repository.get_tasks_by_recruiter(recruiter_id)
