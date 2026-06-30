from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate import Candidate
    from src.data.models.postgres.candidate_experience_skill import (
        CandidateExperienceSkill,
    )


class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )
    company_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    candidate: Mapped[Candidate] = relationship(
        back_populates="experiences",
    )
    skills: Mapped[list[CandidateExperienceSkill]] = relationship(
        back_populates="experience",
        cascade="all, delete-orphan",
    )
