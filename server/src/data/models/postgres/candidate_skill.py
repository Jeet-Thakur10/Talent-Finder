from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate import Candidate


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    candidate: Mapped[Candidate] = relationship(
        back_populates="skills",
    )
