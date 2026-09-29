import { describe, expect, it } from "vitest";

const productionLiveSources = import.meta.glob([
  "../app/LiveApp.tsx",
  "../components/live/**/*.{ts,tsx}",
  "../pages/live/**/*.{ts,tsx}",
  "../api/**/*.{ts,tsx}",
  "../query/**/*.{ts,tsx}",
  "../realtime/**/*.{ts,tsx}",
  "../router/**/*.{ts,tsx}",
  "../state/**/*.{ts,tsx}",
  "../domain/**/*.{ts,tsx}",
  "../config/**/*.{ts,tsx}",
  "!../**/*.test.{ts,tsx}",
], { query: "?raw", import: "default", eager: true }) as Record<string, string>;

describe("Phase 3 live architecture boundary", () => {
  it("keeps Phase 2 demo fixtures out of live production modules", () => {
    expect(Object.keys(productionLiveSources).length).toBeGreaterThan(0);

    for (const [path, source] of Object.entries(productionLiveSources)) {
      expect(source, `${path} must not import Phase 2 fixture data`).not.toMatch(
        /(?:from\s+|import\s*\()\s*["'][^"']*(?:\/data\/|\.\.\/data\/|\.\/data\/)[^"']*["']/,
      );
      expect(source, `${path} must not reference frozen demo fixture symbols`).not.toMatch(
        /\b(?:companiesDemo|eventsDemo|networkStructureDemo|networkImpactDemo)\b/,
      );
    }
  });

  it("keeps Neo4j transport out of the React frontend boundary", () => {
    for (const [path, source] of Object.entries(productionLiveSources)) {
      expect(source, `${path} must communicate through FastAPI rather than Neo4j directly`).not.toMatch(
        /\bneo4j-driver\b|bolt:\/\/|neo4j:\/\//i,
      );
    }
  });
});
