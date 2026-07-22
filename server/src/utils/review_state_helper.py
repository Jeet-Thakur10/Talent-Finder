"""Helper functions for evaluating Hiring Manager candidate review state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.data.models.postgres.pipeline import HiringManagerDecision

if TYPE_CHECKING:
    from src.data.models.postgres.pipeline import Pipeline


def has_pipeline_entry_review_started(entry: Pipeline) -> bool:
    """Determines whether a Hiring Manager has started reviewing an entry.

    Review is considered started if:
    - hm_decision is set and is NOT PENDING (e.g. INTERVIEW_SENT or REJECTED)
    - hiring_manager_notes is not None and not empty
    - interview_sent_at or interview_link is set
    """
    if (
        entry.hm_decision is not None
        and entry.hm_decision != HiringManagerDecision.PENDING
    ):
        return True
    if (
        entry.hiring_manager_notes is not None
        and entry.hiring_manager_notes.strip() != ""
    ):
        return True
    return entry.interview_sent_at is not None or entry.interview_link is not None


def has_campaign_review_started(pipeline_entries: list[Pipeline]) -> bool:
    """Determines whether HM review has started on any shared shortlist candidate."""
    shared_entries = [p for p in pipeline_entries if p.shared_with_hiring_manager]
    return any(has_pipeline_entry_review_started(p) for p in shared_entries)
