import type { ReactNode } from "react";

import {
  AlertTriangle,
  Clock3,
  Inbox,
  LoaderCircle,
} from "lucide-react";

import { Button } from "./Button";

type StatePanelVariant =
  | "loading"
  | "empty"
  | "error"
  | "stale";

type StatePanelProps = {
  variant: StatePanelVariant;
  title: string;
  description: string;

  actionLabel?: string;
  onAction?: () => void;

  children?: ReactNode;
  compact?: boolean;
};

const stateIcons = {
  loading: LoaderCircle,
  empty: Inbox,
  error: AlertTriangle,
  stale: Clock3,
};

export function StatePanel({
  variant,
  title,
  description,
  actionLabel,
  onAction,
  children,
  compact = false,
}: StatePanelProps) {
  const Icon = stateIcons[variant];

  return (
    <div
      className={`state-panel state-panel--${variant}${
        compact ? " is-compact" : ""
      }`}
      role={variant === "error" ? "alert" : "status"}
    >
      <div className="state-panel-icon" aria-hidden="true">
        <Icon
          size={compact ? 17 : 20}
          className={
            variant === "loading"
              ? "state-panel-spinner"
              : undefined
          }
        />
      </div>

      <div className="state-panel-copy">
        <strong>{title}</strong>

        <p>{description}</p>

        {children}
      </div>

      {actionLabel && (
        <Button
          variant="secondary"
          onClick={onAction}
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}