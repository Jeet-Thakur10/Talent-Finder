from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from src.config.settings import settings
from src.core.celery_app import celery_app
from src.core.services.notification_service import NotificationService
from src.core.services.progress_reporter import DatabaseProgressReporter
from src.core.services.scoring_service import ScoringService
from src.core.services.scoring_task_service import ScoringTaskService
from src.data.clients.postgres import get_background_scoped_db_context
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.notification import NotificationType
from src.data.models.postgres.user import User
from src.schemas.auth_schema import AuthenticatedUserContext
from src.schemas.scoring_schema import PipelineExecutionRequest
from src.utils.email_templates import get_generic_email_html

logger = logging.getLogger(__name__)


async def async_run_scoring_pipeline(
    task_id: UUID,
    recruiter_id: UUID,
    job_description_id: UUID,
    request_data: dict,
) -> None:
    scoring_service = None
    pipeline_failed = False
    error_message = ""

    async with get_background_scoped_db_context() as session_factory:
        try:
            async with session_factory() as db:
                task_service = ScoringTaskService(db)
                # 1. Update task started state (RUNNING status)
                await task_service.update_task_started(task_id)
                await db.commit()

                # Initialize pipeline dependencies inside this async block
                scoring_service = ScoringService(db)
                progress_reporter = DatabaseProgressReporter(task_service, task_id)

                current_user = AuthenticatedUserContext(
                    user_id=recruiter_id,
                    role="recruiter",
                )
                exec_req = PipelineExecutionRequest(**request_data)

                # 2. Execute pipeline
                response = await scoring_service.pipeline_prescore_and_score(
                    job_description_id=job_description_id,
                    current_user=current_user,
                    data=exec_req,
                    progress_reporter=progress_reporter,
                )

                # 3. Update task success state
                payload = response.model_dump(mode="json")
                await task_service.update_task_success(
                    task_id=task_id,
                    payload=payload,
                    matched=response.matched_candidate_count,
                    eligible=response.eligible_candidate_count,
                    selected=response.selected_candidate_count,
                )
                await db.commit()

                # 4. Best-effort success notification
                try:
                    user_res = await db.execute(
                        select(User).where(User.id == recruiter_id)
                    )
                    user = user_res.scalar_one_or_none()

                    jd_res = await db.execute(
                        select(JobDescription).where(
                            JobDescription.id == job_description_id
                        )
                    )
                    jd = jd_res.scalar_one_or_none()

                    if user and jd:
                        notification_service = NotificationService(db)
                        frontend_base = (
                            settings.ALLOWED_ORIGINS[0]
                            if settings.ALLOWED_ORIGINS
                            else "http://localhost:5173"
                        )
                        absolute_target_url = f"{frontend_base}/recruiter/job-descriptions/{job_description_id}/candidates"

                        email_body = (
                            f"Hello {user.name},\n\n"
                            f"Great news! The candidate evaluation pipeline for your job description "
                            f'"{jd.title}" has completed successfully.\n\n'
                            f"You can now review the candidate scores and shortlist recommendations "
                            f"on the recruiter candidate board."
                        )

                        email_html = get_generic_email_html(
                            title="Scoring Completed",
                            body=email_body,
                            action_text="View Candidate Board",
                            action_url=absolute_target_url,
                        )

                        await notification_service.notify(
                            user=user,
                            notification_type=NotificationType.SCORING_COMPLETED,
                            title="Scoring Completed",
                            message=f'Candidate evaluation has completed for "{jd.title}". Your shortlisted candidates are now available for review.',
                            target_url=f"/recruiter/job-descriptions/{job_description_id}/candidates",
                            metadata={
                                "job_description_id": str(job_description_id),
                                "task_id": str(task_id),
                            },
                            send_in_app=True,
                            send_email=True,
                            email_subject=f"Scoring completed for {jd.title}",
                            email_html=email_html,
                        )
                        logger.info(
                            "Pipeline completed notification sent successfully for task %s",
                            task_id,
                        )
                    else:
                        logger.warning(
                            "Could not send pipeline success notification: User or JobDescription not found."
                        )
                except Exception as ne:
                    logger.warning(
                        "Failed to send success notification for task %s: %s",
                        task_id,
                        str(ne),
                        exc_info=True,
                    )

        except Exception as e:
            pipeline_failed = True
            logger.exception(
                "Error executing background scoring task %s: %s", task_id, str(e)
            )
            import traceback

            error_message = "".join(
                traceback.format_exception(type(e), e, e.__traceback__)
            )
        finally:
            if scoring_service:
                try:
                    await scoring_service.close()
                except Exception as ce:
                    logger.error(
                        "Error closing scoring service clients for task %s: %s",
                        task_id,
                        str(ce),
                        exc_info=True,
                    )

        if pipeline_failed:
            # We log the failure in a fresh transaction block using a brand new session
            try:
                async with session_factory() as logging_db:
                    logging_task_service = ScoringTaskService(logging_db)
                    await logging_task_service.update_task_failure(
                        task_id, error_message
                    )
                    await logging_db.commit()
                    logger.info(
                        "Successfully persisted task failure state to DB for task %s",
                        task_id,
                    )

                    # 4. Best-effort failure notification using a fresh DB session
                    try:
                        user_res = await logging_db.execute(
                            select(User).where(User.id == recruiter_id)
                        )
                        user = user_res.scalar_one_or_none()

                        jd_res = await logging_db.execute(
                            select(JobDescription).where(
                                JobDescription.id == job_description_id
                            )
                        )
                        jd = jd_res.scalar_one_or_none()

                        if user and jd:
                            notification_service = NotificationService(logging_db)
                            frontend_base = (
                                settings.ALLOWED_ORIGINS[0]
                                if settings.ALLOWED_ORIGINS
                                else "http://localhost:5173"
                            )
                            absolute_tasks_url = f"{frontend_base}/recruiter/tasks"

                            email_body = (
                                f"Hello {user.name},\n\n"
                                f"We are writing to inform you that the candidate evaluation pipeline for your job description "
                                f'"{jd.title}" has failed and could not be completed.\n\n'
                                f"Please visit the Tasks center to review the status of your tasks."
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
                                message=f'Candidate evaluation for "{jd.title}" could not be completed.',
                                target_url="/recruiter/tasks",
                                metadata={
                                    "job_description_id": str(job_description_id),
                                    "task_id": str(task_id),
                                },
                                send_in_app=True,
                                send_email=True,
                                email_subject=f"Scoring failed for {jd.title}",
                                email_html=email_html,
                            )
                            logger.info(
                                "Pipeline failure notification sent successfully for task %s",
                                task_id,
                            )
                        else:
                            logger.warning(
                                "Could not send pipeline failure notification: User or JobDescription not found."
                            )
                    except Exception as ne:
                        logger.warning(
                            "Failed to send failure notification for task %s: %s",
                            task_id,
                            str(ne),
                            exc_info=True,
                        )

            except Exception as fe:
                logger.error(
                    "Critical: Failed to persist task failure state to DB for task %s. Error: %s",
                    task_id,
                    str(fe),
                    exc_info=True,
                )


@celery_app.task(bind=True)
def run_scoring_pipeline_task(
    self,
    task_id_str: str,
    recruiter_id_str: str,
    job_description_id_str: str,
    request_data: dict,
) -> None:
    """Celery background task execution wrapper."""
    task_id = UUID(task_id_str)
    recruiter_id = UUID(recruiter_id_str)
    job_description_id = UUID(job_description_id_str)

    # Run the async execution logic inside the celery sync thread loop
    asyncio.run(
        async_run_scoring_pipeline(
            task_id=task_id,
            recruiter_id=recruiter_id,
            job_description_id=job_description_id,
            request_data=request_data,
        )
    )
