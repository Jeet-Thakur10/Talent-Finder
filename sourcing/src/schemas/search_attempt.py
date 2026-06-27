from pydantic import BaseModel

class SearchAttempt(BaseModel):
    attempt_number: int
    title: str
    skills: list[str]
    resumes_found: int
    candidates_persisted: int
    new_candidates_persisted: int
    candidates_remaining: int
    reason: str
    query_url: str

class SearchOptimizationPlan(BaseModel):
    generalize_title: str | None = None
    skills_to_remove: list[str] = []
    reason: str
