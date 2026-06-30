from src.schemas.candidate_search_request import CandidateSearchRequest
from src.schemas.search_attempt import SearchAttempt
from src.core.services.search_strategies import SearchOptimizationStrategy


class SearchQueryOptimizer:
    def __init__(self, strategies: list[SearchOptimizationStrategy]) -> None:
        self._strategies = strategies

    async def get_optimized_request(
        self,
        original_request: CandidateSearchRequest,
        history: list[SearchAttempt],
    ) -> tuple[CandidateSearchRequest, str]:
        """Sequence and apply optimization strategies based on history length."""
        attempt_idx = len(history)

        if attempt_idx >= len(self._strategies):
            # Fall back to the last strategy in sequence (typically LLMStrategy)
            strategy = self._strategies[-1]
        else:
            strategy = self._strategies[attempt_idx]

        optimized_request = await strategy.optimize(original_request, history)
        reason = strategy.get_reason()

        return optimized_request, reason
