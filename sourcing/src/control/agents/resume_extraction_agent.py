from __future__ import annotations

import json
import logging
from typing import cast

import httpx
from groq import APIError, RateLimitError
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from pydantic import ValidationError

from src.config.settings import settings
from src.control.agents.groq_client import RotationalChatGroq as ChatGroq
from src.schemas.resume_candidate_output import (
    ResumeCandidateOutput,
)
from src.schemas.resume_extraction_result import (
    ResumeExtractionResult,
)

logger = logging.getLogger(__name__)


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

    def _format_pydantic_error(self, exc: ValidationError) -> str:
        try:
            errors = []
            for err in exc.errors():
                field = ".".join(str(loc) for loc in err["loc"])
                if err.get("type") == "missing":
                    errors.append(f"{field} is missing")
                else:
                    errors.append(f"{field}: {err.get('msg')}")
            return f"Structured output validation failed: {', '.join(errors)}."
        except Exception:
            return f"Structured output validation failed: {str(exc)}"

    def extract(
        self,
        resume_text: str,
        resume_url: str | None = None,
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

        print("Invoking Groq extraction...\n")

        try:
            result = cast(
                ResumeCandidateOutput,
                self._structured_llm.invoke(
                    messages,
                ),
            )

            print("Groq extraction completed.\n")
            print("Validating structured output...\n")
            print("Validation passed.\n")

        except (ValidationError, OutputParserException) as exc:
            print("Groq extraction completed.\n")
            print("Validating structured output...\n")

            if isinstance(exc, ValidationError):
                stage = "Pydantic validation"
                error_code = "EXTRACTION_VALIDATION"
                error_msg = self._format_pydantic_error(exc)
            else:
                stage = "Structured output validation"
                error_code = "EXTRACTION_OUTPUT_PARSER"
                error_msg = f"Structured output validation failed: {str(exc)}"

            logger.error(
                "Resume extraction failed during stage: '%s'\n"
                "Provider: groq\n"
                "Resume URL: %s\n"
                "Error Code: %s\n"
                "Error Message: %s",
                stage,
                resume_url or "N/A",
                error_code,
                error_msg,
                exc_info=True
            )

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=error_msg,
                error_code=error_code,
                failure_stage=stage,
            )

        except RateLimitError:
            stage = "Provider rate limiting"
            error_code = "EXTRACTION_RATE_LIMIT"
            error_msg = "Groq Rate Limit (429)."

            logger.error(
                "Resume extraction failed during stage: '%s'\n"
                "Provider: groq\n"
                "Resume URL: %s\n"
                "Error Code: %s\n"
                "Error Message: %s",
                stage,
                resume_url or "N/A",
                error_code,
                error_msg,
                exc_info=True
            )

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=error_msg,
                error_code=error_code,
                failure_stage=stage,
            )

        except (httpx.TimeoutException, TimeoutError):
            stage = "Groq API"
            error_code = "EXTRACTION_TIMEOUT"
            error_msg = "Groq request timed out."

            logger.error(
                "Resume extraction failed during stage: '%s'\n"
                "Provider: groq\n"
                "Resume URL: %s\n"
                "Error Code: %s\n"
                "Error Message: %s",
                stage,
                resume_url or "N/A",
                error_code,
                error_msg,
                exc_info=True
            )

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=error_msg,
                error_code=error_code,
                failure_stage=stage,
            )

        except httpx.RequestError:
            stage = "Network errors"
            error_code = "EXTRACTION_NETWORK"
            error_msg = "Groq request failed due to connection issue."

            logger.error(
                "Resume extraction failed during stage: '%s'\n"
                "Provider: groq\n"
                "Resume URL: %s\n"
                "Error Code: %s\n"
                "Error Message: %s",
                stage,
                resume_url or "N/A",
                error_code,
                error_msg,
                exc_info=True
            )

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=error_msg,
                error_code=error_code,
                failure_stage=stage,
            )

        except APIError as exc:
            stage = "Groq API"
            error_code = "EXTRACTION_UNKNOWN"
            error_msg = f"Groq API error: {str(exc)}"

            logger.error(
                "Resume extraction failed during stage: '%s'\n"
                "Provider: groq\n"
                "Resume URL: %s\n"
                "Error Code: %s\n"
                "Error Message: %s",
                stage,
                resume_url or "N/A",
                error_code,
                error_msg,
                exc_info=True
            )

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=error_msg,
                error_code=error_code,
                failure_stage=stage,
            )

        except Exception as exc:
            stage = "Any unexpected exception"
            error_code = "EXTRACTION_UNKNOWN"
            error_msg = f"Unexpected exception: {str(exc)}"

            logger.error(
                "Resume extraction failed during stage: '%s'\n"
                "Provider: groq\n"
                "Resume URL: %s\n"
                "Error Code: %s\n"
                "Error Message: %s",
                stage,
                resume_url or "N/A",
                error_code,
                error_msg,
                exc_info=True
            )

            return ResumeExtractionResult(
                success=False,
                provider="groq",
                error=error_msg,
                error_code=error_code,
                failure_stage=stage,
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
                error_code="EXTRACTION_VALIDATION",
                failure_stage="Structured output validation",
            )

        return ResumeExtractionResult(
            success=True,
            payload=result,
            provider="groq",
        )
