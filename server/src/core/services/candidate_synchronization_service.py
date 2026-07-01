from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from src.config.settings import settings
from src.data.clients.candidate_search_client import CandidateSearchClient
from src.schemas.sync_result import CandidateSyncResultItem, SyncBatchResult

if TYPE_CHECKING:
    from src.core.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


class CandidateSynchronizationService:
    """Service responsible for ensuring candidate details profiles
    are synchronized locally.

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
    ) -> SyncBatchResult:
        """Verify which candidates exist locally, check freshness,
        and synchronize stale/missing ones.

        Args:
            selected_candidate_ids: A list of candidate UUIDs
            selected for deep scoring.
        """

        batch_result = SyncBatchResult()

        if not selected_candidate_ids:
            return batch_result

        # 1. Fetch candidates that already exist in the local database
        existing_candidates = (
            await self.scoring_service.repository.get_candidates_by_ids(
                selected_candidate_ids
            )
        )
        local_lookup = {c.id: c for c in existing_candidates}

        # 2. Partition candidate IDs into three groups: missing, stale, fresh
        missing_ids: list[UUID] = []
        stale_ids: list[UUID] = []
        fresh_ids: list[UUID] = []

        now = datetime.now(UTC)
        threshold = timedelta(days=settings.CANDIDATE_REFRESH_AFTER_DAYS)

        for cid in selected_candidate_ids:
            candidate = local_lookup.get(cid)
            if candidate is None:
                missing_ids.append(cid)
                logger.info(
                    (
                        "Synchronization Decision: candidate_id=%s, "
                        "local_existence=False, local_updated_at=None, "
                        "freshness_decision=missing, "
                        "status=synchronized, "
                        "reason_for_synchronization=missing"
                    ),
                    cid,
                )
            else:
                updated_at = candidate.updated_at
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=UTC)

                time_diff = now - updated_at
                if time_diff > threshold:
                    stale_ids.append(cid)
                    logger.info(
                        (
                            "Synchronization Decision: candidate_id=%s, "
                            "local_existence=True, local_updated_at=%s, "
                            "freshness_decision=stale, "
                            "status=synchronized, "
                            "reason_for_synchronization=stale"
                        ),
                        cid,
                        candidate.updated_at,
                    )
                else:
                    fresh_ids.append(cid)
                    logger.info(
                        (
                            "Synchronization Decision: candidate_id=%s, "
                            "local_existence=True, local_updated_at=%s, "
                            "freshness_decision=fresh, "
                            "status=skipped, "
                            "reason_for_synchronization=skipped"
                        ),
                        cid,
                        candidate.updated_at,
                    )
                    batch_result.results[cid] = CandidateSyncResultItem(
                        candidate_id=cid, success=True, duration_ms=0.0
                    )

        # 3. Combine Missing and Stale candidate IDs
        union_ids = missing_ids + stale_ids

        # 4. If no candidates to synchronize, return batch_result
        if not union_ids:
            return batch_result

        # 5. Fetch updated/latest profiles from the Sourcing Service in a single request
        start_time = time.perf_counter()
        try:
            updated_details = await self.search_client.get_candidate_details(union_ids)
            api_duration = (time.perf_counter() - start_time) * 1000.0
        except Exception as e:
            api_duration = (time.perf_counter() - start_time) * 1000.0
            logger.exception(
                "Failed to fetch candidate details for synchronization: %s", e
            )
            for cid in union_ids:
                batch_result.results[cid] = CandidateSyncResultItem(
                    candidate_id=cid,
                    success=False,
                    error_code="SOURCING_CLIENT_ERROR",
                    error_message=str(e),
                    duration_ms=api_duration,
                )
            return batch_result

        returned_ids = [d.id for d in updated_details]
        missing_sync_ids = [cid for cid in union_ids if cid not in returned_ids]
        if missing_sync_ids:
            logger.warning(
                "Synchronization mismatch\nRequested:\n%s\nReturned:\n%s\nMissing:\n%s",
                [str(i) for i in union_ids],
                [str(i) for i in returned_ids],
                [str(i) for i in missing_sync_ids],
            )
            for cid in missing_sync_ids:
                batch_result.results[cid] = CandidateSyncResultItem(
                    candidate_id=cid,
                    success=False,
                    error_code="CANDIDATE_OMITTED_IN_RESPONSE",
                    error_message=(
                        "Candidate details not returned by "
                        "external sourcing service"
                    ),
                    duration_ms=api_duration,
                )

        # 6. Persist each fetched profile sequentially to ensure transaction safety
        for details in updated_details:
            cid = details.id
            db_start = time.perf_counter()
            try:
                await self.scoring_service.upsert_candidate_profile(details)
                db_duration = (time.perf_counter() - db_start) * 1000.0
                batch_result.results[cid] = CandidateSyncResultItem(
                    candidate_id=cid,
                    success=True,
                    duration_ms=api_duration + db_duration,
                )
            except Exception as e:
                db_duration = (time.perf_counter() - db_start) * 1000.0
                logger.exception(
                    "Failed to synchronize candidate profile for ID %s: %s", cid, e
                )
                batch_result.results[cid] = CandidateSyncResultItem(
                    candidate_id=cid,
                    success=False,
                    error_code="DB_PERSISTENCE_ERROR",
                    error_message=str(e),
                    duration_ms=api_duration + db_duration,
                )

        return batch_result
