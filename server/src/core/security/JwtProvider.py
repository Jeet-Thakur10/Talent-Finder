from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import ExpiredSignatureError, JWTError, jwt

from src.config.settings import settings
from src.core.exceptions.auth_exceptions import InvalidToken


class JWTProvider:

    def create_access_token(self, user_id: UUID, role: str) -> str:

        payload = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            ),
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def create_refresh_token(self, user_id: UUID) -> str:

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
            ),
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def decode_token(self, token: str) -> dict:

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )

        except ExpiredSignatureError:
            raise InvalidToken(details="Token has expired", error_code="TOKEN_EXPIRED")

        except JWTError:
            raise InvalidToken(details="Token is malformed or invalid")

        return payload
    
    def create_password_reset_token(self, user_id: UUID) -> str:

        payload = {
            "sub": str(user_id),
            "type": "password_reset",
            "exp": datetime.now(UTC)
            + timedelta(minutes=10),
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )