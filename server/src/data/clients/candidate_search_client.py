from __future__ import annotations

from uuid import UUID

import httpx

from src.config.settings import settings
from src.core.exceptions.scoring_exceptions import SourcingServiceClientError
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse,
    CandidateSearchRequest,
    CandidateSearchResponse,
)


class CandidateSearchClient:
    """HTTP Client for communicating with the Sourcing Service."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.SOURCING_SERVICE_BASE_URL
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=settings.SOURCING_CLIENT_TIMEOUT_SECONDS,
        )

    async def search_candidates(
        self,
        request: CandidateSearchRequest,
    ) -> CandidateSearchResponse:
        """Send a candidate search request to the Sourcing Service.

        Args:
            request: The CandidateSearchRequest schema containing search criteria.

        Returns:
            CandidateSearchResponse containing the list of matching CandidateSummary
            items.

        Raises:
            SourcingServiceClientError on any HTTP or connection failures.
        """
        try:
            # Sourcing service search endpoint: POST /candidates/search
            payload = request.model_dump(mode="json")

            response = await self._client.post(
                "/candidates/search",
                json=payload,
            )

            if response.is_error:
                raise SourcingServiceClientError(
                    details=(
                        f"Sourcing service returned status code "
                        f"{response.status_code}: {response.text}"
                    ),
                    status_code=response.status_code,
                )

            response_json = response.json()
            return CandidateSearchResponse.model_validate(response_json)

        except httpx.HTTPError as e:
            raise SourcingServiceClientError(
                details=(
                    f"HTTP network error while communicating with Sourcing Service: {e}"
                ),
                status_code=500,
            ) from e
        except Exception as e:
            if isinstance(e, SourcingServiceClientError):
                raise e
            raise SourcingServiceClientError(
                details=f"Unexpected error in sourcing client: {str(e)}",
                status_code=500,
            ) from e

    async def get_candidate_details(
        self,
        candidate_ids: list[UUID],
    ) -> list[CandidateDetailsResponse]:
        """Fetch full candidate details for a list of candidate IDs.

        Args:
            candidate_ids: A list of candidate UUIDs.

        Returns:
            A list of CandidateDetailsResponse containing full details of the
            candidates.

        Raises:
            SourcingServiceClientError on any HTTP or connection failures.
        """
        try:
            payload = {"candidate_ids": [str(cid) for cid in candidate_ids]}

            response = await self._client.post(
                "/candidates/by-ids",
                json=payload,
            )

            if response.is_error:
                raise SourcingServiceClientError(
                    details=(
                        f"Sourcing service returned status code "
                        f"{response.status_code}: {response.text}"
                    ),
                    status_code=response.status_code,
                )

            response_json = response.json()
            return [
                CandidateDetailsResponse.model_validate(item) for item in response_json
            ]

        except httpx.HTTPError as e:
            raise SourcingServiceClientError(
                details=(
                    f"HTTP network error while communicating with Sourcing Service: {e}"
                ),
                status_code=500,
            ) from e
        except Exception as e:
            if isinstance(e, SourcingServiceClientError):
                raise e
            raise SourcingServiceClientError(
                details=f"Unexpected error in sourcing client: {str(e)}",
                status_code=500,
            ) from e

    async def close(self) -> None:
        """Close the underlying HTTP client transport."""
        await self._client.aclose()

    async def __aenter__(self) -> CandidateSearchClient:
        return self

    async def __aexit__(  # type: ignore[no-untyped-def]
        self, exc_type, exc_val, exc_tb
    ) -> None:
        await self.close()
