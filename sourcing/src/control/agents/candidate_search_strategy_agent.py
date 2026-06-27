from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config.settings import settings
from src.schemas.candidate_search_request import CandidateSearchRequest
from src.schemas.search_attempt import SearchAttempt, SearchOptimizationPlan


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
        history: list[SearchAttempt],
        remaining: int,
    ) -> SearchOptimizationPlan:
        schema_json = json.dumps(
            SearchOptimizationPlan.model_json_schema(),
            indent=2,
        )

        history_summary = []
        for attempt in history:
            history_summary.append(
                f"Attempt {attempt.attempt_number}:\n"
                f"  Title: {attempt.title}\n"
                f"  Skills: {attempt.skills}\n"
                f"  Resumes Found: {attempt.resumes_found}\n"
                f"  New Unique Candidates Persisted: {attempt.new_candidates_persisted}\n"
                f"  Reasoning: {attempt.reason}\n"
                f"  URL: {attempt.query_url}"
            )
        history_text = "\n\n".join(history_summary) if history_summary else "None"

        system_prompt = (
            "You are an expert search strategy advisor for candidate sourcing.\n\n"
            "Your task is to analyze the original search criteria and the history of previous search attempts, "
            "and suggest how to relax the search parameters to find more resumes on PostJobFree.\n\n"
            "STRICT CONSTRAINTS:\n"
            "1. You must ONLY generalize the Job Title (e.g., 'Lead Backend Python Engineer' -> 'Python Developer').\n"
            "2. You must ONLY suggest skills to remove from the search criteria (skills_to_remove).\n"
            "3. You must NEVER invent technologies, tools, or skills that are not present in the original CandidateSearchRequest.\n"
            "4. You must NEVER reduce the minimum experience requirement or alter core recruiter intent (e.g. don't look for Java developers if they want Python).\n\n"
            "OBJECTIVE:\n"
            "Suggest adjustments to maximize the candidate pool size while remaining faithful to the original recruiter request.\n\n"
            "Return a JSON object matching exactly this schema:\n"
            f"{schema_json}"
        )

        human_content = (
            f"ORIGINAL REQUEST:\n"
            f"Title: {original_request.title}\n"
            f"Skills: {original_request.skills}\n"
            f"Min Experience: {original_request.min_experience}\n"
            f"Candidates Still Required: {remaining}\n\n"
            f"ATTEMPT HISTORY:\n"
            f"{history_text}\n"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        try:
            result: SearchOptimizationPlan = await self._structured_llm.ainvoke(messages)
            return result
        except Exception as exc:
            # Fallback optimization plan on error: drop some skills
            print(f"[CandidateSearchStrategyAgent] Error invoking Groq LLM: {exc}")
            # Try to return a safe fallback: keep original title, suggest removing the last skill
            fallback_skills = []
            if original_request.skills:
                fallback_skills = [original_request.skills[-1]]
            return SearchOptimizationPlan(
                generalize_title=original_request.title,
                skills_to_remove=fallback_skills,
                reason="Groq agent invocation failed; falling back to dropping the last skill.",
            )
