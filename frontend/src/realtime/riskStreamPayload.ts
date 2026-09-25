import type { ConnectionEstablishedDto, RiskUpdatedDto } from "../api/dtos";

function isHop(value: unknown): value is 1 | 2 | 3 {
  return value === 1 || value === 2 || value === 3;
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function parseRiskStreamPayload(raw: string): ConnectionEstablishedDto | RiskUpdatedDto | null {
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    return null;
  }

  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;

  if (record.type === "connection.established" && typeof record.message === "string") {
    return { type: "connection.established", message: record.message };
  }

  if (
    record.type === "risk.updated"
    && typeof record.company_id === "string"
    && isNumber(record.risk_score)
    && typeof record.risk_level === "string"
    && isNumber(record.contributing_event_count)
    && isHop(record.max_hops)
    && typeof record.timestamp === "string"
  ) {
    return {
      type: "risk.updated",
      company_id: record.company_id,
      risk_score: record.risk_score,
      risk_level: record.risk_level,
      contributing_event_count: record.contributing_event_count,
      max_hops: record.max_hops,
      timestamp: record.timestamp,
      ...(typeof record.event_id === "string" ? { event_id: record.event_id } : {}),
      ...(typeof record.trigger_event_type === "string" ? { trigger_event_type: record.trigger_event_type } : {}),
    };
  }

  return null;
}
