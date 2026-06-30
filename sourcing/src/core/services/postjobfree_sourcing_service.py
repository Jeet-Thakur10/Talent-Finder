import asyncio
import random
import urllib.parse

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
from src.core.services.search_query_optimizer import SearchQueryOptimizer


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

        attempts_history: list[SearchAttempt] = []
        best_resumes_found = 0
        no_improvement_count = 0

        # Load existing candidates matching the original request
        existing_candidates = await self._candidate_service.search_candidates(
            request,
        )
        existing_count = len(existing_candidates)
        existing_ids = {c.candidate_id for c in existing_candidates}
        candidates_remaining = max(request.required_candidates - existing_count, 0)

        print(f"\n[PostJobFreeSourcingService] Starting Adaptive Sourcing Loop:")
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
                print(f"  [PostJobFreeSourcingService] Approaching timeout limit ({elapsed:.1f}s / {settings.SOURCING_LOOP_TIMEOUT_SECONDS}s). Terminating loop early.")
                break

            try:
                # Get optimized query from the strategy-driven optimizer
                optimized_req, reason = await self._optimizer.get_optimized_request(
                    request,
                    attempts_history,
                )
            except Exception as opt_err:
                print(f"  [Attempt {current_attempt}] Strategy optimization failed: {opt_err}")
                break

            # Generate the provider request
            search_request = self.generate_postjobfree_search_request(
                optimized_req,
            )

            import urllib.parse
            params = {
                "q": search_request.required_words,
                "n": search_request.excluded_words,
                "t": search_request.title_words,
                "d": search_request.resume_text_words,
                "r": 10,
            }
            url = f"https://www.postjobfree.com/resumes?{urllib.parse.urlencode(params)}"

            print(f"\n" + "-" * 50)
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
                        print(f"  [PostJobFreeSourcingService] Approaching timeout limit ({elapsed:.1f}s / {settings.SOURCING_LOOP_TIMEOUT_SECONDS}s). Stopping attempt loop.")
                        break

                    # Stopping condition check during loop
                    current_missing = max(request.required_candidates - len(existing_ids), 0)
                    if current_missing == 0:
                        print("  Reached target candidates count mid-scrape. Stopping attempt loop.")
                        break

                    print(f"  -> Scraping URL: {result.resume_url}")
                    try:
                        resume_html = await self._client.get_resume_page(
                            result.resume_url,
                        )
                        resume = self._resume_parser.parse(
                            html=resume_html,
                            source_url=result.resume_url,
                        )
                        extraction_result = self._extraction_agent.extract(
                            resume.raw_resume_text,
                        )

                        if not extraction_result.success:
                            print(f"     [Scrape] Rejected: extraction failed: {extraction_result.error}")
                            continue

                        stored_candidate = await self._candidate_service.create_candidate(
                            candidate=extraction_result.payload,
                            resume_text=resume.raw_resume_text,
                            source_type="postjobfree",
                        )
                        await self._candidate_service.commit()
                        candidates_persisted_this_attempt += 1

                        if stored_candidate.id in request.exclude_candidate_ids:
                            print(f"     [Scrape] Excluded: candidate ID in exclude_candidate_ids.")
                            continue

                        if stored_candidate.id not in existing_ids:
                            new_candidates_persisted += 1
                            existing_ids.add(stored_candidate.id)
                            print(f"     [Scrape] Successfully stored new unique candidate: {stored_candidate.id}")
                        else:
                            print(f"     [Scrape] Duplicate candidate ID: {stored_candidate.id}")

                        # Delay between requests
                        sleep_seconds = random.randint(15, 25)
                        print(f"     Sleeping for {sleep_seconds} seconds...")
                        await asyncio.sleep(sleep_seconds)

                    except Exception as exc:
                        print(f"     [Scrape] Failed scraping {result.resume_url}: {exc}")

            # Recompute remaining needed candidates
            candidates_remaining = max(request.required_candidates - len(existing_ids), 0)

            # Evaluate improvement stopping condition
            if resumes_found > best_resumes_found or new_candidates_persisted > 0:
                no_improvement_count = 0
                best_resumes_found = max(best_resumes_found, resumes_found)
                print(f"  Attempt {current_attempt} improved the candidate pool (New unique persisted: {new_candidates_persisted}, Resumes: {resumes_found}).")
            else:
                no_improvement_count += 1
                print(f"  Attempt {current_attempt} failed to improve the candidate pool. Consecutive no-improvement count: {no_improvement_count}.")

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
            print(f"\n==================================================")
            print(f"SEARCH ATTEMPT SUMMARY:")
            print(f"  Attempt Number: {current_attempt}")
            print(f"  Generated Query URL: {url}")
            print(f"  Title Used: '{optimized_req.title}'")
            print(f"  Skills Used: {optimized_req.skills}")
            print(f"  Reason for query adjustments: {reason}")
            print(f"  Resumes Found: {resumes_found}")
            print(f"  Candidates Persisted: {candidates_persisted_this_attempt}")
            print(f"  New Unique Candidates Persisted: {new_candidates_persisted}")
            print(f"  Candidates Remaining: {candidates_remaining}")
            print(f"==================================================\n")

            if no_improvement_count >= settings.MAX_CONSECUTIVE_NO_IMPROVEMENT:
                print(f"[PostJobFreeSourcingService] Terminating loop early: {no_improvement_count} consecutive no-improvement attempts.")
                break

        # Log final loop status and stop reason
        stop_reason = "TARGET_SATISFIED" if candidates_remaining == 0 else (
            "NO_IMPROVEMENT" if no_improvement_count >= settings.MAX_CONSECUTIVE_NO_IMPROVEMENT else "MAX_ATTEMPTS_REACHED"
        )
        print(f"\n[PostJobFreeSourcingService] Sourcing Loop Complete:")
        print(f"  Stopping Reason: {stop_reason}")
        print(f"  Total Attempts: {current_attempt}")
        print(f"  Final Candidates Remaining: {candidates_remaining}")
        print()
