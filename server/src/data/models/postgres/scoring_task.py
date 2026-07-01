from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.job_description import JobDescription
    from src.data.models.postgres.user import User


class ScoringTask(Base):
    __tablename__ = "scoring_tasks"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    job_description_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_descriptions.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="PENDING",
    )
    current_stage: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="QUEUED",
    )
    schema_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    cancel_requested: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    matched_candidate_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    eligible_candidate_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    selected_candidate_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    final_response_payload: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    recruiter: Mapped[User] = relationship(
        foreign_keys=[recruiter_id],
    )
    job_description: Mapped[JobDescription] = relationship(
        foreign_keys=[job_description_id],
    )
