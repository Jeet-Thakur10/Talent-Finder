from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate_experience import CandidateExperience


class CandidateExperienceSkill(Base):
    __tablename__ = "candidate_experience_skills"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    experience_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidate_experiences.id"),
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    experience: Mapped[CandidateExperience] = relationship(
        back_populates="skills",
    )
