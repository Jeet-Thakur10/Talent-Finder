export interface HMCampaign {
  id: string;
  title: string;
  department: string | null;
  recruiter_name: string;
  shared_at: string | null;
  shared_candidate_count: number;
  accepted_candidate_count: number;
  rejected_candidate_count: number;
  pending_candidate_count: number;
}

export interface HMSharedCandidate {
  candidate_id: string;
  full_name: string;
  current_title: string | null;
  total_experience_months: number;
  location: string | null;
  final_score: number | null;
  recruiter_notes: string | null;
  shared_at: string | null;
  hm_decision: "PENDING" | "INTERVIEW_SENT" | "REJECTED";
  hiring_manager_notes: string | null;
  interview_link: string | null;
  interview_datetime: string | null;
  interview_timezone: string | null;
  interview_message: string | null;
  interview_sent_at: string | null;
}
