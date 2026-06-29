import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/hooks/useAuth";
import { authService } from "../../features/auth/services/auth.service";
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
    try {
      await authService.logout();
    } catch {
      // Ignore API errors and still clear local auth state.
    } finally {
      logout();
      navigate("/login", { replace: true });
    }
  };

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "U";

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white">
      {/* Brand logo */}
      <div className="dashboard-brand px-6 py-5 border-b border-slate-100 flex items-center gap-3">
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

      {/* Navigation */}
      <nav className="dashboard-nav flex-1 px-4 py-6 space-y-1.5">
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

      {/* Mini Profile Footer in Sidebar */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-sm">
            {userInitial}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs font-semibold text-slate-900 truncate">
              {user?.name}
            </div>
            <div className="text-[10px] text-slate-500 truncate">
              {user?.email}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen w-full bg-slate-50">
      {/* Mobile Drawer Backdrop */}
      {isMobileMenuOpen && (
        <div
          onClick={() => setIsMobileMenuOpen(false)}
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar for Desktop */}
      <aside className="w-64 border-r border-slate-200 bg-white shrink-0 hidden md:block">
        <SidebarContent />
      </aside>

      {/* Sidebar for Mobile (Slide out drawer) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-200 bg-white flex flex-col transform transition-transform duration-300 ease-in-out md:hidden ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="absolute top-4 right-4 z-50">
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-1 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <SidebarContent />
      </aside>

      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-slate-200/80 px-6 py-4 flex items-center justify-between shadow-sm shrink-0">
          {/* Left section: Hamburger and Brand info on Mobile */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(true)}
              className="p-2 -ml-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 md:hidden focus:outline-none"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2 md:hidden">
              <div className="h-8 w-8 rounded-lg bg-slate-900 text-white flex items-center justify-center font-bold text-sm shadow-md">
                {brandMark}
              </div>
              <span className="text-base font-semibold text-slate-950">{brandName}</span>
            </div>
            <div className="hidden md:block">
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                {portalName}
              </span>
            </div>
          </div>

          {/* Right section: Logged-in user information and Logout */}
          <div className="flex items-center gap-4">
            <NavLink
              to={user?.role === "recruiter" ? "/recruiter/notifications" : "/hm/notifications"}
              className="relative p-2 text-slate-500 hover:text-slate-900 rounded-full hover:bg-slate-100 transition focus:outline-none"
              title="Notifications"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white shadow-sm animate-pulse">
                  {unreadCount}
                </span>
              )}
            </NavLink>

            <div className="flex items-center gap-3 border-r border-slate-200 pr-4">
              <div className="h-8 w-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs">
                {userInitial}
              </div>
              <div className="hidden sm:block text-right">
                <div className="text-xs font-semibold text-slate-900">
                  {user?.name}
                </div>
                <div className="text-[10px] text-slate-400 capitalize">
                  {user?.role ? user.role.replace("_", " ") : "User"}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="workspace-ghost-button !py-2 !px-3.5 !rounded-xl text-xs hover:bg-slate-50 flex items-center gap-1.5 focus:outline-none"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>Logout</span>
            </button>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto bg-slate-50 focus:outline-none">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
