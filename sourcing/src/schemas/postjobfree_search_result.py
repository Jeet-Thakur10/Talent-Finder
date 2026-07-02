from pydantic import BaseModel


class PostJobFreeSearchResult(BaseModel):
    title: str
    location: str
    resume_url: str
    posted_date: str | None = None
