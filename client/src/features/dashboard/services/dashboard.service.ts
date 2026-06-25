import { api } from "../../../lib/api";

import type { JobDescription } from "./dashboard.types";

export const dashboardService = {
  async listJobDescriptions(): Promise<JobDescription[]> {
    const response =
      await api.get<JobDescription[]>(
        "/job-descriptions",
      );

    return response.data;
  },

  async getJobDescription(
    jobDescriptionId: string,
  ): Promise<JobDescription> {
    const response =
      await api.get<JobDescription>(
        `/job-descriptions/${jobDescriptionId}`,
      );

    return response.data;
  },
};
