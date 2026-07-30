export interface RecruiterStage {
  label: string;
  percent: number;
}

export const RECRUITER_STAGES: Record<string, RecruiterStage> = {
  QUEUED: { label: "Understanding Job Requirements", percent: 10 },
  ACQUIRING: { label: "Searching Candidate Sources", percent: 25 },
  SOURCING: { label: "Searching Candidate Sources", percent: 45 },
  PRE_SCORING: { label: "Evaluating Candidate Matches", percent: 60 },
  SYNCHRONIZING: { label: "Evaluating Candidate Matches", percent: 75 },
  DEEP_SCORING: { label: "Evaluating Candidate Matches", percent: 90 },
  COMPLETED: { label: "Preparing Candidate Shortlist", percent: 100 },
};

export const RECRUITER_LABELS = {
  EVALUATION_STATUS: "Evaluation Status",
  MATCH_STATUS: "Match Status",
  EVALUATION_IN_PROGRESS: "Evaluation In Progress",
  FIND_CANDIDATES: "Find Candidates",
  REEVALUATE_CANDIDATES: "Re-evaluate Candidates",
  MATCH_SCORE: "Match Score",
  CONTINUE_TO_CANDIDATE_SEARCH: "Continue to Candidate Search",
};
