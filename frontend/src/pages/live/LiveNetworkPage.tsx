import { useEffect, useMemo, useState } from "react";
import { GitBranch, RotateCcw, Search, ShieldAlert } from "lucide-react";
import { useSearchParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import type { EntityType, GraphEdge, GraphNode, ImpactAnalysis, ImpactTarget, SearchResult, StructureGraph } from "../../domain/types";
import { useCompany, useCompanyImpact, useCompanyNetwork, useEntitySearch, useEvent, useEventImpact } from "../../query/hooks";
import { parseNetworkUrlState, serializeNetworkUrlState, type NetworkMode, type NetworkUrlState } from "../../router/networkState";
import { useUiStore } from "../../state/uiStore";

import "../NetworkPage.css";
import "../NetworkPhase2.css";
import "./LiveNetworkPage.css";

type Position = { x: number; y: number };

type FocusFilter = "ALL" | EntityType;

export function LiveNetworkPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const state = parseNetworkUrlState(searchParams);
  const setInspectorRef = useUiStore((store) => store.setInspectorRef);
  const inspectorRef = useUiStore((store) => store.inspectorRef);
  const selectedId = useUiStore((store) => store.selectedGraphObjectId);
  const highlightedPathId = useUiStore((store) => store.highlightedPathId);
  const setSelectedId = useUiStore((store) => store.setSelectedGraphObjectId);
  const setHighlightedPathId = useUiStore((store) => store.setHighlightedPathId);
  const clearSelection = useUiStore((store) => store.clearSelection);
  const [focusQuery, setFocusQuery] = useState("");
  const [debouncedFocusQuery, setDebouncedFocusQuery] = useState("");
  const [nodeTypeFilter, setNodeTypeFilter] = useState<FocusFilter>("ALL");
  const [relationshipFilter, setRelationshipFilter] = useState("ALL");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedFocusQuery(focusQuery.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [focusQuery]);

  const search = useEntitySearch(debouncedFocusQuery, 20);

  const updateUrl = (next: NetworkUrlState) => setSearchParams(serializeNetworkUrlState(next));
  const changeMode = (mode: NetworkMode) => {
    updateUrl({ ...state, mode, ...(mode === "impact" && state.focusType === "Event" && state.focusId ? { eventId: state.focusId } : {}) });
    setNodeTypeFilter("ALL");
    setRelationshipFilter("ALL");
    clearSelection();
  };
  const chooseFocus = (result: SearchResult) => {
    const type = result.entity.type;
    updateUrl({
      ...state,
      focusType: type,
      focusId: result.entity.id,
      ...(type === "Event" ? { eventId: result.entity.id } : { eventId: undefined }),
    });
    setFocusQuery("");
    clearSelection();
  };
  const reset = () => {
    updateUrl({ ...state, depth: 1, maxHops: 1 });
    setNodeTypeFilter("ALL");
    setRelationshipFilter("ALL");
    clearSelection();
  };

  return (
    <div className="network-page">
      <header className="network-header">
        <div><div className="network-title-context"><span className="metadata-text">GRAPH INVESTIGATION</span><span className="demo-badge">LIVE DATA</span></div><h1 className="page-title">Network</h1><p className="body-text network-subtitle">Structure answers how entities connect. Impact answers where a disruption propagates. These are separate live data products.</p></div>
        <div className="network-mode-switch" role="group" aria-label="Network mode"><button type="button" className={`network-mode-button${state.mode === "structure" ? " is-active" : ""}`} onClick={() => changeMode("structure")}>STRUCTURE</button><button type="button" className={`network-mode-button${state.mode === "impact" ? " is-active" : ""}`} onClick={() => changeMode("impact")}>IMPACT</button></div>
      </header>

      <section className="network-toolbar" aria-label="Network controls">
        <div className="network-focus-control"><Search size={14} aria-hidden="true" /><input value={focusQuery} onChange={(event) => setFocusQuery(event.target.value)} placeholder={state.focusId ? "Change focus…" : "Choose focus…"} aria-label="Focus Network" /><small>{state.focusType ?? "None"}</small>{focusQuery.trim().length >= 2 && <div className="network-focus-results">{search.isPending ? <div className="network-focus-empty">Searching live graph…</div> : search.isError ? <div className="network-focus-empty">Search unavailable. Current focus is unchanged.</div> : search.data?.length ? search.data.map((result) => <button type="button" key={`${result.entity.type}:${result.entity.id}`} onClick={() => chooseFocus(result)}><strong>{result.entity.name}</strong><span>{result.entity.type} · {result.entity.id}</span></button>) : <div className="network-focus-empty">No matching entity.</div>}</div>}</div>
        <span className="network-toolbar-divider" />
        <div className="network-control-group"><span className="network-control-label">{state.mode === "structure" ? "Depth" : "Max Hops"}</span>{([1, 2, 3] as const).map((value) => <button type="button" className={`depth-button${(state.mode === "structure" ? state.depth : state.maxHops) === value ? " is-active" : ""}`} key={value} onClick={() => updateUrl({ ...state, ...(state.mode === "structure" ? { depth: value } : { maxHops: value }) })}>{value}</button>)}</div>
        {state.mode === "structure" && <><label className="live-network-select">Node type<select value={nodeTypeFilter} onChange={(event) => setNodeTypeFilter(event.target.value as FocusFilter)}><option value="ALL">All</option><option value="Company">Company</option><option value="Facility">Facility</option><option value="Product">Product</option><option value="Material">Material</option><option value="Technology">Technology</option><option value="Industry">Industry</option><option value="Location">Location</option><option value="Country">Country</option></select></label><label className="live-network-select">Relationship<select value={relationshipFilter} onChange={(event) => setRelationshipFilter(event.target.value)}><option value="ALL">All</option><option value="SUPPLIES">SUPPLIES</option><option value="DEPENDS_ON">DEPENDS_ON</option><option value="OPERATES">OPERATES</option><option value="OWNS">OWNS</option><option value="USES">USES</option><option value="PRODUCES">PRODUCES</option><option value="LOCATED_IN">LOCATED_IN</option><option value="OPERATES_IN">OPERATES_IN</option></select></label></>}
        <div className="network-toolbar-spacer" /><Button variant="ghost" icon={<RotateCcw size={14} />} onClick={reset}>Reset</Button>
      </section>

      {!state.focusId || !state.focusType ? <NetworkState title="Choose a focus" detail="Use live graph search to choose an entity. Search typing alone never replaces the current analytical focus." />
        : state.mode === "structure" ? <StructureWorkspace state={state} nodeTypeFilter={nodeTypeFilter} relationshipFilter={relationshipFilter} selectedId={selectedId} inspectorId={inspectorRef?.id} onInspect={(node) => { setSelectedId(node.id); setInspectorRef({ kind: "entity", id: node.entityId, entityType: node.entityType, name: node.label }); }} onInspectEdge={(edge) => { setSelectedId(edge.id); setInspectorRef({ kind: "relationship", id: edge.id, name: edge.type, context: { graphFocusId: state.focusId, graphDepth: state.depth, relationshipId: edge.id } }); }} onFilteredSelection={() => clearSelection()} />
        : <ImpactWorkspace state={state} selectedId={selectedId} highlightedPathId={highlightedPathId} onSelect={(target) => { setSelectedId(target.company.id); setHighlightedPathId(target.pathId); setInspectorRef({ kind: "entity", id: target.company.id, entityType: "Company", name: target.company.name }); }} onClear={() => clearSelection()} />}
    </div>
  );
}

function StructureWorkspace({ state, nodeTypeFilter, relationshipFilter, selectedId, inspectorId, onInspect, onInspectEdge, onFilteredSelection }: { state: NetworkUrlState; nodeTypeFilter: FocusFilter; relationshipFilter: string; selectedId: string | null; inspectorId?: string; onInspect: (node: GraphNode) => void; onInspectEdge: (edge: GraphEdge) => void; onFilteredSelection: () => void }) {
  const graph = useCompanyNetwork(state.focusType === "Company" ? state.focusId : undefined, state.depth);

  const visibleNodes = useMemo(() => (graph.data?.nodes ?? []).filter((node) => nodeTypeFilter === "ALL" || node.entityType === nodeTypeFilter), [graph.data?.nodes, nodeTypeFilter]);
  const visibleIds = useMemo(() => new Set(visibleNodes.map((node) => node.id)), [visibleNodes]);
  const visibleEdges = useMemo(() => (graph.data?.edges ?? []).filter((edge) => visibleIds.has(edge.sourceId) && visibleIds.has(edge.targetId) && (relationshipFilter === "ALL" || edge.type === relationshipFilter)), [graph.data?.edges, relationshipFilter, visibleIds]);
  const positions = useMemo(() => graph.data ? structurePositions(graph.data, visibleNodes) : new Map<string, Position>(), [graph.data, visibleNodes]);

  useEffect(() => {
    if (!selectedId && !inspectorId) return;
    const nodeStillVisible = visibleNodes.some((node) => node.id === selectedId || node.entityId === inspectorId);
    const edgeStillVisible = visibleEdges.some((edge) => edge.id === selectedId || edge.id === inspectorId);
    if (!nodeStillVisible && !edgeStillVisible) onFilteredSelection();
  }, [inspectorId, onFilteredSelection, selectedId, visibleEdges, visibleNodes]);

  if (state.focusType !== "Company") return <NetworkState title="Structure focus not supported by the current endpoint" detail={`The live structural endpoint requires a Company focus. ${state.focusType}:${state.focusId} is preserved in the URL; it is not replaced with another company.`} />;
  if (graph.isPending) return <NetworkState title="Loading Structure graph" detail="Retrieving the bounded live company neighborhood…" />;
  if (graph.isError) return <NetworkState title="Structure graph unavailable" detail={`${errorText(graph.error)} No development topology is substituted.`} error />;
  if (!graph.data) return <NetworkState title="Structure graph unavailable" detail="No graph response was returned." error />;

  return <div className="network-canvas network-canvas--structure"><div className="network-canvas-header"><div><strong>{graph.data.focus.name}</strong><span className="metadata-text">STRUCTURE · DEPTH {graph.data.depth}</span></div><div className="network-canvas-actions"><span>{visibleNodes.length} nodes · {visibleEdges.length} visible relationships</span></div></div><div className="network-graph-surface">
    <svg className="network-edges" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><defs><marker id="live-structure-arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 z" className="network-arrow-head" /></marker></defs>{visibleEdges.map((edge) => { const source = positions.get(edge.sourceId); const target = positions.get(edge.targetId); if (!source || !target) return null; return <line key={edge.id} x1={source.x} y1={source.y} x2={target.x} y2={target.y} className={`network-edge${selectedId === edge.id ? " phase2-structure-edge-highlight" : ""}`} markerEnd="url(#live-structure-arrow)" />; })}</svg>
    {visibleEdges.map((edge) => { const source = positions.get(edge.sourceId); const target = positions.get(edge.targetId); if (!source || !target) return null; return <button type="button" className={`relationship-label live-relationship-label${selectedId === edge.id ? " is-selected" : ""}`} style={{ left: `${(source.x + target.x) / 2}%`, top: `${(source.y + target.y) / 2}%` }} key={`label:${edge.id}`} onClick={() => onInspectEdge(edge)}>{edge.type}</button>; })}
    {visibleNodes.map((node) => { const position = positions.get(node.id) ?? { x: 50, y: 50 }; const cssType = node.entityType.toLowerCase(); const selected = selectedId === node.id || inspectorId === node.entityId; return <div className="graph-node-wrapper" style={{ left: `${position.x}%`, top: `${position.y}%` }} key={node.id}><button type="button" className={`graph-node graph-node--${cssType}${node.entityId === graph.data!.focus.id ? " is-focus" : ""}${selected ? " is-selected" : ""}`} onClick={() => onInspect(node)} aria-label={`Inspect ${node.label}`} /><div className="graph-node-copy"><strong>{node.label}</strong><span>{node.entityType}</span></div></div>; })}
  </div><div className="network-legend"><span className="network-legend-title">Live semantics</span><span className="network-legend-item">Arrow direction = backend relationship direction</span><span className="network-legend-item">Depth = structural distance, not risk hop</span></div></div>;
}

function ImpactWorkspace({ state, selectedId, highlightedPathId, onSelect, onClear }: { state: NetworkUrlState; selectedId: string | null; highlightedPathId: string | null; onSelect: (target: ImpactTarget) => void; onClear: () => void }) {
  const companyImpact = useCompanyImpact(state.focusType === "Company" ? state.focusId : undefined, state.maxHops);
  const eventImpact = useEventImpact(state.focusType === "Event" ? state.eventId ?? state.focusId : undefined, state.maxHops);
  const company = useCompany(state.focusType === "Company" ? state.focusId : undefined);
  const event = useEvent(state.focusType === "Event" ? state.eventId ?? state.focusId : undefined);
  const query = state.focusType === "Company" ? companyImpact : state.focusType === "Event" ? eventImpact : undefined;
  const analysis = query?.data;

  if (state.focusType !== "Company" && state.focusType !== "Event") return <NetworkState title="Impact origin not supported" detail={`Impact requires a Company or Event origin. ${state.focusType ?? "Unknown"}:${state.focusId} remains preserved; no origin is substituted.`} />;
  if (query?.isPending) return <NetworkState title="Loading Impact analysis" detail="Retrieving backend-authoritative propagation results…" />;
  if (query?.isError) return <NetworkState title="Impact data unavailable" detail={`${errorText(query.error)} The requested origin is preserved and no TSMC or other demo path is substituted.`} error />;
  if (!analysis) return <NetworkState title="Impact data unavailable" detail="No propagation response was returned for this origin." />;

  const originName = state.focusType === "Company" ? company.data?.name ?? state.focusId ?? "Company" : String(event.data?.eventType ?? state.focusId ?? "Event");
  return <ImpactCanvas analysis={analysis} originName={originName} selectedId={selectedId} highlightedPathId={highlightedPathId} onSelect={onSelect} onClear={onClear} />;
}

function ImpactCanvas({ analysis, originName, selectedId, highlightedPathId, onSelect, onClear }: { analysis: ImpactAnalysis; originName: string; selectedId: string | null; highlightedPathId: string | null; onSelect: (target: ImpactTarget) => void; onClear: () => void }) {
  const highlightedPath = analysis.paths.find((path) => path.pathId === highlightedPathId);
  return <div className="network-canvas impact-canvas"><div className="network-canvas-header"><div><strong>{originName}</strong><span className="metadata-text">IMPACT · MAX {analysis.maxHops} HOPS</span></div><div className="network-canvas-actions"><span>{analysis.targets.length} returned targets · {analysis.metricType === "TRANSMISSION_FACTOR" ? "Transmission Factor" : "Propagated Risk"}</span>{selectedId && <Button variant="ghost" onClick={onClear}>Clear Highlight</Button>}</div></div><div className="impact-surface"><div className="impact-origin-card"><strong>Origin</strong><span>{originName}</span><span>{analysis.origin.kind}</span></div><div className="blast-radius-stage"><div className="blast-ring blast-ring--one"><span className="blast-ring-label">HOP 1</span></div>{analysis.maxHops >= 2 && <div className="blast-ring blast-ring--two"><span className="blast-ring-label">HOP 2</span></div>}{analysis.maxHops >= 3 && <div className="blast-ring blast-ring--three"><span className="blast-ring-label">HOP 3</span></div>}<div className="blast-origin-node"><strong>{originName}</strong><span>{analysis.origin.kind}</span></div>{analysis.targets.map((target, index) => { const position = impactPosition(target.hop, index, analysis.targets); const metric = analysis.metricType === "TRANSMISSION_FACTOR" ? target.transmissionFactor : target.propagatedRisk; return <button type="button" className={`impact-company live-impact-company${selectedId === target.company.id ? " is-selected" : ""}`} style={{ left: `${position.x}%`, top: `${position.y}%` }} key={`${target.company.id}:${target.pathId}`} onClick={() => onSelect(target)}><span className="impact-company-node" /><span className="impact-company-copy"><strong>{target.company.name}</strong><span>Hop {target.hop}</span><span>{analysis.metricType === "TRANSMISSION_FACTOR" ? "Transmission Factor" : "Propagated Risk"}: {metric === undefined ? "—" : metric.toFixed(3)}</span></span></button>; })}{analysis.targets.length === 0 && <div className="phase2-impact-filter-empty"><strong>No affected targets returned</strong><span>The backend returned an empty impact set for this origin and max-hop depth.</span></div>}</div><aside className="impact-context-panel"><div><span className="metadata-text">SELECTED PATH</span><strong>{highlightedPath ? highlightedPath.nodes.map((node) => node.name).join(" → ") : "Select a target"}</strong></div>{highlightedPath ? <><div className="impact-context-grid"><div><span>Hop</span><strong>{highlightedPath.trace.hop}</strong></div>{highlightedPath.trace.initialRisk !== undefined && <div><span>Initial Risk</span><strong>{highlightedPath.trace.initialRisk.toFixed(3)}</strong></div>}{highlightedPath.trace.combinedPathDependency !== undefined && <div><span>Path Dependency</span><strong>{highlightedPath.trace.combinedPathDependency.toFixed(3)}</strong></div>}{highlightedPath.trace.distanceDecay !== undefined && <div><span>Distance Decay</span><strong>{highlightedPath.trace.distanceDecay.toFixed(3)}</strong></div>}{highlightedPath.trace.propagatedRisk !== undefined && <div><span>Propagated Risk</span><strong>{highlightedPath.trace.propagatedRisk.toFixed(3)}</strong></div>}</div><p>{analysis.metricType === "TRANSMISSION_FACTOR" ? "Company-origin Blast Radius uses Transmission Factor. It is not labeled Current Risk." : "Event-origin Impact displays backend-returned propagated risk factors. Direct Hop 0 exposure is valid."}</p></> : <p>Single click selects a target, highlights its returned path, and opens the Inspector. The frontend does not invent alternative paths.</p>}</aside></div><div className="impact-legend"><span>{analysis.metricType === "TRANSMISSION_FACTOR" ? "Transmission Factor = structural propagation strength under unit starting risk" : "Propagated Risk = backend event-risk result"}</span></div></div>;
}

function structurePositions(graph: StructureGraph, nodes: GraphNode[]): Map<string, Position> {
  const result = new Map<string, Position>();
  const focusNode = nodes.find((node) => node.entityId === graph.focus.id);
  if (focusNode) result.set(focusNode.id, { x: 50, y: 50 });
  const others = nodes.filter((node) => node.id !== focusNode?.id);
  const radius = others.length > 10 ? 38 : 32;
  others.forEach((node, index) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * index) / Math.max(1, others.length);
    result.set(node.id, { x: 50 + Math.cos(angle) * radius, y: 50 + Math.sin(angle) * Math.min(radius, 36) });
  });
  return result;
}

function impactPosition(hop: number, index: number, targets: ImpactTarget[]): Position {
  const sameHop = targets.filter((target) => target.hop === hop);
  const positionInHop = sameHop.findIndex((target) => target === targets[index]);
  const count = Math.max(1, sameHop.length);
  const xByHop: Record<number, number> = { 0: 55, 1: 64, 2: 76, 3: 87 };
  const y = 18 + ((positionInHop + 1) * 64) / (count + 1);
  return { x: xByHop[hop] ?? 88, y };
}

function NetworkState({ title, detail, error = false }: { title: string; detail: string; error?: boolean }) {
  return <div className="network-canvas network-canvas--state"><div className="network-canvas-header"><div><strong>{title}</strong><span className="metadata-text">LIVE NETWORK STATE</span></div></div><div className="phase2-network-state" role={error ? "alert" : "status"}>{error ? <ShieldAlert size={20} aria-hidden="true" /> : <GitBranch size={20} aria-hidden="true" />}<div><strong>{title}</strong><span>{detail}</span></div></div></div>;
}

function errorText(error: unknown): string { return error instanceof Error ? error.message : "Unknown backend error."; }
