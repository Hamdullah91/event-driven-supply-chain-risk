# Phase 3 — Executable Backend / Frontend Contract Audit

**Branch:** `feat/frontend-phase3`  
**Starting HEAD:** `cfa6cbdc1f18be84fdfdfdef3e0f799dcbde1d2b`  
**Frozen baseline tag:** `frontend-phase2-freeze` → `cfa6cbdc1f18be84fdfdfdef3e0f799dcbde1d2b`  
**Source-of-truth:** executable FastAPI routers + Pydantic schemas + current services/tests.

## Verified router surface

| Method | Path | Query / Body | Response | IDs / semantics | Frontend notes |
|---|---|---|---|---|---|
| GET | `/health` | — | `{status}` | app-level only | Not a substitute for per-service health. |
| GET | `/api/v1/info` | — | `{app_name, environment}` | — | Metadata only. |
| GET | `/api/v1/health/detailed` | — | `DetailedHealthResponse` | keyed services | Neo4j, agent configuration, WebSocket manager, poller, classifier, news API are separately reported. |
| GET | `/companies` | `limit 1..500`, `offset>=0`, optional `search`, `industry_id`, `entity_type` | `CompanyListResponse` | `company_id` | Offset pagination. No authoritative risk fields in list response. |
| GET | `/companies/{company_id}` | path ID | `CompanyDetail` | `company_id` | `facilities/products/materials/technologies` are names only, not rich canonical entities. |
| GET | `/companies/{company_id}/network` | `depth 1..3` | `CompanyNetwork` | stable node IDs where backend provides them | Relationship `source`/`target` direction must be preserved. |
| GET | `/api/v1/search` | `q`, `limit 1..100` | `EntitySearchResponse` | `entity_id`, `label` | Server-backed cross-entity discovery. `properties` remains unstructured transport metadata. |
| GET | `/api/v1/events` | `limit 1..500`, `offset>=0` | `EventListResponse` | `event_id` | Newest-first read API exists. |
| GET | `/api/v1/events/{event_id}` | path ID | `EventDetail` | `event_id`, optional `entity_id` | Event type aliases must be normalized in frontend adapter. |
| GET | `/api/v1/events/{event_id}/blast-radius` | `max_hops 1..3` | `EventBlastRadiusResponse` | `event_id`, target/origin `company_id` | Metric is propagated event risk; hop 0 is valid for direct impact. |
| POST | `/api/v1/events/validate` | `EventRequest` | `EventRequest` | — | Validation only; no graph mutation. |
| GET | `/risk/{company_id}` | `max_hops 1..3` | `RiskSummary` | `company_id` | Aggregate current company risk. |
| GET | `/risk/{company_id}/history` | `max_hops 1..3`, `limit 1..500` | `RiskHistoryResponse` | `company_id`, `event_id` | Event-derived reconstructed cumulative history; not persisted wall-clock snapshots. |
| GET | `/risk/{company_id}/exposure` | `max_hops 1..3` | `CompanyExposureResponse` | `event_id` retained | Propagated risk factors are backend-authoritative. Exposure record identity must never replace event ID. |
| GET | `/risk/{company_id}/blast-radius` | `max_hops 1..3` | `BlastRadiusResponse` | target `company_id` | `transmission_factor` is structural propagation strength, not current risk. |
| POST | `/api/v1/agent/query` | `{question}` | `AgentQueryResponse` | event refs/path IDs when present | Public API exists. Never expose chain-of-thought. |
| WS | `/risk-stream` | WebSocket | `connection.established`, `risk.updated` | `company_id`, optional `event_id` | Runtime poller is wired to publish company risk after persisted events. |

## Pydantic transport findings

- Event severity is categorical: `unknown | low | medium | high | critical`.
- Canonical classifier-facing event types are six uppercase labels: `SUPPLY_DISRUPTION`, `REGULATION_CHANGE`, `FACILITY_OUTAGE`, `TECHNOLOGY_EMBARGO`, `TRADE_POLICY_CHANGE`, `QUOTA_CHANGE`.
- `EventDetail` includes `source_url` and `evidence_status`, but not a rich evidence collection.
- `CompanyNetwork` returns generic graph nodes and directed relationships with `properties` dictionaries.
- Event-origin Impact exposes `initial_risk`, `path_dependency`, `distance_decay`, and `propagated_risk`.
- Company-origin Blast Radius exposes `transmission_factor`; this must remain a different domain field/type from risk.
- Company exposure returns canonical `event_id` and backend risk factors. There is no separate public exposure-record ID in the current DTO.
- Agent provenance is intentionally partial when the explainer only has event references.

## Verified WebSocket contract

Handshake:

```json
{"type":"connection.established","message":"Connected to supply-chain risk stream."}
```

Risk update:

```json
{
  "type":"risk.updated",
  "event_id":"string|null",
  "company_id":"string",
  "risk_score":0.0,
  "risk_level":"NONE|LOW|MEDIUM|HIGH|CRITICAL",
  "contributing_event_count":0,
  "max_hops":3,
  "trigger_event_type":"string|null",
  "timestamp":"ISO-8601"
}
```

The news poller invokes the risk stream after a dynamic event is persisted and linked to companies. Streaming failure is isolated from event persistence.

## Backend contract gaps that Phase 3 must handle honestly

### GAP-01 — System-wide risk ranking / Overview aggregates
There is no single aggregate endpoint for highest-risk companies, industry risk, or full Overview metrics. Phase 3 must not issue uncontrolled per-company N+1 risk requests merely to populate a dashboard. Unsupported aggregate panels remain explicitly unavailable or use only already-fetched finite data.

### GAP-02 — Rich typed affected-entity collection on Event detail
`EventDetail` exposes optional `entity_id` plus an untyped `payload`, not a strongly typed `affected_entities[]`. The adapter may preserve a typed entity only when the backend payload explicitly supplies type/name/id; it must not reclassify unknown non-company entities as Industry.

### GAP-03 — Rich sub-entity IDs in Company detail
Company facilities/products/materials/technologies are strings. Live Company Profile may display them, but cannot manufacture canonical Facility/Product/Material/Technology IDs or false profile actions.

### GAP-04 — First-class evidence model
Evidence availability exists, and some source/source URL/provenance fields are embedded in endpoints, but there is no standalone strongly typed evidence endpoint. Frontend evidence remains `AVAILABLE | PARTIAL | UNAVAILABLE` and only renders returned fields.

### GAP-05 — Agent entity canonical IDs
`AgentQueryResponse.affected_entities` and `dependency_paths` are string-based. `path_ids` may exist, but the public response does not guarantee a typed `{id,type,name}` for each entity. `Show Network` may only navigate when a canonical focus ID/type can be resolved safely from known cached/search/graph data; otherwise it remains an honest unavailable action.

### GAP-06 — WebSocket event/network change messages
The verified stream publishes `risk.updated` and handshake messages. It does not expose separate `event.created` or `network.updated` contracts. Cache invalidation is therefore targeted to the affected company risk/exposure/blast-radius/history plus event queries when `event_id` is present; no global invalidation.

## Phase 3 frontend contract rules

1. Backend DTOs never flow directly through presentation components.
2. DTO → adapter → canonical domain is mandatory.
3. `StructureGraph` and `ImpactAnalysis` are separate products.
4. `currentRisk`, `propagatedRisk`, `transmissionFactor`, `severity`, and `confidence` use different domain names.
5. Live failure never falls back to demo fixtures.
6. Names are presentation; stable backend IDs are identity.
7. Frontend displays backend risk; it does not implement production risk mathematics.
8. Search and pagination remain server-backed in LIVE mode.
9. History is described as reconstructed event-derived history.
10. Real-time messages signal stale data / targeted refetch; they never hijack active investigation.
