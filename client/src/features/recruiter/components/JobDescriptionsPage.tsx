import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecruiterJobDescriptions } from "../hooks/useRecruiterJobDescriptions";
import { useRecruiterTasks } from "../hooks/useRecruiterTasks";
import { AddRecruiterModal } from "./AddRecruiterModal";

export function JobDescriptionsPage() {
  const navigate = useNavigate();
  const [isAddRecruiterOpen, setIsAddRecruiterOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
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
      <span className={`status-badge ${badgeClass}`}>
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
      chipClass = "bg-blue-50 text-blue-700 border-blue-200";
      label = "Scoring Running";
    } else if (code === "SUCCESS") {
      chipClass = "bg-emerald-50 text-emerald-700 border-emerald-200";
      label = "Completed";
    } else if (code === "FAILED") {
      chipClass = "bg-rose-50 text-rose-700 border-rose-250";
      label = "Failed";
    }

    return (
      <span className={`status-badge shrink-0 !rounded-md !px-2 !py-0.5 text-[10px] uppercase tracking-[0.14em] ${chipClass}`}>
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

        <div className="flex items-center gap-3">
          {successMessage && (
            <span className="text-xs text-emerald-600 font-semibold bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-250 animate-fade-in">
              {successMessage}
            </span>
          )}
          <button
            type="button"
            onClick={() => setIsAddRecruiterOpen(true)}
            className="workspace-ghost-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
          >
            Add User
          </button>
          <button
            type="button"
            onClick={() => navigate("/recruiter/job-descriptions/create")}
            className="workspace-primary-button !rounded-xl !py-2.5 !px-5 text-sm cursor-pointer focus:outline-none"
          >
            Create Job Description
          </button>
        </div>
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
        <div className="workspace-empty-state mt-2">
          <div className="workspace-empty-icon">
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
        <div className="workspace-grid grid-cols-1">
          <div className="workspace-table-wrap hidden lg:block">
            <table className="workspace-table">
              <thead>
                <tr>
                  <th scope="col">Job Title</th>
                  <th scope="col">Department</th>
                  <th scope="col">Employment Type</th>
                  <th scope="col">Hiring Manager</th>
                  <th scope="col">Job Status</th>
                  <th scope="col">Scoring Status</th>
                  <th scope="col">Created Date</th>
                  <th scope="col">Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {jobDescriptions.map((job) => (
                  <tr
                    key={job.id}
                    onClick={() => navigate(`/recruiter/job-descriptions/${job.id}`)}
                    className="workspace-table-row cursor-pointer"
                  >
                    <td className="workspace-table-cell">
                      <div className="workspace-table-title">
                        {job.title}
                      </div>
                    </td>
                    <td className="workspace-table-cell">
                      {job.department || "-"}
                    </td>
                    <td className="workspace-table-cell">
                      {getEmploymentTypeName(job.employment_type_id)}
                    </td>
                    <td className="workspace-table-cell">
                      {getHiringManagerName(job.hiring_manager_id)}
                    </td>
                    <td className="workspace-table-cell">
                      {getStatusBadge(job.status_id)}
                    </td>
                    <td className="workspace-table-cell">
                      {getTaskStatusChip(job.id) || (
                        <span className="text-slate-400 font-medium">—</span>
                      )}
                    </td>
                    <td className="workspace-table-cell">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="workspace-table-cell">
                      {formatDate(job.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="lg:hidden space-y-4">
            {jobDescriptions.map((job) => (
              <div
                key={job.id}
                onClick={() => navigate(`/recruiter/job-descriptions/${job.id}`)}
                className="workspace-list-card cursor-pointer"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="min-w-0 break-words text-base font-semibold leading-tight text-slate-900">
                    {job.title}
                  </h3>
                  <div className="flex shrink-0 flex-wrap items-center justify-end gap-1">
                    {getStatusBadge(job.status_id)}
                    {getTaskStatusChip(job.id)}
                  </div>
                </div>

                <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
                  <div>
                    <span className="text-slate-400 block font-medium">Department</span>
                    <span className="mt-0.5 block break-words font-semibold text-slate-700">{job.department || "-"}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Employment Type</span>
                    <span className="mt-0.5 block break-words font-semibold text-slate-700">{getEmploymentTypeName(job.employment_type_id)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Hiring Manager</span>
                    <span className="mt-0.5 block break-words font-semibold text-slate-700">{getHiringManagerName(job.hiring_manager_id)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Last Updated</span>
                    <span className="mt-0.5 block font-semibold text-slate-700">{formatDate(job.updated_at)}</span>
                  </div>
                </div>

                <div className="mt-1 flex flex-wrap justify-between gap-2 border-t border-slate-100 pt-3 text-[10px] text-slate-400">
                  <span>ID: {job.id.substring(0, 8)}...</span>
                  <span>Created: {formatDate(job.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <AddRecruiterModal
        isOpen={isAddRecruiterOpen}
        onClose={() => setIsAddRecruiterOpen(false)}
        onSuccess={(msg) => {
          setSuccessMessage(msg);
          setTimeout(() => setSuccessMessage(null), 5000);
        }}
      />
    </div>
  );
}
