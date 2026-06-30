from abc import ABC, abstractmethod
from src.schemas.candidate_search_request import CandidateSearchRequest
from src.schemas.search_attempt import SearchAttempt
from src.control.agents.candidate_search_strategy_agent import CandidateSearchStrategyAgent


class SearchOptimizationStrategy(ABC):
    @abstractmethod
    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> CandidateSearchRequest:
        """Derive an optimized CandidateSearchRequest from the original request."""
        pass

    @abstractmethod
    def get_reason(self) -> str:
        """Get the reason/explanation for this search query relaxation."""
        pass


class OriginalQueryStrategy(SearchOptimizationStrategy):
    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> CandidateSearchRequest:
        return original_request.model_copy()

    def get_reason(self) -> str:
        return "Search with original title and all requested skills."


class MandatorySkillsStrategy(SearchOptimizationStrategy):
    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> CandidateSearchRequest:
        # Relax query by keeping only the top 2 skills, dropping lower-priority ones
        relaxed_skills = (
            original_request.skills[:2]
            if len(original_request.skills) > 2
            else original_request.skills
        )
        return original_request.model_copy(update={"skills": relaxed_skills})

    def get_reason(self) -> str:
        return "Deterministic relaxation: keep top-priority skills, drop lower-priority skills."


class TitleOnlyStrategy(SearchOptimizationStrategy):
    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> CandidateSearchRequest:
        # Relax query by dropping all skills and searching purely by job title
        return original_request.model_copy(update={"skills": []})

    def get_reason(self) -> str:
        return "Deterministic relaxation: drop all skills, search purely by job title."


class LLMOptimizationStrategy(SearchOptimizationStrategy):
    def __init__(self, agent: CandidateSearchStrategyAgent) -> None:
        self._agent = agent
        self._last_reason = ""

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> CandidateSearchRequest:
        remaining = (
            history[-1].candidates_remaining
            if history
            else original_request.required_candidates
        )

        plan = await self._agent.optimize(original_request, history, remaining)
        self._last_reason = plan.reason or "LLM-driven query relaxation plan."

        # Apply LLM plan transformations to the original request
        new_title = plan.generalize_title if plan.generalize_title else original_request.title

        skills_to_remove = {s.lower().strip() for s in plan.skills_to_remove}
        new_skills = [
            s
            for s in original_request.skills
            if s.lower().strip() not in skills_to_remove
        ]

        return original_request.model_copy(update={
            "title": new_title,
            "skills": new_skills,
        })

    def get_reason(self) -> str:
        return self._last_reason or "LLM-driven query relaxation."
