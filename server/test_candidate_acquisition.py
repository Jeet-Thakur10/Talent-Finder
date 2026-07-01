"""Verification script for CandidateAcquisitionService.

Tests three cases with mocked dependencies — no DB, no external service, no LLM required.

Usage:
    cd server
    python test_candidate_acquisition.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.services.candidate_acquisition_service import (
    CandidateAcquisitionService,
)
from src.schemas.candidate_search_schema import (
    CandidateSearchRequest,
    CandidateSearchResponse,
    CandidateSummary,
)
from src.schemas.scoring_schema import CompressedCandidate

# ── Helpers ──────────────────────────────────────────────────────────────────


def make_fake_candidate(index: int) -> MagicMock:
    """Create a mock Candidate ORM object with a unique id and name."""
    candidate = MagicMock()
    candidate.id = uuid4()
    candidate.full_name = f"Local Candidate {index}"
    candidate.current_title = f"Engineer {index}"
    candidate.total_experience_months = 36 + index
    candidate.skills = []
    candidate.experiences = []
    return candidate


def make_fake_sourced_summary(index: int) -> CandidateSummary:
    """Create a CandidateSummary as the sourcing service would return."""
    return CandidateSummary(
        candidate_id=uuid4(),
        profile_text=f"Sourced Candidate {index} | Engineer | 3+ years",
    )


def make_compressed(candidate: MagicMock) -> CompressedCandidate:
    """Simulate _build_compressed_candidate logic."""
    return CompressedCandidate(
        candidate_id=candidate.id,
        profile_text=f"Title: {candidate.current_title}\nExperience: {candidate.total_experience_months / 12:.1f} years",
    )


def make_fake_job_description() -> MagicMock:
    """Create a mock JobDescription with skills."""
    jd = MagicMock()
    jd.id = uuid4()
    jd.title = "Senior Backend Engineer"
    jd.min_experience = 3
    jd.max_experience = 8
    jd.skills = []

    skill1 = MagicMock()
    skill1.skill_name = "Python"
    skill1.is_mandatory = True

    skill2 = MagicMock()
    skill2.skill_name = "PostgreSQL"
    skill2.is_mandatory = False

    jd.skills = [skill1, skill2]
    return jd


# ── Test Cases ───────────────────────────────────────────────────────────────


async def test_case_1():
    """Case 1: local_count (150) >= required (100) — no external call."""
    print("\n" + "=" * 70)
    print("CASE 1: Local pool sufficient (150 local, 100 required)")
    print("=" * 70)

    local_candidates = [make_fake_candidate(i) for i in range(150)]
    jd = make_fake_job_description()

    local_search_fn = AsyncMock(return_value=local_candidates)
    compress_fn = MagicMock(side_effect=make_compressed)
    search_query_agent = MagicMock()
    search_client = MagicMock()
    search_client.search_candidates = AsyncMock()

    service = CandidateAcquisitionService(
        local_search_fn=local_search_fn,
        compress_candidate_fn=compress_fn,
        search_query_agent=search_query_agent,
        search_client=search_client,
    )

    result = await service.acquire_candidates(
        job_description=jd,
        job_description_id=jd.id,
        required_prescore_candidates=100,
    )

    # Assertions
    assert result.sourcing_skipped is True, "Expected sourcing to be skipped"
    assert result.local_count == 150, (
        f"Expected local_count=150, got {result.local_count}"
    )
    assert result.sourced_count == 0, (
        f"Expected sourced_count=0, got {result.sourced_count}"
    )
    assert len(result.candidates) == 150, (
        f"Expected 150 candidates, got {len(result.candidates)}"
    )

    # External service should NEVER have been called
    search_query_agent.generate_search_query.assert_not_called()
    search_client.search_candidates.assert_not_called()

    print(f"\n  * Local candidates found:       {result.local_count}")
    print("  [OK] External request payload:      SKIPPED (local pool sufficient)")
    print(f"  * External candidates received:  {result.sourced_count}")
    print(f"  * Total merged candidates:       {len(result.candidates)}")
    print(f"  * Sourcing skipped:              {result.sourcing_skipped}")
    print("\n  >>> CASE 1 PASSED\n")


async def test_case_2():
    """Case 2: local_count (30) < required (100) — external sourcing triggered."""
    print("\n" + "=" * 70)
    print("CASE 2: Local pool insufficient (30 local, 100 required)")
    print("=" * 70)

    local_candidates = [make_fake_candidate(i) for i in range(30)]
    sourced_summaries = [make_fake_sourced_summary(i) for i in range(70)]
    jd = make_fake_job_description()

    local_search_fn = AsyncMock(return_value=local_candidates)
    compress_fn = MagicMock(side_effect=make_compressed)

    # Mock the search query agent to return a CandidateSearchRequest
    mock_search_request = CandidateSearchRequest(
        title="Backend Engineer",
        skills=["Python", "PostgreSQL"],
        min_experience=3,
        required_candidates=70,
        max_source_resumes=20,
    )
    search_query_agent = MagicMock()
    search_query_agent.generate_search_query.return_value = mock_search_request

    # Mock the search client to return sourced candidates
    mock_response = CandidateSearchResponse(candidates=sourced_summaries)
    search_client = MagicMock()
    search_client.search_candidates = AsyncMock(return_value=mock_response)

    service = CandidateAcquisitionService(
        local_search_fn=local_search_fn,
        compress_candidate_fn=compress_fn,
        search_query_agent=search_query_agent,
        search_client=search_client,
    )

    result = await service.acquire_candidates(
        job_description=jd,
        job_description_id=jd.id,
        required_prescore_candidates=100,
    )

    # Assertions
    assert result.sourcing_skipped is False, "Expected sourcing NOT to be skipped"
    assert result.local_count == 30, (
        f"Expected local_count=30, got {result.local_count}"
    )
    assert result.sourced_count == 70, (
        f"Expected sourced_count=70, got {result.sourced_count}"
    )
    assert len(result.candidates) == 100, (
        f"Expected 100 candidates, got {len(result.candidates)}"
    )

    # Verify the agent was called
    search_query_agent.generate_search_query.assert_called_once()

    # Verify the search client received the correct request
    search_client.search_candidates.assert_called_once()
    actual_request = search_client.search_candidates.call_args[0][0]
    assert actual_request.required_candidates == 70, (
        f"Expected required_candidates=70, got {actual_request.required_candidates}"
    )
    assert len(actual_request.exclude_candidate_ids) == 30, (
        f"Expected 30 exclude IDs, got {len(actual_request.exclude_candidate_ids)}"
    )

    # Verify exclude IDs match local candidate IDs
    local_ids = {c.id for c in local_candidates}
    exclude_ids = set(actual_request.exclude_candidate_ids)
    assert local_ids == exclude_ids, "Exclude IDs should match local candidate IDs"

    print(f"\n  * Local candidates found:       {result.local_count}")
    print("  * External request payload:")
    print(f"      required_candidates:        {actual_request.required_candidates}")
    print(
        f"      exclude_candidate_ids:      {len(actual_request.exclude_candidate_ids)} IDs"
    )
    print(f"      title:                      {actual_request.title}")
    print(f"      skills:                     {actual_request.skills}")
    print(f"  * External candidates received:  {result.sourced_count}")
    print(f"  * Total merged candidates:       {len(result.candidates)}")
    print(f"  * Sourcing skipped:              {result.sourcing_skipped}")
    print("\n  >>> CASE 2 PASSED\n")


async def test_case_3():
    """Case 3: local_count (0) — entire pool from external sourcing."""
    print("\n" + "=" * 70)
    print("CASE 3: No local candidates (0 local, 100 required)")
    print("=" * 70)

    local_candidates: list = []
    sourced_summaries = [make_fake_sourced_summary(i) for i in range(100)]
    jd = make_fake_job_description()

    local_search_fn = AsyncMock(return_value=local_candidates)
    compress_fn = MagicMock(side_effect=make_compressed)

    mock_search_request = CandidateSearchRequest(
        title="Backend Engineer",
        skills=["Python", "PostgreSQL"],
        min_experience=3,
        required_candidates=100,
        max_source_resumes=20,
    )
    search_query_agent = MagicMock()
    search_query_agent.generate_search_query.return_value = mock_search_request

    mock_response = CandidateSearchResponse(candidates=sourced_summaries)
    search_client = MagicMock()
    search_client.search_candidates = AsyncMock(return_value=mock_response)

    service = CandidateAcquisitionService(
        local_search_fn=local_search_fn,
        compress_candidate_fn=compress_fn,
        search_query_agent=search_query_agent,
        search_client=search_client,
    )

    result = await service.acquire_candidates(
        job_description=jd,
        job_description_id=jd.id,
        required_prescore_candidates=100,
    )

    # Assertions
    assert result.sourcing_skipped is False, "Expected sourcing NOT to be skipped"
    assert result.local_count == 0, f"Expected local_count=0, got {result.local_count}"
    assert result.sourced_count == 100, (
        f"Expected sourced_count=100, got {result.sourced_count}"
    )
    assert len(result.candidates) == 100, (
        f"Expected 100 candidates, got {len(result.candidates)}"
    )

    # Verify external call with correct parameters
    search_client.search_candidates.assert_called_once()
    actual_request = search_client.search_candidates.call_args[0][0]
    assert actual_request.required_candidates == 100, (
        f"Expected required_candidates=100, got {actual_request.required_candidates}"
    )
    assert len(actual_request.exclude_candidate_ids) == 0, (
        f"Expected 0 exclude IDs, got {len(actual_request.exclude_candidate_ids)}"
    )

    print(f"\n  * Local candidates found:       {result.local_count}")
    print("  * External request payload:")
    print(f"      required_candidates:        {actual_request.required_candidates}")
    print(
        f"      exclude_candidate_ids:      {len(actual_request.exclude_candidate_ids)} IDs"
    )
    print(f"      title:                      {actual_request.title}")
    print(f"      skills:                     {actual_request.skills}")
    print(f"  * External candidates received:  {result.sourced_count}")
    print(f"  * Total merged candidates:       {len(result.candidates)}")
    print(f"  * Sourcing skipped:              {result.sourcing_skipped}")
    print("\n  >>> CASE 3 PASSED\n")


# -- Main ---------------------------------------------------------------------


async def run_all():
    print("\n" + "#" * 70)
    print("  CANDIDATE ACQUISITION SERVICE -- VERIFICATION")
    print("#" * 70)

    # Enable logging so acquisition service logs are visible
    logging.basicConfig(
        level=logging.INFO,
        format="  [%(levelname)s] %(name)s: %(message)s",
    )

    passed = 0
    failed = 0

    for test_fn in [test_case_1, test_case_2, test_case_3]:
        try:
            await test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n  [FAIL] {test_fn.__doc__.strip()} FAILED: {e}\n")
            import traceback

            traceback.print_exc()

    print("=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all())
