import { useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  CircleDot,
  LocateFixed,
  Maximize2,
  Network,
  RotateCcw,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { RiskBadge } from "../components/ui/RiskBadge";
import { networkImpactDemo } from "../data/networkImpactDemo";
import {
  networkStructureDemoNodes,
  type DemoGraphNodeType,
} from "../data/networkStructureDemo";

import "./NetworkPage.css";

type NetworkMode = "structure" | "impact";

const legendItems: Array<{
  type: DemoGraphNodeType;
  label: string;
}> = [
  { type: "Company", label: "Company" },
  { type: "Facility", label: "Facility" },
  { type: "Material", label: "Material" },
  { type: "Product", label: "Product" },
  { type: "Technology", label: "Technology" },
  { type: "Country", label: "Country" },
];

export function NetworkPage() {
  const [mode, setMode] = useState<NetworkMode>("structure");

  return (
    <div className="network-page">
      <header className="network-header">
        <div>
          <div className="network-title-context">
            <span className="metadata-text">GRAPH EXPLORER</span>
            <span className="demo-badge">DEVELOPMENT DATA</span>
          </div>

          <h1 className="page-title">Network</h1>

          <p className="body-text network-subtitle">
            {mode === "structure"
              ? "Explore structural supply-chain relationships across companies and connected entities."
              : "Inspect how disruption risk propagates across downstream supply-chain paths."}
          </p>
        </div>

        <div className="network-mode-switch" aria-label="Network mode">
          <button
            type="button"
            className={`network-mode-button${
              mode === "structure" ? " is-active" : ""
            }`}
            aria-pressed={mode === "structure"}
            onClick={() => setMode("structure")}
          >
            STRUCTURE
          </button>

          <button
            type="button"
            className={`network-mode-button${
              mode === "impact" ? " is-active" : ""
            }`}
            aria-pressed={mode === "impact"}
            onClick={() => setMode("impact")}
          >
            IMPACT
          </button>
        </div>
      </header>

      <section className="network-toolbar" aria-label="Network controls">
        <div className="network-search-control">
          <Search size={15} aria-hidden="true" />
          <span>Search entity</span>
          <small>Adapter pending</small>
        </div>

        <div className="network-toolbar-divider" />

        <div className="network-control-group">
          <span className="network-control-label">
            {mode === "structure" ? "Depth" : "Max Hops"}
          </span>

          <button type="button" className="depth-button is-active">
            1
          </button>

          <button type="button" className="depth-button">
            2
          </button>

          <button type="button" className="depth-button">
            3
          </button>
        </div>

        <div className="network-toolbar-divider" />

        {mode === "structure" ? (
          <>
            <button type="button" className="network-toolbar-button">
              <CircleDot size={14} aria-hidden="true" />
              <span>Node Types</span>
              <ChevronDown size={13} aria-hidden="true" />
            </button>

            <button type="button" className="network-toolbar-button">
              <SlidersHorizontal size={14} aria-hidden="true" />
              <span>Relationships</span>
              <ChevronDown size={13} aria-hidden="true" />
            </button>
          </>
        ) : (
          <div className="impact-toolbar-context">
            <AlertTriangle size={14} aria-hidden="true" />
            <span>Demo propagation context</span>
          </div>
        )}

        <div className="network-toolbar-spacer" />

        <Button variant="ghost" icon={<RotateCcw size={14} />}>
          Reset
        </Button>
      </section>

      {mode === "structure" ? (
        <StructureCanvas />
      ) : (
        <ImpactCanvas />
      )}
    </div>
  );
}

function StructureCanvas() {
  return (
    <section
      className="network-canvas"
      aria-label="Structure graph preview"
    >
      <div className="network-canvas-header">
        <div>
          <span className="metadata-text">STRUCTURE MODE</span>
          <strong>Supply Network Structure</strong>
        </div>

        <CanvasActions label="Demo topology" />
      </div>

      <div className="network-graph-surface">
        <svg
          className="network-edges"
          viewBox="0 0 1000 600"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <marker
              id="structure-arrow"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="4"
              orient="auto"
            >
              <path
                d="M0,0 L8,4 L0,8 Z"
                className="network-arrow-head"
              />
            </marker>
          </defs>

          <line x1="170" y1="144" x2="450" y2="235" className="network-edge" markerEnd="url(#structure-arrow)" />
          <line x1="470" y1="235" x2="750" y2="170" className="network-edge" markerEnd="url(#structure-arrow)" />
          <line x1="450" y1="250" x2="360" y2="420" className="network-edge" markerEnd="url(#structure-arrow)" />
          <line x1="755" y1="185" x2="670" y2="420" className="network-edge" markerEnd="url(#structure-arrow)" />
          <line x1="775" y1="185" x2="850" y2="340" className="network-edge" markerEnd="url(#structure-arrow)" />
        </svg>

        <div className="relationship-label relationship-label--one">SUPPLIES</div>
        <div className="relationship-label relationship-label--two">SUPPLIES</div>
        <div className="relationship-label relationship-label--three">OPERATES</div>
        <div className="relationship-label relationship-label--four">USES</div>
        <div className="relationship-label relationship-label--five">PRODUCES</div>

        {networkStructureDemoNodes.map((node) => (
          <div
            key={node.id}
            className="graph-node-wrapper"
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
          >
            <div
              className={`graph-node graph-node--${node.type.toLowerCase()}${
                node.label === "TSMC" ? " is-selected" : ""
              }`}
            >
              {node.type === "Company" && (
                <Network size={16} aria-hidden="true" />
              )}
            </div>

            <div className="graph-node-copy">
              <strong>{node.label}</strong>
              <span>{node.type}</span>
            </div>
          </div>
        ))}

        <div className="network-canvas-notice">
          <span>DEMO STRUCTURE</span>
          <p>
            Static visual fixture for Phase 1. Relationship direction is
            preserved.
          </p>
        </div>
      </div>

      <StructureLegend />
    </section>
  );
}

function ImpactCanvas() {
  const { origin, companies, paths, context } = networkImpactDemo;

  return (
    <section
      className="network-canvas impact-canvas"
      aria-label="Impact graph preview"
    >
      <div className="network-canvas-header">
        <div>
          <span className="metadata-text">IMPACT MODE</span>
          <strong>Blast Radius Preview</strong>
        </div>

        <CanvasActions label="Demo propagation" />
      </div>

      <div className="impact-surface">
        <div className="impact-origin-card">
          <span className="metadata-text">DEMO ORIGIN</span>
          <strong>{origin.label}</strong>
          <span>Development-only propagation scenario</span>
        </div>

        <div className="blast-radius-stage">
          <div className="blast-ring blast-ring--three">
            <span className="blast-ring-label">HOP 3</span>
          </div>

          <div className="blast-ring blast-ring--two">
            <span className="blast-ring-label">HOP 2</span>
          </div>

          <div className="blast-ring blast-ring--one">
            <span className="blast-ring-label">HOP 1</span>
          </div>

          <div className="blast-origin-node">
            <AlertTriangle size={19} aria-hidden="true" />
            <strong>{origin.company}</strong>
            <span>Origin</span>
          </div>

          {companies.map((company) => (
            <ImpactCompany
              key={company.id}
              className={`impact-company--${company.position}`}
              company={company.company}
              hop={company.hop}
              score={company.score}
              level={company.level}
            />
          ))}

          <svg
            className="impact-paths"
            viewBox="0 0 1000 600"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="impact-arrow"
                markerWidth="8"
                markerHeight="8"
                refX="7"
                refY="4"
                orient="auto"
              >
                <path
                  d="M0,0 L8,4 L0,8 Z"
                  className="impact-arrow-head"
                />
              </marker>
            </defs>

            {paths.map((path) => (
              <line
                key={path.id}
                x1={path.x1}
                y1={path.y1}
                x2={path.x2}
                y2={path.y2}
                className={`impact-path impact-path--${path.tone}`}
                markerEnd="url(#impact-arrow)"
              />
            ))}
          </svg>
        </div>

        <div className="impact-context-panel">
          <div>
            <span className="metadata-text">PROPAGATION CONTEXT</span>
            <strong>3-hop downstream preview</strong>
          </div>

          <div className="impact-context-grid">
            <div>
              <span>Initial Risk</span>
              <strong>{context.initialRisk}</strong>
            </div>

            <div>
              <span>Max Hops</span>
              <strong>{context.maxHops}</strong>
            </div>

            <div>
              <span>Distance Decay</span>
              <strong>{context.distanceDecay}</strong>
            </div>

            <div>
              <span>Affected Companies</span>
              <strong>{context.affectedCompanies}</strong>
            </div>
          </div>

          <p>
            Demo values are shown only to validate the Phase 1 Impact-mode
            visual hierarchy.
          </p>
        </div>
      </div>

      <footer className="impact-legend">
        <span>Risk:</span>
        <RiskBadge level="CRITICAL" />
        <RiskBadge level="HIGH" />
        <RiskBadge level="MEDIUM" />
      </footer>
    </section>
  );
}

type ImpactCompanyProps = {
  company: string;
  hop: string;
  score: string;
  level: "CRITICAL" | "HIGH" | "MEDIUM";
  className: string;
};

function ImpactCompany({
  company,
  hop,
  score,
  level,
  className,
}: ImpactCompanyProps) {
  return (
    <div className={`impact-company ${className}`}>
      <div
        className={`impact-company-node impact-company-node--${level.toLowerCase()}`}
      />

      <div className="impact-company-copy">
        <strong>{company}</strong>
        <span>{hop}</span>
        <span>Demo risk {score}</span>
      </div>
    </div>
  );
}

function CanvasActions({ label }: { label: string }) {
  return (
    <div className="network-canvas-actions">
      <span>{label}</span>

      <button
        type="button"
        className="network-icon-button"
        aria-label="Center graph"
      >
        <LocateFixed size={15} />
      </button>

      <button
        type="button"
        className="network-icon-button"
        aria-label="Expand graph canvas"
      >
        <Maximize2 size={15} />
      </button>
    </div>
  );
}

function StructureLegend() {
  return (
    <footer className="network-legend">
      <div className="network-legend-title">
        <CircleDot size={14} aria-hidden="true" />
        <span>Entity Types</span>
      </div>

      <div className="network-legend-items">
        {legendItems.map((item) => (
          <div className="network-legend-item" key={item.type}>
            <span
              className={`legend-shape legend-shape--${item.type.toLowerCase()}`}
              aria-hidden="true"
            />

            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </footer>
  );
}
