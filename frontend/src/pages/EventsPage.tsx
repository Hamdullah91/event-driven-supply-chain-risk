import { useMemo, useState } from "react";
import { ArrowRight, Building2, Clock3, FileText, MapPin, Search, ShieldCheck } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import { companiesDemo } from "../data/companiesDemo";
import { eventsDemo, type DemoEvent, type EventSeverity } from "../data/eventsDemo";
import type { InspectorContext } from "../data/inspectorDemo";

import "./EventsPage.css";

const severityClasses: Record<EventSeverity, string> = {
  MEDIUM: "events-severity events-severity--medium",
  HIGH: "events-severity events-severity--high",
  CRITICAL: "events-severity events-severity--critical",
};

type EventsPageProps = {
  selectedEventId: string;
  onSelectEvent: (id: string) => void;
  onInspect: (context: InspectorContext) => void;
  onOpenImpact: (focus: { id: string; name: string; type: "Company" | "Event"; eventId?: string }) => void;
  onOpenCompanyProfile: (companyId: string) => void;
};

function eventContext(event: DemoEvent): InspectorContext {
  return {
    id: event.id,
    type: "Event",
    name: event.type,
    subtitle: event.title,
    fields: [
      { label: "Severity", value: event.severity },
      { label: "Classifier confidence", value: `${(event.confidence * 100).toFixed(0)}%` },
      { label: "Timestamp", value: event.timestamp },
      { label: "Source", value: event.source },
    ],
    evidence: {
      availability: "PARTIAL",
      source: event.source,
      confidence: `${(event.confidence * 100).toFixed(0)}%`,
      provenance: "Development fixture",
      excerpt: "Not available",
    },
  };
}

export function EventsPage({ selectedEventId, onSelectEvent, onInspect, onOpenImpact, onOpenCompanyProfile }: EventsPageProps) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState<"ALL" | EventSeverity>("ALL");
  const [showEvidence, setShowEvidence] = useState(false);

  const filteredEvents = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return eventsDemo.filter((event) => {
      const matchesSeverity = severity === "ALL" || event.severity === severity;
      const matchesQuery = !normalized || `${event.type} ${event.title} ${event.affectedEntities.join(" ")}`.toLowerCase().includes(normalized);
      return matchesSeverity && matchesQuery;
    });
  }, [query, severity]);

  const selectedEvent = eventsDemo.find((event) => event.id === selectedEventId) ?? filteredEvents[0] ?? eventsDemo[0];

  const selectEvent = (event: DemoEvent) => {
    onSelectEvent(event.id);
    onInspect(eventContext(event));
    setShowEvidence(false);
  };

  const affectedCompany = companiesDemo.find((company) => selectedEvent.affectedEntities.includes(company.name));

  return (
    <div className="events-page">
      <header className="events-header">
        <div>
          <div className="events-heading-context"><span className="metadata-text">EVENT INTELLIGENCE</span><span className="demo-badge">DEVELOPMENT FIXTURE</span></div>
          <h1 className="page-title">Events</h1>
          <p className="body-text events-subtitle">Review detected disruption context, classification metadata, affected entities, and available evidence.</p>
        </div>
        <div className="events-api-state"><Clock3 size={14} aria-hidden="true" /><span>Master-detail selection stays on this screen</span></div>
      </header>

      <div className="events-toolbar">
        <div className="events-search">
          <Search size={15} aria-hidden="true" />
          <input type="search" placeholder="Search development events" aria-label="Search development events" value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <div className="events-filter-group">
          <label className="phase2-interaction-note" htmlFor="event-severity-filter">Severity</label>
          <select id="event-severity-filter" className="phase2-filter-select" value={severity} onChange={(event) => setSeverity(event.target.value as "ALL" | EventSeverity)}>
            <option value="ALL">All</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="CRITICAL">CRITICAL</option>
          </select>
          {(query || severity !== "ALL") && <Button variant="ghost" onClick={() => { setQuery(""); setSeverity("ALL"); }}>Clear Filters</Button>}
        </div>
      </div>

      <div className="events-master-detail">
        <Panel className="events-list-panel" eyebrow="Detected context" title="Disruption Events" description="Finite development fixture supports safe client-side search/severity filtering.">
          <div className="events-list">
            {filteredEvents.length > 0 ? filteredEvents.map((event) => {
              const isSelected = event.id === selectedEvent.id;
              return (
                <button type="button" key={event.id} className={`events-list-item${isSelected ? " is-selected" : ""}`} aria-pressed={isSelected} onClick={() => selectEvent(event)}>
                  <span className="events-selection-accent" aria-hidden="true" />
                  <div className="events-list-main">
                    <div className="events-list-top"><span className="events-type">{event.type}</span><span className={severityClasses[event.severity]}>{event.severity}</span></div>
                    <strong>{event.title}</strong>
                    <div className="events-list-meta"><span>{event.timestamp}</span><span aria-hidden="true">•</span><span>Confidence {(event.confidence * 100).toFixed(0)}%</span></div>
                  </div>
                  <ArrowRight className="events-list-arrow" size={15} aria-hidden="true" />
                </button>
              );
            }) : (
              <div className="event-unavailable"><strong>No events match these filters.</strong><Button variant="ghost" onClick={() => { setQuery(""); setSeverity("ALL"); }}>Clear Filters</Button></div>
            )}
          </div>
        </Panel>

        <section className="event-detail" aria-label="Selected event detail">
          <div className="event-detail-header">
            <div><span className="metadata-text">SELECTED DEVELOPMENT EVENT</span><h2>{selectedEvent.title}</h2></div>
            <span className={severityClasses[selectedEvent.severity]}>{selectedEvent.severity}</span>
          </div>

          <div className="event-detail-identity">
            <div><span>Event type</span><strong>{selectedEvent.type}</strong></div>
            <div><span>Classifier confidence</span><strong>{(selectedEvent.confidence * 100).toFixed(0)}%</strong></div>
            <div><span>Timestamp</span><strong>{selectedEvent.timestamp}</strong></div>
            <div><span>Source</span><strong>{selectedEvent.source}</strong></div>
          </div>
          <p className="phase2-interaction-note">Severity describes operational impact; classifier confidence describes model certainty. They are not risk equivalents.</p>

          <section className="event-detail-section"><span className="event-detail-label">DESCRIPTION</span><p>{selectedEvent.description}</p></section>

          <section className="event-detail-section">
            <div className="event-section-heading"><div><span className="event-detail-label">AFFECTED ENTITIES</span><h3>Known event context</h3></div><Building2 size={17} aria-hidden="true" /></div>
            <div className="affected-entity-list">
              {selectedEvent.affectedEntities.map((entity) => (
                <button
                  type="button"
                  className="affected-entity phase2-entity-button"
                  key={entity}
                  onClick={() => {
                    const company = companiesDemo.find((candidate) => candidate.name === entity);
                    onInspect({
                      id: company?.companyId ?? `demo-${entity.toLowerCase().replaceAll(" ", "-")}`,
                      type: company ? "Company" : "Industry",
                      name: entity,
                      subtitle: "Affected entity from development event",
                      riskLevel: company?.riskLevel,
                      riskScore: company?.riskScore,
                      fields: [{ label: "Related event", value: selectedEvent.type }],
                      evidence: { availability: "UNAVAILABLE" },
                    });
                  }}
                ><Building2 size={15} aria-hidden="true" /><span>{entity}</span></button>
              ))}
            </div>
            {affectedCompany && <div className="phase2-inline-actions"><Button variant="ghost" onClick={() => onOpenCompanyProfile(affectedCompany.companyId)}>Open Company</Button></div>}
          </section>

          <section className="event-detail-section">
            <div className="event-section-heading"><div><span className="event-detail-label">LOCATION CONTEXT</span><h3>Geography</h3></div><MapPin size={17} aria-hidden="true" /></div>
            <div className="event-unavailable"><span>{selectedEvent.location}</span><p>This fixture does not invent a plotted location.</p></div>
          </section>

          <section className="event-detail-section">
            <div className="event-section-heading"><div><span className="event-detail-label">EVIDENCE</span><h3>Available provenance context</h3></div><FileText size={17} aria-hidden="true" /></div>
            <div className="event-evidence">
              <div><ShieldCheck size={16} aria-hidden="true" /><div><strong>{selectedEvent.evidence}</strong><span>Production rendering must use returned provenance only.</span></div></div>
              <Button variant="secondary" aria-expanded={showEvidence} onClick={() => setShowEvidence((value) => !value)}>View Evidence</Button>
            </div>
            {showEvidence && <div className="phase2-evidence-detail"><strong>PARTIAL · DEVELOPMENT FIXTURE</strong><span>Source: {selectedEvent.source}</span><span>Confidence: {(selectedEvent.confidence * 100).toFixed(0)}%</span><span>Extracted context: Not available</span></div>}
          </section>

          <div className="event-detail-actions">
            <Button variant="primary" onClick={() => onOpenImpact({ id: selectedEvent.id, name: selectedEvent.type, type: "Event", eventId: selectedEvent.id })}>Open Impact</Button>
            <Button variant="secondary" onClick={() => onInspect(eventContext(selectedEvent))}>Inspect Event</Button>
            <Button variant="ghost" disabled title="No valid URL exists in the development fixture">Open Source</Button>
          </div>
        </section>
      </div>
    </div>
  );
}
