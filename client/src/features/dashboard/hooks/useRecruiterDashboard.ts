import { useEffect, useMemo, useState } from "react";

import { dashboardService } from "../services/dashboard.service";
import type {
  CandidateEvaluationBoard,
  EmploymentType,
  HiringManager,
  JDSkill,
  JobDescription,
  JobDescriptionPayload,
  PipelineCandidateResult,
  PipelineExecutionResponse,
} from "../services/dashboard.types";

export const PIPELINE_TOP_K = 10;
const FINALIZED_STAGE = "FINALIZED";
const SHORTLIST_THRESHOLD = 75;

export type DashboardNavView =
  | "job-campaigns"
  | "talent-pool";

export type DashboardCanvasView =
  | "campaigns"
  | "create"
  | "board";

export interface JobDescriptionFormValues {
  title: string;
  department: string;
  summary: string;
  responsibilities: string;
  min_experience: string;
  max_experience: string;
  location: string;
  employment_type_id: string;
  hiring_manager_id: string;
  education_requirement: string;
  preferred_qualifications: string;
  mandatory_skills: string[];
  optional_skills: string[];
}

function createEmptyFormValues(
  employmentTypeId = "",
  hiringManagerId = "",
): JobDescriptionFormValues {
  return {
    title: "",
    department: "",
    summary: "",
    responsibilities: "",
    min_experience: "0",
    max_experience: "0",
    location: "",
    employment_type_id: employmentTypeId,
    hiring_manager_id: hiringManagerId,
    education_requirement: "",
    preferred_qualifications: "",
    mandatory_skills: [""],
    optional_skills: [""],
  };
}

function mapJobToFormValues(
  job: JobDescription,
): JobDescriptionFormValues {
  return {
    title: job.title,
    department: job.department ?? "",
    summary: job.job_purpose,
    responsibilities: job.responsibilities,
    min_experience: String(
      job.min_experience,
    ),
    max_experience: String(
      job.max_experience,
    ),
    location: job.location,
    employment_type_id:
      job.employment_type_id,
    hiring_manager_id:
      job.hiring_manager_id ?? "",
    education_requirement:
      job.education_requirement,
    preferred_qualifications:
      job.preferred_qualifications ?? "",
    mandatory_skills:
      job.skills
        .filter(
          (skill) => skill.is_mandatory,
        )
        .map((skill) => skill.skill_name) ||
      [""],
    optional_skills:
      job.skills
        .filter(
          (skill) =>
            !skill.is_mandatory,
        )
        .map((skill) => skill.skill_name) ||
      [""],
  };
}

function buildSkills(
  values: JobDescriptionFormValues,
): JDSkill[] {
  return [
    ...values.mandatory_skills.map(
      (skill_name) => ({
        skill_name: skill_name.trim(),
        is_mandatory: true,
      }),
    ),
    ...values.optional_skills.map(
      (skill_name) => ({
        skill_name: skill_name.trim(),
        is_mandatory: false,
      }),
    ),
  ].filter(
    (skill) => skill.skill_name.length > 0,
  );
}

function toJobDescriptionPayload(
  values: JobDescriptionFormValues,
): JobDescriptionPayload {
  return {
    title: values.title.trim(),
    department:
      values.department.trim() || null,
    job_purpose: values.summary.trim(),
    responsibilities:
      values.responsibilities.trim() ||
      values.summary.trim(),
    min_experience: Number(
      values.min_experience,
    ),
    max_experience: Number(
      values.max_experience,
    ),
    location: values.location.trim(),
    employment_type_id:
      values.employment_type_id,
    hiring_manager_id:
      values.hiring_manager_id || null,
    education_requirement:
      values.education_requirement.trim(),
    preferred_qualifications:
      values.preferred_qualifications.trim() ||
      null,
    skills: buildSkills(values),
  };
}

export function useRecruiterDashboard() {
  const [activeNavView, setActiveNavView] =
    useState<DashboardNavView>(
      "job-campaigns",
    );
  const [canvasView, setCanvasView] =
    useState<DashboardCanvasView>(
      "campaigns",
    );
  const [jobDescriptions, setJobDescriptions] =
    useState<JobDescription[]>([]);
  const [employmentTypes, setEmploymentTypes] =
    useState<EmploymentType[]>([]);
  const [hiringManagers, setHiringManagers] =
    useState<HiringManager[]>([]);
  const [selectedJobId, setSelectedJobId] =
    useState<string | null>(null);
  const [draftJobId, setDraftJobId] =
    useState<string | null>(null);
  const [
    candidateResultsByJob,
    setCandidateResultsByJob,
  ] = useState<
    Record<
      string,
      PipelineCandidateResult[]
    >
  >({});
  const [
    matchedCountByJob,
    setMatchedCountByJob,
  ] = useState<Record<string, number>>(
    {},
  );
  const [
    formValues,
    setFormValues,
  ] = useState<JobDescriptionFormValues>(
    createEmptyFormValues(),
  );
  const [
    pipelinePreview,
    setPipelinePreview,
  ] = useState<PipelineExecutionResponse | null>(
    null,
  );
  const [
    activeCandidateId,
    setActiveCandidateId,
  ] = useState<string | null>(null);
  const [
    activeCandidateBoard,
    setActiveCandidateBoard,
  ] = useState<CandidateEvaluationBoard | null>(
    null,
  );
  const [
    selectedCandidateIds,
    setSelectedCandidateIds,
  ] = useState<string[]>([]);
  const [
    notesDraft,
    setNotesDraft,
  ] = useState("");
  const [isLoading, setIsLoading] =
    useState(true);
  const [isSavingJob, setIsSavingJob] =
    useState(false);
  const [isRunningPipeline, setIsRunningPipeline] =
    useState(false);
  const [isLoadingBoard, setIsLoadingBoard] =
    useState(false);
  const [isSavingNotes, setIsSavingNotes] =
    useState(false);
  const [
    isSharingShortlist,
    setIsSharingShortlist,
  ] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const bootstrapDashboard = async () => {
      try {
        setIsLoading(true);
        setError("");

        const [
          jobs,
          lookupEmploymentTypes,
          lookupHiringManagers,
        ] = await Promise.all([
          dashboardService.listJobDescriptions(),
          dashboardService.listEmploymentTypes(),
          dashboardService.listHiringManagers(),
        ]);

        setJobDescriptions(jobs);
        setEmploymentTypes(
          lookupEmploymentTypes,
        );
        setHiringManagers(
          lookupHiringManagers,
        );
        setSelectedJobId(
          jobs[0]?.id ?? null,
        );
        setFormValues(
          createEmptyFormValues(
            lookupEmploymentTypes[0]?.id ??
              "",
            lookupHiringManagers[0]?.id ??
              "",
          ),
        );

        if (jobs.length > 0) {
          const rankedEntries =
            await Promise.all(
              jobs.map(async (job) => [
                job.id,
                await dashboardService.listRankedCandidates(
                  job.id,
                ),
              ]),
            );

          setCandidateResultsByJob(
            Object.fromEntries(
              rankedEntries,
            ),
          );
        }
      } catch {
        setError(
          "Unable to load the recruiter dashboard right now.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    void bootstrapDashboard();
  }, []);

  const selectedJob = useMemo(
    () =>
      jobDescriptions.find(
        (job) => job.id === selectedJobId,
      ) ?? null,
    [jobDescriptions, selectedJobId],
  );

  const selectedCandidates =
    selectedJobId
      ? candidateResultsByJob[
          selectedJobId
        ] ?? []
      : [];


  const metrics = useMemo(() => {
    const allCandidates = Object.values(
      candidateResultsByJob,
    ).flat();

    return {
      activeJds:
        jobDescriptions.length,
      reviewedCandidates:
        allCandidates.length,
      pendingShortlists:
        allCandidates.filter(
          (candidate) =>
            candidate.stage !==
              FINALIZED_STAGE &&
            (candidate.final_score ?? 0) >=
              SHORTLIST_THRESHOLD,
        ).length,
    };
  }, [
    candidateResultsByJob,
    jobDescriptions.length,
  ]);

  const talentPool = useMemo(() => {
    const all = Object.values(candidateResultsByJob)
      .flat()
      .sort(
        (left, right) =>
          (right.final_score ?? 0) -
          (left.final_score ?? 0),
      );
    const seenIds = new Set<string>();
    return all.filter((c) => {
      if (seenIds.has(c.candidate_id)) {
        return false;
      }
      seenIds.add(c.candidate_id);
      return true;
    });
  }, [candidateResultsByJob]);

  const resetDrawer = () => {
    setActiveCandidateId(null);
    setActiveCandidateBoard(null);
    setNotesDraft("");
  };

  const dismissPipelinePreview = () => {
    setPipelinePreview(null);
  };

  const upsertJobDescription = (
    job: JobDescription,
  ) => {
    setJobDescriptions((currentJobs) => {
      const existingIndex =
        currentJobs.findIndex(
          (currentJob) =>
            currentJob.id === job.id,
        );

      if (existingIndex === -1) {
        return [job, ...currentJobs];
      }

      const nextJobs = [
        ...currentJobs,
      ];

      nextJobs[existingIndex] = job;

      return nextJobs;
    });
  };

  const refreshCandidatesForJob = async (
    jobId: string,
  ) => {
    const candidates =
      await dashboardService.listRankedCandidates(
        jobId,
      );

    setCandidateResultsByJob(
      (currentResults) => ({
        ...currentResults,
        [jobId]: candidates,
      }),
    );
  };

  const openCampaignBoard = async (
    job: JobDescription,
  ) => {
    setError("");
    setSelectedJobId(job.id);
    setCanvasView("board");
    setSelectedCandidateIds([]);
    resetDrawer();

    if (
      candidateResultsByJob[job.id] ===
      undefined
    ) {
      try {
        await refreshCandidatesForJob(job.id);
      } catch {
        setError(
          "Unable to load candidates for this campaign.",
        );
      }
    }
  };

  const startJobCreation = () => {
    setCanvasView("create");
    setDraftJobId(null);
    setPipelinePreview(null);
    setError("");
    resetDrawer();
    setFormValues(
      createEmptyFormValues(
        employmentTypes[0]?.id ?? "",
        hiringManagers[0]?.id ?? "",
      ),
    );
  };

  const editJob = (
    job: JobDescription,
  ) => {
    setCanvasView("create");
    setSelectedJobId(job.id);
    setDraftJobId(job.id);
    setPipelinePreview(null);
    setError("");
    setFormValues(
      mapJobToFormValues(job),
    );
  };

  const updateSkillArray = (
    field:
      | "mandatory_skills"
      | "optional_skills",
    index: number,
    value: string,
  ) => {
    setFormValues((currentValues) => ({
      ...currentValues,
      [field]: currentValues[field].map(
        (skill, skillIndex) =>
          skillIndex === index
            ? value
            : skill,
      ),
    }));
  };

  const addSkillField = (
    field:
      | "mandatory_skills"
      | "optional_skills",
  ) => {
    setFormValues((currentValues) => ({
      ...currentValues,
      [field]: [
        ...currentValues[field],
        "",
      ],
    }));
  };

  const removeSkillField = (
    field:
      | "mandatory_skills"
      | "optional_skills",
    index: number,
  ) => {
    setFormValues((currentValues) => {
      const nextValues =
        currentValues[field].filter(
          (_, skillIndex) =>
            skillIndex !== index,
        );

      return {
        ...currentValues,
        [field]:
          nextValues.length > 0
            ? nextValues
            : [""],
      };
    });
  };

  const submitJobForPreview = async () => {
    try {
      setIsSavingJob(true);
      setError("");

      const payload =
        toJobDescriptionPayload(
          formValues,
        );
      const savedJob = draftJobId
        ? await dashboardService.updateJobDescription(
            draftJobId,
            payload,
          )
        : await dashboardService.createJobDescription(
            payload,
          );

      upsertJobDescription(savedJob);
      setSelectedJobId(savedJob.id);
      setDraftJobId(savedJob.id);

      const preview =
        await dashboardService.previewPipeline(
          savedJob.id,
          {
            k: PIPELINE_TOP_K,
          },
        );

      setMatchedCountByJob(
        (currentCounts) => ({
          ...currentCounts,
          [savedJob.id]:
            preview.matched_candidate_count,
        }),
      );
      setPipelinePreview(preview);
    } catch {
      setError(
        "Unable to save this job description or fetch the preview candidate count.",
      );
    } finally {
      setIsSavingJob(false);
    }
  };

  const saveJobAsDraft = async () => {
    try {
      setIsSavingJob(true);
      setError("");

      const payload = toJobDescriptionPayload(formValues);
      const savedJob = draftJobId
        ? await dashboardService.updateJobDescription(
            draftJobId,
            payload,
          )
        : await dashboardService.createJobDescription(
            payload,
          );

      upsertJobDescription(savedJob);
      setSelectedJobId(savedJob.id);
      setDraftJobId(null);
      setPipelinePreview(null);
      setCanvasView("campaigns");
    } catch {
      setError("Unable to save this job description as a draft.");
    } finally {
      setIsSavingJob(false);
    }
  };

  const initializeDraftEdit = (job: JobDescription) => {
    setSelectedJobId(job.id);
    setDraftJobId(job.id);
    setFormValues(mapJobToFormValues(job));
    setPipelinePreview(null);
  };

  const confirmPipeline = async () => {
    const jobId =
      draftJobId ?? selectedJobId;

    if (!jobId) {
      return;
    }

    try {
      setIsRunningPipeline(true);
      setError("");

      const response =
        await dashboardService.executePipeline(
          jobId,
          {
            k: PIPELINE_TOP_K,
          },
        );

      setMatchedCountByJob(
        (currentCounts) => ({
          ...currentCounts,
          [jobId]:
            response.matched_candidate_count,
        }),
      );
      setCandidateResultsByJob(
        (currentResults) => ({
          ...currentResults,
          [jobId]: response.candidates,
        }),
      );
      setPipelinePreview(response);
      setCanvasView("board");
    } catch {
      setError(
        "The scoring pipeline could not be completed right now.",
      );
    } finally {
      setIsRunningPipeline(false);
    }
  };


  const openCandidateDrawer = async (
    candidateId: string,
    jobId?: string,
  ) => {
    const targetJobId = jobId ?? selectedJobId;
    if (!targetJobId) {
      return;
    }

    try {
      setIsLoadingBoard(true);
      setActiveCandidateId(candidateId);

      const board =
        await dashboardService.getCandidateEvaluationBoard(
          targetJobId,
          candidateId,
        );

      setActiveCandidateBoard(board);
      setNotesDraft(
        board.pipeline
          ?.recruiter_notes ?? "",
      );
    } catch {
      setError(
        "Unable to load the candidate evaluation details.",
      );
    } finally {
      setIsLoadingBoard(false);
    }
  };

  const toggleCandidateSelection = (
    candidateId: string,
  ) => {
    setSelectedCandidateIds(
      (currentIds) =>
        currentIds.includes(candidateId)
          ? currentIds.filter(
              (id) => id !== candidateId,
            )
          : [
              ...currentIds,
              candidateId,
            ],
    );
  };

  const saveRecruiterNotes =
    async () => {
      if (
        !selectedJobId ||
        !activeCandidateId
      ) {
        return;
      }

      try {
        setIsSavingNotes(true);

        const pipelineSnapshot =
          await dashboardService.updatePipelineNotes(
            selectedJobId,
            activeCandidateId,
            {
              recruiter_notes:
                notesDraft.trim() || null,
            },
          );

        setActiveCandidateBoard(
          (currentBoard) =>
            currentBoard
              ? {
                  ...currentBoard,
                  pipeline:
                    pipelineSnapshot,
                }
              : currentBoard,
        );
        setCandidateResultsByJob(
          (currentResults) => ({
            ...currentResults,
            [selectedJobId]:
              (currentResults[
                selectedJobId
              ] ?? []).map(
                (candidate) =>
                  candidate.candidate_id ===
                  activeCandidateId
                    ? {
                        ...candidate,
                        recruiter_notes:
                          pipelineSnapshot.recruiter_notes,
                        stage:
                          pipelineSnapshot.stage,
                      }
                    : candidate,
              ),
          }),
        );
      } catch {
        setError(
          "Unable to save recruiter notes right now.",
        );
      } finally {
        setIsSavingNotes(false);
      }
    };

  const shareShortlistWithHiringManager =
    async () => {
      if (
        !selectedJobId ||
        selectedCandidateIds.length === 0
      ) {
        return;
      }

      try {
        setIsSharingShortlist(true);

        await dashboardService.updatePipelineStage(
          selectedJobId,
          {
            stage: FINALIZED_STAGE,
            candidate_ids:
              selectedCandidateIds,
          },
        );

        await refreshCandidatesForJob(
          selectedJobId,
        );
        setSelectedCandidateIds([]);

        if (activeCandidateId) {
          await openCandidateDrawer(
            activeCandidateId,
          );
        }
      } catch {
        setError(
          "Unable to share the shortlist with the hiring manager.",
        );
      } finally {
        setIsSharingShortlist(false);
      }
    };

  const breadcrumbItems = useMemo(() => {
    if (activeNavView === "talent-pool") {
      return ["Talent Pool"];
    }

    if (
      canvasView === "board" &&
      selectedJob
    ) {
      return [
        "Job Campaigns",
        selectedJob.title,
        "Scored Candidates",
      ];
    }

    if (canvasView === "create") {
      return [
        "Job Campaigns",
        draftJobId
          ? "Edit Job Description"
          : "Create Job Description",
      ];
    }

    return ["Job Campaigns"];
  }, [
    activeNavView,
    canvasView,
    draftJobId,
    selectedJob,
  ]);

  const createJobConfirmed =
    pipelinePreview !== null;

  return {
    FINALIZED_STAGE,
    PIPELINE_TOP_K,
    activeCandidateBoard,
    activeNavView,
    breadcrumbItems,
    canvasView,
    candidateResultsByJob,
    createJobConfirmed,
    editJob,
    employmentTypes,
    error,
    formValues,
    hiringManagers,
    isLoading,
    isLoadingBoard,
    isRunningPipeline,
    isSavingJob,
    isSavingNotes,
    isSharingShortlist,
    jobDescriptions,
    matchedCountByJob,
    metrics,
    notesDraft,
    openCampaignBoard,
    openCandidateDrawer,
    pipelinePreview,
    refreshCandidatesForJob,
    removeSkillField,
    resetDrawer,
    dismissPipelinePreview,
    saveRecruiterNotes,
    selectedCandidateIds,
    selectedCandidates,
    selectedJob,
    selectedJobId,
    setActiveNavView,
    setCanvasView,
    setFormValues,
    setNotesDraft,
    saveJobAsDraft,
    initializeDraftEdit,
    shareShortlistWithHiringManager,
    startJobCreation,
    submitJobForPreview,
    talentPool,
    toggleCandidateSelection,
    updateSkillArray,
    addSkillField,
    confirmPipeline,
  };
}
