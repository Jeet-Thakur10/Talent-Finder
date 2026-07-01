from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config.settings import settings
from src.schemas.scoring_schema import (
    CandidateEvaluationOutput,
    CandidatePrescoreBatchOutput,
    CandidateScoreOutput,
    CandidateScoringInput,
    CompressedCandidate,
    CompressedJobDescription,
    JobDescriptionScoringInput,
    ResumeCandidateOutput,
)


@dataclass(slots=True)
class ResumeExtractionResult:
    payload: dict[str, object]
    provider: str

class ResumeExtractionClient:
    def __init__(self) -> None:
        self.provider = settings.SCORING_LLM_PROVIDER
        self.groq_model = settings.GROQ_MODEL

        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=self.groq_model,
            temperature=0,
        )

        # Keeping your preferred with_structured_output framework using json_mode
        self.structured_llm = self.llm.with_structured_output(
            ResumeCandidateOutput,
            method="json_mode"
        )

    def extract(
        self,
        resume_text: str,
    ) -> ResumeExtractionResult:
        try:
            print(f"Attempting Groq extraction with model: {self.groq_model}")

            # 1. Grab the exact schema keys (full_name, experiences, etc.) dynamically
            schema_json = json.dumps(ResumeCandidateOutput.model_json_schema(), indent=2)

            messages = [
                SystemMessage(
                    content=(
                        "Extract candidate information from the resume.\n"
                        "Return all available information.\n"
                        "Do not invent information that is not present.\n"
                        "Dates should be returned in ISO format (YYYY-MM-DD) whenever possible.\n\n"
                        "CRITICAL: You must respond strictly with a valid JSON object matching this exact schema layout:\n"
                        f"{schema_json}"
                    )
                ),
                HumanMessage(
                    content=resume_text.strip(),
                ),
            ]

            result: ResumeCandidateOutput = (
                self.structured_llm.invoke(
                    messages,
                )
            )

            return ResumeExtractionResult(
                payload=result.model_dump(),
                provider="groq",
            )

        except Exception:
            import traceback
            print("\n --- GROQ EXTRACTION CRASHED --- ")
            traceback.print_exc()
            print("------------------------------------\n")

            return ResumeExtractionResult(
                payload={},
                provider="fallback",
            )


@dataclass(slots=True)
class CandidateScoringResult:
    payload: CandidateEvaluationOutput | None
    provider: str

class CandidateScoringClient:
    def __init__(self) -> None:
        self.provider = settings.SCORING_LLM_PROVIDER
        self.groq_model = settings.GROQ_MODEL

        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=self.groq_model,
            temperature=0,
        )

        self.structured_llm = (
            self.llm.with_structured_output(
                CandidateEvaluationOutput,
                method="json_mode",
            )
        )
    async def score_candidate(
        self,
        job_description: JobDescriptionScoringInput,
        candidate: CandidateScoringInput,
    ) -> CandidateScoringResult:
        try:
            schema_json = json.dumps(
                CandidateEvaluationOutput.model_json_schema(),
                indent=2,
            )

            payload = {
                "job_description": (
                    job_description.model_dump(
                        mode="json",
                    )
                ),
                "candidate": (
                    candidate.model_dump(
                        mode="json",
                    )
                ),
            }

            messages = [
                SystemMessage(
                    content=(
                        "You are an expert technical recruiter.\n\n"

                        "Compare the candidate against the job description.\n\n"

                        "Your responsibilities:\n"
                        "- identify mandatory skill matches\n"
                        "- identify optional skill matches\n"
                        "- identify missing mandatory skills\n"
                        "- evaluate role fit\n"
                        "- evaluate education alignment\n\n"

                        "IMPORTANT:\n"
                        "- Be strict about mandatory skills.\n"
                        "- Do not invent skills or experience.\n"
                        "- Copy candidate_id exactly from the input.\n"
                        "- Do not generate a new candidate_id.\n\n"

                        "Skill Proficiency Matching:\n"
                        "- When comparing skills, assess the proficiency level match.\n"
                        "- For each matched skill (mandatory or optional), append a pipe and match quality float.\n"
                        "- Format: \"SkillName|quality\" where quality is a float between 0.0 and 1.0.\n"
                        "- Match quality values:\n"
                        "  1.0 = exact proficiency match, or candidate exceeds required level, or no proficiency specified on either side\n"
                        "  0.75 = candidate is roughly one level below the required proficiency (slight gap)\n"
                        "  0.4 = candidate is two or more levels below the required proficiency (significant gap)\n"
                        "- If a skill is completely absent from the candidate, do NOT include it in matched lists. Put it in missing_mandatory_skills instead (without a pipe suffix).\n"
                        "- Examples:\n"
                        "  JD requires \"Advanced Python\", candidate has \"Advanced Python\" → \"Python|1.0\"\n"
                        "  JD requires \"Advanced Python\", candidate has \"Expert Python\" → \"Python|1.0\"\n"
                        "  JD requires \"Advanced Python\", candidate has \"Python\" (intermediate inferred) → \"Python|0.75\"\n"
                        "  JD requires \"Advanced Python\", candidate has \"Basic Python\" → \"Python|0.4\"\n"
                        "  JD requires \"Python\", candidate has \"Python\" → \"Python|1.0\"\n"
                        "  JD requires \"Kubernetes\", candidate has no Kubernetes → missing_mandatory_skills: [\"Kubernetes\"]\n"
                        "- Document any proficiency gaps in the explanation weaknesses list.\n\n"

                        "Role Fit Scoring (0-12):\n"
                        "- 0 = no alignment\n"
                        "- 6 = moderate alignment\n"
                        "- 12 = excellent alignment\n\n"

                        "Education Scoring (0-8):\n"
                        "- 8 = exact match\n"
                        "- 7 = higher qualification\n"
                        "- 6 = related field\n"
                        "- 4 = same level only\n"
                        "- 0 = poor match\n\n"

                        "Confidence must be between 0 and 100.\n\n"

                        "Return JSON matching this schema:\n"
                        f"{schema_json}"
                    )
                ),
                HumanMessage(
                    content=json.dumps(
                        payload,
                        indent=2,
                    )
                ),
            ]

            result: CandidateEvaluationOutput = (
                await self.structured_llm.ainvoke(
                    messages,
                )
            )

            score = self._calculate_candidate_score(
                evaluation=result,
                job_description=job_description,
                candidate=candidate,
            )

            return CandidateScoringResult(
                payload=score,
                provider="groq",
            )

        except Exception:
            print("\n --- CANDIDATE SCORING FAILED --- ")
            traceback.print_exc()
            print("-----------------------------------\n")

            return CandidateScoringResult(
                payload=None,
                provider="fallback",
            )

    def _parse_skill_weight(
        self,
        skill_entry: str,
    ) -> tuple[str, float]:
        """Extract skill name and match quality from a pipe-delimited entry.

        Returns (skill_name, weight) where weight is clamped to [0.0, 1.0].
        If no pipe delimiter is found, weight defaults to 1.0 (backward compatible).
        """
        if "|" in skill_entry:
            parts = skill_entry.rsplit("|", 1)
            try:
                weight = float(parts[1])
                return parts[0], max(0.0, min(1.0, weight))
            except (ValueError, IndexError):
                return skill_entry, 1.0
        return skill_entry, 1.0

    def _calculate_candidate_score(
        self,
        evaluation: CandidateEvaluationOutput,
        job_description: JobDescriptionScoringInput,
        candidate: CandidateScoringInput,
    ) -> CandidateScoreOutput:
        skills_score = self._calculate_skills_score(
            evaluation,
            job_description,
        )

        experience_score = self._calculate_experience_score(
            candidate,
            job_description,
        )

        recency_score = self._calculate_recency_score(
            candidate,
        )

        final_score = (
            skills_score
            + experience_score
            + recency_score
            + evaluation.role_fit_score
            + evaluation.education_score
        )

        # Strip pipe-delimited weights from skill names before output.
        # The weights are consumed only by _calculate_skills_score above;
        # downstream consumers (persistence, API, frontend) receive clean names.
        clean_mandatory = [
            self._parse_skill_weight(s)[0]
            for s in evaluation.matched_mandatory_skills
        ]
        clean_optional = [
            self._parse_skill_weight(s)[0]
            for s in evaluation.matched_optional_skills
        ]

        return CandidateScoreOutput(
            candidate_id=evaluation.candidate_id,
            final_score=round(
                final_score,
                2,
            ),
            confidence=evaluation.confidence,
            skills_score=round(
                skills_score,
                2,
            ),
            experience_score=round(
                experience_score,
                2,
            ),
            recency_score=round(
                recency_score,
                2,
            ),
            role_fit_score=round(
                evaluation.role_fit_score,
                2,
            ),
            education_score=round(
                evaluation.education_score,
                2,
            ),
            matched_mandatory_skills=clean_mandatory,
            matched_optional_skills=clean_optional,
            missing_mandatory_skills=(
                evaluation.missing_mandatory_skills
            ),
            explanation=evaluation.explanation.model_dump(),
        )

    def _calculate_skills_score(
        self,
        evaluation: CandidateEvaluationOutput,
        job_description: JobDescriptionScoringInput,
    ) -> float:
        mandatory_skills = [
            skill
            for skill in job_description.skills
            if skill.is_mandatory
        ]

        optional_skills = [
            skill
            for skill in job_description.skills
            if not skill.is_mandatory
        ]

        mandatory_score = 0.0

        if mandatory_skills:
            weighted_sum = sum(
                self._parse_skill_weight(skill)[1]
                for skill in evaluation.matched_mandatory_skills
            )
            mandatory_score = (
                weighted_sum / len(mandatory_skills)
            ) * 28

        optional_score = 0.0

        if optional_skills:
            weighted_sum = sum(
                self._parse_skill_weight(skill)[1]
                for skill in evaluation.matched_optional_skills
            )
            optional_score = (
                weighted_sum / len(optional_skills)
            ) * 12

        return mandatory_score + optional_score

    def _calculate_experience_score(
        self,
        candidate: CandidateScoringInput,
        job_description: JobDescriptionScoringInput,
    ) -> float:
        candidate_years = (
            candidate.total_experience_months / 12
        )

        min_years = job_description.min_experience

        max_years = job_description.max_experience

        if candidate_years < min_years:
            ratio = candidate_years / max(
                min_years,
                1,
            )

            return max(
                0,
                ratio * 25,
            )

        if candidate_years <= max_years:
            return 25

        excess_years = (
            candidate_years - max_years
        )

        decay = min(
            excess_years * 0.5,
            10,
        )

        return max(
            15,
            25 - decay,
        )

    def _calculate_recency_score(
        self,
        candidate: CandidateScoringInput,
    ) -> float:
        if not candidate.experiences:
            return 0

        current_experience = any(
            experience.is_current
            for experience in candidate.experiences
        )

        if current_experience:
            return 15

        latest_end_date = max(
            (
                experience.end_date
                for experience in candidate.experiences
                if experience.end_date is not None
            ),
            default=None,
        )

        if latest_end_date is None:
            return 5

        years_since = (
            date.today() - latest_end_date
        ).days / 365

        if years_since <= 1:
            return 13.5

        if years_since <= 2:
            return 11.25

        if years_since <= 3:
            return 8.25

        if years_since <= 4:
            return 5.25

        return 3.5

@dataclass(slots=True)
class CandidatePrescoringResult:
    payload: CandidatePrescoreBatchOutput | None
    provider: str

class CandidatePrescoringClient:
    def __init__(self) -> None:
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0,
        )

        self.structured_llm = (
            self.llm.with_structured_output(
                CandidatePrescoreBatchOutput,
                method="json_mode",
            )
        )

    async def prescore_candidates(
        self,
        candidates: list[CompressedCandidate],
        job_description: CompressedJobDescription,
    ) -> CandidatePrescoreBatchOutput:

        schema_json = json.dumps(
            CandidatePrescoreBatchOutput.model_json_schema(),
            indent=2,
        )

        payload = {
            "job_description": (
                job_description.model_dump(
                    mode="json",
                )
            ),
            "candidates": [
                candidate.model_dump(
                    mode="json",
                )
                for candidate in candidates
            ],
        }

        messages = [
            SystemMessage(
                content=(
                    "You are a recruiting pre-screening engine.\n\n"

                    "Evaluate each candidate using broad semantic matching.\n"
                    "Assign a preliminary score from 0 to 100 indicating how promising "
                    "the candidate is for further evaluation.\n\n"

                    "Use the FULL scoring range, not just 0, 50, or 100.\n"
                    "Choose the score that best reflects the overall strength of the match.\n\n"

                    "Scoring guide:\n"
                    "90-100 : Exceptional match, highly recommended.\n"
                    "75-89  : Strong match with only minor gaps.\n"
                    "60-74  : Good match but several noticeable gaps.\n"
                    "40-59  : Partial match, worth reviewing if needed.\n"
                    "20-39  : Weak match with significant gaps.\n"
                    "0-19   : Clear mismatch.\n\n"

                    "Do NOT round to multiples of 10 or 25 unless they are truly appropriate.\n"
                    "Scores such as 67, 73, 81, 88, and 94 are perfectly acceptable.\n\n"

                    "IMPORTANT:\n"
                    "- Copy candidate_id exactly.\n"
                    "- Return only valid JSON.\n\n"

                    "Return JSON matching:\n"
                    f"{schema_json}"
                )
            ),
            HumanMessage(
                content=json.dumps(
                    payload,
                    indent=2,
                )
            ),
        ]

        return await self.structured_llm.ainvoke(
            messages,
        )
