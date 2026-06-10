from datetime import UTC, datetime, timedelta
from random import randint
import smtplib

from email.mime.text import MIMEText
from src.core.security.JwtProvider import JWTProvider
from src.core.exceptions.auth_exceptions import InvalidToken
from src.data.repositories.auth_repository import AuthRepository
from src.core.security.otp_store import otp_store

from src.config.settings import settings


class OTPService:

    def __init__(self, db):
        self.auth_repository = AuthRepository(db)
        self.jwt_provider = JWTProvider()

    async def forgot_password(self, email: str) -> None:

        user = await self.auth_repository.get_user_by_email(
            email,
        )

        if not user:
            return

        otp = self.generate_otp(
            email,
        )

        self.send_otp(
            email=email,
            otp=otp,
        )

        print(
            f"OTP for {email}: {otp}",
        )

    def generate_otp(self, email: str) -> str:

        otp = str(randint(100000, 999999))

        otp_store[email] = {
            "otp": otp,
            "expires_at": datetime.now(UTC)
            + timedelta(minutes=10),
        }

        return otp
    
    def verify_otp_code(self, email: str, otp: str) -> bool:

        record = otp_store.get(email)

        if not record:
            return False

        if datetime.now(UTC) > record["expires_at"]:
            del otp_store[email]
            return False

        if record["otp"] != otp:
            return False

        del otp_store[email]

        return True
    
    async def verify_otp(
        self,
        email: str,
        otp: str,
    ) -> str:

        is_valid = self.verify_otp_code(
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
    
    
    def send_otp(
        self,
        email: str,
        otp: str,
    ) -> None:

        message = MIMEText(
            f"Your password reset OTP is: {otp}"
        )

        message["Subject"] = "Password Reset OTP"
        message["From"] = settings.SMTP_EMAIL
        message["To"] = email

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
        ) as server:

            server.starttls()

            server.login(
                settings.SMTP_EMAIL,
                settings.SMTP_APP_PASSWORD,
            )

            server.send_message(message)