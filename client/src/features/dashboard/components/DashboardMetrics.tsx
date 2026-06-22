interface DashboardMetricsProps {
  activeJds: number;
  pendingShortlists: number;
}

const METRIC_ITEMS = [
  {
    key: "activeJds",
    label: "Active JDs",
    copy: "Open recruiter briefs currently being tracked.",
  },
  {
    key: "pendingShortlists",
    label: "Pending Shortlists",
    copy: "Score >= 75 with no missing mandatory skills.",
  },
] as const;

export function DashboardMetrics(
  props: DashboardMetricsProps,
) {
  return (
    <section className="metrics-grid">
      {METRIC_ITEMS.map((metric) => (
        <div
          key={metric.key}
          className="metric-surface"
        >
          <div className="metric-surface-label">
            {metric.label}
          </div>

          <div className="metric-surface-value">
            {props[metric.key]}
          </div>

          <p className="metric-surface-copy">
            {metric.copy}
          </p>
        </div>
      ))}
    </section>
  );
}
