import { useState, useEffect, useCallback } from "react";
import { hiringManagerService } from "../services/hiringManager.service";
import type { HMCampaign, HMSharedCandidate } from "../services/hiringManager.types";

export function useCampaignCandidates(jobDescriptionId: string | undefined) {
  const [campaign, setCampaign] = useState<HMCampaign | null>(null);
  const [candidates, setCandidates] = useState<HMSharedCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!jobDescriptionId) return;

    try {
      setIsLoading(true);
      setError(null);

      // Fetch campaigns list (to find campaign metadata) and shared candidates in parallel
      const [campaignsList, candidatesList] = await Promise.all([
        hiringManagerService.getSharedCampaigns(),
        hiringManagerService.getSharedCandidates(jobDescriptionId),
      ]);

      const foundCampaign = campaignsList.find((c) => c.id === jobDescriptionId) || null;
      setCampaign(foundCampaign);

      // Apply the required sorting:
      // 1. Pending Review first, then Accepted, then Rejected
      // 2. Descending by final_score (match score) within each group
      const decisionRanks = { PENDING: 0, INTERVIEW_SENT: 1, REJECTED: 2 };
      const sortedCandidates = [...candidatesList].sort((a, b) => {
        const rankA = decisionRanks[a.hm_decision] ?? 0;
        const rankB = decisionRanks[b.hm_decision] ?? 0;

        if (rankA !== rankB) {
          return rankA - rankB;
        }

        return (b.final_score ?? 0) - (a.final_score ?? 0);
      });

      setCandidates(sortedCandidates);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load campaign shortlist candidates. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  }, [jobDescriptionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    campaign,
    candidates,
    isLoading,
    error,
    retry: loadData,
  };
}
