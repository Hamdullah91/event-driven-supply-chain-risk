# Phase 2 — Interaction Audit & Implementation Record

**Project:** Event-Driven Supply Chain Risk Intelligence Using Dynamic Knowledge Graphs  
**Branch:** `feat/frontend-phase2`  
**Phase:** Phase 2 — Component & Interaction Specification  
**Status:** Interaction implementation complete; final browser-level manual verification pending.

## 1. Source of Truth Used

Work was performed in this order:

1. Current executable repository code
2. Current backend/frontend contracts and Phase 1 handoff
3. Frozen Phase 0 backend audit
4. Frozen Phase 1 UX / visual blueprint
5. Phase 2 Component & Interaction Specification
6. Existing tests / build / lint behavior

Current code superseded stale Phase 0 gaps where the repository had since added Events read APIs, event Blast Radius, global search, detailed health, risk history, and the public Agent endpoint.

Phase 1 visual architecture was preserved. No Phase 3 state architecture, final API adapter layer, graph library, chart library, Zustand store, TanStack Query model, or canonical domain model was frozen.

---

## 2. Interaction Audit

| Area | Phase 1 State | Phase 2 Result | Notes |
| --- | --- | --- | --- |
| Global interaction rule | PARTIAL | IMPLEMENTED | Click selects/inspects; explicit actions navigate/expand. |
| Global Search | MISSING | IMPLEMENTED | Development search fixture; entity type visible; result opens Inspector first. |
| Entity Inspector | PARTIAL | IMPLEMENTED | Adaptive sections/actions, close behavior, evidence states, path context. |
| Relationship Inspector | MISSING | IMPLEMENTED | Directed source/target semantics, evidence unavailable state, path action. |
| Overview interactions | PARTIAL | IMPLEMENTED | Event/company selection + explicit deeper actions. |
| Events master-detail | PARTIAL | IMPLEMENTED | Row selection, local fixture filters, evidence, Open Impact, no forced navigation. |
| Companies directory | NEEDS CORRECTION | IMPLEMENTED | Row click now inspects; Open Profile explicit. |
| Company Profile | PARTIAL | IMPLEMENTED | Risk driver selection, related-entity inspection, Network/Impact bridges. |
| Structure Mode | PARTIAL | IMPLEMENTED | Node/edge selection, filters, depth, expansion, reset, focused neighborhood. |
| Impact Mode | PARTIAL | IMPLEMENTED | Context, origin semantics, max hops, single-ring view, visibility filter. |
| Blast Radius | PARTIAL | IMPLEMENTED | Controlled rings, node/path selection, dimming, clear, Replay, strongest-path honesty. |
| Risk trace | PARTIAL | IMPLEMENTED | Backend-shaped factors only; no frontend recalculation. |
| Risk Analysis | PARTIAL | IMPLEMENTED | Ranking, hop filter, event contribution, lens preservation, Impact bridge. |
| Geography | PARTIAL | IMPLEMENTED | Country/Location/Facility selection fixture; no invented coordinates/telemetry. |
| Intelligence | PARTIAL | IMPLEMENTED | Composer, processing state, entity/path selection, Network/Impact/evidence actions. |
| Real-time UX behavior | PARTIAL | IMPLEMENTED | Non-hijacking development update signal and explicit refresh behavior. |
| Browser Back/Forward | MISSING | IMPLEMENTED | Temporary Phase 2 history state restores investigation context. |
| Accessibility interactions | PARTIAL | IMPLEMENTED | Visible actions/focus; graph meaning additionally exposed as lists/text. |
| Production API/state adapters | DEFERRED | DEFERRED | Correctly remains Phase 3/4 work. |

---

## 3. Frozen Global Interaction Model

The implemented Phase 2 interaction rule is:

> **Hover gives lightweight context. Single click selects and inspects. Explicit actions expand or navigate.**

No required workflow depends on double-click, right-click, long-press, or hidden keyboard shortcuts.

Primary selection is singular. Selecting a different analytical object replaces the prior primary selection. Selection does not automatically navigate away.

---

## 4. Global Search

The top-bar search now behaves as an investigation entry point rather than page navigation.

Current Phase 2 development results include multiple entity types and visibly show the entity type. Selecting a result opens the contextual Inspector first.

The fixture remains isolated from production data. Production server-backed discovery remains an adapter concern for Phase 3/4 even though `/api/v1/search` already exists in the backend.

---

## 5. Inspector Behavior

The global right-side Inspector now:

- opens only when an object is selected,
- adapts fields/actions to entity type,
- closes through a visible `X`,
- also permits `Escape` as a convenience,
- frees workspace width when closed,
- does not reset the current page or graph investigation,
- shows risk/exposure only when present,
- shows path context when present,
- shows evidence availability as `AVAILABLE`, `PARTIAL`, or `UNAVAILABLE`,
- never opens an empty evidence panel,
- uses `Not available` where a field is absent.

Contextual actions include:

- Company → `Open Profile`, `Explore Network`, `Open Impact`
- Event → `Open Event`, `Open Impact`
- Facility → `Explore Network`, `Open Company` when a related company is known
- Relationship → `Highlight Path`
- Other graph entities → `Explore Network`

---

## 6. Relationship Interaction

Structure graph relationship labels are selectable controls.

Relationship selection preserves semantic direction and opens a Relationship Inspector with:

- relationship type,
- source,
- target,
- dependency weight when available,
- weight source when available,
- confidence when available,
- evidence availability.

Missing fixture metadata is rendered as `Not available`; it is not invented.

The graph also exposes a textual accessible relationship list so core meaning is not trapped in the visual renderer.

---

## 7. Structure Mode

Implemented Structure interactions:

- focus entity retained,
- bounded depth `1 / 2 / 3`,
- focused neighborhood rather than whole-graph rendering,
- node single-click selection,
- direct relationships emphasized,
- unrelated visible nodes/edges dimmed,
- edge selection and Relationship Inspector,
- explicit `Expand 1 Hop`,
- node-type visibility filters,
- relationship-type visibility filters,
- selected hidden object clears selection/Inspector,
- `Reset` restores depth, filters, focus, layout state, selection, and path highlight without navigating.

Structure depth represents structural distance only. It is not labeled as event-risk propagation hop semantics.

---

## 8. Impact Mode

Impact keeps propagation semantics separate from Structure.

Implemented behavior:

- requires/preserves a valid Event or Company origin context,
- Structure → Impact preserves the relevant focus,
- Impact → Structure removes propagation as the dominant visual language,
- separate `Max Hops` and `Show ring` controls,
- event-origin analysis uses propagated-risk terminology,
- company-origin analysis uses `Transmission Factor`, never `Current Risk`,
- risk/exposure controls only change visibility,
- selecting a target opens the Inspector and highlights its path,
- unrelated content is dimmed rather than removed,
- `Clear Highlight` is visible,
- returned/fixture strongest-path semantics are stated honestly.

The frontend does not recompute risk.

---

## 9. Blast Radius

Blast Radius remains inside `Network → Impact` and uses the frozen concentric/radial hop model.

Implemented:

- origin center,
- Hop 1 ring,
- Hop 2 ring,
- Hop 3 ring,
- max-hop limit,
- single-ring inspection,
- target selection,
- propagation-path highlight,
- unrelated-content dimming,
- clear highlight,
- one-time hop reveal sequence,
- visible `Replay`,
- reduced-motion support,
- no continuous pulsing/animation,
- accessible textual result list.

No unrestricted force layout is used for Blast Radius.

---

## 10. Risk Calculation Inspection

Risk/exposure selection exposes backend-shaped factors such as:

- Initial Risk,
- Combined Path Dependency,
- Distance Decay,
- Propagated Risk,
- Hop Distance,
- Path.

The UI does not reconstruct unavailable per-edge dependency multipliers and does not implement a second authoritative risk engine.

---

## 11. Overview

Overview remains an entry/monitoring surface rather than a duplicate deep workspace.

Implemented:

- event click → inspect,
- explicit `Open Event`,
- explicit `Open Impact`,
- company click → inspect,
- explicit `Open Profile`,
- explicit company `Open Impact`,
- Propagation Spotlight entity inspection,
- explicit Spotlight `Open Impact`.

---

## 12. Events

Implemented master-detail behavior:

- selecting an event keeps the analyst on Events,
- selected state is visually explicit,
- local search/severity filtering is allowed only because the current dataset is a finite development fixture,
- empty filtered result provides `Clear Filters`,
- severity and classifier confidence are explicitly separated,
- affected entities can be inspected,
- `Open Company` is explicit when a matching fixture company exists,
- `Open Impact` preserves Event origin,
- `View Evidence` expands only fields that exist,
- `Open Source` remains disabled when no valid URL exists.

No source URL is fabricated.

---

## 13. Companies / Company Profile

Directory behavior:

- row click → Company Inspector,
- `Open Profile` → explicit navigation,
- safe local fixture search/industry filtering.

Profile behavior:

- `Explore Network`,
- `Open Impact`,
- contributing-event selection,
- returned risk-path inspection,
- risk calculation trace,
- related Facility/Product/Material/Technology selection → Inspector,
- contextual embedded graph remains secondary,
- `Explore Full Network` moves to Network.

Aggregate company risk and individual contributing-event risk remain conceptually separate.

---

## 14. Risk Analysis

Risk Analysis remains system-wide concentration/comparison rather than origin-specific propagation.

Implemented:

- ranking company click → Inspector,
- explicit `Open Profile`,
- explicit `Open Impact`,
- Hop 1/2/3 selection filters analytical presentation only,
- event contribution selection → Inspector/risk context,
- explicit contribution `Open Impact`,
- Network / Geography / Heatmap switching preserves the current fixture scope/hop state,
- history text does not claim persisted market-grade snapshots.

---

## 15. Geography

Geography remains a secondary analytical lens.

The Phase 2 fixture defines selection behavior for:

- Country,
- Location,
- Facility.

Selection opens the contextual Inspector and displays only known fixture context. Coordinate is explicitly shown as unavailable in the interaction fixture.

No ships, vessels, shipment routes, ETA, AIS, port telemetry, truck tracking, or synthetic coordinates were added.

---

## 16. Intelligence

Intelligence remains graph-grounded rather than a generic chatbot.

Implemented interaction behavior:

- text composer,
- `Send`,
- Enter through form submission,
- blank submission disabled,
- simple `Preparing response...` state,
- no chain-of-thought/reasoning UI,
- clickable entity references → Inspector,
- clickable path → select/highlight,
- explicit `Show Network`,
- explicit `Open Impact`,
- evidence expansion,
- `Technical Details` separated from analyst-facing answer,
- generated Cypher is not invented when absent.

The current Phase 2 response remains a clearly labeled development fixture. Production Agent API execution and provider/runtime handling belong to the later data/integration architecture.

---

## 17. Real-Time UX

The interaction model distinguishes the WebSocket states:

- CONNECTING
- CONNECTED
- RECONNECTING
- DISCONNECTED
- ERROR

The current Phase 2 frontend fixture truthfully displays `DISCONNECTED` because no production WebSocket adapter is wired into this interaction-only phase.

A development update signal demonstrates the required non-hijacking behavior:

- active graph remains visible,
- nodes are not moved,
- selection remains intact,
- Inspector remains intact,
- focus remains intact,
- analyst receives `New development risk signal available`,
- analyst explicitly chooses `Refresh Impact`.

A WebSocket connection is never presented as proof that news/classifier/risk publishing subsystems are healthy.

---

## 18. Loading / Refresh / Error / Stale / Empty Behavior

The Phase 2 behavior is frozen as follows:

- Initial load with no usable data → loading/skeleton state.
- Refresh with existing valid data → keep old data visible and show refresh progress.
- Domain error → preserve unrelated valid domains.
- Refresh failure with prior data → preserve prior result and mark stale/error locally.
- Disconnection → preserve current information and show connection state.
- Empty results → meaningful non-error state plus corrective action where useful.
- Stale data → remain visible with a stale/last-updated indication when available.

Phase 1 reusable visual state primitives remain available; production server-state wiring is explicitly deferred rather than being prematurely implemented in Phase 2.

---

## 19. Browser Back / Investigation Context

A temporary Phase 2 history layer uses browser history entries to preserve:

- active top-level section,
- selected Event,
- current Company Profile,
- Network mode,
- Network focus,
- max hop/depth,
- selected graph object/path,
- Inspector context.

This is intentionally a behavior prototype rather than the final URL/state architecture.

The required flow is therefore modeled as:

`Event → Open Impact → select affected company → Open Profile → Browser Back → prior Impact context`

The canonical URL/shareable state model remains Phase 3 work.

---

## 20. Accessibility

Implemented/retained interaction accessibility includes:

- visible focus states,
- no required double-click/right-click/long-press,
- visible controls for all important actions,
- keyboard-reachable buttons/rows/filters/search,
- Escape only as a convenience,
- graph meaning exposed through Inspector and textual node/path/relationship lists,
- no essential information available only on hover,
- reduced-motion handling for Blast Radius Replay,
- disabled Event source action includes an understandable reason.

---

## 21. Phase 2 Source Deviations / Current-Code Corrections

1. The original Phase 0 document described several APIs as missing. Current executable code and the frozen Phase 1 handoff show they now exist, so Phase 2 does **not** preserve those stale gaps.
2. Phase 2 uses isolated development fixtures for interaction demonstration rather than building production adapters. This preserves the Phase 3/4 boundary.
3. A temporary local browser-history interaction model is used only to prove context-preservation behavior. It is explicitly not the final routing/state architecture.
4. Global Search uses a development fixture even though a backend search endpoint exists; the final adapter is deferred.
5. Intelligence submission uses a development response fixture; it does not claim successful live provider execution.
6. Real-time update behavior is demonstrated through a development signal rather than a production WebSocket store.
7. Geography uses clearly labeled development entities without coordinates. No coordinates are invented.
8. No graph library was selected or frozen.

---

## 22. Backend / Integration Constraints Encountered

- Current backend capabilities are ahead of the old Phase 0 audit; adapters are not part of this phase.
- Production Agent responses can still depend on runtime provider configuration.
- WebSocket publication semantics have deployment/runtime caveats documented by Phase 1; Phase 2 only freezes analyst behavior.
- Some fixture relationship fields do not provide dependency weight, confidence, or evidence, so they display `Not available`.
- Some Event fixture records have no valid external source URL, so `Open Source` is disabled rather than fabricated.

---

## 23. Automated Verification

A branch-scoped GitHub Actions workflow was added for the exact required frontend commands:

```text
npm ci
npm run build
npm run lint
```

At least one full Phase 2 validation run completed successfully after the major interaction implementation, with both Build and Lint passing. The workflow continues to run for subsequent branch updates.

Frontend interaction tests were **not added** because the current frontend package has no test runner or test script. Adding an entire test architecture solely for Phase 2 would prematurely expand implementation scope. This follows the Phase 2 instruction to add focused tests only when tests already exist or can be added without creating a large new test architecture.

---

## 24. Manual Interaction Verification

**Pending in a real browser session.**

This environment can edit the repository and execute branch CI, but it does not provide a live browser session against the branch. Therefore the following required workflows must still be manually exercised before Phase 2 is formally frozen:

1. Overview
2. Events
3. Network Structure
4. Network Impact
5. Blast Radius
6. Companies
7. Company Profile
8. Risk Analysis
9. Intelligence

Required end-to-end flows to verify:

```text
Event
→ Open Impact
→ select affected company
→ highlight propagation path
→ inspect calculation
→ Open Company Profile
→ Browser Back
→ return to same Impact context
```

```text
Company
→ Explore Network
→ select relationship
→ View Evidence / Evidence unavailable state
```

```text
Intelligence result
→ select entity/path
→ Show Network
```

No claim is made that these browser-level workflows have been executed in this tool environment.

---

## 25. Phase 2 Exit Checklist

### Global
- ✅ Hover behavior defined.
- ✅ Single-click behavior defined.
- ✅ Explicit navigation behavior defined.
- ✅ Hidden gestures not required.
- ✅ Selection states visible.
- ✅ Investigation context behavior defined and prototyped.

### Search
- ✅ Search result behavior defined by entity type.
- ✅ Search does not force unnecessary navigation.

### Inspector
- ✅ Adaptive content defined/implemented.
- ✅ Entity actions defined/implemented.
- ✅ Close behavior defined/implemented.
- ✅ Relationship Inspector defined/implemented.

### Structure
- ✅ Node click.
- ✅ Edge click.
- ✅ Expansion.
- ✅ Depth.
- ✅ Node filters.
- ✅ Relationship filters.
- ✅ Reset.
- ✅ Focused graph rather than full-graph hairball.

### Impact
- ✅ Origin/context requirement.
- ✅ Event-origin behavior.
- ✅ Company-origin behavior.
- ✅ Structure ↔ Impact switching.
- ✅ Risk/exposure filtering.
- ✅ `Transmission Factor` terminology preserved.

### Blast Radius
- ✅ Concentric hop model.
- ✅ Max-hop and single-ring controls distinguished.
- ✅ Node selection.
- ✅ Path highlighting.
- ✅ Unrelated content dimming.
- ✅ Clear Highlight.
- ✅ Replay behavior.
- ✅ Multiple/strongest-path semantics truthful.

### Overview
- ✅ Event entry points.
- ✅ Company entry points.
- ✅ Impact entry point.
- ✅ No duplicate full-screen deep workflow.

### Events
- ✅ Master-detail.
- ✅ Row selection.
- ✅ Supported fixture filters.
- ✅ Severity/confidence distinction.
- ✅ Impact action.
- ✅ Evidence/source behavior.

### Companies
- ✅ Row selection.
- ✅ Inspector.
- ✅ Explicit Profile navigation.
- ✅ Explore Network.
- ✅ Open Impact.
- ✅ Related-entity interaction.

### Risk Analysis
- ✅ Ranking selection.
- ✅ Hop selection.
- ✅ Event contribution.
- ✅ Lens switching.
- ✅ History semantics truthful.
- ✅ Geography entity selection behavior.

### Intelligence
- ✅ Submission.
- ✅ Loading state.
- ✅ No chain-of-thought.
- ✅ Clickable entities.
- ✅ Clickable paths.
- ✅ Evidence actions.
- ✅ Network/Impact actions.

### Real-Time
- ✅ Connection-state model defined.
- ✅ Update notification behavior demonstrated.
- ✅ Active investigation preserved by update signal.
- ✅ Analyst-controlled refresh behavior.
- ✅ Stale/disconnect preservation rule defined.
- ✅ Connection state not confused with full system health.

### Accessibility
- ✅ No required double-click.
- ✅ No required right-click.
- ✅ No essential hover-only information.
- ✅ Focus visible.
- ✅ Keyboard access for major controls.
- ✅ Graph meaning available outside renderer.

### Verification
- ✅ `npm run build` has passed in branch CI after the major implementation.
- ✅ `npm run lint` has passed in branch CI after the major implementation.
- ⚠️ Latest-head CI must be green after any final documentation/style commit.
- ⚠️ Required browser-level manual workflow verification is still pending.

---

## 26. Remaining Deferred Work — Phase 3 / 4 Only

The following are intentionally **not** Phase 2 work:

- canonical TypeScript domain models,
- API response normalization,
- production API client/adapters,
- final routing/query-parameter schema,
- server-state vs UI-state architecture,
- Zustand/TanStack decisions,
- WebSocket store/reconnect implementation,
- canonical URL/shareable investigation state,
- production graph renderer/library selection,
- chart library selection,
- production Geography renderer,
- final mock schema/data boundary,
- full backend/live integration.

These items must implement the behavior frozen here rather than redesign it.

---

## 27. Current Phase Decision

The Phase 2 interaction implementation is complete in code and the required build/lint checks have passed on the implemented branch state. Formal freeze remains blocked only by the required manual browser workflow verification (and a final green CI run at the exact final head after documentation/style-only commits).

**PHASE 2: NOT COMPLETE**
