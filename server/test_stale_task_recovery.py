import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select, text

from src.core.services.scoring_task_service import ScoringTaskService
from src.data.clients.postgres import Base, async_session_local, engine
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.notification import Notification
from src.data.models.postgres.scoring_task import ScoringTask
from src.data.models.postgres.user import User


async def clear_tasks(db):
    await db.execute(delete(Notification))
    await db.execute(delete(ScoringTask))
    await db.commit()


async def run_recovery_test():
    print("Running Stale Task Recovery Integration Verification Script...\n")

    # Recreate the table scoring_tasks to ensure the new error_code column is present
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS scoring_tasks CASCADE;"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_local() as db:
        from src.utils.master_data_seeder import seed_master_data

        await seed_master_data(db)

        # Seed user/job description if not present (although master seeder/user seeder usually does it)
        # Check for recruiter
        res_u = await db.execute(select(User).where(User.role == "recruiter"))
        recruiter = res_u.scalars().first()
        if not recruiter:
            # Seed standard user/recruiter if needed
            from src.utils.user_seeder import UserSeeder

            await UserSeeder.seed(db)
            res_u = await db.execute(select(User).where(User.role == "recruiter"))
            recruiter = res_u.scalars().first()
            if not recruiter:
                print("Error: No recruiter user found in DB.")
                return

        recruiter_id = recruiter.id

        # Check for job description
        res_jd = await db.execute(select(JobDescription))
        jd = res_jd.scalars().first()
        if not jd:
            # Seed job description
            from src.data.models.postgres.employment_type import EmploymentType
            from src.data.models.postgres.job_description_status import (
                JobDescriptionStatus,
            )

            res_et = await db.execute(select(EmploymentType).limit(1))
            et = res_et.scalars().first()
            res_st = await db.execute(select(JobDescriptionStatus).limit(1))
            st = res_st.scalars().first()

            jd = JobDescription(
                recruiter_id=recruiter_id,
                title="Software Engineer",
                department="Engineering",
                job_purpose="To build apps.",
                responsibilities="Code in Python.",
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
            db.add(jd)
            await db.flush()

        jd_id = jd.id

        # Clean existing tasks/notifications
        await clear_tasks(db)

        # 2. Seed test cases:
        # Case A: Stale QUEUED task (status="PENDING", created_at = 20 mins ago)
        stale_queued = ScoringTask(
            id=uuid4(),
            recruiter_id=recruiter_id,
            job_description_id=jd_id,
            status="PENDING",
            current_stage="QUEUED",
            created_at=datetime.now(UTC) - timedelta(minutes=20),
        )
        # Case B: Stale RUNNING task (status="RUNNING", started_at = 25 mins ago, created_at = 30 mins ago)
        stale_running = ScoringTask(
            id=uuid4(),
            recruiter_id=recruiter_id,
            job_description_id=jd_id,
            status="RUNNING",
            current_stage="ACQUIRING",
            created_at=datetime.now(UTC) - timedelta(minutes=30),
            started_at=datetime.now(UTC) - timedelta(minutes=25),
        )
        # Case C: Fresh QUEUED task (status="PENDING", created_at = 2 mins ago)
        fresh_queued = ScoringTask(
            id=uuid4(),
            recruiter_id=recruiter_id,
            job_description_id=jd_id,
            status="PENDING",
            current_stage="QUEUED",
            created_at=datetime.now(UTC) - timedelta(minutes=2),
        )
        # Case D: Fresh RUNNING task (status="RUNNING", started_at = 5 mins ago, created_at = 6 mins ago)
        fresh_running = ScoringTask(
            id=uuid4(),
            recruiter_id=recruiter_id,
            job_description_id=jd_id,
            status="RUNNING",
            current_stage="DEEP_SCORING",
            created_at=datetime.now(UTC) - timedelta(minutes=6),
            started_at=datetime.now(UTC) - timedelta(minutes=5),
        )

        db.add_all([stale_queued, stale_running, fresh_queued, fresh_running])
        await db.commit()

        print("Test tasks seeded successfully.")

        # 3. Execute recovery (with 15 minutes timeout config)
        service = ScoringTaskService(db)
        await service.recover_stale_tasks(timeout_minutes=15)

        # 4. Assert database states
        await db.refresh(stale_queued)
        await db.refresh(stale_running)
        await db.refresh(fresh_queued)
        await db.refresh(fresh_running)

        # Stale tasks must be FAILED, have the error code, error message, completed_at
        print(
            f"Stale Queued Task -> Status: {stale_queued.status}, Error Code: {stale_queued.error_code}, Completed At: {stale_queued.completed_at}"
        )
        assert stale_queued.status == "FAILED"
        assert stale_queued.current_stage == "FAILED"
        assert stale_queued.error_code == "WORKER_UNAVAILABLE"
        assert stale_queued.completed_at is not None
        assert "Background worker became unavailable" in stale_queued.error_message

        print(
            f"Stale Running Task -> Status: {stale_running.status}, Error Code: {stale_running.error_code}, Completed At: {stale_running.completed_at}"
        )
        assert stale_running.status == "FAILED"
        assert stale_running.current_stage == "FAILED"
        assert stale_running.error_code == "WORKER_UNAVAILABLE"
        assert stale_running.completed_at is not None
        assert "Background worker became unavailable" in stale_running.error_message

        # Fresh tasks must remain unchanged
        print(
            f"Fresh Queued Task -> Status: {fresh_queued.status}, Stage: {fresh_queued.current_stage}"
        )
        assert fresh_queued.status == "PENDING"
        assert fresh_queued.current_stage == "QUEUED"
        assert fresh_queued.error_code is None
        assert fresh_queued.completed_at is None

        print(
            f"Fresh Running Task -> Status: {fresh_running.status}, Stage: {fresh_running.current_stage}"
        )
        assert fresh_running.status == "RUNNING"
        assert fresh_running.current_stage == "DEEP_SCORING"
        assert fresh_running.error_code is None
        assert fresh_running.completed_at is None

        # 5. Check if notifications were successfully created in DB
        notif_res = await db.execute(
            select(Notification).where(Notification.user_id == recruiter_id)
        )
        notifications = notif_res.scalars().all()
        print(f"Notifications created for Recruiter: {len(notifications)}")
        assert len(notifications) == 2
        for notif in notifications:
            assert notif.title == "Scoring Failed"
            assert "could not be completed" in notif.message

        print("\nALL STALE TASK RECOVERY TESTS PASSED SUCCESSFULLY!")

        # Cleanup
        await clear_tasks(db)


if __name__ == "__main__":
    asyncio.run(run_recovery_test())
