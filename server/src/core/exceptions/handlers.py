from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions.auth_exceptions import (
    GeneralException,
    InvalidAuthorizationFormat,
    InvalidPasswordException,
    InvalidToken,
)
from src.core.exceptions.job_description_exception import JobDescriptionBaseException
from src.core.exceptions.scoring_exceptions import ScoringBaseException


async def invalid_token_handler(
        request: Request, exc: InvalidToken,
        ) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "error_code": exc.error_code if hasattr(exc, "error_code") else None,
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )


async def invalid_authorization_format_handler(
        request: Request,
        exc: InvalidAuthorizationFormat,
        ) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )


async def general_exception_handler(
        request: Request, exc: GeneralException,
        ) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )

async def invalid_password_exception_handler(
        request: Request,
        exc: InvalidPasswordException,
        ) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.message,
            **({"info": exc.details} if exc.details else {})
        }
    )


# Job Description Exceptions
async def job_description_exception_handler(
    request: Request,
    exc: JobDescriptionBaseException,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error_code": exc.error_code
            if hasattr(exc, "error_code")
            else None,
            "detail": exc.message,
            **(
                {"info": exc.details}
                if exc.details
                else {}
            ),
        },
    )


async def scoring_exception_handler(
    request: Request,
    exc: ScoringBaseException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.message,
            **(
                {"info": exc.details}
                if exc.details
                else {}
            ),
        },
    )
