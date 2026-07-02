from abc import ABC, abstractmethod

from src.schemas.candidate_search_request import CandidateSearchRequest
from src.schemas.search_attempt import SearchOptimizationPlan


class SearchOptimizationStrategy(ABC):
    @abstractmethod
    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        plan: SearchOptimizationPlan | None,
    ) -> CandidateSearchRequest:
        """Derive an optimized CandidateSearchRequest from the original
           request using the optimization plan."""
        pass

    @abstractmethod
    def get_reason(self) -> str:
        """Get the reason/explanation for this search query."""
        pass


class RepresentativeSkillsStrategy(SearchOptimizationStrategy):
    def __init__(self) -> None:
        self._reason = ""

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        plan: SearchOptimizationPlan | None,
    ) -> CandidateSearchRequest:
        skills = plan.representative_skills if plan else original_request.skills
        reasoning = plan.reasoning if plan else "Fallback using original skills."
        self._reason = (
            "Recruiter-optimized search (representative skills only). "
            f"Reasoning: {reasoning}"
        )
        return original_request.model_copy(update={"skills": skills})

    def get_reason(self) -> str:
        return self._reason


class GeneralizedTitleStrategy(SearchOptimizationStrategy):
    def __init__(self) -> None:
        self._reason = ""

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        plan: SearchOptimizationPlan | None,
    ) -> CandidateSearchRequest:
        title = plan.representative_title if plan else original_request.title
        skills = plan.representative_skills if plan else original_request.skills
        reasoning = plan.reasoning if plan else "Fallback using original title/skills."
        self._reason = (
            "Generalized recruiter search (generalized title + "
            f"representative skills). Reasoning: {reasoning}"
        )
        return original_request.model_copy(update={"title": title, "skills": skills})

    def get_reason(self) -> str:
        return self._reason


class SingleCoreSkillStrategy(SearchOptimizationStrategy):
    def __init__(self) -> None:
        self._reason = ""

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        plan: SearchOptimizationPlan | None,
    ) -> CandidateSearchRequest:
        title = plan.representative_title if plan else original_request.title
        skills = (
            [plan.representative_skills[0]]
            if plan and plan.representative_skills
            else [original_request.skills[0]]
            if original_request.skills
            else []
        )
        self._reason = (
            "Broadened recruiter search (generalized title + "
            f"single most important skill: {skills})."
        )
        return original_request.model_copy(update={"title": title, "skills": skills})

    def get_reason(self) -> str:
        return self._reason


class TitleOnlyStrategy(SearchOptimizationStrategy):
    def __init__(self) -> None:
        self._reason = ""

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        plan: SearchOptimizationPlan | None,
    ) -> CandidateSearchRequest:
        title = plan.representative_title if plan else original_request.title
        self._reason = (
            "Broadest search: generalized job title only, "
            "dropping all skill constraints."
        )
        return original_request.model_copy(update={"title": title, "skills": []})

    def get_reason(self) -> str:
        return self._reason
