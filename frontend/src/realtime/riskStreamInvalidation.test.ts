import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { invalidateForRiskUpdate, refetchForRiskUpdate } from "./riskStreamInvalidation";

describe("risk stream targeted invalidation", () => {
  it("marks only the affected company and Event query families stale without refetching active analysis", async () => {
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

    const filters = invalidate.mock.calls.map(([value]) => value);
    const keys = filters.map((value) => value?.queryKey);
    expect(keys).toEqual(expect.arrayContaining([
      ["company-risk", "nvidia"],
      ["company-exposure", "nvidia"],
      ["company-blast-radius", "nvidia"],
      ["risk-history", "nvidia"],
      ["event", "evt-1"],
      ["event-blast-radius", "evt-1"],
      ["events"],
    ]));
    expect(filters.every((value) => value?.refetchType === "none")).toBe(true);
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

  it("refetches only active targeted query families after the analyst explicitly refreshes", async () => {
    const client = new QueryClient();
    const refetch = vi.spyOn(client, "refetchQueries").mockResolvedValue(undefined);

    await refetchForRiskUpdate(client, { companyId: "nvidia", eventId: "evt-1" });

    expect(refetch).toHaveBeenCalledTimes(7);
    expect(refetch.mock.calls.every(([filters]) => filters?.type === "active")).toBe(true);
    expect(refetch.mock.calls.map(([filters]) => filters?.queryKey)).toContainEqual(["company-risk", "nvidia"]);
    expect(refetch.mock.calls.map(([filters]) => filters?.queryKey)).toContainEqual(["events"]);
  });
});
