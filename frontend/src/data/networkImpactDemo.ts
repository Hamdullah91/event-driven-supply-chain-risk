export type DemoImpactLevel = "CRITICAL" | "HIGH" | "MEDIUM";
export type DemoImpactTone = "critical" | "high" | "medium";
export type DemoImpactOriginType = "Company" | "Event";

export type DemoImpactCompany = {
  id: string;
  position: "nvidia" | "demo-a" | "demo-b";
  company: string;
  hop: string;
  score: string;
  level: DemoImpactLevel;
  path: string[];
  pathDependency?: string;
  distanceDecay?: string;
};

export type DemoImpactPath = {
  id: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  tone: DemoImpactTone;
};

export type DemoImpactFixture = {
  origin: {
    id: string;
    type: DemoImpactOriginType;
    name: string;
    label: string;
  };
  companies: DemoImpactCompany[];
  paths: DemoImpactPath[];
  context: {
    initialRisk?: string;
    maxHops: "3";
    distanceDecay?: string;
    affectedCompanies: string;
  };
};

const sharedPaths: DemoImpactPath[] = [
  { id: "origin-hop1", x1: 500, y1: 300, x2: 660, y2: 300, tone: "critical" },
  { id: "hop1-hop2", x1: 690, y1: 300, x2: 750, y2: 180, tone: "high" },
  { id: "hop2-hop3", x1: 770, y1: 170, x2: 840, y2: 110, tone: "medium" },
];

const companyTsmcFixture: DemoImpactFixture = {
  origin: { id: "demo-tsmc", type: "Company", name: "TSMC", label: "TSMC transmission fixture" },
  companies: [
    {
      id: "demo-impact-nvidia",
      position: "nvidia",
      company: "NVIDIA",
      hop: "Hop 1",
      score: "0.75",
      level: "CRITICAL",
      path: ["TSMC", "NVIDIA"],
    },
    {
      id: "demo-impact-company-a",
      position: "demo-a",
      company: "Demo Company A",
      hop: "Hop 2",
      score: "0.525",
      level: "HIGH",
      path: ["TSMC", "NVIDIA", "Demo Company A"],
    },
    {
      id: "demo-impact-company-b",
      position: "demo-b",
      company: "Demo Company B",
      hop: "Hop 3",
      score: "0.368",
      level: "MEDIUM",
      path: ["TSMC", "NVIDIA", "Demo Company A", "Demo Company B"],
    },
  ],
  paths: sharedPaths,
  context: { maxHops: "3", affectedCompanies: "3" },
};

const eventFacilityOutageFixture: DemoImpactFixture = {
  origin: { id: "demo-event-001", type: "Event", name: "FACILITY_OUTAGE", label: "Facility outage development fixture" },
  companies: [
    {
      id: "demo-impact-nvidia",
      position: "nvidia",
      company: "NVIDIA",
      hop: "Hop 1",
      score: "0.75",
      level: "CRITICAL",
      path: ["FACILITY_OUTAGE", "TSMC", "NVIDIA"],
      pathDependency: "1.00",
      distanceDecay: "1.00",
    },
    {
      id: "demo-impact-company-a",
      position: "demo-a",
      company: "Demo Company A",
      hop: "Hop 2",
      score: "0.525",
      level: "HIGH",
      path: ["FACILITY_OUTAGE", "TSMC", "NVIDIA", "Demo Company A"],
      pathDependency: "1.00",
      distanceDecay: "0.70",
    },
    {
      id: "demo-impact-company-b",
      position: "demo-b",
      company: "Demo Company B",
      hop: "Hop 3",
      score: "0.368",
      level: "MEDIUM",
      path: ["FACILITY_OUTAGE", "TSMC", "NVIDIA", "Demo Company A", "Demo Company B"],
      pathDependency: "1.00",
      distanceDecay: "0.49",
    },
  ],
  paths: sharedPaths,
  context: { initialRisk: "0.75", maxHops: "3", distanceDecay: "0.70", affectedCompanies: "3" },
};

export const impactFixturesByOriginId: Record<string, DemoImpactFixture> = {
  "Company:demo-tsmc": companyTsmcFixture,
  "Event:demo-event-001": eventFacilityOutageFixture,
};

export function getImpactFixture(
  originType: DemoImpactOriginType | undefined,
  originId: string | undefined,
): DemoImpactFixture | undefined {
  if (!originType || !originId) return undefined;
  return impactFixturesByOriginId[`${originType}:${originId}`];
}

export const networkImpactDemo = companyTsmcFixture;
