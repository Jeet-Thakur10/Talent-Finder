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
                    "Extract candidate information from the resume.\n"
                    "Return all available information.\n"
                    "Do not invent information that is not present.\n"
                    "Dates should be returned in ISO format "
                    "(YYYY-MM-DD) whenever possible.\n\n"
                    "CRITICAL: You must respond strictly with a "
                    "valid JSON object matching this exact schema:\n"
                    f"{schema_json}"
                ),
            ),
            HumanMessage(
                content=resume_text.strip(),
            ),
        ]

        result: ResumeCandidateOutput = (
            self._structured_llm.invoke(
                messages,
            )
        )

        return ResumeExtractionResult(
            payload=result,
            provider="groq",
        )