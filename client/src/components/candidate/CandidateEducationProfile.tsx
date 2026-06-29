import type { CandidateEducation } from "../../features/dashboard/services/dashboard.types";

export interface CandidateEducationProfileProps {
  educations: CandidateEducation[];
}

function formatDate(value: string | null) {
  if (!value) return "N/A";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
  });
}

export function CandidateEducationProfile({ educations }: CandidateEducationProfileProps) {
  return (
    <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-4">
      <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Education Profile</h2>

      {educations.length === 0 ? (
        <p className="text-xs text-slate-450 italic">No education entries found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {educations.map((edu, idx) => (
            <div key={edu.id || idx} className="border border-slate-150 bg-slate-50/20 p-4 rounded-xl space-y-1">
              <h4 className="text-xs font-bold text-slate-950">
                {edu.degree}
                {edu.field_of_study ? ` in ${edu.field_of_study}` : ""}
              </h4>
              <p className="text-xs text-slate-655 font-semibold">
                {edu.institution_name || "Unknown Institution"}
              </p>
              {(edu.start_date || edu.end_date) && (
                <span className="text-[10px] text-slate-400 font-medium block">
                  Graduation: {edu.end_date ? formatDate(edu.end_date) : "N/A"}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
