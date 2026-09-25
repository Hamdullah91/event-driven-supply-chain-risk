import { describe, expect, it } from "vitest";
import { parseNetworkUrlState, serializeNetworkUrlState } from "./networkState";

describe("network URL state", () => {
  it("round-trips navigable Structure investigation identity", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=structure&focusType=Company&focusId=tsmc&depth=2"));
    expect(state).toMatchObject({ mode: "structure", focusType: "Company", focusId: "tsmc", depth: 2 });
    expect(serializeNetworkUrlState(state).get("focusId")).toBe("tsmc");
  });

  it("rejects invalid depth and unknown entity types instead of inventing state", () => {
    const state = parseNetworkUrlState(new URLSearchParams("mode=impact&focusType=Supplier&focusId=x&maxHops=99"));
    expect(state.focusType).toBeUndefined();
    expect(state.maxHops).toBe(3);
    expect(state.focusId).toBe("x");
  });
});
