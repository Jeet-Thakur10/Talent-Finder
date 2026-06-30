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

export interface CandidateScoreBreakdown {
  skills: number;
  experience: number;
  recency: number;
  role_fit: number;
  education: number;
}

export interface CandidateScore {
  candidate_id: string;
  job_description_id: string;
  final_score: number;
  confidence: number;
  breakdown: CandidateScoreBreakdown;
  matched_mandatory_skills: string[];
  matched_optional_skills: string[];
  missing_mandatory_skills: string[];
  explanation: Record<string, unknown>;
  updated_at: string;
}

export interface CandidateListItem {
  candidate_id: string;
  full_name: string;
  current_title: string | null;
  final_score: number;
  confidence: number;
  updated_at: string;
}

export interface CandidateImportRequest {
  job_description_id: string;
  resume_text: string;
}

export interface CandidateImportResponse {
  candidate: CandidateDetails;
  score: CandidateScore;
}
