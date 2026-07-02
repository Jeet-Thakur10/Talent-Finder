import logging

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)


class BrevoClient:

    def __init__(self) -> None:
        self.api_key = settings.BREVO_API_KEY
        self.sender_email = settings.BREVO_SENDER_EMAIL
        self.sender_name = settings.BREVO_SENDER_NAME
        self.api_url = "https://api.brevo.com/v3/smtp/email"

    async def send_email(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_content: str,
    ) -> None:
        """Sends a transactional email via Brevo SMTP API.

        Bypasses the actual HTTP call if BREVO_API_KEY is not configured (logs instead).
        """
        if not self.api_key:
            logger.warning(
                "Brevo API Key is missing. Simulating sending email:\n"
                "To: %s <%s>\n"
                "Subject: %s\n"
                "Body snippet: %s",
                recipient_name,
                recipient_email,
                subject,
                html_content[:150] + "...",
            )
            print(
                f"[BREVO SIMULATION] Email sent to {recipient_email} "
                f"- Subject: {subject}"
            )
            return

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "sender": {
                "name": self.sender_name,
                "email": self.sender_email,
            },
            "to": [
                {
                    "email": recipient_email,
                    "name": recipient_name,
                }
            ],
            "subject": subject,
            "htmlContent": html_content,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                )
                if response.is_error:
                    logger.error(
                        "Failed to send email via Brevo. Status: %s, Error: %s",
                        response.status_code,
                        response.text,
                    )
                    response.raise_for_status()
                else:
                    logger.info(
                        "Successfully sent email to %s via Brevo.",
                        recipient_email,
                    )
            except httpx.HTTPError as e:
                logger.exception("HTTP error sending email via Brevo client")
                raise RuntimeError(f"Brevo email sending failed: {e}") from e
