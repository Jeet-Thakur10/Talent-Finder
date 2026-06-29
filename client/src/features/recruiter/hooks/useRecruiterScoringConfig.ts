import { useState, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";

export function useRecruiterScoringConfig(jobDescriptionId: string | undefined) {
  const [k, setK] = useState(10);
  const [minPrescoreThreshold, setMinPrescoreThreshold] = useState(0);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submitScoring = useCallback(async () => {
    if (!jobDescriptionId) {
      setError("No Job Description ID provided.");
      return;
    }

    // Client-side validations
    if (k < 1 || k > 25) {
      setError("Final Shortlist Size (k) must be between 1 and 25.");
      return;
    }

    if (minPrescoreThreshold < 0 || minPrescoreThreshold > 100) {
      setError("Minimum Pre-score Threshold must be between 0 and 100.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await dashboardService.executePipeline(jobDescriptionId, {
        k,
        minimum_prescore_threshold: minPrescoreThreshold,
      });

      setTaskId(response.task_id);
      setIsSuccess(true);
    } catch {
      setError("Failed to trigger background candidate scoring task. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }, [jobDescriptionId, k, minPrescoreThreshold]);

  return {
    k,
    setK,
    minPrescoreThreshold,
    setMinPrescoreThreshold,
    isSubmitting,
    isSuccess,
    taskId,
    error,
    setError,
    submitScoring,
  };
}
