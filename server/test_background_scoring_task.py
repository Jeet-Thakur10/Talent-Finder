import asyncio
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from src.core.services.scoring_ai_client import CandidateScoringResult
from src.core.services.scoring_task_service import ScoringTaskService
from src.core.tasks import async_run_scoring_pipeline
from src.data.clients.postgres import async_session_local
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import CandidateExperienceSkill
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.pipeline import Pipeline
from src.data.models.postgres.scoring_task import ScoringTask
from src.data.models.postgres.user import User
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse,
    CandidateEducationResponse,
    CandidateExperienceResponse,
    CandidateSearchResponse,
    CandidateSkillResponse,
    CandidateSummary,
)
from src.schemas.scoring_schema import (
    CandidatePrescoreBatchOutput,
    CandidatePrescoreOutput,
    CandidateScoreExplanation,
    CandidateScoreOutput,
)


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

    async def get_candidate_details(
        self, candidate_ids: list[UUID]
    ) -> list[CandidateDetailsResponse]:
        self.details_calls.append(candidate_ids)
        return [
            self.mock_details[cid] for cid in candidate_ids if cid in self.mock_details
        ]

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
    await db.execute(delete(CandidateExperienceSkill))
    await db.execute(delete(CandidateExperience))
    await db.execute(delete(CandidateEducation))
    await db.execute(delete(CandidateSkill))
    await db.execute(delete(CandidateJobScore))
    await db.execute(delete(Pipeline))
    await db.execute(delete(Candidate))
    await db.execute(delete(ScoringTask))
    await db.commit()


def make_mock_details(candidate_id, name):
    now = datetime.now(UTC)
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
        skills=[
            CandidateSkillResponse(id=uuid4(), skill_name="Python", is_primary=True)
        ],
        experiences=[
            CandidateExperienceResponse(
                id=uuid4(),
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
                id=uuid4(),
                institution_name="Univ",
                degree="BS",
                field_of_study="CS",
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 1),
            )
        ],
    )


async def run_verification():
    print("Running Background Scoring Task Integration Verification Script...\n")

    # 1. Initialize DB schema and seed base data
    from src.data.clients.postgres import Base, engine
    from src.utils.master_data_seeder import seed_master_data
    from src.utils.user_seeder import UserSeeder

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_local() as db:
        await seed_master_data(db)
        await UserSeeder.seed(db)

        # Resolve recruiter ID and Job Description ID
        res_u = await db.execute(select(User).where(User.role == "recruiter"))
        recruiter = res_u.scalars().first()
        if not recruiter:
            print("Error: No recruiter user found in DB.")
            return
        recruiter_id = recruiter.id

        res_jd = await db.execute(select(JobDescription))
        jd = res_jd.scalars().first()
        if not jd:
            print("Seeding dummy job description...")
            from src.data.models.postgres.employment_type import EmploymentType
            from src.data.models.postgres.jd_skill import JDSkill
            from src.data.models.postgres.job_description_status import (
                JobDescriptionStatus,
            )

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
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                raw_job_description="Need Python developer",
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

        # Clean database of test entries
        await clear_database(db)

    # 2. Build mocks
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
            weaknesses=[],
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
            explanation=explanation,
        )
        return CandidateScoringResult(payload=score, provider="mock")

    async with async_session_local() as db:
        # Patch ScoringService methods to use our mocks when constructed in task
        # We can construct the service and patch it or rely on monkeypatching.
        # However, to preserve clean architecture, let's inject mocks by mocking search clients.
        # But wait, tasks.py instantiates ScoringService inside async_run_scoring_pipeline.
        # So we can temporarily mock or subclass ScoringService or mock its internal client instances:

        # We can temporarily patch CandidateScoringClient and CandidatePrescoringClient:
        from src.core.services.scoring_ai_client import (
            CandidatePrescoringClient,
            CandidateScoringClient,
        )
        from src.data.clients.candidate_search_client import CandidateSearchClient

        mock_search_client = MockCandidateSearchClient()
        mock_search_client.mock_search_response = CandidateSearchResponse(
            candidates=[
                CandidateSummary(candidate_id=C1_ID, profile_text="C1 Profile"),
                CandidateSummary(candidate_id=C2_ID, profile_text="C2 Profile"),
                CandidateSummary(candidate_id=C3_ID, profile_text="C3 Profile"),
            ]
        )
        mock_search_client.mock_details[C1_ID] = make_mock_details(
            C1_ID, "Candidate One"
        )
        mock_search_client.mock_details[C2_ID] = make_mock_details(
            C2_ID, "Candidate Two"
        )
        mock_search_client.mock_details[C3_ID] = make_mock_details(
            C3_ID, "Candidate Three"
        )

        # Mock the search client and ai clients constructors or instance methods
        original_init_search = CandidateSearchClient.__init__
        original_search = CandidateSearchClient.search_candidates
        original_details = CandidateSearchClient.get_candidate_details

        CandidateSearchClient.__init__ = lambda self: None
        CandidateSearchClient.search_candidates = lambda self, req: (
            mock_search_client.search_candidates(req)
        )
        CandidateSearchClient.get_candidate_details = lambda self, ids: (
            mock_search_client.get_candidate_details(ids)
        )

        original_prescore = CandidatePrescoringClient.prescore_candidates
        CandidatePrescoringClient.prescore_candidates = AsyncMock(
            return_value=mock_prescores
        )

        original_score = CandidateScoringClient.score_candidate
        CandidateScoringClient.score_candidate = AsyncMock(
            side_effect=lambda job, cand: mock_deep_score(cand.candidate_id)
        )

        try:
            # ====================================================
            # CASE 1: Successful Background Task Run
            # ====================================================
            print("\n" + "=" * 70)
            print("CASE 1: Successful Background Task Run")
            print("=" * 70)

            task_service = ScoringTaskService(db)
            task = await task_service.create_task(
                recruiter_id=recruiter_id,
                job_description_id=jd_id,
            )
            await db.commit()

            print(
                f"Task created in DB: ID={task.id}, status={task.status}, stage={task.current_stage}"
            )
            assert task.status == "PENDING"
            assert task.current_stage == "QUEUED"

            # Execute background runner directly
            request_data = {"confirm": True, "k": 3, "minimum_prescore_threshold": 0}
            await async_run_scoring_pipeline(
                task_id=task.id,
                recruiter_id=recruiter_id,
                job_description_id=jd_id,
                request_data=request_data,
            )

            # Reload task
            await db.refresh(task)
            print(
                f"Task state after run: status={task.status}, stage={task.current_stage}"
            )
            print(
                f"Summary counts: matched={task.matched_candidate_count}, eligible={task.eligible_candidate_count}, selected={task.selected_candidate_count}"
            )

            assert task.status == "SUCCESS"
            assert task.current_stage == "COMPLETED"
            assert task.matched_candidate_count == 3
            assert task.eligible_candidate_count == 3
            assert task.selected_candidate_count == 3
            assert task.final_response_payload is not None
            assert len(task.final_response_payload["candidates"]) == 3
            print("CASE 1 PASSED!")

            # ====================================================
            # CASE 2: Failed Background Task Run (Exception Handling)
            # ====================================================
            print("\n" + "=" * 70)
            print("CASE 2: Failed Background Task Run (Exception Handling)")
            print("=" * 70)

            # Force pre-scoring client to throw an exception
            CandidatePrescoringClient.prescore_candidates.side_effect = Exception(
                "Groq AI Timeout Exception"
            )

            task2 = await task_service.create_task(
                recruiter_id=recruiter_id,
                job_description_id=jd_id,
            )
            await db.commit()

            print(f"Task 2 created: ID={task2.id}, status={task2.status}")

            await async_run_scoring_pipeline(
                task_id=task2.id,
                recruiter_id=recruiter_id,
                job_description_id=jd_id,
                request_data=request_data,
            )

            # Reload task
            await db.refresh(task2)
            print(
                f"Task 2 state after failure: status={task2.status}, stage={task2.current_stage}"
            )
            print(f"Error Message logged: {task2.error_message[:100]}...")

            assert task2.status == "FAILED"
            assert task2.current_stage == "FAILED"
            assert "Groq AI Timeout Exception" in task2.error_message
            print("CASE 2 PASSED!")

        finally:
            # Restore original classes/methods to prevent side effects
            CandidateSearchClient.__init__ = original_init_search
            CandidateSearchClient.search_candidates = original_search
            CandidateSearchClient.get_candidate_details = original_details
            CandidatePrescoringClient.prescore_candidates = original_prescore
            CandidateScoringClient.score_candidate = original_score

            await clear_database(db)

    print("\n==================================================")
    print("ALL BACKGROUND SCORING INTEGRATION TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
