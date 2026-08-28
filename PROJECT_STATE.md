# Project State

## 1. Project

**Name:** Semiconductor Market Risk & Prediction Engine via Knowledge Graphs

**Type:** Final Year Project

**Primary Goal:**
Build a knowledge-graph-driven system that models semiconductor supply-chain dependencies, detects market and geopolitical events, and propagates risk through multi-hop supply-chain relationships.

---

## 2. Current Phase

**Phase:** 1 — Foundation

**Current Milestone:** Day 5 — Graph Infrastructure

**Current Git Commit:** `c21b45a`

**Current Branch:** `main`

**Remote Status:** `main` is ahead of `origin/main` by 2 commits.
---

## 3. Architectural Overview

```text
SEC Filings ───────────────┐
                           │
                           ▼
                    Ingestion Layer
                           │
                           ▼
                 NLP / Transformation
                           │
              ┌────────────┴────────────┐
              │                         │
        Entity Extraction         Event Extraction
              │                         │
              └────────────┬────────────┘
                           ▼
                Entity Resolution /
                Canonicalization /
                    Validation
                           │
                           ▼
                 Knowledge Graph
                      (Neo4j)
                           │
                           ▼
                    Risk Engine
                           │
                           ▼
                    FastAPI API
                           │
                           ▼
                      Dashboard
```

Financial news enters through the event-driven pipeline and produces validated events that update the Knowledge Graph and can trigger graph-based risk propagation.

---

## 4. Architectural Principles

### Knowledge Graph as Source of Truth

Neo4j stores validated entities, relationships, events, and associated metadata required for structural reasoning.

### Deterministic Graph Reasoning

Risk propagation should rely on deterministic graph structure and validated relationships rather than treating probabilistic language-model output as the source of truth.

### Separation of Responsibilities

The system is being developed as separate layers:

* Domain/event models
* Event creation and serialization
* Ingestion
* Extraction
* Normalization
* Graph persistence
* Risk analysis
* Prediction
* API
* Utilities/configuration

Existing functionality should be reused rather than reimplemented using a different technique.

---

## 5. Implemented Components

### Configuration

Implemented:

```text
src/config/
├── settings.py
├── logging.py
└── validation.py
```

Environment configuration is provided through `.env` and `.env.example`.

---

### Event Domain

Implemented:

```text
src/events/
├── types.py
├── models.py
├── factory.py
├── serialization.py
└── __init__.py
```

Current event model:

`SupplyChainEvent`

Core fields include:

* `event_type`
* `source`
* `timestamp`
* `entity_id`
* `severity`
* `payload`
* `event_id`
* `created_at`

Supported event types and severity levels are defined in `types.py`.

Events are created through the existing `create_event()` factory.

Events are serialized through the existing serialization utilities.

---

### Graph Infrastructure

Neo4j has been integrated using Docker.

Current infrastructure:

```text
Docker Compose
      │
      ▼
Neo4j 5 Community
      │
      ├── Browser: localhost:7474
      └── Bolt: localhost:7687
```

Python uses the Neo4j driver.

Existing graph connection component:

```text
src/graph/connection.py
```

Existing integration test:

```text
tests/test_neo4j.py
```

The integration test currently verifies:

1. Python can connect to Neo4j.
2. A test `Company` node can be created.
3. The node can be read.
4. Temporary test data is deleted.
5. The connection is closed.

---

## 6. Current Repository Structure

```text
event-driven-supply-chain-risk/
│
├── data/
│
├── docs/
│   └── architecture/
│       ├── architecture.drawio
│       ├── architecture.drawio.png
│       └── architecture_notes.md
│
├── src/
│   ├── api/
│   ├── config/
│   ├── events/
│   ├── extraction/
│   ├── graph/
│   ├── ingestion/
│   ├── normalization/
│   ├── prediction/
│   ├── risk/
│   └── utils/
│
├── tests/
│   ├── __init__.py
│   └── test_neo4j.py
│
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
├── requirements.txt
└── PROJECT_STATE.md
```

Some application directories currently contain only their initial package structure/README and have not yet been implemented.

---

## 7. Git Milestones

```text
b47b0d7  chore: initialize project structure
ae1027f  docs: add system architecture
6930210  docs: refine system architecture and event flow
bd9a7aa  chore: set up Python environment and dependencies
8439be9  chore: add environment configuration template
03b73e4  feat: establish application configuration layer
dda0dc6  feat: add supply chain event domain models
fc9002d  feat: add event factory and serialization
c30aee2  feat: integrate Neo4j graph database
9ea5140  docs: add project state tracking
c21b45a  feat: add Neo4j graph repository
```

---

## 8. Important Existing Decisions

* Python is the primary implementation language.
* Neo4j is the Knowledge Graph database.
* Docker Compose is used for local Neo4j infrastructure.
* The official Neo4j Python driver is used for Python-to-Neo4j communication.
* `SupplyChainEvent` is the existing normalized event domain object.
* `create_event()` is the existing event factory and should be reused.
* Event serialization already exists and should be reused.
* Graph database access should remain separate from domain/event logic.
* Tests are kept outside `src/`.
* Environment secrets are stored through `.env` and should not be committed.

---

## 9. Current Graph Layer

Currently implemented:

```text
src/graph/

├── connection.py
├── repository.py
└── README.md

The connection layer is responsible only for establishing and closing the Neo4j driver connection and verifying connectivity.

A graph repository/persistence layer has **not yet been implemented**.

Therefore, the next graph implementation should build on `Neo4jConnection` rather than creating another independent Neo4j connection mechanism.

---

## 10. Rules for Future Development

Before implementing or changing functionality:

1. Inspect the existing source code.
2. Inspect relevant tests.
3. Inspect relevant documentation.
4. Inspect relevant Git history when previous implementation decisions matter.
5. Reuse existing components where appropriate.
6. Do not introduce a second implementation of an existing responsibility without a clear architectural reason.
7. Make changes incrementally.
8. Run the relevant tests after each meaningful change.
9. Review `git diff` and `git diff --check`.
10. Commit completed milestones with clear commit messages.
11. Update this document whenever the project's architectural state materially changes.

---

## 11. Current Known Issues

Only verified issues should be recorded here.

At the current baseline, no unresolved implementation issue is blocking the graph infrastructure milestone.

Documentation contains a few textual/encoding artifacts in `architecture_notes.md`; these are not currently treated as implementation blockers and should not be mixed into unrelated development work.

---

## 12. Immediate Next Objective

Day 5 graph persistence has been implemented and verified.

Current architecture:

```text
SupplyChainEvent
        +
Neo4jConnection
        ↓
GraphRepository
        ↓
Neo4j Knowledge Graph
```

Before implementation, inspect all relevant existing graph/event code and define the repository responsibility so that domain logic and database logic remain separated.
