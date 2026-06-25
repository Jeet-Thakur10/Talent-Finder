from __future__ import annotations

from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.job_description_schema import JobDescriptionResponse, JDSkillResponse
from src.core.exceptions.job_description_exception import (
    RecruiterAccessRequired,
)
from src.core.exceptions.scoring_exceptions import (
    ResumeImportValidationError,
)
from src.core.services.resume_parser import ResumeParser
from src.core.services.scoring_ai_client import CandidateScoringClient, CandidatePrescoringClient
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.job_description import JobDescription
from src.data.repositories.scoring_repository import ScoringRepository
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.scoring_schema import (
    CandidateBatchScoreOutput,
    CandidateEducationInput,
    CandidateExperienceInput,
    CandidateImportRequest,
    CandidatePrescoreBatchOutput,
    CandidateScoringInput,
    CandidateSkillInput,
    CompressedCandidate,
    CompressedJobDescription,
    JobDescriptionScoringInput,
    JobSkillInput,

    ParsedCandidateProfile,
)


class ScoringService:
    def __init__(self, db: AsyncSession):
        self.repository = ScoringRepository(db)
        self.resume_parser = ResumeParser()
        self.scoring_client = CandidateScoringClient()
        self.prescoring_client = CandidatePrescoringClient()

    async def import_candidate_resume(
        self,
        data: CandidateImportRequest,
        current_user: AuthenticatedUserContext,
    ) -> ParsedCandidateProfile:
        job_description = await self._get_authorized_job_description(
            data.job_description_id,
            current_user,
        )

        if not data.resume_text.strip():
            raise ResumeImportValidationError(
                details="Resume text cannot be empty",
                error_code="RESUME_TEXT_REQUIRED",
            )

        parsed_candidate = self.resume_parser.parse_resume(
            data.resume_text,
        )

        await self.repository.store_parsed_candidate_profile(
            parsed_candidate,
            data.resume_text,
            "temp_hash5",
        )

        return parsed_candidate


    async def score_candidates_for_job_description(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
        candidate_ids: list[UUID] | None = None,
    ) -> CandidateBatchScoreOutput:
        job_description = await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        candidates = await self.repository.get_candidates_for_job_description(
            candidate_ids=candidate_ids,
        )

        scoring_job = self._build_job_description_scoring_input(
            job_description,
        )

        scoring_tasks = [
            self.scoring_client.score_candidate(
                scoring_job,
                self._build_candidate_scoring_input(
                    candidate,
                ),
            )
            for candidate in candidates
        ]

        results = await asyncio.gather(
            *scoring_tasks,
        )

        candidate_scores = [
            result.payload
            for result in results
            if result.payload is not None
        ]

        await self.repository.upsert_candidate_scores(
            job_description_id=job_description_id,
            scores=candidate_scores,
        )

        return CandidateBatchScoreOutput(
            scores=candidate_scores,
        )

    async def pipeline_prescore_and_score(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
        k: int,
    ) -> CandidateBatchScoreOutput:
        prescore_output = await self.prescore_candidates_for_job_description(
            job_description_id,
        )

        top_candidate_ids = [
            score.candidate_id
            for score in prescore_output.scores[:k]
        ]

        return await self.score_candidates_for_job_description(
            job_description_id,
            current_user,
            candidate_ids=top_candidate_ids,
        )

    async def prescore_candidates_for_job_description(
        self,
        job_description_id: UUID,
    ) -> CandidatePrescoreBatchOutput:

        job_description = (
            await self.repository.get_job_description_by_id(
                job_description_id,
            )
        )

        candidates = (
            await self.repository.get_candidates_for_job_description()
        )

        compressed_jd = (
            self._build_compressed_job_description(
                job_description,
            )
        )

        compressed_candidates = [
            self._build_compressed_candidate(
                candidate,
            )
            for candidate in candidates
        ]

        score_results = (
            await self.prescoring_client.prescore_candidates(
                compressed_candidates,
                compressed_jd,
            )
        )

        score_results.scores.sort(
            key=lambda score: score.score,
            reverse=True,
        )

        return score_results
# prescoring functions

    def _build_compressed_job_description(
        self,
        job_description: JobDescription,
    ) -> CompressedJobDescription:

        mandatory_skills = [
            skill.skill_name
            for skill in job_description.skills
            if skill.is_mandatory
        ]

        optional_skills = [
            skill.skill_name
            for skill in job_description.skills
            if not skill.is_mandatory
        ]

        profile_text = (
            f"Title: {job_description.title}\n"
            f"Experience: {job_description.min_experience}-"
            f"{job_description.max_experience} years\n"
            f"Required Skills: {', '.join(mandatory_skills)}\n"
            f"Optional Skills: {', '.join(optional_skills)}"
        )

        return CompressedJobDescription(
            job_description_id=job_description.id,
            profile_text=profile_text,
        )

    def _build_compressed_candidate(
        self,
        candidate: Candidate,
    ) -> CompressedCandidate:

        global_skills = ", ".join(
            skill.skill_name
            for skill in candidate.skills
        )

        experience_titles = [
            experience.title
            for experience in candidate.experiences
        ]

        profile_text = (
            f"Title: {candidate.current_title or ''}\n"
            f"Experience: "
            f"{round(candidate.total_experience_months / 12, 1)} years\n"
            f"Skills: {global_skills}\n"
            f"Career: {', '.join(experience_titles)}"
        )

        return CompressedCandidate(
            candidate_id=candidate.id,
            profile_text=profile_text,
        )

# prescoring functions end

# scoring functions
    def _build_job_description_scoring_input(
        self,
        job_description: JobDescriptionResponse,
    ) -> JobDescriptionScoringInput:
        return JobDescriptionScoringInput(
            job_description_id=job_description.id,
            title=job_description.title,
            department=job_description.department,
            job_purpose=job_description.job_purpose,
            responsibilities=job_description.responsibilities,
            min_experience=job_description.min_experience,
            max_experience=job_description.max_experience,
            location=job_description.location,
            education_requirement=(
                job_description.education_requirement
            ),
            preferred_qualifications=(
                job_description.preferred_qualifications
            ),
            skills=[
                JobSkillInput(
                    skill_name=skill.skill_name,
                    is_mandatory=skill.is_mandatory,
                )
                for skill in job_description.skills
            ],
        )

    def _build_candidate_scoring_input(
        self,
        candidate: Candidate,
    ) -> CandidateScoringInput:
        return CandidateScoringInput(
            candidate_id=candidate.id,
            full_name=candidate.full_name,
            current_title=candidate.current_title,
            location=candidate.location,
            summary=candidate.summary,
            total_experience_months=(
                candidate.total_experience_months
            ),
            skills=[
                CandidateSkillInput(
                    skill_name=skill.skill_name,
                )
                for skill in candidate.skills
            ],
            experiences=[
                CandidateExperienceInput(
                    company_name=experience.company_name,
                    title=experience.title,
                    description=experience.description,
                    start_date=experience.start_date,
                    end_date=experience.end_date,
                    is_current=experience.is_current,
                    skills=[
                        CandidateSkillInput(
                            skill_name=skill.skill_name,
                        )
                        for skill in experience.skills
                    ],
                )
                for experience in candidate.experiences
            ],
            educations=[
                CandidateEducationInput(
                    institution_name=education.institution_name,
                    degree=education.degree,
                    field_of_study=education.field_of_study,
                    start_date=education.start_date,
                    end_date=education.end_date,
                )
                for education in candidate.educations
            ],
        )

    async def _get_authorized_job_description(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> JobDescriptionResponse:
        recruiter_id = (
            await self.repository.get_recruiter_id_by_job_description_id(
                job_description_id,
            )
        )

        if recruiter_id != current_user.user_id:
            raise RecruiterAccessRequired(
                details="You do not have access to this job description",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        jd = (
            await self.repository.get_job_description_by_id(
                job_description_id,
            )
        )

        return JobDescriptionResponse(
            id=jd.id,
            title=jd.title,
            department=jd.department,
            job_purpose=jd.job_purpose,
            responsibilities=jd.responsibilities,
            min_experience=jd.min_experience,
            max_experience=jd.max_experience,
            location=jd.location,
            education_requirement=jd.education_requirement,
            preferred_qualifications=jd.preferred_qualifications,
            employment_type_id=jd.employment_type_id,
            status_id=jd.status_id,
            created_at=jd.created_at,
            updated_at=jd.updated_at,
            skills=[
                JDSkillResponse(
                    id=skill.id,
                    skill_name=skill.skill_name,
                    is_mandatory=skill.is_mandatory,
                )
                for skill in jd.skills
            ],
        )
    
# scoring functions end