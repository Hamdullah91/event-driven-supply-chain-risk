# Frontend Phase 1 Implementation Handoff

## Project

Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs

## Phase

Frontend Phase 1 — UX Layout & Visual System Blueprint

## Status

Phase 1 visual implementation candidate complete pending final local verification.

## Source-of-Truth Order

1. Current executable backend/frontend code
2. Current schemas and API contracts
3. Phase 0 frontend repository/API audit
4. Phase 1 UX Layout & Visual System Blueprint
5. Older README/project-state/chat assumptions

## Primary Navigation

Exactly six top-level sections:

1. Overview
2. Events
3. Network
4. Companies
5. Risk Analysis
6. Intelligence

## Implemented Phase 1 Surfaces

### Overview

Command-center layout containing disruption context, risk landscape,
propagation spotlight, and broader context.

Unsupported aggregate values remain unavailable or development-only.

### Events

Desktop master-detail visual architecture.

Currently development/mock-backed because system-wide event read APIs are
not yet publicly available.

### Network

Two visually separate modes:

- Structure
- Impact

Blast Radius is nested inside Impact.

The current graph is a static Phase 1 visual fixture.

A later implementation pass should replace the static renderer with an
interactive graph library such as vis-network, using Neo4j-backed data
through FastAPI.

### Companies

Company directory and full Company Profile layout.

Company profile includes:

- current risk
- contributing events
- exposure paths
- focused network area
- facilities
- products
- materials
- technologies
- evidence

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

Geography does not invent coordinates.

Historical risk controls are unavailable until a backend history contract
exists.

### Intelligence

Graph-grounded analytical workspace containing:

- query composer
- grounded answer
- supporting graph/path
- supporting entities
- risk trace
- evidence

Query submission remains disabled until a public Agentic RAG API exists.

## Entity Inspector

Permanent contextual right-side Inspector.

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

Current context is development-backed.

Detailed interaction behavior belongs to Phase 2.

## Frozen Risk Terminology

- NONE
- LOW
- MEDIUM
- HIGH
- CRITICAL

The frontend does not independently calculate authoritative risk.

## Graph Rules

Structure and risk propagation remain separate concepts.

Structure may use multiple structural relationship types.

Risk propagation follows downstream SUPPLIES semantics and a maximum
three-hop model.

Relationship direction must be preserved.

## Blast Radius Rule

Blast Radius belongs inside Network → Impact.

Backend transmission_factor must not be mislabeled as aggregate/current
company risk.

## Evidence Rule

Never invent evidence.

Unavailable evidence must display:

Not available

## Geography Rule

Never invent coordinates.

Geography remains secondary to graph analysis.

## Current Backend Gaps Relevant to Frontend

- system-wide Event read/detail APIs
- event-originated Blast Radius
- global multi-entity search
- public Intelligence/Agent API
- confirmed concrete live LLM provider
- historical risk series
- strongly typed evidence endpoint
- rich per-service health
- verified geographic coordinates
- complete production WebSocket event-to-stream wiring

## Development Fixtures

Development/demo data is isolated under src/data and must remain clearly
identified as non-production information.

## Deferred Graph Upgrade

The static Phase 1 graph renderer is not the intended final graph engine.

Later implementation should use vis-network / vis.js, Cytoscape, Sigma,
or another appropriate graph renderer.

The preferred current direction is vis-network because the project requires:

- draggable nodes
- physics layout
- zoom
- pan
- directed relationships
- node selection
- relationship selection
- Entity Inspector integration
- Structure / Impact visual modes
- Neo4j-backed graph rendering

## Phase 2 Boundary

Phase 2 should define interaction details, including:

- entity click behavior
- graph expansion
- Structure / Impact switching behavior
- Blast Radius interaction
- filters
- search
- path highlighting
- Inspector behavior
- Events master-detail behavior
- real-time update behavior
- Intelligence-to-graph actions
- context preservation

Phase 2 must build on Phase 1 rather than redesign it.