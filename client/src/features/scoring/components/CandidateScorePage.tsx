import { useEffect, useState } from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import { scoringService } from "../services/scoring.service";
import type {
  CandidateDetails,
  CandidateScore,
} from "../services/scoring.types";

const SCORE_LIMITS = {
  skills: 40,
  experience: 25,
  recency: 15,
  role_fit: 12,
  education: 8,
} as const;

export function CandidateScorePage() {
  const { jobId, candidateId } = useParams();
  const hasRouteContext = Boolean(
    jobId && candidateId,
  );
  const [candidate, setCandidate] =
    useState<CandidateDetails | null>(null);
  const [score, setScore] =
    useState<CandidateScore | null>(null);
  const [isLoading, setIsLoading] =
    useState(true);
  const [isRescoring, setIsRescoring] =
    useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!hasRouteContext || !jobId || !candidateId) {
      return;
    }

    const loadData = async () => {
      try {
        setIsLoading(true);
        const [
          candidateResult,
          scoreResult,
        ] = await Promise.all([
          scoringService.getCandidateDetails(
            jobId,
            candidateId,
          ),
          scoringService.getCandidateScore(
            jobId,
            candidateId,
          ),
        ]);

        setCandidate(candidateResult);
        setScore(scoreResult);
      } catch {
        setError(
          "Unable to load the candidate score.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    void loadData();
  }, [
    candidateId,
    hasRouteContext,
    jobId,
  ]);

  const handleRescore = async () => {
    if (!jobId || !candidateId) {
      return;
    }

    try {
      setIsRescoring(true);
      const updatedScore =
        await scoringService.rescoreCandidate(
          jobId,
          candidateId,
        );

      setScore(updatedScore);
    } catch {
      setError(
        "Unable to refresh the score right now.",
      );
    } finally {
      setIsRescoring(false);
    }
  };

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <div className="auth-kicker">
            Scoring Result
          </div>

          <h1 className="workspace-title">
            Candidate Score View
          </h1>
        </div>

        <div className="button-row">
          <Link
            to="/dashboard"
            className="workspace-ghost-button"
          >
            Dashboard
          </Link>

          {jobId && candidateId && (
            <Link
              to={`/dashboard/job-descriptions/${jobId}/candidates/${candidateId}`}
              className="workspace-ghost-button"
            >
              Candidate Details
            </Link>
          )}

          <button
            type="button"
            onClick={handleRescore}
            disabled={isRescoring}
            className="workspace-primary-button"
          >
            {isRescoring
              ? "Re-scoring..."
              : "Re-score"}
          </button>
        </div>
      </div>

      <div className="surface-card surface-card-hero">
        {isLoading ? (
          <p className="empty-copy">
            Loading score...
          </p>
        ) : !hasRouteContext ? (
          <div className="workspace-alert">
            Missing scoring context.
          </div>
        ) : candidate && score ? (
          <>
            <div className="score-hero">
              <div>
                <h2 className="section-title">
                  {candidate.full_name}
                </h2>

                <p className="section-copy">
                  {candidate.current_title ??
                    "Imported candidate"}
                </p>
              </div>

              <div className="score-cluster">
                <div className="score-badge">
                  <span className="score-badge-value">
                    {Math.round(
                      score.final_score,
                    )}
                    %
                  </span>

                  <span className="score-badge-label">
                    Final Score
                  </span>
                </div>

                <div className="score-badge score-badge-secondary">
                  <span className="score-badge-value">
                    {Math.round(
                      score.confidence,
                    )}
                    %
                  </span>

                  <span className="score-badge-label">
                    Confidence
                  </span>
                </div>
              </div>
            </div>

            {error && (
              <div className="workspace-alert">
                {error}
              </div>
            )}

            <div className="score-grid">
              {(
                Object.keys(
                  score.breakdown,
                ) as Array<
                  keyof typeof score.breakdown
                >
              ).map((key) => (
                <div
                  key={key}
                  className="metric-card"
                >
                  <div className="metric-header">
                    <span className="metric-title">
                      {key
                        .replace("_", " ")
                        .replace(
                          /\b\w/g,
                          (char) =>
                            char.toUpperCase(),
                        )}
                    </span>

                    <span className="metric-value">
                      {
                        score.breakdown[
                          key
                        ]
                      }
                      {" / "}
                      {SCORE_LIMITS[key]}
                    </span>
                  </div>

                  <div className="metric-bar">
                    <span
                      className="metric-bar-fill"
                      style={{
                        width: `${
                          (score.breakdown[key] /
                            SCORE_LIMITS[
                              key
                            ]) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="detail-grid">
              <div className="detail-block">
                <div className="detail-label">
                  Matched Mandatory Skills
                </div>

                <div className="chip-row">
                  {score.matched_mandatory_skills.map(
                    (skill) => (
                      <span
                        key={skill}
                        className="skill-chip skill-chip-primary"
                      >
                        {skill}
                      </span>
                    ),
                  )}
                </div>
              </div>

              <div className="detail-block">
                <div className="detail-label">
                  Matched Optional Skills
                </div>

                <div className="chip-row">
                  {score.matched_optional_skills.map(
                    (skill) => (
                      <span
                        key={skill}
                        className="skill-chip skill-chip-secondary"
                      >
                        {skill}
                      </span>
                    ),
                  )}
                </div>
              </div>

              <div className="detail-block detail-block-full">
                <div className="detail-label">
                  Missing Mandatory Skills
                </div>

                <div className="chip-row">
                  {score.missing_mandatory_skills
                    .length === 0 ? (
                    <span className="skill-chip skill-chip-success">
                      None
                    </span>
                  ) : (
                    score.missing_mandatory_skills.map(
                      (skill) => (
                        <span
                          key={skill}
                          className="skill-chip skill-chip-danger"
                        >
                          {skill}
                        </span>
                      ),
                    )
                  )}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="workspace-alert">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
