# System Architecture Notes

## 1. Purpose

The Semiconductor Market Risk & Prediction Engine models semiconductor supply-chain dependencies using a Knowledge Graph and propagates market and geopolitical risk through multi-hop relationships.

## 2. Data Sources

### SEC Filings

SEC 10-K and 10-Q filings provide historical and baseline information about companies, suppliers, manufacturing relationships, facilities, materials, and dependencies.

### Financial News

Financial and geopolitical news provides incremental events that may change the risk state of entities already represented in the Knowledge Graph.

## 3. Data Processing

The ingestion layer processes SEC filings in batch and financial news through an event-driven pipeline.

The NLP and transformation layer performs entity extraction, relationship extraction, event extraction, entity resolution, canonicalization, validation, and provenance tracking.

## 4. Knowledge Graph

Neo4j stores the validated entities, relationships, events, and associated metadata required for structural reasoning.

## 5. Risk Engine

The graph risk engine performs multi-hop graph traversal and risk propagation using techniques such as BFS, PageRank, path weighting, and graph-based exposure analysis.

## 6. API Layer

FastAPI provides application interfaces for graph queries, risk analysis, event processing, and analytics consumed by the dashboard.

## 7. Dashboard

The dashboard visualizes the Knowledge Graph, risk levels, event timelines, and supply-chain blast radius.

## 8. Event-Driven Flow

A new financial or geopolitical event enters through the news pipeline, is transformed into a validated event representation, updates the Knowledge Graph, triggers graph-based risk propagation, and produces updated risk information for the dashboard.

## 9. Architectural Principle

The system prioritizes deterministic graph structure and validated relationships for risk propagation rather than relying on probabilistic language-model output as the source of truth.