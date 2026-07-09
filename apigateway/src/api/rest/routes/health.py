from typing import Any

import httpx
from fastapi import APIRouter, Depends

from src.api.rest.dependencies import check_upstream_health, get_gateway_client

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check(
    verify_upstreams: bool = False,
    client: httpx.AsyncClient = Depends(get_gateway_client),
) -> dict[str, Any]:
    """Lightweight endpoint to confirm the gateway is alive.

    If verify_upstreams=true is passed, it queries the backend upstreams.
    """
    response: dict[str, Any] = {
        "status": "ok",
        "service": "apigateway",
    }

    if verify_upstreams:
        response["upstreams"] = await check_upstream_health(client)

    return response
