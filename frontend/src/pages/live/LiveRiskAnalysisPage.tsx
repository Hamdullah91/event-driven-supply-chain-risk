import { useEffect, useMemo, useState } from "react";
import { Activity, BarChart3, Clock3, Map, Search, ShieldAlert } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Panel } from "../../components/ui/Panel";
import { RiskBadge } from "../../components/ui/RiskBadge";
import type { SearchResult } from "../../domain/types";
import { useCompany, useCompanyExposure, useCompanyRisk, useEntitySearch, useRiskHistory } from "../../query/hooks";
import { useUiStore } from "../../state/uiStore";

import "../RiskAnalysisPage.css";
import "./LiveRiskAnalysisPage.css";

type Lens = "NETWORK" | "GEOGRAPHY" | "HEATMAP";

export function LiveRiskAnalysisPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const companyId = params.get("companyId") || undefined;
  const maxHops = hop(params.get("maxHops"));
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [lens, setLens] = useState<Lens>("NETWORK");
  const search = useEntitySearch(debouncedQuery, 20);
  const company = useCompany(companyId);
  const risk = useCompanyRisk(companyId, maxHops);
  const exposure = useCompanyExposure(companyId, maxHops);
  const history = useRiskHistory(companyId, maxHops, 100);
  const setInspectorRef = useUiStore((state) => state.setInspectorRef);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const companyResults = useMemo(() => (search.data ?? []).filter((result) => result.entity.type === "Company"), [search.data]);
  const selectCompany = (result: SearchResult) => {
    const next = new URLSearchParams(params);
    next.set("companyId", result.entity.id);
    next.set("maxHops", String(maxHops));
    setParams(next);
    setQuery("");
    setInspectorRef({ kind: "entity", id: result.entity.id, entityType: "Company", name: result.entity.name });
  };
  const setMaxHops = (value: 1 | 2 | 3) => {
    const next = new URLSearchParams(params);
    next.set("maxHops", String(value));
    setParams(next);
  };

  return <div className="risk-analysis-page">
    <header className="risk-analysis-header"><div><div className="risk-analysis-title-context"><span className="metadata-text">SYSTEM RISK WORKSPACE</span><span className="demo-badge">LIVE DATA</span></div><h1 className="page-title">Risk Analysis</h1><p className="body-text risk-analysis-subtitle">The backend has no system-wide aggregate ranking endpoint, so LIVE mode analyzes one explicitly selected company without issuing uncontrolled per-company risk requests.</p></div><div className="risk-analysis-history-state"><Clock3 size={14} aria-hidden="true" /><span>History is event-derived reconstruction, not persisted market snapshots.</span></div></header>

    <section className="risk-scope-bar" aria-label="Risk analysis scope">
      <div className="live-risk-search"><Search size={14} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={company.data?.name ? `Focused: ${company.data.name}` : "Choose a company…"} aria-label="Choose company for risk analysis" />{query.trim().length >= 2 && <div className="network-focus-results">{search.isPending ? <div className="network-focus-empty">Searching…</div> : search.isError ? <div className="network-focus-empty">Search unavailable. Current scope unchanged.</div> : companyResults.length ? companyResults.map((result) => <button key={result.entity.id} type="button" onClick={() => selectCompany(result)}><strong>{result.entity.name}</strong><span>{result.entity.id}</span></button>) : <div className="network-focus-empty">No matching Company.</div>}</div>}</div>
      <div className="risk-scope-item"><span>Max hops</span>{([1, 2, 3] as const).map((value) => <button type="button" className={`live-risk-hop${maxHops === value ? " is-active" : ""}`} key={value} onClick={() => setMaxHops(value)}>{value}</button>)}</div>
      <div className="risk-scope-item is-disabled"><span>System-wide ranking</span><strong>BACKEND CONTRACT GAP</strong></div>
    </section>

    {!companyId ? <RiskState text="Choose a Company to inspect current risk, contributing Events, hop exposure, and reconstructed history. No demo ranking is substituted." /> : company.isError ? <RiskState text={`Requested Company unavailable: ${errorText(company.error)} No unrelated Company is substituted.`} error /> : <>
      <section className="risk-summary-grid">
        <Panel eyebrow="Current company risk" title={company.data?.name ?? companyId}>{risk.isPending ? <RiskState text="Loading current risk…" compact /> : risk.isError ? <RiskState text={`Risk unavailable: ${errorText(risk.error)}`} error compact /> : risk.data ? <div className="live-risk-primary"><strong>{risk.data.currentRisk.toFixed(3)}</strong><RiskBadge level={risk.data.riskLevel} /><span>{risk.data.contributingEventCount} contributing events · max {risk.data.maxHops} hops</span><div className="phase2-inline-actions"><Button variant="secondary" onClick={() => navigate(`/companies/${encodeURIComponent(companyId)}`)}>Open Profile</Button><Button variant="primary" onClick={() => navigate(`/network?mode=impact&focusType=Company&focusId=${encodeURIComponent(companyId)}&maxHops=${maxHops}`)}>Open Impact</Button></div></div> : null}</Panel>
        <Panel eyebrow="Hop exposure" title="Returned Contributions">{exposure.isPending ? <RiskState text="Loading exposure…" compact /> : exposure.isError ? <RiskState text={`Exposure unavailable: ${errorText(exposure.error)}`} error compact /> : <div className="hop-exposure-list">{([0, 1, 2, 3] as const).filter((hopValue) => hopValue <= maxHops).map((hopValue) => { const count = (exposure.data ?? []).filter((item) => item.hop === hopValue).length; return <div className="hop-exposure-row" key={hopValue}><div className="hop-exposure-icon"><Activity size={14} /></div><div className="risk-ranking-company"><strong>Hop {hopValue}</strong><span>{hopValue === 0 ? "Direct event exposure" : "Supply-path exposure"}</span></div><strong>{count}</strong></div>; })}</div>}</Panel>
        <Panel eyebrow="History semantics" title="Reconstructed Risk History">{history.isPending ? <RiskState text="Loading history…" compact /> : history.isError ? <RiskState text={`History unavailable: ${errorText(history.error)}`} error compact /> : <div className="live-history-summary"><strong>{history.data?.count ?? 0}</strong><span>event-derived points</span><p>Each point is reconstructed from ordered event contributions. The UI does not imply persisted wall-clock snapshots.</p></div>}</Panel>
      </section>

      <Panel variant="workspace" eyebrow="Contributing events" title="Risk Drivers" description="Each contribution keeps its canonical Event ID and backend-returned risk factors.">
        {exposure.isPending ? <RiskState text="Loading risk drivers…" /> : exposure.isError ? <RiskState text={`Risk drivers unavailable: ${errorText(exposure.error)}`} error /> : !(exposure.data?.length) ? <RiskState text="No exposure contributions returned for the selected Company." /> : <div className="event-contribution-list">{exposure.data.map((item) => <button type="button" className="live-risk-driver" key={item.exposureId} onClick={() => setInspectorRef({ kind: "event", id: item.eventId, entityType: "Event", name: item.eventType ?? item.eventId, context: { relatedCompanyId: companyId } })}><div><strong>{item.eventType ?? "EVENT"}</strong><span>{item.eventId} · Hop {item.hop} · {item.source ?? "Source not available"}</span></div><div><span>Propagated Risk</span><strong>{item.propagatedRisk.toFixed(3)}</strong></div></button>)}</div>}
      </Panel>

      <section className="live-risk-lens-bar" aria-label="Analytical lens"><span className="metadata-text">ANALYTICAL LENS</span>{(["NETWORK", "GEOGRAPHY", "HEATMAP"] as Lens[]).map((item) => <button type="button" key={item} className={lens === item ? "is-active" : ""} onClick={() => setLens(item)}>{item === "NETWORK" ? <BarChart3 size={14} /> : item === "GEOGRAPHY" ? <Map size={14} /> : <Activity size={14} />}{item}</button>)}</section>
      {lens === "NETWORK" ? <Panel variant="workspace" eyebrow="Company scope" title="Network Lens"><div className="phase2-network-empty"><div><strong>Open Impact for propagation analysis</strong><span>The dedicated Network workspace owns the live Structure/Impact visualization so Risk Analysis does not create a second graph system.</span></div><Button variant="primary" onClick={() => navigate(`/network?mode=impact&focusType=Company&focusId=${encodeURIComponent(companyId)}&maxHops=${maxHops}`)}>Open Impact</Button></div></Panel> : <Panel variant="workspace" eyebrow={lens} title={`${lens[0]}${lens.slice(1).toLowerCase()} lens unavailable`}><RiskState text={lens === "GEOGRAPHY" ? "Verified coordinate coverage is not guaranteed by the current public contracts. No map coordinates are invented." : "The backend does not expose a system-wide heatmap aggregate contract. No client-side N+1 risk ranking is fabricated."} /></Panel>}

      <Panel eyebrow="Historical risk" title="Event-Derived Timeline">{history.data?.points.length ? <div className="live-risk-history-list">{history.data.points.slice(-12).map((point) => <button type="button" key={`${point.eventId}:${point.timestamp}`} onClick={() => navigate(`/events/${encodeURIComponent(point.eventId)}`)}><span>{formatTimestamp(point.timestamp)}</span><strong>{point.currentRisk.toFixed(3)}</strong><RiskBadge level={point.riskLevel} /><small>{point.eventId}</small></button>)}</div> : <span className="metadata-text">No historical points returned.</span>}</Panel>
    </>}
  </div>;
}

function RiskState({ text, error = false, compact = false }: { text: string; error?: boolean; compact?: boolean }) { return <div className={`live-risk-state${compact ? " is-compact" : ""}`} role={error ? "alert" : "status"}><ShieldAlert size={16} aria-hidden="true" /><span>{text}</span></div>; }
function hop(value: string | null): 1 | 2 | 3 { return value === "1" ? 1 : value === "2" ? 2 : 3; }
function errorText(error: unknown): string { return error instanceof Error ? error.message : "Unknown backend error."; }
function formatTimestamp(value: string): string { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString(); }
