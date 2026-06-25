from __future__ import annotations

import json
import math
from datetime import date
import traceback
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from huggingface_hub import InferenceClient

from src.config.settings import settings
from src.schemas.scoring_schema import CandidateEvaluationOutput, CandidatePrescoreBatchOutput, CompressedCandidate, CompressedJobDescription, ResumeCandidateOutput

from src.schemas.scoring_schema import (
    CandidateScoringInput,
    CandidateScoreOutput,
    JobDescriptionScoringInput,
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
            print(f"🚀 Attempting Groq extraction with model: {self.groq_model}")
            
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

        except Exception as e:
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
            matched_mandatory_skills=(
                evaluation.matched_mandatory_skills
            ),
            matched_optional_skills=(
                evaluation.matched_optional_skills
            ),
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
            mandatory_score = (
                len(
                    evaluation.matched_mandatory_skills,
                )
                / len(mandatory_skills)
            ) * 28

        optional_score = 0.0

        if optional_skills:
            optional_score = (
                len(
                    evaluation.matched_optional_skills,
                )
                / len(optional_skills)
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

                    "Evaluate each candidate quickly.\n"

                    "Use broad semantic matching.\n"

                    "The score should represent whether "
                    "the candidate is worth deeper scoring.\n\n"

                    "0 = obvious mismatch\n"
                    "50 = possible fit\n"
                    "100 = excellent fit\n\n"

                    "IMPORTANT:\n"
                    "Copy candidate_id exactly.\n"

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


class SemanticEmbeddingClient:
    def __init__(self) -> None:
        self.provider = settings.SCORING_EMBEDDING_PROVIDER
        self.model_name = settings.HF_EMBEDDING_MODEL

        self.client = InferenceClient(
            api_key=settings.HF_TOKEN,
        )

        self._cache: dict[str, list[float]] = {}

    def similarity(
        self,
        left_text: str,
        right_text: str,
    ) -> float:
        left_vector, right_vector = self.embed_texts(
            [left_text, right_text]
        )

        return self._cosine_similarity(
            left_vector,
            right_vector,
        )

    def best_similarity(
        self,
        target_text: str,
        candidates: list[str],
    ) -> tuple[float, str | None]:
        best_score = 0.0
        best_value: str | None = None

        target_vector = self.embed_texts(
            [target_text]
        )[0]

        for candidate in candidates:
            if not candidate:
                continue

            candidate_vector = self.embed_texts(
                [candidate]
            )[0]

            score = self._cosine_similarity(
                target_vector,
                candidate_vector,
            )

            if score > best_score:
                best_score = score
                best_value = candidate

        return best_score, best_value

    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        results: list[list[float]] = []

        missing_texts: list[str] = []
        missing_indices: list[int] = []

        for index, text in enumerate(texts):
            cached = self._cache.get(text)

            if cached is None:
                missing_texts.append(text)
                missing_indices.append(index)
                results.append([])
            else:
                results.append(cached)

        if missing_texts:
            vectors = []

            for text in missing_texts:
                vector = self.client.feature_extraction(
                    text,
                    model=self.model_name,
                )

                vectors.append(
                    [float(value) for value in vector]
                )

            for idx, vector in zip(
                missing_indices,
                vectors,
                strict=False,
            ):
                self._cache[texts[idx]] = vector
                results[idx] = vector

        return results

    def _cosine_similarity(
        self,
        left_vector: list[float],
        right_vector: list[float],
    ) -> float:
        if not left_vector or not right_vector:
            return 0.0

        numerator = sum(
            left * right
            for left, right in zip(
                left_vector,
                right_vector,
                strict=False,
            )
        )

        left_norm = math.sqrt(
            sum(value * value for value in left_vector)
        )

        right_norm = math.sqrt(
            sum(value * value for value in right_vector)
        )

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return numerator / (
            left_norm * right_norm
        )

