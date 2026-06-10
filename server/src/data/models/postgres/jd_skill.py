"""SQLAlchemy JD Skill model."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base


class JDSkill(Base):
    __tablename__ = "jd_skills"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    jd_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_descriptions.id"),
        nullable=False,
    )

    skill_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    job_description: Mapped["JobDescription"] = relationship(
        back_populates="skills",
    )