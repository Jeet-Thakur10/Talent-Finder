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


def get_postjobfree_sourcing_service(
    client: PostJobFreeClient = Depends(
        get_postjobfree_client,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
) -> PostJobFreeSourcingService:

    return PostJobFreeSourcingService(
        client=client,
        extraction_agent=ResumeExtractionAgent(),
        candidate_service=CandidateService(
            db,
        ),
    )

def get_candidate_search_service(
    db: AsyncSession = Depends(
        get_db,
    ),
    client: PostJobFreeClient = Depends(
        get_postjobfree_client,
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
        )
    )

    return CandidateSearchService(
        candidate_service=candidate_service,
        sourcing_service=sourcing_service,
    )