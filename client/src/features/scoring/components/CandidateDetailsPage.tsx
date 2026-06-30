import { useEffect, useState } from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import { scoringService } from "../services/scoring.service";
import type { CandidateDetails } from "../services/scoring.types";

function formatDate(value: string | null) {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleDateString();
}

export function CandidateDetailsPage() {
  const { jobId, candidateId } = useParams();
  const hasRouteContext = Boolean(
    jobId && candidateId,
  );
  const [candidate, setCandidate] =
    useState<CandidateDetails | null>(null);
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!hasRouteContext || !jobId || !candidateId) {
      return;
    }

    const loadCandidate = async () => {
      try {
        setIsLoading(true);
        const result =
          await scoringService.getCandidateDetails(
            jobId,
            candidateId,
          );

        setCandidate(result);
      } catch {
        setError(
          "Unable to load candidate details.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    void loadCandidate();
  }, [
    candidateId,
    hasRouteContext,
    jobId,
  ]);

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <div className="auth-kicker">
            Candidate Profile
          </div>

          <h1 className="workspace-title">
            Candidate Details
          </h1>
        </div>

        <div className="button-row">
          <Link
            to="/dashboard"
            className="workspace-ghost-button"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="surface-card surface-card-hero">
        {isLoading ? (
          <p className="empty-copy">
            Loading candidate details...
          </p>
        ) : !hasRouteContext ? (
          <div className="workspace-alert">
            Missing candidate context.
          </div>
        ) : candidate ? (
          <>
            <div className="section-header">
              <div>
                <h2 className="section-title">
                  {candidate.full_name}
                </h2>

                <p className="section-copy">
                  {candidate.current_title ??
                    "Imported candidate"}
                </p>
              </div>

              <span className="score-pill score-pill-muted">
                {Math.round(
                  candidate.total_experience_months /
                    12,
                )}
                {" yrs"}
              </span>
            </div>

            <div className="detail-grid">
              <div className="detail-block">
                <div className="detail-label">
                  Email
                </div>

                <p className="detail-copy">
                  {candidate.email ??
                    "Not extracted"}
                </p>
              </div>

              <div className="detail-block">
                <div className="detail-label">
                  Phone
                </div>

                <p className="detail-copy">
                  {candidate.phone ??
                    "Not extracted"}
                </p>
              </div>

              <div className="detail-block">
                <div className="detail-label">
                  Location
                </div>

                <p className="detail-copy">
                  {candidate.location ??
                    "Not extracted"}
                </p>
              </div>

              <div className="detail-block detail-block-full">
                <div className="detail-label">
                  Summary
                </div>

                <p className="detail-copy">
                  {candidate.summary ??
                    "No summary extracted."}
                </p>
              </div>
            </div>

            <div className="section-header section-header-tight">
              <div>
                <h3 className="section-title">
                  Skills
                </h3>
              </div>
            </div>

            <div className="chip-row">
              {candidate.skills.map((skill) => (
                <span
                  key={skill.id}
                  className="skill-chip skill-chip-primary"
                >
                  {skill.skill_name}
                </span>
              ))}
            </div>

            <div className="section-header section-header-tight">
              <div>
                <h3 className="section-title">
                  Experience
                </h3>
              </div>
            </div>

            <div className="stack-list">
              {candidate.experiences.map(
                (experience) => (
                  <div
                    key={experience.id}
                    className="timeline-card"
                  >
                    <div className="job-card-header">
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

                    <p className="detail-copy">
                      {experience.description ??
                        "No description extracted."}
                    </p>

                    <div className="chip-row">
                      {experience.skills.map(
                        (skill) => (
                          <span
                            key={skill.id}
                            className="skill-chip skill-chip-secondary"
                          >
                            {
                              skill.skill_name
                            }
                          </span>
                        ),
                      )}
                    </div>
                  </div>
                ),
              )}
            </div>

            <div className="section-header section-header-tight">
              <div>
                <h3 className="section-title">
                  Education
                </h3>
              </div>
            </div>

            <div className="stack-list">
              {candidate.educations.map(
                (education) => (
                  <div
                    key={education.id}
                    className="timeline-card"
                  >
                    <h4 className="job-card-title">
                      {education.degree}
                    </h4>

                    <p className="job-card-meta">
                      {education.institution_name ??
                        "Unknown institution"}
                    </p>

                    <p className="detail-copy">
                      {education.field_of_study ??
                        "Field not extracted"}
                    </p>
                  </div>
                ),
              )}
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
