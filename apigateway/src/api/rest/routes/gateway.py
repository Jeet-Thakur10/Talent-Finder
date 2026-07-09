import httpx
from fastapi import APIRouter, Depends, Request, Response

from src.api.rest.dependencies import get_gateway_client
from src.core.services.gateway_service import GatewayService

router = APIRouter()


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def catch_all_gateway(
    request: Request,
    client: httpx.AsyncClient = Depends(get_gateway_client),
) -> Response:
    """Generic proxy router.

    Delegates all request routing and forward proxying to GatewayService.
    """
    service = GatewayService(client)
    return await service.forward(request)
