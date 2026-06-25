from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.candidate import Candidate


class CandidateEducation(Base):
    __tablename__ = "candidate_educations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
    )
    institution_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    degree: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    field_of_study: Mapped[str | None] = mapped_column(
        String,
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

    candidate: Mapped[Candidate] = relationship(
        back_populates="educations",
    )
