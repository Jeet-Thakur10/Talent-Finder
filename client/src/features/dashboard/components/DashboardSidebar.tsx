import type { User } from "../../auth/services/auth.types";
import type { DashboardNavView } from "../hooks/useRecruiterDashboard";

interface DashboardSidebarProps {
  activeNavView: DashboardNavView;
  onLogout: () => void;
  onSelectNav: (
    view: DashboardNavView,
  ) => void;
  user: User | null;
}

export function DashboardSidebar({
  activeNavView,
  onLogout,
  onSelectNav,
  user,
}: DashboardSidebarProps) {
  return (
    <aside className="dashboard-sidebar">
      <div>
        <div className="dashboard-brand">
          <div className="dashboard-brand-mark">
            TF
          </div>

          <div>
            <div className="dashboard-brand-name">
              Talent Finder
            </div>

            <div className="dashboard-brand-copy">
              Recruiter Workspace
            </div>
          </div>
        </div>

        <nav className="dashboard-nav">
          <button
            type="button"
            onClick={() =>
              onSelectNav(
                "job-campaigns",
              )
            }
            className={`dashboard-nav-link ${
              activeNavView ===
              "job-campaigns"
                ? "dashboard-nav-link-active"
                : ""
            }`}
          >
            Dashboard / Job Campaigns
          </button>

          <button
            type="button"
            onClick={() =>
              onSelectNav("talent-pool")
            }
            className={`dashboard-nav-link ${
              activeNavView ===
              "talent-pool"
                ? "dashboard-nav-link-active"
                : ""
            }`}
          >
            Talent Pool
          </button>
        </nav>
      </div>

      <div className="profile-card">
        <div className="profile-card-name">
          {user?.name}
        </div>

        <div className="profile-card-email">
          {user?.email}
        </div>

        <div className="button-row">
          <span className="status-badge status-badge-draft">
            Recruiter
          </span>

          <button
            type="button"
            onClick={onLogout}
            className="workspace-ghost-button"
          >
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}
