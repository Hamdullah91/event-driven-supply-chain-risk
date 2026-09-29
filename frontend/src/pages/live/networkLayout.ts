import type { GraphEdge } from "../../domain/types";

export type NetworkPosition = { x: number; y: number };

export const STRUCTURE_RELATIONSHIP_TYPES = [
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
] as const;

const LABEL_OFFSET_STEP = 14;

function clamp(value: number): number {
  return Math.min(94, Math.max(6, value));
}

function pairKey(edge: GraphEdge): string {
  return [edge.sourceId, edge.targetId].sort().join("\u0000");
}

export function relationshipLabelPositions(
  edges: GraphEdge[],
  positions: Map<string, NetworkPosition>,
): Map<string, NetworkPosition> {
  const grouped = new Map<string, GraphEdge[]>();

  for (const edge of edges) {
    const key = pairKey(edge);
    const group = grouped.get(key) ?? [];
    group.push(edge);
    grouped.set(key, group);
  }

  const result = new Map<string, NetworkPosition>();

  for (const group of grouped.values()) {
    const sorted = [...group].sort((left, right) => left.id.localeCompare(right.id));
    const endpointIds = [sorted[0].sourceId, sorted[0].targetId].sort();
    const first = positions.get(endpointIds[0]);
    const second = positions.get(endpointIds[1]);
    if (!first || !second) continue;

    const midpoint = { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 };
    const dx = second.x - first.x;
    const dy = second.y - first.y;
    const length = Math.hypot(dx, dy) || 1;
    const perpendicular = { x: -dy / length, y: dx / length };

    sorted.forEach((edge, index) => {
      const centeredIndex = index - (sorted.length - 1) / 2;
      const offset = sorted.length === 1 ? 0 : centeredIndex * LABEL_OFFSET_STEP;
      result.set(edge.id, {
        x: clamp(midpoint.x + perpendicular.x * offset),
        y: clamp(midpoint.y + perpendicular.y * offset),
      });
    });
  }

  return result;
}
