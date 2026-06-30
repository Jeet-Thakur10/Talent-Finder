import type { CandidateScoreBreakdown as ScoreType } from "../../features/dashboard/services/dashboard.types";

export interface CandidateScoreBreakdownProps {
  score: ScoreType | null;
}

export function CandidateScoreBreakdown({ score }: CandidateScoreBreakdownProps) {
  return (
    <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-5">
      <div>
        <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Matching Breakdown</h2>
        <p className="text-[10px] text-slate-400 mt-1">Weighted evaluation values explaining the matching pipeline scores.</p>
      </div>

      {score ? (
        <div className="space-y-4">
          {[
            { label: "Skills Match Score", value: score.skill_score, desc: "Matches mandatory & optional skills against job requirements." },
            { label: "Experience Match Score", value: score.experience_score, desc: "Measures depth and duration of relevant professional experience." },
            { label: "Industry & Role Fit", value: score.role_fit_score, desc: "Checks compatibility with industry background and overall role fit." },
            { label: "Education Match Score", value: score.education_score, desc: "Compares academic credentials against the educational bar." },
          ].map((item, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between items-baseline">
                <span className="text-xs font-semibold text-slate-800">{item.label}</span>
                <span className="text-xs font-bold text-slate-950 font-sans">{Math.round(item.value)}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-slate-900 rounded-full transition-all duration-500"
                  style={{ width: `${item.value}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">{item.desc}</p>
            </div>
          ))}

          {score.explanation && (
            <div className="pt-4 border-t border-slate-100 space-y-3.5">
              {(score.explanation as any).summary && (
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">AI Match Rationale</span>
                  <p className="text-xs text-slate-650 leading-relaxed whitespace-pre-wrap">
                    {(score.explanation as any).summary}
                  </p>
                </div>
              )}

              {Array.isArray((score.explanation as any).strengths) && (score.explanation as any).strengths.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">Key Highlights</span>
                  <ul className="text-xs text-slate-700 space-y-1 pl-4 list-disc">
                    {(score.explanation as any).strengths.map((str: string, index: number) => (
                      <li key={index}>{str}</li>
                    ))}
                  </ul>
                </div>
              )}

              {Array.isArray((score.explanation as any).weaknesses) && (score.explanation as any).weaknesses.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider block">Identified Gaps</span>
                  <ul className="text-xs text-slate-700 space-y-1 pl-4 list-disc">
                    {(score.explanation as any).weaknesses.map((weak: string, index: number) => (
                      <li key={index}>{weak}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-slate-400 italic">No score breakdown available for this candidate.</p>
      )}
    </div>
  );
}
