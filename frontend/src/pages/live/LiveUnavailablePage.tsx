import { ShieldCheck } from "lucide-react";
import { Panel } from "../../components/ui/Panel";

export function LiveUnavailablePage({ title, description }: { title: string; description: string }) {
  return (
    <div className="phase3-live-state">
      <header><span className="metadata-text">LIVE DATA MODE</span><h1 className="page-title">{title}</h1></header>
      <Panel variant="workspace" eyebrow="Controlled migration" title="Live integration pending for this workspace" description={description}>
        <div className="phase2-interaction-note"><ShieldCheck size={16} aria-hidden="true" /> Phase 3 never falls back to development fixtures when a live contract is unavailable or fails.</div>
      </Panel>
    </div>
  );
}
