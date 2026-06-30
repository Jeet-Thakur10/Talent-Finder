import { api } from "../../../lib/api";

import type {
  CandidateDetails,
  CandidateImportRequest,
  CandidateImportResponse,
  CandidateListItem,
  CandidateScore,
} from "./scoring.types";

export const scoringService = {
  async importCandidate(
    data: CandidateImportRequest,
  ): Promise<CandidateImportResponse> {
    const response =
      await api.post<CandidateImportResponse>(
        "/scoring/candidates/import",
        data,
      );

    return response.data;
  },

  async listCandidatesForJob(
    jobDescriptionId: string,
  ): Promise<CandidateListItem[]> {
    const response =
      await api.get<CandidateListItem[]>(
        `/scoring/jobs/${jobDescriptionId}/candidates`,
      );

    return response.data;
  },

  async getCandidateDetails(
    jobDescriptionId: string,
    candidateId: string,
  ): Promise<CandidateDetails> {
    const response =
      await api.get<CandidateDetails>(
        `/scoring/jobs/${jobDescriptionId}/candidates/${candidateId}`,
      );

    return response.data;
  },

  async getCandidateScore(
    jobDescriptionId: string,
    candidateId: string,
  ): Promise<CandidateScore> {
    const response =
      await api.get<CandidateScore>(
        `/scoring/jobs/${jobDescriptionId}/candidates/${candidateId}/score`,
      );

    return response.data;
  },

  async rescoreCandidate(
    jobDescriptionId: string,
    candidateId: string,
  ): Promise<CandidateScore> {
    const response =
      await api.post<CandidateScore>(
        `/scoring/jobs/${jobDescriptionId}/candidates/${candidateId}/rescore`,
      );

    return response.data;
  },
};
