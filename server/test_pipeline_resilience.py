"""Verification script for scoring pipeline resilience.

Mocks external sourcing failures, synchronization failures, and deep scoring failures
to verify that they are correctly isolated and do not crash the pipeline request.

Usage:
    cd server
    uv run python test_pipeline_resilience.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timezone

from src.core.services.candidate_acquisition_service import CandidateAcquisitionService
from src.core.services.candidate_synchronization_service import CandidateSynchronizationService
from src.core.services.scoring_service import ScoringService
from src.core.exceptions.scoring_exceptions import SourcingServiceClientError
from src.schemas.candidate_search_schema import (
    CandidateSearchRequest,
    CandidateSearchResponse,
    CandidateSummary,
)
from src.schemas.scoring_schema import (
    PipelineExecutionRequest,
    CompressedCandidate,
    CandidateScoreResponse,
    CandidateScoreOutput,
    CandidateScoreExplanation,
)
from src.schemas.job_description_schema import (
    JobDescriptionResponse,
    JDSkillResponse,
)


# Setup basic logger
logging.basicConfig(level=logging.INFO, format="  [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_pipeline_resilience")


# Fake Data Generators
def make_fake_candidate(index: int) -> MagicMock:
    candidate = MagicMock()
    candidate.id = uuid4()
    candidate.full_name = f"Local Candidate {index}"
    candidate.current_title = f"Engineer {index}"
    candidate.location = f"Location {index}"
    candidate.summary = f"Summary {index}"
    candidate.total_experience_months = 36 + index
    candidate.skills = []
    candidate.experiences = []
    return candidate


def mock_compress(candidate: MagicMock) -> CompressedCandidate:
    return CompressedCandidate(
        candidate_id=candidate.id,
        profile_text=f"Title: {candidate.current_title}\nExperience: {candidate.total_experience_months / 12:.1f} years",
    )


# ── Test Cases ───────────────────────────────────────────────────────────────

async def test_candidate_acquisition_resilience():
    """Verify that SourcingServiceClientError is caught and local candidates are returned."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Candidate Acquisition Resilience to Sourcing Client Failure")
    logger.info("=" * 80)

    local_candidates = [make_fake_candidate(i) for i in range(5)]
    local_search_fn = AsyncMock(return_value=local_candidates)
    compress_fn = MagicMock(side_effect=mock_compress)
    search_query_agent = MagicMock()
    
    # Mock client to throw SourcingServiceClientError
    search_client = MagicMock()
    search_client.search_candidates = AsyncMock(
        side_effect=SourcingServiceClientError(
            details="Sourcing service is down!",
            status_code=503
        )
    )

    service = CandidateAcquisitionService(
        local_search_fn=local_search_fn,
        compress_candidate_fn=compress_fn,
        search_query_agent=search_query_agent,
        search_client=search_client,
    )

    # Trigger acquisition. Even though sourcing fails, it should catch the error
    # and return the local matched summaries.
    jd = MagicMock()
    jd.id = uuid4()
    jd.title = "Backend Engineer"
    jd.skills = []

    result = await service.acquire_candidates(
        job_description=jd,
        job_description_id=jd.id,
        required_prescore_candidates=20,  # exceeds local count (5), so sourcing is triggered
    )

    # Sourcing should fail, but local summaries must still be returned
    assert len(result.candidates) == len(local_candidates)
    logger.info("  [PASS] Successfully caught SourcingServiceClientError and returned local candidates.")


async def test_candidate_synchronization_resilience():
    """Verify that synchronization catches individual upsert failures and continues."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Candidate Synchronization Resilience to Upsert Failures")
    logger.info("=" * 80)

    scoring_service = MagicMock()
    
    # Mock upsert_candidate_profile to fail for the first candidate, but succeed for the second
    c1_id = uuid4()
    c2_id = uuid4()
    
    async def mock_upsert(details):
        if details.id == c1_id:
            raise ValueError("Database constraint error for C1")
        return MagicMock()
        
    scoring_service.upsert_candidate_profile = AsyncMock(side_effect=mock_upsert)
    scoring_service.repository.get_candidates_by_ids = AsyncMock(return_value=[])

    search_client = MagicMock()
    details_c1 = MagicMock(id=c1_id)
    details_c2 = MagicMock(id=c2_id)
    search_client.get_candidate_details = AsyncMock(return_value=[details_c1, details_c2])

    sync_service = CandidateSynchronizationService(
        scoring_service=scoring_service,
        search_client=search_client,
    )

    # Run synchronization. It should not raise an exception.
    await sync_service.synchronize_candidates([c1_id, c2_id])
    
    # Assertions
    assert scoring_service.upsert_candidate_profile.call_count == 2
    logger.info("  [PASS] Successfully caught individual upsert exception and proceeded to next candidate.")


async def test_deep_scoring_isolation():
    """Verify that a failure in one candidate's scoring does not fail the entire deep-scoring run."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Deep Scoring Resilience to Individual Candidate Failures")
    logger.info("=" * 80)

    # Initialize a mock DB session
    db_mock = MagicMock()
    service = ScoringService(db_mock)
    
    c1 = make_fake_candidate(1)
    c2 = make_fake_candidate(2)
    service.repository.get_candidates_for_job_description = AsyncMock(return_value=[c1, c2])
    service.repository.upsert_candidate_scores = AsyncMock()
    service.repository.upsert_pipeline_entries = AsyncMock()
    
    # Mock authorized JD using schema
    jd_resp = JobDescriptionResponse(
        id=uuid4(),
        title="Backend Engineer",
        department="Engineering",
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=2,
        max_experience=5,
        location="Remote",
        education_requirement="BS",
        preferred_qualifications="MS",
        employment_type_id=uuid4(),
        status_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        skills=[]
    )
    service._get_authorized_job_description = AsyncMock(return_value=jd_resp)

    # Mock scoring client: candidate 1 throws ValueError (e.g. LLM API failed), candidate 2 succeeds
    async def mock_score_candidate(jd_input, cand_input):
        if cand_input.candidate_id == c1.id:
            raise ValueError("LLM request rate-limited for Candidate 1")
        
        explanation = CandidateScoreExplanation(
            summary="Fine fit",
            strengths=["Python"],
            weaknesses=[]
        )
        score_output = CandidateScoreOutput(
            candidate_id=c2.id,
            final_score=90.0,
            confidence=85.0,
            skills_score=10.0,
            experience_score=10.0,
            recency_score=10.0,
            role_fit_score=10.0,
            education_score=10.0,
            matched_mandatory_skills=["Python"],
            matched_optional_skills=[],
            missing_mandatory_skills=[],
            explanation=explanation
        )
        return MagicMock(payload=score_output)

    service.scoring_client.score_candidate = AsyncMock(side_effect=mock_score_candidate)

    # Run scoring
    output = await service.score_candidates_for_job_description(
        job_description_id=jd_resp.id,
        current_user=MagicMock(),
        candidate_ids=[c1.id, c2.id],
    )

    # Assertions: candidate 2's score should be returned, candidate 1's error should be caught
    assert len(output.scores) == 1
    assert output.scores[0].candidate_id == c2.id
    service.repository.upsert_candidate_scores.assert_called_once_with(
        job_description_id=jd_resp.id,
        scores=[output.scores[0]]
    )
    logger.info("  [PASS] Successfully isolated individual deep scoring exceptions using return_exceptions=True.")


# ── Run All ──────────────────────────────────────────────────────────────────

async def main():
    logger.info("Starting Pipeline Resilience Verification Script...")
    passed = 0
    failed = 0

    tests = [
        test_candidate_acquisition_resilience,
        test_candidate_synchronization_resilience,
        test_deep_scoring_isolation,
    ]

    for test_fn in tests:
        try:
            await test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            logger.error(f"[FAIL] {test_fn.__name__} failed: {e}")
            import traceback
            traceback.print_exc()

    logger.info("\n" + "=" * 80)
    logger.info(f"  RESILIENCE RESULTS: {passed} passed, {failed} failed")
    logger.info("=" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
