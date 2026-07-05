import { Link, useNavigate, useParams } from "react-router-dom";
import { useRecruiterJobDescriptionDetail } from "../hooks/useRecruiterJobDescriptionDetail";
import { useLatestJobTask } from "../hooks/useLatestJobTask";

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

export function JobDescriptionDetailPage() {
  const { jobDescriptionId } = useParams<{ jobDescriptionId: string }>();
  const navigate = useNavigate();
  
  const {
    jobDescription,
    employmentTypes,
    hiringManagers,
    statuses,
    isLoading,
    error,
  } = useRecruiterJobDescriptionDetail(jobDescriptionId);

  const { latestTask } = useLatestJobTask(jobDescriptionId);

  const isOutdated = Boolean(
    latestTask &&
    latestTask.status.toUpperCase() === "SUCCESS" &&
    jobDescription &&
    new Date(jobDescription.updated_at) >
      new Date(
        latestTask.completed_at ||
          latestTask.started_at ||
          latestTask.created_at
      )
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getEmploymentTypeName = (typeId: string) => {
    const found = employmentTypes.find((t) => t.id === typeId);
    return found ? found.name : "Full Time";
  };

  const getHiringManagerName = (managerId: string | null) => {
    if (!managerId) return "Unassigned";
    const found = hiringManagers.find((m) => m.id === managerId);
    return found ? found.name : "Unassigned";
  };

  const getStatusBadge = (statusId: string) => {
    const found = statuses.find((s) => s.id === statusId);
    const code = found ? found.code.toUpperCase() : "DRAFT";
    const name = found ? found.name : "Draft";

    let badgeClass = "bg-slate-100 text-slate-800 border-slate-200";
    if (code === "ACTIVE") {
      badgeClass = "bg-emerald-100 text-emerald-800 border-emerald-200";
    } else if (code === "CLOSED") {
      badgeClass = "bg-rose-100 text-rose-800 border-rose-200";
    }

    return (
      <span className={`status-badge !px-3 !py-1 text-xs ${badgeClass}`}>
        {name}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="workspace-shell">
        <div className="surface-card flex justify-center py-12">
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (error || !jobDescription) {
    return (
      <div className="workspace-shell">
        <div className="workspace-alert">
          {error || "Job Description not found."}
        </div>
        <Link to="/recruiter/job-descriptions" className="workspace-ghost-button mt-4">
          Back to Workspace
        </Link>
      </div>
    );
  }

  const mandatorySkills = jobDescription.skills.filter((s) => s.is_mandatory);
  const preferredSkills = jobDescription.skills.filter((s) => !s.is_mandatory);

  return (
    <div className="workspace-shell">
      {/* 1. Breadcrumb */}
      <nav className="workspace-breadcrumbs mb-6">
        <Link to="/recruiter/job-descriptions" className="hover:text-slate-900 transition">
          Job Descriptions
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-800 font-bold truncate max-w-xs">{jobDescription.title}</span>
      </nav>

      {/* Outdated shortlist / warning banner */}
      {isOutdated && (
        <div className="mb-6 flex flex-col justify-between gap-4 rounded-[1.2rem] border border-amber-200 bg-amber-50 p-5 shadow-sm sm:flex-row sm:items-center">
          <div className="space-y-1 text-left">
            <div className="text-sm font-bold text-amber-900 flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              The candidate shortlist and scores were generated from an older version of this Job Description.
            </div>
            <p className="text-xs text-amber-700">
              The job profile was updated on {formatDate(jobDescription.updated_at)} after the last evaluation was completed.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/score-config`)}
            className="workspace-primary-button shrink-0 !bg-amber-600 !px-4 !py-2.5 text-xs font-bold hover:!bg-amber-700"
          >
            Re-score Candidates
          </button>
        </div>
      )}

      {/* Prominent Task Awareness Banner */}
      {latestTask && (latestTask.status.toUpperCase() === "PENDING" || latestTask.status.toUpperCase() === "RUNNING") && (
        <div className="mb-6 flex flex-col justify-between gap-4 rounded-[1.2rem] border border-blue-200 bg-blue-50 p-5 shadow-sm sm:flex-row sm:items-center">
          <div className="space-y-1 text-left">
            <div className="text-sm font-bold text-blue-900 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-600" />
              Candidate evaluation is currently running in the background.
            </div>
            <p className="text-xs text-blue-700">
              Current Stage: <span className="font-semibold">{getStageFriendlyName(latestTask.current_stage)}</span> | Last Updated: {new Date(latestTask.completed_at || latestTask.started_at || latestTask.created_at).toLocaleTimeString()}
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/recruiter/tasks")}
            className="workspace-ghost-button shrink-0 !border-blue-300 !px-4 !py-2 text-xs font-bold !text-blue-700 hover:!bg-blue-100/50"
          >
            View Task
          </button>
        </div>
      )}

      <div className="space-y-6">
        <div className="surface-card space-y-6">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0 space-y-2">
              <span className="block text-[10px] font-bold uppercase tracking-widest text-slate-400">Campaign Summary</span>
              <h1 className="break-words text-2xl font-bold text-slate-900">{jobDescription.title}</h1>
              <div className="flex flex-wrap gap-2">
                {getStatusBadge(jobDescription.status_id)}
                <span className="status-badge border-slate-200 bg-slate-50 text-slate-700">{getEmploymentTypeName(jobDescription.employment_type_id)}</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 xl:justify-end">
              <button
                type="button"
                disabled={!latestTask || latestTask.status.toUpperCase() !== "SUCCESS"}
                onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/candidates`)}
                className="workspace-ghost-button !py-2.5 text-sm font-semibold disabled:opacity-40"
              >
                View Candidates
              </button>
              <button
                type="button"
                onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/score-config`)}
                className="workspace-ghost-button !py-2.5 text-sm font-semibold"
              >
                {latestTask ? "Recalculate / Start Scoring" : "Start Scoring"}
              </button>
              <button
                type="button"
                onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/edit`)}
                className="workspace-ghost-button !py-2.5 text-sm font-semibold"
              >
                Edit Job Description
              </button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="detail-block">
              <div className="detail-label">Department</div>
              <p className="detail-copy">{jobDescription.department || "-"}</p>
            </div>
            <div className="detail-block">
              <div className="detail-label">Hiring Manager</div>
              <p className="detail-copy">{getHiringManagerName(jobDescription.hiring_manager_id)}</p>
            </div>
            <div className="detail-block">
              <div className="detail-label">Experience Range</div>
              <p className="detail-copy">{jobDescription.min_experience} - {jobDescription.max_experience} Years</p>
            </div>
            <div className="detail-block">
              <div className="detail-label">Last Updated</div>
              <p className="detail-copy">{formatDate(jobDescription.updated_at)}</p>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
            <div className="detail-block">
              <div className="detail-label">Education Requirement</div>
              <p className="detail-copy">{jobDescription.education_requirement}</p>
            </div>

            {latestTask && (latestTask.status.toUpperCase() === "PENDING" || latestTask.status.toUpperCase() === "RUNNING") ? (
              <div className="detail-block bg-slate-50 text-xs">
                <span className="block font-bold text-slate-700">Scoring Pipeline Active</span>
                <p className="mt-1 leading-relaxed text-slate-450">Please wait for evaluations to finish before viewing candidates.</p>
                <button
                  type="button"
                  onClick={() => navigate("/recruiter/tasks")}
                  className="workspace-primary-button mt-3 w-full justify-center !py-2.5 text-xs font-semibold"
                >
                  View Tasks Console
                </button>
              </div>
            ) : latestTask && latestTask.status.toUpperCase() === "FAILED" ? (
              <div className="detail-block border-rose-100 bg-rose-50 text-xs text-rose-900">
                <span className="block font-bold text-rose-950">Candidate evaluation failed.</span>
                <p className="mt-1 text-[11px] leading-relaxed text-rose-750">An error occurred during matching pipeline.</p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => navigate("/recruiter/tasks")}
                    className="workspace-ghost-button !border-rose-300 !py-2 text-xs font-semibold !text-rose-800 hover:!bg-rose-100/50"
                  >
                    View Task
                  </button>
                  <button
                    type="button"
                    disabled
                    className="workspace-primary-button justify-center !py-2 text-xs font-semibold opacity-40"
                  >
                    Retry Scoring
                  </button>
                </div>
              </div>
            ) : (
              <div className="detail-block bg-slate-50/85 text-xs">
                <span className="block font-bold text-slate-700">Pipeline Status</span>
                {latestTask && latestTask.status.toUpperCase() === "SUCCESS" ? (
                  <p className="mt-1 font-semibold text-emerald-700">Candidate evaluation completed successfully.</p>
                ) : (
                  <p className="mt-1 leading-relaxed text-slate-500">Run scoring to generate ranked candidates for this job description.</p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="surface-card p-8">
          <h2 className="mb-6 text-xl font-semibold text-slate-900">Structured Job Profile</h2>

          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-5">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Job Purpose</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
                {jobDescription.job_purpose}
              </p>
            </div>

            <div className="border-b border-slate-100 pb-5">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Responsibilities</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
                {jobDescription.responsibilities}
              </p>
            </div>

            <div className="border-b border-slate-100 pb-5">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Required Skills</h3>

              {mandatorySkills.length > 0 && (
                <div className="mb-4">
                  <span className="mb-2 block text-xs font-semibold text-slate-900">Mandatory Skills</span>
                  <div className="flex flex-wrap gap-2">
                    {mandatorySkills.map((skill, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white shadow-sm"
                      >
                        {skill.skill_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {preferredSkills.length > 0 && (
                <div>
                  <span className="mb-2 block text-xs font-semibold text-slate-500">Preferred Skills</span>
                  <div className="flex flex-wrap gap-2">
                    {preferredSkills.map((skill, index) => (
                      <span
                        key={index}
                        className="status-badge border-slate-200 bg-slate-50 text-xs font-medium text-slate-650 !px-3 !py-1"
                      >
                        {skill.skill_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {jobDescription.skills.length === 0 && (
                <p className="text-xs italic text-slate-400">No skills extracted for this profile.</p>
              )}
            </div>

            {jobDescription.preferred_qualifications && (
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Preferred Qualifications</h3>
                <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
                  {jobDescription.preferred_qualifications}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
