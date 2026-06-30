import { useNavigate } from "react-router-dom";
import { useSharedCampaigns } from "../hooks/useSharedCampaigns";

export function SharedCampaignsPage() {
  const navigate = useNavigate();
  const { campaigns, isLoading, error, retry } = useSharedCampaigns();

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="workspace-shell animate-fade-in">
      {/* 1. Header */}
      <div className="workspace-header">
        <div>
          <h1 className="workspace-title">Shared Campaigns</h1>
          <p className="workspace-subtitle">
            Review shortlists and register decisions for candidates shared with you.
          </p>
        </div>
      </div>

      {/* 2. Loading State */}
      {isLoading ? (
        <div className="space-y-4">
          <div className="surface-card p-6 animate-pulse">
            <div className="h-6 bg-slate-200 rounded w-1/4 mb-4"></div>
            <div className="h-4 bg-slate-100 rounded w-1/2"></div>
          </div>
          <div className="surface-card p-6 animate-pulse">
            <div className="h-6 bg-slate-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-slate-100 rounded w-2/3"></div>
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
          <h3 className="mt-4 text-base font-semibold text-slate-900">Failed to Load Campaigns</h3>
          <p className="mt-2 text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
            We couldn't retrieve the campaigns shared with you. This could be due to a temporary network issue.
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
      ) : campaigns.length === 0 ? (
        /* 4. Empty State */
        <div className="surface-card p-12 text-center max-w-xl mx-auto border border-slate-200/60 rounded-[2rem] bg-white">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 shadow-sm">
            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="mt-5 text-base font-semibold text-slate-900">No Shared Campaigns</h3>
          <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
            Your recruiters have not shared any candidate shortlists with you yet. Once they complete scoring and share profiles, they will appear here.
          </p>
        </div>
      ) : (
        /* 5. Campaign List */
        <div className="workspace-grid grid-cols-1">
          {/* Desktop Table View */}
          <div className="hidden lg:block overflow-hidden bg-white border border-slate-200/80 rounded-2xl shadow-sm">
            <table className="min-w-full divide-y divide-slate-100 text-left">
              <thead className="bg-slate-50/70">
                <tr>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Position</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Recruiter</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Shared Date</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Candidates Stats</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {campaigns.map((campaign) => (
                  <tr
                    key={campaign.id}
                    onClick={() => navigate(`/hm/shared-campaigns/${campaign.id}`)}
                    className="hover:bg-slate-50/50 transition cursor-pointer"
                  >
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm font-semibold text-slate-900 group">
                      <div className="flex flex-col">
                        <span className="text-slate-900 group-hover:text-slate-700 font-semibold leading-tight">
                          {campaign.title}
                        </span>
                        <span className="text-[11px] text-slate-400 font-normal mt-0.5">
                          {campaign.department || "No Department"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {campaign.recruiter_name}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {formatDate(campaign.shared_at)}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                          {campaign.shared_candidate_count} Shared
                        </span>
                        {campaign.pending_candidate_count > 0 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                            {campaign.pending_candidate_count} Pending
                          </span>
                        )}
                        {campaign.accepted_candidate_count > 0 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                            {campaign.accepted_candidate_count} Accepted
                          </span>
                        )}
                        {campaign.rejected_candidate_count > 0 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-rose-50 text-rose-700 border border-rose-100">
                            {campaign.rejected_candidate_count} Rejected
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/hm/shared-campaigns/${campaign.id}`);
                        }}
                        className="workspace-ghost-button !py-1.5 !px-3.5 text-xs font-medium flex items-center gap-1.5 border border-slate-200 hover:border-slate-300 rounded-xl cursor-pointer ml-auto focus:outline-none"
                      >
                        Open Campaign
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="lg:hidden space-y-4">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                onClick={() => navigate(`/hm/shared-campaigns/${campaign.id}`)}
                className="surface-card p-5 hover:border-slate-300 transition cursor-pointer"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-sm leading-snug">{campaign.title}</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">{campaign.department || "No Department"}</p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/hm/shared-campaigns/${campaign.id}`);
                    }}
                    className="workspace-ghost-button !py-1 !px-2.5 text-xs border border-slate-200 rounded-lg focus:outline-none"
                  >
                    Open
                  </button>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-2 gap-y-3 text-xs text-slate-500">
                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">Recruiter</span>
                    <span className="text-slate-700 font-medium">{campaign.recruiter_name}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">Shared Date</span>
                    <span className="text-slate-700 font-medium">{formatDate(campaign.shared_at)}</span>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                    {campaign.shared_candidate_count} Shared
                  </span>
                  {campaign.pending_candidate_count > 0 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                      {campaign.pending_candidate_count} Pending
                    </span>
                  )}
                  {campaign.accepted_candidate_count > 0 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
                      {campaign.accepted_candidate_count} Accepted
                    </span>
                  )}
                  {campaign.rejected_candidate_count > 0 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-100">
                      {campaign.rejected_candidate_count} Rejected
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
