"""SQLAlchemy Job Description model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base


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

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    min_experience: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    education_requirement: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    recruiter: Mapped["User"] = relationship(
        back_populates="job_descriptions",
    )

    skills: Mapped[list["JDSkill"]] = relationship(
        back_populates="job_description",
    )