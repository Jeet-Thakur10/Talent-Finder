import asyncio
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import func, select

from src.core.services.scoring_service import ScoringService
from src.data.clients.postgres import async_session_local
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import CandidateExperienceSkill
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.pipeline import Pipeline
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse,
    CandidateEducationResponse,
    CandidateExperienceResponse,
    CandidateExperienceSkillResponse,
    CandidateSkillResponse,
)


async def query_db_counts(db, candidate_id):
    # Candidate exists
    res = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    cand = res.scalar_one_or_none()

    # Count skills
    res = await db.execute(
        select(func.count(CandidateSkill.id)).where(
            CandidateSkill.candidate_id == candidate_id
        )
    )
    skills_count = res.scalar()

    # Count experiences
    res = await db.execute(
        select(func.count(CandidateExperience.id)).where(
            CandidateExperience.candidate_id == candidate_id
        )
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
        select(func.count(CandidateEducation.id)).where(
            CandidateEducation.candidate_id == candidate_id
        )
    )
    edu_count = res.scalar()

    return cand, skills_count, exp_count, exp_skills_count, edu_count


async def run_verification():
    candidate_id = uuid4()
    now = datetime.now(UTC)

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
                skills=[CandidateExperienceSkillResponse(skill_name="Python")],
            )
        ],
        educations=[
            CandidateEducationResponse(
                institution_name="State Univ",
                degree="BS CS",
                field_of_study="Computer Science",
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 1),
            )
        ],
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
            current_title="Senior Engineer",  # updated
            location="New York, NY",
            summary="An experienced senior software engineer.",  # updated
            total_experience_months=36,  # updated
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
                    ],
                )
            ],
            educations=[
                # State Univ removed, Ivy League added
                CandidateEducationResponse(
                    institution_name="Ivy League",
                    degree="MS CS",
                    field_of_study="Computer Science",
                    start_date=date(2022, 9, 1),
                    end_date=date(2024, 6, 1),
                )
            ],
        )

        await service.upsert_candidate_profile(modified_details)
        await db.commit()

        # Verify database state after modifications
        cand, skills, exps, exp_skills, edus = await query_db_counts(db, candidate_id)
        assert cand.email == "verify_updated@example.com", (
            f"Expected updated email, got {cand.email}"
        )
        assert cand.current_title == "Senior Engineer", (
            f"Expected updated title, got {cand.current_title}"
        )
        assert cand.total_experience_months == 36
        assert skills == 3, f"Expected 3 skills, got {skills}"
        assert exps == 1, f"Expected 1 experience, got {exps}"
        assert exp_skills == 2, f"Expected 2 experience skills, got {exp_skills}"
        assert edus == 1, f"Expected 1 education, got {edus}"

        # Fetch the experience to check details
        res = await db.execute(
            select(CandidateExperience).where(
                CandidateExperience.candidate_id == candidate_id
            )
        )
        exp_row = res.scalar()
        assert exp_row.company_name == "NextCorp", (
            f"Expected NextCorp experience, got {exp_row.company_name}"
        )
        assert exp_row.is_current is True

        # Fetch the education to check details
        res = await db.execute(
            select(CandidateEducation).where(
                CandidateEducation.candidate_id == candidate_id
            )
        )
        edu_row = res.scalar()
        assert edu_row.institution_name == "Ivy League"

        print(
            "Step 3 PASSED: Candidate modifications, additions, and deletions synchronized cleanly."
        )

        # ====================================================
        # Step 4: Verify stale candidate cleanup
        # ====================================================
        print("\n--- Step 4: Testing stale candidate score and pipeline cleanup ---")
        from sqlalchemy import delete
        
        # Fetch an existing job description
        res_jd = await db.execute(select(JobDescription).limit(1))
        existing_jd = res_jd.scalar_one_or_none()
        if existing_jd:
            test_jd_id = existing_jd.id
            
            # Create a second candidate for stale test
            stale_candidate_id = uuid4()
            stale_candidate = Candidate(
                id=stale_candidate_id,
                full_name="Stale Candidate",
                email="stale@example.com",
                phone="+111",
                current_title="Junior Engineer",
                location="Remote",
                summary="Summary",
                total_experience_months=12,
                source_type="SOURCED",
                created_at=now,
                updated_at=now,
            )
            db.add(stale_candidate)
            await db.flush()

            # Insert scores and pipeline records for both candidates
            score_active = CandidateJobScore(
                candidate_id=candidate_id,
                job_description_id=test_jd_id,
                final_score=90.0,
                confidence=85.0,
                skills_score=10.0,
                experience_score=10.0,
                recency_score=10.0,
                role_fit_score=10.0,
                education_score=10.0,
                matched_mandatory_skills=[],
                matched_optional_skills=[],
                missing_mandatory_skills=[],
                explanation={},
                created_at=now,
                updated_at=now,
            )
            score_stale = CandidateJobScore(
                candidate_id=stale_candidate_id,
                job_description_id=test_jd_id,
                final_score=80.0,
                confidence=80.0,
                skills_score=8.0,
                experience_score=8.0,
                recency_score=8.0,
                role_fit_score=8.0,
                education_score=8.0,
                matched_mandatory_skills=[],
                matched_optional_skills=[],
                missing_mandatory_skills=[],
                explanation={},
                created_at=now,
                updated_at=now,
            )
            db.add(score_active)
            db.add(score_stale)
            
            pipe_active = Pipeline(
                candidate_id=candidate_id,
                jd_id=test_jd_id,
                stage="SHORTLISTED",
                created_at=now,
            )
            pipe_stale = Pipeline(
                candidate_id=stale_candidate_id,
                jd_id=test_jd_id,
                stage="SHORTLISTED",
                created_at=now,
            )
            db.add(pipe_active)
            db.add(pipe_stale)
            await db.flush()

            # Verify both scores exist
            res_s = await db.execute(select(CandidateJobScore).where(CandidateJobScore.job_description_id == test_jd_id))
            assert len(res_s.scalars().all()) >= 2
            
            # Execute cleanup (active is candidate_id, stale is stale_candidate_id)
            await service.repository.delete_stale_candidate_scores_and_pipelines(
                job_description_id=test_jd_id,
                active_candidate_ids=[candidate_id],
            )
            await db.flush()

            # Verify stale records are deleted
            res_s_after = await db.execute(
                select(CandidateJobScore).where(
                    CandidateJobScore.job_description_id == test_jd_id,
                    CandidateJobScore.candidate_id == stale_candidate_id,
                )
            )
            assert res_s_after.scalar_one_or_none() is None, "Stale CandidateJobScore record was not deleted!"

            res_p_after = await db.execute(
                select(Pipeline).where(
                    Pipeline.jd_id == test_jd_id,
                    Pipeline.candidate_id == stale_candidate_id,
                )
            )
            assert res_p_after.scalar_one_or_none() is None, "Stale Pipeline record was not deleted!"

            # Verify active records remain
            res_s_act = await db.execute(
                select(CandidateJobScore).where(
                    CandidateJobScore.job_description_id == test_jd_id,
                    CandidateJobScore.candidate_id == candidate_id,
                )
            )
            assert res_s_act.scalar_one_or_none() is not None, "Active CandidateJobScore record was deleted!"

            # Clean up active score & pipeline, and delete stale candidate master
            await db.execute(delete(CandidateJobScore).where(CandidateJobScore.job_description_id == test_jd_id))
            await db.execute(delete(Pipeline).where(Pipeline.jd_id == test_jd_id))
            await db.delete(stale_candidate)
            await db.flush()
            print("Step 4 PASSED: Database cleanup of stale candidates verified successfully.")
        else:
            print("Skipped Step 4: No existing job description found to verify cleanup.")

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
