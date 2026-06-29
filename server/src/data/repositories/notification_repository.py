from uuid import UUID
from typing import Any
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.models.postgres.notification import Notification, NotificationType


class NotificationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        target_url: str | None = None,
        metadata_: dict[str, Any] | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            target_url=target_url,
            metadata_=metadata_,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def list_notifications(
        self,
        user_id: UUID,
    ) -> list[Notification]:
        stmt = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await self.db.commit()
            await self.db.refresh(notification)
        return notification

    async def mark_all_as_read(
        self,
        user_id: UUID,
    ) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def unread_count(
        self,
        user_id: UUID,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
