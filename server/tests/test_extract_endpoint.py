import asyncio
from pprint import pprint

from src.core.services.job_description_service import JobDescriptionService
from src.data.clients.postgres import async_session_local
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JDSkillCreateRequest,
    JobDescriptionCreateRequest,
    JobDescriptionExtractRequest,
)


async def main():
    print("Testing Job Description Extraction and Persistence...")
    sample_jd = """
    Job Title: Senior Software Engineer
    Department: Core Infrastructure
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

    # User context (Recruiter role is required)
    # We use a static UUID for recruiter that exists in db seeds or first recruiter user
    # Let's query recruiters from database first to use a valid one
    async with async_session_local() as db:
        from sqlalchemy import select

        from src.data.models.postgres.user import User
        result = await db.execute(select(User).where(User.role == "recruiter"))
        recruiter = result.scalars().first()
        if not recruiter:
            print("Error: No recruiter found in database. Make sure seeds are run.")
            return
        recruiter_id = recruiter.id

    current_user = AuthenticatedUserContext(
        user_id=recruiter_id,
        role=UserRole.recruiter
    )

    # 1. Test extraction
    print("\n--- 1. Testing extraction ---")
    data = JobDescriptionExtractRequest(raw_job_description=sample_jd)
    async with async_session_local() as db:
        service = JobDescriptionService(db)
        extract_res = await service.extract_job_description(data, current_user)
        print("Extracted fields response successfully generated.")

    # 2. Test creation (persistence)
    print("\n--- 2. Testing persistence (saving JD with raw_job_description) ---")
    # Resolve the employment type ID and skill requests from the extracted result
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
        raw_job_description=sample_jd  # Original raw JD exactly as received
    )

    async with async_session_local() as db:
        service = JobDescriptionService(db)
        saved_jd = await service.create_job_description(create_req, current_user)
        print("\nSave Success! Saved Job Description details:")
        pprint(saved_jd.model_dump(mode="json"))

        # 3. Retrieve and verify raw_job_description is stored exactly as received
        print("\n--- 3. Verifying stored raw_job_description ---")
        retrieved_jd = await service.get_job_description(saved_jd.id, current_user)
        print(f"Retrieved raw_job_description matches original: {retrieved_jd.raw_job_description == sample_jd}")
        print("Stored raw_job_description snippet:")
        print(retrieved_jd.raw_job_description[:100] + "...")


if __name__ == "__main__":
    asyncio.run(main())
