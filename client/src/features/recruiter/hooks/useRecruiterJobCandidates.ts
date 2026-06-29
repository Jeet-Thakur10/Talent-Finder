import { useEffect, useState, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type {
  JobDescription,
  PipelineCandidateResult,
  JobDescriptionStatus,
  HiringManager,
} from "../../dashboard/services/dashboard.types";

export function useRecruiterJobCandidates(jobDescriptionId: string | undefined) {
  const [jobDescription, setJobDescription] = useState<JobDescription | null>(null);
  const [candidates, setCandidates] = useState<PipelineCandidateResult[]>([]);
  const [statuses, setStatuses] = useState<JobDescriptionStatus[]>([]);
  const [hiringManagers, setHiringManagers] = useState<HiringManager[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCandidatesAndJob = useCallback(async () => {
    if (!jobDescriptionId) {
      setError("No Job Description ID provided.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const [job, rankedCandidates, lookupsStatuses, lookupsManagers] = await Promise.all([
        dashboardService.getJobDescription(jobDescriptionId),
        dashboardService.listRankedCandidates(jobDescriptionId),
        dashboardService.listJobDescriptionStatuses(),
        dashboardService.listHiringManagers(),
      ]);

      setJobDescription(job);
      setStatuses(lookupsStatuses);
      setHiringManagers(lookupsManagers);

      // Sort candidates by final_score descending
      const sorted = [...rankedCandidates].sort((a, b) => {
        const scoreA = a.final_score ?? 0;
        const scoreB = b.final_score ?? 0;
        return scoreB - scoreA;
      });
      setCandidates(sorted);
    } catch {
      setError("Unable to load scored candidates. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  }, [jobDescriptionId]);

  useEffect(() => {
    void fetchCandidatesAndJob();
  }, [fetchCandidatesAndJob]);

  return {
    jobDescription,
    candidates,
    statuses,
    hiringManagers,
    isLoading,
    error,
    refetch: fetchCandidatesAndJob,
  };
}
