import { describe, expect, it } from "vitest";
import { parseNetworkUrlState, serializeNetworkUrlState } from "./networkState";

describe("network URL state", () => {
  it("round-trips navigable Structure investigation identity", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=structure&focusType=Company&focusId=tsmc&depth=2"));
    expect(state).toMatchObject({ mode: "structure", focusType: "Company", focusId: "tsmc", depth: 2 });
    expect(serializeNetworkUrlState(state).get("focusId")).toBe("tsmc");
  });

  it("round-trips Event Impact identity and selected path for reload restoration", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=impact&focusType=Event&focusId=evt-123&eventId=evt-123&maxHops=2&targetId=nvidia&pathId=path%3Aevt-123%3Anvidia"));
    const serialized = serializeNetworkUrlState(state);

    expect(state).toMatchObject({
      mode: "impact",
      focusType: "Event",
      focusId: "evt-123",
      eventId: "evt-123",
      maxHops: 2,
      selectedTargetId: "nvidia",
      pathId: "path:evt-123:nvidia",
    });
    expect(serialized.get("mode")).toBe("impact");
    expect(serialized.get("focusType")).toBe("Event");
    expect(serialized.get("focusId")).toBe("evt-123");
    expect(serialized.get("eventId")).toBe("evt-123");
    expect(serialized.get("maxHops")).toBe("2");
    expect(serialized.get("targetId")).toBe("nvidia");
    expect(serialized.get("pathId")).toBe("path:evt-123:nvidia");
  });

  it("does not carry Impact-only selection into Structure state", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=structure&focusType=Company&focusId=nvidia&depth=1&targetId=amd&pathId=stale"));
    const serialized = serializeNetworkUrlState({ ...state, selectedTargetId: "amd", pathId: "stale" });

    expect(state.selectedTargetId).toBeUndefined();
    expect(state.pathId).toBeUndefined();
    expect(serialized.get("targetId")).toBeNull();
    expect(serialized.get("pathId")).toBeNull();
  });

  it("rejects invalid depth and unknown entity types instead of inventing state", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=impact&focusType=Supplier&focusId=x&maxHops=99"));
    expect(state.focusType).toBeUndefined();
    expect(state.maxHops).toBe(3);
    expect(state.focusId).toBe("x");
  });
});
