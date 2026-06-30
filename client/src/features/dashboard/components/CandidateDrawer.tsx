import type {
  CandidateEvaluationBoard,
} from "../services/dashboard.types";

function formatDate(value: string | null) {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleDateString();
}

interface CandidateDrawerProps {
  board: CandidateEvaluationBoard | null;
  isLoading: boolean;
  notesDraft: string;
  onClose: () => void;
  onNotesChange: (value: string) => void;
  onSaveNotes: () => void;
  isSavingNotes: boolean;
}

const BREAKDOWN_ITEMS = [
  {
    key: "skill_score",
    label: "Skill Score",
  },
  {
    key: "experience_score",
    label: "Experience Score",
  },
  {
    key: "recency_score",
    label: "Recency Score",
  },
  {
    key: "role_fit_score",
    label: "Role Fit Score",
  },
  {
    key: "education_score",
    label: "Education Score",
  },
  {
    key: "confidence",
    label: "Confidence",
  },
] as const;

export function CandidateDrawer({
  board,
  isLoading,
  notesDraft,
  onClose,
  onNotesChange,
  onSaveNotes,
  isSavingNotes,
}: CandidateDrawerProps) {
  if (!board && !isLoading) {
    return null;
  }

  return (
    <aside className="candidate-drawer">
      <div className="section-header">
        <div>
          <h2 className="section-title">
            Candidate Deep-Dive
          </h2>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="workspace-ghost-button"
        >
          Close
        </button>
      </div>

      {isLoading ? (
        <p className="empty-copy">
          Loading candidate profile...
        </p>
      ) : !board ? (
        <p className="empty-copy">
          Select a candidate from the board to inspect their evaluation.
        </p>
      ) : (
        <div className="stack-list">
          <section className="detail-block">
            <div className="section-header">
              <div>
                <h3 className="section-title">
                  {board.candidate.full_name}
                </h3>

                <p className="section-copy">
                  {board.candidate.current_title ??
                    "Candidate profile"}
                </p>
              </div>

              <span className="score-pill">
                {board.score
                  ? `${board.score.final_score}%`
                  : "--"}
              </span>
            </div>

            <div className="detail-grid">
              <div>
                <div className="detail-label">
                  Email
                </div>
                <p className="detail-copy">
                  {board.candidate.email ??
                    "Not extracted"}
                </p>
              </div>

              <div>
                <div className="detail-label">
                  Phone
                </div>
                <p className="detail-copy">
                  {board.candidate.phone ??
                    "Not extracted"}
                </p>
              </div>

              <div className="detail-block-full">
                <div className="detail-label">
                  Summary
                </div>
                <p className="detail-copy">
                  {board.candidate.summary ??
                    "No summary extracted."}
                </p>
              </div>
            </div>
          </section>

          <section className="detail-block">
            <div className="detail-label">
              Extracted Skills
            </div>

            <div className="chip-row">
              {board.candidate.skills.map(
                (skill) => (
                  <span
                    key={skill.id}
                    className="skill-chip skill-chip-primary"
                  >
                    {skill.skill_name}
                  </span>
                ),
              )}
            </div>
          </section>

          <section className="detail-block">
            <div className="detail-label">
              Experience Background
            </div>

            <div className="stack-list">
              {board.candidate.experiences.map(
                (experience) => (
                  <div
                    key={experience.id}
                    className="timeline-card"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h4 className="job-card-title">
                          {experience.title}
                        </h4>

                        <p className="job-card-meta">
                          {experience.company_name ??
                            "Unknown company"}
                        </p>
                      </div>

                      <span className="score-pill score-pill-muted">
                        {formatDate(
                          experience.start_date,
                        )}
                        {" - "}
                        {experience.is_current
                          ? "Present"
                          : formatDate(
                              experience.end_date,
                            )}
                      </span>
                    </div>

                    {experience.description && (
                      <p className="mt-4 text-sm leading-relaxed text-slate-600 whitespace-pre-wrap">
                        {experience.description}
                      </p>
                    )}
                  </div>
                ),
              )}
            </div>
          </section>

          <section className="detail-block">
            <div className="detail-label">
              Education
            </div>

            <div className="stack-list">
              {board.candidate.educations.map(
                (education) => (
                  <div
                    key={education.id}
                    className="timeline-card"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h4 className="job-card-title">
                          {education.degree}
                          {education.field_of_study ? ` in ${education.field_of_study}` : ""}
                        </h4>

                        <p className="job-card-meta">
                          {education.institution_name ??
                            "Unknown institution"}
                        </p>
                      </div>

                      {(education.start_date || education.end_date) && (
                        <span className="score-pill score-pill-muted">
                          {education.start_date ? formatDate(education.start_date) : ""}
                          {education.start_date && education.end_date ? " - " : ""}
                          {education.end_date ? formatDate(education.end_date) : ""}
                        </span>
                      )}
                    </div>
                  </div>
                ),
              )}
            </div>
          </section>

          <section className="detail-block">
            <div className="detail-label">
              Explainable Breakdown
            </div>

            <div className="score-grid">
              {BREAKDOWN_ITEMS.map((item) => (
                <div
                  key={item.key}
                  className="metric-card"
                >
                  <div className="metric-title">
                    {item.label}
                  </div>

                  <div className="metric-surface-value metric-surface-value-compact">
                    {board.score
                      ? `${board.score[item.key]}%`
                      : "--"}
                  </div>
                </div>
              ))}
            </div>

            {board.score?.explanation && (
              <div className="mt-4 space-y-4 bg-slate-50 rounded-2xl p-5 border border-slate-200">
                {(board.score.explanation as any).summary && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Evaluation Justification</div>
                    <p className="mt-2 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {(board.score.explanation as any).summary}
                    </p>
                  </div>
                )}

                {Array.isArray((board.score.explanation as any).strengths) && (board.score.explanation as any).strengths.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Key Strengths</div>
                    <ul className="mt-2 list-disc list-inside text-sm text-slate-700 space-y-1">
                      {(board.score.explanation as any).strengths.map((strength: string, idx: number) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {Array.isArray((board.score.explanation as any).weaknesses) && (board.score.explanation as any).weaknesses.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Key Weaknesses / Gaps</div>
                    <ul className="mt-2 list-disc list-inside text-sm text-slate-700 space-y-1">
                      {(board.score.explanation as any).weaknesses.map((weakness: string, idx: number) => (
                        <li key={idx}>{weakness}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>

          <section className="detail-block">
            <div className="detail-label">
              Recruiter Notes
            </div>

            <textarea
              value={notesDraft}
              onChange={(event) =>
                onNotesChange(
                  event.target.value,
                )
              }
              className="form-textarea"
              rows={5}
              placeholder="Add recruiter context, concerns, or shortlist rationale."
            />

            <div className="button-row drawer-actions">
              <button
                type="button"
                onClick={onSaveNotes}
                disabled={isSavingNotes}
                className="workspace-primary-button"
              >
                {isSavingNotes
                  ? "Saving Notes..."
                  : "Save Notes"}
              </button>
            </div>
          </section>
        </div>
      )}
    </aside>
  );
}
