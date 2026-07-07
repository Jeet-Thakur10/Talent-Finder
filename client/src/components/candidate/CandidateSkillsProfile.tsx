import { useState } from "react";
import type { CandidateSkill } from "../../features/dashboard/services/dashboard.types";

export interface CandidateSkillsProfileProps {
  skills: CandidateSkill[];
  matchedMandatorySkills?: string[];
  matchedOptionalSkills?: string[];
  missingMandatorySkills?: string[];
}

export function CandidateSkillsProfile({
  skills,
  matchedMandatorySkills = [],
  matchedOptionalSkills = [],
  missingMandatorySkills = [],
}: CandidateSkillsProfileProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const primarySkills = skills.filter((s) => s.is_primary);
  const secondarySkills = skills.filter((s) => !s.is_primary);

  return (
    <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-6">
      <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Skills Profile</h2>

      <div className="space-y-4">
        {/* Matched Mandatory Skills */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-900 block">Matched Mandatory Skills</span>
          <div className="flex flex-wrap gap-1.5">
            {matchedMandatorySkills.map((s, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/60"
              >
                {s}
              </span>
            ))}
            {matchedMandatorySkills.length === 0 && (
              <span className="text-xs text-slate-400 italic">None matched.</span>
            )}
          </div>
        </div>

        {/* Matched Optional Skills */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-500 block">Matched Optional Skills</span>
          <div className="flex flex-wrap gap-1.5">
            {matchedOptionalSkills.map((s, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200/80"
              >
                {s}
              </span>
            ))}
            {matchedOptionalSkills.length === 0 && (
              <span className="text-xs text-slate-400 italic">None matched.</span>
            )}
          </div>
        </div>

        {/* Missing Mandatory Skills */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-900 block">Missing Mandatory Skills</span>
          <div className="flex flex-wrap gap-1.5">
            {missingMandatorySkills.map((s, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200/60"
              >
                {s}
              </span>
            ))}
            {missingMandatorySkills.length === 0 && (
              <span className="text-xs text-emerald-700 italic">None missing.</span>
            )}
          </div>
        </div>
      </div>

      <div className="border-t border-slate-100 pt-4">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between text-xs font-semibold text-slate-655 hover:text-slate-900 transition focus:outline-none"
        >
          <span>View All Candidate Skills</span>
          <svg
            className={`w-4 h-4 transform transition-transform duration-200 ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isExpanded && (
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-5 animate-fade-in">
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
        )}
      </div>
    </div>
  );
}
