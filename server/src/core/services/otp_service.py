import json
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from random import randint

import aiosmtplib
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.exceptions.auth_exceptions import InvalidToken
from src.core.security.JwtProvider import JWTProvider
from src.core.security.otp_store import OTPRecord, redis_client
from src.data.repositories.auth_repository import AuthRepository


class OTPService:
    def __init__(self, db: AsyncSession) -> None:
        self.auth_repository = AuthRepository(db)
        self.jwt_provider = JWTProvider()

    async def forgot_password(self, email: str) -> None:

        user = await self.auth_repository.get_user_by_email(
            email,
        )

        if not user:
            return

        otp = await self.generate_otp(
            email,
        )

        await self.send_otp(
            email=email,
            otp=otp,
        )

    async def generate_otp(self, email: str) -> str:

        otp = str(randint(100000, 999999))

        record: OTPRecord = {
            "otp": otp,
            "expires_at": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
        }
        await redis_client.set(f"otp:{email}", json.dumps(record), ex=600)

        return otp

    async def verify_otp_code(self, email: str, otp: str) -> bool:

        key = f"otp:{email}"
        record_str = await redis_client.get(key)

        if not record_str:
            return False

        try:
            record = json.loads(record_str)
            expires_at = datetime.fromisoformat(record["expires_at"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

        if datetime.now(UTC) > expires_at:
            await redis_client.delete(key)
            return False

        if record["otp"] != otp:
            return False

        await redis_client.delete(key)

        return True

    async def verify_otp(self, email: str, otp: str) -> str:

        is_valid = await self.verify_otp_code(
            email=email,
            otp=otp,
        )

        if not is_valid:
            raise InvalidToken(
                details="Invalid OTP",
            )

        user = await self.auth_repository.get_user_by_email(
            email,
        )

        if not user:
            raise InvalidToken(
                details="User not found",
            )

        return self.jwt_provider.create_password_reset_token(
            user.id,
        )

    async def send_otp(self, email: str, otp: str) -> None:

        message = MIMEText(f"Your password reset OTP is: {otp}")

        message["Subject"] = "Password Reset OTP"
        message["From"] = settings.SMTP_EMAIL
        message["To"] = email

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_APP_PASSWORD,
            use_tls=False,
            start_tls=True,
        )
