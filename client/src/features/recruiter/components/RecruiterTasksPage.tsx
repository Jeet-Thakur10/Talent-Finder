import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecruiterTasks } from "../hooks/useRecruiterTasks";

const STAGES_LIST = [
  { code: "QUEUED", label: "Queued" },
  { code: "ACQUIRING", label: "Acquiring" },
  { code: "SOURCING", label: "Sourcing" },
  { code: "PRE_SCORING", label: "Pre-screening" },
  { code: "SYNCHRONIZING", label: "Preparing Profiles" },
  { code: "DEEP_SCORING", label: "Evaluation" },
  { code: "COMPLETED", label: "Completed" },
];

function getStageFriendlyName(stage: string): string {
  switch (stage.toUpperCase()) {
    case "QUEUED":
      return "Queued";
    case "ACQUIRING":
      return "Acquiring Candidates";
    case "SOURCING":
      return "External Sourcing";
    case "PRE_SCORING":
      return "Pre-screening Candidates";
    case "SYNCHRONIZING":
      return "Preparing Candidate Profiles";
    case "DEEP_SCORING":
      return "Evaluating Candidates";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    default:
      return stage;
  }
}

function getStageIndex(stage: string): number {
  return STAGES_LIST.findIndex((s) => s.code === stage.toUpperCase());
}

export function RecruiterTasksPage() {
  const navigate = useNavigate();
  const { tasks, isLoading, error, isPolling, refetch } = useRecruiterTasks();
  
  // Track expanded task IDs for showing failure details
  const [expandedTaskIds, setExpandedTaskIds] = useState<Record<string, boolean>>({});

  const toggleExpandTask = (taskId: string) => {
    setExpandedTaskIds((prev) => ({
      ...prev,
      [taskId]: !prev[taskId],
    }));
  };

  const getStatusBadgeClass = (status: string) => {
    const code = status.toUpperCase();
    if (code === "SUCCESS") {
      return "bg-emerald-100 text-emerald-800 border-emerald-250";
    }
    if (code === "FAILED") {
      return "bg-rose-100 text-rose-800 border-rose-250";
    }
    if (code === "RUNNING") {
      return "bg-blue-100 text-blue-800 border-blue-250";
    }
    return "bg-slate-100 text-slate-800 border-slate-250";
  };

  const getStatusLabel = (status: string) => {
    const code = status.toUpperCase();
    if (code === "SUCCESS") return "Completed";
    if (code === "FAILED") return "Failed";
    if (code === "RUNNING") return "Running";
    return "Queued";
  };

  const formatTimeAgo = (dateStr: string) => {
    const time = new Date(dateStr).getTime();
    const diff = Date.now() - time;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return "Just now";
    if (minutes === 1) return "1 minute ago";
    if (minutes < 60) return `${minutes} minutes ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours === 1) return "1 hour ago";
    if (hours < 24) return `${hours} hours ago`;
    
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <div className="workspace-shell">
      {/* Page Header */}
      <div className="workspace-header !mb-6">
        <div>
          <div className="auth-kicker">Campaign Center</div>
          <div className="flex items-center gap-3">
            <h1 className="workspace-title">Background Scoring Tasks</h1>
            {isPolling && (
              <span className="status-badge bg-blue-50 text-blue-700 border-blue-200 text-[10px] !px-2.5 !py-0.5">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
                Auto-Refreshing
              </span>
            )}
          </div>
          <p className="workspace-subtitle">
            Monitor background recruiter matching pipelines, candidate extraction, and deep NLP evaluations.
          </p>
        </div>

        <button
          type="button"
          onClick={refetch}
          className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-sm font-semibold flex items-center gap-2 focus:outline-none"
        >
          <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.5" />
          </svg>
          Sync Now
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="workspace-alert mb-6">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="surface-card flex justify-center py-12">
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading task center...</p>
        </div>
      ) : tasks.length === 0 ? (
        /* Empty State */
        <div className="surface-card p-12 text-center max-w-xl mx-auto mt-8 bg-white border border-slate-200/60 rounded-3xl">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 border border-slate-200">
            <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">No scoring tasks yet</h3>
          <p className="mt-2 text-sm text-slate-500 leading-relaxed">
            No pipeline matching tasks have been created. Paste a Job Description to trigger AI matching campaigns.
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={() => navigate("/recruiter/job-descriptions/create")}
              className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
            >
              Create Job Description
            </button>
          </div>
        </div>
      ) : (
        <div className="w-full space-y-4">
          {tasks.map((task) => {
            const currentStageIndex = getStageIndex(task.current_stage);
            const isCompleted = task.status.toUpperCase() === "SUCCESS";
            const isFailed = task.status.toUpperCase() === "FAILED";
            const isRunning = task.status.toUpperCase() === "RUNNING";
            const isQueued = task.status.toUpperCase() === "PENDING";
            const isExpanded = expandedTaskIds[task.id] || false;

            return (
              <div
                key={task.id}
                className="workspace-list-card space-y-5"
              >
                {/* Top Block: Title, Status, Created Time */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-900 leading-snug">
                      {task.job_description_title || "Unknown Campaign"}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-medium">
                      Triggered {formatTimeAgo(task.created_at)}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`status-badge text-xs ${getStatusBadgeClass(task.status)}`}>
                      {getStatusLabel(task.status)}
                    </span>
                  </div>
                </div>

                {/* Middle Block: Active Stage display (recruiter-friendly) */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400 font-semibold uppercase tracking-wider">Current Pipeline Stage</span>
                    <span className="text-slate-700 font-bold">
                      {isFailed ? "Failed" : getStageFriendlyName(task.current_stage)}
                    </span>
                  </div>

                  {/* Horizontal Stepper Progress Indicator (unless Failed) */}
                  {!isFailed && (
                    <div className="grid grid-cols-7 gap-1">
                      {STAGES_LIST.map((step, idx) => {
                        const isPastStep = idx < currentStageIndex;
                        const isCurrentStep = idx === currentStageIndex;

                        let colorClass = "bg-slate-200";
                        if (isCompleted) {
                          colorClass = "bg-emerald-500";
                        } else if (isPastStep) {
                          colorClass = "bg-blue-600";
                        } else if (isCurrentStep) {
                          colorClass = isRunning ? "bg-blue-400" : "bg-slate-400";
                        }

                        return (
                          <div key={step.code} className="space-y-1">
                            <div className={`h-1.5 w-full rounded-full transition-all ${colorClass}`} />
                            <span className={`hidden md:block text-[9px] text-center font-bold truncate ${isCurrentStep ? "text-slate-900 font-extrabold" : "text-slate-400"}`}>
                              {step.label}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Task Evaluation Summary Counts (when completed or evaluation stages) */}
                {((isCompleted || currentStageIndex >= 3) && !isFailed) && (
                  <div className="grid grid-cols-3 gap-4 rounded-xl border border-slate-150 bg-slate-50/80 p-4 text-center text-xs">
                    <div>
                      <span className="text-[10px] font-semibold text-slate-400 block uppercase tracking-wider">Candidates Fetched</span>
                      <span className="text-base font-extrabold text-slate-800 mt-0.5 block">
                        {task.matched_candidate_count !== null ? task.matched_candidate_count : "--"}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-semibold text-slate-400 block uppercase tracking-wider">Qualified</span>
                      <span className="text-base font-extrabold text-slate-800 mt-0.5 block">
                        {task.eligible_candidate_count !== null ? task.eligible_candidate_count : "--"}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-semibold text-slate-400 block uppercase tracking-wider">Shortlisted</span>
                      <span className="text-base font-extrabold text-slate-800 mt-0.5 block">
                        {task.selected_candidate_count !== null ? task.selected_candidate_count : "--"}
                      </span>
                    </div>
                  </div>
                )}

                {/* Expanded Failure Details Panel */}
                {isFailed && isExpanded && (
                  <div className="animate-fade-in space-y-2.5 rounded-xl border border-rose-150 bg-rose-50 p-4 text-xs leading-relaxed text-rose-900">
                    <div className="font-bold text-rose-950">Matching Error Details</div>
                    <p className="font-medium">
                      Error: {task.error_message || "A system error occurred during AI candidate evaluation."}
                    </p>
                    <div className="text-[10px] text-rose-600 font-semibold">
                      Failed at stage: {getStageFriendlyName(task.current_stage)} | Completed: {new Date(task.completed_at || task.created_at).toLocaleString()}
                    </div>
                  </div>
                )}

                {/* Actions Row */}
                <div className="pt-4 border-t border-slate-100 flex flex-wrap gap-2 items-center justify-end">
                  {isCompleted && (
                    <>
                      <button
                        type="button"
                        onClick={() => navigate(`/recruiter/job-descriptions/${task.job_description_id}`)}
                        className="workspace-ghost-button !py-2 !px-4 !rounded-xl text-xs font-semibold focus:outline-none"
                      >
                        View Job Description
                      </button>
                      <button
                        type="button"
                        onClick={() => navigate(`/recruiter/job-descriptions/${task.job_description_id}/candidates`)}
                        className="workspace-primary-button !px-4 !py-2 text-xs font-semibold"
                      >
                        View Candidates
                      </button>
                    </>
                  )}

                  {(isRunning || isQueued) && (
                    <button
                      type="button"
                      onClick={() => navigate(`/recruiter/job-descriptions/${task.job_description_id}`)}
                      className="workspace-ghost-button !py-2 !px-4 !rounded-xl text-xs font-semibold focus:outline-none"
                    >
                      Open Job Description
                    </button>
                  )}

                  {isFailed && (
                    <>
                      <button
                        type="button"
                        onClick={() => toggleExpandTask(task.id)}
                        className="workspace-ghost-button !py-2 !px-4 !rounded-xl text-xs font-semibold focus:outline-none"
                      >
                        {isExpanded ? "Hide Details" : "View Failure Details"}
                      </button>
                      
                      <button
                        type="button"
                        disabled
                        className="workspace-primary-button !py-2 !px-4 !rounded-xl text-xs font-semibold focus:outline-none opacity-40 cursor-not-allowed"
                      >
                        Retry
                      </button>
                    </>
                  )}
                </div>

              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
