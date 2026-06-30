import { useState, useEffect, useCallback } from "react";
import { dashboardService } from "../../dashboard/services/dashboard.service";
import type {
  JobDescription,
  EmploymentType,
  HiringManager,
  JDSkill,
  JobDescriptionPayload,
} from "../../dashboard/services/dashboard.types";

export type WizardStep = 1 | 2 | 3 | 4;

export function useRecruiterJobDescriptionWizard() {
  const [step, setStep] = useState<WizardStep>(1);
  const [rawJobDescription, setRawJobDescription] = useState("");
  const [hiringManagerId, setHiringManagerId] = useState("");
  const [extractedJob, setExtractedJob] = useState<JobDescription | null>(null);
  
  // Lookups
  const [employmentTypes, setEmploymentTypes] = useState<EmploymentType[]>([]);
  const [hiringManagers, setHiringManagers] = useState<HiringManager[]>([]);
  
  // State indicators
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load lookup lists on mount
  useEffect(() => {
    const bootstrapLookups = async () => {
      try {
        setError(null);
        const [types, managers] = await Promise.all([
          dashboardService.listEmploymentTypes(),
          dashboardService.listHiringManagers(),
        ]);
        setEmploymentTypes(types);
        setHiringManagers(managers);
        if (managers.length > 0) {
          setHiringManagerId(managers[0].id);
        }
      } catch {
        setError("Unable to load lookup references. Please refresh the page.");
      }
    };
    void bootstrapLookups();
  }, []);

  // Step 2 -> Step 3: Trigger backend AI extraction
  const handleExtract = useCallback(async () => {
    if (!rawJobDescription.trim()) {
      setError("Job description text cannot be empty.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const extracted = await dashboardService.extractJobDescription(rawJobDescription);
      
      // Override or pre-fill with recruiter selected manager from Step 1
      setExtractedJob({
        ...extracted,
        hiring_manager_id: hiringManagerId || null,
        raw_job_description: rawJobDescription,
      });
      setStep(3);
    } catch {
      setError("AI Extraction failed. Please review the raw text and try again.");
    } finally {
      setIsLoading(false);
    }
  }, [rawJobDescription, hiringManagerId]);

  // Step 4: Final save (creates the JD in draft state)
  const saveJobDescription = useCallback(async (): Promise<string | null> => {
    if (!extractedJob) {
      setError("No structured job description data found to save.");
      return null;
    }

    // Basic client-side validation
    if (!extractedJob.title.trim()) {
      setError("Job Title is required.");
      return null;
    }
    if (!extractedJob.job_purpose.trim()) {
      setError("Job Purpose/Mission is required.");
      return null;
    }
    if (extractedJob.max_experience < extractedJob.min_experience) {
      setError("Maximum experience cannot be less than minimum experience.");
      return null;
    }
    if (extractedJob.skills.length === 0) {
      setError("At least one required skill is required.");
      return null;
    }

    try {
      setIsLoading(true);
      setError(null);

      const payload: JobDescriptionPayload = {
        title: extractedJob.title.trim(),
        department: extractedJob.department?.trim() || null,
        job_purpose: extractedJob.job_purpose.trim(),
        responsibilities: extractedJob.responsibilities.trim(),
        min_experience: extractedJob.min_experience,
        max_experience: extractedJob.max_experience,
        location: extractedJob.location.trim() || "Remote",
        employment_type_id: extractedJob.employment_type_id || employmentTypes[0]?.id,
        education_requirement: extractedJob.education_requirement.trim() || "Bachelor's Degree",
        preferred_qualifications: extractedJob.preferred_qualifications?.trim() || null,
        hiring_manager_id: extractedJob.hiring_manager_id || null,
        skills: extractedJob.skills.map((s) => ({
          skill_name: s.skill_name.trim(),
          is_mandatory: s.is_mandatory,
        })),
      };

      const savedJob = await dashboardService.createJobDescription(payload);
      return savedJob.id;
    } catch {
      setError("Failed to save the job description. Please check the values and try again.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [extractedJob, employmentTypes]);

  // Modifying structured job fields in Step 3
  const updateStructuredField = useCallback((field: keyof JobDescription, value: any) => {
    setExtractedJob((current) => {
      if (!current) return null;
      return {
        ...current,
        [field]: value,
      };
    });
  }, []);

  const addSkill = useCallback((skill_name: string, is_mandatory: boolean) => {
    if (!skill_name.trim()) return;
    setExtractedJob((current) => {
      if (!current) return null;
      const newSkill: JDSkill = {
        skill_name: skill_name.trim(),
        is_mandatory,
      };
      return {
        ...current,
        skills: [...current.skills, newSkill],
      };
    });
  }, []);

  const removeSkill = useCallback((skillName: string) => {
    setExtractedJob((current) => {
      if (!current) return null;
      return {
        ...current,
        skills: current.skills.filter((s) => s.skill_name !== skillName),
      };
    });
  }, []);

  return {
    step,
    setStep,
    rawJobDescription,
    setRawJobDescription,
    hiringManagerId,
    setHiringManagerId,
    extractedJob,
    setExtractedJob,
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
  };
}
