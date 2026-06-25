from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate import Candidate
    from src.data.models.postgres.job_description import JobDescription


class Pipeline(Base):
    __tablename__ = "pipeline"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "jd_id",
            name="uq_pipeline_candidate_jd",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )
    jd_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_descriptions.id"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="PRE_SCORED",
    )
    recruiter_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    hiring_manager_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    candidate: Mapped[Candidate] = relationship(
        back_populates="pipeline_entries",
    )
    job_description: Mapped[JobDescription] = relationship(
        back_populates="pipeline_entries",
    )
