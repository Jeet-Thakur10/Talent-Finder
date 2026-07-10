import asyncio
from datetime import UTC, datetime
from pprint import pprint
from uuid import uuid4

from src.core.services.job_description_service import JobDescriptionService
from src.core.services.scoring_service import ScoringService
from src.data.clients.postgres import async_session_local
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JDSkillCreateRequest,
    JobDescriptionCreateRequest,
    JobDescriptionExtractRequest,
)
from src.schemas.scoring_schema import PipelineExecutionRequest


async def main():
    print("Testing Pre-Score Threshold Filtering Pipeline...")
    sample_jd = """
    Job Title: Senior Software Engineer
    Department: Engineering
    Location: San Francisco, CA (Hybrid)
    Employment Type: Full-time
    Hiring Manager: Sarah Connor
    
    Job Purpose:
    We are looking for a Senior Software Engineer to build and scale our core data processing pipelines. You will lead design and implementation of highly available systems.

    Responsibilities:
    - Design and develop robust backend APIs using Python and FastAPI
    - Optimize database queries and schemas in PostgreSQL
    - Mentor junior developers and conduct code reviews
    
    Education Requirements:
    Bachelor's degree in Computer Science or equivalent experience.

    Preferred Qualifications:
    - Master's degree in Computer Science
    - Experience with Kubernetes and Docker in production
    
    Experience:
    Looking for candidates with 1 to 3 years of experience.

    Skills:
    - Python (Mandatory)
    - PostgreSQL (Mandatory)
    - FastAPI (Mandatory)
    - Kubernetes (Optional)
    """

    # Resolve recruiter ID
    async with async_session_local() as db:
        from sqlalchemy import select

        from src.data.models.postgres.user import User

        result = await db.execute(select(User).where(User.role == "recruiter"))
        recruiter = result.scalars().first()
        if not recruiter:
            print("Error: No recruiter found.")
            return
        recruiter_id = recruiter.id

    current_user = AuthenticatedUserContext(
        user_id=recruiter_id, role=UserRole.recruiter
    )

    # Seed candidates to postgres database
    print("\n--- Seeding Candidate Data ---")
    now = datetime.now(UTC)
    c1_id = uuid4()
    c2_id = uuid4()
    c3_id = uuid4()

    c1 = Candidate(
        id=c1_id,
        full_name="Arjun Vance",
        email="arjun@example.com",
        current_title="Senior Software Engineer",
        location="San Francisco, CA (Hybrid)",
        resume_text="Arjun Vance: Experienced Python, PostgreSQL, FastAPI, Kubernetes backend developer",
        resume_hash="hash_arjun_vance_123",
        source_type="IMPORT",
        total_experience_months=43,
        created_at=now,
        updated_at=now,
        skills=[
            CandidateSkill(skill_name="Python", is_primary=True),
            CandidateSkill(skill_name="PostgreSQL", is_primary=True),
            CandidateSkill(skill_name="FastAPI", is_primary=True),
            CandidateSkill(skill_name="Kubernetes", is_primary=False),
        ],
    )
    c2 = Candidate(
        id=c2_id,
        full_name="Niharika Singh",
        email="niharika@example.com",
        current_title="Software Developer",
        location="San Francisco, CA",
        resume_text="Niharika Singh: Software engineer skilled in Python, PostgresSql, and database design",
        resume_hash="hash_niharika_singh_456",
        source_type="IMPORT",
        total_experience_months=38,
        created_at=now,
        updated_at=now,
        skills=[
            CandidateSkill(skill_name="Python", is_primary=True),
            CandidateSkill(skill_name="PostgresSql", is_primary=True),
        ],
    )
    c3 = Candidate(
        id=c3_id,
        full_name="Sarah Jenkins",
        email="sarah@example.com",
        current_title="Intern",
        location="Boston, MA",
        resume_text="Sarah Jenkins: Student looking for Java internship",
        resume_hash="hash_sarah_jenkins_789",
        source_type="IMPORT",
        total_experience_months=12,
        created_at=now,
        updated_at=now,
        skills=[CandidateSkill(skill_name="Java", is_primary=True)],
    )

    async with async_session_local() as db:
        db.add_all([c1, c2, c3])
        await db.commit()
    print("Candidates seeded successfully.")

    # Extract raw text using service
    print("\n--- 2. Extracting raw JD text ---")
    extract_data = JobDescriptionExtractRequest(raw_job_description=sample_jd)
    async with async_session_local() as db:
        jd_service = JobDescriptionService(db)
        extract_res = await jd_service.extract_job_description(
            extract_data, current_user
        )
        print(
            f"Extraction complete. Title: {extract_res.title}, Min Experience: {extract_res.min_experience}"
        )

    # Persist extracted JD (simulating user preview confirm)
    print("\n--- 3. Saving extracted Job Description to DB ---")
    skills_req = [
        JDSkillCreateRequest(skill_name=s.skill_name, is_mandatory=s.is_mandatory)
        for s in extract_res.skills
    ]
    create_req = JobDescriptionCreateRequest(
        title=extract_res.title,
        department=extract_res.department,
        job_purpose=extract_res.job_purpose,
        responsibilities=extract_res.responsibilities,
        min_experience=extract_res.min_experience,
        max_experience=extract_res.max_experience,
        location=extract_res.location,
        employment_type_id=extract_res.employment_type_id,
        education_requirement=extract_res.education_requirement,
        preferred_qualifications=extract_res.preferred_qualifications,
        skills=skills_req,
        hiring_manager_id=extract_res.hiring_manager_id,
        raw_job_description=sample_jd,
    )

    async with async_session_local() as db:
        jd_service = JobDescriptionService(db)
        saved_jd = await jd_service.create_job_description(create_req, current_user)
        print(f"Job Description saved with ID: {saved_jd.id}")
        await db.commit()

    try:
        # 4. Test Preview Stage (confirm=False)
        print("\n--- 4. Testing Preview Stage (confirm=False) ---")
        preview_req = PipelineExecutionRequest(
            confirm=False, k=5, minimum_prescore_threshold=60
        )
        async with async_session_local() as db:
            scoring_service = ScoringService(db)
            preview_res = await scoring_service.pipeline_prescore_and_score(
                saved_jd.id, current_user, preview_req
            )
            print("Preview Response:")
            pprint(preview_res.model_dump())
            assert preview_res.stage == "preview"
            assert preview_res.eligible_candidate_count is None
            assert preview_res.selected_candidate_count is None
            assert len(preview_res.candidates) == 0
            print("Preview Stage test passed successfully!")

        # 5. Test Case C: Threshold = 0 (Everyone eligible)
        # We run this first to dynamically read the pre-scores of each candidate.
        print("\n--- 5. Testing Case C (Threshold = 0, k = 5) ---")
        case_c_req = PipelineExecutionRequest(
            confirm=True, k=5, minimum_prescore_threshold=0
        )
        async with async_session_local() as db:
            scoring_service = ScoringService(db)
            res_c = await scoring_service.pipeline_prescore_and_score(
                saved_jd.id, current_user, case_c_req
            )
            print("Case C Response:")
            pprint(res_c.model_dump())
            assert res_c.stage == "completed"
            assert res_c.eligible_candidate_count == 2
            assert res_c.selected_candidate_count == 2
            assert len(res_c.candidates) == 2

            # Map full_name to prescore_score to choose a threshold dynamically
            prescores = {c.full_name: c.prescore_score for c in res_c.candidates}
            print(f"Dynamically retrieved Candidate Pre-scores: {prescores}")

            arjun_score = prescores.get("Arjun Vance")
            niharika_score = prescores.get("Niharika Singh")

            print(f"Arjun score: {arjun_score}, Niharika score: {niharika_score}")
            await db.commit()

        # 6. Test Case A: Threshold filters to subset (minimum_prescore_threshold = Arjun's score, k = 5)
        # Set threshold to Arjun's score (which is expected to be >= 75 and higher than the others).
        # We'll set the threshold to arjun_score. Only Arjun should meet it.
        threshold_a = arjun_score
        print(f"\n--- 6. Testing Case A (Threshold = {threshold_a}, k = 5) ---")
        case_a_req = PipelineExecutionRequest(
            confirm=True, k=5, minimum_prescore_threshold=threshold_a
        )
        async with async_session_local() as db:
            scoring_service = ScoringService(db)
            res_a = await scoring_service.pipeline_prescore_and_score(
                saved_jd.id, current_user, case_a_req
            )
            print("Case A Response:")
            pprint(res_a.model_dump())
            assert res_a.stage == "completed"

            # Verify only Arjun Vance (and other candidates who meet this threshold, if any) is selected.
            # Since Arjun has the highest score, if we set the threshold to his score, eligible count must be >= 1.
            # Let's count how many candidates meet this threshold in res_c:
            expected_eligible_count = sum(
                1 for name, score in prescores.items() if score >= threshold_a
            )
            assert res_a.eligible_candidate_count == expected_eligible_count
            assert res_a.selected_candidate_count == expected_eligible_count
            assert len(res_a.candidates) == expected_eligible_count

            candidate_names = [c.full_name for c in res_a.candidates]
            assert "Arjun Vance" in candidate_names
            print("Case A test passed successfully!")
            await db.commit()

        # 7. Test Case B: High threshold (minimum_prescore_threshold = 100)
        # Nobody should meet the threshold (since Arjun is 94 < 100). Deep scoring should be skipped entirely.
        print("\n--- 7. Testing Case B (Threshold = 100, k = 5) ---")
        case_b_req = PipelineExecutionRequest(
            confirm=True, k=5, minimum_prescore_threshold=100
        )
        async with async_session_local() as db:
            scoring_service = ScoringService(db)
            res_b = await scoring_service.pipeline_prescore_and_score(
                saved_jd.id, current_user, case_b_req
            )
            print("Case B Response:")
            pprint(res_b.model_dump())
            assert res_b.stage == "completed"
            assert res_b.eligible_candidate_count == 0
            assert res_b.selected_candidate_count == 0
            assert len(res_b.candidates) == 0
            print("Case B test passed successfully!")
            await db.commit()

    finally:
        # Cleanup candidates, Job Description and scores
        print("\n--- Cleanup ---")
        async with async_session_local() as db:
            from sqlalchemy import delete

            from src.data.models.postgres.candidate_job_score import CandidateJobScore
            from src.data.models.postgres.jd_skill import JDSkill
            from src.data.models.postgres.job_description import JobDescription
            from src.data.models.postgres.pipeline import Pipeline

            # Clean candidate scores & pipeline
            await db.execute(
                delete(CandidateJobScore).where(
                    CandidateJobScore.job_description_id == saved_jd.id
                )
            )
            await db.execute(delete(Pipeline).where(Pipeline.jd_id == saved_jd.id))
            await db.execute(delete(JDSkill).where(JDSkill.jd_id == saved_jd.id))
            await db.execute(
                delete(JobDescription).where(JobDescription.id == saved_jd.id)
            )

            # Clean candidate skills and candidate records
            await db.execute(
                delete(CandidateSkill).where(
                    CandidateSkill.candidate_id.in_([c1_id, c2_id, c3_id])
                )
            )
            await db.execute(
                delete(Candidate).where(Candidate.id.in_([c1_id, c2_id, c3_id]))
            )

            await db.commit()
            print("Cleanup completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
