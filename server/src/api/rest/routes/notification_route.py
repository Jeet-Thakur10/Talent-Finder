from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from src.api.rest.dependencies import (
    get_authenticated_user_context,
    get_notification_service,
)
from src.core.services.notification_service import NotificationService
from src.schemas.auth_schema import AuthenticatedUserContext
from src.schemas.notification_schema import (
    NotificationResponse,
    UnreadCountResponse,
    MessageResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> list[NotificationResponse]:
    return await service.list_notifications(current_user.user_id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> NotificationResponse:
    result = await service.mark_as_read(notification_id, current_user.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result


@router.patch("/read-all", response_model=MessageResponse)
async def mark_all_as_read(
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> MessageResponse:
    await service.mark_all_as_read(current_user.user_id)
    return MessageResponse(message="All notifications marked as read")


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> UnreadCountResponse:
    count = await service.get_unread_count(current_user.user_id)
    return UnreadCountResponse(unread_count=count)
