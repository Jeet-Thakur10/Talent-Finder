import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute path to sourcing/.env relative to this file
current_dir = Path(__file__).resolve().parent
sourcing_dir = current_dir.parent.parent
env_file_path = sourcing_dir / ".env"

if not env_file_path.exists():
    raise RuntimeError(

            "Critical Configuration Error: Sourcing environment file '.env' "
            f"was not found at expected path: {env_file_path.as_posix()}. "
            "Please check your deployment and working directory structure."

    )

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_SECOND_API_KEY: str = ""
    GROQ_API_KEYS: str = ""
    DATABASE_URL: str = ""
    PORT: int = 8001
    HOST: str = "127.0.0.1"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    SERVER_URL: str = "http://127.0.0.1:8000"
    RECRUITER_EMAIL: str = "11a08cnn@gmail.com"
    RECRUITER_PASSWORD: str = "Temppass@123"

    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    MAX_SOURCING_ATTEMPTS: int = 4
    MAX_CONSECUTIVE_NO_IMPROVEMENT: int = 2
    SOURCING_LOOP_TIMEOUT_SECONDS: float = 260.0

    @property
    def groq_keys(self) -> list[str]:
        if self.GROQ_API_KEYS:
            return [k.strip() for k in self.GROQ_API_KEYS.split(",") if k.strip()]
        keys = []
        if self.GROQ_API_KEY:
            keys.append(self.GROQ_API_KEY)
        if self.GROQ_SECOND_API_KEY:
            keys.append(self.GROQ_SECOND_API_KEY)
        return keys

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()

# Log configuration status at startup
logger = logging.getLogger(__name__)
try:
    from urllib.parse import urlparse
    url = urlparse(settings.DATABASE_URL)
    masked_db_url = f"{url.scheme}://{url.username}:****@{url.hostname}:{url.port}{url.path}"
    db_name = url.path.lstrip('/')
except Exception:
    masked_db_url = "Invalid URL structure"
    db_name = "Unknown"

print(f"[CONFIG SOURCING] Loaded .env from: {env_file_path.as_posix()}")
print(f"[CONFIG SOURCING] DATABASE_URL: {masked_db_url}")
print(f"[CONFIG SOURCING] Database Name: {db_name}")
logger.info(f"Loaded .env from: {env_file_path.as_posix()}")
logger.info(f"DATABASE_URL: {masked_db_url}")
logger.info(f"Database Name: {db_name}")

