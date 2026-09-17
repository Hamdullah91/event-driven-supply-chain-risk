import type { RiskLevel } from "../components/ui/RiskBadge";

export type InspectorEntityType =
  | "Company"
  | "Facility"
  | "Material"
  | "Product"
  | "Technology"
  | "Country"
  | "Location"
  | "Event"
  | "Relationship";

export type InspectorField = {
  label: string;
  value: string;
};

export type InspectorEvidence = {
  source: string;
  confidence?: string;
  provenance?: string;
};

export type InspectorContext = {
  id: string;
  type: InspectorEntityType;
  name: string;
  subtitle?: string;

  riskLevel?: RiskLevel;
  riskScore?: string;

  fields: InspectorField[];

  evidence?: InspectorEvidence;
};

export const defaultInspectorContext: InspectorContext = {
  id: "demo-tsmc",
  type: "Company",
  name: "TSMC",
  subtitle: "Static Phase 1 development fixture — not a production selection",

  riskLevel: "HIGH",
  riskScore: "0.61",

  fields: [
    {
      label: "Entity ID",
      value: "demo-tsmc",
    },
    {
      label: "Industry",
      value: "Semiconductors",
    },
    {
      label: "Connected role",
      value: "Supplier / manufacturer",
    },
  ],

  evidence: {
    source: "Development source",
    confidence: "Not available",
    provenance: "Development fixture",
  },
};
