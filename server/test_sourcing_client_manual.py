import asyncio
from pprint import pprint
from uuid import uuid4

from src.schemas.candidate_search_schema import CandidateSearchRequest
from src.data.clients.candidate_search_client import CandidateSearchClient


async def main():
    print("Initializing CandidateSearchClient...")
    
    # 1. Construct request payload with some exclude IDs
    request = CandidateSearchRequest(
        title="Backend Engineer",
        skills=["Python", "PostgreSQL", "FastAPI"],
        min_experience=3,
        required_candidates=5,
        max_source_resumes=20,
        exclude_candidate_ids=[uuid4()]
    )
    
    print("\n==================================================")
    print("Request Payload (serialized):")
    pprint(request.model_dump(mode="json"))
    print("==================================================")

    print("\nSending search request to Sourcing Service...")
    async with CandidateSearchClient() as client:
        try:
            response = await client.search_candidates(request)
            print("\n==================================================")
            print("Response successfully received and validated!")
            print(f"Number of candidates returned: {len(response.candidates)}")
            if response.candidates:
                print("First candidate summary:")
                pprint(response.candidates[0].model_dump(mode="json"))
            else:
                print("No candidates returned from search.")
            print("==================================================")
        except Exception as e:
            import traceback
            print(f"\nRequest failed: {type(e).__name__} - {str(e)}")
            if hasattr(e, "details"):
                print(f"Details: {e.details}")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
