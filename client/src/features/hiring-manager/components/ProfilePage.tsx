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
      <div className="workspace-grid grid-cols-1">
        <div className="surface-card space-y-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <span className="block text-[10px] font-bold uppercase tracking-widest text-slate-400">Account</span>
              <h2 className="text-xl font-semibold text-slate-900">{user?.name ?? "N/A"}</h2>
              <p className="text-sm text-slate-500">Your hiring manager account details and access information.</p>
            </div>
            <span className="status-badge border-slate-200 bg-slate-50 text-slate-700 capitalize">
              {user?.role ?? "N/A"}
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="detail-block">
              <div className="detail-label">Name</div>
              <p className="detail-copy">{user?.name ?? "N/A"}</p>
            </div>
            <div className="detail-block">
              <div className="detail-label">Email</div>
              <p className="detail-copy break-all">{user?.email ?? "N/A"}</p>
            </div>
            <div className="detail-block">
              <div className="detail-label">Role</div>
              <p className="detail-copy capitalize">{user?.role ?? "N/A"}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
