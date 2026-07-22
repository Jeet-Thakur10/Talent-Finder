from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.job_description_constants import (
    ACTIVE,
    CLOSED,
    CONTRACT,
    DRAFT,
    FULL_TIME,
    INTERNSHIP,
    PART_TIME,
)
from src.data.models.postgres.employment_type import EmploymentType
from src.data.models.postgres.job_description_status import JobDescriptionStatus


async def seed_employment_types(
    db: AsyncSession,
) -> None:

    employment_types = [
        {
            "code": FULL_TIME,
            "name": "Full Time",
        },
        {
            "code": PART_TIME,
            "name": "Part Time",
        },
        {
            "code": CONTRACT,
            "name": "Contract",
        },
        {
            "code": INTERNSHIP,
            "name": "Internship",
        },
    ]

    for employment_type in employment_types:
        existing = await db.execute(
            select(EmploymentType).where(EmploymentType.code == employment_type["code"])
        )

        if existing.scalar_one_or_none():
            continue

        db.add(
            EmploymentType(
                code=employment_type["code"],
                name=employment_type["name"],
            )
        )

    await db.commit()


async def seed_job_description_statuses(
    db: AsyncSession,
) -> None:

    statuses = [
        {
            "code": DRAFT,
            "name": "Draft",
        },
        {
            "code": ACTIVE,
            "name": "Active",
        },
        {
            "code": CLOSED,
            "name": "Closed",
        },
    ]

    for status in statuses:
        existing = await db.execute(
            select(JobDescriptionStatus).where(
                JobDescriptionStatus.code == status["code"]
            )
        )

        if existing.scalar_one_or_none():
            continue

        db.add(
            JobDescriptionStatus(
                code=status["code"],
                name=status["name"],
            )
        )

    await db.commit()


async def seed_master_data(db: AsyncSession) -> None:
    # Update table schemas if needed
    await db.execute(
        text("""
        ALTER TABLE job_descriptions
        ADD COLUMN IF NOT EXISTS hiring_manager_id UUID REFERENCES users(id)
    """)
    )
    await db.commit()

    await seed_employment_types(db)
    await seed_job_description_statuses(db)
