import { useParams, useNavigate } from "react-router-dom";
import { useCampaignCandidates } from "../hooks/useCampaignCandidates";
import { useState } from "react";
import { toast } from "react-hot-toast";
import { hiringManagerService } from "../services/hiringManager.service";

export function SharedCampaignDetailsPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();
  const navigate = useNavigate();
  const { campaign, candidates, isLoading, error, retry } = useCampaignCandidates(jobDescriptionId);

  const [showEndModal, setShowEndModal] = useState(false);
  const [showReopenModal, setShowReopenModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleEndCampaign = async () => {
    if (!jobDescriptionId) return;
    try {
      setIsSubmitting(true);
      await hiringManagerService.endCampaign(jobDescriptionId);
      toast.success("Campaign ended successfully!");
      setShowEndModal(false);
      void retry();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || "Failed to end campaign.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReopenCampaign = async () => {
    if (!jobDescriptionId) return;
    try {
      setIsSubmitting(true);
      await hiringManagerService.reopenCampaign(jobDescriptionId);
      toast.success("Campaign reopened successfully!");
      setShowReopenModal(false);
      void retry();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || "Failed to reopen campaign.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getDecisionBadge = (decision: "PENDING" | "INTERVIEW_SENT" | "REJECTED") => {
    switch (decision) {
      case "INTERVIEW_SENT":
        return (
          <span className="status-badge bg-emerald-50 text-emerald-700 border-emerald-250 text-xs">
            Interview Scheduled
          </span>
        );
      case "REJECTED":
        return (
          <span className="status-badge bg-rose-50 text-rose-700 border-rose-250 text-xs">
            Rejected
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="status-badge bg-amber-50 text-amber-700 border-amber-250 text-xs">
            Pending Review
          </span>
        );
    }
  };



  return (
    <div className="workspace-shell animate-fade-in">
      {/* 1. Breadcrumbs */}
      <nav className="workspace-breadcrumbs mb-6">
        <span
          className="text-slate-400 cursor-pointer hover:text-slate-600"
          onClick={() => navigate("/hm/shared-campaigns")}
        >
          Shared Campaigns
        </span>
        <span className="mx-2 text-slate-400">/</span>
        <span className="text-slate-900 font-semibold">{campaign?.title || "Campaign Details"}</span>
      </nav>

      {/* 2. Loading State */}
      {isLoading ? (
        <div className="space-y-4">
          <div className="surface-card p-6 animate-pulse">
            <div className="h-6 bg-slate-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-slate-100 rounded w-2/3"></div>
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="surface-card p-5 animate-pulse flex items-center justify-between">
                <div className="space-y-2 w-1/2">
                  <div className="h-5 bg-slate-200 rounded w-1/3"></div>
                  <div className="h-4 bg-slate-100 rounded w-1/2"></div>
                </div>
                <div className="h-8 bg-slate-200 rounded w-24"></div>
              </div>
            ))}
          </div>
        </div>
      ) : error ? (
        /* 3. Error State */
        <div className="surface-card p-8 text-center max-w-lg mx-auto border border-rose-200/50 bg-rose-50/20 rounded-2xl">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 border border-rose-200">
            <svg className="h-6 w-6 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Failed to Load Campaign Shortlist</h3>
          <p className="mt-2 text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
            We couldn't retrieve candidates shortlist for this campaign.
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={retry}
              className="workspace-primary-button !rounded-xl !py-2 !px-4 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              Try Again
            </button>
          </div>
        </div>
      ) : !campaign ? (
        <div className="surface-card p-8 text-center max-w-lg mx-auto">
          <h3 className="text-base font-semibold text-slate-900">Campaign Not Found</h3>
          <p className="text-sm text-slate-500 mt-2">
            The requested campaign does not exist or has not been shared with your account.
          </p>
        </div>
      ) : (
        /* 4. Content Area */
        <div className="space-y-6">
          {/* Campaign Header Details */}
          <div className="surface-card">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h1 className="text-xl md:text-2xl font-bold text-slate-900">{campaign.title}</h1>
                <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs font-medium text-slate-450 mt-1.5">
                  {campaign.department && (
                    <span>
                      Dept: <span className="text-slate-700">{campaign.department}</span>
                    </span>
                  )}
                  <span>
                    Recruiter: <span className="text-slate-700">{campaign.recruiter_name}</span>
                  </span>
                  <span>
                    Shared: <span className="text-slate-700">{formatDate(campaign.shared_at)}</span>
                  </span>
                </div>
              </div>

              {/* Status & Actions Container */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                {/* Status Summary Pills */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="status-badge rounded-md bg-slate-100 text-[11px] text-slate-700 border-slate-200">
                    {campaign.shared_candidate_count} Shortlisted
                  </span>
                  {campaign.pending_candidate_count > 0 && (
                    <span className="status-badge rounded-md bg-blue-50 text-[11px] text-blue-700 border-blue-100">
                      {campaign.pending_candidate_count} Pending
                    </span>
                  )}
                  {campaign.accepted_candidate_count > 0 && (
                    <span className="status-badge rounded-md bg-emerald-50 text-[11px] text-emerald-700 border-emerald-100">
                      {campaign.accepted_candidate_count} Interview Scheduled
                    </span>
                  )}
                  {campaign.rejected_candidate_count > 0 && (
                    <span className="status-badge rounded-md bg-rose-50 text-[11px] text-rose-700 border-rose-100">
                      {campaign.rejected_candidate_count} Rejected
                    </span>
                  )}
                </div>

                {/* Campaign Action Buttons */}
                <div className="flex items-center gap-2 border-l border-slate-200/50 pl-3">
                  {campaign.status_code === "CLOSED" ? (
                    <>
                      <button
                        type="button"
                        onClick={() => setShowReopenModal(true)}
                        className="workspace-primary-button !rounded-xl !py-2 !px-4 text-xs font-semibold focus:outline-none cursor-pointer"
                      >
                        Reopen Campaign
                      </button>
                      <button
                        type="button"
                        disabled
                        title="This campaign has been completed."
                        className="workspace-ghost-button !rounded-xl !py-2 !px-4 text-xs font-semibold opacity-40 cursor-not-allowed"
                      >
                        End Campaign
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      disabled={campaign.pending_candidate_count > 0}
                      onClick={() => setShowEndModal(true)}
                      title={
                        campaign.pending_candidate_count > 0
                          ? "Complete a decision for every shortlisted candidate before ending the campaign."
                          : undefined
                      }
                      className={`workspace-ghost-button !rounded-xl !py-2 !px-4 text-xs font-semibold ${
                        campaign.pending_candidate_count > 0
                          ? "opacity-40 cursor-not-allowed"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      End Campaign
                    </button>
                  )}
                </div>
              </div>
            </div>


          </div>

          {/* Candidate List Title */}
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">
              Shortlisted Candidates ({candidates.length})
            </h2>
            <p className="text-[11px] text-slate-500">
              Ranked in priority order: Pending Review, then Accepted, then Rejected.
            </p>
          </div>

          {/* 5. Candidates List */}
          {candidates.length === 0 ? (
            <div className="surface-card p-12 text-center border border-slate-200/60 bg-white rounded-2xl">
              <h3 className="text-base font-semibold text-slate-900">No Candidates Shared</h3>
              <p className="text-sm text-slate-500 mt-2">
                All shared candidates have been removed from the shortlist.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {candidates.map((c) => {
                const yrsExp = Math.round(c.total_experience_months / 12);
                const matchPct = c.final_score !== null ? Math.round(c.final_score) : 0;

                // Color score based on ranges
                let scoreColor = "text-indigo-650 bg-indigo-50 border-indigo-200";
                if (matchPct >= 90) {
                  scoreColor = "text-emerald-700 bg-emerald-50 border-emerald-250";
                } else if (matchPct < 70) {
                  scoreColor = "text-slate-550 bg-slate-50 border-slate-200";
                }

                return (
                  <div
                    key={c.candidate_id}
                    onClick={() => navigate(`/hm/shared-campaigns/${jobDescriptionId}/candidates/${c.candidate_id}`)}
                    className="workspace-list-card group flex cursor-pointer flex-col justify-between gap-5 md:flex-row md:items-center"
                  >
                    {/* Left Info Column */}
                    <div className="space-y-2 min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-base font-bold text-slate-900 group-hover:text-slate-700 group-hover:underline decoration-slate-400 underline-offset-4 leading-none">
                          {c.full_name}
                        </h3>
                        <span className={`status-badge text-xs ${scoreColor}`}>
                          {matchPct}% Match
                        </span>
                        {getDecisionBadge(c.hm_decision)}
                      </div>

                      <div className="flex flex-wrap gap-y-1 gap-x-4 text-xs text-slate-500">
                        <span className="truncate max-w-[240px]">
                          Role: <span className="text-slate-800 font-semibold">{c.current_title || "N/A"}</span>
                        </span>
                        <span>
                          Exp: <span className="text-slate-800 font-semibold">{yrsExp} Years</span>
                        </span>
                        <span>
                          Location: <span className="text-slate-800 font-semibold">{c.location || "N/A"}</span>
                        </span>
                      </div>

                      {/* Recruiter Remarks inline bubble */}
                      {c.recruiter_notes && (
                        <div className="mt-2.5 text-xs text-slate-600 bg-slate-50 border border-slate-100 p-2.5 rounded-lg max-w-xl italic">
                          <span className="font-semibold text-slate-700 not-italic">Recruiter remark: </span>
                          "{c.recruiter_notes}"
                        </div>
                      )}
                    </div>

                    {/* Right Action Column */}
                    <div className="flex items-center gap-3 shrink-0 self-end md:self-auto">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/hm/shared-campaigns/${jobDescriptionId}/candidates/${c.candidate_id}`);
                        }}
                        className="workspace-ghost-button !px-4 !py-2 text-xs font-semibold hover:border-indigo-200 hover:text-indigo-650"
                      >
                        Review Candidate
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* End Campaign Confirmation Modal */}
          {showEndModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/55 backdrop-blur-sm p-4">
              <div className="surface-card max-w-md w-full p-6 animate-fade-in shadow-2xl">
                <h3 className="text-lg font-bold text-slate-900 font-sans">End Campaign?</h3>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                  This will permanently mark the hiring campaign as completed. Recruiters will no longer be able to modify or continue this campaign.
                </p>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => setShowEndModal(false)}
                    className="workspace-ghost-button !py-2 !px-4 text-xs font-semibold cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleEndCampaign}
                    className="workspace-primary-button !py-2 !px-4 text-xs font-semibold bg-rose-600 hover:bg-rose-700 shadow-md shadow-rose-900/10 cursor-pointer"
                  >
                    {isSubmitting ? "Ending..." : "End Campaign"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Reopen Campaign Confirmation Modal */}
          {showReopenModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/55 backdrop-blur-sm p-4">
              <div className="surface-card max-w-md w-full p-6 animate-fade-in shadow-2xl">
                <h3 className="text-lg font-bold text-slate-900 font-sans">Reopen Campaign?</h3>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                  This will reopen the campaign, allowing recruiters to edit requirements or run scoring and allowing you to update candidate decisions.
                </p>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => setShowReopenModal(false)}
                    className="workspace-ghost-button !py-2 !px-4 text-xs font-semibold cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleReopenCampaign}
                    className="workspace-primary-button !py-2 !px-4 text-xs font-semibold cursor-pointer"
                  >
                    {isSubmitting ? "Reopening..." : "Reopen Campaign"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
