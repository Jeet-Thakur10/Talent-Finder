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
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${badgeClass}`}>
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
      <nav className="flex items-center text-xs font-semibold uppercase tracking-[0.16em] text-slate-400 mb-6">
        <Link to="/recruiter/job-descriptions" className="hover:text-slate-900 transition">
          Job Descriptions
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-800 font-bold truncate max-w-xs">{jobDescription.title}</span>
      </nav>

      {/* Prominent Task Awareness Banner */}
      {latestTask && (latestTask.status.toUpperCase() === "PENDING" || latestTask.status.toUpperCase() === "RUNNING") && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm animate-pulse">
          <div className="space-y-1 text-left">
            <div className="text-sm font-bold text-blue-900 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-600 animate-ping" />
              Candidate evaluation is currently running in the background.
            </div>
            <p className="text-xs text-blue-700">
              Current Stage: <span className="font-semibold">{getStageFriendlyName(latestTask.current_stage)}</span> | Last Updated: {new Date(latestTask.completed_at || latestTask.started_at || latestTask.created_at).toLocaleTimeString()}
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/recruiter/tasks")}
            className="workspace-ghost-button !border-blue-300 !text-blue-700 hover:!bg-blue-100/50 !py-2 !px-4 !rounded-xl text-xs font-bold focus:outline-none shrink-0"
          >
            View Task
          </button>
        </div>
      )}

      {/* Responsive Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Structured Job Description */}
        <div className="lg:col-span-2 space-y-6">
          <div className="surface-card p-8 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
            <h1 className="text-2xl font-bold text-slate-900 mb-6">Structured Job Profile</h1>
            
            <div className="space-y-6">
              {/* Job Purpose */}
              <div className="border-b border-slate-100 pb-5">
                <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-2">
                  Job Purpose
                </h3>
                <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-line">
                  {jobDescription.job_purpose}
                </p>
              </div>

              {/* Responsibilities */}
              <div className="border-b border-slate-100 pb-5">
                <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-2">
                  Responsibilities
                </h3>
                <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-line">
                  {jobDescription.responsibilities}
                </p>
              </div>

              {/* Required Skills */}
              <div className="border-b border-slate-100 pb-5">
                <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-3">
                  Required Skills
                </h3>
                
                {mandatorySkills.length > 0 && (
                  <div className="mb-4">
                    <span className="text-xs font-semibold text-slate-900 block mb-2">
                      Mandatory Skills
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {mandatorySkills.map((skill, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-900 text-white shadow-sm"
                        >
                          {skill.skill_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {preferredSkills.length > 0 && (
                  <div>
                    <span className="text-xs font-semibold text-slate-500 block mb-2">
                      Preferred Skills
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {preferredSkills.map((skill, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-650 border border-slate-200"
                        >
                          {skill.skill_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {jobDescription.skills.length === 0 && (
                  <p className="text-xs text-slate-400 italic">No skills extracted for this profile.</p>
                )}
              </div>

              {/* Preferred Qualifications */}
              {jobDescription.preferred_qualifications && (
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-2">
                    Preferred Qualifications
                  </h3>
                  <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-line">
                    {jobDescription.preferred_qualifications}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Summary & Workspace Actions */}
        <div className="space-y-6">
          {/* 2. Job Description Summary */}
          <div className="surface-card p-6 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3 mb-4">
              Campaign Summary
            </h2>
            <div className="space-y-4 text-sm">
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Position Title</span>
                <span className="text-slate-800 font-semibold mt-0.5 block">{jobDescription.title}</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Department</span>
                <span className="text-slate-700 font-medium mt-0.5 block">{jobDescription.department || "-"}</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Hiring Manager</span>
                <span className="text-slate-700 font-medium mt-0.5 block">{getHiringManagerName(jobDescription.hiring_manager_id)}</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Employment Type</span>
                <span className="text-slate-700 font-medium mt-0.5 block">{getEmploymentTypeName(jobDescription.employment_type_id)}</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Experience Range</span>
                <span className="text-slate-700 font-medium mt-0.5 block">
                  {jobDescription.min_experience} - {jobDescription.max_experience} Years
                </span>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Education Requirement</span>
                <span className="text-slate-700 font-medium mt-0.5 block">{jobDescription.education_requirement}</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Campaign Status</span>
                <div className="mt-1">{getStatusBadge(jobDescription.status_id)}</div>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Last Updated</span>
                <span className="text-slate-500 font-medium mt-0.5 block">{formatDate(jobDescription.updated_at)}</span>
              </div>
            </div>
          </div>

          {/* 4. Workspace Actions */}
          <div className="surface-card p-6 bg-white border border-slate-200/80 rounded-2xl shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider pb-1">
              Workspace Actions
            </h2>
            
            {latestTask && (latestTask.status.toUpperCase() === "PENDING" || latestTask.status.toUpperCase() === "RUNNING") ? (
              <div className="space-y-2 bg-slate-50 border border-slate-200 p-4 rounded-xl text-center text-xs">
                <span className="font-bold text-slate-700 block">Scoring Pipeline Active</span>
                <p className="text-slate-450 mt-1">Please wait for evaluations to finish before viewing candidates.</p>
                <button
                  type="button"
                  onClick={() => navigate("/recruiter/tasks")}
                  className="workspace-primary-button w-full justify-center !rounded-xl !py-2.5 text-xs font-semibold mt-3 focus:outline-none cursor-pointer"
                >
                  View Tasks Console
                </button>
              </div>
            ) : latestTask && latestTask.status.toUpperCase() === "FAILED" ? (
              <div className="space-y-2.5 bg-rose-50 border border-rose-100 p-4 rounded-xl text-xs text-rose-900">
                <span className="font-bold text-rose-950 block">⚠️ Candidate evaluation failed.</span>
                <p className="text-[11px] leading-relaxed text-rose-750">
                  An error occurred during matching pipeline.
                </p>
                <div className="grid grid-cols-2 gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => navigate("/recruiter/tasks")}
                    className="workspace-ghost-button !border-rose-300 !text-rose-800 hover:!bg-rose-100/50 !py-2 !rounded-xl text-xs font-semibold focus:outline-none cursor-pointer"
                  >
                    View Task
                  </button>
                  <button
                    type="button"
                    disabled
                    className="workspace-primary-button !py-2 !rounded-xl text-xs font-semibold opacity-40 cursor-not-allowed justify-center focus:outline-none"
                  >
                    Retry Scoring
                  </button>
                </div>
              </div>
            ) : (
              <>
                {latestTask && latestTask.status.toUpperCase() === "SUCCESS" && (
                  <div className="p-3.5 bg-emerald-50 border border-emerald-100 rounded-xl text-xs text-emerald-800 mb-3 font-semibold text-center">
                    ✓ Candidate evaluation completed successfully.
                  </div>
                )}
                
                <button
                  type="button"
                  disabled={!latestTask || latestTask.status.toUpperCase() !== "SUCCESS"}
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/candidates`)}
                  className="workspace-primary-button w-full justify-center !rounded-xl !py-3 text-sm font-semibold cursor-pointer focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  View Candidates
                </button>

                <button
                  type="button"
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/score-config`)}
                  className="workspace-ghost-button w-full justify-center !rounded-xl !py-3 text-sm font-semibold hover:bg-slate-50 cursor-pointer focus:outline-none"
                >
                  {latestTask ? "Recalculate / Start Scoring" : "Start Scoring"}
                </button>

                <button
                  type="button"
                  onClick={() => navigate(`/recruiter/job-descriptions/${jobDescription.id}/edit`)}
                  className="workspace-ghost-button w-full justify-center !rounded-xl !py-3 text-sm font-semibold hover:bg-slate-50 cursor-pointer focus:outline-none"
                >
                  Edit Job Description
                </button>
              </>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
