import {
  ArrowRight,
  Building2,
  Factory,
  FileText,
  Globe2,
  Link2,
  MapPin,
  Package,
  ShieldCheck,
  Wrench,
  X,
  Boxes,
} from "lucide-react";

import { Button } from "../ui/Button";
import { RiskBadge } from "../ui/RiskBadge";

import type {
  InspectorContext,
  InspectorEntityType,
} from "../../data/inspectorDemo";

import "./EntityInspector.css";

type EntityInspectorProps = {
  context: InspectorContext | null;
  onClose?: () => void;
};

const entityIcons: Record<
  InspectorEntityType,
  typeof Building2
> = {
  Company: Building2,
  Facility: Factory,
  Material: Boxes,
  Product: Package,
  Technology: Wrench,
  Country: Globe2,
  Location: MapPin,
  Event: ShieldCheck,
  Relationship: Link2,
};

export function EntityInspector({
  context,
  onClose,
}: EntityInspectorProps) {
  if (!context) {
    return (
      <aside className="entity-inspector">
        <div className="inspector-header">
          <span className="metadata-text">CONTEXT</span>

          <h2 className="card-heading">
            Entity Inspector
          </h2>
        </div>

        <div className="inspector-empty">
          <div
            className="inspector-empty-icon"
            aria-hidden="true"
          >
            +
          </div>

          <p>
            Select an entity to inspect its available context.
          </p>

          <span>
            Company, facility, material, product, technology, country,
            location, event, and relationship context will appear here.
          </span>
        </div>
      </aside>
    );
  }

  const Icon = entityIcons[context.type];

  return (
    <aside
      className="entity-inspector"
      aria-label={`${context.name} inspector`}
    >
      <div className="entity-inspector-toolbar">
        <div>
          <span className="metadata-text">
            CONTEXT
          </span>

          <span className="inspector-demo-label">
            DEVELOPMENT
          </span>
        </div>

        {onClose && (
          <button
            type="button"
            className="inspector-close-button"
            aria-label="Close inspector"
            onClick={onClose}
          >
            <X size={15} />
          </button>
        )}
      </div>

      <section className="inspector-identity">
        <div className="inspector-identity-icon">
          <Icon size={20} aria-hidden="true" />
        </div>

        <div>
          <span>{context.type}</span>

          <h2>{context.name}</h2>

          {context.subtitle && (
            <p>{context.subtitle}</p>
          )}
        </div>
      </section>

      {(context.riskLevel || context.riskScore) && (
        <section className="inspector-section">
          <span className="inspector-section-label">
            CURRENT RISK
          </span>

          <div className="inspector-risk">
            {context.riskScore && (
              <strong>{context.riskScore}</strong>
            )}

            {context.riskLevel && (
              <RiskBadge level={context.riskLevel} />
            )}
          </div>
        </section>
      )}

      <section className="inspector-section">
        <span className="inspector-section-label">
          METADATA
        </span>

        <div className="inspector-field-list">
          {context.fields.map((field) => (
            <div
              className="inspector-field"
              key={field.label}
            >
              <span>{field.label}</span>
              <strong>{field.value}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="inspector-section">
        <div className="inspector-section-heading">
          <span className="inspector-section-label">
            EVIDENCE
          </span>

          <FileText size={14} aria-hidden="true" />
        </div>

        {context.evidence ? (
          <div className="inspector-evidence">
            <InspectorEvidenceField
              label="Source"
              value={context.evidence.source}
            />

            <InspectorEvidenceField
              label="Confidence"
              value={
                context.evidence.confidence ??
                "Not available"
              }
            />

            <InspectorEvidenceField
              label="Provenance"
              value={
                context.evidence.provenance ??
                "Not available"
              }
            />
          </div>
        ) : (
          <span className="inspector-unavailable">
            Not available
          </span>
        )}
      </section>

      <section className="inspector-actions">
        <Button
          variant="secondary"
          icon={<ArrowRight size={14} />}
          disabled
        >
          Open Profile
        </Button>

        <Button
          variant="ghost"
          disabled
        >
          View Evidence
        </Button>
      </section>
    </aside>
  );
}

type InspectorEvidenceFieldProps = {
  label: string;
  value: string;
};

function InspectorEvidenceField({
  label,
  value,
}: InspectorEvidenceFieldProps) {
  return (
    <div className="inspector-evidence-field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}