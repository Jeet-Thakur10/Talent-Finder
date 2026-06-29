import type { CandidateSkill } from "../../features/dashboard/services/dashboard.types";

export interface CandidateSkillsProfileProps {
  skills: CandidateSkill[];
}

export function CandidateSkillsProfile({ skills }: CandidateSkillsProfileProps) {
  const primarySkills = skills.filter((s) => s.is_primary);
  const secondarySkills = skills.filter((s) => !s.is_primary);

  return (
    <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-4">
      <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Skills Profile</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {/* Primary/Technical Skills */}
        <div className="space-y-3">
          <span className="text-xs font-semibold text-slate-900 block">Primary / Technical Skills</span>
          <div className="flex flex-wrap gap-1.5">
            {primarySkills.map((s, idx) => (
              <span
                key={s.id || idx}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-950 text-white border border-slate-900"
              >
                {s.skill_name}
              </span>
            ))}
            {primarySkills.length === 0 && (
              <span className="text-xs text-slate-400 italic">No primary skills extracted.</span>
            )}
          </div>
        </div>

        {/* Additional/Soft Skills */}
        <div className="space-y-3">
          <span className="text-xs font-semibold text-slate-500 block">Additional / General Skills</span>
          <div className="flex flex-wrap gap-1.5">
            {secondarySkills.map((s, idx) => (
              <span
                key={s.id || idx}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-white text-slate-700 border border-slate-200"
              >
                {s.skill_name}
              </span>
            ))}
            {secondarySkills.length === 0 && (
              <span className="text-xs text-slate-400 italic">No additional skills extracted.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
