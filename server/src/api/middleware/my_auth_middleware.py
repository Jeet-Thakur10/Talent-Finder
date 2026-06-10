"""Custom authentication middleware.

Validates the `Authorization` header for protected endpoints and decodes
JWTs using the configured `JWTProvider`. Excluded paths and OPTIONS are
skipped to allow docs and public auth endpoints.
"""


from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions.auth_exceptions import (
    GeneralException,
    InvalidAuthorizationFormat,
    InvalidToken,
)
from src.core.security.JwtProvider import JWTProvider


class MyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        
        excluded_paths = [
            "/docs",
            "/openapi.json",
            "/ws",
            "/auth/login",
            "/auth/signup"
        ]

        if request.url.path in excluded_paths:
            return await call_next(request)
        
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"message": "Authorization header missing"}
            )
        
        try:
            parts = auth_header.split()
            if len(parts) != 2:
                raise InvalidAuthorizationFormat()

            scheme, token = parts

            if scheme.lower() != "bearer":
                raise InvalidAuthorizationFormat()

            provider = JWTProvider()
            provider.decode_token(token)

        except (InvalidAuthorizationFormat, InvalidToken):
            raise  

        except Exception as e:
            raise GeneralException(details=str(e))

        return await call_next(request)
