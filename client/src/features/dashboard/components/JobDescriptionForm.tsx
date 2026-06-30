import type {
  EmploymentType,
  HiringManager,
} from "../services/dashboard.types";
import type { JobDescriptionFormValues } from "../hooks/useRecruiterDashboard";

interface JobDescriptionFormProps {
  employmentTypes: EmploymentType[];
  hiringManagers: HiringManager[];
  formValues: JobDescriptionFormValues;
  isSubmitting: boolean;
  onAddSkillField: (
    field:
      | "mandatory_skills"
      | "optional_skills",
  ) => void;
  onChange: (
    field: keyof JobDescriptionFormValues,
    value: string,
  ) => void;
  onRemoveSkillField: (
    field:
      | "mandatory_skills"
      | "optional_skills",
    index: number,
  ) => void;
  onSkillArrayChange: (
    field:
      | "mandatory_skills"
      | "optional_skills",
    index: number,
    value: string,
  ) => void;
  onSubmit: () => void;
  onSaveAsDraft: () => void;
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
  onChange: (
    index: number,
    value: string,
  ) => void;
  onRemove: (index: number) => void;
}) {
  return (
    <div className="detail-block">
      <div className="section-header">
        <div>
          <h3 className="section-title">
            {label}
          </h3>
        </div>

        <button
          type="button"
          onClick={onAdd}
          className="workspace-ghost-button"
        >
          Add
        </button>
      </div>

      <div className="skill-editor-list">
        {skills.map((skill, index) => (
          <div
            key={`${label}-${index}`}
            className="skill-editor-row"
          >
            <input
              type="text"
              value={skill}
              onChange={(event) =>
                onChange(
                  index,
                  event.target.value,
                )
              }
              className="auth-input"
              placeholder={
                label ===
                "Mandatory Skills"
                  ? "React"
                  : "GraphQL"
              }
            />

            <button
              type="button"
              onClick={() =>
                onRemove(index)
              }
              className="workspace-ghost-button"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function JobDescriptionForm({
  employmentTypes,
  hiringManagers,
  formValues,
  isSubmitting,
  onAddSkillField,
  onChange,
  onRemoveSkillField,
  onSkillArrayChange,
  onSubmit,
  onSaveAsDraft,
}: JobDescriptionFormProps) {
  const isSaveDraftDisabled = isSubmitting || !formValues.title.trim();

  const isFormValid =
    formValues.title.trim() !== "" &&
    formValues.summary.trim() !== "" &&
    formValues.min_experience.trim() !== "" &&
    formValues.location.trim() !== "" &&
    formValues.education_requirement.trim() !== "" &&
    formValues.mandatory_skills.some((skill) => skill.trim() !== "");

  const isPreviewDisabled = isSubmitting || !isFormValid;

  return (
    <div className="surface-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">
            Step 1. Create Job Description
          </h2>

          <p className="section-copy">
            Capture the role profile first. The candidate count preview will appear before scoring begins.
          </p>
        </div>
      </div>

      <div className="dashboard-form">
        <div className="detail-grid">
          <div className="auth-field">
            <label className="auth-label">
              Job Title
            </label>

            <input
              type="text"
              value={formValues.title}
              onChange={(event) =>
                onChange(
                  "title",
                  event.target.value,
                )
              }
              className="auth-input"
              placeholder="SDE 1"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Department
            </label>

            <input
              type="text"
              value={formValues.department}
              onChange={(event) =>
                onChange(
                  "department",
                  event.target.value,
                )
              }
              className="auth-input"
              placeholder="Engineering"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Min Experience
            </label>

            <input
              type="number"
              min="0"
              value={
                formValues.min_experience
              }
              onChange={(event) =>
                onChange(
                  "min_experience",
                  event.target.value,
                )
              }
              className="auth-input"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Max Experience
            </label>

            <input
              type="number"
              min="0"
              value={
                formValues.max_experience
              }
              onChange={(event) =>
                onChange(
                  "max_experience",
                  event.target.value,
                )
              }
              className="auth-input"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Location
            </label>

            <input
              type="text"
              value={formValues.location}
              onChange={(event) =>
                onChange(
                  "location",
                  event.target.value,
                )
              }
              className="auth-input"
              placeholder="Bengaluru / Hybrid"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Employment Type
            </label>

            <select
              value={
                formValues.employment_type_id
              }
              onChange={(event) =>
                onChange(
                  "employment_type_id",
                  event.target.value,
                )
              }
              className="auth-input"
            >
              {employmentTypes.map((type) => (
                <option
                  key={type.id}
                  value={type.id}
                >
                  {type.name}
                </option>
              ))}
            </select>
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Assign Hiring Manager
            </label>

            <select
              value={
                formValues.hiring_manager_id
              }
              onChange={(event) =>
                onChange(
                  "hiring_manager_id",
                  event.target.value,
                )
              }
              className="auth-input"
              required
            >
              {hiringManagers.map((manager) => (
                <option
                  key={manager.id}
                  value={manager.id}
                >
                  {manager.name} ({manager.email})
                </option>
              ))}
            </select>
          </div>

          <div className="auth-field detail-block-full">
            <label className="auth-label">
              Summary
            </label>

            <textarea
              value={formValues.summary}
              onChange={(event) =>
                onChange(
                  "summary",
                  event.target.value,
                )
              }
              className="form-textarea"
              rows={4}
              placeholder="Describe the mission, product scope, and expected candidate profile."
            />
          </div>

          <div className="auth-field detail-block-full">
            <label className="auth-label">
              Responsibilities
            </label>

            <textarea
              value={
                formValues.responsibilities
              }
              onChange={(event) =>
                onChange(
                  "responsibilities",
                  event.target.value,
                )
              }
              className="form-textarea"
              rows={4}
              placeholder="List the responsibilities or leave aligned to the summary."
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Education Requirement
            </label>

            <input
              type="text"
              value={
                formValues.education_requirement
              }
              onChange={(event) =>
                onChange(
                  "education_requirement",
                  event.target.value,
                )
              }
              className="auth-input"
              placeholder="B.Tech / B.E. in Computer Science"
            />
          </div>

          <div className="auth-field">
            <label className="auth-label">
              Preferred Qualifications
            </label>

            <input
              type="text"
              value={
                formValues.preferred_qualifications
              }
              onChange={(event) =>
                onChange(
                  "preferred_qualifications",
                  event.target.value,
                )
              }
              className="auth-input"
              placeholder="Fast-moving product experience"
            />
          </div>
        </div>

        <div className="detail-grid">
          <SkillTagEditor
            label="Mandatory Skills"
            skills={
              formValues.mandatory_skills
            }
            onAdd={() =>
              onAddSkillField(
                "mandatory_skills",
              )
            }
            onChange={(index, value) =>
              onSkillArrayChange(
                "mandatory_skills",
                index,
                value,
              )
            }
            onRemove={(index) =>
              onRemoveSkillField(
                "mandatory_skills",
                index,
              )
            }
          />

          <SkillTagEditor
            label="Optional Skills"
            skills={
              formValues.optional_skills
            }
            onAdd={() =>
              onAddSkillField(
                "optional_skills",
              )
            }
            onChange={(index, value) =>
              onSkillArrayChange(
                "optional_skills",
                index,
                value,
              )
            }
            onRemove={(index) =>
              onRemoveSkillField(
                "optional_skills",
                index,
              )
            }
          />
        </div>

        <div className="button-row">
          <button
            type="button"
            onClick={onSubmit}
            disabled={isPreviewDisabled}
            className="workspace-primary-button disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting
              ? "Saving Preview..."
              : "Preview Candidate Match Count"}
          </button>

          <button
            type="button"
            onClick={onSaveAsDraft}
            disabled={isSaveDraftDisabled}
            className="workspace-ghost-button disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save as Draft
          </button>
        </div>
      </div>
    </div>
  );
}
