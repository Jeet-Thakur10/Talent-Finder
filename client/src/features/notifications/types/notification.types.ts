export interface Notification {
  id: string;
  user_id: string;
  notification_type:
    | "SCORING_COMPLETED"
    | "SHORTLIST_SHARED"
    | "CANDIDATE_ACCEPTED"
    | "INTERVIEW_INVITATION"
    | "JD_CLOSED"
    | "SYSTEM";
  title: string;
  message: string;
  target_url: string | null;
  is_read: boolean;
  metadata: Record<string, any> | null;
  created_at: string;
}

export interface UnreadCountResponse {
  unread_count: number;
}
