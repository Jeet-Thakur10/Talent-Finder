import { Link, useNavigate, useParams } from "react-router-dom";
import { useRecruiterJobDescriptionDetail } from "../hooks/useRecruiterJobDescriptionDetail";
import { useLatestJobTask } from "../hooks/useLatestJobTask";

function getRecruiterFriendlyStatus(
  status: string,
  stage: string,
  matchedCount?: number | null
): { text: string; icon: "spinner" | "check" | "warning" | "neutral" } {
  const statusUpper = status.toUpperCase();
  const stageUpper = stage.toUpperCase();

  if (statusUpper === "FAILED" || stageUpper === "FAILED") {
    return {
      text: "We couldn't complete the candidate evaluation. Please try again.",
      icon: "warning",
    };
  }

  if (statusUpper === "SUCCESS" || stageUpper === "COMPLETED") {
    return {
      text: "Your shortlist is ready.",
      icon: "check",
    };
  }

  switch (stageUpper) {
    case "QUEUED":
      return { text: "Preparing your search...", icon: "spinner" };
    case "ACQUIRING":
    case "SOURCING":
      return { text: "Searching our candidate database...", icon: "spinner" };
    case "SYNCHRONIZING":
      return {
        text: `Found ${matchedCount ?? 18} potential candidates.`,
        icon: "spinner",
      };
    case "PRE_SCORING":
      return { text: "Evaluating candidate suitability...", icon: "spinner" };
    case "DEEP_SCORING":
      return { text: "Ranking the best candidates...", icon: "spinner" };
    case "PERSISTING":
    case "PERSISTING_RESULTS":
      return { text: "Preparing your shortlist...", icon: "spinner" };
    default:
      return { text: "Searching our candidate database...", icon: "spinner" };
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

  const jobStatus = jobDescription && statuses ? statuses.find((s) => s.id === jobDescription.status_id) : null;
  const isCampaignClosed = jobStatus ? jobStatus.code.toUpperCase() === "CLOSED" : false;

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

  const isRunning = Boolean(
    latestTask &&
      (latestTask.status.toUpperCase() === "PENDING" ||
        latestTask.status.toUpperCase() === "RUNNING")
  );

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
            Re-evaluate Candidates
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
              {(() => {
                const isCompleted = latestTask && (latestTask.status.toUpperCase() === "SUCCESS" || latestTask.current_stage.toUpperCase() === "COMPLETED");

                if (isCompleted) {
                  return (
                    <>
                      <button
                        type="button"
                        onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/candidates`)}
                        className="workspace-primary-button !py-2.5 text-sm font-semibold shadow-md shadow-blue-900/10"
                      >
                        View Candidates
                      </button>
                      <button
                        type="button"
                        disabled={isCampaignClosed}
                        onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/score-config`)}
                        title={isCampaignClosed ? "This campaign has been completed." : undefined}
                        className={`workspace-ghost-button !py-2.5 text-sm font-semibold ${
                          isCampaignClosed ? "opacity-45 cursor-not-allowed" : ""
                        }`}
                      >
                        Start New Scoring
                      </button>
                    </>
                  );
                }

                if (isRunning || isCampaignClosed) {
                  return (
                    <button
                      type="button"
                      disabled
                      title={isCampaignClosed ? "This campaign has been completed." : undefined}
                      className="workspace-ghost-button !py-2.5 text-sm font-semibold opacity-45 cursor-not-allowed"
                    >
                      Start Candidate Evaluation
                    </button>
                  );
                }

                return (
                  <button
                    type="button"
                    onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/score-config`)}
                    className="workspace-ghost-button !py-2.5 text-sm font-semibold"
                  >
                    Start Candidate Evaluation
                  </button>
                );
              })()}
              <button
                type="button"
                disabled={isRunning || isCampaignClosed}
                onClick={() => {
                  if (isRunning || isCampaignClosed) return;
                  navigate(`/recruiter/job-descriptions/${jobDescription.id}/edit`);
                }}
                className={`workspace-ghost-button !py-2.5 text-sm font-semibold ${
                  (isRunning || isCampaignClosed) ? "opacity-45 cursor-not-allowed" : ""
                }`}
                title={
                  isCampaignClosed
                    ? "This campaign has been completed."
                    : isRunning
                    ? "Editing is disabled while candidate scoring is in progress."
                    : undefined
                }
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
              <p className="detail-copy">
                {jobDescription.max_experience === null || jobDescription.max_experience === undefined
                  ? `${jobDescription.min_experience}+ Years`
                  : `${jobDescription.min_experience} - ${jobDescription.max_experience} Years`}
              </p>
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

            <div className="detail-block bg-slate-50/85 text-xs">
              <span className="block font-bold text-slate-700 mb-1">Evaluation Status</span>
              {(() => {
                if (!latestTask) {
                  return (
                    <div className="flex items-start gap-2 mt-2 text-slate-500">
                      <p className="leading-relaxed">Click 'Start Candidate Evaluation' to find and rank candidates for this job description.</p>
                    </div>
                  );
                }

                const friendlyStatus = getRecruiterFriendlyStatus(
                  latestTask.status,
                  latestTask.current_stage,
                  latestTask.matched_candidate_count
                );

                if (friendlyStatus.icon === "spinner") {
                  return (
                    <div key={friendlyStatus.text} className="flex items-center gap-2.5 mt-2 text-blue-700 animate-fade-in">
                      <div className="h-4 w-4 shrink-0 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
                      <span className="font-semibold text-sm leading-none">{friendlyStatus.text}</span>
                    </div>
                  );
                }

                if (friendlyStatus.icon === "check") {
                  return (
                    <div key={friendlyStatus.text} className="flex items-center gap-2 mt-2 text-emerald-700 animate-fade-in">
                      <span className="text-base font-bold shrink-0 leading-none mr-0.5">✓</span>
                      <span className="font-semibold text-sm leading-none">{friendlyStatus.text}</span>
                    </div>
                  );
                }

                if (friendlyStatus.icon === "warning") {
                  return (
                    <div key={friendlyStatus.text} className="flex items-center gap-2 mt-2 text-rose-700 animate-fade-in">
                      <span className="text-base font-bold shrink-0 leading-none mr-0.5">⚠</span>
                      <span className="font-semibold text-sm leading-none">{friendlyStatus.text}</span>
                    </div>
                  );
                }

                return (
                  <div className="flex items-start gap-2 mt-2 text-slate-500">
                    <p className="leading-relaxed">{friendlyStatus.text}</p>
                  </div>
                );
              })()}
            </div>
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
