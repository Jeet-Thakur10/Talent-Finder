from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.settings import settings
from src.control.agents.candidate_search_query_agent import CandidateSearchQueryAgent
from src.control.agents.scoring_agent import (
    CandidatePrescoringClient,
    CandidateScoringClient,
    CandidateScoringResult,
)
from src.core.exceptions.job_description_exception import (
    RecruiterAccessRequired,
)
from src.core.exceptions.scoring_exceptions import (
    CandidateNotFound,
    ResumeImportValidationError,
    ScoringBaseException,
)
from src.core.services.candidate_acquisition_service import CandidateAcquisitionService
from src.core.services.candidate_synchronization_service import (
    CandidateSynchronizationService,
)
from src.core.services.notification_service import NotificationService
from src.core.services.progress_reporter import PipelineProgressReporter
from src.core.services.resume_parser import ResumeParser
from src.data.clients.candidate_search_client import CandidateSearchClient
from src.data.models.postgres.candidate import Candidate
from src.data.models.postgres.candidate_job_score import CandidateJobScore
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.notification import NotificationType
from src.data.models.postgres.pipeline import HiringManagerDecision, Pipeline
from src.data.models.postgres.user import User
from src.data.repositories.scoring_repository import ScoringRepository
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.candidate_search_schema import (
    CandidateDetailsResponse as SourcedCandidateDetailsResponse,
)
from src.schemas.job_description_schema import (
    JDSkillResponse,
    JobDescriptionResponse,
)
from src.schemas.pipeline_candidate_state import PipelineExecutionContext
from src.schemas.scoring_schema import (
    CandidateBatchScoreOutput,
    CandidateDetailsResponse,
    CandidateEducationInput,
    CandidateEducationResponse,
    CandidateEvaluationBoardResponse,
    CandidateExperienceInput,
    CandidateExperienceResponse,
    CandidateExperienceSkillResponse,
    CandidateImportRequest,
    CandidatePrescoreBatchOutput,
    CandidateScoreBreakdownResponse,
    CandidateScoreDetailBreakdown,
    CandidateScoreOutput,
    CandidateScoreResponse,
    CandidateScoringInput,
    CandidateSkillInput,
    CandidateSkillResponse,
    CompressedCandidate,
    CompressedJobDescription,
    HMCampaignResponse,
    JobDescriptionScoringInput,
    JobSkillInput,
    ParsedCandidateProfile,
    PipelineCandidateResult,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineNotesUpdateRequest,
    PipelineSnapshotResponse,
    PipelineStageUpdateRequest,
    SharedCampaignCandidateResponse,
)
from src.utils.email_templates import get_generic_email_html

logger = logging.getLogger(__name__)

class ScoringService:
    def __init__(self, db: AsyncSession):
        self.repository = ScoringRepository(db)
        self.resume_parser = ResumeParser()
        self.scoring_client = CandidateScoringClient()
        self.prescoring_client = CandidatePrescoringClient()

        # Concurrency Semaphore configuration
        num_keys = len(settings.groq_keys)
        if num_keys == 0:
            num_keys = 1
        effective_concurrency = num_keys * settings.GROQ_CONCURRENCY_PER_KEY
        self.concurrency_semaphore = asyncio.Semaphore(effective_concurrency)

        # Instantiate clients and agents
        self.search_client: CandidateSearchClient | None = CandidateSearchClient()
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
        context: PipelineExecutionContext | None = None,
    ) -> CandidateBatchScoreOutput:
        import time

        from src.schemas.pipeline_candidate_state import StageStatus

        job_description = await self._get_authorized_job_description(
            job_description_id,
            current_user,
        )

        candidates = await self.repository.get_candidates_for_job_description(
            candidate_ids=candidate_ids,
        )

        if not candidates:
            if context and candidate_ids:
                for cid in candidate_ids:
                    if cid in context.candidates:
                        state = context.candidates[cid]
                        if state.scoring == StageStatus.PENDING:
                            state.mark_scoring_failed(
                                error_code="NO_CANDIDATE_RECORD_IN_DB",
                                error_message=(
                                    "Candidate record does not exist "
                                    "in local database"
                                ),
                            )
            return CandidateBatchScoreOutput(
                scores=[],
            )

        scoring_job = self._build_job_description_scoring_input(
            job_description,
        )

        scoring_tasks = []
        task_candidate_ids = []
        active_requests_count = 0
        max_active_requests = 0

        async def throttled_scoring_task(
            candidate: Candidate,
        ) -> CandidateScoringResult:
            nonlocal active_requests_count, max_active_requests
            async with self.concurrency_semaphore:
                active_requests_count += 1
                if active_requests_count > max_active_requests:
                    max_active_requests = active_requests_count
                try:
                    res = await self.scoring_client.score_candidate(
                        scoring_job,
                        self._build_candidate_scoring_input(
                            candidate,
                        ),
                    )
                    return res
                finally:
                    active_requests_count -= 1

        for candidate in candidates:
            cid = candidate.id
            if context and cid in context.candidates:
                state = context.candidates[cid]
                if state.synchronization != StageStatus.SUCCESS:
                    state.mark_scoring_failed(
                        error_code="SYNC_FAILED",
                        error_message="Skipping scoring because synchronization failed",
                    )
                    continue
                state.scoring = StageStatus.PENDING

            scoring_tasks.append(
                throttled_scoring_task(candidate)
            )
            task_candidate_ids.append(cid)

        if not scoring_tasks:
            return CandidateBatchScoreOutput(
                scores=[],
            )

        start_time = time.perf_counter()
        results = await asyncio.gather(
            *scoring_tasks,
            return_exceptions=True,
        )
        scoring_duration = (time.perf_counter() - start_time) * 1000.0
        per_task_duration = scoring_duration / len(scoring_tasks)

        logger.info(
            f"Candidate scoring batch execution complete. "
            f"Max simultaneous requests: {max_active_requests}. "
            f"Total tasks: {len(scoring_tasks)}. "
            f"Duration: {scoring_duration:.2f}ms. "
            f"Average task duration: {per_task_duration:.2f}ms."
        )

        candidate_scores: list[CandidateScoreOutput] = []
        for cid, result in zip(task_candidate_ids, results):
            cand_state = (
                context.candidates[cid]
                if (context and cid in context.candidates)
                else None
            )

            if isinstance(result, BaseException):
                logger.error(
                    "Recoverable deep-scoring error encountered for a candidate: %s",
                    str(result),
                )
                if cand_state:
                    cand_state.mark_scoring_failed(
                        error_code="LLM_SCORING_ERROR",
                        error_message=str(result),
                        duration_ms=per_task_duration,
                    )
            elif result is not None and isinstance(result.payload,CandidateScoreOutput):
                candidate_scores.append(result.payload)
                if cand_state:
                    cand_state.mark_scoring_success(
                        final_score=result.payload.final_score,
                        confidence=result.payload.confidence,
                        duration_ms=per_task_duration,
                    )
            else:
                if cand_state:
                    cand_state.mark_scoring_failed(
                        error_code="LLM_SCORING_EMPTY",
                        error_message="AI client returned an empty scoring result",
                        duration_ms=per_task_duration,
                    )

        # Persistence Stage
        persist_start = time.perf_counter()
        persistence_failed_flag = False
        persistence_error_str = ""
        try:
            await self.repository.upsert_candidate_scores(
                job_description_id=job_description_id,
                scores=candidate_scores,
            )
            await self.repository.upsert_pipeline_entries(
                job_description_id,
                [score.candidate_id for score in candidate_scores],
                stage="SHORTLISTED",
            )
            if context is not None:
                active_candidate_ids = [
                    score.candidate_id for score in candidate_scores]
                await self.repository.delete_stale_candidate_scores_and_pipelines(
                    job_description_id=job_description_id,
                    active_candidate_ids=active_candidate_ids,
                )
            await self._transition_to_active_if_needed(job_description_id)
        except Exception as e:
            persistence_failed_flag = True
            persistence_error_str = str(e)
            logger.exception("Failed to persist scoring results: %s", e)

        persist_duration = (time.perf_counter() - persist_start) * 1000.0
        per_task_persist_duration = persist_duration / max(1, len(candidate_scores))

        for cid in task_candidate_ids:
            cand_state = (
                context.candidates[cid]
                if (context and cid in context.candidates)
                else None
            )
            if cand_state and cand_state.scoring == StageStatus.SUCCESS:
                if persistence_failed_flag:
                    cand_state.mark_persistence_failed(
                        error_code="DB_PERSISTENCE_FAILED",
                        error_message=persistence_error_str,
                        duration_ms=per_task_persist_duration,
                    )
                else:
                    cand_state.mark_persistence_success(
                        duration_ms=per_task_persist_duration
                    )

        if persistence_failed_flag:
            raise ScoringBaseException(
                details=f"Failed to persist candidate scores: {persistence_error_str}",
                error_code="PERSISTENCE_FAILED",
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
        import time
        from uuid import uuid4

        from src.schemas.pipeline_candidate_state import (
            CandidateTerminalOutcome,
            PipelineCandidateState,
            PipelineExecutionContext,
            StageOutcome,
            StageStatus,
        )

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
        acquisition_start = time.perf_counter()
        acquisition_result = await self.acquisition_service.acquire_candidates(
            job_description=job_description,
            job_description_id=job_description_id,
            required_prescore_candidates=required_prescore_candidates,
        )
        acquisition_duration = (time.perf_counter() - acquisition_start) * 1000.0

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

        # Initialize the transient PipelineExecutionContext coordinator
        context = PipelineExecutionContext(
            execution_id=uuid4(),
            job_description_id=job_description_id,
            recruiter_id=current_user.user_id,
        )

        for c in acquisition_result.candidates:
            state = PipelineCandidateState(
                candidate_id=c.candidate_id,
                profile_text=c.profile_text,
            )
            state.mark_acquired(
                duration_ms=acquisition_duration / max(1, matched_candidate_count)
            )
            context.candidates[c.candidate_id] = state

        if not acquisition_result.candidates:
            await self._transition_to_active_if_needed(job_description_id)
            is_incomplete = data.k > 0
            warning_reason = "INSUFFICIENT_QUALIFIED" if is_incomplete else None
            warning_message = (
                "Only 0 candidates satisfied the required criteria. "
                "The remaining candidates did not meet the qualification threshold."
            ) if is_incomplete else None
            return PipelineExecutionResponse(
                stage="completed",
                matched_candidate_count=0,
                eligible_candidate_count=0,
                selected_candidate_count=0,
                top_k=data.k,
                candidates=[],
                is_shortlist_incomplete=is_incomplete,
                warning_reason=warning_reason,
                warning_message=warning_message,
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
        prescore_start = time.perf_counter()
        prescore_output = await self._prescore_candidates(
            job_description_id,
            compressed_candidates,
        )
        prescore_duration = (time.perf_counter() - prescore_start) * 1000.0
        per_candidate_prescore_duration = prescore_duration / len(compressed_candidates)

        for score in prescore_output.scores:
            if score.candidate_id in context.candidates:
                context.candidates[score.candidate_id].mark_prescored(
                    prescore=score.score, duration_ms=per_candidate_prescore_duration
                )

        print("\n" + "=" * 40 + "\nPrescore Output (Sorted)\n" + "=" * 40)
        for idx, score in enumerate(prescore_output.scores):
            print(f"{idx + 1}. ID: {score.candidate_id} -> Score: {score.score}")
        print("=" * 40 + "\n")

        # 5. Apply the pre-score threshold logic
        eligible_scores = [
            score
            for score in prescore_output.scores
            if score.score >= data.minimum_prescore_threshold
        ]
        eligible_candidate_ids = [score.candidate_id for score in eligible_scores]

        # 6. Select the top K candidates
        top_scores = eligible_scores[: data.k]
        top_candidate_ids = [score.candidate_id for score in top_scores]

        # Mark and transition all candidates to their proper lifecycle status
        prescored_ids = {score.candidate_id for score in prescore_output.scores}
        for cid, state in context.candidates.items():
            if cid not in prescored_ids:
                state.prescoring = StageStatus.FAILED
                state.terminal_outcome = CandidateTerminalOutcome.FAILED_SCORING
                state.diagnostics.prescoring = StageOutcome(
                    status=StageStatus.FAILED,
                    error_code="OMITTED_FROM_PRESCORING",
                    error_message="Candidate summary was not pre-scored by AI client",
                )
            elif cid not in eligible_candidate_ids:
                state.mark_skipped_threshold()
            elif cid not in top_candidate_ids:
                rank = next(
                    (
                        idx + 1
                        for idx, s in enumerate(prescore_output.scores)
                        if s.candidate_id == cid
                    ),
                    999,
                )
                state.mark_skipped_top_k(rank=rank)
            else:
                rank = next(
                    (
                        idx + 1
                        for idx, s in enumerate(prescore_output.scores)
                        if s.candidate_id == cid
                    ),
                    1,
                )
                state.mark_selected(rank=rank)

        # Count metrics directly from the transient state coordinator
        matched_candidate_count = sum(
            1
            for c in context.candidates.values()
            if c.acquisition == StageStatus.SUCCESS
        )
        eligible_candidate_count = sum(
            1
            for c in context.candidates.values()
            if c.prescoring == StageStatus.SUCCESS
            and c.terminal_outcome != CandidateTerminalOutcome.SKIPPED_THRESHOLD
        )
        selected_candidate_count = sum(
            1
            for c in context.candidates.values()
            if c.terminal_outcome == CandidateTerminalOutcome.PENDING
        )

        if selected_candidate_count == 0:
            await self.repository.delete_stale_candidate_scores_and_pipelines(
                job_description_id=job_description_id,
                active_candidate_ids=[],
            )
            await self._transition_to_active_if_needed(job_description_id)
            final_report = self._generate_pipeline_report(context, api_returned_count=0)
            logger.info(final_report)
            is_incomplete = data.k > 0
            warning_reason = "INSUFFICIENT_QUALIFIED" if is_incomplete else None
            warning_message = (
                f"Only {eligible_candidate_count} candidates satisfied the required "
                "criteria. "
                "The remaining candidates did not meet the qualification threshold."
            ) if is_incomplete else None
            return PipelineExecutionResponse(
                stage="completed",
                matched_candidate_count=matched_candidate_count,
                eligible_candidate_count=eligible_candidate_count,
                selected_candidate_count=0,
                top_k=data.k,
                candidates=[],
                is_shortlist_incomplete=is_incomplete,
                warning_reason=warning_reason,
                warning_message=warning_message,
            )

        await progress_reporter.update_stage("SYNCHRONIZING")

        # 7. Pass selected candidate IDs to CandidateSynchronizationService
        # (returns result batch)
        sync_result = await self.synchronization_service.synchronize_candidates(
            top_candidate_ids
        )

        # ScoringService centralizes applying synchronization mutations:
        for cid in top_candidate_ids:
            if cid in context.candidates:
                state = context.candidates[cid]
                res_item = sync_result.results.get(cid)
                if res_item and res_item.success:
                    state.mark_synchronization_success(duration_ms=res_item.duration_ms)
                elif res_item:
                    state.mark_synchronization_failed(
                        error_code=res_item.error_code or "SYNC_FAILED",
                        error_message=res_item.error_message
                        or "Unknown synchronization failure",
                        duration_ms=res_item.duration_ms,
                    )
                else:
                    state.mark_synchronization_failed(
                    error_code="SYNC_OMITTED",
                    error_message=(
                        "Sourcing service failed to process "
                        "candidate profile"
                    ),
                    duration_ms=0.0,
                )

        # 8. Load the selected Candidate ORM objects from local DB
        db_candidates = await self.repository.get_candidates_by_ids(top_candidate_ids)
        candidate_lookup = {c.id: c for c in db_candidates}

        await progress_reporter.update_stage("DEEP_SCORING")

        # 9. Execute deep scoring on the selected candidates, passing the coordinator
        # context
        deep_score_output = await self.score_candidates_for_job_description(
            job_description_id,
            current_user,
            candidate_ids=top_candidate_ids,
            context=context,
        )

        print("\n" + "=" * 40 + "\nDeep Score Output\n" + "=" * 40)
        for idx, deep_score in enumerate(deep_score_output.scores):
            c_name = (
                candidate_lookup[deep_score.candidate_id].full_name
                if deep_score.candidate_id in candidate_lookup
                else "Unknown"
            )
            print(f"{idx + 1}. Name: {c_name} (ID: {deep_score.candidate_id})")
            print(

                    f"   Final Score: {deep_score.final_score} | "
                    f"Confidence: {deep_score.confidence}%"

            )
            print(
                f"   Breakdown -> Skills: {deep_score.skills_score} | "
                f"Exp: {deep_score.experience_score} | "
                f"Recency: {deep_score.recency_score} | "
                f"Role Fit: {deep_score.role_fit_score} | "
                f"Edu: {deep_score.education_score}"
            )
            print(f"   Matched Mandatory Skills: {deep_score.matched_mandatory_skills}")
            print(f"   Missing Mandatory Skills: {deep_score.missing_mandatory_skills}")
            explanation_summary = (
                deep_score.explanation.get("summary")
                if isinstance(deep_score.explanation, dict)
                else getattr(deep_score.explanation, "summary", "")
            )
            print(f"   Explanation Summary: {explanation_summary}")
            print("-" * 20)
        print("=" * 40 + "\n")

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
            score.candidate_id: score for score in deep_score_output.scores
        }

        candidates = [
            self._build_pipeline_candidate_result(
                candidate=candidate_lookup[candidate_id],
                prescore_rank=prescore_lookup[candidate_id][0],
                prescore_score=prescore_lookup[candidate_id][1],
                score=deep_score_lookup[candidate_id],
            )
            for candidate_id in top_candidate_ids
            if candidate_id in candidate_lookup and candidate_id in deep_score_lookup
        ]

        candidates.sort(
            key=lambda candidate: (
                candidate.final_score or 0,
                -(candidate.prescore_rank or 0),
            ),
            reverse=True,
        )

        api_returned_count = len(candidates)
        final_report = self._generate_pipeline_report(context, api_returned_count)
        logger.info(final_report)

        # Invariant Assertion Checks (limited only to selected pool)
        completed_count = sum(
            1
            for c in context.candidates.values()
            if c.terminal_outcome == CandidateTerminalOutcome.SUCCESS
        )
        failed_count = sum(
            1
            for c in context.candidates.values()
            if c.terminal_outcome
            in (
                CandidateTerminalOutcome.FAILED_SYNCHRONIZATION,
                CandidateTerminalOutcome.FAILED_SCORING,
                CandidateTerminalOutcome.FAILED_PERSISTENCE,
            )
            and c.metrics.prescore_rank is not None
            and c.metrics.prescore_rank <= data.k
        )

        inv1 = selected_candidate_count == (completed_count + failed_count)
        inv2 = completed_count == api_returned_count

        if not (inv1 and inv2):
            discrepancy_msg = (
                "Pipeline Consistency Discrepancy Found!\n"
                "Assertion Invariant 1 "
                "(Selected == Completed + Failed): "
                f"{inv1} (Selected: {selected_candidate_count}, "
                f"Completed: {completed_count}, "
                f"Failed: {failed_count})\n"
                "Assertion Invariant 2 "
                "(Completed == API Returned): "
                f"{inv2} (Completed: {completed_count}, "
                f"API Returned: {api_returned_count})"
            )
            logger.error(discrepancy_msg)

        is_shortlist_incomplete = len(candidates) < data.k
        warning_reason = None
        warning_message = None
        if is_shortlist_incomplete:
            if eligible_candidate_count < data.k:
                warning_reason = "INSUFFICIENT_QUALIFIED"
                warning_message = (
                    f"Only {eligible_candidate_count} candidates satisfied "
                    "the required criteria. "
                    "The remaining candidates did not meet the qualification threshold."
                )
            else:
                warning_reason = "EVALUATION_FAILURE"
                warning_message = (
                    f"Only {len(candidates)} candidates successfully "
                    "completed the evaluation. "
                    "Some selected candidates could not be processed due to temporary "
                    "evaluation failures. Try rescoring again later."
                )

        return PipelineExecutionResponse(
            stage="completed",
            matched_candidate_count=matched_candidate_count,
            eligible_candidate_count=eligible_candidate_count,
            selected_candidate_count=api_returned_count,
            top_k=data.k,
            candidates=candidates,
            is_shortlist_incomplete=is_shortlist_incomplete,
            warning_reason=warning_reason,
            warning_message=warning_message,
        )

    def _generate_pipeline_report(
        self, context: PipelineExecutionContext, api_returned_count: int
    ) -> str:
        from src.schemas.pipeline_candidate_state import (
            CandidateTerminalOutcome,
            StageStatus,
        )

        selected_candidates = [
            c
            for c in context.candidates.values()
            if c.terminal_outcome
            in (
                CandidateTerminalOutcome.SUCCESS,
                CandidateTerminalOutcome.FAILED_SYNCHRONIZATION,
                CandidateTerminalOutcome.FAILED_SCORING,
                CandidateTerminalOutcome.FAILED_PERSISTENCE,
            )
        ]
        selected_ids = {c.candidate_id for c in selected_candidates}
        selected_count = len(selected_candidates)

        matched_count = sum(
            1
            for c in context.candidates.values()
            if c.acquisition == StageStatus.SUCCESS
        )
        eligible_count = sum(
            1
            for c in context.candidates.values()
            if c.prescoring == StageStatus.SUCCESS
            and c.terminal_outcome != CandidateTerminalOutcome.SKIPPED_THRESHOLD
        )

        sync_success = sum(
            1
            for c in context.candidates.values()
            if c.synchronization == StageStatus.SUCCESS
            and c.candidate_id in selected_ids
        )
        sync_failed = sum(
            1
            for c in context.candidates.values()
            if c.synchronization == StageStatus.FAILED
            and c.candidate_id in selected_ids
        )

        deep_success = sum(
            1
            for c in context.candidates.values()
            if c.scoring == StageStatus.SUCCESS and c.candidate_id in selected_ids
        )
        deep_failed = sum(
            1
            for c in context.candidates.values()
            if c.scoring == StageStatus.FAILED and c.candidate_id in selected_ids
        )

        persist_success = sum(
            1
            for c in context.candidates.values()
            if c.persistence == StageStatus.SUCCESS and c.candidate_id in selected_ids
        )
        # persist_failed = sum(
        #     1
        #     for c in context.candidates.values()
        #     if c.persistence == StageStatus.FAILED and c.candidate_id in selected_ids
        # )

        # Check validation invariants
        inv1 = selected_count == (sync_success + sync_failed)
        inv2 = sync_success == (deep_success + deep_failed)
        inv3 = deep_success == persist_success
        inv4 = persist_success == api_returned_count

        consistency_passed = all([inv1, inv2, inv3, inv4])
        status_str = "PASSED" if consistency_passed else "FAILED"

        reasons = []
        if not inv1:
            reasons.append(

                    f"Selected count ({selected_count}) != "
                    f"Sync Success ({sync_success}) + "
                    f"Sync Failed ({sync_failed})"

            )

        if not inv2:
            reasons.append(

                    f"Sync Success ({sync_success}) != "
                    f"Deep Score Success ({deep_success}) + "
                    f"Deep Score Failed ({deep_failed})"

            )

        if not inv3:
            reasons.append(

                    f"Deep Score Success ({deep_success}) != "
                    f"Persist Success ({persist_success})"

            )

        if not inv4:
            reasons.append(

                    f"Persist Success ({persist_success}) != "
                    f"API Returned Count ({api_returned_count})"

            )

        reason_str = (
            "\n".join(reasons)
            if reasons
            else (
                "All database invariants and API serialization mappings "
                "are fully consistent."
            )
        )

        report = f"""
==================================================
PIPELINE EXECUTION REPORT
==================================================
Pipeline Execution ID: {context.execution_id}
Job Description ID: {context.job_description_id}
Recruiter ID: {context.recruiter_id}

Matched: {matched_count}
Eligible: {eligible_count}
Selected: {selected_count}

Synchronization
  Success: {sync_success}
  Failed: {sync_failed}

Deep Scoring
  Success: {deep_success}
  Failed: {deep_failed}

Persistence
  CandidateJobScore: {persist_success}
  Pipeline Entries: {persist_success}
  API Response: {api_returned_count}

Consistency: {status_str}
Reason:
{reason_str}
==================================================
"""
        return report

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
                matched_mandatory_skills=score.matched_mandatory_skills,
                matched_optional_skills=score.matched_optional_skills,
                missing_mandatory_skills=score.missing_mandatory_skills,
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
            raise ScoringBaseException(
                message="Access denied",
                details="Only hiring managers can access this endpoint.",
                status_code=403,
            )

        job_description = await self.repository.get_job_description_by_id(
            job_description_id
        )
        if (
            not job_description
            or job_description.hiring_manager_id != current_user.user_id
        ):
            raise ScoringBaseException(
                message="Access denied",
                details="Hiring manager does not own this campaign.",
                status_code=403,
            )

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
        if job_description is None:
            raise ValueError(f"Job Description with ID {job_description_id} not found")

        compressed_jd = self._build_compressed_job_description(
            job_description,
        )

        print("\n" + "=" * 40 + "\nPrescoring LLM Input\n" + "=" * 40)
        print(f"Compressed JD Profile:\n{compressed_jd.profile_text}\n")
        print("Compressed Candidates Profiles sent to LLM:")
        for cc in candidates:
            print(
                f"- ID: {cc.candidate_id}\nProfile Text:\n{cc.profile_text}\n"
                + "-" * 20
            )
        print("=" * 40 + "\n")

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
        if job_description is None:
            raise ValueError(f"Job Description with ID {job_description_id} not found")

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
            candidate_title = (candidate.current_title or "").lower()
            experience_years = candidate.total_experience_months / 12

            mandatory_matches = len(
                mandatory_skills & candidate_skills,
            )
            optional_matches = len(
                optional_skills & candidate_skills,
            )

            matches_experience = experience_years >= max(
                job_description.min_experience - 1, 0
            )
            matches_role_hint = (
                any(term in candidate_title for term in job_title_terms)
                if job_title_terms
                else False
            )

            has_relevant_skills = (
                mandatory_matches > 0 or optional_matches > 0 or not mandatory_skills
            )

            if not matches_experience:
                continue

            if not has_relevant_skills and not matches_role_hint:
                continue

            sourced_candidates.append(
                candidate,
            )
        print("\n" + "=" * 40 + "\nSourced Candidates\n" + "=" * 40)
        for idx, candidate in enumerate(sourced_candidates):
            print(
                f"{idx + 1}. Name: {candidate.full_name} | "
                f"ID: {candidate.id} | "
                f"Email: {candidate.email} | "
                f"Exp: {candidate.total_experience_months} months"
            )
        print("=" * 40 + "\n")

        return sourced_candidates

    def _extract_candidate_skill_names(
        self,
        candidate: Candidate,
    ) -> set[str]:
        skill_names = {skill.skill_name.strip().lower() for skill in candidate.skills}

        for experience in candidate.experiences:
            skill_names.update(
                skill.skill_name.strip().lower() for skill in experience.skills
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
        pipeline_entry: Pipeline,
    ) -> PipelineSnapshotResponse:
        return PipelineSnapshotResponse(
            id=pipeline_entry.id,
            candidate_id=pipeline_entry.candidate_id,
            jd_id=pipeline_entry.jd_id,
            stage=pipeline_entry.stage,
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
            created_at=pipeline_entry.created_at,
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
            skill.skill_name for skill in job_description.skills if skill.is_mandatory
        ]

        optional_skills = [
            skill.skill_name
            for skill in job_description.skills
            if not skill.is_mandatory
        ]

        exp_range = (
            f"{job_description.min_experience}+"
            if job_description.max_experience is None
            else f"{job_description.min_experience}-{job_description.max_experience}"
        )
        profile_text = (
            f"Title: {job_description.title}\n"
            f"Experience: {exp_range} years\n"
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
        global_skills = ", ".join(skill.skill_name for skill in candidate.skills)

        experience_titles = [experience.title for experience in candidate.experiences]

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
            total_experience_months=(candidate.total_experience_months),
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

    async def _transition_to_active_if_needed(self, job_description_id: UUID) -> None:
        active_status_id = await self.repository.get_status_by_code("ACTIVE")
        if active_status_id:
            await self.repository.update_job_description_status(
                job_description_id,
                active_status_id,
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
        if job_description is None:
            raise ValueError(f"Job Description with ID {job_description_id} not found")

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
            raise ScoringBaseException(
                message="Access denied",
                details="Only recruiters are allowed to share shortlists.",
                status_code=403,
            )

        # 1. Validate that all submitted candidates already exist in the
        # pipeline for this job description
        invalid_ids = await self.repository.validate_candidates_belong_to_job(
            job_description_id,
            candidate_ids,
        )
        if invalid_ids:
            invalid_str = ", ".join(str(cid) for cid in invalid_ids)
            raise ScoringBaseException(
                message="Validation failed",
                details=(
                    "Invalid candidate IDs for this job description: "
                    f"{invalid_str}"
                ),
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
        logger.info(
            (
                "Shortlist shared: JobDescription %s successfully "
                "committed sharing for %s candidates"
            ),
            job_description_id,
            shared_count,
        )

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
                frontend_base = (
                    settings.ALLOWED_ORIGINS[0]
                    if settings.ALLOWED_ORIGINS
                    else "http://localhost:5173"
                )
                absolute_target_url = (
                    f"{frontend_base}/hm/shared-campaigns/{job_description_id}"
                )

                email_body = (
                    f"Hello {jd.hiring_manager.name},\n\n"
                    f"{jd.recruiter.name} has shared a new candidate shortlist for "
                    f'"{jd.title}" with you.\n\n'
                    f"There are {len(candidate_ids)} recommended candidates "
                    "ready for your review."
                )

                email_html = get_generic_email_html(
                    title="New Shortlist Shared",
                    body=email_body,
                    action_text="Review Candidates",
                    action_url=absolute_target_url,
                )

                await notification_service.notify(
                    user=jd.hiring_manager,
                    notification_type=NotificationType.SHORTLIST_SHARED,
                    title="New Candidate Shortlist Shared",
                    message=(
                        f'A new shortlist for "{jd.title}" has been shared with you '
                        f"by {jd.recruiter.name}. "
                        "Review the recommended candidates."
                    ),
                    target_url=f"/hm/shared-campaigns/{job_description_id}",
                    metadata={
                        "job_description_id": str(job_description_id),
                        "candidate_count": len(candidate_ids),
                    },
                    send_in_app=True,
                    send_email=True,
                    email_subject=f"New candidate shortlist for {jd.title}",
                    email_html=email_html,
                )
                logger.info(
                    (
                        "Hiring Manager notification created and email sent "
                        "for shortlist share on campaign %s"
                    ),
                    job_description_id,
                )
            elif not jd:
                logger.warning(
                    (
                        "Could not send shortlist share notification: "
                        "Job description %s not found."
                    ),
                    job_description_id,
                )
            else:
                logger.warning(
                    (
                        "Could not send shortlist share notification: "
                        "Job description %s has no assigned Hiring Manager."
                    ),
                    job_description_id,
                )
        except Exception as e:
            # Notification failures must NEVER rollback or fail the shortlist sharing
            # transaction
            logger.exception(
                (
                    "Hiring Manager email failed: Failed to send "
                    "shortlist shared notification: %s"
                ),
                e,
            )

        return shared_count

    async def get_hm_shared_campaigns(
        self,
        current_user: AuthenticatedUserContext,
    ) -> list[HMCampaignResponse]:
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(
                message="Access denied",
                details="Only hiring managers can view shared campaigns.",
                status_code=403,
            )

        jds = await self.repository.get_hm_campaigns(current_user.user_id)

        from src.data.models.postgres.pipeline import HiringManagerDecision

        response = []
        for jd in jds:
            shared_entries = [
                p for p in jd.pipeline_entries if p.shared_with_hiring_manager
            ]

            # calculate counts
            shared_candidate_count = len(shared_entries)
            accepted_candidate_count = sum(
                1
                for p in shared_entries
                if p.hm_decision == HiringManagerDecision.INTERVIEW_SENT
            )
            rejected_candidate_count = sum(
                1
                for p in shared_entries
                if p.hm_decision == HiringManagerDecision.REJECTED
            )
            pending_candidate_count = sum(
                1
                for p in shared_entries
                if p.hm_decision == HiringManagerDecision.PENDING
            )

            # calculate latest shared date
            shared_dates = [
                p.shared_at for p in shared_entries if p.shared_at is not None
            ]
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
            raise ScoringBaseException(
                message="Access denied",
                details="Only hiring managers can view shared candidates.",
                status_code=403,
            )

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
                hm_decision=pipe.hm_decision or HiringManagerDecision.PENDING,
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
        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(
                message="Access denied",
                details="Only hiring managers can submit candidate reviews.",
                status_code=403,
            )

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
                details=(
                    "Failed to submit review. Candidate may not be shared, "
                    "or job description is not assigned to you."
                ),
                status_code=400,
            )

        # Publish CANDIDATE_REVIEWED event (stub/log for future integration)
        print(
            f"[EVENT] CANDIDATE_REVIEWED: Candidate {candidate_id} "
            f"reviewed for JobDescription {job_description_id}. "
            f"Decision: {decision}"
        )

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

        if current_user.role != UserRole.hiring_manager:
            raise ScoringBaseException(
                message="Access denied",
                details="Only hiring managers can schedule interviews.",
                status_code=403,
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
                details=("Hiring manager does not own this campaign or "
                    "job description not found."
                    ),
                status_code=403,
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
                status_code=403,
            )

        # 3. Validate candidate email exists
        candidate = await self.repository.get_candidate_by_id(candidate_id)
        if not candidate:
            raise CandidateNotFound(
                details="Candidate could not be found", error_code="CANDIDATE_NOT_FOUND"
            )
        if not candidate.email or not candidate.email.strip():
            raise ScoringBaseException(
                message="Validation failed",
                details=(
                    "Candidate email address is missing. "
                    "Cannot send interview invitation."
                    ),
                status_code=400,
            )

        # 4. Dispatch Email to Candidate
        notification_service = NotificationService(self.repository.db)

        date_str = interview_datetime.strftime("%B %d, %Y")
        time_str = interview_datetime.strftime("%I:%M %p")

        candidate_body = (
            f"Hello {candidate.full_name},\n\n"
            f"Congratulations! You have been selected for an interview for the "
            f'"{jd.title}" role.\n\n'
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
            action_url=interview_link,
        )

        # This will raise exception if Brevo client fails
        await notification_service.send_email(
            recipient_email=candidate.email,
            recipient_name=candidate.full_name,
            subject=f"Interview Invitation – {jd.title}",
            html_content=candidate_html,
        )
        logger.info(
            "Hiring Manager email sent successfully to candidate %s", candidate.email
        )

        # 5. Only AFTER successful email dispatch, update pipeline in DB
        pipeline_entry.hm_decision = HiringManagerDecision.INTERVIEW_SENT
        pipeline_entry.interview_link = interview_link
        pipeline_entry.interview_datetime = interview_datetime
        pipeline_entry.interview_timezone = timezone
        pipeline_entry.interview_message = message
        pipeline_entry.interview_sent_at = datetime.now(UTC)

        await self.repository.db.commit()
        logger.info(
            "Pipeline status updated to INTERVIEW_SENT for candidate %s on campaign %s",
            candidate_id,
            job_description_id,
        )

        # 6. Recruiter Notification (best-effort)
        try:
            res_hm = await self.repository.db.execute(
                select(User).where(User.id == current_user.user_id)
            )
            hm_user = res_hm.scalar_one_or_none()
            hm_name = hm_user.name if hm_user else "Hiring Manager"

            recruiter_user = jd.recruiter
            frontend_base = (
                settings.ALLOWED_ORIGINS[0]
                if settings.ALLOWED_ORIGINS
                else "http://localhost:5173"
            )

            recruiter_body = (
                f"Hello {recruiter_user.name},\n\n"
                f"{hm_name} has scheduled an interview with "
                f'{candidate.full_name} for your job description "{jd.title}".\n\n'
                "Interview Details:\n"
                f"- **Date & Time:** {date_str} at {time_str} ({timezone})\n"
                f"- **Link:** {interview_link}\n"
            )
            recruiter_html = get_generic_email_html(
                title="Interview Scheduled",
                body=recruiter_body,
                action_text="View Candidate Detail",
                action_url=f"{frontend_base}/recruiter/job-descriptions/{job_description_id}/candidates/{candidate_id}",
            )

            await notification_service.notify(
                user=recruiter_user,
                notification_type=NotificationType.INTERVIEW_INVITATION,
                title="Interview Scheduled",
                message=(
                    f'{hm_name} has scheduled an interview with '
                    f'{candidate.full_name} for "{jd.title}".'
                ),
                target_url=(
                    f"/recruiter/job-descriptions/{job_description_id}/"
                    f"candidates/{candidate_id}"
                ),
                metadata={
                    "job_description_id": str(job_description_id),
                    "candidate_id": str(candidate_id),
                    "candidate_name": candidate.full_name,
                },
                send_in_app=True,
                send_email=True,
                email_subject=f"Interview scheduled for {candidate.full_name}",
                email_html=recruiter_html,
            )
            logger.info(
                (
                    "Hiring Manager notification created and Recruiter "
                    "email sent successfully for interview on candidate %s"
                ),
                candidate_id,
            )
        except Exception as recruiter_notify_err:
            logger.warning(
                "Failed to send recruiter notification for interview invitation: %s",
                str(recruiter_notify_err),
            )

        return pipeline_entry

    async def close(self) -> None:
        """Close any active resources, clients, or connection pools."""
        if hasattr(self, "search_client") and self.search_client:
            client = self.search_client
            self.search_client = None
            try:
                await client.close()
            except Exception as e:
                logger.warning("Error during search client cleanup: %s", str(e))
