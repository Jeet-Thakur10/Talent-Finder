from contextlib import asynccontextmanager
from typing import Any, cast

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from src.api.rest.routes.auth_route import router as auth_router
from src.api.rest.routes.job_description_route import router as job_description_router
from src.api.rest.routes.lookup_route import router as lookup_router
from src.api.rest.routes.otp_router import router as otp_router
from src.api.rest.routes.scoring_route import router as scoring_router
from src.config.settings import settings
from src.core.exceptions.auth_exceptions import (
    GeneralException,
    InvalidAuthorizationFormat,
    InvalidCredentials,
    InvalidPasswordException,
    InvalidToken,
)
from src.core.exceptions.handlers import (
    general_exception_handler,
    invalid_authorization_format_handler,
    invalid_password_exception_handler,
    invalid_token_handler,
    job_description_exception_handler,
    scoring_exception_handler,
)
from src.core.exceptions.job_description_exception import JobDescriptionBaseException
from src.core.exceptions.scoring_exceptions import ScoringBaseException
from src.data.clients.postgres import Base, async_session_local, engine
from src.utils.master_data_seeder import seed_master_data
from src.utils.user_seeder import UserSeeder


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_local() as db:
        await seed_master_data(db)
        await UserSeeder.seed(db)

    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(
    InvalidToken,
    cast(Any, invalid_token_handler),
)
app.add_exception_handler(
    InvalidAuthorizationFormat,
    cast(Any, invalid_authorization_format_handler),
    )
app.add_exception_handler(
    InvalidPasswordException,
    cast(Any, invalid_password_exception_handler),
)
app.add_exception_handler(
    GeneralException,
    cast(Any, general_exception_handler),
)
app.add_exception_handler(
    InvalidCredentials,
    cast(Any, general_exception_handler),
)
app.add_exception_handler(
    JobDescriptionBaseException,
    cast(Any, job_description_exception_handler),
)
app.add_exception_handler(
    ScoringBaseException,
    cast(Any, scoring_exception_handler),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["*"],
)

# app.add_middleware(MyAuthMiddleware)

app.include_router(auth_router)
app.include_router(otp_router)
app.include_router(job_description_router)
app.include_router(lookup_router)
app.include_router(scoring_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT)
