import { useNavigate } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";
import type { Notification } from "../types/notification.types";

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 10) return "Just now";
  if (diffSecs < 60) return `${diffSecs}s ago`;
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getNotificationBadge(type: string) {
  switch (type) {
    case "SCORING_COMPLETED":
      return (
        <span className="status-badge bg-sky-50 text-sky-700 border border-sky-200 text-[10px] !px-2.5 !py-0.5 rounded-full font-semibold">
          Scoring Complete
        </span>
      );
    case "SHORTLIST_SHARED":
      return (
        <span className="status-badge bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] !px-2.5 !py-0.5 rounded-full font-semibold">
          Shortlist Shared
        </span>
      );
    case "CANDIDATE_ACCEPTED":
      return (
        <span className="status-badge bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] !px-2.5 !py-0.5 rounded-full font-semibold">
          Accepted
        </span>
      );
    case "INTERVIEW_INVITATION":
      return (
        <span className="status-badge bg-amber-50 text-amber-700 border border-amber-200 text-[10px] !px-2.5 !py-0.5 rounded-full font-semibold">
          Interview
        </span>
      );
    case "JD_CLOSED":
      return (
        <span className="status-badge bg-rose-50 text-rose-700 border border-rose-200 text-[10px] !px-2.5 !py-0.5 rounded-full font-semibold">
          Closed
        </span>
      );
    default:
      return (
        <span className="status-badge bg-slate-50 text-slate-600 border border-slate-200 text-[10px] !px-2.5 !py-0.5 rounded-full font-semibold">
          System
        </span>
      );
  }
}

export function NotificationsPage() {
  const { notifications, isLoading, error, refetch, markAsRead, markAllAsRead } =
    useNotifications();
  const navigate = useNavigate();

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }
    if (notification.target_url) {
      navigate(notification.target_url);
    }
  };

  const unreadNotifications = notifications.filter((n) => !n.is_read);
  const hasUnread = unreadNotifications.length > 0;

  return (
    <div className="workspace-shell">
      <div className="workspace-header">
        <div>
          <h1 className="workspace-title">Notifications</h1>
          <p className="workspace-subtitle">
            Stay updated with updates, workflow status alerts, and activity logs.
          </p>
        </div>
        <div>
          {hasUnread && (
            <button
              type="button"
              onClick={markAllAsRead}
              className="workspace-ghost-button !py-2.5 !px-4 hover:bg-slate-50 text-xs font-semibold flex items-center gap-1.5 focus:outline-none"
            >
              <svg
                className="w-4 h-4 text-slate-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <span>Mark all as read</span>
            </button>
          )}
        </div>
      </div>

      <div className="surface-card">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-16 space-y-3">
            <svg
              className="animate-spin h-8 w-8 text-slate-800"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <p className="text-sm font-medium text-slate-500">Loading notifications...</p>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-6 text-center">
            <svg
              className="mx-auto h-12 w-12 text-rose-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="mt-3 text-sm font-semibold text-rose-800">
              Failed to load notifications
            </h3>
            <p className="mt-1 text-xs text-rose-600 max-w-sm mx-auto">{error}</p>
            <button
              type="button"
              onClick={refetch}
              className="workspace-ghost-button mt-4 !py-2 !px-4 text-xs font-semibold hover:bg-white text-slate-700"
            >
              Try Again
            </button>
          </div>
        )}

        {!isLoading && !error && notifications.length === 0 && (
          <div className="py-20 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
              <svg
                className="w-8 h-8 text-slate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900">All caught up!</h3>
            <p className="empty-copy mt-1 max-w-sm mx-auto">
              You have no notifications at the moment. We'll let you know when something important happens.
            </p>
          </div>
        )}

        {!isLoading && !error && notifications.length > 0 && (
          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={`group flex items-start gap-4 p-5 hover:bg-slate-50/70 transition cursor-pointer text-left ${
                  !notification.is_read ? "bg-indigo-50/20" : ""
                }`}
              >
                {/* Unread indicator dot */}
                <div className="flex h-5 items-center justify-center shrink-0">
                  <div
                    className={`h-2.5 w-2.5 rounded-full ${
                      !notification.is_read ? "bg-indigo-600" : "bg-transparent border border-slate-300"
                    }`}
                  />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      {getNotificationBadge(notification.notification_type)}
                      <h4
                        className={`text-sm tracking-tight ${
                          !notification.is_read
                            ? "font-semibold text-slate-950"
                            : "font-medium text-slate-800"
                        }`}
                      >
                        {notification.title}
                      </h4>
                    </div>
                    <span className="text-xs font-medium text-slate-400 whitespace-nowrap shrink-0">
                      {formatRelativeTime(notification.created_at)}
                    </span>
                  </div>
                  <p
                    className={`mt-1.5 text-sm leading-relaxed ${
                      !notification.is_read ? "text-slate-700" : "text-slate-500"
                    }`}
                  >
                    {notification.message}
                  </p>
                </div>

                {notification.target_url && (
                  <div className="shrink-0 flex items-center self-center opacity-0 group-hover:opacity-100 transition duration-150 pl-2">
                    <svg
                      className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transform translate-x-0 group-hover:translate-x-0.5 transition-all"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2.5}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
