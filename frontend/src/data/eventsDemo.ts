export type EventSeverity = "MEDIUM" | "HIGH" | "CRITICAL";

export type DemoEvent = {
  id: string;
  type: string;
  severity: EventSeverity;
  confidence: number;
  timestamp: string;
  source: string;
  title: string;
  description: string;
  affectedEntities: string[];
  location?: string;
  evidence: string;
};

export const eventsDemo: DemoEvent[] = [
  {
    id: "demo-event-001",
    type: "FACILITY_OUTAGE",
    severity: "HIGH",
    confidence: 0.94,
    timestamp: "Fixture timestamp · 08:42 UTC",
    source: "Development source",
    title: "Manufacturing facility disruption detected",
    description:
      "Development-only event used to validate the Phase 1 Events workspace and its master-detail information hierarchy.",
    affectedEntities: ["TSMC", "Demo Facility"],
    location: "Fixture location not supplied",
    evidence: "Development evidence placeholder",
  },
  {
    id: "demo-event-002",
    type: "SUPPLY_DISRUPTION",
    severity: "CRITICAL",
    confidence: 0.89,
    timestamp: "Fixture timestamp · 07:16 UTC",
    source: "Development source",
    title: "Supplier disruption affecting semiconductor context",
    description:
      "This example demonstrates a high-priority disruption without representing a live backend event.",
    affectedEntities: ["Samsung Electronics"],
    location: "Fixture location not supplied",
    evidence: "Development evidence placeholder",
  },
  {
    id: "demo-event-003",
    type: "REGULATION_CHANGE",
    severity: "MEDIUM",
    confidence: 0.82,
    timestamp: "Fixture timestamp · 06:04 UTC",
    source: "Development source",
    title: "Regulatory change detected in monitored context",
    description:
      "Development-only classifier-facing example for validating event metadata and evidence presentation.",
    affectedEntities: ["Semiconductor domain"],
    location: "Fixture location not supplied",
    evidence: "Development evidence placeholder",
  },
];
