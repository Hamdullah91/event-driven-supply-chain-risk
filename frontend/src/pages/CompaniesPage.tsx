import { useMemo, useState, type ReactNode } from "react";
import { ArrowLeft, ArrowRight, Boxes, Building2, Cpu, Factory, FileText, Layers3, Network, Package, Search, ShieldAlert } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import { RiskBadge } from "../components/ui/RiskBadge";
import {
  companiesDemo,
  getCompanyExposureFixture,
  getCompanyProfile,
  type DemoCompany,
  type DemoCompanyExposure,
} from "../data/companiesDemo";
import type { InspectorContext, InspectorEntityType } from "../data/inspectorDemo";

import "./CompaniesPage.css";

type CompaniesPageProps = {
  profileCompanyId: string | null;
  selectedInspectorId?: string;
  onOpenProfile: (companyId: string) => void;
  onBackFromProfile: () => void;
  onInspect: (context: InspectorContext) => void;
  onExploreNetwork: (company: DemoCompany) => void;
  onOpenImpact: (company: DemoCompany) => void;
};

function companyContext(company: DemoCompany): InspectorContext {
  return {
    id: company.companyId,
    type: "Company",
    name: company.name,
    subtitle: company.legalName,
    riskLevel: company.riskLevel,
    riskScore: company.riskScore,
    fields: [
      { label: "Entity type", value: company.entityType },
      { label: "Industry", value: company.industryId },
      { label: "Contributing events", value: String(company.contributingEventCount) },
    ],
    evidence: { availability: "PARTIAL", source: company.seedSource, provenance: "Development fixture" },
  };
}

export function CompaniesPage(props: CompaniesPageProps) {
  if (props.profileCompanyId) {
    const selectedCompany = getCompanyProfile(props.profileCompanyId);
    if (selectedCompany) return <CompanyProfile company={selectedCompany} {...props} />;
    return <CompanyProfileUnavailable requestedId={props.profileCompanyId} onBack={props.onBackFromProfile} />;
  }

  return <CompaniesList {...props} />;
}

function CompanyProfileUnavailable({ requestedId, onBack }: { requestedId: string; onBack: () => void }) {
  return (
    <div className="company-profile">
      <button type="button" className="company-profile-back" onClick={onBack}><ArrowLeft size={14} aria-hidden="true" /><span>Back</span></button>
      <Panel
        variant="workspace"
        eyebrow="Company profile"
        title="Profile unavailable for this development entity"
        description="The requested company ID does not resolve to a Company Profile fixture. The Companies directory is not shown as though profile navigation succeeded."
      >
        <div className="company-network-placeholder" role="status">
          <ShieldAlert size={22} aria-hidden="true" />
          <div><strong>No profile fixture for {requestedId}</strong><span>Return to the previous investigation or choose a supported company from the Companies directory.</span></div>
          <Button variant="secondary" onClick={onBack}>Return</Button>
        </div>
      </Panel>
    </div>
  );
}

function CompaniesList({ selectedInspectorId, onOpenProfile, onInspect }: CompaniesPageProps) {
  const [query, setQuery] = useState("");
  const [industry, setIndustry] = useState("ALL");

  const companies = useMemo(() => companiesDemo.filter((company) => {
    const matchesQuery = !query.trim() || `${company.name} ${company.legalName}`.toLowerCase().includes(query.trim().toLowerCase());
    const matchesIndustry = industry === "ALL" || company.industryId === industry;
    return matchesQuery && matchesIndustry;
  }), [industry, query]);

  return (
    <div className="companies-page">
      <header className="companies-header">
        <div><div className="companies-title-context"><span className="metadata-text">KNOWLEDGE GRAPH ENTITIES</span><span className="demo-badge">DEVELOPMENT DATA</span></div><h1 className="page-title">Companies</h1><p className="body-text companies-subtitle">Single click inspects a company. Open Profile is an explicit action.</p></div>
        <div className="companies-count"><Building2 size={15} aria-hidden="true" /><div><strong>{companies.length}</strong><span>visible development companies</span></div></div>
      </header>

      <section className="companies-toolbar" aria-label="Company controls">
        <div className="companies-search"><Search size={15} aria-hidden="true" /><input className="phase2-search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search companies" aria-label="Search development companies" /></div>
        <label className="companies-filter"><span>Industry</span><select className="phase2-filter-select" value={industry} onChange={(event) => setIndustry(event.target.value)}><option value="ALL">All</option><option value="semiconductor">Semiconductor</option><option value="electronics">Electronics</option></select></label>
        <div className="companies-filter"><span>Risk</span><strong>Adapter pending</strong></div>
        <div className="companies-filter"><span>Active Events</span><strong>Adapter pending</strong></div>
      </section>

      <Panel eyebrow="Company directory" title="Known Companies" description="Finite fixture filters are local; production filtering remains backend-owned.">
        <div className="companies-table-wrapper">
          <table className="companies-table">
            <thead><tr><th>Company</th><th>Legal Name</th><th>Entity Type</th><th>Industry ID</th><th>Action</th></tr></thead>
            <tbody>
              {companies.map((company) => (
                <tr
                  key={company.companyId}
                  className={`phase2-selectable${selectedInspectorId === company.companyId ? " is-selected" : ""}`}
                  tabIndex={0}
                  onClick={() => onInspect(companyContext(company))}
                  onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onInspect(companyContext(company)); }}
                >
                  <td><div className="company-table-identity"><span className="company-table-icon"><Building2 size={15} aria-hidden="true" /></span><div><strong>{company.name}</strong><span>{company.companyId}</span></div></div></td>
                  <td>{company.legalName}</td><td>{company.entityType}</td><td>{company.industryId}</td>
                  <td><Button variant="ghost" icon={<ArrowRight size={14} />} onClick={(event) => { event.stopPropagation(); onOpenProfile(company.companyId); }}>Open Profile</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {companies.length === 0 && <div className="companies-table-note"><span>No companies match these filters.</span><Button variant="ghost" onClick={() => { setQuery(""); setIndustry("ALL"); }}>Clear Filters</Button></div>}
      </Panel>
    </div>
  );
}

function CompanyProfile({ company, onBackFromProfile, onInspect, onExploreNetwork, onOpenImpact }: CompaniesPageProps & { company: DemoCompany }) {
  const [selectedExposureId, setSelectedExposureId] = useState<string | null>(null);
  const exposures = getCompanyExposureFixture(company.companyId);
  const selectedExposure = exposures.find((exposure) => exposure.id === selectedExposureId);

  const inspectExposure = (exposure: DemoCompanyExposure) => {
    setSelectedExposureId(exposure.id);
    onInspect({
      id: exposure.id,
      type: "Event",
      name: exposure.eventType,
      subtitle: `Contributing event · ${company.name}`,
      riskScore: exposure.propagatedRisk,
      fields: [
        { label: "Severity", value: exposure.severity },
        { label: "Classifier confidence", value: exposure.confidence },
        { label: "Hop distance", value: String(exposure.hopDistance) },
        { label: "Initial Risk", value: exposure.initialRisk },
        { label: "Path Dependency", value: exposure.pathDependency },
        { label: "Distance Decay", value: exposure.distanceDecay },
        { label: "Propagated Risk", value: exposure.propagatedRisk },
      ],
      path: exposure.path,
      evidence: { availability: "PARTIAL", source: exposure.source, confidence: exposure.confidence, provenance: "Development fixture" },
    });
  };

  return (
    <div className="company-profile">
      <button type="button" className="company-profile-back" onClick={onBackFromProfile}><ArrowLeft size={14} aria-hidden="true" /><span>Back</span></button>
      <header className="company-profile-header">
        <div className="company-profile-heading"><div className="companies-title-context"><span className="metadata-text">COMPANY INTELLIGENCE PROFILE</span><span className="demo-badge">DEVELOPMENT DATA</span></div><h1 className="page-title">{company.legalName}</h1><div className="company-profile-meta"><span>{company.entityType}</span><span aria-hidden="true">•</span><span>{company.industryId}</span><span aria-hidden="true">•</span><span>{company.companyId}</span></div></div>
        <div className="company-profile-actions"><RiskBadge level={company.riskLevel} /><Button variant="secondary" icon={<Network size={15} />} onClick={() => onExploreNetwork(company)}>Explore Network</Button><Button variant="primary" icon={<ShieldAlert size={15} />} onClick={() => onOpenImpact(company)}>Open Impact</Button></div>
      </header>

      <section className="company-profile-summary">
        <Panel eyebrow="Current risk" title="Risk Summary"><div className="company-risk-summary"><strong>{company.riskScore}</strong><RiskBadge level={company.riskLevel} /><span>{company.contributingEventCount} contributing events</span></div></Panel>
        <Panel eyebrow="Event context" title="Contributing Events"><div className="company-event-summary"><strong>{company.contributingEventCount}</strong><span>Aggregate event counts may be available even when detailed development exposure paths are not.</span></div></Panel>
      </section>

      <Panel variant="workspace" eyebrow="Why is this company exposed?" title="Risk Paths & Contributing Events" description="Select a supported contribution to reveal its backend-shaped risk trace and path.">
        {exposures.length > 0 ? (
          <div className="company-exposure-list">
            {exposures.map((exposure) => (
              <article key={exposure.id} className={`company-exposure phase2-selectable${selectedExposureId === exposure.id ? " is-selected" : ""}`} tabIndex={0} role="button" onClick={() => inspectExposure(exposure)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inspectExposure(exposure); }}>
                <div className="company-exposure-header"><div><span className="company-exposure-type">{exposure.eventType}</span><strong>{exposure.path.join(" → ")}</strong></div><span className="company-exposure-hop">HOP {exposure.hopDistance}</span></div>
                <div className="company-exposure-meta"><span>Severity {exposure.severity}</span><span aria-hidden="true">•</span><span>Confidence {exposure.confidence}</span><span aria-hidden="true">•</span><span>{exposure.source}</span></div>
                <div className="company-risk-trace"><TraceValue label="Initial Risk" value={exposure.initialRisk} /><span>×</span><TraceValue label="Combined Path Dependency" value={exposure.pathDependency} /><span>×</span><TraceValue label="Distance Decay" value={exposure.distanceDecay} /><span>=</span><TraceValue label="Propagated Risk" value={exposure.propagatedRisk} emphasized /></div>
                <div className="phase2-inline-actions"><Button variant="ghost" onClick={(event) => { event.stopPropagation(); inspectExposure(exposure); }}>Highlight Path</Button><Button variant="secondary" onClick={(event) => { event.stopPropagation(); onOpenImpact(company); }}>Open Impact</Button></div>
              </article>
            ))}
          </div>
        ) : (
          <div className="company-network-placeholder" role="status">
            <ShieldAlert size={22} aria-hidden="true" />
            <div><strong>Detailed development exposure paths are unavailable for this company.</strong><span>Aggregate risk and event counts may still be available. No other company's path is substituted.</span></div>
          </div>
        )}
        {selectedExposure && <p className="phase2-interaction-note">Selected strongest/returned path: {selectedExposure.path.join(" → ")}. No alternate path is invented.</p>}
      </Panel>

      <Panel variant="workspace" eyebrow="Supply network" title="Focused Company Network" description="Contextual only; full exploration belongs in Network.">
        <div className="company-network-placeholder"><Network size={22} aria-hidden="true" /><div><strong>Focused network context</strong><span>Use the explicit action to move into the main Structure workspace. Unsupported fixture contexts remain unavailable there.</span></div><Button variant="secondary" onClick={() => onExploreNetwork(company)}>Explore Full Network</Button></div>
      </Panel>

      <section className="company-entity-grid">
        <CompanyEntityPanel title="Facilities" entityType="Facility" icon={<Factory size={16} />} values={company.facilities} company={company} onInspect={onInspect} />
        <CompanyEntityPanel title="Products" entityType="Product" icon={<Package size={16} />} values={company.products} company={company} onInspect={onInspect} />
        <CompanyEntityPanel title="Materials" entityType="Material" icon={<Layers3 size={16} />} values={company.materials} company={company} onInspect={onInspect} />
        <CompanyEntityPanel title="Technologies" entityType="Technology" icon={<Cpu size={16} />} values={company.technologies} company={company} onInspect={onInspect} />
      </section>

      <Panel eyebrow="Evidence & provenance" title="Available Evidence" description="Evidence remains first-class and only renders returned fields.">
        <div className="company-evidence-state"><FileText size={18} aria-hidden="true" /><div><strong>PARTIAL · development fixture</strong><span>Source: {company.seedSource}. Missing extracted context remains Not available.</span></div><Button variant="secondary" onClick={() => onInspect(companyContext(company))}>View Evidence</Button></div>
      </Panel>
    </div>
  );
}

function TraceValue({ label, value, emphasized = false }: { label: string; value: string; emphasized?: boolean }) {
  return <div className={`trace-value${emphasized ? " is-emphasized" : ""}`}><span>{label}</span><strong>{value}</strong></div>;
}

type CompanyEntityPanelProps = { title: string; entityType: InspectorEntityType; icon: ReactNode; values: string[]; company: DemoCompany; onInspect: (context: InspectorContext) => void };

function CompanyEntityPanel({ title, entityType, icon, values, company, onInspect }: CompanyEntityPanelProps) {
  return (
    <Panel eyebrow="Known entities" title={title} action={icon}>
      <div className="company-entity-list">
        {values.length > 0 ? values.map((value) => (
          <button
            type="button"
            className="company-entity-value phase2-entity-button"
            key={value}
            onClick={() => onInspect({ id: `demo-${entityType.toLowerCase()}-${value.toLowerCase().replaceAll(" ", "-")}`, type: entityType, name: value, subtitle: `Related to ${company.name}`, relatedCompanyId: company.companyId, fields: [{ label: "Related company", value: company.name }], evidence: { availability: "UNAVAILABLE" } })}
          ><Boxes size={13} aria-hidden="true" /><span>{value}</span></button>
        )) : <span className="company-missing-data">Not available</span>}
      </div>
    </Panel>
  );
}
