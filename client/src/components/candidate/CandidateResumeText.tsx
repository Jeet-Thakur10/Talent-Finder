export interface CandidateResumeTextProps {
  resumeText: string | null;
}

export function CandidateResumeText({ resumeText }: CandidateResumeTextProps) {
  return (
    <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-4">
      <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Resume Original Text</h2>
      {resumeText ? (
        <div className="bg-slate-950 text-slate-200 font-mono text-xs rounded-xl p-4 overflow-auto max-h-[30rem] leading-relaxed whitespace-pre-wrap scrollbar-thin select-text">
          {resumeText}
        </div>
      ) : (
        <p className="text-xs text-slate-400 italic">No original resume text payload is stored in the database.</p>
      )}
    </div>
  );
}
