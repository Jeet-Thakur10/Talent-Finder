from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel
from src.data.models.postgres.notification import NotificationType


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    target_url: str | None = None
    is_read: bool
    metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class UnreadCountResponse(BaseModel):
    unread_count: int


class MessageResponse(BaseModel):
    message: str
