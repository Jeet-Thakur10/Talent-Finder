"""Unit tests for invalidating shared shortlists when Job Description changes."""

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.utils.jd_comparison_helper import has_scoring_fields_changed
from src.utils.review_state_helper import (
    has_campaign_review_started,
    has_pipeline_entry_review_started,
)
from src.core.services.job_description_service import JobDescriptionService
from src.data.models.postgres.job_description import JobDescription
from src.data.models.postgres.jd_skill import JDSkill
from src.data.models.postgres.pipeline import HiringManagerDecision, Pipeline
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    JDSkillCreateRequest,
    JobDescriptionUpdateRequest,
)


@pytest.mark.asyncio
async def test_has_scoring_fields_changed_helper():
    recruiter_id = uuid4()
    emp_type_id = uuid4()
    status_id = uuid4()

    jd = JobDescription(
        id=uuid4(),
        recruiter_id=recruiter_id,
        title="Senior Python Developer",
        department="Engineering",
        job_purpose="Build backend services",
        responsibilities="Python, FastAPI, PostgreSQL",
        min_experience=5,
        max_experience=8,
        location="Remote",
        employment_type_id=emp_type_id,
        education_requirement="Bachelor's",
        preferred_qualifications="AWS experience",
        status_id=status_id,
        hiring_manager_id=None,
        skills=[
            JDSkill(id=uuid4(), skill_name="Python", is_mandatory=True),
            JDSkill(id=uuid4(), skill_name="FastAPI", is_mandatory=False),
        ],
    )

    # 1. Non-scoring update: only department and hiring_manager_id change
    new_hm_id = uuid4()
    non_scoring_req = JobDescriptionUpdateRequest(
        title="Senior Python Developer",
        department="Product Engineering",  # changed
        job_purpose="Build backend services",
        responsibilities="Python, FastAPI, PostgreSQL",
        min_experience=5,
        max_experience=8,
        location="Remote",
        employment_type_id=emp_type_id,
        education_requirement="Bachelor's",
        preferred_qualifications="AWS experience",
        hiring_manager_id=new_hm_id,  # changed
        skills=[
            JDSkillCreateRequest(skill_name="Python", is_mandatory=True),
            JDSkillCreateRequest(skill_name="FastAPI", is_mandatory=False),
        ],
    )
    assert has_scoring_fields_changed(jd, non_scoring_req) is False

    # 2. Scoring update: title changes
    scoring_req_title = non_scoring_req.model_copy(update={"title": "Staff Python Developer"})
    assert has_scoring_fields_changed(jd, scoring_req_title) is True

    # 3. Scoring update: mandatory skill added
    scoring_req_skills = non_scoring_req.model_copy(
        update={
            "skills": [
                JDSkillCreateRequest(skill_name="Python", is_mandatory=True),
                JDSkillCreateRequest(skill_name="FastAPI", is_mandatory=False),
                JDSkillCreateRequest(skill_name="Docker", is_mandatory=True),
            ]
        }
    )
    assert has_scoring_fields_changed(jd, scoring_req_skills) is True


@pytest.mark.asyncio
async def test_review_state_helpers():
    # 1. Unreviewed entry (PENDING)
    entry_unreviewed = Pipeline(
        jd_id=uuid4(),
        candidate_id=uuid4(),
        shared_with_hiring_manager=True,
        hm_decision=HiringManagerDecision.PENDING,
        hiring_manager_notes=None,
        interview_sent_at=None,
    )
    assert has_pipeline_entry_review_started(entry_unreviewed) is False
    assert has_campaign_review_started([entry_unreviewed]) is False

    # 2. Rejected entry
    entry_rejected = Pipeline(
        jd_id=uuid4(),
        candidate_id=uuid4(),
        shared_with_hiring_manager=True,
        hm_decision=HiringManagerDecision.REJECTED,
        hiring_manager_notes="Not enough experience",
    )
    assert has_pipeline_entry_review_started(entry_rejected) is True
    assert has_campaign_review_started([entry_unreviewed, entry_rejected]) is True

    # 3. Scheduled interview entry
    entry_interview = Pipeline(
        jd_id=uuid4(),
        candidate_id=uuid4(),
        shared_with_hiring_manager=True,
        hm_decision=HiringManagerDecision.INTERVIEW_SENT,
        interview_sent_at=datetime.now(UTC),
    )
    assert has_pipeline_entry_review_started(entry_interview) is True


@pytest.mark.asyncio
async def test_scenario_a_unreviewed_shortlist_invalidated_on_jd_edit():
    db_mock = MagicMock()
    service = JobDescriptionService(db_mock)

    jd_id = uuid4()
    recruiter_id = uuid4()
    now = datetime.now(UTC)

    mock_status = MagicMock()
    mock_status.code = "ACTIVE"

    mock_emp_type = MagicMock()
    mock_emp_type.id = uuid4()

    mock_skill = JDSkill(id=uuid4(), jd_id=jd_id, skill_name="Python", is_mandatory=True)

    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.status = mock_status
    mock_jd.status_id = uuid4()
    mock_jd.title = "Backend Engineer"
    mock_jd.department = "Engineering"
    mock_jd.job_purpose = "Build microservices"
    mock_jd.responsibilities = "Python"
    mock_jd.min_experience = 3
    mock_jd.max_experience = 5
    mock_jd.location = "Remote"
    mock_jd.employment_type_id = mock_emp_type.id
    mock_jd.education_requirement = "BS CS"
    mock_jd.preferred_qualifications = None
    mock_jd.hiring_manager_id = uuid4()
    mock_jd.raw_job_description = "raw"
    mock_jd.created_at = now
    mock_jd.updated_at = now
    mock_jd.skills = [mock_skill]

    # Mock DB query for active scoring task -> None
    mock_res = MagicMock()
    mock_res.scalar_one_or_none = MagicMock(return_value=None)
    db_mock.execute = AsyncMock(return_value=mock_res)

    # Mock repo methods
    service.job_description_repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    service.job_description_repository.get_employment_type_by_id = AsyncMock(return_value=mock_emp_type)
    service.job_description_repository.delete_skills_for_job_description = AsyncMock()
    service.job_description_repository.save_job_description = AsyncMock(return_value=mock_jd)

    # Unreviewed shared pipeline entry
    shared_entry = Pipeline(
        jd_id=jd_id,
        candidate_id=uuid4(),
        shared_with_hiring_manager=True,
        hm_decision=HiringManagerDecision.PENDING,
    )
    service.job_description_repository.get_pipeline_entries_for_job = AsyncMock(return_value=[shared_entry])
    service.job_description_repository.unshare_pipeline_entries_for_job = AsyncMock(return_value=1)

    recruiter_user_ctx = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    update_req = JobDescriptionUpdateRequest(
        title="Senior Backend Engineer",  # scoring-relevant change
        department="Engineering",
        job_purpose="Build microservices",
        responsibilities="Python",
        min_experience=3,
        max_experience=5,
        location="Remote",
        employment_type_id=mock_emp_type.id,
        education_requirement="BS CS",
        hiring_manager_id=uuid4(),
        skills=[JDSkillCreateRequest(skill_name="Python", is_mandatory=True)],
    )

    await service.update_job_description(jd_id, update_req, recruiter_user_ctx)

    service.job_description_repository.unshare_pipeline_entries_for_job.assert_called_once_with(jd_id)


@pytest.mark.asyncio
async def test_scenario_b_reviewed_shortlist_preserved_on_jd_edit():
    db_mock = MagicMock()
    service = JobDescriptionService(db_mock)

    jd_id = uuid4()
    recruiter_id = uuid4()
    now = datetime.now(UTC)

    mock_status = MagicMock()
    mock_status.code = "ACTIVE"
    mock_emp_type = MagicMock()
    mock_emp_type.id = uuid4()
    mock_skill = JDSkill(id=uuid4(), jd_id=jd_id, skill_name="React", is_mandatory=True)

    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.status = mock_status
    mock_jd.status_id = uuid4()
    mock_jd.title = "Frontend Engineer"
    mock_jd.department = "Engineering"
    mock_jd.job_purpose = "Build UI components"
    mock_jd.responsibilities = "React"
    mock_jd.min_experience = 2
    mock_jd.max_experience = 4
    mock_jd.location = "Remote"
    mock_jd.employment_type_id = mock_emp_type.id
    mock_jd.education_requirement = "BS CS"
    mock_jd.preferred_qualifications = None
    mock_jd.hiring_manager_id = uuid4()
    mock_jd.raw_job_description = "raw"
    mock_jd.created_at = now
    mock_jd.updated_at = now
    mock_jd.skills = [mock_skill]

    mock_res = MagicMock()
    mock_res.scalar_one_or_none = MagicMock(return_value=None)
    db_mock.execute = AsyncMock(return_value=mock_res)

    service.job_description_repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    service.job_description_repository.get_employment_type_by_id = AsyncMock(return_value=mock_emp_type)
    service.job_description_repository.delete_skills_for_job_description = AsyncMock()
    service.job_description_repository.save_job_description = AsyncMock(return_value=mock_jd)

    # Reviewed shared pipeline entry (interview scheduled)
    reviewed_entry = Pipeline(
        jd_id=jd_id,
        candidate_id=uuid4(),
        shared_with_hiring_manager=True,
        hm_decision=HiringManagerDecision.INTERVIEW_SENT,
        interview_sent_at=now,
    )
    service.job_description_repository.get_pipeline_entries_for_job = AsyncMock(return_value=[reviewed_entry])
    service.job_description_repository.unshare_pipeline_entries_for_job = AsyncMock()

    recruiter_user_ctx = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    update_req = JobDescriptionUpdateRequest(
        title="Senior Frontend Engineer",  # scoring-relevant change
        department="Engineering",
        job_purpose="Build UI components",
        responsibilities="React",
        min_experience=2,
        max_experience=4,
        location="Remote",
        employment_type_id=mock_emp_type.id,
        education_requirement="BS CS",
        hiring_manager_id=uuid4(),
        skills=[JDSkillCreateRequest(skill_name="React", is_mandatory=True)],
    )

    await service.update_job_description(jd_id, update_req, recruiter_user_ctx)

    # Unshare should NOT be called because review has started
    service.job_description_repository.unshare_pipeline_entries_for_job.assert_not_called()


@pytest.mark.asyncio
async def test_non_scoring_jd_edit_does_not_unshare_shortlist():
    db_mock = MagicMock()
    service = JobDescriptionService(db_mock)

    jd_id = uuid4()
    recruiter_id = uuid4()
    emp_type_id = uuid4()
    now = datetime.now(UTC)

    mock_status = MagicMock()
    mock_status.code = "ACTIVE"
    mock_emp_type = MagicMock()
    mock_emp_type.id = emp_type_id

    mock_skill = JDSkill(id=uuid4(), jd_id=jd_id, skill_name="Python", is_mandatory=True)

    mock_jd = MagicMock()
    mock_jd.id = jd_id
    mock_jd.recruiter_id = recruiter_id
    mock_jd.status = mock_status
    mock_jd.status_id = uuid4()
    mock_jd.title = "Software Engineer"
    mock_jd.department = "Engineering"
    mock_jd.job_purpose = "Purpose"
    mock_jd.responsibilities = "Responsibilities"
    mock_jd.min_experience = 3
    mock_jd.max_experience = 5
    mock_jd.location = "Remote"
    mock_jd.employment_type_id = emp_type_id
    mock_jd.education_requirement = "BS CS"
    mock_jd.preferred_qualifications = None
    mock_jd.hiring_manager_id = uuid4()
    mock_jd.raw_job_description = "raw"
    mock_jd.created_at = now
    mock_jd.updated_at = now
    mock_jd.skills = [mock_skill]

    mock_res = MagicMock()
    mock_res.scalar_one_or_none = MagicMock(return_value=None)
    db_mock.execute = AsyncMock(return_value=mock_res)

    service.job_description_repository.get_job_description_by_id = AsyncMock(return_value=mock_jd)
    service.job_description_repository.get_employment_type_by_id = AsyncMock(return_value=mock_emp_type)
    service.job_description_repository.delete_skills_for_job_description = AsyncMock()
    service.job_description_repository.save_job_description = AsyncMock(return_value=mock_jd)
    service.job_description_repository.get_pipeline_entries_for_job = AsyncMock()
    service.job_description_repository.unshare_pipeline_entries_for_job = AsyncMock()

    recruiter_user_ctx = AuthenticatedUserContext(user_id=recruiter_id, role=UserRole.recruiter)
    
    # Update ONLY non-scoring fields: department & hiring_manager_id
    non_scoring_update = JobDescriptionUpdateRequest(
        title="Software Engineer",
        department="Platform Engineering",  # non-scoring
        job_purpose="Purpose",
        responsibilities="Responsibilities",
        min_experience=3,
        max_experience=5,
        location="Remote",
        employment_type_id=emp_type_id,
        education_requirement="BS CS",
        hiring_manager_id=uuid4(),  # non-scoring
        skills=[JDSkillCreateRequest(skill_name="Python", is_mandatory=True)],
    )

    await service.update_job_description(jd_id, non_scoring_update, recruiter_user_ctx)

    # get_pipeline_entries_for_job and unshare should NOT be called at all
    service.job_description_repository.get_pipeline_entries_for_job.assert_not_called()
    service.job_description_repository.unshare_pipeline_entries_for_job.assert_not_called()
