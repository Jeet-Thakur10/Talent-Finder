import { useState } from "react";

interface DashboardHeaderProps {
  breadcrumbs: string[];
  onBreadcrumbClick?: (crumb: string) => void;
}

const MOCK_NOTIFICATIONS = [
  {
    id: 1,
    text: "Hiring Manager left feedback on candidate Sarah Jenkins",
    time: "10 mins ago",
  },
  {
    id: 2,
    text: "Pipeline scoring completed for Software Engineer II profile",
    time: "1 hour ago",
  },
  {
    id: 3,
    text: "New resume import batch initiated for Senior React Developer",
    time: "2 hours ago",
  },
];

export function DashboardHeader({
  breadcrumbs,
  onBreadcrumbClick,
}: DashboardHeaderProps) {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="dashboard-topbar relative">
      <div>
        <div className="dashboard-breadcrumbs flex items-center gap-1">
          {breadcrumbs.map((crumb, idx) => {
            const isClickable = crumb === "Job Campaigns";
            return (
              <span key={crumb} className="flex items-center">
                {idx > 0 && <span className="text-slate-400 mx-1">/</span>}
                {isClickable ? (
                  <button
                    type="button"
                    onClick={() => onBreadcrumbClick?.(crumb)}
                    className="hover:text-slate-900 hover:underline cursor-pointer transition text-slate-500 font-medium"
                  >
                    {crumb}
                  </button>
                ) : (
                  <span className="text-slate-950 font-semibold">{crumb}</span>
                )}
              </span>
            );
          })}
        </div>
      </div>

      <div className="relative">
        <button
          type="button"
          onClick={() => setShowNotifications(!showNotifications)}
          className="notification-indicator relative flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-medium text-slate-600 hover:border-slate-350 transition cursor-pointer"
        >
          <span className="notification-dot h-2 w-2 rounded-full bg-indigo-600 animate-pulse" />
          Notifications
        </button>

        {showNotifications && (
          <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl z-50">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
              <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
                Notifications
              </span>
              <button
                type="button"
                onClick={() => setShowNotifications(false)}
                className="text-slate-400 hover:text-slate-600 text-xs cursor-pointer"
              >
                Close
              </button>
            </div>
            <div className="space-y-3">
              {MOCK_NOTIFICATIONS.map((notif) => (
                <div key={notif.id} className="text-xs text-slate-700 hover:bg-slate-50 p-2 rounded-lg transition text-left">
                  <p className="font-medium text-slate-800 leading-snug">{notif.text}</p>
                  <span className="text-[10px] text-slate-400 block mt-1">{notif.time}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
