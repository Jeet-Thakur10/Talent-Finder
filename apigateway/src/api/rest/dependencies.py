import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.config.settings import settings

logger = logging.getLogger(__name__)

class GatewayState:
    http_client: httpx.AsyncClient

state = GatewayState()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize the global shared httpx AsyncClient
    # Configure pool limits and timeouts to avoid infinite waits or resource leaks
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    state.http_client = httpx.AsyncClient(
        timeout=settings.UPSTREAM_TIMEOUT_SECONDS,
        limits=limits,
    )
    logger.info("Gateway shared HTTPX client initialized.")
    yield
    # Cleanup on shutdown
    await state.http_client.aclose()
    logger.info("Gateway shared HTTPX client closed.")

def get_gateway_client() -> httpx.AsyncClient:
    """Dependency injection provider for the shared HTTPX client."""
    return state.http_client

async def check_upstream_health(client: httpx.AsyncClient) -> dict[str, str]:
    """Helper to check connectivity to upstream services."""
    results = {}

    # Check Server
    server_health_url = f"{settings.SERVER_BASE_URL.rstrip('/')}/docs"
    try:
        # Use short timeout specifically for health check to avoid blocking
        response = await client.get(server_health_url, timeout=5.0)
        if response.status_code == 200:
            results["server"] = "healthy"
        else:
            results["server"] = f"unhealthy (status {response.status_code})"
    except Exception as e:
        logger.warning(f"Health check failed for Server upstream: {e}")
        results["server"] = f"unreachable ({type(e).__name__})"

    # Check Sourcing
    sourcing_health_url = f"{settings.SOURCING_BASE_URL.rstrip('/')}/health"
    try:
        response = await client.get(sourcing_health_url, timeout=5.0)
        if response.status_code == 200:
            results["sourcing"] = "healthy"
        else:
            results["sourcing"] = f"unhealthy (status {response.status_code})"
    except Exception as e:
        logger.warning(f"Health check failed for Sourcing upstream: {e}")
        results["sourcing"] = f"unreachable ({type(e).__name__})"

    return results
