"""Authentication request/response schemas."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, field_validator


class UserRole(StrEnum):
    recruiter = "recruiter"
    hiring_manager = "hiring_manager"


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("Invalid email address")
        return value


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: UserRole

    model_config = {
        "from_attributes": True,
    }


class LoginResponse(BaseModel):
    user: UserResponse


class AuthenticatedUserContext(BaseModel):
    user_id: UUID
    role: UserRole

class RefreshResponse(BaseModel):
    message: str

class LogoutResponse(BaseModel):
    message: str
