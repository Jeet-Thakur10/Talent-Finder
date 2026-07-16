import { useEffect, useState } from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import { dashboardService } from "../../dashboard/services/dashboard.service";
import type { JobDescription } from "../../dashboard/services/dashboard.types";
import { scoringService } from "../services/scoring.service";

export function ResumeImportPage() {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const hasJobId = Boolean(jobId);
  const [job, setJob] =
    useState<JobDescription | null>(null);
  const [resumeText, setResumeText] =
    useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!hasJobId || !jobId) {
      return;
    }

    const loadJob = async () => {
      try {
        setIsLoading(true);
        const result =
          await dashboardService.getJobDescription(
            jobId,
          );

        setJob(result);
      } catch {
        setError(
          "Unable to load the selected job description.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    void loadJob();
  }, [hasJobId, jobId]);

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!jobId) {
      return;
    }

    try {
      setError("");
      setIsSubmitting(true);

      const response =
        await scoringService.importCandidate({
          job_description_id: jobId,
          resume_text: resumeText,
        });

      navigate(
        `/dashboard/job-descriptions/${jobId}/candidates/${response.candidate.id}/score`,
      );
    } catch {
      setError(
        "Resume import failed. Check the text format and try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <div className="auth-kicker">
            Resume Import
          </div>

          <h1 className="workspace-title">
            Import Candidate Resume
          </h1>

          <p className="workspace-subtitle">
            Paste raw resume text and run the
            parsing + scoring pipeline for the
            selected job description.
          </p>
        </div>

        <Link
          to="/dashboard"
          className="workspace-ghost-button"
        >
          Back to Dashboard
        </Link>
      </div>

      <div className="surface-card surface-card-hero">
        {isLoading ? (
          <p className="empty-copy">
            Loading job details...
          </p>
        ) : !hasJobId ? (
          <div className="workspace-alert">
            Missing job description.
          </div>
        ) : job ? (
          <>
            <div className="section-header">
              <div>
                <h2 className="section-title">
                  {job.title}
                </h2>

                <p className="section-copy">
                  {job.location} •{" "}
                  {job.max_experience === null || job.max_experience === undefined
                    ? `${job.min_experience}+ years`
                    : `${job.min_experience} - ${job.max_experience} years`}
                </p>
              </div>
            </div>

            <form
              onSubmit={handleSubmit}
              className="import-form"
            >
              <label
                htmlFor="resume-text"
                className="auth-label"
              >
                Resume Text
              </label>

              <textarea
                id="resume-text"
                value={resumeText}
                onChange={(event) =>
                  setResumeText(
                    event.target.value,
                  )
                }
                placeholder="Paste the full resume text here..."
                className="resume-textarea"
                rows={18}
              />

              {error && (
                <div className="workspace-alert">
                  {error}
                </div>
              )}

              <div className="button-row">
                <button
                  type="submit"
                  disabled={
                    isSubmitting ||
                    resumeText.trim().length < 20
                  }
                  className="workspace-primary-button"
                >
                  {isSubmitting
                    ? "Scoring Candidate..."
                    : "Import and Score"}
                </button>
              </div>
            </form>
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
