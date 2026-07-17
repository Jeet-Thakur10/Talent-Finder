from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.notification import Notification, NotificationType
from src.data.repositories.notification_repository import NotificationRepository
from src.handlers.http_clients.brevo_client import BrevoClient
from src.utils.email_templates import get_generic_email_html


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_repository = NotificationRepository(db)
        self.brevo_client = BrevoClient()

    async def create_in_app_notification(
        self,
        user_id: Any,
        notification_type: NotificationType,
        title: str,
        message: str,
        target_url: str | None = None,
        metadata_: dict[str, Any] | None = None,
    ) -> Notification:
        return await self.notification_repository.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            target_url=target_url,
            metadata_=metadata_,
        )

    async def send_email(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_content: str,
    ) -> None:
        await self.brevo_client.send_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            html_content=html_content,
        )

    async def notify(
        self,
        *,
        user: Any,  # Expected to have fields: id, email, name
        notification_type: NotificationType,
        title: str,
        message: str,
        target_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        send_in_app: bool = True,
        send_email: bool = False,
        email_subject: str | None = None,
        email_html: str | None = None,
    ) -> None:
        """Sends a notification to the user in-app and/or via email."""

        # 1. In-App Notification
        if send_in_app:
            await self.create_in_app_notification(
                user_id=user.id,
                notification_type=notification_type,
                title=title,
                message=message,
                target_url=target_url,
                metadata_=metadata,
            )

        # 2. Email Notification via Brevo
        if send_email:
            subject = email_subject or title
            html_content = email_html

            if not html_content:
                action_text = "View Details"
                action_url = target_url

                html_content = get_generic_email_html(
                    title=title,
                    body=message,
                    action_text=action_text if action_url else None,
                    action_url=action_url,
                )

            await self.send_email(
                recipient_email=user.email,
                recipient_name=user.name,
                subject=subject,
                html_content=html_content,
            )

    async def list_notifications(self, user_id: Any) -> list[Notification]:
        return await self.notification_repository.list_notifications(user_id)

    async def mark_as_read(
        self,
        notification_id: Any,
        user_id: Any,
    ) -> Notification | None:
        return await self.notification_repository.mark_as_read(
            notification_id,
            user_id,
        )

    async def mark_all_as_read(self, user_id: Any) -> None:
        await self.notification_repository.mark_all_as_read(user_id)

    async def get_unread_count(self, user_id: Any) -> int:
        return await self.notification_repository.unread_count(user_id)
