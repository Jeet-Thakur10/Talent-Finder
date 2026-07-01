from __future__ import annotations

import json
import traceback

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from src.config.settings import settings
from src.control.agents.prompts import JOB_DESCRIPTION_EXTRACTION_PROMPT
from src.schemas.job_description_extraction_schema import JobDescriptionExtraction


class JobDescriptionExtractionAgent:
    def __init__(self) -> None:
        # Use LangChain's native HuggingFaceEndpoint and ChatHuggingFace wrapper
        self._endpoint = HuggingFaceEndpoint(
            repo_id=settings.HF_MODEL,
            task="text-generation",
            huggingfacehub_api_token=settings.HF_TOKEN,
            temperature=0.01,
            max_new_tokens=4096,
        )
        self._llm = ChatHuggingFace(llm=self._endpoint)

        # with_structured_output using json_mode returns a dictionary matching the schema
        self._structured_llm = self._llm.with_structured_output(
            JobDescriptionExtraction,
            method="json_mode",
        )

    def extract(self, raw_job_description: str) -> JobDescriptionExtraction:
        try:
            schema_json = json.dumps(
                JobDescriptionExtraction.model_json_schema(),
                indent=2,
            )

            system_content = JOB_DESCRIPTION_EXTRACTION_PROMPT.format(
                schema_json=schema_json
            )

            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=raw_job_description.strip()),
            ]

            result_dict = self._structured_llm.invoke(messages)
            if not result_dict:
                return JobDescriptionExtraction()

            # Parse and validate the returned dictionary into the Pydantic model
            return JobDescriptionExtraction.model_validate(result_dict)

        except Exception:
            print("\n --- JOB DESCRIPTION EXTRACTION CRASHED --- ")
            traceback.print_exc()
            print("-------------------------------------------\n")

            # Return a default JobDescriptionExtraction model with all fields set to null/empty
            return JobDescriptionExtraction()
