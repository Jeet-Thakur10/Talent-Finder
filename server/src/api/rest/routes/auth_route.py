from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from src.api.rest.dependencies import (
    get_auth_service,
    get_authenticated_user_context,
    get_notification_service,
    get_refresh_token_payload,
)
from src.config.settings import settings
from src.core.exceptions.job_description_exception import RecruiterAccessRequired
from src.core.services.auth_service import AuthService
from src.core.services.notification_service import NotificationService
from src.schemas.auth_schema import (
    AddUserRequest,
    AuthenticatedUserContext,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    UserResponse,
    UserRole,
)
from src.schemas.otp_schema import ResetPasswordRequest, ResetPasswordResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
    ) -> LoginResponse:

    access_token, refresh_token, result = (await auth_service.login(data))

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60*2,
    )

    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return result

@router.get("/me", response_model=UserResponse)
async def me(
    user_context: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return await auth_service.get_user_by_id(user_context.user_id)

@router.post(
    "/refresh",
    response_model=RefreshResponse,
)
async def refresh(
    response: Response,
    payload: dict[str, Any] = Depends(
        get_refresh_token_payload,
    ),
    auth_service: AuthService = Depends(
        get_auth_service,
    ),
) -> RefreshResponse:

    access_token = await auth_service.refresh(
        UUID(payload["sub"]),
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return RefreshResponse(
        message="Access token refreshed successfully",
    )

@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:

    response.delete_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    return LogoutResponse(
        message="Logged out successfully",
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    data: ResetPasswordRequest,
    auth_service: AuthService = Depends(
        get_auth_service,
    ),
) -> ResetPasswordResponse:

    await auth_service.reset_password(
        reset_token=data.reset_token,
        new_password=data.new_password,
    )

    return ResetPasswordResponse(
        message="Password reset successfully",
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    data: AddUserRequest,
    current_user: AuthenticatedUserContext = Depends(
        get_authenticated_user_context,
    ),
    auth_service: AuthService = Depends(get_auth_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UserResponse:

    if current_user.role != UserRole.recruiter:
        raise RecruiterAccessRequired(
            details="Only recruiters can create user accounts.",
            error_code="RECRUITER_ACCESS_REQUIRED",
        )

    return await auth_service.create_user(data, notification_service)

