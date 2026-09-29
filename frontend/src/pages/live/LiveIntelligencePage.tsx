import { useState } from "react";
import { AlertTriangle, ArrowRight, BrainCircuit, FileText, GitBranch, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Panel } from "../../components/ui/Panel";
import { useAgentQuery } from "../../query/hooks";

import "../IntelligencePage.css";
import "./LiveIntelligencePage.css";

export function LiveIntelligencePage() {
  const navigate = useNavigate();
  const agent = useAgentQuery();
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(null);
  const canSubmit = question.trim().length > 0 && !agent.isPending;

  const submit = () => {
    if (!canSubmit) return;
    const normalized = question.trim();
    setSubmittedQuestion(normalized);
    agent.mutate(normalized);
  };

  const answer = agent.data;

  return <div className="intelligence-page">
    <header className="intelligence-header">
      <div><div className="intelligence-title-context"><span className="metadata-text">GRAPH-GROUNDED INTELLIGENCE</span><span className="demo-badge">LIVE AGENT API</span></div><h1 className="page-title">Intelligence</h1><p className="body-text intelligence-subtitle">Ask natural-language questions about the knowledge graph. The frontend displays the grounded answer, returned evidence references, paths, and warnings—never hidden chain-of-thought.</p></div>
      <div className="intelligence-api-state"><BrainCircuit size={18} aria-hidden="true" /><div><strong>POST /api/v1/agent/query</strong><span>{agent.isPending ? "Query running" : agent.isError ? "Last query failed" : answer ? "Grounded response returned" : "Ready"}</span></div></div>
    </header>

    <form className="intelligence-query-composer" onSubmit={(event) => { event.preventDefault(); submit(); }}>
      <BrainCircuit size={22} aria-hidden="true" />
      <div className="intelligence-query-copy"><span className="metadata-text">ASK INTELLIGENCE</span><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="e.g. What supply-chain dependencies connect TSMC to downstream companies?" aria-label="Ask Intelligence" /></div>
      <Button type="submit" variant="primary" disabled={!canSubmit}>{agent.isPending ? "Analyzing…" : "Ask"}</Button>
    </form>
    <div className="intelligence-api-note"><ShieldCheck size={14} aria-hidden="true" /> Queries are sent explicitly. Failed live requests never fall back to canned/demo answers.</div>

    {agent.isError && <Panel variant="workspace" eyebrow="Agent error" title="Intelligence request unavailable"><div className="live-intelligence-state is-error" role="alert"><AlertTriangle size={18} /><span>{errorText(agent.error)} No fabricated answer is displayed.</span></div></Panel>}

    {!answer && !agent.isPending && !agent.isError && <Panel variant="workspace" eyebrow="Grounded answer" title="Ask a graph question"><div className="live-intelligence-state"><BrainCircuit size={22} /><span>The Agent response will appear here with evidence status, path summaries, Event references, and warnings returned by the backend.</span></div></Panel>}

    {agent.isPending && <Panel variant="workspace" eyebrow="Grounded answer" title="Inspecting graph evidence"><div className="live-intelligence-state"><BrainCircuit size={22} /><span>Waiting for the live Agent API. The current question remains visible and no previous/demo answer is substituted.</span></div></Panel>}

    {answer && <>
      <div className="intelligence-result-header"><div><span className="metadata-text">QUESTION</span><h2>{submittedQuestion}</h2></div><span className="intelligence-grounded-badge">{answer.evidenceStatus || "UNKNOWN EVIDENCE"}</span></div>

      <section className="intelligence-result-grid">
        <Panel variant="workspace" eyebrow="Grounded answer" title="Response">
          <div className="intelligence-answer"><div className="intelligence-answer-icon"><BrainCircuit size={20} /></div><p>{answer.answer}</p></div>
          <div className="intelligence-answer-actions">
            {answer.eventRefs.slice(0, 3).map((eventId) => <Button key={eventId} variant="secondary" icon={<FileText size={14} />} onClick={() => navigate(`/events/${encodeURIComponent(eventId)}`)}>Open Event {eventId}</Button>)}
            {answer.eventRefs[0] && <Button variant="primary" icon={<ArrowRight size={14} />} onClick={() => navigate(`/network?mode=impact&focusType=Event&focusId=${encodeURIComponent(answer.eventRefs[0])}&eventId=${encodeURIComponent(answer.eventRefs[0])}&maxHops=3`)}>Open Event Impact</Button>}
          </div>
        </Panel>

        <Panel eyebrow="Graph support" title="Returned Paths">
          {answer.paths.length ? <div className="live-intelligence-paths">{answer.paths.map((path, index) => <div key={`${path.pathId ?? "path"}:${index}`} className="intelligence-path-summary"><GitBranch size={15} aria-hidden="true" /><div><span>Path {index + 1}{path.pathId ? ` · ${path.pathId}` : ""}</span><strong>{path.names.join(" → ")}</strong></div></div>)}</div> : <div className="live-intelligence-empty">No dependency path was returned.</div>}
          <p className="phase2-interaction-note">Show Network is not fabricated from names alone. The public Agent contract does not guarantee canonical typed IDs for every returned entity/path node.</p>
        </Panel>
      </section>

      <section className="intelligence-support-grid">
        <Panel eyebrow="Affected entities" title="Entities Mentioned">{answer.entities.length ? <div className="live-intelligence-tags">{answer.entities.map((entity, index) => <span key={`${entity.name}:${index}`}>{entity.name}{entity.type ? ` · ${entity.type}` : ""}</span>)}</div> : <div className="live-intelligence-empty">No affected entities returned.</div>}<p className="phase2-interaction-note">Names without canonical IDs are display-only and do not receive false profile/network actions.</p></Panel>
        <Panel eyebrow="Evidence / provenance" title="Supporting References">{answer.provenance.length ? <div className="live-intelligence-provenance">{answer.provenance.map((item, index) => <div key={`${item.eventId ?? "evidence"}:${index}`}><strong>{item.availability}</strong><span>Source: {item.source ?? "Not available"}</span><span>Event: {item.eventId ?? "Not available"}</span><span>Confidence: {item.confidence === undefined ? "Not available" : `${(item.confidence * 100).toFixed(0)}%`}</span></div>)}</div> : <div className="live-intelligence-empty">No provenance records returned.</div>}</Panel>
      </section>

      {(answer.hopCounts.length > 0 || answer.warnings.length > 0) && <section className="intelligence-support-grid">
        <Panel eyebrow="Traversal" title="Hop Evidence"><div className="live-intelligence-tags">{answer.hopCounts.length ? answer.hopCounts.map((hop, index) => <span key={`${hop}:${index}`}>Hop {hop}</span>) : <span>No hop counts returned</span>}</div></Panel>
        <Panel eyebrow="Guardrails" title="Warnings">{answer.warnings.length ? <div className="live-intelligence-warnings">{answer.warnings.map((warning, index) => <div key={`${warning}:${index}`}><AlertTriangle size={14} /><span>{warning}</span></div>)}</div> : <div className="live-intelligence-empty">No warnings returned.</div>}</Panel>
      </section>}
    </>}
  </div>;
}

function errorText(error: unknown): string { return error instanceof Error ? error.message : "Unknown Agent API error."; }
