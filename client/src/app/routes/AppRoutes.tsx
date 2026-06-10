import { Routes, Route, Navigate } from "react-router-dom";

import { LoginPage } from "../../features/auth/components/LoginPage";
import { ForgotPasswordPage } from "../../features/auth/components/ForgotPasswordPage";
import { VerifyOtpPage } from "../../features/auth/components/VerifyOtpPage";
import { ResetPasswordPage } from "../../features/auth/components/ResetPasswordPage";
import { ProtectedRoute } from "../../features/auth/components/ProtectedRoute";
import { DashboardPage } from "../../features/dashboard/components/DashboardPage";

import { PublicRoute } from "../../features/auth/components/PublicRoute";
import { useAuth } from "../../features/auth/hooks/useAuth";

function RootRedirect() {
  const { isAuthenticated, isLoading } =
    useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <Navigate
      to={
        isAuthenticated
          ? "/dashboard"
          : "/login"
      }
      replace
    />
  );
}

export function AppRoutes() {
  return (

    <Routes>
      <Route
        path="/"
        element={<RootRedirect />}
      />
      <Route
        path="/login"
        element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>}
      />

      <Route
        path="/forgot-password"
        element={
        <PublicRoute>
          <ForgotPasswordPage />
        </PublicRoute>}
      />

      <Route
        path="/verify-otp"
        element={
        <PublicRoute>
          <VerifyOtpPage />
        </PublicRoute>}
      />

      <Route
        path="/reset-password"
        element={
        <PublicRoute>
          <ResetPasswordPage />
        </PublicRoute>}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}