import { useState } from "react";

import { Link, useNavigate } from "react-router-dom";

import { authService } from "../services/auth.service";

import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const navigate = useNavigate();

  const { login } = useAuth();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
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

      const response =
        await authService.login({
          email,
          password,
        });

      login(response.user);

      navigate("/dashboard", {
        replace: true,
      });
    } catch {
      setError(
        "Invalid email or password",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-kicker">Talent Finder</div>

        <h1 className="auth-title">Welcome back</h1>

        <p className="auth-subtitle">
          Sign in to continue finding the right talent faster.
        </p>

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >
          <div className="auth-field">
            <label
              htmlFor="email"
              className="auth-label"
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
              className="auth-input"
            />
          </div>

          <div className="auth-field">
            <label
              htmlFor="password"
              className="auth-label"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              placeholder="Enter your password"
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
              ? "Logging in..."
              : "Login"}
          </button>
        </form>

        <div className="auth-footer">
          <Link
            to="/forgot-password"
            className="auth-link"
          >
            Forgot Password?
          </Link>
        </div>
      </div>
    </div>
  );
}