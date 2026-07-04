import { useParams, useNavigate, Link } from "react-router-dom";
import { useRecruiterJobDescriptionDetail } from "../hooks/useRecruiterJobDescriptionDetail";
import { useRecruiterScoringConfig } from "../hooks/useRecruiterScoringConfig";

export function JobDescriptionScoringConfigPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();
  const navigate = useNavigate();

  // Load Job Description details (bread crumbs, summary headers)
  const {
    jobDescription,
    hiringManagers,
    statuses,
    isLoading: isJobLoading,
    error: jobError,
  } = useRecruiterJobDescriptionDetail(jobDescriptionId);

  // Manage Scoring configuration parameter state
  const {
    k,
    setK,
    minPrescoreThreshold,
    setMinPrescoreThreshold,
    isSubmitting,
    isSuccess,
    error,
    submitScoring,
  } = useRecruiterScoringConfig(jobDescriptionId);

  const getHiringManagerName = (managerId: string | null) => {
    if (!managerId) return "Unassigned";
    const found = hiringManagers.find((m) => m.id === managerId);
    return found ? found.name : "Unassigned";
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

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void submitScoring();
  };

  const isPageLoading = isJobLoading;

  return (
    <div className="workspace-shell">
      {/* Breadcrumb */}
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
        <span className="text-slate-800 font-bold">Scoring Configuration</span>
      </nav>

      {isPageLoading ? (
        <div className="surface-card flex justify-center py-12">
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading workspace...</p>
        </div>
      ) : jobError || !jobDescription ? (
        <div className="workspace-alert max-w-2xl mx-auto">
          {jobError || "Job Description not found."}
        </div>
      ) : (
        <div className="max-w-2xl mx-auto space-y-6">
          
          {/* 1. Job Summary */}
          <div className="surface-card">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Scoring Campaign Profile</h2>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-xl font-bold text-slate-900">{jobDescription.title}</h1>
                <p className="text-xs text-slate-500 mt-1">
                  Department: <span className="text-slate-700 font-medium">{jobDescription.department || "-"}</span> | Manager: <span className="text-slate-700 font-medium">{getHiringManagerName(jobDescription.hiring_manager_id)}</span>
                </p>
              </div>
              <div className="shrink-0">
                <span className={`status-badge !px-3 !py-1 text-xs uppercase tracking-[0.16em] ${getStatusBadgeClass(jobDescription.status_id)}`}>
                  {getStatusName(jobDescription.status_id)}
                </span>
              </div>
            </div>
          </div>

          {/* Error display */}
          {error && (
            <div className="workspace-alert">
              <div className="flex items-start gap-2.5">
                <svg className="w-5 h-5 text-amber-800 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="text-sm font-medium">{error}</div>
              </div>
            </div>
          )}

          {/* Success Submission State vs. Form State */}
          {isSuccess ? (
            /* Successful Submission */
            <div className="surface-card space-y-6 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-blue-200 bg-blue-50 shadow-inner">
                <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <div className="space-y-2">
                <h2 className="text-lg font-bold text-slate-900">Task Queued Successfully</h2>
                <div className="status-badge bg-blue-50 text-xs text-blue-700 border-blue-150 !px-3 !py-1">
                  Current Status: <span className="ml-1 font-bold">Queued</span>
                </div>
                <p className="text-sm text-slate-500 leading-relaxed max-w-md mx-auto pt-2">
                  You may safely leave this page. The scoring pipeline will continue running in the background.
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  type="button"
                  onClick={() => navigate("/recruiter/tasks")}
                  className="workspace-primary-button !px-5 !py-2.5 text-sm shadow-md shadow-slate-900/10"
                >
                  View Tasks
                </button>
                <button
                  type="button"
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}`)}
                  className="workspace-ghost-button !px-5 !py-2.5 text-sm hover:bg-slate-50"
                >
                  Back to Job Description
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleFormSubmit} className="surface-card space-y-6">
              <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">Scoring Constraints Configuration</h2>
              
              {/* Final Shortlist Size */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label htmlFor="k-value" className="auth-label text-xs">Final Shortlist Size (k)</label>
                  <span className="text-xs font-semibold text-slate-500">{k} Candidates</span>
                </div>
                <input
                  id="k-value"
                  type="number"
                  min={1}
                  max={25}
                  value={k}
                  onChange={(e) => setK(Number(e.target.value))}
                  className="auth-input !py-2.5 text-sm"
                />
                <p className="text-[11px] text-slate-400">
                  The number of top-ranking candidates that should appear in the final campaign evaluation shortlist (1 - 25).
                </p>
              </div>

              {/* Pre-score Threshold */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label htmlFor="threshold" className="auth-label text-xs">Minimum Pre-score Threshold</label>
                  <span className="text-xs font-semibold text-slate-500">{minPrescoreThreshold}% Match</span>
                </div>
                <input
                  id="threshold"
                  type="number"
                  min={0}
                  max={100}
                  value={minPrescoreThreshold}
                  onChange={(e) => setMinPrescoreThreshold(Number(e.target.value))}
                  className="auth-input !py-2.5 text-sm"
                />
                <p className="text-[11px] text-slate-400">
                  Candidates scoring below this value in the initial fast-match phase will be excluded from the detailed LLM candidate evaluation (0 - 100).
                </p>
              </div>

              {/* 3. Submit Action */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}`)}
                  className="workspace-ghost-button !px-5 !py-2.5 text-sm hover:bg-slate-50"
                >
                  Cancel
                </button>
                
                <button
                  type="submit"
                  disabled={isSubmitting || k < 1 || k > 25 || minPrescoreThreshold < 0 || minPrescoreThreshold > 100}
                  className="workspace-primary-button !px-5 !py-2.5 text-sm font-semibold disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Enqueuing Scoring Task...</span>
                    </>
                  ) : (
                    <span>Start Background Scoring</span>
                  )}
                </button>
              </div>

            </form>
          )}

        </div>
      )}
    </div>
  );
}
