from __future__ import annotations

import asyncio
from datetime import datetime, UTC
import hashlib
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.config.settings import settings
from src.data.models.postgres.notification import NotificationType
from src.core.services.notification_service import NotificationService
from src.utils.email_templates import get_generic_email_html

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.job_description_exception import (
    RecruiterAccessRequired,
)
from src.core.exceptions.scoring_exceptions import (
    CandidateNotFound,
    ResumeImportValidationError,
    ScoringBaseException,
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
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JDSkillResponse,
    JobDescriptionResponse,
)
from src.schemas.scoring_schema import (
    SharedCampaignCandidateResponse,
    HMCampaignResponse,
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
from src.schemas.candidate_search_schema import CandidateDetailsResponse as SourcedCandidateDetailsResponse
from src.core.services.candidate_acquisition_service import CandidateAcquisitionService
from src.core.services.candidate_synchronization_service import CandidateSynchronizationService
from src.data.clients.candidate_search_client import CandidateSearchClient
from src.control.agents.candidate_search_query_agent import CandidateSearchQueryAgent
from src.schemas.candidate_search_schema import CandidateSummary
from src.core.services.progress_reporter import PipelineProgressReporter


class ScoringService:
    def __init__(self, db: AsyncSession):
        self.repository = ScoringRepository(db)
        self.resume_parser = ResumeParser()
        self.scoring_client = CandidateScoringClient()
        self.prescoring_client = CandidatePrescoringClient()

        # Instantiate clients and agents
        self.search_client = CandidateSearchClient()
        self.search_query_agent = CandidateSearchQueryAgent()

        # Instantiate services
        self.acquisition_service = CandidateAcquisitionService(
            local_search_fn=self._source_candidates_for_job_description,
            compress_candidate_fn=self._build_compressed_candidate,
            search_query_agent=self.search_query_agent,
            search_client=self.search_client,
        )
        self.synchronization_service = CandidateSynchronizationService(
            scoring_service=self,
            search_client=self.search_client,
        )

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
            return_exceptions=True,
        )

        candidate_scores = []
        for result in results:
            if isinstance(result, Exception):
                import logging
                logging.getLogger(__name__).error(
                    "Recoverable deep-scoring error encountered for a candidate: %s",
                    str(result),
                )
            elif result is not None and result.payload is not None:
                candidate_scores.append(result.payload)

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
        progress_reporter: PipelineProgressReporter | None = None,
    ) -> PipelineExecutionResponse:
        if progress_reporter is None:
            from src.core.services.progress_reporter import NoOpProgressReporter
            progress_reporter = NoOpProgressReporter()

        job_description = await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        await progress_reporter.update_stage("ACQUIRING")

        # 1. Acquire candidate summaries using CandidateAcquisitionService
        required_prescore_candidates = 10 * data.k
        acquisition_result = await self.acquisition_service.acquire_candidates(
            job_description=job_description,
            job_description_id=job_description_id,
            required_prescore_candidates=required_prescore_candidates,
        )

        # Check if external sourcing was executed, set stage to SOURCING
        if not acquisition_result.sourcing_skipped:
            await progress_reporter.update_stage("SOURCING")

        matched_candidate_count = len(acquisition_result.candidates)

        # 2. If confirm == False, return preview immediately
        if not data.confirm:
            return PipelineExecutionResponse(
                stage="preview",
                matched_candidate_count=matched_candidate_count,
                eligible_candidate_count=None,
                selected_candidate_count=None,
                top_k=data.k,
            )

        if not acquisition_result.candidates:
            return PipelineExecutionResponse(
                stage="completed",
                matched_candidate_count=0,
                eligible_candidate_count=0,
                selected_candidate_count=0,
                top_k=data.k,
                candidates=[],
            )

        # 3. Convert CandidateSummary objects to CompressedCandidate objects
        compressed_candidates = [
            CompressedCandidate(
                candidate_id=c.candidate_id,
                profile_text=c.profile_text,
            )
            for c in acquisition_result.candidates
        ]

        await progress_reporter.update_stage("PRE_SCORING")

        # 4. Run pre-scoring implementation on the acquired summaries
        prescore_output = await self._prescore_candidates(
            job_description_id,
            compressed_candidates,
        )
        print("\n" + "="*40 + "\nPrescore Output (Sorted)\n" + "="*40)
        for idx, score in enumerate(prescore_output.scores):
            print(f"{idx+1}. ID: {score.candidate_id} -> Score: {score.score}")
        print("="*40 + "\n")

        # 5. Apply the existing pre-score threshold logic
        eligible_scores = [
            score
            for score in prescore_output.scores
            if score.score >= data.minimum_prescore_threshold
        ]
        eligible_candidate_count = len(eligible_scores)

        # 6. Select the top K candidates
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

        await progress_reporter.update_stage("SYNCHRONIZING")

        # 7. Pass selected candidate IDs to CandidateSynchronizationService
        await self.synchronization_service.synchronize_candidates(top_candidate_ids)

        # 8. Load the selected Candidate ORM objects from local DB
        db_candidates = await self.repository.get_candidates_by_ids(top_candidate_ids)
        candidate_lookup = {c.id: c for c in db_candidates}

        await progress_reporter.update_stage("DEEP_SCORING")

        # 9. Execute deep scoring on the selected candidates
        deep_score_output = await self.score_candidates_for_job_description(
            job_description_id,
            current_user,
            candidate_ids=top_candidate_ids,
        )
        print("\n" + "="*40 + "\nDeep Score Output\n" + "="*40)
        for idx, score in enumerate(deep_score_output.scores):
            c_name = candidate_lookup[score.candidate_id].full_name if score.candidate_id in candidate_lookup else "Unknown"
            print(f"{idx+1}. Name: {c_name} (ID: {score.candidate_id})")
            print(f"   Final Score: {score.final_score} | Confidence: {score.confidence}%")
            print(f"   Breakdown -> Skills: {score.skills_score} | Exp: {score.experience_score} | Recency: {score.recency_score} | Role Fit: {score.role_fit_score} | Edu: {score.education_score}")
            print(f"   Matched Mandatory Skills: {score.matched_mandatory_skills}")
            print(f"   Missing Mandatory Skills: {score.missing_mandatory_skills}")
            explanation_summary = score.explanation.get("summary") if isinstance(score.explanation, dict) else getattr(score.explanation, "summary", "")
            print(f"   Explanation Summary: {explanation_summary}")
            print("-" * 20)
        print("="*40 + "\n")

        # 10. Construct response using the existing response building logic
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

    async def _get_candidate_details_dto(
        self,
        candidate_id: UUID,
    ) -> CandidateDetailsResponse:
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
            resume_text=candidate.resume_text,
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
        return await self._get_candidate_details_dto(candidate_id)

    async def _get_candidate_evaluation_board_internal(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
    ) -> CandidateEvaluationBoardResponse:
        candidate = await self._get_candidate_details_dto(candidate_id)

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

    async def get_candidate_evaluation_board(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> CandidateEvaluationBoardResponse:
        await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )
        return await self._get_candidate_evaluation_board_internal(
            job_description_id,
            candidate_id,
        )

    async def get_hm_candidate_evaluation_board(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> CandidateEvaluationBoardResponse:
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(message="Access denied", details="Only hiring managers can access this endpoint.", status_code=403)

        job_description = await self.repository.get_job_description_by_id(job_description_id)
        if not job_description or job_description.hiring_manager_id != current_user.user_id:
            raise ScoringBaseException(message="Access denied", details="Hiring manager does not own this campaign.", status_code=403)

        pipeline_entry = await self.repository.get_pipeline_entry(
            job_description_id,
            candidate_id,
        )

        if not pipeline_entry or not pipeline_entry.shared_with_hiring_manager:
            raise ScoringBaseException(
                message="Access denied",
                details="Candidate shortlist is not shared with the hiring manager.",
                status_code=403,
            )

        return await self._get_candidate_evaluation_board_internal(
            job_description_id,
            candidate_id,
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
        candidates: list[CompressedCandidate],
    ) -> CandidatePrescoreBatchOutput:
        job_description = await self.repository.get_job_description_by_id(
            job_description_id,
        )

        compressed_jd = self._build_compressed_job_description(
            job_description,
        )

        print("\n" + "="*40 + "\nPrescoring LLM Input\n" + "="*40)
        print(f"Compressed JD Profile:\n{compressed_jd.profile_text}\n")
        print("Compressed Candidates Profiles sent to LLM:")
        for cc in candidates:
            print(f"- ID: {cc.candidate_id}\nProfile Text:\n{cc.profile_text}\n" + "-"*20)
        print("="*40 + "\n")

        score_results = await self.prescoring_client.prescore_candidates(
            candidates,
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
        shared_with_hiring_manager = getattr(
            pipeline_entry,
            "shared_with_hiring_manager",
            False,
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
            shared_with_hiring_manager=shared_with_hiring_manager,
            updated_at=updated_at,
            hm_decision=getattr(pipeline_entry, "hm_decision", None),
            interview_link=getattr(pipeline_entry, "interview_link", None),
            interview_datetime=getattr(pipeline_entry, "interview_datetime", None),
            interview_timezone=getattr(pipeline_entry, "interview_timezone", None),
            interview_message=getattr(pipeline_entry, "interview_message", None),
            interview_sent_at=getattr(pipeline_entry, "interview_sent_at", None),
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
            hm_decision=getattr(pipeline_entry, "hm_decision", None),
            interview_link=getattr(pipeline_entry, "interview_link", None),
            interview_datetime=getattr(pipeline_entry, "interview_datetime", None),
            interview_timezone=getattr(pipeline_entry, "interview_timezone", None),
            interview_message=getattr(pipeline_entry, "interview_message", None),
            interview_sent_at=getattr(pipeline_entry, "interview_sent_at", None),
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

    async def upsert_candidate_profile(
        self,
        candidate_details: SourcedCandidateDetailsResponse,
    ) -> Candidate:
        """Upsert a candidate details profile received from the Sourcing Service.

        Ensures transaction safety by relying on the session transaction boundary.
        """
        return await self.repository.upsert_candidate(candidate_details)

    async def share_shortlist(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
        candidate_ids: list[UUID],
        notes_by_candidate: dict[UUID, str],
    ) -> int:
        if current_user.role != UserRole.recruiter:
            raise ScoringBaseException(message="Access denied", details="Only recruiters are allowed to share shortlists.", status_code=403)
            
        # 1. Validate that all submitted candidates already exist in the pipeline for this job description
        invalid_ids = await self.repository.validate_candidates_belong_to_job(
            job_description_id,
            candidate_ids,
        )
        if invalid_ids:
            invalid_str = ", ".join(str(cid) for cid in invalid_ids)
            raise ScoringBaseException(
                message="Validation failed",
                details=f"Invalid candidate IDs for this job description: {invalid_str}",
                status_code=400,
            )
            
        # 2. Perform the update
        shared_count = await self.repository.share_shortlist_with_hiring_manager(
            job_description_id,
            candidate_ids,
            notes_by_candidate,
        )
        
        # 3. Commit transaction successfully
        await self.repository.db.commit()
        logger.info("Shortlist shared: JobDescription %s successfully committed sharing for %s candidates", job_description_id, shared_count)
        
        # 4. Best-effort notification dispatch to the Hiring Manager
        try:
            # Load JobDescription along with recruiter and hiring_manager relations
            stmt = (
                select(JobDescription)
                .options(
                    selectinload(JobDescription.recruiter),
                    selectinload(JobDescription.hiring_manager),
                )
                .where(JobDescription.id == job_description_id)
            )
            res = await self.repository.db.execute(stmt)
            jd = res.scalar_one_or_none()

            if jd and jd.hiring_manager:
                notification_service = NotificationService(self.repository.db)
                frontend_base = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
                absolute_target_url = f"{frontend_base}/hm/shared-campaigns/{job_description_id}"
                
                email_body = (
                    f"Hello {jd.hiring_manager.name},\n\n"
                    f"{jd.recruiter.name} has shared a new candidate shortlist for "
                    f"\"{jd.title}\" with you.\n\n"
                    f"There are {len(candidate_ids)} recommended candidates ready for your review."
                )

                email_html = get_generic_email_html(
                    title="New Shortlist Shared",
                    body=email_body,
                    action_text="Review Candidates",
                    action_url=absolute_target_url
                )

                await notification_service.notify(
                    user=jd.hiring_manager,
                    notification_type=NotificationType.SHORTLIST_SHARED,
                    title="New Candidate Shortlist Shared",
                    message=f"A new shortlist for \"{jd.title}\" has been shared with you by {jd.recruiter.name}. Review the recommended candidates.",
                    target_url=f"/hm/shared-campaigns/{job_description_id}",
                    metadata={"job_description_id": str(job_description_id), "candidate_count": len(candidate_ids)},
                    send_in_app=True,
                    send_email=True,
                    email_subject=f"New candidate shortlist for {jd.title}",
                    email_html=email_html
                )
                logger.info("Hiring Manager notification created and email sent for shortlist share on campaign %s", job_description_id)
            elif not jd:
                logger.warning("Could not send shortlist share notification: Job description %s not found.", job_description_id)
            else:
                logger.warning("Could not send shortlist share notification: Job description %s has no assigned Hiring Manager.", job_description_id)
        except Exception as e:
            # Notification failures must NEVER rollback or fail the shortlist sharing transaction
            logger.exception("Hiring Manager email failed: Failed to send shortlist shared notification: %s", str(e))
        
        return shared_count

    async def get_hm_shared_campaigns(
        self,
        current_user: AuthenticatedUserContext,
    ) -> list[HMCampaignResponse]:
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(message="Access denied", details="Only hiring managers can view shared campaigns.", status_code=403)
            
        jds = await self.repository.get_hm_campaigns(current_user.user_id)
        
        from src.data.models.postgres.pipeline import HiringManagerDecision
        
        response = []
        for jd in jds:
            shared_entries = [p for p in jd.pipeline_entries if p.shared_with_hiring_manager]
            
            # calculate counts
            shared_candidate_count = len(shared_entries)
            accepted_candidate_count = sum(1 for p in shared_entries if p.hm_decision == HiringManagerDecision.INTERVIEW_SENT)
            rejected_candidate_count = sum(1 for p in shared_entries if p.hm_decision == HiringManagerDecision.REJECTED)
            pending_candidate_count = sum(1 for p in shared_entries if p.hm_decision == HiringManagerDecision.PENDING)
            
            # calculate latest shared date
            shared_dates = [p.shared_at for p in shared_entries if p.shared_at is not None]
            shared_at = max(shared_dates) if shared_dates else None
            
            recruiter_name = jd.recruiter.name if jd.recruiter else "Unknown Recruiter"
            
            response.append(
                HMCampaignResponse(
                    id=jd.id,
                    title=jd.title,
                    department=jd.department,
                    recruiter_name=recruiter_name,
                    shared_at=shared_at,
                    shared_candidate_count=shared_candidate_count,
                    accepted_candidate_count=accepted_candidate_count,
                    rejected_candidate_count=rejected_candidate_count,
                    pending_candidate_count=pending_candidate_count,
                )
            )
            
        return response

    async def get_hm_shared_candidates(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> list[SharedCampaignCandidateResponse]:
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(message="Access denied", details="Only hiring managers can view shared candidates.", status_code=403)
            
        rows = await self.repository.get_shared_candidates_for_hm(
            job_description_id,
            current_user.user_id,
        )
        
        return [
            SharedCampaignCandidateResponse(
                candidate_id=cand.id,
                full_name=cand.full_name,
                current_title=cand.current_title,
                total_experience_months=cand.total_experience_months,
                location=cand.location,
                final_score=score.final_score,
                recruiter_notes=pipe.recruiter_notes,
                shared_at=pipe.shared_at,
                hm_decision=pipe.hm_decision,
                hiring_manager_notes=pipe.hiring_manager_notes,
                interview_link=pipe.interview_link,
                interview_datetime=pipe.interview_datetime,
                interview_timezone=pipe.interview_timezone,
                interview_message=pipe.interview_message,
                interview_sent_at=pipe.interview_sent_at,
            )
            for cand, pipe, score in rows
        ]

    async def submit_hm_candidate_review(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
        decision: HiringManagerDecision,
        remarks: str | None,
    ) -> Pipeline:
        from src.data.models.postgres.pipeline import HiringManagerDecision
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(message="Access denied", details="Only hiring managers can submit candidate reviews.", status_code=403)
            
        pipeline_entry = await self.repository.submit_hm_review(
            job_description_id,
            candidate_id,
            current_user.user_id,
            decision,
            remarks,
        )
        
        if not pipeline_entry:
            raise ScoringBaseException(
                message="Review failed",
                details="Failed to submit review. Candidate may not be shared, or job description is not assigned to you.",
                status_code=400,
            )
            
        # Publish CANDIDATE_REVIEWED event (stub/log for future integration)
        print(f"[EVENT] CANDIDATE_REVIEWED: Candidate {candidate_id} reviewed for JobDescription {job_description_id}. Decision: {decision}")
        
        return pipeline_entry

    async def schedule_interview(
        self,
        job_description_id: UUID,
        candidate_id: UUID,
        current_user: AuthenticatedUserContext,
        interview_link: str,
        interview_datetime: datetime,
        timezone: str,
        message: str | None,
    ) -> Pipeline:
        from src.data.models.postgres.pipeline import HiringManagerDecision
        from src.data.models.postgres.user import User
        from datetime import UTC
        
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(
                message="Access denied",
                details="Only hiring managers can schedule interviews.",
                status_code=403
            )
            
        # 1. Authorize: Load JobDescription along with recruiter relation
        stmt = (
            select(JobDescription)
            .options(
                selectinload(JobDescription.recruiter),
            )
            .where(JobDescription.id == job_description_id)
        )
        res = await self.repository.db.execute(stmt)
        jd = res.scalar_one_or_none()
        
        if not jd or jd.hiring_manager_id != current_user.user_id:
            raise ScoringBaseException(
                message="Access denied",
                details="Hiring manager does not own this campaign or job description not found.",
                status_code=403
            )
            
        # 2. Validate candidate is shared
        pipeline_entry = await self.repository.get_pipeline_entry(
            job_description_id,
            candidate_id,
        )
        if not pipeline_entry or not pipeline_entry.shared_with_hiring_manager:
            raise ScoringBaseException(
                message="Access denied",
                details="Candidate shortlist is not shared with the hiring manager.",
                status_code=403
            )
            
        # 3. Validate candidate email exists
        candidate = await self.repository.get_candidate_by_id(candidate_id)
        if not candidate:
            raise CandidateNotFound(
                details="Candidate could not be found",
                error_code="CANDIDATE_NOT_FOUND"
            )
        if not candidate.email or not candidate.email.strip():
            raise ScoringBaseException(
                message="Validation failed",
                details="Candidate email address is missing. Cannot send interview invitation.",
                status_code=400
            )

        # 4. Dispatch Email to Candidate
        notification_service = NotificationService(self.repository.db)
        
        date_str = interview_datetime.strftime("%B %d, %Y")
        time_str = interview_datetime.strftime("%I:%M %p")
        
        candidate_body = (
            f"Hello {candidate.full_name},\n\n"
            f"Congratulations! You have been selected for an interview for the "
            f"\"{jd.title}\" role.\n\n"
            f"Please find the details below:\n"
            f"- **Date:** {date_str}\n"
            f"- **Time:** {time_str}\n"
            f"- **Timezone:** {timezone}\n"
            f"- **Link:** {interview_link}\n"
        )
        if message:
            candidate_body += f"\n**Message from Hiring Manager:**\n{message}\n"

        candidate_html = get_generic_email_html(
            title="Interview Invitation",
            body=candidate_body,
            action_text="Join Interview",
            action_url=interview_link
        )
        
        # This will raise exception if Brevo client fails
        await notification_service.send_email(
            recipient_email=candidate.email,
            recipient_name=candidate.full_name,
            subject=f"Interview Invitation – {jd.title}",
            html_content=candidate_html
        )
        logger.info("Hiring Manager email sent successfully to candidate %s", candidate.email)

        # 5. Only AFTER successful email dispatch, update pipeline in DB
        pipeline_entry.hm_decision = HiringManagerDecision.INTERVIEW_SENT
        pipeline_entry.interview_link = interview_link
        pipeline_entry.interview_datetime = interview_datetime
        pipeline_entry.interview_timezone = timezone
        pipeline_entry.interview_message = message
        pipeline_entry.interview_sent_at = datetime.now(UTC)
        
        await self.repository.db.commit()
        logger.info("Pipeline status updated to INTERVIEW_SENT for candidate %s on campaign %s", candidate_id, job_description_id)

        # 6. Recruiter Notification (best-effort)
        try:
            res_hm = await self.repository.db.execute(select(User).where(User.id == current_user.user_id))
            hm_user = res_hm.scalar_one_or_none()
            hm_name = hm_user.name if hm_user else "Hiring Manager"

            recruiter_user = jd.recruiter
            frontend_base = settings.ALLOWED_ORIGINS[0] if settings.ALLOWED_ORIGINS else "http://localhost:5173"
            
            recruiter_body = (
                f"Hello {recruiter_user.name},\n\n"
                f"{hm_name} has scheduled an interview with {candidate.full_name} for your job description \"{jd.title}\".\n\n"
                f"Interview Details:\n"
                f"- **Date & Time:** {date_str} at {time_str} ({timezone})\n"
                f"- **Link:** {interview_link}\n"
            )
            recruiter_html = get_generic_email_html(
                title="Interview Scheduled",
                body=recruiter_body,
                action_text="View Candidate Detail",
                action_url=f"{frontend_base}/recruiter/job-descriptions/{job_description_id}/candidates/{candidate_id}"
            )

            await notification_service.notify(
                user=recruiter_user,
                notification_type=NotificationType.INTERVIEW_INVITATION,
                title="Interview Scheduled",
                message=f"{hm_name} has scheduled an interview with {candidate.full_name} for \"{jd.title}\".",
                target_url=f"/recruiter/job-descriptions/{job_description_id}/candidates/{candidate_id}",
                metadata={
                    "job_description_id": str(job_description_id),
                    "candidate_id": str(candidate_id),
                    "candidate_name": candidate.full_name
                },
                send_in_app=True,
                send_email=True,
                email_subject=f"Interview scheduled for {candidate.full_name}",
                email_html=recruiter_html
            )
            logger.info("Hiring Manager notification created and Recruiter email sent successfully for interview on candidate %s", candidate_id)
        except Exception as recruiter_notify_err:
            logger.warning("Failed to send recruiter notification for interview invitation: %s", str(recruiter_notify_err))

        return pipeline_entry
