
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.job_description import JobDescription


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    name: Mapped[str] = mapped_column(String, nullable=False)

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    job_descriptions: Mapped[list[JobDescription]] = relationship(
        back_populates="recruiter",
    )
