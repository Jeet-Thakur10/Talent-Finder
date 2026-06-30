import asyncio
from uuid import uuid4
from pprint import pprint
from datetime import datetime, UTC

from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JobDescriptionExtractRequest,
    JobDescriptionCreateRequest,
    JobDescriptionUpdateRequest,
    JDSkillCreateRequest,
)
from src.schemas.scoring_schema import PipelineExecutionRequest
from src.core.services.job_description_service import JobDescriptionService
from src.core.services.scoring_service import ScoringService
from src.data.clients.postgres import async_session_local


async def main():
    print("Testing update flow and candidate scoring with an extracted Job Description...")
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
        await db.commit()

    # 3. Execute Candidate Scoring Pipeline initially
    print("\n--- 3. Running Initial Scoring Pipeline ---")
    pipeline_req = PipelineExecutionRequest(confirm=True, k=5)
    async with async_session_local() as db:
        scoring_service = ScoringService(db)
        pipeline_res = await scoring_service.pipeline_prescore_and_score(
            saved_jd.id,
            current_user,
            pipeline_req
        )
        print("\nInitial Pipeline execution complete! Candidate match results:")
        for idx, candidate in enumerate(pipeline_res.candidates):
            print(f"{idx+1}. {candidate.full_name} | Final Score: {candidate.final_score} | Confidence: {candidate.confidence}%")
        await db.commit()

    # 4. Update structured fields of JD
    print("\n--- 4. Updating Job Description (Editing structured fields, leaving raw_job_description alone) ---")
    
    # We update:
    # - min_experience to 7
    # - title to "Principal Backend Engineer"
    # In the request, we pass a dummy raw_job_description to prove that it is ignored.
    update_req = JobDescriptionUpdateRequest(
        title="Principal Backend Engineer",
        department=extract_res.department,
        job_purpose=extract_res.job_purpose,
        responsibilities=extract_res.responsibilities,
        min_experience=7,
        max_experience=12,
        location=extract_res.location,
        employment_type_id=extract_res.employment_type_id,
        education_requirement=extract_res.education_requirement,
        preferred_qualifications=extract_res.preferred_qualifications,
        skills=skills_req,
        hiring_manager_id=extract_res.hiring_manager_id,
        raw_job_description="THIS DUMMY TEXT SHOULD BE COMPLETELY IGNORED BY THE UPDATE SERVICE AND ENDPOINT"
    )

    async with async_session_local() as db:
        jd_service = JobDescriptionService(db)
        updated_jd_res = await jd_service.update_job_description(saved_jd.id, update_req, current_user)
        print(f"Updated JD Title: {updated_jd_res.title}")
        print(f"Updated JD Min Experience: {updated_jd_res.min_experience}")
        await db.commit()

    # 5. Retrieve JD from DB to verify that raw_job_description did NOT change
    print("\n--- 5. Retrieving JD from database and verifying immutability of raw_job_description ---")
    async with async_session_local() as db:
        jd_service = JobDescriptionService(db)
        db_jd = await jd_service.get_job_description(saved_jd.id, current_user)
        
        print(f"Stored raw_job_description changed: {db_jd.raw_job_description == 'THIS DUMMY TEXT SHOULD BE COMPLETELY IGNORED BY THE UPDATE SERVICE AND ENDPOINT'}")
        print(f"Stored raw_job_description matches original: {db_jd.raw_job_description == sample_jd}")
        
        assert db_jd.title == "Principal Backend Engineer", "Title was not updated!"
        assert db_jd.min_experience == 7, "Min experience was not updated!"
        assert db_jd.raw_job_description == sample_jd, "Raw job description was incorrectly updated!"
        print("Success! Structured fields updated successfully, while original raw_job_description was preserved exactly!")

    # 6. Execute Candidate Scoring Pipeline on updated Job Description
    print("\n--- 6. Re-running Scoring Pipeline on updated Job Description ---")
    async with async_session_local() as db:
        scoring_service = ScoringService(db)
        pipeline_res_updated = await scoring_service.pipeline_prescore_and_score(
            saved_jd.id,
            current_user,
            pipeline_req
        )
        print("\nUpdated Pipeline execution complete! Candidate match results:")
        for idx, candidate in enumerate(pipeline_res_updated.candidates):
            print(f"{idx+1}. {candidate.full_name} | Final Score: {candidate.final_score} | Confidence: {candidate.confidence}%")
        await db.commit()

    # 7. Cleanup
    print("\n--- 7. Cleaning up test data from DB ---")
    async with async_session_local() as db:
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
        print("Cleanup completed.")


if __name__ == "__main__":
    asyncio.run(main())
