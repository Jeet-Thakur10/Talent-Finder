import asyncio
from datetime import date, datetime, timezone
from pprint import pprint
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.data.clients.candidate_search_client import CandidateSearchClient


CANDIDATE_ID = UUID("a0000000-0000-0000-0000-000000000001")
EXPERIENCE_ID = UUID("e0000000-0000-0000-0000-000000000001")

SOURCING_DB_URL = "postgresql+asyncpg://postgres:jeetu@localhost:5432/sourcing"


async def seed_sourcing_database():
    print(f"Seeding Sourcing database with candidate ID: {CANDIDATE_ID}")
    engine = create_async_engine(SOURCING_DB_URL)
    
    async with engine.begin() as conn:
        # Clear existing test data
        await conn.execute(
            text("DELETE FROM candidate_experience_skills WHERE experience_id = :exp_id"),
            {"exp_id": EXPERIENCE_ID}
        )
        await conn.execute(
            text("DELETE FROM candidate_experiences WHERE candidate_id = :candidate_id"),
            {"candidate_id": CANDIDATE_ID}
        )
        await conn.execute(
            text("DELETE FROM candidate_educations WHERE candidate_id = :candidate_id"),
            {"candidate_id": CANDIDATE_ID}
        )
        await conn.execute(
            text("DELETE FROM candidate_skills WHERE candidate_id = :candidate_id"),
            {"candidate_id": CANDIDATE_ID}
        )
        await conn.execute(
            text("DELETE FROM candidates WHERE id = :candidate_id"),
            {"candidate_id": CANDIDATE_ID}
        )
        
        # Insert Candidate
        await conn.execute(
            text(
                """
                INSERT INTO candidates (
                    id, full_name, email, phone, current_title, location, summary,
                    resume_text, resume_hash, source_type, total_experience_months,
                    compressed_profile_text, created_at, updated_at
                ) VALUES (
                    :id, :full_name, :email, :phone, :current_title, :location, :summary,
                    :resume_text, :resume_hash, :source_type, :total_experience_months,
                    :compressed_profile_text, :created_at, :updated_at
                )
                """
            ),
            {
                "id": CANDIDATE_ID,
                "full_name": "Jane Test Candidate",
                "email": "jane.test@example.com",
                "phone": "+1234567890",
                "current_title": "Senior Staff Python Engineer",
                "location": "San Francisco, CA",
                "summary": "An experienced software engineer specializing in Python and PostgreSQL.",
                "resume_text": "Resume of Jane Test Candidate. Senior Staff Python Engineer. Python, FastAPI, PostgreSQL, Kubernetes.",
                "resume_hash": "jane_test_hash_unique_123456",
                "source_type": "sourcing_test",
                "total_experience_months": 96,
                "compressed_profile_text": "Senior Staff Python Engineer\nPython, FastAPI, PostgreSQL, Kubernetes",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        
        # Insert Skills
        await conn.execute(
            text(
                """
                INSERT INTO candidate_skills (id, candidate_id, skill_name, is_primary)
                VALUES (:id, :candidate_id, :skill_name, :is_primary)
                """
            ),
            [
                {"id": UUID("c0000000-0000-0000-0000-000000000001"), "candidate_id": CANDIDATE_ID, "skill_name": "Python", "is_primary": True},
                {"id": UUID("c0000000-0000-0000-0000-000000000002"), "candidate_id": CANDIDATE_ID, "skill_name": "FastAPI", "is_primary": True},
            ]
        )
        
        # Insert Experience
        await conn.execute(
            text(
                """
                INSERT INTO candidate_experiences (id, candidate_id, company_name, title, description, start_date, end_date, is_current)
                VALUES (:id, :candidate_id, :company_name, :title, :description, :start_date, :end_date, :is_current)
                """
            ),
            {
                "id": EXPERIENCE_ID,
                "candidate_id": CANDIDATE_ID,
                "company_name": "Tech Corp",
                "title": "Senior Python Developer",
                "description": "Built FastAPI applications and optimized Postgres database queries.",
                "start_date": date(2020, 1, 1),
                "end_date": date(2024, 1, 1),
                "is_current": False,
            }
        )
        
        # Insert Experience Skill
        await conn.execute(
            text(
                """
                INSERT INTO candidate_experience_skills (id, experience_id, skill_name)
                VALUES (:id, :experience_id, :skill_name)
                """
            ),
            {
                "id": UUID("10000000-0000-0000-0000-000000000001"),
                "experience_id": EXPERIENCE_ID,
                "skill_name": "Python"
            }
        )
        
        # Insert Education
        await conn.execute(
            text(
                """
                INSERT INTO candidate_educations (id, candidate_id, institution_name, degree, field_of_study, start_date, end_date)
                VALUES (:id, :candidate_id, :institution_name, :degree, :field_of_study, :start_date, :end_date)
                """
            ),
            {
                "id": UUID("d0000000-0000-0000-0000-000000000001"),
                "candidate_id": CANDIDATE_ID,
                "institution_name": "Stanford University",
                "degree": "Master of Science",
                "field_of_study": "Computer Science",
                "start_date": date(2015, 9, 1),
                "end_date": date(2017, 6, 1),
            }
        )
        
    print("Database seeding completed.")
    await engine.dispose()


async def run_verification():
    await seed_sourcing_database()
    
    print("\nInitializing CandidateSearchClient...")
    async with CandidateSearchClient() as client:
        print(f"Calling get_candidate_details with ID: {CANDIDATE_ID}")
        try:
            results = await client.get_candidate_details([CANDIDATE_ID])
            print("\n==================================================")
            print("Response successfully received and validated!")
            print(f"Number of candidates details returned: {len(results)}")
            
            if not results:
                print("Error: No candidate details returned!")
                return
            
            candidate = results[0]
            print("\nCandidate Profile Details:")
            pprint(candidate.model_dump(mode="json"))
            
            # Assertions to verify correctness
            assert candidate.id == CANDIDATE_ID, f"Expected ID {CANDIDATE_ID}, got {candidate.id}"
            assert candidate.full_name == "Jane Test Candidate"
            assert candidate.email == "jane.test@example.com"
            assert candidate.phone == "+1234567890"
            assert candidate.current_title == "Senior Staff Python Engineer"
            assert candidate.location == "San Francisco, CA"
            assert candidate.summary == "An experienced software engineer specializing in Python and PostgreSQL."
            assert candidate.total_experience_months == 96
            assert candidate.source_type == "sourcing_test"
            
            skills = {sk.skill_name for sk in candidate.skills}
            assert "Python" in skills, "Python skill missing"
            assert "FastAPI" in skills, "FastAPI skill missing"
            
            assert len(candidate.experiences) == 1, "Expected 1 experience entry"
            exp = candidate.experiences[0]
            assert exp.company_name == "Tech Corp"
            assert exp.title == "Senior Python Developer"
            assert exp.description == "Built FastAPI applications and optimized Postgres database queries."
            assert exp.start_date == date(2020, 1, 1)
            assert exp.end_date == date(2024, 1, 1)
            assert exp.is_current is False
            assert len(exp.skills) == 1, "Expected 1 experience skill"
            assert exp.skills[0].skill_name == "Python"
            
            assert len(candidate.educations) == 1, "Expected 1 education entry"
            edu = candidate.educations[0]
            assert edu.institution_name == "Stanford University"
            assert edu.degree == "Master of Science"
            assert edu.field_of_study == "Computer Science"
            assert edu.start_date == date(2015, 9, 1)
            assert edu.end_date == date(2017, 6, 1)
            
            print("\nVerification PASSED successfully!")
            print("==================================================")
            
        except Exception as e:
            print(f"\nVerification FAILED: {type(e).__name__} - {str(e)}")
            if hasattr(e, "details"):
                print(f"Details: {e.details}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_verification())
