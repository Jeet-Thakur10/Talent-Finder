import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select

from src.core.services.candidate_synchronization_service import (
    CandidateSynchronizationService,
)
from src.core.services.scoring_service import ScoringService
from src.data.clients.postgres import async_session_local
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import CandidateExperienceSkill
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.pipeline import Pipeline
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse,
    CandidateEducationResponse,
    CandidateExperienceResponse,
    CandidateSkillResponse,
)

# Configure logging to verify log output format
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# Spy Mock CandidateSearchClient
class MockCandidateSearchClient:
    def __init__(self):
        self.called_with_ids = []
        self.mock_details = {}

    async def get_candidate_details(
        self, candidate_ids: list[UUID]
    ) -> list[CandidateDetailsResponse]:
        self.called_with_ids.append(candidate_ids)
        return [
            self.mock_details[cid] for cid in candidate_ids if cid in self.mock_details
        ]

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


C1_ID = UUID("f0000000-0000-0000-0000-000000000001")
C2_ID = UUID("f0000000-0000-0000-0000-000000000002")
C3_ID = UUID("f0000000-0000-0000-0000-000000000003")


async def clear_test_candidates(db):
    test_ids = [C1_ID, C2_ID, C3_ID]
    for cid in test_ids:
        # Delete experience skills
        await db.execute(
            delete(CandidateExperienceSkill).where(
                CandidateExperienceSkill.experience_id.in_(
                    select(CandidateExperience.id).where(
                        CandidateExperience.candidate_id == cid
                    )
                )
            )
        )
        await db.execute(
            delete(CandidateExperience).where(CandidateExperience.candidate_id == cid)
        )
        await db.execute(
            delete(CandidateEducation).where(CandidateEducation.candidate_id == cid)
        )
        await db.execute(
            delete(CandidateSkill).where(CandidateSkill.candidate_id == cid)
        )
        await db.execute(
            delete(CandidateJobScore).where(CandidateJobScore.candidate_id == cid)
        )
        await db.execute(delete(Pipeline).where(Pipeline.candidate_id == cid))
        await db.execute(delete(Candidate).where(Candidate.id == cid))
    await db.commit()


def make_mock_details(candidate_id, name, updated_at=None):
    now = updated_at or datetime.now(UTC)
    return CandidateDetailsResponse(
        id=candidate_id,
        full_name=name,
        email=f"{name.lower().replace(' ', '')}@example.com",
        phone="+123456",
        current_title="Engineer",
        location="New York",
        summary="A profile summary.",
        total_experience_months=24,
        source_type="SOURCED",
        created_at=now,
        updated_at=now,
        skills=[CandidateSkillResponse(skill_name="Python")],
        experiences=[
            CandidateExperienceResponse(
                company_name="Corp",
                title="Dev",
                description="Dev work",
                start_date=date(2022, 1, 1),
                end_date=None,
                is_current=True,
                skills=[],
            )
        ],
        educations=[
            CandidateEducationResponse(
                institution_name="Univ",
                degree="BS",
                field_of_study="CS",
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 1),
            )
        ],
    )


async def run_verification():
    print("Running Candidate Freshness Synchronization Verification Script...\n")

    async with async_session_local() as db:
        # Clean up database
        await clear_test_candidates(db)

        scoring_service = ScoringService(db)
        mock_client = MockCandidateSearchClient()
        sync_service = CandidateSynchronizationService(scoring_service, mock_client)

        now = datetime.now(UTC)

        # Populate client mocks with current data
        mock_client.mock_details[C1_ID] = make_mock_details(C1_ID, "Candidate One")
        mock_client.mock_details[C2_ID] = make_mock_details(C2_ID, "Candidate Two")
        mock_client.mock_details[C3_ID] = make_mock_details(C3_ID, "Candidate Three")

        # ====================================================
        # CASE 1: Candidate does not exist locally
        # ====================================================
        print("\n" + "=" * 70)
        print("CASE 1: Candidate does not exist locally (Download & Persist)")
        print("=" * 70)

        mock_client.called_with_ids.clear()

        await sync_service.synchronize_candidates([C2_ID])
        await db.commit()

        print(f"HTTP requests made: {mock_client.called_with_ids}")
        assert mock_client.called_with_ids == [[C2_ID]], (
            f"Expected sync call for [C2_ID], got {mock_client.called_with_ids}"
        )

        # Verify Candidate Two was persisted in local DB
        cand = await scoring_service.repository.get_candidate_by_id(C2_ID)
        assert cand is not None, "Candidate Two was not persisted!"
        print("Case 1 PASSED!")

        # Clean up database
        await clear_test_candidates(db)

        # ====================================================
        # CASE 2: Candidate exists locally and is fresh
        # ====================================================
        print("\n" + "=" * 70)
        print("CASE 2: Candidate exists locally and is fresh (Within threshold, Skip)")
        print("=" * 70)

        # Pre-seed C1 as fresh (updated 10 days ago)
        fresh_time = now - timedelta(days=10)
        fresh_details = make_mock_details(C1_ID, "Candidate One", updated_at=fresh_time)
        await scoring_service.upsert_candidate_profile(fresh_details)

        # Override local updated_at directly on ORM object to ensure database has correct date
        cand_c1 = await scoring_service.repository.get_candidate_by_id(C1_ID)
        cand_c1.updated_at = fresh_time
        await db.commit()

        mock_client.called_with_ids.clear()

        await sync_service.synchronize_candidates([C1_ID])
        await db.commit()

        print(f"HTTP requests made: {mock_client.called_with_ids}")
        assert len(mock_client.called_with_ids) == 0, (
            f"Expected no sync calls, got {mock_client.called_with_ids}"
        )
        print("Case 2 PASSED!")

        # Clean up database
        await clear_test_candidates(db)

        # ====================================================
        # CASE 3: Candidate exists locally and is stale
        # ====================================================
        print("\n" + "=" * 70)
        print(
            "CASE 3: Candidate exists locally and is stale (Older than threshold, Refresh)"
        )
        print("=" * 70)

        # Pre-seed C3 as stale (updated 45 days ago)
        stale_time = now - timedelta(days=45)
        stale_details = make_mock_details(
            C3_ID, "Candidate Three", updated_at=stale_time
        )
        await scoring_service.upsert_candidate_profile(stale_details)

        # Override local updated_at to ensure it is stale
        cand_c3 = await scoring_service.repository.get_candidate_by_id(C3_ID)
        cand_c3.updated_at = stale_time
        await db.commit()

        mock_client.called_with_ids.clear()

        # Update mock client to return latest details (current timestamp)
        mock_client.mock_details[C3_ID] = make_mock_details(
            C3_ID, "Candidate Three (Refreshed)"
        )

        await sync_service.synchronize_candidates([C3_ID])
        await db.commit()

        print(f"HTTP requests made: {mock_client.called_with_ids}")
        assert mock_client.called_with_ids == [[C3_ID]], (
            f"Expected sync call for [C3_ID], got {mock_client.called_with_ids}"
        )

        # Verify candidate name was updated (verifying UPSERT executed)
        cand = await scoring_service.repository.get_candidate_by_id(C3_ID)
        assert cand.full_name == "Candidate Three (Refreshed)", (
            "Candidate was not updated via UPSERT!"
        )
        print("Case 3 PASSED!")

        # Clean up database
        await clear_test_candidates(db)

        # ====================================================
        # CASE 4: Mixed batch of selected candidates
        # ====================================================
        print("\n" + "=" * 70)
        print("CASE 4: Mixed batch (Missing, Fresh, Stale)")
        print("=" * 70)

        # Setup:
        # C1_ID: exists locally, fresh (updated 10 days ago)
        # C2_ID: missing
        # C3_ID: exists locally, stale (updated 45 days ago)

        # Pre-seed C1 as fresh
        fresh_details = make_mock_details(
            C1_ID, "Candidate One", updated_at=now - timedelta(days=10)
        )
        await scoring_service.upsert_candidate_profile(fresh_details)
        cand_c1 = await scoring_service.repository.get_candidate_by_id(C1_ID)
        cand_c1.updated_at = now - timedelta(days=10)

        # Pre-seed C3 as stale
        stale_details = make_mock_details(
            C3_ID, "Candidate Three", updated_at=now - timedelta(days=45)
        )
        await scoring_service.upsert_candidate_profile(stale_details)
        cand_c3 = await scoring_service.repository.get_candidate_by_id(C3_ID)
        cand_c3.updated_at = now - timedelta(days=45)

        await db.commit()

        mock_client.called_with_ids.clear()

        # Execute mixed sync
        await sync_service.synchronize_candidates([C1_ID, C2_ID, C3_ID])
        await db.commit()

        print(f"HTTP requests made: {mock_client.called_with_ids}")
        # Only C2_ID (missing) and C3_ID (stale) should be requested in a single combined call
        assert len(mock_client.called_with_ids) == 1, "Expected exactly 1 HTTP call"
        requested_set = set(mock_client.called_with_ids[0])
        assert requested_set == {C2_ID, C3_ID}, (
            f"Expected request for {C2_ID, C3_ID}, got {requested_set}"
        )

        print("Case 4 PASSED!")

        # Clean up database
        await clear_test_candidates(db)

    print("\n==================================================")
    print("ALL CANDIDATE SYNCHRONIZATION VERIFICATIONS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
