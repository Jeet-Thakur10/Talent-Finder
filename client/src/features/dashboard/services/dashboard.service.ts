import { api } from "../../../lib/api";

import type {
  CandidateEvaluationBoard,
  EmploymentType,
  HiringManager,
  JobDescription,
  JobDescriptionPayload,
  JobDescriptionStatus,
  PipelineExecutionPayload,
  PipelineNotesPayload,
  PipelineSnapshot,
  PipelineStagePayload,
  PipelineCandidateResult,
  PipelineEnqueueResponse,
  PipelineTaskStatus,
} from "./dashboard.types";

export const dashboardService = {
  async listEmploymentTypes(): Promise<
    EmploymentType[]
  > {
    const response =
      await api.get<EmploymentType[]>(
        "/lookups/employment-types",
      );

    return response.data;
  },

  async listHiringManagers(): Promise<
    HiringManager[]
  > {
    const response =
      await api.get<HiringManager[]>(
        "/lookups/hiring-managers",
      );

    return response.data;
  },

  async listJobDescriptionStatuses(): Promise<
    JobDescriptionStatus[]
  > {
    const response =
      await api.get<JobDescriptionStatus[]>(
        "/lookups/job-description-statuses",
      );

    return response.data;
  },

  async listJobDescriptions(): Promise<
    JobDescription[]
  > {
    const response =
      await api.get<JobDescription[]>(
        "/job-descriptions",
      );

    return response.data;
  },

  async extractJobDescription(
    raw_job_description: string,
  ): Promise<JobDescription> {
    const response = await api.post<JobDescription>(
      "/job-descriptions/extract",
      { raw_job_description },
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

  async createJobDescription(
    data: JobDescriptionPayload,
  ): Promise<JobDescription> {
    const response =
      await api.post<JobDescription>(
        "/job-descriptions",
        data,
      );

    return response.data;
  },

  async updateJobDescription(
    jobDescriptionId: string,
    data: JobDescriptionPayload,
  ): Promise<JobDescription> {
    const response =
      await api.put<JobDescription>(
        `/job-descriptions/${jobDescriptionId}`,
        data,
      );

    return response.data;
  },

  async previewPipeline(
    jobDescriptionId: string,
    payload: Omit<
      PipelineExecutionPayload,
      "confirm"
    > & { minimum_prescore_threshold?: number },
  ): Promise<PipelineEnqueueResponse> {
    const response =
      await api.post<PipelineEnqueueResponse>(
        `/scoring/${jobDescriptionId}/pipeline`,
        {
          ...payload,
          confirm: false,
        },
      );

    return response.data;
  },

  async executePipeline(
    jobDescriptionId: string,
    payload: Omit<
      PipelineExecutionPayload,
      "confirm"
    > & { minimum_prescore_threshold?: number },
  ): Promise<PipelineEnqueueResponse> {
    const response =
      await api.post<PipelineEnqueueResponse>(
        `/scoring/${jobDescriptionId}/pipeline`,
        {
          ...payload,
          confirm: true,
        },
      );

    return response.data;
  },

  async listRankedCandidates(
    jobDescriptionId: string,
  ): Promise<PipelineCandidateResult[]> {
    const response =
      await api.get<
        PipelineCandidateResult[]
      >(
        `/scoring/jobs/${jobDescriptionId}/candidates`,
      );

    return response.data;
  },

  async getCandidateEvaluationBoard(
    jobDescriptionId: string,
    candidateId: string,
  ): Promise<CandidateEvaluationBoard> {
    const response =
      await api.get<CandidateEvaluationBoard>(
        `/scoring/jobs/${jobDescriptionId}/candidates/${candidateId}/board`,
      );

    return response.data;
  },

  async updatePipelineNotes(
    jobDescriptionId: string,
    candidateId: string,
    payload: PipelineNotesPayload,
  ): Promise<PipelineSnapshot> {
    const response =
      await api.patch<PipelineSnapshot>(
        `/scoring/jobs/${jobDescriptionId}/candidates/${candidateId}/pipeline-notes`,
        payload,
      );

    return response.data;
  },

  async updatePipelineStage(
    jobDescriptionId: string,
    payload: PipelineStagePayload,
  ): Promise<PipelineSnapshot[]> {
    const response =
      await api.patch<PipelineSnapshot[]>(
        `/scoring/jobs/${jobDescriptionId}/pipeline-stage`,
        payload,
      );

    return response.data;
  },

  async listRecruiterTasks(): Promise<PipelineTaskStatus[]> {
    const response =
      await api.get<PipelineTaskStatus[]>(
        "/scoring/tasks",
      );

    return response.data;
  },

  async shareShortlist(
    jobDescriptionId: string,
    payload: {
      candidate_ids: string[];
      notes_by_candidate: Record<string, string>;
    }
  ): Promise<{ message: string; shared_candidate_count: number }> {
    const response = await api.post<{ message: string; shared_candidate_count: number }>(
      `/scoring/recruiter/job-descriptions/${jobDescriptionId}/share`,
      payload
    );
    return response.data;
  },
};
