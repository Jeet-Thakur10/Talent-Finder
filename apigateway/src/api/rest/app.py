from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.rest.dependencies import lifespan
from src.api.rest.routes.gateway import router as gateway_router
from src.api.rest.routes.health import router as health_router
from src.config.settings import settings

app = FastAPI(
    title="Talent Finder API Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend connection compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
# Catch-all gateway router must be included last so it doesn't mask specific paths
app.include_router(gateway_router)
