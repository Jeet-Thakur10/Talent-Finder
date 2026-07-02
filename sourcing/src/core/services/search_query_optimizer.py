from src.control.agents.candidate_search_strategy_agent import (
    CandidateSearchStrategyAgent,
)
from src.core.services.search_strategies import (
    GeneralizedTitleStrategy,
    RepresentativeSkillsStrategy,
    SingleCoreSkillStrategy,
    TitleOnlyStrategy,
)
from src.schemas.candidate_search_request import CandidateSearchRequest
from src.schemas.search_attempt import SearchAttempt, SearchOptimizationPlan


class SearchQueryOptimizer:
    def __init__(self, agent: CandidateSearchStrategyAgent) -> None:
        self._agent = agent
        self._plan: SearchOptimizationPlan | None = None
        self._strategies = [
            RepresentativeSkillsStrategy(),
            GeneralizedTitleStrategy(),
            SingleCoreSkillStrategy(),
            TitleOnlyStrategy(),
        ]

    async def initialize(self, original_request: CandidateSearchRequest) -> None:
        """Generate the optimization plan once at the beginning
        of the sourcing session."""
        self._plan = await self._agent.optimize(original_request)

    def get_plan(self) -> SearchOptimizationPlan | None:
        """Retrieve the generated optimization plan."""
        return self._plan

    async def get_optimized_request(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> tuple[CandidateSearchRequest, str]:
        """Sequence and apply optimization strategies based on history length."""
        attempt_idx = len(history)

        if attempt_idx >= len(self._strategies):
            strategy = self._strategies[-1]
        else:
            strategy = self._strategies[attempt_idx]

        optimized_request = await strategy.optimize(original_request, self._plan)
        reason = strategy.get_reason()

        return optimized_request, reason
