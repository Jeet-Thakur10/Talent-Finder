import { useEffect, useState, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type {
  JobDescription,
  EmploymentType,
  HiringManager,
  JobDescriptionStatus,
} from "../../dashboard/services/dashboard.types";

export function useRecruiterJobDescriptionDetail(jobDescriptionId: string | undefined) {
  const [jobDescription, setJobDescription] = useState<JobDescription | null>(null);
  const [employmentTypes, setEmploymentTypes] = useState<EmploymentType[]>([]);
  const [hiringManagers, setHiringManagers] = useState<HiringManager[]>([]);
  const [statuses, setStatuses] = useState<JobDescriptionStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobDescription = useCallback(async () => {
    if (!jobDescriptionId) {
      setError("No Job Description ID provided.");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const [job, lookupsEmployment, lookupsManagers, lookupsStatuses] = await Promise.all([
        dashboardService.getJobDescription(jobDescriptionId),
        dashboardService.listEmploymentTypes(),
        dashboardService.listHiringManagers(),
        dashboardService.listJobDescriptionStatuses(),
      ]);

      setJobDescription(job);
      setEmploymentTypes(lookupsEmployment);
      setHiringManagers(lookupsManagers);
      setStatuses(lookupsStatuses);
    } catch (err: any) {
      if (err?.response?.status === 404) {
        setError("Job Description not found.");
      } else {
        setError("Unable to load Job Description details. Please try again later.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [jobDescriptionId]);

  useEffect(() => {
    void fetchJobDescription();
  }, [fetchJobDescription]);

  return {
    jobDescription,
    employmentTypes,
    hiringManagers,
    statuses,
    isLoading,
    error,
    refetch: fetchJobDescription,
  };
}
