from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate import Candidate
    from src.data.models.postgres.job_description import JobDescription


class HiringManagerDecision(str, enum.Enum):
    PENDING = "PENDING"
    INTERVIEW_SENT = "INTERVIEW_SENT"
    REJECTED = "REJECTED"


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
    shared_with_hiring_manager: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    shared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    hm_decision: Mapped[HiringManagerDecision | None] = mapped_column(
        SQLEnum(HiringManagerDecision, name="hiring_manager_decision"),
        nullable=True,
        default=HiringManagerDecision.PENDING,
    )
    interview_link: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    interview_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    interview_timezone: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    interview_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    interview_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
