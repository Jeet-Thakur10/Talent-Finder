from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:jeetu@localhost:5432/delete"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    SECRET_KEY: str = "jeetsecret"
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_COOKIE_NAME : str = "access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"

    COOKIE_HTTP_ONLY : bool = True
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    SMTP_EMAIL: str = ""
    SMTP_APP_PASSWORD: str = ""

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
    )

settings = Settings()