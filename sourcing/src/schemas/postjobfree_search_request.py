from pydantic import BaseModel


class PostJobFreeSearchRequest(BaseModel):
    title_words: str = ""
    required_words: str = ""
    resume_text_words: str = ""
    excluded_words: str = ""
