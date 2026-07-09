import uvicorn

from src.api.rest.app import app  # noqa: F401
from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )
