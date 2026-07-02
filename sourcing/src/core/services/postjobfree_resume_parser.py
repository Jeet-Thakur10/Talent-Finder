from bs4 import BeautifulSoup

from src.schemas.postjobfree_resume import PostJobFreeResume


class PostJobFreeResumeParser:
    def parse(
        self,
        html: str,
        source_url: str,
    ) -> PostJobFreeResume:

        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("h1").get_text(strip=True)

        location = (
            soup.select_one(".colorLocation")
            .get_text(strip=True)
        )

        posted_date = (
            soup.select_one(".colorDate")
            .get_text(strip=True)
        )

        resume_div = soup.select_one(".normalText")

        paragraphs = resume_div.find_all("p")

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
