import type {
  JobDescription,
  PipelineCandidateResult,
  HiringManager,
} from "../services/dashboard.types";

function formatDate(value: string) {
  return new Date(value).toLocaleDateString();
}

function formatCampaignStatus({
  candidates,
}: {
  candidates: PipelineCandidateResult[];
}) {
  const isFinalized = candidates.some(
    (candidate) =>
      candidate.stage === "FINALIZED",
  );

  if (isFinalized) {
    return "Finalized";
  }

  if (candidates.length > 0) {
    return "Scored";
  }

  return "Draft";
}

interface CampaignsTableProps {
  candidateResultsByJob: Record<
    string,
    PipelineCandidateResult[]
  >;
  jobDescriptions: JobDescription[];
  matchedCountByJob: Record<
    string,
    number
  >;
  hiringManagers: HiringManager[];
  onCreateJobDescription: () => void;
  onOpenCampaign: (
    job: JobDescription,
  ) => void;
}

export function CampaignsTable({
  candidateResultsByJob,
  jobDescriptions,
  matchedCountByJob,
  hiringManagers,
  onCreateJobDescription,
  onOpenCampaign,
}: CampaignsTableProps) {
  return (
    <section className="surface-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">
            Job Campaigns Tracker
          </h2>

          <p className="section-copy">
            Monitor JD activity, sourcing status, and scored-candidate coverage from one workspace.
          </p>
        </div>

        <button
          type="button"
          onClick={onCreateJobDescription}
          className="workspace-primary-button"
        >
          + Create Job Description
        </button>
      </div>

      {jobDescriptions.length === 0 ? (
        <p className="empty-copy">
          No campaigns exist yet. Create the first job description to start the sourcing workflow.
        </p>
      ) : (
        <div className="campaign-table">
          <div className="campaign-table-header">
            <span>Job Title</span>
            <span>Creation Date</span>
            <span>Assigned Hiring Manager</span>
            <span>Status</span>
            <span>Total Candidates</span>
          </div>

          {jobDescriptions.map((job) => {
            const candidates =
              candidateResultsByJob[job.id] ??
              [];
            const campaignStatus =
              formatCampaignStatus({
                candidates,
              });

            const selectedManager = hiringManagers.find(
              (m) => m.id === job.hiring_manager_id,
            );
            const managerName = selectedManager
              ? selectedManager.name
              : "Talent Finder Admin";

            return (
              <button
                key={job.id}
                type="button"
                onClick={() =>
                  onOpenCampaign(job)
                }
                className="campaign-table-row"
              >
                <span className="campaign-table-title">
                  {job.title}
                </span>

                <span className="campaign-table-value">
                  {formatDate(
                    job.created_at,
                  )}
                </span>

                <span className="campaign-table-value">
                  {managerName}
                </span>

                <span className="campaign-table-value">
                  <span className={`status-badge status-badge-${campaignStatus.toLowerCase()}`}>
                    {campaignStatus}
                  </span>
                </span>

                <span className="campaign-table-value">
                  {matchedCountByJob[job.id] ??
                    candidates.length}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
