import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecruiterJobDescriptionWizard } from "../hooks/useRecruiterJobDescriptionWizard";

export function JobDescriptionCreatePage() {
  const navigate = useNavigate();
  const {
    step,
    setStep,
    rawJobDescription,
    setRawJobDescription,
    hiringManagerId,
    setHiringManagerId,
    extractedJob,
    employmentTypes,
    hiringManagers,
    isLoading,
    error,
    setError,
    handleExtract,
    saveJobDescription,
    updateStructuredField,
    addSkill,
    removeSkill,
  } = useRecruiterJobDescriptionWizard();

  // Local skills inputs
  const [newMandatorySkill, setNewMandatorySkill] = useState("");
  const [newPreferredSkill, setNewPreferredSkill] = useState("");

  const stepsList = [
    { num: 1, label: "Paste JD" },
    { num: 2, label: "Review Raw" },
    { num: 3, label: "Review Structured" },
    { num: 4, label: "Finish" },
  ];

  const handleSaveDraft = async () => {
    const jobDescriptionId = await saveJobDescription();
    if (jobDescriptionId) {
      navigate(`/recruiter/job-descriptions/${jobDescriptionId}`);
    }
  };

  const handleContinueScoring = async () => {
    const jobDescriptionId = await saveJobDescription();
    if (jobDescriptionId) {
      navigate(`/recruiter/job-descriptions/${jobDescriptionId}/score-config`);
    }
  };

  const getHiringManagerName = (managerId: string | null) => {
    if (!managerId) return "Unassigned";
    const found = hiringManagers.find((m) => m.id === managerId);
    return found ? found.name : "Unassigned";
  };

  const getEmploymentTypeName = (typeId: string) => {
    const found = employmentTypes.find((t) => t.id === typeId);
    return found ? found.name : "Full Time";
  };

  return (
    <div className="workspace-shell">
      {/* Page Header */}
      <div className="workspace-header !mb-6">
        <div>
          <div className="auth-kicker">Wizard</div>
          <h1 className="workspace-title">Job Description Creation Wizard</h1>
          <p className="workspace-subtitle">
            AI-assisted job description extraction and configuration setup.
          </p>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="surface-card !p-5 mb-8 bg-white border border-slate-200/80 rounded-2xl shadow-sm">
        <div className="flex items-center justify-between max-w-2xl mx-auto">
          {stepsList.map((s, idx) => (
            <div key={s.num} className="flex items-center flex-1 last:flex-initial">
              <div className="flex items-center gap-2.5">
                <div
                  className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs border-2 transition ${
                    step === s.num
                      ? "bg-slate-900 border-slate-900 text-white shadow-md shadow-slate-900/15"
                      : step > s.num
                      ? "bg-emerald-500 border-emerald-500 text-white"
                      : "bg-white border-slate-200 text-slate-400"
                  }`}
                >
                  {step > s.num ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    s.num
                  )}
                </div>
                <span
                  className={`text-xs font-semibold uppercase tracking-wider hidden sm:inline ${
                    step === s.num ? "text-slate-900 font-bold" : "text-slate-400"
                  }`}
                >
                  {s.label}
                </span>
              </div>
              {idx < stepsList.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-4 transition ${
                    step > s.num ? "bg-emerald-500" : "bg-slate-200"
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="workspace-alert mb-6 max-w-4xl mx-auto">
          <div className="flex items-start gap-2.5">
            <svg className="w-5 h-5 text-amber-800 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="text-sm font-medium">{error}</div>
          </div>
        </div>
      )}

      {/* Wizard Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="surface-card max-w-sm p-8 text-center shadow-2xl relative bg-white border border-slate-200 rounded-3xl">
            <div className="h-10 w-10 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4" />
            <h3 className="text-base font-semibold text-slate-900">Extracting Job Profile</h3>
            <p className="mt-2 text-xs text-slate-500 leading-relaxed">
              Our AI is extracting structured responsibilities, experiences, and candidate mandatory requirements from your text...
            </p>
          </div>
        </div>
      )}

      {/* STEP CONTAINER */}
      <div className="max-w-4xl mx-auto">
        
        {/* Step 1 — Paste Job Description */}
        {step === 1 && (
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-5">
            <div>
              <h2 className="text-base font-bold text-slate-900 mb-1">Paste Raw Job Description</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Paste the original JD text below. AI will automatically build the structured profile.
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="raw-jd" className="auth-label text-xs">Job Description Text</label>
              <textarea
                id="raw-jd"
                value={rawJobDescription}
                onChange={(e) => setRawJobDescription(e.target.value)}
                placeholder="Paste the full job description text here..."
                rows={12}
                className="resume-textarea !min-h-[16rem] focus:outline-none"
              />
            </div>

            <div className="space-y-2 max-w-xs">
              <label htmlFor="hiring-manager" className="auth-label text-xs">Assign Hiring Manager</label>
              <select
                id="hiring-manager"
                value={hiringManagerId}
                onChange={(e) => setHiringManagerId(e.target.value)}
                className="auth-input !py-2.5 !rounded-xl text-sm cursor-pointer focus:outline-none"
              >
                {hiringManagers.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.email})
                  </option>
                ))}
              </select>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => navigate("/recruiter/job-descriptions")}
                className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={rawJobDescription.trim().length < 20}
                onClick={() => setStep(2)}
                className="workspace-primary-button !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Review Raw Job Description */}
        {step === 2 && (
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-5">
            <div>
              <h2 className="text-base font-bold text-slate-900 mb-1">Verify Raw Formatting</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Review pasted content. Correct any formatting mistakes before invoking the AI extraction agent.
              </p>
            </div>

            <div className="space-y-2">
              <textarea
                value={rawJobDescription}
                onChange={(e) => setRawJobDescription(e.target.value)}
                rows={12}
                className="resume-textarea !min-h-[16rem] focus:outline-none"
              />
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleExtract}
                className="workspace-primary-button !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none"
              >
                Extract Structured Job Description
              </button>
            </div>
          </div>
        )}

        {/* Step 3 — Review Structured Job Description */}
        {step === 3 && extractedJob && (
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900 mb-1">Verify AI Extraction</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                We've extracted the following structure. Double-check and correct any fields before final verification.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Title */}
              <div className="space-y-1">
                <label className="auth-label text-xs">Position Title</label>
                <input
                  type="text"
                  value={extractedJob.title}
                  onChange={(e) => updateStructuredField("title", e.target.value)}
                  className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                />
              </div>

              {/* Department */}
              <div className="space-y-1">
                <label className="auth-label text-xs">Department</label>
                <input
                  type="text"
                  value={extractedJob.department || ""}
                  onChange={(e) => updateStructuredField("department", e.target.value)}
                  className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                />
              </div>

              {/* Employment Type */}
              <div className="space-y-1">
                <label className="auth-label text-xs">Employment Type</label>
                <select
                  value={extractedJob.employment_type_id}
                  onChange={(e) => updateStructuredField("employment_type_id", e.target.value)}
                  className="auth-input !py-2.5 !rounded-xl text-sm cursor-pointer focus:outline-none"
                >
                  {employmentTypes.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Hiring Manager */}
              <div className="space-y-1">
                <label className="auth-label text-xs">Hiring Manager</label>
                <select
                  value={extractedJob.hiring_manager_id || ""}
                  onChange={(e) => updateStructuredField("hiring_manager_id", e.target.value || null)}
                  className="auth-input !py-2.5 !rounded-xl text-sm cursor-pointer focus:outline-none"
                >
                  <option value="">Unassigned</option>
                  {hiringManagers.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Experience Min */}
              <div className="space-y-1">
                <label className="auth-label text-xs">Minimum Experience (Years)</label>
                <input
                  type="number"
                  min={0}
                  value={extractedJob.min_experience}
                  onChange={(e) => updateStructuredField("min_experience", Number(e.target.value))}
                  className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                />
              </div>

              {/* Experience Max */}
              <div className="space-y-1">
                <label className="auth-label text-xs">Maximum Experience (Years)</label>
                <input
                  type="number"
                  min={0}
                  value={extractedJob.max_experience}
                  onChange={(e) => updateStructuredField("max_experience", Number(e.target.value))}
                  className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                />
              </div>

              {/* Education Requirement */}
              <div className="space-y-1 md:col-span-2">
                <label className="auth-label text-xs">Education Requirement</label>
                <input
                  type="text"
                  value={extractedJob.education_requirement}
                  onChange={(e) => updateStructuredField("education_requirement", e.target.value)}
                  className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                />
              </div>

              {/* Job Purpose */}
              <div className="space-y-1 md:col-span-2">
                <label className="auth-label text-xs">Job Purpose</label>
                <textarea
                  value={extractedJob.job_purpose}
                  onChange={(e) => updateStructuredField("job_purpose", e.target.value)}
                  rows={3}
                  className="form-textarea focus:outline-none"
                />
              </div>

              {/* Responsibilities */}
              <div className="space-y-1 md:col-span-2">
                <label className="auth-label text-xs">Responsibilities</label>
                <textarea
                  value={extractedJob.responsibilities}
                  onChange={(e) => updateStructuredField("responsibilities", e.target.value)}
                  rows={4}
                  className="form-textarea focus:outline-none"
                />
              </div>

              {/* Preferred Qualifications */}
              <div className="space-y-1 md:col-span-2">
                <label className="auth-label text-xs">Preferred Qualifications</label>
                <textarea
                  value={extractedJob.preferred_qualifications || ""}
                  onChange={(e) => updateStructuredField("preferred_qualifications", e.target.value)}
                  rows={3}
                  className="form-textarea focus:outline-none"
                />
              </div>

              {/* Skills Visual Editor */}
              <div className="md:col-span-2 border-t border-slate-100 pt-4 space-y-4">
                <h3 className="text-sm font-bold text-slate-800">Verify Candidate Skills Requirements</h3>

                {/* Mandatory Skills */}
                <div className="space-y-2.5 p-4 border border-slate-150 rounded-xl bg-slate-50/30">
                  <span className="text-xs font-semibold text-slate-900 block">Mandatory Skills</span>
                  <div className="flex flex-wrap gap-2">
                    {extractedJob.skills
                      .filter((s) => s.is_mandatory)
                      .map((skill, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-950 text-white"
                        >
                          <span>{skill.skill_name}</span>
                          <button
                            type="button"
                            onClick={() => removeSkill(skill.skill_name)}
                            className="text-slate-400 hover:text-white shrink-0 cursor-pointer focus:outline-none"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </span>
                      ))}
                    {extractedJob.skills.filter((s) => s.is_mandatory).length === 0 && (
                      <span className="text-xs text-slate-400 italic">No mandatory skills added.</span>
                    )}
                  </div>
                  <div className="flex gap-2 max-w-sm pt-2">
                    <input
                      type="text"
                      placeholder="Add mandatory skill..."
                      value={newMandatorySkill}
                      onChange={(e) => setNewMandatorySkill(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addSkill(newMandatorySkill, true);
                          setNewMandatorySkill("");
                        }
                      }}
                      className="auth-input !py-1.5 !px-3 !rounded-lg text-xs focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        addSkill(newMandatorySkill, true);
                        setNewMandatorySkill("");
                      }}
                      className="workspace-ghost-button !py-1.5 !px-3 !rounded-lg text-xs shrink-0 focus:outline-none"
                    >
                      + Add
                    </button>
                  </div>
                </div>

                {/* Preferred Skills */}
                <div className="space-y-2.5 p-4 border border-slate-150 rounded-xl bg-slate-50/30">
                  <span className="text-xs font-semibold text-slate-500 block">Preferred/Optional Skills</span>
                  <div className="flex flex-wrap gap-2">
                    {extractedJob.skills
                      .filter((s) => !s.is_mandatory)
                      .map((skill, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-white text-slate-700 border border-slate-200"
                        >
                          <span>{skill.skill_name}</span>
                          <button
                            type="button"
                            onClick={() => removeSkill(skill.skill_name)}
                            className="text-slate-400 hover:text-slate-650 shrink-0 cursor-pointer focus:outline-none"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </span>
                      ))}
                    {extractedJob.skills.filter((s) => !s.is_mandatory).length === 0 && (
                      <span className="text-xs text-slate-400 italic">No preferred skills added.</span>
                    )}
                  </div>
                  <div className="flex gap-2 max-w-sm pt-2">
                    <input
                      type="text"
                      placeholder="Add preferred skill..."
                      value={newPreferredSkill}
                      onChange={(e) => setNewPreferredSkill(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addSkill(newPreferredSkill, false);
                          setNewPreferredSkill("");
                        }
                      }}
                      className="auth-input !py-1.5 !px-3 !rounded-lg text-xs focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        addSkill(newPreferredSkill, false);
                        setNewPreferredSkill("");
                      }}
                      className="workspace-ghost-button !py-1.5 !px-3 !rounded-lg text-xs shrink-0 focus:outline-none"
                    >
                      + Add
                    </button>
                  </div>
                </div>

              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="workspace-ghost-button !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none"
              >
                Back
              </button>
              <button
                type="button"
                disabled={!extractedJob.title.trim() || extractedJob.skills.length === 0}
                onClick={() => {
                  setError(null);
                  setStep(4);
                }}
                className="workspace-primary-button !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 4 — Final Confirmation */}
        {step === 4 && extractedJob && (
          <div className="surface-card bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900 mb-1">Verify Campaign Setup</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ensure everything is correct. Choose to save as a draft to continue later, or proceed directly to scoring configuration.
              </p>
            </div>

            {/* Visual Overview */}
            <div className="p-5 border border-slate-200 rounded-xl bg-slate-50/30 text-sm space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Position Title</span>
                  <span className="text-slate-800 font-bold text-base mt-0.5 block">{extractedJob.title}</span>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Department</span>
                  <span className="text-slate-700 font-medium mt-0.5 block">{extractedJob.department || "-"}</span>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Employment Type</span>
                  <span className="text-slate-700 font-medium mt-0.5 block">{getEmploymentTypeName(extractedJob.employment_type_id)}</span>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Assigned Hiring Manager</span>
                  <span className="text-slate-700 font-medium mt-0.5 block">{getHiringManagerName(extractedJob.hiring_manager_id)}</span>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Experience Requirement</span>
                  <span className="text-slate-700 font-medium mt-0.5 block">{extractedJob.min_experience} - {extractedJob.max_experience} Years</span>
                </div>
                <div>
                  <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">Skills Requirements Count</span>
                  <span className="text-slate-700 font-medium mt-0.5 block">
                    {extractedJob.skills.filter((s) => s.is_mandatory).length} Mandatory,{" "}
                    {extractedJob.skills.filter((s) => !s.is_mandatory).length} Preferred
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-slate-100 justify-between items-center">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="workspace-ghost-button w-full sm:w-auto !py-2.5 !px-5 !rounded-xl text-sm focus:outline-none"
              >
                Back
              </button>
              
              <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={handleSaveDraft}
                  className="workspace-ghost-button w-full sm:w-auto !py-2.5 !px-5 !rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 focus:outline-none"
                >
                  Save as Draft
                </button>
                <button
                  type="button"
                  onClick={handleContinueScoring}
                  className="workspace-primary-button w-full sm:w-auto !py-2.5 !px-5 !rounded-xl text-sm font-semibold focus:outline-none shadow-md shadow-slate-900/10"
                >
                  Continue to Scoring
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
