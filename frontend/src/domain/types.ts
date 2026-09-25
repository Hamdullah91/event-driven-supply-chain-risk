export type EntityType =
  | "Company"
  | "Facility"
  | "Product"
  | "Material"
  | "Technology"
  | "Industry"
  | "Location"
  | "Country"
  | "Event"
  | "Unknown";

export type EventType =
  | "SUPPLY_DISRUPTION"
  | "REGULATION_CHANGE"
  | "FACILITY_OUTAGE"
  | "TECHNOLOGY_EMBARGO"
  | "TRADE_POLICY_CHANGE"
  | "QUOTA_CHANGE";

export type EventSeverity = "unknown" | "low" | "medium" | "high" | "critical";
export type RiskLevel = "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type EvidenceAvailability = "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";
export type HopDepth = 1 | 2 | 3;

export type EntityRef = {
  id: string;
  type: EntityType;
  name: string;
};

export type EvidenceRef = {
  availability: EvidenceAvailability;
  source?: string;
  sourceUrl?: string;
  timestamp?: string;
  confidence?: number;
  eventId?: string;
};

export type ProvenanceRef = EvidenceRef;

export type CompanySummary = {
  companyId: string;
  name: string;
  legalName?: string;
  entityType?: string;
  industryId?: string;
};

export type Company = CompanySummary & {
  seedSource?: string;
  facilities: string[];
  products: string[];
  materials: string[];
  technologies: string[];
};

export type Facility = EntityRef;
export type Product = EntityRef;
export type Material = EntityRef;
export type Technology = EntityRef;
export type Industry = EntityRef;
export type Location = EntityRef;
export type Country = EntityRef;

export type SupplyChainEvent = {
  eventId: string;
  eventType: EventType | string;
  timestamp: string;
  severity: EventSeverity;
  confidence?: number;
  description?: string;
  source: string;
  sourceUrl?: string;
  affectedEntities: EntityRef[];
  evidence: EvidenceRef;
};

export type GraphNode = {
  id: string;
  entityId: string;
  entityType: EntityType;
  label: string;
  metadata: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  type: string;
  sourceId: string;
  targetId: string;
  directed: true;
  weight?: number;
  weightSource?: string;
  confidence?: number;
  evidence?: EvidenceRef;
  metadata: Record<string, unknown>;
};

export type StructureGraph = {
  focus: EntityRef;
  depth: HopDepth;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type PathEntity = {
  id?: string;
  type?: EntityType;
  name: string;
};

export type ImpactOrigin = {
  kind: "Company" | "Event";
  id: string;
  name: string;
};

export type RiskTrace = {
  hop: number;
  initialRisk?: number;
  combinedPathDependency?: number;
  distanceDecay?: number;
  propagatedRisk?: number;
};

export type ImpactPath = {
  pathId: string;
  nodes: PathEntity[];
  trace: RiskTrace;
};

export type ImpactTarget = {
  company: EntityRef;
  hop: number;
  riskLevel?: RiskLevel;
  propagatedRisk?: number;
  transmissionFactor?: number;
  pathId: string;
};

export type ImpactAnalysis = {
  origin: ImpactOrigin;
  maxHops: HopDepth;
  targets: ImpactTarget[];
  paths: ImpactPath[];
  metricType: "PROPAGATED_RISK" | "TRANSMISSION_FACTOR";
};

export type CompanyRiskSummary = {
  companyId: string;
  currentRisk: number;
  riskLevel: RiskLevel;
  contributingEventCount: number;
  maxHops: HopDepth;
};

export type ExposureContribution = {
  exposureId: string;
  eventId: string;
  eventType?: string;
  severity: EventSeverity;
  sourceEntity: EntityRef;
  targetCompany: EntityRef;
  hop: number;
  initialRisk: number;
  combinedPathDependency: number;
  distanceDecay: number;
  propagatedRisk: number;
  path: PathEntity[];
  confidence?: number;
  source?: string;
  timestamp?: string;
  description?: string;
  evidence: EvidenceRef;
};

export type RiskHistoryPoint = {
  timestamp: string;
  currentRisk: number;
  riskLevel: RiskLevel;
  eventId: string;
};

export type RiskHistory = {
  companyId: string;
  maxHops: HopDepth;
  points: RiskHistoryPoint[];
  count: number;
  semantics: "EVENT_DERIVED_RECONSTRUCTION";
};

export type SearchResult = {
  entity: EntityRef;
  metadata: Record<string, unknown>;
};

export type AgentEntity = { name: string; id?: string; type?: EntityType };
export type AgentPath = { names: string[]; pathId?: string };

export type AgentAnswer = {
  answer: string;
  evidenceStatus: string;
  entities: AgentEntity[];
  paths: AgentPath[];
  hopCounts: number[];
  eventRefs: string[];
  warnings: string[];
  provenance: ProvenanceRef[];
};

export type ServiceHealth = { status: string; detail?: string };
export type SystemHealth = { status: string; services: Record<string, ServiceHealth> };

export type RiskStreamMessage =
  | { type: "connection.established"; message: string }
  | {
      type: "risk.updated";
      eventId?: string;
      companyId: string;
      currentRisk: number;
      riskLevel: RiskLevel;
      contributingEventCount: number;
      maxHops: HopDepth;
      triggerEventType?: string;
      timestamp: string;
    };
