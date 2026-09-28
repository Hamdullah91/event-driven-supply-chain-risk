import { describe, expect, it } from "vitest";
import type { GraphEdge } from "../../domain/types";
import { relationshipLabelPositions, STRUCTURE_RELATIONSHIP_TYPES } from "./networkLayout";

function edge(id: string, type: string, sourceId: string, targetId: string): GraphEdge {
  return {
    id,
    type,
    sourceId,
    targetId,
    directed: true,
    metadata: {},
  };
}

describe("live network relationship layout", () => {
  it("places reciprocal relationship labels at distinct hit positions", () => {
    const edges = [
      edge("a-supplies-b", "SUPPLIES", "a", "b"),
      edge("b-depends-a", "DEPENDS_ON", "b", "a"),
    ];
    const positions = new Map([
      ["a", { x: 20, y: 50 }],
      ["b", { x: 80, y: 50 }],
    ]);

    const labels = relationshipLabelPositions(edges, positions);
    const supplies = labels.get("a-supplies-b");
    const depends = labels.get("b-depends-a");

    expect(supplies).toBeDefined();
    expect(depends).toBeDefined();
    expect(supplies).not.toEqual(depends);
    expect(Math.abs((supplies?.y ?? 0) - (depends?.y ?? 0))).toBeGreaterThanOrEqual(10);
  });

  it("keeps the full backend relationship vocabulary filterable", () => {
    expect(STRUCTURE_RELATIONSHIP_TYPES).toEqual([
      "SUPPLIES",
      "DEPENDS_ON",
      "OPERATES",
      "OWNS",
      "USES",
      "PRODUCES",
      "LOCATED_IN",
      "OPERATES_IN",
      "AFFECTS",
      "OCCURS_AT",
    ]);
  });
});
