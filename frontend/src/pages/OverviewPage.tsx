import {
  Activity,
  ArrowRight,
  Building2,
  Clock3,
  Network,
  RadioTower,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { MetricCard } from "../components/ui/MetricCard";
import { Panel } from "../components/ui/Panel";
import { RiskBadge } from "../components/ui/RiskBadge";
import { companiesDemo } from "../data/companiesDemo";
import type { InspectorContext } from "../data/inspectorDemo";
import { overviewDemoEvents, overviewDemoRiskCompanies } from "../data/overviewDemo";

import "./OverviewPage.css";

const severityClass = {
  HIGH: "event-severity event-severity--high",
  MEDIUM: "event-severity event-severity--medium",
};

type OverviewPageProps = {
  selectedInspectorId?: string;
  onInspect: (context: InspectorContext) => void;
  onOpenEvent: (eventId: string) => void;
  onOpenCompanyProfile: (companyId: string) => void;
  onOpenImpact: (focus: { id: string; name: string; type: "Company" | "Event"; eventId?: string }) => void;
};

const companyIdForName = (name: string) =>
  companiesDemo.find((company) => company.name === name)?.companyId ?? `demo-${name.toLowerCase().replaceAll(" ", "-")}`;

export function OverviewPage({
  selectedInspectorId,
  onInspect,
  onOpenEvent,
  onOpenCompanyProfile,
  onOpenImpact,
}: OverviewPageProps) {
  const inspectEvent = (event: (typeof overviewDemoEvents)[number]) => {
    onInspect({
      id: event.id,
      type: "Event",
      name: event.type,
      subtitle: "Development overview event",
      fields: [
        { label: "Severity", value: event.severity },
        { label: "Affected entity", value: event.entity },
        { label: "Source", value: event.source },
        { label: "Timestamp", value: event.timestamp },
      ],
      evidence: {
        availability: "PARTIAL",
        source: event.source,
        provenance: "Development fixture",
      },
    });
  };

  const inspectCompany = (company: (typeof overviewDemoRiskCompanies)[number]) => {
    const id = companyIdForName(company.company);
    onInspect({
      id,
      type: "Company",
      name: company.company,
      subtitle: "Development overview company",
      riskLevel: company.level,
      riskScore: company.score,
      fields: [{ label: "Contributing events", value: String(company.events) }],
      evidence: { availability: "UNAVAILABLE" },
    });
  };

  return (
    <div className="overview-page">
      <header className="overview-header">
        <div>
          <div className="overview-title-row">
            <span className="metadata-text">COMMAND CENTER</span>
            <span className="demo-badge">DEVELOPMENT DATA</span>
          </div>
          <h1 className="page-title">Overview</h1>
          <p className="body-text overview-subtitle">
            Monitor detected disruptions, exposure, propagation, and current supply-chain risk context.
          </p>
        </div>
        <div className="overview-header-context">
          <Clock3 size={14} aria-hidden="true" />
          <span>Monitoring entry point · deeper actions remain explicit</span>
        </div>
      </header>

      <section className="overview-metrics" aria-label="Overview metrics">
        <MetricCard label="Detected Events" value="—" detail="Event list API available · overview adapter pending" status={<RadioTower size={16} aria-hidden="true" />} />
        <MetricCard label="Companies at Risk" value="—" detail="Aggregate overview endpoint required" status={<Building2 size={16} aria-hidden="true" />} />
        <MetricCard label="Active Propagations" value="—" detail="Aggregate propagation state not exposed" status={<Network size={16} aria-hidden="true" />} />
        <MetricCard label="Highest Current Risk" value="—" detail="Company context required" status={<Activity size={16} aria-hidden="true" />} />
      </section>

      <section className="overview-primary-grid">
        <Panel
          className="overview-events-panel"
          eyebrow="What happened?"
          title="Recent Disruption Context"
          description="Click selects and inspects. Open Event / Open Impact are explicit."
        >
          <div className="event-list">
            {overviewDemoEvents.map((event) => (
              <article
                className={`event-row phase2-selectable${selectedInspectorId === event.id ? " is-selected" : ""}`}
                key={event.id}
                tabIndex={0}
                role="button"
                aria-label={`Inspect ${event.type}`}
                onClick={() => inspectEvent(event)}
                onKeyDown={(keyboardEvent) => {
                  if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") inspectEvent(event);
                }}
              >
                <div className="event-marker" aria-hidden="true" />
                <div className="event-main">
                  <div className="event-title-row">
                    <span className="event-type">{event.type}</span>
                    <span className={severityClass[event.severity]}>{event.severity}</span>
                  </div>
                  <span className="event-entity">{event.entity}</span>
                  <div className="event-metadata">
                    <span>{event.source}</span><span aria-hidden="true">•</span><span>{event.timestamp}</span>
                  </div>
                  <div className="phase2-inline-actions">
                    <Button variant="ghost" onClick={(clickEvent) => { clickEvent.stopPropagation(); onOpenEvent(event.id); }}>Open Event</Button>
                    <Button
                      variant="secondary"
                      onClick={(clickEvent) => {
                        clickEvent.stopPropagation();
                        onOpenImpact({ id: event.id, name: event.type, type: "Event", eventId: event.id });
                      }}
                    >Open Impact</Button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </Panel>

        <Panel className="overview-risk-panel" eyebrow="How serious?" title="Current Risk Landscape" description="Click inspects; navigation remains explicit.">
          <div className="risk-company-list">
            {overviewDemoRiskCompanies.map((company) => {
              const companyId = companyIdForName(company.company);
              return (
                <article
                  className={`risk-company-row phase2-selectable${selectedInspectorId === companyId ? " is-selected" : ""}`}
                  key={company.company}
                  tabIndex={0}
                  role="button"
                  onClick={() => inspectCompany(company)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") inspectCompany(company);
                  }}
                >
                  <div className="risk-company-main">
                    <span className="risk-company-name">{company.company}</span>
                    <span className="risk-company-events">{company.events} contributing event{company.events === 1 ? "" : "s"}</span>
                    <div className="phase2-inline-actions">
                      <Button variant="ghost" onClick={(event) => { event.stopPropagation(); onOpenCompanyProfile(companyId); }}>Open Profile</Button>
                      <Button variant="secondary" onClick={(event) => { event.stopPropagation(); onOpenImpact({ id: companyId, name: company.company, type: "Company" }); }}>Open Impact</Button>
                    </div>
                  </div>
                  <div className="risk-company-value"><span className="risk-score">{company.score}</span><RiskBadge level={company.level} /></div>
                </article>
              );
            })}
          </div>
        </Panel>
      </section>

      <Panel
        className="propagation-spotlight"
        variant="workspace"
        eyebrow="Who is affected?"
        title="Active Propagation Spotlight"
        description="Signature multi-hop risk story preview. Values below are development-only."
        action={<Button variant="primary" icon={<Network size={15} />} onClick={() => onOpenImpact({ id: "demo-event-001", name: "FACILITY_OUTAGE", type: "Event", eventId: "demo-event-001" })}>Open Impact</Button>}
      >
        <div className="propagation-layout">
          <div className="propagation-story">
            <div className="propagation-origin"><span className="propagation-label">DEMO ORIGIN</span><strong>TSMC disruption</strong><span>Initial risk 0.75</span></div>
            <div className="propagation-path">
              <button className="propagation-node propagation-node--origin phase2-node-button" type="button" onClick={() => onInspect({ id: "demo-tsmc", type: "Company", name: "TSMC", riskLevel: "HIGH", riskScore: "0.61", fields: [{ label: "Path role", value: "Origin" }], evidence: { availability: "PARTIAL", source: "Development source", provenance: "Development fixture" } })}><span>Origin</span><strong>TSMC</strong></button>
              <div className="propagation-connector"><span>SUPPLIES</span><ArrowRight size={18} aria-hidden="true" /></div>
              <button className="propagation-node phase2-node-button" type="button" onClick={() => onInspect({ id: "demo-nvidia", type: "Company", name: "NVIDIA", riskLevel: "CRITICAL", riskScore: "0.75", fields: [{ label: "Hop", value: "1" }], path: ["TSMC", "NVIDIA"], evidence: { availability: "PARTIAL", source: "Development source", provenance: "Development fixture" } })}><span>Hop 1</span><strong>NVIDIA</strong></button>
              <div className="propagation-connector"><span>SUPPLIES</span><ArrowRight size={18} aria-hidden="true" /></div>
              <button className="propagation-node phase2-node-button" type="button" onClick={() => onInspect({ id: "demo-company-a", type: "Company", name: "Demo Company A", riskLevel: "HIGH", riskScore: "0.525", fields: [{ label: "Hop", value: "2" }], path: ["TSMC", "NVIDIA", "Demo Company A"], evidence: { availability: "UNAVAILABLE" } })}><span>Hop 2</span><strong>Demo Company A</strong></button>
            </div>
          </div>

          <div className="propagation-math">
            <span className="metadata-text">PROPAGATION TRACE</span>
            <div className="trace-equation">
              <span>Initial Risk<strong>0.75</strong></span><span className="trace-operator">×</span>
              <span>Combined Path Dependency<strong>1.00</strong></span><span className="trace-operator">×</span>
              <span>Distance Decay<strong>0.70</strong></span><span className="trace-operator">=</span>
              <span>Propagated Risk<strong>0.525</strong></span>
            </div>
            <p>This preview intentionally shows combined path dependency, not invented per-edge dependency multipliers.</p>
          </div>
        </div>
      </Panel>

      <section className="overview-context-grid">
        <Panel eyebrow="Domain context" title="Industry Exposure" description="Aggregate domain exposure requires additional backend support.">
          <div className="unavailable-state"><Building2 size={18} aria-hidden="true" /><div><strong>Not available</strong><span>No aggregate industry-risk contract is currently exposed.</span></div></div>
        </Panel>
        <Panel eyebrow="Recent context" title="Risk Activity" description="Historical risk endpoint is available; chart integration belongs to later data integration.">
          <div className="unavailable-state"><Activity size={18} aria-hidden="true" /><div><strong>Frontend adapter pending</strong><span>GET /risk/&#123;company_id&#125;/history is available.</span></div></div>
        </Panel>
      </section>
    </div>
  );
}
