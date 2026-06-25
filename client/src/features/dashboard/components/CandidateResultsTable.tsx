import type {
  PipelineCandidateResult,
} from "../services/dashboard.types";

function formatExperience(
  totalExperienceMonths: number,
) {
  return `${(
    totalExperienceMonths / 12
  ).toFixed(1)} yrs`;
}

function formatStage(stage: string) {
  return stage
    .toLowerCase()
    .split("_")
    .map(
      (token) =>
        token.charAt(0).toUpperCase() +
        token.slice(1),
    )
    .join(" ");
}

interface CandidateResultsTableProps {
  candidates: PipelineCandidateResult[];
  isLoading: boolean;
  onOpenCandidate: (
    candidateId: string,
  ) => void;
  onToggleCandidate?: (
    candidateId: string,
  ) => void;
  selectedCandidateIds?: string[];
  isGlobalPoolView?: boolean;
}

export function CandidateResultsTable({
  candidates,
  isLoading,
  onOpenCandidate,
  onToggleCandidate,
  selectedCandidateIds = [],
  isGlobalPoolView = false,
}: CandidateResultsTableProps) {
  if (isLoading) {
    return (
      <p className="empty-copy">
        Loading ranked candidates...
      </p>
    );
  }

  if (candidates.length === 0) {
    return (
      <p className="empty-copy">
        No scored candidates are available for this campaign yet.
      </p>
    );
  }

  return (
    <div className="results-table">
      <div
        className="campaign-table-header candidate-board-header"
        style={isGlobalPoolView ? { gridTemplateColumns: "2.5fr 1.2fr 3fr 1.2fr 1.2fr" } : undefined}
      >
        {!isGlobalPoolView && <span />}
        <span>Candidate</span>
        <span>Score</span>
        <span>Core Skills</span>
        <span>Experience</span>
        <span>Stage</span>
      </div>

      {candidates.map((candidate) => (
        <div
          key={candidate.candidate_id}
          className="campaign-table-row candidate-board-row"
          style={isGlobalPoolView ? { gridTemplateColumns: "2.5fr 1.2fr 3fr 1.2fr 1.2fr" } : undefined}
        >
          {!isGlobalPoolView && onToggleCandidate && (
            <div className="candidate-checkbox-cell">
              <input
                type="checkbox"
                checked={selectedCandidateIds.includes(
                  candidate.candidate_id,
                )}
                onChange={() =>
                  onToggleCandidate(
                    candidate.candidate_id,
                  )
                }
              />
            </div>
          )}

          <button
            type="button"
            onClick={() =>
              onOpenCandidate(
                candidate.candidate_id,
              )
            }
            className="candidate-board-trigger"
          >
            <span className="results-label">
              Candidate
            </span>

            <div>
              <div className="candidate-name">
                {candidate.full_name}
              </div>

              <p className="candidate-meta">
                {candidate.current_title ??
                  "Candidate profile"}
              </p>
            </div>
          </button>

          <div className="results-cell">
            <span className="results-label">
              Score
            </span>

            <div className="results-score-stack">
              <span className="score-pill">
                {candidate.final_score !==
                null
                  ? `${candidate.final_score}%`
                  : "--"}
              </span>

              <span className="candidate-meta">
                Confidence{" "}
                {candidate.confidence !==
                null
                  ? `${candidate.confidence}%`
                  : "--"}
              </span>
            </div>
          </div>

          <div className="results-cell">
            <span className="results-label">
              Core Skills
            </span>

            <div className="chip-row chip-row-compact">
              {candidate.matched_mandatory_skills
                .slice(0, 3)
                .map((skill) => (
                  <span
                    key={skill}
                    className="skill-chip skill-chip-primary"
                  >
                    {skill}
                  </span>
                ))}
            </div>
          </div>

          <div className="results-cell">
            <span className="results-label">
              Experience
            </span>

            <span className="score-pill score-pill-muted">
              {formatExperience(
                candidate.total_experience_months,
              )}
            </span>
          </div>

          <div className="results-cell">
            <span className="results-label">
              Stage
            </span>

            <span className={`status-badge status-badge-${candidate.stage === "FINALIZED" ? "finalized" : "scored"}`}>
              {formatStage(
                candidate.stage,
              )}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
