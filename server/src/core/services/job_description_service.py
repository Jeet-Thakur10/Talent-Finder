from datetime import UTC, datetime
from uuid import UUID
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.job_description_constants import DRAFT
from src.core.exceptions.job_description_exception import (
    InvalidEmploymentType,
    InvalidJobDescriptionStatus,
    JobDescriptionNotFound,
    RecruiterAccessRequired,
)
from src.control.agents.job_description_extraction_agent import JobDescriptionExtractionAgent
from src.data.models.postgres.jd_skill import JDSkill
from src.data.models.postgres.job_description import JobDescription
from src.data.repositories.job_description_repository import (
    JobDescriptionRepository,
)
from src.schemas.auth_schema import AuthenticatedUserContext, UserRole
from src.schemas.job_description_schema import (
    EmploymentTypeResponse,
    HiringManagerResponse,
    JDSkillResponse,
    JobDescriptionCreateRequest,
    JobDescriptionResponse,
    JobDescriptionUpdateRequest,
    JobDescriptionStatusResponse,
    JobDescriptionExtractRequest,
)


class JobDescriptionService:

    def __init__(self, db: AsyncSession):
        self.job_description_repository = (
            JobDescriptionRepository(db)
        )
        self.extraction_agent = JobDescriptionExtractionAgent()

    async def create_job_description(
            self,
            data: JobDescriptionCreateRequest,
            current_user: AuthenticatedUserContext) -> JobDescriptionResponse:

        if current_user.role != UserRole.recruiter:
            raise RecruiterAccessRequired(
                details="Only recruiters can create job descriptions.",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        employment_type = (
            await self.job_description_repository.get_employment_type_by_id(
                data.employment_type_id,
            )
        )

        if not employment_type:
            raise InvalidEmploymentType(
                details=f"Employment type '{data.employment_type_id}' does not exist"
            )
        draft_status = (
            await self.job_description_repository.get_status_by_code(
                DRAFT,
            )
        )

        if not draft_status:
            raise InvalidJobDescriptionStatus(
                details=f"Status '{DRAFT}' does not exist",
            )

        now = datetime.now(UTC)

        job_description = JobDescription(
            recruiter_id=current_user.user_id,

            title=data.title,
            department=data.department,

            job_purpose=data.job_purpose,
            responsibilities=data.responsibilities,

            min_experience=data.min_experience,
            max_experience=data.max_experience,

            location=data.location,

            employment_type_id=employment_type.id,

            education_requirement=data.education_requirement,

            preferred_qualifications=data.preferred_qualifications,

            status_id=draft_status.id,
            hiring_manager_id=data.hiring_manager_id,
            raw_job_description=data.raw_job_description,

            created_at=now,
            updated_at=now,
        )

        job_description = (
            await self.job_description_repository.create_job_description(
                job_description,
            )
        )

        skills = [
            JDSkill(
                jd_id=job_description.id,
                skill_name=skill.skill_name,
                is_mandatory=skill.is_mandatory,
            )
            for skill in data.skills
        ]

        await self.job_description_repository.create_skills(
            skills,
        )

        return JobDescriptionResponse(
            id=job_description.id,
            title=job_description.title,
            department=job_description.department,
            job_purpose=job_description.job_purpose,
            responsibilities=job_description.responsibilities,
            min_experience=job_description.min_experience,
            max_experience=job_description.max_experience,
            location=job_description.location,
            education_requirement=job_description.education_requirement,
            preferred_qualifications=job_description.preferred_qualifications,
            employment_type_id=job_description.employment_type_id,
            status_id=job_description.status_id,
            hiring_manager_id=job_description.hiring_manager_id,
            raw_job_description=job_description.raw_job_description,
            created_at=job_description.created_at,
            updated_at=job_description.updated_at,
            skills=[
                JDSkillResponse(
                    id=skill.id,
                    skill_name=skill.skill_name,
                    is_mandatory=skill.is_mandatory,
                )
                for skill in skills
            ],
        )

    async def update_job_description(
        self,
        job_description_id: UUID,
        data: JobDescriptionUpdateRequest,
        current_user: AuthenticatedUserContext,
    ) -> JobDescriptionResponse:
        if current_user.role != UserRole.recruiter:
            raise RecruiterAccessRequired(
                details="Only recruiters can update job descriptions.",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        job_description = await (
            self.job_description_repository
            .get_job_description_by_id(
                job_description_id,
            )
        )

        if not job_description:
            raise JobDescriptionNotFound(
                error_code="JOB_DESCRIPTION_NOT_FOUND",
            )

        if job_description.recruiter_id != current_user.user_id:
            raise JobDescriptionNotFound(
                error_code="JOB_DESCRIPTION_NOT_FOUND",
            )

        employment_type = (
            await self.job_description_repository.get_employment_type_by_id(
                data.employment_type_id,
            )
        )

        if not employment_type:
            raise InvalidEmploymentType(
                details=f"Employment type '{data.employment_type_id}' does not exist"
            )

        job_description.title = data.title
        job_description.department = data.department
        job_description.job_purpose = data.job_purpose
        job_description.responsibilities = data.responsibilities
        job_description.min_experience = data.min_experience
        job_description.max_experience = data.max_experience
        job_description.location = data.location
        job_description.employment_type_id = employment_type.id
        job_description.education_requirement = (
            data.education_requirement
        )
        job_description.preferred_qualifications = (
            data.preferred_qualifications
        )
        job_description.hiring_manager_id = data.hiring_manager_id
        job_description.updated_at = datetime.now(UTC)

        await self.job_description_repository.delete_skills_for_job_description(
            job_description.id,
        )

        job_description.skills = [
            JDSkill(
                jd_id=job_description.id,
                skill_name=skill.skill_name,
                is_mandatory=skill.is_mandatory,
            )
            for skill in data.skills
        ]

        updated_job_description = await (
            self.job_description_repository.save_job_description(
                job_description,
            )
        )

        return self._build_job_description_response(
            updated_job_description,
        )

    def _build_job_description_response(
        self,
        job_description: JobDescription,
    ) -> JobDescriptionResponse:
        return JobDescriptionResponse(
            id=job_description.id,
            title=job_description.title,
            department=job_description.department,
            job_purpose=job_description.job_purpose,
            responsibilities=job_description.responsibilities,
            min_experience=job_description.min_experience,
            max_experience=job_description.max_experience,
            location=job_description.location,
            education_requirement=job_description.education_requirement,
            preferred_qualifications=job_description.preferred_qualifications,
            employment_type_id=job_description.employment_type_id,
            status_id=job_description.status_id,
            hiring_manager_id=job_description.hiring_manager_id,
            raw_job_description=job_description.raw_job_description,
            created_at=job_description.created_at,
            updated_at=job_description.updated_at,
            skills=[
                JDSkillResponse(
                    id=skill.id,
                    skill_name=skill.skill_name,
                    is_mandatory=skill.is_mandatory,
                )
                for skill in job_description.skills
            ],
        )

    async def get_job_descriptions(
            self,
            current_user: AuthenticatedUserContext) -> list[JobDescriptionResponse]:
        if current_user.role != UserRole.recruiter:
            raise RecruiterAccessRequired(
                details="Only recruiters can view job descriptions.",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        job_descriptions = (
            await self.job_description_repository
            .get_job_descriptions_by_recruiter(
                current_user.user_id,
            )
        )

        responses = []

        for jd in job_descriptions:

            responses.append(
                JobDescriptionResponse(
                    id=jd.id,
                    title=jd.title,
                    department=jd.department,
                    job_purpose=jd.job_purpose,
                    responsibilities=jd.responsibilities,
                    min_experience=jd.min_experience,
                    max_experience=jd.max_experience,
                    location=jd.location,
                    education_requirement=jd.education_requirement,
                    preferred_qualifications=jd.preferred_qualifications,
                    employment_type_id=jd.employment_type_id,
                    status_id=jd.status_id,
                    hiring_manager_id=jd.hiring_manager_id,
                    raw_job_description=jd.raw_job_description,
                    created_at=jd.created_at,
                    updated_at=jd.updated_at,
                    skills=[
                        JDSkillResponse(
                            id=skill.id,
                            skill_name=skill.skill_name,
                            is_mandatory=skill.is_mandatory,
                        )
                        for skill in jd.skills
                    ],
                )
            )

        return responses

    async def get_job_description(
        self,
        job_description_id: UUID,
        current_user: AuthenticatedUserContext,
    ) -> JobDescriptionResponse:
        if current_user.role != UserRole.recruiter:
            raise RecruiterAccessRequired(
                details="Only recruiters can view job descriptions.",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        job_description = await (
            self.job_description_repository
            .get_job_description_by_id(
                job_description_id,
            )
        )
        if not job_description:
            raise JobDescriptionNotFound(
                error_code="JOB_DESCRIPTION_NOT_FOUND",
            )

        if job_description.recruiter_id != current_user.user_id:
            raise JobDescriptionNotFound(
                error_code="JOB_DESCRIPTION_NOT_FOUND",
            )

        return self._build_job_description_response(
            job_description,
        )

    async def get_employment_types(
        self,
    ) -> list[EmploymentTypeResponse]:

        employment_types = (
            await self.job_description_repository.get_employment_types()
        )

        return [
            EmploymentTypeResponse.model_validate(
                employment_type
            )
            for employment_type in employment_types
        ]


    async def get_job_description_statuses(
        self,
    ) -> list[JobDescriptionStatusResponse]:

        statuses = (
            await self.job_description_repository
            .get_job_description_statuses()
        )

        return [
            JobDescriptionStatusResponse.model_validate(
                status
            )
            for status in statuses
        ]

    async def get_hiring_managers(
        self,
    ) -> list[HiringManagerResponse]:
        hiring_managers = (
            await self.job_description_repository.get_hiring_managers()
        )

        return [
            HiringManagerResponse(
                id=hiring_manager.id,
                name=hiring_manager.name,
                email=hiring_manager.email,
            )
            for hiring_manager in hiring_managers
        ]

    async def extract_job_description(
        self,
        data: JobDescriptionExtractRequest,
        current_user: AuthenticatedUserContext,
    ) -> JobDescriptionResponse:
        if current_user.role != UserRole.recruiter:
            raise RecruiterAccessRequired(
                details="Only recruiters can extract job descriptions.",
                error_code="RECRUITER_ACCESS_REQUIRED",
            )

        extracted = self.extraction_agent.extract(data.raw_job_description)

        # 1. Resolve employment type
        employment_types = await self.job_description_repository.get_employment_types()
        matched_type = None
        if extracted.employment_type:
            et_lower = extracted.employment_type.lower()
            for et in employment_types:
                if et.code.lower() in et_lower or et.name.lower() in et_lower or et_lower in et.code.lower() or et_lower in et.name.lower():
                    matched_type = et
                    break
        if not matched_type and employment_types:
            matched_type = employment_types[0]

        # 2. Resolve hiring manager
        hiring_managers = await self.job_description_repository.get_hiring_managers()
        matched_manager = None
        if extracted.hiring_manager:
            hm_lower = extracted.hiring_manager.lower()
            for hm in hiring_managers:
                if hm.name.lower() in hm_lower or hm_lower in hm.name.lower():
                    matched_manager = hm
                    break
        hiring_manager_id = matched_manager.id if matched_manager else None

        # 3. Construct response mapping
        dummy_jd_id = uuid.uuid4()
        
        responsibilities = "\n".join(extracted.responsibilities) if extracted.responsibilities else ""
        preferred_qualifications = "\n".join(extracted.preferred_qualifications) if extracted.preferred_qualifications else None

        skills_list = [
            JDSkillResponse(
                id=uuid.uuid4(),
                skill_name=skill.skill_name,
                is_mandatory=skill.is_mandatory
            )
            for skill in extracted.skills
        ]

        return JobDescriptionResponse(
            id=dummy_jd_id,
            title=extracted.title or "",
            department=extracted.department,
            job_purpose=extracted.job_purpose or "",
            responsibilities=responsibilities,
            min_experience=extracted.min_experience or 0,
            max_experience=extracted.max_experience or 0,
            location=extracted.location or "",
            education_requirement=extracted.education_requirement or "",
            preferred_qualifications=preferred_qualifications,
            employment_type_id=matched_type.id if matched_type else uuid.uuid4(),
            status_id=uuid.uuid4(),  # dummy status UUID
            hiring_manager_id=hiring_manager_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            skills=skills_list
        )
