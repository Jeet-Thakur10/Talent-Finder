from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import (
    CandidateExperienceSkill,
)
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.job_description import JobDescription
from src.schemas.scoring_schema import (
    CandidateScoreOutput,
    ParsedCandidateProfile,
)


class ScoringRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recruiter_id_by_job_description_id(
        self, job_description_id: UUID
    ) -> UUID | None:
        query: Select = (
            select(JobDescription.recruiter_id)
            .where(JobDescription.id == job_description_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_job_description_by_id(
        self, job_description_id: UUID) -> JobDescription | None:

        result = await self.db.execute(
            select(JobDescription)
            .options(
                selectinload(JobDescription.skills),
            )
            .where(
                JobDescription.id == job_description_id
            )
        )

        return result.scalar_one_or_none()
    
    async def store_parsed_candidate_profile(
        self,
        parsed_candidate: ParsedCandidateProfile,
        resume_text: str,
        resume_hash: str,
    ) -> Candidate:
        now = datetime.now(UTC)

        candidate = Candidate(
            full_name=parsed_candidate.full_name,
            email=parsed_candidate.email,
            phone=parsed_candidate.phone,
            current_title=parsed_candidate.current_title,
            location=parsed_candidate.location,
            summary=parsed_candidate.summary,
            resume_text=resume_text,
            resume_hash=resume_hash,
            total_experience_months=(
                parsed_candidate.total_experience_months
            ),
            created_at=now,
            updated_at=now,
            skills=[
                CandidateSkill(
                    skill_name=skill.skill_name,
                )
                for skill in parsed_candidate.skills
            ],
            experiences=[
                CandidateExperience(
                    company_name=experience.company_name,
                    title=experience.title,
                    description=experience.description,
                    start_date=experience.start_date,
                    end_date=experience.end_date,
                    is_current=experience.is_current,
                    skills=[
                        CandidateExperienceSkill(
                            skill_name=skill.skill_name,
                        )
                        for skill in experience.skills
                    ],
                )
                for experience in parsed_candidate.experiences
            ],
            educations=[
                CandidateEducation(
                    institution_name=education.institution_name,
                    degree=education.degree,
                    field_of_study=education.field_of_study,
                    start_date=education.start_date,
                    end_date=education.end_date,
                )
                for education in parsed_candidate.educations
            ],
        )

        self.db.add(candidate)

        await self.db.flush()
        await self.db.refresh(candidate)

        return candidate
    
    async def get_candidates_for_job_description(
        self,
        candidate_ids: list[UUID] | None = None,
    ) -> list[Candidate]:
        if candidate_ids is not None and not candidate_ids:
            return []

        query = select(Candidate).options(
            selectinload(Candidate.skills),
            selectinload(Candidate.experiences).selectinload(
                CandidateExperience.skills,
            ),
            selectinload(Candidate.educations),
        )

        if candidate_ids is not None:
            query = query.where(
                Candidate.id.in_(candidate_ids),
            )

        result = await self.db.execute(
            query,
        )

        return list(result.scalars().unique().all())
    
    async def upsert_candidate_scores(
        self,
        job_description_id: UUID,
        scores: list[CandidateScoreOutput],
    ) -> None:
        now = datetime.now(
            UTC,
        )

        for score in scores:

            result = await self.db.execute(
                select(
                    CandidateJobScore,
                ).where(
                    CandidateJobScore.candidate_id
                    == score.candidate_id,
                    CandidateJobScore.job_description_id
                    == job_description_id,
                )
            )

            existing = result.scalar_one_or_none()

            if existing:

                existing.final_score = score.final_score
                existing.confidence = score.confidence

                existing.skills_score = score.skills_score
                existing.experience_score = (
                    score.experience_score
                )
                existing.recency_score = (
                    score.recency_score
                )
                existing.role_fit_score = (
                    score.role_fit_score
                )
                existing.education_score = (
                    score.education_score
                )

                existing.matched_mandatory_skills = (
                    score.matched_mandatory_skills
                )

                existing.matched_optional_skills = (
                    score.matched_optional_skills
                )

                existing.missing_mandatory_skills = (
                    score.missing_mandatory_skills
                )

                existing.explanation = (
                    score.explanation.model_dump()
                    if hasattr(
                        score.explanation,
                        "model_dump",
                    )
                    else score.explanation
                )

                existing.updated_at = now

            else:

                self.db.add(
                    CandidateJobScore(
                        candidate_id=score.candidate_id,
                        job_description_id=job_description_id,

                        final_score=score.final_score,
                        confidence=score.confidence,

                        skills_score=score.skills_score,
                        experience_score=(
                            score.experience_score
                        ),
                        recency_score=(
                            score.recency_score
                        ),
                        role_fit_score=(
                            score.role_fit_score
                        ),
                        education_score=(
                            score.education_score
                        ),

                        matched_mandatory_skills=(
                            score.matched_mandatory_skills
                        ),

                        matched_optional_skills=(
                            score.matched_optional_skills
                        ),

                        missing_mandatory_skills=(
                            score.missing_mandatory_skills
                        ),

                        explanation=(
                            score.explanation.model_dump()
                            if hasattr(
                                score.explanation,
                                "model_dump",
                            )
                            else score.explanation
                        ),

                        created_at=now,
                        updated_at=now,
                    )
                )