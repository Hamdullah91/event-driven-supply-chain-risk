# Phase 3 Browser Audit Remediation

## Status

The first human-browser audit found six code defects and two environment/testability blocks. This document records the code remediation performed on `feat/frontend-phase3` after that audit.

Phase 4 has not been started.

Current code verdict after remediation:

`PHASE 3: COMPLETE IN CODE — HUMAN BROWSER VERIFICATION REMAINS`

A clean rerun of the browser acceptance audit is still required before Phase 3 can be frozen.

## Audit Findings Addressed

### DEF-01 — reciprocal Structure relationship controls overlap — FIXED IN CODE

- Added deterministic reciprocal/multi-edge label separation.
- Relationship labels sharing the same unordered endpoint pair are offset on opposite sides of the edge midpoint.
- Added an explicit accessible relationship label containing type, source, and target.
- Added unit coverage proving reciprocal label positions do not collide.

Relevant implementation:

- `frontend/src/pages/live/networkLayout.ts`
- `frontend/src/pages/live/networkLayout.test.ts`
- `frontend/src/pages/live/LiveNetworkPage.tsx`

### DEF-03 — Company directory backend search returns unrelated companies — FIXED IN CODE

- Moved Company search and entity-type filtering before the optional Industry match.
- Industry filtering now occurs after the optional Industry projection.
- The same filter ordering is used by the list and count queries.
- Added repository regression coverage for the Cypher query boundary and trimmed parameters.

Relevant implementation:

- `src/graph/company_repository.py`
- `tests/test_company_repository_filters.py`

### DEF-02 — Exposure inspection becomes Event inspection — FIXED IN CODE

- Added first-class `exposure` Inspector references.
- Exposure ID remains the primary Inspector identity.
- Canonical Event ID is retained separately as linked context.
- Exposure details are re-resolved from the live Company exposure query instead of copying a stale domain object into UI state.
- Exposure Inspector displays source/target, hop, severity, confidence, risk trace, and evidence.
- Open Event / Open Impact actions use the separately stored canonical Event ID.
- Added component regression coverage for Exposure/Event identity separation.

Relevant implementation:

- `frontend/src/state/uiStore.ts`
- `frontend/src/pages/live/LiveCompaniesPage.tsx`
- `frontend/src/components/live/LiveEntityInspector.tsx`
- `frontend/src/components/live/LiveEntityInspector.test.tsx`
- `frontend/src/app/LiveApp.tsx`

### DEF-06 — stale cross-section Inspector remains visible — FIXED IN CODE

- Top-level section changes now clear incompatible Inspector, graph selection, and highlighted path state before navigation.
- Real-time risk notification state is not discarded by this cleanup.

Relevant implementation:

- `frontend/src/app/LiveApp.tsx`
- `frontend/src/state/uiStore.ts`

### DEF-05 — hard reload loses selected Impact target/path/Inspector — FIXED IN CODE

- Added optional `targetId` and `pathId` to Impact URL state.
- Target selection writes canonical target/path identity into the URL.
- Hard-load/reload reconstructs graph selection, highlighted path, and Company Inspector from backend-returned Impact data.
- Structure URLs explicitly discard Impact-only target/path state.
- Changing Impact hop depth clears an invalidated target/path selection.
- Added router and React integration coverage for URL round-trip and hard-load restoration.

Relevant implementation:

- `frontend/src/router/networkState.ts`
- `frontend/src/router/networkState.test.ts`
- `frontend/src/pages/live/LiveNetworkPage.tsx`
- `frontend/src/pages/live/liveNetworkSelection.integration.test.tsx`

### DEF-04 — returned relationship types missing from Structure filter — FIXED IN CODE

The Structure filter vocabulary now matches the backend bounded-network relationship vocabulary:

- `SUPPLIES`
- `DEPENDS_ON`
- `OPERATES`
- `OWNS`
- `USES`
- `PRODUCES`
- `LOCATED_IN`
- `OPERATES_IN`
- `AFFECTS`
- `OCCURS_AT`

The vocabulary is centralized and unit tested.

## Automated Verification

GitHub Actions workflow:

`Frontend Phase 3 Verification`

Repair verification run:

- Run ID: `36481224004`
- HEAD: `8ba6a948846aff02dd44f1625407b209feed667b`
- Dependency lock: PASS
- Focused backend Company-filter contract: PASS
- Production build: PASS
- ESLint: PASS
- Phase 2 integrity checks: 33 PASS
- Vitest test files: 12 PASS
- Vitest tests: 33 PASS

New regression coverage includes:

- reciprocal relationship label separation,
- complete Structure relationship vocabulary,
- Impact URL selection serialization/restoration,
- hard-load restoration of target/path/Inspector,
- first-class Exposure Inspector semantics,
- Company repository filter placement.

The Phase 3 workflow now includes a focused Python backend-contract job that runs `tests/test_company_repository_filters.py`, so the corrected Cypher filter boundary is CI-enforced in addition to frontend verification.

The repaired Company search must still be verified against the live Neo4j-backed application during the browser rerun by searching for a guaranteed nonexistent Company and confirming zero results with no Industry corruption.

## Still Blocked by Environment / Testability

### Intelligence acceptance

The original browser audit could not execute the grounded Agent flow because the backend LLM provider was unconfigured. No frontend fallback or fabricated Agent answer has been added. A configured supported LLM provider is required to rerun this acceptance test.

### Real `risk.updated` browser acceptance

WebSocket connect/reconnect behavior is already implemented and tested. The original audit could not produce a genuine `risk.updated` message because the same-process event poller was disabled and no production-safe real update occurred during the audit.

No artificial production WebSocket injection endpoint was added as a workaround. The browser acceptance should be rerun when a legitimate event-processing path can emit a real update.

## Required Browser Rerun

Before freeze, rerun at minimum:

1. Test B — click both reciprocal `SUPPLIES` and `DEPENDS_ON` controls and verify type and direction independently.
2. Test D — inspect an Exposure, verify primary Exposure ID, then Open Event and verify canonical Event ID.
3. Companies exploratory search — query `no-such-company-xyz`; expect zero results and no Industry projection corruption.
4. Network filter — verify `AFFECTS` and `OCCURS_AT` are available when applicable.
5. Event Impact reload — select NVIDIA/path, reload the page, and verify target/path/Inspector restoration.
6. Cross-section Inspector — select a Network relationship, navigate to Events, and verify stale Network Inspector state is cleared.
7. Test F — rerun after Agent provider configuration.
8. Test G — rerun when a legitimate real `risk.updated` can be produced.

Only after the required browser acceptance succeeds should the verdict change to:

`PHASE 3: COMPLETE — READY TO FREEZE AND BEGIN PHASE 4`
