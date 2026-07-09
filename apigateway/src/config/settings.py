import logging
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure default logging style on package import
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

# Resolve absolute path to apigateway/.env relative to this file
current_dir = Path(__file__).resolve().parent
gateway_dir = current_dir.parent.parent
env_file_path = gateway_dir / ".env"

class Settings(BaseSettings):
    SERVER_BASE_URL: str = "http://localhost:8000"
    SOURCING_BASE_URL: str = "http://localhost:8001"
    PORT: int = 8080
    HOST: str = "127.0.0.1"
    ALLOWED_ORIGINS: str | list[str] = ["http://localhost:5173"]
    UPSTREAM_TIMEOUT_SECONDS: float = 300.0

    @property
    def route_map(self) -> dict[str, str]:
        """Mapping of path prefixes to their respective upstream services."""
        return {
            "/auth": self.SERVER_BASE_URL,
            "/otp": self.SERVER_BASE_URL,
            "/job-descriptions": self.SERVER_BASE_URL,
            "/lookups": self.SERVER_BASE_URL,
            "/scoring": self.SERVER_BASE_URL,
            "/notifications": self.SERVER_BASE_URL,
            "/candidates": self.SOURCING_BASE_URL,
            "/sourcing": self.SOURCING_BASE_URL,
        }

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=str(env_file_path) if env_file_path.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()

logger = logging.getLogger(__name__)

if env_file_path.exists():
    print(f"[CONFIG GATEWAY] Loaded .env from: {env_file_path.as_posix()}")
    logger.info(f"Loaded .env from: {env_file_path.as_posix()}")
else:
    print("[CONFIG GATEWAY] Loaded settings from environment variables")
    logger.info("Loaded settings from environment variables")

print(f"[CONFIG GATEWAY] SERVER_BASE_URL: {settings.SERVER_BASE_URL}")
print(f"[CONFIG GATEWAY] SOURCING_BASE_URL: {settings.SOURCING_BASE_URL}")
logger.info(f"SERVER_BASE_URL: {settings.SERVER_BASE_URL}")
logger.info(f"SOURCING_BASE_URL: {settings.SOURCING_BASE_URL}")
