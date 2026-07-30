import { Link, useNavigate, useParams } from "react-router-dom";
import { useRecruiterJobDescriptionDetail } from "../hooks/useRecruiterJobDescriptionDetail";
import { useLatestJobTask } from "../hooks/useLatestJobTask";
import { RECRUITER_LABELS, RECRUITER_STAGES } from "../utils/recruiterTerms";
import { useSmoothProgress } from "../hooks/useSmoothProgress";



function getStepStatus(
  stepCode: "req" | "src" | "eval" | "short",
  latestTask: any
): "completed" | "active" | "pending" | "failed" {
  if (!latestTask) return "pending";

  const statusUpper = latestTask.status.toUpperCase();
  const stageUpper = latestTask.current_stage.toUpperCase();
  const isTaskFailed = statusUpper === "FAILED";
  const isTaskSuccess = statusUpper === "SUCCESS" || stageUpper === "COMPLETED";

  if (isTaskSuccess) return "completed";

  if (stepCode === "req") {
    if (stageUpper === "QUEUED") {
      return isTaskFailed ? "failed" : "active";
    }
    return "completed";
  }

  if (stepCode === "src") {
    if (stageUpper === "QUEUED") return "pending";
    if (stageUpper === "ACQUIRING" || stageUpper === "SOURCING") {
      return isTaskFailed ? "failed" : "active";
    }
    return "completed";
  }

  if (stepCode === "eval") {
    if (stageUpper === "QUEUED" || stageUpper === "ACQUIRING" || stageUpper === "SOURCING") return "pending";
    if (stageUpper === "PRE_SCORING" || stageUpper === "SYNCHRONIZING" || stageUpper === "DEEP_SCORING") {
      return isTaskFailed ? "failed" : "active";
    }
    return "completed";
  }

  if (stepCode === "short") {
    if (stageUpper === "COMPLETED") {
      return isTaskFailed ? "failed" : "active";
    }
    return "pending";
  }

  return "pending";
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
  const smoothPercent = useSmoothProgress(latestTask?.current_stage, latestTask?.status);

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
                        {RECRUITER_LABELS.REEVALUATE_CANDIDATES}
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
                      Find Matching Candidates
                    </button>
                  );
                }
 
                return (
                  <button
                    type="button"
                    onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/score-config`)}
                    className="workspace-ghost-button !py-2.5 text-sm font-semibold"
                  >
                    Find Matching Candidates
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
                    ? "Editing is disabled while candidate evaluation is in progress."
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

            <div className="detail-block bg-white text-xs border border-slate-200/80 rounded-2xl p-5 space-y-4 shadow-sm">
              <style>{`
                @keyframes progress-bar-stripes {
                  0% { background-position: 1rem 0; }
                  100% { background-position: 0 0; }
                }
                .animate-stripes-slow {
                  background-image: linear-gradient(45deg, rgba(255,255,255,0.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0.15) 75%, transparent 75%, transparent);
                  background-size: 1rem 1rem;
                  animation: progress-bar-stripes 1.5s linear infinite;
                }
              `}</style>

              <div className="flex justify-between items-baseline border-b border-slate-100 pb-2">
                <span className="block font-bold text-slate-700">Evaluation Status</span>
                {latestTask && (
                  <span className={`status-badge shrink-0 !rounded-md !px-2 !py-0.5 text-[9px] uppercase tracking-[0.12em] ${
                    latestTask.status.toUpperCase() === "FAILED"
                      ? "bg-rose-50 text-rose-700 border-rose-250"
                      : (latestTask.status.toUpperCase() === "SUCCESS" || latestTask.current_stage.toUpperCase() === "COMPLETED"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-blue-50 text-blue-700 border-blue-200")
                  }`}>
                    {latestTask.status.toUpperCase() === "FAILED"
                      ? "Failed"
                      : (latestTask.status.toUpperCase() === "SUCCESS" || latestTask.current_stage.toUpperCase() === "COMPLETED"
                        ? "Completed"
                        : "In Progress")}
                  </span>
                )}
              </div>

              {!latestTask ? (
                <div className="space-y-3">
                  <p className="text-slate-500 leading-relaxed text-[11px]">
                    No evaluation campaigns executed. Click 'Find Matching Candidates' to start candidate search and matching.
                  </p>
                </div>
              ) : (() => {
                const stageUpper = latestTask.current_stage.toUpperCase();
                const taskStatusUpper = latestTask.status.toUpperCase();
                const isFailed = taskStatusUpper === "FAILED";
                const isSuccess = taskStatusUpper === "SUCCESS" || stageUpper === "COMPLETED";

                const currentStageConfig = RECRUITER_STAGES[stageUpper] || { label: "Evaluating Candidate Matches", percent: 50 };
                const percent = smoothPercent;
                const currentRecruiterLabel = isSuccess 
                  ? "Candidate Shortlist Ready" 
                  : currentStageConfig.label;

                return (
                  <div className="space-y-4">
                    {/* Progress Header & Percent */}
                    <div className="flex justify-between items-center">
                      <span className="text-[11px] font-semibold text-slate-600 block truncate max-w-[70%]">
                        {isFailed ? "Failed at: " + currentRecruiterLabel : currentRecruiterLabel}
                      </span>
                      <span className="text-lg font-black text-slate-900 font-sans tracking-tight">{percent}%</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden relative">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ease-out relative ${
                          isFailed ? "bg-rose-500" : (isSuccess ? "bg-emerald-500" : "bg-blue-600 animate-stripes-slow")
                        }`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>

                    {/* Steps Checklist */}
                    <div className="space-y-2.5 pt-1">
                      {[
                        { id: "req", label: "Understanding Job Requirements" },
                        { id: "src", label: "Searching Candidate Sources" },
                        { id: "eval", label: "Evaluating Candidate Matches" },
                        { id: "short", label: "Preparing Candidate Shortlist" },
                      ].map((step) => {
                        const stepStatus = getStepStatus(step.id as any, latestTask);
                        let icon = null;
                        let textClass = "text-slate-400";
                        
                        if (stepStatus === "completed") {
                          icon = (
                            <div className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-50 border border-emerald-200 shrink-0">
                              <span className="text-[9px] font-bold text-emerald-600">✓</span>
                            </div>
                          );
                          textClass = "text-slate-700 font-medium";
                        } else if (stepStatus === "failed") {
                          icon = (
                            <div className="flex h-4 w-4 items-center justify-center rounded-full bg-rose-50 border border-rose-200 shrink-0">
                              <span className="text-[9px] font-bold text-rose-600">✕</span>
                            </div>
                          );
                          textClass = "text-rose-700 font-semibold";
                        } else if (stepStatus === "active") {
                          icon = (
                            <div className="flex h-4 w-4 items-center justify-center rounded-full bg-blue-50 border border-blue-200 shrink-0">
                              <div className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-ping" />
                            </div>
                          );
                          textClass = "text-slate-900 font-bold";
                        } else {
                          icon = (
                            <div className="flex h-4 w-4 items-center justify-center rounded-full bg-slate-50 border border-slate-150 shrink-0">
                              <span className="text-[7px] text-slate-355">○</span>
                            </div>
                          );
                          textClass = "text-slate-400";
                        }

                        return (
                          <div key={step.id} className="flex items-center gap-2.5 text-xs">
                            {icon}
                            <span className={textClass}>{step.label}</span>
                          </div>
                        );
                      })}
                    </div>

                    {isFailed && (
                      <div className="mt-2 p-2 bg-rose-50 border border-rose-100 rounded-lg text-[10px] text-rose-700 leading-relaxed">
                        {latestTask.error_message || "A system error occurred during AI evaluation."}
                      </div>
                    )}
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
