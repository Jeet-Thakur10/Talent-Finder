import type { ReactNode } from "react";

import { Navigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

interface PublicRouteProps {
  children: ReactNode;
}

export function PublicRoute({
  children,
}: PublicRouteProps) {
  const {
    isAuthenticated,
    isLoading,
    user,
  } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  if (isAuthenticated) {
    if (user?.role === "recruiter") {
      return (
        <Navigate
          to="/recruiter/job-descriptions"
          replace
        />
      );
    }
    if (user?.role === "hiring_manager") {
      return (
        <Navigate
          to="/hm/shared-campaigns"
          replace
        />
      );
    }
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <>{children}</>;
}