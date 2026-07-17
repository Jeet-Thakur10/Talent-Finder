from typing import TypedDict

import redis.asyncio as aioredis

from src.config.settings import settings


class OTPRecord(TypedDict):
    otp: str
    expires_at: str


redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)
