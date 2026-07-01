from __future__ import annotations

import json
import traceback

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from src.config.settings import settings
from src.control.agents.prompts import CANDIDATE_SEARCH_QUERY_PROMPT
from src.data.models.postgres.job_description import JobDescription
from src.schemas.candidate_search_schema import (
    CandidateSearchQueryOutput,
    CandidateSearchRequest,
)
from src.schemas.job_description_schema import JobDescriptionResponse
from src.schemas.scoring_schema import JobDescriptionScoringInput


class CandidateSearchQueryAgent:
    def __init__(self) -> None:
        # Use LangChain's native HuggingFaceEndpoint and ChatHuggingFace wrapper
        self._endpoint = HuggingFaceEndpoint(
            repo_id=settings.HF_MODEL,
            task="text-generation",
            huggingfacehub_api_token=settings.HF_TOKEN,
            temperature=0.0,
            max_new_tokens=4096,
        )
        self._llm = ChatHuggingFace(llm=self._endpoint)

        # with_structured_output using json_mode returns a dictionary matching the schema
        self._structured_llm = self._llm.with_structured_output(
            CandidateSearchQueryOutput,
            method="json_mode",
        )

    def generate_search_query(
        self,
        job_description: JobDescription | JobDescriptionResponse | JobDescriptionScoringInput,
        min_candidates: int,
        max_source_resumes: int,
    ) -> CandidateSearchRequest:
        try:
            # Extract skills list
            skill_names = []
            if job_description.skills:
                # Support both models/schemas (each has skill_name field)
                skill_names = [skill.skill_name for skill in job_description.skills]

            input_data = {
                "title": job_description.title,
                "min_experience": job_description.min_experience,
                "skills": skill_names,
            }

            schema_json = json.dumps(
                CandidateSearchQueryOutput.model_json_schema(),
                indent=2,
            )

            system_content = CANDIDATE_SEARCH_QUERY_PROMPT.format(
                schema_json=schema_json
            )

            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=json.dumps(input_data, indent=2)),
            ]

            result_dict = self._structured_llm.invoke(messages)
            if not result_dict:
                # Return default/fallback request
                return CandidateSearchRequest(
                    title=job_description.title,
                    skills=[s for s in skill_names],
                    min_experience=job_description.min_experience,
                    min_candidates=min_candidates,
                    max_source_resumes=max_source_resumes,
                )

            # Validate the returned dictionary into CandidateSearchQueryOutput model
            query_output = CandidateSearchQueryOutput.model_validate(result_dict)

            # Construct the final CandidateSearchRequest schema combining generated and passed fields
            return CandidateSearchRequest(
                title=query_output.title,
                skills=query_output.skills,
                min_experience=query_output.min_experience,
                min_candidates=min_candidates,
                max_source_resumes=max_source_resumes,
            )

        except Exception:
            print("\n --- CANDIDATE SEARCH QUERY GENERATION CRASHED --- ")
            traceback.print_exc()
            print("--------------------------------------------------\n")

            # Return default/fallback request on failure
            fallback_skills = []
            if job_description.skills:
                fallback_skills = [skill.skill_name for skill in job_description.skills]

            return CandidateSearchRequest(
                title=job_description.title,
                skills=fallback_skills,
                min_experience=job_description.min_experience,
                min_candidates=min_candidates,
                max_source_resumes=max_source_resumes,
            )
