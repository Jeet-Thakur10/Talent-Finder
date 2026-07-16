import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/hooks/useAuth";
import { useUnreadNotificationCount } from "../../features/notifications/hooks/useUnreadNotificationCount";

export interface NavLinkConfig {
  to: string;
  label: string;
  icon: ReactNode;
}

export interface WorkspaceLayoutProps {
  navLinks: NavLinkConfig[];
  portalName: string;
  workspaceName: string;
  brandMark?: string;
  brandName?: string;
}

export function WorkspaceLayout({
  navLinks,
  portalName,
  workspaceName,
  brandMark = "TF",
  brandName = "Talent Finder",
}: WorkspaceLayoutProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { unreadCount } = useUnreadNotificationCount();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "U";

  const SidebarContent = () => (
    <div className="flex h-full flex-col bg-transparent">
      <div className="dashboard-brand border-b border-[#6A89A7]/20 px-6 py-5">
        <div className="dashboard-brand-mark">
          {brandMark}
        </div>
        <div>
          <div className="dashboard-brand-name">
            {brandName}
          </div>
          <div className="dashboard-brand-copy">
            {workspaceName}
          </div>
        </div>
      </div>

      <nav className="dashboard-nav flex-1 px-4 py-5">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            onClick={() => setIsMobileMenuOpen(false)}
            className={({ isActive }) =>
              `dashboard-nav-link ${isActive ? "dashboard-nav-link-active" : ""}`
            }
          >
            {link.icon}
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-[#6A89A7]/20 p-4">
        <div className="flex items-center gap-3">
          <div className="workspace-avatar rounded-full">
            {userInitial}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs font-semibold text-white truncate">
              {user?.name}
            </div>
            <div className="text-[10px] text-[#BDDDFC] truncate">
              {user?.email}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="dashboard-shell">
      {isMobileMenuOpen && (
        <div
          onClick={() => setIsMobileMenuOpen(false)}
          className="fixed inset-0 z-40 bg-slate-900/40 md:hidden"
        />
      )}

      <aside className="workspace-app-sidebar hidden shrink-0 md:block">
        <SidebarContent />
      </aside>

      <aside
        className={`workspace-app-sidebar-mobile fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="absolute top-4 right-4 z-50">
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(false)}
            className="workspace-icon-button px-2 py-2"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <SidebarContent />
      </aside>

      <div className="workspace-main min-w-0 overflow-hidden">
        <header className="workspace-topbar shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(true)}
              className="workspace-icon-button -ml-1 px-2 py-2 md:hidden"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2 md:hidden">
              <div className="workspace-avatar h-8 w-8 rounded-lg text-sm">
                {brandMark}
              </div>
              <span className="text-base font-semibold text-white">{brandName}</span>
            </div>
            <div className="hidden md:block">
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#BDDDFC]">
                {portalName}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <NavLink
              to={user?.role === "recruiter" ? "/recruiter/notifications" : "/hm/notifications"}
              className="workspace-icon-button relative rounded-full p-2"
              title="Notifications"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-[#384959] shadow-sm">
                  {unreadCount}
                </span>
              )}
            </NavLink>

            <div className="flex items-center gap-3 border-r border-[#6A89A7]/30 pr-4">
              <div className="workspace-avatar h-8 w-8 rounded-full text-xs">
                {userInitial}
              </div>
              <div className="hidden sm:block text-right">
                <div className="text-xs font-semibold text-white">
                  {user?.name}
                </div>
                <div className="text-[10px] text-[#BDDDFC] capitalize">
                  {user?.role ? user.role.replace("_", " ") : "User"}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="workspace-ghost-button !px-3.5 !py-2 text-xs"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>Logout</span>
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto focus:outline-none">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
