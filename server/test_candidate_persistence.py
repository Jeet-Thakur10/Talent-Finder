import asyncio
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import select, func
from src.data.clients.postgres import async_session_local
from src.core.services.scoring_service import ScoringService
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse,
    CandidateSkillResponse,
    CandidateExperienceResponse,
    CandidateExperienceSkillResponse,
    CandidateEducationResponse,
)
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import CandidateExperienceSkill
from src.data.models.postgres.candidate_education import CandidateEducation


async def query_db_counts(db, candidate_id):
    # Candidate exists
    res = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    cand = res.scalar_one_or_none()
    
    # Count skills
    res = await db.execute(
        select(func.count(CandidateSkill.id)).where(CandidateSkill.candidate_id == candidate_id)
    )
    skills_count = res.scalar()
    
    # Count experiences
    res = await db.execute(
        select(func.count(CandidateExperience.id)).where(CandidateExperience.candidate_id == candidate_id)
    )
    exp_count = res.scalar()
    
    # Count nested skills
    res = await db.execute(
        select(func.count(CandidateExperienceSkill.id))
        .join(CandidateExperience)
        .where(CandidateExperience.candidate_id == candidate_id)
    )
    exp_skills_count = res.scalar()
    
    # Count educations
    res = await db.execute(
        select(func.count(CandidateEducation.id)).where(CandidateEducation.candidate_id == candidate_id)
    )
    edu_count = res.scalar()
    
    return cand, skills_count, exp_count, exp_skills_count, edu_count


async def run_verification():
    candidate_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # 1. Construct initial CandidateDetailsResponse
    initial_details = CandidateDetailsResponse(
        id=candidate_id,
        full_name="Verification Candidate",
        email="verify@example.com",
        phone="+999999999",
        current_title="Junior Engineer",
        location="New York, NY",
        summary="A motivated junior software engineer.",
        total_experience_months=12,
        source_type="SOURCED",
        created_at=now,
        updated_at=now,
        skills=[
            CandidateSkillResponse(skill_name="Python"),
            CandidateSkillResponse(skill_name="SQL"),
        ],
        experiences=[
            CandidateExperienceResponse(
                company_name="StartCorp",
                title="Backend Developer",
                description="Built REST APIs.",
                start_date=date(2022, 1, 1),
                end_date=date(2023, 1, 1),
                is_current=False,
                skills=[
                    CandidateExperienceSkillResponse(skill_name="Python")
                ]
            )
        ],
        educations=[
            CandidateEducationResponse(
                institution_name="State Univ",
                degree="BS CS",
                field_of_study="Computer Science",
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 1)
            )
        ]
    )

    print("Initializing ScoringService...")
    async with async_session_local() as db:
        service = ScoringService(db)
        
        # ====================================================
        # Step 1: Persist brand-new candidate
        # ====================================================
        print("\n--- Step 1: Persisting brand-new candidate ---")
        await service.upsert_candidate_profile(initial_details)
        await db.commit()
        
        # Verify database state
        cand, skills, exps, exp_skills, edus = await query_db_counts(db, candidate_id)
        assert cand is not None, "Candidate was not persisted!"
        assert cand.full_name == "Verification Candidate"
        assert cand.email == "verify@example.com"
        assert cand.resume_text is None, "Expected resume_text to be null"
        assert cand.resume_hash is None, "Expected resume_hash to be null"
        assert skills == 2, f"Expected 2 skills, got {skills}"
        assert exps == 1, f"Expected 1 experience, got {exps}"
        assert exp_skills == 1, f"Expected 1 experience skill, got {exp_skills}"
        assert edus == 1, f"Expected 1 education, got {edus}"
        print("Step 1 PASSED: Brand-new candidate persisted successfully.")

        # ====================================================
        # Step 2: Persist the same candidate again (Idempotence)
        # ====================================================
        print("\n--- Step 2: Persisting same candidate again ---")
        await service.upsert_candidate_profile(initial_details)
        await db.commit()
        
        # Verify database state remains unchanged
        cand, skills, exps, exp_skills, edus = await query_db_counts(db, candidate_id)
        assert cand is not None
        assert skills == 2, f"Expected 2 skills, got {skills}"
        assert exps == 1, f"Expected 1 experience, got {exps}"
        assert exp_skills == 1, f"Expected 1 experience skill, got {exp_skills}"
        assert edus == 1, f"Expected 1 education, got {edus}"
        print("Step 2 PASSED: Idempotency verified. No duplicates created.")

        # ====================================================
        # Step 3: Modify fields, add/remove child entities
        # ====================================================
        print("\n--- Step 3: Updating candidate details and syncing collections ---")
        modified_details = CandidateDetailsResponse(
            id=candidate_id,
            full_name="Verification Candidate",
            email="verify_updated@example.com",  # updated
            phone="+999999999",
            current_title="Senior Engineer",     # updated
            location="New York, NY",
            summary="An experienced senior software engineer.",  # updated
            total_experience_months=36,          # updated
            source_type="SOURCED",
            created_at=now,
            updated_at=now,
            skills=[
                CandidateSkillResponse(skill_name="Python"),
                CandidateSkillResponse(skill_name="SQL"),
                CandidateSkillResponse(skill_name="Docker"),  # added
            ],
            experiences=[
                # StartCorp removed, NextCorp added
                CandidateExperienceResponse(
                    company_name="NextCorp",
                    title="Senior Backend Dev",
                    description="Lead development of backend services.",
                    start_date=date(2023, 1, 1),
                    end_date=None,
                    is_current=True,
                    skills=[
                        CandidateExperienceSkillResponse(skill_name="Python"),
                        CandidateExperienceSkillResponse(skill_name="Docker"),
                    ]
                )
            ],
            educations=[
                # State Univ removed, Ivy League added
                CandidateEducationResponse(
                    institution_name="Ivy League",
                    degree="MS CS",
                    field_of_study="Computer Science",
                    start_date=date(2022, 9, 1),
                    end_date=date(2024, 6, 1)
                )
            ]
        )
        
        await service.upsert_candidate_profile(modified_details)
        await db.commit()
        
        # Verify database state after modifications
        cand, skills, exps, exp_skills, edus = await query_db_counts(db, candidate_id)
        assert cand.email == "verify_updated@example.com", f"Expected updated email, got {cand.email}"
        assert cand.current_title == "Senior Engineer", f"Expected updated title, got {cand.current_title}"
        assert cand.total_experience_months == 36
        assert skills == 3, f"Expected 3 skills, got {skills}"
        assert exps == 1, f"Expected 1 experience, got {exps}"
        assert exp_skills == 2, f"Expected 2 experience skills, got {exp_skills}"
        assert edus == 1, f"Expected 1 education, got {edus}"
        
        # Fetch the experience to check details
        res = await db.execute(select(CandidateExperience).where(CandidateExperience.candidate_id == candidate_id))
        exp_row = res.scalar()
        assert exp_row.company_name == "NextCorp", f"Expected NextCorp experience, got {exp_row.company_name}"
        assert exp_row.is_current is True
        
        # Fetch the education to check details
        res = await db.execute(select(CandidateEducation).where(CandidateEducation.candidate_id == candidate_id))
        edu_row = res.scalar()
        assert edu_row.institution_name == "Ivy League"
        
        print("Step 3 PASSED: Candidate modifications, additions, and deletions synchronized cleanly.")

        # ====================================================
        # Clean up database
        # ====================================================
        print("\n--- Cleaning up verification candidate from database ---")
        # Due to delete-orphan cascade, deleting the candidate deletes all nested entities
        await db.delete(cand)
        await db.commit()
        
        cand, skills, exps, exp_skills, edus = await query_db_counts(db, candidate_id)
        assert cand is None, "Candidate was not deleted!"
        assert skills == 0, "Candidate skills remained!"
        assert exps == 0, "Candidate experiences remained!"
        assert exp_skills == 0, "Candidate experience skills remained!"
        assert edus == 0, "Candidate educations remained!"
        print("Cleanup successful.")
        
    print("\n==================================================")
    print("ALL CANDIDATE PERSISTENCE VERIFICATIONS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_verification())
