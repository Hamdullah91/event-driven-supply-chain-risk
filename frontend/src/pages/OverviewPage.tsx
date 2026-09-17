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
import {
  RiskBadge,
  type RiskLevel,
} from "../components/ui/RiskBadge";

import "./OverviewPage.css";

type DemoEvent = {
  id: string;
  type: string;
  severity: "HIGH" | "MEDIUM";
  source: string;
  timestamp: string;
  entity: string;
};

type DemoRiskCompany = {
  company: string;
  score: string;
  level: RiskLevel;
  events: number;
};

const demoEvents: DemoEvent[] = [
  {
    id: "demo-event-001",
    type: "FACILITY_OUTAGE",
    severity: "HIGH",
    source: "Demo source",
    timestamp: "12 min ago",
    entity: "TSMC",
  },
  {
    id: "demo-event-002",
    type: "SUPPLY_DISRUPTION",
    severity: "MEDIUM",
    source: "Demo source",
    timestamp: "38 min ago",
    entity: "Samsung Electronics",
  },
  {
    id: "demo-event-003",
    type: "REGULATION_CHANGE",
    severity: "MEDIUM",
    source: "Demo source",
    timestamp: "1 hr ago",
    entity: "Semiconductor domain",
  },
];

const demoRiskCompanies: DemoRiskCompany[] = [
  {
    company: "NVIDIA",
    score: "0.75",
    level: "CRITICAL",
    events: 2,
  },
  {
    company: "TSMC",
    score: "0.61",
    level: "HIGH",
    events: 2,
  },
  {
    company: "Samsung Electronics",
    score: "0.42",
    level: "MEDIUM",
    events: 1,
  },
];

const severityClass = {
  HIGH: "event-severity event-severity--high",
  MEDIUM: "event-severity event-severity--medium",
};

export function OverviewPage() {
  return (
    <div className="overview-page">
      <header className="overview-header">
        <div>
          <div className="overview-title-row">
            <span className="metadata-text">COMMAND CENTER</span>

            <span className="demo-badge">
              DEVELOPMENT DATA
            </span>
          </div>

          <h1 className="page-title">Overview</h1>

          <p className="body-text overview-subtitle">
            Monitor detected disruptions, exposure, propagation, and current
            supply-chain risk context.
          </p>
        </div>

        <div className="overview-header-context">
          <Clock3 size={14} aria-hidden="true" />
          <span>Live overview API not yet available</span>
        </div>
      </header>

      <section
        className="overview-metrics"
        aria-label="Overview metrics"
      >
        <MetricCard
          label="Detected Events"
          value="—"
          detail="System-wide event read API required"
          status={<RadioTower size={16} aria-hidden="true" />}
        />

        <MetricCard
          label="Companies at Risk"
          value="—"
          detail="Aggregate overview endpoint required"
          status={<Building2 size={16} aria-hidden="true" />}
        />

        <MetricCard
          label="Active Propagations"
          value="—"
          detail="Aggregate propagation state not exposed"
          status={<Network size={16} aria-hidden="true" />}
        />

        <MetricCard
          label="Highest Current Risk"
          value="—"
          detail="Company context required"
          status={<Activity size={16} aria-hidden="true" />}
        />
      </section>

      <section className="overview-primary-grid">
        <Panel
          className="overview-events-panel"
          eyebrow="What happened?"
          title="Recent Disruption Context"
          description="Development-only examples until system-wide event read APIs are available."
          action={
            <Button variant="ghost">
              Events unavailable
            </Button>
          }
        >
          <div className="event-list">
            {demoEvents.map((event) => (
              <article className="event-row" key={event.id}>
                <div className="event-marker" aria-hidden="true" />

                <div className="event-main">
                  <div className="event-title-row">
                    <span className="event-type">
                      {event.type}
                    </span>

                    <span
                      className={severityClass[event.severity]}
                    >
                      {event.severity}
                    </span>
                  </div>

                  <span className="event-entity">
                    {event.entity}
                  </span>

                  <div className="event-metadata">
                    <span>{event.source}</span>
                    <span aria-hidden="true">•</span>
                    <span>{event.timestamp}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </Panel>

        <Panel
          className="overview-risk-panel"
          eyebrow="How serious?"
          title="Current Risk Landscape"
          description="Development-only examples of the intended company risk presentation."
        >
          <div className="risk-company-list">
            {demoRiskCompanies.map((company) => (
              <article
                className="risk-company-row"
                key={company.company}
              >
                <div className="risk-company-main">
                  <span className="risk-company-name">
                    {company.company}
                  </span>

                  <span className="risk-company-events">
                    {company.events} contributing event
                    {company.events === 1 ? "" : "s"}
                  </span>
                </div>

                <div className="risk-company-value">
                  <span className="risk-score">
                    {company.score}
                  </span>

                  <RiskBadge level={company.level} />
                </div>
              </article>
            ))}
          </div>
        </Panel>
      </section>

      <Panel
        className="propagation-spotlight"
        variant="workspace"
        eyebrow="Who is affected?"
        title="Active Propagation Spotlight"
        description="Signature multi-hop risk story preview. Values below are explicitly development-only."
        action={
          <Button
            variant="primary"
            icon={<Network size={15} />}
          >
            Explore Network
          </Button>
        }
      >
        <div className="propagation-layout">
          <div className="propagation-story">
            <div className="propagation-origin">
              <span className="propagation-label">
                DEMO ORIGIN
              </span>

              <strong>TSMC disruption</strong>

              <span>Initial risk 0.75</span>
            </div>

            <div className="propagation-path">
              <div className="propagation-node propagation-node--origin">
                <span>Origin</span>
                <strong>TSMC</strong>
              </div>

              <div className="propagation-connector">
                <span>SUPPLIES</span>
                <ArrowRight size={18} aria-hidden="true" />
              </div>

              <div className="propagation-node">
                <span>Hop 1</span>
                <strong>NVIDIA</strong>
              </div>

              <div className="propagation-connector">
                <span>SUPPLIES</span>
                <ArrowRight size={18} aria-hidden="true" />
              </div>

              <div className="propagation-node">
                <span>Hop 2</span>
                <strong>Demo Company</strong>
              </div>
            </div>
          </div>

          <div className="propagation-math">
            <span className="metadata-text">
              PROPAGATION TRACE
            </span>

            <div className="trace-equation">
              <span>
                Initial Risk
                <strong>0.75</strong>
              </span>

              <span className="trace-operator">×</span>

              <span>
                Combined Path Dependency
                <strong>1.00</strong>
              </span>

              <span className="trace-operator">×</span>

              <span>
                Distance Decay
                <strong>0.70</strong>
              </span>

              <span className="trace-operator">=</span>

              <span>
                Propagated Risk
                <strong>0.525</strong>
              </span>
            </div>

            <p>
              This preview intentionally shows combined path dependency,
              not invented per-edge dependency multipliers.
            </p>
          </div>
        </div>
      </Panel>

      <section className="overview-context-grid">
        <Panel
          eyebrow="Domain context"
          title="Industry Exposure"
          description="Aggregate domain exposure requires additional backend support."
        >
          <div className="unavailable-state">
            <Building2 size={18} aria-hidden="true" />

            <div>
              <strong>Not available</strong>
              <span>
                No aggregate industry-risk contract is currently exposed.
              </span>
            </div>
          </div>
        </Panel>

        <Panel
          eyebrow="Recent context"
          title="Risk Activity"
          description="Historical risk series is not currently available."
        >
          <div className="unavailable-state">
            <Activity size={18} aria-hidden="true" />

            <div>
              <strong>Not available</strong>
              <span>
                Historical risk controls will remain hidden until supported.
              </span>
            </div>
          </div>
        </Panel>
      </section>
    </div>
  );
}