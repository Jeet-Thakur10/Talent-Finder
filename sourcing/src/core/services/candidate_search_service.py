from src.core.services.candidate_service import (
    CandidateService,
)
from src.core.services.postjobfree_sourcing_service import (
    PostJobFreeSourcingService,
)
from src.schemas.candidate_search_request import (
    CandidateSearchRequest,
)
from src.schemas.candidate_search_response import (
    CandidateSearchResponse,
)


class CandidateSearchService:
    def __init__(
        self,
        candidate_service: CandidateService,
        sourcing_service: PostJobFreeSourcingService,
    ) -> None:
        self._candidate_service = candidate_service
        self._sourcing_service = sourcing_service

    async def search_or_source_candidates(
        self,
        request: CandidateSearchRequest,
    ) -> CandidateSearchResponse:

        print(f"\n[SourcingService] Received CandidateSearchRequest:")
        print(f"  title: {request.title}")
        print(f"  skills: {request.skills}")
        print(f"  min_experience: {request.min_experience}")
        print(f"  required_candidates: {request.required_candidates}")
        print(f"  max_source_resumes: {request.max_source_resumes}")
        print(f"  exclude_candidate_ids count: {len(request.exclude_candidate_ids)}")

        # Determine number of candidates matched locally (ignoring exclusions)
        temp_req = request.model_copy(update={"exclude_candidate_ids": []})
        all_matched = await self._candidate_service.search_candidates(temp_req)

        candidates = (
            await self._candidate_service.search_candidates(
                request,
            )
        )

        num_matched = len(all_matched)
        num_returned = len(candidates)
        num_excluded = num_matched - num_returned

        print(f"\n[SourcingService] Local database search results:")
        print(f"  Candidates matched locally: {num_matched}")
        print(f"  Candidates excluded: {num_excluded}")
        print(f"  Candidates returned: {num_returned}")

        if len(candidates) >= request.required_candidates:
            print(f"\n[SourcingService] Decision Point:")
            print(f"  External scraping is NOT triggered.")
            print(f"  Reason: Local matched candidates ({len(candidates)}) meets or exceeds required_candidates ({request.required_candidates}).")

            selected_candidates = candidates[:request.required_candidates]
            
            print(f"\n[SourcingService] Completion:")
            print(f"  Requested candidates: {request.required_candidates}")
            print(f"  Candidates returned: {len(selected_candidates)}")
            print(f"  Target satisfied: True")
            print()

            return CandidateSearchResponse(
                candidates=selected_candidates,
                requested_candidates=request.required_candidates,
                returned_candidates=len(
                    selected_candidates,
                ),
                sourced=False,
            )

        print(f"\n[SourcingService] Decision Point:")
        print(f"  External scraping IS triggered.")
        print(f"  Reason: Local matched candidates ({len(candidates)}) is less than required_candidates ({request.required_candidates}).")

        try:
            await self._sourcing_service.source_candidates(
                request,
            )
        except Exception as sourcing_err:
            print(f"[SourcingService] Sourcing failed or timed out: {sourcing_err}")

        candidates = (
            await self._candidate_service.search_candidates(
                request,
            )
        )

        selected_candidates = candidates[:request.required_candidates]
        target_satisfied = len(selected_candidates) >= request.required_candidates

        print(f"\n[SourcingService] Completion:")
        print(f"  Requested candidates: {request.required_candidates}")
        print(f"  Candidates returned: {len(selected_candidates)}")
        print(f"  Target satisfied: {target_satisfied}")
        print()

        return CandidateSearchResponse(
            candidates=selected_candidates,
            requested_candidates=request.required_candidates,
            returned_candidates=len(
                selected_candidates,
            ),
            sourced=True,
        )