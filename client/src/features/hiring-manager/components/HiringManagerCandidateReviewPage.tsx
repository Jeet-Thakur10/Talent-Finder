import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useCandidateReview } from "../hooks/useCandidateReview";
import { CandidateExperienceTimeline } from "../../../components/candidate/CandidateExperienceTimeline";
import { CandidateSkillsProfile } from "../../../components/candidate/CandidateSkillsProfile";
import { CandidateEducationProfile } from "../../../components/candidate/CandidateEducationProfile";
import { CandidateResumeText } from "../../../components/candidate/CandidateResumeText";
import { CandidateScoreBreakdown } from "../../../components/candidate/CandidateScoreBreakdown";

export function HiringManagerCandidateReviewPage() {
  const { jobDescriptionId, candidateId } = useParams<{ jobDescriptionId: string; candidateId: string }>();
  const navigate = useNavigate();

  const {
    evaluationBoard,
    campaign,
    isLoading,
    isSaving,
    error,
    saveReview,
    scheduleHMInterview,
    retry,
  } = useCandidateReview(jobDescriptionId, candidateId);

  // Local state for decision panel
  const [notes, setNotes] = useState("");
  const [isSavedSuccessfully, setIsSavedSuccessfully] = useState(false);

  // Schedule Interview modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [interviewLink, setInterviewLink] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [interviewTime, setInterviewTime] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [message, setMessage] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateAndSendInvitation = async () => {
    setValidationError(null);

    // 1. Link Validation
    if (!interviewLink.trim()) {
      setValidationError("Interview link is required.");
      return;
    }
    try {
      new URL(interviewLink);
    } catch {
      setValidationError("Please enter a valid URL for the interview link (e.g. https://...).");
      return;
    }

    // 2. Date Validation
    if (!interviewDate) {
      setValidationError("Interview date is required.");
      return;
    }
    if (!interviewTime) {
      setValidationError("Interview time is required.");
      return;
    }

    const selectedDatetime = new Date(`${interviewDate}T${interviewTime}`);
    if (selectedDatetime.getTime() < Date.now()) {
      setValidationError("Interview date and time cannot be in the past.");
      return;
    }

    // 3. Timezone Validation
    if (!timezone.trim()) {
      setValidationError("Timezone is required.");
      return;
    }

    // Submit scheduling
    const success = await scheduleHMInterview({
      interview_link: interviewLink,
      interview_datetime: selectedDatetime.toISOString(),
      timezone: timezone,
      message: message.trim() || null,
    });

    if (success) {
      setIsModalOpen(false);
      // Reset form
      setInterviewLink("");
      setInterviewDate("");
      setInterviewTime("");
      setMessage("");
      setIsSavedSuccessfully(true);
      setTimeout(() => setIsSavedSuccessfully(false), 3000);
    }
  };

  // Sync state from loaded pipeline snapshot
  useEffect(() => {
    if (evaluationBoard?.pipeline) {
      setNotes(evaluationBoard.pipeline.hiring_manager_notes || "");
    }
  }, [evaluationBoard]);

  const handleSaveReview = async () => {
    const success = await saveReview("REJECTED", notes);
    if (success) {
      setIsSavedSuccessfully(true);
      setTimeout(() => setIsSavedSuccessfully(false), 3000);
    }
  };

  const getMatchCategory = (score: number | null) => {
    if (score === null || score === undefined) return { label: "Unrated", badge: "bg-slate-100 text-slate-650 border-slate-200" };
    if (score >= 85) return { label: "Excellent Match", badge: "bg-emerald-100 text-emerald-850 border-emerald-200" };
    if (score >= 70) return { label: "Strong Match", badge: "bg-sky-100 text-sky-850 border-sky-200" };
    if (score >= 50) return { label: "Moderate Match", badge: "bg-amber-100 text-amber-850 border-amber-200" };
    return { label: "Weak Match", badge: "bg-slate-150 text-slate-700 border-slate-300" };
  };

  const getDecisionPill = (decisionVal: "PENDING" | "INTERVIEW_SENT" | "REJECTED") => {
    switch (decisionVal) {
      case "INTERVIEW_SENT":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-250">
            Interview Scheduled
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-250">
            Rejected
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-250">
            Pending Review
          </span>
        );
    }
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
          <p className="text-sm text-slate-500 animate-pulse font-medium">Loading candidate details...</p>
        </div>
      </div>
    );
  }

  if (error || !evaluationBoard) {
    return (
      <div className="workspace-shell">
        <div className="surface-card p-8 text-center max-w-lg mx-auto border border-rose-200/50 bg-rose-50/20 rounded-2xl">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 border border-rose-200">
            <svg className="h-6 w-6 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Failed to Load Candidate Profile</h3>
          <p className="mt-2 text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
            {error || "Unable to retrieve candidate evaluation board details."}
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={retry}
              className="workspace-primary-button !rounded-xl !py-2 !px-4 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { candidate, score, pipeline } = evaluationBoard;
  const match = getMatchCategory(score?.final_score ?? null);
  const experienceYrs = Math.round(candidate.total_experience_months / 12);
  const activeDecision = pipeline?.hm_decision as "PENDING" | "INTERVIEW_SENT" | "REJECTED" || "PENDING";

  return (
    <div className="workspace-shell animate-fade-in">
      {/* 1. Breadcrumbs */}
      <nav className="flex items-center text-xs font-semibold uppercase tracking-[0.16em] text-slate-400 mb-6">
        <span
          onClick={() => navigate("/hm/shared-campaigns")}
          className="hover:text-slate-900 transition cursor-pointer"
        >
          Shared Campaigns
        </span>
        <span className="mx-2">/</span>
        {campaign ? (
          <span
            onClick={() => navigate(`/hm/shared-campaigns/${jobDescriptionId}`)}
            className="hover:text-slate-900 transition cursor-pointer"
          >
            {campaign.title}
          </span>
        ) : (
          <span>Campaign</span>
        )}
        <span className="mx-2">/</span>
        <span className="text-slate-800 font-bold">{candidate.full_name}</span>
      </nav>

      {/* Header Actions */}
      <div className="flex items-center justify-between mb-6">
        <button
          type="button"
          onClick={() => navigate(`/hm/shared-campaigns/${jobDescriptionId}`)}
          className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-sm font-semibold flex items-center gap-1.5 focus:outline-none cursor-pointer"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Campaign
        </button>
      </div>

      {/* Main Responsive Grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Candidate Hero Card Summary */}
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-5">
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Shortlisted Candidate</span>
                <h1 className="text-2xl font-black text-slate-900 leading-none">{candidate.full_name}</h1>
                <p className="text-sm text-slate-655 font-medium">{candidate.current_title || "No Title Specified"}</p>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                  <span>📍 {candidate.location || "Location N/A"}</span>
                  <span>•</span>
                  <span>💼 {experienceYrs} Years Experience</span>
                </p>
              </div>

              {/* Match Score Display */}
              <div className="flex items-center gap-4 bg-slate-50/50 p-4 border border-slate-200/60 rounded-2xl shrink-0">
                <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Match Score</span>
                  <span className="text-3xl font-black text-slate-950 block leading-tight">
                    {score ? `${Math.round(score.final_score)}%` : "N/A"}
                  </span>
                  <div className="flex items-center gap-1.5 mt-1 justify-end">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border ${match.badge}`}>
                      {match.label}
                    </span>
                    {getDecisionPill(activeDecision)}
                  </div>
                </div>
              </div>
            </div>

            {/* Resume Action Footer */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Source: <span className="font-semibold text-slate-600 capitalize">{candidate.source_type}</span>
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
                Download Resume
              </button>
            </div>
          </div>

          {/* Why this candidate was shortlisted (Recruiter Remarks) */}
          {pipeline?.recruiter_notes && (
            <div className="surface-card bg-indigo-50/30 border border-indigo-100 rounded-2xl p-6">
              <h3 className="text-xs font-bold text-indigo-700 uppercase tracking-widest flex items-center gap-2 mb-3">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                Why this candidate was shortlisted
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed italic">
                "{pipeline.recruiter_notes}"
              </p>
            </div>
          )}

          {/* Experience Timeline */}
          <CandidateExperienceTimeline experiences={candidate.experiences} />

          {/* Skills chips */}
          <CandidateSkillsProfile skills={candidate.skills} />

          {/* Education list */}
          <CandidateEducationProfile educations={candidate.educations} />

          {/* Raw Resume text */}
          <CandidateResumeText resumeText={candidate.resume_text} />
        </div>

        {/* Right Column (1/3 width) - Sticky panel & score breakdown */}
        <div className="space-y-6 lg:sticky lg:top-6">
          
          {/* Decision Panel */}
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Decision Panel</h2>
              <p className="text-[10px] text-slate-400 mt-1">Submit your decision and remarks on this candidate.</p>
            </div>

            <div className="space-y-4">
              {activeDecision === "INTERVIEW_SENT" ? (
                <div className="space-y-3.5">
                  <div className="p-4 bg-emerald-50 border border-emerald-200/60 rounded-xl space-y-2">
                    <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-widest block">Status</span>
                    <span className="text-sm font-bold text-slate-900 block">Interview Invitation Sent</span>
                    <div className="text-xs text-slate-655 space-y-1.5 pt-2 border-t border-emerald-100">
                      <p><strong>Link:</strong> <a href={pipeline?.interview_link || ""} target="_blank" rel="noreferrer" className="text-indigo-650 hover:underline break-all">{pipeline?.interview_link}</a></p>
                      <p><strong>Date & Time:</strong> {pipeline?.interview_datetime ? new Date(pipeline.interview_datetime).toLocaleDateString() : "N/A"} at {pipeline?.interview_datetime ? new Date(pipeline.interview_datetime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "N/A"} ({pipeline?.interview_timezone})</p>
                      {pipeline?.interview_message && <p><strong>Message:</strong> "{pipeline.interview_message}"</p>}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(true)}
                    className="w-full workspace-ghost-button !py-2.5 !rounded-xl text-xs font-semibold focus:outline-none cursor-pointer border border-slate-200 hover:border-indigo-250 hover:text-indigo-650"
                  >
                    Reschedule Interview
                  </button>
                </div>
              ) : activeDecision === "REJECTED" ? (
                <div className="space-y-3.5">
                  <div className="p-4 bg-rose-50 border border-rose-200/60 rounded-xl space-y-2">
                    <span className="text-[10px] font-bold text-rose-800 uppercase tracking-widest block">Status</span>
                    <span className="text-sm font-bold text-slate-900 block">Rejected</span>
                    {pipeline?.hiring_manager_notes && (
                      <p className="text-xs text-slate-655 pt-2 border-t border-rose-100">
                        <strong>Remarks:</strong> "{pipeline.hiring_manager_notes}"
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(true)}
                    className="w-full workspace-primary-button !py-2.5 !rounded-xl text-xs font-semibold focus:outline-none cursor-pointer shadow-sm"
                  >
                    Schedule Interview
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Review Remarks (Optional)</label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="resume-textarea !min-h-[7rem] text-xs focus:outline-none"
                      placeholder="Add remarks or justification prior to scheduling or rejecting..."
                      rows={4}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <button
                      type="button"
                      disabled={isSaving}
                      onClick={handleSaveReview}
                      className="workspace-ghost-button !py-2.5 !rounded-xl text-xs font-semibold focus:outline-none cursor-pointer border border-rose-200 text-rose-700 hover:bg-rose-50"
                    >
                      {isSaving ? "Saving..." : "Reject"}
                    </button>
                    <button
                      type="button"
                      disabled={isSaving}
                      onClick={() => setIsModalOpen(true)}
                      className="workspace-primary-button !py-2.5 !rounded-xl text-xs font-semibold focus:outline-none cursor-pointer shadow-sm"
                    >
                      Schedule Interview
                    </button>
                  </div>
                  {isSavedSuccessfully && (
                    <p className="text-[10px] text-emerald-600 font-bold text-center">✓ Rejection saved successfully</p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Scoring breakdown */}
          <CandidateScoreBreakdown score={score} />
        </div>
      </div>

      {/* 6. Schedule Interview Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.25)] max-w-lg w-full overflow-hidden animate-scale-up">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div>
                <h3 className="text-base font-bold text-slate-900">Schedule Interview</h3>
                <p className="text-xs text-slate-500 mt-0.5">Send an interview invitation email directly to the candidate.</p>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 transition focus:outline-none cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4">
              {validationError && (
                <div className="p-3.5 bg-rose-50 border border-rose-200/50 rounded-xl text-xs font-semibold text-rose-700 leading-normal animate-shake">
                  ⚠ {validationError}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-655 uppercase tracking-wider block">Interview Link *</label>
                <input
                  type="text"
                  value={interviewLink}
                  onChange={(e) => setInterviewLink(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:border-slate-900 focus:bg-white outline-none transition"
                  placeholder="https://meet.google.com/abc-defg-hij"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-655 uppercase tracking-wider block">Interview Date *</label>
                  <input
                    type="date"
                    value={interviewDate}
                    onChange={(e) => setInterviewDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:border-slate-900 focus:bg-white outline-none transition"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-655 uppercase tracking-wider block">Interview Time *</label>
                  <input
                    type="time"
                    value={interviewTime}
                    onChange={(e) => setInterviewTime(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-800 focus:border-slate-900 focus:bg-white outline-none transition"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-655 uppercase tracking-wider block">Timezone *</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs font-semibold text-slate-800 focus:border-slate-900 focus:bg-white outline-none transition"
                  required
                >
                  <option value="UTC">UTC (GMT)</option>
                  <option value="EST">EST (Eastern Standard Time)</option>
                  <option value="CST">CST (Central Standard Time)</option>
                  <option value="PST">PST (Pacific Standard Time)</option>
                  <option value="IST">IST (Indian Standard Time)</option>
                  <option value="GMT">GMT (Greenwich Mean Time)</option>
                  <option value="CET">CET (Central European Time)</option>
                  <option value="AEDT">AEDT (Australian Eastern Daylight Time)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-655 uppercase tracking-wider block">Optional Message</label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="resume-textarea !min-h-[6rem] text-xs focus:outline-none"
                  placeholder="Introduce yourself, list requirements, or outline prep material..."
                  rows={3}
                />
              </div>
            </div>

            <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-xs font-bold border border-slate-200 hover:bg-slate-100 focus:outline-none cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSaving}
                onClick={validateAndSendInvitation}
                className="workspace-primary-button !py-2.5 !px-5 !rounded-xl text-xs font-black shadow-md focus:outline-none cursor-pointer"
              >
                {isSaving ? "Sending Invitation..." : "Send Invitation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
