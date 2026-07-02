from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from uuid import UUID

from pydantic import BaseModel

from src.config.settings import settings
from src.control.agents.candidate_search_query_agent import CandidateSearchQueryAgent
from src.data.clients.candidate_search_client import CandidateSearchClient
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.job_description import JobDescription
from src.schemas.candidate_search_schema import CandidateSummary
from src.schemas.job_description_schema import JobDescriptionResponse
from src.schemas.scoring_schema import CompressedCandidate, JobDescriptionScoringInput

logger = logging.getLogger(__name__)


class CandidateAcquisitionResult(BaseModel):
    """Unified result from the candidate acquisition process.

    The caller receives a single flat list of CandidateSummary objects
    and does not need to know where each candidate originated.
    """

    candidates: list[CandidateSummary]
    local_count: int
    sourced_count: int
    sourcing_skipped: bool


class CandidateAcquisitionService:
    """Orchestrates building the complete candidate pool for scoring.

    Responsible only for acquiring candidates from local DB search
    and external sourcing. Does NOT perform pre-scoring, deep scoring,
    ranking, filtering, or thresholding.

    Dependencies are injected as callables to avoid direct repository
    coupling and to reuse existing search logic from the ScoringService.
    """

    def __init__(
        self,
        local_search_fn: Callable[[UUID], Awaitable[list[Candidate]]],
        compress_candidate_fn: Callable[[Candidate], CompressedCandidate],
        search_query_agent: CandidateSearchQueryAgent,
        search_client: CandidateSearchClient,
    ) -> None:
        self._local_search_fn = local_search_fn
        self._compress_candidate_fn = compress_candidate_fn
        self._search_query_agent = search_query_agent
        self._search_client = search_client

    async def acquire_candidates(
        self,
        job_description: JobDescription
        | JobDescriptionResponse
        | JobDescriptionScoringInput,
        job_description_id: UUID,
        required_prescore_candidates: int,
    ) -> CandidateAcquisitionResult:
        """Acquire a unified candidate pool from local search + external sourcing.

        Args:
            job_description: The job description to source candidates for.
            job_description_id: ID of the job description (used for local search).
            required_prescore_candidates: Target pool size (n × k).

        Returns:
            CandidateAcquisitionResult with a deduplicated, unified candidate list.
        """

        # Step 1 — Search local candidate database using existing logic
        local_candidates = await self._local_search_fn(job_description_id)
        local_count = len(local_candidates)

        logger.info(
            "Local candidate search completed: found %d candidates",
            local_count,
        )

        # Step 2 — Convert local Candidates to unified CandidateSummary type
        local_summaries = [
            self._to_candidate_summary(candidate) for candidate in local_candidates
        ]

        # Step 3 — If local pool is sufficient, return ALL without truncation
        if local_count >= required_prescore_candidates:
            logger.info(
                "Local pool (%d) >= required (%d) — skipping external sourcing",
                local_count,
                required_prescore_candidates,
            )
            return CandidateAcquisitionResult(
                candidates=local_summaries,
                local_count=local_count,
                sourced_count=0,
                sourcing_skipped=True,
            )

        # Step 4 — External sourcing needed
        needed = required_prescore_candidates - local_count
        logger.info(
            "Local pool (%d) < required (%d) — requesting %d from external sourcing",
            local_count,
            required_prescore_candidates,
            needed,
        )

        # 4a. Generate search request using the LLM agent
        search_request = self._search_query_agent.generate_search_query(
            job_description,
            min_candidates=needed,
            max_source_resumes=settings.DEFAULT_MAX_SOURCE_RESUMES,
        )

        # 4b. Override with computed acquisition parameters
        search_request.required_candidates = needed
        search_request.exclude_candidate_ids = [
            candidate.id for candidate in local_candidates
        ]
        print("\n[ScoringService] LLM generated CandidateSearchRequest:")
        print(f"  Generated title: {search_request.title}")
        print(f"  Generated skills (full list): {search_request.skills}")
        print(f"  min_experience: {search_request.min_experience}")
        print(f"  required_candidates: {search_request.required_candidates}")
        print(f"  max_source_resumes: {search_request.max_source_resumes}")
        print()

        logger.info(
            "External search request: required_candidates=%d, exclude_ids=%d, title=%s",
            search_request.required_candidates,
            len(search_request.exclude_candidate_ids),
            search_request.title,
        )

        # 4c. Call sourcing service
        from src.core.exceptions.scoring_exceptions import SourcingServiceClientError

        sourced_candidates = []
        try:
            response = await self._search_client.search_candidates(search_request)
            sourced_candidates = response.candidates
        except SourcingServiceClientError as e:
            logger.warning(
                "External sourcing client encountered a recoverable failure: %s", e
            )

        sourced_count = len(sourced_candidates)

        logger.info(
            "External sourcing completed: received %d candidates",
            sourced_count,
        )

        # Step 5 — Merge and deduplicate
        merged = local_summaries + sourced_candidates

        # Defensive deduplication by candidate_id
        seen: set[UUID] = set()
        deduplicated: list[CandidateSummary] = []
        for candidate in merged:
            if candidate.candidate_id not in seen:
                seen.add(candidate.candidate_id)
                deduplicated.append(candidate)

        duplicates_removed = len(merged) - len(deduplicated)
        if duplicates_removed > 0:
            logger.warning(
                "Defensive deduplication removed %d duplicate candidates",
                duplicates_removed,
            )

        logger.info(
            "Acquisition complete: local=%d, sourced=%d, total=%d",
            local_count,
            sourced_count,
            len(deduplicated),
        )

        return CandidateAcquisitionResult(
            candidates=deduplicated,
            local_count=local_count,
            sourced_count=sourced_count,
            sourcing_skipped=False,
        )

    def _to_candidate_summary(self, candidate: Candidate) -> CandidateSummary:
        """Convert a local Candidate ORM object to CandidateSummary
        using the existing compression logic."""
        compressed = self._compress_candidate_fn(candidate)
        return CandidateSummary(
            candidate_id=compressed.candidate_id,
            profile_text=compressed.profile_text,
        )
