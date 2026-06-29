import { useState, useEffect, useCallback } from "react";
import { hiringManagerService } from "../services/hiringManager.service";
import type { HMCampaign } from "../services/hiringManager.types";

export function useSharedCampaigns() {
  const [campaigns, setCampaigns] = useState<HMCampaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await hiringManagerService.getSharedCampaigns();
      setCampaigns(data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load shared campaigns. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  return {
    campaigns,
    isLoading,
    error,
    retry: fetchCampaigns,
  };
}
