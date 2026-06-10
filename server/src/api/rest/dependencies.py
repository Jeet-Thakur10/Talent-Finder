from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Request, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.otp_service import OTPService
from src.schemas.auth_schema import AuthenticatedUserContext
from src.core.exceptions.auth_exceptions import InvalidToken
from src.core.security.JwtProvider import JWTProvider
from src.core.services.auth_service import AuthService
from src.data.clients.postgres import async_session_local
from src.config.settings import settings

jwt_provider = JWTProvider()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_local() as session:
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

def _parse_uuid_claim(value: str | None, claim_name: str) -> UUID | None:
    if value is None:
        return None

    try:
        return UUID(value)
    except ValueError as exc:
        raise InvalidToken(details=f"Token contains an invalid '{claim_name}' claim") from exc

async def get_authenticated_user_context(access_token: str | None = Cookie(mdefault=None, alias=settings.ACCESS_TOKEN_COOKIE_NAME)) -> AuthenticatedUserContext:

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
) -> dict:

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