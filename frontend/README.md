# Supply Chain Risk Intelligence Frontend

React + TypeScript + Vite frontend for the Final Year Project:

**Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs**

## Phase 1 Status

This branch contains the frozen Phase 1 visual architecture candidate:

- exactly six top-level sections: Overview, Events, Network, Companies, Risk Analysis, Intelligence
- professional dark analytical workstation visual system
- permanent right-side Entity Inspector
- Structure and Impact graph modes
- controlled concentric/radial Blast Radius inside Network → Impact
- canonical risk labels: NONE, LOW, MEDIUM, HIGH, CRITICAL
- development fixtures clearly separated from live backend data

Phase 1 does **not** freeze the final graph-rendering library and does not implement the full live API adapter layer.

## Backend Capabilities Already Available

The current backend exposes event list/detail/blast-radius APIs, company/network APIs, global search, risk/history/exposure/blast-radius APIs, detailed health, geographic coordinates, the public Agent query API, and `/risk-stream` WebSocket connectivity.

Several Phase 1 screens remain intentionally fixture-backed. Their UI copy must say that frontend adapter/integration work is pending rather than claiming that the backend endpoint does not exist.

Production Agent responses require valid runtime LLM provider configuration. WebSocket connection and same-process event-to-risk publishing are distinct concerns; the current in-memory connection manager requires the poller and FastAPI application to share a runtime for live publication.

## Development

From `frontend/`:

```bash
npm install
npm run dev
```

Final Phase 1 verification:

```bash
npm run build
npm run lint
```

## Fixture Policy

Development/demo fixtures are isolated under `src/data/` or are explicitly marked in the relevant Phase 1 page component. Synthetic events, risk values, paths, and Inspector context must never be presented as current production data.

## Graph Boundary

The final graph engine is intentionally not selected in Phase 1. A later implementation decision must satisfy these capabilities:

- directed edges
- multigraph-style relationships
- pan and zoom
- drag where useful
- node and edge selection
- custom node and edge styles
- Structure Mode styling
- Impact Mode styling
- path highlighting
- bounded expansion
- controlled concentric/radial Blast Radius by hop
- Neo4j-backed data through the backend API

See `frontend_phase1_handoff.md` for the complete frozen design and Phase 2 boundary.
