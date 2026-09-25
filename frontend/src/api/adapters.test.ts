import { describe, expect, it } from "vitest";
import { adaptCompanyBlastRadius, adaptCompanyExposure, adaptCompanyNetwork, adaptEvent, adaptEventBlastRadius, normalizeEventType } from "./adapters";

const path = [{ company_id: "tsmc", company_name: "TSMC" }, { company_id: "nvidia", company_name: "NVIDIA" }];

describe("Phase 3 adapters", () => {
  it("normalizes compatibility aliases once at the adapter boundary", () => {
    expect(normalizeEventType("REGULATORY_CHANGE")).toBe("REGULATION_CHANGE");
    expect(normalizeEventType("FACILITY_SHUTDOWN")).toBe("FACILITY_OUTAGE");
  });

  it("preserves directed structure edges and canonical entity type", () => {
    const graph = adaptCompanyNetwork({
      company_id: "tsmc",
      depth: 2,
      nodes: [
        { id: "company:tsmc", label: "Company", name: "TSMC", properties: { company_id: "tsmc" } },
        { id: "company:nvidia", label: "Company", name: "NVIDIA", properties: { company_id: "nvidia" } },
      ],
      relationships: [{ id: "r1", source: "company:tsmc", target: "company:nvidia", relationship_type: "SUPPLIES", properties: {}, evidence_status: "UNAVAILABLE" }],
    });
    expect(graph.focus).toEqual({ id: "tsmc", type: "Company", name: "TSMC" });
    expect(graph.edges[0]).toMatchObject({ sourceId: "company:tsmc", targetId: "company:nvidia", directed: true });
  });

  it("keeps transmission factor separate from propagated risk", () => {
    const companyImpact = adaptCompanyBlastRadius({ company_id: "tsmc", max_hops: 3, affected_company_count: 1, hop_counts: { "1": 1 }, companies: [{ company_id: "nvidia", company_name: "NVIDIA", hop_distance: 1, transmission_factor: 0.8, path }] });
    expect(companyImpact.metricType).toBe("TRANSMISSION_FACTOR");
    expect(companyImpact.targets[0].transmissionFactor).toBe(0.8);
    expect(companyImpact.targets[0].propagatedRisk).toBeUndefined();

    const eventImpact = adaptEventBlastRadius({ event_id: "evt-1", event_type: "FACILITY_OUTAGE", severity: "high", max_hops: 3, affected_company_count: 1, hop_counts: { "1": 1 }, companies: [{ company_id: "nvidia", company_name: "NVIDIA", origin_company_id: "tsmc", origin_company_name: "TSMC", hop_distance: 1, initial_risk: 0.75, path_dependency: 0.8, distance_decay: 1, propagated_risk: 0.6, path }] });
    expect(eventImpact.metricType).toBe("PROPAGATED_RISK");
    expect(eventImpact.targets[0].propagatedRisk).toBe(0.6);
    expect(eventImpact.targets[0].transmissionFactor).toBeUndefined();
  });

  it("keeps exposure record identity distinct from event identity", () => {
    const [exposure] = adaptCompanyExposure({ company_id: "nvidia", event_count: 1, exposures: [{ event_id: "evt-1", event_type: "FACILITY_OUTAGE", severity: "high", affected_company_id: "tsmc", affected_company_name: "TSMC", hop_distance: 1, initial_risk: 0.75, path_dependency: 0.8, distance_decay: 1, propagated_risk: 0.6, path, evidence_status: "PARTIAL" }] });
    expect(exposure.eventId).toBe("evt-1");
    expect(exposure.exposureId).not.toBe(exposure.eventId);
    expect(exposure.targetCompany.id).toBe("nvidia");
  });

  it("does not invent typed affected entities from a bare entity_id", () => {
    const event = adaptEvent({ event_id: "evt-1", event_type: "FACILITY_OUTAGE", source: "news", timestamp: "2026-09-25T00:00:00Z", entity_id: "facility-1", severity: "high", payload: {}, evidence_status: "PARTIAL" });
    expect(event.affectedEntities).toEqual([]);
  });
});
