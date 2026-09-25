import { describe, expect, it } from "vitest";
import { parseNetworkUrlState, serializeNetworkUrlState } from "./networkState";

describe("network URL state", () => {
  it("round-trips navigable Structure investigation identity", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=structure&focusType=Company&focusId=tsmc&depth=2"));
    expect(state).toMatchObject({ mode: "structure", focusType: "Company", focusId: "tsmc", depth: 2 });
    expect(serializeNetworkUrlState(state).get("focusId")).toBe("tsmc");
  });

  it("round-trips Event Impact identity required for browser history restoration", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=impact&focusType=Event&focusId=evt-123&eventId=evt-123&maxHops=2"));
    const serialized = serializeNetworkUrlState(state);

    expect(state).toMatchObject({ mode: "impact", focusType: "Event", focusId: "evt-123", eventId: "evt-123", maxHops: 2 });
    expect(serialized.get("mode")).toBe("impact");
    expect(serialized.get("focusType")).toBe("Event");
    expect(serialized.get("focusId")).toBe("evt-123");
    expect(serialized.get("eventId")).toBe("evt-123");
    expect(serialized.get("maxHops")).toBe("2");
  });

  it("rejects invalid depth and unknown entity types instead of inventing state", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=impact&focusType=Supplier&focusId=x&maxHops=99"));
    expect(state.focusType).toBeUndefined();
    expect(state.maxHops).toBe(3);
    expect(state.focusId).toBe("x");
  });
});
