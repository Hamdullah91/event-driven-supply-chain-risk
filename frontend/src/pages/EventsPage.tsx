import { useState } from "react";
import {
  ArrowRight,
  Building2,
  Clock3,
  FileText,
  MapPin,
  Search,
  ShieldCheck,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import {
  eventsDemo,
  type EventSeverity,
} from "../data/eventsDemo";

import "./EventsPage.css";

const severityClasses: Record<EventSeverity, string> = {
  MEDIUM: "events-severity events-severity--medium",
  HIGH: "events-severity events-severity--high",
  CRITICAL: "events-severity events-severity--critical",
};

export function EventsPage() {
  const [selectedEventId, setSelectedEventId] = useState(
    eventsDemo[0].id,
  );

  const selectedEvent =
    eventsDemo.find((event) => event.id === selectedEventId) ??
    eventsDemo[0];

  return (
    <div className="events-page">
      <header className="events-header">
        <div>
          <div className="events-heading-context">
            <span className="metadata-text">EVENT INTELLIGENCE</span>
            <span className="demo-badge">DEVELOPMENT FIXTURE</span>
          </div>

          <h1 className="page-title">Events</h1>

          <p className="body-text events-subtitle">
            Review detected disruption context, classification metadata,
            affected entities, and available evidence.
          </p>
        </div>

        <div className="events-api-state">
          <Clock3 size={14} aria-hidden="true" />
          <span>Event APIs available · frontend adapter pending</span>
        </div>
      </header>

      <div className="events-toolbar">
        <div className="events-search">
          <Search size={15} aria-hidden="true" />

          <input
            type="text"
            placeholder="Search development events"
            aria-label="Search development events"
            disabled
          />

          <span>Adapter pending</span>
        </div>

        <div className="events-filter-group">
          <button type="button" className="events-filter is-active">
            All
          </button>

          <button type="button" className="events-filter" disabled>
            Severity
          </button>

          <button type="button" className="events-filter" disabled>
            Type
          </button>

          <button type="button" className="events-filter" disabled>
            Time
          </button>
        </div>
      </div>

      <div className="events-master-detail">
        <Panel
          className="events-list-panel"
          eyebrow="Detected context"
          title="Disruption Events"
          description="Development fixtures. GET /api/v1/events and event detail endpoints are available; live frontend adapter work is deferred."
        >
          <div className="events-list">
            {eventsDemo.map((event) => {
              const isSelected = event.id === selectedEvent.id;

              return (
                <button
                  type="button"
                  key={event.id}
                  className={`events-list-item${
                    isSelected ? " is-selected" : ""
                  }`}
                  aria-pressed={isSelected}
                  onClick={() => setSelectedEventId(event.id)}
                >
                  <span
                    className="events-selection-accent"
                    aria-hidden="true"
                  />

                  <div className="events-list-main">
                    <div className="events-list-top">
                      <span className="events-type">
                        {event.type}
                      </span>

                      <span className={severityClasses[event.severity]}>
                        {event.severity}
                      </span>
                    </div>

                    <strong>{event.title}</strong>

                    <div className="events-list-meta">
                      <span>{event.timestamp}</span>
                      <span aria-hidden="true">•</span>
                      <span>
                        Confidence {(event.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <ArrowRight
                    className="events-list-arrow"
                    size={15}
                    aria-hidden="true"
                  />
                </button>
              );
            })}
          </div>
        </Panel>

        <section
          className="event-detail"
          aria-label="Selected event detail"
        >
          <div className="event-detail-header">
            <div>
              <span className="metadata-text">
                SELECTED DEVELOPMENT EVENT
              </span>

              <h2>{selectedEvent.title}</h2>
            </div>

            <span className={severityClasses[selectedEvent.severity]}>
              {selectedEvent.severity}
            </span>
          </div>

          <div className="event-detail-identity">
            <div>
              <span>Event type</span>
              <strong>{selectedEvent.type}</strong>
            </div>

            <div>
              <span>Classifier confidence</span>
              <strong>
                {(selectedEvent.confidence * 100).toFixed(0)}%
              </strong>
            </div>

            <div>
              <span>Timestamp</span>
              <strong>{selectedEvent.timestamp}</strong>
            </div>

            <div>
              <span>Source</span>
              <strong>{selectedEvent.source}</strong>
            </div>
          </div>

          <section className="event-detail-section">
            <span className="event-detail-label">DESCRIPTION</span>

            <p>{selectedEvent.description}</p>
          </section>

          <section className="event-detail-section">
            <div className="event-section-heading">
              <div>
                <span className="event-detail-label">
                  AFFECTED ENTITIES
                </span>

                <h3>Known event context</h3>
              </div>

              <Building2 size={17} aria-hidden="true" />
            </div>

            <div className="affected-entity-list">
              {selectedEvent.affectedEntities.map((entity) => (
                <div className="affected-entity" key={entity}>
                  <Building2 size={15} aria-hidden="true" />
                  <span>{entity}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="event-detail-section">
            <div className="event-section-heading">
              <div>
                <span className="event-detail-label">
                  LOCATION CONTEXT
                </span>

                <h3>Geography</h3>
              </div>

              <MapPin size={17} aria-hidden="true" />
            </div>

            <div className="event-unavailable">
              <span>{selectedEvent.location}</span>
              <p>
                Backend Location entities expose verified coordinates. This
                development event fixture does not include a plotted location.
              </p>
            </div>
          </section>

          <section className="event-detail-section">
            <div className="event-section-heading">
              <div>
                <span className="event-detail-label">
                  EVIDENCE
                </span>

                <h3>Available provenance context</h3>
              </div>

              <FileText size={17} aria-hidden="true" />
            </div>

            <div className="event-evidence">
              <div>
                <ShieldCheck size={16} aria-hidden="true" />

                <div>
                  <strong>{selectedEvent.evidence}</strong>
                  <span>
                    Production rendering must use only provenance and
                    evidence fields returned by the selected event contract.
                  </span>
                </div>
              </div>

              <Button variant="secondary" disabled>
                View Evidence
              </Button>
            </div>
          </section>

          <div className="event-detail-actions">
            <Button variant="primary" disabled>
              Open Impact
            </Button>

            <Button variant="secondary" disabled>
              Explore Network
            </Button>

            <span>
              Event Blast Radius API is available; action wiring remains
              deferred to frontend interaction/integration work.
            </span>
          </div>
        </section>
      </div>
    </div>
  );
}
