import type { EntityType, HopDepth } from "../domain/types";

export type NetworkMode = "structure" | "impact";
export type NetworkUrlState = {
  mode: NetworkMode;
  focusType?: EntityType;
  focusId?: string;
  depth: HopDepth;
  maxHops: HopDepth;
  eventId?: string;
  selectedTargetId?: string;
  pathId?: string;
};

const ENTITY_TYPES: EntityType[] = ["Company", "Facility", "Product", "Material", "Technology", "Industry", "Location", "Country", "Event"];

function hop(value: string | null, fallback: HopDepth): HopDepth {
  const parsed = Number(value);
  return parsed === 1 || parsed === 2 || parsed === 3 ? parsed : fallback;
}

function entityType(value: string | null): EntityType | undefined {
  return ENTITY_TYPES.find((candidate) => candidate === value);
}

export function parseNetworkUrlState(params: URLSearchParams): NetworkUrlState {
  const mode: NetworkMode = params.get("mode") === "impact" ? "impact" : "structure";
  const focusId = params.get("focusId") || undefined;
  const focusType = entityType(params.get("focusType"));
  const eventId = params.get("eventId") || undefined;
  const selectedTargetId = mode === "impact" ? params.get("targetId") || undefined : undefined;
  const pathId = mode === "impact" ? params.get("pathId") || undefined : undefined;
  return {
    mode,
    ...(focusId ? { focusId } : {}),
    ...(focusType ? { focusType } : {}),
    depth: hop(params.get("depth"), 1),
    maxHops: hop(params.get("maxHops"), 3),
    ...(eventId ? { eventId } : {}),
    ...(selectedTargetId ? { selectedTargetId } : {}),
    ...(pathId ? { pathId } : {}),
  };
}

export function serializeNetworkUrlState(state: NetworkUrlState): URLSearchParams {
  const params = new URLSearchParams();
  params.set("mode", state.mode);
  if (state.focusType) params.set("focusType", state.focusType);
  if (state.focusId) params.set("focusId", state.focusId);
  if (state.mode === "structure") params.set("depth", String(state.depth));
  else params.set("maxHops", String(state.maxHops));
  if (state.eventId) params.set("eventId", state.eventId);
  if (state.mode === "impact" && state.selectedTargetId) params.set("targetId", state.selectedTargetId);
  if (state.mode === "impact" && state.pathId) params.set("pathId", state.pathId);
  return params;
}
