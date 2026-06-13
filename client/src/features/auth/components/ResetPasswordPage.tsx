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
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-kicker">Talent Finder</div>

        <h1 className="auth-title">Choose a new password</h1>

        <p className="auth-subtitle">
          Create a fresh password to finish securing your account.
        </p>

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >
          <div className="auth-field">
            <label
              htmlFor="new-password"
              className="auth-label"
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
              ? "Resetting..."
              : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
}