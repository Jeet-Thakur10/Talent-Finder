from __future__ import annotations

from typing import Any
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
        payload: dict[str, Any],
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

    async def recover_stale_tasks(self, timeout_minutes: int) -> None:
        import logging
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import select

        from src.config.settings import settings
        from src.core.services.notification_service import NotificationService
        from src.data.models.postgres.job_description import JobDescription
        from src.data.models.postgres.notification import NotificationType
        from src.data.models.postgres.user import User
        from src.utils.email_templates import get_generic_email_html

        logger = logging.getLogger(__name__)

        cutoff_time = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
        stale_tasks = await self.repository.find_stale_tasks(cutoff_time)

        if not stale_tasks:
            return

        logger.info("Found %d stale scoring tasks to recover.", len(stale_tasks))

        notification_service = NotificationService(self.repository.db)

        for task in stale_tasks:
            logger.info(
                "Recovering stale task %s (status: %s, job_description_id: %s)",
                task.id,
                task.status,
                task.job_description_id,
            )

            task.status = "FAILED"
            task.current_stage = "FAILED"
            task.completed_at = datetime.now(UTC)
            task.error_message = (
                "Background worker became unavailable while processing this task. "
                "The task was automatically marked as failed."
            )
            task.error_code = "WORKER_UNAVAILABLE"

            await self.repository.db.flush()

            try:
                user_res = await self.repository.db.execute(
                    select(User).where(User.id == task.recruiter_id)
                )
                user = user_res.scalar_one_or_none()

                jd_res = await self.repository.db.execute(
                    select(JobDescription).where(
                        JobDescription.id == task.job_description_id
                    )
                )
                jd = jd_res.scalar_one_or_none()

                if user and jd:
                    frontend_base = (
                        settings.ALLOWED_ORIGINS[0]
                        if settings.ALLOWED_ORIGINS
                        else "http://localhost:5173"
                    )
                    absolute_tasks_url = f"{frontend_base}/recruiter/tasks"

                    email_body = (
                        f"Hello {user.name},\n\n"
                        f"We are writing to inform you that the candidate "
                        "evaluation pipeline for your job description "
                        f'"{jd.title}" has failed and could not be completed.\n\n'
                        f"Please visit the Tasks center to review the "
                        "status of your tasks."
                    )

                    email_html = get_generic_email_html(
                        title="Scoring Failed",
                        body=email_body,
                        action_text="Go to Task Center",
                        action_url=absolute_tasks_url,
                    )

                    await notification_service.notify(
                        user=user,
                        notification_type=NotificationType.SYSTEM,
                        title="Scoring Failed",
                        message=(
                            f'Candidate evaluation for "{jd.title}" '
                            'could not be completed.'
                        ),
                        target_url="/recruiter/tasks",
                        metadata={
                            "job_description_id": str(task.job_description_id),
                            "task_id": str(task.id),
                        },
                        send_in_app=True,
                        send_email=True,
                        email_subject=f"Scoring failed for {jd.title}",
                        email_html=email_html,
                    )
                    logger.info(
                        (
                            "Pipeline failure notification sent successfully "
                            "for recovered stale task %s",
                        ),
                        task.id,
                    )
                else:
                    logger.warning(
                        (
                            "Could not send failure notification for "
                            "recovered task %s: "
                            "User or JobDescription not found."
                        ),
                        task.id,
                    )
            except Exception as ne:
                logger.warning(
                    "Failed to send failure notification for recovered task %s: %s",
                    task.id,
                    str(ne),
                    exc_info=True,
                )

        await self.repository.db.commit()
