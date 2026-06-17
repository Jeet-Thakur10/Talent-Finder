
from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_otp_service
from src.core.services.otp_service import OTPService
from src.schemas.otp_schema import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)

router = APIRouter(prefix="/otp", tags=["OTP"])

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    otp_service: OTPService = Depends(
        get_otp_service,
    ),
) -> ForgotPasswordResponse:

    await otp_service.forgot_password(
        data.email,
    )

    return ForgotPasswordResponse(
        message="If the email exists, an OTP has been sent.",
    )

@router.post(
    "/verify",
    response_model=VerifyOTPResponse,
)
async def verify_otp(
    data: VerifyOTPRequest,
    otp_service: OTPService = Depends(
        get_otp_service,
    ),
) -> VerifyOTPResponse:

    reset_token = await otp_service.verify_otp(
        email=data.email,
        otp=data.otp,
    )

    return VerifyOTPResponse(
        reset_token=reset_token,
    )
