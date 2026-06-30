from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate import Candidate
    from src.data.models.postgres.job_description import JobDescription


class CandidateJobScore(Base):
    __tablename__ = "candidate_job_scores"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "job_description_id",
            name="uq_candidate_job_score_candidate_job",
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
    job_description_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_descriptions.id"),
        nullable=False,
    )
    final_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    skills_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    experience_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    recency_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    role_fit_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    education_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    matched_mandatory_skills: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )
    matched_optional_skills: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )
    missing_mandatory_skills: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )
    explanation: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    candidate: Mapped[Candidate] = relationship(
        back_populates="scores",
    )
    job_description: Mapped[JobDescription] = relationship(
        back_populates="candidate_scores",
    )
