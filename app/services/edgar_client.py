import asyncio
from typing import Optional
import httpx
from app.config import settings


class EdgarClient:
    def __init__(self):
        self._semaphore = asyncio.Semaphore(settings.rate_limit_per_second)
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self):
        self._client = httpx.AsyncClient(
            headers={"User-Agent": settings.sec_user_agent},
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def stop(self):
        if self._client:
            await self._client.aclose()

    async def get(self, url: str, **kwargs) -> httpx.Response:
        async with self._semaphore:
            response = await self._client.get(url, **kwargs)
            response.raise_for_status()
            return response


# Global singleton used by default
edgar_client = EdgarClient()


def get_edgar_client() -> EdgarClient:
    return edgar_client
