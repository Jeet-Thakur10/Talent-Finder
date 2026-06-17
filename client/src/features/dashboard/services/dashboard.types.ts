export interface JDSkill {
  id: string;
  skill_name: string;
  is_mandatory: boolean;
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
  created_at: string;
  updated_at: string;
  skills: JDSkill[];
}
