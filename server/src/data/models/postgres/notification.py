from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.postgres import Base

if TYPE_CHECKING:
    from src.data.models.postgres.user import User


class NotificationType(str, enum.Enum):
    SCORING_COMPLETED = "SCORING_COMPLETED"
    SHORTLIST_SHARED = "SHORTLIST_SHARED"
    CANDIDATE_ACCEPTED = "CANDIDATE_ACCEPTED"
    INTERVIEW_INVITATION = "INTERVIEW_INVITATION"
    JD_CLOSED = "JD_CLOSED"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, name="notification_types"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    target_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        name="metadata",
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    user: Mapped[User] = relationship(
        foreign_keys=[user_id],
    )
