import { useNavigate } from "react-router-dom";
import { useRecruiterJobDescriptions } from "../hooks/useRecruiterJobDescriptions";
import { useRecruiterTasks } from "../hooks/useRecruiterTasks";

export function JobDescriptionsPage() {
  const navigate = useNavigate();
  const {
    jobDescriptions,
    employmentTypes,
    hiringManagers,
    statuses,
    isLoading,
    error,
  } = useRecruiterJobDescriptions();
  
  const { tasks } = useRecruiterTasks();

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
      badgeClass = "bg-rose-100 text-rose-850 border-rose-200";
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${badgeClass}`}>
        {name}
      </span>
    );
  };

  const getTaskStatusChip = (jobId: string) => {
    const task = tasks.find((t) => t.job_description_id === jobId);
    if (!task) return null;
    const code = task.status.toUpperCase();
    let chipClass = "bg-slate-50 text-slate-600 border-slate-200";
    let label = "Queued";
    
    if (code === "RUNNING") {
      chipClass = "bg-blue-50 text-blue-700 border-blue-200 animate-pulse";
      label = "Scoring Running";
    } else if (code === "SUCCESS") {
      chipClass = "bg-emerald-50 text-emerald-700 border-emerald-200";
      label = "Completed";
    } else if (code === "FAILED") {
      chipClass = "bg-rose-50 text-rose-700 border-rose-250";
      label = "Failed";
    }

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${chipClass} ml-2 shrink-0`}>
        {label}
      </span>
    );
  };

  return (
    <div className="workspace-shell">
      {/* 1. Page Header */}
      <div className="workspace-header">
        <div>
          <h1 className="workspace-title">Job Descriptions</h1>
          <p className="workspace-subtitle">
            Manage your active job campaigns, requirements, and candidate matching pipelines.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/recruiter/job-descriptions/create")}
          className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
        >
          Create Job Description
        </button>
      </div>

      {/* States: Loading, Error, Content/Empty */}
      {isLoading ? (
        <div className="surface-card flex justify-center py-12">
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading workspace...</p>
        </div>
      ) : error ? (
        <div className="workspace-alert">
          {error}
        </div>
      ) : jobDescriptions.length === 0 ? (
        /* 3. Empty State */
        <div className="surface-card p-12 text-center max-w-xl mx-auto mt-8 border border-slate-200/60 rounded-[2rem] bg-white">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 border border-slate-200">
            <svg className="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">No Job Descriptions</h3>
          <p className="mt-2 text-sm text-slate-500 leading-relaxed">
            Get started by creating your first job description. This will initialize your sourcing campaign and matching pipeline.
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={() => navigate("/recruiter/job-descriptions/create")}
              className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
            >
              Create Job Description
            </button>
          </div>
        </div>
      ) : (
        /* 2. Job Description List */
        <div className="workspace-grid grid-cols-1">
          {/* Desktop View (Table Layout) */}
          <div className="hidden lg:block overflow-hidden bg-white border border-slate-200/80 rounded-2xl shadow-sm">
            <table className="min-w-full divide-y divide-slate-100 text-left">
              <thead className="bg-slate-50/70">
                <tr>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Job Title</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Department</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Employment Type</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Hiring Manager</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Status</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Created Date</th>
                  <th scope="col" className="px-6 py-4 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Last Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {jobDescriptions.map((job) => (
                  <tr
                    key={job.id}
                    onClick={() => navigate(`/recruiter/job-descriptions/${job.id}`)}
                    className="hover:bg-slate-50/50 transition cursor-pointer"
                  >
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm font-semibold text-slate-900 group">
                      <span className="group-hover:text-slate-700 group-hover:underline decoration-slate-400 underline-offset-4">
                        {job.title}
                      </span>
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {job.department || "-"}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {getEmploymentTypeName(job.employment_type_id)}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {getHiringManagerName(job.hiring_manager_id)}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm flex items-center">
                      {getStatusBadge(job.status_id)}
                      {getTaskStatusChip(job.id)}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm text-slate-500">
                      {formatDate(job.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile & Tablet View (Stacked List & Cards Layout) */}
          <div className="lg:hidden space-y-4">
            {jobDescriptions.map((job) => (
              <div
                key={job.id}
                onClick={() => navigate(`/recruiter/job-descriptions/${job.id}`)}
                className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm hover:border-slate-350 transition cursor-pointer flex flex-col gap-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base font-semibold text-slate-900 leading-tight">
                    {job.title}
                  </h3>
                  <div className="shrink-0 flex items-center gap-1">
                    {getStatusBadge(job.status_id)}
                    {getTaskStatusChip(job.id)}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-1 text-xs">
                  <div>
                    <span className="text-slate-400 block font-medium">Department</span>
                    <span className="text-slate-700 font-semibold mt-0.5 block">{job.department || "-"}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Employment Type</span>
                    <span className="text-slate-700 font-semibold mt-0.5 block">{getEmploymentTypeName(job.employment_type_id)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Hiring Manager</span>
                    <span className="text-slate-700 font-semibold mt-0.5 block">{getHiringManagerName(job.hiring_manager_id)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Last Updated</span>
                    <span className="text-slate-700 font-semibold mt-0.5 block">{formatDate(job.updated_at)}</span>
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 pt-2 border-t border-slate-100 mt-1 flex justify-between">
                  <span>ID: {job.id.substring(0, 8)}...</span>
                  <span>Created: {formatDate(job.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
