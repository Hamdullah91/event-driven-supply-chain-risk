import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Building2, FileText, Network, Search, ShieldAlert } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../api/error";
import { Button } from "../../components/ui/Button";
import { Panel } from "../../components/ui/Panel";
import { RiskBadge } from "../../components/ui/RiskBadge";
import type { Company, ExposureContribution } from "../../domain/types";
import { useCompanies, useCompany, useCompanyExposure, useCompanyNetwork, useCompanyRisk } from "../../query/hooks";
import { useUiStore } from "../../state/uiStore";

import "../CompaniesPage.css";

const PAGE_SIZE = 25;

export function LiveCompaniesPage() {
  const { companyId } = useParams<{ companyId: string }>();
  return companyId ? <LiveCompanyProfile companyId={companyId} /> : <LiveCompanyDirectory />;
}

function LiveCompanyDirectory() {
  const navigate = useNavigate();
  const setInspectorRef = useUiStore((state) => state.setInspectorRef);
  const inspectorId = useUiStore((state) => state.inspectorRef?.id);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(query.trim());
      setOffset(0);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  const companies = useCompanies({ limit: PAGE_SIZE, offset, search: debouncedQuery || undefined });
  const visible = companies.data?.companies ?? [];
  const count = companies.data?.count ?? 0;
  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  return (
    <div className="companies-page">
      <header className="companies-header">
        <div><div className="companies-title-context"><span className="metadata-text">KNOWLEDGE GRAPH ENTITIES</span><span className="demo-badge">LIVE DATA</span></div><h1 className="page-title">Companies</h1><p className="body-text companies-subtitle">Single click inspects a company. Open Profile is an explicit action. Directory rows do not trigger per-company risk requests.</p></div>
        <div className="companies-count"><Building2 size={15} aria-hidden="true" /><div><strong>{companies.isPending ? "—" : count}</strong><span>matching companies</span></div></div>
      </header>

      <section className="companies-toolbar" aria-label="Company controls">
        <div className="companies-search"><Search size={15} aria-hidden="true" /><input className="phase2-search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search companies" aria-label="Search live companies" /></div>
        <div className="companies-filter"><span>Risk</span><strong>Not a list contract</strong></div>
        <div className="companies-filter"><span>Active Events</span><strong>Not a list contract</strong></div>
      </section>

      <Panel eyebrow="Company directory" title="Known Companies" description="Search and pagination are backend-owned in LIVE mode.">
        {companies.isPending ? <LiveState text="Loading companies…" />
          : companies.isError ? <LiveState text={`Companies unavailable: ${errorMessage(companies.error)} No demo rows are substituted.`} error />
          : visible.length === 0 ? <LiveState text="No live companies match the current search." />
          : <div className="companies-table-wrapper"><table className="companies-table"><thead><tr><th>Company</th><th>Legal Name</th><th>Entity Type</th><th>Industry ID</th><th>Action</th></tr></thead><tbody>{visible.map((company) => (
            <tr key={company.companyId} className={`phase2-selectable${inspectorId === company.companyId ? " is-selected" : ""}`} tabIndex={0} onClick={() => setInspectorRef({ kind: "entity", id: company.companyId, entityType: "Company", name: company.name })} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") setInspectorRef({ kind: "entity", id: company.companyId, entityType: "Company", name: company.name }); }}>
              <td><div className="company-table-identity"><span className="company-table-icon"><Building2 size={15} aria-hidden="true" /></span><div><strong>{company.name}</strong><span>{company.companyId}</span></div></div></td>
              <td>{company.legalName ?? "Not available"}</td><td>{company.entityType ?? "Company"}</td><td>{company.industryId ?? "Not available"}</td>
              <td><Button variant="ghost" icon={<ArrowRight size={14} />} onClick={(event) => { event.stopPropagation(); navigate(`/companies/${encodeURIComponent(company.companyId)}`); }}>Open Profile</Button></td>
            </tr>
          ))}</tbody></table></div>}

        <div className="companies-table-note"><span>Page {page} of {totalPages}</span><div className="phase2-inline-actions"><Button variant="ghost" disabled={offset === 0 || companies.isPending} onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}>Previous</Button><Button variant="ghost" disabled={offset + PAGE_SIZE >= count || companies.isPending} onClick={() => setOffset((value) => value + PAGE_SIZE)}>Next</Button></div></div>
      </Panel>
    </div>
  );
}

function LiveCompanyProfile({ companyId }: { companyId: string }) {
  const navigate = useNavigate();
  const setInspectorRef = useUiStore((state) => state.setInspectorRef);
  const [selectedExposureId, setSelectedExposureId] = useState<string | null>(null);
  const company = useCompany(companyId);
  const risk = useCompanyRisk(companyId, 3);
  const exposure = useCompanyExposure(companyId, 3);
  const network = useCompanyNetwork(companyId, 1);

  const nodeNames = useMemo(() => Object.fromEntries((network.data?.nodes ?? []).map((node) => [node.id, node.label])), [network.data?.nodes]);

  if (company.isPending) return <ProfileState title="Loading Company Profile" detail={`Resolving canonical company ID ${companyId}…`} />;
  if (company.isError) {
    const notFound = company.error instanceof ApiError && company.error.kind === "NOT_FOUND";
    return <ProfileState title={notFound ? "Company profile not found" : "Company profile unavailable"} detail={`${errorMessage(company.error)} No other company is substituted for ${companyId}.`} onBack={() => navigate("/companies")} />;
  }

  const value = company.data;
  const exposures = exposure.data ?? [];
  const selectedExposure = exposures.find((item) => item.exposureId === selectedExposureId);

  const inspectExposure = (item: ExposureContribution) => {
    setSelectedExposureId(item.exposureId);
    setInspectorRef({ kind: "event", id: item.eventId, entityType: "Event", name: item.eventType ?? item.eventId, context: { relatedCompanyId: companyId } });
  };

  return (
    <div className="company-profile">
      <button type="button" className="company-profile-back" onClick={() => navigate(-1)}><ArrowLeft size={14} aria-hidden="true" /><span>Back</span></button>
      <header className="company-profile-header">
        <div className="company-profile-heading"><div className="companies-title-context"><span className="metadata-text">COMPANY INTELLIGENCE PROFILE</span><span className="demo-badge">LIVE DATA</span></div><h1 className="page-title">{value.legalName ?? value.name}</h1><div className="company-profile-meta"><span>{value.entityType ?? "Company"}</span><span aria-hidden="true">•</span><span>{value.industryId ?? "Industry not available"}</span><span aria-hidden="true">•</span><span>{value.companyId}</span></div></div>
        <div className="company-profile-actions">{risk.data && <RiskBadge level={risk.data.riskLevel} />}<Button variant="secondary" icon={<Network size={15} />} onClick={() => navigate(`/network?mode=structure&focusType=Company&focusId=${encodeURIComponent(companyId)}&depth=1`)}>Explore Network</Button><Button variant="primary" icon={<ShieldAlert size={15} />} onClick={() => navigate(`/network?mode=impact&focusType=Company&focusId=${encodeURIComponent(companyId)}&maxHops=3`)}>Open Impact</Button></div>
      </header>

      <section className="company-profile-summary">
        <Panel eyebrow="Current risk" title="Risk Summary">{risk.isPending ? <LiveState text="Loading current risk…" /> : risk.isError ? <LiveState text={`Risk unavailable: ${errorMessage(risk.error)}`} error /> : risk.data ? <div className="company-risk-summary"><strong>{risk.data.currentRisk.toFixed(3)}</strong><RiskBadge level={risk.data.riskLevel} /><span>{risk.data.contributingEventCount} contributing events · max {risk.data.maxHops} hops</span></div> : null}</Panel>
        <Panel eyebrow="Event context" title="Contributing Events"><div className="company-event-summary"><strong>{risk.data?.contributingEventCount ?? "—"}</strong><span>Detailed contributions are loaded from the dedicated exposure contract below.</span></div></Panel>
      </section>

      <Panel variant="workspace" eyebrow="Why is this company exposed?" title="Risk Paths & Contributing Events" description="Backend-returned risk factors are displayed; the frontend does not recalculate production risk.">
        {exposure.isPending ? <LiveState text="Loading exposure contributions…" />
          : exposure.isError ? <LiveState text={`Exposure unavailable: ${errorMessage(exposure.error)} No demo path is substituted.`} error />
          : exposures.length === 0 ? <LiveState text="No returned exposure contributions for this company." />
          : <div className="company-exposure-list">{exposures.map((item) => <article key={item.exposureId} className={`company-exposure phase2-selectable${selectedExposureId === item.exposureId ? " is-selected" : ""}`} tabIndex={0} role="button" onClick={() => inspectExposure(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inspectExposure(item); }}>
            <div className="company-exposure-header"><div><span className="company-exposure-type">{item.eventType ?? "EVENT"}</span><strong>{item.path.map((node) => node.name).join(" → ") || `${item.sourceEntity.name} → ${item.targetCompany.name}`}</strong></div><span className="company-exposure-hop">HOP {item.hop}</span></div>
            <div className="company-exposure-meta"><span>Severity {item.severity.toUpperCase()}</span><span aria-hidden="true">•</span><span>Confidence {item.confidence === undefined ? "Not available" : `${(item.confidence * 100).toFixed(0)}%`}</span><span aria-hidden="true">•</span><span>{item.source ?? "Source not available"}</span></div>
            <div className="company-risk-trace"><Trace label="Initial Risk" value={item.initialRisk} /><span>×</span><Trace label="Combined Path Dependency" value={item.combinedPathDependency} /><span>×</span><Trace label="Distance Decay" value={item.distanceDecay} /><span>=</span><Trace label="Propagated Risk" value={item.propagatedRisk} emphasized /></div>
            <div className="phase2-inline-actions"><Button variant="ghost" onClick={(event) => { event.stopPropagation(); inspectExposure(item); }}>Highlight / Inspect</Button><Button variant="secondary" onClick={(event) => { event.stopPropagation(); navigate(`/events/${encodeURIComponent(item.eventId)}`); }}>Open Event</Button><Button variant="secondary" onClick={(event) => { event.stopPropagation(); navigate(`/network?mode=impact&focusType=Event&focusId=${encodeURIComponent(item.eventId)}&eventId=${encodeURIComponent(item.eventId)}&maxHops=3`); }}>Open Impact</Button></div>
          </article>)}</div>}
        {selectedExposure && <p className="phase2-interaction-note">Selected exposure record: {selectedExposure.exposureId}. Canonical Event ID remains {selectedExposure.eventId}.</p>}
      </Panel>

      <Panel variant="workspace" eyebrow="Supply network" title="Focused Company Network" description="One-hop structural context; edge direction is preserved exactly as returned.">
        {network.isPending ? <LiveState text="Loading structural network…" /> : network.isError ? <LiveState text={`Network unavailable: ${errorMessage(network.error)}`} error /> : network.data ? <div className="company-network-placeholder"><Network size={22} aria-hidden="true" /><div><strong>{network.data.nodes.length} nodes · {network.data.edges.length} relationships</strong><span>{network.data.edges.slice(0, 4).map((edge) => `${nodeNames[edge.sourceId] ?? edge.sourceId} —${edge.type}→ ${nodeNames[edge.targetId] ?? edge.targetId}`).join(" · ") || "No structural relationships returned."}</span></div><Button variant="secondary" onClick={() => navigate(`/network?mode=structure&focusType=Company&focusId=${encodeURIComponent(companyId)}&depth=1`)}>Explore Full Network</Button></div> : null}
      </Panel>

      <section className="company-entity-grid">
        <NamesOnlyPanel title="Facilities" values={value.facilities} />
        <NamesOnlyPanel title="Products" values={value.products} />
        <NamesOnlyPanel title="Materials" values={value.materials} />
        <NamesOnlyPanel title="Technologies" values={value.technologies} />
      </section>

      <Panel eyebrow="Evidence & provenance" title="Available Evidence" description="The company contract exposes seed provenance but not a standalone evidence object."><div className="company-evidence-state"><FileText size={18} aria-hidden="true" /><div><strong>{value.seedSource ? "PARTIAL" : "UNAVAILABLE"}</strong><span>Source: {value.seedSource ?? "Not available"}. Missing provenance is not manufactured.</span></div></div></Panel>
    </div>
  );
}

function NamesOnlyPanel({ title, values }: { title: string; values: string[] }) {
  return <Panel eyebrow="Names-only backend contract" title={title}><div className="company-entity-list">{values.length ? values.map((value) => <span className="company-entity-value" key={value}>{value}</span>) : <span className="company-missing-data">Not available</span>}</div><p className="phase2-interaction-note">No profile action is offered because this contract does not provide canonical IDs for these names.</p></Panel>;
}

function Trace({ label, value, emphasized = false }: { label: string; value: number; emphasized?: boolean }) {
  return <div className={`trace-value${emphasized ? " is-emphasized" : ""}`}><span>{label}</span><strong>{value.toFixed(3)}</strong></div>;
}

function LiveState({ text, error = false }: { text: string; error?: boolean }) {
  return <div className="company-network-placeholder" role={error ? "alert" : "status"}><ShieldAlert size={20} aria-hidden="true" /><div><strong>{text}</strong></div></div>;
}

function ProfileState({ title, detail, onBack }: { title: string; detail: string; onBack?: () => void }) {
  return <div className="company-profile">{onBack && <button type="button" className="company-profile-back" onClick={onBack}><ArrowLeft size={14} aria-hidden="true" /><span>Back to Companies</span></button>}<Panel variant="workspace" eyebrow="Company profile" title={title} description={detail}><LiveState text={detail} error={title.toLowerCase().includes("unavailable") || title.toLowerCase().includes("not found")} /></Panel></div>;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unknown backend error.";
}
