import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from src.core.services.job_description_service import JobDescriptionService
from src.core.services.scoring_service import ScoringService
from src.core.exceptions.job_description_exception import JobDescriptionClosed, JobDescriptionActive
from src.schemas.job_description_schema import JobDescriptionUpdateRequest
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.data.models.postgres.pipeline import HiringManagerDecision, Pipeline
from src.core.exceptions.scoring_exceptions import ScoringBaseException


@pytest.mark.asyncio
async def test_update_job_description_fails_when_campaign_is_closed():
    # Setup mocks
    db_mock = MagicMock()
    service = JobDescriptionService(db_mock)
    
    jd_id = uuid4()
    recruiter_id = uuid4()
    
    # Mock repository methods
    mock_status = MagicMock()
    mock_status.code = "CLOSED"
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.status = mock_status
    mock_jd.skills = []
    
    service.job_description_repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    
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
    
    # Trigger update, which should raise JobDescriptionClosed
    with pytest.raises(JobDescriptionClosed) as exc_info:
        await service.update_job_description(jd_id, update_data, current_user)
        
    assert exc_info.value.status_code == 409
    assert "This campaign has been completed." in exc_info.value.message


@pytest.mark.asyncio
async def test_end_campaign_raises_exception_if_not_hiring_manager():
    db_mock = MagicMock()
    db_mock.commit = AsyncMock()
    service = ScoringService(db_mock)
    
    jd_id = uuid4()
    recruiter_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    
    with pytest.raises(ScoringBaseException) as exc_info:
        await service.end_campaign(jd_id, current_user)
        
    assert exc_info.value.status_code == 403
    assert "Only hiring managers can end campaigns." in exc_info.value.details


@pytest.mark.asyncio
async def test_end_campaign_raises_exception_if_not_all_decided():
    db_mock = MagicMock()
    db_mock.commit = AsyncMock()
    service = ScoringService(db_mock)
    
    jd_id = uuid4()
    hm_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=hm_id, role=UserRole.hiring_manager)
    
    # Mock repository
    mock_status = MagicMock()
    mock_status.code = "ACTIVE"
    
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.hiring_manager_id = hm_id
    mock_jd.status = mock_status
    
    service.repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    
    # Mock shared pipeline entries, one is PENDING
    entry1 = Pipeline(jd_id=jd_id, candidate_id=uuid4(), shared_with_hiring_manager=True, hm_decision=HiringManagerDecision.INTERVIEW_SENT)
    entry2 = Pipeline(jd_id=jd_id, candidate_id=uuid4(), shared_with_hiring_manager=True, hm_decision=HiringManagerDecision.PENDING)
    
    service.repository.bulk_get_pipeline_entries_for_job = AsyncMock(return_value=[entry1, entry2])
    
    with pytest.raises(ScoringBaseException) as exc_info:
        await service.end_campaign(jd_id, current_user)
        
    assert exc_info.value.status_code == 409
    assert "All shared candidates must be decided" in exc_info.value.details


@pytest.mark.asyncio
async def test_end_campaign_succeeds_when_all_decided():
    db_mock = MagicMock()
    db_mock.commit = AsyncMock()
    service = ScoringService(db_mock)
    
    jd_id = uuid4()
    hm_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=hm_id, role=UserRole.hiring_manager)
    
    # Mock repository
    mock_status = MagicMock()
    mock_status.code = "ACTIVE"
    
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.hiring_manager_id = hm_id
    mock_jd.status = mock_status
    
    service.repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    
    # Mock shared pipeline entries, all decided
    entry1 = Pipeline(jd_id=jd_id, candidate_id=uuid4(), shared_with_hiring_manager=True, hm_decision=HiringManagerDecision.INTERVIEW_SENT)
    entry2 = Pipeline(jd_id=jd_id, candidate_id=uuid4(), shared_with_hiring_manager=True, hm_decision=HiringManagerDecision.REJECTED)
    
    service.repository.bulk_get_pipeline_entries_for_job = AsyncMock(return_value=[entry1, entry2])
    service.repository.get_status_by_code = AsyncMock(return_value=uuid4())
    service.repository.update_job_description_status = AsyncMock()
    
    # Trigger end campaign
    await service.end_campaign(jd_id, current_user)
    
    service.repository.update_job_description_status.assert_called_once()
    db_mock.commit.assert_called_once()


@pytest.mark.asyncio
async def test_reopen_campaign_reopens_successfully():
    db_mock = MagicMock()
    db_mock.commit = AsyncMock()
    service = ScoringService(db_mock)
    
    jd_id = uuid4()
    hm_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=hm_id, role=UserRole.hiring_manager)
    
    # Mock repository
    mock_status = MagicMock()
    mock_status.code = "CLOSED"
    
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.hiring_manager_id = hm_id
    mock_jd.status = mock_status
    
    service.repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    service.repository.get_status_by_code = AsyncMock(return_value=uuid4())
    service.repository.update_job_description_status = AsyncMock()
    
    # Trigger reopen campaign
    await service.reopen_campaign(jd_id, current_user)
    
    service.repository.update_job_description_status.assert_called_once()
    db_mock.commit.assert_called_once()


@pytest.mark.asyncio
async def test_schedule_interview_skips_email_if_redacted_or_invalid():
    db_mock = MagicMock()
    db_mock.commit = AsyncMock()
    
    jd_id = uuid4()
    candidate_id = uuid4()
    hm_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=hm_id, role=UserRole.hiring_manager)
    
    # Mock JD status
    mock_status = MagicMock()
    mock_status.code = "ACTIVE"
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.hiring_manager_id = hm_id
    mock_jd.status = mock_status
    
    # Mock db.execute for load JD query
    mock_res = MagicMock()
    mock_res.scalar_one_or_none = MagicMock(return_value=mock_jd)
    db_mock.execute = AsyncMock(return_value=mock_res)
    
    service = ScoringService(db_mock)
    
    # Mock candidate with redacted email
    mock_candidate = MagicMock()
    mock_candidate.id = candidate_id
    mock_candidate.email = "*********@***.**.***"
    mock_candidate.full_name = "Ken Bae"
    
    # Mock pipeline entry
    mock_pipeline = MagicMock()
    mock_pipeline.jd_id = jd_id
    mock_pipeline.candidate_id = candidate_id
    mock_pipeline.hm_decision = HiringManagerDecision.PENDING
    
    service.repository.get_candidate_by_id = AsyncMock(return_value=mock_candidate)
    service.repository.get_pipeline_entry_for_job_and_candidate = AsyncMock(return_value=mock_pipeline)
    service.repository.update_pipeline_entry = AsyncMock()
    
    # Mock NotificationService.send_email
    from src.core.services.notification_service import NotificationService
    mock_send = AsyncMock()
    NotificationService.send_email = mock_send
    
    from datetime import datetime
    
    res, email_skipped = await service.schedule_interview(
        job_description_id=jd_id,
        candidate_id=candidate_id,
        interview_link="https://meet.google.com/abc-defg-hij",
        interview_datetime=datetime.now(),
        timezone="UTC",
        message="Test message",
        current_user=current_user
    )
    
    assert email_skipped is True
    mock_send.assert_not_called()


def make_mock_jd(jd_id, recruiter_id, status_code="CLOSED"):
    from datetime import datetime, UTC
    now = datetime.now(UTC)
    mock_status = MagicMock()
    mock_status.code = status_code
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.title = "Software Engineer"
    mock_jd.department = "Engineering"
    mock_jd.job_purpose = "Purpose"
    mock_jd.responsibilities = "Responsibilities"
    mock_jd.min_experience = 3
    mock_jd.max_experience = 5
    mock_jd.location = "Remote"
    mock_jd.education_requirement = "BS"
    mock_jd.preferred_qualifications = "MS"
    mock_jd.employment_type_id = uuid4()
    mock_jd.status_id = uuid4()
    mock_jd.created_at = now
    mock_jd.updated_at = now
    mock_jd.status = mock_status
    mock_jd.skills = []
    return mock_jd


@pytest.mark.asyncio
async def test_get_authorized_job_description_allows_closed_when_requested():
    db_mock = MagicMock()
    service = ScoringService(db_mock)

    jd_id = uuid4()
    recruiter_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    mock_jd = make_mock_jd(jd_id, recruiter_id, "CLOSED")

    service.repository.get_recruiter_id_by_job_description_id = AsyncMock(return_value=recruiter_id)
    service.repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)

    # When allow_closed=False (default), it raises JobDescriptionClosed
    with pytest.raises(JobDescriptionClosed):
        await service._get_authorized_job_description(jd_id, current_user, allow_closed=False)

    # When allow_closed=True, it succeeds
    res = await service._get_authorized_job_description(jd_id, current_user, allow_closed=True)
    assert res.id == jd_id


@pytest.mark.asyncio
async def test_get_authorized_job_description_enforces_ownership_even_if_allow_closed_true():
    db_mock = MagicMock()
    service = ScoringService(db_mock)

    jd_id = uuid4()
    owner_recruiter_id = uuid4()
    other_user_id = uuid4()
    other_user = AuthenticatedUserContext(user_id=other_user_id, role=UserRole.recruiter)

    service.repository.get_recruiter_id_by_job_description_id = AsyncMock(return_value=owner_recruiter_id)

    from src.core.exceptions.job_description_exception import RecruiterAccessRequired
    with pytest.raises(RecruiterAccessRequired):
        await service._get_authorized_job_description(jd_id, other_user, allow_closed=True)


@pytest.mark.asyncio
async def test_scenario_a_closed_campaign_read_only_access():
    db_mock = MagicMock()
    service = ScoringService(db_mock)

    jd_id = uuid4()
    recruiter_id = uuid4()
    current_user = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    mock_jd = make_mock_jd(jd_id, recruiter_id, "CLOSED")

    service.repository.get_recruiter_id_by_job_description_id = AsyncMock(return_value=recruiter_id)
    service.repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    service.repository.get_candidate_scores_for_job_description = AsyncMock(return_value=[])
    service.repository.bulk_get_pipeline_entries_for_job = AsyncMock(return_value=[])

    # list_ranked_candidates_for_job_description should succeed when CLOSED
    candidates = await service.list_ranked_candidates_for_job_description(jd_id, current_user)
    assert candidates == []

    # Mutating operation like share_shortlist should fail when CLOSED
    with pytest.raises(JobDescriptionClosed):
        await service.share_shortlist(jd_id, current_user, [uuid4()], {})


@pytest.mark.asyncio
async def test_scenario_b_and_c_reopen_and_edit_jd():
    from datetime import datetime, UTC
    db_mock = MagicMock()
    db_mock.commit = AsyncMock()
    service = ScoringService(db_mock)

    jd_id = uuid4()
    hm_id = uuid4()
    recruiter_id = uuid4()
    hm_user = AuthenticatedUserContext(user_id=hm_id, role=UserRole.hiring_manager)
    recruiter_user = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)

    mock_status = MagicMock()
    mock_status.code = "CLOSED"

    creation_time = datetime.now(UTC)
    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.hiring_manager_id = hm_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.status = mock_status
    mock_jd.updated_at = creation_time

    service.repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    service.repository.get_status_by_code = AsyncMock(return_value=uuid4())
    
    # Custom update_job_description_status that DOES NOT touch updated_at
    async def mock_update_status(j_id, s_id):
        mock_status.code = "ACTIVE"
    service.repository.update_job_description_status = AsyncMock(side_effect=mock_update_status)

    # Reopen campaign
    await service.reopen_campaign(jd_id, hm_user)

    # Verify updated_at was preserved across reopen
    assert mock_jd.updated_at == creation_time
    assert mock_status.code == "ACTIVE"


