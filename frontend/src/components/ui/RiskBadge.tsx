import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  CircleMinus,
  ShieldAlert,
} from "lucide-react";

export type RiskLevel =
  | "NONE"
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

type RiskBadgeProps = {
  level: RiskLevel;
};

const riskIcons = {
  NONE: CircleMinus,
  LOW: CheckCircle2,
  MEDIUM: AlertCircle,
  HIGH: AlertTriangle,
  CRITICAL: ShieldAlert,
};

export function RiskBadge({ level }: RiskBadgeProps) {
  const Icon = riskIcons[level];

  return (
    <span
      className={`risk-badge risk-badge--${level.toLowerCase()}`}
      aria-label={`${level} risk`}
    >
      <Icon size={13} strokeWidth={2} aria-hidden="true" />
      <span>{level}</span>
    </span>
  );
}