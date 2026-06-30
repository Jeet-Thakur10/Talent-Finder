from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.job_description import JobDescription


class JobDescriptionStatus(Base):
    __tablename__ = "job_description_statuses"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    code: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    job_descriptions: Mapped[list[JobDescription]] = relationship(
        back_populates="status",
    )
