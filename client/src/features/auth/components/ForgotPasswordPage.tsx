import { useState } from "react";

import { useNavigate } from "react-router-dom";

import { authService } from "../services/auth.service";

export function ForgotPasswordPage() {
  const navigate = useNavigate();

  const [email, setEmail] =
    useState("");

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setError("");

    try {
      setIsSubmitting(true);

      await authService.forgotPassword({
        email,
      });

      navigate("/verify-otp", {
        state: {
          email,
        },
      });
    } catch {
      setError(
        "Unable to send OTP. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-bold">
          Forgot Password
        </h1>

        <form
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium"
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              placeholder="Enter your email"
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
              ? "Sending OTP..."
              : "Send OTP"}
          </button>
        </form>
      </div>
    </div>
  );
}