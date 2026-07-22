from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID


class StageStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class CandidateTerminalOutcome(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED_SYNCHRONIZATION = "FAILED_SYNCHRONIZATION"
    FAILED_SCORING = "FAILED_SCORING"
    FAILED_PERSISTENCE = "FAILED_PERSISTENCE"
    SKIPPED_THRESHOLD = "SKIPPED_THRESHOLD"
    SKIPPED_TOP_K = "SKIPPED_TOP_K"


@dataclass
class StageOutcome:
    status: StageStatus = StageStatus.PENDING
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: float = 0.0


@dataclass
class CandidateMetrics:
    prescore: int | None = None
    prescore_rank: int | None = None
    final_score: float | None = None
    confidence: float | None = None


@dataclass
class CandidateDiagnostics:
    acquisition: StageOutcome = field(default_factory=StageOutcome)
    prescoring: StageOutcome = field(default_factory=StageOutcome)
    synchronization: StageOutcome = field(default_factory=StageOutcome)
    scoring: StageOutcome = field(default_factory=StageOutcome)
    persistence: StageOutcome = field(default_factory=StageOutcome)


@dataclass
class PipelineCandidateState:
    candidate_id: UUID
    profile_text: str | None = None

    # Terminal Outcome
    terminal_outcome: CandidateTerminalOutcome = CandidateTerminalOutcome.PENDING

    # Lifecycle Stage Statuses
    acquisition: StageStatus = StageStatus.PENDING
    prescoring: StageStatus = StageStatus.PENDING
    synchronization: StageStatus = StageStatus.PENDING
    scoring: StageStatus = StageStatus.PENDING
    persistence: StageStatus = StageStatus.PENDING

    # Metrics and Diagnostics (Typed Dataclasses)
    metrics: CandidateMetrics = field(default_factory=CandidateMetrics)
    diagnostics: CandidateDiagnostics = field(default_factory=CandidateDiagnostics)

    # Atomic state transition methods
    def mark_acquired(self, duration_ms: float = 0.0) -> None:
        self.acquisition = StageStatus.SUCCESS
        self.diagnostics.acquisition = StageOutcome(
            status=StageStatus.SUCCESS, duration_ms=duration_ms
        )

    def mark_prescored(self, prescore: int, duration_ms: float = 0.0) -> None:
        self.prescoring = StageStatus.SUCCESS
        self.metrics.prescore = prescore
        self.diagnostics.prescoring = StageOutcome(
            status=StageStatus.SUCCESS, duration_ms=duration_ms
        )

    def mark_skipped_threshold(self) -> None:
        self.terminal_outcome = CandidateTerminalOutcome.SKIPPED_THRESHOLD
        self.synchronization = StageStatus.SKIPPED
        self.scoring = StageStatus.SKIPPED
        self.persistence = StageStatus.SKIPPED

    def mark_skipped_top_k(self, rank: int) -> None:
        self.terminal_outcome = CandidateTerminalOutcome.SKIPPED_TOP_K
        self.metrics.prescore_rank = rank
        self.synchronization = StageStatus.SKIPPED
        self.scoring = StageStatus.SKIPPED
        self.persistence = StageStatus.SKIPPED

    def mark_selected(self, rank: int) -> None:
        self.terminal_outcome = CandidateTerminalOutcome.PENDING
        self.metrics.prescore_rank = rank

    def mark_synchronization_success(self, duration_ms: float = 0.0) -> None:
        self.synchronization = StageStatus.SUCCESS
        self.diagnostics.synchronization = StageOutcome(
            status=StageStatus.SUCCESS, duration_ms=duration_ms
        )

    def mark_synchronization_failed(
        self, error_code: str, error_message: str, duration_ms: float = 0.0
    ) -> None:
        self.synchronization = StageStatus.FAILED
        self.terminal_outcome = CandidateTerminalOutcome.FAILED_SYNCHRONIZATION
        self.scoring = StageStatus.SKIPPED
        self.persistence = StageStatus.SKIPPED
        self.diagnostics.synchronization = StageOutcome(
            status=StageStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
            duration_ms=duration_ms,
        )

    def mark_scoring_success(
        self, final_score: float, confidence: float, duration_ms: float = 0.0
    ) -> None:
        self.scoring = StageStatus.SUCCESS
        self.metrics.final_score = final_score
        self.metrics.confidence = confidence
        self.diagnostics.scoring = StageOutcome(
            status=StageStatus.SUCCESS, duration_ms=duration_ms
        )

    def mark_scoring_failed(
        self, error_code: str, error_message: str, duration_ms: float = 0.0
    ) -> None:
        self.scoring = StageStatus.FAILED
        self.terminal_outcome = CandidateTerminalOutcome.FAILED_SCORING
        self.persistence = StageStatus.SKIPPED
        self.diagnostics.scoring = StageOutcome(
            status=StageStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
            duration_ms=duration_ms,
        )

    def mark_persistence_success(self, duration_ms: float = 0.0) -> None:
        self.persistence = StageStatus.SUCCESS
        self.terminal_outcome = CandidateTerminalOutcome.SUCCESS
        self.diagnostics.persistence = StageOutcome(
            status=StageStatus.SUCCESS, duration_ms=duration_ms
        )

    def mark_persistence_failed(
        self, error_code: str, error_message: str, duration_ms: float = 0.0
    ) -> None:
        self.persistence = StageStatus.FAILED
        self.terminal_outcome = CandidateTerminalOutcome.FAILED_PERSISTENCE
        self.diagnostics.persistence = StageOutcome(
            status=StageStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
            duration_ms=duration_ms,
        )


@dataclass
class PipelineExecutionContext:
    execution_id: UUID
    job_description_id: UUID
    recruiter_id: UUID
    candidates: dict[UUID, PipelineCandidateState] = field(default_factory=dict)
