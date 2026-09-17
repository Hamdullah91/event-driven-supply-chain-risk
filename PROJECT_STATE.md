# Project State

## Project

**Name:** Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs

**Type:** Computer Science Final Year Project

**Goal:** Detect supply-chain disruption events, maintain a dynamic Neo4j knowledge graph, propagate direct and indirect risk across multi-tier supplier networks, and provide explainable graph-grounded intelligence through APIs, WebSockets, Agentic Graph RAG, and a React frontend.

**Industry scope:** Semiconductors, EV/batteries, and aerospace/electronics.

## Current State — 2026-09-17

The roadmap is implemented through **Day 53 (Agentic Graph RAG grounded explanations)**. The **Phase 0 frontend/repository/API readiness audit and residual runtime-hardening pass are complete on `fix/phase0-residual-runtime-hardening` pending merge to `main`**. React frontend implementation has not started and requires explicit approval before beginning.

Final reopened-Phase-0 automated regression: **390 tests passed, 2 warnings in 68.42s**.

Final live graph-contract audit: **PASSED**.

Final strengthened live integration result:

```text
PHASE 0 LIVE INTEGRATION VERIFICATION PASSED
```

## Implemented Architecture

```text
SEC 10-K → Async crawler → Parser → spaCy → Resolution/validation → Neo4j baseline KG
Financial News → Poller/dedup → DistilBERT → spaCy → deterministic severity → Dynamic Event → AFFECTS/OCCURS_AT
Dynamic KG → Directed SUPPLIES traversal → 1/2/3-hop risk → FastAPI REST/WebSockets
User query → Structured LLM → Cypher validator → Graph inspector → Evidence assessment → Grounded explanation
```

For the live FYP runtime, the News poller can run as an optional FastAPI lifespan background task (`NEWS_POLLER_ENABLED=true`) so event processing, risk publication, and `/risk-stream` clients share the same in-process connection manager. The standalone poller is not assumed to broadcast into a separately running API process.

## Canonical Graph Ontology

Nine node labels are supported:

`Company`, `Facility`, `Product`, `Material`, `Technology`, `Industry`, `Location`, `Country`, `Event`.

**Supplier is not a node type.** Supplier is a role of `Company` expressed by:

```text
(:Company)-[:SUPPLIES]->(:Company)
```

Legal relationships:

```text
Company -SUPPLIES-> Company
Company -DEPENDS_ON-> Company
Company -OPERATES-> Facility
Company -OWNS-> Facility
Company -USES-> Material/Technology
Company -PRODUCES-> Product/Material
Company -OPERATES_IN-> Industry
Facility -LOCATED_IN-> Location
Location -LOCATED_IN-> Country
Event -AFFECTS-> Company/Facility
Event -OCCURS_AT-> Facility
```

Canonical IDs use `company_id`, `facility_id`, `product_id`, `material_id`, `technology_id`, `industry_id`, `location_id`, `country_id`, and `event_id`.

The final live graph audit verified canonical-ID completeness for all nine labels:

```text
Company     51/51
Facility    13/13
Product      6/6
Material     3/3
Technology   2/2
Industry     3/3
Location    11/11
Country      6/6
Event        2/2
```

Geographic contract:

```text
Location total: 11
geocoded:       11
missing:         0
partial:         0
contract_valid: true
```

## Event System

Canonical event types are:

`SUPPLY_DISRUPTION`, `REGULATION_CHANGE`, `FACILITY_OUTAGE`, `TECHNOLOGY_EMBARGO`, `TRADE_POLICY_CHANGE`, and `QUOTA_CHANGE`.

Canonical severities are `unknown`, `low`, `medium`, `high`, and `critical`.

New dynamic news events use a deterministic rule-based severity assessor based on disruption language/context. This severity is separate from DistilBERT classification confidence; confidence is not reused as severity. The severity assessment rationale is retained with event context.

Compatibility aliases remain intentionally at ingestion boundaries for older input spellings such as `FACILITY_SHUTDOWN` and `REGULATORY_CHANGE`. The stale Agent display mapping for `RAW_MATERIAL_SHORTAGE` was removed from the active canonical presentation path.

The news pipeline performs classification, NLP/entity resolution, severity assessment, Event persistence, automatic company `AFFECTS` linking, and conservative automatic `OCCURS_AT` linking for explicit known facility mentions. Facility matching intentionally rejects ambiguous city-only and fuzzy partial-name guesses.

### Historical data note

The live Neo4j graph contains two older integration/test Event nodes created before this hardening pass. One retains `event_type=facility_shutdown` and `severity=unknown`; another retains `facility_shutdown` with `severity=high`. These historical nodes were deliberately not rewritten. Their current Blast Radius calculations therefore reflect their persisted historical severity, including zero initial risk for the `unknown` event. New pipeline events use the current canonical taxonomy/severity path.

## Risk Engine

Severity risk mapping:

```text
unknown=0.00  low=0.25  medium=0.50  high=0.75  critical=1.00
```

Path risk:

```text
initial_risk × product(dependency_weights) × 0.70^(hop-1)
```

Propagation follows directed downstream `SUPPLIES` paths up to three hops. Multiple events use strongest-path-per-event followed by:

```text
1 - product(1-risk_i)
```

Company Blast Radius `transmission_factor` is a structural path coefficient using hypothetical `initial_risk=1.0`; it is not current risk or classifier confidence.

### Risk history semantics

`GET /risk/{company_id}/history` reconstructs a chronological cumulative series from timestamped Event exposure. It is **not** a persisted wall-clock risk snapshot ledger. The service now deduplicates multiple paths for the same event by retaining the strongest path before emitting one point for that event, matching current-risk semantics.

## Public Backend Surface

```text
GET  /health
GET  /api/v1/info
GET  /api/v1/health/detailed
GET  /api/v1/events
GET  /api/v1/events/{event_id}
GET  /api/v1/events/{event_id}/blast-radius
POST /api/v1/events/validate
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

Company filtering, global graph search, canonical frontend graph IDs, geographic coordinates, risk analytics, and evidence availability are implemented.

## Evidence / Provenance

The frontend does not require a separate evidence service at this stage. Evidence/provenance is surfaced through the existing Event, Network relationship, Risk Exposure, and Agent Intelligence contracts.

Evidence availability uses explicit states:

```text
AVAILABLE
PARTIAL
UNAVAILABLE
```

Missing metadata is not fabricated.

The final live provenance audit covered **119 relationships** and reports fields by relationship type because seeded, extracted, derived, and dynamic relationships have different evidence contracts.

Final Event provenance:

```text
total:            2
with_source:      2
with_timestamp:   2
with_confidence:  2
with_description: 2
core_evidence_complete: true
```

`core_evidence_complete` explicitly means **source + timestamp + confidence**. Description completeness is reported separately and was also 2/2. It must not be described as part of the core predicate unless the audit contract is changed.

## WebSocket Runtime

`WS /risk-stream` uses the in-process `ConnectionManager`.

Implemented/tested path:

```text
EventPipeline
→ linked companies
→ RiskAnalyticsService
→ RiskStreamService.publish_company_risk
→ risk.updated
→ /risk-stream client
```

The residual-hardening suite includes a same-process integration test for this path.

For live FYP mode, enable the FastAPI lifespan poller with:

```text
NEWS_POLLER_ENABLED=true
```

This avoids adding Redis or another broker solely for the FYP. A standalone poller running in a different process does not share the API process's in-memory WebSocket manager and must not be presented as cross-process streaming.

## Agentic Graph RAG

Implemented:

- structured LLM boundary,
- concrete OpenAI adapter,
- planner,
- natural-language-to-Cypher proposal generation,
- read-only Cypher validation,
- maximum-three-hop guardrails,
- Graph Inspector,
- event evidence assessment,
- grounded explanation,
- public `POST /api/v1/agent/query` API.

The final live environment reported:

```text
agent_llm: unconfigured
real_external_call_tested: false
```

This is intentional/truthful. A real external Agent call is environment-dependent and was **not** claimed as part of the final live pass.

## Detailed Health

`GET /api/v1/health/detailed` now reports runtime state for:

- Neo4j,
- Agent LLM configuration,
- WebSocket manager,
- same-process Event poller,
- Event classifier model availability,
- News API configuration.

The final live environment reported:

```text
neo4j:           healthy
agent_llm:       unconfigured
websocket:       available
event_poller:    disabled
event_classifier: available
news_api:        configured
```

Disabled/unconfigured optional components are reported explicitly rather than being falsely labelled healthy.

## Phase 0 Residual-Hardening Resolution

The reopened residual pass addressed the following issues:

1. **Dynamic Event severity** — deterministic rule-based severity assessment added; confidence remains separate.
2. **WebSocket runtime architecture** — optional same-process FastAPI lifespan poller added; same-process `risk.updated` integration test added.
3. **Taxonomy cleanup** — stale Agent display label removed; ingestion compatibility aliases retained intentionally.
4. **Evidence/provenance frontend usability** — explicit availability states added to existing surfaces; no unnecessary standalone evidence service added.
5. **Agent external runtime** — concrete adapter remains implemented; final external call honestly remains unverified because provider is unconfigured.
6. **Risk history semantics** — documented as reconstructed event-derived history and strongest-path-per-event deduplication added.
7. **Detailed health** — expanded and made dependency-testable/truthful.
8. **Facility resolution** — conservative behavior retained and precision tests strengthened.
9. **C4 audit semantics** — `core_evidence_complete` meaning clarified as source + timestamp + confidence; description reported separately.
10. **Final regression/live verification** — completed successfully.

## Final Verification

### Automated regression — RUN AND PASSED

```text
390 passed, 2 warnings in 68.42s
```

### Live graph-contract audit — RUN AND PASSED

- canonical IDs complete,
- 11/11 Location nodes geocoded,
- 119 relationships audited,
- Event core evidence complete,
- description 2/2.

### Strengthened live integration — RUN AND PASSED

```text
PHASE 0 LIVE INTEGRATION VERIFICATION PASSED
```

The live verifier exercised health/info, company/detail/network, risk/exposure/history/company Blast Radius, global search, Event list/detail/Event Blast Radius, Event validation, expected 404 behavior, invalid-depth validation, and WebSocket handshake against the configured FastAPI/Neo4j runtime.

The Agent external provider remained unconfigured and therefore was correctly recorded as environment-dependent rather than falsely counted as a successful external call.

## Phase Boundary

**Phase 0 residual hardening is verified complete on the feature branch and is ready to merge to `main`.**

React/frontend Phase 1 has **not started**. Do not begin it without explicit approval.
