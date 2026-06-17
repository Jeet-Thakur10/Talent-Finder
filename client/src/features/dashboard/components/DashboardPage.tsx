import { useEffect, useState } from "react";

import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/hooks/useAuth";
import { authService } from "../../auth/services/auth.service";
import { dashboardService } from "../services/dashboard.service";
import type { JobDescription } from "../services/dashboard.types";
import { scoringService } from "../../scoring/services/scoring.service";
import type { CandidateListItem } from "../../scoring/services/scoring.types";

export function DashboardPage() {
  const navigate = useNavigate();
  const {
    user,
    logout,
  } = useAuth();
  const [jobDescriptions, setJobDescriptions] =
    useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] =
    useState<string | null>(null);
  const [candidates, setCandidates] =
    useState<CandidateListItem[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] =
    useState(true);
  const [isLoadingCandidates, setIsLoadingCandidates] =
    useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadJobDescriptions = async () => {
      try {
        setIsLoadingJobs(true);
        const jobs =
          await dashboardService.listJobDescriptions();

        setJobDescriptions(jobs);
        setSelectedJobId(
          jobs[0]?.id ?? null,
        );
      } catch {
        setError(
          "Unable to load job descriptions right now.",
        );
      } finally {
        setIsLoadingJobs(false);
      }
    };

    void loadJobDescriptions();
  }, []);

  useEffect(() => {
    if (!selectedJobId) {
      return;
    }

    const loadCandidates = async () => {
      try {
        setIsLoadingCandidates(true);
        const items =
          await scoringService.listCandidatesForJob(
            selectedJobId,
          );

        setCandidates(items);
      } catch {
        setCandidates([]);
      } finally {
        setIsLoadingCandidates(false);
      }
    };

    void loadCandidates();
  }, [selectedJobId]);

  const selectedJob =
    jobDescriptions.find(
      (job) => job.id === selectedJobId,
    ) ?? null;

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore API errors and still clear local auth state.
    } finally {
      logout();

      navigate("/login", {
        replace: true,
      });
    }
  };

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <div className="auth-kicker">
            Talent Finder
          </div>

          <h1 className="workspace-title">
            Scoring Dashboard
          </h1>

          <p className="workspace-subtitle">
            Welcome {user?.name}. Select a
            job description and move directly
            into the resume scoring workflow.
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="workspace-ghost-button"
        >
          Logout
        </button>
      </div>

      {error && (
        <div className="workspace-alert">
          {error}
        </div>
      )}

      <div className="workspace-grid">
        <section className="surface-card">
          <div className="section-header">
            <div>
              <h2 className="section-title">
                Job Descriptions
              </h2>

              <p className="section-copy">
                Existing requisitions from the
                backend JD service.
              </p>
            </div>

            <span className="count-chip">
              {jobDescriptions.length}
            </span>
          </div>

          {isLoadingJobs ? (
            <p className="empty-copy">
              Loading job descriptions...
            </p>
          ) : jobDescriptions.length === 0 ? (
            <p className="empty-copy">
              No job descriptions exist yet.
            </p>
          ) : (
            <div className="job-list">
              {jobDescriptions.map((job) => (
                <button
                  key={job.id}
                  type="button"
                  onClick={() =>
                    setSelectedJobId(job.id)
                  }
                  className={`job-card ${
                    selectedJobId === job.id
                      ? "job-card-active"
                      : ""
                  }`}
                >
                  <div className="job-card-header">
                    <div>
                      <h3 className="job-card-title">
                        {job.title}
                      </h3>

                      <p className="job-card-meta">
                        {job.department ??
                          "General"}{" "}
                        • {job.location}
                      </p>
                    </div>

                    <span className="score-pill score-pill-muted">
                      {job.min_experience}
                      {" - "}
                      {job.max_experience} yrs
                    </span>
                  </div>

                  <p className="job-card-copy">
                    {job.job_purpose}
                  </p>

                  <div className="chip-row">
                    {job.skills
                      .slice(0, 4)
                      .map((skill) => (
                        <span
                          key={skill.id}
                          className={`skill-chip ${
                            skill.is_mandatory
                              ? "skill-chip-primary"
                              : "skill-chip-secondary"
                          }`}
                        >
                          {skill.skill_name}
                        </span>
                      ))}
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="surface-card surface-card-hero">
          {selectedJob ? (
            <>
              <div className="section-header">
                <div>
                  <h2 className="section-title">
                    {selectedJob.title}
                  </h2>

                  <p className="section-copy">
                    {selectedJob.location} •{" "}
                    {selectedJob.min_experience}
                    {" - "}
                    {selectedJob.max_experience}
                    {" years"}
                  </p>
                </div>

                <Link
                  to={`/dashboard/job-descriptions/${selectedJob.id}/import`}
                  className="workspace-primary-button"
                >
                  Import Resume
                </Link>
              </div>

              <div className="detail-grid">
                <div className="detail-block">
                  <div className="detail-label">
                    Purpose
                  </div>

                  <p className="detail-copy">
                    {selectedJob.job_purpose}
                  </p>
                </div>

                <div className="detail-block">
                  <div className="detail-label">
                    Education
                  </div>

                  <p className="detail-copy">
                    {
                      selectedJob.education_requirement
                    }
                  </p>
                </div>

                <div className="detail-block detail-block-full">
                  <div className="detail-label">
                    Responsibilities
                  </div>

                  <p className="detail-copy">
                    {
                      selectedJob.responsibilities
                    }
                  </p>
                </div>
              </div>

              <div className="section-header section-header-tight">
                <div>
                  <h3 className="section-title">
                    Scored Candidates
                  </h3>

                  <p className="section-copy">
                    Resume imports and
                    deterministic scores for the
                    selected job.
                  </p>
                </div>
              </div>

              {isLoadingCandidates ? (
                <p className="empty-copy">
                  Loading scored candidates...
                </p>
              ) : candidates.length === 0 ? (
                <p className="empty-copy">
                  No candidates have been scored
                  for this job yet.
                </p>
              ) : (
                <div className="candidate-list">
                  {candidates.map((candidate) => (
                    <div
                      key={candidate.candidate_id}
                      className="candidate-row"
                    >
                      <div>
                        <h4 className="candidate-name">
                          {
                            candidate.full_name
                          }
                        </h4>

                        <p className="candidate-meta">
                          {candidate.current_title ??
                            "Imported candidate"}
                        </p>
                      </div>

                      <div className="candidate-actions">
                        <span className="score-pill">
                          {Math.round(
                            candidate.final_score,
                          )}
                          %
                        </span>

                        <Link
                          to={`/dashboard/job-descriptions/${selectedJob.id}/candidates/${candidate.candidate_id}`}
                          className="workspace-inline-link"
                        >
                          Details
                        </Link>

                        <Link
                          to={`/dashboard/job-descriptions/${selectedJob.id}/candidates/${candidate.candidate_id}/score`}
                          className="workspace-inline-link"
                        >
                          Score
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p className="empty-copy">
              Select a job description to begin.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
