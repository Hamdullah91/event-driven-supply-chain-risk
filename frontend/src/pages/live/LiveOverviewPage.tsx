import { Activity, ArrowRight, Database, RadioTower, ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { MetricCard } from "../../components/ui/MetricCard";
import { Panel } from "../../components/ui/Panel";
import { useDetailedHealth, useEventImpact, useEvents } from "../../query/hooks";
import { useUiStore } from "../../state/uiStore";

import "../OverviewPage.css";
import "./LiveOverviewPage.css";

export function LiveOverviewPage() {
  const navigate = useNavigate();
  const events = useEvents(5, 0);
  const health = useDetailedHealth();
  const setInspectorRef = useUiStore((state) => state.setInspectorRef);
  const latestEvent = events.data?.events[0];
  const spotlight = useEventImpact(latestEvent?.eventId, 3);

  return <div className="overview-page">
    <header className="overview-header"><div><div className="overview-title-row"><span className="metadata-text">SUPPLY CHAIN RISK OVERVIEW</span><span className="demo-badge">LIVE DATA</span></div><h1 className="page-title">Current disruption and exposure intelligence</h1><p className="body-text overview-subtitle">Overview uses only verified public contracts. Unsupported system-wide active-risk aggregates remain visibly unavailable instead of being reconstructed with browser-side N+1 requests.</p></div><div className="overview-header-context"><RadioTower size={14} aria-hidden="true" /><span>Recent Event feed + detailed backend health</span></div></header>

    <section className="overview-metrics">
      <MetricCard label="Detected Event Records" value={events.isPending ? "—" : events.data?.count ?? "—"} detail="Total records from the Events read contract; not labeled active Events." status={<RadioTower size={14} />} />
      <MetricCard label="Backend Health" value={health.isPending ? "Checking" : health.isError ? "Unavailable" : health.data?.status ?? "Unknown"} detail="Detailed health is backend-reported; individual services are not inferred." status={<Activity size={14} />} />
      <MetricCard label="Recent Feed Loaded" value={events.data?.events.length ?? "—"} detail="Newest returned Event records shown below." status={<Database size={14} />} />
      <MetricCard label="System-wide Current Risk" value="N/A" detail="BACKEND CONTRACT GAP — no authoritative aggregate ranking/heatmap endpoint." status={<ShieldAlert size={14} />} />
    </section>

    <section className="overview-primary-grid">
      <Panel eyebrow="What happened?" title="Recent Events" description="Newest Event records from the live backend.">
        {events.isPending ? <OverviewState text="Loading recent Events…" /> : events.isError ? <OverviewState text={`Recent Events unavailable: ${errorText(events.error)} No demo feed is substituted.`} error /> : events.data?.events.length ? <div className="event-list">{events.data.events.map((event) => <button type="button" className="live-overview-event" key={event.eventId} onClick={() => { setInspectorRef({ kind: "event", id: event.eventId, entityType: "Event", name: String(event.eventType) }); navigate(`/events/${encodeURIComponent(event.eventId)}`); }}><span className="event-marker" aria-hidden="true" /><span className="event-main"><span className="event-title-row"><strong className="event-type">{event.eventType}</strong><span className={`event-severity event-severity--${event.severity}`}>{event.severity.toUpperCase()}</span></span><span className="event-entity">{event.description ?? "Description not available"}</span><span className="event-metadata"><span>{formatTimestamp(event.timestamp)}</span><span>{event.source}</span><span>{event.confidence === undefined ? "Confidence —" : `${(event.confidence * 100).toFixed(0)}% confidence`}</span></span></span></button>)}</div> : <OverviewState text="No Event records returned." />}
        <Button variant="ghost" icon={<ArrowRight size={14} />} onClick={() => navigate("/events")}>Open Events</Button>
      </Panel>

      <Panel eyebrow="Who is exposed?" title="Current Risk Landscape" description="System-wide ranking is intentionally not fabricated.">
        <div className="live-overview-gap"><ShieldAlert size={20} aria-hidden="true" /><strong>Aggregate risk endpoint required</strong><span>The current public API can calculate risk for a selected Company, but it does not expose one system-wide ranking contract. LIVE Overview therefore does not issue a risk request for every Company.</span><Button variant="secondary" onClick={() => navigate("/risk-analysis")}>Open Scoped Risk Analysis</Button></div>
      </Panel>
    </section>

    <Panel variant="workspace" eyebrow="How is it propagating?" title="Recent Event Propagation Spotlight" description={latestEvent ? `Latest returned Event: ${latestEvent.eventType} · ${latestEvent.eventId}` : "No recent Event available for propagation context."}>
      {!latestEvent ? <OverviewState text="No Event is available for an Impact spotlight." /> : spotlight.isPending ? <OverviewState text="Loading latest Event Impact…" /> : spotlight.isError ? <OverviewState text={`Impact unavailable: ${errorText(spotlight.error)} No demo path is substituted.`} error /> : spotlight.data ? <div className="live-propagation-spotlight"><div className="live-propagation-origin"><span>EVENT ORIGIN</span><strong>{latestEvent.eventType}</strong><small>{latestEvent.eventId}</small></div><ArrowRight size={22} aria-hidden="true" /><div className="live-propagation-targets">{spotlight.data.targets.length ? spotlight.data.targets.slice(0, 8).map((target) => <button type="button" key={`${target.company.id}:${target.pathId}`} onClick={() => navigate(`/network?mode=impact&focusType=Event&focusId=${encodeURIComponent(latestEvent.eventId)}&eventId=${encodeURIComponent(latestEvent.eventId)}&maxHops=3`)}><strong>{target.company.name}</strong><span>Hop {target.hop}</span><span>Propagated Risk {target.propagatedRisk?.toFixed(3) ?? "—"}</span></button>) : <span className="metadata-text">No affected targets returned.</span>}</div><Button variant="primary" onClick={() => navigate(`/network?mode=impact&focusType=Event&focusId=${encodeURIComponent(latestEvent.eventId)}&eventId=${encodeURIComponent(latestEvent.eventId)}&maxHops=3`)}>Open Impact</Button></div> : null}
    </Panel>

    <section className="overview-secondary-grid"><Panel eyebrow="Domain context" title="Industry / Domain Context"><div className="live-overview-gap"><span>Industry-wide aggregate risk is not a current public contract.</span><span>Semiconductors · EV Batteries · Aerospace & Electronics remain the project scope, but no risk value is invented for a domain.</span></div></Panel><Panel eyebrow="System context" title="Verified Services">{health.isPending ? <OverviewState text="Loading service health…" /> : health.isError ? <OverviewState text={`Detailed health unavailable: ${errorText(health.error)}`} error /> : <div className="live-service-list">{Object.entries(health.data?.services ?? {}).map(([name, service]) => <div key={name}><span>{name}</span><strong>{service.status}</strong><small>{service.detail ?? "No detail"}</small></div>)}</div>}</Panel></section>
  </div>;
}

function OverviewState({ text, error = false }: { text: string; error?: boolean }) { return <div className="live-overview-state" role={error ? "alert" : "status"}><ShieldAlert size={16} aria-hidden="true" /><span>{text}</span></div>; }
function errorText(error: unknown): string { return error instanceof Error ? error.message : "Unknown backend error."; }
function formatTimestamp(value: string): string { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString(); }
