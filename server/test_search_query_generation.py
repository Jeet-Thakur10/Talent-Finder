import asyncio
from pprint import pprint
from uuid import uuid4
from datetime import datetime, UTC

from src.schemas.job_description_schema import JobDescriptionResponse, JDSkillResponse
from src.control.agents.candidate_search_query_agent import CandidateSearchQueryAgent


async def main():
    print("Initializing Candidate Search Query Agent...")
    agent = CandidateSearchQueryAgent()
    
    # 1. Define sample Job Description Response matching the schema
    sample_jd = JobDescriptionResponse(
        id=uuid4(),
        title="Senior Backend Engineer",
        department="Engineering",
        job_purpose="Build high scale backend systems",
        responsibilities="Design APIs, write database migrations",
        min_experience=5,
        max_experience=10,
        location="Remote",
        education_requirement="B.S. in Computer Science",
        preferred_qualifications="M.S. in Computer Science",
        employment_type_id=uuid4(),
        status_id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        skills=[
            JDSkillResponse(id=uuid4(), skill_name="Advanced Python", is_mandatory=True),
            JDSkillResponse(id=uuid4(), skill_name="Basic Java", is_mandatory=False),
            JDSkillResponse(id=uuid4(), skill_name="Hands-on PostgreSQL", is_mandatory=True),
            JDSkillResponse(id=uuid4(), skill_name="Expert Kubernetes", is_mandatory=False),
            JDSkillResponse(id=uuid4(), skill_name="REST API Development", is_mandatory=True),
            JDSkillResponse(id=uuid4(), skill_name="Microservices Architecture", is_mandatory=True),
            JDSkillResponse(id=uuid4(), skill_name="Object-Oriented Programming", is_mandatory=False),
        ]
    )

    print("\n==================================================")
    print("Input Job Description:")
    print(f"Title: {sample_jd.title}")
    print(f"Min Experience: {sample_jd.min_experience}")
    print("Skills:")
    for s in sample_jd.skills:
        print(f"  - {s.skill_name} (Mandatory: {s.is_mandatory})")
    print("==================================================")

    print("\nGenerating CandidateSearchRequest...")
    search_request = agent.generate_search_query(
        job_description=sample_jd,
        min_candidates=10,
        max_source_resumes=50
    )

    print("\n==================================================")
    print("Generated CandidateSearchRequest:")
    pprint(search_request.model_dump())
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
