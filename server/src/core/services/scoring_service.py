from __future__ import annotations

import asyncio
import hashlib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.job_description_exception import (
    RecruiterAccessRequired,
)
from src.core.exceptions.scoring_exceptions import (
    CandidateNotFound,
    ResumeImportValidationError,
)
from src.core.services.resume_parser import ResumeParser
from src.core.services.scoring_ai_client import (
    CandidatePrescoringClient,
    CandidateScoringClient,
)
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.job_description import JobDescription
from src.data.repositories.scoring_repository import ScoringRepository
from src.schemas.auth_schema import AuthenticatedUserContext
from src.schemas.job_description_schema import (
    JDSkillResponse,
    JobDescriptionResponse,
)
from src.schemas.scoring_schema import (
    CandidateBatchScoreOutput,
    CandidateEvaluationBoardResponse,
    CandidateScoreBreakdownResponse,
    CandidateDetailsResponse,
    CandidateEducationResponse,
    CandidateEducationInput,
    CandidateExperienceResponse,
    CandidateExperienceSkillResponse,
    CandidateExperienceInput,
    CandidateImportRequest,
    CandidatePrescoreBatchOutput,
    CandidateScoringInput,
    CandidateSkillResponse,
    CandidateSkillInput,
    CompressedCandidate,
    CompressedJobDescription,
    JobDescriptionScoringInput,
    JobSkillInput,
    ParsedCandidateProfile,
    PipelineNotesUpdateRequest,
    PipelineCandidateResult,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineSnapshotResponse,
    PipelineStageUpdateRequest,
    CandidateScoreResponse,
    CandidateScoreDetailBreakdown,
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
        await self._get_authorized_job_description(
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

        resume_hash = hashlib.sha256(data.resume_text.encode("utf-8")).hexdigest()

        await self.repository.store_parsed_candidate_profile(
            parsed_candidate,
            data.resume_text,
            resume_hash,
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

        if not candidates:
            return CandidateBatchScoreOutput(
                scores=[],
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
        await self.repository.upsert_pipeline_entries(
            job_description_id,
            [
                score.candidate_id
                for score in candidate_scores
            ],
        )

        return CandidateBatchScoreOutput(
            scores=candidate_scores,
        )

    async def pipeline_prescore_and_score(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
        data: PipelineExecutionRequest,
    ) -> PipelineExecutionResponse:
        job_description = await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        sourced_candidates = await self._source_candidates_for_job_description(
            job_description_id,
        )

        matched_candidate_count = len(
            sourced_candidates,
        )

        if not data.confirm:
            return PipelineExecutionResponse(
                stage="preview",
                matched_candidate_count=matched_candidate_count,
                eligible_candidate_count=None,
                selected_candidate_count=None,
                top_k=data.k,
            )

        if not sourced_candidates:
            return PipelineExecutionResponse(
                stage="completed",
                matched_candidate_count=0,
                eligible_candidate_count=0,
                selected_candidate_count=0,
                top_k=data.k,
                candidates=[],
            )

        prescore_output = await self._prescore_candidates(
            job_description_id,
            sourced_candidates,
        )
        print("\n" + "="*40 + "\nPrescore Output (Sorted)\n" + "="*40)
        for idx, score in enumerate(prescore_output.scores):
            # Resolve name from sourced_candidates
            c_name = next((c.full_name for c in sourced_candidates if c.id == score.candidate_id), "Unknown")
            print(f"{idx+1}. {c_name} (ID: {score.candidate_id}) -> Score: {score.score}")
        print("="*40 + "\n")

        # Filter candidates whose pre-score >= minimum_prescore_threshold
        # Note: _prescore_candidates() returns results already sorted in descending order.
        eligible_scores = [
            score
            for score in prescore_output.scores
            if score.score >= data.minimum_prescore_threshold
        ]
        eligible_candidate_count = len(eligible_scores)

        # Select up to top K from the filtered list
        top_scores = eligible_scores[: data.k]
        selected_candidate_count = len(top_scores)

        if selected_candidate_count == 0:
            return PipelineExecutionResponse(
                stage="completed",
                matched_candidate_count=matched_candidate_count,
                eligible_candidate_count=eligible_candidate_count,
                selected_candidate_count=selected_candidate_count,
                top_k=data.k,
                candidates=[],
            )

        top_candidate_ids = [
            score.candidate_id
            for score in top_scores
        ]

        deep_score_output = await self.score_candidates_for_job_description(
            job_description_id,
            current_user,
            candidate_ids=top_candidate_ids,
        )
        print("\n" + "="*40 + "\nDeep Score Output\n" + "="*40)
        for idx, score in enumerate(deep_score_output.scores):
            c_name = next((c.full_name for c in sourced_candidates if c.id == score.candidate_id), "Unknown")
            print(f"{idx+1}. Name: {c_name} (ID: {score.candidate_id})")
            print(f"   Final Score: {score.final_score} | Confidence: {score.confidence}%")
            print(f"   Breakdown -> Skills: {score.skills_score} | Exp: {score.experience_score} | Recency: {score.recency_score} | Role Fit: {score.role_fit_score} | Edu: {score.education_score}")
            print(f"   Matched Mandatory Skills: {score.matched_mandatory_skills}")
            print(f"   Missing Mandatory Skills: {score.missing_mandatory_skills}")
            explanation_summary = score.explanation.get("summary") if isinstance(score.explanation, dict) else getattr(score.explanation, "summary", "")
            print(f"   Explanation Summary: {explanation_summary}")
            print("-" * 20)
        print("="*40 + "\n")

        candidate_lookup = {
            candidate.id: candidate
            for candidate in sourced_candidates
        }

        prescore_lookup = {
            score.candidate_id: (
                index + 1,
                score.score,
            )
            for index, score in enumerate(
                prescore_output.scores,
            )
        }

        deep_score_lookup = {
            score.candidate_id: score
            for score in deep_score_output.scores
        }

        candidates = [
            self._build_pipeline_candidate_result(
                candidate=candidate_lookup[candidate_id],
                prescore_rank=prescore_lookup[candidate_id][0],
                prescore_score=prescore_lookup[candidate_id][1],
                score=deep_score_lookup.get(
                    candidate_id,
                ),
            )
            for candidate_id in top_candidate_ids
            if candidate_id in candidate_lookup
        ]

        candidates.sort(
            key=lambda candidate: (
                candidate.final_score or 0,
                -(candidate.prescore_rank or 0),
            ),
            reverse=True,
        )

        return PipelineExecutionResponse(
            stage="completed",
            matched_candidate_count=matched_candidate_count,
            eligible_candidate_count=eligible_candidate_count,
            selected_candidate_count=selected_candidate_count,
            top_k=data.k,
            candidates=candidates,
        )

    async def list_ranked_candidates_for_job_description(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> list[PipelineCandidateResult]:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        stored_scores = await self.repository.get_candidate_scores_for_job_description(
            job_description_id,
        )
        pipeline_entries = await self.repository.bulk_get_pipeline_entries_for_job(
            job_description_id,
        )
        pipeline_lookup = {
            pipeline_entry.candidate_id: pipeline_entry
            for pipeline_entry in pipeline_entries
        }

        return [
            self._build_pipeline_candidate_result(
                candidate=stored_score.candidate,
                score=stored_score,
                pipeline_entry=pipeline_lookup.get(
                    stored_score.candidate_id,
                ),
            )
            for stored_score in stored_scores
        ]

    async def get_candidate_details(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> CandidateDetailsResponse:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        candidate = await self.repository.get_candidate_by_id(
            candidate_id,
        )

        if not candidate:
            raise CandidateNotFound(
                details="Candidate could not be found",
                error_code="CANDIDATE_NOT_FOUND",
            )

        return CandidateDetailsResponse(
            id=candidate.id,
            full_name=candidate.full_name,
            email=candidate.email,
            phone=candidate.phone,
            current_title=candidate.current_title,
            location=candidate.location,
            summary=candidate.summary,
            source_type=candidate.source_type,
            total_experience_months=candidate.total_experience_months,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            skills=[
                CandidateSkillResponse(
                    id=skill.id,
                    skill_name=skill.skill_name,
                    is_primary=skill.is_primary,
                )
                for skill in candidate.skills
            ],
            experiences=[
                CandidateExperienceResponse(
                    id=experience.id,
                    company_name=experience.company_name,
                    title=experience.title,
                    description=experience.description,
                    start_date=experience.start_date,
                    end_date=experience.end_date,
                    is_current=experience.is_current,
                    skills=[
                        CandidateExperienceSkillResponse(
                            id=skill.id,
                            skill_name=skill.skill_name,
                        )
                        for skill in experience.skills
                    ],
                )
                for experience in candidate.experiences
            ],
            educations=[
                CandidateEducationResponse(
                    id=education.id,
                    institution_name=education.institution_name,
                    degree=education.degree,
                    field_of_study=education.field_of_study,
                    start_date=education.start_date,
                    end_date=education.end_date,
                )
                for education in candidate.educations
            ],
        )

    async def get_candidate_evaluation_board(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> CandidateEvaluationBoardResponse:
        candidate = await self.get_candidate_details(
            job_description_id,
            candidate_id,
            current_user,
        )

        pipeline_entry = await self.repository.get_pipeline_entry(
            job_description_id,
            candidate_id,
        )
        score = await self.repository.get_candidate_job_score(
            job_description_id,
            candidate_id,
        )

        return CandidateEvaluationBoardResponse(
            candidate=candidate,
            pipeline=self._build_pipeline_snapshot(
                pipeline_entry,
            )
            if pipeline_entry
            else None,
            score=CandidateScoreBreakdownResponse(
                final_score=score.final_score,
                skill_score=score.skills_score,
                experience_score=score.experience_score,
                recency_score=score.recency_score,
                role_fit_score=score.role_fit_score,
                education_score=score.education_score,
                confidence=score.confidence,
                explanation=score.explanation,
            )
            if score
            else None,
        )

    async def update_pipeline_notes(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        data: PipelineNotesUpdateRequest,
        current_user: AuthenticatedUserContext,
    ) -> PipelineSnapshotResponse:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )
        candidate = await self.repository.get_candidate_by_id(
            candidate_id,
        )

        if not candidate:
            raise CandidateNotFound(
                details="Candidate could not be found",
                error_code="CANDIDATE_NOT_FOUND",
            )

        pipeline_entry = await self.repository.update_pipeline_notes(
            job_description_id,
            candidate_id,
            data.recruiter_notes,
        )

        return self._build_pipeline_snapshot(
            pipeline_entry,
        )

    async def bulk_update_pipeline_stage(
        self,
        job_description_id: UUID,
        data: PipelineStageUpdateRequest,
        current_user: AuthenticatedUserContext,
    ) -> list[PipelineSnapshotResponse]:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        pipeline_entries = await self.repository.bulk_update_pipeline_stage(
            job_description_id,
            data.candidate_ids,
            data.stage,
        )

        return [
            self._build_pipeline_snapshot(
                pipeline_entry,
            )
            for pipeline_entry in pipeline_entries
        ]


    async def _prescore_candidates(
        self,
        job_description_id: UUID,
        candidates: list[Candidate],
    ) -> CandidatePrescoreBatchOutput:
        job_description = await self.repository.get_job_description_by_id(
            job_description_id,
        )

        compressed_jd = self._build_compressed_job_description(
            job_description,
        )

        compressed_candidates = [
            self._build_compressed_candidate(
                candidate,
            )
            for candidate in candidates
        ]

        print("\n" + "="*40 + "\nPrescoring LLM Input\n" + "="*40)
        print(f"Compressed JD Profile:\n{compressed_jd.profile_text}\n")
        print("Compressed Candidates Profiles sent to LLM:")
        for cc in compressed_candidates:
            print(f"- ID: {cc.candidate_id}\nProfile Text:\n{cc.profile_text}\n" + "-"*20)
        print("="*40 + "\n")

        score_results = await self.prescoring_client.prescore_candidates(
            compressed_candidates,
            compressed_jd,
        )

        score_results.scores.sort(
            key=lambda score: score.score,
            reverse=True,
        )
        return score_results

    async def _source_candidates_for_job_description(
        self,
        job_description_id: UUID,
    ) -> list[Candidate]:
        job_description = await self.repository.get_job_description_by_id(
            job_description_id,
        )

        all_candidates = await self.repository.get_candidates_for_job_description()

        mandatory_skills = {
            skill.skill_name.strip().lower()
            for skill in job_description.skills
            if skill.is_mandatory
        }
        optional_skills = {
            skill.skill_name.strip().lower()
            for skill in job_description.skills
            if not skill.is_mandatory
        }
        job_title_terms = {
            term.strip().lower()
            for term in job_description.title.split()
            if len(term.strip()) > 2
        }

        sourced_candidates: list[Candidate] = []

        for candidate in all_candidates:
            candidate_skills = self._extract_candidate_skill_names(
                candidate,
            )
            candidate_title = (
                candidate.current_title or ""
            ).lower()
            experience_years = (
                candidate.total_experience_months / 12
            )

            mandatory_matches = len(
                mandatory_skills & candidate_skills,
            )
            optional_matches = len(
                optional_skills & candidate_skills,
            )

            matches_experience = (
                experience_years
                >= max(job_description.min_experience - 1, 0)
            )
            matches_role_hint = (
                any(
                    term in candidate_title
                    for term in job_title_terms
                )
                if job_title_terms
                else False
            )

            has_relevant_skills = (
                mandatory_matches > 0
                or optional_matches > 0
                or not mandatory_skills
            )

            if not matches_experience:
                continue

            if not has_relevant_skills and not matches_role_hint:
                continue

            sourced_candidates.append(
                candidate,
            )
        print("\n" + "="*40 + "\nSourced Candidates\n" + "="*40)
        for idx, candidate in enumerate(sourced_candidates):
            print(f"{idx+1}. Name: {candidate.full_name} | ID: {candidate.id} | Email: {candidate.email} | Exp: {candidate.total_experience_months} months")
        print("="*40 + "\n")

        return sourced_candidates

    def _extract_candidate_skill_names(
        self,
        candidate: Candidate,
    ) -> set[str]:
        skill_names = {
            skill.skill_name.strip().lower()
            for skill in candidate.skills
        }

        for experience in candidate.experiences:
            skill_names.update(
                skill.skill_name.strip().lower()
                for skill in experience.skills
            )

        return skill_names

    def _build_pipeline_candidate_result(
        self,
        candidate: Candidate,
        score: CandidateJobScore | object | None = None,
        pipeline_entry: object | None = None,
        prescore_rank: int | None = None,
        prescore_score: int | None = None,
    ) -> PipelineCandidateResult:
        final_score = getattr(
            score,
            "final_score",
            None,
        )
        confidence = getattr(
            score,
            "confidence",
            None,
        )
        matched_mandatory_skills = getattr(
            score,
            "matched_mandatory_skills",
            [],
        )
        matched_optional_skills = getattr(
            score,
            "matched_optional_skills",
            [],
        )
        missing_mandatory_skills = getattr(
            score,
            "missing_mandatory_skills",
            [],
        )
        updated_at = getattr(
            score,
            "updated_at",
            None,
        )
        stage = getattr(
            pipeline_entry,
            "stage",
            "PRE_SCORED",
        )
        recruiter_notes = getattr(
            pipeline_entry,
            "recruiter_notes",
            None,
        )
        hiring_manager_notes = getattr(
            pipeline_entry,
            "hiring_manager_notes",
            None,
        )

        return PipelineCandidateResult(
            candidate_id=candidate.id,
            full_name=candidate.full_name,
            current_title=candidate.current_title,
            location=candidate.location,
            total_experience_months=candidate.total_experience_months,
            prescore_rank=prescore_rank,
            prescore_score=prescore_score,
            final_score=final_score,
            confidence=confidence,
            matched_mandatory_skills=matched_mandatory_skills,
            matched_optional_skills=matched_optional_skills,
            missing_mandatory_skills=missing_mandatory_skills,
            stage=stage,
            recruiter_notes=recruiter_notes,
            hiring_manager_notes=hiring_manager_notes,
            updated_at=updated_at,
        )

    def _build_pipeline_snapshot(
        self,
        pipeline_entry: object,
    ) -> PipelineSnapshotResponse:
        return PipelineSnapshotResponse(
            id=getattr(pipeline_entry, "id"),
            candidate_id=getattr(
                pipeline_entry,
                "candidate_id",
            ),
            jd_id=getattr(pipeline_entry, "jd_id"),
            stage=getattr(pipeline_entry, "stage"),
            recruiter_notes=getattr(
                pipeline_entry,
                "recruiter_notes",
                None,
            ),
            hiring_manager_notes=getattr(
                pipeline_entry,
                "hiring_manager_notes",
                None,
            ),
            created_at=getattr(
                pipeline_entry,
                "created_at",
            ),
        )

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
            education_requirement=job_description.education_requirement,
            preferred_qualifications=job_description.preferred_qualifications,
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

    async def get_candidate_score(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> CandidateScoreResponse:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )
        score = await self.repository.get_candidate_job_score(
            job_description_id,
            candidate_id,
        )
        if not score:
            raise CandidateNotFound(
                details="Candidate score could not be found",
                error_code="SCORE_NOT_FOUND",
            )
        return CandidateScoreResponse(
            candidate_id=score.candidate_id,
            job_description_id=score.job_description_id,
            final_score=score.final_score,
            confidence=score.confidence,
            breakdown=CandidateScoreDetailBreakdown(
                skills=score.skills_score,
                experience=score.experience_score,
                recency=score.recency_score,
                role_fit=score.role_fit_score,
                education=score.education_score,
            ),
            matched_mandatory_skills=score.matched_mandatory_skills,
            matched_optional_skills=score.matched_optional_skills,
            missing_mandatory_skills=score.missing_mandatory_skills,
            explanation=score.explanation,
            updated_at=score.updated_at,
        )

    async def rescore_candidate(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> CandidateScoreResponse:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )
        await self.score_candidates_for_job_description(
            job_description_id=job_description_id,
            current_user=current_user,
            candidate_ids=[candidate_id],
        )
        return await self.get_candidate_score(
            job_description_id=job_description_id,
            candidate_id=candidate_id,
            current_user=current_user,
        )

    async def _get_authorized_job_description(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> JobDescriptionResponse:
        recruiter_id = await self.repository.get_recruiter_id_by_job_description_id(
            job_description_id,
        )

        if recruiter_id != current_user.user_id:
            raise RecruiterAccessRequired(
                details="You do not have access to this job description",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        job_description = await self.repository.get_job_description_by_id(
            job_description_id,
        )

        return JobDescriptionResponse(
            id=job_description.id,
            title=job_description.title,
            department=job_description.department,
            job_purpose=job_description.job_purpose,
            responsibilities=job_description.responsibilities,
            min_experience=job_description.min_experience,
            max_experience=job_description.max_experience,
            location=job_description.location,
            education_requirement=job_description.education_requirement,
            preferred_qualifications=job_description.preferred_qualifications,
            employment_type_id=job_description.employment_type_id,
            status_id=job_description.status_id,
            created_at=job_description.created_at,
            updated_at=job_description.updated_at,
            skills=[
                JDSkillResponse(
                    id=skill.id,
                    skill_name=skill.skill_name,
                    is_mandatory=skill.is_mandatory,
                )
                for skill in job_description.skills
            ],
        )
