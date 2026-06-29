import { useAuth } from "../../auth/hooks/useAuth";

export function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <h1 className="workspace-title">Profile</h1>
          <p className="workspace-subtitle">
            View your account details and user settings.
          </p>
        </div>
      </div>
      <div className="surface-card">
        <div className="space-y-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Name</span>
            <p className="text-sm font-medium text-slate-900 mt-1">{user?.name ?? "N/A"}</p>
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Email</span>
            <p className="text-sm font-medium text-slate-900 mt-1">{user?.email ?? "N/A"}</p>
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Role</span>
            <p className="text-sm font-medium text-slate-900 mt-1 capitalize">{user?.role ?? "N/A"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
