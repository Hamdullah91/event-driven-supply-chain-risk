import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Boxes,
  Building2,
  Cpu,
  Factory,
  FileText,
  Layers3,
  Network,
  Package,
  Search,
  ShieldAlert,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import { RiskBadge } from "../components/ui/RiskBadge";

import {
  companiesDemo,
  demoNvidiaExposures,
  type DemoCompany,
} from "../data/companiesDemo";

import "./CompaniesPage.css";

export function CompaniesPage() {
  const [selectedCompany, setSelectedCompany] =
    useState<DemoCompany | null>(null);

  if (selectedCompany) {
    return (
      <CompanyProfile
        company={selectedCompany}
        onBack={() => setSelectedCompany(null)}
      />
    );
  }

  return (
    <CompaniesList onOpenCompany={setSelectedCompany} />
  );
}

type CompaniesListProps = {
  onOpenCompany: (company: DemoCompany) => void;
};

function CompaniesList({
  onOpenCompany,
}: CompaniesListProps) {
  return (
    <div className="companies-page">
      <header className="companies-header">
        <div>
          <div className="companies-title-context">
            <span className="metadata-text">
              KNOWLEDGE GRAPH ENTITIES
            </span>

            <span className="demo-badge">
              DEVELOPMENT DATA
            </span>
          </div>

          <h1 className="page-title">
            Companies
          </h1>

          <p className="body-text companies-subtitle">
            Review company entities known to the supply-chain knowledge
            graph and open their intelligence profiles.
          </p>
        </div>

        <div className="companies-count">
          <Building2 size={15} aria-hidden="true" />

          <div>
            <strong>{companiesDemo.length}</strong>
            <span>development companies</span>
          </div>
        </div>
      </header>

      <section
        className="companies-toolbar"
        aria-label="Company controls"
      >
        <div className="companies-search">
          <Search size={15} aria-hidden="true" />

          <span>Search companies</span>

          <small>Adapter pending</small>
        </div>

        <div className="companies-filter">
          <span>Industry</span>
          <strong>All</strong>
        </div>

        <div className="companies-filter">
          <span>Risk</span>
          <strong>Reserved</strong>
        </div>

        <div className="companies-filter">
          <span>Active Events</span>
          <strong>Reserved</strong>
        </div>
      </section>

      <Panel
        eyebrow="Company directory"
        title="Known Companies"
        description="Initial table architecture follows the current company API contract. Global search and company filtering APIs are available; interaction wiring is deferred."
      >
        <div className="companies-table-wrapper">
          <table className="companies-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Legal Name</th>
                <th>Entity Type</th>
                <th>Industry ID</th>
                <th aria-label="Open profile" />
              </tr>
            </thead>

            <tbody>
              {companiesDemo.map((company) => (
                <tr key={company.companyId}>
                  <td>
                    <div className="company-table-identity">
                      <span className="company-table-icon">
                        <Building2
                          size={15}
                          aria-hidden="true"
                        />
                      </span>

                      <div>
                        <strong>{company.name}</strong>
                        <span>{company.companyId}</span>
                      </div>
                    </div>
                  </td>

                  <td>{company.legalName}</td>
                  <td>{company.entityType}</td>
                  <td>{company.industryId}</td>

                  <td>
                    <button
                      type="button"
                      className="company-open-button"
                      aria-label={`Open ${company.name} profile`}
                      onClick={() => onOpenCompany(company)}
                    >
                      <ArrowRight
                        size={15}
                        aria-hidden="true"
                      />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="companies-table-note">
          <span>
            Risk and active-event columns are intentionally not populated
            in this fixture directory because the current company-list
            response does not directly return those values.
          </span>
        </div>
      </Panel>
    </div>
  );
}

type CompanyProfileProps = {
  company: DemoCompany;
  onBack: () => void;
};

function CompanyProfile({
  company,
  onBack,
}: CompanyProfileProps) {
  const isNvidia = company.companyId === "demo-nvidia";

  const exposures = isNvidia
    ? demoNvidiaExposures
    : demoNvidiaExposures.slice(0, 1);

  return (
    <div className="company-profile">
      <button
        type="button"
        className="company-profile-back"
        onClick={onBack}
      >
        <ArrowLeft size={14} aria-hidden="true" />
        <span>Companies</span>
      </button>

      <header className="company-profile-header">
        <div className="company-profile-heading">
          <div className="companies-title-context">
            <span className="metadata-text">
              COMPANY INTELLIGENCE PROFILE
            </span>

            <span className="demo-badge">
              DEVELOPMENT DATA
            </span>
          </div>

          <h1 className="page-title">
            {company.legalName}
          </h1>

          <div className="company-profile-meta">
            <span>{company.entityType}</span>
            <span aria-hidden="true">•</span>
            <span>{company.industryId}</span>
            <span aria-hidden="true">•</span>
            <span>{company.companyId}</span>
          </div>
        </div>

        <div className="company-profile-actions">
          <RiskBadge level={company.riskLevel} />

          <Button
            variant="secondary"
            icon={<Network size={15} />}
            disabled
          >
            Explore Network
          </Button>

          <Button
            variant="primary"
            icon={<ShieldAlert size={15} />}
            disabled
          >
            View Impact
          </Button>
        </div>
      </header>

      <section className="company-profile-summary">
        <Panel
          eyebrow="Current risk"
          title="Risk Summary"
        >
          <div className="company-risk-summary">
            <strong>{company.riskScore}</strong>

            <RiskBadge level={company.riskLevel} />

            <span>
              {company.contributingEventCount} contributing events
            </span>
          </div>
        </Panel>

        <Panel
          eyebrow="Event context"
          title="Contributing Events"
        >
          <div className="company-event-summary">
            <strong>
              {company.contributingEventCount}
            </strong>

            <span>
              Company exposure can be sourced from the existing risk
              exposure endpoint.
            </span>
          </div>
        </Panel>
      </section>

      <Panel
        variant="workspace"
        eyebrow="Why is this company exposed?"
        title="Risk Paths & Contributing Events"
        description="Development examples using the exact risk-trace structure supported by the existing exposure contract."
      >
        <div className="company-exposure-list">
          {exposures.map((exposure) => (
            <article
              className="company-exposure"
              key={exposure.id}
            >
              <div className="company-exposure-header">
                <div>
                  <span className="company-exposure-type">
                    {exposure.eventType}
                  </span>

                  <strong>
                    {exposure.path.join(" → ")}
                  </strong>
                </div>

                <span className="company-exposure-hop">
                  HOP {exposure.hopDistance}
                </span>
              </div>

              <div className="company-exposure-meta">
                <span>
                  Severity {exposure.severity}
                </span>

                <span aria-hidden="true">•</span>

                <span>
                  Confidence {exposure.confidence}
                </span>

                <span aria-hidden="true">•</span>

                <span>{exposure.source}</span>
              </div>

              <div className="company-risk-trace">
                <TraceValue
                  label="Initial Risk"
                  value={exposure.initialRisk}
                />

                <span>×</span>

                <TraceValue
                  label="Combined Path Dependency"
                  value={exposure.pathDependency}
                />

                <span>×</span>

                <TraceValue
                  label="Distance Decay"
                  value={exposure.distanceDecay}
                />

                <span>=</span>

                <TraceValue
                  label="Propagated Risk"
                  value={exposure.propagatedRisk}
                  emphasized
                />
              </div>
            </article>
          ))}
        </div>
      </Panel>

      <Panel
        variant="workspace"
        eyebrow="Supply network"
        title="Focused Company Network"
        description="The production version will use the existing 1–3 hop company network endpoint."
      >
        <div className="company-network-placeholder">
          <Network size={22} aria-hidden="true" />

          <div>
            <strong>
              Interactive focused graph
            </strong>

            <span>
              Final graph renderer will use Neo4j-backed nodes and
              relationships through FastAPI. The graph library is not frozen
              in Phase 1.
            </span>
          </div>
        </div>
      </Panel>

      <section className="company-entity-grid">
        <CompanyEntityPanel
          title="Facilities"
          icon={<Factory size={16} />}
          values={company.facilities}
        />

        <CompanyEntityPanel
          title="Products"
          icon={<Package size={16} />}
          values={company.products}
        />

        <CompanyEntityPanel
          title="Materials"
          icon={<Layers3 size={16} />}
          values={company.materials}
        />

        <CompanyEntityPanel
          title="Technologies"
          icon={<Cpu size={16} />}
          values={company.technologies}
        />
      </section>

      <Panel
        eyebrow="Evidence & provenance"
        title="Available Evidence"
        description="Evidence remains first-class and must only display fields actually returned by the backend."
      >
        <div className="company-evidence-state">
          <FileText size={18} aria-hidden="true" />

          <div>
            <strong>
              Typed provenance supported
            </strong>

            <span>
              Source, confidence, provenance, evidence status, and
              relationship metadata render only when returned by the selected
              backend contract.
            </span>
          </div>

          <Button variant="secondary" disabled>
            View Evidence
          </Button>
        </div>
      </Panel>
    </div>
  );
}

type TraceValueProps = {
  label: string;
  value: string;
  emphasized?: boolean;
};

function TraceValue({
  label,
  value,
  emphasized = false,
}: TraceValueProps) {
  return (
    <div
      className={`trace-value${
        emphasized ? " is-emphasized" : ""
      }`}
    >
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

type CompanyEntityPanelProps = {
  title: string;
  icon: React.ReactNode;
  values: string[];
};

function CompanyEntityPanel({
  title,
  icon,
  values,
}: CompanyEntityPanelProps) {
  return (
    <Panel
      eyebrow="Known entities"
      title={title}
      action={icon}
    >
      <div className="company-entity-list">
        {values.length > 0 ? (
          values.map((value) => (
            <div
              className="company-entity-value"
              key={value}
            >
              <Boxes size={13} aria-hidden="true" />
              <span>{value}</span>
            </div>
          ))
        ) : (
          <span className="company-missing-data">
            Not available
          </span>
        )}
      </div>
    </Panel>
  );
}
