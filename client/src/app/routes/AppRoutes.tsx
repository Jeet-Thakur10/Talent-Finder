import { Routes, Route, Navigate } from "react-router-dom";

import { LoginPage } from "../../features/auth/components/LoginPage";
import { ProtectedRoute } from "../../features/auth/components/ProtectedRoute";

import { PublicRoute } from "../../features/auth/components/PublicRoute";
import { useAuth } from "../../features/auth/hooks/useAuth";

// Recruiter Layout & Components
import { RecruiterLayout } from "../../components/layout/RecruiterLayout";
import { JobDescriptionsPage } from "../../features/recruiter/components/JobDescriptionsPage";
import { JobDescriptionCreatePage } from "../../features/recruiter/components/JobDescriptionCreatePage";
import { JobDescriptionDetailPage } from "../../features/recruiter/components/JobDescriptionDetailPage";
import { JobDescriptionEditPage } from "../../features/recruiter/components/JobDescriptionEditPage";
import { JobDescriptionScoringConfigPage } from "../../features/recruiter/components/JobDescriptionScoringConfigPage";
import { JobDescriptionCandidatesPage } from "../../features/recruiter/components/JobDescriptionCandidatesPage";
import { RecruiterCandidateDetailPage } from "../../features/recruiter/components/RecruiterCandidateDetailPage";

import { ProfilePage as RecruiterProfilePage } from "../../features/recruiter/components/ProfilePage";

// Hiring Manager Layout & Components
import { HiringManagerLayout } from "../../components/layout/HiringManagerLayout";
import { SharedCampaignsPage } from "../../features/hiring-manager/components/SharedCampaignsPage";
import { HiringManagerTasksPage } from "../../features/hiring-manager/components/HiringManagerTasksPage";
import { ProfilePage as HMProfilePage } from "../../features/hiring-manager/components/ProfilePage";
import { SharedCampaignDetailsPage } from "../../features/hiring-manager/components/SharedCampaignDetailsPage";
import { HiringManagerCandidateReviewPage } from "../../features/hiring-manager/components/HiringManagerCandidateReviewPage";
import { NotificationsPage } from "../../features/notifications/components/NotificationsPage";

function RootRedirect() {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  if (isAuthenticated) {
    if (user?.role === "recruiter") {
      return <Navigate to="/recruiter/job-descriptions" replace />;
    }
    if (user?.role === "hiring_manager") {
      return <Navigate to="/hm/shared-campaigns" replace />;
    }
    // Fallback if role is undefined or unrecognized
    return <Navigate to="/login" replace />;
  }

  return <Navigate to="/login" replace />;
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
          </PublicRoute>
        }
      />

      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      <Route
        path="/verify-otp"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      <Route
        path="/reset-password"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      {/* Recruiter Shell Routes */}
      <Route
        path="/recruiter"
        element={
          <ProtectedRoute>
            <RecruiterLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="job-descriptions" replace />} />
        <Route path="job-descriptions" element={<JobDescriptionsPage />} />
        <Route path="job-descriptions/create" element={<JobDescriptionCreatePage />} />
        <Route path="job-descriptions/:jobDescriptionId" element={<JobDescriptionDetailPage />} />
        <Route path="job-descriptions/:jobDescriptionId/edit" element={<JobDescriptionEditPage />} />
        <Route path="job-descriptions/:jobDescriptionId/score-config" element={<JobDescriptionScoringConfigPage />} />
        <Route path="job-descriptions/:jobDescriptionId/candidates" element={<JobDescriptionCandidatesPage />} />
        <Route path="job-descriptions/:jobDescriptionId/candidates/:candidateId" element={<RecruiterCandidateDetailPage />} />

        <Route path="profile" element={<RecruiterProfilePage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Hiring Manager Shell Routes */}
      <Route
        path="/hm"
        element={
          <ProtectedRoute>
            <HiringManagerLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="shared-campaigns" replace />} />
        <Route path="shared-campaigns" element={<SharedCampaignsPage />} />
        <Route path="shared-campaigns/:jobDescriptionId" element={<SharedCampaignDetailsPage />} />
        <Route path="shared-campaigns/:jobDescriptionId/candidates/:candidateId" element={<HiringManagerCandidateReviewPage />} />
        <Route path="tasks" element={<HiringManagerTasksPage />} />
        <Route path="profile" element={<HMProfilePage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Legacy Dashboard Redirections */}
      <Route
        path="/dashboard/*"
        element={<Navigate to="/" replace />}
      />
      <Route
        path="/dashboard"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  );
}
