import asyncio
from unittest import TestCase
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.services.job_description_service import JobDescriptionService
from src.core.services.scoring_service import ScoringService
from src.data.clients.postgres import Base
from src.data.models.postgres.employment_type import EmploymentType
from src.data.models.postgres.user import User
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JDSkillCreateRequest,
    JobDescriptionCreateRequest,
)
from src.schemas.scoring_schema import CandidateImportRequest
from src.utils.master_data_seeder import seed_master_data
from src.utils.user_seeder import UserSeeder

TEST_DATABASE_NAME = "usecase_scoring_test"
SAMPLE_RESUME = """
Priya Raman
Senior Backend Engineer
priya.raman@example.com
+91 98765 43210
Bangalore, India

SUMMARY
Backend engineer with 6 years of experience building APIs and cloud services.

SKILLS
Python, FastAPI, AWS, PostgreSQL, Docker

EXPERIENCE
Senior Backend Engineer | Acme Labs | Jan 2022 - Present
Built FastAPI services on AWS and PostgreSQL.

Software Engineer | Beta Tech | Jun 2019 - Dec 2021
Developed Python APIs and containerized deployments with Docker.

EDUCATION
B.Tech in Computer Science, Anna University, 2019
"""


def _replace_database_name(database_url: str, database_name: str) -> str:
    parsed = urlsplit(database_url)
    path = f"/{database_name}"

    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.query,
            parsed.fragment,
        )
    )


class ScoringServiceIntegrationTests(TestCase):
    database_url: str

    @classmethod
    def setUpClass(cls) -> None:
        from src.config.settings import settings

        cls.database_url = _replace_database_name(
            settings.DATABASE_URL,
            TEST_DATABASE_NAME,
        )
        admin_database_url = _replace_database_name(
            settings.DATABASE_URL,
            "postgres",
        )
        asyncio.run(
            cls._recreate_database(
                admin_database_url=admin_database_url,
                database_name=TEST_DATABASE_NAME,
            )
        )
        asyncio.run(cls._create_schema_and_seed())

    @classmethod
    async def _recreate_database(
        cls,
        admin_database_url: str,
        database_name: str,
    ) -> None:
        admin_engine = create_async_engine(
            admin_database_url,
            isolation_level="AUTOCOMMIT",
        )
        async with admin_engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {"database_name": database_name},
            )
            await conn.execute(text(f"DROP DATABASE IF EXISTS {database_name}"))
            await conn.execute(text(f"CREATE DATABASE {database_name}"))
        await admin_engine.dispose()

    @classmethod
    async def _create_schema_and_seed(cls) -> None:
        engine = create_async_engine(
            cls.database_url,
            isolation_level="AUTOCOMMIT",
        )
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            await UserSeeder.seed(session)
            await seed_master_data(session)

        await engine.dispose()

    def test_import_resume_persists_candidate_and_score(self) -> None:
        asyncio.run(self._exercise_import_flow())

    async def _exercise_import_flow(self) -> None:
        engine = create_async_engine(
            self.database_url,
            isolation_level="AUTOCOMMIT",
        )
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            recruiter = await self._get_recruiter(session)
            current_user = AuthenticatedUserContext(
                user_id=recruiter.id,
                role=UserRole.recruiter,
            )
            job_service = JobDescriptionService(session)
            scoring_service = ScoringService(session)
            employment_type = await self._get_employment_type(session)
            job_description = await job_service.create_job_description(
                JobDescriptionCreateRequest(
                    title="Senior Backend Engineer",
                    department="Platform",
                    job_purpose="Build backend services for talent workflows.",
                    responsibilities=(
                        "Design FastAPI services, maintain PostgreSQL "
                        "schemas, and operate cloud workloads on AWS."
                    ),
                    min_experience=3,
                    max_experience=6,
                    location="Bangalore",
                    employment_type_id=employment_type.id,
                    education_requirement="Bachelor in Computer Science",
                    preferred_qualifications="Experience with Docker",
                    skills=[
                        JDSkillCreateRequest(
                            skill_name="Python",
                            is_mandatory=True,
                        ),
                        JDSkillCreateRequest(
                            skill_name="FastAPI",
                            is_mandatory=True,
                        ),
                        JDSkillCreateRequest(
                            skill_name="AWS",
                            is_mandatory=False,
                        ),
                    ],
                ),
                current_user,
            )
            await session.commit()

            result = await scoring_service.import_candidate_resume(
                CandidateImportRequest(
                    job_description_id=job_description.id,
                    resume_text=SAMPLE_RESUME,
                ),
                current_user,
            )
            await session.commit()

            self.assertEqual(result.candidate.full_name, "Priya Raman")
            self.assertEqual(
                result.candidate.email,
                "priya.raman@example.com",
            )
            self.assertGreaterEqual(result.score.final_score, 90.0)
            self.assertEqual(
                result.score.matched_mandatory_skills,
                ["fastapi", "python"],
            )
            self.assertEqual(result.score.matched_optional_skills, ["aws"])

            candidates = await scoring_service.list_candidates_for_job(
                job_description.id,
                current_user,
            )
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].full_name, "Priya Raman")

            score = await scoring_service.get_candidate_score(
                job_description.id,
                result.candidate.id,
                current_user,
            )
            self.assertEqual(score.candidate_id, result.candidate.id)
            self.assertGreaterEqual(score.breakdown.skills, 40.0)

        await engine.dispose()

    async def _get_recruiter(
        self,
        session: AsyncSession,
    ) -> User:
        result = await session.execute(
            select(User).where(User.role == UserRole.recruiter.value)
        )
        recruiter = result.scalar_one_or_none()

        if recruiter is None:
            raise AssertionError("Recruiter seed user is missing")

        return recruiter

    async def _get_employment_type(
        self,
        session: AsyncSession,
    ) -> EmploymentType:
        result = await session.execute(select(EmploymentType))
        employment_type = result.scalars().first()

        if employment_type is None:
            raise AssertionError("Employment type seed data is missing")

        return employment_type
