from typing import Literal

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
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    SMTP_EMAIL: str = "11a08cnn@gmail.com"
    SMTP_APP_PASSWORD: str = "hqtugeunpycqqwyz"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile" # llama3-70b-8192 llama-3.3-70b-versatile

    SCORING_LLM_PROVIDER: str = "groq"

    HF_TOKEN: str = ""
    HF_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    HF_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    SCORING_EMBEDDING_PROVIDER: str = "huggingface"
    SCORING_EMBEDDING_TIMEOUT: int = 30

    SOURCING_SERVICE_BASE_URL: str = "http://localhost:8001"
    SOURCING_CLIENT_TIMEOUT_SECONDS: float = 300.0

    DEFAULT_MAX_SOURCE_RESUMES: int = 20
    CANDIDATE_REFRESH_AFTER_DAYS: int = 30

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
    )

settings = Settings()
