import { useEffect, useMemo, useState } from "react";
import { ExternalLink, RadioTower, Search, ShieldAlert } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../api/error";
import { Button } from "../../components/ui/Button";
import { Panel } from "../../components/ui/Panel";
import type { EventSeverity, SupplyChainEvent } from "../../domain/types";
import { useEvent, useEvents } from "../../query/hooks";
import { useUiStore } from "../../state/uiStore";

import "../EventsPage.css";

const PAGE_SIZE = 100;
const severityOptions: Array<"ALL" | Uppercase<EventSeverity>> = ["ALL", "UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export function LiveEventsPage() {
  const navigate = useNavigate();
  const { eventId } = useParams<{ eventId: string }>();
  const setInspectorRef = useUiStore((state) => state.setInspectorRef);
  const inspectorRef = useUiStore((state) => state.inspectorRef);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState<(typeof severityOptions)[number]>("ALL");
  const [eventType, setEventType] = useState("ALL");
  const page = useEvents(PAGE_SIZE, offset);
  const selected = useEvent(eventId);

  const eventTypes = useMemo(() => Array.from(new Set((page.data?.events ?? []).map((event) => event.eventType))).sort(), [page.data?.events]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return (page.data?.events ?? []).filter((event) => {
      const searchMatch = !normalized || `${event.eventType} ${event.description ?? ""} ${event.source} ${event.eventId}`.toLowerCase().includes(normalized);
      const severityMatch = severity === "ALL" || event.severity.toUpperCase() === severity;
      const typeMatch = eventType === "ALL" || event.eventType === eventType;
      return searchMatch && severityMatch && typeMatch;
    });
  }, [eventType, page.data?.events, query, severity]);

  useEffect(() => {
    if (!eventId || !page.data) return;
    const existsOnLoadedPage = page.data.events.some((event) => event.eventId === eventId);
    if (!existsOnLoadedPage) return;
    const stillVisible = filtered.some((event) => event.eventId === eventId);
    if (stillVisible) return;
    if (inspectorRef?.id === eventId) setInspectorRef(null);
    navigate("/events", { replace: true });
  }, [eventId, filtered, inspectorRef?.id, navigate, page.data, setInspectorRef]);

  const selectEvent = (event: SupplyChainEvent) => {
    setInspectorRef({ kind: "event", id: event.eventId, entityType: "Event", name: String(event.eventType) });
    navigate(`/events/${encodeURIComponent(event.eventId)}`);
  };

  const count = page.data?.count ?? 0;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  return (
    <div className="events-page">
      <header className="events-header"><div><div className="events-title-context"><span className="metadata-text">DETECTED DISRUPTIONS</span><span className="demo-badge">LIVE DATA</span></div><h1 className="page-title">Events</h1><p className="body-text events-subtitle">Select an Event for rapid master-detail inspection. Open Impact remains an explicit navigation action.</p></div><div className="events-count"><RadioTower size={15} aria-hidden="true" /><div><strong>{page.isPending ? "—" : count}</strong><span>events</span></div></div></header>

      <section className="events-toolbar" aria-label="Event controls">
        <div className="events-search"><Search size={15} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter loaded event page" aria-label="Filter loaded event page" /></div>
        <label className="events-filter">Type<select value={eventType} onChange={(event) => setEventType(event.target.value)}><option value="ALL">All loaded types</option>{eventTypes.map((type) => <option value={type} key={type}>{type}</option>)}</select></label>
        <label className="events-filter">Severity<select value={severity} onChange={(event) => setSeverity(event.target.value as (typeof severityOptions)[number])}>{severityOptions.map((option) => <option value={option} key={option}>{option}</option>)}</select></label>
        <span className="phase2-interaction-note">Filters are client-side within the current finite backend page; no server filter is fabricated.</span>
      </section>

      <section className="events-master-detail">
        <Panel eyebrow="Event feed" title="Detected Events" description={`Loaded page ${currentPage} of ${totalPages}.`}>
          {page.isPending ? <EventState text="Loading events…" /> : page.isError ? <EventState text={`Events unavailable: ${message(page.error)} No demo feed is substituted.`} error /> : filtered.length === 0 ? <EventState text="No events match the current loaded-page filters." /> : <div className="event-list">{filtered.map((event) => <button type="button" key={event.eventId} className={`event-row${event.eventId === eventId ? " is-selected" : ""}`} onClick={() => selectEvent(event)}><div className="event-row-main"><strong>{event.eventType}</strong><span>{event.description ?? "No description returned."}</span></div><div className="event-row-meta"><span>{event.severity.toUpperCase()}</span><span>{event.confidence === undefined ? "Confidence —" : `Confidence ${(event.confidence * 100).toFixed(0)}%`}</span><span>{formatTimestamp(event.timestamp)}</span></div></button>)}</div>}
          <div className="phase2-inline-actions"><Button variant="ghost" disabled={offset === 0 || page.isPending} onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}>Previous</Button><Button variant="ghost" disabled={offset + PAGE_SIZE >= count || page.isPending} onClick={() => setOffset((value) => value + PAGE_SIZE)}>Next</Button></div>
        </Panel>

        <Panel eyebrow="Event detail" title={eventId ? "Selected Event" : "Select an Event"}>
          {!eventId ? <EventState text="Select an Event to inspect live classification, evidence, and impact context." />
            : selected.isPending ? <EventState text={`Loading ${eventId}…`} />
            : selected.isError ? <EventState text={`${selected.error instanceof ApiError && selected.error.kind === "NOT_FOUND" ? "Event not found" : "Event unavailable"}: ${message(selected.error)} No unrelated Event is substituted.`} error />
            : selected.data ? <EventDetail event={selected.data} onOpenImpact={() => navigate(`/network?mode=impact&focusType=Event&focusId=${encodeURIComponent(selected.data!.eventId)}&eventId=${encodeURIComponent(selected.data!.eventId)}&maxHops=3`)} onOpenCompany={(companyId) => navigate(`/companies/${encodeURIComponent(companyId)}`)} /> : null}
        </Panel>
      </section>
    </div>
  );
}

function EventDetail({ event, onOpenImpact, onOpenCompany }: { event: SupplyChainEvent; onOpenImpact: () => void; onOpenCompany: (companyId: string) => void }) {
  const company = event.affectedEntities.find((entity) => entity.type === "Company");
  return <div className="event-detail-content">
    <section className="event-detail-section"><span className="metadata-text">WHAT HAPPENED?</span><h2>{event.eventType}</h2><p>{event.description ?? "Description not available from the backend."}</p></section>
    <section className="event-detail-grid"><div><span>Severity</span><strong>{event.severity.toUpperCase()}</strong></div><div><span>Classifier Confidence</span><strong>{event.confidence === undefined ? "Not available" : `${(event.confidence * 100).toFixed(1)}%`}</strong></div><div><span>Timestamp</span><strong>{formatTimestamp(event.timestamp)}</strong></div><div><span>Source</span><strong>{event.source}</strong></div></section>
    <section className="event-detail-section"><span className="metadata-text">AFFECTED ENTITIES</span>{event.affectedEntities.length ? <div className="event-entity-list">{event.affectedEntities.map((entity) => <button type="button" key={`${entity.type}:${entity.id}`} onClick={() => entity.type === "Company" && onOpenCompany(entity.id)} disabled={entity.type !== "Company"}><strong>{entity.name}</strong><span>{entity.type}</span></button>)}</div> : <p>The current Event contract did not return a typed affected-entity collection. No entity type is inferred from a bare ID.</p>}</section>
    <section className="event-detail-section"><span className="metadata-text">EVIDENCE</span><div className={`evidence-availability evidence-availability--${event.evidence.availability.toLowerCase()}`}>{event.evidence.availability}</div><p>Source: {event.evidence.source ?? "Not available"}</p>{event.sourceUrl ? <a href={event.sourceUrl} target="_blank" rel="noreferrer" className="phase2-external-link">Open Source <ExternalLink size={13} aria-hidden="true" /></a> : <span className="inspector-unavailable">Source URL not available</span>}</section>
    <div className="event-detail-actions"><Button variant="primary" onClick={onOpenImpact}>Open Impact</Button>{company && <Button variant="secondary" onClick={() => onOpenCompany(company.id)}>Open Company</Button>}</div>
  </div>;
}

function EventState({ text, error = false }: { text: string; error?: boolean }) {
  return <div className="event-detail-empty" role={error ? "alert" : "status"}><ShieldAlert size={18} aria-hidden="true" /><p>{text}</p></div>;
}

function formatTimestamp(value: string): string {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Unknown backend error.";
}
