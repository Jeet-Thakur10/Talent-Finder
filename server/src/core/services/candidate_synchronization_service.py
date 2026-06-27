from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from src.config.settings import settings
from src.data.clients.candidate_search_client import CandidateSearchClient

if TYPE_CHECKING:
    from src.core.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


class CandidateSynchronizationService:
    """Service responsible for ensuring candidate details profiles are synchronized locally.

    It coordinates checking candidate presence, querying external sourced details,
    and persisting them idempotently inside transaction scopes.
    """

    def __init__(
        self,
        scoring_service: ScoringService,
        search_client: CandidateSearchClient,
    ) -> None:
        self.scoring_service = scoring_service
        self.search_client = search_client

    async def synchronize_candidates(
        self,
        selected_candidate_ids: list[UUID],
    ) -> None:
        """Verify which candidates exist locally, check freshness, and synchronize stale/missing ones.

        Args:
            selected_candidate_ids: A list of candidate UUIDs selected for deep scoring.
        """
        if not selected_candidate_ids:
            return

        # 1. Fetch candidates that already exist in the local database
        existing_candidates = await self.scoring_service.repository.get_candidates_by_ids(
            selected_candidate_ids
        )
        local_lookup = {c.id: c for c in existing_candidates}

        # 2. Partition candidate IDs into three groups: missing, stale, fresh
        missing_ids: list[UUID] = []
        stale_ids: list[UUID] = []
        fresh_ids: list[UUID] = []

        now = datetime.now(timezone.utc)
        threshold = timedelta(days=settings.CANDIDATE_REFRESH_AFTER_DAYS)

        for cid in selected_candidate_ids:
            candidate = local_lookup.get(cid)
            if candidate is None:
                missing_ids.append(cid)
                logger.info(
                    "Synchronization Decision: candidate_id=%s, local_existence=False, local_updated_at=None, "
                    "freshness_decision=missing, status=synchronized, reason_for_synchronization=missing",
                    cid,
                )
            else:
                updated_at = candidate.updated_at
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)

                time_diff = now - updated_at
                if time_diff > threshold:
                    stale_ids.append(cid)
                    logger.info(
                        "Synchronization Decision: candidate_id=%s, local_existence=True, local_updated_at=%s, "
                        "freshness_decision=stale, status=synchronized, reason_for_synchronization=stale",
                        cid,
                        candidate.updated_at,
                    )
                else:
                    fresh_ids.append(cid)
                    logger.info(
                        "Synchronization Decision: candidate_id=%s, local_existence=True, local_updated_at=%s, "
                        "freshness_decision=fresh, status=skipped, reason_for_synchronization=skipped",
                        cid,
                        candidate.updated_at,
                    )

        # 3. Combine Missing and Stale candidate IDs
        union_ids = missing_ids + stale_ids

        # 4. If no candidates to synchronize, return immediately
        if not union_ids:
            return

        # 5. Fetch updated/latest profiles from the Sourcing Service in a single request
        try:
            updated_details = await self.search_client.get_candidate_details(union_ids)
        except Exception as e:
            logger.exception("Failed to fetch candidate details for synchronization: %s", e)
            return

        # 6. Persist each fetched profile sequentially to ensure transaction safety
        for details in updated_details:
            try:
                await self.scoring_service.upsert_candidate_profile(details)
            except Exception as e:
                logger.exception("Failed to synchronize candidate profile for ID %s: %s", details.id, e)
