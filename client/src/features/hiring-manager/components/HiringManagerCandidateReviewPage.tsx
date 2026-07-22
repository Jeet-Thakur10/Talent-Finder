import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useCandidateReview } from "../hooks/useCandidateReview";
import { CandidateExperienceTimeline } from "../../../components/candidate/CandidateExperienceTimeline";
import { CandidateSkillsProfile } from "../../../components/candidate/CandidateSkillsProfile";
import { CandidateEducationProfile } from "../../../components/candidate/CandidateEducationProfile";
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

      // Toast notification
      if (!evaluationBoard?.candidate?.email) {
        toast.success("Candidate approved. No email address was available, so no interview invitation was sent.");
      } else {
        toast.success("Interview scheduled successfully and invitation email sent!");
      }
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
      toast.success("Candidate rejected successfully.");
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
          <span className="status-badge border-emerald-250 bg-emerald-50 text-xs text-emerald-700">
            Interview Scheduled
          </span>
        );
      case "REJECTED":
        return (
          <span className="status-badge border-rose-250 bg-rose-50 text-xs text-rose-700">
            Rejected
          </span>
        );
      case "PENDING":
      default:
        return (
          <span className="status-badge border-slate-250 bg-slate-100 text-xs text-slate-600">
            Pending Review
          </span>
        );
    }
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
      <nav className="workspace-breadcrumbs mb-6">
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
      <div className="mb-6 flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate(`/hm/shared-campaigns/${jobDescriptionId}`)}
          className="workspace-ghost-button !px-5 !py-2.5 text-sm"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Campaign
        </button>
      </div>

      <div className="space-y-6">
        <div className="surface-card space-y-5">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0 space-y-2">
              <span className="block text-[10px] font-bold uppercase tracking-widest text-slate-400">Shortlisted Candidate</span>
              <h1 className="break-words text-2xl font-black leading-tight text-slate-900">{candidate.full_name}</h1>
              <p className="text-sm font-medium text-slate-655">{candidate.current_title || "No Title Specified"}</p>
              <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
                <span>Location: <span className="font-semibold text-slate-700">{candidate.location || "N/A"}</span></span>
                <span>Experience: <span className="font-semibold text-slate-700">{experienceYrs} Years</span></span>
                <span>Source: <span className="font-semibold capitalize text-slate-700">{candidate.source_type}</span></span>
              </div>
            </div>

            <div className="grid min-w-[15rem] gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-4 py-3">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Match Score</span>
                <span className="mt-1 block text-3xl font-black leading-tight text-slate-950">
                  {score ? `${Math.round(score.final_score)}%` : "N/A"}
                </span>
              </div>
              <div className="rounded-[1rem] border border-slate-200 bg-white px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  <span className={`status-badge text-[9px] uppercase tracking-[0.14em] ${match.badge}`}>
                    {match.label}
                  </span>
                  {getDecisionPill(activeDecision)}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(18rem,0.9fr)_minmax(0,1.1fr)]">
          <div className="surface-card space-y-4">
            <div>
              <h2 className="border-b border-slate-100 pb-2 text-sm font-bold text-slate-900">Decision Panel</h2>
              <p className="mt-1 text-[10px] text-slate-400">Submit your decision and remarks on this candidate.</p>
            </div>

            <div className="space-y-4">
              {(() => {
                const isCampaignClosed = campaign?.status_code === "CLOSED";

                if (activeDecision === "INTERVIEW_SENT") {
                  return (
                    <div className="space-y-3.5">
                      <div className="space-y-2 rounded-xl border border-emerald-200/60 bg-emerald-50 p-4">
                        <span className="block text-[10px] font-bold uppercase tracking-widest text-emerald-800">Status</span>
                        <span className="block text-sm font-bold text-slate-900">
                          {evaluationBoard?.candidate?.email ? "Interview Invitation Sent" : "Candidate Approved"}
                        </span>
                        {!evaluationBoard?.candidate?.email && (
                          <p className="text-xs text-emerald-850 mt-1 font-medium">
                            No email address was available, so no interview invitation was sent.
                          </p>
                        )}
                        <div className="space-y-1.5 border-t border-emerald-100 pt-2 text-xs text-slate-655">
                          <p><strong>Link:</strong> <a href={pipeline?.interview_link || ""} target="_blank" rel="noreferrer" className="break-all text-indigo-650 hover:underline">{pipeline?.interview_link}</a></p>
                          <p><strong>Date & Time:</strong> {pipeline?.interview_datetime ? new Date(pipeline.interview_datetime).toLocaleDateString() : "N/A"} at {pipeline?.interview_datetime ? new Date(pipeline.interview_datetime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "N/A"} ({pipeline?.interview_timezone})</p>
                          {pipeline?.interview_message && <p><strong>Message:</strong> "{pipeline.interview_message}"</p>}
                        </div>
                      </div>
                      <button
                        type="button"
                        disabled={isCampaignClosed}
                        onClick={() => setIsModalOpen(true)}
                        title={isCampaignClosed ? "This campaign has been completed and is read-only." : undefined}
                        className={`w-full workspace-ghost-button !py-2.5 text-xs font-semibold hover:border-indigo-250 hover:text-indigo-650 ${
                          isCampaignClosed ? "opacity-40 cursor-not-allowed" : ""
                        }`}
                      >
                        Reschedule Interview
                      </button>
                    </div>
                  );
                }

                if (activeDecision === "REJECTED") {
                  return (
                    <div className="space-y-3.5">
                      <div className="space-y-2 rounded-xl border border-rose-200/60 bg-rose-50 p-4">
                        <span className="block text-[10px] font-bold uppercase tracking-widest text-rose-800">Status</span>
                        <span className="block text-sm font-bold text-slate-900">Rejected</span>
                        {pipeline?.hiring_manager_notes && (
                          <p className="border-t border-rose-100 pt-2 text-xs text-slate-655">
                            <strong>Remarks:</strong> "{pipeline.hiring_manager_notes}"
                          </p>
                        )}
                      </div>
                      <button
                        type="button"
                        disabled={isCampaignClosed}
                        onClick={() => setIsModalOpen(true)}
                        title={isCampaignClosed ? "This campaign has been completed and is read-only." : undefined}
                        className={`w-full workspace-primary-button !py-2.5 text-xs font-semibold shadow-sm ${
                          isCampaignClosed ? "opacity-40 cursor-not-allowed" : ""
                        }`}
                      >
                        Schedule Interview
                      </button>
                    </div>
                  );
                }

                return (
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">Review Remarks (Optional)</label>
                      <textarea
                        value={notes}
                        disabled={isCampaignClosed}
                        onChange={(e) => setNotes(e.target.value)}
                        className={`resume-textarea !min-h-[7rem] text-xs focus:outline-none ${isCampaignClosed ? "opacity-60 cursor-not-allowed bg-slate-50" : ""}`}
                        placeholder="Add remarks or justification prior to scheduling or rejecting..."
                        rows={4}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-2">
                      <button
                        type="button"
                        disabled={isSaving || isCampaignClosed}
                        onClick={handleSaveReview}
                        title={isCampaignClosed ? "This campaign has been completed and is read-only." : undefined}
                        className={`workspace-ghost-button !py-2.5 text-xs font-semibold border-rose-200 text-rose-700 hover:bg-rose-50 ${
                          isCampaignClosed ? "opacity-40 cursor-not-allowed" : ""
                        }`}
                      >
                        {isSaving ? "Saving..." : "Reject"}
                      </button>
                      <button
                        type="button"
                        disabled={isSaving || isCampaignClosed}
                        onClick={() => setIsModalOpen(true)}
                        title={isCampaignClosed ? "This campaign has been completed and is read-only." : undefined}
                        className={`workspace-primary-button !py-2.5 text-xs font-semibold shadow-sm ${
                          isCampaignClosed ? "opacity-40 cursor-not-allowed" : ""
                        }`}
                      >
                        Schedule Interview
                      </button>
                    </div>
                    {isSavedSuccessfully && (
                      <p className="text-center text-[10px] font-bold text-emerald-600">✓ Rejection saved successfully</p>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>

          <CandidateScoreBreakdown score={score} />
        </div>

        {pipeline?.recruiter_notes && (
          <div className="surface-card border border-indigo-100 bg-indigo-50/30">
            <h3 className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-indigo-700">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              Why this candidate was shortlisted
            </h3>
            <p className="text-sm italic leading-relaxed text-slate-700">
              "{pipeline.recruiter_notes}"
            </p>
          </div>
        )}

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
      </div>

      {isModalOpen && createPortal(
        <div className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="animate-scale-up max-w-lg overflow-hidden rounded-[1.4rem] border border-slate-200 bg-white shadow-[0_25px_50px_-12px_rgba(0,0,0,0.25)] w-full">
            <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 p-6">
              <div>
                <h3 className="text-base font-bold text-slate-900">Schedule Interview</h3>
                <p className="text-xs text-slate-500 mt-0.5">Send an interview invitation email directly to the candidate.</p>
              </div>
              <button type="button" onClick={() => setIsModalOpen(false)} className="text-slate-400 transition hover:text-slate-600 focus:outline-none">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4">
              {validationError && (
                <div className="animate-shake rounded-xl border border-rose-200/50 bg-rose-50/20 p-3.5 text-xs font-semibold leading-normal text-rose-700">
                  {validationError}
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
                className="workspace-ghost-button !px-5 !py-2.5 text-xs font-bold hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSaving}
                onClick={validateAndSendInvitation}
                className="workspace-primary-button !px-5 !py-2.5 text-xs font-black shadow-md"
              >
                {isSaving ? "Sending Invitation..." : "Send Invitation"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
