import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useRecruiterJobCandidates } from "../hooks/useRecruiterJobCandidates";
import { useLatestJobTask } from "../hooks/useLatestJobTask";
import { useShortlistSharing } from "../hooks/useShortlistSharing";
import { ShortlistShareDialog } from "./ShortlistShareDialog";

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

export function JobDescriptionCandidatesPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();
  const navigate = useNavigate();

  const {
    jobDescription,
    candidates,
    statuses,
    hiringManagers,
    isLoading,
    error,
    refetch: refetchCandidates,
  } = useRecruiterJobCandidates(jobDescriptionId);

  const { latestTask, refetch: refetchTask } = useLatestJobTask(jobDescriptionId);

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
        <div className="workspace-alert max-w-4xl mx-auto">
          {error}
        </div>
      ) : (
        <div className="max-w-4xl mx-auto space-y-6 pb-24">
          
          {/* 2. Job Summary */}
          {jobDescription && (
            <div className="surface-card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest block">Scoring Campaign Summary</span>
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

          {/* 3. Candidate Review Board */}
          {latestTask && (latestTask.status.toUpperCase() === "PENDING" || latestTask.status.toUpperCase() === "RUNNING") ? (
            /* Running/In-Progress State */
            <div className="workspace-empty-state mt-2 space-y-6">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-blue-200 bg-blue-50 shadow-inner">
                <svg className="h-8 w-8 text-blue-650 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.5" />
                </svg>
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-bold text-slate-900">Candidate Evaluation In Progress</h3>
                <p className="text-sm text-slate-500 leading-relaxed max-w-md mx-auto">
                  Evaluation is still running in the background. Current pipeline stage:{" "}
                  <span className="font-bold text-slate-700">{getStageFriendlyName(latestTask.current_stage)}</span>.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 flex gap-3 justify-center">
                <button
                  type="button"
                  onClick={() => navigate("/recruiter/tasks")}
                  className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none shadow-md shadow-slate-900/10"
                >
                  View Tasks
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
          ) : candidates.length === 0 ? (
            /* Empty State */
            <div className="workspace-empty-state mt-2">
              <div className="workspace-empty-icon rounded-full">
                <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="mt-4 text-base font-semibold text-slate-900">No Scored Candidates</h3>
              <p className="mt-2 text-sm text-slate-500 leading-relaxed">
                No candidates have been scored for this Job Description yet. You must configure matching constraints and run evaluations first.
              </p>
              <div className="mt-6">
                <button
                  type="button"
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}/score-config`)}
                  className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
                >
                  Start Scoring
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                <div>
                  <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Ranked Applicants ({candidates.length})</h2>
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
                {candidates.map((c) => {
                  const match = getMatchCategory(c.final_score);
                  const experienceYrs = Math.round(c.total_experience_months / 12);
                  const displayScore = c.final_score !== null ? Math.round(c.final_score) : null;
                  const isChecked = selectedIds.has(c.candidate_id);

                  return (
                    <div
                      key={c.candidate_id}
                      onClick={() => toggleCandidate(c.candidate_id)}
                      className={`relative flex cursor-pointer flex-col justify-between gap-5 rounded-[1.2rem] border p-5 shadow-[0_14px_36px_-34px_rgba(15,23,42,0.32)] transition md:flex-row md:items-center ${
                        isChecked
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
                            toggleCandidate(c.candidate_id);
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            readOnly
                            disabled={isLoading}
                            className="h-4 w-4 rounded border-slate-300 text-indigo-650 transition focus:ring-indigo-500 cursor-pointer disabled:opacity-40"
                          />
                        </div>

                        <div className="space-y-2 min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-3">
                            <h3 className="text-base font-bold text-slate-900 leading-none">
                              {c.full_name}
                            </h3>
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
            <div className="animate-slide-up fixed bottom-5 left-1/2 z-40 flex w-11/12 max-w-xl -translate-x-1/2 items-center justify-between gap-6 rounded-[1.2rem] border border-slate-800 bg-slate-950 px-5 py-3.5 text-white shadow-[0_20px_50px_-10px_rgba(15,23,42,0.6)] transition-all">
              <span className="text-xs font-semibold text-slate-200">
                {selectedIds.size} {selectedIds.size === 1 ? "candidate" : "candidates"} selected
              </span>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={clearSelection}
                  className="px-3.5 py-2 text-xs font-bold text-slate-350 hover:text-white transition focus:outline-none cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleOpenShareDialog}
                  className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-black text-white shadow-md shadow-blue-900/30 transition hover:bg-blue-500 focus:outline-none"
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
