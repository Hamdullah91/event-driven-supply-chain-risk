import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  CircleDot,
  Network,
  RotateCcw,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { RiskBadge } from "../components/ui/RiskBadge";
import { hasCompanyProfile } from "../data/companiesDemo";
import type { InspectorContext } from "../data/inspectorDemo";
import { getImpactFixture, type DemoImpactCompany } from "../data/networkImpactDemo";
import {
  getStructureFixture,
  networkFocusEntities,
  networkStructureDemoRelationships,
  type DemoGraphNode,
  type DemoGraphNodeType,
  type DemoGraphRelationship,
  type DemoStructureFixture,
} from "../data/networkStructureDemo";
import type { HopDepth, NetworkInvestigation } from "../phase2";

import "./NetworkPage.css";
import "./NetworkPhase2.css";

type NetworkPageProps = {
  investigation: NetworkInvestigation;
  onInvestigationChange: (next: NetworkInvestigation) => void;
  onInspect: (context: InspectorContext) => void;
  onClearInspector: () => void;
  onOpenCompanyProfile: (companyId: string) => void;
};

const legendItems: Array<{ type: DemoGraphNodeType; label: string }> = [
  { type: "Company", label: "Company" },
  { type: "Facility", label: "Facility" },
  { type: "Material", label: "Material" },
  { type: "Product", label: "Product" },
  { type: "Technology", label: "Technology" },
  { type: "Country", label: "Country" },
];

const companyIdByName: Record<string, string> = {
  TSMC: "demo-tsmc",
  NVIDIA: "demo-nvidia",
  "Samsung Electronics": "demo-samsung",
};

function structuralNeighborhood(
  relationships: DemoGraphRelationship[],
  focusId: string,
  depth: HopDepth,
) {
  const visible = new Set([focusId]);
  let frontier = new Set([focusId]);

  for (let hop = 0; hop < depth; hop += 1) {
    const next = new Set<string>();
    for (const relationship of relationships) {
      if (frontier.has(relationship.source)) next.add(relationship.target);
      if (frontier.has(relationship.target)) next.add(relationship.source);
    }
    next.forEach((id) => visible.add(id));
    frontier = next;
  }

  return visible;
}

function pathIncludesDirectedEdge(path: string[] | undefined, source: string, target: string) {
  if (!path) return false;
  return path.some((label, index) => label === source && path[index + 1] === target);
}

function selectedStructureNodeFromImpact(investigation: NetworkInvestigation): string | undefined {
  if (
    investigation.mode !== "impact" ||
    !investigation.focusId ||
    !investigation.selectedObjectId ||
    (investigation.focusType !== "Company" && investigation.focusType !== "Event")
  ) {
    return undefined;
  }

  const impactFixture = getImpactFixture(investigation.focusType, investigation.focusId);
  const selectedImpactCompany = impactFixture?.companies.find(
    (company) => company.id === investigation.selectedObjectId,
  );
  const structureFixture = getStructureFixture(investigation.focusId);
  if (!selectedImpactCompany || !structureFixture) return undefined;

  const canonicalCompanyId = companyIdByName[selectedImpactCompany.company]
    ?? networkFocusEntities.find((entity) => entity.label === selectedImpactCompany.company)?.id;

  if (!canonicalCompanyId) return undefined;
  return structureFixture.nodes.some((node) => node.id === canonicalCompanyId)
    ? canonicalCompanyId
    : undefined;
}

export function NetworkPage({
  investigation,
  onInvestigationChange,
  onInspect,
  onClearInspector,
  onOpenCompanyProfile,
}: NetworkPageProps) {
  const [nodeTypes, setNodeTypes] = useState<Set<DemoGraphNodeType>>(
    () => new Set(legendItems.map((item) => item.type)),
  );
  const [relationshipTypes, setRelationshipTypes] = useState<Set<DemoGraphRelationship["type"]>>(
    () => new Set(networkStructureDemoRelationships.map((relationship) => relationship.type)),
  );
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [pendingUpdate, setPendingUpdate] = useState(false);
  const [lastRefreshLabel, setLastRefreshLabel] = useState("CURRENT · Fixture baseline");
  const [replayKey, setReplayKey] = useState(0);
  const [focusQuery, setFocusQuery] = useState(investigation.focusName ?? "");
  const [focusOpen, setFocusOpen] = useState(false);

  const allowedFocusEntities = investigation.mode === "impact"
    ? networkFocusEntities.filter((node) => node.type === "Company")
    : networkFocusEntities;
  const normalizedFocusQuery = focusQuery.trim().toLowerCase();
  const focusResults = allowedFocusEntities.filter((node) =>
    !normalizedFocusQuery || `${node.label} ${node.type}`.toLowerCase().includes(normalizedFocusQuery),
  );

  const structureFixture = investigation.focusId
    ? getStructureFixture(investigation.focusId)
    : undefined;

  const setMode = (mode: NetworkInvestigation["mode"]) => {
    if (mode === investigation.mode) return;

    if (investigation.mode === "impact" && mode === "structure") {
      const preservedSelectionId = selectedStructureNodeFromImpact(investigation);
      onInvestigationChange({
        ...investigation,
        mode,
        hopOnly: null,
        selectedObjectId: preservedSelectionId,
        highlightedPath: undefined,
      });
      if (investigation.selectedObjectId && !preservedSelectionId) onClearInspector();
      return;
    }

    onInvestigationChange({
      ...investigation,
      mode,
      hopOnly: null,
      selectedObjectId: undefined,
      highlightedPath: undefined,
    });
    onClearInspector();
  };

  const setMaxHops = (maxHops: HopDepth) => {
    onInvestigationChange({ ...investigation, maxHops });
  };

  const selectFocus = (node: (typeof networkFocusEntities)[number]) => {
    setFocusQuery(node.label);
    setFocusOpen(false);
    onInvestigationChange({
      ...investigation,
      focusId: node.id,
      focusName: node.label,
      focusType: node.type,
      eventId: undefined,
      hopOnly: null,
      selectedObjectId: undefined,
      highlightedPath: undefined,
    });
    onClearInspector();
  };

  const reset = () => {
    setNodeTypes(new Set(legendItems.map((item) => item.type)));
    setRelationshipTypes(new Set(networkStructureDemoRelationships.map((relationship) => relationship.type)));
    setRiskFilter("ALL");
    setFocusQuery(investigation.focusName ?? "");
    onInvestigationChange({
      ...investigation,
      maxHops: 1,
      hopOnly: null,
      selectedObjectId: undefined,
      highlightedPath: undefined,
    });
    onClearInspector();
  };

  const clearHighlight = () => {
    const hadPrimarySelection = Boolean(investigation.selectedObjectId);
    onInvestigationChange({
      ...investigation,
      highlightedPath: undefined,
      selectedObjectId: undefined,
    });
    if (hadPrimarySelection) onClearInspector();
  };

  const chooseAnotherEntity = () => {
    setFocusQuery("");
    setFocusOpen(true);
  };

  return (
    <div className="network-page">
      <header className="network-header">
        <div>
          <div className="network-title-context"><span className="metadata-text">GRAPH EXPLORER</span><span className="demo-badge">DEVELOPMENT DATA</span></div>
          <h1 className="page-title">Network</h1>
          <p className="body-text network-subtitle">
            {investigation.mode === "structure"
              ? "Explore topology. Click selects and inspects; expansion remains explicit."
              : "Analyze one-to-three-hop propagation while preserving origin, hop, and path meaning."}
          </p>
        </div>

        <div className="network-mode-switch" aria-label="Network mode">
          <button type="button" className={`network-mode-button${investigation.mode === "structure" ? " is-active" : ""}`} aria-pressed={investigation.mode === "structure"} onClick={() => setMode("structure")}>STRUCTURE</button>
          <button type="button" className={`network-mode-button${investigation.mode === "impact" ? " is-active" : ""}`} aria-pressed={investigation.mode === "impact"} onClick={() => setMode("impact")}>IMPACT</button>
        </div>
      </header>

      {pendingUpdate && (
        <div className="phase2-update-banner" role="status">
          <div><strong>STALE · New development risk signal available</strong><span>Last updated: fixture baseline. The active graph, selection, and Inspector remain unchanged until refresh.</span></div>
          <Button variant="secondary" onClick={() => { setPendingUpdate(false); setLastRefreshLabel("CURRENT · Refreshed development fixture"); }}>Refresh Impact</Button>
        </div>
      )}

      <section className="network-toolbar" aria-label="Network controls">
        <div className="network-focus-control">
          <Search size={15} aria-hidden="true" />
          <input
            value={focusQuery}
            onChange={(event) => { setFocusQuery(event.target.value); setFocusOpen(true); }}
            onFocus={() => setFocusOpen(true)}
            onKeyDown={(event) => { if (event.key === "Escape") setFocusOpen(false); }}
            aria-label="Focus Network"
            aria-expanded={focusOpen}
            placeholder="Focus Network"
          />
          <small>{investigation.focusType ?? "Focus"}</small>
          {focusOpen && (
            <div className="network-focus-results" aria-label="Network focus results">
              {focusResults.length > 0 ? focusResults.map((node) => (
                <button type="button" key={node.id} onClick={() => selectFocus(node)}>
                  <strong>{node.label}</strong>
                  <span>{node.type}{getStructureFixture(node.id) ? "" : " · Network fixture unavailable"}</span>
                </button>
              )) : <div className="network-focus-empty">No development entities match this search.</div>}
            </div>
          )}
        </div>

        <div className="network-toolbar-divider" />
        <div className="network-control-group">
          <span className="network-control-label">{investigation.mode === "structure" ? "Depth" : "Max Hops"}</span>
          {([1, 2, 3] as HopDepth[]).map((depth) => <button key={depth} type="button" className={`depth-button${investigation.maxHops === depth ? " is-active" : ""}`} aria-pressed={investigation.maxHops === depth} onClick={() => setMaxHops(depth)}>{depth}</button>)}
        </div>
        <div className="network-toolbar-divider" />

        {investigation.mode === "structure" ? (
          <>
            <details className="network-filter-menu">
              <summary className="network-toolbar-button"><CircleDot size={14} aria-hidden="true" /><span>Node Types</span><ChevronDown size={13} aria-hidden="true" /></summary>
              <div className="network-filter-popover">
                {legendItems.map((item) => <label key={item.type}><input type="checkbox" checked={nodeTypes.has(item.type)} onChange={() => {
                  const next = new Set(nodeTypes);
                  if (next.has(item.type)) next.delete(item.type); else next.add(item.type);
                  setNodeTypes(next);
                  const selected = structureFixture?.nodes.find((node) => node.id === investigation.selectedObjectId);
                  if (selected && !next.has(selected.type)) {
                    onInvestigationChange({ ...investigation, selectedObjectId: undefined, highlightedPath: undefined });
                    onClearInspector();
                  }
                }} />{item.label}</label>)}
              </div>
            </details>
            <details className="network-filter-menu">
              <summary className="network-toolbar-button"><SlidersHorizontal size={14} aria-hidden="true" /><span>Relationships</span><ChevronDown size={13} aria-hidden="true" /></summary>
              <div className="network-filter-popover">
                {Array.from(new Set(networkStructureDemoRelationships.map((relationship) => relationship.type))).map((type) => <label key={type}><input type="checkbox" checked={relationshipTypes.has(type)} onChange={() => {
                  const next = new Set(relationshipTypes);
                  if (next.has(type)) next.delete(type); else next.add(type);
                  setRelationshipTypes(next);
                  const selectedRelationship = structureFixture?.relationships.find((relationship) => relationship.id === investigation.selectedObjectId);
                  if (selectedRelationship && !next.has(selectedRelationship.type)) {
                    onInvestigationChange({ ...investigation, selectedObjectId: undefined, highlightedPath: undefined });
                    onClearInspector();
                  }
                }} />{type}</label>)}
              </div>
            </details>
            <Button variant="ghost" onClick={() => setMaxHops(Math.min(3, investigation.maxHops + 1) as HopDepth)} disabled={investigation.maxHops === 3 || !structureFixture}>Expand 1 Hop</Button>
          </>
        ) : (
          <>
            <label className="impact-toolbar-context">Show ring
              <select value={investigation.hopOnly ?? "ALL"} onChange={(event) => onInvestigationChange({ ...investigation, hopOnly: event.target.value === "ALL" ? null : Number(event.target.value) as HopDepth })}>
                <option value="ALL">All visible hops</option><option value="1">Hop 1 only</option><option value="2">Hop 2 only</option><option value="3">Hop 3 only</option>
              </select>
            </label>
            <label className="impact-toolbar-context">Risk / exposure
              <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                <option value="ALL">All</option><option value="CRITICAL">CRITICAL</option><option value="HIGH">HIGH</option><option value="MEDIUM">MEDIUM</option><option value="LOW">LOW</option><option value="NONE">NONE</option>
              </select>
            </label>
          </>
        )}

        <div className="network-toolbar-spacer" />
        {investigation.highlightedPath && <Button variant="ghost" onClick={clearHighlight}>Clear Highlight</Button>}
        <Button variant="ghost" icon={<RotateCcw size={14} />} onClick={reset}>Reset</Button>
      </section>

      {investigation.mode === "structure" ? (
        !investigation.focusId ? (
          <NetworkState
            title="Choose an entity to explore"
            detail="Network has no universal root. Use Focus Network to select a supported development entity."
            actionLabel="Choose Entity"
            onAction={chooseAnotherEntity}
          />
        ) : structureFixture ? (
          <StructureCanvas
            fixture={structureFixture}
            investigation={investigation}
            nodeTypes={nodeTypes}
            relationshipTypes={relationshipTypes}
            onInvestigationChange={onInvestigationChange}
            onInspect={onInspect}
            onClearInspector={onClearInspector}
            onReset={reset}
          />
        ) : (
          <NetworkState
            title={`No development network fixture is available for ${investigation.focusName ?? "this entity"}.`}
            detail="The requested focus is preserved. No TSMC or other topology is substituted."
            actionLabel="Choose Another Entity"
            onAction={chooseAnotherEntity}
          />
        )
      ) : (
        <ImpactCanvas
          key={`impact-${replayKey}`}
          investigation={investigation}
          riskFilter={riskFilter}
          lastRefreshLabel={lastRefreshLabel}
          onInvestigationChange={onInvestigationChange}
          onInspect={onInspect}
          onClearInspector={onClearInspector}
          onOpenCompanyProfile={onOpenCompanyProfile}
          onReplay={() => setReplayKey((value) => value + 1)}
          onSimulateUpdate={() => setPendingUpdate(true)}
          onReturnToStructure={() => setMode("structure")}
        />
      )}
    </div>
  );
}

type StructureCanvasProps = {
  fixture: DemoStructureFixture;
  investigation: NetworkInvestigation;
  nodeTypes: Set<DemoGraphNodeType>;
  relationshipTypes: Set<DemoGraphRelationship["type"]>;
  onInvestigationChange: (next: NetworkInvestigation) => void;
  onInspect: (context: InspectorContext) => void;
  onClearInspector: () => void;
  onReset: () => void;
};

function StructureCanvas({ fixture, investigation, nodeTypes, relationshipTypes, onInvestigationChange, onInspect, onClearInspector, onReset }: StructureCanvasProps) {
  const depthVisible = useMemo(
    () => structuralNeighborhood(fixture.relationships, fixture.focusId, investigation.maxHops),
    [fixture, investigation.maxHops],
  );
  const visibleNodes = fixture.nodes.filter((node) => depthVisible.has(node.id) && nodeTypes.has(node.type));
  const visibleIds = new Set(visibleNodes.map((node) => node.id));
  const visibleRelationships = fixture.relationships.filter((relationship) => visibleIds.has(relationship.source) && visibleIds.has(relationship.target) && relationshipTypes.has(relationship.type));
  const selectedNode = fixture.nodes.find((node) => node.id === investigation.selectedObjectId);
  const selectedRelationship = fixture.relationships.find((relationship) => relationship.id === investigation.selectedObjectId);
  const selectedObjectStillVisible = !investigation.selectedObjectId
    || visibleNodes.some((node) => node.id === investigation.selectedObjectId)
    || visibleRelationships.some((relationship) => relationship.id === investigation.selectedObjectId);
  const connectedIds = new Set<string>();

  useEffect(() => {
    if (selectedObjectStillVisible || !investigation.selectedObjectId) return;
    onInvestigationChange({ ...investigation, selectedObjectId: undefined, highlightedPath: undefined });
    onClearInspector();
  }, [investigation, onClearInspector, onInvestigationChange, selectedObjectStillVisible]);

  if (selectedNode) {
    connectedIds.add(selectedNode.id);
    fixture.relationships.forEach((relationship) => {
      if (relationship.source === selectedNode.id) connectedIds.add(relationship.target);
      if (relationship.target === selectedNode.id) connectedIds.add(relationship.source);
    });
  }

  const selectNode = (node: DemoGraphNode) => {
    onInvestigationChange({ ...investigation, selectedObjectId: node.id, highlightedPath: undefined });
    onInspect({
      id: node.id,
      type: node.type,
      name: node.label,
      subtitle: node.id === fixture.focusId ? "Current Structure focus" : "Selected from Structure Mode",
      relatedCompanyId: node.type === "Facility" ? "demo-tsmc" : undefined,
      fields: [
        { label: "Graph node ID", value: node.id },
        { label: "Entity type", value: node.type },
        { label: "Structural depth", value: String(investigation.maxHops) },
      ],
      evidence: { availability: "UNAVAILABLE" },
    });
  };

  const selectRelationship = (relationship: DemoGraphRelationship) => {
    const source = fixture.nodes.find((node) => node.id === relationship.source)!;
    const target = fixture.nodes.find((node) => node.id === relationship.target)!;
    onInvestigationChange({ ...investigation, selectedObjectId: relationship.id, highlightedPath: [source.label, target.label] });
    onInspect({
      id: relationship.id,
      type: "Relationship",
      name: `${source.label} ${relationship.type} → ${target.label}`,
      subtitle: "Direction preserved from the development graph fixture",
      fields: [
        { label: "Relationship Type", value: relationship.type },
        { label: "Source", value: source.label },
        { label: "Target", value: target.label },
        { label: "Dependency Weight", value: "Not available" },
        { label: "Weight Source", value: "Not available" },
        { label: "Confidence", value: "Not available" },
      ],
      path: [source.label, target.label],
      evidence: { availability: "UNAVAILABLE" },
    });
  };

  return (
    <section className="network-canvas network-canvas--structure" aria-label="Structure graph preview">
      <div className="network-canvas-header">
        <div><span className="metadata-text">STRUCTURE MODE</span><strong>Supply Network Structure</strong></div>
        <CanvasActions label={`Focus ${investigation.focusName ?? "—"} · Depth ${investigation.maxHops} · ${visibleNodes.length} nodes`} />
      </div>

      <div className="network-graph-surface">
        <svg className="network-edges" viewBox="0 0 1000 600" preserveAspectRatio="none" aria-hidden="true">
          <defs><marker id="structure-arrow" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" className="network-arrow-head" /></marker></defs>
          {visibleRelationships.map((relationship) => {
            const source = fixture.nodes.find((node) => node.id === relationship.source)!;
            const target = fixture.nodes.find((node) => node.id === relationship.target)!;
            const dim = selectedNode && !(relationship.source === selectedNode.id || relationship.target === selectedNode.id);
            const highlighted = selectedRelationship?.id === relationship.id || pathIncludesDirectedEdge(investigation.highlightedPath, source.label, target.label);
            return (
              <line
                key={relationship.id}
                x1={source.x * 10}
                y1={source.y * 6}
                x2={target.x * 10}
                y2={target.y * 6}
                className={`network-edge${dim ? " phase2-dimmed" : ""}${highlighted ? " phase2-structure-edge-highlight" : ""}`}
                markerEnd="url(#structure-arrow)"
              />
            );
          })}
        </svg>

        {visibleRelationships.map((relationship) => {
          const source = fixture.nodes.find((node) => node.id === relationship.source)!;
          const target = fixture.nodes.find((node) => node.id === relationship.target)!;
          const dim = selectedNode && !(relationship.source === selectedNode.id || relationship.target === selectedNode.id);
          return (
            <button
              type="button"
              title={`${relationship.type}: ${source.label} → ${target.label}`}
              key={relationship.id}
              style={{ left: `${(source.x + target.x) / 2}%`, top: `${(source.y + target.y) / 2}%` }}
              className={`relationship-label phase2-relationship-button${dim ? " phase2-dimmed" : ""}${selectedRelationship?.id === relationship.id ? " is-selected" : ""}`}
              onClick={() => selectRelationship(relationship)}
            >
              {relationship.type}
            </button>
          );
        })}

        {visibleNodes.map((node) => {
          const selected = selectedNode?.id === node.id;
          const onPath = investigation.highlightedPath?.includes(node.label);
          const dim = selectedNode ? !connectedIds.has(node.id) : investigation.highlightedPath ? !onPath : false;
          return (
            <div key={node.id} className={`graph-node-wrapper${dim ? " phase2-dimmed" : ""}`} style={{ left: `${node.x}%`, top: `${node.y}%` }}>
              <button
                type="button"
                title={`${node.label} · ${node.type}`}
                className={`graph-node graph-node--${node.type.toLowerCase()}${node.id === fixture.focusId ? " is-focus" : ""}${selected ? " is-selected" : ""}`}
                onClick={() => selectNode(node)}
                aria-pressed={selected}
              >
                {node.type === "Company" && <Network size={16} aria-hidden="true" />}
              </button>
              <div className="graph-node-copy"><strong>{node.label}</strong><span>{node.type}</span></div>
            </div>
          );
        })}
      </div>

      {visibleRelationships.length === 0 && (
        <div className="phase2-network-empty" role="status">
          <div><strong>No relationships found at this depth or with the current filters.</strong><span>Increase depth or reset filters; no hidden relationship is invented.</span></div>
          <div className="phase2-inline-actions">
            {investigation.maxHops < 3 && <Button variant="secondary" onClick={() => onInvestigationChange({ ...investigation, maxHops: Math.min(3, investigation.maxHops + 1) as HopDepth })}>Increase Depth</Button>}
            <Button variant="ghost" onClick={onReset}>Reset Filters</Button>
          </div>
        </div>
      )}

      <div>
        <StructureLegend />
        <div className="phase2-accessible-list">
          <h3>Accessible relationship list</h3>
          <ul>{visibleRelationships.map((relationship) => {
            const source = fixture.nodes.find((node) => node.id === relationship.source)!;
            const target = fixture.nodes.find((node) => node.id === relationship.target)!;
            return <li key={`list-${relationship.id}`}><button type="button" onClick={() => selectRelationship(relationship)}>{source.label} {relationship.type} → {target.label}</button></li>;
          })}</ul>
        </div>
      </div>
    </section>
  );
}

type ImpactCanvasProps = {
  investigation: NetworkInvestigation;
  riskFilter: string;
  lastRefreshLabel: string;
  onInvestigationChange: (next: NetworkInvestigation) => void;
  onInspect: (context: InspectorContext) => void;
  onClearInspector: () => void;
  onOpenCompanyProfile: (companyId: string) => void;
  onReplay: () => void;
  onSimulateUpdate: () => void;
  onReturnToStructure: () => void;
};

function ImpactCanvas({ investigation, riskFilter, lastRefreshLabel, onInvestigationChange, onInspect, onClearInspector, onOpenCompanyProfile, onReplay, onSimulateUpdate, onReturnToStructure }: ImpactCanvasProps) {
  const validOriginType = investigation.focusType === "Company" || investigation.focusType === "Event"
    ? investigation.focusType
    : undefined;
  const fixture = validOriginType && investigation.focusId
    ? getImpactFixture(validOriginType, investigation.focusId)
    : undefined;
  const riskOrder = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

  const visibleCompanies = useMemo(() => {
    if (!fixture) return [];
    return fixture.companies.filter((company) => {
      const hop = Number(company.hop.replace("Hop ", ""));
      const hopVisible = hop <= investigation.maxHops && (!investigation.hopOnly || hop === investigation.hopOnly);
      const riskVisible = riskFilter === "ALL"
        ? true
        : riskFilter === "NONE"
          ? false
          : riskOrder.indexOf(company.level) >= riskOrder.indexOf(riskFilter);
      return hopVisible && riskVisible;
    });
  }, [fixture, investigation.hopOnly, investigation.maxHops, riskFilter]);

  const selectedCompany = fixture?.companies.find((company) => company.id === investigation.selectedObjectId);
  const selectedCompanyVisible = selectedCompany
    ? visibleCompanies.some((company) => company.id === selectedCompany.id)
    : true;

  useEffect(() => {
    if (!selectedCompany || selectedCompanyVisible) return;
    onInvestigationChange({ ...investigation, selectedObjectId: undefined, highlightedPath: undefined });
    onClearInspector();
  }, [investigation, onClearInspector, onInvestigationChange, selectedCompany, selectedCompanyVisible]);

  if (!validOriginType || !investigation.focusId) {
    return (
      <ImpactUnavailableState
        title="Select an event or origin company to analyze propagation."
        detail="Impact does not render risk rings or paths without a valid origin context. Use Focus Network to select a Company, or open Impact from an Event."
        onReturnToStructure={onReturnToStructure}
      />
    );
  }

  if (!fixture) {
    return (
      <ImpactUnavailableState
        title={`Impact data is not available for ${investigation.focusName ?? "this development origin"}.`}
        detail="The current origin is preserved. No TSMC path or other origin is substituted."
        onReturnToStructure={onReturnToStructure}
      />
    );
  }

  const isEventOrigin = fixture.origin.type === "Event";
  const originName = fixture.origin.name;

  const selectCompany = (company: DemoImpactCompany) => {
    onInvestigationChange({ ...investigation, selectedObjectId: company.id, highlightedPath: company.path });
    const profileId = companyIdByName[company.company];
    const inspectorId = profileId ?? company.id;
    const traceFields = isEventOrigin ? [
      { label: "Initial Risk", value: fixture.context.initialRisk ?? "Not available" },
      { label: "Path Dependency", value: company.pathDependency ?? "Not available" },
      { label: "Distance Decay", value: company.distanceDecay ?? "Not available" },
    ] : [];

    onInspect({
      id: inspectorId,
      type: "Company",
      name: company.company,
      subtitle: isEventOrigin ? "Event-origin propagated exposure" : "Company-origin transmission result",
      riskLevel: isEventOrigin ? company.level : undefined,
      riskScore: company.score,
      fields: [
        { label: "Hop", value: company.hop.replace("Hop ", "") },
        { label: "Origin", value: originName },
        { label: isEventOrigin ? "Propagated Risk" : "Transmission Factor", value: company.score },
        ...traceFields,
      ],
      path: company.path,
      evidence: { availability: "UNAVAILABLE" },
    });
  };

  const selectedProfileId = selectedCompany ? companyIdByName[selectedCompany.company] : undefined;

  return (
    <section className="network-canvas impact-canvas" aria-label="Impact blast radius">
      <div className="network-canvas-header"><div><span className="metadata-text">IMPACT MODE</span><strong>Blast Radius</strong></div><div className="network-canvas-actions"><span>{lastRefreshLabel}</span><Button variant="ghost" onClick={onReplay}>Replay</Button><Button variant="ghost" onClick={onSimulateUpdate}>DEMO UPDATE</Button></div></div>
      <div className="impact-surface">
        <div className="impact-origin-card"><span className="metadata-text">{isEventOrigin ? "EVENT ORIGIN" : "COMPANY ORIGIN"}</span><strong>{originName}</strong><span>{isEventOrigin ? "Propagated risk semantics" : "Transmission Factor semantics — not Current Risk"}</span></div>
        <div className="blast-radius-stage phase2-propagation-sequence">
          <div className={`blast-ring blast-ring--three${investigation.maxHops < 3 || investigation.hopOnly && investigation.hopOnly !== 3 ? " phase2-dimmed" : ""}`}><span className="blast-ring-label">HOP 3</span></div>
          <div className={`blast-ring blast-ring--two${investigation.maxHops < 2 || investigation.hopOnly && investigation.hopOnly !== 2 ? " phase2-dimmed" : ""}`}><span className="blast-ring-label">HOP 2</span></div>
          <div className={`blast-ring blast-ring--one${investigation.hopOnly && investigation.hopOnly !== 1 ? " phase2-dimmed" : ""}`}><span className="blast-ring-label">HOP 1</span></div>
          <div className="blast-origin-node"><AlertTriangle size={19} aria-hidden="true" /><strong>{isEventOrigin ? "EVENT" : originName}</strong><span>Origin</span></div>

          {visibleCompanies.map((company) => {
            const selected = company.id === investigation.selectedObjectId;
            const dim = investigation.highlightedPath && !investigation.highlightedPath.includes(company.company);
            return <ImpactCompany key={company.id} className={`impact-company--${company.position}${dim ? " phase2-dimmed" : ""}`} company={company.company} hop={company.hop} score={company.score} level={company.level} valueLabel={isEventOrigin ? "Risk" : "Transmission"} selected={selected} onClick={() => selectCompany(company)} />;
          })}

          <svg className="impact-paths" viewBox="0 0 1000 600" preserveAspectRatio="none" aria-hidden="true">
            <defs><marker id="impact-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" className="impact-arrow-head" /></marker></defs>
            {visibleCompanies.length > 0 && fixture.paths.map((path, index) => {
              const hop = index + 1;
              if (hop > investigation.maxHops || investigation.hopOnly && investigation.hopOnly !== hop) return null;
              const dim = investigation.highlightedPath && selectedCompany && hop > Number(selectedCompany.hop.replace("Hop ", ""));
              return <line key={path.id} x1={path.x1} y1={path.y1} x2={path.x2} y2={path.y2} className={`impact-path impact-path--${path.tone}${dim ? " phase2-dimmed" : ""}${investigation.highlightedPath ? " phase2-impact-path-highlight" : ""}`} markerEnd="url(#impact-arrow)" />;
            })}
          </svg>

          {visibleCompanies.length === 0 && (
            <div className="phase2-impact-filter-empty" role="status">
              <strong>No impact results match the current risk / exposure filter.</strong>
              <span>The development fixture contains no {riskFilter} results.</span>
            </div>
          )}
        </div>

        <div className="impact-context-panel">
          <div><span className="metadata-text">PROPAGATION CONTEXT</span><strong>{investigation.maxHops}-hop maximum depth</strong></div>
          <div className="impact-context-grid">
            {isEventOrigin ? <><div><span>Initial Risk</span><strong>{fixture.context.initialRisk ?? "Not available"}</strong></div><div><span>Distance Decay</span><strong>{fixture.context.distanceDecay ?? "Not available"}</strong></div></> : <><div><span>Metric</span><strong>Transmission Factor</strong></div><div><span>Unit Origin</span><strong>1.00</strong></div></>}
            <div><span>Visible Results</span><strong>{visibleCompanies.length}</strong></div><div><span>Strongest Path</span><strong>Fixture only</strong></div>
          </div>
          <p>{isEventOrigin ? "Selecting a company exposes only the factors carried by this explicit event fixture. Missing per-edge factors are not reconstructed." : "Company-origin analysis describes fixture transmission strength, not aggregate Current Risk."}</p>
          {investigation.highlightedPath && <div className="phase2-highlight-path-text"><strong>Highlighted path</strong><span>{investigation.highlightedPath.join(" → ")}</span></div>}
          {selectedCompany && (
            selectedProfileId && hasCompanyProfile(selectedProfileId)
              ? <Button variant="secondary" onClick={() => onOpenCompanyProfile(selectedProfileId)}>Open Profile</Button>
              : <span className="phase2-profile-unavailable">Profile unavailable for this development entity.</span>
          )}
        </div>
      </div>
      <footer className="impact-legend"><span>{isEventOrigin ? "Risk:" : "Transmission bands (development fixture):"}</span>{isEventOrigin ? <><RiskBadge level="CRITICAL" /><RiskBadge level="HIGH" /><RiskBadge level="MEDIUM" /></> : <span className="phase2-interaction-note">Not Current Risk</span>}</footer>
      <div className="phase2-accessible-list"><h3>Accessible Blast Radius results</h3><ul>{visibleCompanies.map((company) => <li key={`impact-list-${company.id}`}><button type="button" onClick={() => selectCompany(company)}>{company.company} · {company.hop} · {isEventOrigin ? "Propagated Risk" : "Transmission Factor"} {company.score}</button></li>)}</ul></div>
    </section>
  );
}

function ImpactUnavailableState({ title, detail, onReturnToStructure }: { title: string; detail: string; onReturnToStructure: () => void }) {
  return (
    <section className="network-canvas impact-canvas" aria-label="Impact unavailable">
      <div className="network-canvas-header"><div><span className="metadata-text">IMPACT MODE</span><strong>Blast Radius</strong></div><CanvasActions label="No impact fixture rendered" /></div>
      <div className="phase2-impact-empty" role="status">
        <AlertTriangle size={24} aria-hidden="true" />
        <div><strong>{title}</strong><span>{detail}</span></div>
        <Button variant="secondary" onClick={onReturnToStructure}>Return to Structure</Button>
      </div>
    </section>
  );
}

function NetworkState({ title, detail, actionLabel, onAction }: { title: string; detail: string; actionLabel: string; onAction: () => void }) {
  return (
    <section className="network-canvas network-canvas--state" aria-label="Structure network state">
      <div className="network-canvas-header"><div><span className="metadata-text">STRUCTURE MODE</span><strong>Supply Network Structure</strong></div><CanvasActions label="No graph substituted" /></div>
      <div className="phase2-network-state" role="status">
        <Network size={26} aria-hidden="true" />
        <div><strong>{title}</strong><span>{detail}</span></div>
        <Button variant="secondary" onClick={onAction}>{actionLabel}</Button>
      </div>
    </section>
  );
}

function ImpactCompany({ company, hop, score, level, className, valueLabel, selected, onClick }: { company: string; hop: string; score: string; level: "CRITICAL" | "HIGH" | "MEDIUM"; className: string; valueLabel: string; selected: boolean; onClick: () => void }) {
  return <button type="button" className={`impact-company ${className}${selected ? " is-selected" : ""}`} onClick={onClick} aria-pressed={selected} title={`${company} · ${hop} · ${valueLabel} ${score}`}><div className={`impact-company-node impact-company-node--${level.toLowerCase()}`} /><div className="impact-company-copy"><strong>{company}</strong><span>{hop}</span><span>{valueLabel} {score}</span></div></button>;
}

function CanvasActions({ label }: { label: string }) {
  return <div className="network-canvas-actions"><span>{label}</span></div>;
}

function StructureLegend() {
  return <footer className="network-legend"><div className="network-legend-title"><CircleDot size={14} aria-hidden="true" /><span>Entity Types</span></div><div className="network-legend-items">{legendItems.map((item) => <div className="network-legend-item" key={item.type}><span className={`legend-shape legend-shape--${item.type.toLowerCase()}`} aria-hidden="true" /><span>{item.label}</span></div>)}</div></footer>;
}
