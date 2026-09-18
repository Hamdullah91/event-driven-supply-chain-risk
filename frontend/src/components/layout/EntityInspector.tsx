import { useEffect, useState } from "react";
import {
  ArrowRight,
  Boxes,
  Building2,
  Factory,
  FileText,
  Globe2,
  Layers3,
  Link2,
  MapPin,
  Package,
  Route,
  ShieldCheck,
  Wrench,
  X,
} from "lucide-react";

import { Button } from "../ui/Button";
import { RiskBadge } from "../ui/RiskBadge";
import type { InspectorContext, InspectorEntityType } from "../../data/inspectorDemo";

import "./EntityInspector.css";

export type InspectorAction =
  | "Open Profile"
  | "Explore Network"
  | "Open Impact"
  | "Open Event"
  | "Open Company"
  | "Highlight Path";

type EntityInspectorProps = {
  context: InspectorContext;
  onClose: () => void;
  onAction?: (action: InspectorAction, context: InspectorContext) => void;
};

const entityIcons: Record<InspectorEntityType, typeof Building2> = {
  Company: Building2,
  Facility: Factory,
  Material: Boxes,
  Product: Package,
  Technology: Wrench,
  Industry: Layers3,
  Country: Globe2,
  Location: MapPin,
  Event: ShieldCheck,
  Relationship: Link2,
};

function contextualActions(context: InspectorContext): InspectorAction[] {
  switch (context.type) {
    case "Company":
      return ["Open Profile", "Explore Network", "Open Impact"];
    case "Event":
      return ["Open Event", "Open Impact"];
    case "Relationship":
      return context.path?.length ? ["Highlight Path"] : [];
    case "Facility":
      return context.relatedCompanyId
        ? ["Explore Network", "Open Company"]
        : ["Explore Network"];
    default:
      return ["Explore Network"];
  }
}

export function EntityInspector({ context, onClose, onAction }: EntityInspectorProps) {
  const [showEvidence, setShowEvidence] = useState(false);
  const Icon = entityIcons[context.type];
  const evidenceAvailable =
    context.evidence && context.evidence.availability !== "UNAVAILABLE";

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <aside className="entity-inspector" aria-label={`${context.name} inspector`}>
      <div className="entity-inspector-toolbar">
        <div>
          <span className="metadata-text">CONTEXT</span>
          <span className="inspector-demo-label">DEVELOPMENT FIXTURE</span>
        </div>

        <button
          type="button"
          className="inspector-close-button"
          aria-label="Close inspector"
          onClick={onClose}
        >
          <X size={15} />
        </button>
      </div>

      <section className="inspector-identity">
        <div className="inspector-identity-icon"><Icon size={20} aria-hidden="true" /></div>
        <div>
          <span>{context.type}</span>
          <h2>{context.name}</h2>
          {context.subtitle && <p>{context.subtitle}</p>}
        </div>
      </section>

      {(context.riskLevel || context.riskScore) && (
        <section className="inspector-section">
          <span className="inspector-section-label">RISK / EXPOSURE</span>
          <div className="inspector-risk">
            {context.riskScore !== undefined && <strong>{context.riskScore}</strong>}
            {context.riskLevel && <RiskBadge level={context.riskLevel} />}
          </div>
        </section>
      )}

      {context.fields.length > 0 && (
        <section className="inspector-section">
          <span className="inspector-section-label">OVERVIEW</span>
          <div className="inspector-field-list">
            {context.fields.map((field) => (
              <div className="inspector-field" key={`${field.label}-${field.value}`}>
                <span>{field.label}</span>
                <strong>{field.value}</strong>
              </div>
            ))}
          </div>
        </section>
      )}

      {context.path && context.path.length > 1 && (
        <section className="inspector-section">
          <div className="inspector-section-heading">
            <span className="inspector-section-label">PATH</span>
            <Route size={14} aria-hidden="true" />
          </div>
          <p className="inspector-path-text">{context.path.join(" → ")}</p>
        </section>
      )}

      {context.evidence && (
        <section className="inspector-section">
          <div className="inspector-section-heading">
            <span className="inspector-section-label">EVIDENCE</span>
            <FileText size={14} aria-hidden="true" />
          </div>

          <div className={`evidence-availability evidence-availability--${context.evidence.availability.toLowerCase()}`}>
            {context.evidence.availability}
          </div>

          {evidenceAvailable ? (
            <>
              <Button
                variant="ghost"
                className="inspector-evidence-toggle"
                onClick={() => setShowEvidence((value) => !value)}
                aria-expanded={showEvidence}
              >
                View Evidence
              </Button>

              {showEvidence && (
                <div className="inspector-evidence" aria-live="polite">
                  <InspectorEvidenceField label="Source" value={context.evidence.source ?? "Not available"} />
                  <InspectorEvidenceField label="Confidence" value={context.evidence.confidence ?? "Not available"} />
                  <InspectorEvidenceField label="Provenance" value={context.evidence.provenance ?? "Not available"} />
                  <InspectorEvidenceField label="Extracted context" value={context.evidence.excerpt ?? "Not available"} />
                </div>
              )}
            </>
          ) : (
            <span className="inspector-unavailable">Evidence unavailable</span>
          )}
        </section>
      )}

      <section className="inspector-actions" aria-label="Inspector actions">
        {contextualActions(context).map((action, index) => (
          <Button
            key={action}
            variant={index === 0 ? "secondary" : "ghost"}
            icon={<ArrowRight size={14} />}
            onClick={() => onAction?.(action, context)}
          >
            {action}
          </Button>
        ))}
      </section>
    </aside>
  );
}

type InspectorEvidenceFieldProps = { label: string; value: string };

function InspectorEvidenceField({ label, value }: InspectorEvidenceFieldProps) {
  return (
    <div className="inspector-evidence-field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
