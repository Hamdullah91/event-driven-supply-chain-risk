import type { CompanyFilters } from "../api/endpoints";

export const queryKeys = {
  companies: (filters: CompanyFilters = {}) => ["companies", filters] as const,
  company: (companyId: string) => ["company", companyId] as const,
  companyNetwork: (companyId: string, depth: number) => ["company-network", companyId, depth] as const,
  search: (query: string, limit: number) => ["search", query, limit] as const,
  events: (limit = 100, offset = 0) => ["events", limit, offset] as const,
  event: (eventId: string) => ["event", eventId] as const,
  eventBlastRadius: (eventId: string, maxHops: number) => ["event-blast-radius", eventId, maxHops] as const,
  companyRisk: (companyId: string, maxHops: number) => ["company-risk", companyId, maxHops] as const,
  companyExposure: (companyId: string, maxHops: number) => ["company-exposure", companyId, maxHops] as const,
  companyBlastRadius: (companyId: string, maxHops: number) => ["company-blast-radius", companyId, maxHops] as const,
  riskHistory: (companyId: string, maxHops: number, limit: number) => ["risk-history", companyId, maxHops, limit] as const,
  health: () => ["health", "detailed"] as const,
};
