from __future__ import annotations

import json
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.settings import settings
from src.control.agents.groq_client import RotationalChatGroq as ChatGroq
from src.schemas.candidate_search_request import CandidateSearchRequest
from src.schemas.search_attempt import SearchOptimizationPlan


class CandidateSearchStrategyAgent:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0,
        )
        self._structured_llm = self._llm.with_structured_output(
            SearchOptimizationPlan,
            method="json_mode",
        )

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
    ) -> SearchOptimizationPlan:
        schema_json = json.dumps(
            SearchOptimizationPlan.model_json_schema(),
            indent=2,
        )

        system_prompt = (
            "You are an experienced technical recruiter specializing in candidate sourcing.\n\n"
            "Your task is to analyze the original job description query and generate a recruiter-oriented search optimization plan for resume databases.\n\n"
            "INSTRUCTIONS:\n"
            "1. First, determine the SINGLE most likely hiring archetype represented by the Job Description (e.g., Frontend Engineer, Backend Engineer, Full Stack Engineer, Machine Learning Engineer, Data Engineer, DevOps Engineer, Mobile Engineer).\n"
            "2. If the JD contains technologies from multiple unrelated domains, you must NOT hedge or mix them. Choose the ONE archetype that best represents the primary recruiter hiring intent, and select title/skills for that single archetype only. Do not mix frontend frameworks and machine learning libraries in the same plan.\n"
            "3. Ignore technologies, libraries, and tools that are merely supportive or common utilities. Select only the 2-3 defining technologies already present in the original request that best define that single chosen archetype.\n"
            "4. Order the list of 'representative_skills' by technical importance / recruiter priority for the chosen archetype (e.g., core language first, primary framework/library second).\n"
            "5. Never invent new technologies, tools, frameworks, certifications, or cloud providers that are not in the original request.\n"
            "6. Generalize the job title into a common industry title that technical candidates are likely to use on their resumes for this archetype (e.g., 'Software Development Engineer II' -> 'Software Engineer', 'Backend Engineer' -> 'Software Engineer', 'ML Engineer' -> 'Machine Learning Engineer').\n"
            "7. The generalized title must remain semantically equivalent and match the chosen archetype. Never invent unrelated roles.\n\n"
            "Return a JSON object matching exactly this schema:\n"
            f"{schema_json}"
        )

        human_content = (
            f"ORIGINAL REQUEST:\n"
            f"Title: {original_request.title}\n"
            f"Skills: {original_request.skills}\n"
            f"Min Experience: {original_request.min_experience}\n"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        try:
            result = cast(
                SearchOptimizationPlan,
                await self._structured_llm.ainvoke(messages),
            )
            return result
        except Exception as exc:
            # Fallback optimization plan on error: drop some skills
            print(f"[CandidateSearchStrategyAgent] Error invoking Groq LLM: {exc}")
            # Try to return a safe fallback: keep original title, suggest first 3 skills
            fallback_skills = (
                original_request.skills[:3]
                if original_request.skills
                else []
            )
            return SearchOptimizationPlan(
                inferred_role="Backend Engineer",
                representative_title=original_request.title,
                representative_skills=fallback_skills,
                reasoning="Fallback optimization plan",
            )
