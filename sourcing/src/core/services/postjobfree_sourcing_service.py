import asyncio
import random

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


class PostJobFreeSourcingService:
    def __init__(
        self,
        client: PostJobFreeClient,
        extraction_agent: ResumeExtractionAgent,
        candidate_service: CandidateService,
    ) -> None:
        self._client = client
        self._extraction_agent = extraction_agent
        self._candidate_service = candidate_service

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

        search_request = (
            self.generate_postjobfree_search_request(
                request,
            )
        )

        search_html = await self._client.search_resumes(
            search_request,
        )

        search_results = self._search_parser.parse(
            search_html,
        )

        if not search_results:
            return

        existing_candidates = await self._candidate_service.search_candidates(
            request,
        )
        existing_count = len(existing_candidates)

        missing_candidates = max(
            request.required_candidates - existing_count,
            0,
        )

        if missing_candidates == 0:
            return

        existing_ids = {c.candidate_id for c in existing_candidates}
        newly_sourced_count = 0

        for result in search_results:
            if newly_sourced_count >= missing_candidates:
                break

            try:
                resume_html = (
                    await self._client.get_resume_page(
                        result.resume_url,
                    )
                )

                resume = self._resume_parser.parse(
                    html=resume_html,
                    source_url=result.resume_url,
                )

                extraction_result = (
                    self._extraction_agent.extract(
                        resume.raw_resume_text,
                    )
                )

                if not extraction_result.success:
                    print(
                        f"Skipping resume: "
                        f"{extraction_result.error}"
                    )
                    continue

                stored_candidate = await self._candidate_service.create_candidate(
                    candidate=extraction_result.payload,
                    resume_text=resume.raw_resume_text,
                    source_type="postjobfree",
                )

                if stored_candidate.id in request.exclude_candidate_ids:
                    print(
                        f"Scraped candidate {stored_candidate.id} "
                        "is in exclude list. Skipping counting."
                    )
                    continue

                if stored_candidate.id not in existing_ids:
                    newly_sourced_count += 1
                    existing_ids.add(stored_candidate.id)
                    print(f"Successfully sourced and stored new candidate: {stored_candidate.id}")

                sleep_seconds = random.randint(
                    15,
                    25,
                )

                print(
                    f"Sleeping for "
                    f"{sleep_seconds} seconds..."
                )

                await asyncio.sleep(
                    sleep_seconds,
                )

            except Exception as exc:
                print(
                    f"Failed sourcing "
                    f"{result.resume_url}: "
                    f"{exc}"
                )

