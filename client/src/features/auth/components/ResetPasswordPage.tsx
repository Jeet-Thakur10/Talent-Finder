import { useState } from "react";

import {
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { authService } from "../services/auth.service";

interface ResetPasswordLocationState {
  resetToken: string;
}

export function ResetPasswordPage() {
  const navigate = useNavigate();

  const location = useLocation();

  const state =
    location.state as
      | ResetPasswordLocationState
      | undefined;

  const resetToken =
    state?.resetToken;

  const [newPassword, setNewPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  if (!resetToken) {
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

      await authService.resetPassword({
        reset_token: resetToken,
        new_password: newPassword,
      });

      navigate("/login", {
        replace: true,
      });
    } catch {
      setError(
        "Unable to reset password. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-bold">
          Reset Password
        </h1>

        <form
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          <div>
            <label
              htmlFor="new-password"
              className="mb-1 block text-sm font-medium"
            >
              New Password
            </label>

            <input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) =>
                setNewPassword(
                  e.target.value,
                )
              }
              placeholder="Enter new password"
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
              ? "Resetting..."
              : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
}