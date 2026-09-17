export type DemoImpactLevel = "CRITICAL" | "HIGH" | "MEDIUM";
export type DemoImpactTone = "critical" | "high" | "medium";

export type DemoImpactCompany = {
  id: string;
  position: "nvidia" | "demo-a" | "demo-b";
  company: string;
  hop: string;
  score: string;
  level: DemoImpactLevel;
};

export type DemoImpactPath = {
  id: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  tone: DemoImpactTone;
};

export const networkImpactDemo = {
  origin: {
    company: "TSMC",
    label: "TSMC disruption",
  },
  companies: [
    {
      id: "demo-impact-nvidia",
      position: "nvidia",
      company: "NVIDIA",
      hop: "Hop 1",
      score: "0.75",
      level: "CRITICAL",
    },
    {
      id: "demo-impact-company-a",
      position: "demo-a",
      company: "Demo Company A",
      hop: "Hop 2",
      score: "0.525",
      level: "HIGH",
    },
    {
      id: "demo-impact-company-b",
      position: "demo-b",
      company: "Demo Company B",
      hop: "Hop 3",
      score: "0.368",
      level: "MEDIUM",
    },
  ] satisfies DemoImpactCompany[],
  paths: [
    {
      id: "origin-hop1",
      x1: 500,
      y1: 300,
      x2: 660,
      y2: 300,
      tone: "critical",
    },
    {
      id: "hop1-hop2",
      x1: 690,
      y1: 300,
      x2: 750,
      y2: 180,
      tone: "high",
    },
    {
      id: "hop2-hop3",
      x1: 770,
      y1: 170,
      x2: 840,
      y2: 110,
      tone: "medium",
    },
  ] satisfies DemoImpactPath[],
  context: {
    initialRisk: "0.75",
    maxHops: "3",
    distanceDecay: "0.70",
    affectedCompanies: "3",
  },
} as const;
