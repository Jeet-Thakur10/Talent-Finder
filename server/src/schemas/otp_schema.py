from pydantic import BaseModel


class ForgotPasswordRequest(BaseModel):
    email: str

class ForgotPasswordResponse(BaseModel):
    message: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class VerifyOTPResponse(BaseModel):
    reset_token: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

class ResetPasswordResponse(BaseModel):
    message: str
