export type EvidenceAvailabilityDto = "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";

export type CompanySummaryDto = {
  company_id: string;
  name: string;
  legal_name?: string | null;
  entity_type?: string | null;
  industry_id?: string | null;
};

export type CompanyListResponseDto = {
  companies: CompanySummaryDto[];
  count: number;
  limit: number;
  offset: number;
};

export type CompanyDetailDto = CompanySummaryDto & {
  seed_source?: string | null;
  facilities: string[];
  products: string[];
  materials: string[];
  technologies: string[];
};

export type EntitySearchResultDto = {
  label: string;
  entity_id: string;
  name: string;
  properties: Record<string, unknown>;
};
export type EntitySearchResponseDto = { query: string; results: EntitySearchResultDto[]; count: number };

export type GraphNodeDto = { id: string; label: string; name: string; properties: Record<string, unknown> };
export type GraphRelationshipDto = {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  properties: Record<string, unknown>;
  evidence_status: EvidenceAvailabilityDto;
};
export type CompanyNetworkDto = { company_id: string; depth: 1 | 2 | 3; nodes: GraphNodeDto[]; relationships: GraphRelationshipDto[] };

export type EventDetailDto = {
  event_id: string;
  event_type: string;
  source: string;
  timestamp: unknown;
  entity_id?: string | null;
  severity: "unknown" | "low" | "medium" | "high" | "critical";
  payload: Record<string, unknown>;
  created_at?: unknown;
  confidence?: number | null;
  description?: string | null;
  source_url?: string | null;
  evidence_status: EvidenceAvailabilityDto;
};
export type EventListResponseDto = { events: EventDetailDto[]; count: number; limit: number; offset: number };

export type RiskSummaryDto = {
  company_id: string;
  risk_score: number;
  risk_level: string;
  contributing_event_count: number;
  max_hops: 1 | 2 | 3;
};

export type RiskHistoryPointDto = { timestamp: unknown; risk_score: number; risk_level: string; event_id: string };
export type RiskHistoryResponseDto = { company_id: string; max_hops: 1 | 2 | 3; points: RiskHistoryPointDto[]; count: number };

export type BlastRadiusCompanyDto = {
  company_id: string;
  company_name: string;
  hop_distance: 1 | 2 | 3;
  transmission_factor: number;
  path: Record<string, unknown>[];
};
export type BlastRadiusResponseDto = {
  company_id: string;
  max_hops: 1 | 2 | 3;
  affected_company_count: number;
  hop_counts: Record<string, number>;
  companies: BlastRadiusCompanyDto[];
};

export type EventBlastRadiusCompanyDto = {
  company_id: string;
  company_name: string;
  origin_company_id: string;
  origin_company_name: string;
  hop_distance: 0 | 1 | 2 | 3;
  initial_risk: number;
  path_dependency: number;
  distance_decay: number;
  propagated_risk: number;
  path: Record<string, unknown>[];
};
export type EventBlastRadiusResponseDto = {
  event_id: string;
  event_type?: string | null;
  severity?: "unknown" | "low" | "medium" | "high" | "critical" | null;
  max_hops: 1 | 2 | 3;
  affected_company_count: number;
  hop_counts: Record<string, number>;
  companies: EventBlastRadiusCompanyDto[];
};

export type EventExposureDto = {
  event_id: string;
  event_type?: string | null;
  severity: "unknown" | "low" | "medium" | "high" | "critical";
  timestamp?: unknown;
  source?: string | null;
  confidence?: number | null;
  description?: string | null;
  affected_company_id: string;
  affected_company_name: string;
  hop_distance: 0 | 1 | 2 | 3;
  initial_risk: number;
  path_dependency: number;
  distance_decay: number;
  propagated_risk: number;
  path: Record<string, unknown>[];
  evidence_status: EvidenceAvailabilityDto;
};
export type CompanyExposureResponseDto = { company_id: string; event_count: number; exposures: EventExposureDto[] };

export type EvidenceProvenanceDto = {
  source?: string | null;
  timestamp?: string | null;
  confidence?: number | null;
  event_id?: string | null;
  availability: EvidenceAvailabilityDto;
};
export type AgentQueryResponseDto = {
  answer: string;
  evidence_status: string;
  affected_entities: string[];
  dependency_paths: string[][];
  hop_counts: number[];
  event_refs: string[];
  path_ids: string[];
  warnings: string[];
  provenance: EvidenceProvenanceDto[];
};

export type ServiceHealthDto = { status: string; detail?: string | null };
export type DetailedHealthResponseDto = { status: string; services: Record<string, ServiceHealthDto> };

export type ConnectionEstablishedDto = { type: "connection.established"; message: string };
export type RiskUpdatedDto = {
  type: "risk.updated";
  event_id?: string | null;
  company_id: string;
  risk_score: number;
  risk_level: string;
  contributing_event_count: number;
  max_hops: 1 | 2 | 3;
  trigger_event_type?: string | null;
  timestamp: string;
};
