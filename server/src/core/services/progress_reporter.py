from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.services.scoring_task_service import ScoringTaskService


class PipelineProgressReporter(ABC):
    """Abstract interface for reporting stage transitions in the
      scoring pipeline."""

    @abstractmethod
    async def update_stage(self, stage: str) -> None:
        """Update the current execution stage of the pipeline."""
        pass


class NoOpProgressReporter(PipelineProgressReporter):
    """A no-op implementation of PipelineProgressReporter for when
      progress updates are not needed (e.g. sync runs, tests)."""

    async def update_stage(self, stage: str) -> None:
        pass


class DatabaseProgressReporter(PipelineProgressReporter):
    """Database-backed implementation of PipelineProgressReporter that
    updates a ScoringTask table record via ScoringTaskService."""

    def __init__(self, scoring_task_service: ScoringTaskService, task_id: UUID):
        self.service = scoring_task_service
        self.task_id = task_id

    async def update_stage(self, stage: str) -> None:
        await self.service.update_task_stage(self.task_id, stage)
