# Project State

## Project

**Name:** Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs

**Type:** Computer Science Final Year Project

**Goal:** Detect supply-chain disruption events, maintain a dynamic Neo4j knowledge graph, propagate direct and indirect risk across multi-tier supplier networks, and provide explainable graph-grounded intelligence through APIs, WebSockets, Agentic Graph RAG, and a React frontend.

**Industry scope:** Semiconductors, EV/batteries, and aerospace/electronics.

## Current State — 2026-09-16

The roadmap is implemented through **Day 53 (Agentic Graph RAG grounded explanations)**. The **Phase 0 frontend/repository/API readiness audit is complete**. React frontend implementation has not started and requires explicit approval before beginning.

Phase 0 Priority A, Priority B, and Priority C are complete.

Latest verified full regression: **372 tests passed**. The C6 full live integration verifier also passed against the live system.

## Implemented Architecture

```text
SEC 10-K → Async crawler → Parser → spaCy → Resolution/validation → Neo4j baseline KG
Financial News → Poller/dedup → DistilBERT → spaCy → Dynamic Event → AFFECTS/OCCURS_AT
Dynamic KG → Directed SUPPLIES traversal → 1/2/3-hop risk → FastAPI REST/WebSockets
User query → Structured LLM → Cypher validator → Graph inspector → Grounded explanation
```

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

Canonical IDs use `company_id`, `facility_id`, `product_id`, `material_id`, `technology_id`, `industry_id`, `location_id`, `country_id`, and `event_id`. Live graph auditing verified canonical-ID completeness and complete latitude/longitude pairs for all 11 Location nodes.

## Event System

Canonical event types are `SUPPLY_DISRUPTION`, `REGULATION_CHANGE`, `FACILITY_OUTAGE`, `TECHNOLOGY_EMBARGO`, `TRADE_POLICY_CHANGE`, and `QUOTA_CHANGE`.

Canonical severities are `unknown`, `low`, `medium`, `high`, and `critical`.

The news pipeline performs classification, NLP/entity resolution, Event persistence, automatic company `AFFECTS` linking, and conservative automatic `OCCURS_AT` linking for explicit known facility mentions.

## Risk Engine

Severity risk mapping:

```text
unknown=0.00  low=0.25  medium=0.50  high=0.75  critical=1.00
```

Path risk:

```text
initial_risk × product(dependency_weights) × 0.70^(hop-1)
```

Propagation follows directed downstream `SUPPLIES` paths up to three hops. Multiple events use strongest-path-per-event followed by `1 - product(1-risk_i)` aggregation. Historical risk series can be reconstructed from timestamped exposures.

## Public Backend Surface

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

Company filtering, global graph search, typed provenance structures, detailed health, canonical frontend graph IDs, and geographic coordinates are implemented.

## Agentic Graph RAG

Implemented: structured LLM adapter, natural-language-to-Cypher proposals, read-only Cypher validation, 3-hop guardrails, graph inspection, event evidence, grounded explanations, and the public agent query API. Neo4j remains the structural source of truth and deterministic risk mathematics remains outside the LLM.

## Phase 0 Audit Status

### Priority A — Complete (8/8)

Event reads; event blast radius; taxonomy alignment; severity alignment; event→risk→WebSocket wiring; public agent API; production StructuredLLM; agent severity compatibility.

### Priority B — Complete (8/8)

Typed provenance structures; global search; company filters; detailed health; historical risk; geographic coordinate contract; automatic facility `OCCURS_AT`; canonical graph-ID completeness.

### Priority C — Complete (6/6)

- C1 README alignment — complete
- C2 PROJECT_STATE alignment — complete
- C3 Supplier ontology documentation correction — complete
- C4 Live provenance completeness verification — complete
- C5 Local working-tree verification — complete
- C6 Full live integration verification — complete

C4 verified relationship and Event provenance completeness in the live graph. C5 verified the local `main` working tree was clean and synchronized before C6 work. C6 exercised the live backend/Neo4j integration and exposed production-path defects in global search, canonical network ID serialization, and the network relationship contract; those defects were corrected and the automated regression suite remained at 372 passing tests before the final live verifier passed.

## Runtime Caveat

The current WebSocket connection manager is in-memory. Event-to-risk publication works when the poller and FastAPI application share a process/runtime. Multi-process deployment requires shared external pub/sub for cross-process delivery.

Production LLM-backed Agentic RAG depends on valid runtime LLM provider configuration; deterministic graph inspection, validation, and grounded explanation components remain separately implemented and tested.

## Next Boundary

**Phase 0 is complete.** The next roadmap boundary is the React frontend implementation stage. Do not begin it without explicit approval.
