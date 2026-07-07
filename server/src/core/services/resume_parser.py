from __future__ import annotations

from datetime import date

from src.control.agents.scoring_agent import ResumeExtractionClient
from src.schemas.scoring_schema import (
    ParsedCandidateProfile,
    ParsedEducation,
    ParsedExperience,
    ParsedSkill,
)


class ResumeParser:
    def __init__(self) -> None:
        self.extraction_client = ResumeExtractionClient()

    def parse_resume(self, resume_text: str) -> ParsedCandidateProfile:
        extraction = self.extraction_client.extract(resume_text)
        payload = extraction.payload

        print("\n"*3)
        print("Extraction payload:", payload)
        print("Extraction provider:", extraction.provider)
        print("\n"*3)

        candidate = self.build_candidate_from_payload(payload)

        return candidate
# codes that return the parsed, structured candidate profile information.
    def _parse_date(
            self,
        value: str | None,
    ) -> date | None:
        if not value:
            return None

        try:
            return date.fromisoformat(value)
        except ValueError:
            return None


    def build_candidate_from_payload(
        self,
        payload: dict[str, object],
    ) -> ParsedCandidateProfile:

        skills: list[ParsedSkill] = []
        skills_raw = payload.get("skills")
        if isinstance(skills_raw, list):
            for skill in skills_raw:
                if isinstance(skill, dict):
                    skill_name = skill.get("skill_name")
                    if isinstance(skill_name, str):
                        skills.append(ParsedSkill(skill_name=skill_name))

        experiences: list[ParsedExperience] = []
        experiences_raw = payload.get("experiences")
        if isinstance(experiences_raw, list):
            for exp in experiences_raw:
                if isinstance(exp, dict):
                    company_name_raw = exp.get("company_name")
                    company_name = (
                        company_name_raw
                        if isinstance(company_name_raw, str)
                        else None)

                    title_raw = exp.get("title")
                    title = title_raw if isinstance(title_raw, str) else ""

                    description_raw = exp.get("description")
                    description = (
                        description_raw
                        if isinstance(description_raw, str)
                        else None)

                    start_date_raw = exp.get("start_date")
                    start_date_str = (
                        start_date_raw
                        if isinstance(start_date_raw, str)
                        else None
                    )
                    start_date = self._parse_date(start_date_str)

                    end_date_raw = exp.get("end_date")
                    end_date_str = (
                        end_date_raw
                        if isinstance(end_date_raw, str)
                        else None
                    )
                    end_date = self._parse_date(end_date_str)

                    is_current_raw = exp.get("is_current")
                    is_current = (
                        is_current_raw
                        if isinstance(is_current_raw, bool)
                        else False)

                    exp_skills: list[ParsedSkill] = []
                    exp_skills_raw = exp.get("skills")
                    if isinstance(exp_skills_raw, list):
                        for skill in exp_skills_raw:
                            if isinstance(skill, dict):
                                skill_name = skill.get("skill_name")
                                if isinstance(skill_name, str):
                                    exp_skills.append(ParsedSkill(skill_name=skill_name))

                    experiences.append(
                        ParsedExperience(
                            company_name=company_name,
                            title=title,
                            description=description,
                            start_date=start_date,
                            end_date=end_date,
                            is_current=is_current,
                            skills=exp_skills,
                        )
                    )

        educations: list[ParsedEducation] = []
        educations_raw = payload.get("educations")
        if isinstance(educations_raw, list):
            for edu in educations_raw:
                if isinstance(edu, dict):
                    inst_raw = edu.get("institution_name")
                    institution_name = inst_raw if isinstance(inst_raw, str) else None

                    degree_raw = edu.get("degree")
                    degree = degree_raw if isinstance(degree_raw, str) else ""

                    field_raw = edu.get("field_of_study")
                    field_of_study = field_raw if isinstance(field_raw, str) else None

                    start_date_raw = edu.get("start_date")
                    start_date_str = (
                        start_date_raw
                        if isinstance(start_date_raw, str)
                        else None
                    )
                    start_date = self._parse_date(start_date_str)

                    end_date_raw = edu.get("end_date")
                    end_date_str = (
                        end_date_raw
                        if isinstance(end_date_raw, str)
                        else None
                    )
                    end_date = self._parse_date(end_date_str)

                    educations.append(
                        ParsedEducation(
                            institution_name=institution_name,
                            degree=degree,
                            field_of_study=field_of_study,
                            start_date=start_date,
                            end_date=end_date,
                        )
                    )

        full_name_raw = payload.get("full_name", "")
        full_name = full_name_raw if isinstance(full_name_raw, str) else ""

        email_raw = payload.get("email")
        email = email_raw if isinstance(email_raw, str) else None

        phone_raw = payload.get("phone")
        phone = phone_raw if isinstance(phone_raw, str) else None

        current_title_raw = payload.get("current_title")
        current_title = current_title_raw if isinstance(current_title_raw,str) else None

        location_raw = payload.get("location")
        location = location_raw if isinstance(location_raw, str) else None

        summary_raw = payload.get("summary")
        summary = summary_raw if isinstance(summary_raw, str) else None

        total_exp_raw = payload.get("total_experience_months", 0)
        total_experience_months = total_exp_raw if isinstance(total_exp_raw, int) else 0

        return ParsedCandidateProfile(
            full_name=full_name,
            email=email,
            phone=phone,
            current_title=current_title,
            location=location,
            summary=summary,
            skills=skills,
            experiences=experiences,
            educations=educations,
            total_experience_months=total_experience_months,
        )

