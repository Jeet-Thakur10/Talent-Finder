import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useRecruiterJobCandidates } from "../hooks/useRecruiterJobCandidates";
import { useLatestJobTask } from "../hooks/useLatestJobTask";
import { useShortlistSharing } from "../hooks/useShortlistSharing";
import { ShortlistShareDialog } from "./ShortlistShareDialog";
import { RECRUITER_STAGES } from "../utils/recruiterTerms";
import { useSmoothProgress } from "../hooks/useSmoothProgress";


export function JobDescriptionCandidatesPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();
  const navigate = useNavigate();

  const [showPartiallyMatching, setShowPartiallyMatching] = useState(false);
  const [isZeroMatchDismissed, setIsZeroMatchDismissed] = useState(false);

  const {
    jobDescription,
    candidates,
    relevantCandidates,
    hasRelevantCandidates,
    relevantCandidatesCount,
    partiallyRelevantCandidatesCount,
    statuses,
    hiringManagers,
    isLoading,
    error,
    refetch: refetchCandidates,
  } = useRecruiterJobCandidates(jobDescriptionId);

  const { latestTask, refetch: refetchTask } = useLatestJobTask(jobDescriptionId);
  const smoothPercent = useSmoothProgress(latestTask?.current_stage, latestTask?.status);

  const {
    selectedIds,
    isSharing,
    isShareDialogOpen,
    candidateNotes,
    error: shareError,
    toggleCandidate,
    clearSelection,
    openShareDialog,
    closeShareDialog,
    updateCandidateNote,
    confirmShare,
  } = useShortlistSharing(jobDescriptionId, () => {
    toast.success("Shortlist shared successfully with Hiring Manager!");
    void refetchCandidates();
  });

  const handleSyncAll = () => {
    void refetchCandidates();
    void refetchTask();
  };

  const getStatusName = (statusId: string) => {
    const found = statuses.find((s) => s.id === statusId);
    return found ? found.name : "Draft";
  };

  const getStatusBadgeClass = (statusId: string) => {
    const found = statuses.find((s) => s.id === statusId);
    const code = found ? found.code.toUpperCase() : "DRAFT";

    if (code === "ACTIVE") {
      return "bg-emerald-100 text-emerald-800 border border-emerald-200";
    } else if (code === "CLOSED") {
      return "bg-rose-100 text-rose-800 border border-rose-200";
    }
    return "bg-slate-100 text-slate-800 border border-slate-200";
  };

  const getMatchCategory = (score: number | null) => {
    if (score === null || score === undefined) return { label: "Unrated", badge: "bg-slate-100 text-slate-650 border-slate-200" };
    if (score >= 85) return { label: "Excellent Match", badge: "bg-emerald-100 text-emerald-850 border-emerald-200" };
    if (score >= 70) return { label: "Strong Match", badge: "bg-sky-100 text-sky-850 border-sky-200" };
    if (score >= 50) return { label: "Moderate Match", badge: "bg-amber-100 text-amber-850 border-amber-200" };
    return { label: "Weak Match", badge: "bg-slate-150 text-slate-700 border-slate-300" };
  };

  const handleOpenShareDialog = () => {
    // Populate notes from candidates recruiter_notes
    const notes: Record<string, string> = {};
    candidates.forEach((c) => {
      if (selectedIds.has(c.candidate_id)) {
        notes[c.candidate_id] = c.recruiter_notes || "";
      }
    });
    openShareDialog(notes);
  };

  const selectedCandidates = candidates.filter((c) => selectedIds.has(c.candidate_id));
  const assignedHM = jobDescription
    ? hiringManagers.find((hm) => hm.id === jobDescription.hiring_manager_id) || null
    : null;
  const jobStatus = jobDescription ? statuses.find((s) => s.id === jobDescription.status_id) : null;
  const isCampaignClosed = jobStatus ? jobStatus.code.toUpperCase() === "CLOSED" : false;
  return (
    <div className="workspace-shell">
      {/* 1. Breadcrumb */}
      <nav className="workspace-breadcrumbs mb-6">
        <Link to="/recruiter/job-descriptions" className="hover:text-slate-900 transition">
          Job Descriptions
        </Link>
        <span className="mx-2">/</span>
        {jobDescription ? (
          <Link
            to={`/recruiter/job-descriptions/${jobDescriptionId}`}
            className="hover:text-slate-900 transition"
          >
            {jobDescription.title}
          </Link>
        ) : (
          <span>Job Details</span>
        )}
        <span className="mx-2">/</span>
        <span className="text-slate-800 font-bold">Candidates</span>
      </nav>

      {isLoading ? (
        <div className="surface-card flex justify-center py-12">
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading candidate board...</p>
        </div>
      ) : error ? (
        <div className="workspace-alert w-full">
          {error}
        </div>
      ) : (
        <div className="w-full space-y-6 pb-24">
          
          {/* 2. Job Summary */}
          {jobDescription && (
            <div className="surface-card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest block">Evaluation Campaign Summary</span>
                <h1 className="text-xl font-bold text-slate-900 mt-1">{jobDescription.title}</h1>
                <p className="text-xs text-slate-500 mt-1">
                  Department: <span className="text-slate-700 font-semibold">{jobDescription.department || "-"}</span>
                </p>
              </div>
              <div className="shrink-0">
                <span className={`status-badge !px-3 !py-1 text-xs uppercase tracking-[0.16em] ${getStatusBadgeClass(jobDescription.status_id)}`}>
                  {getStatusName(jobDescription.status_id)}
                </span>
              </div>
            </div>
          )}

          {/* Shortlist Warning Alert */}
          {latestTask && latestTask.status.toUpperCase() === "SUCCESS" && latestTask.is_shortlist_incomplete && latestTask.warning_message && (
            <div className="workspace-alert !max-w-full flex flex-col gap-1.5 animate-fade-in">
              <div className="flex items-center gap-2 font-bold text-amber-950">
                <svg className="w-4 h-4 text-amber-700 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Shortlist Notice</span>
              </div>
              <div className="text-[13px] leading-relaxed space-y-0.5">
                <p>Requested shortlist size : <strong>{latestTask.top_k}</strong></p>
                <p>{latestTask.warning_message}</p>
              </div>
            </div>
          )}

          {/* Zero-Match Modal (Scenario 2) */}
          {!hasRelevantCandidates && !isZeroMatchDismissed && candidates.length > 0 && !isLoading && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in">
              <div className="surface-card w-full max-w-lg space-y-5 rounded-2xl p-6 shadow-2xl border border-slate-200">
                <div className="flex items-center gap-3 text-amber-600">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 border border-amber-200 shrink-0">
                    <svg className="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">No Close Matches Found</h3>
                    <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Candidate Verification Audit</span>
                  </div>
                </div>

                <p className="text-sm text-slate-600 leading-relaxed">
                  We could not find candidates that closely match your Job Description requirements. We did find <strong>{candidates.length} partially matching candidates</strong>.
                </p>

                <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-xl p-3.5 leading-relaxed">
                  Would you like to view those suggested candidates anyway, or return to refine your search criteria?
                </p>

                <div className="flex flex-col sm:flex-row gap-3 justify-end pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}`)}
                    className="workspace-ghost-button !py-2.5 !px-4 text-xs font-semibold hover:bg-slate-100"
                  >
                    Back to Job Description
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsZeroMatchDismissed(true);
                      setShowPartiallyMatching(true);
                    }}
                    className="workspace-primary-button !py-2.5 !px-5 text-xs font-bold shadow-md"
                  >
                    View Suggested Candidates ({candidates.length})
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 3. Candidate Review Board */}
          {latestTask && (latestTask.status.toUpperCase() === "PENDING" || latestTask.status.toUpperCase() === "RUNNING") ? (
            (() => {
              const stageUpper = latestTask.current_stage.toUpperCase();
              const currentStageConfig = RECRUITER_STAGES[stageUpper] || { label: "Evaluating Candidate Matches", percent: 50 };
              const percent = smoothPercent;
              const currentRecruiterLabel = currentStageConfig.label;

              return (
                /* Running/In-Progress State */
                <div className="workspace-empty-state mt-2 space-y-6">
                  <style>{`
                    @keyframes progress-bar-stripes {
                      0% { background-position: 1rem 0; }
                      100% { background-position: 0 0; }
                    }
                    .animate-stripes {
                      background-image: linear-gradient(45deg, rgba(255,255,255,0.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0.15) 75%, transparent 75%, transparent);
                      background-size: 1rem 1rem;
                      animation: progress-bar-stripes 1s linear infinite;
                    }
                  `}</style>
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-blue-200 bg-blue-50 shadow-inner">
                    <svg className="h-8 w-8 text-blue-650 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.5" />
                    </svg>
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg font-bold text-slate-900">Candidate Search In Progress</h3>
                    <p className="text-sm text-slate-500 leading-relaxed max-w-md mx-auto">
                      We are currently finding and evaluating candidates for this job description.
                    </p>
                  </div>

                  {/* Progress Panel */}
                  <div className="w-full max-w-md mx-auto bg-white border border-slate-200/60 rounded-3xl p-6 shadow-sm space-y-5 text-left">
                    
                    {/* Header & Percentage */}
                    <div className="flex justify-between items-baseline">
                      <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Campaign Progress</h4>
                        <p className="text-sm font-semibold text-slate-700 mt-1">{currentRecruiterLabel}</p>
                      </div>
                      <span className="text-2xl font-black text-blue-600 font-sans tracking-tight">{percent}%</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden relative">
                      <div 
                        className="h-full bg-blue-600 rounded-full transition-all duration-500 ease-out relative animate-stripes"
                        style={{ width: `${percent}%` }}
                      />
                    </div>

                    {/* Stages List */}
                    <div className="space-y-3 pt-2">
                      {[
                        { id: "req", label: "Understanding Job Requirements", status: stageUpper === "QUEUED" ? "active" : "completed" },
                        { id: "src", label: "Searching Candidate Sources", status: stageUpper === "QUEUED" ? "pending" : (stageUpper === "ACQUIRING" || stageUpper === "SOURCING" ? "active" : "completed") },
                        { id: "eval", label: "Evaluating Candidate Matches", status: (stageUpper === "QUEUED" || stageUpper === "ACQUIRING" || stageUpper === "SOURCING") ? "pending" : (stageUpper === "COMPLETED" ? "completed" : "active") },
                        { id: "short", label: "Preparing Candidate Shortlist", status: stageUpper === "COMPLETED" ? "completed" : "pending" },
                      ].map((step) => {
                        let icon = null;
                        let textClass = "text-slate-400";
                        if (step.status === "completed") {
                          icon = (
                            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-50 border border-emerald-200 shrink-0">
                              <span className="text-[10px] font-bold text-emerald-600">✓</span>
                            </div>
                          );
                          textClass = "text-slate-700 font-medium";
                        } else if (step.status === "active") {
                          icon = (
                            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-50 border border-blue-200 shrink-0">
                              <div className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-ping" />
                            </div>
                          );
                          textClass = "text-slate-900 font-bold";
                        } else {
                          icon = (
                            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-50 border border-slate-150 shrink-0">
                              <span className="text-[8px] text-slate-355">○</span>
                            </div>
                          );
                          textClass = "text-slate-400";
                        }

                        return (
                          <div key={step.id} className="flex items-center gap-3 text-xs">
                            {icon}
                            <span className={textClass}>{step.label}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-100 flex gap-3 justify-center">
                    <button
                      type="button"
                      onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}`)}
                      className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none shadow-md shadow-slate-900/10"
                    >
                      Return to Job Description
                    </button>
                    <button
                      type="button"
                      onClick={handleSyncAll}
                      className="workspace-ghost-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer hover:bg-slate-50/50 focus:outline-none"
                    >
                      Refresh Status
                    </button>
                  </div>
                </div>
              );
            })()
          ) : candidates.length === 0 ? (
            /* Empty State */
            <div className="workspace-empty-state mt-2">
              <div className="workspace-empty-icon rounded-full">
                <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="mt-4 text-base font-semibold text-slate-900">No Evaluated Candidates</h3>
              <p className="mt-2 text-sm text-slate-500 leading-relaxed">
                No candidates have been evaluated for this Job Description yet. Please configure match constraints and find candidates first.
              </p>
              <div className="mt-6">
                <button
                  type="button"
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}/score-config`)}
                  className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
                >
                  Find Candidates
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Option C Hybrid Banner */}
              {hasRelevantCandidates && partiallyRelevantCandidatesCount > 0 && (
                <div className="surface-card !py-3 !px-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border border-emerald-200 bg-emerald-50/40 rounded-2xl mb-4">
                  <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-700">
                    <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 shrink-0" />
                    <span>Showing <strong>{relevantCandidatesCount} Genuinely Relevant</strong> {relevantCandidatesCount === 1 ? 'Candidate' : 'Candidates'}</span>
                    <span className="text-slate-300">|</span>
                    <span className="text-slate-500">{partiallyRelevantCandidatesCount} partially matching suggestions available</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowPartiallyMatching(!showPartiallyMatching)}
                    className="workspace-ghost-button !px-3.5 !py-1.5 text-xs font-bold text-emerald-800 hover:bg-emerald-100/60 border border-emerald-200/80 rounded-xl"
                  >
                    {showPartiallyMatching ? "Hide Partially Matching Suggestions" : `Show ${partiallyRelevantCandidatesCount} Partially Matching Suggestions`}
                  </button>
                </div>
              )}

              {/* Zero Relevant Candidates Warning Banner */}
              {!hasRelevantCandidates && candidates.length > 0 && isZeroMatchDismissed && (
                <div className="workspace-alert !max-w-full flex items-center justify-between gap-3 mb-4 !bg-amber-50/80 !border-amber-200">
                  <div className="flex items-center gap-2.5 text-xs font-semibold text-amber-950">
                    <svg className="w-4 h-4 text-amber-700 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Displaying {candidates.length} Partially Matching Candidates — No exact matches were found for your requirements.</span>
                  </div>
                </div>
              )}

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                <div>
                  <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">
                    Ranked Applicants ({(hasRelevantCandidates && !showPartiallyMatching ? relevantCandidates : candidates).length})
                  </h2>
                  <p className="text-[11px] text-slate-500">Sorted by Overall Score descending. Use checkboxes to select profiles for Hiring Manager handoff.</p>
                </div>
                {selectedIds.size > 0 && (
                  <button
                    onClick={clearSelection}
                    className="text-[11px] font-semibold text-slate-550 hover:text-slate-800 underline transition cursor-pointer self-start"
                  >
                    Clear selection
                  </button>
                )}
              </div>

              {/* Candidates Grid List */}
              <div className="grid grid-cols-1 gap-4">
                {(hasRelevantCandidates && !showPartiallyMatching ? relevantCandidates : candidates).map((c) => {
                  const match = getMatchCategory(c.final_score);
                  const experienceYrs = Math.round(c.total_experience_months / 12);
                  const displayScore = c.final_score !== null ? Math.round(c.final_score) : null;
                  const isChecked = selectedIds.has(c.candidate_id);
                  const isRelevant = (c.relevance_status || "RELEVANT") === "RELEVANT";
                  const relevanceReasonSummary =
                    typeof c.relevance_reason === "object" && c.relevance_reason
                      ? (c.relevance_reason.summary as string)
                      : null;

                  return (
                    <div
                      key={c.candidate_id}
                      onClick={() => !isCampaignClosed && toggleCandidate(c.candidate_id)}
                      className={`relative flex cursor-pointer flex-col justify-between gap-5 rounded-[1.2rem] border p-5 shadow-[0_14px_36px_-34px_rgba(15,23,42,0.32)] transition md:flex-row md:items-center ${
                        isCampaignClosed
                          ? "border-slate-200 bg-white opacity-85 !cursor-default"
                          : isChecked
                          ? "border-blue-500 bg-blue-50/25"
                          : "border-slate-200 bg-white hover:border-slate-350"
                      }`}
                    >
                      {/* Left Block: Checkbox and Info */}
                      <div className="flex items-start gap-4 min-w-0 flex-1">
                        {/* Custom checkbox */}
                        <div
                          className="mt-1 shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (!isCampaignClosed) {
                              toggleCandidate(c.candidate_id);
                            }
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            readOnly
                            disabled={isLoading || isCampaignClosed}
                            className={`h-4 w-4 rounded border-slate-300 text-indigo-650 transition focus:ring-indigo-500 disabled:opacity-40 ${
                              isCampaignClosed ? "cursor-default" : "cursor-pointer"
                            }`}
                          />
                        </div>

                        <div className="space-y-2 min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2.5">
                            <h3 className="text-base font-bold text-slate-900 leading-none">
                              {c.full_name}
                            </h3>
                            
                            {/* Relevance Badge */}
                            {isRelevant ? (
                              <span
                                className="status-badge shrink-0 gap-1 bg-emerald-50 text-[9px] uppercase tracking-[0.14em] text-emerald-750 border-emerald-200 font-bold"
                                title={relevanceReasonSummary || "Genuinely Relevant Match"}
                              >
                                <svg className="w-2.5 h-2.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                                Relevant
                              </span>
                            ) : (
                              <span
                                className="status-badge shrink-0 gap-1 bg-amber-50 text-[9px] uppercase tracking-[0.14em] text-amber-850 border-amber-250 font-bold"
                                title={relevanceReasonSummary || "Partially Matching Candidate"}
                              >
                                <svg className="w-2.5 h-2.5 text-amber-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                Partially Relevant
                              </span>
                            )}

                            <span className={`status-badge text-[10px] uppercase tracking-[0.14em] ${match.badge}`}>
                              {match.label}
                            </span>

                            {c.shared_with_hiring_manager && (
                              <span className="status-badge shrink-0 gap-1 bg-indigo-50 text-[9px] uppercase tracking-[0.14em] text-indigo-700 border-indigo-150">
                                <svg className="w-2.5 h-2.5 text-indigo-650" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Shared with HM
                              </span>
                            )}
                            {c.hm_decision === "INTERVIEW_SENT" && (
                              <span className="status-badge shrink-0 gap-1 bg-emerald-50 text-[9px] uppercase tracking-[0.14em] text-emerald-700 border-emerald-150">
                                Interview Scheduled
                              </span>
                            )}
                            {c.hm_decision === "REJECTED" && (
                              <span className="status-badge shrink-0 gap-1 bg-rose-50 text-[9px] uppercase tracking-[0.14em] text-rose-700 border-rose-150">
                                HM Rejected
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap gap-y-1 gap-x-4 text-xs text-slate-500">
                            <span className="truncate max-w-[240px]">
                              Role: <span className="text-slate-800 font-semibold">{c.current_title || "N/A"}</span>
                            </span>
                            <span>
                              Exp: <span className="text-slate-800 font-semibold">{experienceYrs} Years</span>
                            </span>
                            <span>
                              Location: <span className="text-slate-800 font-semibold">{c.location || "N/A"}</span>
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Right Block: Score & CTA */}
                      <div
                        className="flex items-center justify-between md:justify-end gap-6 shrink-0 pt-3 md:pt-0 border-t border-slate-100 md:border-t-0"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {/* Score Indicator */}
                        <div className="text-right">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest block">Match Score</span>
                          <span className="text-2xl font-black text-slate-950 font-sans tracking-tight">
                            {displayScore !== null ? `${displayScore}%` : "Pending"}
                          </span>
                        </div>

                        {/* CTA button */}
                        <button
                          type="button"
                          onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}/candidates/${c.candidate_id}`)}
                  className="workspace-ghost-button !px-4 !py-2.5 text-xs font-bold hover:bg-slate-50"
                >
                  View Details
                </button>
                      </div>

                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Floating Sticky Handoff Action Bar */}
          {selectedIds.size > 0 && (
            <div className="workspace-selection-bar animate-slide-up fixed bottom-5 left-1/2 z-40 flex w-11/12 max-w-xl items-center justify-between gap-6 rounded-[1.2rem] border border-[#6A89A7]/40 bg-[#384959] px-5 py-3.5 text-white shadow-[0_20px_50px_-10px_rgba(15,23,42,0.6)] transition-all">
              <span className="text-xs font-semibold text-[#BDDDFC]">
                {selectedIds.size} {selectedIds.size === 1 ? "candidate" : "candidates"} selected
              </span>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={clearSelection}
                  className="px-3.5 py-2 text-xs font-bold text-[#BDDDFC] hover:text-white transition focus:outline-none cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isCampaignClosed}
                  onClick={handleOpenShareDialog}
                  title={isCampaignClosed ? "This campaign has been completed." : undefined}
                  className={`workspace-primary-button !py-2 !px-4 text-xs ${
                    isCampaignClosed ? "opacity-50 cursor-not-allowed" : ""
                  }`}
                >
                  Share Shortlist
                </button>
              </div>
            </div>
          )}

          {/* Handoff Confirmation Dialog */}
          <ShortlistShareDialog
            isOpen={isShareDialogOpen}
            onClose={closeShareDialog}
            onConfirm={confirmShare}
            isSharing={isSharing}
            selectedCandidates={selectedCandidates}
            candidateNotes={candidateNotes}
            onNoteChange={updateCandidateNote}
            jobTitle={jobDescription?.title || ""}
            assignedHM={assignedHM}
            error={shareError}
          />

        </div>
      )}
    </div>
  );
}
