# Log configuration status at startup
import logging
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute path to server/.env relative to this file
current_dir = Path(__file__).resolve().parent
server_dir = current_dir.parent.parent
env_file_path = server_dir / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = "" # Required field - removing fallback value to prevent
                           # silent failure
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

    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "11a08cnn@gmail.com"
    BREVO_SENDER_NAME: str = "Talent Finder"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    SCORING_LLM_PROVIDER: str = "groq"

    HF_TOKEN: str = ""
    HF_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    HF_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    SCORING_EMBEDDING_PROVIDER: str = "huggingface"
    SCORING_EMBEDDING_TIMEOUT: int = 30

    SOURCING_SERVICE_BASE_URL: str = "http://localhost:8001"
    SOURCING_CLIENT_TIMEOUT_SECONDS: float = 300.0
    SCORING_TASK_TIMEOUT_MINUTES: int = 15

    DEFAULT_MAX_SOURCE_RESUMES: int = 20
    CANDIDATE_REFRESH_AFTER_DAYS: int = 30

    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(
        cls, v : str | list[str]
        ) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=str(env_file_path) if env_file_path.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()

logger = logging.getLogger(__name__)
# Mask database URL password for security
try:
    from urllib.parse import urlparse
    url = urlparse(settings.DATABASE_URL)
    masked_db_url = f"{url.scheme}://{url.username}:****@{url.hostname}:{url.port}{url.path}"
    db_name = url.path.lstrip('/')
except Exception:
    masked_db_url = "Invalid URL structure"
    db_name = "Unknown"

if env_file_path.exists():
    print(f"[CONFIG] Loaded .env from: {env_file_path.as_posix()}")
    logger.info(f"Loaded .env from: {env_file_path.as_posix()}")
else:
    print("[CONFIG] Loaded settings from environment variables")
    logger.info("Loaded settings from environment variables")
print(f"[CONFIG] DATABASE_URL: {masked_db_url}")
print(f"[CONFIG] Database Name: {db_name}")
logger.info(f"DATABASE_URL: {masked_db_url}")
logger.info(f"Database Name: {db_name}")

