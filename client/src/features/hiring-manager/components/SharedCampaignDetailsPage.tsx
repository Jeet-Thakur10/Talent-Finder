import { useParams, useNavigate } from "react-router-dom";
import { useCampaignCandidates } from "../hooks/useCampaignCandidates";

export function SharedCampaignDetailsPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();
  const navigate = useNavigate();
  const { campaign, candidates, isLoading, error, retry } = useCampaignCandidates(jobDescriptionId);

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
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-250">
            Interview Scheduled
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-250">
            Rejected
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-250 animate-pulse">
            Pending Review
          </span>
        );
    }
  };

  // Collect recruiter remarks to show as a unified handoff note if any exist
  const handoffNotes = candidates
    .filter((c) => c.recruiter_notes && c.recruiter_notes.trim())
    .map((c) => ({
      name: c.full_name,
      notes: c.recruiter_notes,
    }));

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
          <div className="surface-card p-6 border border-slate-200/80 bg-white shadow-sm rounded-2xl">
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

              {/* Status Summary Pills */}
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                  {campaign.shared_candidate_count} Shortlisted
                </span>
                {campaign.pending_candidate_count > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-100">
                    {campaign.pending_candidate_count} Pending
                  </span>
                )}
                {campaign.accepted_candidate_count > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                    {campaign.accepted_candidate_count} Interview Scheduled
                  </span>
                )}
                {campaign.rejected_candidate_count > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-100">
                    {campaign.rejected_candidate_count} Rejected
                  </span>
                )}
              </div>
            </div>

            {/* Recruiter Handoff Remarks Summary */}
            {handoffNotes.length > 0 && (
              <div className="mt-5 p-4 bg-indigo-50/40 border border-indigo-100/60 rounded-xl">
                <span className="text-[10px] uppercase font-bold text-indigo-700 tracking-wider flex items-center gap-1.5 mb-2">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  Recruiter Handoff Recommendation notes
                </span>
                <ul className="space-y-2 text-xs text-slate-650 pl-1.5 list-disc list-inside">
                  {handoffNotes.map((hn, idx) => (
                    <li key={idx} className="leading-normal">
                      <strong className="text-slate-800">{hn.name}</strong>: "{hn.notes}"
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
                    className="bg-white border border-slate-200 rounded-2xl p-5 hover:border-slate-350 shadow-sm transition flex flex-col md:flex-row md:items-center justify-between gap-5 cursor-pointer group"
                  >
                    {/* Left Info Column */}
                    <div className="space-y-2 min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-base font-bold text-slate-900 group-hover:text-slate-700 group-hover:underline decoration-slate-400 underline-offset-4 leading-none">
                          {c.full_name}
                        </h3>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold border ${scoreColor}`}>
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
                        className="workspace-ghost-button !py-2 !px-4 text-xs font-semibold border border-slate-200 hover:border-indigo-200 hover:text-indigo-650 rounded-xl focus:outline-none cursor-pointer"
                      >
                        Review Candidate
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
