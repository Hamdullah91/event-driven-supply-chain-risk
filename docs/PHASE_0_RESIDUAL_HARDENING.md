# Phase 0 Residual Runtime Hardening — Final Resolution

**Branch:** `fix/phase0-residual-runtime-hardening`

**Baseline:** Phase 0 exit commit `6ec3187`

**Purpose:** Reopen Phase 0 only for the residual runtime/backend issues identified by the independent-review record. No React/frontend implementation is part of this work.

## A. Executive Summary

The residual-hardening pass is complete and verified on the feature branch.

Final gates:

```text
pytest -q
390 passed, 2 warnings in 68.42s

python scripts/audit_graph_contracts.py
PASS: canonical IDs complete; 11/11 locations geocoded; Event core evidence complete

python scripts/verify_live_integration.py
PHASE 0 LIVE INTEGRATION VERIFICATION PASSED
```

The pass intentionally kept the FYP architecture small: no Redis/message broker and no standalone evidence microservice were introduced because the required behavior can be provided by a same-process live poller and the existing frontend-facing evidence surfaces.

## B. Issue 1 — Dynamic Event Severity

### Previous problem

News Events could reach `EventPipeline` without an explicit severity and therefore default to `UNKNOWN`, which maps to `initial_risk=0.0`.

### Resolution

Added deterministic rule-based severity assessment for new news events. The assessor uses event type and disruption-language/context cues. It does not derive severity from DistilBERT classifier confidence.

Classifier confidence and severity remain separate concepts:

```text
confidence → how confident the classifier is in the event category
severity   → estimated operational disruption magnitude
```

Severity rationale is retained with Event context/payload.

### Historical-data policy

Existing Neo4j Events are not rewritten automatically. The final live database still contains older integration events with legacy `facility_shutdown` labels and one `unknown` severity. Their current risk output correctly reflects persisted historical data.

## C. Issue 2 — WebSocket Runtime Architecture

### Previous problem

The WebSocket manager is in-memory. A standalone news poller process and a separately running FastAPI process cannot share the same active connection list.

### Resolution

The live FYP architecture now supports running the news poller as an optional FastAPI lifespan background task:

```text
NEWS_POLLER_ENABLED=true
```

This creates the intended live path in one process:

```text
News poller
→ EventPipeline
→ linked companies
→ RiskAnalyticsService
→ RiskStreamService
→ ConnectionManager.broadcast
→ /risk-stream client
```

A same-process integration test connects through the actual WebSocket route and drives the EventPipeline/risk-publisher path to verify receipt of `risk.updated`.

The standalone poller script remains available for non-live/worker usage, but cross-process WebSocket delivery is not claimed.

## D. Issue 3 — Taxonomy Cleanup

Canonical Event taxonomy remains:

```text
SUPPLY_DISRUPTION
REGULATION_CHANGE
FACILITY_OUTAGE
TECHNOLOGY_EMBARGO
TRADE_POLICY_CHANGE
QUOTA_CHANGE
```

The stale Agent display mapping for `RAW_MATERIAL_SHORTAGE` was removed from the active presentation path.

`FACILITY_SHUTDOWN` and `REGULATORY_CHANGE` remain intentionally as ingestion-boundary compatibility aliases for older inputs and are normalized to canonical values for new Events.

Historical persisted Event nodes are not silently migrated by this hardening pass.

## E. Issue 4 — Evidence / Provenance Frontend Usability

A new standalone evidence endpoint was evaluated and intentionally not added. The planned frontend can obtain evidence through existing surfaces:

- Event list/detail,
- Network relationships,
- Risk Exposure,
- Agent Intelligence.

Explicit availability states were added:

```text
AVAILABLE
PARTIAL
UNAVAILABLE
```

Missing metadata is never fabricated merely to satisfy the UI.

## F. Issue 5 — Agent External Runtime

The concrete OpenAI StructuredLLM adapter and public Agent API remain implemented.

Final live environment:

```text
agent_llm = unconfigured
real_external_call_tested = false
```

This is not treated as a failed Phase 0 backend test because provider credentials are environment-dependent. The system reports the state truthfully and does not claim an external call succeeded.

## G. Issue 6 — Risk History Semantics

`GET /risk/{company_id}/history` is explicitly defined as:

> an event-derived chronological cumulative reconstruction from graph Event exposures.

It is not a persisted wall-clock risk snapshot ledger.

The service now retains the strongest path per event before emitting a history point, preventing duplicate history points when one event reaches a company over multiple paths.

## H. Issue 7 — Detailed Health

Detailed health now reports:

```text
neo4j
agent_llm
websocket
event_poller
event_classifier
news_api
```

The Neo4j dependency is injectable/testable rather than being hard-wired inside the route.

Final live environment reported:

```text
neo4j            healthy
agent_llm        unconfigured
websocket        available
event_poller     disabled
event_classifier available
news_api         configured
```

Optional disabled/unconfigured services are reported explicitly rather than being falsely called healthy.

## I. Issue 8 — Facility Resolution

Facility resolution remains intentionally conservative.

Verified behavior includes:

- explicit seeded facility-name matching,
- case/hyphen normalization,
- no city-only guessing,
- no ambiguous fuzzy partial-name matching.

This prioritizes precision and explainability over recall for the FYP.

## J. Issue 9 — C4 Provenance Audit Semantics

The graph audit now names the Event completeness predicate `core_evidence_complete` and explicitly publishes its fields:

```text
source
timestamp
confidence
```

Description completeness is reported separately.

Final live Event result:

```text
total             2
with_source       2
with_timestamp    2
with_confidence   2
with_description  2
core_evidence_complete true
```

Relationship evidence is reported by relationship type because seeded, extracted, derived and dynamic links intentionally have different evidence contracts.

## K. Issue 10 — Final Verification

### Automated regression

**RUN AND PASSED**

```text
390 passed, 2 warnings in 68.42s
```

### Live graph-contract audit

**RUN AND PASSED**

Canonical IDs:

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

Geography:

```text
11/11 geocoded
0 missing
0 partial
contract_valid=true
```

The audit inspected 119 relationships and verified Event core evidence completeness.

### Strengthened live integration

**RUN AND PASSED**

```text
PHASE 0 LIVE INTEGRATION VERIFICATION PASSED
```

Verified live surfaces include:

- basic health,
- application info,
- detailed service health,
- company list/detail/network,
- risk summary/exposure/history/company Blast Radius,
- global search,
- Event list/detail/Event Blast Radius,
- Event validation,
- expected not-found behavior,
- invalid graph depth validation,
- WebSocket connection handshake.

The real external Agent call remained untested because the provider was unconfigured; the verifier records that fact rather than hiding it.

## L. Final Decision

The reopened Phase 0 residual-runtime work is **complete and verified on the feature branch**.

No React/frontend work was started.

The branch is ready to merge to `main` after the user performs the normal Git merge workflow.

### Remaining intentional/environment-dependent limitations

These are not hidden:

1. Existing historical Neo4j Event nodes retain their original legacy taxonomy/severity values.
2. A separately running standalone poller cannot broadcast to API-process WebSocket clients without a shared broker; the FYP live mode uses the same-process lifespan poller instead.
3. A real external Agent LLM call depends on runtime provider credentials and was not performed in the final environment.
4. Facility resolution intentionally favors exact/conservative matching over fuzzy recall.
5. Risk history is reconstructed from Events rather than persisted as periodic snapshots.

These limitations do not require reopening the frontend architecture. They are explicit system-contract boundaries for future work.
