import { useState } from "react";
import { useNavigate } from "react-router-dom";

import type { JobDescription } from "../services/dashboard.types";
import { useAuth } from "../../auth/hooks/useAuth";
import { authService } from "../../auth/services/auth.service";
import { CampaignsTable } from "./CampaignsTable";
import { CandidateDrawer } from "./CandidateDrawer";
import { CandidateResultsTable } from "./CandidateResultsTable";
import { DashboardHeader } from "./DashboardHeader";
import { DashboardMetrics } from "./DashboardMetrics";
import { DashboardSidebar } from "./DashboardSidebar";
import { JobDescriptionForm } from "./JobDescriptionForm";
import { JobDescriptionDrawer } from "./JobDescriptionDrawer";
import { useRecruiterDashboard } from "../hooks/useRecruiterDashboard";

function formatStageLabel(stage: string) {
  return stage
    .toLowerCase()
    .split("_")
    .map(
      (token) =>
        token.charAt(0).toUpperCase() +
        token.slice(1),
    )
    .join(" ");
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [activeJobForDetails, setActiveJobForDetails] = useState<JobDescription | null>(null);
  const {
    user,
    logout,
  } = useAuth();
  const {
    PIPELINE_TOP_K,
    activeCandidateBoard,
    activeNavView,
    breadcrumbItems,
    canvasView,
    candidateResultsByJob,
    confirmPipeline,
    dismissPipelinePreview,
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
    resetDrawer,
    removeSkillField,
    saveRecruiterNotes,
    selectedCandidateIds,
    selectedCandidates,
    selectedJob,
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
    updateJobSkills,
    triggerScoringPreview,
  } = useRecruiterDashboard();

  const handleLogout = async () => {
    await logout();

    navigate("/login", {
      replace: true,
    });
  };

  return (
    <div className="dashboard-shell">
      <DashboardSidebar
        activeNavView={activeNavView}
        onLogout={handleLogout}
        onSelectNav={(view) => {
          setActiveJobForDetails(null);
          setActiveNavView(view);
          setCanvasView(
            view === "talent-pool"
              ? "campaigns"
              : "campaigns",
          );
        }}
        user={user}
      />

      <main className="dashboard-main">
        <DashboardHeader
          breadcrumbs={breadcrumbItems}
          onBreadcrumbClick={(crumb) => {
            if (crumb === "Job Campaigns") {
              setActiveJobForDetails(null);
              setCanvasView("campaigns");
              setActiveNavView("job-campaigns");
            }
          }}
        />

        {error && (
          <div className="workspace-alert">
            {error}
          </div>
        )}

        {activeNavView ===
        "talent-pool" ? (
          <section className="surface-card">
            <div className="section-header">
              <div>
                <h1 className="workspace-title">
                  Talent Pool
                </h1>

                <p className="workspace-subtitle">
                  Recruiter-wide candidate coverage pulled from scored campaign results.
                </p>
              </div>
            </div>

            <CandidateResultsTable
              candidates={talentPool}
              isLoading={isLoading}
              onOpenCandidate={(candidateId) => {
                const campaignJobId = Object.keys(candidateResultsByJob).find((jobId) =>
                  candidateResultsByJob[jobId].some((c) => c.candidate_id === candidateId)
                );
                if (campaignJobId) {
                  void openCandidateDrawer(candidateId, campaignJobId);
                }
              }}
              isGlobalPoolView={true}
            />
          </section>
        ) : (
          <>
            <DashboardMetrics
              activeJds={metrics.activeJds}
              pendingShortlists={
                metrics.pendingShortlists
              }
            />

            {canvasView === "campaigns" && (
              <CampaignsTable
                candidateResultsByJob={
                  candidateResultsByJob
                }
                jobDescriptions={
                  jobDescriptions
                }
                matchedCountByJob={
                  matchedCountByJob
                }
                hiringManagers={hiringManagers}
                onCreateJobDescription={() => {
                  setActiveJobForDetails(null);
                  startJobCreation();
                }}
                onOpenCampaign={(job) => {
                  setActiveJobForDetails(null);
                  void openCampaignBoard(
                    job,
                  );
                }}
              />
            )}

            {canvasView === "create" && (
              <div className="stack-list">
                <JobDescriptionForm
                  employmentTypes={
                    employmentTypes
                  }
                  hiringManagers={hiringManagers}
                  formValues={formValues}
                  isSubmitting={
                    isSavingJob
                  }
                  onAddSkillField={
                    addSkillField
                  }
                  onChange={(field, value) =>
                    setFormValues(
                      (
                        currentValues,
                      ) => ({
                        ...currentValues,
                        [field]: value,
                      }),
                    )
                  }
                  onRemoveSkillField={
                    removeSkillField
                  }
                  onSkillArrayChange={
                    updateSkillArray
                  }
                  onSubmit={() => {
                    void submitJobForPreview();
                  }}
                  onSaveAsDraft={() => {
                    void saveJobAsDraft();
                  }}
                />

                {pipelinePreview && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
                    <div className="surface-card w-full max-w-lg p-8 shadow-2xl relative text-left">
                      <div className="text-indigo-600 font-semibold mb-2 uppercase tracking-wider text-xs">
                        Token Saver Confirmation Gate
                      </div>

                      <h2 className="section-title text-xl font-bold mb-4">
                        The system has matched {pipelinePreview.matched_candidate_count} candidates for this profile. Would you like to proceed to scoring?
                      </h2>

                      <p className="section-copy text-sm mb-6">
                        Confirming this step will run the pre-scoring and deep-scoring pipeline for the top {PIPELINE_TOP_K} candidates.
                      </p>

                      <div className="button-row flex justify-end gap-3">
                        <button
                          type="button"
                          onClick={dismissPipelinePreview}
                          className="workspace-ghost-button"
                        >
                          Go Back & Edit
                        </button>

                        <button
                          type="button"
                          onClick={async () => {
                            await confirmPipeline();
                            dismissPipelinePreview();
                          }}
                          disabled={isRunningPipeline}
                          className="workspace-primary-button disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isRunningPipeline ? "Scoring Candidates..." : "Proceed to Score"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {canvasView === "board" && (
              <div className="board-layout">
                <section className="surface-card">
                  <div className="section-header">
                    <div>
                      <h1 className="workspace-title">
                        {selectedJob?.title ??
                          "Scored Candidates"}
                      </h1>

                      <p className="workspace-subtitle">
                        Ranked candidates, explainable scores, and pipeline actions for this campaign.
                      </p>
                    </div>

                    <div className="button-row">
                      <button
                        type="button"
                        onClick={() => {
                          resetDrawer();
                          const isDraft = selectedJob ? (candidateResultsByJob[selectedJob.id] ?? []).length === 0 : false;
                          if (isDraft && selectedJob) {
                            initializeDraftEdit(selectedJob);
                          }
                          setActiveJobForDetails(selectedJob);
                        }}
                        className="workspace-primary-button"
                      >
                        Preview Again
                      </button>
                    </div>
                  </div>

                  {selectedJob && (
                    <div className="detail-grid">
                      <div className="detail-block">
                        <div className="detail-label">
                          Summary
                        </div>

                        <p className="detail-copy">
                          {
                            selectedJob.job_purpose
                          }
                        </p>
                      </div>

                      <div className="detail-block">
                        <div className="detail-label">
                          Campaign Status
                        </div>

                        <p className="detail-copy">
                          {selectedCandidates.some((c) => c.stage === "FINALIZED")
                            ? "Finalized"
                            : selectedCandidates.length > 0
                            ? "Scored"
                            : "Draft"}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="section-header section-header-tight">
                    <div>
                      <h2 className="section-title">
                        Candidate Evaluation Board
                      </h2>

                      <p className="section-copy">
                        Click a candidate to open the slide-out profile drawer and update recruiter notes.
                      </p>
                    </div>

                    {selectedJob && (
                      <button
                        type="button"
                        onClick={() => {
                          void refreshCandidatesForJob(
                            selectedJob.id,
                          );
                        }}
                        className="workspace-ghost-button"
                      >
                        Refresh Board
                      </button>
                    )}
                  </div>

                  <CandidateResultsTable
                    candidates={
                      selectedCandidates
                    }
                    isLoading={isLoading}
                    onOpenCandidate={(
                      candidateId,
                    ) => {
                      setActiveJobForDetails(null);
                      void openCandidateDrawer(
                        candidateId,
                      );
                    }}
                    onToggleCandidate={
                      toggleCandidateSelection
                    }
                    selectedCandidateIds={
                      selectedCandidateIds
                    }
                  />
                </section>

                <CandidateDrawer
                  board={
                    activeCandidateBoard
                  }
                  isLoading={isLoadingBoard}
                  notesDraft={notesDraft}
                  onClose={resetDrawer}
                  onNotesChange={
                    setNotesDraft
                  }
                  onSaveNotes={() => {
                    void saveRecruiterNotes();
                  }}
                  isSavingNotes={
                    isSavingNotes
                  }
                />

                <JobDescriptionDrawer
                  job={activeJobForDetails}
                  onClose={() => setActiveJobForDetails(null)}
                  isDraft={activeJobForDetails ? (candidateResultsByJob[activeJobForDetails.id] ?? []).length === 0 : false}
                  employmentTypes={employmentTypes}
                  hiringManagers={hiringManagers}
                  formValues={formValues}
                  isSubmitting={isSavingJob}
                  onAddSkillField={addSkillField}
                  onChange={(field, value) =>
                    setFormValues((currentValues) => ({
                      ...currentValues,
                      [field]: value,
                    }))
                  }
                  onRemoveSkillField={removeSkillField}
                  onSkillArrayChange={updateSkillArray}
                  onSubmit={() => {
                    void submitJobForPreview();
                  }}
                  onSaveJobSkills={async (jobId, skills) => {
                    const updated = await updateJobSkills(jobId, skills);
                    setActiveJobForDetails(updated);
                  }}
                  onTriggerScoringPreview={async (jobId) => {
                    await triggerScoringPreview(jobId);
                    setActiveJobForDetails(null);
                  }}
                />

                {pipelinePreview && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
                    <div className="surface-card w-full max-w-lg p-8 shadow-2xl relative text-left">
                      <div className="text-indigo-600 font-semibold mb-2 uppercase tracking-wider text-xs">
                        Token Saver Confirmation Gate
                      </div>

                      <h2 className="section-title text-xl font-bold mb-4">
                        The system has matched {pipelinePreview.matched_candidate_count} candidates for this profile. Would you like to proceed to scoring?
                      </h2>

                      <p className="section-copy text-sm mb-6">
                        Confirming this step will run the pre-scoring and deep-scoring pipeline for the top {PIPELINE_TOP_K} candidates.
                      </p>

                      <div className="button-row flex justify-end gap-3">
                        <button
                          type="button"
                          onClick={dismissPipelinePreview}
                          className="workspace-ghost-button"
                        >
                          Go Back & Edit
                        </button>

                        <button
                          type="button"
                          onClick={async () => {
                            await confirmPipeline();
                            setActiveJobForDetails(null);
                            dismissPipelinePreview();
                          }}
                          disabled={isRunningPipeline}
                          className="workspace-primary-button disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isRunningPipeline ? "Scoring Candidates..." : "Proceed to Score"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>

      {activeNavView !== "talent-pool" && selectedCandidateIds.length > 0 && (
        <div className="action-bar">
          <div>
            <div className="action-bar-title">
              {selectedCandidateIds.length} candidate
              {selectedCandidateIds.length > 1
                ? "s"
                : ""}{" "}
              selected
            </div>

            <p className="candidate-meta">
              Transition selected candidates to{" "}
              {formatStageLabel(
                "FINALIZED",
              )} and share the shortlist with the hiring manager.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              void shareShortlistWithHiringManager();
            }}
            disabled={isSharingShortlist}
            className="workspace-primary-button"
          >
            {isSharingShortlist
              ? "Sharing Shortlist..."
              : "Share Shortlist with Hiring Manager"}
          </button>
        </div>
      )}
    </div>
  );
}
