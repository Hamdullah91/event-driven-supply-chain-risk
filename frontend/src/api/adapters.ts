import type {
  AgentQueryResponseDto,
  BlastRadiusResponseDto,
  CompanyDetailDto,
  CompanyExposureResponseDto,
  CompanyNetworkDto,
  CompanySummaryDto,
  DetailedHealthResponseDto,
  EntitySearchResultDto,
  EventBlastRadiusResponseDto,
  EventDetailDto,
  RiskHistoryResponseDto,
  RiskSummaryDto,
  RiskUpdatedDto,
  ConnectionEstablishedDto,
} from "./dtos";
import type {
  AgentAnswer,
  Company,
  CompanyRiskSummary,
  CompanySummary,
  EntityRef,
  EntityType,
  EventType,
  ExposureContribution,
  ImpactAnalysis,
  PathEntity,
  RiskHistory,
  RiskLevel,
  RiskStreamMessage,
  SearchResult,
  StructureGraph,
  SupplyChainEvent,
  SystemHealth,
} from "../domain/types";

const EVENT_ALIASES: Record<string, EventType> = {
  SUPPLY_DISRUPTION: "SUPPLY_DISRUPTION",
  REGULATION_CHANGE: "REGULATION_CHANGE",
  REGULATORY_CHANGE: "REGULATION_CHANGE",
  FACILITY_OUTAGE: "FACILITY_OUTAGE",
  FACILITY_SHUTDOWN: "FACILITY_OUTAGE",
  TECHNOLOGY_EMBARGO: "TECHNOLOGY_EMBARGO",
  TRADE_POLICY_CHANGE: "TRADE_POLICY_CHANGE",
  QUOTA_CHANGE: "QUOTA_CHANGE",
};

const ENTITY_TYPES: EntityType[] = ["Company", "Facility", "Product", "Material", "Technology", "Industry", "Location", "Country", "Event"];
const RISK_LEVELS: RiskLevel[] = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export function normalizeEventType(value: string): EventType | string {
  const key = value.trim().toUpperCase();
  return EVENT_ALIASES[key] ?? key;
}

export function normalizeEntityType(label: string): EntityType {
  const found = ENTITY_TYPES.find((candidate) => candidate.toLowerCase() === label.trim().toLowerCase());
  return found ?? "Unknown";
}

export function normalizeRiskLevel(value: string): RiskLevel {
  const normalized = value.trim().toUpperCase();
  return RISK_LEVELS.includes(normalized as RiskLevel) ? normalized as RiskLevel : "NONE";
}

function optionalString(value: unknown): string | undefined {
  if (value === null || value === undefined || value === "") return undefined;
  return String(value);
}

function toTimestamp(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

function entityIdFromNode(label: EntityType, fallbackId: string, properties: Record<string, unknown>): string {
  const keys: Partial<Record<EntityType, string>> = {
    Company: "company_id",
    Facility: "facility_id",
    Product: "product_id",
    Material: "material_id",
    Technology: "technology_id",
    Industry: "industry_id",
    Location: "location_id",
    Country: "country_id",
    Event: "event_id",
  };
  const key = keys[label];
  const explicit = key ? properties[key] : undefined;
  if (typeof explicit === "string" && explicit) return explicit;
  const separator = fallbackId.indexOf(":");
  return separator >= 0 ? fallbackId.slice(separator + 1) : fallbackId;
}

function pathEntities(path: Record<string, unknown>[]): PathEntity[] {
  return path.map((item, index) => {
    const name = optionalString(item.name) ?? optionalString(item.company_name) ?? optionalString(item.label) ?? `Path node ${index + 1}`;
    const rawType = optionalString(item.type) ?? optionalString(item.entity_type) ?? optionalString(item.label_type);
    const id = optionalString(item.company_id) ?? optionalString(item.entity_id) ?? optionalString(item.id);
    return { name, ...(id ? { id } : {}), ...(rawType ? { type: normalizeEntityType(rawType) } : {}) };
  });
}

function pathId(prefix: string, path: PathEntity[]): string {
  return `${prefix}:${path.map((item) => item.id ?? item.name).join(">")}`;
}

function affectedEntitiesFromPayload(payload: Record<string, unknown>): EntityRef[] {
  const value = payload.affected_entities;
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const record = item as Record<string, unknown>;
    const id = optionalString(record.id) ?? optionalString(record.entity_id);
    const name = optionalString(record.name);
    const type = optionalString(record.type) ?? optionalString(record.entity_type);
    if (!id || !name || !type) return [];
    return [{ id, name, type: normalizeEntityType(type) }];
  });
}

export function adaptCompanySummary(dto: CompanySummaryDto): CompanySummary {
  return {
    companyId: dto.company_id,
    name: dto.name,
    ...(dto.legal_name ? { legalName: dto.legal_name } : {}),
    ...(dto.entity_type ? { entityType: dto.entity_type } : {}),
    ...(dto.industry_id ? { industryId: dto.industry_id } : {}),
  };
}

export function adaptCompany(dto: CompanyDetailDto): Company {
  return {
    ...adaptCompanySummary(dto),
    ...(dto.seed_source ? { seedSource: dto.seed_source } : {}),
    facilities: dto.facilities ?? [],
    products: dto.products ?? [],
    materials: dto.materials ?? [],
    technologies: dto.technologies ?? [],
  };
}

export function adaptSearchResult(dto: EntitySearchResultDto): SearchResult {
  return { entity: { id: dto.entity_id, type: normalizeEntityType(dto.label), name: dto.name }, metadata: dto.properties ?? {} };
}

export function adaptEvent(dto: EventDetailDto): SupplyChainEvent {
  return {
    eventId: dto.event_id,
    eventType: normalizeEventType(dto.event_type),
    timestamp: toTimestamp(dto.timestamp),
    severity: dto.severity,
    ...(dto.confidence === null || dto.confidence === undefined ? {} : { confidence: dto.confidence }),
    ...(dto.description ? { description: dto.description } : {}),
    source: dto.source,
    ...(dto.source_url ? { sourceUrl: dto.source_url } : {}),
    affectedEntities: affectedEntitiesFromPayload(dto.payload ?? {}),
    evidence: {
      availability: dto.evidence_status,
      source: dto.source,
      ...(dto.source_url ? { sourceUrl: dto.source_url } : {}),
      ...(dto.confidence === null || dto.confidence === undefined ? {} : { confidence: dto.confidence }),
      eventId: dto.event_id,
    },
  };
}

export function adaptCompanyNetwork(dto: CompanyNetworkDto): StructureGraph {
  const nodes = dto.nodes.map((node) => {
    const entityType = normalizeEntityType(node.label);
    return { id: node.id, entityId: entityIdFromNode(entityType, node.id, node.properties ?? {}), entityType, label: node.name, metadata: node.properties ?? {} };
  });
  const focusNode = nodes.find((node) => node.entityType === "Company" && node.entityId === dto.company_id)
    ?? nodes.find((node) => node.entityId === dto.company_id);
  return {
    focus: { id: dto.company_id, type: focusNode?.entityType ?? "Company", name: focusNode?.label ?? dto.company_id },
    depth: dto.depth,
    nodes,
    edges: dto.relationships.map((relationship) => ({
      id: relationship.id,
      type: relationship.relationship_type,
      sourceId: relationship.source,
      targetId: relationship.target,
      directed: true as const,
      ...(typeof relationship.properties?.dependency_weight === "number" ? { weight: relationship.properties.dependency_weight } : {}),
      ...(typeof relationship.properties?.weight_source === "string" ? { weightSource: relationship.properties.weight_source } : {}),
      ...(typeof relationship.properties?.confidence === "number" ? { confidence: relationship.properties.confidence } : {}),
      evidence: { availability: relationship.evidence_status, source: optionalString(relationship.properties?.source) },
      metadata: relationship.properties ?? {},
    })),
  };
}

export function adaptCompanyRisk(dto: RiskSummaryDto): CompanyRiskSummary {
  return { companyId: dto.company_id, currentRisk: dto.risk_score, riskLevel: normalizeRiskLevel(dto.risk_level), contributingEventCount: dto.contributing_event_count, maxHops: dto.max_hops };
}

export function adaptCompanyBlastRadius(dto: BlastRadiusResponseDto): ImpactAnalysis {
  const paths = dto.companies.map((company) => {
    const nodes = pathEntities(company.path);
    const id = pathId(`company:${dto.company_id}:${company.company_id}`, nodes);
    return { pathId: id, nodes, trace: { hop: company.hop_distance } };
  });
  return {
    origin: { kind: "Company", id: dto.company_id, name: dto.company_id },
    maxHops: dto.max_hops,
    metricType: "TRANSMISSION_FACTOR",
    paths,
    targets: dto.companies.map((company, index) => ({
      company: { id: company.company_id, type: "Company", name: company.company_name },
      hop: company.hop_distance,
      transmissionFactor: company.transmission_factor,
      pathId: paths[index].pathId,
    })),
  };
}

export function adaptEventBlastRadius(dto: EventBlastRadiusResponseDto): ImpactAnalysis {
  const paths = dto.companies.map((company) => {
    const nodes = pathEntities(company.path);
    return {
      pathId: pathId(`event:${dto.event_id}:${company.company_id}`, nodes),
      nodes,
      trace: {
        hop: company.hop_distance,
        initialRisk: company.initial_risk,
        combinedPathDependency: company.path_dependency,
        distanceDecay: company.distance_decay,
        propagatedRisk: company.propagated_risk,
      },
    };
  });
  return {
    origin: { kind: "Event", id: dto.event_id, name: normalizeEventType(dto.event_type ?? "Event") },
    maxHops: dto.max_hops,
    metricType: "PROPAGATED_RISK",
    paths,
    targets: dto.companies.map((company, index) => ({
      company: { id: company.company_id, type: "Company", name: company.company_name },
      hop: company.hop_distance,
      propagatedRisk: company.propagated_risk,
      pathId: paths[index].pathId,
    })),
  };
}

export function adaptCompanyExposure(dto: CompanyExposureResponseDto): ExposureContribution[] {
  return dto.exposures.map((exposure) => {
    const path = pathEntities(exposure.path);
    const targetName = path.at(-1)?.name ?? dto.company_id;
    const exposureId = pathId(`exposure:${exposure.event_id}:${dto.company_id}:${exposure.hop_distance}`, path);
    return {
      exposureId,
      eventId: exposure.event_id,
      ...(exposure.event_type ? { eventType: normalizeEventType(exposure.event_type) } : {}),
      severity: exposure.severity,
      sourceEntity: { id: exposure.affected_company_id, type: "Company", name: exposure.affected_company_name },
      targetCompany: { id: dto.company_id, type: "Company", name: targetName },
      hop: exposure.hop_distance,
      initialRisk: exposure.initial_risk,
      combinedPathDependency: exposure.path_dependency,
      distanceDecay: exposure.distance_decay,
      propagatedRisk: exposure.propagated_risk,
      path,
      ...(exposure.confidence === null || exposure.confidence === undefined ? {} : { confidence: exposure.confidence }),
      ...(exposure.source ? { source: exposure.source } : {}),
      ...(exposure.timestamp === null || exposure.timestamp === undefined ? {} : { timestamp: toTimestamp(exposure.timestamp) }),
      ...(exposure.description ? { description: exposure.description } : {}),
      evidence: { availability: exposure.evidence_status, ...(exposure.source ? { source: exposure.source } : {}), eventId: exposure.event_id },
    };
  });
}

export function adaptRiskHistory(dto: RiskHistoryResponseDto): RiskHistory {
  return {
    companyId: dto.company_id,
    maxHops: dto.max_hops,
    count: dto.count,
    semantics: "EVENT_DERIVED_RECONSTRUCTION",
    points: dto.points.map((point) => ({ timestamp: toTimestamp(point.timestamp), currentRisk: point.risk_score, riskLevel: normalizeRiskLevel(point.risk_level), eventId: point.event_id })),
  };
}

export function adaptAgentAnswer(dto: AgentQueryResponseDto): AgentAnswer {
  return {
    answer: dto.answer,
    evidenceStatus: dto.evidence_status,
    entities: dto.affected_entities.map((name) => ({ name })),
    paths: dto.dependency_paths.map((names, index) => ({ names, ...(dto.path_ids[index] ? { pathId: dto.path_ids[index] } : {}) })),
    hopCounts: dto.hop_counts,
    eventRefs: dto.event_refs,
    warnings: dto.warnings,
    provenance: dto.provenance.map((item) => ({
      availability: item.availability,
      ...(item.source ? { source: item.source } : {}),
      ...(item.timestamp ? { timestamp: item.timestamp } : {}),
      ...(item.confidence === null || item.confidence === undefined ? {} : { confidence: item.confidence }),
      ...(item.event_id ? { eventId: item.event_id } : {}),
    })),
  };
}

export function adaptSystemHealth(dto: DetailedHealthResponseDto): SystemHealth {
  return { status: dto.status, services: Object.fromEntries(Object.entries(dto.services).map(([key, value]) => [key, { status: value.status, ...(value.detail ? { detail: value.detail } : {}) }])) };
}

export function adaptRiskStreamMessage(dto: ConnectionEstablishedDto | RiskUpdatedDto): RiskStreamMessage {
  if (dto.type === "connection.established") return dto;
  return {
    type: "risk.updated",
    ...(dto.event_id ? { eventId: dto.event_id } : {}),
    companyId: dto.company_id,
    currentRisk: dto.risk_score,
    riskLevel: normalizeRiskLevel(dto.risk_level),
    contributingEventCount: dto.contributing_event_count,
    maxHops: dto.max_hops,
    ...(dto.trigger_event_type ? { triggerEventType: normalizeEventType(dto.trigger_event_type) } : {}),
    timestamp: dto.timestamp,
  };
}
