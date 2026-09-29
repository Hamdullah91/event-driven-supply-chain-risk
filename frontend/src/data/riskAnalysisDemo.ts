import type { RiskLevel } from "../components/ui/RiskBadge";

export type DemoRiskRanking = {
  company: string;
  score: string;
  level: RiskLevel;
  contributingEvents: number;
};

export type DemoDomainExposure = {
  domain: string;
  exposedCompanies: number;
  highestRisk: RiskLevel;
};

export type DemoHopExposure = {
  hop: string;
  companies: number;
  description: string;
};

export type DemoEventContribution = {
  eventType: string;
  company: string;
  propagatedRisk: string;
  hop: number;
  initialRisk?: string;
  pathDependency?: string;
  distanceDecay?: string;
  path?: string[];
};

export const riskRankingDemo: DemoRiskRanking[] = [
  {
    company: "NVIDIA",
    score: "0.75",
    level: "CRITICAL",
    contributingEvents: 2,
  },
  {
    company: "TSMC",
    score: "0.61",
    level: "HIGH",
    contributingEvents: 2,
  },
  {
    company: "Samsung Electronics",
    score: "0.42",
    level: "MEDIUM",
    contributingEvents: 1,
  },
  {
    company: "Demo Company",
    score: "0.18",
    level: "LOW",
    contributingEvents: 1,
  },
];

export const domainExposureDemo: DemoDomainExposure[] = [
  {
    domain: "Semiconductors",
    exposedCompanies: 3,
    highestRisk: "CRITICAL",
  },
  {
    domain: "Electronics",
    exposedCompanies: 2,
    highestRisk: "HIGH",
  },
  {
    domain: "EV / Battery",
    exposedCompanies: 1,
    highestRisk: "MEDIUM",
  },
];

export const hopExposureDemo: DemoHopExposure[] = [
  {
    hop: "Hop 1",
    companies: 3,
    description: "Direct downstream exposure",
  },
  {
    hop: "Hop 2",
    companies: 2,
    description: "Indirect downstream exposure",
  },
  {
    hop: "Hop 3",
    companies: 1,
    description: "Extended downstream exposure",
  },
];

export const eventContributionDemo: DemoEventContribution[] = [
  {
    eventType: "FACILITY_OUTAGE",
    company: "NVIDIA",
    propagatedRisk: "0.75",
    hop: 1,
    initialRisk: "0.75",
    pathDependency: "1.00",
    distanceDecay: "1.00",
    path: ["TSMC", "NVIDIA"],
  },
  {
    eventType: "SUPPLY_DISRUPTION",
    company: "TSMC",
    propagatedRisk: "0.61",
    hop: 1,
  },
  {
    eventType: "REGULATION_CHANGE",
    company: "Samsung Electronics",
    propagatedRisk: "0.42",
    hop: 2,
  },
];
