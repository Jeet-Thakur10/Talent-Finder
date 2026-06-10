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
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-bold">
          Verify OTP
        </h1>

        <form
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          <div>
            <label
              htmlFor="otp"
              className="mb-1 block text-sm font-medium"
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
              className="w-full rounded border px-3 py-2"
            />
          </div>

          {error && (
            <p className="text-sm text-red-500">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded bg-black px-4 py-2 text-white disabled:opacity-50"
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