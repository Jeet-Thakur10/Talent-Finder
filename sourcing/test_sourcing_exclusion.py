import asyncio
import hashlib
from uuid import uuid4, UUID
from datetime import datetime, UTC
from sqlalchemy import delete
from src.data.clients.postgres import async_session_local
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.schemas.candidate_search_request import CandidateSearchRequest
from src.core.services.candidate_service import CandidateService
from src.core.services.candidate_search_service import CandidateSearchService


from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_experience_skill import CandidateExperienceSkill


# Helper to seed a candidate matching a specific title and skills
async def seed_candidate(db, title, skills):
    candidate_id = uuid4()
    resume_text = f"Resume for candidate {candidate_id}"
    resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
    
    candidate = Candidate(
        id=candidate_id,
        full_name=f"Candidate {candidate_id}",
        current_title=title,
        resume_text=resume_text,
        resume_hash=resume_hash,
        source_type="seed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(candidate)
    await db.flush()
    
    for skill in skills:
        skill_model = CandidateSkill(
            candidate_id=candidate_id,
            skill_name=skill,
            is_primary=True,
        )
        db.add(skill_model)
    await db.flush()
    return candidate_id


# Mock Sourcing Service to simulate scraping on the fly
class MockSourcingService:
    def __init__(self, db, title, skills, num_to_source):
        self.db = db
        self.title = title
        self.skills = skills
        self.num_to_source = num_to_source
        self.called = False

    async def source_candidates(self, request):
        self.called = True
        print(f"[Mock Sourcing] Scraping triggered! Sourcing {self.num_to_source} candidates...")
        for _ in range(self.num_to_source):
            await seed_candidate(self.db, self.title, self.skills)
        await self.db.flush()


async def clear_database(db):
    await db.execute(delete(CandidateExperienceSkill))
    await db.execute(delete(CandidateExperience))
    await db.execute(delete(CandidateEducation))
    await db.execute(delete(CandidateSkill))
    await db.execute(delete(Candidate))
    await db.commit()



async def run_tests():
    title = "Backend Engineer"
    skills = ["Python", "PostgreSQL"]

    print("Running Sourcing Exclusion Verification Script...\n")

    # ====================================================
    # Case 1: required_candidates = 50, DB returns 70, Excluded 30
    # ====================================================
    print("--- Case 1 ---")
    async with async_session_local() as db:
        await clear_database(db)

        # Seed 70 total candidates:
        # - 50 match title/skills
        # - 20 do NOT match
        matching_ids = []
        for _ in range(50):
            cid = await seed_candidate(db, title, skills)
            matching_ids.append(cid)
        for _ in range(20):
            await seed_candidate(db, "Frontend Designer", ["React"])

        # Exclude 30 matching ones
        exclude_ids = matching_ids[:30]

        # Remaining matching existing = 50 - 30 = 20
        # Target = 50, so we need 30 scraped.
        mock_sourcing = MockSourcingService(db, title, skills, 30)
        candidate_service = CandidateService(db)
        search_service = CandidateSearchService(candidate_service, mock_sourcing)

        req = CandidateSearchRequest(
            title=title,
            skills=skills,
            min_experience=0,
            required_candidates=50,
            max_source_resumes=5,
            exclude_candidate_ids=exclude_ids
        )

        response = await search_service.search_or_source_candidates(req)
        print(f"Scraping called: {mock_sourcing.called}")
        print(f"Returned candidates count: {len(response.candidates)}")
        assert mock_sourcing.called is True, "Sourcing should have been triggered"
        assert len(response.candidates) == 50, f"Expected 50 returned, got {len(response.candidates)}"
        print("Case 1 PASSED!\n")

    # ====================================================
    # Case 2: required_candidates = 50, DB returns 70, Excluded 5
    # ====================================================
    print("--- Case 2 ---")
    async with async_session_local() as db:
        await clear_database(db)

        # Seed 70 matching candidates
        matching_ids = []
        for _ in range(70):
            cid = await seed_candidate(db, title, skills)
            matching_ids.append(cid)

        # Exclude 5
        exclude_ids = matching_ids[:5]

        # Remaining matching = 70 - 5 = 65 (>= 50, no scraping)
        mock_sourcing = MockSourcingService(db, title, skills, 30)
        candidate_service = CandidateService(db)
        search_service = CandidateSearchService(candidate_service, mock_sourcing)

        req = CandidateSearchRequest(
            title=title,
            skills=skills,
            min_experience=0,
            required_candidates=50,
            max_source_resumes=5,
            exclude_candidate_ids=exclude_ids
        )

        response = await search_service.search_or_source_candidates(req)
        print(f"Scraping called: {mock_sourcing.called}")
        print(f"Returned candidates count: {len(response.candidates)}")
        assert mock_sourcing.called is False, "Sourcing should NOT have been triggered"
        assert len(response.candidates) == 50, f"Expected 50 returned, got {len(response.candidates)}"
        print("Case 2 PASSED!\n")

    # ====================================================
    # Case 3: required_candidates = 50, DB returns 20, Excluded 0
    # ====================================================
    print("--- Case 3 ---")
    async with async_session_local() as db:
        await clear_database(db)

        # Seed 20 matching candidates
        for _ in range(20):
            await seed_candidate(db, title, skills)

        # Target = 50, expect 30 scraped
        mock_sourcing = MockSourcingService(db, title, skills, 30)
        candidate_service = CandidateService(db)
        search_service = CandidateSearchService(candidate_service, mock_sourcing)

        req = CandidateSearchRequest(
            title=title,
            skills=skills,
            min_experience=0,
            required_candidates=50,
            max_source_resumes=5,
            exclude_candidate_ids=[]
        )

        response = await search_service.search_or_source_candidates(req)
        print(f"Scraping called: {mock_sourcing.called}")
        print(f"Returned candidates count: {len(response.candidates)}")
        assert mock_sourcing.called is True, "Sourcing should have been triggered"
        assert len(response.candidates) == 50, f"Expected 50 returned, got {len(response.candidates)}"
        print("Case 3 PASSED!\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
