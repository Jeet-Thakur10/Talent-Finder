from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.scoring_task import ScoringTask


class ScoringTaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        recruiter_id: UUID,
        job_description_id: UUID,
    ) -> ScoringTask:
        task = ScoringTask(
            id=uuid4(),
            recruiter_id=recruiter_id,
            job_description_id=job_description_id,
            status="PENDING",
            current_stage="QUEUED",
            created_at=datetime.now(UTC),
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_by_id(self, task_id: UUID) -> ScoringTask | None:
        result = await self.db.execute(
            select(ScoringTask).where(ScoringTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def update_celery_task_id(self, task_id: UUID, celery_task_id: str) -> None:
        await self.db.execute(
            update(ScoringTask)
            .where(ScoringTask.id == task_id)
            .values(celery_task_id=celery_task_id)
        )
        await self.db.flush()

    async def update_task_stage(self, task_id: UUID, stage: str) -> None:
        await self.db.execute(
            update(ScoringTask)
            .where(ScoringTask.id == task_id)
            .values(current_stage=stage)
        )
        await self.db.flush()

    async def update_task_started(self, task_id: UUID) -> None:
        await self.db.execute(
            update(ScoringTask)
            .where(ScoringTask.id == task_id)
            .values(
                status="RUNNING",
                started_at=datetime.now(UTC),
            )
        )
        await self.db.flush()

    async def update_task_success(
        self,
        task_id: UUID,
        payload: dict[str, Any],
        matched: int,
        eligible: int | None,
        selected: int | None,
    ) -> None:
        await self.db.execute(
            update(ScoringTask)
            .where(ScoringTask.id == task_id)
            .values(
                status="SUCCESS",
                current_stage="COMPLETED",
                completed_at=datetime.now(UTC),
                final_response_payload=payload,
                matched_candidate_count=matched,
                eligible_candidate_count=eligible,
                selected_candidate_count=selected,
            )
        )
        await self.db.flush()

    async def update_task_failure(self, task_id: UUID, error_message: str) -> None:
        await self.db.execute(
            update(ScoringTask)
            .where(ScoringTask.id == task_id)
            .values(
                status="FAILED",
                current_stage="FAILED",
                completed_at=datetime.now(UTC),
                error_message=error_message,
            )
        )
        await self.db.flush()

    async def get_tasks_by_recruiter(self, recruiter_id: UUID) -> list[ScoringTask]:
        from sqlalchemy.orm import joinedload

        result = await self.db.execute(
            select(ScoringTask)
            .options(joinedload(ScoringTask.job_description))
            .where(ScoringTask.recruiter_id == recruiter_id)
            .order_by(ScoringTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_stale_tasks(self, cutoff_time: datetime) -> list[ScoringTask]:
        from sqlalchemy import and_, or_

        query = select(ScoringTask).where(
            or_(
                and_(
                    ScoringTask.status == "PENDING",
                    ScoringTask.created_at < cutoff_time,
                ),
                and_(
                    ScoringTask.status == "RUNNING",
                    or_(
                        ScoringTask.started_at < cutoff_time,
                        and_(
                            ScoringTask.started_at.is_(None),
                            ScoringTask.created_at < cutoff_time,
                        ),
                    ),
                ),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
