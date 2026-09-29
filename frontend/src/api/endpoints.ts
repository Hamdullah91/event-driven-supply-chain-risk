import { apiRequest } from "./httpClient";
import type {
  AgentQueryResponseDto,
  BlastRadiusResponseDto,
  CompanyDetailDto,
  CompanyExposureResponseDto,
  CompanyListResponseDto,
  CompanyNetworkDto,
  DetailedHealthResponseDto,
  EntitySearchResponseDto,
  EventBlastRadiusResponseDto,
  EventDetailDto,
  EventListResponseDto,
  RiskHistoryResponseDto,
  RiskSummaryDto,
} from "./dtos";

function queryString(values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export type CompanyFilters = { limit?: number; offset?: number; search?: string; industryId?: string; entityType?: string };

export const api = {
  listCompanies(filters: CompanyFilters = {}, signal?: AbortSignal) {
    return apiRequest<CompanyListResponseDto>(`/companies${queryString({ limit: filters.limit ?? 100, offset: filters.offset ?? 0, search: filters.search, industry_id: filters.industryId, entity_type: filters.entityType })}`, { signal });
  },
  getCompany(companyId: string, signal?: AbortSignal) {
    return apiRequest<CompanyDetailDto>(`/companies/${encodeURIComponent(companyId)}`, { signal });
  },
  getCompanyNetwork(companyId: string, depth: 1 | 2 | 3, signal?: AbortSignal) {
    return apiRequest<CompanyNetworkDto>(`/companies/${encodeURIComponent(companyId)}/network?depth=${depth}`, { signal });
  },
  search(q: string, limit = 25, signal?: AbortSignal) {
    return apiRequest<EntitySearchResponseDto>(`/api/v1/search${queryString({ q, limit })}`, { signal });
  },
  listEvents(limit = 100, offset = 0, signal?: AbortSignal) {
    return apiRequest<EventListResponseDto>(`/api/v1/events${queryString({ limit, offset })}`, { signal });
  },
  getEvent(eventId: string, signal?: AbortSignal) {
    return apiRequest<EventDetailDto>(`/api/v1/events/${encodeURIComponent(eventId)}`, { signal });
  },
  getEventBlastRadius(eventId: string, maxHops: 1 | 2 | 3, signal?: AbortSignal) {
    return apiRequest<EventBlastRadiusResponseDto>(`/api/v1/events/${encodeURIComponent(eventId)}/blast-radius?max_hops=${maxHops}`, { signal });
  },
  getCompanyRisk(companyId: string, maxHops: 1 | 2 | 3, signal?: AbortSignal) {
    return apiRequest<RiskSummaryDto>(`/risk/${encodeURIComponent(companyId)}?max_hops=${maxHops}`, { signal });
  },
  getCompanyExposure(companyId: string, maxHops: 1 | 2 | 3, signal?: AbortSignal) {
    return apiRequest<CompanyExposureResponseDto>(`/risk/${encodeURIComponent(companyId)}/exposure?max_hops=${maxHops}`, { signal });
  },
  getCompanyBlastRadius(companyId: string, maxHops: 1 | 2 | 3, signal?: AbortSignal) {
    return apiRequest<BlastRadiusResponseDto>(`/risk/${encodeURIComponent(companyId)}/blast-radius?max_hops=${maxHops}`, { signal });
  },
  getRiskHistory(companyId: string, maxHops: 1 | 2 | 3, limit = 100, signal?: AbortSignal) {
    return apiRequest<RiskHistoryResponseDto>(`/risk/${encodeURIComponent(companyId)}/history${queryString({ max_hops: maxHops, limit })}`, { signal });
  },
  queryAgent(question: string, signal?: AbortSignal) {
    return apiRequest<AgentQueryResponseDto>("/api/v1/agent/query", { method: "POST", body: { question }, signal, timeoutMs: 30_000 });
  },
  getDetailedHealth(signal?: AbortSignal) {
    return apiRequest<DetailedHealthResponseDto>("/api/v1/health/detailed", { signal });
  },
};
