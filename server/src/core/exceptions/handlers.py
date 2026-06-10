from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions.auth_exceptions import (
    GeneralException,
    InvalidAuthorizationFormat,
    InvalidPasswordException,
    InvalidToken,
)


async def invalid_token_handler(request: Request, exc: InvalidToken):
    return JSONResponse(
        status_code=401,
        content={
            "error_code": exc.error_code if hasattr(exc, "error_code") else None,
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )


async def invalid_authorization_format_handler(request: Request, exc: InvalidAuthorizationFormat):
    return JSONResponse(
        status_code=401,
        content={
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )


async def general_exception_handler(request: Request, exc: GeneralException):
    return JSONResponse(
        status_code=500,
        content={
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )

async def invalid_password_exception_handler(request: Request, exc: InvalidPasswordException):
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )