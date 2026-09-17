import {
  ArrowRight,
  BrainCircuit,
  Building2,
  FileText,
  Network,
  Route,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";

import { intelligenceDemo } from "../data/intelligenceDemo";

import "./IntelligencePage.css";

export function IntelligencePage() {
  return (
    <div className="intelligence-page">
      <header className="intelligence-header">
        <div>
          <div className="intelligence-title-context">
            <span className="metadata-text">
              GRAPH-GROUNDED ANALYSIS
            </span>

            <span className="demo-badge">
              DEVELOPMENT DATA
            </span>
          </div>

          <h1 className="page-title">
            Intelligence
          </h1>

          <p className="body-text intelligence-subtitle">
            Ask supply-chain questions and connect explanations back to
            graph paths, risk calculations, entities, and available
            evidence.
          </p>
        </div>

        <div className="intelligence-api-state">
          <BrainCircuit size={15} aria-hidden="true" />

          <div>
            <strong>Agent API available</strong>
            <span>Runtime provider configuration required</span>
          </div>
        </div>
      </header>

      <section
        className="intelligence-query-composer"
        aria-label="Intelligence query composer"
      >
        <Search size={18} aria-hidden="true" />

        <div className="intelligence-query-copy">
          <span className="metadata-text">
            ASK INTELLIGENCE
          </span>

          <span>
            Ask a question about the graph, companies, risk, events, or
            evidence...
          </span>
        </div>

        <Button
          variant="primary"
          icon={<Sparkles size={15} />}
          disabled
        >
          Ask
        </Button>
      </section>

      <div className="intelligence-api-note">
        <ShieldCheck size={14} aria-hidden="true" />

        <span>
          POST /api/v1/agent/query is available. Live query wiring remains
          pending in the frontend, and production LLM responses require a
          configured runtime provider.
        </span>
      </div>

      <section className="intelligence-result-header">
        <div>
          <span className="metadata-text">
            DEVELOPMENT EXAMPLE
          </span>

          <h2>
            {intelligenceDemo.question}
          </h2>
        </div>

        <span className="intelligence-grounded-badge">
          GRAPH GROUNDED
        </span>
      </section>

      <section className="intelligence-result-grid">
        <Panel
          className="intelligence-answer-panel"
          variant="workspace"
          eyebrow="Grounded answer"
          title="Explanation"
          description="Development-only example of the intended graph-grounded response architecture."
        >
          <div className="intelligence-answer">
            <div className="intelligence-answer-icon">
              <BrainCircuit size={22} aria-hidden="true" />
            </div>

            <p>
              {intelligenceDemo.answer}
            </p>
          </div>

          <div className="intelligence-answer-actions">
            <Button
              variant="secondary"
              icon={<Network size={14} />}
              disabled
            >
              Show Network
            </Button>

            <Button
              variant="secondary"
              icon={<Route size={14} />}
              disabled
            >
              Open Impact
            </Button>

            <Button
              variant="ghost"
              icon={<FileText size={14} />}
              disabled
            >
              View Evidence
            </Button>
          </div>
        </Panel>

        <Panel
          className="intelligence-support-panel"
          eyebrow="Supporting graph"
          title="Graph Evidence"
          description="The answer should visibly connect back to graph structure."
        >
          <div className="intelligence-graph-preview">
            <div className="intelligence-graph-node">
              <span>Company</span>
              <strong>TSMC</strong>
            </div>

            <div className="intelligence-graph-edge">
              <span>{intelligenceDemo.relationship}</span>

              <ArrowRight
                size={22}
                aria-hidden="true"
              />
            </div>

            <div className="intelligence-graph-node is-target">
              <span>Company</span>
              <strong>NVIDIA</strong>
            </div>
          </div>

          <div className="intelligence-path-summary">
            <Route size={15} aria-hidden="true" />

            <div>
              <span>Highlighted path</span>

              <strong>
                {intelligenceDemo.path.join(" → ")}
              </strong>
            </div>
          </div>
        </Panel>
      </section>

      <section className="intelligence-support-grid">
        <Panel
          eyebrow="Entities"
          title="Supporting Entities"
        >
          <div className="intelligence-entity-list">
            {intelligenceDemo.entities.map((entity) => (
              <article
                className="intelligence-entity"
                key={entity.id}
              >
                <div className="intelligence-entity-icon">
                  <Building2
                    size={15}
                    aria-hidden="true"
                  />
                </div>

                <div>
                  <strong>{entity.name}</strong>
                  <span>{entity.type}</span>
                </div>
              </article>
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="Risk result"
          title="Exposure Trace"
        >
          <div className="intelligence-risk-trace">
            <TraceItem
              label="Hop Distance"
              value={String(
                intelligenceDemo.risk.hopDistance,
              )}
            />

            <TraceItem
              label="Initial Risk"
              value={intelligenceDemo.risk.initialRisk}
            />

            <TraceItem
              label="Combined Path Dependency"
              value={intelligenceDemo.risk.pathDependency}
            />

            <TraceItem
              label="Distance Decay"
              value={intelligenceDemo.risk.distanceDecay}
            />

            <TraceItem
              label="Propagated Risk"
              value={intelligenceDemo.risk.propagatedRisk}
              emphasized
            />
          </div>
        </Panel>
      </section>

      <Panel
        eyebrow="Evidence & provenance"
        title="Supporting Evidence"
        description="Only evidence fields actually available should appear in the production response."
      >
        <div className="intelligence-evidence-list">
          {intelligenceDemo.evidence.map((evidence) => (
            <article
              className="intelligence-evidence"
              key={evidence.id}
            >
              <div className="intelligence-evidence-icon">
                <FileText
                  size={17}
                  aria-hidden="true"
                />
              </div>

              <div className="intelligence-evidence-fields">
                <EvidenceField
                  label="Source"
                  value={evidence.source}
                />

                <EvidenceField
                  label="Document"
                  value={evidence.document}
                />

                <EvidenceField
                  label="Confidence"
                  value={evidence.confidence}
                />

                <EvidenceField
                  label="Extracted Context"
                  value={evidence.extractedContext}
                  unavailable={
                    evidence.extractedContext ===
                    "Not available"
                  }
                />
              </div>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}

type TraceItemProps = {
  label: string;
  value: string;
  emphasized?: boolean;
};

function TraceItem({
  label,
  value,
  emphasized = false,
}: TraceItemProps) {
  return (
    <div
      className={`intelligence-trace-item${
        emphasized ? " is-emphasized" : ""
      }`}
    >
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

type EvidenceFieldProps = {
  label: string;
  value: string;
  unavailable?: boolean;
};

function EvidenceField({
  label,
  value,
  unavailable = false,
}: EvidenceFieldProps) {
  return (
    <div className="intelligence-evidence-field">
      <span>{label}</span>

      <strong
        className={
          unavailable ? "is-unavailable" : undefined
        }
      >
        {value}
      </strong>
    </div>
  );
}
