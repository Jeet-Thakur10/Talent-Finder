from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_education import (
    CandidateEducation,
)
from src.data.models.postgres.candidate_experience import (
    CandidateExperience,
)
from src.data.models.postgres.candidate_experience_skill import (
    CandidateExperienceSkill,
)
from src.data.models.postgres.candidate_skill import (
    CandidateSkill,
)
from src.schemas.candidate_details_response import (
    CandidateDetailsResponse,
    CandidateEducationResponse,
    CandidateExperienceResponse,
    CandidateExperienceSkillResponse,
    CandidateSkillResponse,
)
from src.schemas.candidate_search_request import (
    CandidateSearchRequest,
)
from src.schemas.compressed_candidate import CompressedCandidate
from src.schemas.resume_candidate_output import (
    ResumeCandidateOutput,
)


class CandidateRepository:
    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self._db = db

    async def store_candidate(
        self,
        candidate: ResumeCandidateOutput,
        resume_text: str,
        resume_hash: str,
        source_type: str,
    ) -> Candidate:
        compressed_profile_parts: list[str] = []

        if candidate.current_title:
            compressed_profile_parts.append(
                candidate.current_title,
            )

        if candidate.skills:
            compressed_profile_parts.append(
                ", ".join(
                    skill.skill_name
                    for skill in candidate.skills
                ),
            )

        if candidate.experiences:
            compressed_profile_parts.extend(
                experience.title
                for experience in candidate.experiences
            )

        compressed_profile_text = "\n".join(
            compressed_profile_parts,
        )

        candidate_model = Candidate(
            full_name=candidate.full_name,
            email=candidate.email,
            phone=candidate.phone,
            current_title=candidate.current_title,
            location=candidate.location,
            summary=candidate.summary,
            compressed_profile_text=compressed_profile_text,
            resume_text=resume_text,
            resume_hash=resume_hash,
            source_type=source_type,
            total_experience_months=(
                candidate.total_experience_months
            ),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self._db.add(
            candidate_model,
        )

        await self._db.flush()

        for skill in candidate.skills:
            skill_model = CandidateSkill(
                candidate_id=candidate_model.id,
                skill_name=skill.skill_name,
                is_primary=True,
            )

            self._db.add(
                skill_model,
            )

        await self._db.flush()

        for experience in candidate.experiences:
            experience_model = CandidateExperience(
                candidate_id=candidate_model.id,
                company_name=experience.company_name,
                title=experience.title,
                description=experience.description,
                start_date=experience.start_date,
                end_date=experience.end_date,
                is_current=experience.is_current,
            )

            self._db.add(
                experience_model,
            )

            await self._db.flush()
            for skill in experience.skills:
                self._db.add(
                    CandidateExperienceSkill(
                        experience_id=experience_model.id,
                        skill_name=skill.skill_name,
                    )
                )

        for education in candidate.educations:
            self._db.add(
                CandidateEducation(
                    candidate_id=candidate_model.id,
                    institution_name=education.institution_name,
                    degree=education.degree,
                    field_of_study=education.field_of_study,
                    start_date=education.start_date,
                    end_date=education.end_date,
                )
            )

        await self._db.flush()

        return candidate_model


    async def get_candidate_by_resume_hash(
        self,
        resume_hash: str,
    ) -> Candidate | None:

        result = await self._db.execute(
            select(
                Candidate,
            ).where(
                Candidate.resume_hash == resume_hash,
            )
        )

        return result.scalar_one_or_none()


    async def get_compressed_candidates(
        self,
    ) -> list[CompressedCandidate]:
        result = await self._db.execute(
            select(
                Candidate.id,
                Candidate.compressed_profile_text,
            )
        )

        rows = result.all()

        return [
            CompressedCandidate(
                candidate_id=row.id,
                profile_text=row.compressed_profile_text or "",
            )
            for row in rows
        ]

    async def get_candidates_by_ids(
        self,
        candidate_ids: list[UUID],
    ) -> list[CandidateDetailsResponse]:
        result = await self._db.execute(
            select(
                Candidate,
            )
            .options(
                selectinload(
                    Candidate.skills,
                ),
                selectinload(
                    Candidate.educations,
                ),
                selectinload(
                    Candidate.experiences,
                ).selectinload(
                    CandidateExperience.skills,
                ),
            )
            .where(
                Candidate.id.in_(
                    candidate_ids,
                )
            )
        )

        candidates = result.scalars().all()

        return [
            CandidateDetailsResponse(
                id=candidate.id,
                full_name=candidate.full_name,
                email=candidate.email,
                phone=candidate.phone,
                current_title=candidate.current_title,
                location=candidate.location,
                summary=candidate.summary,
                total_experience_months=(
                    candidate.total_experience_months
                ),
                source_type=candidate.source_type,
                created_at=candidate.created_at,
                updated_at=candidate.updated_at,
                skills=[
                    CandidateSkillResponse(
                        skill_name=skill.skill_name,
                    )
                    for skill in candidate.skills
                ],
                experiences=[
                    CandidateExperienceResponse(
                        company_name=experience.company_name,
                        title=experience.title,
                        description=experience.description,
                        start_date=experience.start_date,
                        end_date=experience.end_date,
                        is_current=experience.is_current,
                        skills=[
                            CandidateExperienceSkillResponse(
                                skill_name=skill.skill_name,
                            )
                            for skill in experience.skills
                        ],
                    )
                    for experience in candidate.experiences
                ],
                educations=[
                    CandidateEducationResponse(
                        institution_name=education.institution_name,
                        degree=education.degree,
                        field_of_study=(
                            education.field_of_study
                        ),
                        start_date=education.start_date,
                        end_date=education.end_date,
                    )
                    for education in candidate.educations
                ],
            )
            for candidate in candidates
        ]

    async def search_candidates_by_skills(
        self,
        request: CandidateSearchRequest,
    ) -> list[CompressedCandidate]:

        candidate_ids: set[UUID] = set()

        #
        # skill matches
        #

        if request.skills:
            query = (
                select(Candidate.id)
                .join(
                    CandidateSkill,
                    CandidateSkill.candidate_id == Candidate.id,
                )
            )
            if request.exclude_candidate_ids:
                query = query.where(Candidate.id.notin_(request.exclude_candidate_ids))

            skill_result = await self._db.execute(
                query.where(
                    or_(
                        *[
                            func.lower(
                                CandidateSkill.skill_name,
                            ).like(
                                f"%{skill.lower()}%"
                            )
                            for skill in request.skills
                            if skill.strip()
                        ]
                    )
                )
            )

            candidate_ids.update(
                row.id
                for row in skill_result.all()
            )

        #
        # title matches
        #

        if request.title.strip():
            query = select(Candidate.id)
            if request.exclude_candidate_ids:
                query = query.where(Candidate.id.notin_(request.exclude_candidate_ids))

            title_result = await self._db.execute(
                query.where(
                    func.lower(
                        Candidate.current_title,
                    ).ilike(
                        f"%{request.title.lower()}%"
                    )
                )
            )

            candidate_ids.update(
                row.id
                for row in title_result.all()
            )

        if not candidate_ids:
            return []

        final_query = select(
            Candidate.id,
            Candidate.compressed_profile_text,
        ).where(
            Candidate.id.in_(
                candidate_ids,
            )
        )
        if request.exclude_candidate_ids:
            final_query = final_query.where(
                Candidate.id.notin_(request.exclude_candidate_ids)
                )

        result = await self._db.execute(final_query)

        rows = result.all()

        return [
            CompressedCandidate(
                candidate_id=row.id,
                profile_text=row.compressed_profile_text
                or "",
            )
            for row in rows
        ]

