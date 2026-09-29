import type { ReactNode } from "react";

type PanelVariant = "analytical" | "workspace";

type PanelProps = {
  title: string;
  eyebrow?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  variant?: PanelVariant;
  className?: string;
};

export function Panel({
  title,
  eyebrow,
  description,
  action,
  children,
  variant = "analytical",
  className = "",
}: PanelProps) {
  return (
    <section
      className={`ui-panel ui-panel--${variant} ${className}`.trim()}
    >
      <header className="ui-panel-header">
        <div className="ui-panel-heading">
          {eyebrow && (
            <span className="metadata-text ui-panel-eyebrow">
              {eyebrow}
            </span>
          )}

          <h2 className="card-heading">{title}</h2>

          {description && (
            <p className="ui-panel-description">{description}</p>
          )}
        </div>

        {action && <div className="ui-panel-action">{action}</div>}
      </header>

      <div className="ui-panel-content">{children}</div>
    </section>
  );
}