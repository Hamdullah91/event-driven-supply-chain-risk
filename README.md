# Event-Driven Supply Chain Risk Intelligence

**Dynamic Knowledge Graphs · Real-Time Event Detection · Multi-Hop Risk Propagation · Agentic Graph RAG**

Final Year Project for detecting supply-chain disruption events, maintaining a dynamic multi-tier Neo4j knowledge graph, and measuring direct and indirect risk exposure.

## Architecture

```text
SEC 10-K → Async Crawler → Parser → spaCy → Entity Resolution → Neo4j Baseline KG
News API → Deduplication → DistilBERT → spaCy → Severity Assessment → Validation → Dynamic Neo4j Events
Dynamic KG → 3-Hop Distance-Decay Risk Engine → FastAPI REST / WebSockets
User Query → Agentic RAG → Cypher Generator → Safety Validator → Neo4j → Grounded Explanation
```

Phase 0 repository/backend/frontend-contract readiness and the residual runtime-hardening pass are complete. React frontend implementation has not started yet.

## Scope

- Semiconductors, EV/batteries, and aerospace/electronics
- Approximately 50 core companies plus facilities and multi-tier dependencies
- SEC-derived structural evidence and dynamic news events
- Maximum 3-hop structural/risk traversal

## Canonical Knowledge Graph Ontology

Node labels:

`Company` · `Facility` · `Product` · `Material` · `Technology` · `Industry` · `Location` · `Country` · `Event`

**Supplier is a role, not a node label.** A supplier is represented as a `Company` participating in a supply relationship:

```text
(:Company)-[:SUPPLIES]->(:Company)
```

Legal relationships include:

`SUPPLIES` · `DEPENDS_ON` · `OPERATES` · `OWNS` · `USES` · `PRODUCES` · `OPERATES_IN` · `LOCATED_IN` · `AFFECTS` · `OCCURS_AT`

Canonical graph identities use domain IDs such as `company_id`, `facility_id`, `product_id`, `material_id`, `technology_id`, `industry_id`, `location_id`, `country_id`, and `event_id`. Geographic `Location` nodes support latitude/longitude coordinates. The final live audit verified canonical-ID completeness and 11/11 geocoded Location nodes.

## Event System

Canonical event categories:

- `SUPPLY_DISRUPTION`
- `REGULATION_CHANGE`
- `FACILITY_OUTAGE`
- `TECHNOLOGY_EMBARGO`
- `TRADE_POLICY_CHANGE`
- `QUOTA_CHANGE`

Canonical severities are `unknown`, `low`, `medium`, `high`, and `critical`.

New news events use a deterministic rule-based severity assessor based on disruption language/context. Severity is deliberately separate from DistilBERT classifier confidence. The assessment rationale is retained with event context. Historical Event nodes are not rewritten merely to conform to newer inference behavior, so older test/integration events may retain legacy event labels or `unknown` severity.

News events are classified, processed by NLP/entity resolution, persisted as timestamped `Event` nodes, and automatically linked to resolved companies through `AFFECTS`. Explicit known facility mentions can also be linked through `OCCURS_AT`; facility matching remains intentionally conservative to avoid ambiguous/fuzzy false positives.

## Risk Propagation

The deterministic risk engine propagates downstream across directed `SUPPLIES` relationships for at most three hops.

```text
Path Risk = Initial Event Risk × Product(Dependency Weights) × Distance Decay
Distance Decay = 0.70^(hop - 1)
```

Severity mapping:

```text
unknown=0.00  low=0.25  medium=0.50  high=0.75  critical=1.00
```

For multiple events, the strongest path for each event is retained before cumulative aggregation:

```text
Company Risk = 1 - Product(1 - event_risk_i)
```

Historical risk is reconstructed from timestamped graph event exposures. It is an event-derived cumulative series, not a persisted wall-clock snapshot ledger. When the same event reaches a company through multiple paths, the strongest path for that event is retained before a history point is emitted.

Company Blast Radius `transmission_factor` is a structural path coefficient calculated with hypothetical `initial_risk=1.0`; it is not current event/company risk or classifier confidence.

## FastAPI Contracts

Implemented public backend capabilities include:

- `GET /health`
- `GET /api/v1/info`
- `GET /api/v1/health/detailed`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events/{event_id}/blast-radius`
- `POST /api/v1/events/validate`
- `GET /companies`
- `GET /companies/{company_id}`
- `GET /companies/{company_id}/network`
- `GET /api/v1/search`
- `GET /risk/{company_id}`
- `GET /risk/{company_id}/history`
- `GET /risk/{company_id}/blast-radius`
- `GET /risk/{company_id}/exposure`
- `POST /api/v1/agent/query`
- `WS /risk-stream`

Company filtering, global graph search, detailed service health, historical risk, event-originated blast radius, canonical frontend graph IDs/geographic coordinates, and explicit evidence-availability states are included.

Evidence is intentionally surfaced through the existing event, network, exposure, and intelligence contracts rather than through a separate evidence service. Availability is represented truthfully as `AVAILABLE`, `PARTIAL`, or `UNAVAILABLE`; missing provenance is not fabricated.

## Live WebSocket Runtime

`WS /risk-stream` uses the in-process connection manager and emits `risk.updated` messages after event-linked company risk is recalculated.

For the FYP live mode, the news poller can run as an optional FastAPI lifespan background task using `NEWS_POLLER_ENABLED=true`. This intentionally keeps the poller, risk publisher, and WebSocket clients in one process so they share the same connection manager without introducing Redis/message-broker infrastructure.

The standalone poller script remains useful for worker/non-live workflows, but it must not be assumed to broadcast to WebSocket clients connected to a different API process.

## Agentic Graph RAG

Natural-language graph questions pass through structured query generation, Cypher validation, graph inspection, evidence assessment, and grounded explanation. Generated Cypher is restricted to safe read-only traversal patterns and graph evidence is used to construct the final explanation.

A concrete OpenAI StructuredLLM adapter and public `POST /api/v1/agent/query` API are implemented. A real external provider call remains environment-dependent: the final Phase 0 runtime had `agent_llm=unconfigured`, so no external LLM call was claimed during final live verification.

## System Status

`GET /api/v1/health/detailed` reports truthful runtime states for Neo4j, Agent LLM configuration, WebSocket manager, same-process event poller, event classifier model availability, and News API configuration. A disabled or unconfigured optional service is reported as such rather than being presented as healthy.

## Technology Stack

Python, asyncio, httpx, Pydantic, spaCy, Transformers/DistilBERT, PyTorch, scikit-learn, Neo4j/Cypher, FastAPI, WebSockets, Git/GitHub, Docker Compose, pytest. React with vis.js/D3.js is planned for the frontend implementation phase.

## Current Implementation Status

### Implemented

- Python/Git/Docker/Neo4j foundation
- Final graph ontology, constraints, canonical IDs and baseline topology
- Async SEC ingestion, parsing, NLP extraction, entity resolution, validation and provenance-aware graph ingestion
- Fine-tuned DistilBERT event classification pipeline
- Financial-news polling, deduplication, NLP, deterministic severity assessment and dynamic event injection
- Event-to-company linking and conservative explicit facility `OCCURS_AT` linking
- 1/2/3-hop distance-decay propagation and cumulative multi-event aggregation
- Risk scenario evaluation and event-derived historical risk
- FastAPI graph, event, risk, search, health and agent endpoints
- Same-process live WebSocket risk-stream architecture and event-to-risk publication path
- Agentic Graph RAG with structured LLM integration, Cypher safety validation, graph inspection and grounded explanations
- Explicit evidence availability on frontend-facing graph/event/risk/intelligence surfaces
- Phase 0 frontend/repository/API readiness audit and residual runtime hardening
- Live provenance, graph-contract, API/Neo4j and WebSocket verification

### Not yet started

- React frontend implementation
- Final frontend/backend integration and final system evaluation/documentation

## Data Quality Principles

- Canonical entity identifiers
- Evidence-backed relationships
- Provenance preservation
- Conservative entity/facility resolution
- Ontology-aware validation
- Duplicate prevention
- No fabricated relationships or evidence for coverage
- Deterministic risk mathematics grounded in graph topology
- Classifier confidence and Event severity remain separate concepts

## Testing and Final Phase 0 Verification

Final reopened-Phase-0 regression gate:

```text
390 passed, 2 warnings in 68.42s
```

Run the automated suite with:

```powershell
pytest -q
```

The final live graph audit verified:

- canonical IDs complete for all nine canonical labels,
- 11/11 Location nodes geocoded with valid complete coordinate pairs,
- 119 relationships audited with evidence semantics reported by relationship type,
- 2/2 Event nodes with source, timestamp, confidence, and description,
- Event `core_evidence_complete=true`, where core evidence explicitly means source + timestamp + confidence and description is reported separately.

The strengthened live verifier ended with:

```text
PHASE 0 LIVE INTEGRATION VERIFICATION PASSED
```

It verified live FastAPI/Neo4j health/info, company/detail/network, risk/exposure/history/blast radius, global search, event list/detail/blast radius, validation, expected 404/invalid-depth behavior, and WebSocket handshake. The Agent provider was truthfully reported as unconfigured, so a real external LLM call was not claimed.

The live Neo4j database still contains historical pre-hardening integration events with legacy `facility_shutdown` labels and/or `unknown` severity. These are retained as historical data rather than rewritten; new pipeline events use the canonical taxonomy and deterministic severity assessment.

## Objective

Build an explainable event-driven supply-chain intelligence system that identifies disruptions, connects them to a dynamic knowledge graph, measures direct and indirect exposure, and produces graph-grounded risk intelligence across multi-tier supplier networks.
