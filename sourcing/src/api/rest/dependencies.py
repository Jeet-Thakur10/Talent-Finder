from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.control.agents.resume_extraction_agent import (
    ResumeExtractionAgent,
)
from src.core.services.candidate_service import (
    CandidateService,
)
from src.core.services.postjobfree_sourcing_service import (
    PostJobFreeSourcingService,
)
from src.data.clients.postgres import (
    async_session_local,
)
from src.handlers.http_clients.postjobfree_client import (
    PostJobFreeClient,
)
from src.core.services.candidate_search_service import (
    CandidateSearchService,
)
from src.control.agents.candidate_search_strategy_agent import CandidateSearchStrategyAgent
from src.core.services.search_strategies import (
    OriginalQueryStrategy,
    MandatorySkillsStrategy,
    TitleOnlyStrategy,
    LLMOptimizationStrategy,
)
from src.core.services.search_query_optimizer import SearchQueryOptimizer


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_local() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise


def get_candidate_service(
    db: AsyncSession = Depends(
        get_db,
    ),
) -> CandidateService:
    return CandidateService(
        db,
    )


def get_resume_extraction_agent() -> ResumeExtractionAgent:
    return ResumeExtractionAgent()


async def get_postjobfree_client():

    client = PostJobFreeClient()

    try:
        yield client

    finally:
        await client.close()


def get_search_query_optimizer() -> SearchQueryOptimizer:
    agent = CandidateSearchStrategyAgent()
    strategies = [
        OriginalQueryStrategy(),
        MandatorySkillsStrategy(),
        TitleOnlyStrategy(),
        LLMOptimizationStrategy(agent),
    ]
    return SearchQueryOptimizer(strategies)


def get_postjobfree_sourcing_service(
    client: PostJobFreeClient = Depends(
        get_postjobfree_client,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
    optimizer: SearchQueryOptimizer = Depends(
        get_search_query_optimizer,
    ),
) -> PostJobFreeSourcingService:

    return PostJobFreeSourcingService(
        client=client,
        extraction_agent=ResumeExtractionAgent(),
        candidate_service=CandidateService(
            db,
        ),
        optimizer=optimizer,
    )


def get_candidate_search_service(
    db: AsyncSession = Depends(
        get_db,
    ),
    client: PostJobFreeClient = Depends(
        get_postjobfree_client,
    ),
    optimizer: SearchQueryOptimizer = Depends(
        get_search_query_optimizer,
    ),
) -> CandidateSearchService:

    candidate_service = CandidateService(
        db,
    )

    sourcing_service = (
        PostJobFreeSourcingService(
            client=client,
            extraction_agent=ResumeExtractionAgent(),
            candidate_service=candidate_service,
            optimizer=optimizer,
        )
    )

    return CandidateSearchService(
        candidate_service=candidate_service,
        sourcing_service=sourcing_service,
    )