from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    PORT: int = 8001
    HOST: str = "127.0.0.1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SERVER_URL: str = "http://127.0.0.1:8000"
    RECRUITER_EMAIL: str = "11a08cnn@gmail.com"
    RECRUITER_PASSWORD: str = "Temppass@123"

    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
