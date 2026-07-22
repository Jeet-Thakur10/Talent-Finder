"""Helper function for detecting changes in scoring-relevant fields of a JD."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.data.models.postgres.job_description import JobDescription
    from src.schemas.job_description_schema import JobDescriptionUpdateRequest


def has_scoring_fields_changed(
    existing_jd: JobDescription,
    update_data: JobDescriptionUpdateRequest,
) -> bool:
    """Checks if update request modifies fields that affect candidate evaluation.

    Fields that affect candidate scoring:
    - title, job_purpose, responsibilities
    - min_experience, max_experience, location, employment_type_id
    - education_requirement, preferred_qualifications
    - skills (skill_name and is_mandatory)

    Fields that do NOT affect scoring:
    - hiring_manager_id, department
    """
    if existing_jd.title != update_data.title:
        return True
    if (existing_jd.job_purpose or "") != (update_data.job_purpose or ""):
        return True
    if (existing_jd.responsibilities or "") != (update_data.responsibilities or ""):
        return True
    if existing_jd.min_experience != update_data.min_experience:
        return True
    if existing_jd.max_experience != update_data.max_experience:
        return True
    if existing_jd.location != update_data.location:
        return True
    if existing_jd.employment_type_id != update_data.employment_type_id:
        return True
    old_edu = existing_jd.education_requirement or ""
    new_edu = update_data.education_requirement or ""
    if old_edu != new_edu:
        return True
    old_pref = existing_jd.preferred_qualifications or ""
    new_pref = update_data.preferred_qualifications or ""
    if old_pref != new_pref:
        return True

    # Compare skills set (skill_name, is_mandatory)
    existing_skills = {
        (s.skill_name.strip().lower(), s.is_mandatory) for s in existing_jd.skills
    }
    updated_skills = {
        (s.skill_name.strip().lower(), s.is_mandatory) for s in update_data.skills
    }
    return existing_skills != updated_skills
