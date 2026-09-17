import type { RiskLevel } from "../components/ui/RiskBadge";

export type OverviewDemoEvent = {
  id: string;
  type: string;
  severity: "HIGH" | "MEDIUM";
  source: string;
  timestamp: string;
  entity: string;
};

export type OverviewDemoRiskCompany = {
  company: string;
  score: string;
  level: RiskLevel;
  events: number;
};

export const overviewDemoEvents: OverviewDemoEvent[] = [
  {
    id: "demo-event-001",
    type: "FACILITY_OUTAGE",
    severity: "HIGH",
    source: "Demo source",
    timestamp: "Demo T+12m",
    entity: "TSMC",
  },
  {
    id: "demo-event-002",
    type: "SUPPLY_DISRUPTION",
    severity: "MEDIUM",
    source: "Demo source",
    timestamp: "Demo T+38m",
    entity: "Samsung Electronics",
  },
  {
    id: "demo-event-003",
    type: "REGULATION_CHANGE",
    severity: "MEDIUM",
    source: "Demo source",
    timestamp: "Demo T+1h",
    entity: "Semiconductor domain",
  },
];

export const overviewDemoRiskCompanies: OverviewDemoRiskCompany[] = [
  {
    company: "NVIDIA",
    score: "0.75",
    level: "CRITICAL",
    events: 2,
  },
  {
    company: "TSMC",
    score: "0.61",
    level: "HIGH",
    events: 2,
  },
  {
    company: "Samsung Electronics",
    score: "0.42",
    level: "MEDIUM",
    events: 1,
  },
];
