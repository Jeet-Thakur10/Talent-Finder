from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_education import CandidateEducation
from src.data.models.postgres.candidate_experience import CandidateExperience
from src.data.models.postgres.candidate_experience_skill import (
    CandidateExperienceSkill,
)
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.candidate_skill import CandidateSkill
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.pipeline import HiringManagerDecision, Pipeline
from src.schemas.candidate_search_schema import CandidateDetailsResponse
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
        query: Select = select(JobDescription.recruiter_id).where(
            JobDescription.id == job_description_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_job_description_by_id(
        self, job_description_id: UUID
    ) -> JobDescription | None:

        result = await self.db.execute(
            select(JobDescription)
            .options(
                selectinload(JobDescription.skills),
            )
            .where(JobDescription.id == job_description_id)
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
            total_experience_months=(parsed_candidate.total_experience_months),
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

    async def get_candidates_by_ids(
        self,
        candidate_ids: list[UUID],
    ) -> list[Candidate]:
        if not candidate_ids:
            return []

        query = (
            select(Candidate)
            .options(
                selectinload(Candidate.skills),
                selectinload(Candidate.experiences).selectinload(
                    CandidateExperience.skills,
                ),
                selectinload(Candidate.educations),
            )
            .where(
                Candidate.id.in_(candidate_ids),
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_candidate_by_id(
        self,
        candidate_id: UUID,
    ) -> Candidate | None:
        result = await self.db.execute(
            select(Candidate)
            .options(
                selectinload(Candidate.skills),
                selectinload(Candidate.experiences).selectinload(
                    CandidateExperience.skills,
                ),
                selectinload(Candidate.educations),
            )
            .where(
                Candidate.id == candidate_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_candidate_scores_for_job_description(
        self,
        job_description_id: UUID,
    ) -> list[CandidateJobScore]:

        result = await self.db.execute(
            select(CandidateJobScore)
            .options(
                selectinload(CandidateJobScore.candidate).selectinload(
                    Candidate.skills,
                ),
            )
            .where(
                CandidateJobScore.job_description_id == job_description_id,
            )
            .order_by(
                desc(CandidateJobScore.final_score),
                desc(CandidateJobScore.updated_at),
            )
        )

        return list(result.scalars().all())

    async def get_candidate_job_score(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
    ) -> CandidateJobScore | None:
        result = await self.db.execute(
            select(CandidateJobScore).where(
                CandidateJobScore.job_description_id == job_description_id,
                CandidateJobScore.candidate_id == candidate_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_pipeline_entry(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
    ) -> Pipeline | None:
        result = await self.db.execute(
            select(Pipeline).where(
                Pipeline.jd_id == job_description_id,
                Pipeline.candidate_id == candidate_id,
            )
        )

        return result.scalar_one_or_none()

    async def bulk_get_pipeline_entries_for_job(
        self,
        job_description_id: UUID,
    ) -> list[Pipeline]:
        result = await self.db.execute(
            select(Pipeline).where(
                Pipeline.jd_id == job_description_id,
            )
        )

        return list(result.scalars().all())

    async def upsert_pipeline_entries(
        self,
        job_description_id: UUID,
        candidate_ids: list[UUID],
        stage: str = "PRE_SCORED",
    ) -> None:
        if not candidate_ids:
            return

        now = datetime.now(UTC)

        for candidate_id in candidate_ids:
            existing = await self.get_pipeline_entry(
                job_description_id,
                candidate_id,
            )

            if existing:
                existing.stage = stage
            else:
                self.db.add(
                    Pipeline(
                        candidate_id=candidate_id,
                        jd_id=job_description_id,
                        stage=stage,
                        created_at=now,
                    )
                )

        await self.db.flush()

    async def update_pipeline_notes(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        recruiter_notes: str | None,
    ) -> Pipeline:
        pipeline_entry = await self.get_pipeline_entry(
            job_description_id,
            candidate_id,
        )

        if pipeline_entry is None:
            pipeline_entry = Pipeline(
                candidate_id=candidate_id,
                jd_id=job_description_id,
                stage="PRE_SCORED",
                recruiter_notes=recruiter_notes,
                created_at=datetime.now(UTC),
            )
            self.db.add(pipeline_entry)
        else:
            pipeline_entry.recruiter_notes = recruiter_notes

        await self.db.flush()
        await self.db.refresh(pipeline_entry)

        return pipeline_entry

    async def bulk_update_pipeline_stage(
        self,
        job_description_id: UUID,
        candidate_ids: list[UUID],
        stage: str,
    ) -> list[Pipeline]:
        updated_entries: list[Pipeline] = []

        for candidate_id in candidate_ids:
            pipeline_entry = await self.get_pipeline_entry(
                job_description_id,
                candidate_id,
            )

            if pipeline_entry is None:
                pipeline_entry = Pipeline(
                    candidate_id=candidate_id,
                    jd_id=job_description_id,
                    stage=stage,
                    created_at=datetime.now(UTC),
                )
                self.db.add(pipeline_entry)
            else:
                pipeline_entry.stage = stage

            updated_entries.append(pipeline_entry)

        await self.db.flush()

        for pipeline_entry in updated_entries:
            await self.db.refresh(pipeline_entry)

        return updated_entries

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
                    CandidateJobScore.candidate_id == score.candidate_id,
                    CandidateJobScore.job_description_id == job_description_id,
                )
            )

            existing = result.scalar_one_or_none()

            if existing:
                existing.final_score = score.final_score
                existing.confidence = score.confidence

                existing.skills_score = score.skills_score
                existing.experience_score = score.experience_score
                existing.recency_score = score.recency_score
                existing.role_fit_score = score.role_fit_score
                existing.education_score = score.education_score

                existing.matched_mandatory_skills = score.matched_mandatory_skills

                existing.matched_optional_skills = score.matched_optional_skills

                existing.missing_mandatory_skills = score.missing_mandatory_skills

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
                        experience_score=(score.experience_score),
                        recency_score=(score.recency_score),
                        role_fit_score=(score.role_fit_score),
                        education_score=(score.education_score),
                        matched_mandatory_skills=(score.matched_mandatory_skills),
                        matched_optional_skills=(score.matched_optional_skills),
                        missing_mandatory_skills=(score.missing_mandatory_skills),
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

        await self.db.flush()

    async def upsert_candidate(
        self,
        candidate_details: CandidateDetailsResponse,
    ) -> Candidate:
        """Upsert a candidate profile and all nested child entities.

        This method is idempotent:
        - If a candidate with this ID exists, updates all mutable fields and
          synchronizes the nested skills, experiences (including experience skills),
          and educations.
        - If the candidate does not exist, creates the entire hierarchy.
        """
        existing_candidate = await self.get_candidate_by_id(candidate_details.id)

        if existing_candidate:
            # 1. Update Candidate master record mutable fields
            existing_candidate.full_name = candidate_details.full_name
            existing_candidate.email = candidate_details.email
            existing_candidate.phone = candidate_details.phone
            existing_candidate.current_title = candidate_details.current_title
            existing_candidate.location = candidate_details.location
            existing_candidate.summary = candidate_details.summary
            existing_candidate.total_experience_months = (
                candidate_details.total_experience_months
            )
            existing_candidate.source_type = candidate_details.source_type
            existing_candidate.updated_at = datetime.now(UTC)

            # 2. Synchronize Skills (match by skill_name)
            incoming_skills = {skill.skill_name for skill in candidate_details.skills}

            # Remove skills not in incoming
            existing_skills = list(existing_candidate.skills)
            for skill in existing_skills:
                if skill.skill_name not in incoming_skills:
                    existing_candidate.skills.remove(skill)

            # Add missing incoming skills
            existing_skill_names = {
                skill.skill_name for skill in existing_candidate.skills
            }
            for skill_name in incoming_skills:
                if skill_name not in existing_skill_names:
                    existing_candidate.skills.append(
                        CandidateSkill(skill_name=skill_name, is_primary=True)
                    )

            # 3. Synchronize Experiences (match by (company_name, title, start_date))
            matched_exps = {}
            for inc in candidate_details.experiences:
                key = (inc.company_name, inc.title, inc.start_date)

                # Check if this experience matches an existing one
                matched_exp = None
                for ext in existing_candidate.experiences:
                    ext_key = (ext.company_name, ext.title, ext.start_date)
                    if ext_key == key:
                        matched_exp = ext
                        break

                if matched_exp:
                    # Update mutable fields
                    matched_exp.description = inc.description
                    matched_exp.end_date = inc.end_date
                    matched_exp.is_current = inc.is_current

                    # Sync nested experience skills (match by skill_name)
                    incoming_exp_skills = {s.skill_name for s in inc.skills}
                    existing_exp_skills = list(matched_exp.skills)

                    # Remove deleted nested skills
                    for skill in existing_exp_skills:
                        if skill.skill_name not in incoming_exp_skills:
                            matched_exp.skills.remove(skill)

                    # Add new nested skills
                    existing_exp_skill_names = {
                        s.skill_name for s in matched_exp.skills
                    }
                    for skill_name in incoming_exp_skills:
                        if skill_name not in existing_exp_skill_names:
                            matched_exp.skills.append(
                                CandidateExperienceSkill(skill_name=skill_name)
                            )

                    matched_exps[matched_exp.id] = matched_exp
                else:
                    # Insert new experience
                    new_exp = CandidateExperience(
                        company_name=inc.company_name,
                        title=inc.title,
                        description=inc.description,
                        start_date=inc.start_date,
                        end_date=inc.end_date,
                        is_current=inc.is_current,
                        skills=[
                            CandidateExperienceSkill(skill_name=s.skill_name)
                            for s in inc.skills
                        ],
                    )
                    existing_candidate.experiences.append(new_exp)

            # Prune unmatched experiences
            for ext in list(existing_candidate.experiences):
                if ext.id not in matched_exps and ext.id is not None:
                    existing_candidate.experiences.remove(ext)

            # 4. Synchronize Educations (match by (
            # institution_name, degree, field_of_study
            # ))
            matched_edus = set()
            for inc in candidate_details.educations:
                key = (inc.institution_name, inc.degree, inc.field_of_study)

                matched_edu = None
                for ext in existing_candidate.educations:
                    ext_key = (ext.institution_name, ext.degree, ext.field_of_study)
                    if ext_key == key:
                        matched_edu = ext
                        break

                if matched_edu:
                    # Update mutable fields
                    matched_edu.start_date = inc.start_date
                    matched_edu.end_date = inc.end_date
                    matched_edus.add(matched_edu.id)
                else:
                    # Insert new education
                    new_edu = CandidateEducation(
                        institution_name=inc.institution_name,
                        degree=inc.degree,
                        field_of_study=inc.field_of_study,
                        start_date=inc.start_date,
                        end_date=inc.end_date,
                    )
                    existing_candidate.educations.append(new_edu)

            # Prune unmatched educations
            for ext in list(existing_candidate.educations):
                if ext.id not in matched_edus and ext.id is not None:
                    existing_candidate.educations.remove(ext)

            await self.db.flush()
            return existing_candidate

        else:
            # Create a completely new candidate using details
            # and the exact id from details
            new_candidate = Candidate(
                id=candidate_details.id,
                full_name=candidate_details.full_name,
                email=candidate_details.email,
                phone=candidate_details.phone,
                current_title=candidate_details.current_title,
                location=candidate_details.location,
                summary=candidate_details.summary,
                resume_text=None,
                resume_hash=None,
                source_type=candidate_details.source_type,
                total_experience_months=candidate_details.total_experience_months,
                created_at=candidate_details.created_at,
                updated_at=candidate_details.updated_at,
                skills=[
                    CandidateSkill(skill_name=skill.skill_name, is_primary=True)
                    for skill in candidate_details.skills
                ],
                experiences=[
                    CandidateExperience(
                        company_name=exp.company_name,
                        title=exp.title,
                        description=exp.description,
                        start_date=exp.start_date,
                        end_date=exp.end_date,
                        is_current=exp.is_current,
                        skills=[
                            CandidateExperienceSkill(skill_name=s.skill_name)
                            for s in exp.skills
                        ],
                    )
                    for exp in candidate_details.experiences
                ],
                educations=[
                    CandidateEducation(
                        institution_name=edu.institution_name,
                        degree=edu.degree,
                        field_of_study=edu.field_of_study,
                        start_date=edu.start_date,
                        end_date=edu.end_date,
                    )
                    for edu in candidate_details.educations
                ],
            )
            self.db.add(new_candidate)
            await self.db.flush()
            return new_candidate

    async def validate_candidates_belong_to_job(
        self,
        job_description_id: UUID,
        candidate_ids: list[UUID],
    ) -> list[UUID]:
        if not candidate_ids:
            return []

        stmt = select(Pipeline.candidate_id).where(
            Pipeline.jd_id == job_description_id,
            Pipeline.candidate_id.in_(candidate_ids),
        )
        res = await self.db.execute(stmt)
        found_ids = set(res.scalars().all())

        return [cid for cid in candidate_ids if cid not in found_ids]

    async def share_shortlist_with_hiring_manager(
        self,
        job_description_id: UUID,
        candidate_ids: list[UUID],
        notes_by_candidate: dict[UUID, str],
    ) -> int:
        from src.data.models.postgres.pipeline import HiringManagerDecision

        now = datetime.now(UTC)

        # 1. Reset shared_with_hiring_manager for all pipeline entries for this JD
        reset_query = (
            update(Pipeline)
            .where(Pipeline.jd_id == job_description_id)
            .values(
                shared_with_hiring_manager=False,
            )
        )
        await self.db.execute(reset_query)

        # 2. For selected candidates, mark as shared, update notes, set PENDING,
        # and clear HM notes
        shared_count = 0
        for candidate_id in candidate_ids:
            pipeline_entry = await self.get_pipeline_entry(
                job_description_id,
                candidate_id,
            )

            if pipeline_entry:
                pipeline_entry.shared_with_hiring_manager = True
                pipeline_entry.shared_at = now
                pipeline_entry.hm_decision = HiringManagerDecision.PENDING
                pipeline_entry.hiring_manager_notes = None

                # Update recruiter notes if notes were provided
                if candidate_id in notes_by_candidate:
                    pipeline_entry.recruiter_notes = notes_by_candidate[candidate_id]

                shared_count += 1

        await self.db.flush()
        return shared_count

    async def get_hm_campaigns(self, hiring_manager_id: UUID) -> list[JobDescription]:
        query = (
            select(JobDescription)
            .options(
                selectinload(JobDescription.recruiter),
                selectinload(JobDescription.pipeline_entries),
            )
            .join(Pipeline, Pipeline.jd_id == JobDescription.id)
            .where(
                JobDescription.hiring_manager_id == hiring_manager_id,
                Pipeline.shared_with_hiring_manager.is_(True),
            )
            .distinct()
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_shared_candidates_for_hm(
        self, job_description_id: UUID, hiring_manager_id: UUID
    ) -> list[tuple[Candidate, Pipeline, CandidateJobScore]]:
        # Verify the job description is assigned to the hiring manager
        jd = await self.get_job_description_by_id(job_description_id)
        if not jd or jd.hiring_manager_id != hiring_manager_id:
            return []

        query = (
            select(Candidate, Pipeline, CandidateJobScore)
            .join(Pipeline, Pipeline.candidate_id == Candidate.id)
            .join(
                CandidateJobScore,
                (CandidateJobScore.candidate_id == Candidate.id)
                & (CandidateJobScore.job_description_id == job_description_id),
            )
            .where(
                Pipeline.jd_id == job_description_id,
                Pipeline.shared_with_hiring_manager.is_(True),
            )
            .order_by(desc(CandidateJobScore.final_score))
        )
        result = await self.db.execute(query)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def submit_hm_review(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        hiring_manager_id: UUID,
        decision: HiringManagerDecision,
        remarks: str | None,
    ) -> Pipeline | None:
        # Verify ownership
        jd = await self.get_job_description_by_id(job_description_id)
        if not jd or jd.hiring_manager_id != hiring_manager_id:
            return None

        pipeline_entry = await self.get_pipeline_entry(
            job_description_id,
            candidate_id,
        )
        if not pipeline_entry or not pipeline_entry.shared_with_hiring_manager:
            return None

        pipeline_entry.hm_decision = decision
        pipeline_entry.hiring_manager_notes = remarks

        await self.db.flush()
        return pipeline_entry

    async def get_status_by_code(self, code: str) -> UUID | None:
        from src.data.models.postgres.job_description_status import JobDescriptionStatus

        result = await self.db.execute(
            select(JobDescriptionStatus.id).where(JobDescriptionStatus.code == code)
        )
        return result.scalar_one_or_none()

    async def update_job_description_status(
        self,
        job_description_id: UUID,
        status_id: UUID,
    ) -> None:
        stmt = (
            update(JobDescription)
            .where(JobDescription.id == job_description_id)
            .values(status_id=status_id, updated_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.flush()
