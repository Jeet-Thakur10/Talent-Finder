import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.exceptions.auth_exceptions import (
    InvalidCredentials,
    InvalidPasswordException,
    InvalidToken,
    UserAlreadyExistsException,
)
from src.core.security.JwtProvider import JWTProvider
from src.core.services.notification_service import NotificationService
from src.data.models.postgres.user import User
from src.data.repositories.auth_repository import AuthRepository
from src.schemas.auth_schema import (
    AddUserRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from src.utils.crypt import hash_password, verify_password
from src.utils.email_templates import get_welcome_email_html
from src.utils.validation import validate_password

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.auth_repository = AuthRepository(db)
        self.jwt_provider = JWTProvider()

    async def login(self, data: LoginRequest) -> tuple[str, str, LoginResponse]:

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
            ),
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

    async def get_user_by_id(self, user_id: UUID) -> UserResponse:
        user = await self.auth_repository.get_user_by_id(
            user_id,
        )

        if not user:
            raise InvalidToken(
                details="User not found",
            )

        return UserResponse.model_validate(user)

    async def create_user(
        self,
        data: AddUserRequest,
        notification_service: NotificationService,
    ) -> UserResponse:
        # Check if email is already in use
        existing_user = await self.auth_repository.get_user_by_email(data.email)
        if existing_user:
            raise UserAlreadyExistsException(details="Email is already in use.")

        # Validate password format
        validate_password(data.password)

        # Create user
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            created_at=datetime.now(UTC),
        )

        created_user = await self.auth_repository.create_user(user)

        # Send welcome email using the first ALLOWED_ORIGINS value
        login_url = "http://localhost:5173/login"
        if settings.ALLOWED_ORIGINS:
            login_url = f"{settings.ALLOWED_ORIGINS[0]}/login"

        email_html = get_welcome_email_html(
            name=created_user.name,
            email=created_user.email,
            password=data.password,
            login_url=login_url,
        )

        try:
            await notification_service.send_email(
                recipient_email=created_user.email,
                recipient_name=created_user.name,
                subject="Welcome to Talent Finder",
                html_content=email_html,
            )
        except Exception as e:
            # Gracefully catch email failure and log it
            logger.exception("Failed to send welcome email via Brevo: %s", str(e))

        return UserResponse.model_validate(created_user)
