import type { PipelineCandidateResult, HiringManager } from "../../dashboard/services/dashboard.types";

export interface ShortlistShareDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isSharing: boolean;
  selectedCandidates: PipelineCandidateResult[];
  candidateNotes: Record<string, string>;
  onNoteChange: (candidateId: string, note: string) => void;
  jobTitle: string;
  assignedHM: HiringManager | null;
  error: string | null;
}

export function ShortlistShareDialog({
  isOpen,
  onClose,
  onConfirm,
  isSharing,
  selectedCandidates,
  candidateNotes,
  onNoteChange,
  jobTitle,
  assignedHM,
  error,
}: ShortlistShareDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-slate-900/40 transition-opacity"
        onClick={onClose}
      />

      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="workspace-modal-panel animate-fade-in flex max-h-[85vh] max-w-2xl flex-col">
          <div className="mb-4">
            <h3 className="text-lg font-bold text-slate-900 leading-tight">Share Candidate Shortlist</h3>
            <p className="text-xs text-slate-500 mt-1">
              Add your remarks and review the handoff list before sending it to the Hiring Manager.
            </p>
          </div>

          <div className="mb-4 grid grid-cols-1 gap-3 rounded-[1rem] border border-slate-150 bg-slate-50/85 p-4 text-xs sm:grid-cols-2">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Hiring Campaign</span>
              <span className="text-slate-800 font-semibold">{jobTitle}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Assigned Hiring Manager</span>
              <span className="text-slate-800 font-semibold">{assignedHM ? `${assignedHM.name} (${assignedHM.email})` : "None Assigned"}</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-thin max-h-[40vh] mb-4">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
              Selected candidates ({selectedCandidates.length})
            </span>

            {selectedCandidates.map((c) => {
              const displayScore = c.final_score !== null ? Math.round(c.final_score) : null;
              return (
                <div key={c.candidate_id} className="space-y-3 rounded-[1rem] border border-slate-200 bg-white p-4">
                  <div className="flex justify-between items-baseline">
                    <div className="min-w-0">
                      <h4 className="text-sm font-bold text-slate-900">{c.full_name}</h4>
                      <p className="mt-0.5 text-[11px] text-slate-450">{c.current_title || "No Title Specified"}</p>
                    </div>
                    {displayScore !== null && (
                      <span className="status-badge bg-slate-900 text-xs text-white border-slate-900">
                        {displayScore}% Match
                      </span>
                    )}
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                      Recruiter Handoff Remarks
                    </label>
                    <textarea
                      value={candidateNotes[c.candidate_id] || ""}
                      onChange={(e) => onNoteChange(c.candidate_id, e.target.value)}
                      className="resume-textarea !min-h-[4rem] text-xs focus:outline-none"
                      placeholder="Add recommendation remarks for the hiring manager..."
                      rows={2}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mb-4 flex items-start gap-2 rounded-xl border border-amber-100/60 bg-amber-50 p-3 text-xs leading-normal text-amber-800">
            <svg className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <span className="font-semibold block">Important Shortlist Action</span>
              Once confirmed, this selection will fully replace the existing shortlist shared with the Hiring Manager for this campaign. Any unselected candidates will be removed from their view.
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
              {error}
            </div>
          )}

          <div className="workspace-modal-footer shrink-0 pt-3">
            <button
              type="button"
              disabled={isSharing}
              onClick={onClose}
              className="workspace-ghost-button !px-4 !py-2 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={isSharing}
              onClick={onConfirm}
              className="workspace-primary-button !px-5 !py-2 text-xs font-semibold shadow-md shadow-slate-900/10"
            >
              {isSharing ? "Sharing Shortlist..." : "Confirm & Share"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
