from bs4 import BeautifulSoup

from src.schemas.postjobfree_resume import PostJobFreeResume


class PostJobFreeResumeParser:
    def parse(
        self,
        html: str,
        source_url: str,
    ) -> PostJobFreeResume:

        soup = BeautifulSoup(html, "html.parser")

        h1_tag = soup.find("h1")
        title = h1_tag.get_text(strip=True) if h1_tag is not None else ""

        loc_tag = soup.select_one(".colorLocation")
        location = loc_tag.get_text(strip=True) if loc_tag is not None else ""

        date_tag = soup.select_one(".colorDate")
        posted_date = date_tag.get_text(strip=True) if date_tag is not None else ""

        resume_div = soup.select_one(".normalText")
        paragraphs = resume_div.find_all("p") if resume_div is not None else []

        candidate_name = (
            paragraphs[0].get_text(strip=True)
            if paragraphs
            else None
        )

        phone = None
        email = None

        for paragraph in paragraphs:
            text = paragraph.get_text(" ", strip=True)

            if text.startswith("Phone:"):
                phone = text

            if text.startswith("Mail id:"):
                email = text

        raw_resume_text = "\n".join(
            paragraph.get_text(" ", strip=True)
            for paragraph in paragraphs
        )

        return PostJobFreeResume(
            title=title,
            location=location,
            posted_date=posted_date,
            candidate_name=candidate_name,
            phone=phone,
            email=email,
            raw_resume_text=raw_resume_text,
            source_url=source_url,
        )
