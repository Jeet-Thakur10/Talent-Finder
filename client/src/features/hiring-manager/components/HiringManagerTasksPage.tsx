export function HiringManagerTasksPage() {
  return (
    <div className="workspace-shell animate-fade-in">
      <div className="workspace-header">
        <div>
          <h1 className="workspace-title">Tasks</h1>
          <p className="workspace-subtitle">
            Monitor background activities and notification logs.
          </p>
        </div>
      </div>

      <div className="surface-card p-8 flex flex-col items-center justify-center text-center min-h-[300px]">
        <div className="h-16 w-16 rounded-2xl bg-slate-50 text-slate-500 flex items-center justify-center mb-4">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-slate-900">No Active Tasks</h3>
        <p className="text-slate-500 text-sm max-w-sm mt-1">
          Background evaluation tasks and notification logs will be displayed here in the future.
        </p>
      </div>
    </div>
  );
}
