from __future__ import annotations

import json

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq

from src.config.settings import settings
from src.schemas.resume_candidate_output import (
    ResumeCandidateOutput,
)
from src.schemas.resume_extraction_result import (
    ResumeExtractionResult,
)


class ResumeExtractionAgent:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0,
        )

        self._structured_llm = (
            self._llm.with_structured_output(
                ResumeCandidateOutput,
                method="json_mode",
            )
        )

    def extract(
        self,
        resume_text: str,
    ) -> ResumeExtractionResult:

        schema_json = json.dumps(
            ResumeCandidateOutput.model_json_schema(),
            indent=2,
        )

        messages = [
            SystemMessage(
                content=(
                    "You are an expert resume parser.\n\n"

                    "Before extracting any information, determine whether "
                    "the resume is predominantly written in English.\n\n"

                    "Ignore programming language names such as Python, Java, "
                    "JavaScript, C++, SQL, React, FastAPI, AWS, Docker, "
                    "Kubernetes and other technical keywords when determining "
                    "the language.\n\n"

                    "If the resume is predominantly written in a language "
                    "other than English, return an EMPTY JSON object matching "
                    "the schema below.\n\n"

                    "If the resume is in English:\n"
                    "- Extract all available information.\n"
                    "- Do not invent information.\n"
                    "- Dates should be returned in ISO format "
                    "(YYYY-MM-DD) whenever possible.\n\n"

                    "When extracting skills:\n"
                    "- Preserve the proficiency level ONLY if it is explicitly "
                    "mentioned in the resume.\n"
                    "- Examples:\n"
                    "  * 'Python (Basic)' -> 'Basic Python'\n"
                    "  * 'Basic knowledge of Java' -> 'Basic Java'\n"
                    "  * 'Intermediate SQL' -> 'Intermediate SQL'\n"
                    "  * 'Advanced React' -> 'Advanced React'\n"
                    "- Do NOT invent or assume proficiency.\n"
                    "- If no proficiency is explicitly mentioned, return only "
                    "the skill name.\n\n"

                    "Return a JSON object matching exactly this schema:\n"
                    f"{schema_json}"
                ),
            ),
            HumanMessage(
                content=resume_text.strip(),
            ),
        ]

        try:

            result: ResumeCandidateOutput = (
                self._structured_llm.invoke(
                    messages,
                )
            )

        except Exception:

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error="Failed to extract resume.",
            )

        #
        # Reject empty / non-English resumes
        #

        if (
            not result.full_name.strip()
            and not result.skills
            and not result.experiences
            and not result.educations
        ):

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=(
                    "Resume is either non-English or "
                    "contains insufficient information."
                ),
            )

        return ResumeExtractionResult(
            success=True,
            payload=result,
            provider="groq",
        )