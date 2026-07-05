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

      if (response.user.role === "recruiter") {
        navigate("/recruiter/job-descriptions", {
          replace: true,
        });
      } else {
        navigate("/dashboard", {
          replace: true,
        });
      }
    } catch {
      setError(
        "Invalid email or password",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#f8fafc] px-4 relative">
      {/* Subtle background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(37,99,235,0.03),transparent_35%)] pointer-events-none" />

      <div className="w-full max-w-[27rem] z-10 flex flex-col items-center">
        {/* Branding header above card */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-600/10 mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-slate-950">Talent Finder</h1>
          <p className="text-xs text-slate-500 mt-1.5">
            AI-powered recruitment platform
          </p>
        </div>

        {/* Login Card */}
        <div className="w-full bg-white border border-slate-200/80 rounded-2xl p-9 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 mb-6">Login to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="email" className="auth-label text-[10px] text-slate-500 font-semibold tracking-wider uppercase">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="auth-label text-[10px] text-slate-500 font-semibold tracking-wider uppercase">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="auth-input !py-2.5 !rounded-xl text-sm focus:outline-none"
                required
              />
            </div>

            {error && (
              <div className="auth-error !rounded-xl !py-2.5 !px-3.5 text-xs font-semibold">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="auth-button w-full !py-3 !rounded-xl text-sm font-semibold tracking-wide flex justify-center items-center gap-2 cursor-pointer shadow-md shadow-blue-500/10 focus:ring-4 focus:ring-blue-100"
            >
              {isSubmitting ? "Logging in..." : "Login"}
            </button>
          </form>

          <div className="mt-6 border-t border-slate-100 pt-5 text-center">
            <Link to="/forgot-password" className="text-xs font-semibold text-slate-550 hover:text-slate-900 transition">
              Forgot password?
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}