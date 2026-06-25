from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.rest.routes.health import router as health_router
from src.api.rest.routes.sourcing_route import router as sourcing_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Sourcing Service",
        description="FastAPI service for scraping and importing candidate profiles",
        version="0.1.0",
    )


    app.include_router(health_router)
    app.include_router(sourcing_router)

    return app
