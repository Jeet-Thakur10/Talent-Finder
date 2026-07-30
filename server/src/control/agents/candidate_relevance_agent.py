from __future__ import annotations

import json
import logging
import traceback
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.control.agents.groq_client import RotationalChatGroq as ChatGroq
from src.control.agents.prompts import CANDIDATE_RELEVANCE_VERIFICATION_PROMPT
from src.schemas.scoring_schema import (
    CandidateRelevanceReason,
    JobDescriptionScoringInput,
    RelevanceStatus,
)

logger = logging.getLogger(__name__)


class CandidateRelevanceAuditItem(BaseModel):
    candidate_id: UUID
    relevance_status: RelevanceStatus
    relevance_reason: CandidateRelevanceReason


class BatchRelevanceAuditOutput(BaseModel):
    evaluations: list[CandidateRelevanceAuditItem] = Field(default_factory=list)


class CandidateRelevanceAgent:
    def __init__(self) -> None:
        self.groq_model = settings.GROQ_MODEL

    async def verify_relevance_batch(
        self,
        job_description: JobDescriptionScoringInput,
        candidates_input: list[dict[str, Any]],
    ) -> dict[UUID, CandidateRelevanceAuditItem]:
        """Perform a single-batch relevance audit for all shortlisted candidates.

        Returns a mapping from candidate_id to CandidateRelevanceAuditItem.
        """
        if not candidates_input:
            return {}

        try:
            schema_json = json.dumps(
                BatchRelevanceAuditOutput.model_json_schema(),
                indent=2,
            )

            payload = {
                "job_description": job_description.model_dump(mode="json"),
                "shortlisted_candidates": candidates_input,
            }

            system_content = CANDIDATE_RELEVANCE_VERIFICATION_PROMPT.format(
                schema_json=schema_json
            )

            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=json.dumps(payload, indent=2)),
            ]

            llm = ChatGroq(
                model=self.groq_model,
                temperature=0,
            )

            structured_llm = llm.with_structured_output(
                BatchRelevanceAuditOutput,
                method="json_mode",
            )

            result: BatchRelevanceAuditOutput = await structured_llm.ainvoke(messages)  # type: ignore[assignment]

            output_map: dict[UUID, CandidateRelevanceAuditItem] = {}
            if result and hasattr(result, "evaluations"):
                for item in result.evaluations:
                    output_map[item.candidate_id] = item

            logger.info(
                f"CandidateRelevanceAgent successfully audited {len(output_map)} candidates."
            )
            return output_map

        except Exception as e:
            logger.error(f"CandidateRelevanceAgent batch verification failed: {e}")
            print("\n --- CANDIDATE RELEVANCE AUDIT FAILED --- ")
            traceback.print_exc()
            print("-------------------------------------------\n")

            # Fallback for error resilience: Return default partial relevance for inputs
            fallback_map: dict[UUID, CandidateRelevanceAuditItem] = {}
            for cand in candidates_input:
                cid_str = cand.get("candidate_id")
                if cid_str:
                    try:
                        cid = UUID(str(cid_str))
                        fallback_map[cid] = CandidateRelevanceAuditItem(
                            candidate_id=cid,
                            relevance_status=RelevanceStatus.PARTIALLY_RELEVANT,
                            relevance_reason=CandidateRelevanceReason(
                                experience="Evaluated via fallback",
                                role="Evaluated via fallback",
                                skills="Evaluated via fallback",
                                location="Evaluated via fallback",
                                recency="Evaluated via fallback",
                                summary="Verification fallback applied due to temporary AI timeout.",
                            ),
                        )
                    except ValueError:
                        pass
            return fallback_map
