from pydantic import BaseModel


class PostJobFreeResume(BaseModel):
    title: str
    location: str
    posted_date: str

    candidate_name: str | None = None
    phone: str | None = None
    email: str | None = None

    raw_resume_text: str

    source_url: str