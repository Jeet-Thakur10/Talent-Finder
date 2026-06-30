from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.auth_exceptions import (
    InvalidCredentials,
    InvalidPasswordException,
    InvalidToken,
)
from src.core.security.JwtProvider import JWTProvider
from src.data.repositories.auth_repository import AuthRepository
from src.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from src.utils.crypt import hash_password, verify_password


class AuthService:

    def __init__(self, db: AsyncSession):
        self.auth_repository = AuthRepository(db)
        self.jwt_provider = JWTProvider()

    async def login(self, data: LoginRequest ) -> tuple[str, str, LoginResponse]:

        user = await self.auth_repository.get_user_by_email(
            data.email,
        )

        if not user:
            raise InvalidCredentials()

        if not verify_password(data.password, user.password_hash):
            raise InvalidPasswordException

        access_token = self.jwt_provider.create_access_token(
            user_id=user.id,
            role=user.role,
        )

        refresh_token = self.jwt_provider.create_refresh_token(
            user_id=user.id,
        )

        return (
            access_token,
            refresh_token,
            LoginResponse(
                user=UserResponse.model_validate(user),
            )
        )

    async def refresh(self, user_id: UUID) -> str:

        user = await self.auth_repository.get_user_by_id(
            user_id,
        )

        if not user:
            raise InvalidToken(
                details="User not found",
            )

        return self.jwt_provider.create_access_token(
            user_id=user.id,
            role=user.role,
        )

    async def reset_password(
        self,
        reset_token: str,
        new_password: str,
    ) -> None:

        payload = self.jwt_provider.decode_token(
            reset_token,
        )

        if payload.get("type") != "password_reset":
            raise InvalidToken(
                details="Invalid reset token",
            )

        user = await self.auth_repository.get_user_by_id(
            UUID(payload["sub"]),
        )

        if not user:
            raise InvalidToken(
                details="User not found",
            )

        user.password_hash = hash_password(
            new_password,
        )

        await self.auth_repository.save(
            user,
        )
