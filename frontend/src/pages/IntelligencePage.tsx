import { useEffect, useState } from "react";
import { ArrowRight, BrainCircuit, Building2, FileText, Network, Route, Search, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import type { InspectorContext } from "../data/inspectorDemo";
import { intelligenceDemo } from "../data/intelligenceDemo";

import "./IntelligencePage.css";
import "./IntelligencePhase2.css";

type IntelligencePageProps = {
  onInspect: (context: InspectorContext) => void;
  onShowNetwork: (path: string[]) => void;
  onOpenImpact: (focus: { id: string; name: string; type: "Company" | "Event"; eventId?: string }) => void;
};

export function IntelligencePage({ onInspect, onShowNetwork, onOpenImpact }: IntelligencePageProps) {
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState(intelligenceDemo.question);
  const [preparing, setPreparing] = useState(false);
  const [failed, setFailed] = useState(false);
  const [selectedPath, setSelectedPath] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);

  useEffect(() => {
    if (!preparing) return;
    const timer = window.setTimeout(() => setPreparing(false), 350);
    return () => window.clearTimeout(timer);
  }, [preparing]);

  const submit = () => {
    const trimmed = question.trim();
    if (!trimmed) return;
    setSubmittedQuestion(trimmed);
    setFailed(false);
    setPreparing(true);
    setSelectedPath(false);
    setShowEvidence(false);
  };

  const retry = () => {
    setFailed(false);
    setPreparing(true);
  };

  const inspectEntity = (entity: (typeof intelligenceDemo.entities)[number]) => {
    onInspect({
      id: entity.name === "TSMC" ? "demo-tsmc" : entity.name === "NVIDIA" ? "demo-nvidia" : entity.id,
      type: entity.type === "Company" ? "Company" : "Material",
      name: entity.name,
      subtitle: "Referenced by development Intelligence result",
      fields: [{ label: "Reference type", value: entity.type }],
      evidence: { availability: "PARTIAL", source: "Development Intelligence evidence", provenance: "Development fixture" },
    });
  };

  return (
    <div className="intelligence-page">
      <header className="intelligence-header">
        <div><div className="intelligence-title-context"><span className="metadata-text">GRAPH-GROUNDED ANALYSIS</span><span className="demo-badge">DEVELOPMENT DATA</span></div><h1 className="page-title">Intelligence</h1><p className="body-text intelligence-subtitle">Ask questions and move explicitly from the explanation into entities, paths, Network, Impact, and evidence.</p></div>
        <div className="intelligence-api-state"><BrainCircuit size={15} aria-hidden="true" /><div><strong>Agent API available</strong><span>Runtime provider configuration may still be required</span></div></div>
      </header>

      <form className="intelligence-query-composer" aria-label="Intelligence query composer" onSubmit={(event) => { event.preventDefault(); submit(); }}>
        <Search size={18} aria-hidden="true" />
        <label className="intelligence-query-copy"><span className="metadata-text">ASK INTELLIGENCE</span><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question about the graph, companies, risk, events, or evidence..." aria-label="Intelligence question" /></label>
        <Button type="submit" variant="primary" icon={<Sparkles size={15} />} disabled={!question.trim() || preparing}>{preparing ? "Preparing response..." : "Send"}</Button>
      </form>

      <div className="intelligence-api-note"><ShieldCheck size={14} aria-hidden="true" /><span>This Phase 2 interaction uses a clearly labeled development response fixture. It does not display hidden reasoning or chain-of-thought.</span><Button variant="ghost" onClick={() => { setPreparing(false); setFailed(true); setShowEvidence(false); }}>DEMO FAILURE</Button></div>

      <section className="intelligence-result-header"><div><span className="metadata-text">DEVELOPMENT RESPONSE</span><h2>{submittedQuestion}</h2></div><span className="intelligence-grounded-badge">GRAPH GROUNDED</span></section>

      {preparing ? (
        <div className="phase2-intelligence-loading" role="status"><BrainCircuit size={20} aria-hidden="true" /><strong>Preparing response...</strong><span>No internal reasoning steps are displayed.</span></div>
      ) : failed ? (
        <div className="phase2-intelligence-error" role="alert"><BrainCircuit size={20} aria-hidden="true" /><strong>Unable to prepare Intelligence response.</strong><span>This is a Phase 2 development failure state; no production Agent API request was made.</span><Button variant="secondary" onClick={retry}>Retry</Button></div>
      ) : (
        <>
          <section className="intelligence-result-grid">
            <Panel className="intelligence-answer-panel" variant="workspace" eyebrow="Grounded answer" title="Explanation" description="Development-only graph-grounded response architecture.">
              <div className="intelligence-answer"><div className="intelligence-answer-icon"><BrainCircuit size={22} aria-hidden="true" /></div><p>{intelligenceDemo.answer}</p></div>
              <div className="intelligence-answer-actions"><Button variant="secondary" icon={<Network size={14} />} onClick={() => onShowNetwork(intelligenceDemo.path)}>Show Network</Button><Button variant="secondary" icon={<Route size={14} />} onClick={() => onOpenImpact({ id: "demo-tsmc", name: intelligenceDemo.path[0], type: "Company" })}>Open Impact</Button><Button variant="ghost" icon={<FileText size={14} />} aria-expanded={showEvidence} onClick={() => setShowEvidence((value) => !value)}>View Evidence</Button></div>
            </Panel>

            <Panel className="intelligence-support-panel" eyebrow="Supporting graph" title="Graph Evidence" description="Select the path first; Show Network is the explicit navigation action.">
              <button type="button" className={`intelligence-graph-preview phase2-path-button${selectedPath ? " is-selected" : ""}`} onClick={() => setSelectedPath(true)} aria-pressed={selectedPath}>
                <div className="intelligence-graph-node"><span>Company</span><strong>TSMC</strong></div><div className="intelligence-graph-edge"><span>{intelligenceDemo.relationship}</span><ArrowRight size={22} aria-hidden="true" /></div><div className="intelligence-graph-node is-target"><span>Company</span><strong>NVIDIA</strong></div>
              </button>
              <button type="button" className={`intelligence-path-summary phase2-path-summary${selectedPath ? " is-selected" : ""}`} onClick={() => setSelectedPath(true)}><Route size={15} aria-hidden="true" /><div><span>Supporting path</span><strong>{intelligenceDemo.path.join(" → ")}</strong></div></button>
              {selectedPath && <div className="phase2-inline-actions"><Button variant="primary" onClick={() => onShowNetwork(intelligenceDemo.path)}>Show Network</Button><Button variant="ghost" onClick={() => setSelectedPath(false)}>Clear Highlight</Button></div>}
            </Panel>
          </section>

          <section className="intelligence-support-grid">
            <Panel eyebrow="Entities" title="Supporting Entities"><div className="intelligence-entity-list">{intelligenceDemo.entities.map((entity) => <button type="button" className="intelligence-entity phase2-intelligence-entity" key={entity.id} onClick={() => inspectEntity(entity)}><div className="intelligence-entity-icon"><Building2 size={15} aria-hidden="true" /></div><div><strong>{entity.name}</strong><span>{entity.type}</span></div></button>)}</div></Panel>
            <Panel eyebrow="Risk result" title="Exposure Trace"><div className="intelligence-risk-trace"><TraceItem label="Hop Distance" value={String(intelligenceDemo.risk.hopDistance)} /><TraceItem label="Initial Risk" value={intelligenceDemo.risk.initialRisk} /><TraceItem label="Combined Path Dependency" value={intelligenceDemo.risk.pathDependency} /><TraceItem label="Distance Decay" value={intelligenceDemo.risk.distanceDecay} /><TraceItem label="Propagated Risk" value={intelligenceDemo.risk.propagatedRisk} emphasized /></div></Panel>
          </section>

          {showEvidence && <Panel eyebrow="Evidence & provenance" title="Supporting Evidence" description="Only fixture fields that actually exist are shown; unavailable context remains explicit."><div className="intelligence-evidence-list">{intelligenceDemo.evidence.map((evidence) => <article className="intelligence-evidence" key={evidence.id}><div className="intelligence-evidence-icon"><FileText size={17} aria-hidden="true" /></div><div className="intelligence-evidence-fields"><EvidenceField label="Source" value={evidence.source} /><EvidenceField label="Document" value={evidence.document} /><EvidenceField label="Confidence" value={evidence.confidence} /><EvidenceField label="Extracted Context" value={evidence.extractedContext} unavailable={evidence.extractedContext === "Not available"} /></div></article>)}</div></Panel>}

          <details className="phase2-technical-details"><summary>Technical Details</summary><p>Generated Cypher is not present in this development fixture, so it is not invented.</p></details>
        </>
      )}
    </div>
  );
}

function TraceItem({ label, value, emphasized = false }: { label: string; value: string; emphasized?: boolean }) { return <div className={`intelligence-trace-item${emphasized ? " is-emphasized" : ""}`}><span>{label}</span><strong>{value}</strong></div>; }
function EvidenceField({ label, value, unavailable = false }: { label: string; value: string; unavailable?: boolean }) { return <div className="intelligence-evidence-field"><span>{label}</span><strong className={unavailable ? "is-unavailable" : undefined}>{value}</strong></div>; }
