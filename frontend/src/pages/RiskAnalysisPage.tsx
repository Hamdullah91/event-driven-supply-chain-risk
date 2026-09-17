import { useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Building2,
  Globe2,
  Layers3,
  MapPin,
  Network,
  ShieldAlert,
} from "lucide-react";

import { Panel } from "../components/ui/Panel";
import { RiskBadge } from "../components/ui/RiskBadge";

import {
  domainExposureDemo,
  eventContributionDemo,
  hopExposureDemo,
  riskRankingDemo,
} from "../data/riskAnalysisDemo";

import "./RiskAnalysisPage.css";

type RiskView = "network" | "geography" | "heatmap";

export function RiskAnalysisPage() {
  const [view, setView] = useState<RiskView>("network");

  return (
    <div className="risk-analysis-page">
      <header className="risk-analysis-header">
        <div>
          <div className="risk-analysis-title-context">
            <span className="metadata-text">SYSTEM RISK</span>

            <span className="demo-badge">
              DEVELOPMENT DATA
            </span>
          </div>

          <h1 className="page-title">
            Risk Analysis
          </h1>

          <p className="body-text risk-analysis-subtitle">
            Examine where risk is concentrated, how far exposure
            propagates, and which events contribute to company risk.
          </p>
        </div>

        <div className="risk-analysis-history-state">
          <BarChart3 size={14} aria-hidden="true" />

          <span>
            Historical risk series not available
          </span>
        </div>
      </header>

      <section
        className="risk-scope-bar"
        aria-label="Risk analysis scope"
      >
        <div className="risk-scope-item">
          <span>Scope</span>
          <strong>Current System</strong>
        </div>

        <div className="risk-scope-item">
          <span>Industry</span>
          <strong>All Domains</strong>
        </div>

        <div className="risk-scope-item is-disabled">
          <span>Time</span>
          <strong>Not available</strong>
        </div>
      </section>

      <section className="risk-summary-grid">
        <Panel
          eyebrow="Concentration"
          title="Risk Ranking"
        >
          <div className="risk-ranking-list">
            {riskRankingDemo.map((company, index) => (
              <article
                className="risk-ranking-row"
                key={company.company}
              >
                <span className="risk-rank-number">
                  {index + 1}
                </span>

                <div className="risk-ranking-company">
                  <strong>{company.company}</strong>

                  <span>
                    {company.contributingEvents} contributing event
                    {company.contributingEvents === 1 ? "" : "s"}
                  </span>
                </div>

                <div className="risk-ranking-value">
                  <strong>{company.score}</strong>
                  <RiskBadge level={company.level} />
                </div>
              </article>
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="Domain concentration"
          title="Domain Exposure"
        >
          <div className="domain-exposure-list">
            {domainExposureDemo.map((domain) => (
              <article
                className="domain-exposure-row"
                key={domain.domain}
              >
                <div>
                  <Building2 size={15} aria-hidden="true" />

                  <span>{domain.domain}</span>
                </div>

                <div>
                  <strong>
                    {domain.exposedCompanies}
                  </strong>

                  <span>companies</span>
                </div>

                <RiskBadge level={domain.highestRisk} />
              </article>
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="Propagation depth"
          title="Hop Exposure"
        >
          <div className="hop-exposure-list">
            {hopExposureDemo.map((hop) => (
              <article
                className="hop-exposure-row"
                key={hop.hop}
              >
                <div className="hop-exposure-icon">
                  <Layers3 size={15} aria-hidden="true" />
                </div>

                <div className="hop-exposure-copy">
                  <strong>{hop.hop}</strong>
                  <span>{hop.description}</span>
                </div>

                <strong className="hop-exposure-count">
                  {hop.companies}
                </strong>
              </article>
            ))}
          </div>
        </Panel>
      </section>

      <Panel
        variant="workspace"
        eyebrow="Analytical view"
        title="Risk Concentration"
        description="Switch between system-level analytical lenses."
      >
        <div className="risk-view-tabs">
          <button
            type="button"
            className={`risk-view-tab${
              view === "network" ? " is-active" : ""
            }`}
            onClick={() => setView("network")}
          >
            <Network size={14} aria-hidden="true" />
            <span>Network</span>
          </button>

          <button
            type="button"
            className={`risk-view-tab${
              view === "geography" ? " is-active" : ""
            }`}
            onClick={() => setView("geography")}
          >
            <Globe2 size={14} aria-hidden="true" />
            <span>Geography</span>
          </button>

          <button
            type="button"
            className={`risk-view-tab${
              view === "heatmap" ? " is-active" : ""
            }`}
            onClick={() => setView("heatmap")}
          >
            <BarChart3 size={14} aria-hidden="true" />
            <span>Heatmap</span>
          </button>
        </div>

        <div className="risk-view-content">
          {view === "network" && <RiskNetworkView />}
          {view === "geography" && <GeographyView />}
          {view === "heatmap" && <HeatmapView />}
        </div>
      </Panel>

      <section className="risk-context-grid">
        <Panel
          eyebrow="Why?"
          title="Event Contributions"
        >
          <div className="event-contribution-list">
            {eventContributionDemo.map((event) => (
              <article
                className="event-contribution-row"
                key={`${event.eventType}-${event.company}`}
              >
                <div>
                  <AlertTriangle
                    size={14}
                    aria-hidden="true"
                  />

                  <div>
                    <strong>{event.eventType}</strong>
                    <span>{event.company}</span>
                  </div>
                </div>

                <div className="event-contribution-value">
                  <span>Hop {event.hop}</span>
                  <strong>{event.propagatedRisk}</strong>
                </div>
              </article>
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="Interpretation"
          title="Risk Context"
        >
          <div className="risk-context-body">
            <ShieldAlert size={20} aria-hidden="true" />

            <div>
              <strong>
                Current-state analysis
              </strong>

              <p>
                This workspace represents current exposure only.
                Historical trend interpretation remains unavailable until
                a backend risk-history contract exists.
              </p>
            </div>
          </div>
        </Panel>
      </section>
    </div>
  );
}

function RiskNetworkView() {
  return (
    <div className="risk-network-view">
      <div className="risk-network-center">
        <ShieldAlert size={21} aria-hidden="true" />
        <strong>System Risk</strong>
        <span>Current exposure</span>
      </div>

      <div className="risk-network-company risk-network-company--critical">
        <strong>NVIDIA</strong>
        <span>0.75</span>
        <RiskBadge level="CRITICAL" />
      </div>

      <div className="risk-network-company risk-network-company--high">
        <strong>TSMC</strong>
        <span>0.61</span>
        <RiskBadge level="HIGH" />
      </div>

      <div className="risk-network-company risk-network-company--medium">
        <strong>Samsung</strong>
        <span>0.42</span>
        <RiskBadge level="MEDIUM" />
      </div>

      <div className="risk-network-demo-label">
        DEMO NETWORK CONCENTRATION
      </div>
    </div>
  );
}

function GeographyView() {
  return (
    <div className="geography-unavailable">
      <div className="geography-icon">
        <MapPin size={24} aria-hidden="true" />
      </div>

      <div>
        <span className="metadata-text">
          GEOGRAPHY LENS
        </span>

        <h3>Precise geographic plotting unavailable</h3>

        <p>
          Facility, country, location, and event concepts exist in the
          graph, but verified latitude and longitude coordinates are not
          currently guaranteed by the frontend contract.
        </p>

        <div className="geography-integrity-note">
          No coordinates have been invented for this view.
        </div>
      </div>
    </div>
  );
}

function HeatmapView() {
  const cells = [
    { label: "Semiconductors", level: "critical" },
    { label: "Electronics", level: "high" },
    { label: "EV / Battery", level: "medium" },
    { label: "Aerospace", level: "low" },
  ];

  return (
    <div className="risk-heatmap">
      <div className="risk-heatmap-grid">
        {cells.map((cell) => (
          <div
            key={cell.label}
            className={`risk-heatmap-cell risk-heatmap-cell--${cell.level}`}
          >
            <span>{cell.label}</span>
            <strong>
              {cell.level.toUpperCase()}
            </strong>
          </div>
        ))}
      </div>

      <p>
        Development-only categorical heatmap. Production values must
        originate from backend risk results.
      </p>
    </div>
  );
}