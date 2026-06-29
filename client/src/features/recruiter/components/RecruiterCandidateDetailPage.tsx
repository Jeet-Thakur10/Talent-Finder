import { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useRecruiterCandidateDetail } from "../hooks/useRecruiterCandidateDetail";
import { CandidateExperienceTimeline } from "../../../components/candidate/CandidateExperienceTimeline";
import { CandidateSkillsProfile } from "../../../components/candidate/CandidateSkillsProfile";
import { CandidateEducationProfile } from "../../../components/candidate/CandidateEducationProfile";
import { CandidateResumeText } from "../../../components/candidate/CandidateResumeText";
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

  const handleDownloadResume = () => {
    if (!evaluationBoard?.candidate?.resume_text) return;
    const element = document.createElement("a");
    const file = new Blob([evaluationBoard.candidate.resume_text], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = `${evaluationBoard.candidate.full_name}_Resume.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
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
      <nav className="flex items-center text-xs font-semibold uppercase tracking-[0.16em] text-slate-400 mb-6">
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
      <div className="flex items-center justify-between mb-6">
        <button
          type="button"
          onClick={() => navigate(`/recruiter/job-descriptions/${jobDescriptionId}/candidates`)}
          className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-sm font-semibold flex items-center gap-1.5 focus:outline-none"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Candidate List
        </button>
      </div>

      {/* Grid Layout: Left Column (Profile & Timelines) + Right Column (Scoring & Remarks) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (2/3 width on large screens) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* 2. Candidate Hero Section */}
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-5">
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Candidate Profile</span>
                <h1 className="text-2xl font-black text-slate-900 leading-none">{candidate.full_name}</h1>
                <p className="text-sm text-slate-650 font-medium">{candidate.current_title || "No Title Specified"}</p>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                  <span>📍 {candidate.location || "Location Not Extracted"}</span>
                  <span>•</span>
                  <span>💼 {experienceYrs} Years Experience</span>
                </p>
              </div>

              {/* Score Highlight Box */}
              <div className="flex items-center gap-4 bg-slate-50/50 p-4 border border-slate-200/60 rounded-2xl shrink-0">
                <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Overall Fit Score</span>
                  <span className="text-3xl font-black text-slate-950 block leading-tight">
                    {score ? `${Math.round(score.final_score)}%` : "N/A"}
                  </span>
                  <span className={`inline-flex items-center px-2 py-0.5 mt-1 rounded-full text-[9px] font-bold uppercase tracking-wider border ${match.badge}`}>
                    {match.label}
                  </span>
                  {evaluationBoard?.pipeline?.hm_decision === "INTERVIEW_SENT" && (
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-250">
                        Interview Scheduled
                      </span>
                    </div>
                  )}
                  {evaluationBoard?.pipeline?.hm_decision === "REJECTED" && (
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-250">
                        Rejected by HM
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Hero CTAs */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Source Type: <span className="font-semibold text-slate-600 capitalize">{candidate.source_type}</span>
              </span>
              <button
                type="button"
                disabled={!candidate.resume_text}
                onClick={handleDownloadResume}
                className="workspace-primary-button !py-2 !px-4 !rounded-xl text-xs font-semibold flex items-center gap-1.5 focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {candidate.resume_text ? "Download Resume" : "Resume Not Uploaded"}
              </button>
            </div>
          </div>

          {/* Interview Details (If scheduled) */}
          {evaluationBoard?.pipeline?.interview_link && (
            <div className="surface-card bg-emerald-50/10 border border-emerald-200/50 rounded-2xl p-6 space-y-4">
              <h2 className="text-sm font-bold text-emerald-800 border-b border-emerald-100 pb-2 flex items-center gap-2">
                📅 Scheduled Interview Details
              </h2>
              <div className="space-y-2 text-sm text-slate-700">
                <p><strong>Date & Time:</strong> {evaluationBoard.pipeline.interview_datetime ? new Date(evaluationBoard.pipeline.interview_datetime).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : "N/A"} at {evaluationBoard.pipeline.interview_datetime ? new Date(evaluationBoard.pipeline.interview_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : "N/A"} ({evaluationBoard.pipeline.interview_timezone})</p>
                <p><strong>Interview Link:</strong> <a href={evaluationBoard.pipeline.interview_link} target="_blank" rel="noreferrer" className="text-indigo-650 hover:underline">{evaluationBoard.pipeline.interview_link}</a></p>
                {evaluationBoard.pipeline.interview_message && <p><strong>Hiring Manager Message:</strong> "{evaluationBoard.pipeline.interview_message}"</p>}
                {evaluationBoard.pipeline.interview_sent_at && <p className="text-xs text-slate-400 mt-2 pt-2 border-t border-slate-100/50">Invitation sent: {new Date(evaluationBoard.pipeline.interview_sent_at).toLocaleString()}</p>}
              </div>
            </div>
          )}

          {/* 4. Professional Summary */}
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Professional Summary</h2>
            <p className="text-sm text-slate-650 leading-relaxed whitespace-pre-wrap">
              {candidate.summary || "No professional summary details extracted from the candidate resume."}
            </p>
          </div>

          {/* 5. Experience Timeline Component */}
          <CandidateExperienceTimeline experiences={candidate.experiences} />

          {/* 6. Skills Component */}
          <CandidateSkillsProfile skills={candidate.skills} />

          {/* 7. Education Component */}
          <CandidateEducationProfile educations={candidate.educations} />

          {/* 8. Resume Text Component */}
          <CandidateResumeText resumeText={candidate.resume_text} />

        </div>

        {/* Right Column (1/3 width on large screens) */}
        <div className="space-y-6">
          
          {/* 3. Score Breakdown Component */}
          <CandidateScoreBreakdown score={score} />

          {/* 9. Recruiter Remarks */}
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Recruiter Remarks</h2>
              <p className="text-[10px] text-slate-400 mt-1">Private annotations and shortlist comments visible to you.</p>
            </div>

            <div className="space-y-3">
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                className="resume-textarea !min-h-[8rem] text-xs focus:outline-none"
                placeholder="Add recruiter notes, candidate feedback, screening results..."
                rows={5}
              />
              
              <div className="flex items-center justify-between">
                {remarksSavedSuccessfully ? (
                  <span className="text-[10px] text-emerald-600 font-bold flex items-center gap-1">
                    ✓ Notes saved
                  </span>
                ) : (
                  <span />
                )}
                
                <button
                  type="button"
                  disabled={isSavingNotes}
                  onClick={handleSaveRemarks}
                  className="workspace-primary-button !py-2 !px-4.5 !rounded-xl text-xs font-semibold focus:outline-none disabled:opacity-50"
                >
                  {isSavingNotes ? "Saving Remarks..." : "Save Remarks"}
                </button>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
