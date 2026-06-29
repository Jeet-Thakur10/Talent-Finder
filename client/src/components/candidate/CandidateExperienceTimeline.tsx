import type { CandidateExperience } from "../../features/dashboard/services/dashboard.types";

export interface CandidateExperienceTimelineProps {
  experiences: CandidateExperience[];
}

function formatDate(value: string | null) {
  if (!value) return "N/A";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
  });
}

export function CandidateExperienceTimeline({ experiences }: CandidateExperienceTimelineProps) {
  // Chronologically sort experiences (most recent first)
  const sortedExperiences = [...experiences].sort((a, b) => {
    if (!a.start_date) return 1;
    if (!b.start_date) return -1;
    return new Date(b.start_date).getTime() - new Date(a.start_date).getTime();
  });

  return (
    <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-6">
      <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Experience Timeline</h2>

      {sortedExperiences.length === 0 ? (
        <p className="text-xs text-slate-450 italic">No experience entries found in candidate history.</p>
      ) : (
        <div className="relative pl-6 border-l-2 border-slate-150 space-y-8">
          {sortedExperiences.map((exp, idx) => (
            <div key={exp.id || idx} className="relative group">
              {/* Bullet marker */}
              <div className="absolute -left-[31px] top-1.5 h-4 w-4 rounded-full border-2 border-slate-200 bg-white group-hover:border-slate-900 group-hover:bg-slate-900 transition" />

              <div>
                <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1">
                  <h3 className="text-sm font-bold text-slate-950 group-hover:text-slate-900 transition">
                    {exp.title}
                  </h3>
                  <span className="text-[11px] font-semibold text-slate-400">
                    {formatDate(exp.start_date)} - {exp.is_current ? "Present" : formatDate(exp.end_date)}
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-semibold mt-0.5">
                  {exp.company_name || "Unknown Company"}
                </p>
                {exp.description && (
                  <p className="text-xs text-slate-650 mt-2 leading-relaxed whitespace-pre-wrap bg-slate-50/30 p-3 rounded-xl border border-slate-150">
                    {exp.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
