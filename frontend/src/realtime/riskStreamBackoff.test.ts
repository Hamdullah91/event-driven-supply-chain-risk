import { describe, expect, it } from "vitest";
import { reconnectDelayForAttempt, STABLE_CONNECTION_RESET_MS } from "./riskStreamBackoff";

describe("risk stream reconnect backoff", () => {
  it("uses the bounded 1/2/5/10/30 second reconnect sequence", () => {
    expect([1, 2, 3, 4, 5, 6, 20].map(reconnectDelayForAttempt)).toEqual([
      1_000,
      2_000,
      5_000,
      10_000,
      30_000,
      30_000,
      30_000,
    ]);
  });

  it("requires a stable connection window before retry state is reset", () => {
    expect(STABLE_CONNECTION_RESET_MS).toBe(30_000);
  });
});
