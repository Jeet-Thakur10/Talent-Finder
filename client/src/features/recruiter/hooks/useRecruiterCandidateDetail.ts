import { useEffect, useState, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type {
  CandidateEvaluationBoard,
  JobDescription,
} from "../../dashboard/services/dashboard.types";

export function useRecruiterCandidateDetail(
  jobDescriptionId: string | undefined,
  candidateId: string | undefined
) {
  const [evaluationBoard, setEvaluationBoard] = useState<CandidateEvaluationBoard | null>(null);
  const [jobDescription, setJobDescription] = useState<JobDescription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!jobDescriptionId || !candidateId) {
      setError("Missing Job Description ID or Candidate ID.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const [board, job] = await Promise.all([
        dashboardService.getCandidateEvaluationBoard(jobDescriptionId, candidateId),
        dashboardService.getJobDescription(jobDescriptionId),
      ]);

      setEvaluationBoard(board);
      setJobDescription(job);
    } catch {
      setError("Unable to load candidate evaluation details. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  }, [jobDescriptionId, candidateId]);

  const saveRemarks = useCallback(async (notes: string) => {
    if (!jobDescriptionId || !candidateId) return false;

    try {
      setIsSavingNotes(true);
      setError(null);
      const updatedSnapshot = await dashboardService.updatePipelineNotes(jobDescriptionId, candidateId, {
        recruiter_notes: notes.trim() || null,
      });

      setEvaluationBoard((current) => {
        if (!current) return null;
        return {
          ...current,
          pipeline: updatedSnapshot,
        };
      });
      return true;
    } catch {
      setError("Failed to save remarks. Please try again.");
      return false;
    } finally {
      setIsSavingNotes(false);
    }
  }, [jobDescriptionId, candidateId]);

  useEffect(() => {
    void fetchDetail();
  }, [fetchDetail]);

  return {
    evaluationBoard,
    jobDescription,
    isLoading,
    isSavingNotes,
    error,
    saveRemarks,
    refetch: fetchDetail,
  };
}
