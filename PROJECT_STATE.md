# Project State

## 1. Project
Name: Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs

Type: Final Year Project

Primary Goal:

Build an event-driven, knowledge-graph-based supply-chain risk intelligence system that models multi-tier dependencies, detects operational/geopolitical/supply-chain events, dynamically updates a Neo4j knowledge graph, and calculates multi-hop downstream risk exposure.

The project focuses on three industries:

Semiconductors
EV Batteries
Aerospace & Electronics

The target baseline consists of approximately 50 core companies plus their suppliers, facilities, products, materials, technologies, and geographic dependencies.

## 2. Current Phase

**Phase:** 4 — SEC EDGAR Ingestion

**Current Milestone:** Day 16 — Async SEC EDGAR 10-K Crawler

**Completed Through:** Day 16

**Phase 4 Status:** IN PROGRESS — Days 15–16 Complete

**Current Git Commit:** 8747157 — feat: build baseline supply chain knowledge graph

**Current Branch:** main

**Remote Status:** Day 16 changes are currently local and awaiting final commit/push.

**Project State Snapshot Date:** 2026-09-02

### Current Verification State

Full automated test suite:

- 15 tests collected
- 15 tests passed
- 0 failures
- 0 errors

Verified components include:

- Neo4j connectivity and CRUD
- GraphRepository event persistence
- SEC CIK normalization
- SEC recent 10-K discovery
- SEC historical filing fallback
- SEC Retry-After handling
- HTTP 429 retry handling
- HTTP 5xx retry handling
- network-error retry handling
- retry exhaustion
- 404 handling
- non-retryable HTTP error handling

## 3. Architectural Overview
                         BASELINE PIPELINE

SEC EDGAR 10-K Filings
          │
          ▼
   Async Ingestion
          │
          ▼
 Parsing / Cleaning
          │
          ▼
      spaCy NLP
          │
    ┌─────┴─────┐
    │           │
 Entities   Relationships
    │           │
    └─────┬─────┘
          ▼
 Entity Resolution
          │
          ▼
 Schema Validation
          │
          ▼
 Neo4j Baseline KG


                         EVENT PIPELINE

Financial News APIs
          │
          ▼
 15-Minute Poller
          │
          ▼
  Deduplication
          │
          ▼
   DistilBERT
 Event Classification
          │
          ▼
      spaCy NLP
          │
          ▼
 Entity Resolution
          │
          ▼
 Schema Validation
          │
          ▼
 Dynamic Event Injection
          │
          ▼
        Neo4j


                         RISK PIPELINE

Dynamic Neo4j KG
       │
       ▼
3-Hop Graph Traversal
       │
       ▼
Distance-Decay Risk Engine
       │
       ▼
    FastAPI
   REST / WebSockets
       │
       ▼
 React Dashboard
 Graph / Blast Radius /
 Risk Heatmap / Event Feed


                         QUERY PIPELINE

Natural-Language Query
          │
          ▼
     Agentic RAG
          │
          ▼
    Cypher Generator
          │
          ▼
 Cypher Safety Validator
          │
          ▼
   Neo4j Traversal
          │
          ▼
Grounded Risk Explanation

The knowledge graph remains the structural source of truth.

LLMs may generate queries and explanations, but supply-chain dependencies and propagated risk must ultimately be grounded in validated graph relationships and deterministic graph traversal.

4. Architectural Principles
Knowledge Graph as Source of Truth

Neo4j stores validated entities, supply-chain relationships, geographic relationships, events, and provenance information required for structural reasoning.

The LLM does not invent supply-chain paths.

Deterministic Graph Reasoning

Multi-hop risk analysis must be derived from graph topology.

The intended risk model is based conceptually on:

Initial Event Risk
        ×
Relationship / Dependency Weight
        ×
Distance Decay
        =
Propagated Risk

Propagation is limited to a maximum of three hops for the FYP implementation.

Event-Driven Architecture

The baseline graph represents relatively stable supply-chain topology.

Dynamic disruptions are represented separately as timestamped Event entities and attached to affected graph entities.

This allows the graph to maintain both:

Structural Knowledge
+
Dynamic Risk Events
Separation of Responsibilities

The system is divided into separate layers:

Configuration
Domain/event models
SEC ingestion
News ingestion
Text parsing
Entity extraction
Relationship/triplet extraction
Entity resolution
Schema validation
Graph persistence
Event classification
Risk propagation
Agentic graph retrieval
API
Visualization
Utilities

Existing functionality should be reused rather than reimplemented using parallel mechanisms.

Supplier Is a Role

Supplier is not a separate final node type.

A supplier is represented as a Company participating in a supply relationship:

(:Company)-[:SUPPLIES]->(:Company)

This avoids representing the same organization as both a Company and a Supplier and simplifies entity resolution and graph traversal.

Provenance-Aware Relationships

Structural relationships seeded manually or extracted later must preserve evidence metadata.

Current relationship provenance fields include:

source_type
source_url
verification_status
confidence
derivation

derivation is used where a relationship is inferred deterministically from another verified graph relationship.

Example:

SUPPLIES   = directly supported by source evidence
DEPENDS_ON = derived inverse of a verified SUPPLIES relationship

This avoids presenting graph-derived relationships as independently sourced facts.

5. Implemented Components
Configuration

Implemented:

src/config/
├── settings.py
├── logging.py
└── validation.py

Environment configuration is provided through:

.env
.env.example

Secrets must remain outside version control.

Event Domain

Implemented:

src/events/
├── types.py
├── models.py
├── factory.py
├── serialization.py
└── __init__.py

Existing normalized event model:

SupplyChainEvent

Core fields include:

event_type
source
timestamp
entity_id
severity
payload
event_id
created_at

Events should continue to be created through:

create_event()

Existing serialization utilities should be reused.

Graph Infrastructure

Neo4j is integrated using Docker Compose.

Docker Compose
      │
      ▼
Neo4j 5 Community
      │
      ├── Browser: localhost:7474
      │
      └── Bolt: localhost:7687

Python communicates with Neo4j through the official Neo4j driver.

Graph components now include:

src/graph/
├── connection.py
├── repository.py
├── seed.py
└── README.md

Existing integration testing includes:

tests/test_neo4j.py

The Neo4j integration has been verified from Python.

The graph repository remains the persistence boundary rather than placing Neo4j queries directly inside domain/event logic.

Neo4j Resource Configuration

Docker Compose now limits Neo4j resource consumption for the current development machine.

Configured values:

Initial heap: 512 MB
Max heap:     1 GB
Page cache:   512 MB
Container RAM limit: 2 GB
CPU limit:    2.0

This was added after local memory pressure caused Python Neo4j-driver imports to fail with MemoryError.

6. Final Ontology

The final ontology contains nine node labels:

Company
Facility
Product
Material
Location
Country
Event
Industry
Technology

Supplier is intentionally excluded as a node label and represented as a role of Company.

7. Final Relationship Dictionary

The legal relationship vocabulary finalized during Day 12 is:

Company Relationships
Company ──SUPPLIES──────> Company
Company ──DEPENDS_ON────> Company
Company ──OPERATES──────> Facility
Company ──OWNS──────────> Facility
Company ──USES──────────> Material
Company ──USES──────────> Technology
Company ──PRODUCES──────> Product
Company ──PRODUCES──────> Material
Company ──OPERATES_IN───> Industry
Geographic Relationships
Facility ──LOCATED_IN──> Location
Location ──LOCATED_IN──> Country
Event Relationships
Event ──AFFECTS───────> Company
Event ──AFFECTS───────> Facility
Event ──OCCURS_AT─────> Facility

Relationship direction is treated as semantically meaningful because later risk propagation depends on direction rather than simple adjacency.

8. Temporal Event Schema

Day 13 finalized the conceptual graph schema for dynamic events.

The Event node represents a timestamped operational, geopolitical, regulatory, technology, or supply-chain disruption.

Core event properties include:

event_id
event_type
timestamp
severity
source
confidence
description

Dynamic graph attachment uses:

Event ──AFFECTS────> Company
Event ──AFFECTS────> Facility
Event ──OCCURS_AT──> Facility

The event layer is intentionally separate from the structural baseline topology.

This preserves the distinction:

Baseline KG = relatively stable structural dependencies
Dynamic KG  = baseline topology + timestamped event nodes

Full real-time event ingestion remains scheduled for the later Dynamic Event Pipeline phase.

9. Baseline Graph Seed Layer

Day 14 introduced a reusable baseline seeding pipeline.

Seed data is stored under:

data/seed/
├── companies.json
├── company_dependencies.json
├── company_materials.json
├── company_products.json
├── company_technologies.json
├── countries.json
├── facilities.json
├── locations.json
├── materials.json
├── products.json
└── technologies.json

The seed loader is implemented in:

src/graph/seed.py

The loader reads JSON seed datasets and sends them through GraphRepository.

Conceptually:

JSON Seed Data
      │
      ▼
src.graph.seed
      │
      ▼
GraphRepository
      │
      ▼
Neo4j

This design keeps the initial manual baseline separate from persistence logic and allows later SEC/spaCy ingestion to reuse the same graph persistence boundary.

10. Baseline Graph Node Counts

Day 14 validation confirmed the following graph counts:

Company:     50
Facility:    13
Location:    11
Country:      6
Material:    11
Product:     10
Technology:  10
Industry:     3

The 50-company baseline is divided across the three target sectors:

Semiconductors:            20
EV Batteries:              15
Aerospace & Electronics:   15
11. Baseline Company Universe
Semiconductors — 20
TSMC
Samsung Electronics
Intel
NVIDIA
AMD
Qualcomm
Broadcom
Micron Technology
SK Hynix
Texas Instruments
Analog Devices
NXP Semiconductors
Infineon Technologies
STMicroelectronics
GlobalFoundries
ASML
Applied Materials
Lam Research
KLA
Tokyo Electron
EV Batteries — 15
Tesla
BYD
CATL
LG Energy Solution
Panasonic Energy
Samsung SDI
SK On
Rivian
Lucid
General Motors
Ford
Volkswagen
BMW
Albemarle
SQM
Aerospace & Electronics — 15
Boeing
Airbus
Lockheed Martin
RTX
Northrop Grumman
General Dynamics
Honeywell
GE Aerospace
Safran
Rolls-Royce Holdings
L3Harris Technologies
BAE Systems
Thales
Teledyne Technologies
TransDigm

Each company seed contains canonical identifiers and baseline metadata.

Key fields include:

company_id
name
legal_name
industry_id
entity_type
seed_source
12. Facility and Geographic Baseline

The baseline currently contains 13 verified facilities, 11 locations, and 6 countries.

Verified structural chain:

Company
   │
OPERATES
   ▼
Facility
   │
LOCATED_IN
   ▼
Location
   │
LOCATED_IN
   ▼
Country

Current facilities include:

TSMC Fab 18
TSMC Arizona
Intel Ocotillo
Intel Oregon
Intel Ireland
Micron Boise
Micron Manassas
Micron Singapore
GlobalFoundries Malta
GlobalFoundries Dresden
GlobalFoundries Singapore
ASML Veldhoven
Applied Materials Singapore

Current geographic validation:

Company -> Facility OPERATES:       13
Facility -> Location LOCATED_IN:    13
Location -> Country LOCATED_IN:     11

Total LOCATED_IN relationship count is therefore:

24
13. Material Baseline

The graph currently contains 11 baseline materials:

Silicon
Copper
Aluminum
Lithium
Nickel
Cobalt
Graphite
Manganese
Titanium
Carbon Fiber
Rare Earth Elements

Material categories distinguish semiconductor materials, industrial metals, battery materials, aerospace materials/composites, and critical materials.

14. Product Baseline

The graph currently contains 10 baseline products:

Semiconductor Chip
Microprocessor
Memory Chip
GPU
Lithium-Ion Battery
Battery Cell
Electric Vehicle
Aircraft
Aircraft Engine
Avionics System
15. Technology Baseline

The graph currently contains 10 baseline technologies:

Extreme Ultraviolet Lithography
Deep Ultraviolet Lithography
Advanced Semiconductor Packaging
FinFET
Lithium-Ion Battery Technology
Lithium Iron Phosphate Battery Technology
Nickel Manganese Cobalt Battery Technology
Electric Powertrain Technology
Turbofan Engine Technology
Avionics Technology
16. Verified Baseline Semantic Relationships

The current validated company semantic relationships are:

Company -> Product
NVIDIA       ──PRODUCES──> GPU
Boeing       ──PRODUCES──> Aircraft
GE Aerospace ──PRODUCES──> Aircraft Engine

Count:

PRODUCES: 3
Company -> Technology
Intel ──USES──> FinFET
TSMC  ──USES──> Advanced Packaging
Company -> Material
Albemarle ──USES──> Lithium
Boeing     ──USES──> Titanium
SQM        ──USES──> Lithium

Together, Company -> Material and Company -> Technology currently produce:

USES: 5
Supplier / Dependency Baseline

Verified supplier relationships:

ASML ──SUPPLIES──> TSMC
TSMC ──SUPPLIES──> NVIDIA

Derived inverse dependency relationships:

TSMC   ──DEPENDS_ON──> ASML
NVIDIA ──DEPENDS_ON──> TSMC

Counts:

SUPPLIES:    2
DEPENDS_ON:  2

The inverse DEPENDS_ON relationships are explicitly marked with:

source_type = "derived_from_verified_supplies"
derivation  = "inverse_of_SUPPLIES"

This keeps graph provenance clear.

17. Current Relationship Counts

Day 14 final validation returned:

OPERATES:      13
LOCATED_IN:    24
PRODUCES:       3
USES:           5
SUPPLIES:       2
DEPENDS_ON:     2
OPERATES_IN:   50

Event relationships are not expected yet because dynamic event injection belongs to a later phase.

18. Multi-Hop Traversal Validation

The baseline graph successfully demonstrated a real upstream dependency chain:

NVIDIA
   │
DEPENDS_ON
   ▼
TSMC
   │
DEPENDS_ON
   ▼
ASML

The Cypher traversal:

DEPENDS_ON*1..3

returned:

1 hop(s): NVIDIA -> TSMC
2 hop(s): NVIDIA -> TSMC -> ASML

This confirms that the baseline topology already supports the graph mechanism required for later multi-hop risk propagation.

The graph currently proves two hops with verified baseline data while retaining a maximum query depth of three hops for the final risk engine.

19. Graph Integrity Validation

Final Day 14 validation confirmed no duplicate canonical IDs for:

Company
Facility
Location
Country
Material
Product
Technology
Industry

All duplicate checks returned:

OK

Required structural orphan checks also passed:

Facility without Company:   0
Facility without Location:  0
Location without Country:   0
Company without Industry:   0

Final result:

PASS: Day 14 baseline graph validation successful.

Some Product, Material, or Technology nodes may intentionally remain unconnected until later ingestion expands the graph.

These are not considered structural validation failures.

20. Graph Constraints

The following uniqueness constraints are established:

company_id_unique
country_id_unique
event_id_unique
facility_id_unique
industry_id_unique
location_id_unique
material_id_unique
product_id_unique
supplier_id_unique
technology_id_unique

Although the final ontology no longer uses Supplier as a separate node label, the historical supplier constraint may still exist in the database from earlier graph-schema work.

The application architecture should not create new Supplier nodes.

21. Graph Repository State

GraphRepository now contains baseline graph persistence methods in addition to existing event persistence.

Implemented responsibilities include:

save_event
seed_companies
seed_facilities
seed_countries
seed_locations
seed_materials
seed_products
seed_technologies
seed_company_products
seed_company_technologies
seed_company_materials
seed_company_dependencies

Seed operations use MERGE for canonical nodes/relationships and MATCH for already-defined relationship endpoints where appropriate.

The use of MATCH prevents a misspelled relationship endpoint ID from silently creating an unintended graph entity.

## SEC EDGAR Ingestion Infrastructure

Days 15–16 introduced the first production-oriented external data ingestion subsystem.

Implemented package:

src/ingestion/sec/

├── __init__.py
├── client.py
├── crawler.py
├── models.py
└── rate_limiter.py

Executable crawler entry point:

scripts/crawl_sec.py

Tests:

tests/test_sec_client.py
tests/test_sec_crawler.py

### SEC Domain Models

The SEC ingestion layer introduces structured models for crawler targets, filing metadata, and download results.

Core models:

- CompanyTarget
- FilingMetadata
- DownloadResult

CompanyTarget normalizes SEC CIK identifiers into:

- SEC API representation: zero-padded 10-digit CIK
- SEC Archives representation: numeric CIK without leading zeros

Invalid CIK values are rejected before SEC requests are made.

### SEC HTTP Client

The asynchronous SEC client is implemented using:

httpx.AsyncClient

Responsibilities include:

- SEC-compliant User-Agent
- asynchronous HTTP requests
- global request-rate limiting
- timeout handling
- retry handling
- Retry-After support
- exponential backoff
- jitter
- network-error recovery
- retryable HTTP status handling
- non-retryable error handling
- JSON validation

Retryable HTTP status codes include:

408
425
429
500
502
503
504

HTTP 404 is represented separately through SECNotFoundError.

Other non-retryable HTTP failures are converted into SECClientError.

### SEC Rate Limiting

An AsyncRateLimiter controls outbound SEC requests.

Configured development rate:

8 requests per second

This intentionally remains below the SEC automated-access ceiling.

The limiter uses monotonic time, an asyncio lock, and request spacing to coordinate concurrent crawler tasks.

### SEC 10-K Discovery

The crawler first requests:

data.sec.gov/submissions/CIK##########.json

The recent filing collection is inspected for Form 10-K.

If no 10-K exists in the recent filing set, the crawler follows the historical submission files listed by the SEC and continues searching older filing metadata.

This provides:

Recent filings
      │
      ▼
Search for 10-K
      │
      ├── Found → Download
      │
      └── Not Found
              │
              ▼
      Historical submission files
              │
              ▼
          Search for 10-K
              │
              ▼
           Download

This fallback prevents the crawler from incorrectly assuming that the latest submissions JSON always contains the required filing.

### SEC Archive URL Construction

Once a filing is identified, the crawler constructs the SEC Archives URL from:

- numeric CIK
- accession number without dashes
- primary document name

The resulting filing document is downloaded directly from the SEC Archives.

### Raw Filing Storage

Raw filings are stored under:

data/raw/sec/<CIK>/<ACCESSION_NUMBER>/

Each successful crawl produces:

10-k.htm
metadata.json

The actual primary-document extension is preserved where appropriate.

Metadata includes:

- company name
- normalized CIK
- form
- accession number
- filing date
- report date
- primary document
- SEC source URL
- UTC download timestamp

### Atomic File Persistence

Raw filings and metadata use atomic-write behavior.

The crawler:

1. writes to a temporary file,
2. flushes data,
3. synchronizes the file,
4. atomically replaces the destination.

This reduces the risk of leaving partially written filing or metadata files after interrupted ingestion.

Successful validation confirmed no temporary `.tmp` files remained after crawler execution.

### Concurrent Company Crawling

The crawler supports multiple company targets through:

crawl_many()

Concurrency is bounded using:

asyncio.Semaphore

Current executable configuration:

max_concurrency = 3

Individual company failures are isolated.

A failure for one company does not terminate crawling for all other companies.

### Verified Live SEC Crawl

The crawler was successfully validated against real SEC EDGAR data for:

- Apple Inc.
- NVIDIA Corporation
- Advanced Micro Devices, Inc.

The crawler successfully:

- resolved company submissions
- identified latest 10-K filings
- generated SEC archive URLs
- downloaded raw filing documents
- stored filing metadata
- wrote persistent logs

### Crawler Logging

Persistent logs are written to:

data/logs/sec_crawler.log

Important lifecycle events include:

- crawl started
- filing discovered
- historical fallback
- retryable HTTP response
- network retry
- crawl completed
- crawl failure

The executable also reports final successful/failed/total company counts.
22. Day-by-Day Development State
Day 1 — Architecture

Status: COMPLETE

The high-level system architecture was finalized.

Major decisions:

Industry Scope:
Semiconductors
EV Batteries
Aerospace & Electronics

Data sources:

SEC EDGAR
Financial News APIs

Core architecture:

SEC → NLP → Baseline KG

News → Event Classification → NLP → Dynamic Events

Dynamic KG → Risk Propagation

Dynamic KG → Agentic RAG

Risk Engine → FastAPI → React

Risk propagation was constrained to three graph hops with distance decay.

Day 2 — Python Environment / Git / Project Structure

Status: COMPLETE

Established:

Python environment
virtual environment
Git repository
GitHub workflow
application directory structure
requirements.txt
.env
.env.example
.gitignore
configuration layer
Day 3 — Python Data / Event Foundation

Status: COMPLETE

Implemented the core event/domain foundation.

Key concepts covered and applied:

Python classes
typing
structured data
event models
event factories
JSON-compatible serialization
configuration
logging
exception-aware design

SupplyChainEvent became the normalized event representation.

Event construction remains centralized through:

create_event()
Day 4 — Async Python Foundation

Status: COMPLETE

Async Python concepts required for the ingestion architecture were covered:

async def
await
asyncio
httpx

The architectural purpose of async processing was established for network-bound ingestion workloads, particularly SEC EDGAR crawling and later financial-news polling.

Day 5 — Docker + Neo4j Infrastructure

Status: COMPLETE

Neo4j was deployed locally through Docker Compose.

Verified:

Neo4j Browser → localhost:7474
Bolt Driver   → localhost:7687

Python-to-Neo4j connectivity was established.

The graph connection layer was separated from application/domain logic.

Day 6 — Graph Theory Fundamentals

Status: COMPLETE

Graph theory fundamentals were studied specifically in the context of supply-chain networks.

Core concepts established:

Node
Edge
Directed relationship
Path
Hop
Degree
Weight
Traversal
BFS
DFS

This provides the theoretical basis for later three-hop risk propagation.

Day 7 — Neo4j / Cypher CRUD

Status: COMPLETE

Cypher fundamentals were learned and exercised.

Core operations covered:

CREATE
MATCH
MERGE
SET
DELETE
DETACH DELETE
RETURN

MERGE was identified as especially important for ingestion and entity deduplication.

Day 8 — Supply-Chain Relationships

Status: COMPLETE

The graph moved from isolated nodes toward a connected supply-chain model.

Important relationship concepts included:

SUPPLIES
DEPENDS_ON
LOCATED_IN
OPERATES
PRODUCES
USES
OWNS

Relationship direction and semantic meaning were kept explicit.

Day 9 — Multi-Hop Cypher Traversal

Status: COMPLETE

Cypher multi-hop traversal concepts were established.

The graph can represent and query:

1-hop
2-hop
3-hop

Variable-length path traversal provides the mechanism required for the later risk engine.

Day 10 — Constraints, IDs, Indexing & Graph Integrity

Status: COMPLETE

Graph integrity concepts were finalized before freezing the ontology.

Key decisions:

Canonical stable IDs
Uniqueness constraints
Indexes
Relationship metadata
Provenance

Names are treated as display properties rather than canonical identity.

Day 11 — Final Ontology

Status: COMPLETE

Final node labels:

Company
Facility
Product
Material
Location
Country
Event
Industry
Technology

The final supplier decision was frozen:

Supplier = Company acting in a SUPPLIES relationship

No separate final Supplier node is required.

Day 12 — Relationship Dictionary

Status: COMPLETE

The legal relationship vocabulary was finalized.

Company relationships:

Company ──SUPPLIES──────> Company
Company ──DEPENDS_ON────> Company
Company ──OPERATES──────> Facility
Company ──OWNS──────────> Facility
Company ──USES──────────> Material
Company ──USES──────────> Technology
Company ──PRODUCES──────> Product
Company ──PRODUCES──────> Material
Company ──OPERATES_IN───> Industry

Geographic relationships:

Facility ──LOCATED_IN──> Location
Location ──LOCATED_IN──> Country

Event relationships:

Event ──AFFECTS───────> Company
Event ──AFFECTS───────> Facility
Event ──OCCURS_AT─────> Facility

The vocabulary is now the schema reference for graph validation and later ingestion.

Day 13 — Temporal Event Schema

Status: COMPLETE

The graph representation of dynamic events was finalized.

Core event properties:

event_id
event_type
timestamp
severity
source
confidence
description

Event attachment semantics were finalized through:

AFFECTS
OCCURS_AT

Dynamic events remain separate from baseline structural knowledge.

The actual news-to-event injection pipeline is intentionally deferred to its roadmap phase.

Day 14 — Baseline Topology

Status: COMPLETE

The initial knowledge graph topology was constructed and validated.

Implemented:

50 core companies
3 industries
13 facilities
11 locations
6 countries
11 materials
10 products
10 technologies
JSON seed datasets
Python seed loader
graph repository seed methods
geographic topology
Company -> Industry topology
Product relationships
Technology relationships
Material relationships
Supplier relationships
derived dependency relationships
provenance metadata
duplicate validation
structural orphan validation
multi-hop traversal validation

Final validation:

PASS: Day 14 baseline graph validation successful.
### Day 15 — SEC EDGAR Structure Study

**Status: COMPLETE**

The SEC EDGAR data model required by the ingestion pipeline was studied before implementing the crawler.

Topics established:

- SEC CIK identifiers
- 10-K filing metadata
- accession numbers
- primary filing documents
- company submissions JSON
- recent filing collections
- historical submission files
- SEC Archives URL structure
- automated-access requirements
- User-Agent requirements
- request-rate constraints
- raw filing storage strategy

Important architectural decision:

The SEC crawler should retrieve and preserve raw filings plus provenance metadata before downstream parsing or NLP processing.

Parsing, text cleaning, NER, and triplet extraction remain separate pipeline stages.

### Day 16 — Async SEC EDGAR 10-K Crawler

**Status: COMPLETE**

Implemented the production-oriented asynchronous SEC EDGAR ingestion foundation.

Implemented:

- async SEC HTTP client
- SEC-compliant configurable User-Agent
- configurable request rate
- configurable request timeout
- bounded retry policy
- exponential backoff
- jitter
- Retry-After handling
- HTTP 429 handling
- retryable 5xx handling
- network failure retry
- explicit 404 handling
- non-retryable HTTP error handling
- CIK normalization
- recent 10-K discovery
- historical filing fallback
- SEC Archives URL construction
- raw filing downloading
- metadata generation
- atomic document writes
- atomic metadata writes
- bounded concurrent company crawling
- per-company failure isolation
- persistent crawler logging
- executable crawler script
- automated SEC client tests
- automated crawler tests

Live SEC validation succeeded for:

- Apple
- NVIDIA
- AMD

Final project test result:

15 passed

Day 16 completion criteria are satisfied.
23. Completed Roadmap
PHASE 1 — FOUNDATION
─────────────────────────────────────
Day 1  Architecture                  ✅
Day 2  Python/Git/Environment        ✅
Day 3  Python Data Foundation        ✅
Day 4  Async Python Foundation       ✅
Day 5  Docker + Neo4j                ✅


PHASE 2 — GRAPH FOUNDATION
─────────────────────────────────────
Day 6  Graph Theory                  ✅
Day 7  Cypher CRUD                   ✅
Day 8  Graph Relationships           ✅
Day 9  Multi-Hop Traversal           ✅
Day 10 Constraints / IDs / Indexes   ✅


PHASE 3 — FINAL GRAPH SCHEMA
─────────────────────────────────────
Day 11 Final Ontology                ✅
Day 12 Relationship Dictionary       ✅
Day 13 Temporal Event Schema         ✅
Day 14 Baseline Topology             ✅

Phase 3 is complete.

PHASE 4 — SEC EDGAR INGESTION
─────────────────────────────────────

Day 15 SEC EDGAR Structure Study      ✅
Day 16 Async SEC 10-K Crawler         ✅
Day 17 Filing Parser                  ⬜
Day 18 Cleaning / Chunking            ⬜
Day 19 spaCy NER                      ⬜
Day 20 Triplet Extraction             ⬜

Phase 4 is IN PROGRESS.

24. Current Repository Structure

Relevant current structure:

event-driven-supply-chain-risk/
│
├── data/
│   ├── raw/
│   │   └── sec/
│   ├── logs/
│   │   └── sec_crawler.log
│   └── seed/
│
├── scripts/
│   └── crawl_sec.py
│
├── src/
│   ├── graph/
│   └── ingestion/
│       └── sec/
│           ├── __init__.py
│           ├── client.py
│           ├── crawler.py
│           ├── models.py
│           └── rate_limiter.py
│
├── tests/
│   ├── test_neo4j.py
│   ├── test_sec_client.py
│   └── test_sec_crawler.py
│
├── docker-compose.yml
├── PROJECT_STATE.md
└── requirements.txt

Some directories remain intentionally unimplemented because their corresponding roadmap phases have not yet been reached.

25. Recorded Git Milestones

Known Git history includes:

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
cdbf92c  docs: update project state after graph repository
8747157  feat: build baseline supply chain knowledge graph

The current local and remote main branches point to:

8747157
26. Important Existing Decisions
Python is the primary implementation language.
Neo4j is the knowledge graph database.
Docker Compose provides local Neo4j infrastructure.
The official Neo4j Python driver is used.
SupplyChainEvent remains the normalized application event model.
create_event() remains the event creation mechanism.
Existing event serialization should be reused.
Neo4j connection logic remains separate from domain logic.
Graph persistence belongs in the graph repository layer.
Seed data is externalized into JSON rather than hard-coded into persistence methods.
Tests remain outside src/.
Environment secrets belong in .env and must not be committed.
Supply-chain reasoning is graph-grounded.
Risk propagation is limited to three hops.
Distance decay will attenuate propagated risk.
Entity identity uses stable canonical IDs.
Entity resolution must prevent duplicate real-world entities.
Relationship direction is semantically important.
Events are represented as nodes rather than only mutable properties on companies.
Supplier is a role represented through relationships, not a separate final node label.
The final ontology contains nine node types.
SUPPLIES relationships require evidence/provenance.
DEPENDS_ON may be deterministically derived as the inverse of verified SUPPLIES where appropriate.
LLM-generated relationships must not enter the graph without validation.
Provenance must remain available for later explainability.
27. Current Known Issues / Technical Notes

No verified issue blocks completion of Day 14.

Development Machine Memory

The current development system has approximately 8 GB RAM.

Neo4j, Docker Desktop, VS Code, and Python can create memory pressure when running simultaneously.

A Python import of the Neo4j driver previously failed with:

MemoryError

when free physical RAM was approximately 1 GB.

Neo4j Docker memory/CPU limits were therefore introduced.

If this recurs:

Check available RAM.
Stop unnecessary processes.
Temporarily stop Neo4j if only performing Python import/static checks.
Restart Neo4j before database-dependent seed/query operations.

This is a local development-resource constraint, not a graph application logic failure.

28. Rules for Future Development

Before implementing or changing functionality:

Inspect existing source code.
Inspect relevant tests.
Inspect relevant project documentation.
Inspect Git history when previous implementation decisions matter.
Reuse existing components where appropriate.
Do not introduce duplicate implementations of an existing responsibility.
Make changes incrementally.
Run relevant tests after meaningful changes.
Review git diff.
Run git diff --check.
Commit completed milestones with clear conventional commit messages.
Update PROJECT_STATE.md whenever the architectural state materially changes.
Keep graph schema decisions consistent with the frozen ontology.
Keep relationship direction explicit.
Do not create Supplier as a separate final node unless the architecture is intentionally revised.
Do not allow LLM-generated relationships into the graph without validation.
Preserve provenance for automatically extracted knowledge.
Keep risk computation deterministic and graph-grounded.
Do not prematurely implement later roadmap phases.
Prefer canonical IDs over entity names for graph identity.
Use MATCH for relationship endpoints when those entities should already exist.
Do not silently create graph nodes because a relationship seed contains a typo.
Do not label synthetic/manual assumptions as externally verified facts.
Keep derived relationships explicitly marked as derived.
29. Current Milestone State

Three major foundations are now complete.

Phase 1 — Foundation
Python
   +
Git
   +
Configuration
   +
Event Domain
   +
Async Foundation
   +
Docker
   +
Neo4j
Phase 2 — Graph Foundation
Graph Theory
     +
Cypher CRUD
     +
Directed Relationships
     +
Multi-Hop Traversal
     +
Constraints / IDs / Indexing
Phase 3 — Final Graph Schema
Final Ontology
      +
Relationship Dictionary
      +
Temporal Event Schema
      +
50-Company Baseline Topology
      +
Seed Pipeline
      +
Provenance
      +
Multi-Hop Validation
## 30. Immediate Next Objective
The project remains in:

PHASE 4 — SEC EDGAR INGESTION

Days 15 and 16 are complete.

The next objective is:

### Day 17 — HTML/Text Filing Parser

The raw SEC acquisition layer is now established.

The next stage must transform downloaded 10-K documents into parser-ready filing text while preserving document provenance.

Day 17 objectives:

- inspect downloaded SEC 10-K HTML structure
- build reusable filing parser module
- parse HTML safely
- remove non-content markup
- preserve meaningful textual structure
- identify SEC filing sections
- support Item-based extraction
- isolate supply-chain-relevant/risk sections where appropriate
- preserve filing metadata linkage
- add parser-specific tests

The parser must consume the raw filing artifacts produced by Day 16 rather than downloading filings independently.

Day 18 will subsequently handle:

- text cleaning
- normalization
- chunking
- chunk metadata

Day 19 will apply spaCy NER.

Day 20 will implement supply-chain relationship/triplet extraction.

### Current Project Position

Days 1–5
Foundation
    │
    ▼
Days 6–10
Graph Foundation
    │
    ▼
Days 11–14
Final Graph Schema
    │
    ▼
Day 15
SEC EDGAR Structure Study
    │
    ▼
Day 16
Async SEC 10-K Crawler
    │
    ▼
[ CURRENT STATE ]
Day 16 COMPLETE
Phase 4 IN PROGRESS
    │
    ▼
Day 17
10-K Filing Parser
    │
    ▼
Day 18
Cleaning / Chunking
    │
    ▼
Day 19
spaCy NER
    │
    ▼
Day 20
Triplet Extraction

Current status: **Day 16 COMPLETE.**

Next objective: **Day 17 — Build HTML/text filing parser.**