import { describe, expect, it } from "vitest";
import { parseRiskStreamPayload } from "./riskStreamPayload";

describe("risk stream schema boundary", () => {
  it("accepts the verified handshake and risk.updated contract", () => {
    expect(parseRiskStreamPayload('{"type":"connection.established","message":"Connected"}')).toEqual({ type: "connection.established", message: "Connected" });
    expect(parseRiskStreamPayload('{"type":"risk.updated","event_id":"evt-1","company_id":"nvidia","risk_score":0.72,"risk_level":"HIGH","contributing_event_count":2,"max_hops":3,"trigger_event_type":"FACILITY_OUTAGE","timestamp":"2026-09-25T01:00:00Z"}')).toMatchObject({ type: "risk.updated", event_id: "evt-1", company_id: "nvidia", max_hops: 3 });
  });

  it("rejects unknown and malformed messages rather than mutating state", () => {
    expect(parseRiskStreamPayload('{"type":"event.created","event_id":"evt-1"}')).toBeNull();
    expect(parseRiskStreamPayload('{"type":"risk.updated","company_id":"nvidia"}')).toBeNull();
    expect(parseRiskStreamPayload("not-json")).toBeNull();
  });
});
