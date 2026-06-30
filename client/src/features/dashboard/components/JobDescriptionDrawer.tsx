import { useState, useEffect } from "react";
import type { EmploymentType, HiringManager, JobDescription, JDSkill } from "../services/dashboard.types";
import type { JobDescriptionFormValues } from "../hooks/useRecruiterDashboard";

interface JobDescriptionDrawerProps {
  job: JobDescription | null;
  onClose: () => void;
  isDraft: boolean;
  employmentTypes?: EmploymentType[];
  hiringManagers?: HiringManager[];
  formValues?: JobDescriptionFormValues;
  isSubmitting?: boolean;
  onAddSkillField?: (field: "mandatory_skills" | "optional_skills") => void;
  onChange?: (field: keyof JobDescriptionFormValues, value: string) => void;
  onRemoveSkillField?: (field: "mandatory_skills" | "optional_skills", index: number) => void;
  onSkillArrayChange?: (field: "mandatory_skills" | "optional_skills", index: number, value: string) => void;
  onSubmit?: () => void;
  onSaveJobSkills?: (jobId: string, skills: JDSkill[]) => Promise<void>;
  onTriggerScoringPreview?: (jobId: string) => Promise<void>;
}

function SkillTagEditor({
  label,
  skills,
  onAdd,
  onChange,
  onRemove,
}: {
  label: string;
  skills: string[];
  onAdd: () => void;
  onChange: (index: number, value: string) => void;
  onRemove: (index: number) => void;
}) {
  return (
    <div className="detail-block">
      <div className="section-header">
        <div>
          <h3 className="section-title text-sm font-semibold text-slate-900">
            {label}
          </h3>
        </div>

        <button
          type="button"
          onClick={onAdd}
          className="workspace-ghost-button text-xs py-1"
        >
          Add
        </button>
      </div>

      <div className="skill-editor-list flex flex-col gap-2 mt-2">
        {skills.map((skill, index) => (
          <div
            key={`${label}-${index}`}
            className="skill-editor-row flex items-center gap-2"
          >
            <input
              type="text"
              value={skill}
              onChange={(event) => onChange(index, event.target.value)}
              className="auth-input text-sm py-1.5 flex-1"
              placeholder={label === "Mandatory Skills" ? "React" : "GraphQL"}
            />

            <button
              type="button"
              onClick={() => onRemove(index)}
              className="workspace-ghost-button text-xs py-1.5"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function JobDescriptionDrawer({
  job,
  onClose,
  isDraft,
  employmentTypes,
  hiringManagers,
  formValues,
  isSubmitting,
  onAddSkillField,
  onChange,
  onRemoveSkillField,
  onSkillArrayChange,
  onSubmit,
  onSaveJobSkills,
  onTriggerScoringPreview,
}: JobDescriptionDrawerProps) {
  const [isEditingSkills, setIsEditingSkills] = useState(false);
  const [localSkills, setLocalSkills] = useState<{
    mandatory: string[];
    optional: string[];
  }>({ mandatory: [], optional: [] });
  const [newMandatorySkill, setNewMandatorySkill] = useState("");
  const [newOptionalSkill, setNewOptionalSkill] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (job) {
      setLocalSkills({
        mandatory: job.skills.filter((s) => s.is_mandatory).map((s) => s.skill_name),
        optional: job.skills.filter((s) => !s.is_mandatory).map((s) => s.skill_name),
      });
      setIsEditingSkills(false);
      setErrorMessage("");
    }
  }, [job]);

  const handleUpdateSkills = async (updatedMandatory: string[], updatedOptional: string[]) => {
    if (!job || !onSaveJobSkills) return;
    setIsSaving(true);
    setErrorMessage("");
    try {
      const skills: JDSkill[] = [
        ...updatedMandatory.map((s) => ({ skill_name: s, is_mandatory: true })),
        ...updatedOptional.map((s) => ({ skill_name: s, is_mandatory: false })),
      ];
      await onSaveJobSkills(job.id, skills);
      setLocalSkills({
        mandatory: updatedMandatory,
        optional: updatedOptional,
      });
    } catch {
      setErrorMessage("Failed to save skill changes.");
      // Rollback to current state
      setLocalSkills({
        mandatory: job.skills.filter((s) => s.is_mandatory).map((s) => s.skill_name),
        optional: job.skills.filter((s) => !s.is_mandatory).map((s) => s.skill_name),
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleStartEdit = () => {
    if (job) {
      setLocalSkills({
        mandatory: job.skills.filter((s) => s.is_mandatory).map((s) => s.skill_name),
        optional: job.skills.filter((s) => !s.is_mandatory).map((s) => s.skill_name),
      });
      setIsEditingSkills(true);
      setErrorMessage("");
    }
  };

  if (!job) {
    return null;
  }

  if (isDraft) {
    if (
      !formValues ||
      !employmentTypes ||
      !hiringManagers ||
      !onChange ||
      !onAddSkillField ||
      !onRemoveSkillField ||
      !onSkillArrayChange ||
      !onSubmit
    ) {
      return null;
    }

    return (
      <aside className="candidate-drawer animate-fade-in">
        <div className="section-header">
          <div>
            <h2 className="section-title">Edit Draft Campaign</h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="workspace-ghost-button"
          >
            Close
          </button>
        </div>

        <div className="stack-list overflow-y-auto flex-1 mt-4 pr-1">
          <div className="dashboard-form">
            <div className="detail-grid grid grid-cols-1 gap-4">
              {/* Job Title */}
              <div className="auth-field">
                <label className="auth-label">Job Title</label>
                <input
                  type="text"
                  value={formValues.title}
                  onChange={(e) => onChange("title", e.target.value)}
                  className="auth-input"
                  placeholder="SDE 1"
                />
              </div>

              {/* Department */}
              <div className="auth-field">
                <label className="auth-label">Department</label>
                <input
                  type="text"
                  value={formValues.department || ""}
                  onChange={(e) => onChange("department", e.target.value)}
                  className="auth-input"
                  placeholder="Engineering"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Min Exp */}
                <div className="auth-field">
                  <label className="auth-label">Min Experience (Yrs)</label>
                  <input
                    type="number"
                    min="0"
                    value={formValues.min_experience}
                    onChange={(e) => onChange("min_experience", e.target.value)}
                    className="auth-input"
                  />
                </div>

                {/* Max Exp */}
                <div className="auth-field">
                  <label className="auth-label">Max Experience (Yrs)</label>
                  <input
                    type="number"
                    min="0"
                    value={formValues.max_experience}
                    onChange={(e) => onChange("max_experience", e.target.value)}
                    className="auth-input"
                  />
                </div>
              </div>

              {/* Location */}
              <div className="auth-field">
                <label className="auth-label">Location</label>
                <input
                  type="text"
                  value={formValues.location}
                  onChange={(e) => onChange("location", e.target.value)}
                  className="auth-input"
                  placeholder="Bengaluru / Hybrid"
                />
              </div>

              {/* Employment Type */}
              <div className="auth-field">
                <label className="auth-label">Employment Type</label>
                <select
                  value={formValues.employment_type_id}
                  onChange={(e) => onChange("employment_type_id", e.target.value)}
                  className="auth-input"
                >
                  {employmentTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Hiring Manager */}
              <div className="auth-field">
                <label className="auth-label">Assign Hiring Manager</label>
                <select
                  value={formValues.hiring_manager_id}
                  onChange={(e) => onChange("hiring_manager_id", e.target.value)}
                  className="auth-input"
                  required
                >
                  {hiringManagers.map((manager) => (
                    <option key={manager.id} value={manager.id}>
                      {manager.name} ({manager.email})
                    </option>
                  ))}
                </select>
              </div>

              {/* Summary */}
              <div className="auth-field">
                <label className="auth-label">Summary</label>
                <textarea
                  value={formValues.summary}
                  onChange={(e) => onChange("summary", e.target.value)}
                  className="form-textarea"
                  rows={3}
                  placeholder="Describe the role mission and product scope."
                />
              </div>

              {/* Responsibilities */}
              <div className="auth-field">
                <label className="auth-label">Responsibilities</label>
                <textarea
                  value={formValues.responsibilities}
                  onChange={(e) => onChange("responsibilities", e.target.value)}
                  className="form-textarea"
                  rows={3}
                  placeholder="List the key responsibilities."
                />
              </div>

              {/* Education Requirement */}
              <div className="auth-field">
                <label className="auth-label">Education Requirement</label>
                <input
                  type="text"
                  value={formValues.education_requirement}
                  onChange={(e) => onChange("education_requirement", e.target.value)}
                  className="auth-input"
                  placeholder="B.Tech / B.E. in Computer Science"
                />
              </div>

              {/* Preferred Qualifications */}
              <div className="auth-field">
                <label className="auth-label">Preferred Qualifications</label>
                <input
                  type="text"
                  value={formValues.preferred_qualifications}
                  onChange={(e) => onChange("preferred_qualifications", e.target.value)}
                  className="auth-input"
                  placeholder="Fast-moving product experience"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 mt-6">
              <SkillTagEditor
                label="Mandatory Skills"
                skills={formValues.mandatory_skills}
                onAdd={() => onAddSkillField("mandatory_skills")}
                onChange={(idx, val) => onSkillArrayChange("mandatory_skills", idx, val)}
                onRemove={(idx) => onRemoveSkillField("mandatory_skills", idx)}
              />

              <SkillTagEditor
                label="Optional Skills"
                skills={formValues.optional_skills}
                onAdd={() => onAddSkillField("optional_skills")}
                onChange={(idx, val) => onSkillArrayChange("optional_skills", idx, val)}
                onRemove={(idx) => onRemoveSkillField("optional_skills", idx)}
              />
            </div>

            <div className="button-row mt-8 flex justify-end">
              <button
                type="button"
                onClick={onSubmit}
                disabled={isSubmitting}
                className="workspace-primary-button w-full"
              >
                {isSubmitting ? "Saving Changes..." : "Proceed to Scoring"}
              </button>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  const mandatorySkills = job.skills.filter((s) => s.is_mandatory);
  const optionalSkills = job.skills.filter((s) => !s.is_mandatory);

  return (
    <aside className="candidate-drawer">
      <div className="section-header">
        <div>
          <h2 className="section-title">Job Description Details</h2>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="workspace-ghost-button"
        >
          Close
        </button>
      </div>

      <div className="stack-list">
        <section className="detail-block">
          <div className="section-header mb-2">
            <div>
              <h3 className="section-title text-xl font-bold text-slate-900">
                {job.title}
              </h3>
              {job.department && (
                <p className="section-copy text-xs text-slate-500 font-medium">
                  {job.department} Department
                </p>
              )}
            </div>
          </div>

          <div className="detail-grid mt-4">
            <div className="detail-block-full">
              <div className="detail-label">Summary / Job Purpose</div>
              <p className="detail-copy text-slate-700 whitespace-pre-wrap">
                {job.job_purpose}
              </p>
            </div>

            {job.responsibilities && (
              <div className="detail-block-full mt-4">
                <div className="detail-label">Responsibilities</div>
                <p className="detail-copy text-slate-700 whitespace-pre-wrap">
                  {job.responsibilities}
                </p>
              </div>
            )}
          </div>
        </section>

        <section className="detail-block border-t border-slate-100 pt-4">
          <div className="detail-grid grid grid-cols-2 gap-4">
            <div>
              <div className="detail-label">Location</div>
              <p className="detail-copy font-medium text-slate-800">
                {job.location}
              </p>
            </div>

            <div>
              <div className="detail-label">Minimum Experience</div>
              <p className="detail-copy font-medium text-slate-800">
                {job.min_experience} {job.min_experience === 1 ? "year" : "years"}
              </p>
            </div>

            <div className="col-span-2">
              <div className="detail-label">Required Education</div>
              <p className="detail-copy font-medium text-slate-800">
                {job.education_requirement}
              </p>
            </div>
          </div>
        </section>

        <section className="detail-block border-t border-slate-100 pt-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="detail-label font-semibold text-slate-900">Mandatory Skills</span>
              {isSaving && (
                <span className="text-[10px] text-indigo-600 animate-pulse font-medium">
                  Saving changes...
                </span>
              )}
            </div>
            {!isEditingSkills && (
              <button
                type="button"
                onClick={handleStartEdit}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
              >
                [Edit / Modify Details]
              </button>
            )}
          </div>

          {errorMessage && (
            <p className="text-xs text-rose-600 mb-2 font-medium">{errorMessage}</p>
          )}

          {isEditingSkills ? (
            <div className={`chip-row flex flex-wrap gap-2 mt-2 items-center ${isSaving ? "opacity-60 pointer-events-none" : ""}`}>
              {localSkills.mandatory.map((skill, index) => (
                <span
                  key={`mandatory-${skill}-${index}`}
                  className="skill-chip skill-chip-primary flex items-center gap-1.5 py-1 px-2.5 transition-opacity"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => {
                      const next = localSkills.mandatory.filter((_, idx) => idx !== index);
                      void handleUpdateSkills(next, localSkills.optional);
                    }}
                    disabled={isSaving}
                    className="text-white hover:text-rose-200 focus:outline-none ml-1 text-sm font-bold leading-none cursor-pointer inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-slate-800 transition"
                    title="Remove skill"
                  >
                    &times;
                  </button>
                </span>
              ))}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const val = newMandatorySkill.trim();
                  if (val && !localSkills.mandatory.includes(val)) {
                    void handleUpdateSkills([...localSkills.mandatory, val], localSkills.optional);
                    setNewMandatorySkill("");
                  }
                }}
                className="inline-flex items-center gap-1"
              >
                <input
                  type="text"
                  value={newMandatorySkill}
                  onChange={(e) => setNewMandatorySkill(e.target.value)}
                  disabled={isSaving}
                  placeholder="Add skill..."
                  className="w-32 px-2 py-0.5 text-xs border border-slate-200 bg-slate-50 focus:bg-white rounded-lg focus:border-slate-400 focus:ring-1 focus:ring-slate-400 outline-none transition"
                />
                <button
                  type="submit"
                  disabled={isSaving || !newMandatorySkill.trim()}
                  className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white hover:border-slate-300 w-5 h-5 text-xs font-bold text-slate-700 hover:text-slate-950 transition cursor-pointer"
                >
                  +
                </button>
              </form>
            </div>
          ) : (
            <>
              {mandatorySkills.length === 0 ? (
                <p className="detail-copy text-slate-500 italic">No mandatory skills listed.</p>
              ) : (
                <div className="chip-row flex flex-wrap gap-2 mt-2">
                  {mandatorySkills.map((skill) => (
                    <span
                      key={skill.id || skill.skill_name}
                      className="skill-chip skill-chip-primary"
                    >
                      {skill.skill_name}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </section>

        <section className="detail-block border-t border-slate-100 pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="detail-label font-semibold text-slate-900">Optional Skills</span>
            {!isEditingSkills && (
              <button
                type="button"
                onClick={handleStartEdit}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
              >
                [Edit / Modify Details]
              </button>
            )}
          </div>

          {isEditingSkills ? (
            <div className={`chip-row flex flex-wrap gap-2 mt-2 items-center ${isSaving ? "opacity-60 pointer-events-none" : ""}`}>
              {localSkills.optional.map((skill, index) => (
                <span
                  key={`optional-${skill}-${index}`}
                  className="skill-chip skill-chip-secondary flex items-center gap-1.5 py-1 px-2.5 transition-opacity"
                >
                  {skill}
                  <button
                    type="button"
                    onClick={() => {
                      const next = localSkills.optional.filter((_, idx) => idx !== index);
                      void handleUpdateSkills(localSkills.mandatory, next);
                    }}
                    disabled={isSaving}
                    className="text-sky-800 hover:text-rose-600 focus:outline-none ml-1 text-sm font-bold leading-none cursor-pointer inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-sky-200 transition"
                    title="Remove skill"
                  >
                    &times;
                  </button>
                </span>
              ))}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const val = newOptionalSkill.trim();
                  if (val && !localSkills.optional.includes(val)) {
                    void handleUpdateSkills(localSkills.mandatory, [...localSkills.optional, val]);
                    setNewOptionalSkill("");
                  }
                }}
                className="inline-flex items-center gap-1"
              >
                <input
                  type="text"
                  value={newOptionalSkill}
                  onChange={(e) => setNewOptionalSkill(e.target.value)}
                  disabled={isSaving}
                  placeholder="Add skill..."
                  className="w-32 px-2 py-0.5 text-xs border border-slate-200 bg-slate-50 focus:bg-white rounded-lg focus:border-slate-400 focus:ring-1 focus:ring-slate-400 outline-none transition"
                />
                <button
                  type="submit"
                  disabled={isSaving || !newOptionalSkill.trim()}
                  className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white hover:border-slate-300 w-5 h-5 text-xs font-bold text-slate-700 hover:text-slate-950 transition cursor-pointer"
                >
                  +
                </button>
              </form>
            </div>
          ) : (
            <>
              {optionalSkills.length === 0 ? (
                <p className="detail-copy text-slate-500 italic">No optional skills listed.</p>
              ) : (
                <div className="chip-row flex flex-wrap gap-2 mt-2">
                  {optionalSkills.map((skill) => (
                    <span
                      key={skill.id || skill.skill_name}
                      className="skill-chip skill-chip-secondary"
                    >
                      {skill.skill_name}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </section>

        <div className="button-row mt-8 flex justify-end gap-3 border-t border-slate-100 pt-4">
          {isEditingSkills && (
            <button
              type="button"
              onClick={() => setIsEditingSkills(false)}
              disabled={isSaving}
              className="workspace-ghost-button flex-1"
            >
              Done Editing
            </button>
          )}
          {onTriggerScoringPreview && (
            <button
              type="button"
              onClick={() => {
                void onTriggerScoringPreview(job.id);
              }}
              disabled={isSaving}
              className="workspace-primary-button flex-1"
            >
              Proceed to Scoring
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
