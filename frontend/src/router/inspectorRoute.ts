import type { InspectorRef } from "../state/uiStore";

export type InspectorRouteContext = {
  section: "overview" | "events" | "network" | "companies" | "risk" | "intelligence";
  companyId?: string;
  eventId?: string;
  riskCompanyId?: string;
  networkMode?: "structure" | "impact";
  networkFocusId?: string;
  networkFocusType?: string;
};

function decodeSegment(value: string | undefined): string | undefined {
  if (!value) return undefined;
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function inspectorRouteContextFromLocation(
  pathname: string,
  search: string,
): InspectorRouteContext {
  const parts = pathname.split("/").filter(Boolean);
  const params = new URLSearchParams(search);

  if (parts[0] === "events") {
    return { section: "events", ...(parts[1] ? { eventId: decodeSegment(parts[1]) } : {}) };
  }
  if (parts[0] === "network") {
    return {
      section: "network",
      networkMode: params.get("mode") === "impact" ? "impact" : "structure",
      ...(params.get("focusId") ? { networkFocusId: params.get("focusId")! } : {}),
      ...(params.get("focusType") ? { networkFocusType: params.get("focusType")! } : {}),
    };
  }
  if (parts[0] === "companies") {
    return { section: "companies", ...(parts[1] ? { companyId: decodeSegment(parts[1]) } : {}) };
  }
  if (parts[0] === "risk-analysis") {
    return {
      section: "risk",
      ...(params.get("companyId") ? { riskCompanyId: params.get("companyId")! } : {}),
    };
  }
  if (parts[0] === "intelligence") return { section: "intelligence" };
  return { section: "overview" };
}

export function isInspectorCompatibleWithRoute(
  inspector: InspectorRef,
  route: InspectorRouteContext,
): boolean {
  if (route.section === "events") {
    if (!route.eventId) return false;
    if ((inspector.kind === "event" || inspector.entityType === "Event") && inspector.id === route.eventId) return true;
    return inspector.kind === "exposure" && inspector.context?.eventId === route.eventId;
  }

  if (route.section === "companies") {
    if (!route.companyId) return false;
    if (inspector.entityType === "Company" && inspector.id === route.companyId) return true;
    return inspector.kind === "exposure" && inspector.context?.relatedCompanyId === route.companyId;
  }

  if (route.section === "network") {
    if (!route.networkFocusId) return false;
    if (inspector.context?.graphFocusId === route.networkFocusId) return true;
    if (route.networkFocusType === "Company" && inspector.entityType === "Company" && inspector.id === route.networkFocusId) return true;
    if (route.networkFocusType === "Event" && (inspector.kind === "event" || inspector.entityType === "Event") && inspector.id === route.networkFocusId) return true;
    return route.networkFocusType === "Event" && inspector.kind === "exposure" && inspector.context?.eventId === route.networkFocusId;
  }

  if (route.section === "risk") {
    if (!route.riskCompanyId) return false;
    if (inspector.entityType === "Company" && inspector.id === route.riskCompanyId) return true;
    if (inspector.kind === "exposure" && inspector.context?.relatedCompanyId === route.riskCompanyId) return true;
    return inspector.kind === "event" && inspector.context?.relatedCompanyId === route.riskCompanyId;
  }

  return false;
}

export function isInspectorCompatibleWithTransition(
  inspector: InspectorRef,
  previous: InspectorRouteContext,
  next: InspectorRouteContext,
): boolean {
  if (previous.section === next.section) {
    if (next.section === "network") {
      const sameFocus = previous.networkFocusId === next.networkFocusId
        && previous.networkFocusType === next.networkFocusType;
      if (sameFocus) {
        if (previous.networkMode === next.networkMode) return true;
        return inspector.kind === "entity" || inspector.kind === "event" || inspector.kind === "exposure";
      }
    } else if (next.section === "events" && previous.eventId === next.eventId) {
      return true;
    } else if (next.section === "companies" && previous.companyId === next.companyId) {
      return true;
    } else if (next.section === "risk" && previous.riskCompanyId === next.riskCompanyId) {
      return true;
    } else if (next.section === "overview" || next.section === "intelligence") {
      return true;
    }
  }

  return isInspectorCompatibleWithRoute(inspector, next);
}
