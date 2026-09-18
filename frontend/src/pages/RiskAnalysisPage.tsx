import { useMemo, useState } from "react";
import { AlertTriangle, BarChart3, Building2, Globe2, Layers3, MapPin, Network, ShieldAlert } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Panel } from "../components/ui/Panel";
import { RiskBadge } from "../components/ui/RiskBadge";
import { companiesDemo } from "../data/companiesDemo";
import { eventsDemo } from "../data/eventsDemo";
import type { InspectorContext } from "../data/inspectorDemo";
import { domainExposureDemo, eventContributionDemo, hopExposureDemo, riskRankingDemo } from "../data/riskAnalysisDemo";

import "./RiskAnalysisPage.css";
import "./RiskAnalysisPhase2.css";

type RiskView = "network" | "geography" | "heatmap";

type RiskAnalysisPageProps = {
  selectedInspectorId?: string;
  onInspect: (context: InspectorContext) => void;
  onOpenProfile: (companyId: string) => void;
  onOpenImpact: (focus: { id: string; name: string; type: "Company" | "Event"; eventId?: string }) => void;
};

export function RiskAnalysisPage({ selectedInspectorId, onInspect, onOpenProfile, onOpenImpact }: RiskAnalysisPageProps) {
  const [view, setView] = useState<RiskView>("network");
  const [hop, setHop] = useState<number | null>(null);
  const [selectedContribution, setSelectedContribution] = useState<string | null>(null);
  const [industry] = useState("All Domains");

  const visibleContributions = useMemo(() => eventContributionDemo.filter((event) => !hop || event.hop === hop), [hop]);

  const inspectRanking = (companyName: string) => {
    const company = companiesDemo.find((candidate) => candidate.name === companyName);
    const ranking = riskRankingDemo.find((candidate) => candidate.company === companyName)!;
    onInspect({
      id: company?.companyId ?? `demo-${companyName.toLowerCase().replaceAll(" ", "-")}`,
      type: "Company",
      name: companyName,
      subtitle: "Selected from system-wide Risk Ranking",
      riskLevel: ranking.level,
      riskScore: ranking.score,
      fields: [{ label: "Contributing events", value: String(ranking.contributingEvents) }, { label: "Scope", value: industry }],
      evidence: { availability: "UNAVAILABLE" },
    });
  };

  return (
    <div className="risk-analysis-page">
      <header className="risk-analysis-header">
        <div><div className="risk-analysis-title-context"><span className="metadata-text">SYSTEM RISK</span><span className="demo-badge">DEVELOPMENT DATA</span></div><h1 className="page-title">Risk Analysis</h1><p className="body-text risk-analysis-subtitle">System-wide concentration and comparison. Specific origin propagation remains in Impact.</p></div>
        <div className="risk-analysis-history-state"><BarChart3 size={14} aria-hidden="true" /><span>History endpoint exists · fixture semantics remain explicit</span></div>
      </header>

      <section className="risk-scope-bar" aria-label="Risk analysis scope"><div className="risk-scope-item"><span>Scope</span><strong>Current System</strong></div><div className="risk-scope-item"><span>Industry</span><strong>{industry}</strong></div><div className="risk-scope-item is-disabled"><span>Time</span><strong>Adapter pending</strong></div></section>

      <section className="risk-summary-grid">
        <Panel eyebrow="Concentration" title="Risk Ranking">
          <div className="risk-ranking-list">{riskRankingDemo.map((company, index) => {
            const id = companiesDemo.find((candidate) => candidate.name === company.company)?.companyId ?? `demo-${company.company.toLowerCase().replaceAll(" ", "-")}`;
            return <article key={company.company} className={`risk-ranking-row phase2-selectable${selectedInspectorId === id ? " is-selected" : ""}`} tabIndex={0} role="button" onClick={() => inspectRanking(company.company)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inspectRanking(company.company); }}><span className="risk-rank-number">{index + 1}</span><div className="risk-ranking-company"><strong>{company.company}</strong><span>{company.contributingEvents} contributing event{company.contributingEvents === 1 ? "" : "s"}</span><div className="phase2-inline-actions">{companiesDemo.some((candidate) => candidate.companyId === id) && <Button variant="ghost" onClick={(event) => { event.stopPropagation(); onOpenProfile(id); }}>Open Profile</Button>}<Button variant="secondary" onClick={(event) => { event.stopPropagation(); onOpenImpact({ id, name: company.company, type: "Company" }); }}>Open Impact</Button></div></div><div className="risk-ranking-value"><strong>{company.score}</strong><RiskBadge level={company.level} /></div></article>;
          })}</div>
        </Panel>

        <Panel eyebrow="Domain concentration" title="Domain Exposure"><div className="domain-exposure-list">{domainExposureDemo.map((domain) => <article className="domain-exposure-row" key={domain.domain}><div><Building2 size={15} aria-hidden="true" /><span>{domain.domain}</span></div><div><strong>{domain.exposedCompanies}</strong><span>companies</span></div><RiskBadge level={domain.highestRisk} /></article>)}</div></Panel>

        <Panel eyebrow="Propagation depth" title="Hop Exposure">
          <div className="hop-exposure-list">{hopExposureDemo.map((item) => { const hopNumber = Number(item.hop.replace("Hop ", "")); return <button type="button" className={`hop-exposure-row phase2-hop-button${hop === hopNumber ? " is-selected" : ""}`} key={item.hop} aria-pressed={hop === hopNumber} onClick={() => setHop((current) => current === hopNumber ? null : hopNumber)}><div className="hop-exposure-icon"><Layers3 size={15} aria-hidden="true" /></div><div className="hop-exposure-copy"><strong>{item.hop}</strong><span>{item.description}</span></div><strong className="hop-exposure-count">{item.companies}</strong></button>; })}</div>
          <p className="phase2-interaction-note">Hop selection filters the view only; it does not recompute backend risk.</p>
        </Panel>
      </section>

      <Panel variant="workspace" eyebrow="Analytical view" title="Risk Concentration" description="Lens switching preserves the same fixture scope and hop selection.">
        <div className="risk-view-tabs">{(["network", "geography", "heatmap"] as RiskView[]).map((lens) => <button key={lens} type="button" className={`risk-view-tab${view === lens ? " is-active" : ""}`} aria-pressed={view === lens} onClick={() => setView(lens)}>{lens === "network" ? <Network size={14} aria-hidden="true" /> : lens === "geography" ? <Globe2 size={14} aria-hidden="true" /> : <BarChart3 size={14} aria-hidden="true" />}<span>{lens[0].toUpperCase() + lens.slice(1)}</span></button>)}</div>
        <div className="risk-view-content">{view === "network" && <RiskNetworkView hop={hop} />}{view === "geography" && <GeographyView onInspect={onInspect} />}{view === "heatmap" && <HeatmapView />}</div>
      </Panel>

      <section className="risk-context-grid">
        <Panel eyebrow="Why?" title="Event Contributions">
          <div className="event-contribution-list">{visibleContributions.length > 0 ? visibleContributions.map((event) => {
            const key = `${event.eventType}-${event.company}`;
            const sourceEvent = eventsDemo.find((candidate) => candidate.type === event.eventType);
            return <button type="button" className={`event-contribution-row phase2-contribution-button${selectedContribution === key ? " is-selected" : ""}`} key={key} onClick={() => { setSelectedContribution(key); onInspect({ id: sourceEvent?.id ?? key, type: "Event", name: event.eventType, subtitle: `Contribution to ${event.company}`, riskScore: event.propagatedRisk, fields: [{ label: "Affected company", value: event.company }, { label: "Hop", value: String(event.hop) }, { label: "Propagated Risk", value: event.propagatedRisk }], evidence: { availability: sourceEvent ? "PARTIAL" : "UNAVAILABLE", source: sourceEvent?.source, provenance: sourceEvent ? "Development fixture" : undefined } }); }}><div><AlertTriangle size={14} aria-hidden="true" /><div><strong>{event.eventType}</strong><span>{event.company}</span></div></div><div className="event-contribution-value"><span>Hop {event.hop}</span><strong>{event.propagatedRisk}</strong></div></button>;
          }) : <div className="phase2-interaction-note">No event contributions match Hop {hop}. Clear the Hop selection to restore all fixture contributions.</div>}</div>
          {selectedContribution && (() => { const event = eventContributionDemo.find((item) => `${item.eventType}-${item.company}` === selectedContribution); const source = eventsDemo.find((candidate) => candidate.type === event?.eventType); return event ? <div className="phase2-inline-actions"><Button variant="primary" onClick={() => onOpenImpact({ id: source?.id ?? selectedContribution, name: event.eventType, type: "Event", eventId: source?.id })}>Open Impact</Button></div> : null; })()}
        </Panel>

        <Panel eyebrow="Interpretation" title="Risk Context"><div className="risk-context-body"><ShieldAlert size={20} aria-hidden="true" /><div><strong>History semantics remain backend-defined</strong><p>Historical interaction may select a point/event when live data is adapted, but this fixture does not claim persisted market-grade snapshots.</p></div></div></Panel>
      </section>
    </div>
  );
}

function RiskNetworkView({ hop }: { hop: number | null }) {
  return <div className="risk-network-view"><div className="risk-network-center"><ShieldAlert size={21} aria-hidden="true" /><strong>System Risk</strong><span>{hop ? `Hop ${hop} filter` : "Current exposure"}</span></div><div className="risk-network-company risk-network-company--critical"><strong>NVIDIA</strong><span>0.75</span><RiskBadge level="CRITICAL" /></div><div className="risk-network-company risk-network-company--high"><strong>TSMC</strong><span>0.61</span><RiskBadge level="HIGH" /></div><div className="risk-network-company risk-network-company--medium"><strong>Samsung</strong><span>0.42</span><RiskBadge level="MEDIUM" /></div><div className="risk-network-demo-label">DEMO NETWORK CONCENTRATION</div></div>;
}

function GeographyView({ onInspect }: { onInspect: (context: InspectorContext) => void }) {
  const entities: Array<{ id: string; type: "Country" | "Location" | "Facility"; name: string; related: string }> = [
    { id: "demo-country-taiwan", type: "Country", name: "Taiwan", related: "TSMC development context" },
    { id: "demo-location-hsinchu", type: "Location", name: "Hsinchu context", related: "Development location fixture · no coordinate invented" },
    { id: "demo-facility-1", type: "Facility", name: "Demo Fab", related: "Related company: TSMC" },
  ];

  return <div className="geography-unavailable"><div className="geography-icon"><MapPin size={24} aria-hidden="true" /></div><div><span className="metadata-text">GEOGRAPHY LENS · DEVELOPMENT FIXTURE</span><h3>Geographic entities inspect without creating logistics telemetry</h3><p>No coordinate is fabricated here. Selecting a Country, Location, or Facility opens the same contextual Inspector pattern used elsewhere.</p><div className="phase2-geography-list">{entities.map((entity) => <button type="button" key={entity.id} onClick={() => onInspect({ id: entity.id, type: entity.type, name: entity.name, subtitle: entity.related, relatedCompanyId: entity.type === "Facility" ? "demo-tsmc" : undefined, fields: [{ label: "Geography role", value: entity.type }, { label: "Coordinate", value: "Not available in this fixture" }], evidence: { availability: "UNAVAILABLE" } })}><strong>{entity.name}</strong><span>{entity.type}</span></button>)}</div><div className="geography-integrity-note">No ships, routes, ETA, AIS, port telemetry, or synthetic coordinates.</div></div></div>;
}

function HeatmapView() {
  const cells = [{ label: "Semiconductors", level: "critical" }, { label: "Electronics", level: "high" }, { label: "EV / Battery", level: "medium" }, { label: "Aerospace", level: "low" }];
  return <div className="risk-heatmap"><div className="risk-heatmap-grid">{cells.map((cell) => <div key={cell.label} className={`risk-heatmap-cell risk-heatmap-cell--${cell.level}`}><span>{cell.label}</span><strong>{cell.level.toUpperCase()}</strong></div>)}</div><p>Development-only categorical heatmap. Production values must originate from backend risk results.</p></div>;
}
