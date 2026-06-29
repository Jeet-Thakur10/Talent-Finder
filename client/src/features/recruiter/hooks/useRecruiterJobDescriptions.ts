import { useEffect, useState, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type {
  JobDescription,
  EmploymentType,
  HiringManager,
  JobDescriptionStatus,
} from "../../dashboard/services/dashboard.types";

export function useRecruiterJobDescriptions() {
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([]);
  const [employmentTypes, setEmploymentTypes] = useState<EmploymentType[]>([]);
  const [hiringManagers, setHiringManagers] = useState<HiringManager[]>([]);
  const [statuses, setStatuses] = useState<JobDescriptionStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobDescriptions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [jobs, lookupsEmployment, lookupsManagers, lookupsStatuses] = await Promise.all([
        dashboardService.listJobDescriptions(),
        dashboardService.listEmploymentTypes(),
        dashboardService.listHiringManagers(),
        dashboardService.listJobDescriptionStatuses(),
      ]);

      setJobDescriptions(jobs);
      setEmploymentTypes(lookupsEmployment);
      setHiringManagers(lookupsManagers);
      setStatuses(lookupsStatuses);
    } catch {
      setError("Unable to load job descriptions. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchJobDescriptions();
  }, [fetchJobDescriptions]);

  return {
    jobDescriptions,
    employmentTypes,
    hiringManagers,
    statuses,
    isLoading,
    error,
    refetch: fetchJobDescriptions,
  };
}
