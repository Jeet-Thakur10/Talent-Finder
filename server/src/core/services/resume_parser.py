from __future__ import annotations

from datetime import date, datetime

from src.core.services.scoring_ai_client import ResumeExtractionClient
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

        skills = [
            ParsedSkill(
                skill_name=skill["skill_name"],
            )
            for skill in payload.get("skills", [])
        ]

        experiences = [
            ParsedExperience(
                company_name=exp.get("company_name"),
                title=exp["title"],
                description=exp.get("description"),
                start_date=self._parse_date(
                    exp.get("start_date"),
                ),
                end_date=self._parse_date(
                    exp.get("end_date"),
                ),
                is_current=exp.get(
                    "is_current",
                    False,
                ),
                skills=[
                    ParsedSkill(
                        skill_name=skill["skill_name"],
                    )
                    for skill in exp.get(
                        "skills",
                        [],
                    )
                ],
            )
            for exp in payload.get(
                "experiences",
                [],
            )
        ]

        educations = [
            ParsedEducation(
                institution_name=edu.get(
                    "institution_name",
                ),
                degree=edu["degree"],
                field_of_study=edu.get(
                    "field_of_study",
                ),
                start_date=self._parse_date(
                    edu.get("start_date"),
                ),
                end_date=self._parse_date(
                    edu.get("end_date"),
                ),
            )
            for edu in payload.get(
                "educations",
                [],
            )
        ]

        return ParsedCandidateProfile(
            full_name=payload.get(
                "full_name",
                "",
            ),
            email=payload.get("email"),
            phone=payload.get("phone"),
            current_title=payload.get(
                "current_title",
            ),
            location=payload.get("location"),
            summary=payload.get("summary"),
            skills=skills,
            experiences=experiences,
            educations=educations,
            total_experience_months=payload.get(
                "total_experience_months",
                0,
            ),
        )

# that code ends here

