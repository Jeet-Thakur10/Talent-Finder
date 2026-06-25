export interface JDSkill {
  id?: string;
  skill_name: string;
  is_mandatory: boolean;
}

export interface EmploymentType {
  id: string;
  code: string;
  name: string;
}

export interface HiringManager {
  id: string;
  name: string;
  email: string;
}

export interface JobDescriptionStatus {
  id: string;
  code: string;
  name: string;
}

export interface JobDescription {
  id: string;
  title: string;
  department: string | null;
  job_purpose: string;
  responsibilities: string;
  min_experience: number;
  max_experience: number;
  location: string;
  education_requirement: string;
  preferred_qualifications: string | null;
  employment_type_id: string;
  status_id: string;
  hiring_manager_id: string | null;
  created_at: string;
  updated_at: string;
  skills: JDSkill[];
}

export interface JobDescriptionPayload {
  title: string;
  department: string | null;
  job_purpose: string;
  responsibilities: string;
  min_experience: number;
  max_experience: number;
  location: string;
  employment_type_id: string;
  education_requirement: string;
  preferred_qualifications: string | null;
  hiring_manager_id: string | null;
  skills: JDSkill[];
}

export interface PipelineCandidateResult {
  candidate_id: string;
  full_name: string;
  current_title: string | null;
  location: string | null;
  total_experience_months: number;
  prescore_score: number | null;
  prescore_rank: number | null;
  final_score: number | null;
  confidence: number | null;
  matched_mandatory_skills: string[];
  matched_optional_skills: string[];
  missing_mandatory_skills: string[];
  stage: string;
  recruiter_notes: string | null;
  hiring_manager_notes: string | null;
  updated_at: string | null;
}

export interface PipelineExecutionPayload {
  confirm: boolean;
  k: number;
}

export interface PipelineExecutionResponse {
  stage: "preview" | "completed";
  matched_candidate_count: number;
  top_k: number;
  candidates: PipelineCandidateResult[];
}

export interface CandidateSkill {
  id: string;
  skill_name: string;
  is_primary: boolean;
}

export interface CandidateExperienceSkill {
  id: string;
  skill_name: string;
}

export interface CandidateExperience {
  id: string;
  company_name: string | null;
  title: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  skills: CandidateExperienceSkill[];
}

export interface CandidateEducation {
  id: string;
  institution_name: string | null;
  degree: string;
  field_of_study: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface CandidateDetails {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  current_title: string | null;
  location: string | null;
  summary: string | null;
  source_type: string;
  total_experience_months: number;
  created_at: string;
  updated_at: string;
  skills: CandidateSkill[];
  experiences: CandidateExperience[];
  educations: CandidateEducation[];
}

export interface PipelineSnapshot {
  id: string;
  candidate_id: string;
  jd_id: string;
  stage: string;
  recruiter_notes: string | null;
  hiring_manager_notes: string | null;
  created_at: string;
}

export interface CandidateScoreBreakdown {
  final_score: number;
  skill_score: number;
  experience_score: number;
  recency_score: number;
  role_fit_score: number;
  education_score: number;
  confidence: number;
  explanation: Record<string, unknown>;
}

export interface CandidateEvaluationBoard {
  candidate: CandidateDetails;
  pipeline: PipelineSnapshot | null;
  score: CandidateScoreBreakdown | null;
}

export interface PipelineNotesPayload {
  recruiter_notes: string | null;
}

export interface PipelineStagePayload {
  stage: string;
  candidate_ids: string[];
}
