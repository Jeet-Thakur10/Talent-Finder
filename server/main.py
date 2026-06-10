from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.user_seeder import UserSeeder
from src.api.middleware.my_auth_middleware import MyAuthMiddleware
from src.api.rest.routes.auth_route import router as auth_router
from src.api.rest.routes.otp_router import router as otp_router

from src.config.settings import settings
from src.core.exceptions.auth_exceptions import (
    GeneralException,
    InvalidAuthorizationFormat,
    InvalidPasswordException,
    InvalidToken,
    InvalidCredentials
)
from src.core.exceptions.handlers import (
    general_exception_handler,
    invalid_authorization_format_handler,
    invalid_password_exception_handler,
    invalid_token_handler,
)
from src.data.clients.postgres import Base, engine, async_session_local


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("tables created")

    async with async_session_local() as db:
        await UserSeeder.seed(db)

    print("seeded users")
    
    yield 
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(InvalidToken, invalid_token_handler)
app.add_exception_handler(InvalidAuthorizationFormat, invalid_authorization_format_handler)
app.add_exception_handler(InvalidPasswordException, invalid_password_exception_handler)
app.add_exception_handler(GeneralException, general_exception_handler)
app.add_exception_handler(InvalidCredentials, general_exception_handler)

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


if __name__ == "__main__": 
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT)
