import { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useRecruiterCandidateDetail } from "../hooks/useRecruiterCandidateDetail";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type { JobDescriptionStatus } from "../../dashboard/services/dashboard.types";
import { CandidateExperienceTimeline } from "../../../components/candidate/CandidateExperienceTimeline";
import { CandidateSkillsProfile } from "../../../components/candidate/CandidateSkillsProfile";
import { CandidateEducationProfile } from "../../../components/candidate/CandidateEducationProfile";
import { CandidateScoreBreakdown } from "../../../components/candidate/CandidateScoreBreakdown";

export function RecruiterCandidateDetailPage() {
  const { jobDescriptionId, candidateId } = useParams<{ jobDescriptionId: string; candidateId: string }>();
  const navigate = useNavigate();

  const {
    evaluationBoard,
    jobDescription,
    isLoading,
    isSavingNotes,
    error,
    saveRemarks,
  } = useRecruiterCandidateDetail(jobDescriptionId, candidateId);

  // Remarks state
  const [remarks, setRemarks] = useState("");
  const [remarksSavedSuccessfully, setRemarksSavedSuccessfully] = useState(false);

  const [statuses, setStatuses] = useState<JobDescriptionStatus[]>([]);
  useEffect(() => {
    dashboardService.listJobDescriptionStatuses().then(setStatuses).catch(() => {});
  }, []);

  const jobStatus = jobDescription ? statuses.find((s) => s.id === jobDescription.status_id) : null;
  const isCampaignClosed = jobStatus ? jobStatus.code.toUpperCase() === "CLOSED" : false;

  // Sync remarks state when evaluationBoard loads
  useEffect(() => {
    if (evaluationBoard?.pipeline?.recruiter_notes) {
      setRemarks(evaluationBoard.pipeline.recruiter_notes);
    }
  }, [evaluationBoard]);

  const handleSaveRemarks = async () => {
    const success = await saveRemarks(remarks);
    if (success) {
      setRemarksSavedSuccessfully(true);
      setTimeout(() => setRemarksSavedSuccessfully(false), 3000);
    }
  };

  const getMatchCategory = (score: number | null) => {
    if (score === null || score === undefined) return { label: "Unrated", badge: "bg-slate-100 text-slate-650 border-slate-200" };
    if (score >= 85) return { label: "Excellent Match", badge: "bg-emerald-100 text-emerald-850 border-emerald-200" };
    if (score >= 70) return { label: "Strong Match", badge: "bg-sky-100 text-sky-850 border-sky-200" };
    if (score >= 50) return { label: "Moderate Match", badge: "bg-amber-100 text-amber-850 border-amber-200" };
    return { label: "Weak Match", badge: "bg-slate-150 text-slate-700 border-slate-300" };
  };



  if (isLoading) {
    return (
      <div className="workspace-shell">
        <div className="surface-card flex justify-center py-12">
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading candidate deep-dive...</p>
        </div>
      </div>
    );
  }

  if (error || !evaluationBoard) {
    return (
      <div className="workspace-shell">
        <div className="workspace-alert max-w-2xl mx-auto">
          {error || "Candidate profile or evaluation board not found."}
        </div>
      </div>
    );
  }

  const { candidate, score } = evaluationBoard;
  const match = getMatchCategory(score?.final_score ?? null);
  const experienceYrs = Math.round(candidate.total_experience_months / 12);

  return (
    <div className="workspace-shell animate-fade-in">
      {/* 1. Breadcrumb */}
      <nav className="workspace-breadcrumbs mb-6">
        <Link to="/recruiter/job-descriptions" className="hover:text-slate-900 transition">
          Job Descriptions
        </Link>
        <span className="mx-2">/</span>
        {jobDescription ? (
          <Link
            to={`/recruiter/job-descriptions/${jobDescriptionId}`}
            className="hover:text-slate-900 transition"
          >
            {jobDescription.title}
          </Link>
        ) : (
          <span>Job Details</span>
        )}
        <span className="mx-2">/</span>
        <Link
          to={`/recruiter/job-descriptions/${jobDescriptionId}/candidates`}
          className="hover:text-slate-900 transition"
        >
          Candidates
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-800 font-bold">{candidate.full_name}</span>
      </nav>

      {/* Header Actions */}
      <div className="mb-6 flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}/candidates`)}
          className="workspace-ghost-button !px-5 !py-2.5 text-sm"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Candidate List
        </button>
      </div>

      <div className="space-y-6">
        <div className="surface-card space-y-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0 space-y-2">
              <span className="block text-[10px] font-bold uppercase tracking-widest text-slate-400">Candidate Profile</span>
              <h1 className="break-words text-2xl font-black leading-tight text-slate-900">{candidate.full_name}</h1>
              <p className="text-sm font-medium text-slate-650">{candidate.current_title || "No Title Specified"}</p>
              <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
                <span>Location: <span className="font-semibold text-slate-700">{candidate.location || "Not Extracted"}</span></span>
                <span>Experience: <span className="font-semibold text-slate-700">{experienceYrs} Years</span></span>
                <span>Source: <span className="font-semibold capitalize text-slate-700">{candidate.source_type}</span></span>
              </div>
            </div>

            <div className="grid min-w-[15rem] gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-4 py-3">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Overall Fit Score</span>
                <span className="mt-1 block text-3xl font-black leading-tight text-slate-950">
                  {score ? `${Math.round(score.final_score)}%` : "N/A"}
                </span>
              </div>
              <div className="rounded-[1rem] border border-slate-200 bg-white px-4 py-3">
                <span className={`status-badge text-[9px] uppercase tracking-[0.14em] ${match.badge}`}>
                  {match.label}
                </span>
                {evaluationBoard?.pipeline?.hm_decision === "INTERVIEW_SENT" && (
                  <div className="mt-2">
                    <span className="status-badge border-emerald-250 bg-emerald-50 text-[9px] uppercase tracking-[0.14em] text-emerald-700">
                      Interview Scheduled
                    </span>
                  </div>
                )}
                {evaluationBoard?.pipeline?.hm_decision === "REJECTED" && (
                  <div className="mt-2">
                    <span className="status-badge border-rose-250 bg-rose-50 text-[9px] uppercase tracking-[0.14em] text-rose-700">
                      Rejected by HM
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {evaluationBoard?.pipeline?.interview_link && (
          <div className="surface-card space-y-4 border border-emerald-200/60 bg-emerald-50/20">
            <h2 className="flex items-center gap-2 border-b border-emerald-100 pb-2 text-sm font-bold text-emerald-800">
              Scheduled Interview Details
            </h2>
            <div className="space-y-2 text-sm text-slate-700">
              <p><strong>Date & Time:</strong> {evaluationBoard.pipeline.interview_datetime ? new Date(evaluationBoard.pipeline.interview_datetime).toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" }) : "N/A"} at {evaluationBoard.pipeline.interview_datetime ? new Date(evaluationBoard.pipeline.interview_datetime).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }) : "N/A"} ({evaluationBoard.pipeline.interview_timezone})</p>
              <p><strong>Interview Link:</strong> <a href={evaluationBoard.pipeline.interview_link} target="_blank" rel="noreferrer" className="text-indigo-650 hover:underline">{evaluationBoard.pipeline.interview_link}</a></p>
              {evaluationBoard.pipeline.interview_message && <p><strong>Hiring Manager Message:</strong> "{evaluationBoard.pipeline.interview_message}"</p>}
              {evaluationBoard.pipeline.interview_sent_at && <p className="mt-2 border-t border-slate-100/50 pt-2 text-xs text-slate-400">Invitation sent: {new Date(evaluationBoard.pipeline.interview_sent_at).toLocaleString()}</p>}
            </div>
          </div>
        )}

        <div className="surface-card space-y-4">
          <h2 className="border-b border-slate-100 pb-2 text-sm font-bold text-slate-900">Professional Summary</h2>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-650">
            {candidate.summary || "No professional summary details extracted from the candidate resume."}
          </p>
        </div>

        <CandidateScoreBreakdown score={score} />

        <div className="grid gap-6 lg:grid-cols-2">
          <CandidateSkillsProfile
            skills={candidate.skills}
            matchedMandatorySkills={score?.matched_mandatory_skills}
            matchedOptionalSkills={score?.matched_optional_skills}
            missingMandatorySkills={score?.missing_mandatory_skills}
          />
          <CandidateEducationProfile educations={candidate.educations} />
        </div>

        <CandidateExperienceTimeline experiences={candidate.experiences} />

        <div className="surface-card space-y-4">
          <div>
            <h2 className="border-b border-slate-100 pb-2 text-sm font-bold text-slate-900">Recruiter Remarks</h2>
            <p className="mt-1 text-[10px] text-slate-400">Private annotations and shortlist comments visible to you.</p>
          </div>

          <div className="space-y-3">
            <textarea
              value={remarks}
              disabled={isCampaignClosed}
              onChange={(e) => setRemarks(e.target.value)}
              className={`resume-textarea !min-h-[8rem] text-xs focus:outline-none ${isCampaignClosed ? "opacity-60 cursor-not-allowed bg-slate-50" : ""}`}
              placeholder="Add recruiter notes, candidate feedback, screening results..."
              rows={5}
            />

            <div className="flex items-center justify-between gap-3">
              {remarksSavedSuccessfully ? (
                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600">
                  ✓ Notes saved
                </span>
              ) : (
                <span />
              )}

              <button
                type="button"
                disabled={isSavingNotes || isCampaignClosed}
                onClick={handleSaveRemarks}
                title={isCampaignClosed ? "This campaign has been completed." : undefined}
                className={`workspace-primary-button !px-4 !py-2 text-xs font-semibold ${isCampaignClosed ? "opacity-50 cursor-not-allowed" : "disabled:opacity-50"}`}
              >
                {isSavingNotes ? "Saving Remarks..." : "Save Remarks"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
