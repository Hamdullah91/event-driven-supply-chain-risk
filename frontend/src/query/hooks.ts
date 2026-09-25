import { useMutation, useQuery } from "@tanstack/react-query";
import { api, type CompanyFilters } from "../api/endpoints";
import {
  adaptAgentAnswer,
  adaptCompany,
  adaptCompanyBlastRadius,
  adaptCompanyExposure,
  adaptCompanyNetwork,
  adaptCompanyRisk,
  adaptCompanySummary,
  adaptEvent,
  adaptEventBlastRadius,
  adaptRiskHistory,
  adaptSearchResult,
  adaptSystemHealth,
} from "../api/adapters";
import { queryKeys } from "./queryKeys";

export function useCompanies(filters: CompanyFilters = {}) {
  return useQuery({
    queryKey: queryKeys.companies(filters),
    queryFn: async ({ signal }) => {
      const dto = await api.listCompanies(filters, signal);
      return { companies: dto.companies.map(adaptCompanySummary), count: dto.count, limit: dto.limit, offset: dto.offset };
    },
  });
}

export function useCompany(companyId: string | undefined) {
  return useQuery({ queryKey: queryKeys.company(companyId ?? ""), queryFn: ({ signal }) => api.getCompany(companyId!, signal).then(adaptCompany), enabled: Boolean(companyId) });
}

export function useCompanyNetwork(companyId: string | undefined, depth: 1 | 2 | 3) {
  return useQuery({ queryKey: queryKeys.companyNetwork(companyId ?? "", depth), queryFn: ({ signal }) => api.getCompanyNetwork(companyId!, depth, signal).then(adaptCompanyNetwork), enabled: Boolean(companyId) });
}

export function useEntitySearch(query: string, limit = 25) {
  const normalized = query.trim();
  return useQuery({
    queryKey: queryKeys.search(normalized, limit),
    queryFn: async ({ signal }) => (await api.search(normalized, limit, signal)).results.map(adaptSearchResult),
    enabled: normalized.length >= 2,
    staleTime: 60_000,
  });
}

export function useEvents(limit = 100, offset = 0) {
  return useQuery({ queryKey: queryKeys.events(limit, offset), queryFn: async ({ signal }) => { const dto = await api.listEvents(limit, offset, signal); return { events: dto.events.map(adaptEvent), count: dto.count, limit: dto.limit, offset: dto.offset }; } });
}

export function useEvent(eventId: string | undefined) {
  return useQuery({ queryKey: queryKeys.event(eventId ?? ""), queryFn: ({ signal }) => api.getEvent(eventId!, signal).then(adaptEvent), enabled: Boolean(eventId) });
}

export function useEventImpact(eventId: string | undefined, maxHops: 1 | 2 | 3) {
  return useQuery({ queryKey: queryKeys.eventBlastRadius(eventId ?? "", maxHops), queryFn: ({ signal }) => api.getEventBlastRadius(eventId!, maxHops, signal).then(adaptEventBlastRadius), enabled: Boolean(eventId) });
}

export function useCompanyRisk(companyId: string | undefined, maxHops: 1 | 2 | 3) {
  return useQuery({ queryKey: queryKeys.companyRisk(companyId ?? "", maxHops), queryFn: ({ signal }) => api.getCompanyRisk(companyId!, maxHops, signal).then(adaptCompanyRisk), enabled: Boolean(companyId) });
}

export function useCompanyExposure(companyId: string | undefined, maxHops: 1 | 2 | 3) {
  return useQuery({ queryKey: queryKeys.companyExposure(companyId ?? "", maxHops), queryFn: ({ signal }) => api.getCompanyExposure(companyId!, maxHops, signal).then(adaptCompanyExposure), enabled: Boolean(companyId) });
}

export function useCompanyImpact(companyId: string | undefined, maxHops: 1 | 2 | 3) {
  return useQuery({ queryKey: queryKeys.companyBlastRadius(companyId ?? "", maxHops), queryFn: ({ signal }) => api.getCompanyBlastRadius(companyId!, maxHops, signal).then(adaptCompanyBlastRadius), enabled: Boolean(companyId) });
}

export function useRiskHistory(companyId: string | undefined, maxHops: 1 | 2 | 3, limit = 100) {
  return useQuery({ queryKey: queryKeys.riskHistory(companyId ?? "", maxHops, limit), queryFn: ({ signal }) => api.getRiskHistory(companyId!, maxHops, limit, signal).then(adaptRiskHistory), enabled: Boolean(companyId) });
}

export function useDetailedHealth() {
  return useQuery({ queryKey: queryKeys.health(), queryFn: ({ signal }) => api.getDetailedHealth(signal).then(adaptSystemHealth), refetchInterval: 60_000 });
}

export function useAgentQuery() {
  return useMutation({ mutationFn: (question: string) => api.queryAgent(question).then(adaptAgentAnswer) });
}
