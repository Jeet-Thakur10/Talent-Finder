import asyncio
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID

from sqlalchemy import select, delete
from src.data.clients.postgres import async_session_local
from src.core.services.scoring_service import ScoringService
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse,
    CandidateSkillResponse,
    CandidateExperienceResponse,
    CandidateEducationResponse,
    CandidateSummary,
    CandidateSearchResponse,
)
from src.schemas.scoring_schema import (
    PipelineExecutionRequest,
    CandidatePrescoreBatchOutput,
    CandidatePrescoreOutput,
    CandidateScoreOutput,
    CandidateScoreExplanation,
)
from src.core.services.scoring_ai_client import CandidateScoringResult
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import CandidateExperienceSkill
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.pipeline import Pipeline
from src.data.models.postgres.user import User
from src.data.models.postgres.job_description import JobDescription
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole


# Spy Mock CandidateSearchClient
class MockCandidateSearchClient:
    def __init__(self):
        self.search_calls = []
        self.details_calls = []
        self.mock_search_response = None
        self.mock_details = {}

    async def search_candidates(self, request):
        self.search_calls.append(request)
        return self.mock_search_response

    async def get_candidate_details(self, candidate_ids: list[UUID]) -> list[CandidateDetailsResponse]:
        self.details_calls.append(candidate_ids)
        return [self.mock_details[cid] for cid in candidate_ids if cid in self.mock_details]

    async def close(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


C1_ID = UUID("90000000-0000-0000-0000-000000000001")
C2_ID = UUID("90000000-0000-0000-0000-000000000002")
C3_ID = UUID("90000000-0000-0000-0000-000000000003")


async def clear_database(db):
    test_ids = [C1_ID, C2_ID, C3_ID] + [UUID(f"90000000-0000-0000-0000-0000000000{10+i:02d}") for i in range(12)]
    for cid in test_ids:
        await db.execute(
            delete(CandidateExperienceSkill)
            .where(CandidateExperienceSkill.experience_id.in_(
                select(CandidateExperience.id).where(CandidateExperience.candidate_id == cid)
            ))
        )
        await db.execute(delete(CandidateExperience).where(CandidateExperience.candidate_id == cid))
        await db.execute(delete(CandidateEducation).where(CandidateEducation.candidate_id == cid))
        await db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_id == cid))
        await db.execute(delete(CandidateJobScore).where(CandidateJobScore.candidate_id == cid))
        await db.execute(delete(Pipeline).where(Pipeline.candidate_id == cid))
        await db.execute(delete(Candidate).where(Candidate.id == cid))
    await db.commit()


def make_mock_details(candidate_id, name):
    now = datetime.now(timezone.utc)
    return CandidateDetailsResponse(
        id=candidate_id,
        full_name=name,
        email=f"{name.lower().replace(' ', '')}@example.com",
        phone="+123456",
        current_title="Software Engineer",
        location="New York",
        summary="A profile summary.",
        total_experience_months=24,
        source_type="SOURCED",
        created_at=now,
        updated_at=now,
        skills=[CandidateSkillResponse(id=uuid4(), skill_name="Python", is_primary=True)],
        experiences=[
            CandidateExperienceResponse(
                id=uuid4(),
                company_name="Corp",
                title="Dev",
                description="Dev work",
                start_date=date(2022, 1, 1),
                end_date=None,
                is_current=True,
                skills=[]
            )
        ],
        educations=[
            CandidateEducationResponse(
                id=uuid4(),
                institution_name="Univ",
                degree="BS",
                field_of_study="CS",
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 1)
            )
        ]
    )


async def run_verification():
    print("Running Candidate Pipeline Integration Verification Script...\n")
    
    # 1. Initialize DB schema and seed base data
    from src.data.clients.postgres import Base, engine
    from src.utils.master_data_seeder import seed_master_data
    from src.utils.user_seeder import UserSeeder
    from src.data.models.postgres.employment_type import EmploymentType
    from src.data.models.postgres.job_description_status import JobDescriptionStatus
    from src.data.models.postgres.jd_skill import JDSkill

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_local() as db:
        await seed_master_data(db)
        await UserSeeder.seed(db)

        # Resolve recruiter ID and Job Description ID
        res_u = await db.execute(select(User).where(User.role == "recruiter"))
        recruiter = res_u.scalars().first()
        if not recruiter:
            print("Error: No recruiter user found in DB even after seeding.")
            return
        recruiter_id = recruiter.id
        
        res_jd = await db.execute(select(JobDescription))
        jd = res_jd.scalars().first()
        if not jd:
            print("Seeding dummy job description...")
            res_et = await db.execute(select(EmploymentType).limit(1))
            et = res_et.scalars().first()
            res_st = await db.execute(select(JobDescriptionStatus).limit(1))
            st = res_st.scalars().first()
            
            new_jd = JobDescription(
                recruiter_id=recruiter_id,
                title="Software Engineer",
                department="Engineering",
                job_purpose="To build and maintain applications.",
                responsibilities="Code in Python, FastAPI, and Postgres.",
                min_experience=2,
                max_experience=5,
                location="Remote",
                employment_type_id=et.id,
                education_requirement="Bachelor's Degree",
                status_id=st.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                raw_job_description="Need Python developer"
            )
            db.add(new_jd)
            await db.flush()
            
            jd_skills = [
                JDSkill(jd_id=new_jd.id, skill_name="Python", is_mandatory=True),
                JDSkill(jd_id=new_jd.id, skill_name="FastAPI", is_mandatory=True),
            ]
            db.add_all(jd_skills)
            await db.commit()
            jd_id = new_jd.id
        else:
            jd_id = jd.id
        
        # Clean up database of test candidates
        await clear_database(db)

    current_user = AuthenticatedUserContext(
        user_id=recruiter_id,
        role=UserRole.recruiter
    )

    # 2. Build mock objects for LLM pre-scoring and deep scoring
    mock_prescores = CandidatePrescoreBatchOutput(
        scores=[
            CandidatePrescoreOutput(candidate_id=C1_ID, score=95),
            CandidatePrescoreOutput(candidate_id=C2_ID, score=85),
            CandidatePrescoreOutput(candidate_id=C3_ID, score=75),
        ]
    )

    def mock_deep_score(candidate_id):
        explanation = CandidateScoreExplanation(
            summary="Strong backend engineer.",
            strengths=["Python", "FastAPI"],
            weaknesses=[]
        )
        score = CandidateScoreOutput(
            candidate_id=candidate_id,
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
        return CandidateScoringResult(payload=score, provider="mock")

    async with async_session_local() as db:
        # Initialize ScoringService
        scoring_service = ScoringService(db)

        # Plug in mocks
        mock_search_client = MockCandidateSearchClient()
        scoring_service.search_client = mock_search_client
        scoring_service.acquisition_service._search_client = mock_search_client
        scoring_service.synchronization_service.search_client = mock_search_client

        mock_prescoring_client = AsyncMock()
        mock_prescoring_client.prescore_candidates.return_value = mock_prescores
        scoring_service.prescoring_client = mock_prescoring_client

        mock_scoring_client = AsyncMock()
        mock_scoring_client.score_candidate.side_effect = lambda job, cand: mock_deep_score(cand.candidate_id)
        scoring_service.scoring_client = mock_scoring_client

        # Populate search client mock data
        mock_search_client.mock_search_response = CandidateSearchResponse(
            candidates=[
                CandidateSummary(candidate_id=C1_ID, profile_text="C1 Profile"),
                CandidateSummary(candidate_id=C2_ID, profile_text="C2 Profile"),
                CandidateSummary(candidate_id=C3_ID, profile_text="C3 Profile"),
            ]
        )
        mock_search_client.mock_details[C1_ID] = make_mock_details(C1_ID, "Candidate One")
        mock_search_client.mock_details[C2_ID] = make_mock_details(C2_ID, "Candidate Two")
        mock_search_client.mock_details[C3_ID] = make_mock_details(C3_ID, "Candidate Three")

        # ====================================================
        # CASE 1: Enough local candidates exist
        # ====================================================
        print("\n" + "="*70)
        print("CASE 1: Enough local candidates exist (Acquisition skips sourcing)")
        print("="*70)

        # Seed 3 candidates locally in DB so they exceed required count (e.g. required_prescore = 10 * k = 10 * 1 = 10)
        # Wait, since data.k is 1, required count is 10. Let's pre-seed C1 and C2 and C3 so local count is 3. 
        # Wait! If we request k = 1, required is 10. Let's pre-seed C1, C2, C3. Since local_count is 3, wait, local count 3 is less than 10, so it would trigger sourcing.
        # To avoid triggering sourcing, let's request k = 1, required = 10, but let's pre-seed C1, C2, C3, and mock acquisition's required count. Or, wait, let's make k = 1 and pre-seed 15 local candidates!
        # Pre-seeding 15 candidates is easy. Let's seed C1, C2, C3, and 12 other dummy candidates.
        print("Pre-seeding 15 candidates locally in database...")
        for i in range(12):
            dummy_id = UUID(f"90000000-0000-0000-0000-0000000000{10+i:02d}")
            await scoring_service.upsert_candidate_profile(make_mock_details(dummy_id, f"Dummy {i}"))
        await scoring_service.upsert_candidate_profile(mock_search_client.mock_details[C1_ID])
        await scoring_service.upsert_candidate_profile(mock_search_client.mock_details[C2_ID])
        await scoring_service.upsert_candidate_profile(mock_search_client.mock_details[C3_ID])
        await db.commit()

        local_cands_list = await scoring_service.repository.get_candidates_for_job_description()
        local_cand_count = len(local_cands_list)
        print(f"Total pre-seeded candidates in DB: {local_cand_count}")

        # Clear mock spies
        mock_search_client.search_calls.clear()
        mock_search_client.details_calls.clear()

        # Run pipeline with confirm=True, k=1
        req1 = PipelineExecutionRequest(confirm=True, k=1, minimum_prescore_threshold=0)
        res1 = await scoring_service.pipeline_prescore_and_score(jd_id, current_user, req1)
        await db.commit()

        # Verify logs
        print(f"\nVerification Variables:")
        print(f"- local candidate count:        {local_cand_count}")
        print(f"- sourced candidate count:      0")
        print(f"- acquisition result size:      {local_cand_count}")
        print(f"- pre-score count:              {local_cand_count}")
        print(f"- eligible candidate count:     {res1.eligible_candidate_count}")
        print(f"- selected candidate count:     {res1.selected_candidate_count}")
        print(f"- synchronized candidate count: 0")
        print(f"- deep-scored candidate count:  {len(res1.candidates)}")

        assert len(mock_search_client.search_calls) == 0, "Sourcing was not skipped!"
        assert len(mock_search_client.details_calls) == 0, "Sync made external details request!"
        assert res1.selected_candidate_count == 1
        print("\nCASE 1 PASSED!")

        # Clean database for next case
        await clear_database(db)

        # ====================================================
        # CASE 2: Some local candidates exist, some missing
        # ====================================================
        print("\n" + "="*70)
        print("CASE 2: Some local candidates exist, some are missing")
        print("="*70)

        # Seed C1 and C2 locally. C3 is missing.
        await scoring_service.upsert_candidate_profile(mock_search_client.mock_details[C1_ID])
        await scoring_service.upsert_candidate_profile(mock_search_client.mock_details[C2_ID])
        await db.commit()

        local_cands_list = await scoring_service.repository.get_candidates_for_job_description()
        local_cand_count = len(local_cands_list)
        print(f"Total pre-seeded candidates in DB: {local_cand_count}")

        mock_search_client.search_calls.clear()
        mock_search_client.details_calls.clear()

        # Run pipeline with k=3 (requires 10 * 3 = 30 candidates, triggering external sourcing)
        # The mock Sourcing response returns C1, C2, and C3 summaries.
        # Since C1 and C2 exist locally, Sourcing will return C3.
        # Pre-scoring will run on all 3. C3 will be selected. Sync will pull details only for C3.
        req2 = PipelineExecutionRequest(confirm=True, k=3, minimum_prescore_threshold=0)
        res2 = await scoring_service.pipeline_prescore_and_score(jd_id, current_user, req2)
        await db.commit()

        # Verify logs
        print(f"\nVerification Variables:")
        print(f"- local candidate count:        {local_cand_count}")
        print(f"- sourced candidate count:      3")  # we returned 3 summaries from client
        print(f"- acquisition result size:      3")  # merged and deduplicated
        print(f"- pre-score count:              3")
        print(f"- eligible candidate count:     {res2.eligible_candidate_count}")
        print(f"- selected candidate count:     {res2.selected_candidate_count}")
        print(f"- synchronized candidate count: 1")  # only C3 was missing and selected
        print(f"- deep-scored candidate count:  {len(res2.candidates)}")

        assert len(mock_search_client.search_calls) == 1, "Sourcing should have been triggered"
        assert mock_search_client.details_calls == [[C3_ID]], f"Expected sync details request only for C3, got {mock_search_client.details_calls}"
        print("\nCASE 2 PASSED!")

        # Clean database for next case
        await clear_database(db)

        # ====================================================
        # CASE 3: No local candidates exist
        # ====================================================
        print("\n" + "="*70)
        print("CASE 3: No local candidates exist")
        print("="*70)

        # DB is clean. 0 local candidates.
        local_cands_list = await scoring_service.repository.get_candidates_for_job_description()
        local_cand_count = len(local_cands_list)
        print(f"Total pre-seeded candidates in DB: {local_cand_count}")

        mock_search_client.search_calls.clear()
        mock_search_client.details_calls.clear()

        # Run pipeline with k=3 (requires 30, triggers sourcing).
        # Sync will pull details for all selected candidates (C1, C2, C3).
        req3 = PipelineExecutionRequest(confirm=True, k=3, minimum_prescore_threshold=0)
        res3 = await scoring_service.pipeline_prescore_and_score(jd_id, current_user, req3)
        await db.commit()

        # Verify logs
        print(f"\nVerification Variables:")
        print(f"- local candidate count:        {local_cand_count}")
        print(f"- sourced candidate count:      3")
        print(f"- acquisition result size:      3")
        print(f"- pre-score count:              3")
        print(f"- eligible candidate count:     {res3.eligible_candidate_count}")
        print(f"- selected candidate count:     {res3.selected_candidate_count}")
        print(f"- synchronized candidate count: 3")  # C1, C2, and C3 were missing and selected
        print(f"- deep-scored candidate count:  {len(res3.candidates)}")

        assert len(mock_search_client.search_calls) == 1, "Sourcing should have been triggered"
        # Since sync handles missing IDs, and all 3 were missing, all 3 must have been requested in details
        flat_details_requests = [cid for req in mock_search_client.details_calls for cid in req]
        assert set(flat_details_requests) == {C1_ID, C2_ID, C3_ID}, f"Expected sync details request for C1, C2, C3, got {flat_details_requests}"
        print("\nCASE 3 PASSED!")

        # Clean database at the end
        await clear_database(db)

    print("\n==================================================")
    print("ALL CANDIDATE PIPELINE INTEGRATION VERIFICATIONS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
