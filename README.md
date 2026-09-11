# Event-Driven Supply Chain Risk Intelligence

**Dynamic Knowledge Graphs · Real-Time Event Detection · Multi-Hop Risk Propagation · Graph RAG**

Final Year Project focused on detecting operational supply-chain disruptions, maintaining a dynamic multi-tier knowledge graph, and propagating risk across indirect supplier dependencies.

## System Architecture

```text
SEC 10-K Filings
    ↓
Async SEC Crawler
    ↓
Parser & Preprocessing
    ↓
spaCy Entity / Relationship Extraction
    ↓
Entity Resolution & Validation
    ↓
Neo4j Baseline Knowledge Graph

Financial News API
    ↓
15-Minute Async Poller
    ↓
Deduplication
    ↓
DistilBERT Event Classification
    ↓
spaCy Entity Extraction
    ↓
Dynamic Neo4j Event Injection
    ↓
3-Hop Distance-Decay Risk Propagation
    ↓
FastAPI REST / WebSockets
    ↓
React Risk Intelligence Dashboard

Natural-Language Query
    ↓
Agentic Graph RAG
    ↓
Validated Cypher
    ↓
Neo4j Traversal
    ↓
Grounded Risk Explanation
```

## Scope

- Semiconductors
- EV & Battery Supply Chains
- Aerospace & Electronics
- ~50 core companies with multi-tier dependency modeling
- SEC filing-derived baseline relationships
- Dynamic operational disruption events
- Up to 3-hop indirect risk propagation

## Knowledge Graph

### Node Types

`Company` · `Facility` · `Supplier` · `Product` · `Material` · `Location` · `Country` · `Event` · `Industry` · `Technology`

### Relationship Types

`SUPPLIES` · `DEPENDS_ON` · `OPERATES` · `OWNS` · `USES` · `PRODUCES` · `LOCATED_IN` · `OPERATES_IN` · `AFFECTS` · `OCCURS_AT`

### Event Schema

```text
event_id
 event_type
 timestamp
 severity
 source
 confidence
 description
```

Relationships derived from external data retain source and provenance metadata.

## Data Pipelines

### SEC Knowledge Graph Pipeline

```text
SEC EDGAR → Async Crawl → Parse → Clean / Chunk → spaCy → Entity Resolution → Validation → Neo4j
```

Production SEC ingestion uses a controlled 10-K target registry, canonical company identifiers, ontology-aware relationship validation, relationship deduplication, and provenance-backed graph ingestion.

### Dynamic Event Pipeline

```text
News API → Polling → Deduplication → DistilBERT → spaCy → Validation → Event Node → Entity Links
```

Detected events are inserted as timestamped Neo4j `Event` nodes and connected to affected companies or facilities through `AFFECTS` and `OCCURS_AT` relationships.

## Event Classification

Fine-tuned **DistilBERT** classifier for supply-chain disruption classification.

```text
News Article
    ↓
Tokenizer
    ↓
DistilBERT
    ↓
Event Classification
    ↓
Confidence Score
```

Evaluation includes accuracy, precision, recall, F1 score, classification reports, predictions, and confusion-matrix analysis.

## Risk Propagation

Risk propagation is modeled across direct and indirect graph dependencies.

```text
Propagated Risk = Initial Risk × Relationship Weight × Distance Decay
```

Traversal scope:

```text
Event → 1-Hop Exposure → 2-Hop Exposure → 3-Hop Exposure
```

The propagation engine is designed for cumulative multi-event exposure and attenuated indirect risk.

## Technology Stack

### Backend & Data

- Python
- asyncio
- httpx
- Pydantic
- JSON / JSONL / CSV
- SQLite
- Logging

### NLP & Machine Learning

- spaCy
- Transformers
- DistilBERT
- PyTorch
- scikit-learn

### Graph

- Neo4j
- Cypher
- APOC
- Neo4j Graph Data Science
- BFS / multi-hop traversal
- Knowledge Graphs

### API & Real-Time Layer

- FastAPI
- REST
- WebSockets

### Frontend

- React
- vis.js / D3.js

### Infrastructure & Development

- Git
- GitHub
- Docker
- Docker Compose
- pytest
- Python virtual environments

## Repository Structure

```text
.
├── data/
│   ├── raw/
│   ├── processed/
│   ├── seed/
│   └── event_classifier/
├── models/
├── scripts/
├── src/
│   ├── events/
│   ├── graph/
│   ├── ingestion/
│   ├── ml/
│   └── nlp/
├── tests/
├── logs/
├── requirements.txt
└── README.md
```

## Current Implementation Status

### Completed

- System architecture and project structure
- Python environment and development tooling
- Docker / Neo4j environment
- Knowledge graph ontology and schema
- Neo4j constraints and canonical identifiers
- Multi-hop Cypher traversal foundation
- ~50-company baseline graph
- Async SEC EDGAR 10-K crawler
- SEC parsing, preprocessing and chunking
- spaCy entity and relationship extraction
- Entity resolution and relationship validation
- Relationship provenance
- Batch SEC-to-Neo4j ingestion pipeline
- DistilBERT dataset preparation and tokenization
- DistilBERT fine-tuning and evaluation
- Modular event-classification inference
- 15-minute financial-news polling pipeline
- News NLP processing
- Dynamic Neo4j event injection
- Event-to-company / facility linking
- End-to-end dynamic event pipeline

### In Progress

- SEC relationship extraction coverage improvements
- Multi-hop distance-decay risk propagation engine

### Remaining

- Risk aggregation and scenario evaluation
- FastAPI graph and risk endpoints
- WebSocket risk stream
- Agentic Graph RAG and Cypher guardrails
- React risk dashboard
- Graph and blast-radius visualization
- Real-time risk heatmap
- End-to-end integration and final evaluation

## Data Quality Principles

- Canonical entity identifiers
- Evidence-backed graph relationships
- Source provenance
- Conservative entity resolution
- Ontology-aware validation
- Duplicate prevention
- No fabricated relationships for coverage
- Precision-first extraction for downstream risk propagation

## Testing

```powershell
$env:PYTHONPATH = "."
python -m pytest -q
```

## Project Objective

Build an explainable event-driven supply-chain intelligence system capable of identifying disruptions, connecting them to a dynamic knowledge graph, measuring direct and indirect exposure, and producing graph-grounded risk intelligence across multi-tier supplier networks.
