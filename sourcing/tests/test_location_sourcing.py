from unittest.mock import MagicMock
from src.schemas.candidate_search_request import CandidateSearchRequest
from src.core.services.postjobfree_sourcing_service import PostJobFreeSourcingService
from src.core.services.search_query_optimizer import SearchQueryOptimizer
from src.config.settings import settings



async def test_generate_postjobfree_search_request_remote_disabled():
    # Setup service with mocked dependencies
    client_mock = MagicMock()
    extraction_mock = MagicMock()
    cand_service_mock = MagicMock()
    optimizer_mock = MagicMock()

    service = PostJobFreeSourcingService(
        client=client_mock,
        extraction_agent=extraction_mock,
        candidate_service=cand_service_mock,
        optimizer=optimizer_mock,
    )

    # 1. Remote Job: APPEND_REMOTE_KEYWORD = False (Default)
    settings.APPEND_REMOTE_KEYWORD = False
    req = CandidateSearchRequest(
        title="Python Developer",
        skills=["FastAPI", "PostgreSQL"],
        location="Remote",
        is_remote=True,
        is_hybrid=False,
    )

    pjf_req = service.generate_postjobfree_search_request(req)
    assert pjf_req.location == ""
    # "remote" should NOT be appended because it's disabled in settings
    assert "remote" not in pjf_req.required_words.lower()
    assert "fastapi" in pjf_req.required_words.lower()


async def test_generate_postjobfree_search_request_remote_enabled():
    client_mock = MagicMock()
    extraction_mock = MagicMock()
    cand_service_mock = MagicMock()
    optimizer_mock = MagicMock()

    service = PostJobFreeSourcingService(
        client=client_mock,
        extraction_agent=extraction_mock,
        candidate_service=cand_service_mock,
        optimizer=optimizer_mock,
    )

    # 2. Remote Job: APPEND_REMOTE_KEYWORD = True
    settings.APPEND_REMOTE_KEYWORD = True
    req = CandidateSearchRequest(
        title="Python Developer",
        skills=["FastAPI", "PostgreSQL"],
        location="Remote",
        is_remote=True,
        is_hybrid=False,
    )

    pjf_req = service.generate_postjobfree_search_request(req)
    assert pjf_req.location == ""
    # "remote" SHOULD be appended
    assert "remote" in pjf_req.required_words.lower()


async def test_generate_postjobfree_search_request_hybrid():
    client_mock = MagicMock()
    extraction_mock = MagicMock()
    cand_service_mock = MagicMock()
    optimizer_mock = MagicMock()

    service = PostJobFreeSourcingService(
        client=client_mock,
        extraction_agent=extraction_mock,
        candidate_service=cand_service_mock,
        optimizer=optimizer_mock,
    )

    # 3. Hybrid Job: Physical location should be passed
    req = CandidateSearchRequest(
        title="React Developer",
        skills=["React", "TypeScript"],
        location="Bangalore",
        is_remote=False,
        is_hybrid=True,
    )

    pjf_req = service.generate_postjobfree_search_request(req)
    assert pjf_req.location == "Bangalore"
    assert "hybrid" not in pjf_req.required_words.lower()


async def test_generate_postjobfree_search_request_no_skills():
    client_mock = MagicMock()
    extraction_mock = MagicMock()
    cand_service_mock = MagicMock()
    optimizer_mock = MagicMock()

    service = PostJobFreeSourcingService(
        client=client_mock,
        extraction_agent=extraction_mock,
        candidate_service=cand_service_mock,
        optimizer=optimizer_mock,
    )

    req = CandidateSearchRequest(
        title="UX/UI Designer",
        skills=[],
        location="Chennai",
        is_remote=False,
        is_hybrid=False,
    )

    pjf_req = service.generate_postjobfree_search_request(req)
    assert pjf_req.location == "Chennai"
    assert pjf_req.required_words == "UX/UI Designer"
    assert pjf_req.title_words == "UX/UI Designer"
    assert pjf_req.resume_text_words == ""


async def test_generate_postjobfree_search_request_attempt_2():
    client_mock = MagicMock()
    extraction_mock = MagicMock()
    cand_service_mock = MagicMock()
    optimizer_mock = MagicMock()

    service = PostJobFreeSourcingService(
        client=client_mock,
        extraction_agent=extraction_mock,
        candidate_service=cand_service_mock,
        optimizer=optimizer_mock,
    )

    original_req = CandidateSearchRequest(
        title="Software Developer",
        skills=["Java", "Python", "SQL"],
        location="Chennai Tamil Nadu India",
        is_remote=False,
        is_hybrid=False,
    )

    # In Attempt 2, the optimizer produces an optimized request where location is None, but skills are preserved.
    optimized_req = CandidateSearchRequest(
        title="Software Developer",
        skills=["Java", "Python", "SQL"],
        location=None,
        is_remote=False,
        is_hybrid=False,
    )

    pjf_req = service.generate_postjobfree_search_request(
        optimized_req,
        original_request=original_req,
        current_attempt=2
    )

    assert pjf_req.location == "Chennai Tamil Nadu India"
    assert pjf_req.required_words == "Java Python SQL"
    assert pjf_req.title_words == "Software Developer"
    assert pjf_req.resume_text_words == ""


async def test_search_strategies_fallback():
    # Verify the fallback order of the optimizer
    from src.schemas.search_attempt import SearchOptimizationPlan
    agent_mock = MagicMock()
    
    # We must mock agent.optimize to return an optimization plan
    agent_mock.optimize = MagicMock()
    async def mock_optimize(req):
        return SearchOptimizationPlan(
            inferred_role="UX/UI Designer",
            representative_title="UX/UI Designer",
            representative_skills=["Figma"],
            reasoning="Test",
        )
    agent_mock.optimize.side_effect = mock_optimize
    
    # 1. With location
    req_with_loc = CandidateSearchRequest(
        title="UX/UI Designer",
        skills=["Figma"],
        location="Chennai",
        min_experience=0,
        required_candidates=5,
        max_source_resumes=10,
    )
    optimizer = SearchQueryOptimizer(agent=agent_mock)
    await optimizer.initialize(req_with_loc)
    
    # Check strategies length
    assert len(optimizer._strategies) == 5
    assert optimizer._strategies[0].__class__.__name__ == "RepresentativeSkillsStrategy"
    assert optimizer._strategies[0]._keep_location is True
    assert optimizer._strategies[1].__class__.__name__ == "RepresentativeSkillsStrategy"
    assert optimizer._strategies[1]._keep_location is False
    assert optimizer._strategies[2].__class__.__name__ == "GeneralizedTitleStrategy"
    assert optimizer._strategies[3].__class__.__name__ == "SingleCoreSkillStrategy"
    assert optimizer._strategies[4].__class__.__name__ == "TitleOnlyStrategy"

    # Verify attempt 0 (keep_location=True) drops skills when location is present
    opt_req_0, reason_0 = await optimizer.get_optimized_request(req_with_loc, [])
    assert opt_req_0.location == "Chennai"
    assert opt_req_0.skills == []

    # Verify attempt 1 (keep_location=False) keeps skills and drops location
    # Create fake history item to simulate attempt 0 completed
    from src.schemas.search_attempt import SearchAttempt
    fake_attempt_0 = SearchAttempt(
        attempt_number=1,
        title="UX/UI Designer",
        skills=[],
        resumes_found=0,
        candidates_persisted=0,
        new_candidates_persisted=0,
        candidates_remaining=5,
        reason="Initial local",
        query_url="",
        location_used="Chennai",
        strategy_name="RepresentativeSkillsStrategy",
    )
    opt_req_1, reason_1 = await optimizer.get_optimized_request(req_with_loc, [fake_attempt_0])
    assert opt_req_1.location is None
    assert opt_req_1.skills == ["Figma"]

    # 2. Without location
    req_no_loc = CandidateSearchRequest(
        title="UX/UI Designer",
        skills=["Figma"],
        location=None,
        min_experience=0,
        required_candidates=5,
        max_source_resumes=10,
    )
    optimizer_no_loc = SearchQueryOptimizer(agent=agent_mock)
    await optimizer_no_loc.initialize(req_no_loc)
    
    assert len(optimizer_no_loc._strategies) == 5
    
    # Verify attempt 0 (keep_location=True) keeps skills because location is absent
    opt_req_no_loc_0, _ = await optimizer_no_loc.get_optimized_request(req_no_loc, [])
    assert opt_req_no_loc_0.location is None
    assert opt_req_no_loc_0.skills == ["Figma"]



if __name__ == "__main__":
    import asyncio
    async def run_all():
        print("Running generate_postjobfree_search_request_remote_disabled...")
        await test_generate_postjobfree_search_request_remote_disabled()
        print("Running generate_postjobfree_search_request_remote_enabled...")
        await test_generate_postjobfree_search_request_remote_enabled()
        print("Running generate_postjobfree_search_request_hybrid...")
        await test_generate_postjobfree_search_request_hybrid()
        print("Running generate_postjobfree_search_request_no_skills...")
        await test_generate_postjobfree_search_request_no_skills()
        print("Running generate_postjobfree_search_request_attempt_2...")
        await test_generate_postjobfree_search_request_attempt_2()
        print("Running search_strategies_fallback...")
        await test_search_strategies_fallback()
        print("All location sourcing unit tests passed successfully!")
    asyncio.run(run_all())
