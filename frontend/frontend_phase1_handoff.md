# Frontend Phase 1 Implementation Handoff

## Project

Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs

## Phase

Frontend Phase 1 — UX Layout & Visual System Blueprint + working React/Vite visual prototype

## Status

Final Phase 1 cleanup applied against the current Phase 0 backend contracts. Formal freeze requires successful final `npm run build`, `npm run lint`, and branch verification.

## Source-of-Truth Order

1. Current executable backend/frontend code
2. Current schemas, route contracts, and integration tests
3. Phase 0 frontend repository/API audit
4. Phase 1 UX Layout & Visual System Blueprint
5. Older README/project-state/chat assumptions

## Frozen Product Architecture

Product: **Graph-Centric Enterprise Supply Chain Risk Intelligence Command Center**.

Exactly six top-level sections:

1. Overview
2. Events
3. Network
4. Companies
5. Risk Analysis
6. Intelligence

Core analytical story:

```text
Event → Network → Impact / Blast Radius → Risk → Evidence → Explanation
```

Blast Radius remains inside `Network → Impact`, never as separate top-level navigation.

Geography remains a secondary analytical lens.

## Frozen Shell and Visual System

```text
Sidebar expanded:   240px
Sidebar collapsed:   72px
Top bar:              64px
Inspector:          ~380px
Page padding:         24px
Desktop grid:         12 columns
```

Visual style: **Professional Dark Analytical Workstation**.

Frozen tokens remain defined in `src/index.css`.

Canonical risk terminology remains exactly:

- NONE
- LOW
- MEDIUM
- HIGH
- CRITICAL

Never use `MODERATE` for company risk.

The frontend never independently calculates authoritative risk.

## Current Public Backend Capabilities

Current executable backend support includes:

```text
GET  /health
GET  /api/v1/health/detailed
GET  /api/v1/events
GET  /api/v1/events/{event_id}
GET  /api/v1/events/{event_id}/blast-radius
GET  /companies
GET  /companies/{company_id}
GET  /companies/{company_id}/network
GET  /api/v1/search
GET  /risk/{company_id}
GET  /risk/{company_id}/history
GET  /risk/{company_id}/blast-radius
GET  /risk/{company_id}/exposure
POST /api/v1/agent/query
WS   /risk-stream
```

Company filtering, global graph search, typed provenance structures, detailed health, canonical frontend graph IDs, and verified Location latitude/longitude coordinates are implemented.

### Runtime caveats

Production LLM-backed Agentic RAG requires valid runtime provider configuration. The public Agent endpoint exists; the frontend must not describe it as missing, but must not claim successful live LLM operation when the provider is unconfigured.

The WebSocket connection manager is in-memory. A WebSocket connection or successful handshake does not by itself prove that the complete event-driven publication path is active. Same-process live event-to-risk publication requires the poller and FastAPI application to share a runtime. Multi-process deployment needs shared external pub/sub.

## Phase 1 Page State

### Overview

Command-center layout containing disruption context, risk landscape, propagation spotlight, and broader context.

The page is still development-fixture-backed. Event list and risk-history backend capabilities exist, while aggregate overview-specific metrics may still require composition or additional backend support. The UI must distinguish “frontend adapter pending” from “backend endpoint unavailable.”

### Events

Desktop master-detail architecture is frozen.

Preserved fields and actions:

- event list
- event detail
- severity
- classifier confidence
- source
- affected entities
- evidence
- Open Impact

Current backend provides event list, event detail, and event-origin Blast Radius endpoints. Phase 1 remains fixture-backed; live adapter/action wiring is deferred.

### Network

Two visually separate modes are frozen:

- Structure
- Impact

Structure Mode may use a flexible structural graph layout.

Impact / Blast Radius must use a controlled concentric/radial hop layout that visibly preserves:

```text
Origin
Ring 1
Ring 2
Ring 3
```

Hop distance is analytically meaningful, so unrestricted graph physics must not determine Blast Radius positioning.

The current renderer remains a static Phase 1 visual prototype. Neo4j-backed interactive rendering belongs to later implementation work.

### Companies

Company directory and Company Profile visual architecture are frozen.

Profile areas include:

- current risk
- contributing events
- exposure paths
- focused network area
- facilities
- products
- materials
- technologies
- evidence/provenance

Global search and company filtering backend capabilities exist. Phase 1 search/filter controls may remain non-interactive while frontend adapter/interaction behavior is deferred.

### Risk Analysis

Contains:

- risk ranking
- domain exposure
- hop exposure
- Network lens
- Geography lens
- Heatmap
- event contributions
- risk context

The backend exposes `/risk/{company_id}/history`. Phase 1 historical charts remain fixture/non-live until a frontend adapter is implemented. The UI must not claim risk history is unavailable or imply stronger persisted-snapshot semantics than the backend contract provides.

Backend Location nodes expose verified latitude/longitude coordinates. Geography remains secondary, and Phase 1 does not invent coordinates or add logistics telemetry.

### Intelligence

Graph-grounded analytical workspace containing:

- query composer
- grounded answer
- supporting graph/path
- supporting entities
- risk trace
- evidence

`POST /api/v1/agent/query` exists. Phase 1 query submission remains disabled because frontend adapter/interaction wiring is deferred. Production LLM-backed responses additionally depend on runtime provider configuration.

The Intelligence surface is not a generic chatbot and must keep answers visibly tied to graph/risk/evidence context.

## Entity Inspector

Permanent contextual right-side Inspector is frozen visually.

Designed for:

- Company
- Facility
- Material
- Product
- Technology
- Country
- Location
- Event
- Relationship

The current TSMC Inspector context is explicitly a **static Phase 1 development fixture**, not a production default selection. Dynamic selection behavior belongs to Phase 2.

## Evidence and Provenance Rule

Evidence remains first-class.

Typed provenance/evidence-status structures exist in the backend. The frontend must display only fields actually returned by the selected contract and must use `Not available` when a field is genuinely absent.

Never invent source, confidence, provenance, document, or extracted context.

## Graph Rules

Structure and risk propagation remain separate concepts.

Structure may use multiple legal structural relationship types.

Risk propagation follows directed downstream `SUPPLIES` semantics and the backend maximum three-hop model.

Relationship direction must be preserved.

Backend `transmission_factor` must not be mislabeled as aggregate/current company risk.

## Final Graph Technology Decision — NOT Frozen

Phase 1 freezes graph capabilities, not a library.

The eventual graph engine must support:

- directed edges
- multigraph-style relationships
- pan
- zoom
- drag where useful
- node selection
- edge selection
- custom node styles
- custom edge styles
- Structure Mode styling
- Impact Mode styling
- path highlighting
- bounded expansion
- controlled concentric/radial Blast Radius
- Neo4j-backed data through the backend API

Library evaluation and implementation belong to a later architecture/implementation phase. No graph library is selected by this Phase 1 handoff.

## Geography Rule

Geography is secondary to graph analysis.

Verified backend Location coordinates may be used when live map integration is implemented. Never invent coordinates for entities that do not provide them.

Do not add ships, vessel tracking, shipment routes, ETAs, port congestion, truck tracking, or unrelated logistics telemetry.

## System Health Rule

Detailed backend health is available at `/api/v1/health/detailed`.

Only statuses actually returned by that endpoint may be displayed. Do not synthesize service states. In particular, do not claim News API, classifier, poller, NLP, Agent provider, or WebSocket publication health unless the current backend health contract returns that state.

## Development Fixtures

Phase 1 fixture datasets are isolated under `src/data/`:

- `overviewDemo.ts`
- `eventsDemo.ts`
- `companiesDemo.ts`
- `networkStructureDemo.ts`
- `networkImpactDemo.ts`
- `riskAnalysisDemo.ts`
- `intelligenceDemo.ts`
- `inspectorDemo.ts`

Pages render those datasets with visible `DEVELOPMENT DATA`, `DEVELOPMENT FIXTURE`, `DEMO`, or equivalent labels. Synthetic events must not appear to be current real news; fixture timestamps are visibly identified as fixture/demo timing.

The Impact fixture contains only prototype company/path/context values. The controlled radial hop-ring structure itself remains a visual rule, not simulated live backend output.

## Accessibility Baseline

Phase 1 preserves:

- visible `:focus-visible`
- keyboard-reachable controls
- practical 40px minimum button target sizing
- text + color risk communication
- no essential hover-only information
- reduced-motion handling
- readable contrast
- practical metadata minimum around 12px

## Responsive Baseline

Primary desktop targets remain 1440×900 and larger. At 1280-class widths the Inspector narrows while analytical content wraps. At ~1024 the sidebar collapses and the persistent desktop Inspector is removed from the inline layout so the primary workspace remains usable.

Below desktop widths, cards and analytical sections may stack. Mobile requires basic compatibility only; Phase 1 is not a mobile redesign.

## Reusable State Primitives

Keep:

- `StatePanel`
- `Skeleton`
- `MetricCard`
- `Panel`
- `RiskBadge`

Temporary component-preview/showcase styling has been removed.

## Phase 2 Boundary

Phase 2 may define interaction behavior, including:

- entity click behavior
- graph expansion
- Structure / Impact switching interaction details
- Blast Radius interaction
- filters
- search behavior
- path highlighting
- Inspector behavior
- Events master-detail behavior
- real-time update behavior
- Intelligence-to-graph actions
- context preservation

Phase 2 must not redesign the frozen Phase 1 visual architecture.

Detailed API adapter implementation and production graph rendering may be scheduled in later implementation phases as appropriate.

## Phase 1 Freeze Gate

Before declaring Phase 1 frozen:

1. `npm run build` must pass from `frontend/`.
2. `npm run lint` must pass from `frontend/`.
3. The pushed branch must contain the complete `frontend/` directory.
4. Final repository audit must confirm no stale backend-unavailable claims remain for capabilities that now exist.
5. No accidental files, secrets, prohibited logistics features, or `MODERATE` company-risk terminology may be present.

After those checks pass, Phase 1 may be declared frozen. Phase 2 must not begin before that declaration.
