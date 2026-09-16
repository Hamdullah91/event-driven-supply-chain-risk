# Event-Driven Supply Chain Risk Intelligence

**Dynamic Knowledge Graphs · Real-Time Event Detection · Multi-Hop Risk Propagation · Agentic Graph RAG**

Final Year Project for detecting supply-chain disruption events, maintaining a dynamic multi-tier Neo4j knowledge graph, and measuring direct and indirect risk exposure.

## Architecture

```text
SEC 10-K → Async Crawler → Parser → spaCy → Entity Resolution → Neo4j Baseline KG
News API → Deduplication → DistilBERT → spaCy → Validation → Dynamic Neo4j Events
Dynamic KG → 3-Hop Distance-Decay Risk Engine → FastAPI REST / WebSockets
User Query → Agentic RAG → Cypher Generator → Safety Validator → Neo4j → Grounded Explanation
```

The backend/frontend contract readiness audit (Phase 0) is complete. React frontend implementation has not started yet.

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

Canonical graph identities use domain IDs such as `company_id`, `facility_id`, `product_id`, `material_id`, `technology_id`, `industry_id`, `location_id`, `country_id`, and `event_id`. Geographic `Location` nodes support latitude/longitude coordinates.

## Event System

Canonical event categories:

- `SUPPLY_DISRUPTION`
- `REGULATION_CHANGE`
- `FACILITY_OUTAGE`
- `TECHNOLOGY_EMBARGO`
- `TRADE_POLICY_CHANGE`
- `QUOTA_CHANGE`

Canonical severities are `unknown`, `low`, `medium`, `high`, and `critical`.

News events are classified, processed by NLP/entity resolution, persisted as timestamped `Event` nodes, and automatically linked to resolved companies through `AFFECTS`. Explicit known facility mentions can also be linked through `OCCURS_AT`.

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

Historical risk can be reconstructed from timestamped graph event exposures.

## FastAPI Contracts

Implemented public backend capabilities include:

- `GET /health`
- `GET /api/v1/health/detailed`
- `GET /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events/{event_id}/blast-radius`
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

Company filtering, global graph search, typed agent provenance, detailed service health, historical risk, event-originated blast radius, and frontend-ready graph IDs/geographic coordinates are included.

## Agentic Graph RAG

Natural-language graph questions pass through structured query generation, Cypher validation, graph inspection, and grounded explanation. Generated Cypher is restricted to safe read-only traversal patterns and graph evidence is used to construct the final explanation.

## Technology Stack

Python, asyncio, httpx, Pydantic, spaCy, Transformers/DistilBERT, PyTorch, scikit-learn, Neo4j/Cypher, FastAPI, WebSockets, Git/GitHub, Docker Compose, pytest. React with vis.js/D3.js is planned for the frontend implementation phase.

## Current Implementation Status

### Implemented

- Python/Git/Docker/Neo4j foundation
- Final graph ontology, constraints, canonical IDs and baseline topology
- Async SEC ingestion, parsing, NLP extraction, entity resolution, validation and provenance-aware graph ingestion
- Fine-tuned DistilBERT event classification pipeline
- Financial-news polling, deduplication, NLP and dynamic event injection
- Event-to-company linking and explicit facility `OCCURS_AT` linking
- 1/2/3-hop distance-decay propagation and cumulative multi-event aggregation
- Risk scenario evaluation
- FastAPI graph, event, risk, search, health and agent endpoints
- WebSocket risk-stream infrastructure and event-to-risk publication path
- Agentic Graph RAG with structured LLM integration, Cypher safety validation, graph inspection and grounded explanations
- Phase 0 frontend/repository/API readiness audit, including Priorities A, B and C
- Live provenance, clean working-tree, and full live integration verification

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
- No fabricated relationships for coverage
- Deterministic risk mathematics grounded in graph topology

## Testing

The latest Phase 0 regression gate passed **372 tests**. Run the automated suite with:

```powershell
pytest -q
```

Live Neo4j audits/integration checks are performed separately where unit tests alone cannot verify database completeness. The Phase 0 C6 live integration verifier passed after validating the live API/graph integration path.

## Objective

Build an explainable event-driven supply-chain intelligence system that identifies disruptions, connects them to a dynamic knowledge graph, measures direct and indirect exposure, and produces graph-grounded risk intelligence across multi-tier supplier networks.
