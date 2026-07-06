from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class CandidateSyncResultItem:
    candidate_id: UUID
    success: bool
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: float = 0.0

@dataclass
class SyncBatchResult:
    results: dict[UUID, CandidateSyncResultItem] = field(default_factory=dict)
