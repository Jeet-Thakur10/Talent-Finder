"""Unit tests for proficiency-aware skill scoring.

Tests the deterministic components introduced by the proficiency enhancement:
- _parse_skill_weight: pipe-delimited weight extraction with edge cases
- _calculate_skills_score: weighted sum scoring vs. old count-based scoring
- _calculate_candidate_score: pipe suffix stripping before output
"""

from uuid import uuid4

import pytest

from src.control.agents.scoring_agent import CandidateScoringClient
from src.schemas.scoring_schema import (
    CandidateEducationInput,
    CandidateEvaluationOutput,
    CandidateExperienceInput,
    CandidateScoreExplanation,
    CandidateScoringInput,
    CandidateSkillInput,
    JobDescriptionScoringInput,
    JobSkillInput,
)


@pytest.fixture
def client():
    """Create a CandidateScoringClient with mocked LLM (not used in unit tests)."""
    # The client constructor initializes a real Groq LLM,
    # but unit tests only call deterministic methods, so it's safe.
    return CandidateScoringClient()


# ─────────────────────────────────────────────────────────────
# _parse_skill_weight tests
# ─────────────────────────────────────────────────────────────


class TestParseSkillWeight:
    """Tests for the pipe-delimited weight parser."""

    def test_exact_match(self, client):
        name, weight = client._parse_skill_weight("Python|1.0")
        assert name == "Python"
        assert weight == 1.0

    def test_slight_gap(self, client):
        name, weight = client._parse_skill_weight("Python|0.75")
        assert name == "Python"
        assert weight == 0.75

    def test_significant_gap(self, client):
        name, weight = client._parse_skill_weight("Python|0.4")
        assert name == "Python"
        assert weight == 0.4

    def test_zero_weight(self, client):
        name, weight = client._parse_skill_weight("Python|0.0")
        assert name == "Python"
        assert weight == 0.0

    def test_no_pipe_backward_compat(self, client):
        """Old-format strings without pipe should default to 1.0."""
        name, weight = client._parse_skill_weight("Python")
        assert name == "Python"
        assert weight == 1.0

    def test_no_pipe_multi_word_skill(self, client):
        name, weight = client._parse_skill_weight("Machine Learning")
        assert name == "Machine Learning"
        assert weight == 1.0

    def test_invalid_weight_fallback(self, client):
        """Non-numeric weight should fallback to 1.0."""
        name, weight = client._parse_skill_weight("Python|invalid")
        assert name == "Python|invalid"
        assert weight == 1.0

    def test_weight_clamped_above_one(self, client):
        """Weight > 1.0 should be clamped to 1.0."""
        name, weight = client._parse_skill_weight("Python|1.5")
        assert name == "Python"
        assert weight == 1.0

    def test_weight_clamped_below_zero(self, client):
        """Negative weight should be clamped to 0.0."""
        name, weight = client._parse_skill_weight("Python|-0.5")
        assert name == "Python"
        assert weight == 0.0

    def test_skill_name_with_spaces(self, client):
        name, weight = client._parse_skill_weight("React Native|0.75")
        assert name == "React Native"
        assert weight == 0.75

    def test_skill_name_with_special_chars(self, client):
        name, weight = client._parse_skill_weight("C++|1.0")
        assert name == "C++"
        assert weight == 1.0

    def test_skill_name_with_dots(self, client):
        name, weight = client._parse_skill_weight("Node.js|0.4")
        assert name == "Node.js"
        assert weight == 0.4

    def test_empty_string(self, client):
        name, weight = client._parse_skill_weight("")
        assert name == ""
        assert weight == 1.0

    def test_pipe_only(self, client):
        """Edge case: just a pipe character."""
        name, weight = client._parse_skill_weight("|0.5")
        assert name == ""
        assert weight == 0.5


# ─────────────────────────────────────────────────────────────
# _calculate_skills_score tests
# ─────────────────────────────────────────────────────────────


def _make_jd(mandatory: list[str], optional: list[str]) -> JobDescriptionScoringInput:
    """Helper to create a JD scoring input with given skill names."""
    skills = [JobSkillInput(skill_name=s, is_mandatory=True) for s in mandatory] + [
        JobSkillInput(skill_name=s, is_mandatory=False) for s in optional
    ]
    return JobDescriptionScoringInput(
        job_description_id=uuid4(),
        title="Test Role",
        job_purpose="Test purpose",
        responsibilities="Test responsibilities",
        min_experience=3,
        max_experience=7,
        location="Remote",
        education_requirement="Bachelor's",
        skills=skills,
    )


def _make_evaluation(
    matched_mandatory: list[str],
    matched_optional: list[str],
    missing_mandatory: list[str],
) -> CandidateEvaluationOutput:
    """Helper to create an LLM evaluation output."""
    return CandidateEvaluationOutput(
        candidate_id=uuid4(),
        confidence=80.0,
        role_fit_score=8.0,
        education_score=6.0,
        matched_mandatory_skills=matched_mandatory,
        matched_optional_skills=matched_optional,
        missing_mandatory_skills=missing_mandatory,
        explanation=CandidateScoreExplanation(
            summary="Test summary",
            strengths=["Good"],
            weaknesses=["Bad"],
        ),
    )


class TestCalculateSkillsScore:
    """Tests for the weighted skills score calculation."""

    def test_all_exact_matches(self, client):
        """All skills at 1.0 should produce the same result as the old count-based formula."""
        jd = _make_jd(["Python", "PostgreSQL", "Docker"], ["Redis", "Kafka"])
        evaluation = _make_evaluation(
            matched_mandatory=["Python|1.0", "PostgreSQL|1.0", "Docker|1.0"],
            matched_optional=["Redis|1.0", "Kafka|1.0"],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # (3/3)*28 + (2/2)*12 = 28 + 12 = 40
        assert score == pytest.approx(40.0)

    def test_backward_compat_no_pipes(self, client):
        """Old-format strings without pipes should give the same result as before."""
        jd = _make_jd(["Python", "PostgreSQL"], ["Docker"])
        evaluation = _make_evaluation(
            matched_mandatory=["Python", "PostgreSQL"],
            matched_optional=["Docker"],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # (2/2)*28 + (1/1)*12 = 28 + 12 = 40
        assert score == pytest.approx(40.0)

    def test_one_slight_gap(self, client):
        """One skill at 0.75 should reduce the score proportionally."""
        jd = _make_jd(["Advanced Python", "PostgreSQL", "Docker"], [])
        evaluation = _make_evaluation(
            matched_mandatory=["Python|0.75", "PostgreSQL|1.0", "Docker|1.0"],
            matched_optional=[],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # (0.75 + 1.0 + 1.0) / 3 * 28 = 2.75/3 * 28 = 25.67
        assert score == pytest.approx(25.67, abs=0.01)

    def test_one_significant_gap(self, client):
        """One skill at 0.4 should reduce the score more significantly."""
        jd = _make_jd(["Advanced Python", "PostgreSQL", "Docker"], [])
        evaluation = _make_evaluation(
            matched_mandatory=["Python|0.4", "PostgreSQL|1.0", "Docker|1.0"],
            matched_optional=[],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # (0.4 + 1.0 + 1.0) / 3 * 28 = 2.4/3 * 28 = 22.4
        assert score == pytest.approx(22.4, abs=0.01)

    def test_one_missing_skill(self, client):
        """A missing skill is not in matched list, so it contributes 0."""
        jd = _make_jd(["Python", "PostgreSQL", "Kubernetes"], [])
        evaluation = _make_evaluation(
            matched_mandatory=["Python|1.0", "PostgreSQL|1.0"],
            matched_optional=[],
            missing_mandatory=["Kubernetes"],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # (1.0 + 1.0) / 3 * 28 = 2.0/3 * 28 = 18.67
        assert score == pytest.approx(18.67, abs=0.01)

    def test_mixed_weights_mandatory_and_optional(self, client):
        """Mixed weights across both mandatory and optional skills."""
        jd = _make_jd(["Advanced Python", "PostgreSQL"], ["Docker", "Redis"])
        evaluation = _make_evaluation(
            matched_mandatory=["Python|0.75", "PostgreSQL|1.0"],
            matched_optional=["Docker|1.0", "Redis|0.4"],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # mandatory: (0.75 + 1.0) / 2 * 28 = 1.75/2 * 28 = 24.5
        # optional:  (1.0 + 0.4) / 2 * 12 = 1.4/2 * 12 = 8.4
        # total: 32.9
        assert score == pytest.approx(32.9, abs=0.01)

    def test_no_mandatory_skills(self, client):
        """JD with no mandatory skills should yield 0 for mandatory component."""
        jd = _make_jd([], ["Docker", "Redis"])
        evaluation = _make_evaluation(
            matched_mandatory=[],
            matched_optional=["Docker|1.0"],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # mandatory: 0 (no mandatory skills)
        # optional:  (1.0) / 2 * 12 = 6.0
        assert score == pytest.approx(6.0)

    def test_no_optional_skills(self, client):
        """JD with no optional skills should yield 0 for optional component."""
        jd = _make_jd(["Python", "PostgreSQL"], [])
        evaluation = _make_evaluation(
            matched_mandatory=["Python|1.0", "PostgreSQL|1.0"],
            matched_optional=[],
            missing_mandatory=[],
        )
        score = client._calculate_skills_score(evaluation, jd)
        # (2.0/2)*28 + 0 = 28
        assert score == pytest.approx(28.0)

    def test_all_skills_missing(self, client):
        """No matched skills should produce 0."""
        jd = _make_jd(["Python", "PostgreSQL"], ["Docker"])
        evaluation = _make_evaluation(
            matched_mandatory=[],
            matched_optional=[],
            missing_mandatory=["Python", "PostgreSQL"],
        )
        score = client._calculate_skills_score(evaluation, jd)
        assert score == pytest.approx(0.0)

    def test_gap_vs_missing_ordering(self, client):
        """A significant gap (0.4) should score higher than missing (0)."""
        jd = _make_jd(["Advanced Python", "PostgreSQL"], [])

        # Scenario 1: significant gap
        eval_gap = _make_evaluation(
            matched_mandatory=["Python|0.4", "PostgreSQL|1.0"],
            matched_optional=[],
            missing_mandatory=[],
        )
        score_gap = client._calculate_skills_score(eval_gap, jd)

        # Scenario 2: missing
        eval_missing = _make_evaluation(
            matched_mandatory=["PostgreSQL|1.0"],
            matched_optional=[],
            missing_mandatory=["Advanced Python"],
        )
        score_missing = client._calculate_skills_score(eval_missing, jd)

        assert score_gap > score_missing


# ─────────────────────────────────────────────────────────────
# _calculate_candidate_score output cleanliness tests
# ─────────────────────────────────────────────────────────────


def _make_candidate() -> CandidateScoringInput:
    """Helper to create a minimal candidate scoring input."""
    return CandidateScoringInput(
        candidate_id=uuid4(),
        full_name="Test Candidate",
        current_title="Software Engineer",
        total_experience_months=60,
        skills=[CandidateSkillInput(skill_name="Python")],
        experiences=[
            CandidateExperienceInput(
                title="Software Engineer",
                is_current=True,
                skills=[CandidateSkillInput(skill_name="Python")],
            ),
        ],
        educations=[
            CandidateEducationInput(
                degree="Bachelor's",
                field_of_study="Computer Science",
            ),
        ],
    )


class TestCandidateScoreOutputCleanliness:
    """Verify that pipe-delimited weights are stripped from the output."""

    def test_pipe_suffixes_stripped_from_mandatory(self, client):
        """Matched mandatory skills in output should have clean names."""
        candidate_id = uuid4()
        evaluation = CandidateEvaluationOutput(
            candidate_id=candidate_id,
            confidence=80.0,
            role_fit_score=8.0,
            education_score=6.0,
            matched_mandatory_skills=["Python|0.75", "PostgreSQL|1.0"],
            matched_optional_skills=["Docker|0.4"],
            missing_mandatory_skills=["Kubernetes"],
            explanation=CandidateScoreExplanation(
                summary="Test",
                strengths=["Good"],
                weaknesses=["Python proficiency gap"],
            ),
        )
        jd = _make_jd(["Advanced Python", "PostgreSQL", "Kubernetes"], ["Docker"])
        candidate = _make_candidate()

        score_output = client._calculate_candidate_score(evaluation, jd, candidate)

        assert score_output.matched_mandatory_skills == ["Python", "PostgreSQL"]
        assert score_output.matched_optional_skills == ["Docker"]
        assert score_output.missing_mandatory_skills == ["Kubernetes"]

    def test_clean_names_already_clean(self, client):
        """Skills without pipe suffixes should pass through unchanged."""
        candidate_id = uuid4()
        evaluation = CandidateEvaluationOutput(
            candidate_id=candidate_id,
            confidence=80.0,
            role_fit_score=8.0,
            education_score=6.0,
            matched_mandatory_skills=["Python", "PostgreSQL"],
            matched_optional_skills=["Docker"],
            missing_mandatory_skills=[],
            explanation=CandidateScoreExplanation(
                summary="Test",
                strengths=["Good"],
                weaknesses=[],
            ),
        )
        jd = _make_jd(["Python", "PostgreSQL"], ["Docker"])
        candidate = _make_candidate()

        score_output = client._calculate_candidate_score(evaluation, jd, candidate)

        assert score_output.matched_mandatory_skills == ["Python", "PostgreSQL"]
        assert score_output.matched_optional_skills == ["Docker"]

    def test_weighted_score_applied_before_stripping(self, client):
        """Verify that the skills_score reflects weighted values even though output is clean."""
        candidate_id = uuid4()
        evaluation = CandidateEvaluationOutput(
            candidate_id=candidate_id,
            confidence=80.0,
            role_fit_score=8.0,
            education_score=6.0,
            matched_mandatory_skills=["Python|0.4", "PostgreSQL|1.0"],
            matched_optional_skills=[],
            missing_mandatory_skills=[],
            explanation=CandidateScoreExplanation(
                summary="Test",
                strengths=["Good"],
                weaknesses=["Python proficiency gap"],
            ),
        )
        jd = _make_jd(["Advanced Python", "PostgreSQL"], [])
        candidate = _make_candidate()

        score_output = client._calculate_candidate_score(evaluation, jd, candidate)

        # skills_score should be weighted: (0.4 + 1.0) / 2 * 28 = 19.6
        assert score_output.skills_score == pytest.approx(19.6, abs=0.01)
        # But output skill names are clean
        assert score_output.matched_mandatory_skills == ["Python", "PostgreSQL"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
