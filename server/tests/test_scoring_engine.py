from datetime import UTC, date, datetime
from unittest import TestCase
from uuid import uuid4

from src.core.services.resume_parser import ResumeParser
from src.core.services.scoring_engine import ScoringEngine
from src.schemas.scoring_schema import (
    NormalizedJobDescriptionProfile,
    ParsedCandidateProfile,
    ParsedEducation,
    ParsedExperience,
    ParsedSkill,
)


class ScoringEngineTests(TestCase):
    def setUp(self) -> None:
        self.parser = ResumeParser()
        self.engine = ScoringEngine(self.parser)

    def test_high_fit_candidate_gets_strong_score(self) -> None:
        candidate = ParsedCandidateProfile(
            full_name="Asha Kumar",
            current_title="Senior Backend Engineer",
            normalized_title="backend engineer",
            skills=[
                ParsedSkill(
                    skill_name="Python",
                    normalized_skill_name="python",
                ),
                ParsedSkill(
                    skill_name="FastAPI",
                    normalized_skill_name="fastapi",
                ),
                ParsedSkill(
                    skill_name="AWS",
                    normalized_skill_name="aws",
                ),
            ],
            experiences=[
                ParsedExperience(
                    company_name="Acme",
                    title="Senior Backend Engineer",
                    normalized_title="backend engineer",
                    start_date=date(2021, 1, 1),
                    end_date=datetime.now(UTC).date(),
                    is_current=True,
                    skills=[
                        ParsedSkill(
                            skill_name="Python",
                            normalized_skill_name="python",
                        ),
                        ParsedSkill(
                            skill_name="FastAPI",
                            normalized_skill_name="fastapi",
                        ),
                        ParsedSkill(
                            skill_name="AWS",
                            normalized_skill_name="aws",
                        ),
                    ],
                )
            ],
            educations=[
                ParsedEducation(
                    degree="B.Tech in Computer Science",
                    normalized_degree_level="bachelor",
                    field_of_study="computer science",
                )
            ],
            total_experience_months=72,
        )
        job = NormalizedJobDescriptionProfile(
            job_description_id=uuid4(),
            normalized_title="backend engineer",
            normalized_location="remote",
            normalized_education_requirement="bachelor computer science",
            min_experience=3,
            max_experience=6,
            mandatory_skills=["python", "fastapi"],
            optional_skills=["aws"],
            search_text="backend engineer python fastapi aws remote",
        )

        result = self.engine.score_candidate(candidate, job)

        self.assertEqual(result.skills_score, 40.0)
        self.assertEqual(result.experience_score, 25.0)
        self.assertEqual(result.recency_score, 15.0)
        self.assertGreaterEqual(result.role_fit_score, 10.0)
        self.assertEqual(result.education_score, 8.0)
        self.assertGreaterEqual(result.final_score, 98.0)
        self.assertEqual(result.matched_mandatory_skills, ["fastapi", "python"])
        self.assertEqual(result.matched_optional_skills, ["aws"])

    def test_underqualified_candidate_is_penalized(self) -> None:
        candidate = ParsedCandidateProfile(
            full_name="Riya Singh",
            current_title="Junior Developer",
            normalized_title="backend engineer",
            skills=[
                ParsedSkill(
                    skill_name="Python",
                    normalized_skill_name="python",
                ),
            ],
            total_experience_months=12,
        )
        job = NormalizedJobDescriptionProfile(
            job_description_id=uuid4(),
            normalized_title="backend engineer",
            normalized_location="remote",
            normalized_education_requirement="bachelor computer science",
            min_experience=4,
            max_experience=6,
            mandatory_skills=["python", "fastapi"],
            optional_skills=[],
            search_text="backend engineer python fastapi remote",
        )

        result = self.engine.score_candidate(candidate, job)

        self.assertLess(result.experience_score, 10.0)
        self.assertEqual(result.missing_mandatory_skills, ["fastapi"])
        self.assertLess(result.final_score, 55.0)
