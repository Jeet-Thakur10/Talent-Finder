import { useState, useEffect, useCallback } from "react";
import { hiringManagerService } from "../services/hiringManager.service";
import type { HMCampaign } from "../services/hiringManager.types";
import type { CandidateEvaluationBoard } from "../../dashboard/services/dashboard.types";

export function useCandidateReview(
  jobDescriptionId: string | undefined,
  candidateId: string | undefined
) {
  const [evaluationBoard, setEvaluationBoard] = useState<CandidateEvaluationBoard | null>(null);
  const [campaign, setCampaign] = useState<HMCampaign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!jobDescriptionId || !candidateId) {
      setError("Missing campaign or candidate identifiers.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const [board, campaignsList] = await Promise.all([
        hiringManagerService.getCandidateDetails(jobDescriptionId, candidateId),
        hiringManagerService.getSharedCampaigns(),
      ]);

      setEvaluationBoard(board);

      const foundCampaign = campaignsList.find((c) => c.id === jobDescriptionId) || null;
      setCampaign(foundCampaign);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load candidate details. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }, [jobDescriptionId, candidateId]);

  const saveReview = useCallback(
    async (decision: "PENDING" | "INTERVIEW_SENT" | "REJECTED", remarks: string) => {
      if (!jobDescriptionId || !candidateId) return false;

      try {
        setIsSaving(true);
        setError(null);

        const response = await hiringManagerService.submitCandidateReview(
          jobDescriptionId,
          candidateId,
          {
            decision,
            remarks: remarks.trim() || null,
          }
        );

        // Update local evaluationBoard state with response to reflect changes instantly
        setEvaluationBoard((current) => {
          if (!current) return null;
          return {
            ...current,
            pipeline: current.pipeline
              ? {
                  ...current.pipeline,
                  hiring_manager_notes: response.hiring_manager_notes,
                }
              : null,
          };
        });

        // Also update local campaign counts if needed, but since it requires a refresh, the hook returns true
        return true;
      } catch (err: any) {
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Failed to save candidate review decision. Please try again."
        );
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [jobDescriptionId, candidateId]
  );

  const scheduleHMInterview = useCallback(
    async (payload: {
      interview_link: string;
      interview_datetime: string;
      timezone: string;
      message: string | null;
    }) => {
      if (!jobDescriptionId || !candidateId) return false;

      try {
        setIsSaving(true);
        setError(null);

        const response = await hiringManagerService.scheduleInterview(
          jobDescriptionId,
          candidateId,
          payload
        );

        // Update local evaluationBoard state with response to reflect changes instantly
        setEvaluationBoard((current) => {
          if (!current) return null;
          return {
            ...current,
            pipeline: current.pipeline
              ? {
                  ...current.pipeline,
                  interview_link: response.interview_link,
                  interview_datetime: response.interview_datetime,
                  interview_timezone: response.interview_timezone,
                  interview_message: response.interview_message,
                }
              : null,
          };
        });

        return true;
      } catch (err: any) {
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Failed to schedule interview. Please try again."
        );
        return false;
      } finally {
        setIsSaving(false);
      }
    },
    [jobDescriptionId, candidateId]
  );

  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    evaluationBoard,
    campaign,
    isLoading,
    isSaving,
    error,
    saveReview,
    scheduleHMInterview,
    retry: loadData,
  };
}
