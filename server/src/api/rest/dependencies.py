from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.exceptions.auth_exceptions import InvalidToken
from src.core.security.JwtProvider import JWTProvider
from src.core.services.auth_service import AuthService
from src.core.services.job_description_service import JobDescriptionService
from src.core.services.notification_service import NotificationService
from src.core.services.otp_service import OTPService
from src.core.services.scoring_service import ScoringService
from src.core.services.scoring_task_service import ScoringTaskService
from src.data.clients.postgres import request_scoped_sessionmaker
from src.schemas.auth_schema import AuthenticatedUserContext

jwt_provider = JWTProvider()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with request_scoped_sessionmaker() as session:
        # this block is a context manager , it automatically closes the session
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:

    return AuthService(db)


async def get_otp_service(db: AsyncSession = Depends(get_db)) -> OTPService:
    return OTPService(db)


async def get_job_description_service(
    db: AsyncSession = Depends(get_db),
) -> JobDescriptionService:
    return JobDescriptionService(db)


async def get_scoring_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ScoringService, None]:
    service = ScoringService(db)
    try:
        yield service
    finally:
        await service.close()


async def get_scoring_task_service(
    db: AsyncSession = Depends(get_db),
) -> ScoringTaskService:
    return ScoringTaskService(db)


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(db)


def _parse_uuid_claim(value: str | None, claim_name: str) -> UUID | None:
    if value is None:
        return None

    try:
        return UUID(value)
    except ValueError as exc:
        raise InvalidToken(
            details=f"Token contains an invalid '{claim_name}' claim"
        ) from exc


async def get_authenticated_user_context(
    access_token: str | None = Cookie(
        default=None, alias=settings.ACCESS_TOKEN_COOKIE_NAME
    ),
) -> AuthenticatedUserContext:

    if not access_token:
        raise InvalidToken(
            details="Access token is missing",
        )

    payload = jwt_provider.decode_token(
        access_token,
    )

    if payload["type"] != "access":
        raise InvalidToken(
            details="Invalid token type",
        )

    return AuthenticatedUserContext(
        user_id=UUID(payload["sub"]),
        role=payload["role"],
    )


async def get_refresh_token_payload(
    refresh_token: str | None = Cookie(
        default=None,
        alias=settings.REFRESH_TOKEN_COOKIE_NAME,
    ),
) -> dict[str, Any]:

    if not refresh_token:
        raise InvalidToken(
            details="Refresh token is missing",
        )

    payload = jwt_provider.decode_token(
        refresh_token,
    )

    if payload["type"] != "refresh":
        raise InvalidToken(
            details="Invalid token type",
        )

    return payload
