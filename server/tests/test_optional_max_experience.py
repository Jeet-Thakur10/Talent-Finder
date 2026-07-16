import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from unittest.mock import MagicMock, AsyncMock
from src.schemas.job_description_schema import JobDescriptionWriteRequest, JDSkillCreateRequest
from src.schemas.scoring_schema import JobDescriptionScoringInput
from src.control.agents.scoring_agent import CandidateScoringClient
from src.schemas.job_description_extraction_schema import JobDescriptionExtraction
from src.core.services.job_description_service import JobDescriptionService

def test_write_request_validation():
    # 1. max_experience is None -> should be valid
    req = JobDescriptionWriteRequest(
        title="Software Engineer",
        department="Engineering",
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=3,
        max_experience=None,
        location="Remote",
        employment_type_id=uuid4(),
        education_requirement="BS",
        preferred_qualifications=None,
        skills=[JDSkillCreateRequest(skill_name="Python", is_mandatory=True)],
        hiring_manager_id=uuid4(),
        raw_job_description=None
    )
    assert req.max_experience is None

    # 2. max_experience >= min_experience -> should be valid
    req_range = JobDescriptionWriteRequest(
        title="Software Engineer",
        department="Engineering",
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=3,
        max_experience=5,
        location="Remote",
        employment_type_id=uuid4(),
        education_requirement="BS",
        preferred_qualifications=None,
        skills=[JDSkillCreateRequest(skill_name="Python", is_mandatory=True)],
        hiring_manager_id=uuid4(),
        raw_job_description=None
    )
    assert req_range.max_experience == 5

    # 3. max_experience < min_experience -> should raise ValidationError
    with pytest.raises(ValueError) as exc_info:
        JobDescriptionWriteRequest(
            title="Software Engineer",
            department="Engineering",
            job_purpose="Purpose",
            responsibilities="Responsibilities",
            min_experience=3,
            max_experience=2,
            location="Remote",
            employment_type_id=uuid4(),
            education_requirement="BS",
            preferred_qualifications=None,
            skills=[JDSkillCreateRequest(skill_name="Python", is_mandatory=True)],
            hiring_manager_id=uuid4(),
            raw_job_description=None
        )
    assert "max_experience must be greater than or equal to min_experience" in str(exc_info.value)


def test_calculate_experience_score_with_no_upper_bound():
    agent = CandidateScoringClient()

    # Candidate with 5 years (60 months)
    candidate = MagicMock()
    candidate.total_experience_months = 60

    # Job description requiring min 3 years, max None
    jd = JobDescriptionScoringInput(
        job_description_id=uuid4(),
        title="Engineer",
        department="Engineering",
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=3,
        max_experience=None,
        location="Remote",
        education_requirement="Degree",
        preferred_qualifications=None,
        skills=[]
    )

    score = agent._calculate_experience_score(candidate, jd)
    # Candidate meets min_experience (5 >= 3) and max_experience is None, so score should be full 25 points
    assert score == 25.0


def test_calculate_experience_score_with_lower_experience():
    agent = CandidateScoringClient()

    # Candidate with 2 years (24 months)
    candidate = MagicMock()
    candidate.total_experience_months = 24

    # Job description requiring min 4 years, max None
    jd = JobDescriptionScoringInput(
        job_description_id=uuid4(),
        title="Engineer",
        department="Engineering",
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=4,
        max_experience=None,
        location="Remote",
        education_requirement="Degree",
        preferred_qualifications=None,
        skills=[]
    )

    score = agent._calculate_experience_score(candidate, jd)
    # Candidate does not meet min_experience (2 < 4), should get scaled score: (2/4) * 25 = 12.5
    assert score == 12.5


@pytest.mark.asyncio
async def test_job_description_extraction_preserves_none():
    db_mock = MagicMock()
    service = JobDescriptionService(db_mock)

    # Mock get_employment_types and get_hiring_managers as async mocks
    service.job_description_repository.get_employment_types = AsyncMock(return_value=[])
    service.job_description_repository.get_hiring_managers = AsyncMock(return_value=[])

    extracted = JobDescriptionExtraction(
        title="Engineer",
        department="IT",
        job_purpose="Purpose",
        responsibilities=["Responsibilities"],
        location="Remote",
        min_experience=None,
        max_experience=None,
        skills=[]
    )
    service.extraction_agent = MagicMock()
    service.extraction_agent.extract = MagicMock(return_value=extracted)

    from src.schemas.job_description_schema import JobDescriptionExtractRequest
    from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
    req = JobDescriptionExtractRequest(raw_job_description="Sample JD text")
    current_user = AuthenticatedUserContext(user_id=uuid4(), role=UserRole.recruiter)

    res = await service.extract_job_description(req, current_user)
    assert res.min_experience is None
    assert res.max_experience is None
