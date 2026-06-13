import { useState } from "react";

import {
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { authService } from "../services/auth.service";

interface VerifyOtpLocationState {
  email: string;
}

export function VerifyOtpPage() {
  const navigate = useNavigate();

  const location = useLocation();

  const state =
    location.state as
      | VerifyOtpLocationState
      | undefined;

  const email = state?.email;

  const [otp, setOtp] =
    useState("");

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  if (!email) {
    return (
      <Navigate
        to="/forgot-password"
        replace
      />
    );
  }

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setError("");

    try {
      setIsSubmitting(true);

      const response =
        await authService.verifyOtp({
          email,
          otp,
        });

      navigate("/reset-password", {
        state: {
          resetToken:
            response.reset_token,
        },
      });
    } catch {
      setError(
        "Invalid OTP. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-kicker">Talent Finder</div>

        <h1 className="auth-title">Verify code</h1>

        <p className="auth-subtitle">
          Enter the one-time code sent to your email address.
        </p>

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >
          <div className="auth-field">
            <label
              htmlFor="otp"
              className="auth-label"
            >
              OTP
            </label>

            <input
              id="otp"
              type="text"
              value={otp}
              onChange={(e) =>
                setOtp(e.target.value)
              }
              placeholder="Enter OTP"
              className="auth-input"
            />
          </div>

          {error && (
            <p className="auth-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="auth-button"
          >
            {isSubmitting
              ? "Verifying..."
              : "Verify OTP"}
          </button>
        </form>
      </div>
    </div>
  );
}