from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.data.models.postgres.employment_type import EmploymentType
from src.data.models.postgres.jd_skill import JDSkill
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.job_description_status import (
    JobDescriptionStatus,
)
from src.data.models.postgres.user import User


class JobDescriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_employment_type_by_id(
        self, employment_type_id: UUID
    ) -> EmploymentType | None:

        result = await self.db.execute(
            select(EmploymentType).where(EmploymentType.id == employment_type_id)
        )

        return result.scalar_one_or_none()

    async def get_status_by_code(self, code: str) -> JobDescriptionStatus | None:

        result = await self.db.execute(
            select(JobDescriptionStatus).where(JobDescriptionStatus.code == code)
        )

        return result.scalar_one_or_none()

    async def create_job_description(
        self, job_description: JobDescription
    ) -> JobDescription:

        self.db.add(job_description)

        await self.db.flush()

        await self.db.refresh(job_description)

        return job_description

    async def save_job_description(
        self,
        job_description: JobDescription,
    ) -> JobDescription:

        await self.db.flush()
        await self.db.refresh(
            job_description,
            attribute_names=["skills"],
        )

        return job_description

    async def create_skills(self, skills: list[JDSkill]) -> None:

        self.db.add_all(skills)

        await self.db.flush()

    async def get_job_description_by_id(
        self, job_description_id: UUID
    ) -> JobDescription | None:

        result = await self.db.execute(
            select(JobDescription)
            .options(
                selectinload(JobDescription.skills),
                selectinload(JobDescription.status),
            )
            .where(JobDescription.id == job_description_id)
        )

        return result.scalar_one_or_none()

    async def delete_skills_for_job_description(
        self,
        job_description_id: UUID,
    ) -> None:

        await self.db.execute(
            delete(JDSkill).where(
                JDSkill.jd_id == job_description_id,
            )
        )

    async def get_job_descriptions_by_recruiter(
        self, recruiter_id: UUID
    ) -> list[JobDescription]:

        result = await self.db.execute(
            select(JobDescription)
            .options(
                selectinload(JobDescription.skills),
            )
            .where(JobDescription.recruiter_id == recruiter_id)
        )

        return list(result.scalars().all())

    async def get_employment_types(
        self,
    ) -> list[EmploymentType]:

        result = await self.db.execute(select(EmploymentType))

        return list(result.scalars().all())

    async def get_job_description_statuses(
        self,
    ) -> list[JobDescriptionStatus]:
        result = await self.db.execute(select(JobDescriptionStatus))

        return list(result.scalars().all())

    async def get_hiring_managers(self) -> list[User]:
        result = await self.db.execute(
            select(User).where(
                User.role == "hiring_manager",
            )
        )

        return list(result.scalars().all())
