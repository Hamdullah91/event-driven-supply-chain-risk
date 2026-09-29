import type { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: ReactNode;
  detail?: string;
  status?: ReactNode;
};

export function MetricCard({
  label,
  value,
  detail,
  status,
}: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <span className="metric-card-label">{label}</span>
        {status && <div className="metric-card-status">{status}</div>}
      </div>

      <div className="metric-card-value">{value}</div>

      {detail && <p className="metric-card-detail">{detail}</p>}
    </article>
  );
}