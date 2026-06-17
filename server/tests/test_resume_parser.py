from unittest import TestCase

from src.core.services.resume_parser import ResumeParser

SAMPLE_RESUME = """
Priya Raman
Senior Backend Engineer
priya.raman@example.com
+91 98765 43210
Bangalore, India

SUMMARY
Backend engineer with 6 years of experience building APIs and cloud services.

SKILLS
Python, FastAPI, AWS, PostgreSQL, Docker

EXPERIENCE
Senior Backend Engineer | Acme Labs | Jan 2022 - Present
Built FastAPI services on AWS and PostgreSQL.

Software Engineer | Beta Tech | Jun 2019 - Dec 2021
Developed Python APIs and containerized deployments with Docker.

EDUCATION
B.Tech in Computer Science, Anna University, 2019
"""

UNSTRUCTURED_RESUME = (
    "Priya Raman is a Senior Backend Engineer based in Bangalore, India. "
    "She can be reached at priya.raman@example.com or +91 98765 43210. "
    "She has 6 years of experience building APIs and cloud services. "
    "Her skills include Python, FastAPI, AWS, PostgreSQL, and Docker. "
    "At Acme Labs from Jan 2022 to Present, she built FastAPI services on AWS and PostgreSQL. "
    "Before that, at Beta Tech from Jun 2019 to Dec 2021, she developed Python APIs and containerized deployments with Docker. "
    "She earned a B.Tech in Computer Science from Anna University in 2019."
)


class ResumeParserTests(TestCase):
    def test_parse_resume_extracts_structured_candidate_profile(self) -> None:
        parser = ResumeParser()

        result = parser.parse_resume(SAMPLE_RESUME)

        self.assertEqual(result.full_name, "Priya Raman")
        self.assertEqual(result.email, "priya.raman@example.com")
        self.assertEqual(result.phone, "919876543210")
        self.assertEqual(result.current_title, "Senior Backend Engineer")
        self.assertIn(
            "python",
            {skill.normalized_skill_name for skill in result.skills},
        )
        self.assertEqual(len(result.experiences), 2)
        self.assertEqual(
            result.educations[0].normalized_degree_level,
            "bachelor",
        )
        self.assertGreaterEqual(result.total_experience_months, 60)

    def test_parse_resume_handles_raw_paragraph_input(self) -> None:
        parser = ResumeParser()

        result = parser.parse_resume(UNSTRUCTURED_RESUME)

        self.assertEqual(result.full_name, "Priya Raman")
        self.assertEqual(result.current_title, "Senior Backend Engineer")
        self.assertEqual(result.email, "priya.raman@example.com")
        self.assertIn(
            "python",
            {skill.normalized_skill_name for skill in result.skills},
        )
        self.assertGreaterEqual(len(result.experiences), 1)
        self.assertGreaterEqual(len(result.educations), 1)
