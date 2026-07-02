from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.rest.routes.candidate_route import (
    router as candidate_router,
)
from src.api.rest.routes.health import (
    router as health_router,
)
from src.config.settings import settings
from src.data.clients.init_db import (
    init_db,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    await init_db()

    print(
        "Database initialized successfully",
    )

    yield


app = FastAPI(
    title="Sourcing Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
)

app.include_router(
    candidate_router,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
