import { Link, useParams } from "react-router-dom";

export function JobDescriptionEditPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <div className="auth-kicker">Edit Flow</div>
          <h1 className="workspace-title">Edit Job Description</h1>
          <p className="workspace-subtitle">
            Update active requirements and details for Job Description ID: <span className="font-mono text-slate-800 bg-slate-100 px-1.5 py-0.5 rounded">{jobDescriptionId}</span>
          </p>
        </div>

        <Link
          to={`/recruiter/job-descriptions/${jobDescriptionId}`}
          className="workspace-ghost-button !py-2 !px-4 !rounded-xl text-sm"
        >
          Back to Details
        </Link>
      </div>

      <div className="surface-card">
        <p className="empty-copy">
          The edit form and skills modifier interface will be implemented here.
        </p>
      </div>
    </div>
  );
}
