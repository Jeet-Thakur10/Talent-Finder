from bs4 import BeautifulSoup

from src.schemas.postjobfree_search_result import (
    PostJobFreeSearchResult,
)


class PostJobFreeSearchParser:

    BASE_URL = "https://www.postjobfree.com"

    def parse(
        self,
        html: str,
    ) -> list[PostJobFreeSearchResult]:

        soup = BeautifulSoup(html, "html.parser")

        results: list[PostJobFreeSearchResult] = []

        cards = soup.select("h3.itemTitle")

        for card in cards:

            link = card.find("a")

            if link is None:
                continue

            href = link.get("href")

            if not href:
                continue

            results.append(
                PostJobFreeSearchResult(
                    title=link.get_text(strip=True),
                    location="",
                    resume_url=f"{self.BASE_URL}{href}",
                )
            )

        return results
