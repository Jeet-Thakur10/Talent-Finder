from httpx import AsyncClient

from src.schemas.postjobfree_search_request import (
    PostJobFreeSearchRequest,
)


class PostJobFreeClient:
    def __init__(self) -> None:
        self._client = AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/137.0.0.0 "
                    "Safari/537.36"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "image/avif,"
                    "image/webp,"
                    "*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            },
        )

    async def get_resume_page(
        self,
        url: str,
    ) -> str:
        response = await self._client.get(
            url,
        )

        response.raise_for_status()

        return response.text

    async def search_resumes(
        self,
        request: PostJobFreeSearchRequest,
    ) -> str:
        response = await self._client.get(
            "https://www.postjobfree.com/resumes",
            params={
                "q": request.required_words,
                "n": request.excluded_words,
                "t": request.title_words,
                "d": request.resume_text_words,
                "r": 10,
            },
        )

        response.raise_for_status()

        return response.text

    async def close(self) -> None:
        await self._client.aclose()