"""SQLAlchemy Job Description model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base
from src.data.models.postgres.employment_type import EmploymentType
from src.data.models.postgres.job_description_status import (
    JobDescriptionStatus,
)

if TYPE_CHECKING:
    from src.data.models.postgres.candidate_job_score import CandidateJobScore
    from src.data.models.postgres.jd_skill import JDSkill
    from src.data.models.postgres.pipeline import Pipeline
    from src.data.models.postgres.user import User

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,  
    )

    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    department: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    job_purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    responsibilities: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    min_experience: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    max_experience: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    employment_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("employment_types.id"),
        nullable=False,
    )

    education_requirement: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    preferred_qualifications: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_description_statuses.id"),
        nullable=False,
    )

    hiring_manager_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    raw_job_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    recruiter: Mapped[User] = relationship(
        back_populates="job_descriptions",
        foreign_keys=[recruiter_id],
    )

    hiring_manager: Mapped[User | None] = relationship(
        foreign_keys=[hiring_manager_id],
    )

    skills: Mapped[list[JDSkill]] = relationship(
        back_populates="job_description",
        cascade="all, delete-orphan",
    )

    employment_type: Mapped[EmploymentType] = relationship(
        back_populates="job_descriptions",
    )

    status: Mapped[JobDescriptionStatus] = relationship(
        back_populates="job_descriptions",
    )
    candidate_scores: Mapped[list[CandidateJobScore]] = relationship(
        back_populates="job_description",
        cascade="all, delete-orphan",
    )
    pipeline_entries: Mapped[list[Pipeline]] = relationship(
        back_populates="job_description",
        cascade="all, delete-orphan",
    )
