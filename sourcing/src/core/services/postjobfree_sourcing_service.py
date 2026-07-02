import asyncio
import logging
import random
import urllib.parse

import httpx

from src.config.settings import settings
from src.control.agents.resume_extraction_agent import (
    ResumeExtractionAgent,
)
from src.core.services.candidate_service import (
    CandidateService,
)
from src.core.services.postjobfree_resume_parser import (
    PostJobFreeResumeParser,
)
from src.core.services.postjobfree_search_parser import (
    PostJobFreeSearchParser,
)
from src.core.services.search_query_optimizer import SearchQueryOptimizer
from src.handlers.http_clients.postjobfree_client import (
    PostJobFreeClient,
)
from src.schemas.candidate_search_request import (
    CandidateSearchRequest,
)
from src.schemas.postjobfree_search_request import (
    PostJobFreeSearchRequest,
)
from src.schemas.search_attempt import SearchAttempt

logger = logging.getLogger(__name__)


class PostJobFreeSourcingService:
    def __init__(
        self,
        client: PostJobFreeClient,
        extraction_agent: ResumeExtractionAgent,
        candidate_service: CandidateService,
        optimizer: SearchQueryOptimizer,
    ) -> None:
        self._client = client
        self._extraction_agent = extraction_agent
        self._candidate_service = candidate_service
        self._optimizer = optimizer

        self._search_parser = PostJobFreeSearchParser()
        self._resume_parser = PostJobFreeResumeParser()

    def generate_postjobfree_search_request(
        self,
        request: CandidateSearchRequest,
    ) -> PostJobFreeSearchRequest:

        return PostJobFreeSearchRequest(
            title_words=request.title,
            required_words=" ".join(
                skill
                for skill in request.skills
                if skill.strip()
            ),
            resume_text_words=request.title,
            excluded_words="",
        )

    async def source_candidates(
        self,
        request: CandidateSearchRequest,
    ) -> None:

        # 1. Pre-generate the optimization plan once at the beginning of
        # the sourcing session
        await self._optimizer.initialize(request)

        plan = self._optimizer.get_plan()
        if plan:
            print("\n================================================")
            print("Recruiter Search Plan")
            print("=====================")
            print(f"Inferred Role:\n{plan.inferred_role}\n")
            print(f"Representative Title:\n{plan.representative_title}\n")
            print(f"Representative Skills:\n{plan.representative_skills}\n")
            print(f"Reasoning:\n{plan.reasoning}")
            print("================================================\n")

        attempts_history: list[SearchAttempt] = []
        best_resumes_found = 0
        no_improvement_count = 0

        # To track executed queries: tuple(title, tuple(sorted_skills))
        seen_queries = set()
        # To track processed resume URLs across attempts
        processed_resume_urls = set()

        # Load existing candidates matching the original request
        existing_candidates = await self._candidate_service.search_candidates(
            request,
        )
        existing_count = len(existing_candidates)
        existing_ids = {c.candidate_id for c in existing_candidates}
        candidates_remaining = max(request.required_candidates - existing_count, 0)

        print("\n[PostJobFreeSourcingService] Starting Adaptive Sourcing Loop:")
        print(f"  Required candidates: {request.required_candidates}")
        print(f"  Existing matching candidates: {existing_count}")
        print(f"  Initial candidates remaining: {candidates_remaining}")

        if candidates_remaining == 0:
            print("  No candidates remaining needed at start. Sourcing skipped.")
            return

        start_time = asyncio.get_event_loop().time()
        current_attempt = 0
        max_attempts = settings.MAX_SOURCING_ATTEMPTS

        while candidates_remaining > 0 and current_attempt < max_attempts:
            current_attempt += 1

            # Check proactive timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > settings.SOURCING_LOOP_TIMEOUT_SECONDS:
                print(
                    "[PostJobFreeSourcingService] Approaching timeout limit "
                    f"({elapsed:.1f}s / "
                    f"{settings.SOURCING_LOOP_TIMEOUT_SECONDS}s). "
                    "Terminating loop early."
                )
                break

            try:
                # Get optimized query from the strategy-driven optimizer
                optimized_req, reason = await self._optimizer.get_optimized_request(
                    request,
                    attempts_history,
                )
            except Exception as opt_err:
                print(
                    f"  [Attempt {current_attempt}] "
                    f"Strategy optimization failed: {opt_err}"
                )
                break

            # Check query deduplication using normalized representation
            normalized_query = (
                optimized_req.title.strip().lower(),
                tuple(sorted(skill.strip().lower() for skill in optimized_req.skills))
            )
            if normalized_query in seen_queries:
                print(
                    f"  [Attempt {current_attempt}] Skipped duplicate query: "
                    f"Title='{optimized_req.title}', Skills={optimized_req.skills}"
                )
                attempt_stat = SearchAttempt(
                    attempt_number=current_attempt,
                    title=optimized_req.title,
                    skills=optimized_req.skills,
                    resumes_found=0,
                    candidates_persisted=0,
                    new_candidates_persisted=0,
                    candidates_remaining=candidates_remaining,
                    reason=f"Skipped duplicate query. (Attempt details: {reason})",
                    query_url="",
                )
                attempts_history.append(attempt_stat)
                continue

            seen_queries.add(normalized_query)

            # Generate the provider request
            search_request = self.generate_postjobfree_search_request(
                optimized_req,
            )

            params = {
                "q": search_request.required_words,
                "n": search_request.excluded_words,
                "t": search_request.title_words,
                "d": search_request.resume_text_words,
                "r": 10,
            }
            url = f"https://www.postjobfree.com/resumes?{urllib.parse.urlencode(params)}"

            print("\n" + "-" * 50)
            print(f"STARTING SEARCH ATTEMPT {current_attempt}")
            print(f"  Title Used: '{optimized_req.title}'")
            print(f"  Skills Used: {optimized_req.skills}")
            print(f"  Query URL: {url}")
            print(f"  Reasoning: {reason}")
            print("-" * 50)

            # Search PostJobFree
            try:
                search_html = await self._client.search_resumes(
                    search_request,
                )
                search_results = self._search_parser.parse(
                    search_html,
                )
            except Exception as e:
                print(f"  [Attempt {current_attempt}] PostJobFree Search Failed: {e}")
                search_results = []

            resumes_found = len(search_results)
            print(f"  Resumes found on PostJobFree: {resumes_found}")

            new_candidates_persisted = 0
            candidates_persisted_this_attempt = 0

            # Scrape matches if found
            if resumes_found > 0:
                for result in search_results:
                    # Check proactive timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > settings.SOURCING_LOOP_TIMEOUT_SECONDS:
                        print(
                            "[PostJobFreeSourcingService] Approaching timeout limit "
                            f"({elapsed:.1f}s / "
                            f"{settings.SOURCING_LOOP_TIMEOUT_SECONDS}s). "
                            "Stopping attempt loop."
                        )
                        break

                    # Stopping condition check during loop
                    current_missing = max(
                        request.required_candidates - len(existing_ids), 0)
                    if current_missing == 0:
                        print(
                            "  Reached target candidates count "
                            "mid-scrape. Stopping attempt loop."
                        )
                        break

                    # Resume URL Deduplication: skip if already processed in this run
                    if result.resume_url in processed_resume_urls:
                        print(
                            "     [Scrape] Skipped duplicate URL "
                            f"(already processed in this run): {result.resume_url}"
                        )
                        continue

                    processed_resume_urls.add(result.resume_url)

                    print(f"  -> Scraping URL: {result.resume_url}\n")
                    try:
                        # 1. Resume download stage
                        print("Downloading resume...\n")
                        try:
                            resume_html = await self._client.get_resume_page(
                                result.resume_url,
                            )
                            print("Resume downloaded successfully.\n")
                        except Exception as exc:
                            if isinstance(
                                exc,
                                (
                                    httpx.TimeoutException,
                                    asyncio.TimeoutError,
                                    TimeoutError,
                                ),
                            ):
                                stage = "Resume download"
                                error_code = "EXTRACTION_TIMEOUT"
                                error_msg = "Resume download request timed out."
                            elif isinstance(exc, httpx.RequestError):
                                stage = "Resume download"
                                error_code = "EXTRACTION_NETWORK"
                                error_msg = (
                                    "Resume download failed due to network issue."
                                )
                            else:
                                stage = "Resume download"
                                error_code = "EXTRACTION_UNKNOWN"
                                error_msg = (
                                    "Resume download failed with unexpected error: "
                                    f"{str(exc)}"
                                )

                            logger.error(
                                "Resume extraction failed during stage: '%s'\n"
                                "Provider: postjobfree\n"
                                "Resume URL: %s\n"
                                "Error Code: %s\n"
                                "Error Message: %s",
                                stage,
                                result.resume_url,
                                error_code,
                                error_msg,
                                exc_info=True
                            )
                            print(f"{error_msg}\n")
                            print("Candidate rejected.\n")
                            continue

                        # 2. HTML parsing stage
                        print("Parsing HTML...\n")
                        try:
                            resume = self._resume_parser.parse(
                                html=resume_html,
                                source_url=result.resume_url,
                            )
                            print("HTML parsed successfully.\n")
                        except Exception as exc:
                            stage = "HTML parsing"
                            error_code = "EXTRACTION_OUTPUT_PARSER"
                            error_msg = f"HTML parsing failed: {str(exc)}"

                            logger.error(
                                "Resume extraction failed during stage: '%s'\n"
                                "Provider: postjobfree\n"
                                "Resume URL: %s\n"
                                "Error Code: %s\n"
                                "Error Message: %s",
                                stage,
                                result.resume_url,
                                error_code,
                                error_msg,
                                exc_info=True
                            )
                            print(f"{error_msg}\n")
                            print("Candidate rejected.\n")
                            continue

                        # 3. Extracting resume text stage
                        print("Extracting resume text...\n")
                        print("Extracted text length:")
                        print(f"{len(resume.raw_resume_text)} characters\n")

                        # 4. Groq extraction stage
                        extraction_result = self._extraction_agent.extract(
                            resume.raw_resume_text,
                            resume_url=result.resume_url,
                        )

                        if not extraction_result.success or extraction_result.payload is None:
                            print(f"{extraction_result.error or 'Payload is None'}\n")
                            print("Candidate rejected.\n")
                            continue

                        # 5. Persistence stage
                        print("Persisting candidate...\n")
                        try:
                            stored_candidate = (
                                await self._candidate_service.create_candidate(
                                    candidate=extraction_result.payload,
                                    resume_text=resume.raw_resume_text,
                                    source_type="postjobfree",
                                )
                            )
                            await self._candidate_service.commit()
                            print("Candidate persisted successfully.\n")
                            candidates_persisted_this_attempt += 1
                        except Exception as exc:
                            stage = "Candidate persistence"
                            error_code = "EXTRACTION_UNKNOWN"
                            error_msg = f"Candidate persistence failed: {str(exc)}"

                            logger.error(
                                "Resume extraction failed during stage: '%s'\n"
                                "Provider: postjobfree\n"
                                "Resume URL: %s\n"
                                "Error Code: %s\n"
                                "Error Message: %s",
                                stage,
                                result.resume_url,
                                error_code,
                                error_msg,
                                exc_info=True
                            )
                            print(f"{error_msg}\n")
                            print("Candidate rejected.\n")
                            continue

                        if stored_candidate.id in request.exclude_candidate_ids:
                            print(
                                "     [Scrape] Excluded: candidate ID "
                                "in exclude_candidate_ids."
                            )
                            continue

                        if stored_candidate.id not in existing_ids:
                            new_candidates_persisted += 1
                            existing_ids.add(stored_candidate.id)
                            print(
                                "     [Scrape] Successfully stored new "
                                f"unique candidate: {stored_candidate.id}"
                            )
                        else:
                            print(
                                "     [Scrape] Duplicate candidate ID: "
                                f"{stored_candidate.id}"
                            )

                        # Delay between requests
                        sleep_seconds = random.randint(10, 15)
                        print(f"     Sleeping for {sleep_seconds} seconds...")
                        await asyncio.sleep(sleep_seconds)

                    except Exception as exc:
                        logger.error(
                            "Unexpected failure in resume scraping pipeline\n"
                            "Provider: postjobfree\n"
                            "Resume URL: %s\n"
                            "Error Code: EXTRACTION_UNKNOWN\n"
                            "Error Message: %s",
                            result.resume_url,
                            str(exc),
                            exc_info=True
                        )
                        print(f"Unexpected error: {exc}\n")
                        print("Candidate rejected.\n")

            # Recompute remaining needed candidates
            candidates_remaining = max(
                request.required_candidates - len(existing_ids), 0)

            # Evaluate improvement stopping condition
            if resumes_found > best_resumes_found or new_candidates_persisted > 0:
                no_improvement_count = 0
                best_resumes_found = max(best_resumes_found, resumes_found)
                print(
                    f"  Attempt {current_attempt} improved the candidate pool "
                    f"(New unique persisted: {new_candidates_persisted}, "
                    f"Resumes: {resumes_found})."
                )
            else:
                no_improvement_count += 1
                print(
                    f"  Attempt {current_attempt} failed to improve the candidate "
                    f"pool. Consecutive no-improvement count: "
                    f"{no_improvement_count}."
                )

            # Record stats in attempt history
            attempt_stat = SearchAttempt(
                attempt_number=current_attempt,
                title=optimized_req.title,
                skills=optimized_req.skills,
                resumes_found=resumes_found,
                candidates_persisted=candidates_persisted_this_attempt,
                new_candidates_persisted=new_candidates_persisted,
                candidates_remaining=candidates_remaining,
                reason=reason,
                query_url=url,
            )
            attempts_history.append(attempt_stat)

            # Log search attempt details clearly
            print("\n==================================================")
            print("SEARCH ATTEMPT SUMMARY:")
            print(f"  Attempt Number: {current_attempt}")
            print(f"  Generated Query URL: {url}")
            print(f"  Title Used: '{optimized_req.title}'")
            print(f"  Skills Used: {optimized_req.skills}")
            print(f"  Reason for query adjustments: {reason}")
            print(f"  Resumes Found: {resumes_found}")
            print(f"  Candidates Persisted: {candidates_persisted_this_attempt}")
            print(f"  New Unique Candidates Persisted: {new_candidates_persisted}")
            print(f"  Candidates Remaining: {candidates_remaining}")
            print("==================================================\n")

            if no_improvement_count >= settings.MAX_CONSECUTIVE_NO_IMPROVEMENT:
                print(
                    "[PostJobFreeSourcingService] Terminating loop early: "
                    f"{no_improvement_count} consecutive no-improvement attempts."
                )
                break

        # Log final loop status and stop reason
        stop_reason = (
            "TARGET_SATISFIED"
            if candidates_remaining == 0
            else (
                "NO_IMPROVEMENT"
                if no_improvement_count >= settings.MAX_CONSECUTIVE_NO_IMPROVEMENT
                else "MAX_ATTEMPTS_REACHED"
            )
        )
        print("\n[PostJobFreeSourcingService] Sourcing Loop Complete:")
        print(f"  Stopping Reason: {stop_reason}")
        print(f"  Total Attempts: {current_attempt}")
        print(f"  Final Candidates Remaining: {candidates_remaining}")
        print()
