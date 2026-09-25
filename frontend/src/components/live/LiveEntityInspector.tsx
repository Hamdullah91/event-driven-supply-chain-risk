import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Building2, FileText, GitBranch, ShieldCheck, X } from "lucide-react";

import { useCompany, useCompanyNetwork, useCompanyRisk, useEvent } from "../../query/hooks";
import type { InspectorRef } from "../../state/uiStore";
import { Button } from "../ui/Button";
import { RiskBadge } from "../ui/RiskBadge";
import type { LiveInspectorAction } from "./LiveAppShell";

import "../layout/EntityInspector.css";

type Props = {
  reference: InspectorRef;
  onClose: () => void;
  onAction: (action: LiveInspectorAction, ref: InspectorRef) => void;
};

export function LiveEntityInspector({ reference, onClose, onAction }: Props) {
  const [showEvidence, setShowEvidence] = useState(false);
  const companyId = reference.entityType === "Company" && reference.kind !== "relationship" ? reference.id : undefined;
  const eventId = reference.entityType === "Event" ? reference.id : undefined;
  const graphFocusId = reference.kind === "relationship" ? reference.context?.graphFocusId : undefined;
  const graphDepth = reference.context?.graphDepth ?? 1;
  const company = useCompany(companyId);
  const companyRisk = useCompanyRisk(companyId, 3);
  const event = useEvent(eventId);
  const relationshipGraph = useCompanyNetwork(graphFocusId, graphDepth);

  const relationship = useMemo(() => relationshipGraph.data?.edges.find((edge) => edge.id === reference.context?.relationshipId), [reference.context?.relationshipId, relationshipGraph.data?.edges]);
  const nodeNames = useMemo(() => Object.fromEntries((relationshipGraph.data?.nodes ?? []).map((node) => [node.id, node.label])), [relationshipGraph.data?.nodes]);

  useEffect(() => {
    const onKeyDown = (keyboardEvent: KeyboardEvent) => { if (keyboardEvent.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const name = relationship ? relationship.type : company.data?.name ?? event.data?.eventType ?? reference.name ?? reference.id;
  const type = reference.kind === "relationship" ? "Relationship" : reference.entityType ?? "Unknown";
  const loading = (company.isPending && Boolean(companyId)) || (event.isPending && Boolean(eventId)) || (relationshipGraph.isPending && Boolean(graphFocusId));
  const error = (company.isError && Boolean(companyId)) || (event.isError && Boolean(eventId)) || (relationshipGraph.isError && Boolean(graphFocusId));
  const evidence = event.data?.evidence;
  const actions: LiveInspectorAction[] = company.data
    ? ["Open Profile", "Explore Network", "Open Impact"]
    : event.data
      ? ["Open Event", "Open Impact"]
      : reference.context?.relatedCompanyId
        ? ["Open Company"]
        : [];

  return (
    <aside className="entity-inspector" aria-label={`${name} inspector`}>
      <div className="entity-inspector-toolbar"><div><span className="metadata-text">CONTEXT</span><span className="inspector-demo-label">LIVE DATA</span></div><button type="button" className="inspector-close-button" aria-label="Close inspector" onClick={onClose}><X size={15} /></button></div>
      <section className="inspector-identity"><div className="inspector-identity-icon">{reference.kind === "relationship" ? <GitBranch size={20} aria-hidden="true" /> : <Building2 size={20} aria-hidden="true" />}</div><div><span>{type}</span><h2>{name}</h2><p>{reference.id}</p></div></section>

      {actions.length > 0 && <section className="inspector-actions" aria-label="Inspector actions">{actions.map((action, index) => <Button key={action} variant={index === 0 ? "secondary" : "ghost"} icon={<ArrowRight size={14} />} onClick={() => onAction(action, reference)}>{action}</Button>)}</section>}

      <div className="entity-inspector-scroll">
        {loading && <section className="inspector-section"><span className="inspector-section-label">LOADING</span><span className="inspector-unavailable">Resolving canonical live context…</span></section>}
        {error && <section className="inspector-section"><span className="inspector-section-label">UNAVAILABLE</span><span className="inspector-unavailable">This reference could not be resolved. No unrelated entity is substituted.</span></section>}

        {relationship && <section className="inspector-section"><span className="inspector-section-label">RELATIONSHIP</span><div className="inspector-field-list"><div className="inspector-field"><span>Direction</span><strong>{nodeNames[relationship.sourceId] ?? relationship.sourceId} → {nodeNames[relationship.targetId] ?? relationship.targetId}</strong></div><div className="inspector-field"><span>Type</span><strong>{relationship.type}</strong></div><div className="inspector-field"><span>Dependency weight</span><strong>{relationship.weight === undefined ? "Not available" : relationship.weight.toFixed(3)}</strong></div><div className="inspector-field"><span>Weight source</span><strong>{relationship.weightSource ?? "Not available"}</strong></div><div className="inspector-field"><span>Confidence</span><strong>{relationship.confidence === undefined ? "Not available" : `${(relationship.confidence * 100).toFixed(0)}%`}</strong></div></div></section>}

        {relationship?.evidence && <section className="inspector-section"><span className="inspector-section-label">EVIDENCE</span><div className={`evidence-availability evidence-availability--${relationship.evidence.availability.toLowerCase()}`}>{relationship.evidence.availability}</div><span className="inspector-unavailable">Source: {relationship.evidence.source ?? "Not available"}</span></section>}

        {company.data && <section className="inspector-section"><span className="inspector-section-label">OVERVIEW</span><div className="inspector-field-list"><div className="inspector-field"><span>Legal name</span><strong>{company.data.legalName ?? "Not available"}</strong></div><div className="inspector-field"><span>Industry</span><strong>{company.data.industryId ?? "Not available"}</strong></div><div className="inspector-field"><span>Entity type</span><strong>{company.data.entityType ?? "Company"}</strong></div></div></section>}

        {companyRisk.data && <section className="inspector-section"><span className="inspector-section-label">CURRENT RISK</span><div className="inspector-risk"><strong>{companyRisk.data.currentRisk.toFixed(3)}</strong><RiskBadge level={companyRisk.data.riskLevel} /></div><div className="inspector-field"><span>Contributing events</span><strong>{companyRisk.data.contributingEventCount}</strong></div></section>}

        {event.data && <section className="inspector-section"><span className="inspector-section-label">EVENT</span><div className="inspector-field-list"><div className="inspector-field"><span>Severity</span><strong>{event.data.severity.toUpperCase()}</strong></div><div className="inspector-field"><span>Classifier confidence</span><strong>{event.data.confidence === undefined ? "Not available" : `${(event.data.confidence * 100).toFixed(0)}%`}</strong></div><div className="inspector-field"><span>Timestamp</span><strong>{event.data.timestamp || "Not available"}</strong></div><div className="inspector-field"><span>Source</span><strong>{event.data.source}</strong></div></div></section>}

        {event.data && <section className="inspector-section"><div className="inspector-section-heading"><span className="inspector-section-label">EVIDENCE</span><FileText size={14} aria-hidden="true" /></div><div className={`evidence-availability evidence-availability--${event.data.evidence.availability.toLowerCase()}`}>{event.data.evidence.availability}</div>{evidence?.availability !== "UNAVAILABLE" ? <><Button variant="ghost" className="inspector-evidence-toggle" onClick={() => setShowEvidence((value) => !value)} aria-expanded={showEvidence}>View Evidence</Button>{showEvidence && <div className="inspector-evidence"><div className="inspector-evidence-field"><span>Source</span><strong>{evidence?.source ?? "Not available"}</strong></div><div className="inspector-evidence-field"><span>Confidence</span><strong>{evidence?.confidence === undefined ? "Not available" : `${(evidence.confidence * 100).toFixed(0)}%`}</strong></div></div>}</> : <span className="inspector-unavailable">Evidence unavailable</span>}</section>}

        {!relationship && !company.data && !event.data && !loading && !error && <section className="inspector-section"><ShieldCheck size={16} aria-hidden="true" /><span className="inspector-unavailable">No dedicated detail endpoint exists for this entity type. Search identity is preserved without inventing metadata or actions.</span></section>}
      </div>
    </aside>
  );
}
