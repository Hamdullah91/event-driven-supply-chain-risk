import type { RiskLevel } from "../components/ui/RiskBadge";

export type InspectorEntityType =
  | "Company"
  | "Facility"
  | "Material"
  | "Product"
  | "Technology"
  | "Industry"
  | "Country"
  | "Location"
  | "Event"
  | "Relationship";

export type InspectorField = {
  label: string;
  value: string;
};

export type EvidenceAvailability = "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";

export type InspectorEvidence = {
  availability: EvidenceAvailability;
  source?: string;
  confidence?: string;
  provenance?: string;
  excerpt?: string;
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
  path?: string[];
  relatedCompanyId?: string;
};

export const defaultInspectorContext: InspectorContext = {
  id: "demo-tsmc",
  type: "Company",
  name: "TSMC",
  subtitle: "Static Phase 1 development fixture — not a production selection",
  riskLevel: "HIGH",
  riskScore: "0.61",
  fields: [
    { label: "Entity ID", value: "demo-tsmc" },
    { label: "Industry", value: "Semiconductors" },
    { label: "Connected role", value: "Supplier / manufacturer" },
  ],
  evidence: {
    availability: "PARTIAL",
    source: "Development source",
    confidence: "Not available",
    provenance: "Development fixture",
    excerpt: "Not available",
  },
};
