import { describe, expect, it } from "vitest";
import {
  adaptAgentAnswer,
  adaptCompanyBlastRadius,
  adaptCompanyExposure,
  adaptCompanyNetwork,
  adaptEvent,
  adaptEventBlastRadius,
  adaptRiskHistory,
  adaptRiskStreamMessage,
  adaptSearchResult,
  normalizeEntityType,
  normalizeEventType,
} from "./adapters";

describe("Phase 3 adapters", () => {
  it("normalizes compatibility Event aliases exactly once", () => {
    expect(normalizeEventType("REGULATORY_CHANGE")).toBe("REGULATION_CHANGE");
    expect(normalizeEventType("facility_shutdown")).toBe("FACILITY_OUTAGE");
  });

  it("preserves directed graph edges and canonical entity IDs", () => {
    const graph = adaptCompanyNetwork({
      company_id: "tsmc",
      depth: 1,
      nodes: [
        { id: "Company:tsmc", label: "Company", name: "TSMC", properties: { company_id: "tsmc" } },
        { id: "Company:nvidia", label: "Company", name: "NVIDIA", properties: { company_id: "nvidia" } },
      ],
      relationships: [{ id: "rel-1", source: "Company:tsmc", target: "Company:nvidia", relationship_type: "SUPPLIES", properties: {}, evidence_status: "UNAVAILABLE" }],
    });
    expect(graph.focus.id).toBe("tsmc");
    expect(graph.edges[0]).toMatchObject({ sourceId: "Company:tsmc", targetId: "Company:nvidia", directed: true, type: "SUPPLIES" });
  });

  it("keeps company Blast Radius transmission factor separate from Event propagated risk", () => {
    const companyImpact = adaptCompanyBlastRadius({
      company_id: "tsmc", max_hops: 2, affected_company_count: 1, hop_counts: { "1": 1 },
      companies: [{ company_id: "nvidia", company_name: "NVIDIA", hop_distance: 1, transmission_factor: 0.8, path: [{ company_id: "tsmc", name: "TSMC" }, { company_id: "nvidia", name: "NVIDIA" }] }],
    });
    const eventImpact = adaptEventBlastRadius({
      event_id: "evt-1", event_type: "FACILITY_OUTAGE", severity: "high", max_hops: 2, affected_company_count: 1, hop_counts: { "1": 1 },
      companies: [{ company_id: "nvidia", company_name: "NVIDIA", origin_company_id: "tsmc", origin_company_name: "TSMC", hop_distance: 1, initial_risk: 0.75, path_dependency: 0.8, distance_decay: 1, propagated_risk: 0.6, path: [{ company_id: "tsmc", name: "TSMC" }, { company_id: "nvidia", name: "NVIDIA" }] }],
    });
    expect(companyImpact.metricType).toBe("TRANSMISSION_FACTOR");
    expect(companyImpact.targets[0].transmissionFactor).toBe(0.8);
    expect(companyImpact.targets[0].propagatedRisk).toBeUndefined();
    expect(eventImpact.metricType).toBe("PROPAGATED_RISK");
    expect(eventImpact.targets[0].propagatedRisk).toBe(0.6);
    expect(eventImpact.targets[0].transmissionFactor).toBeUndefined();
  });

  it("keeps generated exposure identity separate from canonical Event identity", () => {
    const [exposure] = adaptCompanyExposure({
      company_id: "nvidia",
      event_count: 1,
      exposures: [{ event_id: "evt-1", event_type: "SUPPLY_DISRUPTION", severity: "high", affected_company_id: "tsmc", affected_company_name: "TSMC", hop_distance: 1, initial_risk: 0.75, path_dependency: 1, distance_decay: 1, propagated_risk: 0.75, path: [{ company_id: "tsmc", name: "TSMC" }, { company_id: "nvidia", name: "NVIDIA" }], evidence_status: "PARTIAL" }],
    });
    expect(exposure.eventId).toBe("evt-1");
    expect(exposure.exposureId).not.toBe(exposure.eventId);
    expect(exposure.exposureId).toContain("evt-1");
  });

  it("does not invent a typed affected entity from a bare Event entity_id", () => {
    const event = adaptEvent({ event_id: "evt-1", event_type: "FACILITY_OUTAGE", source: "wire", timestamp: "2026-09-24T00:00:00Z", entity_id: "mystery-1", severity: "high", payload: {}, evidence_status: "UNAVAILABLE" });
    expect(event.affectedEntities).toEqual([]);
  });

  it("preserves Facility identity from typed search and Event payloads", () => {
    const search = adaptSearchResult({ label: "Facility", entity_id: "fab-1", name: "Hsinchu Fab", properties: {} });
    const event = adaptEvent({
      event_id: "evt-fab",
      event_type: "FACILITY_OUTAGE",
      source: "wire",
      timestamp: "2026-09-24T00:00:00Z",
      severity: "high",
      payload: { affected_entities: [{ id: "fab-1", name: "Hsinchu Fab", type: "Facility" }] },
      evidence_status: "PARTIAL",
    });

    expect(search.entity).toEqual({ id: "fab-1", name: "Hsinchu Fab", type: "Facility" });
    expect(event.affectedEntities[0]).toEqual({ id: "fab-1", name: "Hsinchu Fab", type: "Facility" });
    expect(normalizeEntityType("Supplier")).toBe("Unknown");
  });

  it("preserves direct Hop 0 Event impact without converting it to structural depth", () => {
    const impact = adaptEventBlastRadius({
      event_id: "evt-direct",
      event_type: "SUPPLY_DISRUPTION",
      severity: "critical",
      max_hops: 3,
      affected_company_count: 1,
      hop_counts: { "0": 1 },
      companies: [{
        company_id: "tsmc",
        company_name: "TSMC",
        origin_company_id: "tsmc",
        origin_company_name: "TSMC",
        hop_distance: 0,
        initial_risk: 1,
        path_dependency: 1,
        distance_decay: 1,
        propagated_risk: 1,
        path: [{ company_id: "tsmc", name: "TSMC", type: "Company" }],
      }],
    });

    expect(impact.targets[0].hop).toBe(0);
    expect(impact.paths[0].trace).toMatchObject({ hop: 0, initialRisk: 1, combinedPathDependency: 1, distanceDecay: 1, propagatedRisk: 1 });
  });

  it("marks risk history as Event-derived reconstruction and preserves canonical Event IDs", () => {
    const history = adaptRiskHistory({
      company_id: "nvidia",
      max_hops: 3,
      count: 1,
      points: [{ timestamp: "2026-09-24T00:00:00Z", risk_score: 0.5, risk_level: "HIGH", event_id: "evt-history" }],
    });

    expect(history.semantics).toBe("EVENT_DERIVED_RECONSTRUCTION");
    expect(history.points[0].eventId).toBe("evt-history");
    expect(history.points[0].currentRisk).toBe(0.5);
  });

  it("keeps Agent string entities display-only rather than inventing canonical IDs", () => {
    const answer = adaptAgentAnswer({
      answer: "TSMC supplies NVIDIA.",
      evidence_status: "PARTIAL",
      affected_entities: ["TSMC", "NVIDIA"],
      dependency_paths: [["TSMC", "NVIDIA"]],
      hop_counts: [1],
      event_refs: ["evt-agent"],
      path_ids: ["path-1"],
      warnings: [],
      provenance: [{ availability: "PARTIAL", source: "filing", event_id: "evt-agent" }],
    });

    expect(answer.entities[0]).toEqual({ name: "TSMC" });
    expect(answer.paths[0]).toEqual({ names: ["TSMC", "NVIDIA"], pathId: "path-1" });
    expect(answer.eventRefs).toEqual(["evt-agent"]);
  });

  it("keeps WebSocket risk, Event identity, and trigger taxonomy semantically separate", () => {
    const update = adaptRiskStreamMessage({
      type: "risk.updated",
      event_id: "evt-stream",
      company_id: "nvidia",
      risk_score: 0.72,
      risk_level: "HIGH",
      contributing_event_count: 2,
      max_hops: 3,
      trigger_event_type: "FACILITY_SHUTDOWN",
      timestamp: "2026-09-25T01:00:00Z",
    });

    expect(update).toMatchObject({
      type: "risk.updated",
      eventId: "evt-stream",
      companyId: "nvidia",
      currentRisk: 0.72,
      riskLevel: "HIGH",
      triggerEventType: "FACILITY_OUTAGE",
    });
  });
});
