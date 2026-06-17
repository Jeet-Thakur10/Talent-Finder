from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate_education import CandidateEducation
    from src.data.models.postgres.candidate_experience import CandidateExperience
    from src.data.models.postgres.candidate_job_score import CandidateJobScore
    from src.data.models.postgres.candidate_skill import CandidateSkill


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    full_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    current_title: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    resume_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    resume_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="resume_import",
    )
    total_experience_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    skills: Mapped[list[CandidateSkill]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    experiences: Mapped[list[CandidateExperience]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="CandidateExperience.start_date.desc()",
    )
    educations: Mapped[list[CandidateEducation]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    scores: Mapped[list[CandidateJobScore]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
