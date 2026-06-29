import { api } from "../../../lib/api";
import type { CandidateEvaluationBoard } from "../../dashboard/services/dashboard.types";
import type { HMCampaign, HMSharedCandidate } from "./hiringManager.types";

export const hiringManagerService = {
  async getSharedCampaigns(): Promise<HMCampaign[]> {
    const response = await api.get<HMCampaign[]>("/scoring/hm/campaigns");
    return response.data;
  },

  async getSharedCandidates(jobDescriptionId: string): Promise<HMSharedCandidate[]> {
    const response = await api.get<HMSharedCandidate[]>(
      `/scoring/hm/campaigns/${jobDescriptionId}/candidates`
    );
    return response.data;
  },

  async getCandidateDetails(jobDescriptionId: string, candidateId: string): Promise<CandidateEvaluationBoard> {
    const response = await api.get<CandidateEvaluationBoard>(
      `/scoring/hm/campaigns/${jobDescriptionId}/candidates/${candidateId}/board`
    );
    return response.data;
  },

  async submitCandidateReview(
    jobDescriptionId: string,
    candidateId: string,
    payload: { decision: "PENDING" | "INTERVIEW_SENT" | "REJECTED"; remarks: string | null }
  ): Promise<{ message: string; candidate_id: string; hm_decision: string; hiring_manager_notes: string | null }> {
    const response = await api.post(
      `/scoring/hm/campaigns/${jobDescriptionId}/candidates/${candidateId}/review`,
      payload
    );
    return response.data;
  },

  async scheduleInterview(
    jobDescriptionId: string,
    candidateId: string,
    payload: {
      interview_link: string;
      interview_datetime: string;
      timezone: string;
      message: string | null;
    }
  ): Promise<{
    message: string;
    candidate_id: string;
    hm_decision: string;
    interview_link: string;
    interview_datetime: string;
    interview_timezone: string;
    interview_message: string | null;
  }> {
    const response = await api.post(
      `/scoring/hm/campaigns/${jobDescriptionId}/candidates/${candidateId}/schedule-interview`,
      payload
    );
    return response.data;
  },
};
