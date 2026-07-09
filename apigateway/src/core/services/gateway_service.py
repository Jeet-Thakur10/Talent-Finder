import logging
import time
from collections.abc import AsyncGenerator

import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Hop-by-hop and connection-specific headers to exclude from forwarding
EXCLUDE_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
    "host",
    "server",
    "date",
    # Exclude upstream CORS headers to prevent duplicates with gateway CORSMiddleware
    "access-control-allow-origin",
    "access-control-allow-credentials",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-expose-headers",
    "access-control-max-age",
}


class GatewayService:
    """Service layer coordinating API request proxying and route mapping."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def forward(self, request: Request) -> Response:
        """Route and forward the incoming HTTP request to the designated upstream."""
        path = request.url.path

        # 1. Match route prefix to upstream base URL (longest match wins)
        target_base_url = None

        sorted_prefixes = sorted(settings.route_map.keys(), key=len, reverse=True)
        for prefix in sorted_prefixes:
            if path.startswith(prefix):
                target_base_url = settings.route_map[prefix]
                break

        if not target_base_url:
            logger.warning(f"No route match found for: {path}")
            return JSONResponse(
                status_code=404,
                content={"detail": f"No gateway route matched for path '{path}'"},
            )

        # Resolve upstream service name for logging and error reporting
        upstream_name = (
            "server"
            if target_base_url == settings.SERVER_BASE_URL
            else "sourcing"
        )

        # 2. Reconstruct target URL
        query = request.url.query
        url = f"{target_base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{query}"

        # 3. Read body and headers
        body = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None)

        # 4. Forward request & track metrics
        start_time = time.perf_counter()
        try:
            req = self.client.build_request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )
            resp = await self.client.send(req, stream=True)
        except httpx.RequestError as exc:
            duration = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"Gateway Error: Connection failed to upstream '{upstream_name}' "
                f"for {request.method} {path} -> {exc} (took {duration:.2f}ms)"
            )
            error_msg = (
                f"Bad Gateway: Upstream service '{upstream_name}' is unreachable."
            )
            return JSONResponse(
                status_code=502,
                content={
                    "detail": error_msg,
                    "upstream": upstream_name,
                    "error": str(exc),
                },
            )

        duration = (time.perf_counter() - start_time) * 1000.0

        # 5. Log proxy transit information
        logger.info(
            f"{request.method} {path} -> {upstream_name} "
            f"({resp.status_code}) in {duration:.2f}ms"
        )

        # 6. Stream response back to client
        async def body_generator() -> AsyncGenerator[bytes, None]:
            try:
                async for chunk in resp.aiter_bytes():
                    yield chunk
            finally:
                await resp.aclose()

        response = StreamingResponse(
            body_generator(),
            status_code=resp.status_code,
        )

        # 7. Append response headers (preserving duplicates like Set-Cookie)
        for name, value in resp.headers.raw:
            header_name = name.decode("latin1").lower()
            if header_name not in EXCLUDE_RESPONSE_HEADERS:
                response.headers.append(name.decode("latin1"), value.decode("latin1"))

        return response
