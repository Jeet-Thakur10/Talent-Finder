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
  } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <>{children}</>;
}