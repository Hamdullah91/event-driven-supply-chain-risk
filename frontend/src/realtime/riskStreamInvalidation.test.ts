import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { invalidateForRiskUpdate } from "./riskStreamInvalidation";

describe("risk stream targeted invalidation", () => {
  it("invalidates only the affected company risk families and referenced Event families", async () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries").mockResolvedValue(undefined);

    await invalidateForRiskUpdate(client, {
      type: "risk.updated",
      eventId: "evt-1",
      companyId: "nvidia",
      currentRisk: 0.72,
      riskLevel: "HIGH",
      contributingEventCount: 2,
      maxHops: 3,
      triggerEventType: "FACILITY_OUTAGE",
      timestamp: "2026-09-25T01:00:00Z",
    });

    const keys = invalidate.mock.calls.map(([filters]) => filters?.queryKey);
    expect(keys).toEqual(expect.arrayContaining([
      ["company-risk", "nvidia"],
      ["company-exposure", "nvidia"],
      ["company-blast-radius", "nvidia"],
      ["risk-history", "nvidia"],
      ["event", "evt-1"],
      ["event-blast-radius", "evt-1"],
      ["events"],
    ]));
    expect(keys).not.toContainEqual(["companies"]);
    expect(keys).not.toContainEqual([]);
  });

  it("does not invalidate Event queries when a risk update has no event reference", async () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries").mockResolvedValue(undefined);

    await invalidateForRiskUpdate(client, {
      type: "risk.updated",
      companyId: "nvidia",
      currentRisk: 0.5,
      riskLevel: "HIGH",
      contributingEventCount: 1,
      maxHops: 2,
      timestamp: "2026-09-25T01:00:00Z",
    });

    const keys = invalidate.mock.calls.map(([filters]) => filters?.queryKey);
    expect(keys).toHaveLength(4);
    expect(keys.some((key) => key?.[0] === "event" || key?.[0] === "events")).toBe(false);
  });
});
