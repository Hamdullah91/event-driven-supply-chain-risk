import type { RiskLevel } from "../components/ui/RiskBadge";

export type DemoCompany = {
  companyId: string;
  name: string;
  legalName: string;
  entityType: string;
  industryId: string;
  seedSource: string;

  riskScore: string;
  riskLevel: RiskLevel;
  contributingEventCount: number;

  facilities: string[];
  products: string[];
  materials: string[];
  technologies: string[];
};

export type DemoCompanyExposure = {
  id: string;
  eventType: string;
  severity: string;
  source: string;
  confidence: string;
  hopDistance: number;

  initialRisk: string;
  pathDependency: string;
  distanceDecay: string;
  propagatedRisk: string;

  path: string[];
};

export const companiesDemo: DemoCompany[] = [
  {
    companyId: "demo-nvidia",
    name: "NVIDIA",
    legalName: "NVIDIA Corporation",
    entityType: "Company",
    industryId: "semiconductor",
    seedSource: "Development fixture",

    riskScore: "0.75",
    riskLevel: "CRITICAL",
    contributingEventCount: 2,

    facilities: ["Demo NVIDIA Facility"],
    products: ["GPU"],
    materials: ["Silicon"],
    technologies: ["Advanced Computing"],
  },
  {
    companyId: "demo-tsmc",
    name: "TSMC",
    legalName: "Taiwan Semiconductor Manufacturing Company",
    entityType: "Company",
    industryId: "semiconductor",
    seedSource: "Development fixture",

    riskScore: "0.61",
    riskLevel: "HIGH",
    contributingEventCount: 2,

    facilities: ["Demo Fab"],
    products: ["Semiconductor Components"],
    materials: ["Silicon"],
    technologies: ["Semiconductor Manufacturing"],
  },
  {
    companyId: "demo-samsung",
    name: "Samsung Electronics",
    legalName: "Samsung Electronics Co., Ltd.",
    entityType: "Company",
    industryId: "electronics",
    seedSource: "Development fixture",

    riskScore: "0.42",
    riskLevel: "MEDIUM",
    contributingEventCount: 1,

    facilities: ["Demo Electronics Facility"],
    products: ["Memory"],
    materials: ["Silicon"],
    technologies: ["Memory Technology"],
  },
];

export const demoNvidiaExposures: DemoCompanyExposure[] = [
  {
    id: "demo-exposure-001",
    eventType: "FACILITY_OUTAGE",
    severity: "HIGH",
    source: "Development source",
    confidence: "94%",
    hopDistance: 1,

    initialRisk: "0.75",
    pathDependency: "1.00",
    distanceDecay: "1.00",
    propagatedRisk: "0.75",

    path: ["TSMC", "NVIDIA"],
  },
  {
    id: "demo-exposure-002",
    eventType: "SUPPLY_DISRUPTION",
    severity: "MEDIUM",
    source: "Development source",
    confidence: "87%",
    hopDistance: 2,

    initialRisk: "0.50",
    pathDependency: "0.90",
    distanceDecay: "0.70",
    propagatedRisk: "0.315",

    path: ["ASML", "TSMC", "NVIDIA"],
  },
];