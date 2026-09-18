import type { InspectorContext } from "./inspectorDemo";

export type SearchDemoResult = {
  id: string;
  label: string;
  type: InspectorContext["type"];
  secondary: string;
  context: InspectorContext;
};

export const searchDemoResults: SearchDemoResult[] = [
  {
    id: "search-company-tsmc",
    label: "TSMC",
    type: "Company",
    secondary: "Semiconductors",
    context: {
      id: "demo-tsmc",
      type: "Company",
      name: "TSMC",
      subtitle: "Development search fixture",
      riskLevel: "HIGH",
      riskScore: "0.61",
      fields: [
        { label: "Entity ID", value: "demo-tsmc" },
        { label: "Industry", value: "Semiconductors" },
      ],
      evidence: {
        availability: "PARTIAL",
        source: "Development source",
        provenance: "Development fixture",
      },
    },
  },
  {
    id: "search-company-nvidia",
    label: "NVIDIA",
    type: "Company",
    secondary: "Semiconductors",
    context: {
      id: "demo-nvidia",
      type: "Company",
      name: "NVIDIA",
      subtitle: "Development search fixture",
      riskLevel: "CRITICAL",
      riskScore: "0.75",
      fields: [
        { label: "Entity ID", value: "demo-nvidia" },
        { label: "Industry", value: "Semiconductors" },
      ],
      evidence: {
        availability: "PARTIAL",
        source: "Development source",
        provenance: "Development fixture",
      },
    },
  },
  {
    id: "search-facility",
    label: "Demo Fab",
    type: "Facility",
    secondary: "Related company: TSMC",
    context: {
      id: "demo-facility-1",
      type: "Facility",
      name: "Demo Fab",
      subtitle: "Development search fixture",
      relatedCompanyId: "demo-tsmc",
      fields: [
        { label: "Facility ID", value: "demo-facility-1" },
        { label: "Related company", value: "TSMC" },
      ],
      evidence: { availability: "UNAVAILABLE" },
    },
  },
  {
    id: "search-event",
    label: "FACILITY_OUTAGE",
    type: "Event",
    secondary: "Development event · TSMC",
    context: {
      id: "demo-event-001",
      type: "Event",
      name: "FACILITY_OUTAGE",
      subtitle: "Development search fixture",
      fields: [
        { label: "Severity", value: "HIGH" },
        { label: "Affected entity", value: "TSMC" },
        { label: "Classifier confidence", value: "94%" },
      ],
      evidence: {
        availability: "PARTIAL",
        source: "Development source",
        provenance: "Development fixture",
      },
    },
  },
  {
    id: "search-material",
    label: "Silicon",
    type: "Material",
    secondary: "Material",
    context: {
      id: "demo-material-1",
      type: "Material",
      name: "Silicon",
      subtitle: "Development search fixture",
      fields: [{ label: "Entity type", value: "Material" }],
      evidence: { availability: "UNAVAILABLE" },
    },
  },
];
