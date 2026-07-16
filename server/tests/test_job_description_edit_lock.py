import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from src.core.services.job_description_service import JobDescriptionService
from src.core.exceptions.job_description_exception import JobDescriptionScoringInProgress
from src.schemas.job_description_schema import JobDescriptionUpdateRequest
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.data.models.postgres.scoring_task import ScoringTask

@pytest.mark.asyncio
async def test_update_job_description_fails_when_scoring_is_active():
    # 1. Setup mocks
    db_mock = MagicMock()
    service = JobDescriptionService(db_mock)
    
    jd_id = uuid4()
    recruiter_id = uuid4()
    
    # Mock repository methods
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.skills = []
    
    service.job_description_repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    
    # 2. Mock db execution results
    # Mock the select(ScoringTask) query to return an active task
    mock_task = ScoringTask(
        id=uuid4(),
        recruiter_id=recruiter_id,
        job_description_id=jd_id,
        status="RUNNING"
    )
    
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_task
    db_mock.execute = AsyncMock(return_value=mock_execute_result)
    
    current_user = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    from src.schemas.job_description_schema import JDSkillCreateRequest
    update_data = JobDescriptionUpdateRequest(
        title="Software Engineer",
        department="Engineering",
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=3,
        max_experience=5,
        location="Remote",
        employment_type_id=uuid4(),
        education_requirement="BS",
        preferred_qualifications="MS",
        skills=[JDSkillCreateRequest(skill_name="Python", is_mandatory=True)],
        hiring_manager_id=uuid4(),
        raw_job_description="raw jd"
    )
    
    # 3. Trigger update, which should raise JobDescriptionScoringInProgress
    with pytest.raises(JobDescriptionScoringInProgress) as exc_info:
        await service.update_job_description(jd_id, update_data, current_user)
        
    assert "This Job Description cannot be edited while candidate scoring is in progress." in str(exc_info.value)
    
    # Verify DB select query was run to look for active tasks
    db_mock.execute.assert_called_once()
