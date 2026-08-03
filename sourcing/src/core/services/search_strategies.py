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
    def __init__(self, keep_location: bool = True) -> None:
        self._reason = ""
        self._keep_location = keep_location

    async def optimize(
        self,
        original_request: CandidateSearchRequest,
        plan: SearchOptimizationPlan | None,
    ) -> CandidateSearchRequest:
        # If keep_location is True and the request has a physical location,
        # we perform the initial local search: Job Title + Location only (no skills).
        if self._keep_location and original_request.location and original_request.location.strip():
            skills = []
            new_loc = original_request.location
            reasoning = "Initial local broad search (Job Title + Location only, no skills)."
        else:
            skills = plan.representative_skills if plan else original_request.skills
            new_loc = None
            reasoning = plan.reasoning if plan else "Fallback using original skills."

        location_desc = (
            "with location"
            if (self._keep_location and original_request.location)
            else "global"
        )
        self._reason = (
            f"Recruiter-optimized search (representative skills only, {location_desc}). "
            f"Reasoning: {reasoning}"
        )
        return original_request.model_copy(update={"skills": skills, "location": new_loc})

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
            f"representative skills, global). Reasoning: {reasoning}"
        )
        return original_request.model_copy(update={"title": title, "skills": skills, "location": None})

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
            f"single most important skill: {skills}, global)."
        )
        return original_request.model_copy(update={"title": title, "skills": skills, "location": None})

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
            "dropping all skill constraints (global)."
        )
        return original_request.model_copy(update={"title": title, "skills": [], "location": None})

    def get_reason(self) -> str:
        return self._reason


