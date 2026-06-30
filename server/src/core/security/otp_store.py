from datetime import datetime
from typing import TypedDict


class OTPRecord(TypedDict):
    otp: str
    expires_at: datetime


otp_store: dict[str, OTPRecord] = {}
