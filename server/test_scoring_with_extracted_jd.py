import asyncio
from uuid import uuid4
from pprint import pprint

from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JobDescriptionExtractRequest,
    JobDescriptionCreateRequest,
    JDSkillCreateRequest,
)
from src.schemas.scoring_schema import PipelineExecutionRequest
from src.core.services.job_description_service import JobDescriptionService
from src.core.services.scoring_service import ScoringService
from src.data.clients.postgres import async_session_local


async def main():
    print("Testing scoring pipeline with an extracted Job Description...")
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
    Looking for candidates with 5 to 10 years of experience.

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
        user_id=recruiter_id,
        role=UserRole.recruiter
    )

    # 1. Extract raw text
    print("\n--- 1. Extracting raw JD text ---")
    extract_data = JobDescriptionExtractRequest(raw_job_description=sample_jd)
    async with async_session_local() as db:
        jd_service = JobDescriptionService(db)
        extract_res = await jd_service.extract_job_description(extract_data, current_user)
        print("Extraction complete.")

    # 2. Persist extracted JD (simulating user preview confirm)
    print("\n--- 2. Saving extracted Job Description to DB ---")
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
        raw_job_description=sample_jd
    )

    async with async_session_local() as db:
        jd_service = JobDescriptionService(db)
        saved_jd = await jd_service.create_job_description(create_req, current_user)
        print(f"Job Description saved with ID: {saved_jd.id}")

        # Commit transaction for scoring service visibility
        await db.commit()

    # 3. Execute Scoring Pipeline with the saved JD
    print("\n--- 3. Running Scoring Pipeline ---")
    pipeline_req = PipelineExecutionRequest(confirm=True, k=5)
    async with async_session_local() as db:
        scoring_service = ScoringService(db)
        pipeline_res = await scoring_service.pipeline_prescore_and_score(
            saved_jd.id,
            current_user,
            pipeline_req
        )
        print("\nPipeline execution complete! Candidate match results:")
        for idx, candidate in enumerate(pipeline_res.candidates):
            print(f"{idx+1}. {candidate.full_name} | Final Score: {candidate.final_score} | Confidence: {candidate.confidence}%")

        # Cleanup saved JD
        from sqlalchemy import delete
        from src.data.models.postgres.candidate_job_score import CandidateJobScore
        from src.data.models.postgres.pipeline import Pipeline
        from src.data.models.postgres.jd_skill import JDSkill
        from src.data.models.postgres.job_description import JobDescription
        await db.execute(delete(CandidateJobScore).where(CandidateJobScore.job_description_id == saved_jd.id))
        await db.execute(delete(Pipeline).where(Pipeline.jd_id == saved_jd.id))
        await db.execute(delete(JDSkill).where(JDSkill.jd_id == saved_jd.id))
        await db.execute(delete(JobDescription).where(JobDescription.id == saved_jd.id))
        await db.commit()
        print("\nCleanup completed.")


if __name__ == "__main__":
    asyncio.run(main())
